"""Job-scoped stdio MCP for Codex. Model code runs only in the Blender sandbox."""
import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import re
import secrets
import sys
import threading
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
from code_policy import prepare_code
from agent_limits import MAX_BUILDS, BUILD_DEADLINE
from runtime.scene_contract import PROMPT, parse_scene
from scene_repair import photo_schema
from photo_input import read_photos, validate_photo_plan
from runtime.model_checkpoint import model_digest

VIEWS = ('front', 'three-quarter', 'face', 'side', 'back')
ASSETS = ('model.glb', 'model.blend', 'scene.json', 'model.froge-scene.json',
          'model.fbx', 'model.obj', 'model.mtl', 'model-mm.stl', 'result.json',
          'textures', 'review', 'edits.py', 'model-ready.json')

# Count the actual nested JSON returned by MCP, including escaped Unicode and
# quotes. Keep even adversarial names/history below the CodeMode tool budget.
SNAPSHOT_MAX_BYTES = 12000
SNAPSHOT_PAGE_CHARS = 8000
SNAPSHOT_SECTIONS = ('scene', 'edits', 'report', 'visual_review')


def snapshot_wire_size(value):
    content = [{'type': 'text', 'text': json.dumps(value, ensure_ascii=False)}]
    return len(json.dumps({'content': content, 'isError': False}).encode('utf-8'))


def section_info(text, section):
    raw = text.encode('utf-8')
    return {'format': 'python' if section == 'edits' else 'json',
            'characters': len(text), 'bytes': len(raw),
            'sha256': hashlib.sha256(raw).hexdigest(), 'inline': False}


class AnatomyBuildError(ValueError):
    """A failed candidate's structural details, suitable for one repair call."""


def anatomy_build_error(candidate, original):
    try:
        data = read_record(candidate/'anatomy-failure.json', 256*1024)
        if data.get('structural_checks_passed') is not False:
            return original
        roles = ('heads','eyes','hands','nails')
        detail = {'code':'ANATOMY_VALIDATION','structural_checks_passed':False}
        for name in ('expected','actual','missing','excess'):
            counts = data.get(name)
            if not isinstance(counts, dict) or any(type(counts.get(role)) is not int or
                    not 0 <= counts[role] <= 100000 for role in roles):
                return original
            detail[name] = {role:counts[role] for role in roles}
        detail['repair_hint'] = str(data.get('repair_hint',''))[:320]
        detail['objects'] = {}; detail['removed_or_untagged'] = {}
        detail['violations'] = []; detail['omitted'] = {'objects':{},'removed_or_untagged':{},'violations':0}
        # The fixed counts lead every error. Names and violations are optional
        # and bounded by their serialized size, including Unicode escaping.
        for group in ('removed_or_untagged','objects'):
            values = data.get(group, {})
            if not isinstance(values, dict): continue
            for role in roles:
                names = values.get(role, [])
                if not isinstance(names, list): continue
                detail[group][role] = []; detail['omitted'][group][role] = len(names)
                for name in names[:8]:
                    if not isinstance(name, str): continue
                    detail[group][role].append(name[:80])
                    detail['omitted'][group][role] -= 1
                    if snapshot_wire_size(detail) > 6000:
                        detail[group][role].pop(); detail['omitted'][group][role] += 1
                        break
        violations = data.get('violations', [])
        if isinstance(violations, list):
            detail['omitted']['violations'] = len(violations)
            for entry in violations[:16]:
                if not isinstance(entry, dict): continue
                item = {key:value[:160] if isinstance(value, str) else value
                        for key,value in entry.items()
                        if key in ('code','component','object','expected','actual','vertices','minimum_vertices','has_uv','message')
                        and (isinstance(value, str) or type(value) in (bool,int,float))}
                detail['violations'].append(item); detail['omitted']['violations'] -= 1
                if snapshot_wire_size(detail) > 6000:
                    detail['violations'].pop(); detail['omitted']['violations'] += 1
                    break
        return AnatomyBuildError('ANATOMY_VALIDATION: '+json.dumps(detail, ensure_ascii=False))
    except (OSError, ValueError, TypeError, AttributeError):
        return original


