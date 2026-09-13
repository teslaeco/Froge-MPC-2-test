"""OpenAI Responses API. Fixed HTTPS origin; credentials never enter model input."""
import json
import re
import urllib.error
import urllib.request

from ai_stream import OpenAIServiceError, openai_error, stream_chat

MODEL = 'gpt-6-astra'
API = 'https://api.openai.com/v1'
KEY = re.compile(r'^sk-[A-Za-z0-9_-]{20,500}$')
TIME_LIMIT = 180


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def verify_key(value):
    if not isinstance(value, str) or not KEY.fullmatch(value):
        raise OpenAIServiceError('Wklej pelny klucz API OpenAI zaczynajacy sie od sk-.')
    request = urllib.request.Request(API + '/models/' + MODEL,
                                     headers={'Authorization': 'Bearer ' + value})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    try:
        with opener.open(request, timeout=12) as response:
            data = json.loads(response.read(16000))
            if data.get('id') != MODEL:
                raise OpenAIServiceError(openai_error('model_not_found'))
    except urllib.error.HTTPError as error:
        error.close()
        raise OpenAIServiceError(openai_error(error.code)) from None
    except (OSError, ValueError):
        raise OpenAIServiceError('Nie udalo sie sprawdzic klucza w OpenAI API. Sprobuj ponownie.') from None
    return value


def generate(messages, api_key, cancelled, progress, timeout, validate_chunk, usage_callback, schema=None, purpose="plan"):
    has_images=any(isinstance(m.get('content'),list) and any(isinstance(item,dict) and item.get('type')=='input_image' for item in m['content']) for m in messages)
    # The output allowance includes reasoning. Max effort exhausted the whole
    # allowance before producing a usable scene. Spend it on geometry instead;
    # reviews return a compact verdict/patch, never a second complete scene.
    effort = 'high' if has_images and purpose == 'plan' else 'low'
    allowance = 6000 if purpose == 'review' else 9000 if purpose == 'repair' else 24000 if has_images else 9000
    payload = {'model': MODEL, 'input': messages, 'stream': True, 'store': False,
               'reasoning': {'effort': effort}, 'max_output_tokens': allowance}
    if schema is not None:
        payload['text'] = {'format': {'type': 'json_schema', 'name': 'froge_scene',
                                      'strict': True, 'schema': schema}}
    return stream_chat(API + '/responses', payload, cancelled, progress, timeout=timeout,
                       interval=2, validate_chunk=validate_chunk, response_protocol='responses',
                       api_key=api_key, usage_callback=usage_callback)
