from django.contrib import admin
from ppars.apps.charge.models import Charge, TransactionCharge, ChargeStep


class ChargeAdmin(admin.ModelAdmin):
    list_display = [
        'pk', 'customer', 'autorefill',
    ]
    list_filter = ('company',)


class ChargeStepAdmin(admin.ModelAdmin):
    list_display = [
        'pk', 'charge', 'action', 'status', 'adv_status', 'created',
    ]
    list_filter = ('status',)
    search_fields = ['adv_status', ]

admin.site.register(Charge, ChargeAdmin)
admin.site.register(TransactionCharge)
admin.site.register(ChargeStep, ChargeStepAdmin)
