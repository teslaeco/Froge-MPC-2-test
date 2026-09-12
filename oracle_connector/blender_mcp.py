"""Job-scoped stdio MCP for Codex. Model code runs only in the Blender sandbox."""
import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import threading
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
from code_policy import prepare_code
from runtime.scene_contract import PROMPT, parse_scene
from scene_repair import photo_schema
from photo_input import read_photos, validate_photo_plan

VIEWS = ('front', 'three-quarter', 'face', 'side', 'back')
ASSETS = ('model.glb', 'model.blend', 'scene.json', 'model.froge-scene.json',
          'model.fbx', 'model.obj', 'model.mtl', 'model-mm.stl', 'result.json',
          'textures', 'review', 'edits.py', 'model-ready.json')


def write(path, value):
    pending = path.with_name(path.name + '.pending')
    pending.write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')
    os.chmod(pending, 0o600); pending.replace(path)


def schema(properties):
    return {'type':'object','properties':properties,'required':list(properties),'additionalProperties':False}


TOOLS = [
    {'name':'get_modeling_contract','description':'Read supported scene operations, coordinate conventions, limits and current job. Call once before modeling.', 'inputSchema':schema({})},
    {'name':'build_model','description':'Build a complete scene JSON in real Blender and produce GLB plus preview renders. Replaces the candidate, preserving earlier attempts. At most three successful or failed builds per job.',
     'inputSchema':schema({'scene_json':{'type':'string','maxLength':256000},'expected_revision':{'type':'integer','minimum':0}})},
    {'name':'edit_model','description':'Apply a short Python geometry/material edit to the current scene using bpy and existing helpers. Edits accumulate. No file/network access. Runs in isolated Blender and generates new renders. Use actual object names from get_current_model.',
     'inputSchema':schema({'code':{'type':'string','maxLength':20000},'expected_revision':{'type':'integer','minimum':1}})},
    {'name':'get_current_model','description':'Read current revision, full scene, edit history, geometry/material report and mesh object names. Does not generate or buy another model.', 'inputSchema':schema({})},
    {'name':'inspect_render','description':'Return a real image rendered from the CURRENT exported GLB. Inspect front, side, back and face for a portrait before finalizing.',
     'inputSchema':schema({'view':{'type':'string','enum':list(VIEWS)},'expected_revision':{'type':'integer','minimum':1}})},
    {'name':'finish_model','description':'Record visual verdict for the inspected current revision and prepare downloadable formats. Report unresolved faults honestly; accepted=false preserves a draft. Does not publish to the shop.',
     'inputSchema':schema({'expected_revision':{'type':'integer','minimum':1},'accepted':{'type':'boolean'},'issues':{'type':'array','items':{'type':'string','maxLength':400},'maxItems':12},'summary':{'type':'string','maxLength':1200}})},
]


