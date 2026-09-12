"""One explicitly requested real Astra trial through the installed worker queue.

Reuses original saved references. A durable ID prevents duplicate purchases if
the Cloud Shell connection is interrupted and the command is repeated.
"""
import argparse
import base64
import json
from pathlib import Path
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.request
import uuid
from blender_mcp import write
from codex_runner import safe_message, NoRedirect
from photo_input import read_photos

ROOT=Path(__file__).resolve().parent
UUID=re.compile(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$')


def prepare(root,source_id):
    if not UUID.fullmatch(source_id):raise ValueError('Nieprawidlowy identyfikator zlecenia do proby.')
    state=root/'state';source=state/'jobs'/source_id
    if source.is_symlink() or not source.is_dir():raise ValueError('Brak zapisanego zlecenia zrodlowego.')
    with sqlite3.connect('file:'+str(state/'jobs.sqlite')+'?mode=ro',uri=True) as db:
        row=db.execute('SELECT prompt,state FROM jobs WHERE id=?',(source_id,)).fetchone()
    if not row or row[1] not in ('succeeded','failed','cancelled'):
        raise ValueError('Zlecenie zrodlowe nie istnieje lub nadal pracuje.')
    receipt=source/'v30-paid-trial.json'
    if receipt.exists():
        saved=json.loads(receipt.read_text());job_id=saved['id']
        if not UUID.fullmatch(job_id):raise ValueError('Nieprawidlowy zapis proby.')
    else:
        job_id=str(uuid.uuid4())
        # Exclusive creation protects against two simultaneous invocations.
        try:
            with receipt.open('x') as out:json.dump({'id':job_id,'source_id':source_id},out)
            receipt.chmod(0o600)
        except FileExistsError:
            job_id=json.loads(receipt.read_text())['id']
            if not UUID.fullmatch(job_id):raise ValueError('Nieprawidlowy zapis proby.')
    path=source/'agent-instructions.json'
    instructions=json.loads(path.read_text()).get('text','') if path.is_file() else ''
    photos=read_photos(source)
    return {'id':job_id,'prompt':row[0],'agentInstructions':instructions,
            'photos':[{**{k:p[k] for k in ('name','view','subject','faceLandmarks','textureMaxSize') if k in p},
                       'dataUrl':'data:image/jpeg;base64,'+base64.b64encode(p['bytes']).decode()} for p in photos]}


def run(source_id, root=ROOT, progress=print):
    payload=prepare(root,source_id)
    token=json.loads((root/'state/config.json').read_text())['token']
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
    def request(path,body=None):
        req=urllib.request.Request('http://127.0.0.1:8765/v1/'+path,
              data=json.dumps(body).encode() if body is not None else None,
              headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'})
        with opener.open(req,timeout=30) as response:return json.loads(response.read(2*1024**2))
    health=request('health')
    if health.get('connectorVersion')!=30 or health.get('executionEngine')!='codex-mcp' or not health.get('ready'):
        raise RuntimeError('Proba wymaga gotowej Astry i zweryfikowanego Codex/MCP v30. Nie wyslano zlecenia.')
    jid=payload['id']
    progress('FROGE_PAID_TRIAL_ID: '+jid,flush=True)
    try:state=request('jobs/'+jid)
    except urllib.error.HTTPError as error:
        if error.code!=404:raise
        error.close()
        # Exactly one submission. On ambiguous failure the durable ID is kept;
        # a repeated command first queries it, never creates a second ID.
        progress('Uruchamiam jedna platna probe: Astra high, Codex i Blender MCP; zapisane oryginalne zdjecia.',flush=True)
        state=request('jobs',payload)
    started=time.monotonic()
    while state.get('state') not in ('succeeded','failed','cancelled'):
        if time.monotonic()-started>2100:
            raise RuntimeError('Proba nadal pracuje lub brak koncowego statusu. Powtorz to samo polecenie, aby odczytac ten sam identyfikator.')
        detail=safe_message(str(state.get('detail','Zlecenie przyjete.')),(token,))
        progress('FROGE_PAID_TRIAL: '+str(state.get('state'))+' — '+detail,flush=True)
        time.sleep(15)
        state=request('jobs/'+jid)
    report=request('jobs/'+jid+'/quality')
    write(root/'state/jobs'/jid/'paid-trial-report.json',report)
    progress('FROGE_PAID_TRIAL_REPORT: '+json.dumps(report,ensure_ascii=True),flush=True)
    progress('Pliki proby: '+str(root/'state/jobs'/jid),flush=True)
    if state.get('state')!='succeeded' or report.get('hasModel') is not True:
        raise RuntimeError('FROGE_PAID_TRIAL_FAILED: '+safe_message(str(state.get('detail')),(token,)))
    progress('FROGE_PAID_TRIAL_MODEL_CREATED: rzeczywisty model zapisany. Ocen wyglad i porownaj go z referencja; sam eksport nie potwierdza podobienstwa.',flush=True)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--source-job',required=True)
    args=parser.parse_args()
    try:run(args.source_job)
    except Exception as error:
        print(safe_message(str(error)),file=sys.stderr)
        raise SystemExit(1)
