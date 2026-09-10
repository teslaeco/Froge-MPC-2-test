"""Inspect the exported GLB, then reopen it in Blender before accepting it.

Structural checks never imply photographic likeness or print readiness.
"""
import json
import math
import struct
from collections import Counter
import bpy


def verify_prop_grip(objects):
    """Check actual fingertip mesh proximity, not just requested pose values."""
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    records=[]
    for hand in objects:
        if 'grip_contact_positions' not in hand:continue
        props=[o for o in objects if o.get('character')==hand.get('character') and
               o.get('froge_role') in ('pleated-fan','fan-grip-handle')]
        vertices=[];faces=[]
        for prop in props:
            start=len(vertices);vertices.extend(prop.matrix_world@v.co for v in prop.data.vertices)
            faces.extend(tuple(start+i for i in f.vertices) for f in prop.data.polygons)
        if not vertices:raise ValueError('A gripping hand has no fan or handle')
        surface=BVHTree.FromPolygons(vertices,faces)
        skin=[hand.matrix_world@v.co for v in hand.data.vertices]
        scale=hand.matrix_world.to_scale().x
        values=list(hand['grip_contact_positions'])
        if len(values)!=15:raise ValueError('Grip must keep all five finger contacts')
        gaps=[];depths=[]
        for i in range(0,15,3):
            centre=hand.matrix_world@Vector(values[i:i+3]);samples=[v for v in skin if (v-centre).length<.010*scale]
            if not samples:raise ValueError('Grip contact is detached from the actual finger mesh')
            distances=[];depth=0.
            for v in samples:
                hit,normal,_,distance=surface.find_nearest(v)
                distances.append(distance)
                depth=max(depth,max(0.,-(v-hit).dot(normal)))
            gap=min(distances)
            if gap>.0035*scale:raise ValueError('Finger %d floats %.3f mm away from the fan grip' % (i//3+1,gap/scale*1000))
            gaps.append(round(gap/scale*1000,3));depths.append(round(depth/scale*1000,3))
        records.append({'fingertip_surface_gaps_mm':gaps,'local_signed_depths_mm':depths})
    return {'hands':len(records),'contacts':5*len(records),'details':records,'passed':True,
            'complete_hand_collision_checked':False}


def verify_free_hand_clearance(objects):
    """Reject hand edges crossing the actual gown or cape after posing."""
    from mathutils.bvhtree import BVHTree
    records=[]
    for hand in objects:
        if not hand.get('anatomical_hand') or not hand.get('couture_pose_revision') or 'grip_contact_positions' in hand:continue
        clothes=[o for o in objects if o.get('character')==hand.get('character') and o.get('froge_role') in
                 ('fitted-gown','conformal-facets','visible-pleated-cape','shoulder-drape')]
        vertices=[];faces=[]
        for cloth in clothes:
            start=len(vertices);vertices.extend(cloth.matrix_world@v.co for v in cloth.data.vertices)
            faces.extend(tuple(start+i for i in f.vertices) for f in cloth.data.polygons)
        if not vertices:raise ValueError('Free couture hand has no garment to check')
        surface=BVHTree.FromPolygons(vertices,faces)
        skin=[hand.matrix_world@v.co for v in hand.data.vertices]
        scale=hand.matrix_world.to_scale().x;epsilon=.000001*scale
        closest=min(surface.find_nearest(v)[3] for v in skin)
        crossings=0
        for edge in hand.data.edges:
            a,b=(skin[i] for i in edge.vertices);direction=b-a;length=direction.length
            if length<=2*epsilon:continue
            direction/=length
            hit=surface.ray_cast(a+direction*epsilon,direction,length-2*epsilon)[0]
            if hit is not None:crossings+=1
        if crossings:raise ValueError('Free hand cuts through gown/cape: %d crossing edges' % crossings)
        if closest<.003*scale:raise ValueError('Free hand has less than 3 mm clearance from gown/cape')
        records.append({'hand':hand.name,'checked_edges':len(hand.data.edges),'crossing_edges':crossings,
                        'minimum_vertex_clearance_mm':round(closest/scale*1000,3)})
    return {'hands':len(records),'details':records,'passed':True,'scope':'free hand skin versus gown and cape'}


def verify_fan_apertures(objects):
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    windows=rays=filled=junctions=0
    for obj in objects:
        count=int(obj.get('open_turbine_windows',0))
        if not count:continue
        coordinates=list(obj['turbine_window_centers']);radius=float(obj['turbine_window_radius'])
        if len(coordinates)!=count*3 or radius<=0:raise ValueError('Invalid turbine window metadata')
        surface=BVHTree.FromPolygons([v.co for v in obj.data.vertices],[f.vertices[:] for f in obj.data.polygons])
        for i in range(count):
            x,_,z=coordinates[i*3:i*3+3]
            # Empty-space tests alone passed when a Boolean removed almost
            # the whole fan. A crystal panel must remain below each window.
            if surface.ray_cast(Vector((x*.55,-.12,z*.55)),Vector((0,1,0)),.3)[0] is None:
                raise ValueError('Fan lost the crystal filling below a turbine')
            filled+=1
            if obj.get('fitted_window_surrounds'):
                for j in range(6):
                    a=(j+.5)*math.tau/6
                    point=Vector((x+radius*1.08*math.sin(a),-.12,z+radius*1.08*math.cos(a)))
                    if surface.ray_cast(point,Vector((0,1,0)),.3)[0] is None:
                        raise ValueError('Gap between crystal filling and turbine frame')
                    junctions+=1
            samples=[(x,z)]+[(x+radius*r*math.sin(j*math.tau/6),z+radius*r*math.cos(j*math.tau/6))
                             for r in (.35,.70) for j in range(6)]
            for xx,zz in samples:
                rays+=1
                if surface.ray_cast(Vector((xx,-.12,zz)),Vector((0,1,0)),.3)[0] is not None:
                    raise ValueError('Fan aperture contains an opaque backing panel')
            windows+=1
    return {'windows':windows,'clear_rays':rays,'filled_panel_rays':filled,'filled_frame_junction_rays':junctions,'passed':True}


def verify_containment(objects):
    from couture_geometry import envelope_ratio
    checked=0;worst=0.
    for obj in objects:
        if not obj.get('contained_by_gown'):continue
        hem,width,offset,thickness=obj['gown_envelope']
        samples=[v.co for v in obj.data.vertices]
        samples += [sum((obj.data.vertices[i].co for i in f.vertices),__import__('mathutils').Vector())/len(f.vertices)
                    for f in obj.data.polygons]
        for point in samples:
            if not .10<=point.z<=1.45:continue
            ratio=envelope_ratio(point,hem,width,offset-thickness)
            worst=max(worst,ratio);checked+=1
            if ratio>1.0001:raise ValueError('Suknia: cialo przecina wewnetrzna powierzchnie ubrania.')
    return {'samples':checked,'worst_envelope_ratio':round(worst,6),'passed':True}


def verify_fingerless_glove(objects):
    """Verify the actual closed leather shell, including after GLB splitting."""
    import bmesh
    records=[]
    for obj in objects:
        if not obj.get('fingerless_wrap_samples'):continue
        mesh=bmesh.new()
        try:
            mesh.from_mesh(obj.data)
            bmesh.ops.remove_doubles(mesh,verts=list(mesh.verts),dist=1e-6)
            if not all(edge.is_manifold for edge in mesh.edges):
                raise ValueError('Fingerless glove lost its closed cloth shell')
            volume=abs(mesh.calc_volume(signed=True))
            if not 1e-8<volume<.0002:
                raise ValueError('Fingerless glove has invalid shell volume')
            records.append({'closed_shell':True,'volume_m3':volume,'surface_samples':int(obj['fingerless_wrap_samples'])})
        finally:mesh.free()
    return {'gloves':len(records),'details':records,'passed':True,'scope':'closed leather shell; does not verify every finger collision'}


def verify_export(path, source_objects):
    verify_containment(source_objects)
    verify_fan_apertures(source_objects)
    verify_prop_grip(source_objects)
    verify_free_hand_clearance(source_objects)
    verify_fingerless_glove(source_objects)
    data=path.read_bytes();magic,version,length=struct.unpack_from('<III',data)
    if (magic,version,length)!=(0x46546C67,2,len(data)):raise ValueError('Invalid GLB header')
    size,kind=struct.unpack_from('<II',data,12)
    if kind!=0x4e4f534a:raise ValueError('Missing GLB JSON chunk')
    doc=json.loads(data[20:20+size])
    if any('uri' in b for b in doc.get('buffers',[])):raise ValueError('External geometry in GLB')
    if any('bufferView' not in image for image in doc.get('images',[])):raise ValueError('Missing packed GLB texture')
    projected=[o for o in source_objects if o.get('reference_surface_faces',0)>0]
    projection_faces=0
    for obj in projected:
        meshes=[m for m in doc.get('meshes',[]) if m.get('name')==obj.data.name]
        matching=[]
        for mesh in meshes:
            for primitive in mesh['primitives']:
                mat=doc['materials'][primitive['material']]
                if mat.get('extras',{}).get('reference_surface_sha256')!=obj['reference_surface_sha256']:continue
                texture=mat.get('pbrMetallicRoughness',{}).get('baseColorTexture')
                if texture is None or 'TEXCOORD_'+str(texture.get('texCoord',0)) not in primitive['attributes']:
                    raise ValueError('Export lost reference image or its mapped UV coordinates')
                matching.append(primitive)
        if not matching:raise ValueError('Export lost original-photo surface: '+obj.name)
        projection_faces+=int(obj['reference_surface_faces'])
    for material in doc.get('materials',[]):
        sheen=material.get('extensions',{}).get('KHR_materials_sheen',{})
        if max(sheen.get('sheenColorFactor',[0]))>.35:
            raise ValueError('Eksport: zbyt jasny polysk przeslania kolor tkaniny.')
        metallic=material.get('pbrMetallicRoughness',{}).get('metallicFactor',0)
        if sheen and metallic>.061:
            raise ValueError('Eksport: satyna zachowuje sie jak metal i traci kolor.')
        transmission=material.get('extensions',{}).get('KHR_materials_transmission',{})
        if transmission and metallic>.081:
            raise ValueError('Eksport: krysztal zachowuje sie jak chrom i traci kolor.')
    makeup_heads=[o for o in source_objects if o.get('anatomical_head') and o.data.color_attributes.get('CosmeticTint')]
    colored_objects=makeup_heads+[o for o in source_objects if o.get('facet_tint_required')]
    for obj in colored_objects:
        meshes=[m for m in doc.get('meshes',[]) if m.get('name')==obj.data.name]
        if not meshes or any('COLOR_0' not in p['attributes'] for m in meshes for p in m['primitives']):
            raise ValueError('Eksport utracil kolor powierzchni COLOR_0: '+obj.name)
    expected=Counter(o.get('froge_role') for o in source_objects if o.get('froge_role'))
    anatomy={key:sum(bool(o.get(key)) for o in source_objects) for key in
             ('anatomical_head','anatomical_eye','anatomical_hand','anatomical_nail')}
    # Import into the current scene and isolate the newly created objects.
    # Do not destroy the artist's source scene or save this inspection copy.
    before=set(bpy.data.objects)
    try:
        bpy.ops.import_scene.gltf(filepath=str(path))
        imported=[o for o in bpy.data.objects if o not in before and o.type=='MESH']
        if not imported:raise ValueError('GLB reimport contains no geometry')
        actual=Counter(o.get('froge_role') for o in imported if o.get('froge_role'))
        if actual!=expected:raise ValueError('Export lost couture parts')
        for key,count in anatomy.items():
            if sum(bool(o.get(key)) for o in imported)!=count:raise ValueError('Export lost anatomy: '+key)
        expected_lashes=[list(o['upper_lashes_per_eye']) for o in source_objects if 'upper_lashes_per_eye' in o]
        actual_lashes=[list(o['upper_lashes_per_eye']) for o in imported if 'upper_lashes_per_eye' in o]
        if sorted(actual_lashes)!=sorted(expected_lashes):raise ValueError('Eksport utracil rzesy portretu.')
        def brow_details(items):
            return sorted((int(o['brow_fibre_count']),bool(o.get('brow_photo_contour_aligned',False)))
                          for o in items if 'brow_fibre_count' in o)
        eyebrows=brow_details(imported)
        if eyebrows!=brow_details(source_objects):raise ValueError('Eksport utracil wloski lub dopasowanie brwi.')
        for obj in imported:
            if not obj.data.vertices or not all(math.isfinite(c) for v in obj.data.vertices for c in v.co):
                raise ValueError('Export contains empty or non-finite geometry')
            if obj.get('anatomical_head') and not obj.data.uv_layers:raise ValueError('Export lost portrait UVs')
            if (obj.get('makeup_tint_required') or obj.get('facet_tint_required')) and not obj.get('reference_surface_faces',0):
                color=obj.data.color_attributes.active_color
                if color is None or not any(min(c.color[:3])<.98 for c in color.data):
                    raise ValueError('Eksport zastapil kolor powierzchni bialym kolorem wierzcholkow.')
        containment=verify_containment(imported)
        apertures=verify_fan_apertures(imported)
        grip=verify_prop_grip(imported)
        free_hand=verify_free_hand_clearance(imported)
        gloves=verify_fingerless_glove(imported)
        return {'reimported':True,'anatomy':anatomy,'roles':dict(actual),'packed_images':len(doc.get('images',[])),
                'reference_surface_objects':len(projected),'reference_surface_faces':projection_faces,
                'fan_apertures':apertures,'prop_grip':grip,'free_hand_clearance':free_hand,'fingerless_glove':gloves,'eyebrows_fibres_and_photo_contour':eyebrows,
                'garment_containment':containment,'makeup_heads':len(makeup_heads),'upper_lashes_per_eye':actual_lashes,
                'likeness_assessed':False,'print_readiness_assessed':False}
    finally:
        for obj in list(bpy.data.objects):
            if obj not in before:bpy.data.objects.remove(obj,do_unlink=True)
