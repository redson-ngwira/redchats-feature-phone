from django import forms


class QuickActionForm(forms.Form):
    label = forms.CharField(max_length=30, widget=forms.TextInput(attrs={'autofocus': True}))
    prompt_template = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={}),
        help_text='Use {input} where user text goes.',
    )
