from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.conf import settings

from conversations.models import Conversation


def _chunk_sms(text, size=160):
    if len(text) <= size:
        return [text]
    chunks = []
    words = text.split()
    current = []
    current_len = 0
    for word in words:
        if current_len + len(word) + 1 > size and current:
            chunks.append(' '.join(current))
            current = [word]
            current_len = len(word)
        else:
            current.append(word)
            current_len += len(word) + 1
    if current:
        chunks.append(' '.join(current))
    return chunks


@login_required
def export_sms(request, pk):
    conv = get_object_or_404(Conversation, pk=pk, user=request.user)
    messages = conv.messages.filter(role__in=['user', 'assistant'])

    fmt = request.GET.get('fmt', 'sms')

    if fmt == 'text':
        lines = []
        for msg in messages:
            role = 'You' if msg.role == 'user' else 'AI'
            lines.append(f'{role}: {msg.content}')
        full_text = '\n\n'.join(lines)
        chunks = [full_text]
    else:
        raw = []
        for msg in messages:
            role = 'You' if msg.role == 'user' else 'AI'
            raw.append(f'{role}: {msg.content}')
        full_text = ' | '.join(raw)
        chunks = _chunk_sms(full_text)

    sms_links = []
    for chunk in chunks:
        sms_links.append(f'sms:?body={chunk}')

    return render(request, 'export/sms.html', {
        'conversation': conv,
        'chunks': chunks,
        'sms_links': sms_links,
        'format': fmt,
        'page_title': 'Export',
    })
