from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from .models import Persona
from .forms import PersonaForm
from conversations.models import Conversation


DEFAULT_PERSONAS = [
    ('Helper', 'You are a friendly and helpful assistant. Keep responses concise.'),
    ('Teacher', 'You are a patient teacher. Explain concepts step by step simply.'),
    ('Coder', 'You are a programming expert. Provide clear code with explanations.'),
    ('Writer', 'You are a creative writer. Help with writing, editing, and brainstorming.'),
    ('Translator', 'You are a translator. Translate text accurately between languages.'),
    ('Summarizer', 'You summarize text concisely. Keep summaries brief and clear.'),
]


@login_required
def persona_list(request):
    personas = Persona.objects.filter(user=request.user)

    if not personas.exists():
        for name, prompt in DEFAULT_PERSONAS:
            Persona.objects.create(
                user=request.user, name=name,
                system_prompt=prompt,
                is_default=(name == 'Helper'),
            )
        personas = Persona.objects.filter(user=request.user)

    numbered = [(i + 1, p) for i, p in enumerate(personas)]

    if request.method == 'POST':
        choice = request.POST.get('choice', '').strip()
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(personas):
                persona = personas[idx]
                conv_id = request.session.get('active_conversation')
                if conv_id:
                    try:
                        conv = Conversation.objects.get(id=conv_id, user=request.user)
                        conv.persona = persona
                        conv.save()
                    except Conversation.DoesNotExist:
                        pass
                return redirect('chat:chat')
        elif choice.lower() == 'n':
            return redirect('personas:create')

    return render(request, 'personas/list.html', {
        'personas': numbered,
        'page_title': 'Personas',
    })


@login_required
def persona_create(request):
    if request.method == 'POST':
        form = PersonaForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['is_default']:
                Persona.objects.filter(user=request.user, is_default=True).update(is_default=False)
            Persona.objects.create(
                user=request.user,
                name=form.cleaned_data['name'],
                system_prompt=form.cleaned_data['system_prompt'],
                is_default=form.cleaned_data['is_default'],
            )
            return redirect('personas:list')
    else:
        form = PersonaForm()
    return render(request, 'personas/create.html', {'form': form, 'page_title': 'New Persona'})


@login_required
def persona_edit(request, pk):
    persona = get_object_or_404(Persona, pk=pk, user=request.user)
    if request.method == 'POST':
        form = PersonaForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['is_default']:
                Persona.objects.filter(user=request.user, is_default=True).exclude(pk=pk).update(is_default=False)
            persona.name = form.cleaned_data['name']
            persona.system_prompt = form.cleaned_data['system_prompt']
            persona.is_default = form.cleaned_data['is_default']
            persona.save()
            return redirect('personas:list')
    else:
        form = PersonaForm(initial={
            'name': persona.name,
            'system_prompt': persona.system_prompt,
            'is_default': persona.is_default,
        })
    return render(request, 'personas/edit.html', {
        'form': form, 'persona': persona, 'page_title': 'Edit Persona',
    })


@login_required
def persona_delete(request, pk):
    persona = get_object_or_404(Persona, pk=pk, user=request.user)
    if request.method == 'POST':
        persona.delete()
        return redirect('personas:list')
    return render(request, 'personas/delete.html', {
        'persona': persona, 'page_title': 'Delete Persona',
    })
