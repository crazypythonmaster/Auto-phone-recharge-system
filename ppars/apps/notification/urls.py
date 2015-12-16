from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required

from views import SpamMessageCreate, CustomPreChargeMessageDetail, WelcomeEmailList, WelcomeEmailCreate,\
    WelcomeEmailEdit, welcome_message_delete


urlpatterns = patterns('',
    url(r'^create/$', login_required(SpamMessageCreate.as_view()), name='sms_create'),
    url(r'^precharge/$', login_required(CustomPreChargeMessageDetail.as_view()), name='custom_message'),
    url(r'^welcome_email/$', login_required(WelcomeEmailList.as_view()), name='welcome_email'),
    url(r'^welcome_email_create/$', login_required(WelcomeEmailCreate.as_view()), name='welcome_email_create'),
    url(r'^welcome_email_edit/(?P<pk>\d+)/$', login_required(WelcomeEmailEdit.as_view()), name='welcome_email_edit'),
    url(r'^welcome_message_delete/(?P<pk>\d+)/$', login_required(welcome_message_delete),
        name='welcome_message_delete'),
)
