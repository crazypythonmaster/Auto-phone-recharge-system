from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from encrypted_fields import EncryptedCharField, EncryptedIntegerField

from ppars.apps.core.fields import BigForeignKey
from ppars.apps.core.models import Customer


class Card(models.Model):
    customer = BigForeignKey(Customer, related_name='cards', on_delete=models.CASCADE, null=True)
    number = EncryptedCharField(max_length=255)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    last4_number = models.IntegerField(blank=True)
    expiration_year = EncryptedIntegerField(max_length=255)
    expiration_month = EncryptedIntegerField(max_length=255)

    cvv = EncryptedCharField(max_length=255)

    created = models.DateTimeField("Created at", auto_now_add=True)
    updated = models.DateTimeField(verbose_name="Updated at", auto_now=True)

    class Meta:
        ordering = ('number',)

    def __unicode__(self):
        return self.masked_number

    @property
    def masked_number(self):
        return u'XXXX%s' % self.last4_number

    def set_last4_number(self):
        self.last4_number = self.number[-4:]
        return self.last4_number


@receiver(pre_save, sender=Card)
def set_last4_number(instance, **kwargs):
    instance.set_last4_number()
