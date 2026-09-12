"""Read local Ollama output with a total deadline and cancellable, visible waits."""
import json
import os
import selectors
import subprocess
import tempfile
import time
from contextlib import ExitStack


class OpenAIServiceError(RuntimeError):
    """A sanitized provider failure, never raw upstream response text."""


class AIStreamTimeout(TimeoutError):
    """Retain bounded draft evidence; never treat a partial stream as success."""
    def __init__(self,message,partial_text='',elapsed=0):
        super().__init__(message)
        self.partial_text=partial_text
        self.elapsed=elapsed


def openai_error(code):
    if code in (401, 'invalid_api_key'):
        return 'OpenAI odrzucilo klucz API. Sprawdz klucz w ustawieniach.'
    if code in (403, 404, 'model_not_found', 'permission_denied'):
        return 'Klucz OpenAI nie ma dostepu do modelu gpt-6-astra.'
    if code in (429, 'insufficient_quota', 'rate_limit_exceeded'):
        return 'OpenAI API: limit zapytan lub brak dostepnych srodkow. Sprawdz limity i rozliczenia API.'
    return 'OpenAI API nie zakonczylo zadania. Sprawdz dostep do modelu i limity API.'


def stream_chat(url, payload, cancelled, progress, timeout=1800, interval=8, validate_chunk=None,
                response_protocol='ollama', api_key=None, usage_callback=None):
    """Curl owns the socket; the worker can cancel even before HTTP headers arrive.

    There is deliberately no short inactivity timeout: loading/prefill on CPU may
    be silent. The entire request, including silent waits, has a fixed deadline.
    No prompts are placed in command-line arguments or diagnostic output.
    """
    is_openai = response_protocol == 'responses'
    timeout_message = ('OpenAI' if is_openai else 'Lokalne AI') + ' przekroczylo limit %.0f s na kompletna odpowiedz.' % max(0,timeout)
    if cancelled.is_set():
        raise InterruptedError('Zlecenie anulowane.')
    if timeout <= 0:
        raise AIStreamTimeout(timeout_message)
    started = time.monotonic()
    last_data = started
    next_progress = started
    command = ['curl', '-q', '--silent', '--show-error', '--no-buffer', '--fail-with-body',
               '--noproxy', '*', '--connect-timeout', str(min(15, timeout)),
               '--max-time', str(timeout), '--header', 'Content-Type: application/json',
               '--data-binary', '@-', url]
    # Supply stdin from a temporary file, avoiding a blocking write to a full pipe.
    with ExitStack() as stack:
        request_body = stack.enter_context(tempfile.TemporaryFile())
        if api_key:
            # Keep the credential out of process arguments, logs and generated code.
            headers = stack.enter_context(tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8'))
            headers.write('Authorization: Bearer ' + api_key + '\n')
            headers.flush()
            command[2:2] = ['--header', '@' + headers.name]
        if is_openai:
            command[2:2] = ['--write-out', '\nFROGE_HTTP_STATUS:%{http_code}\n']
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
        http_status = 0
        try:
            while selector.get_map():
                now = time.monotonic()
                if cancelled.is_set():
                    raise InterruptedError('Zlecenie anulowane.')
                if now - started >= timeout:
                    raise AIStreamTimeout(timeout_message,''.join(pieces),now-started)
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
                        if is_openai:
                            if raw.startswith(b'FROGE_HTTP_STATUS:'):
                                http_status = int(raw.split(b':', 1)[1])
                                continue
                            if not raw.startswith(b'data:'):
                                continue
                            raw = raw[5:].strip()
                            if raw == b'[DONE]':
                                continue
                        item = json.loads(raw)
                        if is_openai:
                            event = item.get('type')
                            response = item.get('response') or {}
                            if event in ('error', 'response.failed'):
                                failure = response.get('error') or item.get('error') or item
                                raise OpenAIServiceError(openai_error(failure.get('code') if isinstance(failure, dict) else None))
                            if event in ('response.refusal.delta', 'response.refusal.done'):
                                raise OpenAIServiceError('OpenAI odmowilo przygotowania tych instrukcji.')
                            if event == 'response.incomplete':
                                raise ValueError('Skrypt AI zostal uciety. Uzyj krotszych funkcji i petli; zwroc kompletny model.')
                            content = item.get('delta', '') if event == 'response.output_text.delta' else ''
                            if event == 'response.completed':
                                if response.get('status') != 'completed':
                                    raise ValueError('OpenAI nie potwierdzilo kompletnej odpowiedzi.')
                                completed = True
                                if usage_callback:
                                    usage = response.get('usage') or {}
                                    usage_callback({k: v for k, v in usage.items() if k in ('input_tokens', 'output_tokens', 'total_tokens') and type(v) is int})
                                if not characters:
                                    raise ValueError('OpenAI zakonczylo odpowiedz bez planu.')
                                # response.completed is the authoritative terminal
                                # event. A proxy may keep the HTTP stream open.
                                progress(characters,time.monotonic()-started,0)
                                return ''.join(pieces)
                        else:
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
                        if size > 256000:
                            raise ValueError('Plan AI przekracza limit 256 kB. Podziel scene na mniej czesci.')
                        if content and validate_chunk is not None:
                            validate_chunk(content)
                        if not is_openai and item.get('done'):
                            if item.get('done_reason') == 'length':
                                raise ValueError('Skrypt AI zostal uciety. Uprosc model i uzyj petli zamiast dlugich list.')
                            completed = True
                    if len(pending) > 200000:
                        raise ValueError('Nieprawidlowa odpowiedz AI: zbyt duzy fragment.')
            remaining = max(0.01, timeout - (time.monotonic() - started))
            try:
                result = process.wait(timeout=remaining)
            except subprocess.TimeoutExpired:
                raise AIStreamTimeout(timeout_message,''.join(pieces),time.monotonic()-started) from None
            if cancelled.is_set():
                raise InterruptedError('Zlecenie anulowane.')
            if result == 28:
                raise AIStreamTimeout(timeout_message,''.join(pieces),time.monotonic()-started)
            if result:
                if is_openai:
                    raise OpenAIServiceError(openai_error(http_status))
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
