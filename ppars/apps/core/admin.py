from django.contrib import admin
from django.contrib.auth.models import User
from .models import Plan, Carrier, UserProfile, AutoRefill, ImportLog,\
    CompanyProfile, PhoneNumber, Log, \
    CommandLog, Customer, CaptchaLogs, CarrierAdmin, UnusedPin, Transaction, \
    PlanDiscount, TransactionStep, ConfirmDP, PinReport, News, TransactionError, \
    PinField, WrongResultRedFin
from django_summernote.admin import SummernoteModelAdmin
import tasks


class AutoRefillAdmin(admin.ModelAdmin):
    list_display = [
        'pk', 'customer', 'phone_number', 'plan', 'pin', 'refill_type',
        'renewal_date', 'last_renewal_status', 'last_renewal_date', 'schedule',
        'trigger', 'enabled',
    ]
    list_filter = ('schedule', 'company', 'trigger', 'refill_type', 'enabled',)

    date_hierarchy = 'renewal_date'


class TransactionStepAdmin(admin.ModelAdmin):
    list_display = [
        'pk', 'transaction', 'operation', 'action', 'created', 'adv_status'
    ]
    search_fields = ['adv_status']


class TransactionErrorAdmin(admin.ModelAdmin):
    list_display = ['transaction', 'step', 'message', 'created']
    search_fields = ['message']


def restart_transaction(modeladmin, request, queryset):
    for obj in queryset:
        tasks.queue_refill.delay(obj.id)


restart_transaction.short_description = "restart transaction"


class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        'pk', 'autorefill', 'trigger', 'state',  'paid', 'completed', 'pin_error',
        'status', 'current_step', 'retry_count', 'locked', 'triggered_by',
        'started', 'ended'
    ]

    list_filter = ('company', 'locked', 'paid', 'state', 'status', 'completed',
                   'trigger', 'pin_error')

    actions = [restart_transaction]
    # todo: uncomment
    # date_hierarchy = 'started'


class PhoneNumberAdmin(admin.ModelAdmin):
    list_display = ['number', 'customer']
    list_filter = ['company']
    search_fields = ['number', 'customer__first_name', 'customer__last_name']


class CustomerAdmin(admin.ModelAdmin):
    list_filter = ['company']
    search_fields = ['company__company_name', 'first_name', 'middle_name', 'last_name', 'company__id', 'id']


class NewsAdmin(SummernoteModelAdmin):
    pass


class LogAdmin(admin.ModelAdmin):
    list_display = ['note', 'company', 'created',]
    list_filter = ['company']
    search_fields = ['note']


class WrongResultRedFinAdmin(admin.ModelAdmin):
    list_display = ['user_profile', 'customer', 'phone_number', 'contract_amount']
    list_filter = ['user_profile']
    search_fields = ['user_profile', 'customer', 'phone_number']

# admin.site.unregister(User)
# admin.site.register(User, UserAdmin)
admin.site.register(CompanyProfile)
admin.site.register(UserProfile)
admin.site.register(Customer, CustomerAdmin)
admin.site.register(PhoneNumber, PhoneNumberAdmin)
admin.site.register(Carrier)
admin.site.register(CarrierAdmin)
admin.site.register(Plan)
admin.site.register(PlanDiscount)
admin.site.register(AutoRefill, AutoRefillAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(TransactionStep, TransactionStepAdmin)
admin.site.register(UnusedPin)
admin.site.register(Log, LogAdmin)
admin.site.register(CaptchaLogs)
admin.site.register(CommandLog)
admin.site.register(ConfirmDP)
admin.site.register(ImportLog)
admin.site.register(PinReport)
admin.site.register(News, NewsAdmin)
admin.site.register(TransactionError, TransactionErrorAdmin)
admin.site.register(PinField)
admin.site.register(WrongResultRedFin, WrongResultRedFinAdmin)
