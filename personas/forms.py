from django import forms


class PersonaForm(forms.Form):
    name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'autofocus': True}))
    system_prompt = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 5}),
        help_text='How should the AI behave? e.g. "You are a helpful coding tutor."',
    )
    is_default = forms.BooleanField(required=False)
