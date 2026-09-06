import json
import time
import urllib.request
from server import MODEL, OLLAMA, STATE, initialize, health, write_json

initialize()
destination = STATE / 'pull-status.json'
if health()['ready']:
    write_json(destination, {'detail': 'Lokalne AI jest gotowe.'})
else:
    for attempt in range(30):
        try:
            with urllib.request.urlopen(OLLAMA + '/api/tags', timeout=5):
                break
        except Exception:
            time.sleep(2)
    request = urllib.request.Request(OLLAMA + '/api/pull', data=json.dumps({'model': MODEL, 'stream': True}).encode(), headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            for line in response:
                data = json.loads(line)
                if data.get('error'):
                    raise RuntimeError(data['error'])
                detail = 'Przygotowanie AI: ' + str(data.get('status', 'pobieranie'))
                if data.get('total'):
                    detail += ' (%d%% tej czesci)' % min(100, round(100 * data.get('completed', 0) / data['total']))
                write_json(destination, {'detail': detail})
        if not health()['ready']:
            raise RuntimeError('Model AI nie pojawil sie na liscie zainstalowanych modeli.')
        write_json(destination, {'detail': 'Lokalne AI jest gotowe.'})
    except Exception:
        write_json(destination, {'detail': 'Pobieranie AI nie powiodlo sie. Usluga sprobuje ponownie; sprawdz polaczenie serwera z Internetem.'})
        raise
