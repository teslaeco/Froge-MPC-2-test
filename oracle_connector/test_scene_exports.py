import tempfile
import unittest
from pathlib import Path
from runtime.scene_exports import _checked_export


class SceneExportTests(unittest.TestCase):
    def run_export(self, operation, existing=False, key='fbx', files=None):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            names = files or ['model.fbx']
            if existing:
                for name in names:
                    (output/name).write_bytes(b'stale')
            report = {'formats': ['glb', 'blend'], key: {}}
            _checked_export(report, output, key, key, names, lambda: operation(output))
            return report, [(output/name).exists() for name in names]

    def test_cancel_does_not_accept_stale_files_or_remove_masters(self):
        report, present = self.run_export(lambda _: {'CANCELLED'}, existing=True)
        self.assertEqual(report['formats'], ['glb', 'blend'])
        self.assertEqual(report['fbx']['status'], 'failed')
        self.assertEqual(present, [False])

    def test_finished_without_output_is_a_failure(self):
        report, _ = self.run_export(lambda _: {'FINISHED'})
        self.assertEqual(report['fbx']['status'], 'failed')

    def test_error_is_isolated_and_cleans_partial_output(self):
        def operation(folder):
            (folder/'model.fbx').write_bytes(b'incomplete')
            raise RuntimeError('Exporter unavailable')
        report, present = self.run_export(operation)
        self.assertEqual(report['formats'], ['glb', 'blend'])
        self.assertEqual(report['fbx']['error'], 'Exporter unavailable')
        self.assertEqual(present, [False])

    def test_success_has_real_size_and_hash(self):
        def operation(folder):
            (folder/'model.fbx').write_bytes(b'exported')
            return {'FINISHED'}
        report, present = self.run_export(operation)
        self.assertEqual(report['formats'], ['glb', 'blend', 'fbx'])
        self.assertEqual(report['fbx']['files'][0]['bytes'], 8)
        self.assertEqual(len(report['fbx']['files'][0]['sha256']), 64)
        self.assertEqual(present, [True])

    def test_missing_obj_texture_is_rejected(self):
        def operation(folder):
            (folder/'model.obj').write_text('mtllib model.mtl')
            (folder/'model.mtl').write_text('map_Kd textures/missing.png')
            return {'FINISHED'}
        report, present = self.run_export(operation, key='obj', files=['model.obj','model.mtl'])
        self.assertEqual(report['obj']['status'], 'failed')
        self.assertEqual(present, [False, False])


if __name__ == '__main__':
    unittest.main()
