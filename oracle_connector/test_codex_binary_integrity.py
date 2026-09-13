"""Pinned executable and readiness regressions; local archives, no AI/network."""
import hashlib
import io
import json
import os
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch

import codex_runner
import install_codex


def archive(name, data):
    output=io.BytesIO()
    with tarfile.open(fileobj=output,mode='w:gz') as package:
        member=tarfile.TarInfo(name);member.size=len(data);member.mode=0o700
        package.addfile(member,io.BytesIO(data))
    return output.getvalue()


class CodexBinaryIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.destination=self.root/'tools/codex'
        self.cli=b'#!/bin/sh\nprintf "codex-cli 0.154.0\\n"\n'
        self.host=b'fixture-code-mode-host-v1'
        self.cli_archive=archive('codex-x86_64-unknown-linux-musl',self.cli)
        self.host_archive=archive('codex-code-mode-host-x86_64-unknown-linux-musl',self.host)
        for name,value in [('platform.machine',lambda:'x86_64'),
                           ('RELEASES',{'x86_64':('x86_64',hashlib.sha256(self.cli_archive).hexdigest())}),
                           ('HOST_DIGESTS',{'x86_64':hashlib.sha256(self.host_archive).hexdigest()})]:
            patched=patch('install_codex.'+name,value);patched.start();self.addCleanup(patched.stop)
        install_codex._BINARY_DIGEST_CACHE.clear()

    def download(self,url,timeout):
        return io.BytesIO(self.host_archive if 'codex-code-mode-host-' in url else self.cli_archive)

    def install(self):
        with patch('install_codex.urllib.request.urlopen',side_effect=self.download) as download:
            result=install_codex.install(self.destination)
        self.assertEqual(download.call_count,2)
        return result

    def prepare_readiness(self):
        self.install()
        for name in ('codex_runner.py','blender_mcp.py'):(self.root/name).write_text('# Fixture source\n')
        sources={name:hashlib.sha256((self.root/name).read_bytes()).hexdigest()
                 for name in ('codex_runner.py','blender_mcp.py')}
        (self.destination/'verified.json').write_text(json.dumps({'sources':sources,'blender_build_roundtrip':True}))

    def test_pinned_install_records_extracted_hash_and_reuses_without_execution_or_download(self):
        path=self.install()
        receipt=json.loads((self.destination/'codex-binary.json').read_text())
        self.assertEqual(receipt['binary_sha256'],hashlib.sha256(self.cli).hexdigest())
        self.assertEqual(receipt['release_sha256'],hashlib.sha256(self.cli_archive).hexdigest())
        self.assertEqual(install_codex.verified_runtime(self.destination),path)
        with patch('install_codex.urllib.request.urlopen') as download,patch('install_codex.subprocess.run') as execute:
            self.assertEqual(install_codex.install(self.destination),path)
        download.assert_not_called();execute.assert_not_called()

    def test_version_only_existing_binary_is_reinstalled_without_running_untrusted_file(self):
        self.destination.mkdir(parents=True)
        existing=self.destination/'codex'
        existing.write_bytes(b'untrusted executable claiming the expected version');existing.chmod(0o700)
        import subprocess
        real_run=subprocess.run
        with patch('install_codex.urllib.request.urlopen',side_effect=self.download), \
                patch('install_codex.subprocess.run',wraps=real_run) as execute:
            install_codex.install(self.destination)
        self.assertEqual(existing.read_bytes(),self.cli)
        self.assertEqual(execute.call_count,1)
        self.assertNotEqual(execute.call_args.args[0][0],str(existing))
        self.assertTrue((self.destination/'codex-binary.json').is_file())

    def test_ready_rejects_missing_modified_or_non_executable_cli_and_host(self):
        self.prepare_readiness()
        with patch.object(codex_runner,'ROOT',self.root):
            self.assertEqual(codex_runner.executable(),self.destination/'codex')
            for name in ('codex','codex-code-mode-host'):
                path=self.destination/name;original=path.read_bytes();original_stat=path.stat()
                with self.subTest(name=name):
                    # Same length and restored mtime still invalidate the cache
                    # through ctime; merely printing --version is insufficient.
                    path.write_bytes(bytes([original[0]^1])+original[1:])
                    os.utime(path,ns=(original_stat.st_atime_ns,original_stat.st_mtime_ns))
                    self.assertIsNone(codex_runner.executable())
                    path.write_bytes(original);path.chmod(0o700)
                    self.assertIsNotNone(codex_runner.executable())
                    path.chmod(0o600);self.assertIsNone(codex_runner.executable())
                    path.chmod(0o700);path.unlink();self.assertIsNone(codex_runner.executable())
                    path.write_bytes(original);path.chmod(0o700)
                    self.assertIsNotNone(codex_runner.executable())

    def test_ready_rejects_missing_or_wrong_release_receipts_even_with_smoke_pass(self):
        self.prepare_readiness()
        with patch.object(codex_runner,'ROOT',self.root):
            for name in ('codex-binary.json','code-mode-host.json'):
                path=self.destination/name;original=path.read_bytes()
                with self.subTest(name=name):
                    path.unlink();self.assertIsNone(codex_runner.executable())
                    value=json.loads(original);value['release_sha256']='wrong-release'
                    path.write_text(json.dumps(value));self.assertIsNone(codex_runner.executable())
                    path.write_bytes(original);self.assertIsNotNone(codex_runner.executable())

    def test_unchanged_binary_digest_uses_stat_cache_and_changed_file_is_rehashed(self):
        self.install();install_codex._BINARY_DIGEST_CACHE.clear()
        path=self.destination/'codex'
        self.assertEqual(install_codex.binary_digest(path),hashlib.sha256(self.cli).hexdigest())
        with patch.object(Path,'open',side_effect=AssertionError('Unchanged binary read again')):
            self.assertEqual(install_codex.binary_digest(path),hashlib.sha256(self.cli).hexdigest())
        path.write_bytes(self.cli+b'# changed\n')
        self.assertEqual(install_codex.binary_digest(path),hashlib.sha256(self.cli+b'# changed\n').hexdigest())


if __name__=='__main__':unittest.main()
