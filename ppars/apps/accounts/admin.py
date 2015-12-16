from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.contrib import admin

from ppars.apps.accounts.forms import (StrengthUserCreationForm,
    StrengthAdminPasswordChangeForm)


class StrengthUserAdmin(UserAdmin):
    add_form = StrengthUserCreationForm
    change_password_form = StrengthAdminPasswordChangeForm

# registration
admin.site.unregister(User)
admin.site.register(User, StrengthUserAdmin)