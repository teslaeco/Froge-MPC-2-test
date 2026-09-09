from pathlib import Path
import hashlib,re,runpy,zipfile
root=Path(__file__).resolve().parents[1]
# Preserve the independently fingerprinted v14 repair; rebuilding it from v15
# source would incorrectly advertise the old patch as compatible with v14.
# Keep the published v15 delta byte-for-byte; v16 ships a full worker archive.
runpy.run_path(str(root/'scripts/create-dragon.py'),run_name='__main__')
with zipfile.ZipFile(root/'public/downloads/froge-blender-addon.zip','w',zipfile.ZIP_DEFLATED) as archive:
    for path in sorted((root/'blender_addon/froge_studio').glob('*.py')):
        info=zipfile.ZipInfo('froge_studio/'+path.name,date_time=(2026,9,5,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
        archive.writestr(info,path.read_bytes())
print('Packaged Blender add-on')
assets = ['runtime/assets/'+name for name in ['anatomy.json.gz','male-skin.png','female-skin.png','cotton-jersey-albedo.png','indigo-denim-albedo.png','LICENSE.CC0.md','SOURCES.md','manifest.json']]
assets += ['runtime/'+name for name in ('portrait.py','portrait_eyes.py','portrait_shape.py','portrait_hands.py','portrait_hair.py','portrait_hair_surface.py','portrait_locks.py','fashion.py','couture.py','couture_geometry.py','couture_qa.py')]
files = ['install.sh', 'server.py', 'ai_stream.py', 'openai_provider.py', 'photo_input.py', 'runtime_check.py', 'apply_update.py', 'code_policy.py', 'pull_model.py', 'runtime/run.py', 'runtime/scene_contract.py', 'runtime/build_scene.py', 'runtime/detailed_geometry.py', 'runtime/anatomy.py', 'runtime/wardrobe.py', 'runtime/textiles.py', 'README.md'] + assets
with zipfile.ZipFile(root/'public/downloads/froge-oracle-connector.zip','w',zipfile.ZIP_DEFLATED) as archive:
    for name in files:
        info=zipfile.ZipInfo(name,date_time=(2026,9,6,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
        archive.writestr(info,(root/'oracle_connector'/name).read_bytes())
print('Packaged Oracle connector')
with zipfile.ZipFile(root/'public/downloads/froge-oracle-update.zip','w',zipfile.ZIP_DEFLATED) as archive:
    for name in ['server.py', 'ai_stream.py', 'openai_provider.py', 'photo_input.py', 'runtime_check.py', 'code_policy.py', 'runtime/run.py', 'runtime/scene_contract.py', 'runtime/build_scene.py', 'runtime/detailed_geometry.py', 'runtime/anatomy.py', 'runtime/wardrobe.py', 'runtime/textiles.py', 'apply_update.py'] + assets:
        info=zipfile.ZipInfo(name,date_time=(2026,9,6,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
        archive.writestr(info,(root/'oracle_connector'/name).read_bytes())
print('Packaged Oracle worker update')
runpy.run_path(str(root/'scripts/package-v19.py'),run_name='__main__')
# The Cloud Shell installer trusts the exact canonical payload, independent of
# browser-renamed ZIP filenames or archive timestamps.
with zipfile.ZipFile(root/'public/downloads/froge-oracle-update.zip') as archive:
    digest = hashlib.sha256()
    for name in sorted(archive.namelist()):
        digest.update(name.encode()+b'\0'+hashlib.sha256(archive.read(name)).digest())
installer = root/'public/downloads/froge-napraw-oracle.py'
updated, count = re.subn(r"^PAYLOAD_HASH = '[a-f0-9]{64}'$", "PAYLOAD_HASH = '"+digest.hexdigest()+"'", installer.read_text(), flags=re.MULTILINE)
if count != 1:
    raise RuntimeError('Missing verified Oracle installer fingerprint')
installer.write_text(updated)
(root/'public/downloads/froge-oracle-texture-fix.zip').write_bytes((root/'public/downloads/froge-oracle-update.zip').read_bytes())
(root/'public/downloads/froge-oracle-openai.zip').write_bytes((root/'public/downloads/froge-oracle-update.zip').read_bytes())
(root/'public/downloads/froge-oracle-rebuild.zip').write_bytes((root/'public/downloads/froge-oracle-update.zip').read_bytes())
(root/'public/downloads/froge-oracle-scene-v6.zip').write_bytes((root/'public/downloads/froge-oracle-update.zip').read_bytes())

(root/'public/downloads/froge-oracle-geometry-v7.zip').write_bytes((root/'public/downloads/froge-oracle-update.zip').read_bytes())

(root/'public/downloads/froge-oracle-characters-v8.zip').write_bytes((root/'public/downloads/froge-oracle-update.zip').read_bytes())

(root/'public/downloads/froge-oracle-wardrobe-v9.zip').write_bytes((root/'public/downloads/froge-oracle-update.zip').read_bytes())

(root/'public/downloads/froge-oracle-portrait-v10.zip').write_bytes((root/'public/downloads/froge-oracle-update.zip').read_bytes())

(root/'public/downloads/froge-oracle-style-v11.zip').write_bytes((root/'public/downloads/froge-oracle-update.zip').read_bytes())

(root/'public/downloads/froge-oracle-figures-v12.zip').write_bytes((root/'public/downloads/froge-oracle-update.zip').read_bytes())

(root/'public/downloads/froge-oracle-figures-v13.zip').write_bytes((root/'public/downloads/froge-oracle-update.zip').read_bytes())
