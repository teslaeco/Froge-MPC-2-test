"""Offline gate: actual Codex -> Code Mode -> Blender MCP -> Responses result.
Only model responses are fixtures. No OpenAI key or external API request.
"""
import io
import json
from pathlib import Path
import shutil
import sys
import threading
import uuid
import hashlib
from unittest.mock import patch
import codex_runner


PROBE = """const matches = ALL_TOOLS.filter(t => t.name.startsWith('mcp__blender__'));
const tool = matches.find(t => t.name === 'mcp__blender__get_current_model');
if (!tool) throw new Error('FORGE_MCP_CATALOG_MISSING');
const result = await tools[tool.name]({});
text({forge_probe: 'TOKEN', tool_names: matches.map(t => t.name), result});"""


def has_value(value, predicate, depth=0):
    if depth > 24: return False
    if isinstance(value, dict):
        return predicate(value) or any(has_value(v, predicate, depth+1) for v in value.values())
    if isinstance(value, list): return any(has_value(v, predicate, depth+1) for v in value)
    if isinstance(value, str):
        try: return has_value(json.loads(value), predicate, depth+1)
        except (ValueError, TypeError): pass
    return False


def result_verified(payload, token):
    # Only the output of our actual exec call qualifies; a request's input,
    # generated code, warning or unavailable-tool response cannot pass.
    for item in payload.get('input', []):
        if not isinstance(item, dict) or item.get('type') != 'custom_tool_call_output' or item.get('call_id') != 'call_fixture': continue
        def verified(value):
            names = value.get('tool_names', [])
            return value.get('forge_probe') == token and all('mcp__blender__'+name in names for name in (
                'get_modeling_contract','build_model','edit_model','get_current_model','inspect_render','finish_model')) and has_value(value.get('result'), lambda v: v.get('has_model') is False and v.get('revision') == 0)
        if has_value(item.get('output'), verified): return True
    return False


class Fixture:
    def __init__(self, token): self.token = token; self.seen = []
    def open(self, request, timeout):
        payload = json.loads(request.data); self.seen.append(payload)
        if len(self.seen) == 1:
            entry = next(((ns,t) for ns,t in codex_runner.request_tools(payload) if t.get('name') == 'exec' and t.get('type') == 'custom'), None)
            if entry is None: raise ValueError('CODEX_EXEC_MISSING')
            namespace, _ = entry
            item = {'id':'ctc_fixture','type':'custom_tool_call','status':'completed','call_id':'call_fixture','name':'exec','input':PROBE.replace('TOKEN',self.token)}
            if namespace: item['namespace'] = namespace
        elif len(self.seen) == 2 and result_verified(payload, self.token):
            item = {'id':'msg_fixture','type':'message','status':'completed','role':'assistant','content':[{'type':'output_text','text':'Offline MCP round-trip complete. No model built.','annotations':[]}]}
        else:
            raise ValueError('CODEX_MCP_RESULT_MISSING: execution did not return all six tools and the actual snapshot')
        response = {'id':'resp_fixture_'+str(len(self.seen)),'object':'response','created_at':1789166000,'status':'completed','model':codex_runner.MODEL,'output':[item],'usage':{'input_tokens':100,'output_tokens':20,'total_tokens':120}}
        events = [{'type':'response.created','response':{**response,'status':'in_progress','output':[]}}, {'type':'response.output_item.done','output_index':0,'item':item}, {'type':'response.completed','response':response}]
        return io.BytesIO(''.join('data: '+json.dumps(e)+'\n\n' for e in events).encode())


