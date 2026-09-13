"""FORGE World owner-only bridge. Reuses the installed Oracle worker on loopback.

No public anonymous generation, no OpenAI key in the browser, no auto-install.
Run on Oracle with --worker-root and --origin. Session token expires in one hour.
"""
import argparse
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import sqlite3
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

IDS = {'076cb6e8-c3de-4a59-a7b9-c0dfeb2d0e0d', '99397623-e45c-48dc-95ec-6f84446a54d5'}
UUID = re.compile(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$')
SAFE_FILES = {'model.glb','model.blend','model-master.glb','model-mm.stl','model.fbx','model.obj','model.mtl','scene.json','model.froge-scene.json','result.json','visual-review.json','model-ready.json','agent-outcome.json','agent-instructions.json','reference-photos.json'}
TERMINAL = {'succeeded','failed','cancelled'}
LOCK = threading.RLock()

def plain(path, root):
    path = Path(path)
    if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('Nieprawidłowa ścieżka pliku.')
    for parent in path.parents:
        if parent == root.parent: break
        if parent.is_symlink(): raise ValueError('Dowiązanie zamiast pliku.')
    return path

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
    return h.hexdigest()

def validate_job(data):
    if not isinstance(data,dict) or not UUID.fullmatch(str(data.get('id',''))): raise ValueError('Nieprawidłowy identyfikator.')
    p=data.get('prompt'); instructions=data.get('agentInstructions','')
    if not isinstance(p,str) or not 1<=len(p.encode('utf-16-le'))//2<=5000: raise ValueError('Opis: 1–5000 znaków.')
    if not isinstance(instructions,str) or not 1<=len(instructions.encode('utf-16-le'))//2<=9999: raise ValueError('Całe polecenie: maks. 9999 znaków.')
    photos=data.get('photos',[])
    if not isinstance(photos,list) or len(photos)>4: raise ValueError('Maks. 4 zdjęcia.')
    return {key:data[key] for key in ('id','prompt','agentInstructions','photos') if key in data}

class Bridge:
    def __init__(self,root,origin,state):
        self.root=Path(root).resolve();self.origin=origin;self.state=Path(state).resolve()
        self.state.mkdir(mode=0o700,parents=True,exist_ok=True)
        self.token=secrets.token_urlsafe(32);self.expires=time.time()+3600
        with self.db() as db: db.execute('CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, request TEXT, status TEXT, detail TEXT, created REAL)')
    def db(self):
        db=sqlite3.connect(self.state/'queue.sqlite',timeout=15);db.row_factory=sqlite3.Row;return db
    def upstream(self,path,data=None):
        # Destination is fixed loopback; caller cannot supply a URL.
        config=json.loads(plain(self.root/'state/config.json',self.root).read_text())
        req=urllib.request.Request('http://127.0.0.1:8765'+path,data=json.dumps(data).encode() if data is not None else None,headers={'Authorization':'Bearer '+config['token'],'Content-Type':'application/json'})
        with urllib.request.urlopen(req,timeout=25) as r: return json.load(r)
    def exists(self,id):
        with self.db() as db:return id in IDS or db.execute('SELECT 1 FROM jobs WHERE id=?',(id,)).fetchone() is not None
    def enqueue(self,data):
        payload=validate_job(data)
        if payload['id'] in IDS: raise ValueError('Identyfikator chronionego modelu. Użyj nowego zlecenia.')
        encoded=json.dumps(payload,sort_keys=True,ensure_ascii=False)
        with LOCK,self.db() as db:
            previous=db.execute('SELECT * FROM jobs WHERE id=?',(data['id'],)).fetchone()
            if previous:
                if previous['request']!=encoded: raise ValueError('To ID ma już inne zlecenie.')
                return {'id':data['id'],'state':previous['status']}
            if db.execute("SELECT COUNT(*) FROM jobs WHERE status NOT IN ('succeeded','failed','cancelled')").fetchone()[0]>=50: raise ValueError('Kolejka ma już 50 modeli.')
            db.execute('INSERT INTO jobs VALUES (?,?,?,?,?)',(data['id'],encoded,'queued','Czeka na wolny Blender.',time.time()))
        return {'id':data['id'],'state':'queued'}
    def archive(self,id):
        if not UUID.fullmatch(id) or not self.exists(id): raise ValueError('Brak dostępu do tego modelu.')
        source=self.root/'state/jobs'/id
        status=self.upstream('/v1/jobs/'+id)
        if status.get('state')!='succeeded': raise ValueError('Model nie jest ukończony.')
        glb=plain(source/'model.glb',self.root);sha=digest(glb)
        dest=self.state/'archive'/id/sha
        if (dest/'MANIFEST.json').exists():
            if digest(plain(dest/'model.glb',self.state))!=sha:raise ValueError('Archiwum ma niezgodny SHA-256.')
            return dest/'model.glb'
        files=[]
        for f in source.rglob('*'):
            if not f.is_file():continue
            rel=f.relative_to(source)
            if len(rel.parts)==1 and (f.name in SAFE_FILES or re.fullmatch(r'reference-\d\.jpg',f.name)):
                files.append(plain(f,self.root))
            elif len(rel.parts)==2 and rel.parts[0] in {'textures','provider-textures'} and re.fullmatch(r'[A-Za-z0-9_.-]+\.(png|jpg|webp)',f.name):files.append(plain(f,self.root))
        total=sum(f.stat().st_size for f in files)
        if shutil.disk_usage(self.state).free<total+512*1024**2:raise ValueError('Za mało miejsca na pełne archiwum. Oryginały zachowano.')
        tmp=dest.with_name(sha+'.partial-'+secrets.token_hex(4));tmp.mkdir(parents=True,mode=0o700)
        records=[]
        try:
            for f in files:
                relative=f.relative_to(source);out=tmp/relative;out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,out);os.chmod(out,0o600)
                actual=digest(out)
                if actual!=digest(f):raise ValueError('Plik zmienił się podczas kopiowania.')
                records.append({'path':str(relative),'bytes':out.stat().st_size,'sha256':actual})
            if digest(tmp/'model.glb')!=sha:raise ValueError('Model zmienił się podczas kopiowania.')
            (tmp/'MANIFEST.json').write_text(json.dumps({'jobId':id,'modelSha256':sha,'review':'unreviewed','created':time.time(),'files':records},indent=2))
            try:tmp.rename(dest)
            except FileExistsError:
                if not (dest/'MANIFEST.json').exists():raise
                shutil.rmtree(tmp)
            return dest/'model.glb'
        except Exception:
            # Remove only this bridge's incomplete new copy; never a source job.
            if tmp.exists():shutil.rmtree(tmp)
            raise
    def status(self,id):
        if not self.exists(id):raise ValueError('Nie znaleziono zlecenia.')
        with self.db() as db:r=db.execute('SELECT * FROM jobs WHERE id=?',(id,)).fetchone()
        if r and r['status'] in {'queued','failed','cancelled'}:return {'id':id,'state':r['status'],'detail':r['detail'],'progress':None}
        j=self.upstream('/v1/jobs/'+id)
        if j.get('state')=='succeeded':
            try:self.archive(id)
            except (ValueError,OSError) as e:return {'id':id,'state':'archiving','detail':'Model gotowy; archiwum wymaga uwagi: '+str(e),'progress':None}
        return {key:j[key] for key in ('id','state','detail','modelStatus') if key in j}|{'progress':100 if j.get('state')=='succeeded' else None}
    def run(self):
        while True:
            try:
                with self.db() as db:running=db.execute("SELECT * FROM jobs WHERE status='submitted' ORDER BY created LIMIT 1").fetchone()
                if running:
                    j=self.upstream('/v1/jobs/'+running['id'])
                    if j.get('state') in TERMINAL:
                        if j['state']=='succeeded':self.archive(running['id'])
                        with self.db() as db:db.execute('UPDATE jobs SET status=?,detail=? WHERE id=?',(j['state'],j.get('detail',''),running['id']))
                else:
                    with self.db() as db:queued=db.execute("SELECT * FROM jobs WHERE status='queued' ORDER BY created LIMIT 1").fetchone()
                    if queued:
                        try:
                            self.upstream('/v1/jobs',json.loads(queued['request']))
                            with self.db() as db:db.execute("UPDATE jobs SET status='submitted' WHERE id=?",(queued['id'],))
                        except urllib.error.HTTPError as e:
                            if e.code!=409:
                                with self.db() as db:db.execute("UPDATE jobs SET status='failed',detail=? WHERE id=?",('Oracle odrzucił zlecenie: HTTP '+str(e.code),queued['id']))
            except Exception:
                # Preserve durable queue after transient network/disk failures.
                pass
            time.sleep(3)

