import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from runtime.scene_exports import export_interchange


class SceneExportTests(unittest.TestCase):
    def test_all_exports_share_master_and_document_lossy_formats(self):
        bpy = SimpleNamespace(ops=SimpleNamespace(
            object=SimpleNamespace(select_all=Mock()),
            export_scene=SimpleNamespace(fbx=Mock()),
            wm=SimpleNamespace(obj_export=Mock(), stl_export=Mock()),
        ))
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            source = folder / 'scene.json'
            source.write_text('{"version":1}')
            with patch.dict('sys.modules', {'bpy': bpy}):
                report = export_interchange(folder, source)
            self.assertEqual((folder / 'model.froge-scene.json').read_bytes(), source.read_bytes())
        bpy.ops.export_scene.fbx.assert_called_once()
        bpy.ops.wm.obj_export.assert_called_once()
        bpy.ops.wm.stl_export.assert_called_once()
        self.assertEqual(bpy.ops.wm.stl_export.call_args.kwargs['global_scale'], 1000.0)
        self.assertTrue(report['fbx']['textures_embedded'])
        self.assertFalse(report['stl']['textures'])
        self.assertFalse(report['stl']['print_readiness_assessed'])
        self.assertIn('model.mtl', report['obj']['mtl'])

    def test_generated_script_has_no_scene_json_claim(self):
        bpy = SimpleNamespace(ops=SimpleNamespace(
            object=SimpleNamespace(select_all=Mock()),
            export_scene=SimpleNamespace(fbx=Mock()),
            wm=SimpleNamespace(obj_export=Mock(), stl_export=Mock()),
        ))
        with tempfile.TemporaryDirectory() as tmp, patch.dict('sys.modules', {'bpy': bpy}):
            report = export_interchange(tmp)
        self.assertFalse(report['scene_json']['present'])


if __name__ == '__main__':
    unittest.main()
