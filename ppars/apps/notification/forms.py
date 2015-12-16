from django import forms
from models import SpamMessage, CustomPreChargeMessage, WelcomeEmail


class SpamMessageForm(forms.ModelForm):
    class Meta:
        model = SpamMessage
        fields = ['message', 'customer_type', 'send_with', 'schedule_type', 'charge_type', 'carrier']


class CustomPreChargeMessageForm(forms.ModelForm):
    class Meta:
        model = CustomPreChargeMessage


class WelcomeEmailForm(forms.ModelForm):
    class Meta:
        model = WelcomeEmail
        exclude = ['company']
