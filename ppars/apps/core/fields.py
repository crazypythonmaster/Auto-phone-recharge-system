from django.conf import settings
from south.modelsinspector import add_introspection_rules
from django.db.models.fields.related import OneToOneField
from django.db.models.fields import BigIntegerField
from django.db import models


class BigForeignKey(models.ForeignKey):

    def db_type(self, connection):
        return BigIntegerField().db_type(connection=connection)


class BigOneToOneField(BigForeignKey, OneToOneField):
    """
    If you use subclass model, you might need to name
    the `ptr` field explicitly. This is the field type you
    might want to use. Here is an example:

    class Base(models.Model):
        title = models.CharField(max_length=40, verbose_name='Title')

    class Concrete(Base):
        base_ptr = fields.BigOneToOneField(Base)
        ext = models.CharField(max_length=12, null=True, verbose_name='Ext')
    """
    pass


class BigAutoField(models.fields.AutoField):
    def db_type(self, connection):
        if 'mysql' in connection.__class__.__module__:
            return 'bigint AUTO_INCREMENT'
        elif 'postgresql' in connection.__class__.__module__:
            return 'bigserial'
        return super(BigAutoField, self).db_type(connection)


if 'south' in settings.INSTALLED_APPS:
    add_introspection_rules([], [r"^ppars\.apps\.core\.fields\.BigAutoField"])
    add_introspection_rules([], [r"^ppars\.apps\.core\.fields\.BigForeignKey"])
    add_introspection_rules([], [r"^ppars\.apps\.core\.fields\.BigOneToOneField"])