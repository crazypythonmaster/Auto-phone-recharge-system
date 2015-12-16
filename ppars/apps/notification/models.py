import json
from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models.signals import pre_save, post_save, pre_delete
from django.dispatch import receiver
import requests, random
from twilio.rest import TwilioRestClient
from datetime import datetime, timedelta
from ppars.apps.core import fields
from ppars.apps.core.models import CompanyProfile, Customer, Log, UserProfile, Carrier, PhoneNumber

from gadjo.requestprovider.signals import get_request


class Notification(models.Model):
    MAIL = 'EM'
    SMS = 'SM'
    SMS_EMAIL = 'SE'
    BOTH = 'B'
    GV_SMS = 'GV'

    SUCCESS = 'S'
    ERROR = 'E'

    SEND_TYPE_CHOICES = (
        (MAIL, 'Email'),
        (SMS, 'Sms'),
        (SMS_EMAIL, 'Sms via email'),
        (BOTH, 'Sms and email'),
        (GV_SMS, 'Sms via Google Voice'),
    )

    STATUS_TYPE_CHOICES = (
        (SUCCESS, 'Success'),
        (ERROR, 'Error'),
    )

    company = fields.BigForeignKey(CompanyProfile)
    customer = fields.BigForeignKey(Customer, null=True)

    email = models.EmailField(blank=True)
    phone_number = models.CharField(max_length=10, blank=True)
    subject = models.TextField()
    body = models.TextField()
    send_with = models.CharField(max_length=2, choices=SEND_TYPE_CHOICES, null=True)
    status = models.CharField(max_length=3, choices=STATUS_TYPE_CHOICES, null=True)
    adv_status = models.TextField()
    created = models.DateTimeField('Created at', auto_now_add=True)

    def __unicode__(self):
        return u'%s' % self.subject

    def send_twilio_sms(self, twilio_sid, twilio_auth_token, twilio_number):
        if not settings.TEST_MODE:
            client = TwilioRestClient(twilio_sid, twilio_auth_token)
            client.messages.create(from_="+1%s" % twilio_number,
                                   to="+1%s" % self.phone_number,
                                   body=self.body.replace('<br/>', '\n'))

    def send_mandrill_email(self, mandrill_key, mandrill_email, body=None):
        if not body:
            body = self.body
        form_fields = {
            "key": mandrill_key,
            "message": {
                "html": body,
                "subject": self.subject,
                "from_email": mandrill_email,
                "to": [{
                    "email": self.email,
                    "type": "to",
                }],
            }
        }
        if not settings.TEST_MODE:
            result = requests.post('https://mandrillapp.com/api/1.0/messages/send.json',
                                   data=json.dumps(form_fields),
                                   headers={'Content-Type': 'application/json'})
            return result

    def send_sms_email(self, sms_email, mandrill_key, mandrill_email):
        self.email = sms_email
        self.subject = ''
        self.body = self.body.replace('<br/>', '\n')
        self.save()
        separator = 140
        for part in [self.body[i:i + separator] for i in range(0, len(self.body), separator)]:
            self.send_mandrill_email(mandrill_key, mandrill_email, body=part)

    # method to randomize the message body with different synonyms
    def randomize_msg_body(self, body):
        words = {'Hi ': ('Hello ', 'Hey ', 'Greetings ', 'Hi '),
                 ' going ': (' in process ', ' going '),
                 ' your card ': (' your card ', ' your credit card ', ' your CC '),
                 ' funds ': (' money ', ' funds ', ' finances '),
                 'Regards': ('Best wishes', 'Sincerely', 'Regards'),
                 'scheduled': ('future', 'scheduled'),
                 'errored': ('errored', 'failed'),
                 'amount': ('quantity', 'amount'),
                 'customer': ('user', 'customer')
                 }
        print 'Old body: %s' % body
        for word in words:
            if word in body:
                new_word = random.choice(words[word])
                body = body.replace(word, new_word)
        print 'New body: %s' % body
        return body

    def send_notification(self, i=None):
        try:
            if self.MAIL == self.send_with or self.BOTH == self.send_with:
                self.send_mandrill_email(self.company.mandrill_key,
                                         self.company.mandrill_email)
            elif self.SMS_EMAIL == self.send_with or self.BOTH == self.send_with:
                for phone_number in PhoneNumber.objects.filter(customer=self.customer, use_for_sms_email=True):
                    self.send_sms_email(phone_number.number+'@'+phone_number.sms_gateway.gateway,
                                        self.company.mandrill_key,
                                        self.company.mandrill_email)
            elif self.SMS == self.send_with or self.BOTH == self.send_with:
                if 'please, reply' not in self.body.lower():
                    self.body = '%s\nPlease, do not reply' % self.body
                self.send_twilio_sms(self.company.twilio_sid,
                                     self.company.twilio_auth_token,
                                     self.company.twilio_number)
            elif (self.GV_SMS == self.send_with or self.BOTH == self.send_with) and self.company.gvoice_enabled:
                # Sending Google Voice Notification with random delay
                from ppars.apps.notification.tasks import send_gvoice_sms
                self.body = self.randomize_msg_body(self.body) # to save new body in notification
                text = self.body.replace('<br/>', '\n')
                if i:
                    count = i
                else:
                    count = 1
                seconds = 60 + random.choice(range(-10, 11))
                send_gvoice_sms.apply_async(args=[self.company.gvoice_email, self.company.gvoice_pass, self.phone_number, text],
                                            countdown=count*seconds)
            self.status = self.SUCCESS
            self.adv_status = 'Notification sent succesfully'
        except Exception, e:
            self.adv_status = 'Notification not sent because: "%s"' % e
            self.status = self.ERROR
            raise Exception(e)
        finally:
            self.save()


