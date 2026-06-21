from django import forms


class MemoryForm(forms.Form):
    key = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'autofocus': True}))
    value = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}))
