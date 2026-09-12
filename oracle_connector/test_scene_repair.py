import json
import unittest
from copy import deepcopy
from unittest.mock import patch
from pathlib import Path

import openai_provider
import server
from scene_repair import photo_schema, apply_replacements, repairable_scene
from runtime.scene_contract import SCHEMA, validate_scene, load_scene_json
from test_timeout_recovery import WorkerTimeoutTests, JOB


def fixture():
    return {'version':2,'name':'Tube','subject_type':'object','reference_views':[],
        'materials':[{'name':'blue','rgb':[0,.2,.8],'pattern':'plain','roughness':.5,'metallic':0,'emission':0}],
        'parts':[{'kind':'tube','name':'tube','material':'blue','points':[[0,0,0],[0,0,0],[0,0,2]],'radii':[.1,.1,.1],'sides':16}]}


class RepairTests(unittest.TestCase):
    def test_complete_large_plan_can_be_repaired_but_oversized_input_is_bounded(self):
        text = json.dumps(fixture()) + ' ' * 90000
        self.assertEqual(repairable_scene(text), fixture())
        self.assertEqual(load_scene_json(text), fixture())
        with self.assertRaises(ValueError): load_scene_json(text + ' ' * 256000)

    def test_photo_constraints_are_in_the_response_schema_without_mutating_legacy(self):
        schema=photo_schema(1)
        self.assertEqual(schema['properties']['version']['enum'],[2])
        self.assertEqual(schema['properties']['reference_views']['minItems'],1)
        self.assertEqual(schema['properties']['reference_views']['items']['properties']['photo_index']['maximum'],0)
        self.assertEqual(SCHEMA['properties']['reference_views']['minItems'],0)
        self.assertEqual(photo_schema(0),SCHEMA)

    def test_repairs_only_specified_fields_and_preserves_original(self):
        original=fixture();saved=deepcopy(original)
        with self.assertRaises(ValueError):validate_scene(deepcopy(original))
        repaired=apply_replacements(original,json.dumps({'changes':[{'path':'/parts/0/points/1','value_json':'[0,0,1]'}]}))
        validate_scene(repaired)
        self.assertEqual(original,saved)
        repaired['parts'][0]['points'][1]=saved['parts'][0]['points'][1]
        self.assertEqual(repaired,saved)

    def test_repair_cannot_replace_parts_or_identity_or_add_arbitrary_fields(self):
        for path in ('/parts','/parts/0','/parts/0/name','/parts/0/kind','/parts/99/points','/config/api_key'):
            with self.subTest(path=path),self.assertRaises(ValueError):
                apply_replacements(fixture(),json.dumps({'changes':[{'path':path,'value_json':'[]'}]}))
        self.assertIsNone(repairable_scene('{"parts": ['))

    def test_repair_uses_astra_with_a_smaller_output_and_reasoning_budget(self):
        with patch.object(openai_provider,'stream_chat',return_value='{}') as stream:
            openai_provider.generate([{'content':[{'type':'input_image','image_url':'fixture'}]}],
                'fixture',None,None,250,None,None,purpose='repair')
        payload=stream.call_args.args[1]
        self.assertEqual(payload['model'],'gpt-6-astra')
        self.assertEqual(payload['reasoning']['effort'],'low')
        self.assertEqual(payload['max_output_tokens'],9000)


class RepairWorkerTests(WorkerTimeoutTests):
    def test_validation_retry_uses_field_patch_and_builds_preserved_scene(self):
        raw=json.dumps(fixture());correction=json.dumps({'changes':[{'path':'/parts/0/points/1','value_json':'[0,0,1]'}]})
        with server.database() as db:db.execute('INSERT INTO jobs VALUES (?,?,?,?,0,0)',(JOB,'Tube','queued',''))
        with patch.object(server,'WAKE') as wake,patch.object(server,'verify_runtime'), \
             patch.object(server,'ai_settings',return_value={'provider':'openai','api_key':'fixture'}), \
             patch.object(server,'generate_code',side_effect=[raw,correction]) as generate, \
             patch.object(server,'run_blender') as build:
            wake.wait.side_effect=[None,StopIteration]
            with self.assertRaises(StopIteration):server.worker()
        self.assertEqual(generate.call_count,2);build.assert_called_once()
        self.assertEqual(generate.call_args.kwargs['purpose'],'repair')
        self.assertIn('COMPLETE SCENE DATA',generate.call_args.args[0][-1]['content'])
        stored=json.loads((server.JOBS/JOB/'scene.json').read_text())
        self.assertEqual(stored['parts'][0]['points'][1],[0,0,1])
        with server.database() as db:row=db.execute('SELECT state FROM jobs WHERE id=?',(JOB,)).fetchone()
        self.assertEqual(row['state'],'succeeded')


if __name__=='__main__':unittest.main()
