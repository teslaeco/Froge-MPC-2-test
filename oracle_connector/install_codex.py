"""Install a pinned official Codex executable; never runs a paid AI request."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import tarfile
import tempfile
import time
import urllib.request

VERSION = '0.154.0'
HOST_DIGESTS = {
    'x86_64': 'a68df7cca23c6da7cde175677df7de61c73a234add1333a1254b86d641af01f7',
    'aarch64': '20aefa302c2022b496e32911bf954a5f76c7fd749c6bdb9fbd711e32b66dcbfa',
}
RELEASES = {
    'x86_64': ('x86_64', 'd7e18b2597ae8f242f5f31ee9e90deef48dbc9edd634d9868fb6435d08c07f02'),
    'aarch64': ('aarch64', '583b48df32804213bdcd338c2e5adb06b34340821fa757a726cc0a524fa33c27'),
}


def install(destination):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True, mode=0o700)
    executable = destination / 'codex'
    if executable.is_file():
        result = subprocess.run([str(executable), '--version'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and result.stdout.strip() == 'codex-cli ' + VERSION:
            install_host(destination)
            return executable
    machine = platform.machine()
    if machine not in RELEASES:
        raise RuntimeError('Codex wymaga Linux x86_64 lub aarch64.')
    arch, digest = RELEASES[machine]
    name = 'codex-' + arch + '-unknown-linux-musl'
    url = 'https://github.com/openai/codex/releases/download/rust-v' + VERSION + '/' + name + '.tar.gz'
    print('Pobieram oficjalny Codex ' + VERSION + '; bez wywolywania API.', flush=True)
    started = time.monotonic()
    with tempfile.TemporaryDirectory(dir=destination) as temporary:
        archive = Path(temporary) / 'codex.tar.gz'
        checksum = hashlib.sha256()
        with urllib.request.urlopen(url, timeout=30) as response, archive.open('wb') as target:
            size = 0
            while chunk := response.read(1024 * 1024):
                size += len(chunk)
                if size > 200 * 1024**2 or time.monotonic() - started > 240:
                    raise RuntimeError('Pobieranie Codexa przekroczylo limit. Dotychczasowy generator zachowany.')
                target.write(chunk); checksum.update(chunk)
        if checksum.hexdigest() != digest:
            raise RuntimeError('Suma kontrolna oficjalnej paczki Codex nie zgadza sie. Nie uruchomiono jej.')
        with tarfile.open(archive, 'r:gz') as package:
            member = package.getmember(name)
            if not member.isfile() or member.size > 300 * 1024**2:
                raise RuntimeError('Nieprawidlowy plik Codexa.')
            incoming = Path(temporary) / 'codex'
            with package.extractfile(member) as source, incoming.open('wb') as target:
                while chunk := source.read(1024 * 1024): target.write(chunk)
            os.chmod(incoming, 0o700)
            result = subprocess.run([str(incoming), '--version'], capture_output=True, text=True, timeout=10)
            if result.returncode or result.stdout.strip() != 'codex-cli ' + VERSION:
                raise RuntimeError('Codex nie uruchamia sie na tym serwerze.')
            incoming.replace(executable)
    install_host(destination)
    print('FROGE_CODEX_READY ' + VERSION, flush=True)
    return executable


def install_host(destination):
    """Install the separate, checksum-pinned JS runtime required by Astra."""
    machine = platform.machine()
    if machine not in HOST_DIGESTS:
        raise RuntimeError('Code Mode wymaga Linux x86_64 lub aarch64.')
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True, mode=0o700)
    executable = destination / 'codex-code-mode-host'
    receipt = destination / 'code-mode-host.json'
    digest = HOST_DIGESTS[machine]
    try:
        installed = json.loads(receipt.read_text())
        if installed.get('release_sha256') == digest and installed.get('binary_sha256') == hashlib.sha256(executable.read_bytes()).hexdigest() and os.access(executable, os.X_OK):
            return executable
    except (OSError, ValueError):
        pass
    name = 'codex-code-mode-host-' + machine + '-unknown-linux-musl'
    url = 'https://github.com/openai/codex/releases/download/rust-v' + VERSION + '/' + name + '.tar.gz'
    print('Pobieram brakujacy Code Mode host ' + VERSION + '; bez API.', flush=True)
    started = time.monotonic()
    with tempfile.TemporaryDirectory(dir=destination) as temporary:
        archive = Path(temporary) / 'host.tar.gz'
        checksum = hashlib.sha256(); size = 0
        with urllib.request.urlopen(url, timeout=30) as response, archive.open('wb') as target:
            while chunk := response.read(1024 * 1024):
                size += len(chunk)
                if size > 100 * 1024**2 or time.monotonic() - started > 240:
                    raise RuntimeError('Pobieranie Code Mode przekroczylo limit; stary kod zachowany.')
                target.write(chunk); checksum.update(chunk)
        if checksum.hexdigest() != digest:
            raise RuntimeError('Nieprawidlowa suma kontrolna Code Mode; nie uruchomiono pliku.')
        with tarfile.open(archive, 'r:gz') as package:
            member = package.getmember(name)
            if not member.isfile() or member.size > 300 * 1024**2:
                raise RuntimeError('Nieprawidlowy plik Code Mode.')
            incoming = Path(temporary) / 'host'
            with package.extractfile(member) as source, incoming.open('wb') as target:
                while chunk := source.read(1024 * 1024): target.write(chunk)
        binary_digest = hashlib.sha256(incoming.read_bytes()).hexdigest()
        os.chmod(incoming, 0o700)
        incoming.replace(executable)
        pending = receipt.with_suffix('.pending')
        pending.write_text(json.dumps({'version': VERSION, 'release_sha256': digest, 'binary_sha256': binary_digest}))
        os.chmod(pending, 0o600); pending.replace(receipt)
    print('FROGE_CODE_MODE_HOST_READY ' + VERSION, flush=True)
    return executable


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--destination', type=Path, default=Path(__file__).resolve().parent / 'tools' / 'codex')
    args = parser.parse_args()
    install(args.destination)
