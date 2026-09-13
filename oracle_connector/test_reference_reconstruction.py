"""CPU regression tests for reference policy; fixtures are not visual benchmarks."""
import copy
import ast
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
import struct
import zlib

sys.path.insert(0, str(Path(__file__).parent/'runtime'))
from reference_reconstruction import (validate_spec, compare_measurements,
    expected_globes, chess512_checks, review_report, REQUIRED_VIEWS, board_checks, board_review_report, refresh_review)


def specimen():
    return {'revision': 1, 'reference_image': 'reference.png', 'reference_sha256': hashlib.sha256(png_fixture()).hexdigest(), 'age_group': 'adult', 'age_evidence': 'adult fictional character requested',
            'image_sides': 'frontal_unmirrored',
            'eyes': {'anatomical_left': 'recessed_eye_in_bone', 'anatomical_right': 'living_eye'},
            'measurements': [{'name': 'head_width_height_ratio', 'reference': .68,
                              'candidate': .69, 'tolerance': .025, 'unit': 'ratio',
                              'evidence': 'synthetic test fixture, not measured E17'}]}


def png_fixture(width=128, height=128):
    def chunk(kind, data):
        return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    pixels = b''.join(b'\0'+bytes((x+y)%256 for x in range(width)) for y in range(height))
    return (b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,0,0,0,0))
            +chunk(b'IDAT',zlib.compress(pixels))+chunk(b'IEND',b''))


def board_fixture(levels=1):
    spec={'revision':1,'size':[8,8,levels],'origin':[0.,0.,0.],'spacing':[.1,.1,.3],
          'position_tolerance':.001,'color_tolerance':.01,
          'palette':{'light':{'material':'ivory','linear_rgb':[.8,.75,.6]},
                     'dark':{'material':'ebony','linear_rgb':[.03,.02,.01]}}}
    cells=[]
    for z in range(levels):
        for y in range(8):
            for x in range(8):
                m=spec['palette']['light' if ((x+y+z)&1)==0 else 'dark']
                cells.append(dict(x=x,y=y,z=z,index=x+8*(y+8*z),center=[x*.1,y*.1,z*.3],
                                  materials=[{'name':m['material'],'linear_rgb':m['linear_rgb'][:]}]))
    return spec,cells


