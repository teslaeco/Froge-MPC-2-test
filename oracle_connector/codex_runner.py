"""Run real Codex with a job-scoped Blender MCP and a bounded API gateway.

The OpenAI key stays in this trusted process. Codex receives a temporary token
valid only on this loopback gateway; Blender gets neither credential.
"""
import hmac
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import secrets
import re
import signal
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from blender_mcp import completed_outcome, current_candidate, retain_candidate, write
from ai_stream import openai_error
from agent_limits import MAX_REQUESTS, MAX_OUTPUT_TOKENS, MAX_SECONDS, MAX_BUILDS

ROOT=Path(__file__).resolve().parent
MODEL='gpt-6-astra'
LITE_HEADER='x-openai-internal-codex-responses-lite'


def request_tools(payload):
    """Codex 0.154 Astra puts schemas in developer additional_tools items."""
    catalog=list(payload.get('tools') or [])
    for item in payload.get('input',[]) if isinstance(payload.get('input'),list) else []:
        if isinstance(item,dict) and item.get('type')=='additional_tools' and item.get('role')=='developer':
            catalog.extend(item.get('tools') or [])
    return tool_entries(catalog)


def tool_entries(tools, namespace=None):
    """Responses supports both plain and namespace-wrapped tool schemas."""
    for tool in tools if isinstance(tools,list) else []:
        if not isinstance(tool,dict):continue
        if tool.get('type')=='namespace':
            yield from tool_entries(tool.get('tools',[]),tool.get('name'))
        else:yield namespace,tool


def safe_message(value, secrets_to_hide=()):
    if not isinstance(value,str):return None
    for secret in secrets_to_hide:
        if secret:value=value.replace(secret,'[redacted]')
    value=re.sub(r'(?i)Bearer\s+\S+|\bsk-[A-Za-z0-9_-]+', '[redacted]', value)
    value=re.sub(r'data:image/[^\s]+', '[image omitted]', value)
    return value[:1800]

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None


def code_errors(value, depth=0):
    """Read tool execution errors only, never assistant analysis or reasoning."""
    if depth > 10:return []
    if isinstance(value, str):
        if len(value)>200000:return []
        try:return code_errors(json.loads(value),depth+1)
        except (ValueError,TypeError):
            # Code Mode often returns a plain text wrapper around a JS error.
            return [match.group(0)[:1200] for line in value.splitlines()
                    for match in [re.search(r'\b(?:ReferenceError|TypeError|SyntaxError|RangeError|Error):.*',line)] if match][:3]
    if isinstance(value,list):
        return [error for item in value[:30] for error in code_errors(item,depth+1)][:3]
    if isinstance(value,dict):
        if value.get('type') in ('image','input_image','reasoning'):return []
        errors=[]
        if isinstance(value.get('error'),str):errors.append(value['error'][:1200])
        elif isinstance(value.get('error'),dict):
            message=value['error'].get('message')
            if isinstance(message,str):errors.append(message[:1200])
        for name in ('output','content','text','result'):
            if name in value:errors.extend(code_errors(value[name],depth+1))
        return errors[:3]
    return []


def executable():
    path=ROOT/'tools'/'codex'/'codex'
    receipt=path.parent/'verified.json'
    try:
        verified=json.loads(receipt.read_text())
        expected={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ('codex_runner.py','blender_mcp.py')}
        return path if (path.is_file() and os.access(path,os.X_OK) and verified.get('sources')==expected
                        and verified.get('blender_build_roundtrip') is True) else None
    except (OSError,ValueError):return None


