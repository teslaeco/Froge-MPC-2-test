"""Build only the complete Oracle worker packages, without frontend/add-on assets."""
from pathlib import Path
import io
import os
import runpy
import sys
import tempfile
import zipfile

root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'oracle_connector'))
worker_files=[*runpy.run_path(str(root/'oracle_connector/apply_update.py'))['FILES'],'apply_update.py']
folder=root/'public/downloads';folder.mkdir(parents=True,exist_ok=True)
for filename,names in (
    ('froge-oracle-connector.zip',['install.sh','pull_model.py','README.md']+worker_files),
    ('froge-oracle-update.zip',worker_files)):
    contents={name:(root/'oracle_connector'/name).read_bytes() for name in names}
    buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,'w',zipfile.ZIP_DEFLATED) as archive:
        for name,data in contents.items():
            info=zipfile.ZipInfo(name,(2026,9,11,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            archive.writestr(info,data)
    with tempfile.NamedTemporaryFile(dir=folder,delete=False) as pending:
        temporary=Path(pending.name);pending.write(buffer.getvalue());pending.flush();os.fsync(pending.fileno())
    try:
        with zipfile.ZipFile(temporary) as archive:
            if archive.testzip() or any(archive.read(name)!=data for name,data in contents.items()):
                raise RuntimeError('Incomplete worker archive: '+filename)
        temporary.replace(folder/filename)
    finally:temporary.unlink(missing_ok=True)
    print(filename,(folder/filename).stat().st_size,'bytes')
runpy.run_path(str(root/'scripts/package-v22.py'),run_name='__main__')