class BulkPromotion(models.Model):
    # In feature there will be more that one sending method
    # TWILIO = 'T'
    # SEND_TYPE_CHOICES = (
    #     (TWILIO, 'Twilio')
    # )
    # send_with = models.CharField(max_length=2, choices=SEND_TYPE_CHOICES, default=TWILIO)
    body = models.TextField(blank=False, null=False)

    def __unicode__(self):
        if len(self.body) > 75:
            return self.body[0:75] + '...'
        return self.body

    def save(self, *args, **kwargs):
        from ppars.apps.notification.tasks import queue_send_bulk_promotion
        self.body += ' Reply "unsubscribe" to unsubscribe.'
        if not self.pk:
            # send messages only if it was just created
            queue_send_bulk_promotion.delay(self.id)
        super(BulkPromotion, self).save(*args, **kwargs)


class WelcomeEmail(models.Model):
    CASH_WITHOUT_SCHEDULED_REFILL = 'CNS'
    CREDIT_CARD_WITH_SCHEDULED_REFILL = 'CCWS'
    CREDIT_CARD_WITHOUT_SCHEDULED_REFILL = 'CCNS'
    CASH_PREPAYMENT_WITH_SCHEDULED_REFILL = 'CPWS'
    CATEGORIES = (
        (CASH_WITHOUT_SCHEDULED_REFILL, 'Cash, without scheduled refill'),
        (CREDIT_CARD_WITH_SCHEDULED_REFILL, 'Credit Card, with scheduled refill'),
        (CREDIT_CARD_WITHOUT_SCHEDULED_REFILL, 'Credit Card, without scheduled refill'),
        (CASH_PREPAYMENT_WITH_SCHEDULED_REFILL, 'Cash PrePayment, with scheduled refill')
    )
    company = fields.BigForeignKey(CompanyProfile)
    body = models.TextField()
    category = models.CharField(max_length=4, choices=CATEGORIES, null=True)
    enabled = models.BooleanField(default=False)


# for sending sms via email
class SmsEmailGateway(models.Model):
    name = models.CharField(max_length=50)
    gateway = models.CharField(max_length=50)

    def __unicode__(self):
        return '%s (@%s)' % (self.name, self.gateway)


class SpamMessage(models.Model):
    ALL = 'A'
    ENABLED = 'E'
    DISABLED = 'D'
    NOT_SCHEDULE_OR_DISABLE = 'N'
    MAIL = 'EM'
    SMS = 'SM'
    SMS_EMAIL = 'SE'
    GV_SMS = 'GV'
    CUSTOMER_TYPE_CHOICES = (
        (ALL, 'All customers'),
        (ENABLED, 'Enabled customers'),
        (DISABLED, 'Disabled customers'),
    )
    SCHEDULE_TYPE_CHOICES = (
        (ALL, 'All schedule'),
        (ENABLED, 'Enabled schedule'),
        (DISABLED, 'Disabled schedule'),
        (NOT_SCHEDULE_OR_DISABLE, 'Not Schedule or Disable'),
    )
    SEND_TYPE_CHOICES = (
        (MAIL, 'Email'),
        (SMS, 'Sms'),
        (SMS_EMAIL, 'Sms via email'),
        (GV_SMS, 'Sms via Google Voice'),
    )
    CHARGE_TYPE_CHOICES = (
        (ALL, 'All type'),
        (Customer.CASH, 'Cash'),
        (Customer.CREDITCARD, 'Credit Card'),
    )
    company = fields.BigForeignKey(CompanyProfile)
    message = models.TextField()
    send_with = models.CharField(max_length=2, choices=SEND_TYPE_CHOICES, default=SMS_EMAIL)
    customer_type = models.CharField(max_length=1, choices=CUSTOMER_TYPE_CHOICES, default=ALL)
    schedule_type = models.CharField(max_length=1, choices=SCHEDULE_TYPE_CHOICES, default=ALL)
    carrier = fields.BigForeignKey(Carrier, null=True, blank=True)
    charge_type = models.CharField(max_length=2, choices=CHARGE_TYPE_CHOICES, default=ALL)
    created = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.message

    def get_absolute_url(self):
        return reverse('sms_create')


