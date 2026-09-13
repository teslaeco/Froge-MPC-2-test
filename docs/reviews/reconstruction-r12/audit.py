import bpy,json,math
from pathlib import Path
from mathutils.bvhtree import BVHTree
ROOT=Path('/workspace/scratch/584c9d97a5a1');OUT=ROOT/'reconstruction-r12'
current=bpy.data.objects['anatomical-head']
with bpy.data.libraries.load(str(ROOT/'face-repair/delivery/FORGE-model-1M.blend'),link=False) as (source,target):target.objects=['anatomical-head']
old=target.objects[0];tree=BVHTree.FromPolygons([v.co for v in old.data.vertices],[p.vertices[:] for p in old.data.polygons])
values=[];regions={k:[] for k in ['forehead','eye_cheek','nose','mouth_chin']}
for v in list(current.data.vertices)[::max(1,len(current.data.vertices)//10000)]:
 p=v.co
 if p.y>.04 or p.z<1.44:continue
 _,_,_,d=tree.find_nearest(p);values.append(d)
 region='forehead' if p.z>1.63 else 'eye_cheek' if p.z>1.55 else 'nose' if p.z>1.505 else 'mouth_chin';regions[region].append(d)
def stats(a):return {'samples':len(a),'unchanged_within_1e-5':sum(x<1e-5 for x in a),'mean_distance_scene_units':sum(a)/max(1,len(a)),'max_distance_scene_units':max(a,default=0)}
r={'comparison':'R11 head against original 1M head surface','sampling':'every Nth vertex, front y<.04 z>1.44; not area-weighted','overall':stats(values),'regions':{k:stats(a) for k,a in regions.items()},'root_cause':'density subdivision preserves existing piecewise surface; material changes cannot repair silhouette or anatomical continuity','visible_failures':['symmetric triangular scalp panel with transverse rails','oversized angular nasal opening','double skeletal jaw overlay and regular tooth rows','detached head-neck transition','bodice and sleeves remain simplified']}
(OUT/'surface-audit.json').write_text(json.dumps(r,indent=2));print(json.dumps(r),flush=True)
