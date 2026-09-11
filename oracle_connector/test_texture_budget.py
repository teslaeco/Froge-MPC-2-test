"""Exercise the real export guard without requiring local Blender installation.

The Cloud Shell repair additionally requires a real isolated Blender/GLB export.
"""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest


class TextureBudgetTests(unittest.TestCase):
    def run_guard(self, material_count=8, image_count=10, unused=0):
        source = Path(__file__).parent / 'runtime/run.py'
        function = next(node for node in ast.parse(source.read_text()).body if isinstance(node, ast.FunctionDef) and node.name == 'finish')
        materials = [SimpleNamespace(users=1) for _ in range(material_count)]
        images = [SimpleNamespace(users=1) for _ in range(image_count)]
        images.extend(SimpleNamespace(users=0) for _ in range(unused))
        self.data = SimpleNamespace(materials=materials, images=images, meshes=[])
        scope = {'Path':Path,'bpy': SimpleNamespace(data=self.data, context=SimpleNamespace(scene=SimpleNamespace(objects=[],get=lambda key,default:default)))}
        exec(compile(ast.Module(body=[function], type_ignores=[]), str(source), 'exec'), scope)
        scope['finish']()

    def test_eight_albedos_plus_shared_normals_reach_geometry_validation(self):
        with self.assertRaisesRegex(ValueError, 'Scene needs'):
            self.run_guard(unused=12)
        self.assertEqual(len(self.data.materials), 8)
        self.assertEqual(len(self.data.images), 10)

    def test_resource_limits_still_apply_to_used_data(self):
        for materials, images in [(17, 10), (8, 17)]:
            with self.subTest(materials=materials, images=images), self.assertRaisesRegex(ValueError, 'Export limit:'):
                self.run_guard(materials, images)


if __name__ == '__main__':
    unittest.main()
