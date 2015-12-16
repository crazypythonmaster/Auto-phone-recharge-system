from django.db import models
from django.core.urlresolvers import reverse
from django.db.models.signals import pre_save, post_save, pre_delete
from django.dispatch import receiver
from gadjo.requestprovider.signals import get_request
from ppars.apps.core import fields
from ppars.apps.core.models import Plan, Carrier, CompanyProfile, Log


class SellingPriceLevel(models.Model):
    level = models.CharField(max_length=1)
    created = models.DateTimeField('Created at', auto_now_add=True)
    updated = models.DateTimeField(verbose_name='Updated at', auto_now=True)

    def __unicode__(self):
        return u'%s level price' % self.level


class PlanSellingPrice(models.Model):
    carrier = fields.BigForeignKey(Carrier)
    plan = fields.BigForeignKey(Plan)
    company = fields.BigForeignKey(CompanyProfile)
    price_level = models.ForeignKey(SellingPriceLevel)
    selling_price = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    created = models.DateTimeField('Created at', auto_now_add=True)
    updated = models.DateTimeField(verbose_name='Updated at', auto_now=True)

    def __unicode__(self):
        return u'%s level price for %s' % (self.price_level.level, self.plan.plan_id)

    def get_absolute_url(self):
        return reverse('plan_selling_price_list')


def level_price_default():
    return SellingPriceLevel.objects.get(level='1')

list_of_models = ('SellingPriceLevel', 'PlanSellingPrice')

@receiver(pre_save)
def logging_update(sender, instance, **kwargs):
    if instance.pk and sender.__name__ in list_of_models:
        from django.forms.models import model_to_dict

        company = None
        user_str = "System"

        if 'company' in dir(instance) and instance.company:
            company = instance.company

        http_request = get_request()
        if http_request:
            request_user = get_request().user
            user_str = 'User %s' % request_user
            if not company:
                if not request_user.is_authenticated():
                    # if 'User AnonymousUser' == user_str:
                    user_str = 'Anonymous User'
                elif request_user.profile.company:
                    company = request_user.profile.company

        new_values = model_to_dict(instance)
        old_values = sender.objects.get(pk=instance.pk).__dict__
        for key in new_values.keys():
            if key not in old_values.keys():  # because there is a things in new_values that we don't need
                new_values.pop(key, None)
        changed = [key for key in new_values.keys() if ((old_values[key] != new_values[key]) and
                                                        not ((old_values[key] is None and new_values[key] == '')
                                                             or (old_values[key] == '' and new_values[key] is None)))]
        if len(changed) > 0:
            update = ''
            for key in changed:
                update += key.replace('_', ' ').upper() + ': from ' + str(old_values[key]) + ' to ' + str(new_values[key]) + '; '
            note = '%s updated %s: %s \n' % (user_str, sender.__name__, str(instance))
            note += update
            Log.objects.create(company=company, note=note)