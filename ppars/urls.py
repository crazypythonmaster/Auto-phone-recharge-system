from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.conf.urls.static import static
from ppars.apps.accounts.views import UserList, UserCreate, UserUpdate, \
    UserDelete
from ppars.apps.charge.views import ChargeList, ChargeDetail, ajax_charge_steps, \
    ajax_mark_charge, ajax_cc_retry, ajax_cc_refund, ajax_cc_void, \
    ajax_charge_create, ajax_charges_list, ajax_change_charge_note, ajax_cc_retry_and_trans_restart
from ppars.apps.core import views
from ppars.apps.notification.views import ez_cloud_news_emails, change_ez_email_list
from ppars.apps.api import views as api
from ppars.apps.search.views import ajax_search, search, ajax_search_dropdown
# Uncomment the next two lines to enable the admin:
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',

    #url(r'^login/$', 'django.contrib.auth.views.login'),
    url(r'^login/$', 'ppars.apps.accounts.views.login_user'),
    url(r'^logout.*', 'django.contrib.auth.views.logout', {'next_page': '/login/'}),
    url(r'^user/password-change/$', 'django.contrib.auth.views.password_change', name="password_change"),
    url(r'^user/password-change-done/$', 'django.contrib.auth.views.password_change_done', name="password_change_done"),

    url(r'^password/reset/$', 'django.contrib.auth.views.password_reset',
        {'post_reset_redirect': 'password_reset_done'}, name='password_reset'),
    #TODO normalize tokens
    url(r'^password/reset/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>.+)/$',
       'django.contrib.auth.views.password_reset_confirm',
        {'post_reset_redirect': 'password_reset_complete'},
        name='password_reset_confirm'),
    url(r'^password/reset/complete/$', 'django.contrib.auth.views.password_reset_complete',
        name='password_reset_complete'),
    url(r'^password/reset/done/$', 'django.contrib.auth.views.password_reset_done',
        name='password_reset_done'),

    url(r'^user/profile/$', login_required(views.CompanyProfileUpdate.as_view()), name="profile"),
    url(r'^change_user/$', login_required(views.change_user), name="change_user"),

    #API
    url(r'^ajax_ez_news/$', api.ajax_ez_news, name="ajax_ez_news"),

    # Ez Cloud News
    url(r'^ez_cloud_news_emails/$', login_required(ez_cloud_news_emails), name="ez_cloud_news_emails"),
    url(r'^change_ez_email_list/$', login_required(change_ez_email_list), name="change_ez_email_list"),

    url(r'^home/$', login_required(views.Home.as_view()), name="home"),
    url(r'^search/$', login_required(search), name="search"),
    url(r'^ajax_search/$', login_required(ajax_search), name="ajax_search"),
    url(r'^ajax_search_dropdown/$', login_required(ajax_search_dropdown), name="ajax_search_dropdown"),
    url(r'^ajax_refill_as_walk_in/$', login_required(views.ajax_refill_as_walk_in), name="ajax_refill_as_walk_in"),

    url(r'^customer$', login_required(views.CustomerList.as_view()), name="customer_list"),
    url(r'^customer/create/$', login_required(views.CustomerCreate.as_view()), name='customer_create'),
    url(r'^customer/(?P<pk>\d+)/$', login_required(views.CustomerUpdate.as_view()), name='customer_update'),
    url(r'^customer/(?P<pk>\d+)/delete/$', login_required(views.CustomerDelete.as_view()), name='customer_delete'),
    url(r'^customer/export/$', login_required(views.CustomerExport.as_view()), name='customer_export'),
    url(r'^customer/import/$', login_required(views.CustomerImport.as_view()), name='customer_import'),
    url(r'^customer/transactions/(?P<pk>\d+)/$', login_required(views.customer_transactions), name='customer_transactions'),
    url(r'^ajax_customer_transactions/$', login_required(views.ajax_customer_transactions), name='ajax_customer_transactions'),
    url(r'^customer/autorefills/(?P<pk>\d+)/$', login_required(views.customer_autorefills), name='customer_autorefills'),
    url(r'^ajax_customer_autorefills/$', login_required(views.ajax_customer_autorefills), name='ajax_customer_autorefills'),
    url(r'^customer/cc_charges/(?P<pk>\d+)/$', login_required(views.customer_cc_charges), name='customer_cc_charges'),
    url(r'^ajax_customer_cc_charges/$', login_required(views.ajax_customer_cc_charges), name='ajax_customer_cc_charges'),
    url(r'swipe_and_refill', login_required(views.SwipeAndRefill.as_view()), name="swipe_and_refill"),
    url(r'^ajax_check_duplicate_number/$', login_required(views.ajax_check_duplicate_number), name='ajax_check_duplicate_number'),

    url(r'^news$', login_required(views.news), name="news"),
    url(r'^news/(?P<pk>\d+)/$', login_required(views.NewsDetail.as_view()), name='news_detail'),
    url(r'^ajax_news/$', login_required(views.ajax_news), name='ajax_news'),
    url(r'^close_updates$', login_required(views.close_updates), name='close_updates'),

    url(r'^plan$', login_required(views.PlanList.as_view()), name="plan_list"),
    url(r'^plan/create/$', login_required(views.PlanCreate.as_view()), name='plan_create'),
    url(r'^plan/(?P<pk>\d+)/$', login_required(views.PlanUpdate.as_view()), name='plan_update'),
    url(r'^plan/(?P<pk>\d+)/delete/$', login_required(views.PlanDelete.as_view()), name='plan_delete'),
    url(r'^plan/export/$', login_required(views.PlanExport.as_view()), name='plan_export'),
    url(r'^plan/import/$', login_required(views.PlanImport.as_view()), name='plan_import'),

    url(r'^plan-discount$', login_required(views.PlanDiscountList.as_view()), name="plan_discount_list"),
    url(r'^plan-discount/create/$', login_required(views.PlanDiscountCreate.as_view()), name='plan_discount_create'),
    url(r'^plan-discount/(?P<pk>\d+)/$', login_required(views.PlanDiscountUpdate.as_view()), name='plan_discount_update'),

    url(r'^carrier$', login_required(views.CarrierList.as_view()), name="carrier_list"),
    url(r'^carrier/create/$', login_required(views.CarrierCreate.as_view()), name='carrier_create'),
    url(r'^carrier/(?P<pk>\d+)/$', login_required(views.CarrierUpdate.as_view()), name='carrier_update'),
    url(r'^carrier/(?P<pk>\d+)/delete/$', login_required(views.CarrierDelete.as_view()), name='carrier_delete'),
    url(r'^carrier/export/$', login_required(views.CarrierExport.as_view()), name='carrier_export'),
    url(r'^carrier/import/$', login_required(views.CarrierImport.as_view()), name='carrier_import'),

    url(r'^carrier-admin$', login_required(views.CarrierAdminList.as_view()), name="carrier_admin_list"),
    url(r'^carrier-admin/create/$', login_required(views.CarrierAdminCreate.as_view()), name='carrier_admin_create'),
    url(r'^carrier-admin/(?P<pk>\d+)/$', login_required(views.CarrierAdminUpdate.as_view()), name='carrier_admin_update'),

    url(r'^manualrefill$', login_required(views.ManualRefill.as_view()), name="manualrefill"),

    url(r'^autorefill$', login_required(views.AutoRefillList.as_view()), name="autorefill_list"),
    url(r'^autorefill/create/$', login_required(views.AutoRefillCreate.as_view()), name='autorefill_create'),
    url(r'^autorefill/(?P<pk>\d+)/$', login_required(views.AutoRefillUpdate.as_view()), name='autorefill_update'),
    url(r'^autorefill/(?P<pk>\d+)/delete/$', login_required(views.AutoRefillDelete.as_view()), name='autorefill_delete'),
    url(r'^autorefill/export/$', login_required(views.AutoRefillExport.as_view()), name='autorefill_export'),
    url(r'^autorefill/import/$', login_required(views.AutoRefillImport.as_view()), name='autorefill_import'),
    url(r'^ajax_check_for_similar_scheduled_refill/$', login_required(views.ajax_check_for_similar_scheduled_refill), name='ajax_check_for_similar_scheduled_refill'),

    url(r'^ajax_unused_pins$', login_required(views.ajax_unused_pins), name="ajax_unused_pins"),
    url(r'^unused-pin$', login_required(views.UnusedPinList.as_view()), name="unusedpin_list"),
    url(r'^unused-pin/create/$', login_required(views.UnusedPinCreate.as_view()), name='unusedpin_create'),
    url(r'^unused-pin/import/$', login_required(views.UnusedPinImport.as_view()), name='unusedpin_import'),
    url(r'^unused-pin/(?P<pk>\d+)/$', login_required(views.UnusedPinUpdate.as_view()), name='unusedpin_update'),
    url(r'^unused-pin/(?P<pk>\d+)/delete/$', login_required(views.UnusedPinDelete.as_view()), name='unusedpin_delete'),
    url(r'^ajax/ajax_mark_unusedpin/$', login_required(views.ajax_mark_unusedpin), name='ajax_mark_unusedpin'),

    url(r'^transaction$', login_required(views.TransactionList.as_view()), name="transaction_list"),
    url(r'^transaction/(?P<pk>\d+)/$', login_required(views.TransactionDetail.as_view()), name='transaction_detail'),
    url(r'^transaction/(?P<pk>\d+).json$', login_required(views.ajax_transaction), name='ajax_transaction'),

    url(r'^pin-report$', login_required(views.PinReportList.as_view()), name="pinreport_list"),
    url(r'^pin-report/(?P<pk>\d+)/$', login_required(views.PinReportDetail.as_view()), name='pinreport_detail'),
    url(r'^pin-report/compare/$', login_required(views.compare_pins_with_dollarphone), name='compare_pins_with_dollarphone'),
    url(r'^pin-report/download/(?P<order_id>\d+)/$', login_required(views.pinreport_download), name='pinreport_download'),

    url(r'^twilio_request/$', views.twilio_request, name='twilio_request'),
    url(r'^twilio_response/$', views.twilio_response, name='twilio_response'),
    url(r'^pparsb-response/(?P<pk>\d+)/$', views.pparsb_response, name='pparsb_response'),

    url(r'^confirm-dp/$', login_required(views.ConfirmDPView.as_view()), name='confirm_dp'),
    url(r'^logs/$', login_required(views.LogList.as_view()), name="log_list"),

    url(r'^import/customers/from-usaepay/$', login_required(views.import_customers_from_usaepay), name='import_customers_from_usaepay'),
    url(r'^import/customers/from-redfin/$', login_required(views.import_customers_from_redfin), name='import_customers_from_redfin'),
    url(r'^restart_creating_schedules/$', login_required(views.restart_creating_schedule_for_customers_from_redfin), name='restart_creating_schedule_for_customers_from_redfin'),
    url(r'^import/log/$', login_required(views.ImportLogView.as_view()), name='import_log'),
    url(r'^import/customers/phone-numbers/$', login_required(views.PhoneNumbersImport.as_view()), name='import_phone_numbers'),

    # url(r'^core/autorefill-import-json/(?P<pk>[a-z\-\d]+)/$', views.import_autorefill_json, name='autorefill_import_json'),
    # url(r'^core/customer-import-json/(?P<pk>[a-z\-\d]+)/$', views.import_customer_json, name='import_customer_json'),
    url(r'^move_number_to_another_customer/$', login_required(views.ajax_move_number_to_another_customer), name='ajax_move_number_to_another_customer'),
    url(r'^ajax_log$', login_required(views.ajax_log), name='ajax_log'),
    url(r'^ajax_customers_list$', login_required(views.ajax_customers_list), name='ajax_customers_list'),
    url(r'^ajax_carriers_list$', login_required(views.ajax_carriers_list), name='ajax_carriers_list'),
    url(r'^ajax_transactions_list$', login_required(views.ajax_transactions_list), name='ajax_transactions_list'),
    url(r'^ajax_last_transaction_data$', login_required(views.ajax_last_transaction_data), name='ajax_last_transaction_data'),
    url(r'^ajax/phone-number/$', login_required(views.ajax_phone_numbers), name='ajax_phone_numbers'),
    url(r'^ajax/add-phone-number/$', login_required(views.ajax_add_phone_number), name='ajax_add_phone_numbers'),
    url(r'^ajax/carriers/$', login_required(views.ajax_carriers), name='ajax_carriers'),
    url(r'^ajax/carrier/$', login_required(views.ajax_carrier), name='ajax_carrier'),
    url(r'^ajax/carrier-plans/$', login_required(views.ajax_carrier_plans), name='ajax_carrier_plans'),
    url(r'^ajax_skip_next_refill/(?P<pk>\d+)/$', login_required(views.ajax_skip_next_refill), name='skip_next_refill'),
    url(r'^ajax/customers/$', login_required(views.ajax_customers), name='ajax_customers'),
    url(r'^ajax_customer_getaway_and_last_of_cc/$', login_required(views.ajax_customer_getaway_and_last_of_cc), name='ajax_customer_getaway_and_last_of_cc'),
    url(r'^ajax/check_customer_cash/(?P<customer_id>\d+)/$', login_required(views.ajax_check_customer_cash), name='ajax_check_customer_cash'),
    url(r'^ajax/total-transactions/$', login_required(views.ajax_total_transactions), name='ajax_total_transactions'),
    url(r'^ajax/transaction-successrate/$', login_required(views.ajax_transaction_successrate), name='ajax_transaction_successrate'),
    url(r'^ajax/transaction-profits/$', login_required(views.ajax_transaction_profits), name='ajax_transaction_profits'),
    url(r'^ajax/transaction-summary/$', login_required(views.ajax_transaction_summary), name='ajax_transaction_summary'),
    url(r'^ajax/pin-usage/$', login_required(views.ajax_pin_usage), name='ajax_pin_usage'),
    url(r'^ajax_get_plan_selling_price$', login_required(views.ajax_get_plan_selling_price), name='ajax_get_plan_selling_price'),
    url(r'^ajax/mark-transaction/(?P<pk>\d+)/$', login_required(views.ajax_mark_transaction), name='ajax_mark_transaction'),
    url(r'^ajax/apply_send_pin_prerefill', login_required(views.ajax_apply_send_pin_prerefill), name='ajax_apply_send_pin_prerefill'),
    url(r'^ajax/set_default_notification', login_required(views.ajax_set_default_notification), name='ajax_set_default_notification'),
    url(r'^ajax/need-pins-report/$', login_required(views.ajax_need_pins_report), name='ajax_need_pins_report'),
    url(r'^ajax_schedule_monthly/(?P<pk>\d+)/$', login_required(views.ajax_schedule_monthly), name='ajax_schedule_monthly'),
    url(r'ajax_create_schedule_in_customer/(?P<pk>\d+)/$', login_required(views.ajax_create_schedule_in_customer), name='ajax_create_schedule_in_customer'),
    url(r'^ajax_check_manual_transaction_ended/(?P<pk>\d+)/$', login_required(views.ajax_check_manual_transaction_ended), name='ajax_check_manual_transaction_ended'),
    url(r'^ajax_dismiss_urgent/$', login_required(views.ajax_dismiss_urgent), name='ajax_dismiss_urgent'),
    url(r'^ajax/manual_duplication/$', login_required(views.ajax_transaction_duplicates), name='ajax_manual_duplication'),
    url(r'^ajax/ajax_verify_carrier/$', login_required(views.ajax_verify_carrier), name='ajax_verify_carrier'),
    url(r'^ajax/ajax_verify_scheduled_refills/$', login_required(views.ajax_verify_scheduled_refills), name='ajax_verify_scheduled_refills'),
    url(r'^ajax_monthly_refills/$', login_required(views.ajax_monthly_refills), name='ajax_monthly_refills'),
    url(r'^ajax_save_note_of_transaction/(?P<pk>\d+)/$', login_required(views.save_note_of_transaction), name='save_note_of_transaction'),
    # Add pin to unused
    url(r'^ajax/add_pin_to_unused/(?P<transaction_id>\d+)$', login_required(views.ajax_add_pin_to_unused), name='ajax_add_pin_to_unused'),
    url(r'^ajax/ajax_mark_pin_field/$', login_required(views.ajax_mark_pin_field), name='ajax_mark_pin_field'),
    url(r'^ajax/get_pin_status/$', login_required(views.ajax_get_pin_status), name='ajax_get_pin_status'),
    url(r'^ajax/ajax_mark_pinreport/$', login_required(views.ajax_mark_pinreport), name='ajax_mark_pinreport'),
    url(r'^ajax_unused_pins_plan_list$', login_required(views.ajax_unused_pins_plan_list), name='ajax_unused_pins_plan_list'),

    # url(r'^get_workers_status$', login_required(views.get_workers_status), name='get_workers_status'),

     #  Price app
    url(r'^plan_selling_price', include('ppars.apps.price.urls')),

    # charge app
    url(r'^charge$', login_required(ChargeList.as_view()), name="charge_list"),
    url(r'^charge/(?P<pk>\d+)/$', login_required(ChargeDetail.as_view()), name='charge_detail'),
    url(r'^charge/(?P<pk>\d+).json$', login_required(ajax_charge_steps), name='ajax_charge_steps'),
    url(r'^ajax/charge-create/$', login_required(ajax_charge_create), name='ajax_charge_create'),
    url(r'^ajax_charges_list/$', login_required(ajax_charges_list), name='ajax_charges_list'),
    url(r'^ajax_change_charge_note/$', login_required(ajax_change_charge_note), name='ajax_change_charge_note'),


    url(r'^ajax/mark-charge/$', login_required(ajax_mark_charge), name='ajax_mark_charge'),
    url(r'^ajax/cc-retry-and-trans-restart/$', login_required(ajax_cc_retry_and_trans_restart), name='ajax_cc_retry_and_trans_restart'),
    url(r'^ajax/cc-retry/$', login_required(ajax_cc_retry), name='ajax_cc_retry'),
    url(r'^ajax/cc-refund/$', login_required(ajax_cc_refund), name='ajax_cc_refund'),
    url(r'^ajax/cc-void/$', login_required(ajax_cc_void), name='ajax_cc_void'),

    # accounts app
    url(r'^user$', login_required(UserList.as_view()), name="user_list"),
    url(r'^user/create/$', login_required(UserCreate.as_view()), name='user_create'),
    url(r'^user/(?P<pk>\d+)/$', login_required(UserUpdate.as_view()), name='user_update'),
    url(r'^user/(?P<pk>\d+)/delete/$', login_required(UserDelete.as_view()), name='user_delete'),

    # notification apps
    url(r'^sms/', include('ppars.apps.notification.urls')),

    # default sending logic temporary link
    url(r'^back-customer-notification/', login_required(views.BackCustomerNotification.as_view()), name='back_customer_notification'),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^$',  login_required(views.Home.as_view())),

    # WYSIWYG
    (r'^summernote/', include('django_summernote.urls'))

) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)