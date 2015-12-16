from django.contrib import admin
from models import Notification, SpamMessage, SmsEmailGateway, BulkPromotion
from ppars.apps.core.models import PhoneNumber, PhoneNumberSettings


class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        'subject', 'send_with', 'status', 'created'
    ]
    list_filter = ('send_with', 'status', 'company')
    search_fields = ['phone_number', 'email', 'subject', 'customer__first_name',
                     'customer__last_name']


class BulkPromotionAdmin(admin.ModelAdmin):

    def render_change_form(self, request, context, *args, **kwargs):
        # here we define a custom template
        self.change_form_template = 'admin/notification/bulkpromotionadmin.html'
        extra = {
            'phone_number_count': str(len(PhoneNumber.objects.all().values('number').distinct())) +
                                  ' phone numbers in the system (' +
                                  str(len(PhoneNumberSettings.objects.filter(bulk_promotion_subscription=True)
                                          .values('phone_number__number').distinct())) +
                                  ' subscribed to bulk promotion).'
        }

        context.update(extra)
        return super(BulkPromotionAdmin, self).render_change_form(request, context, *args, **kwargs)


admin.site.register(Notification, NotificationAdmin)
admin.site.register(SpamMessage)
admin.site.register(SmsEmailGateway)
admin.site.register(BulkPromotion, BulkPromotionAdmin)