def write(path, value):
    pending = path.with_name(path.name + '.pending')
    pending.write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')
    os.chmod(pending, 0o600); pending.replace(path)


def schema(properties, required=None):
    return {'type':'object','properties':properties,'required':list(properties) if required is None else required,'additionalProperties':False}


def check_tool_arguments(arguments, tool_schema):
    # Scene records intentionally require an exact field set. MCP tools also
    # have optional pagination arguments, so validate the tool envelope here.
    if (not isinstance(arguments, dict) or not set(tool_schema['required']) <= set(arguments) or
            not set(arguments) <= set(tool_schema['properties'])):
        raise ValueError('Nieprawidlowe argumenty MCP; wymagane pola: '+', '.join(tool_schema['required']))
    from runtime.scene_contract import check
    for name, value in arguments.items():
        check(value, tool_schema['properties'][name], name)


TOOLS = [
    {'name':'get_modeling_contract','description':'Read supported scene operations, coordinate conventions, limits and current job. Call once before modeling.', 'inputSchema':schema({})},
    {'name':'build_model','description':'Build a complete scene JSON in real Blender and produce GLB plus preview renders. Replaces the candidate, preserving earlier attempts. At most five successful or failed builds per job.',
     'inputSchema':schema({'scene_json':{'type':'string','maxLength':256000},'expected_revision':{'type':'integer','minimum':0}})},
    {'name':'edit_model','description':'Apply a short Python geometry/material edit to the current scene using bpy and existing helpers. Edits accumulate. No file/network access. Runs in isolated Blender and generates new renders. Use actual object names from get_current_model.',
     'inputSchema':schema({'code':{'type':'string','maxLength':20000},'expected_revision':{'type':'integer','minimum':1}})},
    {'name':'get_current_model','description':'Read a bounded current-model snapshot. Small scene/edit/report sections are inline; an oversized section is null with its SHA256 and length in sections. Read it using section, offset and expected_revision; concatenate page.text using next_offset until null. Offsets count Unicode code points, not bytes or JavaScript UTF-16 units. Pass the section SHA256 as expected_sha256 to prevent mixing changed pages. JSON.parse the concatenated scene/report text in CodeMode and store it; print only needed summaries or object names. Does not generate or buy another model.',
     'inputSchema':schema({'section':{'type':'string','enum':['summary']+list(SNAPSHOT_SECTIONS)},
                          'offset':{'type':'integer','minimum':0},
                          'limit':{'type':'integer','minimum':1,'maximum':16000},
                          'expected_revision':{'type':'integer','minimum':0},
                          'expected_sha256':{'type':'string','pattern':'^[0-9a-f]{64}$'}}, required=[])},
    {'name':'inspect_render','description':'Return a real image rendered from the CURRENT exported GLB. Inspect front, side, back and face for a portrait before finalizing.',
     'inputSchema':schema({'view':{'type':'string','enum':list(VIEWS)},'expected_revision':{'type':'integer','minimum':1}})},
    {'name':'finish_model','description':'Record visual verdict for the inspected current revision and prepare downloadable formats. Report unresolved faults honestly; accepted=false preserves a draft. Does not publish to the shop.',
     'inputSchema':schema({'expected_revision':{'type':'integer','minimum':1},'accepted':{'type':'boolean'},'issues':{'type':'array','items':{'type':'string','maxLength':400},'minItems':0,'maxItems':12},'summary':{'type':'string','maxLength':1200}})},
]


def tool_error(error):
    value = str(error)
    value = re.sub(r'(?i)Bearer\s+\S+|\bsk-[A-Za-z0-9_-]+', '[redacted]', value)
    value = re.sub(r'data:image/[^\s]+', '[image omitted]', value)
    if isinstance(error, AnatomyBuildError): return value
    # Blender adds a traceback and export/log lines. Put the actual exception
    # first, so the job card's short preview does not hide it behind stack frames.
    causes = [line.strip() for line in value.splitlines() if re.match(
        r'^\s*(?:[\w.]+\.)?[A-Za-z_][\w]*(?:Error|Exception):', line)]
    if causes:return causes[-1][:1400]
    if isinstance(error, (KeyError, TypeError, AttributeError, SyntaxError)):
        value = type(error).__name__+': '+value
    return value[-1800:]