class BuildFixture:
    """Real CLI + MCP + Blender build/review/export, scripted model decisions."""
    def __init__(self, token): self.token=token;self.seen=[]

    def open(self, request, timeout):
        payload=json.loads(request.data);step=len(self.seen);self.seen.append(payload)
        if step:
            outputs=[v.get('output') for v in payload.get('input',[]) if isinstance(v,dict)
                     and v.get('type')=='custom_tool_call_output' and v.get('call_id')=='workflow_'+str(step-1)]
            checks=[lambda v:v.get('forge_contract')==self.token and v.get('validated_error') is True and v.get('complete_schema') is True,
                    lambda v:v.get('has_model') is True and v.get('revision')==1,
                    lambda v:v.get('forge_views')==self.token and v.get('images')==3,
                    lambda v:v.get('assessment_completed') is True and v.get('accepted') is True]
            if not any(has_value(v,checks[step-1]) for v in outputs):
                raise ValueError('REAL_WORKFLOW_MISSING: step '+str(step))
        cube={'version':1,'name':'MCP export fixture','materials':[{'name':'blue','rgb':[.02,.2,.7],
              'pattern':'metal','roughness':.35,'metallic':.2,'emission':0}],
              'parts':[{'kind':'box','name':'body','material':'blue','center':[0,0,1],
                        'size':[1,1,2],'rotation':[0,0,0]}]}
        programs=[
            "let bad;try{bad=await tools.mcp__blender__build_model({scene_json:'{}'});}catch(e){bad={isError:true};} "
            "const r=await tools.mcp__blender__get_modeling_contract({}); "
            "const c=JSON.parse(r.content.find(x=>x.type==='text').text); "
            "store('forge_contract',c); "
            "text({forge_contract:"+json.dumps(self.token)+",validated_error:bad.isError===true,"
            "complete_schema:!!c.scene_schema.properties.parts && !!c.coordinate_and_geometry_guide && Array.isArray(c.references)});",
            "if(!load('forge_contract')?.scene_schema)throw new Error('CONTRACT_STATE_LOST'); "
            "const r=await tools.mcp__blender__build_model({scene_json:"+json.dumps(json.dumps(cube))+",expected_revision:0});text(r);",
            "let n=0; for(const view of ['front','side','back']) { const r=await tools.mcp__blender__inspect_render({view,expected_revision:1}); "
            "for(const b of r.content||[]) {if(b.type==='image'){image(b);n++;} else if(b.type==='text')text(b.text);}} "
            "text({forge_views:"+json.dumps(self.token)+",images:n});",
            "text(await tools.mcp__blender__finish_model({expected_revision:1,accepted:true,issues:[],summary:'Offline export fixture; no AI likeness evaluation.'}));"
        ]
        if step < len(programs):
            namespace=next(ns for ns,t in codex_runner.request_tools(payload) if t.get('name')=='exec')
            # exec timeout covers actual CPU Blender work, not a fake callback.
            program='// @exec: {"yield_time_ms": 120000, "max_output_tokens": 12000}\n'+programs[step]
            item={'id':'ctc_workflow_'+str(step),'type':'custom_tool_call','status':'completed',
                  'call_id':'workflow_'+str(step),'name':'exec','input':program}
            if namespace:item['namespace']=namespace
        elif step==4:
            item={'id':'msg_done','type':'message','status':'completed','role':'assistant',
                  'content':[{'type':'output_text','text':'Offline Blender workflow complete.','annotations':[]}]}
        else:raise ValueError('Unexpected extra request in offline workflow')
        response={'id':'resp_workflow_'+str(step),'object':'response','created_at':1789170000,
                  'status':'completed','model':codex_runner.MODEL,'output':[item],
                  'usage':{'input_tokens':100,'output_tokens':20,'total_tokens':120}}
        events=[{'type':'response.created','response':{**response,'status':'in_progress','output':[]}},
                {'type':'response.output_item.done','output_index':0,'item':item},
                {'type':'response.completed','response':response}]
        return io.BytesIO(''.join('data: '+json.dumps(e)+'\n\n' for e in events).encode())


class RecoveringBuildFixture(BuildFixture):
    """Require a real Code Mode ReferenceError to reach the repair guidance."""
    def __init__(self,token):
        super().__init__(token);self.failed_exec_sent=False;self.error_received=False
    def open(self,request,timeout):
        payload=json.loads(request.data)
        if not self.failed_exec_sent:
            self.failed_exec_sent=True
            namespace=next(ns for ns,t in codex_runner.request_tools(payload) if t.get('name')=='exec')
            item={'id':'ctc_execution_error','type':'custom_tool_call','status':'completed',
                  'call_id':'execution_error','name':'exec','input':"throw new ReferenceError('FORGE_FIXTURE_SCENE_UNDEFINED');"}
            if namespace:item['namespace']=namespace
            response={'id':'resp_execution_error','object':'response','created_at':1789170000,
                      'status':'completed','model':codex_runner.MODEL,'output':[item],
                      'usage':{'input_tokens':100,'output_tokens':20,'total_tokens':120}}
            events=[{'type':'response.created','response':{**response,'status':'in_progress','output':[]}},
                    {'type':'response.output_item.done','output_index':0,'item':item},
                    {'type':'response.completed','response':response}]
            return io.BytesIO(''.join('data: '+json.dumps(e)+'\n\n' for e in events).encode())
        if not self.error_received:
            outputs=[v.get('output') for v in payload.get('input',[]) if v.get('call_id')=='execution_error' and v.get('type')=='custom_tool_call_output']
            if not any('FORGE_FIXTURE_SCENE_UNDEFINED' in error for v in outputs for error in codex_runner.code_errors(v)):
                raise ValueError('REAL_EXECUTION_ERROR_MISSING: '+repr(outputs)[:1200])
            if 'Correct this exact error: ReferenceError: FORGE_FIXTURE_SCENE_UNDEFINED' not in json.dumps(payload.get('input',[])):
                raise ValueError('REAL_EXECUTION_REPAIR_GUIDANCE_MISSING')
            self.error_received=True
        return super().open(request,timeout)