def handler(bridge):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def send_headers(self,status,typ='application/json',length=None):
            self.send_response(status);self.send_header('Content-Type',typ);self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff')
            if self.headers.get('Origin')==bridge.origin:self.send_header('Access-Control-Allow-Origin',bridge.origin);self.send_header('Vary','Origin')
            if length is not None:self.send_header('Content-Length',str(length))
            self.end_headers()
        def send(self,data,status=200):
            blob=json.dumps(data,ensure_ascii=False).encode();self.send_headers(status,length=len(blob));self.wfile.write(blob)
        def do_OPTIONS(self):
            if self.headers.get('Origin')!=bridge.origin:return self.send({'error':'Origin rejected'},403)
            self.send_response(204);self.send_header('Access-Control-Allow-Origin',bridge.origin);self.send_header('Access-Control-Allow-Methods','GET, POST, OPTIONS');self.send_header('Access-Control-Allow-Headers','Authorization, Content-Type');self.send_header('Vary','Origin');self.end_headers()
        def do_GET(self):self.handle_api(False)
        def do_POST(self):self.handle_api(True)
        def handle_api(self,write):
            if self.headers.get('Origin') not in (None,bridge.origin):return self.send({'error':'Origin rejected'},403)
            if time.time()>bridge.expires or not hmac.compare_digest(self.headers.get('Authorization',''),'Bearer '+bridge.token):return self.send({'error':'Token sesji jest nieważny lub wygasł.'},401)
            try:
                if self.path=='/api/health' and not write:
                    h=bridge.upstream('/v1/health');return self.send({k:h.get(k) for k in ('ready','connectorVersion','model','executionEngine','detail')})
                if self.path=='/api/jobs' and write:
                    size=int(self.headers.get('Content-Length','0'))
                    if not 1<=size<=9*1024*1024 or self.headers.get('Content-Type')!='application/json':raise ValueError('Nieprawidłowe żądanie.')
                    self.connection.settimeout(15);return self.send(bridge.enqueue(json.loads(self.rfile.read(size))),202)
                m=re.fullmatch(r'/api/(jobs|archive)/([a-f0-9-]{36})(?:/(model))?',self.path)
                if not m or not UUID.fullmatch(m[2]) or not bridge.exists(m[2]) or write:return self.send({'error':'Nie znaleziono.'},404)
                if m[1]=='archive' or m[3]=='model':
                    path=bridge.archive(m[2]);size=path.stat().st_size
                    if size>100*1024*1024:return self.send({'error':'GLB przekracza limit podglądu 100 MB. Pełne archiwum pozostaje na serwerze.'},413)
                    self.send_headers(200,'model/gltf-binary',size)
                    with path.open('rb') as f:shutil.copyfileobj(f,self.wfile)
                else:self.send(bridge.status(m[2]))
            except urllib.error.HTTPError as e:self.send({'error':'Oracle: HTTP '+str(e.code)},502)
            except (ValueError,TypeError,KeyError,OSError) as e:self.send({'error':str(e)},400)
    return Handler

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--worker-root',type=Path,default=Path.home()/'froge-connector');p.add_argument('--state',type=Path,default=Path.home()/'forge-world-state');p.add_argument('--origin',required=True);p.add_argument('--port',type=int,default=8866);args=p.parse_args()
    if not re.fullmatch(r'https://[a-zA-Z0-9.-]+(?::\d+)?',args.origin):p.error('--origin wymaga dokładnego origin HTTPS bez ścieżki.')
    os.umask(0o077);bridge=Bridge(args.worker_root,args.origin,args.state)
    bridge.upstream('/v1/health')
    for id in sorted(IDS):
        try:bridge.archive(id);print('Archiwum gotowe:',id,flush=True)
        except Exception as e:print('Archiwum oczekuje:',id,str(e),flush=True)
    print('Token sesji (ważny 1 godzinę, nie zapisuj w Git):',bridge.token,flush=True)
    print('Most nasłuchuje lokalnie na porcie',args.port,flush=True)
    threading.Thread(target=bridge.run,daemon=True).start();ThreadingHTTPServer(('127.0.0.1',args.port),handler(bridge)).serve_forever()
