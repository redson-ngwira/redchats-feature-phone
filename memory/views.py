from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from .models import MemoryItem
from .forms import MemoryForm
from .extractor import extract_and_save
from conversations.models import Conversation


@login_required
def memory_list(request):
    memories = MemoryItem.objects.filter(user=request.user)
    numbered = [(i + 1, m) for i, m in enumerate(memories)]

    if request.method == 'POST':
        choice = request.POST.get('choice', '').strip()
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(memories):
                return redirect('memory:edit', pk=memories[idx].pk)
        elif choice.lower() == 'n':
            return redirect('memory:create')
        elif choice.lower() == 'e':
            conv_id = request.session.get('active_conversation')
            if conv_id:
                return redirect('memory:extract', pk=conv_id)

    return render(request, 'memory/list.html', {
        'memories': numbered,
        'page_title': 'Memory',
    })


@login_required
def memory_create(request):
    if request.method == 'POST':
        form = MemoryForm(request.POST)
        if form.is_valid():
            MemoryItem.objects.create(
                user=request.user,
                key=form.cleaned_data['key'],
                value=form.cleaned_data['value'],
            )
            return redirect('memory:list')
    else:
        form = MemoryForm()
    return render(request, 'memory/create.html', {'form': form, 'page_title': 'Add Memory'})


@login_required
def memory_edit(request, pk):
    mem = get_object_or_404(MemoryItem, pk=pk, user=request.user)
    if request.method == 'POST':
        form = MemoryForm(request.POST)
        if form.is_valid():
            mem.key = form.cleaned_data['key']
            mem.value = form.cleaned_data['value']
            mem.save()
            return redirect('memory:list')
    else:
        form = MemoryForm(initial={'key': mem.key, 'value': mem.value})
    return render(request, 'memory/edit.html', {
        'form': form, 'memory': mem, 'page_title': 'Edit Memory',
    })


@login_required
def memory_delete(request, pk):
    mem = get_object_or_404(MemoryItem, pk=pk, user=request.user)
    if request.method == 'POST':
        mem.delete()
        return redirect('memory:list')
    return render(request, 'memory/delete.html', {
        'memory': mem, 'page_title': 'Delete Memory',
    })


@login_required
def memory_extract(request, pk):
    conv = get_object_or_404(Conversation, pk=pk, user=request.user)
    if request.method == 'POST':
        saved = extract_and_save(request.user, conv)
        return render(request, 'memory/extract_result.html', {
            'saved': saved,
            'conversation': conv,
            'page_title': 'Extracted',
        })
    return render(request, 'memory/extract.html', {
        'conversation': conv, 'page_title': 'Extract Facts',
    })
