from django import forms


class LoginForm(forms.Form):
    phone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'inputmode': 'tel', 'autofocus': True}),
    )
    pin = forms.CharField(
        max_length=6, min_length=4,
        widget=forms.PasswordInput(attrs={'inputmode': 'numeric'}),
    )


class RegisterForm(forms.Form):
    phone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'inputmode': 'tel', 'autofocus': True}),
    )
    display_name = forms.CharField(
        max_length=50, required=False,
        widget=forms.TextInput(attrs={}),
    )
    pin = forms.CharField(
        max_length=6, min_length=4,
        widget=forms.PasswordInput(attrs={'inputmode': 'numeric'}),
    )
    pin_confirm = forms.CharField(
        max_length=6, min_length=4,
        widget=forms.PasswordInput(attrs={'inputmode': 'numeric'}),
    )

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('pin') != cleaned.get('pin_confirm'):
            raise forms.ValidationError('PINs do not match.')
        return cleaned


class ProfileForm(forms.Form):
    display_name = forms.CharField(max_length=50, required=False)
    default_model = forms.ChoiceField(choices=[])
