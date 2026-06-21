import json
import re
from urllib.parse import quote

import httpx
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

CONTEXT_TOKEN_BUDGET = 6000
SUMMARY_TOKEN_BUDGET = 500


def _estimate_tokens(text):
    return len(text) // 4


def _summarize_old_messages(conversation, cutoff_time):
    old_msgs = conversation.messages.filter(
        role__in=['user', 'assistant'],
        created_at__lt=cutoff_time,
    )
    if not old_msgs.exists():
        return ''

    existing = conversation.summary or ''
    old_text = '\n'.join(f'{m.role}: {m.content}' for m in old_msgs[:30])
    if existing:
        old_text = f'Previous summary: {existing}\n\nNew messages to add:\n{old_text}'

    prompt = (
        'Summarize this conversation history into 2-3 short sentences. '
        'Focus on key topics, decisions, and facts. Plain text only, no markdown.'
    )
    messages = [
        {'role': 'system', 'content': prompt},
        {'role': 'user', 'content': old_text},
    ]
    result = client.chat(messages, max_tokens=150)
    if result.get('error'):
        return existing
    return result['content'].strip()

BASE_SYSTEM_PROMPT = (
    'You are a helpful assistant on a feature phone with a very small screen. '
    'CRITICAL RULES: '
    '1. Keep responses SHORT - aim for 2-4 sentences max unless the user explicitly asks for detail. '
    '2. Use PLAIN TEXT ONLY. Never use markdown, headers (#), bold (**), tables, bullet points, or code blocks. '
    '3. No lists with dashes or asterisks. Use simple numbered points like 1. 2. 3. if needed. '
    '4. Be direct and concise. Feature phone users scroll painfully on tiny screens. '
    '5. If the user needs more detail, ask them to follow up with specific questions.'
)

SEARCH_TOOL = {
    'type': 'function',
    'function': {
        'name': 'web_search',
        'description': 'Search the web for current information. Use when the user asks about current events, prices, weather, news, or anything requiring up-to-date info.',
        'parameters': {
            'type': 'object',
            'properties': {
                'query': {
                    'type': 'string',
                    'description': 'The search query',
                },
            },
            'required': ['query'],
        },
    },
}

DAILY_PROMPTS = [
    'Tell me a fun fact',
    'Give me a quick tip for today',
    'What is a good question to ask?',
    'Explain something interesting in 2 sentences',
    'Help me practice English',
]


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


def _web_search(query):
    try:
        with httpx.Client(timeout=10.0) as c:
            resp = c.get(
                'https://api.duckduckgo.com/',
                params={'q': query, 'format': 'json', 'no_html': 1, 'skip_disambig': 1},
            )
            data = resp.json()
            abstract = data.get('AbstractText', '')
            answer = data.get('Answer', '')
            related = data.get('RelatedTopics', [])
            parts = []
            if answer:
                parts.append(answer)
            if abstract:
                parts.append(abstract[:300])
            for topic in related[:3]:
                text = topic.get('Text', '')
                if text:
                    parts.append(text[:150])
            return ' '.join(parts) if parts else f'No results found for: {query}'
    except Exception:
        return f'Search failed for: {query}'


