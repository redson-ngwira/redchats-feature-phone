from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from .models import Conversation
from .forms import ConversationForm, RenameForm


@login_required
def conversation_list(request):
    conversations = Conversation.objects.filter(user=request.user)
    numbered = [(i + 1, c) for i, c in enumerate(conversations)]

    if request.method == 'POST':
        choice = request.POST.get('choice', '').strip()
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(conversations):
                conv = conversations[idx]
                request.session['active_conversation'] = conv.id
                return redirect('chat:chat')
        elif choice.lower() == 'n':
            return redirect('conversations:create')

    return render(request, 'conversations/list.html', {
        'conversations': numbered,
        'page_title': 'Conversations',
    })


@login_required
def conversation_create(request):
    if request.method == 'POST':
        form = ConversationForm(request.POST)
        if form.is_valid():
            conv = Conversation.objects.create(
                user=request.user,
                title=form.cleaned_data['title'],
                model=request.user.default_model,
            )
            request.session['active_conversation'] = conv.id
            return redirect('chat:chat')
    else:
        form = ConversationForm(initial={'title': 'New Chat'})
    return render(request, 'conversations/create.html', {'form': form, 'page_title': 'New Chat'})


@login_required
def conversation_rename(request, pk):
    conv = get_object_or_404(Conversation, pk=pk, user=request.user)
    if request.method == 'POST':
        form = RenameForm(request.POST)
        if form.is_valid():
            conv.title = form.cleaned_data['title']
            conv.save()
            return redirect('conversations:list')
    else:
        form = RenameForm(initial={'title': conv.title})
    return render(request, 'conversations/rename.html', {
        'form': form, 'conversation': conv, 'page_title': 'Rename',
    })


@login_required
def conversation_delete(request, pk):
    conv = get_object_or_404(Conversation, pk=pk, user=request.user)
    if request.method == 'POST':
        conv.delete()
        if request.session.get('active_conversation') == conv.id:
            del request.session['active_conversation']
        return redirect('conversations:list')
    return render(request, 'conversations/delete.html', {
        'conversation': conv, 'page_title': 'Delete',
    })


@login_required
def conversation_pin(request, pk):
    conv = get_object_or_404(Conversation, pk=pk, user=request.user)
    conv.is_pinned = not conv.is_pinned
    conv.save()
    return redirect('conversations:list')
