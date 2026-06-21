from django import forms


class ShareForm(forms.Form):
    title = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'autofocus': True}))
    content = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}))
    share_type = forms.ChoiceField(choices=[('persona', 'Persona'), ('prompt', 'Prompt')])


class ImportForm(forms.Form):
    share_code = forms.CharField(
        max_length=6,
        widget=forms.TextInput(attrs={'autofocus': True, 'style': 'text-transform:uppercase'}),
    )