class ReconstructionTests(unittest.TestCase):
    def test_skeletal_eye_is_not_missing(self):
        self.assertEqual(expected_globes(specimen()), 2)
        spec = specimen(); spec['eyes']['anatomical_left'] = 'empty_socket'
        self.assertEqual(expected_globes(spec), 1)
        spec['eyes']['anatomical_left'] = 'occluded'
        self.assertEqual(expected_globes(spec), 2)

    def test_grey_hair_cannot_supply_age(self):
        spec = specimen(); spec['age_evidence'] = ''
        with self.assertRaises(ValueError): validate_spec(spec)
        spec['age_group'] = 'unknown'
        validate_spec(spec)

    def test_head_enlargement_regression(self):
        spec = specimen(); spec['measurements'][0]['candidate'] = .85
        self.assertFalse(compare_measurements(spec)[0]['passed'])

    def test_nan_and_duplicate_measurements_rejected(self):
        spec = specimen(); spec['measurements'][0]['candidate'] = float('nan')
        with self.assertRaises(ValueError): validate_spec(spec)
        spec = specimen(); spec['measurements'] *= 2
        with self.assertRaises(ValueError): validate_spec(spec)

    def test_board_parity_includes_height(self):
        cells = [dict(x=x,y=y,z=z,index=x+8*(y+8*z),light=((x+y+z)&1)==0)
                 for z in range(8) for y in range(8) for x in range(8)]
        self.assertTrue(chess512_checks(cells)['passed'])
        wrong = copy.deepcopy(cells)
        for c in wrong: c['light'] = ((c['x']+c['y'])&1)==0
        self.assertIn('parity', chess512_checks(wrong)['failures'])
        cells[-1] = cells[0]
        self.assertIn('duplicate', chess512_checks(cells)['failures'])

    def test_actual_board_64_and_512_contracts(self):
        for levels in (1,8):
            spec,cells=board_fixture(levels)
            result=board_checks(cells,spec)
            self.assertTrue(result['passed'])
            self.assertEqual(result['actual_cells'],64*levels)
            cells[1]['index']=True
            self.assertIn('index',board_checks(cells,spec)['failures'])

    def test_actual_board_material_color_position_and_duplicate(self):
        spec,cells=board_fixture(8)
        cells[64]['materials']=copy.deepcopy(cells[0]['materials'])
        result=board_checks(cells,spec)
        self.assertIn('material_parity',result['failures'])
        self.assertIn('material_color',result['failures'])
        spec,cells=board_fixture()
        cells[3]['center'][0]+=.04
        cells[-1]=cells[0]
        result=board_checks(cells,spec)
        self.assertTrue({'cell_position','duplicate','cell_count'}.issubset(result['failures']))

    def test_board_missing_and_textured_color_are_unverified(self):
        spec,cells=board_fixture()
        self.assertFalse(board_checks([],spec)['passed'])
        self.assertEqual(board_checks([],spec)['status'],'unverified')
        cells[0]['materials'][0]['linear_rgb']=None
        self.assertIn('texture_color_requires_render_review',board_checks(cells,spec)['unverified'])
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(board_review_report(td,[])['status'],'unverified')

    def test_export_is_only_a_draft_without_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            folder = Path(td); (folder/'model.glb').write_bytes(b'test-model')
            report = review_report(folder, {})
            self.assertEqual(report['status'], 'needs_correction')
            self.assertFalse(report['catalogue_accepted'])
            self.assertFalse(report['training']['weights_updated'])

    def test_current_complete_review_cannot_auto_accept_likeness(self):
        with tempfile.TemporaryDirectory() as td:
            folder = Path(td); payload = b'test-model'; (folder/'model.glb').write_bytes(payload)
            sha = hashlib.sha256(payload).hexdigest()
            (folder/'reference-spec.json').write_text(json.dumps(specimen()))
            (folder/'reference.png').write_bytes(png_fixture())
            (folder/'review').mkdir()
            # Valid synthetic PNGs exercise file integrity, not model image QA.
            for view in REQUIRED_VIEWS:
                (folder/'review'/('reference-'+view+'.png')).write_bytes(png_fixture())
            evidence = {'model_sha256': sha, 'reference_sha256': specimen()['reference_sha256'], 'reimport_verified': True,
                        'same_camera_as_baseline': True, 'critical_defects': [],
                        'views': {v: {'model_sha256': sha, 'reference_sha256': specimen()['reference_sha256'], 'image_sha256': hashlib.sha256((folder/'review'/('reference-'+v+'.png')).read_bytes()).hexdigest(), 'nonempty_verified': True} for v in REQUIRED_VIEWS}}
            (folder/'reference-evidence.json').write_text(json.dumps(evidence))
            export = {'portrait_quality': {'structural_checks_passed': True, 'actual': {'heads': 1, 'eyes': 2}},
                      'reference_socket_checks': {'passed': True}}
            report = review_report(folder, export)
            self.assertEqual(report['status'], 'ready_for_human_review')
            self.assertFalse(report['likeness_verified'])
            evidence['views']['front']['image_sha256'] = '0'*64
            (folder/'reference-evidence.json').write_text(json.dumps(evidence))
            self.assertIn('view_missing_or_unverified:front',review_report(folder,export)['failures'])
            (folder/'model.glb').write_bytes(b'edited-model')
            self.assertIn('stale_or_missing_review', review_report(folder, export)['failures'])

    def test_corrupt_and_oversized_sidecars_preserve_draft(self):
        with tempfile.TemporaryDirectory() as td:
            folder = Path(td); model = folder/'model.glb'; model.write_bytes(b'draft')
            for data in ('{broken', ' '*256001, '[]', '{"revision":1,"age_group": "adult", "age_evidence": 4}'):
                (folder/'reference-spec.json').write_text(data)
                report = review_report(folder,{})
                self.assertEqual(report['status'],'needs_correction')
                self.assertIn('invalid_reconstruction_sidecar', report['failures'])
                self.assertTrue(report['validation_errors'])
                self.assertEqual(model.read_bytes(),b'draft')
            model.unlink()
            with self.assertRaises(FileNotFoundError): review_report(folder,{})

    def test_png_container_and_minimum_resolution(self):
        from reference_reconstruction import _png_dimensions
        self.assertEqual(_png_dimensions(png_fixture()),[128,128])
        self.assertIsNone(_png_dimensions(png_fixture(127,128)))
        self.assertIsNone(_png_dimensions(b'\x89PNG\r\n\x1a\n'+b'0'*200))
        corrupted=bytearray(png_fixture()); corrupted[50]^=1
        self.assertIsNone(_png_dimensions(bytes(corrupted)))
        self.assertIsNone(_png_dimensions(png_fixture()[:-12]))

    def test_reference_changed_missing_and_unsafe_path(self):
        with tempfile.TemporaryDirectory() as td:
            folder=Path(td);(folder/'model.glb').write_bytes(b'draft')
            spec=specimen();(folder/'reference-spec.json').write_text(json.dumps(spec))
            reference=folder/'reference.png';reference.write_bytes(png_fixture())
            (folder/'reference-evidence.json').write_text(json.dumps({'reference_sha256':spec['reference_sha256']}))
            self.assertNotIn('reference_hash_mismatch',review_report(folder,{})['failures'])
            reference.write_bytes(png_fixture(129,128))
            result=review_report(folder,{})
            self.assertIn('reference_hash_mismatch',result['failures'])
            self.assertIn('stale_or_missing_reference_review',result['failures'])
            reference.unlink()
            self.assertIn('reference_image_unverified',review_report(folder,{})['failures'])
            reference.symlink_to(folder/'model.glb')
            result=review_report(folder,{})
            self.assertIn('reference_image_unverified',result['failures'])
            self.assertTrue(any(e['message']=='reference_image_symlink' for e in result['validation_errors']))
            spec['reference_image']='../reference.png'
            with self.assertRaises(ValueError):validate_spec(spec)

    def test_refresh_writes_latest_evidence_without_catalogue_acceptance(self):
        with tempfile.TemporaryDirectory() as td:
            folder=Path(td);payload=b'model';(folder/'model.glb').write_bytes(payload)
            sha=hashlib.sha256(payload).hexdigest();spec=specimen()
            (folder/'reference.png').write_bytes(png_fixture())
            (folder/'reference-spec.json').write_text(json.dumps(spec))
            export={'portrait_quality':{'structural_checks_passed':True,'actual':{'heads':1,'eyes':2}},
                    'reference_socket_checks':{'passed':True},'custom_metadata':'preserve'}
            (folder/'result.json').write_text(json.dumps(export))
            self.assertEqual(refresh_review(folder)['status'],'needs_correction')
            (folder/'review').mkdir()
            views={}
            for view in REQUIRED_VIEWS:
                data=png_fixture();(folder/'review'/('reference-'+view+'.png')).write_bytes(data)
                views[view]={'model_sha256':sha,'reference_sha256':spec['reference_sha256'],
                             'image_sha256':hashlib.sha256(data).hexdigest(),'nonempty_verified':True}
            evidence={'model_sha256':sha,'reference_sha256':spec['reference_sha256'],
                      'reimport_verified':True,'same_camera_as_baseline':True,'critical_defects':[],'views':views}
            (folder/'reference-evidence.json').write_text(json.dumps(evidence))
            review=refresh_review(folder)
            self.assertEqual(review['status'],'ready_for_human_review')
            result=json.loads((folder/'result.json').read_text())
            self.assertEqual(result['reconstruction_review'],json.loads((folder/'reconstruction-review.json').read_text()))
            self.assertEqual(result['custom_metadata'],'preserve')
            self.assertFalse(review['catalogue_accepted']);self.assertFalse(review['likeness_verified'])
            (folder/'model.glb').write_bytes(b'changed')
            self.assertIn('stale_or_missing_review',refresh_review(folder)['failures'])

    def test_planner_policy_is_actually_loaded(self):
        from scene_contract import PROMPT
        self.assertIn('REFERENCE RECONSTRUCTION / E17', PROMPT)
        self.assertIn('not empty_socket', PROMPT)

    def test_updater_includes_new_runtime_dependency(self):
        path=Path(__file__).parent/'apply_update.py'
        tree=ast.parse(path.read_text())
        assignments=[]
        for node in tree.body:
            target=node.targets[0] if isinstance(node,ast.Assign) else node.target if isinstance(node,ast.AugAssign) else None
            if isinstance(target,ast.Name) and target.id in ('FILES','ASSETS'):
                assignments.append(node)
        namespace={'__builtins__':{'tuple':tuple}}
        exec(compile(ast.Module(body=assignments,type_ignores=[]),str(path),'exec'),namespace)
        self.assertEqual(namespace['FILES'].count('runtime/reference_reconstruction.py'),1)
        self.assertTrue((path.parent/'runtime/reference_reconstruction.py').is_file())


if __name__ == '__main__': unittest.main()
