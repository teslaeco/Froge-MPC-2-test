from pathlib import Path
import hashlib,re,runpy,zipfile,sys,io,os,tempfile
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
# One authoritative worker manifest keeps fresh installs and every update complete.
sys.path.insert(0,str(root/'oracle_connector'))
worker_files=[*runpy.run_path(str(root/'oracle_connector/apply_update.py'))['FILES'],'apply_update.py']
files=['install.sh','pull_model.py','README.md']+worker_files
def write_worker_archive(filename, names):
    contents={name:(root/'oracle_connector'/name).read_bytes() for name in names}
    buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,'w',zipfile.ZIP_DEFLATED) as archive:
        for name,data in contents.items():
            info=zipfile.ZipInfo(name,date_time=(2026,9,6,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            archive.writestr(info,data)
    destination=root/'public/downloads'/filename
    with tempfile.NamedTemporaryFile(dir=destination.parent,delete=False) as pending:
        temporary=Path(pending.name)
        pending.write(buffer.getvalue());pending.flush();os.fsync(pending.fileno())
    try:
        with zipfile.ZipFile(temporary) as archive:
            if archive.testzip() is not None or any(archive.read(name)!=data for name,data in contents.items()):
                raise RuntimeError('Incomplete worker archive: '+filename)
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)
write_worker_archive('froge-oracle-connector.zip',files)
print('Packaged Oracle connector')
write_worker_archive('froge-oracle-update.zip',worker_files)
print('Packaged Oracle worker update')
runpy.run_path(str(root/'scripts/package-v21.py'),run_name='__main__')
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