class Gateway:
    def __init__(self,key,folder,cancelled):
        self.key=key;self.folder=folder;self.cancelled=cancelled
        self.token=secrets.token_urlsafe(32);self.requests=0;self.output=0;self.input=0
        self.unknown_usage=False;self.lock=threading.Lock();self.save_lock=threading.Lock();self.active=False;self.error=None
        self.error_code=None;self.error_source=None;self.upstream_status=None;self.retry_after=None
        self.execution_calls=[];self.execution_ids=set();self.completed=False
        outer=self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*_):pass
            def reject(self,code,message,error_code='forge_request'):
                body=json.dumps({'error':{'message':message,'type':'invalid_request_error','code':error_code}}).encode()
                self.send_response(code);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
            def do_GET(self):
                if self.path.split('?',1)[0]!='/v1/models' or not hmac.compare_digest(self.headers.get('Authorization',''),'Bearer '+outer.token):
                    return self.reject(403,'Unauthorized job request')
                # Codex can use its built-in/fallback metadata for an explicitly
                # selected model. No remote account listing or extra API call.
                body=b'{"models":[]}'
                self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
            def do_POST(self):
                if self.path!='/v1/responses' or not hmac.compare_digest(self.headers.get('Authorization',''),'Bearer '+outer.token):
                    return self.reject(403,'Unauthorized job request')
                acquired=False
                try:
                    size=int(self.headers.get('Content-Length','0'))
                    if not 1<=size<=32*1024**2:return self.reject(413,'Request too large')
                    payload=json.loads(self.rfile.read(size))
                    if not isinstance(payload,dict) or payload.get('model')!=MODEL:return self.reject(400,'Only the configured Astra model is available')
                    # finish_model is the terminal operation. Do not buy another
                    # Astra turn solely to announce already verified artifacts.
                    if completed_outcome(outer.folder) is not None:
                        outer.completed=True;outer.save()
                        return self.reject(422,'Model i ocena zostaly zapisane. Zlecenie zakonczone.', 'FORGE_JOB_FINISHED')
                    entries=list(request_tools(payload))
                    if not any(t.get('name')=='exec' and t.get('type')=='custom' for _,t in entries):
                        outer.stop('CODEX_TOOLS_MISSING','CODEX_TOOLS_MISSING: Astra nie otrzymala narzedzia exec. Sprawdz instalacje trybu kodowego i Blender MCP; nie wyslano zapytania do OpenAI.')
                        return self.reject(422,outer.error)
                    outer.observe_execution(payload)
                    if len(outer.execution_calls)>=3:
                        recent=outer.execution_calls[-3:]
                        if all(v.get('errors') and v['errors']==recent[0].get('errors') for v in recent):
                            outer.stop('FORGE_REPEATED_CODE_ERROR','Trzy takie same bledy wykonania kodu przed MCP: '+recent[-1]['errors'][0]+'. Zachowano diagnostyke; przerwano petle.')
                            return self.reject(422,outer.error,outer.error_code)
                    trace=outer.folder/'agent-tools.json'
                    if trace.is_file() and trace.stat().st_size<200000:
                        history=json.loads(trace.read_text()).get('calls',[])
                        completed=[v for v in history if v.get('status')!='started'][-3:]
                        if len(completed)==3 and all(v.get('status')=='failed' and
                            (v.get('tool'),v.get('error'))==(completed[0].get('tool'),completed[0].get('error')) for v in completed):
                            outer.stop('FORGE_REPEATED_TOOL_ERROR','Trzy takie same bledy narzedzia '+str(completed[-1].get('tool'))+'. Przerwano petle bez kolejnego zapytania API. Szczegoly sa w raporcie MCP.')
                            return self.reject(422,outer.error,outer.error_code)
                    with outer.lock:
                        if outer.active:return self.reject(409,'A model request is already running')
                        if outer.error:
                            return self.reject(422,outer.error,outer.error_code or 'forge_stopped')
                        if outer.cancelled.is_set() or outer.unknown_usage:
                            outer.stop('FORGE_UNCERTAIN_USAGE','Zlecenie zatrzymane po przerwaniu polaczenia lub anulowaniu. Nie uruchomiono kolejnego zapytania API.')
                            return self.reject(422,outer.error,outer.error_code)
                        if outer.requests>=MAX_REQUESTS or outer.output>=MAX_OUTPUT_TOKENS:
                            outer.stop('FORGE_JOB_BUDGET','Osiagnieto lokalny limit zlecenia FORGE (%d zapytan, %d tokenow odpowiedzi i rozumowania). To nie jest limit konta OpenAI. Nie uruchomiono kolejnego zapytania.'%(MAX_REQUESTS,MAX_OUTPUT_TOKENS))
                            return self.reject(422,outer.error,outer.error_code)
                        outer.requests+=1
                        outer.active=True;acquired=True
                        allowance=min(16000,MAX_OUTPUT_TOKENS-outer.output)
                    payload['max_output_tokens']=allowance
                    payload['store']=False;payload['stream']=True
                    payload['reasoning']={**payload.get('reasoning',{}),'effort':'high'}
                    # Actual state and execution recipe accompany every turn.
                    # This does not synthesize tool results or model decisions.
                    if isinstance(payload.get('input'),list):
                        payload['input'].append({'type':'message','role':'developer','content':[{
                            'type':'input_text','text':outer.execution_guidance()}]})
                    headers={'Authorization':'Bearer '+outer.key,'Content-Type':'application/json'}
                    # Preserve the official CLI's wire protocol marker. No
                    # caller credentials or arbitrary headers are forwarded.
                    if self.headers.get(LITE_HEADER)=='true':headers[LITE_HEADER]='true'
                    request=urllib.request.Request('https://api.openai.com/v1/responses',data=json.dumps(payload).encode(),headers=headers)
                    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
                    with opener.open(request,timeout=180) as response:
                        self.send_response(200);self.send_header('Content-Type','text/event-stream');self.send_header('Cache-Control','no-store');self.end_headers()
                        measured=False
                        try:
                            for line in response:
                                if outer.cancelled.is_set():break
                                terminal=False
                                if line.startswith(b'data:'):
                                    try:
                                        event=json.loads(line[5:]);value=event.get('response') or {}
                                        if event.get('type') in ('response.completed','response.incomplete','response.failed'):
                                            terminal=True
                                            if event.get('type')=='response.failed':
                                                issue=value.get('error') or {}
                                                outer.stop(str(issue.get('code') or 'OPENAI_RESPONSE_FAILED'),str(issue.get('message') or 'OpenAI nie ukonczylo odpowiedzi.'),'openai')
                                            usage=value.get('usage') or {}
                                            if type(usage.get('output_tokens')) is int:
                                                with outer.lock:
                                                    outer.output+=usage['output_tokens'];outer.input+=usage.get('input_tokens',0)
                                                measured=True;outer.save()
                                    except (ValueError,TypeError):pass
                                self.wfile.write(line);self.wfile.flush()
                                if terminal:
                                    # Complete the SSE event and release the slot
                                    # even when a proxy keeps its stream open.
                                    self.wfile.write(b'\n');self.wfile.flush();break
                        finally:
                            if not measured:
                                # Unknown billing after a disconnected stream is
                                # not permission to silently buy another attempt.
                                outer.unknown_usage=True;outer.save()
                except urllib.error.HTTPError as error:
                    status=error.code
                    try:
                        data=json.loads(error.read(8000));code=(data.get('error') or {}).get('code')
                    except (ValueError,OSError,AttributeError):code=None
                    outer.upstream_status=status
                    outer.retry_after=safe_message(error.headers.get('Retry-After')) if error.headers else None
                    error.close()
                    quota_messages={
                        'insufficient_quota':'Brak dostepnego limitu rozliczen lub kredytow.',
                        'credit_balance_exhausted':'Wyczerpano kredyty API.',
                        'organization_spend_limit_exceeded':'Osiagnieto limit wydatkow organizacji.',
                        'project_spend_limit_exceeded':'Osiagnieto limit wydatkow projektu.',
                        'organization_usage_limit_exceeded':'Osiagnieto limit wykorzystania organizacji.'}
                    message=('OpenAI API: '+quota_messages[code]+' Sprawdz rozliczenia i limity API.'
                             if code in quota_messages else openai_error(status))
                    outer.stop(str(code or 'OPENAI_HTTP_'+str(status)),message,'openai')
                    # A terminal provider error must not invite a Codex retry
                    # or be overwritten by our separate local request budget.
                    self.reject(422,outer.error,outer.error_code)
                except (OSError,ValueError,TypeError):
                    outer.unknown_usage=True
                    outer.stop('FORGE_STREAM_INTERRUPTED','Przerwano odbior odpowiedzi API. Koszt proby jest niepewny; automatyczne ponowienie zatrzymane.')
                    try:self.reject(422,outer.error,outer.error_code)
                    except OSError:pass
                finally:
                    if acquired:
                        with outer.lock:outer.active=False
        self.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        self.server.daemon_threads=True
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True)
    def save(self):
        # The HTTP thread and completed-job supervisor may finish together.
        # Serialize writes using their shared atomic temporary-file name.
        with self.save_lock:
            write(self.folder/'agent-usage.json',{'model':MODEL,'requests':self.requests,'input_tokens':self.input,
                  'output_tokens':self.output,'output_token_limit':MAX_OUTPUT_TOKENS,'request_limit':MAX_REQUESTS,
                  'seconds_limit':MAX_SECONDS,'build_limit':MAX_BUILDS,
                  'unknown_usage':self.unknown_usage,'completed':self.completed,'last_error':self.error,'error_code':self.error_code,
                  'error_source':self.error_source,'upstream_status':self.upstream_status,'retry_after':self.retry_after})
    def observe_execution(self,payload):
        for item in payload.get('input',[]) if isinstance(payload.get('input'),list) else []:
            if not isinstance(item,dict) or item.get('type') not in ('custom_tool_call_output','function_call_output'):continue
            call_id=item.get('call_id')
            if not isinstance(call_id,str) or call_id in self.execution_ids:continue
            self.execution_ids.add(call_id)
            errors=[safe_message(error,(self.key,self.token)) for error in code_errors(item.get('output'))]
            self.execution_calls.append({'call_id':call_id[:120],'request':self.requests,'errors':errors})
        if self.execution_calls:
            write(self.folder/'agent-execution.json',{'calls':self.execution_calls[-40:],
                  'failed_calls':sum(bool(v['errors']) for v in self.execution_calls)})
    def execution_guidance(self):
        candidate={}
        path=self.folder/'agent-candidate.json'
        if path.is_file() and path.stat().st_size<10000:
            try:candidate=json.loads(path.read_text())
            except (ValueError,OSError):pass
        revision=candidate.get('revision',0)
        text=('FORGE execution state: current revision=%s; has_model=%s; model requests remaining=%d. '
              'You are GPT-6 Astra, the model designer. Codex executes your calls and Blender creates the geometry. '
              'Use the registered tools via Code Mode, always await the result. Each exec is a FRESH JavaScript isolate: '
              'local const/let values do not survive into the next exec. Use store(key, JSON-serializable value) and load(key), '
              'or define the complete scene inside the same exec that calls build_model. '
              'MCP returns {content:[{type:"text",text:"JSON"}],isError}. Parse the text, not the wrapper object. '
              'For a build: const scene = /* your complete scene */; '
              'text(await tools.mcp__blender__build_model({scene_json:JSON.stringify(scene),expected_revision:%s})); '
              'Use // @exec: {"yield_time_ms":120000,"max_output_tokens":16000} before long build/render calls. '
              'Only wait when exec actually returns a running cell identifier. Await that same cell instead of starting a duplicate build. '
              'Return render image blocks using image(block); preserve original references. '
              'A successful finish_model is terminal: artifacts and verdict are saved. Do not start another model turn, '
              'repeat exports or continue editing after it; the supervisor delivers the saved result. '
              )%(revision,str(bool(revision)).lower(),max(0,MAX_REQUESTS-self.requests),revision)
        if not revision:
            text+='No model has been built. After reading the contract once, your next substantive action must be build_model with a complete scene, not further empty state reads or announcements. '
        if self.execution_calls and self.execution_calls[-1]['errors']:
            text+='The last Code Mode call failed before or during MCP. Correct this exact error: '+self.execution_calls[-1]['errors'][0]
        return text
    def stop(self,code,message,source='forge'):
        self.error_code=code;self.error_source=source;self.error=safe_message(message,(self.key,self.token));self.save()
    def __enter__(self):self.thread.start();return self
    def __exit__(self,*_):self.server.shutdown();self.server.server_close();self.save()


