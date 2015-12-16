from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required
from ppars.apps.price.views import PlanSellingPriceList, PlanSellingPriceUpdate


urlpatterns = patterns('',
    url(r'^/$', login_required(PlanSellingPriceList.as_view()), name="plan_selling_price_list"),
    url(r'^/(?P<pk>\d+)/$', login_required(PlanSellingPriceUpdate.as_view()), name='plan_selling_price_update'),
)
