from .models import MemoryItem
from chat.cerebras_client import CerebrasClient


def extract_and_save(user, conversation):
    messages = conversation.messages.filter(role__in=['user', 'assistant'])
    if messages.count() < 2:
        return 0

    text = '\n'.join(f'{m.role}: {m.content}' for m in messages[:20])
    client = CerebrasClient()
    facts = client.extract_facts(text)

    saved = 0
    for fact in facts:
        key = fact.get('key', '').strip()
        value = fact.get('value', '').strip()
        if key and value:
            existing = MemoryItem.objects.filter(user=user, key=key)
            if existing.exists():
                existing.update(value=value, source_conversation=conversation)
            else:
                MemoryItem.objects.create(
                    user=user, key=key, value=value,
                    source_conversation=conversation,
                )
            saved += 1
    return saved
