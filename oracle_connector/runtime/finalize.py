"""Export an already reviewed, locally generated Blender file without remodeling."""
import json
from pathlib import Path
import sys
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from scene_exports import export_interchange
from model_checkpoint import save_ready

def finalize(folder=Path('/work')):
    folder=Path(folder)
    bpy.ops.wm.open_mainfile(filepath=str(folder/'model.blend'),use_scripts=False)
    report=json.loads((folder/'result.json').read_text())
    report['interchange_exports']=export_interchange(folder,folder/'scene.json')
    report['master_export']['formats']=report['interchange_exports']['formats']
    (folder/'result.json').write_text(json.dumps(report))
    save_ready(folder,report,'interchange_exports')
    return report

if __name__=='__main__':
    finalize()
    print('FROGE_EXPORTS_READY')
