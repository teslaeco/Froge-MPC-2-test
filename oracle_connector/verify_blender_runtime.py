"""Real Blender material/export smoke test; not a test of AI output quality.

Run with a Python environment containing bpy 4.3. Only /work output paths are
remapped into a temporary directory; the runtime, policy and helpers are unchanged.
"""
import json
from pathlib import Path
import struct
import tempfile

import bpy
from code_policy import StreamPolicyGuard, validate_code

FIXTURE = '''bark = make_material("oak_bark", (0.27, 0.14, 0.06), "bark")
leaves = make_material("oak_leaves", (0.12, 0.36, 0.05), "leaf")
tube("trunk", [(0,0,0), (0.1,0,1), (0.2,0.1,2)], [0.18,0.12,0.04], bark)
mesh_object("leaf", [(0.2,0.1,2), (0.4,0.1,2.1), (0.6,0.3,2.05), (0.3,0.3,2)], [(0,1,2), (0,2,3)], leaves)
'''


def main():
    validate_code(FIXTURE)
    guard = StreamPolicyGuard()
    guard.feed(FIXTURE)
    runtime = Path(__file__).resolve().parent / 'runtime/run.py'
    with tempfile.TemporaryDirectory(prefix='froge-blender-') as directory:
        folder = Path(directory)
        (folder / 'generate.py').write_text(FIXTURE)
        source = runtime.read_text().replace('/work/', folder.as_posix() + '/')
        exec(compile(source, str(runtime), 'exec'), {'__name__': '__main__', '__file__': str(runtime)})
        data = (folder / 'model.glb').read_bytes()
        magic, version, length = struct.unpack_from('<III', data)
        assert magic == 0x46546C67 and version == 2 and length == len(data)
        json_length, chunk_type = struct.unpack_from('<II', data, 12)
        assert chunk_type == 0x4E4F534A
        document = json.loads(data[20:20 + json_length])
        images = document['images']
        assert len(images) == 2
        binary_start = 20 + json_length + 8
        for image in images:
            assert image.get('mimeType') == 'image/png' and 'uri' not in image
            view = document['bufferViews'][image['bufferView']]
            start = binary_start + view.get('byteOffset', 0)
            assert data[start:start + 8] == b'\x89PNG\r\n\x1a\n'
            assert view['byteLength'] > 1000
        assert len(document['meshes']) == 2
        assert len(document['materials']) == 2
        report = json.loads((folder / 'result.json').read_text())
        assert report['objects'] == 2 and report['triangles'] > 0
        print(json.dumps({'blender': bpy.app.version_string, 'bytes': len(data),
                          'embedded_png_textures': len(images), **report}))


if __name__ == '__main__':
    main()
