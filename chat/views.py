import math
import re
from datetime import date

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.conf import settings

from .models import Message
from .forms import ChatForm, ModelForm
from .cerebras_client import CerebrasClient
from .token_tracker import get_usage, add_usage, check_limit
from conversations.models import Conversation
from personas.models import Persona
from memory.models import MemoryItem

client = CerebrasClient()

BASE_SYSTEM_PROMPT = (
    'You are a helpful assistant on a feature phone with a very small screen. '
    'CRITICAL RULES: '
    '1. Keep responses SHORT - aim for 2-4 sentences max unless the user explicitly asks for detail. '
    '2. Use PLAIN TEXT ONLY. Never use markdown, headers (#), bold (**), tables, bullet points, or code blocks. '
    '3. No lists with dashes or asterisks. Use simple numbered points like 1. 2. 3. if needed. '
    '4. Be direct and concise. Feature phone users scroll painfully on tiny screens. '
    '5. If the user needs more detail, ask them to follow up with specific questions.'
)


def _strip_markdown(text):
    text = re.sub(r'#{1,6}\s*', '', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)
    text = re.sub(r'_(.+?)_', r'\1', text)
    text = re.sub(r'`{1,3}[^`]*`{1,3}', '', text)
    text = re.sub(r'^[-*]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\|.*\|', '', text)
    text = re.sub(r'^[-=]{3,}$', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def _get_or_create_conversation(request):
    conv_id = request.session.get('active_conversation')
    if conv_id:
        try:
            return Conversation.objects.get(id=conv_id, user=request.user)
        except Conversation.DoesNotExist:
            pass
    conv = Conversation.objects.create(
        user=request.user,
        title='New Chat',
        model=request.user.default_model,
    )
    request.session['active_conversation'] = conv.id
    return conv


def _build_messages(conversation, user_message):
    messages = []
    system_parts = [BASE_SYSTEM_PROMPT]

    persona = conversation.persona
    if persona:
        system_parts.append(persona.system_prompt)

    memories = MemoryItem.objects.filter(user=conversation.user)
    if memories.exists():
        memory_text = 'You know these facts about the user: '
        memory_text += '; '.join(f'{m.key}: {m.value}' for m in memories[:20])
        system_parts.append(memory_text)

    messages.append({'role': 'system', 'content': '\n\n'.join(system_parts)})

    for msg in conversation.messages.filter(role__in=['user', 'assistant']):
        messages.append({'role': msg.role, 'content': msg.content})

    messages.append({'role': 'user', 'content': user_message})
    return messages


def _handle_slash_command(command, conversation, request):
    cmd = command.lower().strip()
    if cmd == '/c':
        conversation.messages.filter(role__in=['user', 'assistant']).delete()
        return 'Chat cleared.', 'done'
    elif cmd == '/n':
        conv = Conversation.objects.create(
            user=request.user,
            title='New Chat',
            model=request.user.default_model,
        )
        request.session['active_conversation'] = conv.id
        return 'New conversation started.', 'done'
    elif cmd == '/p':
        return None, 'redirect:personas:list'
    elif cmd == '/m':
        return None, 'redirect:memory:list'
    elif cmd == '/q':
        return None, 'redirect:quickactions:list'
    elif cmd == '/s':
        return None, 'redirect:conversations:list'
    elif cmd == '/e':
        return None, f'redirect:export:export_sms:{conversation.id}'
    elif cmd == '/h' or cmd == '/help':
        help_text = (
            'Commands:\n'
            '/c = Clear chat\n'
            '/n = New conversation\n'
            '/p = Personas\n'
            '/m = Memory\n'
            '/q = Quick actions\n'
            '/s = Switch conversation\n'
            '/e = Export as SMS\n'
            '/model = Change model\n'
            '/help = This help'
        )
        return help_text, 'done'
    elif cmd == '/model':
        return None, 'redirect:chat:model_select'
    return None, None


def _chunk_text(text, chunk_size=None):
    chunk_size = chunk_size or settings.RESPONSE_CHUNK_SIZE
    if len(text) <= chunk_size:
        return [text]
    chunks = []
    words = text.split()
    current = []
    current_len = 0
    for word in words:
        if current_len + len(word) + 1 > chunk_size and current:
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
def chat_view(request):
    conversation = _get_or_create_conversation(request)
    chunk_page = request.GET.get('chunk', '0')
    msg_page = request.GET.get('page', '0')

    try:
        chunk_page = int(chunk_page)
    except ValueError:
        chunk_page = 0
    try:
        msg_page = int(msg_page)
    except ValueError:
        msg_page = 0

    last_response_chunks = request.session.get('last_chunks', [])
    last_chunk_page = request.session.get('last_chunk_page', 0)

    if request.method == 'POST':
        form = ChatForm(request.POST)
        if form.is_valid():
            user_input = form.cleaned_data['message'].strip()

            if user_input.startswith('/'):
                result = _handle_slash_command(user_input, conversation, request)
                if result:
                    msg, action = result
                    if action and isinstance(action, str) and action.startswith('redirect:'):
                        parts = action.replace('redirect:', '').split(':')
                        if len(parts) == 2:
                            return redirect(f'{parts[0]}:{parts[1]}')
                        elif len(parts) == 3:
                            return redirect(f'{parts[0]}:{parts[1]}', parts[2])
                    if msg:
                        request.session['flash_message'] = msg
                    return redirect('chat:chat')

            # Check quick action shortcut (digit prefix)
            if len(user_input) >= 2 and user_input[0].isdigit() and user_input[1] == ' ':
                from quickactions.models import QuickAction
                key_num = int(user_input[0])
                try:
                    qa = QuickAction.objects.get(user=request.user, key_number=key_num)
                    user_input = qa.prompt_template.replace('{input}', user_input[2:])
                except QuickAction.DoesNotExist:
                    pass

            Message.objects.create(
                conversation=conversation, role='user', content=user_input
            )

            if conversation.title == 'New Chat':
                conversation.title = user_input[:30]
                conversation.save()

            messages = _build_messages(conversation, user_input)
            result = client.chat(messages, model=conversation.model, max_tokens=300)

            if result.get('error'):
                request.session['flash_message'] = result['error']
            else:
                total_tokens = result.get('total_tokens', 0)
                clean_content = _strip_markdown(result['content'])
                Message.objects.create(
                    conversation=conversation,
                    role='assistant',
                    content=clean_content,
                    model_used=result.get('model', ''),
                    token_count=total_tokens,
                )
                add_usage(request.user, total_tokens)

                chunks = _chunk_text(clean_content)
                request.session['last_chunks'] = chunks
                request.session['last_chunk_page'] = 0
                chunk_page = 0

            return redirect('chat:chat')
    else:
        form = ChatForm()

    flash = request.session.pop('flash_message', None)
    all_messages = conversation.messages.filter(role__in=['user', 'assistant'])
    total_msgs = all_messages.count()
    msgs_per_page = settings.MESSAGES_PER_PAGE
    start = max(0, total_msgs - (msg_page + 1) * msgs_per_page)
    end = total_msgs - msg_page * msgs_per_page
    messages = list(all_messages[start:end])
    has_older = start > 0
    has_newer = msg_page > 0

    usage = get_usage(request.user)
    limit_info = check_limit(request.user)

    chunks = request.session.get('last_chunks', [])
    chunk_page_idx = request.session.get('last_chunk_page', 0)
    current_chunk = chunks[chunk_page_idx] if chunks and chunk_page_idx < len(chunks) else ''
    total_chunks = len(chunks)

    return render(request, 'chat/chat.html', {
        'form': form,
        'conversation': conversation,
        'messages': messages,
        'flash': flash,
        'has_older': has_older,
        'has_newer': has_newer,
        'msg_page': msg_page,
        'current_chunk': current_chunk,
        'chunk_page': chunk_page_idx,
        'total_chunks': total_chunks,
        'has_next_chunk': chunk_page_idx < total_chunks - 1,
        'has_prev_chunk': chunk_page_idx > 0,
        'usage': usage,
        'limit_warning': limit_info.get('warning', False),
        'usage_percent': limit_info.get('percent', 0),
        'page_title': conversation.title,
    })


@login_required
def chunk_nav(request, direction):
    chunks = request.session.get('last_chunks', [])
    idx = request.session.get('last_chunk_page', 0)
    if direction == 'next' and idx < len(chunks) - 1:
        idx += 1
    elif direction == 'prev' and idx > 0:
        idx -= 1
    elif direction == 'full':
        idx = 0
    request.session['last_chunk_page'] = idx
    return redirect('chat:chat')


@login_required
def msg_nav(request, direction):
    return redirect(f'/chat/?page={request.GET.get("page", "0")}')


@login_required
def model_select(request):
    model_choices = settings.CEREBRAS_MODELS
    conv_id = request.session.get('active_conversation')
    if request.method == 'POST':
        form = ModelForm(request.POST)
        form.fields['model'].choices = model_choices
        if form.is_valid() and conv_id:
            try:
                conv = Conversation.objects.get(id=conv_id, user=request.user)
                conv.model = form.cleaned_data['model']
                conv.save()
            except Conversation.DoesNotExist:
                pass
            return redirect('chat:chat')
    else:
        form = ModelForm()
        form.fields['model'].choices = model_choices
        if conv_id:
            try:
                conv = Conversation.objects.get(id=conv_id, user=request.user)
                form.fields['model'].initial = conv.model
            except Conversation.DoesNotExist:
                pass
    return render(request, 'chat/model_select.html', {'form': form, 'page_title': 'Select Model'})
