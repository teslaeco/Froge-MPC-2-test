"""Retain a verified primary model if optional export/review exceeds its time."""
import hashlib
import json
from pathlib import Path
import struct

NAME='model-ready.json'


def model_digest(folder):
    path=Path(folder)/'model.glb'
    if path.is_symlink() or not path.is_file():return None
    size=path.stat().st_size
    if not 20<=size<=48*1024**2:return None
    with path.open('rb') as stream:
        header=stream.read(12)
        if len(header)!=12 or struct.unpack('<III',header)!=(0x46546c67,2,size):return None
        digest=hashlib.sha256(header)
        for block in iter(lambda:stream.read(1024**2),b''):digest.update(block)
    return size,digest.hexdigest()


def save_ready(folder,report,phase):
    folder=Path(folder)
    identity=model_digest(folder)
    if identity is None:raise ValueError('Nieprawidlowy glowny eksport GLB.')
    value={'revision':1,'bytes':identity[0],'sha256':identity[1],'phase':phase,'result':report}
    pending=folder/(NAME+'.tmp')
    pending.write_text(json.dumps(value),encoding='utf-8')
    pending.replace(folder/NAME)


def recover_ready(folder):
    folder=Path(folder);path=folder/NAME
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size>2*1024**2:return None
        value=json.loads(path.read_text())
        identity=model_digest(folder)
        if value.get('revision')!=1 or identity is None or identity!=(value.get('bytes'),value.get('sha256')):return None
        report=value['result']
        if not isinstance(report,dict) or report.get('triangles',0)<1:return None
        if value.get('phase') not in ('core_export','interchange_exports'):return None
        report['timeout_recovery']={'phase':value['phase'],'model_sha256':identity[1],
                                  'likeness_verified':False,'review_complete':False}
        report['review_render']={'status':'interrupted_by_timeout'}
        pending=folder/'result.json.tmp'
        pending.write_text(json.dumps(report),encoding='utf-8');pending.replace(folder/'result.json')
        return report
    except (OSError,ValueError,KeyError,TypeError):
        return None