class JobTools:
    def __init__(self, folder, build=None, finalize=None):
        self.folder = Path(folder)
        self.request = json.loads((self.folder/'agent-request.json').read_text())
        self.photos = read_photos(self.folder)
        self.revision = 0; self.attempts = 0; self.current = None; self.seen = set()
        self.build_callback = build; self.finalize_callback = finalize
        self.started = time.monotonic(); self.blender_seconds = 0.; self.finished = False

    def check(self, revision=None):
        if (self.folder/'agent-cancelled').exists(): raise InterruptedError('Zlecenie anulowane.')
        if time.monotonic()-self.started > 840: raise TimeoutError('Wykorzystano czas zlecenia Codexa.')
        if revision is not None and revision != self.revision: raise ValueError('CONFLICT: odczytaj aktualna rewizje modelu.')

    def progress(self, detail):
        write(self.folder/'agent-progress.json', {'detail':detail,'revision':self.revision,'blender_seconds':round(self.blender_seconds,2)})

    def snapshot(self):
        if self.current is None: return {'revision':0,'has_model':False,'builds_remaining':3-self.attempts}
        report = json.loads((self.current/'result.json').read_text())
        return {'revision':self.revision,'has_model':True,'builds_remaining':3-self.attempts,
                'scene':json.loads((self.current/'scene.json').read_text()),
                'edits':(self.current/'edits.py').read_text() if (self.current/'edits.py').exists() else '',
                'report':report,'inspected_views':sorted(self.seen)}

    def build(self, scene, edits=''):
        self.check()
        if self.attempts >= 3: raise ValueError('Wykorzystano trzy proby budowy. Zachowaj najlepszy istniejacy model i opisz wady.')
        validate_photo_plan(scene, self.photos)
        self.attempts += 1
        candidate = self.folder/'candidates'/str(self.attempts)
        candidate.mkdir(parents=True, mode=0o700)
        write(candidate/'scene.json',scene)
        if edits: (candidate/'edits.py').write_text(edits,encoding='utf-8')
        for name in ['reference-photos.json'] + ['reference-%d.jpg'%i for i in range(len(self.photos))]:
            path=self.folder/name
            if path.is_file(): shutil.copy2(path,candidate/name)
        write(candidate/'review-request.json',{'enabled':True,'preview_only':True})
        self.progress('Codex przekazal model do Blendera. Budowa i rendery proby %d/3.'%self.attempts)
        started=time.monotonic()
        try:
            if self.build_callback: self.build_callback(candidate)
            else:
                import server
                event = threading.Event()
                # Parent terminates the process group on cancellation. No user
                # API key or worker state is mounted in this Blender container.
                server.run_blender(self.folder.name,candidate,event,timeout=min(420,840-(time.monotonic()-self.started)))
        finally:
            self.blender_seconds+=time.monotonic()-started
            self.progress('Blender zakonczyl probe. Codex sprawdza geometrie i rendery.')
        if not (candidate/'result.json').is_file() or not (candidate/'model.glb').is_file():
            raise ValueError('Brak poprawnego eksportu; poprzedni model pozostaje zachowany.')
        self.current=candidate; self.revision+=1; self.seen=set()
        write(self.folder/'agent-candidate.json',{'path':str(candidate.relative_to(self.folder)),'revision':self.revision,'blender_seconds':self.blender_seconds})
        return self.snapshot()

    def call(self, name, arguments):
        self.check(arguments.get('expected_revision'))
        if self.finished: raise ValueError('To zlecenie jest zakonczone.')
        if name=='get_modeling_contract':
            return {'job_id':self.folder.name,'prompt':self.request['prompt'],
                    'instructions':self.request['instructions'],'scene_schema':photo_schema(len(self.photos)),
                    'coordinate_and_geometry_guide':PROMPT,
                    'edit_helpers':'bpy, math, random, Vector, make_material(name,rgb,pattern,roughness,metallic), mesh_object(name,vertices,faces,material), tube(name,points,radii,material,sides), ellipsoid(name,center,radii,material), join_meshes(objects,name). No imports except bpy/math/random/mathutils. No files, shell or network.',
                    'references':[{'index':i,'view':p.get('view'),'name':p.get('name')} for i,p in enumerate(self.photos)],'revision':self.revision}
        if name=='get_current_model': return self.snapshot()
        if name=='build_model':
            return self.build(parse_scene(arguments['scene_json'],self.request['prompt']))
        if name=='edit_model':
            if self.current is None: raise ValueError('Najpierw zbuduj scene z poprawna anatomia.')
            code,_=prepare_code(arguments['code'])
            previous=(self.current/'edits.py').read_text() if (self.current/'edits.py').is_file() else ''
            combined=previous+'\n'+code
            prepare_code(combined)
            return self.build(json.loads((self.current/'scene.json').read_text()),combined)
        if name=='inspect_render':
            if self.current is None: raise ValueError('Nie ma aktualnego modelu.')
            view=arguments['view']
            if view not in VIEWS: raise ValueError('Nieprawidlowy widok.')
            path=self.current/'review'/(view+'.png')
            if not path.is_file() or not 24<=path.stat().st_size<=2*1024**2: raise ValueError('Ten render nie zostal ukonczony.')
            self.seen.add(view)
            return [{'type':'text','text':'Rzeczywisty GLB; rewizja %d; widok %s.'%(self.revision,view)},
                    {'type':'image','mimeType':'image/png','data':base64.b64encode(path.read_bytes()).decode()}]
        if name=='finish_model':
            if self.current is None: raise ValueError('Brak modelu. Sam opis nie jest wykonaniem.')
            scene=json.loads((self.current/'scene.json').read_text())
            required={'front','side','back'} | ({'face'} if scene['subject_type'] in ('person','portrait') else set())
            reviewed=required<=self.seen
            accepted=arguments['accepted'] is True and reviewed and not arguments['issues']
            if arguments['accepted'] and not accepted:
                raise ValueError('Akceptacja wymaga obejrzenia aktualnych renderow i braku nierozwiazanych bledow. W przeciwnym razie zachowaj szkic: accepted=false.')
            self.progress('Codex zakonczyl ocene. Blender przygotowuje formaty do pobrania.')
            started=time.monotonic()
            try:
                if self.finalize_callback: self.finalize_callback(self.current)
                else:
                    import server
                    server.run_blender_finalize(self.folder.name,self.current,threading.Event(),timeout=300)
            finally:self.blender_seconds+=time.monotonic()-started
            retain_candidate(self.folder,self.current)
            report={'revision':3,'status':'reviewed' if accepted else 'needs_revision',
                    'assessment_completed':reviewed,'accepted':accepted,'issues':arguments['issues'],
                    'summary':arguments['summary'],'model_revision':self.revision,'inspected_views':sorted(self.seen),
                    'executor':'codex-mcp','likeness_verified':False}
            write(self.folder/'visual-review.json',report)
            write(self.folder/'agent-outcome.json',{'finished':True,'revision':self.revision,'accepted':accepted,'blender_seconds':self.blender_seconds,'builds':self.attempts})
            self.finished=True
            return report
        raise ValueError('Nieznane narzedzie MCP.')


