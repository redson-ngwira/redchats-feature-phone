from django import forms


class ChatForm(forms.Form):
    message = forms.CharField(
        max_length=500,
        widget=forms.Textarea(attrs={
            'rows': 2,
            'cols': 30,
            'autofocus': True,
            'placeholder': 'Type msg or /help...',
            'maxlength': 500,
        }),
    )


class ModelForm(forms.Form):
    model = forms.ChoiceField(choices=[])
