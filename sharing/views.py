from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from .models import SharedPrompt
from .forms import ShareForm, ImportForm
from personas.models import Persona


@login_required
def share_list(request):
    shared = SharedPrompt.objects.filter(user=request.user)
    numbered = [(i + 1, s) for i, s in enumerate(shared)]

    if request.method == 'POST':
        choice = request.POST.get('choice', '').strip()
        if choice.lower() == 'n':
            return redirect('sharing:create')
        elif choice.lower() == 'i':
            return redirect('sharing:import')

    return render(request, 'sharing/list.html', {
        'shared': numbered,
        'page_title': 'Sharing',
    })


@login_required
def share_create(request):
    if request.method == 'POST':
        form = ShareForm(request.POST)
        if form.is_valid():
            SharedPrompt.objects.create(
                user=request.user,
                title=form.cleaned_data['title'],
                content=form.cleaned_data['content'],
                share_type=form.cleaned_data['share_type'],
            )
            return redirect('sharing:list')
    else:
        form = ShareForm()
    return render(request, 'sharing/create.html', {'form': form, 'page_title': 'Share New'})


@login_required
def share_import(request):
    if request.method == 'POST':
        form = ImportForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['share_code'].upper()
            try:
                shared = SharedPrompt.objects.get(share_code=code)
                if shared.share_type == 'persona':
                    Persona.objects.create(
                        user=request.user,
                        name=f'{shared.title} (imported)',
                        system_prompt=shared.content,
                    )
                else:
                    Persona.objects.create(
                        user=request.user,
                        name=f'{shared.title} (imported)',
                        system_prompt=shared.content,
                    )
                return redirect('personas:list')
            except SharedPrompt.DoesNotExist:
                form.add_error('share_code', 'Code not found.')
    else:
        form = ImportForm()
    return render(request, 'sharing/import.html', {'form': form, 'page_title': 'Import'})


def share_public(request, code):
    shared = get_object_or_404(SharedPrompt, share_code=code.upper())
    return render(request, 'sharing/public.html', {
        'shared': shared, 'page_title': shared.title,
    })
