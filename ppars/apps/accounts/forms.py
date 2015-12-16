from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Reset
from django import forms
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.forms import (UserCreationForm, AdminPasswordChangeForm)
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from django.forms import ValidationError
from django.utils.translation import ugettext as _



def validate_password_strength(value):
    """Validates that a password is as least 7 characters long and has at least
    1 digit and 1 letter.
    """
    min_length = 8

    if len(value) < min_length:
        raise ValidationError(_('Password must be at least {0} characters '
                                'long.').format(min_length))

    # check for digit
    if not any(char.isdigit() for char in value):
        raise ValidationError(_('Password must container at least 1 digit.'))

    # check for letter
    if not any(char.isalpha() for char in value):
        raise ValidationError(_('Password must container at least 1 letter.'))

    # check for letter
    if not any(char.islower() for char in value):
        raise ValidationError(_('Password must container at least 1 lower case letter.'))

    # check for letter
    if not any(char.isupper() for char in value):
        raise ValidationError(_('Password must container at least 1 upper case letter.'))


class StrengthSetPasswordForm(SetPasswordForm):

    def __init__(self, *args, **kwargs):
        super(StrengthSetPasswordForm, self).__init__(*args, **kwargs)
        self.fields['new_password1'].validators.append(validate_password_strength)
        self.fields['password1'].help_text ='Min length 8 characters. Password must container at least 1 digit, 1 lower case letter, 1 upper case letter.'


class StrengthUserCreationForm(UserCreationForm):

    def __init__(self, *args, **kwargs):
        super(StrengthUserCreationForm, self).__init__(*args, **kwargs)
        self.fields['password1'].validators.append(validate_password_strength)
        self.fields['password1'].help_text ='Min length 8 characters. Password must container at least 1 digit, 1 lower case letter, 1 upper case letter.'


class StrengthAdminPasswordChangeForm(AdminPasswordChangeForm):

    def __init__(self, *args, **kwargs):
        super(StrengthAdminPasswordChangeForm, self).__init__(*args, **kwargs)
        self.fields['password1'].validators.append(validate_password_strength)
        self.fields['password1'].help_text ='Min length 8 characters. Password must container at least 1 digit, 1 lower case letter, 1 upper case letter.'


class PparsStrengthUserCreationForm(StrengthUserCreationForm):
    def __init__(self, *args, **kwargs):
        super(StrengthUserCreationForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-sm-3'
        self.helper.field_class = 'col-sm-5'
        self.helper.form_method = 'post'
        self.helper.form_action = reverse('user_create')

        self.helper.add_input(Submit('submit', 'Add'))
        self.helper.add_input(Reset('reset', 'Cancel'))
        # print self.helper.layout

    class Meta:
        model = User
        fields = ("username", "password1", "password2", "first_name", "last_name", "email")



    # helper.layout = Layout(
    #     'email',
    #     'password',
    #     'remember_me',
    #     StrictButton('Sign in', css_class='btn-default'),
    # )

    # first_name = forms.CharField(required=False)
    # last_name = forms.CharField(required=False)
    # email = forms.EmailField(required=False)

    # def clean_username(self):
    #     data = self.cleaned_data['username'].strip()
    #     if not data:
    #         raise forms.ValidationError("This field is required.")
    #     # login = User.objects.filter(username=data)
    #     # if login.exists():
    #     #     raise forms.ValidationError("user with this login already exist")
    #     return data

    # def clean_first_name(self):
    #     data = self.cleaned_data['first_name'].strip()
    #     return data
    #
    # def clean_last_name(self):
    #     data = self.cleaned_data['last_name'].strip()
    #     return data
    #
    # def clean_email(self):
    #     data = self.cleaned_data['email'].strip()
    #     return data

    # def save(self, commit=True):
    #     login = self.cleaned_data['login']
    #     password = self.cleaned_data['password']
    #     if User.objects.filter(username=login):
    #         user = User.objects.get(username=login)
    #     else:
    #         user = User.objects.create_user(login)
    #     user.set_password(password)
    #     user.first_name = self.cleaned_data['first_name']
    #     user.last_name = self.cleaned_data['last_name']
    #     user.email = self.cleaned_data['email']
    #     user.save()
    #     return user



class UserEditForm(forms.Form):
    login = forms.CharField()
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)
    email = forms.EmailField(required=False)

    def clean_login(self):
        data = self.cleaned_data['login'].strip()
        if not data:
            raise forms.ValidationError("This field is required.")
        # login = User.objects.filter(username=data)
        # if login.exists():
        #     raise forms.ValidationError("user with this login already exist")
        return data

    def clean_first_name(self):
        data = self.cleaned_data['first_name'].strip()
        return data

    def clean_last_name(self):
        data = self.cleaned_data['last_name'].strip()
        return data

    def clean_email(self):
        data = self.cleaned_data['email'].strip()
        return data

    def save(self, commit=True):
        login = self.cleaned_data['login']
        user = User.objects.get(username=login)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        user.save()
        return user