def read_record(path, limit=2*1024**2):
    if path.is_symlink() or not path.is_file() or path.stat().st_size > limit:
        raise ValueError('Nieprawidlowy zapis wyniku.')
    value=json.loads(path.read_text())
    if not isinstance(value,dict):raise ValueError('Nieprawidlowy zapis wyniku.')
    return value


def current_candidate(folder, execution_id=None):
    """Return only the current run's complete, renderer-checked GLB candidate."""
    folder=Path(folder)
    try:
        request=read_record(folder/'agent-request.json',100000)
        current_id=request.get('execution_id')
        info=read_record(folder/'agent-candidate.json',10000)
        if (not isinstance(current_id,str) or not current_id or info.get('execution_id')!=current_id or
                (execution_id is not None and current_id!=execution_id) or
                type(info.get('revision')) is not int or info['revision']<1):return None
        relative=info.get('path')
        if not isinstance(relative,str) or not re.fullmatch(r'candidates/[1-9][0-9]*',relative):return None
        candidate=folder/relative
        if ((folder/'candidates').is_symlink() or candidate.is_symlink() or
                candidate.resolve().parent!=(folder/'candidates').resolve()):return None
        identity=model_digest(candidate)
        if identity is None:return None
        ready=read_record(candidate/'model-ready.json')
        result=read_record(candidate/'result.json')
        if (ready.get('revision')!=1 or (ready.get('bytes'),ready.get('sha256'))!=identity or
                ready.get('phase') not in ('core_export','interchange_exports') or
                type(result.get('triangles')) is not int or result['triangles']<1 or
                ready.get('result',{}).get('triangles')!=result['triangles']):return None
        return {'path':candidate,'info':info,'identity':identity,'result':result}
    except (OSError,ValueError,KeyError,TypeError,AttributeError):return None


def completed_outcome(folder):
    """Read-only completion check bound to THIS run and its renderer artifacts.

    A lone outcome, a previous job's GLB or an unfinished candidate cannot end
    the runner. Only finish_model writes the atomic outcome after all copies.
    """
    folder=Path(folder)
    try:
        outcome=read_record(folder/'agent-outcome.json',10000)
        current=current_candidate(folder)
        if current is None:return None
        info=current['info'];execution_id=info['execution_id']
        revision=outcome.get('revision')
        if (not isinstance(execution_id,str) or not execution_id or
                outcome.get('execution_id')!=execution_id or info.get('execution_id')!=execution_id or
                outcome.get('finished') is not True or type(revision) is not int or revision<1 or
                info.get('revision')!=revision or type(outcome.get('accepted')) is not bool):return None
        identity=current['identity'];result=current['result']
        if (identity!=model_digest(folder) or outcome.get('model_sha256')!=identity[1] or
                read_record(folder/'result.json')!=result):return None
        review=read_record(folder/'visual-review.json',10000)
        if (review.get('model_revision')!=revision or review.get('accepted') is not outcome['accepted'] or
                (outcome['accepted'] and (review.get('assessment_completed') is not True or review.get('issues')))):
            return None
        return outcome
    except (OSError,ValueError,KeyError,TypeError,AttributeError):return None


