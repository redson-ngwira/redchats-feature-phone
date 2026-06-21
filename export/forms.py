from django import forms


class ExportForm(forms.Form):
    format = forms.ChoiceField(choices=[
        ('sms', 'SMS Chunks (160 chars)'),
        ('text', 'Plain Text'),
    ])