def command(binary,folder,port):
    config={
        'model_provider':'forge',
        'model_providers.forge.name':'FORGE job gateway',
        'model_providers.forge.base_url':'http://127.0.0.1:%d/v1'%port,
        'model_providers.forge.env_key':'FORGE_CODEX_RUN_TOKEN',
        'model_providers.forge.wire_api':'responses',
        'model_providers.forge.request_max_retries':0,
        'model_providers.forge.stream_max_retries':0,
        'model_reasoning_effort':'high','web_search':'disabled',
        # Astra's official CLI catalog uses code_mode_only. Keep its execution
        # surface even with a fresh model cache; the MCP tools are nested in it.
        'features.code_mode_only':True,
        'features.code_mode_host.enabled':True,
        'features.code_mode_host.disable_in_process_fallback':True,
        'shell_environment_policy.inherit':'none',
        'mcp_servers.blender.command':sys.executable,
        'mcp_servers.blender.args':[str(ROOT/'blender_mcp.py'),str(folder)],
        'mcp_servers.blender.env_vars':[],
        'mcp_servers.blender.required':True,
        'mcp_servers.blender.startup_timeout_sec':20,
        'mcp_servers.blender.supports_parallel_tool_calls':False,
        'mcp_servers.blender.tool_timeout_sec':480,
        'mcp_servers.blender.default_tools_approval_mode':'approve',
        'mcp_servers.blender.tools.get_modeling_contract.output_token_limit':16000,
        'mcp_servers.blender.tools.get_current_model.output_token_limit':16000,
        'check_for_update_on_startup':False,
    }
    args=[str(binary),'exec','--ignore-user-config','--strict-config','--ephemeral','--json',
          '--sandbox','read-only','--skip-git-repo-check','--model',MODEL,'--cd',str(folder)]
    # No model-authored host commands, external apps, subagents, hooks or web.
    for feature in ('shell_tool','shell_snapshot','workspace_dependencies','unified_exec','apps','plugins','hooks','multi_agent','browser_use','computer_use','image_generation','skill_mcp_dependency_install','skill_search','view_image'):
        args+=['--disable',feature]
    for key,value in config.items():args+=['-c',key+'='+json.dumps(value)]
    for path in sorted(folder.glob('reference-[0-3].jpg')):args+=['--image',str(path)]
    return args+['-']


