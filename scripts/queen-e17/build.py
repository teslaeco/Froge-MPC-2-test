"""Reproduce the authored Queen Neptune fixture using the production runtime.
Face remains approximate because the matching source photograph is unavailable.
"""
from pathlib import Path
import sys,json,runpy,time
import bpy
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'runtime'))
from scene_contract import parse_scene
from build_scene import build_scene
started=time.monotonic()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.render.threads_mode='FIXED'
bpy.context.scene.render.threads=2
runtime=runpy.run_path(str(ROOT/'runtime/run.py'),run_name='queen_fixture')
scene=parse_scene((ROOT/'scene.json').read_text())
build_scene(scene,*(runtime[n] for n in ('make_material','mesh_object','tube','ellipsoid','join_meshes')),reference_folder=ROOT)
runtime['finish'](ROOT)
report=json.loads((ROOT/'result.json').read_text())
report.update(source='Queen Neptune: authored production couture fixture, parameterized adult face',source_photo_matching=False,poster_used_as_general_design_reference=True,likeness_accepted=False,build_seconds=round(time.monotonic()-started,2))
(ROOT/'queen-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print('QUEEN_E17_READY',report['triangles'],flush=True)
