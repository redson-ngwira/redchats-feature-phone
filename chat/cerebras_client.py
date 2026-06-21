import httpx
from django.conf import settings


class CerebrasClient:
    def __init__(self):
        self.api_url = settings.CEREBRAS_API_URL
        self.api_key = settings.CEREBRAS_API_KEY
        self.timeout = 60.0

    def chat(self, messages, model=None, max_tokens=1024):
        model = model or settings.CEREBRAS_DEFAULT_MODEL
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }
        payload = {
            'model': model,
            'messages': messages,
            'max_tokens': max_tokens,
        }
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(self.api_url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                choice = data['choices'][0]
                usage = data.get('usage', {})
                return {
                    'content': choice['message']['content'],
                    'model': model,
                    'prompt_tokens': usage.get('prompt_tokens', 0),
                    'completion_tokens': usage.get('completion_tokens', 0),
                    'total_tokens': usage.get('total_tokens', 0),
                }
        except httpx.TimeoutException:
            return {'error': 'Request timed out. Please try again.', 'content': ''}
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                return {'error': 'Rate limit reached. Wait a moment and try again.', 'content': ''}
            return {'error': f'API error: {e.response.status_code}', 'content': ''}
        except Exception as e:
            return {'error': f'Connection error: {str(e)[:100]}', 'content': ''}

    def extract_facts(self, conversation_text):
        messages = [
            {
                'role': 'system',
                'content': (
                    'Extract key facts about the user from this conversation. '
                    'Return ONLY a JSON array of objects with "key" and "value" fields. '
                    'Example: [{"key": "name", "value": "John"}]. '
                    'If no facts found, return empty array [].'
                ),
            },
            {'role': 'user', 'content': conversation_text},
        ]
        result = self.chat(messages, max_tokens=256)
        if result.get('error'):
            return []
        try:
            import json
            content = result['content'].strip()
            if content.startswith('```'):
                content = content.split('\n', 1)[1].rsplit('```', 1)[0]
            return json.loads(content)
        except (json.JSONDecodeError, IndexError):
            return []
