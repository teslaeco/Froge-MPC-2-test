"""E19 restrained groom correction for an open E18R scene.
Preserves the accepted fine-fibre groom; reduces thick core diameter by verified
longitudinal UV rings. Head/body/eyes/teeth are intentionally outside this module.
"""
import bpy, math, json, hashlib
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def apply():
    if bpy.context.scene.get('E19_hair_refined'):
        raise RuntimeError('Hair correction already applied')
    cores=[o for o in bpy.context.scene.objects if o.type=='MESH' and o.name.startswith('R11_Reference_')]
    fine=bpy.data.objects.get('E17 individual hair fibers and swept hairline')
    if len(cores)!=312 or fine is None:
        raise RuntimeError('Expected original E18R 312 hair cores and fine fibre groom; refusing unknown layout')
    anatomy={o.name:len(o.data.vertices) for o in bpy.context.scene.objects if o.type=='MESH' and o not in cores and o!=fine}
    changed=[];max_ring_radius=0.;mean_before=[];mean_after=[]
    for o in cores:
        me=o.data;uv=me.uv_layers.active
        if uv is None:raise RuntimeError('Hair core has no original longitudinal UV: '+o.name)
        coords=np.empty(len(me.vertices)*3,dtype=np.float32);me.vertices.foreach_get('co',coords);coords=coords.reshape(-1,3)
        t=np.full(len(coords),np.nan,dtype=np.float64)
        for loop in me.loops:t[loop.vertex_index]=round(float(uv.data[loop.index].uv.y),5)
        if not np.isfinite(t).all():raise RuntimeError('Incomplete hair UV ring coordinates')
        vals,inv=np.unique(t,return_inverse=True);counts=np.bincount(inv)
        if len(vals)<80 or np.any(counts!=8):raise RuntimeError('Unexpected hair ring topology: '+o.name)
        centers=np.stack([np.bincount(inv,weights=coords[:,i])/counts for i in range(3)],axis=1)
        radial=coords-centers[inv];before=np.linalg.norm(radial,axis=1)
        # Keep roots attached; middle cores become finer and taper further into tips.
        factors=.58+.25*np.exp(-(t/.10)**2)
        factors*=1-.15*np.maximum(0,(t-.70)/.30)
        after=centers[inv]+radial*factors[:,None]
        me.vertices.foreach_set('co',after.astype(np.float32).ravel());me.update()
        mean_before.append(float(np.mean(before)));mean_after.append(float(np.mean(before*factors)))
        max_ring_radius=max(max_ring_radius,float(np.max(before)))
        changed.append(o.name)
    # Keep a shared mild silhouette deformation on both fibres and core meshes,
    # retaining their alignment; upper root silhouette and head stay unchanged.
    for o in cores+[fine]:
        me=o.data;a=np.empty(len(me.vertices)*3,dtype=np.float32);me.vertices.foreach_get('co',a);a=a.reshape(-1,3)
        mat=np.array(o.matrix_world,dtype=np.float32);inv=np.linalg.inv(mat)
        world=a@mat[:3,:3].T+mat[:3,3]
        z=world[:,2];w=np.clip((1.58-z)/.22,0,1);w=w*w*(3-2*w)
        world[:,0]*=1-.035*w
        rear=np.clip((world[:,1]-.10)/.15,0,1)
        world[:,1]-=.009*w*rear
        restored=(world-mat[:3,3])@inv[:3,:3].T
        me.vertices.foreach_set('co',restored.astype(np.float32).ravel());me.update()
    edited_materials=[]
    for m in bpy.data.materials:
        if not (m.name.startswith('E17 chestnut') or m.name.startswith('E17 aged silver') or m.name.startswith('E18R root substrate')):continue
        bs=m.node_tree.nodes.get('Principled BSDF') if m.use_nodes else None
        if not bs:continue
        root=m.name.startswith('E18R root substrate')
        silver='silver' in m.name or (root and m.name.endswith('1'))
        try:shade=int(m.name.rsplit(' ',1)[-1])
        except ValueError:shade=2
        variation=.8+.11*min(shade,5)
        c=(.050*variation,.026*variation,.011*variation,1) if not silver else (.22*variation,.225*variation,.208*variation,1)
        if root:c=tuple(x*.43 for x in c[:3])+(1,)
        bs.inputs['Base Color'].default_value=c;bs.inputs['Roughness'].default_value=.65 if root else .50+.023*min(shade,5)
        bs.inputs['Metallic'].default_value=0
        if 'Coat Weight' in bs.inputs:bs.inputs['Coat Weight'].default_value=0
        if 'Anisotropic IOR Level' in bs.inputs:bs.inputs['Anisotropic IOR Level'].default_value=.55
        edited_materials.append(m.name)
    for name,n in anatomy.items():assert len(bpy.data.objects[name].data.vertices)==n
    bpy.context.scene['E19_hair_refined']=True
    report={'status':'restrained refinement of original accepted groom','changed_core_objects':len(changed),'preserved_fine_groom_triangles':sum(len(p.vertices)-2 for p in fine.data.polygons),'triangles_added':0,'mean_original_core_radius':sum(mean_before)/len(mean_before),'mean_refined_core_radius':sum(mean_after)/len(mean_after),'material_changes':edited_materials,'head_body_eye_teeth_geometry_edited':False,'silhouette_change':'Maximum 3.5% lower-hair width reduction; rear lower hair moved toward body by at most 9 mm; shared by core and fine fibres','limitations':['Still imperfect long-lock grouping and gaps; this is not a photorealism or reference-identity certification.','Fine strands require a separate fused production copy and manufacturing feature-size verification.','Rejected new curtain groom variants are not part of this patch.']}
    (ROOT/'hair-report.json').write_text(json.dumps(report,indent=2))
    print('E19_HAIR',json.dumps(report))
    return report

if __name__=='__main__':
    bpy.ops.wm.open_mainfile(filepath='/workspace/scratch/584c9d97a5a1/resume-model/FORGE-E18R-recovered-checkpoint.blend')
    apply()
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'hair-test.blend'),compress=True)
