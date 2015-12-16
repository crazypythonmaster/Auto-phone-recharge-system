from django.contrib import admin
from .models import SellingPriceLevel, PlanSellingPrice


class PlanSellingPriceAdmin(admin.ModelAdmin):
    list_filter = ('company', 'carrier', 'plan', 'price_level')
admin.site.register(PlanSellingPrice, PlanSellingPriceAdmin)
admin.site.register(SellingPriceLevel)



