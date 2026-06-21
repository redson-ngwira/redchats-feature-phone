from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.conf import settings

from .forms import LoginForm, RegisterForm, ProfileForm
from .models import UserProfile


def login_view(request):
    if request.user.is_authenticated:
        return redirect('chat:chat')
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            phone = form.cleaned_data['phone']
            pin = form.cleaned_data['pin']
            try:
                user = UserProfile.objects.get(phone=phone)
                if user.check_pin(pin):
                    login(request, user)
                    return redirect('chat:chat')
            except UserProfile.DoesNotExist:
                pass
            form.add_error(None, 'Invalid phone or PIN.')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form, 'page_title': 'Login'})


def register_view(request):
    if request.user.is_authenticated:
        return redirect('chat:chat')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            phone = form.cleaned_data['phone']
            if UserProfile.objects.filter(phone=phone).exists():
                form.add_error('phone', 'Phone already registered.')
            else:
                user = UserProfile(
                    phone=phone,
                    username=phone,
                    display_name=form.cleaned_data.get('display_name', ''),
                )
                user.set_pin(form.cleaned_data['pin'])
                user.save()
                login(request, user)
                return redirect('chat:chat')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form, 'page_title': 'Register'})


def logout_view(request):
    logout(request)
    return redirect('accounts:login')


@login_required
def profile_view(request):
    model_choices = settings.CEREBRAS_MODELS
    if request.method == 'POST':
        form = ProfileForm(request.POST)
        form.fields['default_model'].choices = model_choices
        if form.is_valid():
            request.user.display_name = form.cleaned_data['display_name']
            request.user.default_model = form.cleaned_data['default_model']
            request.user.save()
            return redirect('accounts:profile')
    else:
        form = ProfileForm(initial={
            'display_name': request.user.display_name,
            'default_model': request.user.default_model,
        })
        form.fields['default_model'].choices = model_choices
    return render(request, 'accounts/profile.html', {'form': form, 'page_title': 'Settings'})


def home_view(request):
    if request.user.is_authenticated:
        return redirect('chat:chat')
    return redirect('accounts:login')
