from django.contrib.auth.signals import user_logged_out
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from .models import UserProfile, CompanyProfile, Customer
from django.dispatch import receiver
from django.contrib import messages


#@receiver(user_logged_out)
#def on_user_logged_out(sender, request, **kwargs):
#    messages.add_message(request, messages.INFO, 'Logged out.')


@receiver(post_save, sender=User, dispatch_uid="create_user_profile")
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        company = None

        UserProfile.objects.create(
            user=instance,
            company=company,
            superuser_profile=instance.is_superuser
        )
    if instance.is_superuser:
        p = instance.profile
        p.superuser_profile = instance.is_superuser
        if not p.company:
            company, created = CompanyProfile.objects.get_or_create(
                superuser_profile=instance.is_superuser,
                defaults={
                    'company_name': "%s's Company" % instance.username,
                    'updated': False,
                }
            )
            p.company = company
        p.save()


# Customer.objects.create(user=instance, first_name="Walk-In", last_name="Customer", enabled=True)

# post_save.connect(create_user_profile, sender=User, dispatch_uid="create_user_profile")

# def create_first_customer(sender, instance, created, **kwargs):
#     Customer.objects.create(user=instance.user, first_name="Walk-In", last_name="Customer", enabled=True)
#
# post_save.connect(create_first_customer, sender=CompanyProfile, dispatch_uid="create_first_customer")