class NewsMessage(models.Model):
    title = models.CharField(max_length=150, blank=True)
    message = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "News Message"

    def send_mandrill_email(self):
        for company in CompanyProfile.objects.filter(superuser_profile=False):
            if company.email_id:
                form_fields = {
                    "key": CompanyProfile.objects.get(superuser_profile=True).mandrill_key,
                    "message": {
                        "html": self.message,
                        "subject": self.title,
                        "from_email": CompanyProfile.objects.get(superuser_profile=True).mandrill_email,
                        "to": [{
                            "email": company.email_id,
                            "type": "to",
                        }],
                    }
                }
                if not settings.TEST_MODE:
                    requests.post('https://mandrillapp.com/api/1.0/messages/send.json',
                                  data=json.dumps(form_fields),
                                  headers={'Content-Type': 'application/json'})
            for user in UserProfile.objects.filter(company=company,
                                                   updates_email__isnull=False).exclude(updates_email=''):
                emails = [email.strip(' ') for email in user.updates_email.split(',') if email != '']
                for email in emails:
                    form_fields = {
                        "key": CompanyProfile.objects.get(superuser_profile=True).mandrill_key,
                        "message": {
                            "html": self.message,
                            "subject": self.title,
                            "from_email": 'news@ezcloudllc.com',
                            "to": [{
                                "email": email,
                                "type": "to",
                            }],
                        }
                    }
                    if not settings.TEST_MODE:
                        requests.post('https://mandrillapp.com/api/1.0/messages/send.json',
                                      data=json.dumps(form_fields),
                                      headers={'Content-Type': 'application/json'})

    def send_ez_cloud_news_mandrill_email(self):
        for email in [email.strip(' ') for email in EzCloudNewsEmails.objects.all()[0].emails.split(',')
                      if email != '']:
            form_fields = {
                "key": CompanyProfile.objects.get(superuser_profile=True).mandrill_key,
                "message": {
                    "html": self.message,
                    "subject": self.title,
                    "from_email": 'news@ezcloudllc.com',
                    "to": [{
                        "email": email,
                        "type": "to",
                    }],
                }
            }
            if not settings.TEST_MODE:
                requests.post('https://mandrillapp.com/api/1.0/messages/send.json',
                              data=json.dumps(form_fields),
                              headers={'Content-Type': 'application/json'})


class EzCloudNewsEmails(models.Model):
    emails = models.TextField(blank=True, default='')


class CustomPreChargeMessage(models.Model):
    company = fields.BigForeignKey(CompanyProfile)
    message = models.TextField(blank=True)
    use_message = models.BooleanField(default=False)

    def __unicode__(self):
        return self.message

    def get_absolute_url(self):
        return reverse('custom_message')


list_of_models = ('CustomPreChargeMessage', 'SpamMessage', 'EzCloudNewsEmails',
                  'NewsMessage')


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


@receiver(post_save)
def logging_create(sender, instance, created, **kwargs):
    if created and sender.__name__ in list_of_models:
        from django.forms.models import model_to_dict

        company = None
        user_str = "System"
        obj_attr = ""

        if 'company' in dir(instance) and instance.company:
            company = instance.company

        http_request = get_request()
        if http_request:
            request_user = http_request.user
            user_str = 'User %s' % request_user
            if not company:
                if not request_user.is_authenticated():
                    # if 'User AnonymousUser' == user_str:
                    user_str = 'Anonymous User'
                elif request_user.profile.company:
                    company = request_user.profile.company

        for key in model_to_dict(instance).keys():
            obj_attr += key.replace('_', ' ').upper() + ': ' + str(model_to_dict(instance)[key]) + '; '
        note = '%s created %s: %s \n %s' % (user_str, sender.__name__, str(instance), obj_attr)
        Log.objects.create(company=company, note=note)


@receiver(pre_delete)
def logging_delete(sender, instance, **kwargs):

    if sender.__name__ in list_of_models:
        from django.forms.models import model_to_dict

        company = None
        user_str = "System"
        obj_attr = ""

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

        for key in model_to_dict(instance).keys():
            obj_attr += key.replace('_', ' ').upper() + ': ' + str(model_to_dict(instance)[key]) + '; '
        note = 'User %s deleted %s: %s \n %s' % (user_str, sender.__name__, str(instance), obj_attr)
        Log.objects.create(company=company, note=note)
