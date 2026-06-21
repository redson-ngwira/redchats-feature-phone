from django import forms


class ConversationForm(forms.Form):
    title = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'autofocus': True}))


class RenameForm(forms.Form):
    title = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'autofocus': True}))
