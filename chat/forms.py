from django import forms


class ChatForm(forms.Form):
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 3,
            'autofocus': True,
            'placeholder': 'Type message or /cmd...',
        }),
    )


class ModelForm(forms.Form):
    model = forms.ChoiceField(choices=[])
