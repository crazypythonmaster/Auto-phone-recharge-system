from django import forms
from ppars.apps.price.models import PlanSellingPrice


class PlanSellingPriceForm(forms.ModelForm):

    # def clean(self):
    #     cleaned_data = super(PlanSellingPriceForm, self).clean()
    #     if self.instance.id:
    #         psp = PlanSellingPrice.objects.exclude(id=self.instance.id).filter(plan=cleaned_data['plan'],
    #                                                price_level=cleaned_data['price_level'],
    #                                                company_id=cleaned_data['company'])
    #     else:
    #         psp = PlanSellingPrice.objects.filter(plan=cleaned_data['plan'],
    #                                               price_level=cleaned_data['price_level'],
    #                                               company_id=cleaned_data['company'])
    #     if psp.exists():
    #         raise forms.ValidationError('Selling price level already exists for this plan.')
    #     return cleaned_data

    class Meta:
        model = PlanSellingPrice
        fields = ['carrier', 'plan', 'company', 'selling_price', 'price_level']