def _chat_with_tools(messages, model, max_tokens=300):
    result = client.chat_with_tools(messages, model=model, tools=[SEARCH_TOOL], max_tokens=max_tokens)

    if result.get('error'):
        return result

    tool_calls = result.get('tool_calls', [])
    if not tool_calls:
        return result

    messages.append(result.get('assistant_message', {}))

    for tc in tool_calls:
        fn_name = tc.get('function', {}).get('name', '')
        fn_args = json.loads(tc.get('function', {}).get('arguments', '{}'))
        tc_id = tc.get('id', '')

        if fn_name == 'web_search':
            search_result = _web_search(fn_args.get('query', ''))
            messages.append({
                'role': 'tool',
                'content': search_result,
                'tool_call_id': tc_id,
            })

    final = client.chat(messages, model=model, max_tokens=max_tokens)
    return final


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

    system_content = '\n\n'.join(system_parts)
    messages.append({'role': 'system', 'content': system_content})
    used_tokens = _estimate_tokens(system_content)

    all_history = list(
        conversation.messages.filter(role__in=['user', 'assistant'])
        .order_by('-created_at')
    )

    included = []
    for msg in all_history:
        msg_tokens = _estimate_tokens(msg.content) + 4
        if used_tokens + msg_tokens + SUMMARY_TOKEN_BUDGET > CONTEXT_TOKEN_BUDGET:
            break
        included.append(msg)
        used_tokens += msg_tokens

    included.reverse()

    if len(included) < len(all_history):
        if included:
            cutoff = included[0].created_at
        else:
            cutoff = all_history[-1].created_at

        if not conversation.summary or conversation.summary_up_to != cutoff:
            new_summary = _summarize_old_messages(conversation, cutoff)
            if new_summary:
                conversation.summary = new_summary
                conversation.summary_up_to = cutoff
                conversation.save(update_fields=['summary', 'summary_up_to'])

        if conversation.summary:
            summary_msg = f'Earlier conversation summary: {conversation.summary}'
            messages.append({'role': 'system', 'content': summary_msg})
            used_tokens += _estimate_tokens(summary_msg)

    for msg in included:
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
            user=request.user, title='New Chat', model=request.user.default_model,
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
    elif cmd == '/d':
        return None, 'redirect:chat:daily_prompts'
    elif cmd == '/h' or cmd == '/help':
        help_text = (
            'Commands:\n'
            '/c = Clear chat\n'
            '/n = New conversation\n'
            '/p = Personas\n'
            '/m = Memory\n'
            '/q = Quick actions\n'
            '/s = Conversations\n'
            '/d = Daily prompts\n'
            '/e = Export SMS\n'
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
    msg_page = 0
    try:
        msg_page = int(request.GET.get('page', '0'))
    except ValueError:
        pass

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

            if len(user_input) >= 2 and user_input[0].isdigit() and user_input[1] in (' ', '.'):
                from quickactions.models import QuickAction
                key_num = int(user_input[0])
                sep_idx = 1
                try:
                    qa = QuickAction.objects.get(user=request.user, key_number=key_num)
                    user_input = qa.prompt_template.replace('{input}', user_input[sep_idx:].strip())
                except QuickAction.DoesNotExist:
                    pass

            Message.objects.create(
                conversation=conversation, role='user', content=user_input[:500],
            )

            if conversation.title == 'New Chat':
                conversation.title = user_input[:30]
                conversation.save()

            api_messages = _build_messages(conversation, user_input)
            result = _chat_with_tools(api_messages, conversation.model, max_tokens=300)

            if result.get('error'):
                request.session['flash_message'] = result['error']
            else:
                total_tokens = result.get('total_tokens', 0)
                clean_content = _strip_markdown(result['content'])
                Message.objects.create(
                    conversation=conversation, role='assistant',
                    content=clean_content, model_used=result.get('model', ''),
                    token_count=total_tokens,
                )
                add_usage(request.user, total_tokens)
                chunks = _chunk_text(clean_content)
                request.session['last_chunks'] = chunks
                request.session['last_chunk_page'] = 0

            return redirect('chat:chat')
    else:
        form = ChatForm()

    flash = request.session.pop('flash_message', None)
    all_msgs = conversation.messages.filter(role__in=['user', 'assistant'])
    total = all_msgs.count()
    per_page = settings.MESSAGES_PER_PAGE

    chunks = request.session.get('last_chunks', [])
    chunk_idx = request.session.get('last_chunk_page', 0)
    last_response_chunked = len(chunks) > 1

    effective_total = total
    if last_response_chunked and total > 0:
        last_msg = all_msgs.last()
        if last_msg and last_msg.role == 'assistant':
            effective_total = total - 1

    start = max(0, effective_total - (msg_page + 1) * per_page)
    end = effective_total - msg_page * per_page
    chat_messages = list(all_msgs[start:end])

    usage = get_usage(request.user)
    limit_info = check_limit(request.user)

    current_chunk = chunks[chunk_idx] if chunks and chunk_idx < len(chunks) else ''

    return render(request, 'chat/chat.html', {
        'form': form,
        'conversation': conversation,
        'chat_messages': chat_messages,
        'flash': flash,
        'has_older': start > 0,
        'has_newer': msg_page > 0,
        'msg_page': msg_page,
        'current_chunk': current_chunk,
        'chunk_page': chunk_idx,
        'total_chunks': len(chunks),
        'has_next_chunk': chunk_idx < len(chunks) - 1,
        'has_prev_chunk': chunk_idx > 0,
        'last_response_chunked': last_response_chunked,
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
    return render(request, 'chat/model_select.html', {'form': form, 'page_title': 'Model'})


@login_required
def daily_prompts(request):
    if request.method == 'POST':
        choice = request.POST.get('choice', '').strip()
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(DAILY_PROMPTS):
                request.session['prefill_prompt'] = DAILY_PROMPTS[idx]
                return redirect('chat:chat')
        elif choice.lower() == 'r':
            import random
            request.session['prefill_prompt'] = random.choice(DAILY_PROMPTS)
            return redirect('chat:chat')

    return render(request, 'chat/daily_prompts.html', {
        'prompts': enumerate(DAILY_PROMPTS, 1),
        'page_title': 'Daily Prompts',
    })
