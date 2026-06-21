from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from .models import QuickAction
from .forms import QuickActionForm
from .defaults import DEFAULT_QUICK_ACTIONS


@login_required
def quickaction_list(request):
    actions = QuickAction.objects.filter(user=request.user)

    if not actions.exists():
        for key, label, template in DEFAULT_QUICK_ACTIONS:
            QuickAction.objects.create(
                user=request.user, key_number=key,
                label=label, prompt_template=template,
            )
        actions = QuickAction.objects.filter(user=request.user)

    numbered = [(a.key_number, a) for a in actions]

    if request.method == 'POST':
        choice = request.POST.get('choice', '').strip()
        if choice.isdigit():
            key = int(choice)
            try:
                qa = actions.get(key_number=key)
                return redirect('quickactions:edit', pk=qa.pk)
            except QuickAction.DoesNotExist:
                pass

    return render(request, 'quickactions/list.html', {
        'actions': numbered,
        'page_title': 'Quick Actions',
    })


@login_required
def quickaction_edit(request, pk):
    qa = get_object_or_404(QuickAction, pk=pk, user=request.user)
    if request.method == 'POST':
        form = QuickActionForm(request.POST)
        if form.is_valid():
            qa.label = form.cleaned_data['label']
            qa.prompt_template = form.cleaned_data['prompt_template']
            qa.save()
            return redirect('quickactions:list')
    else:
        form = QuickActionForm(initial={
            'label': qa.label,
            'prompt_template': qa.prompt_template,
        })
    return render(request, 'quickactions/edit.html', {
        'form': form, 'action': qa, 'page_title': f'Edit #{qa.key_number}',
    })
