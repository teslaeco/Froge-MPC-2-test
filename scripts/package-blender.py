from pathlib import Path
import runpy,zipfile
root=Path(__file__).resolve().parents[1]
runpy.run_path(str(root/'scripts/create-dragon.py'),run_name='__main__')
with zipfile.ZipFile(root/'public/downloads/froge-blender-addon.zip','w',zipfile.ZIP_DEFLATED) as archive:
    for path in sorted((root/'blender_addon/froge_studio').glob('*.py')):
        info=zipfile.ZipInfo('froge_studio/'+path.name,date_time=(2026,9,5,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
        archive.writestr(info,path.read_bytes())
print('Packaged Blender add-on')