def run(folder,prompt,instructions,key,cancelled,progress,binary=None):
    folder=Path(folder);binary=binary or executable()
    if binary is None:raise RuntimeError('Codex nie jest zainstalowany lub zweryfikowany. Uruchom instalator v30.')
    execution_id=secrets.token_hex(16)
    write(folder/'agent-request.json',{'prompt':prompt,'instructions':instructions,'execution_id':execution_id})
    (folder/'agent-cancelled').unlink(missing_ok=True)
    task=('Complete the user 3D task using the attached original images and the Blender MCP tools. '
          'A prompt or plan alone is not completion. Read get_modeling_contract once, build real geometry, '
          'inspect exported renders, and edit specific faults with edit_model. Available bpy edits allow '
          'custom geometry beyond scene presets. Match reference silhouette and proportions; avoid generic '
          'placeholder balls for hair and face. Keep hair attached and correctly scaled, no duplicate eye textures. '
          'There are at most 5 builds and a bounded API/time budget: produce compact tool calls promptly, '
          'spend time correcting observed defects. Full format exports happen once at finish_model. '
          'Inspect front, side, back, and face for people on the FINAL revision. '
          'Finish with accepted=false and specific issues if quality is insufficient. '
          'After finish_model succeeds, the job is complete. Do not make further tool calls or request further work. '
          'No shell, external generators, network tools or shop publication are authorized in this job. '
          'MCP tools are called INSIDE Code Mode exec using their exact fully qualified names. '
          'Do not call an unqualified tools.get_modeling_contract or invent shell tools. '
          'For your first exec use: const r = await tools.mcp__blender__get_modeling_contract({}); '
          'const c = JSON.parse(r.content.find(b=>b.type==="text").text); store("contract",c); text(c); '
          'The MCP response contains content text blocks: parse their text as JSON when using scene_schema. '
          'Then call tools.mcp__blender__build_model({scene_json: JSON.stringify(scene), expected_revision: 0}). '
          'Always await calls and print their results with text; do not merely describe them. '
          'After each isError result, correct the exact reported argument, do not repeat the same call. '
          'There are 32 model turns total. Each exec has fresh variables; use store/load for cross-call state. '
          'Define scene and call build_model together. Use one exec to inspect multiple render views sequentially, '
          'returning image blocks with image(block) so you can actually see them. '
          'The latest user brief below and attached images define the task; supplementary instructions follow.\n\n'
          'USER BRIEF:\n'+prompt+'\n\nEXECUTION INSTRUCTIONS:\n'+instructions)
    started=time.monotonic();failure=None
    with Gateway(key,folder,cancelled) as gateway:
        env={k:v for k,v in os.environ.items() if k in ('PATH','HOME','USER','LOGNAME','LANG','XDG_RUNTIME_DIR','DBUS_SESSION_BUS_ADDRESS','TMPDIR')}
        env['FORGE_CODEX_RUN_TOKEN']=gateway.token
        # Invocation-scoped API mode avoids using an unrelated cached ChatGPT
        # login for CLI startup. This token only authenticates our local gateway.
        env['CODEX_API_KEY']=gateway.token
        # Official Code Mode host is a sibling executable in the release bundle.
        env['PATH']=str(Path(binary).resolve().parent)+os.pathsep+env.get('PATH',os.defpath)
        diagnostics=[]
        with (folder/'codex-events.jsonl').open('w') as events, (folder/'codex-stderr.log').open('w') as errors:
            process=subprocess.Popen(command(binary,folder,gateway.server.server_port),stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=errors,env=env,text=True,start_new_session=True)
            process.stdin.write(task);process.stdin.close()
            def consume():
                for line in process.stdout:
                    try:event=json.loads(line)
                    except ValueError:continue
                    item=event.get('item') or {}
                    # Persist execution evidence without hidden reasoning or
                    # verbose raw tool responses/images.
                    safe={'type':event.get('type'),'thread_id':event.get('thread_id')}
                    if item.get('type'):safe['item_type']=item['type']
                    if item.get('type')=='mcp_tool_call':safe['tool']={k:item[k] for k in ('type','name','tool','server','status') if k in item}
                    if event.get('type') in ('turn.completed','turn.failed','error'):safe['usage']=event.get('usage')
                    message=(event.get('error') or {}).get('message') if isinstance(event.get('error'),dict) else event.get('message')
                    if item.get('type')=='error':message=item.get('message')
                    if message and (event.get('type') in ('turn.failed','error') or item.get('type')=='error'):
                        safe['message']=safe_message(message,(key,gateway.token))
                        diagnostics.append(safe['message'])
                    events.write(json.dumps(safe)+'\n');events.flush()
            reader=threading.Thread(target=consume,daemon=True);reader.start()
            last=None;finished_at=None
            def terminate():
                if process.poll() is not None:return
                try:os.killpg(process.pid,signal.SIGTERM)
                except ProcessLookupError:return
                try:process.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    try:os.killpg(process.pid,signal.SIGKILL)
                    except ProcessLookupError:pass
                    process.wait(timeout=5)
            while process.poll() is None:
                if completed_outcome(folder) is not None:
                    if finished_at is None:finished_at=time.monotonic()
                    # A brief drain lets the final MCP response finish. The
                    # gateway already refuses another paid request after this
                    # atomic outcome, so a lingering CLI cannot spend more.
                    if gateway.completed or time.monotonic()-finished_at>=2:
                        gateway.completed=True;gateway.save();terminate();break
                startup_stalled=gateway.requests==0 and time.monotonic()-started>60
                if cancelled.wait(1) or startup_stalled or time.monotonic()-started>MAX_SECONDS:
                    (folder/'agent-cancelled').touch()
                    terminate()
                    # Rootless container may outlive the supervising process.
                    try:subprocess.run(['podman','rm','--force','froge-job-'+folder.name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=20)
                    except (OSError,subprocess.TimeoutExpired):pass
                    if cancelled.is_set():raise InterruptedError('Zlecenie anulowane.')
                    failure=('Codex nie uruchomil polaczenia z modelem w 60 s. Nie rozpoczeto platnego zapytania.' if startup_stalled else 'Codex przekroczyl czas zlecenia.');break
                path=folder/'agent-progress.json'
                if path.exists():
                    try:detail=json.loads(path.read_text()).get('detail','')
                    except ValueError:continue
                else:detail='Codex laczy Astre z Blender MCP i analizuje zalaczone zdjecia.'
                if detail!=last:progress(detail);last=detail
            reader.join(timeout=3)
            if not reader.is_alive():process.stdout.close()
            if completed_outcome(folder) is not None:
                gateway.completed=True;gateway.save()
            if process.returncode and not failure and not gateway.completed:failure=gateway.error or ('Codex: '+diagnostics[-1] if diagnostics else 'Codex zakonczyl prace bledem. Zachowano diagnostyke i gotowy model, jezeli powstal.')
    outcome=completed_outcome(folder)
    if outcome is not None:return outcome
    candidate=folder/'agent-candidate.json'
    if candidate.is_file():
        current=current_candidate(folder,execution_id)
        if current is None:
            raise RuntimeError(failure or 'Brak poprawnego modelu z aktualnego uruchomienia. Zachowany starszy lub niekompletny model nie jest nowym wynikiem.')
        info=current['info'];retain_candidate(folder,current['path'])
        write(folder/'visual-review.json',{'status':'not_completed','assessment_completed':False,'accepted':False,'executor':'codex-mcp','issues':[failure or 'Codex nie zakonczyl oceny aktualnego eksportu.']})
        return {'finished':False,'accepted':False,'blender_seconds':info.get('blender_seconds',0)}
    raise RuntimeError(failure or 'Codex nie wykonal modelu. Sam tekst polecenia nie jest wynikiem; nie uruchomiono innego platnego generatora.')
