from django.conf import settings
from django.db import models
from encrypted_fields import EncryptedFieldMixin
from south.modelsinspector import add_introspection_rules


class EncryptedDateField(EncryptedFieldMixin, models.DateField):
    pass

if 'south' in settings.INSTALLED_APPS:
    add_introspection_rules([], [r"^ppars\.apps\.card\.fields\.EncryptedDateField"])