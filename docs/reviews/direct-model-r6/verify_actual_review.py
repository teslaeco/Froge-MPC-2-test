import sys,json
from pathlib import Path
import bpy
from mathutils import Vector
ROOT=Path('/workspace/scratch/584c9d97a5a1')
sys.path.insert(0,str(ROOT/'forge-worker/oracle_connector/runtime'))
from review_views import render_review,face_framing,geometry_bounds
OUT=ROOT/'model-repair/review-r4'
render_review(ROOT/'model-repair/FORGE-model-poprawka-r4.glb',OUT)
mesh=[o for o in bpy.context.scene.objects if o.type=='MESH']
eyes=[o for o in mesh if o.get('anatomical_eye')]
centre,scale,_=face_framing(mesh)
report={'eye_origins':[list(o.matrix_world.translation) for o in eyes],'eye_geometry_bounds':[[list(v) for v in geometry_bounds([o])] for o in eyes],'correct_face_target':list(centre),'face_scale':scale,'source':'actual exported r4 GLB','likeness_accepted':False}
(OUT/'actual-framing-proof.json').write_text(json.dumps(report,indent=2))
print('ACTUAL_FRAMING',json.dumps(report))