class JobTools:
    def __init__(self, folder, build=None, finalize=None):
        self.folder = Path(folder)
        self.request = json.loads((self.folder/'agent-request.json').read_text())
        self.execution_id = self.request.get('execution_id') or secrets.token_hex(16)
        if not self.request.get('execution_id'):
            self.request['execution_id']=self.execution_id
            write(self.folder/'agent-request.json',self.request)
        self.photos = read_photos(self.folder)
        self.revision = 0; self.attempts = 0; self.current = None; self.seen = set()
        self.build_callback = build; self.finalize_callback = finalize
        self.started = time.monotonic(); self.blender_seconds = 0.; self.finished = False
        self.calls = []; self.tool_failures = 0; self.final_report = None

    def record(self, name, status, error=None):
        entry = {'tool':name,'status':status,'revision':self.revision,
                 'elapsed_seconds':round(time.monotonic()-self.started,2)}
        if error: entry['error'] = tool_error(error)
        if status == 'failed': self.tool_failures += 1
        self.calls.append(entry)
        # No prompt, tool arguments, generated code, images or reasoning.
        write(self.folder/'agent-tools.json', {'calls':self.calls[-40:],
              'total_calls':sum(c['status'] != 'started' for c in self.calls),'failures':self.tool_failures,
              'build_attempts':self.attempts,'revision':self.revision})
        if status=='failed': self.progress('Blad narzedzia '+name+': '+entry['error'][:400])
        elif status=='started':
            labels={'get_modeling_contract':'Astra odczytuje narzedzia geometrii i materialow.',
                    'get_current_model':'Astra sprawdza aktualna geometrie i rewizje.',
                    'build_model':'Astra przekazuje plan do walidacji i budowy w Blenderze.',
                    'edit_model':'Astra przekazuje konkretne poprawki geometrii.',
                    'inspect_render':'Astra pobiera rzeczywisty render do oceny.',
                    'finish_model':'Astra konczy ocene; Blender przygotowuje eksporty.'}
            self.progress(labels.get(name,'Codex wykonuje narzedzie Blender MCP.'))

    def check(self, revision=None):
        if (self.folder/'agent-cancelled').exists(): raise InterruptedError('Zlecenie anulowane.')
        if time.monotonic()-self.started > BUILD_DEADLINE: raise TimeoutError('Wykorzystano czas zlecenia Codexa.')
        if revision is not None and revision != self.revision: raise ValueError('CONFLICT: odczytaj aktualna rewizje modelu.')

    def progress(self, detail):
        write(self.folder/'agent-progress.json', {'detail':detail,'revision':self.revision,'blender_seconds':round(self.blender_seconds,2)})

    def snapshot(self, section='summary', offset=0, limit=SNAPSHOT_PAGE_CHARS,
                 expected_revision=None, expected_sha256=None):
        if section not in ('summary',)+SNAPSHOT_SECTIONS:
            raise ValueError('Nieprawidlowa sekcja modelu.')
        if expected_revision is not None and (type(expected_revision) is not int or expected_revision != self.revision):
            raise ValueError('CONFLICT: odczytaj aktualna rewizje modelu.')
        if type(offset) is not int or offset < 0 or type(limit) is not int or not 1 <= limit <= 16000:
            raise ValueError('Nieprawidlowy offset lub limit strony modelu.')
        if section == 'summary' and (offset != 0 or expected_sha256 is not None):
            raise ValueError('Offset i SHA256 wymagaja wskazania konkretnej sekcji modelu.')
        if expected_sha256 is not None and (not isinstance(expected_sha256, str) or
                re.fullmatch('[0-9a-f]{64}', expected_sha256) is None):
            raise ValueError('Nieprawidlowy SHA256 sekcji modelu.')
        if self.current is None:
            if section != 'summary':
                raise ValueError('Nie ma aktualnego modelu do odczytania.')
            return {'revision':0,'has_model':False,'finished':False,
                    'builds_remaining':MAX_BUILDS-self.attempts,'sections':{}}
        # Pages use the original UTF-8 text, not a shortened or reformatted JSON
        # object. Concatenation is lossless even across non-ASCII object names.
        sections = {'scene':(self.current/'scene.json').read_text(encoding='utf-8'),
                    'edits':(self.current/'edits.py').read_text(encoding='utf-8') if (self.current/'edits.py').exists() else '',
                    'report':(self.current/'result.json').read_text(encoding='utf-8'),
                    'visual_review':json.dumps(self.final_report, ensure_ascii=False)}
        info = {name:section_info(text, name) for name,text in sections.items()}
        if section != 'summary':
            text = sections[section]; descriptor = info[section]
            if offset > len(text):
                raise ValueError('Offset wykracza poza sekcje modelu.')
            if offset and expected_revision is None:
                raise ValueError('Kolejna strona wymaga expected_revision z pierwszego odczytu.')
            if expected_sha256 is not None and expected_sha256 != descriptor['sha256']:
                raise ValueError('CONFLICT: sekcja modelu zmienila sie; odczytaj ja od poczatku.')
            def page(end):
                return {'revision':self.revision,'section':section,
                        'sha256':descriptor['sha256'],'format':descriptor['format'],
                        'total_characters':descriptor['characters'],'total_bytes':descriptor['bytes'],
                        'offset_unit':'unicode_code_points','offset':offset,
                        'next_offset':end if end < len(text) else None,
                        'complete':end == len(text),'text':text[offset:end]}
            end = min(len(text), offset+limit)
            result = page(end)
            if snapshot_wire_size(result) > SNAPSHOT_MAX_BYTES:
                low, high = 0, end-offset-1
                while low < high:
                    middle = (low+high+1)//2
                    if snapshot_wire_size(page(offset+middle)) <= SNAPSHOT_MAX_BYTES:
                        low = middle
                    else:
                        high = middle-1
                result = page(offset+low)
            return result
        result = {'revision':self.revision,'has_model':True,'finished':self.finished,
                  'builds_remaining':0 if self.finished else MAX_BUILDS-self.attempts,
                  'scene':None,'edits':None,'report':None,'visual_review':None,
                  'inspected_views':sorted(self.seen),'sections':info}
        # Keep small existing snapshots compatible, but never silently chop a
        # scene, code history, object-name list, or visual-issues array.
        for name in ('report','scene','edits','visual_review'):
            if len(sections[name]) > SNAPSHOT_MAX_BYTES:
                continue
            value = sections[name] if name == 'edits' else json.loads(sections[name])
            result[name] = value; info[name]['inline'] = True
            if snapshot_wire_size(result) > SNAPSHOT_MAX_BYTES:
                result[name] = None; info[name]['inline'] = False
        return result

    def review_result(self):
        if snapshot_wire_size(self.final_report) <= SNAPSHOT_MAX_BYTES:
            return self.final_report
        # An allowed 12-issue verdict can still exceed the transport budget with
        # Unicode. Completion and its saved evidence remain intact; only the
        # response body switches to an explicit paginated-details reference.
        result = {name:self.final_report[name] for name in
                  ('revision','status','assessment_completed','accepted','model_revision',
                   'inspected_views','executor','likeness_verified')}
        result.update({'issues':None,'summary':None,'issues_count':len(self.final_report['issues']),
                       'sections':{'visual_review':section_info(json.dumps(self.final_report,ensure_ascii=False),'visual_review')}})
        return result

    def build(self, scene, edits=''):
        self.check()
        if self.attempts >= MAX_BUILDS: raise ValueError('Wykorzystano piec prob budowy. Zachowaj najlepszy istniejacy model i opisz wady.')
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
        self.progress('Codex przekazal model do Blendera. Budowa i rendery proby %d/%d.'%(self.attempts,MAX_BUILDS))
        started=time.monotonic()
        try:
            if self.build_callback: self.build_callback(candidate)
            else:
                import server
                event = threading.Event()
                # Parent terminates the process group on cancellation. No user
                # API key or worker state is mounted in this Blender container.
                server.run_blender(self.folder.name,candidate,event,timeout=min(420,BUILD_DEADLINE-(time.monotonic()-self.started)))
        except (ValueError, RuntimeError, OSError, TimeoutError) as error:
            diagnostic = anatomy_build_error(candidate, error)
            if diagnostic is error: raise
            raise diagnostic from error
        finally:
            self.blender_seconds+=time.monotonic()-started
            self.progress('Blender zakonczyl probe. Codex sprawdza geometrie i rendery.')
        if not (candidate/'result.json').is_file() or not (candidate/'model.glb').is_file():
            raise ValueError('Brak poprawnego eksportu; poprzedni model pozostaje zachowany.')
        self.current=candidate; self.revision+=1; self.seen=set()
        write(self.folder/'agent-candidate.json',{'path':str(candidate.relative_to(self.folder)),'revision':self.revision,
              'execution_id':self.execution_id,'blender_seconds':self.blender_seconds})
        return self.snapshot()

    def call(self, name, arguments):
        if self.finished:
            if arguments.get('expected_revision',self.revision)!=self.revision:
                raise ValueError('CONFLICT: odczytaj aktualna rewizje modelu.')
            if name=='finish_model':
                if any(arguments.get(key)!=self.final_report.get(key) for key in ('accepted','issues','summary')):
                    raise ValueError('Model juz zakonczony. Odczytaj get_current_model; zmiana oceny wymaga nowego zlecenia.')
                return self.review_result()
            if name in ('build_model','edit_model'):
                raise ValueError('Model juz zakonczony. Odczytaj get_current_model; nowa budowa wymaga nowego zlecenia.')
        else:self.check(arguments.get('expected_revision'))
        if name=='get_modeling_contract':
            return {'job_id':self.folder.name,'prompt':self.request['prompt'],
                    'instructions':self.request['instructions'],'scene_schema':photo_schema(len(self.photos)),
                    'coordinate_and_geometry_guide':PROMPT,
                    'edit_helpers':'bpy, math, random, Vector. make_material(name,rgb,pattern="plain",roughness=0.7,metallic=0.0) returns a bpy.types.Material. At most 8 NEW materials across all accumulated edits; reuse existing materials with bpy.data.materials.get(name). mesh_object(name,vertices,faces,material), tube(name,points,radii,material,sides=12), ellipsoid(name,center,scale=None,material=None,subdivisions=4,*,radii=None), join_meshes(objects,name) each return one bpy.types.Object, not a tuple. ellipsoid radii is a compatibility alias for scale; provide only one. No imports except bpy/math/random/mathutils. No files, shell or network.',
                    'references':[{'index':i,'view':p.get('view'),'name':p.get('name')} for i,p in enumerate(self.photos)],'revision':self.revision}
        if name=='get_current_model': return self.snapshot(**arguments)
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
            if not self.finished:self.seen.add(view)
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
            identity=model_digest(self.folder)
            write(self.folder/'agent-outcome.json',{'finished':True,'revision':self.revision,'accepted':accepted,
                  'execution_id':self.execution_id,'model_sha256':identity[1] if identity else None,
                  'blender_seconds':self.blender_seconds,'builds':self.attempts})
            self.finished=True;self.final_report=report
            self.progress('Model i ocena zapisane. Zlecenie zakonczone; przygotowano wynik do odebrania.')
            return self.review_result()
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
        rid = None
        try:
            request=json.loads(raw);method=request.get('method');rid=request.get('id')
            if rid is None:continue
            if method=='initialize':
                result={'protocolVersion':'2025-03-26','capabilities':{'tools':{}},'serverInfo':{'name':'forge-blender','version':'29'}}
            elif method=='ping':result={}
            elif method=='tools/list':result={'tools':TOOLS}
            elif method=='tools/call':
                params=request.get('params',{});name=params.get('name');arguments=params.get('arguments',{})
                try:
                    tool=next((t for t in TOOLS if t['name']==name),None)
                    if tool is None:raise ValueError('Nieznane narzedzie MCP.')
                    check_tool_arguments(arguments,tool['inputSchema'])
                    job.record(name,'started')
                    value=job.call(name,arguments)
                    content=value if isinstance(value,list) else [{'type':'text','text':json.dumps(value,ensure_ascii=False)}]
                    result={'content':content,'isError':False}
                    job.record(name,'completed')
                except (ValueError,RuntimeError,OSError,TimeoutError,KeyError,TypeError,SyntaxError,AttributeError) as error:
                    job.record(name if isinstance(name,str) else 'invalid_tool','failed',error)
                    # An execution/argument error belongs to this tool call.
                    # Keep its request ID so Codex can read and repair it.
                    result={'content':[{'type':'text','text':tool_error(error)}],'isError':True}
            else:
                outgoing.write(json.dumps({'jsonrpc':'2.0','id':rid,'error':{'code':-32601,'message':'Method not found'}})+'\n');outgoing.flush();continue
            outgoing.write(json.dumps({'jsonrpc':'2.0','id':rid,'result':result})+'\n');outgoing.flush()
        except (ValueError,TypeError,KeyError):
            outgoing.write(json.dumps({'jsonrpc':'2.0','id':rid,'error':{'code':-32600,'message':'Invalid request'}})+'\n');outgoing.flush()


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
