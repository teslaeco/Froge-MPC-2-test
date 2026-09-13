"""Create a separate 200 mm engineering candidate; never edits the visual source.

blender -b --threads 2 --python build_print_candidate.py -- \
  --input FINAL_E19.glb --output-dir print-candidate --height-mm 200 --voxel-mm 0.4

The requested height includes a 5 mm base. It is an explicit working assumption,
not a user-approved order dimension. Fine surface fibers are omitted from this
candidate; larger hair locks are retained. A real post-export audit is mandatory.
"""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
import bpy
import bmesh
import numpy as np
from mathutils import Matrix, Vector


def activate(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def world_bounds(objects):
    points=[obj.matrix_world @ Vector(p) for obj in objects for p in obj.bound_box]
    return np.min(points,axis=0),np.max(points,axis=0)


def write_binary_stl(obj, path):
    import struct
    mesh=obj.data
    mesh.calc_loop_triangles()
    with path.open('wb') as stream:
        stream.write(b'FORGE E19 engineering candidate millimetres; NOT CERTIFIED'.ljust(80,b' '))
        stream.write(struct.pack('<I',len(mesh.loop_triangles)))
        for tri in mesh.loop_triangles:
            a,b,c=[obj.matrix_world @ mesh.vertices[i].co for i in tri.vertices]
            normal=(b-a).cross(c-a)
            if normal.length:normal.normalize()
            stream.write(struct.pack('<12fH',*normal,*a,*b,*c,0))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--height-mm',type=float,default=200.)
    parser.add_argument('--voxel-mm',type=float,default=0.4)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if not 100<=args.height_mm<=500 or not 0.3<=args.voxel_mm<=0.5:
        raise ValueError('Bounded prototype: height100–500mm, voxel0.3–0.5mm')
    out=args.output_dir.resolve();out.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(args.input.resolve()))
    source_objects=[o for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_render]
    # Textures are irrelevant to the uncoloured STL and can consume substantial
    # RAM for8K visual maps. Only this separately imported scene is affected.
    for material in list(bpy.data.materials):bpy.data.materials.remove(material)
    for texture_image in list(bpy.data.images):bpy.data.images.remove(texture_image)
    low,high=world_bounds(source_objects)
    body_height=args.height_mm-4.0
    scale=body_height/(high[2]-low[2])
    origin=np.array([(high[0]+low[0])/2,(high[1]+low[1])/2,low[2]])
    matrix=Matrix.Translation(Vector((0,0,4.0))) @ Matrix.Diagonal((scale,scale,scale,1.)) @ Matrix.Translation(Vector(-origin))
    # Original glTF coordinates are metres; these prototype object coordinates
    # intentionally become millimetres. Scene unit scale is adjusted below.
    skipped=[];solidified=[];decimated=[];capped=[];objects=[]
    for obj in list(source_objects):
        name=obj.name.lower()
        if any(t in name for t in ('individual hair fibers','960 tapered hairline fibers','lash','eyeliner','cornea','tearline','catchlight')):
            skipped.append({'name':obj.name,'triangles_estimate':sum(max(0,len(p.vertices)-2) for p in obj.data.polygons),'reason':'submillimetre visual layer, larger anatomical/hair masses retained'})
            bpy.data.objects.remove(obj,do_unlink=True)
            continue
        obj.data=obj.data.copy()  # preserve independent instances during transform apply
        obj.matrix_world=matrix @ obj.matrix_world
        activate(obj)
        bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
        triangle_count=sum(max(0,len(face.vertices)-2) for face in obj.data.polygons)
        if triangle_count>400000:
            simplify=obj.modifiers.new('Print-copy bounded simplification','DECIMATE')
            simplify.ratio=300000/triangle_count
            bpy.ops.object.modifier_apply(modifier=simplify.name)
            decimated.append({'name':obj.name,'before_triangles':triangle_count,'target_triangles':300000})
        # Weld print-copy export seams at0.0001mm, far below0.4mm voxel.
        # This is explicit geometric repair, unlike the exact-only read audit.
        bm=bmesh.new();bm.from_mesh(obj.data)
        bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-4)
        bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-7)
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
        boundary=sum(e.is_boundary for e in bm.edges)
        if boundary and any(token in obj.name.lower() for token in ('tailored_split_gown','continuous_shoulders_neck','gathered_sleeve','upper_arm')):
            filled=bmesh.ops.holes_fill(bm,edges=[e for e in bm.edges if e.is_boundary],sides=0)
            bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
            capped.append({'name':obj.name,'boundary_before':boundary,'cap_faces_created':len(filled.get('faces',[])),'purpose':'filled structural body instead of hollow shell'})
            boundary=sum(e.is_boundary for e in bm.edges)
        bm.to_mesh(obj.data);bm.free();obj.data.update()
        obj.data.materials.clear()
        for layer in list(obj.data.uv_layers):obj.data.uv_layers.remove(layer)
        if boundary:
            modifier=obj.modifiers.new('Engineering shell thickness 0.9 mm','SOLIDIFY')
            modifier.thickness=0.9;modifier.offset=-1.0
            modifier.use_even_offset=False  # avoid miter spikes at broken/near-parallel seams
            modifier.use_rim=True
            bpy.ops.object.modifier_apply(modifier=modifier.name)
            solidified.append({'name':obj.name,'boundary_edges_before':boundary,'nominal_shell_thickness_mm':0.9,'not_measured_minimum':True})
        objects.append(obj)
        print('PREPARED',obj.name,flush=True)
    # Wide plinth overlaps the hem by1mm. It is part of the candidate's physical
    # silhouette and deliberately visible in the manufacturing comparison.
    bpy.context.view_layer.update()
    low2,high2=world_bounds(objects)
    print('PRE_UNION_BOUNDS_MM',low2.tolist(),high2.tolist(),flush=True)
    if max(high2-low2)>args.height_mm*1.2:
        raise RuntimeError('Unexpected prototype bounds; refusing oversized voxel grid')
    bpy.ops.mesh.primitive_cylinder_add(vertices=128,radius=1,depth=5,location=(0,0,2.5))
    base=bpy.context.object;base.name='E19 engineering base 5mm'
    base.scale=(max(abs(low2[0]),abs(high2[0]))+5,max(abs(low2[1]),abs(high2[1]))+5,1)
    activate(base);bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    objects.append(base)
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:obj.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    bpy.ops.object.join()
    merged=bpy.context.object;merged.name='FORGE E19 print engineering candidate'
    for unused_mesh in list(bpy.data.meshes):
        if unused_mesh.users==0:bpy.data.meshes.remove(unused_mesh)
    print('VOXEL_BEGIN',args.voxel_mm,'input_faces',len(merged.data.polygons),flush=True)
    merged.data.remesh_voxel_size=args.voxel_mm
    merged.data.use_remesh_preserve_volume=True
    bpy.ops.object.voxel_remesh()
    print('VOXEL_DONE',len(merged.data.polygons),flush=True)
    # Clean generated topology only; no automatic disconnection deletion.
    bm=bmesh.new();bm.from_mesh(merged.data)
    bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-7)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(merged.data);bm.free();merged.data.update()
    bpy.context.view_layer.update()
    pre_low,pre_high=world_bounds([merged])
    final_scale=args.height_mm/(pre_high[2]-pre_low[2])
    for vertex in merged.data.vertices:
        vertex.co.z-=float(pre_low[2])
        vertex.co*=final_scale
    merged.data.update()
    bpy.context.view_layer.update()
    bpy.context.scene.unit_settings.system='METRIC'
    bpy.context.scene.unit_settings.scale_length=0.001
    # Report first. Mesh can be watertight but still contain multiple pieces;
    # audit script decides that rather than deleting floating anatomy silently.
    stem='FORGE-E19-print-candidate-%gmm' % args.height_mm
    stl=out/(stem+'.stl')
    write_binary_stl(merged,stl)
    bpy.ops.wm.save_as_mainfile(filepath=str(out/(stem+'.blend')),compress=True)
    # GLB must use metres: exporter receives a scaled copy, preserving mm BLEND.
    clone=merged.copy();clone.data=merged.data.copy();bpy.context.collection.objects.link(clone)
    clone.scale=(0.001,)*3;activate(clone)
    bpy.ops.export_scene.gltf(filepath=str(out/(stem+'.glb')),export_format='GLB',use_selection=True,export_materials='NONE')
    dims=(world_bounds([merged])[1]-world_bounds([merged])[0]).tolist()
    report={'schema':'forge.print-candidate-build/1','source':args.input.name,
            'source_sha256':hashlib.sha256(args.input.read_bytes()).hexdigest(),
            'working_assumed_total_height_mm':args.height_mm,'measured_dimensions_mm':dims,
            'scale_confirmed_by_customer':False,'nominal_voxel_mm':args.voxel_mm,'print_copy_seam_weld_tolerance_mm':0.0001,'post_remesh_uniform_dimension_scale':final_scale,
            'nominal_added_shell_thickness_mm':0.9,'base_height_mm':5.,'base_overlap_with_hem_mm':1.,
            'omitted_visual_layers':skipped,'solidified_objects':solidified,'print_only_simplification':decimated,'structural_opening_caps':capped,
            'manufacturing_ready':False,'post_export_audit_required':True,
            'limitations':['Nominal solidify thickness is not measured minimum thickness.','Voxel union changes fine details, hair, teeth and seam edges.','STL has no texture or standardized stored unit; this file uses mm.','FDM infill is a separate slicer parameter; no100%infill print was performed.','Machine/material/supports/thickness/tool access and physical proof are unverified.'],
            'stl_sha256':hashlib.sha256(stl.read_bytes()).hexdigest()}
    (out/'print-build-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PRINT_CANDIDATE_DONE',json.dumps({'dimensions_mm':dims,'stl':str(stl),'bytes':stl.stat().st_size}),flush=True)

if __name__=='__main__':main()
