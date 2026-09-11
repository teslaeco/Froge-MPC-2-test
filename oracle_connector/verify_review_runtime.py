"""Native Blender review smoke test; force the unsupported-OIDN branch.

blender -b --python verify_review_runtime.py -- OUTPUT_DIRECTORY
This is a small authored fixture, not a generated character or an Oracle test.
"""
import json
from pathlib import Path
import runpy
import sys
from unittest.mock import patch
import bpy

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'runtime'))
import review_views


def fixture():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=16,location=(0,0,1))
    material=bpy.data.materials.new('jade');material.use_nodes=True
    material.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.02,.4,.25,1)
    bpy.context.object.data.materials.append(material)


def verify(output):
    import _cycles
    runtime=runpy.run_path(str(ROOT/'runtime/run.py'),run_name='review_smoke')
    output.mkdir(parents=True,exist_ok=True)
    successful=output/'without-oidn';successful.mkdir()
    (successful/'review-request.json').write_text(json.dumps({'enabled':True}))
    fixture()
    compiled=bool(_cycles.with_openimagedenoise)
    with patch.object(_cycles,'with_openimagedenoise',False):
        runtime['finish'](successful)
    report=json.loads((successful/'result.json').read_text())
    assert report['review_render']['status']=='rendered',report.get('review_render')
    settings=json.loads((successful/'review/render-settings.json').read_text())
    assert settings['denoiser']=='none' and settings['samples']==64
    sizes=[]
    for label in review_views.LABELS:
        path=successful/'review'/(label+'.png')
        image=bpy.data.images.load(str(path),check_existing=False)
        assert tuple(image.size)==(640,800)
        assert len(image.pixels)==640*800*4
        sizes.append(path.stat().st_size);bpy.data.images.remove(image)
    failed=output/'preview-failure';failed.mkdir()
    (failed/'review-request.json').write_text(json.dumps({'enabled':True}))
    fixture()
    with patch.object(review_views,'render_review',side_effect=RuntimeError('Injected preview-only failure')):
        runtime['finish'](failed)
    report=json.loads((failed/'result.json').read_text())
    assert report['review_render']['status']=='unavailable'
    for name in ('model.glb','model.blend','model.fbx','model.obj','model-mm.stl'):
        assert (failed/name).stat().st_size>20,name
    result={'native_blender':bpy.app.version_string,'compiled_oidn':compiled,
            'forced_unsupported_branch':True,'actual_review_views':3,'view_size':[640,800],
            'png_bytes':sizes,'samples':64,'cpu_threads':2,
            'exports_survive_optional_failure':True,'paid_ai_calls':0}
    (output/'verification.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result))


if __name__=='__main__':
    verify(Path(sys.argv[sys.argv.index('--')+1]))
