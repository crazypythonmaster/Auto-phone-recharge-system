from django.views.generic import ListView
from django.views.generic.edit import UpdateView
from ppars.apps.price.models import PlanSellingPrice
from ppars.apps.price.forms import PlanSellingPriceForm


class PlanSellingPriceList(ListView):
    model = PlanSellingPrice

    def get_queryset(self):
        return PlanSellingPrice.objects.filter(company=self.request.user.profile.company)


class PlanSellingPriceUpdate(UpdateView):
    model = PlanSellingPrice
    form_class = PlanSellingPriceForm