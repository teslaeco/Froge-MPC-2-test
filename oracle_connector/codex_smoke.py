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


def main(binary=None):
    folder = codex_runner.ROOT/'state/jobs'/str(uuid.uuid4()); folder.mkdir(parents=True)
    fixture = Fixture(uuid.uuid4().hex)
    passed = False
    try:
        with patch('codex_runner.urllib.request.build_opener', return_value=fixture), patch.object(codex_runner,'MAX_SECONDS',50):
            try:
                codex_runner.run(folder,'Offline connection test','Read get_current_model; do not build.', 'offline-unused-key', threading.Event(), print, binary=binary or codex_runner.ROOT/'tools/codex/codex')
            except RuntimeError as error:
                print('Kontrola braku modelu:', str(error), flush=True)
        if len(fixture.seen) != 2 or not result_verified(fixture.seen[-1], fixture.token):
            raise RuntimeError('Nie przeszedl test Codex -> Code Mode -> Blender MCP -> odpowiedz. Platne API nie bylo wywolywane.')
        if (folder/'model.glb').exists(): raise RuntimeError('Test polaczenia nie powinien tworzyc modelu.')
        codex_runner.write(codex_runner.ROOT/'tools/codex/verified.json', {'sources':{name:hashlib.sha256((codex_runner.ROOT/name).read_bytes()).hexdigest() for name in ('codex_runner.py','blender_mcp.py')}, 'cli_mcp_roundtrip':True, 'code_mode_roundtrip':True})
        passed = True
        print('CODEX_MCP_REAL_CLI_ROUNDTRIP_OK; 6 narzedzi, rzeczywisty wynik MCP; bez platnego API', flush=True)
    except Exception:
        # Keep only safe execution metadata after the updater restores old code.
        destination = codex_runner.ROOT/'state/diagnostics'/('codex-'+folder.name)
        destination.mkdir(parents=True, exist_ok=True, mode=0o700)
        for name in ('codex-events.jsonl','agent-usage.json'):
            if (folder/name).is_file(): shutil.copy2(folder/name,destination/name)
        print('Diagnostyka:',destination,flush=True)
        if (folder/'codex-events.jsonl').is_file(): print((folder/'codex-events.jsonl').read_text()[-6000:],flush=True)
        if (folder/'codex-stderr.log').is_file(): print(codex_runner.safe_message((folder/'codex-stderr.log').read_text()[-1800:]),flush=True)
        raise
    finally:
        shutil.rmtree(folder)
    return passed


if __name__ == '__main__': main()