def main(binary=None, build=False, test_blender=None):
    folder = codex_runner.ROOT/'state/jobs'/str(uuid.uuid4()); folder.mkdir(parents=True)
    fixture = RecoveringBuildFixture(uuid.uuid4().hex) if build else Fixture(uuid.uuid4().hex)
    passed = False
    try:
        original_command=codex_runner.command
        def fixture_command(*args):
            command=original_command(*args)
            if test_blender:
                for i,value in enumerate(command):
                    if value.startswith('mcp_servers.blender.args='):
                        command[i]='mcp_servers.blender.args='+json.dumps([str(Path(__file__).with_name('test_mcp_blender_bridge.py')),str(folder),str(Path(test_blender).resolve())])
            return command
        with patch('codex_runner.urllib.request.build_opener', return_value=fixture), patch.object(codex_runner,'MAX_SECONDS',220 if build else 50), patch.object(codex_runner,'command',fixture_command):
            try:
                codex_runner.run(folder,'Offline connection test','Read get_current_model; do not build.', 'offline-unused-key', threading.Event(), print, binary=binary or codex_runner.ROOT/'tools/codex/codex')
            except RuntimeError as error:
                print('Kontrola braku modelu:', str(error), flush=True)
        if build:
            if len(fixture.seen)!=5 or not (folder/'agent-outcome.json').is_file():
                raise RuntimeError('Codex nie ukonczyl rzeczywistej budowy, renderow i eksportow przez MCP.')
            report=json.loads((folder/'result.json').read_text())
            if report.get('triangles',0)<=0 or not (folder/'model.fbx').is_file():
                raise RuntimeError('Brak rzeczywistego modelu/FBX z testu.')
            execution=json.loads((folder/'agent-execution.json').read_text())
            if not fixture.error_received or execution.get('failed_calls')!=1:
                raise RuntimeError('Brak zapisanego rzeczywistego bledu Code Mode i jego naprawy.')
            print('CODEX_EXECUTION_ERROR_RECOVERY_OK; real ReferenceError, store/load, then Blender build',flush=True)
            print('CODEX_MCP_BLENDER_BUILD_OK; real GLB, texture, 3 renders and FBX; fixture model responses; no paid API',flush=True)
        elif len(fixture.seen) != 2 or not result_verified(fixture.seen[-1], fixture.token):
            raise RuntimeError('Nie przeszedl test Codex -> Code Mode -> Blender MCP -> odpowiedz. Platne API nie bylo wywolywane.')
        if not build and (folder/'model.glb').exists(): raise RuntimeError('Test polaczenia nie powinien tworzyc modelu.')
        codex_runner.write(codex_runner.ROOT/'tools/codex/verified.json', {'sources':{name:hashlib.sha256((codex_runner.ROOT/name).read_bytes()).hexdigest() for name in ('codex_runner.py','blender_mcp.py')}, 'cli_mcp_roundtrip':True, 'code_mode_roundtrip':True, 'blender_build_roundtrip':build})
        passed = True
        print('CODEX_MCP_REAL_CLI_ROUNDTRIP_OK; 6 narzedzi, rzeczywisty wynik MCP; bez platnego API', flush=True)
    except Exception:
        # Keep only safe execution metadata after the updater restores old code.
        destination = codex_runner.ROOT/'state/diagnostics'/('codex-'+folder.name)
        destination.mkdir(parents=True, exist_ok=True, mode=0o700)
        for name in ('codex-events.jsonl','agent-usage.json','agent-tools.json','agent-execution.json'):
            if (folder/name).is_file(): shutil.copy2(folder/name,destination/name)
        print('Diagnostyka:',destination,flush=True)
        if (folder/'codex-events.jsonl').is_file(): print((folder/'codex-events.jsonl').read_text()[-6000:],flush=True)
        if (folder/'codex-stderr.log').is_file(): print(codex_runner.safe_message((folder/'codex-stderr.log').read_text()[-1800:]),flush=True)
        raise
    finally:
        shutil.rmtree(folder)
    return passed


if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--build',action='store_true');parser.add_argument('--test-blender')
    args=parser.parse_args();main(build=args.build,test_blender=args.test_blender)
