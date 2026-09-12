"""Project verified source pixels onto observed mesh faces with masks and depth.

Camera/mask estimates come from the scene plan. Hidden surfaces retain their
original materials. This does not recover intrinsic albedo or missing geometry.
"""
import hashlib
import json
import math
from pathlib import Path
from projection_math import camera_basis, project, inside


def apply_projections(views, parts, folder):
    report={'revision':2,'status':'not_requested','mapped_faces':0,'unmapped_faces':0,
            'source_images':[],'regions':[],'camera_estimates_verified':False,
            'photographed_lighting_removed':False,'likeness_verified':False}
    if not views:return report
    if folder is None:raise ValueError('Projekcja wymaga zapisanych zdjec referencyjnych.')
    folder=Path(folder);manifest=folder/'reference-photos.json'
    if manifest.is_symlink() or not manifest.is_file() or manifest.stat().st_size>160000:
        raise ValueError('Brak poprawnego manifestu zdjec do projekcji.')
    entries=json.loads(manifest.read_text())
    if not isinstance(entries,list) or len(entries)>4:raise ValueError('Nieprawidlowe referencje.')
    import bpy
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    images={}
    for index in sorted({v['photo_index'] for v in views}):
        if index>=len(entries):raise ValueError('Plan wskazuje nieprzeslane zdjecie: '+str(index))
        path=folder/('reference-%d.jpg'%index)
        if path.is_symlink() or not path.is_file() or not 20<=path.stat().st_size<=12*1024*1024:
            raise ValueError('Nieprawidlowy plik referencyjny.')
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        if digest!=entries[index].get('sha256'):raise ValueError('Zdjecie projekcji nie odpowiada manifestowi.')
        image=bpy.data.images.load(str(path),check_existing=True)
        if min(image.size)<1 or max(image.size)>8192:raise ValueError('Nieprawidlowe wymiary referencji.')
        image.name='photo-projection-'+digest[:16];image.pack();images[index]=image
        image['source_sha256']=digest;image['contains_photographed_lighting']=True
        report['source_images'].append({'photo_index':index,'sha256':digest,'size':list(image.size),'resampled':False})
    bpy.context.view_layer.update()
    all_objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
    vertices=[];polygons=[]
    for obj in all_objects:
        offset=len(vertices)
        vertices.extend(obj.matrix_world@v.co for v in obj.data.vertices)
        polygons.extend(tuple(offset+j for j in p.vertices) for p in obj.data.polygons)
    if not polygons:raise ValueError('Brak powierzchni do teksturowania.')
    bvh=BVHTree.FromPolygons(vertices,polygons,all_triangles=False)
    span=max(max(p[k] for p in vertices)-min(p[k] for p in vertices) for k in range(3))
    tolerance=max(1e-6,span*1e-5)
    choices={};target_objects=set()
    for view in views:
        image=images[view['photo_index']];aspect=image.size[0]/image.size[1]
        basis=camera_basis(view);forward=Vector(basis[0]);position=Vector(view['position'])
        for region in view['regions']:
            stats={'part':region['part'],'photo_index':view['photo_index'],'eligible_faces':0,
                   'protected_anatomy_faces':0,
                   'outside_mask':0,'back_facing':0,'occluded':0}
            for obj in parts[region['part']]:
                if obj.type!='MESH':continue
                # A fitted head already uses landmark-aligned colour and UVs.
                # A guessed whole-body camera must not overwrite those surfaces:
                # it paints a second pair of eyes/mouth onto the actual anatomy.
                if obj.get('anatomical_head') or obj.get('anatomical_eye') or obj.get('photo_fit_rigid_eye'):
                    stats['protected_anatomy_faces']+=len(obj.data.polygons)
                    continue
                target_objects.add(obj)
                normal_matrix=obj.matrix_world.to_3x3().inverted().transposed()
                for face in obj.data.polygons:
                    world=[obj.matrix_world@obj.data.vertices[j].co for j in face.vertices]
                    center=sum(world,Vector())/len(world)
                    normal=(normal_matrix@face.normal).normalized()
                    facing=normal.dot((position-center).normalized() if view['projection']=='perspective' else -forward)
                    if facing<.08:stats['back_facing']+=1;continue
                    samples=[center]+[p.lerp(center,.02) for p in world]
                    projected=[project(p,view,aspect,basis) for p in samples]
                    corners=[project(p,view,aspect,basis) for p in world]
                    if any(q is None or not (0<=q[0]<=1 and 0<=q[1]<=1) or not inside(q[:2],region['polygon']) for q in projected+corners):
                        stats['outside_mask']+=1;continue
                    visible=True
                    for point,q in zip(samples,projected):
                        origin=position if view['projection']=='perspective' else point-forward*q[2]
                        delta=point-origin;distance=delta.length
                        hit,_,_,hit_distance=bvh.ray_cast(origin,delta.normalized(),distance+tolerance)
                        if hit is None or abs(hit_distance-distance)>tolerance:
                            visible=False;break
                    if not visible:stats['occluded']+=1;continue
                    # Prefer a facing, sufficiently large observation for each face.
                    size=view['vertical_span'] if view['projection']=='orthographic' else 2*projected[0][2]*math.tan(view['fov']/2)
                    score=facing*image.size[1]/size
                    key=(obj,face.index)
                    if key not in choices or score>choices[key][0]:
                        choices[key]=(score,view['photo_index'],[(q[0],1-q[1]) for q in corners])
                    stats['eligible_faces']+=1
            report['regions'].append(stats)
    layers={};materials={}
    for obj in target_objects:
        # Copy mesh data to keep different projections of linked instances separate.
        if obj.data.users>1:obj.data=obj.data.copy()
        previous=obj.data.uv_layers.active
        layer=obj.data.uv_layers.get('PhotoProjectionUV') or obj.data.uv_layers.new(name='PhotoProjectionUV')
        if previous and previous!=layer:
            for i in range(len(layer.data)):layer.data[i].uv=previous.data[i].uv
        layers[obj]=layer
    for (obj,face_index),(_,index,uvs) in choices.items():
        face=obj.data.polygons[face_index]
        original=obj.data.materials[face.material_index] if obj.data.materials else None
        if original is None:raise ValueError('Brak bazowego materialu do projekcji.')
        key=(original,index)
        if key not in materials:
            mat=original.copy();mat.name=original.name+'-photo-'+str(index)
            shader=mat.node_tree.nodes.get('Principled BSDF')
            if shader is None:raise ValueError('Nieobslugiwany shader projekcji.')
            uv=mat.node_tree.nodes.new('ShaderNodeUVMap');uv.uv_map='PhotoProjectionUV'
            tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=images[index];tex.extension='CLIP'
            mat.node_tree.links.new(uv.outputs['UV'],tex.inputs['Vector'])
            mat.node_tree.links.new(tex.outputs['Color'],shader.inputs['Base Color'])
            mat['photo_projection']=True;mat['contains_photographed_lighting']=True
            mat['source_sha256']=images[index]['source_sha256'];materials[key]=mat
        mat=materials[key]
        if mat not in list(obj.data.materials):obj.data.materials.append(mat)
        face.material_index=list(obj.data.materials).index(mat)
        for i,uv in zip(face.loop_indices,uvs):layers[obj].data[i].uv=uv
    report['mapped_faces']=len(choices)
    report['unmapped_faces']=sum(len(o.data.polygons) for o in target_objects)-len(choices)
    report['added_materials']=len(materials)
    report['status']='projected_requires_visual_review' if choices else 'no_visible_faces_projected'
    report['hidden_surfaces']='original materials retained; unobserved geometry remains inferred'
    return report
