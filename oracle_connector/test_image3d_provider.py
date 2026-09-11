"""Offline protocol tests; these are not neural-generation or likeness results."""
import base64
import io
import json
from pathlib import Path
import struct
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch

import image3d_provider as provider


def protocol_glb(**overrides):
    data = {'asset': {'version': '2.0'}, 'meshes': [{}], 'images': [{'bufferView': 0}],
            'textures': [{'source': 0}], **overrides}
    raw = json.dumps(data).encode()
    raw += b' ' * (-len(raw) % 4)
    return struct.pack('<5I', 0x46546C67, 2, 20 + len(raw), len(raw), 0x4E4F534A) + raw


class Image3DTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.folder = Path(self.temporary.name)
        self.photos = [{'view': 'front', 'name': 'reference.jpg', 'bytes': b'first-subject-image'}]
        self.settings = {'provider': 'meshy', 'api_key': 'test-key-is-never-a-real-credential', 'texture_resolution': '8k'}
        self.cancel = threading.Event()
        self.done = {'status': 'SUCCEEDED', 'consumed_credits': 40,
                     'model_urls': {'glb': 'https://assets.meshy.ai/model.glb?private-signature=test'},
                     'texture_urls': []}
        self.transport = Mock(side_effect=[{'result': 'task-123'}, self.done])
        self.download = Mock(side_effect=lambda url, path, cancel: path.write_bytes(protocol_glb()))

    def tearDown(self):
        self.temporary.cleanup()

    def run_job(self, **kwargs):
        return provider.generate(self.photos, self.settings, self.folder, self.cancel,
            Mock(), transport=kwargs.pop('transport', self.transport),
            download_asset=kwargs.pop('download_asset', self.download), **kwargs)

    def test_different_subjects_send_their_own_image_bytes(self):
        for data in (b'woman-in-emerald-dress', b'other-model-short-red-hair', b'ceramic-coffee-cup'):
            with self.subTest(data=data):
                _, payload = provider.make_payload([{'view': 'front', 'bytes': data}], self.settings)
                self.assertEqual(base64.b64decode(payload['image_url'].split(',')[1]), data)
                self.assertEqual(payload['texture_image_url'], payload['image_url'])
                self.assertEqual(payload['ai_model'], 'meshy-7')
                self.assertTrue(payload['ultra_mode'])
                self.assertTrue(payload['enable_pbr'])
                self.assertFalse(payload['should_remesh'])
                self.assertFalse(payload['image_enhancement'])
                self.assertEqual(payload['pose_mode'], '')
                self.assertNotIn('texture_prompt', payload)

    def test_multiview_front_is_primary_and_all_photos_are_retained(self):
        photos = [{'view': view, 'bytes': view.encode(), 'subject': 'same person'} for view in ('back', 'front', 'side')]
        endpoint, payload = provider.make_payload(photos, self.settings)
        self.assertEqual(endpoint, 'multi-image-to-3d')
        self.assertEqual([base64.b64decode(x.split(',')[1]) for x in payload['image_urls']], [b'front', b'back', b'side'])
        self.assertEqual(payload['image_urls'], payload['texture_image_urls'])

    def test_different_people_are_not_blended_into_one_model(self):
        with self.assertRaisesRegex(provider.Image3DError, 'osobnym'):
            provider.make_payload([{'view': 'front', 'bytes': b'a', 'subject': 'Anna'},
                                   {'view': 'front', 'bytes': b'b', 'subject': 'Maria'}], self.settings)

    def test_missing_key_cannot_submit_or_make_template(self):
        self.settings.pop('api_key')
        with self.assertRaisesRegex(provider.Image3DError, 'Podlacz Meshy'):
            self.run_job()
        self.transport.assert_not_called()
        self.assertFalse((self.folder / 'image3d-task.json').exists())

    def test_success_retains_original_bytes_and_truthful_provenance(self):
        report = self.run_job()
        self.assertEqual((self.folder / 'model-master.glb').read_bytes(), protocol_glb())
        self.assertEqual(report['task_id'], 'task-123')
        self.assertFalse(report['likeness_verified'])
        self.assertFalse(report['remeshed'])
        self.assertEqual(report['consumed_credits'], 40)
        saved = (self.folder / 'image3d-task.json').read_text() + (self.folder / 'image3d-manifest.json').read_text()
        self.assertNotIn(self.settings['api_key'], saved)
        self.assertNotIn('private-signature', saved)
        self.assertNotIn('data:image', saved)

    def test_ambiguous_paid_post_never_repeats_on_resume(self):
        self.transport.side_effect = TimeoutError('response lost')
        with self.assertRaisesRegex(provider.Image3DError, 'Nie potwierdzono'):
            self.run_job()
        with self.assertRaisesRegex(provider.Image3DError, 'drugi|drugiej'):
            self.run_job()
        self.assertEqual(self.transport.call_count, 1)

    def test_poll_and_export_retry_reuse_remote_task_without_new_post(self):
        self.download.side_effect = provider.Image3DError('download interrupted')
        with self.assertRaisesRegex(provider.Image3DError, 'download interrupted'):
            self.run_job()
        self.transport.reset_mock(side_effect=True)
        self.transport.return_value = self.done
        self.download.side_effect = lambda url, path, cancel: path.write_bytes(protocol_glb())
        self.run_job()
        self.assertEqual([c.args[0] for c in self.transport.call_args_list], ['GET'])
        self.assertEqual(self.transport.call_args.args[1], 'image-to-3d/task-123')

    def test_changed_input_does_not_reuse_or_buy_another_subject(self):
        self.run_job()
        self.photos[0]['bytes'] = b'another-subject'
        self.transport.reset_mock()
        with self.assertRaisesRegex(provider.Image3DError, 'innych zdjec'):
            self.run_job()
        self.transport.assert_not_called()

    def test_cancel_before_submit_costs_no_request(self):
        self.cancel.set()
        with self.assertRaises(InterruptedError):
            self.run_job()
        self.transport.assert_not_called()

    def test_poll_timeout_keeps_id_for_free_resume(self):
        with self.assertRaisesRegex(provider.Image3DError, 'Wznow'):
            self.run_job(timeout=0)
        self.assertEqual(json.loads((self.folder / 'image3d-task.json').read_text())['id'], 'task-123')
        self.assertEqual(self.transport.call_count, 1)

    def test_terminal_failure_does_not_download_or_substitute(self):
        self.transport.side_effect = [{'result': 'task-123'}, {'status': 'FAILED', 'task_error': {'message': 'private payload'}}]
        with self.assertRaisesRegex(provider.Image3DError, 'FAILED') as caught:
            self.run_job()
        self.assertNotIn('private payload', str(caught.exception))
        self.download.assert_not_called()
        self.assertFalse((self.folder / 'model.glb').exists())

    def test_readonly_key_check_is_not_a_generation(self):
        with patch.object(provider, 'request', return_value=[]) as request:
            provider.verify_key('test-credential-for-offline-only')
        self.assertEqual(request.call_args.args[:2], ('GET', 'image-to-3d?page_size=1'))

    def test_rejects_external_glb_dependencies(self):
        path = self.folder / 'foreign.glb'
        for uri in ('file:///etc/passwd', '../../outside.png', 'https://example.com/x.png'):
            path.write_bytes(protocol_glb(images=[{'uri': uri}]))
            with self.assertRaisesRegex(provider.Image3DError, 'zewnetrznego'):
                provider.validate_glb(path)

    def test_rejects_wrong_asset_origin_before_download(self):
        for url in ('http://assets.meshy.ai/a', 'https://127.0.0.1/a', 'https://assets.meshy.ai.evil.test/a',
                    'https://user:secret@assets.meshy.ai/a', 'file:///etc/passwd'):
            with self.subTest(url=url), self.assertRaises(provider.Image3DError):
                provider.asset_url(url)

    def test_texture_dimensions_are_measured_not_claimed_from_setting(self):
        self.done['texture_urls'] = [{'base_color': 'https://assets.meshy.ai/base.png'}]
        def download(url, path, cancelled):
            path.write_bytes(protocol_glb() if path.suffix == '.glb' else b'\x89PNG\r\n\x1a\n' + b'\x00\x00\x00\rIHDR' + struct.pack('>II', 2048, 1024) + b'\0'*30)
        report = self.run_job(download_asset=download)
        self.assertEqual(report['requested_texture_resolution'], '8k')
        self.assertEqual(report['textures'][0]['size'], [2048, 1024])
        self.assertFalse(report['textures'][0]['pixels_resampled'])


if __name__ == '__main__':
    unittest.main()
