"""Read local Ollama output with a total deadline and cancellable, visible waits."""
import json
import os
import selectors
import subprocess
import time


def stream_chat(url, payload, cancelled, progress, timeout=1800, interval=8):
    """Curl owns the socket; the worker can cancel even before HTTP headers arrive.

    There is deliberately no short inactivity timeout: loading/prefill on CPU may
    be silent. The entire request, including silent waits, has a fixed deadline.
    No prompts are placed in command-line arguments or diagnostic output.
    """
    if cancelled.is_set():
        raise InterruptedError('Zlecenie anulowane.')
    if timeout <= 0:
        raise TimeoutError('AI przekroczylo laczny limit 30 minut. Model nie zostal zapisany.')
    started = time.monotonic()
    last_data = started
    next_progress = started
    command = ['curl', '--silent', '--show-error', '--no-buffer', '--fail-with-body',
               '--noproxy', '*', '--connect-timeout', str(min(15, timeout)),
               '--max-time', str(timeout), '--header', 'Content-Type: application/json',
               '--data-binary', '@-', url]
    # Supply stdin from a temporary file, avoiding a blocking write to a full pipe.
    import tempfile
    with tempfile.TemporaryFile() as request_body:
        request_body.write(json.dumps(payload).encode())
        request_body.seek(0)
        process = subprocess.Popen(command, stdin=request_body, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        selector = selectors.DefaultSelector()
        selector.register(process.stdout, selectors.EVENT_READ, 'output')
        selector.register(process.stderr, selectors.EVENT_READ, 'error')
        pending = b''
        stderr = b''
        pieces = []
        characters = size = 0
        completed = False
        try:
            while selector.get_map():
                now = time.monotonic()
                if cancelled.is_set():
                    raise InterruptedError('Zlecenie anulowane.')
                if now - started >= timeout:
                    raise TimeoutError('AI przekroczylo laczny limit 30 minut. Model nie zostal zapisany.')
                if now >= next_progress:
                    progress(characters, now - started, now - last_data)
                    next_progress = now + interval
                wait = min(0.25, timeout - (now - started), max(0.001, next_progress - now))
                for key, _ in selector.select(wait):
                    data = os.read(key.fileobj.fileno(), 65536)
                    if not data:
                        selector.unregister(key.fileobj)
                        continue
                    if key.data == 'error':
                        stderr = (stderr + data)[-2000:]
                        continue
                    pending += data
                    while b'\n' in pending:
                        raw, pending = pending.split(b'\n', 1)
                        if len(raw) > 200000:
                            raise ValueError('Nieprawidlowa odpowiedz AI: zbyt duzy fragment.')
                        if not raw.strip():
                            continue
                        item = json.loads(raw)
                        if item.get('error'):
                            raise ValueError(str(item['error'])[:500])
                        content = item.get('message', {}).get('content', '')
                        if not isinstance(content, str):
                            raise ValueError('Nieprawidlowa odpowiedz AI.')
                        if content:
                            last_data = time.monotonic()
                            pieces.append(content)
                            characters += len(content)
                            size += len(content.encode())
                        if size > 80000:
                            raise ValueError('AI zwrocilo zbyt dlugi skrypt.')
                        if item.get('done'):
                            if item.get('done_reason') == 'length':
                                raise ValueError('Skrypt AI zostal uciety. Uprosc model i uzyj petli zamiast dlugich list.')
                            completed = True
                    if len(pending) > 200000:
                        raise ValueError('Nieprawidlowa odpowiedz AI: zbyt duzy fragment.')
            remaining = max(0.01, timeout - (time.monotonic() - started))
            try:
                result = process.wait(timeout=remaining)
            except subprocess.TimeoutExpired:
                raise TimeoutError('AI przekroczylo laczny limit 30 minut. Model nie zostal zapisany.') from None
            if cancelled.is_set():
                raise InterruptedError('Zlecenie anulowane.')
            if result == 28:
                raise TimeoutError('AI nie zakonczylo odpowiedzi w limicie czasu. Model nie zostal zapisany.')
            if result:
                detail = stderr.decode('utf-8', errors='replace').strip()[-500:]
                raise ConnectionError('Przerwane polaczenie z lokalnym AI. ' + detail)
            if not completed or not characters:
                raise ValueError('AI przerwalo odpowiedz bez kompletnego skryptu. Model nie zostal zapisany.')
            progress(characters, time.monotonic() - started, 0)
            return ''.join(pieces)
        finally:
            # Closing curl also closes its Ollama request; no abandoned inference
            # request remains when the user cancels or the total deadline expires.
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=2)
            selector.close()
            process.stdout.close()
            process.stderr.close()
