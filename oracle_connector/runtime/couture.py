"""Trusted, bounded reference-couture geometry; no generated code is executed."""
import math
import bpy
from mathutils import Vector

from detailed_geometry import person


def rotor(p, material, accent, mesh_object):
    """One compact, editable turbine mesh suitable for linked radial copies."""
    r, depth, blades = p['radius'], p['depth'], p['blades']
    verts, faces, materials = [], [], []
    for y in (-depth / 2, depth / 2):
        for i in range(16):
            a = math.tau * i / 16
            verts.append((p['center'][0] + r*.24*math.cos(a), p['center'][1] + y,
                          p['center'][2] + r*.24*math.sin(a)))
    for i in range(16):
        faces.append((i, (i+1)%16, 16+(i+1)%16, 16+i)); materials.append(1)
    for blade in range(blades):
        a = math.tau*blade/blades
        start = len(verts)
        for y in (-depth*.35, depth*.35):
            for radius, da in ((r*.28, -.10), (r, .16), (r*.78, .42), (r*.31, .22)):
                verts.append((p['center'][0]+radius*math.cos(a+da), p['center'][1]+y,
                              p['center'][2]+radius*math.sin(a+da)))
        faces += [(start,start+1,start+2,start+3), (start+7,start+6,start+5,start+4)]
        faces += [(start+i,start+(i+1)%4,start+4+(i+1)%4,start+4+i) for i in range(4)]
        materials += [0]*6
    obj = mesh_object(p['name'], verts, faces, material)
    obj.data.materials.append(accent)
    for polygon, index in zip(obj.data.polygons, materials): polygon.material_index=index
    obj['froge_role']='reusable-rotor'
    return obj


def reference_character(p, materials, mesh_object, tube, ellipsoid, join_meshes, loft):
    """Complete anatomy plus close-fit couture and explicitly reconstructed unseen areas."""
    base = {**p, 'top_material': p['dress_material'], 'trouser_material': p['dress_material'],
            'presentation': 'feminine', 'outfit': 'sweatshirt', 'hair_style': 'short',
            'headwear': 'none', 'microphone': False}
    parts = person(base, materials, mesh_object, tube, ellipsoid, join_meshes)
    center, h = Vector(p['center']), p['height']; s=h/1.8
    dress, accent, hair = (materials[p[k]] for k in ('dress_material','accent_material','hair_material'))
    def world(x,y,z): return tuple(center + Vector((x*s,y*s,z*s)))
    # The skirt starts at the anatomical waist and stays close before opening at the hem.
    sections=[]
    for z,rx,ry in ((.06,p['hem_radius'],.31),(.18,p['hem_radius']*.98,.30),(.48,.31,.19),
                    (.82,.205,.125),(1.00,.184,.112),(1.08,.181,.111)):
        sections.append({'center':world(0,0,z),'radii':[rx*s+p['garment_offset'],ry*s+p['garment_offset']]})
    skirt=loft(p['name']+'-floor-gown',sections,64,dress,mesh_object)
    skirt['froge_role']='reconstructed-floor-gown'; skirt['garment_offset_m']=p['garment_offset']; skirt['garment_thickness_m']=p['garment_thickness']
    parts.append(skirt)
    # Belt and collar are surface-attached tubes, never torso shells.
    for label,z,rx,ry in (('belt',1.075,.183,.114),('collar',1.475,.076,.067)):
        points=[world(rx*math.cos(math.tau*i/48),ry*math.sin(math.tau*i/48),z) for i in range(49)]
        obj=tube(p['name']+'-'+label,points,[max(.0025,p['garment_thickness'])*s]*49,accent,8)
        obj['froge_role']='observed-'+label; parts.append(obj)
    # Four thin crystalline panels touch the dress at every row.
    for index,(x0,x1,z0,z1) in enumerate(((-.15,-.02,.18,1.05),(.02,.15,.18,1.05),(-.20,-.11,.72,1.39),(.11,.20,.72,1.39))):
        y=-(.116+p['garment_offset']/s)
        verts=[world(x0,y,z0),world(x1,y,z0),world(x1*.75,y-.002,z1),world(x0*.75,y-.002,z1)]
        panel=mesh_object(p['name']+'-crystal-panel-%d'%index,verts,[(0,1,2,3)],accent)
        solid=panel.modifiers.new('bounded-panel-thickness','SOLIDIFY'); solid.thickness=p['garment_thickness']
        bpy.context.view_layer.objects.active=panel; bpy.ops.object.modifier_apply(modifier=solid.name)
        panel['froge_role']='attached-crystalline-panel'; panel['thickness_m']=p['garment_thickness']; parts.append(panel)
    if p['updo']:
        for i,(x,y,z,scale) in enumerate(((0,.035,1.75,.090),(-.035,.045,1.79,.068),(.035,.042,1.81,.060),(0,.065,1.84,.045))):
            obj=ellipsoid(p['name']+'-updo-%d'%i,world(x,y,z),(scale*s,scale*.78*s,scale*.82*s),hair,3)
            obj['froge_role']='sculpted-updo'; parts.append(obj)
    if p['hair_ornament']:
        ornament=ellipsoid(p['name']+'-hair-ornament',world(.065,-.005,1.79),(.025*s,.012*s,.045*s),accent,2)
        ornament['froge_role']='hair-ornament'; parts.append(ornament)
    for obj in parts:
        obj['characterStandard']=18
        obj['observedFeatures']='; '.join(p['observed_features'])
        obj['reconstructedFeatures']='; '.join(p['reconstructed_features'])
    return parts