def retain_candidate(folder,candidate):
    # Only renderer artifacts; never overwrite job identity or instructions.
    for name in ASSETS:
        source=candidate/name
        if source.is_symlink():raise ValueError('Nieprawidlowy plik wyniku.')
        if not source.exists():continue
        destination=folder/name
        if source.is_dir():shutil.copytree(source,destination,dirs_exist_ok=True)
        else:shutil.copy2(source,destination)


def serve(job, incoming=sys.stdin, outgoing=sys.stdout):
    for raw in incoming:
        if len(raw)>600000:break
        try:
            request=json.loads(raw);method=request.get('method');rid=request.get('id')
            if rid is None:continue
            if method=='initialize':
                result={'protocolVersion':'2025-03-26','capabilities':{'tools':{}},'serverInfo':{'name':'forge-blender','version':'27'}}
            elif method=='ping':result={}
            elif method=='tools/list':result={'tools':TOOLS}
            elif method=='tools/call':
                params=request.get('params',{});name=params.get('name');arguments=params.get('arguments',{})
                tool=next((t for t in TOOLS if t['name']==name),None)
                if tool is None:raise ValueError('Nieznane narzedzie MCP.')
                from runtime.scene_contract import check
                check(arguments,tool['inputSchema'])
                try:
                    value=job.call(name,arguments)
                    content=value if isinstance(value,list) else [{'type':'text','text':json.dumps(value,ensure_ascii=False)}]
                    result={'content':content,'isError':False}
                except (ValueError,RuntimeError,OSError,TimeoutError) as error:
                    result={'content':[{'type':'text','text':str(error)[-1800:]}],'isError':True}
            else:
                outgoing.write(json.dumps({'jsonrpc':'2.0','id':rid,'error':{'code':-32601,'message':'Method not found'}})+'\n');outgoing.flush();continue
            outgoing.write(json.dumps({'jsonrpc':'2.0','id':rid,'result':result})+'\n');outgoing.flush()
        except (ValueError,TypeError,KeyError):
            outgoing.write(json.dumps({'jsonrpc':'2.0','id':None,'error':{'code':-32600,'message':'Invalid request'}})+'\n');outgoing.flush()


if __name__=='__main__':
    # Strip credentials only in the MCP process, never as an import side effect.
    for key in ('CODEX_API_KEY', 'OPENAI_API_KEY', 'FORGE_CODEX_RUN_TOKEN'):
        os.environ.pop(key, None)
    root=Path(__file__).resolve().parent/'state'/'jobs'
    folder=Path(sys.argv[1]).resolve()
    import re
    if folder.parent!=root.resolve() or not re.fullmatch(r'[a-f0-9-]{36}',folder.name) or folder.is_symlink():
        raise SystemExit('Invalid job directory')
    serve(JobTools(folder))
