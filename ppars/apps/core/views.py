import uuid
import logging
import datetime
import json
import calendar
import csv
import traceback
import pytz
import requests
from requests.auth import HTTPBasicAuth
import xlrd
import operator
import re
from dateutil.relativedelta import relativedelta
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.template.defaultfilters import slugify
from django.views.generic import ListView, DetailView
from django.views.generic.edit import View, CreateView, DeleteView, UpdateView
from django.utils import timezone as django_tz
from django.core.validators import validate_email
from django.forms import ValidationError
from django.db.models import Q
from lxml import etree
from pytz import timezone
import ext_lib
import forms
from models import Customer, AutoRefill, Transaction, TransactionStep, Plan, Carrier,\
    UnusedPin, CarrierAdmin,  PlanDiscount, CompanyProfile, \
    ConfirmDP, ImportLog, PinReport, Log, UserProfile, News, PhoneNumber, \
    SUCCESS, WAITING, ERROR, TransactionCreatedFromTo, PinField
from ppars.apps.charge.models import Charge, TransactionCharge
from ppars.apps.core import verify_carrier
from ppars.apps.notification.tasks import notification_about_status_of_pin
from tasks import queue_refill, queue_customer_import, queue_autorefill_import,\
    queue_import_customers_from_usaepay, \
    queue_compare_pins_with_dollarphone, queue_import_phone_numbers, \
    queue_prerefill, back_from_logs, queue_import_customers_from_redfin, \
    restart_auto_creating_schedules_refill, verify_scheduled_refills
from ppars.apps.notification.models import SmsEmailGateway
logger = logging.getLogger('ppars')


class Home(View):
    template_name = 'core/home.html'

    def get(self, request, *args, **kwargs):
        today = datetime.datetime.now(timezone('US/Eastern')).date()
        if request.user.is_superuser:
            refills = AutoRefill.objects.filter(enabled=True, renewal_date=today, trigger=AutoRefill.TRIGGER_SC)
        else:
            refills = AutoRefill.objects.filter(company=request.user.profile.company, enabled=True, renewal_date=today,
                                                trigger=AutoRefill.TRIGGER_SC)
        urgent_update = {}
        if News.objects.filter(category='UU').order_by('-created'):
            if News.objects.filter(category='UU').order_by('-created')[0].created.date() + datetime.timedelta(days=1)\
                    > datetime.datetime.now(timezone('US/Eastern')).date() and request.user.profile.show_urgent:
                urgent_update = {'title': News.objects.filter(category='UU').order_by('-created')[0],
                                 'id': News.objects.filter(category='UU').order_by('-created')[0].id}

        return render(request, self.template_name, {'autorefill_list': refills,
                                                    'sellingprices': request.user.profile.company.sellingprices_amount_for_week(),
                                                    'date_gmt': datetime.datetime.now(),
                                                    'last_updates': News.objects.order_by('-created')[:2],
                                                    'show_updates': request.user.profile.company.show_updates,
                                                    'urgent_update': urgent_update
                                                    })


class SwipeAndRefill(View):
    form_class = forms.SwipeAndRefillForm
    model = Customer
    template_name = 'core/swipe_and_refill.html'

    def get(self, request, *args, **kwargs):
        if not request.user.profile.company.can_swipe_card_in_search:
            return HttpResponseRedirect('/')
        form = forms.SwipeAndRefillForm()
        return render(request, self.template_name,
                      {
                          'form': form,
                          'use_sellercloud': request.user.profile.company.use_sellercloud,
                          'sms_email_gateways': [(gateway.id, gateway.__unicode__())
                                                 for gateway in SmsEmailGateway.objects.all()]
                      })

    def post(self, request, *args, **kwargs):
        if not request.user.profile.company.can_swipe_card_in_search:
            return HttpResponseRedirect('/')
        form = forms.SwipeAndRefillForm(request.POST, request=request)
        if request.is_ajax():
            if not form.is_valid():
                return HttpResponse(json.dumps({'status': 'error', 'errors': form.errors}))
        if form.is_valid():
            self.object = customer = form.save(commit=True)
            customer.user = request.user
            customer.company = request.user.profile.company
            if not customer.charge_getaway:
                if customer.company.cccharge_type and customer.charge_type == Customer.CREDITCARD:
                    customer.charge_getaway = customer.company.cccharge_type
                else:
                    customer.charge_getaway = Customer.CASH_PREPAYMENT
            phones = []
            titles = []
            sms_emails = []
            sms_gateways = []
            i = 1
            print form.data
            while True:
                if 'phone_number'+str(i) in form.data and form.data['phone_number'+str(i)] and\
                        form.data['phone_number'+str(i)].isdigit() and len(form.data['phone_number'+str(i)]) == 10:
                    phones.append(form.data['phone_number'+str(i)])
                    titles.append(form.data['phone_title'+str(i)])
                    sms_gateways.append(form.data['sms_gateway'+str(i)])
                    if 'for_sms_email'+str(i) in form.data:
                        sms_emails.append(form.data['for_sms_email'+str(i)])
                    else:
                        sms_emails.append('')
                    i += 1
                else:
                    break
            print phones
            customer.set_phone_numbers(phones, titles, sms_gateways, sms_emails)
            customer.save()
            if form.cleaned_data.get('local_card'):
                from ppars.apps.card.models import Card
                card = Card.objects.get(id=form.cleaned_data.get('local_card'))
                card.customer = customer
                card.save()
            if form.message:
                messages.add_message(request, messages.WARNING, '%s' % form.message)
            messages.add_message(
                request,
                messages.SUCCESS,
                'Customer <a href="%s">%s</a> created successfully.' %
                (request.build_absolute_uri(reverse('customer_update', args=[customer.id])), customer)
            )
            if customer.get_charge_getaway_display().lower() in form.message.lower():
                return HttpResponseRedirect('/customer')
            else:
                # just to clean flash messages, as other way it doesn't work
                for message in messages.get_messages(request):
                    pass
            if 'with_charge' in request.GET:
                return HttpResponseRedirect(reverse('charge_list') + '?cid='+str(customer.id))
            elif 'schedule' in request.GET:
                return HttpResponseRedirect('/autorefill/create/?ph=' + request.POST['phone_number1'] + '&cid=' + str(customer.id))
            else:
                return HttpResponseRedirect('/manualrefill?ph=' + request.POST['phone_number1'] + '&cid=' + str(customer.id))
        else:
            logger.debug(form.errors)
            return render(request, self.template_name,
                          {
                              'form': form,
                              'use_sellercloud': request.user.profile.company.use_sellercloud,
                              'number': request.POST['phone_numbers'],
                              'sms_email_gateways': [(gateway.id, gateway.__unicode__())
                                                     for gateway in SmsEmailGateway.objects.all()]
                          })


def ajax_monthly_refills(request):
    today = datetime.datetime.now(timezone('US/Eastern')).date()
    ajax_response = {"sEcho": request.GET['sEcho'], "aaData": [], 'iTotalRecords': 0}
    total_price = 0
    for refill in AutoRefill.objects.filter(company=request.user.profile.company, enabled=True,
                                            renewal_date__month=today.month):
        cost, tax = refill.calculate_cost_and_tax()
        discount = 0
        if PlanDiscount.objects.filter(carrier=refill.plan.carrier,
                                       plan=refill.plan, company=request.user.profile.company).exists():
            discount = PlanDiscount.objects.get(carrier=refill.plan.carrier,
                                                plan=refill.plan, company=request.user.profile.company).discount
        elif PlanDiscount.objects.filter(carrier=refill.plan.carrier, plan=None,
                                         company=request.user.profile.company).exists():
            discount = PlanDiscount.objects.get(carrier=refill.plan.carrier, plan=None,
                                                company=request.user.profile.company).discount
        total_price += cost * (discount/100)
    ajax_response['aaData'].append(['Total',
                                    AutoRefill.objects.filter(company=request.user.profile.company,
                                                              enabled=True, renewal_date__month=today.month).count(),
                                    '$'+str(total_price)[:-2]])
    for plan in Plan.objects.all():
        total_price = 0
        refills_for_this_month = AutoRefill.objects.filter(company=request.user.profile.company, enabled=True,
                                                           renewal_date__month=today.month, plan=plan)
        if refills_for_this_month:
            for refill in refills_for_this_month:
                cost, tax = refill.calculate_cost_and_tax()
                discount = 0
                if PlanDiscount.objects.filter(carrier=refill.plan.carrier,
                                               plan=refill.plan, company=request.user.profile.company).exists():
                    discount = PlanDiscount.objects.get(carrier=refill.plan.carrier,
                                                        plan=refill.plan, company=request.user.profile.company).discount
                elif PlanDiscount.objects.filter(carrier=refill.plan.carrier, plan=None,
                                                 company=request.user.profile.company).exists():
                    discount = PlanDiscount.objects.get(carrier=refill.plan.carrier, plan=None,
                                                        company=request.user.profile.company).discount
                total_price += cost * (discount/100)
            ajax_response['aaData'].append([plan.plan_id,
                                            AutoRefill.objects.filter(company=request.user.profile.company, plan=plan,
                                                                      enabled=True, renewal_date__month=today.month).count(),
                                            '$'+str(total_price)[:-2]])
    ajax_response['iTotalDisplayRecords'] = len(ajax_response['aaData'])
    start = int(request.GET['iDisplayStart'])
    length = int(request.GET['iDisplayLength'])
    ajax_response['aaData'] = ajax_response['aaData'][start:start+length]
    return HttpResponse(json.dumps(ajax_response), content_type='application/json')


class LogList(ListView):
    model = Log
    template_name = 'core/templates/ppars/log_list.html'
    context_object_name = 'log_list'

    def get_queryset(self):
        return self.request.user.profile.get_company_logs()


class CompanyProfileUpdate(View):
    model = CompanyProfile
    template_name = 'core/userprofile_form.html'
    form_class = forms.CompanyProfileForm

    def get(self, request, *args, **kwargs):
        form = forms.CompanyProfileForm(instance=request.user.profile.company)
        number_of_manual, number_of_schedule = ext_lib.number_of_transaction_from_month_by_now_of_company(
            UserProfile.objects.filter(user=self.request.user).get().company)
        return render(request, self.template_name, {'form': form,
                                                    'manual': number_of_manual,
                                                    'schedule': number_of_schedule})

    def post(self, request, *args, **kwargs):
        form = forms.CompanyProfileForm(request.POST, instance=request.user.profile.company)
        if form.is_valid():
            p = self.request.user.profile
            if self.request.user.is_superuser:
                    form.instance.company_name = p.company.company_name
            form.instance.updated = True
            form.instance.superuser_profile = self.request.user.is_superuser
            form.save()
            messages.add_message(self.request, messages.SUCCESS, 'Company Profile updated successfully.')
            return render(request, self.template_name, {'form': form})
        else:
            logger.debug(form.errors)
            return render(request, self.template_name, {'form': form})


class CustomerList(ListView):
    model = Customer
    template_name = 'core/customer_list.html'

    def get_queryset(self):
        return self.request.user.profile.get_company_customers()

    def get(self, request, *args, **kwargs):
        return render(request,self.template_name)


class CustomerCreate(View):
    form_class = forms.CustomerForm
    model = Customer
    template_name = 'core/customer_form.html'

    def get(self, request, *args, **kwargs):
        form = forms.CustomerForm()
        form.fields['send_pin_prerefill'].initial = request.user.profile.company.send_pin_prerefill
        form.fields['send_status'].initial = request.user.profile.company.send_status
        return render(request, self.template_name,
                      {
                          'form': form,
                          'use_sellercloud': request.user.profile.company.use_sellercloud,
                          'sms_email_gateways': [(gateway.id, gateway.__unicode__())
                                                 for gateway in SmsEmailGateway.objects.all()],
                          'customers': request.user.profile.get_company_customers()
                      })

    def post(self, request, *args, **kwargs):
        form = forms.CustomerForm(request.POST, request=request)
        if request.is_ajax():
            if not form.is_valid():
                return HttpResponse(json.dumps({'status': 'error', 'errors': form.errors}))
        if form.is_valid():
            self.object = customer = form.save(commit=True)
            customer.user = request.user
            customer.company = request.user.profile.company
            if not customer.charge_getaway:
                if customer.company.cccharge_type and customer.charge_type == Customer.CREDITCARD:
                    customer.charge_getaway = customer.company.cccharge_type
                else:
                    customer.charge_getaway = Customer.CASH_PREPAYMENT
            phones = []
            titles = []
            sms_emails = []
            sms_gateways = []
            i = 1
            while True:
                if 'phone_number'+str(i) in form.data and form.data['phone_number'+str(i)] and\
                        form.data['phone_number'+str(i)].isdigit() and len(form.data['phone_number'+str(i)]) == 10:
                    phones.append(form.data['phone_number'+str(i)])
                    titles.append(form.data['phone_title'+str(i)])
                    sms_gateways.append(form.data['sms_gateway'+str(i)])
                    if 'for_sms_email'+str(i) in form.data:
                        sms_emails.append(form.data['for_sms_email'+str(i)])
                    else:
                        sms_emails.append('')
                    i += 1
                else:
                    break
            customer.set_phone_numbers(phones, titles, sms_gateways, sms_emails)
            customer.save()
            if form.cleaned_data.get('local_card'):
                from ppars.apps.card.models import Card
                card = Card.objects.get(id=form.cleaned_data.get('local_card'))
                card.customer = customer
                card.save()
            if request.is_ajax():
                return HttpResponse(json.dumps({'status': 'success', 'id': customer.id}))
            if form.message:
                messages.add_message(request, messages.WARNING, '%s' % form.message)
            messages.add_message(
                request,
                messages.SUCCESS,
                'Customer <a href="%s">%s</a> created successfully.' %
                (request.build_absolute_uri(reverse('customer_update', args=[customer.id])), customer))
            return render(request, 'core/customer_list.html',
                          {
                              'customer_list': request.user.profile.get_company_customers(),
                          })
        else:
            logger.debug(form.errors)
            return render(request, self.template_name,
                          {
                              'form': form,
                              'use_sellercloud': request.user.profile.company.use_sellercloud,
                              'sms_email_gateways': [(gateway.id, gateway.__unicode__())
                                                     for gateway in SmsEmailGateway.objects.all()],
                              'customers': request.user.profile.get_company_customers()
                          })


class CustomerUpdate(View):
    form_class = forms.CustomerForm
    model = Customer
    template_name = 'core/customer_form.html'

    def get(self, request, pk, *args, **kwargs):
        customer = get_object_or_404(Customer, pk=pk)
        form = forms.CustomerForm(instance=customer, request=request, initial={'phone_numbers': ",".join(PhoneNumber.objects.filter(customer=customer).values_list('number', flat=True)),
                                                                               'phone_titles': ",".join(PhoneNumber.objects.filter(customer=customer).values_list('title', flat=True)),
                                                                               'phone_gateways': ",".join(str(id) for id in PhoneNumber.objects.filter(customer=customer).values_list('sms_gateway', flat=True)),
                                                                               'phone_sms_emails': ",".join(str(use) for use in PhoneNumber.objects.filter(customer=customer).values_list('use_for_sms_email', flat=True))})
        amount = 0
        for charge in Charge.objects.filter(used=False, customer=customer):
            amount += charge.amount-charge.summ
        return render(request, self.template_name,
                      {
                          'form': form,
                          'verify_carrier': customer.company.verify_carrier,
                          'customer': customer,
                          'object': customer,
                          'use_sellercloud': customer.company.use_sellercloud,
                          'unused_charge_count': Charge.objects.filter(used=False, customer=customer).count(),
                          'unused_charge_amount_left': amount,
                          'sms_email_gateways': [(gateway.id, gateway.__unicode__())
                                                 for gateway in SmsEmailGateway.objects.all()],
                          'customers': request.user.profile.get_company_customers()
                      })

    def post(self, request, pk, *args, **kwargs):
        customer = get_object_or_404(Customer, pk=pk)
        form = forms.CustomerForm(request.POST, instance=customer, request=request)
        if request.is_ajax():
            if not form.is_valid():
                return HttpResponse(json.dumps({'status': 'error', 'errors': form.errors}))
        if form.is_valid():
            self.object = customer = form.save(commit=True)
            if not customer.charge_getaway and customer.company.cccharge_type:
                customer.charge_getaway = customer.company.cccharge_type
                customer.save()
            if 'enabled' in form.changed_data and not form.instance.enabled:
                autorefills = AutoRefill.objects.filter(customer=form.instance)
                for autorefill in autorefills:
                        autorefill.enabled = False
                        autorefill.save()
            phones = []
            titles = []
            sms_emails = []
            sms_gateways = []
            i = 1
            while True:
                if 'phone_number'+str(i) in form.data and form.data['phone_number'+str(i)] and\
                        form.data['phone_number'+str(i)].isdigit() and len(form.data['phone_number'+str(i)]) == 10:
                    phones.append(form.data['phone_number'+str(i)])
                    titles.append(form.data['phone_title'+str(i)])
                    sms_gateways.append(form.data['sms_gateway'+str(i)])
                    if 'for_sms_email'+str(i) in form.data:
                        sms_emails.append(form.data['for_sms_email'+str(i)])
                    else:
                        sms_emails.append('')
                    i += 1
                else:
                    break
            customer.set_phone_numbers(phones, titles, sms_gateways, sms_emails)
            customer.save()
            if form.cleaned_data.get('local_card'):
                from ppars.apps.card.models import Card
                card = Card.objects.get(id=form.cleaned_data.get('local_card'))
                card.customer = form.instance
                card.save()
            if request.is_ajax():
                return HttpResponse(json.dumps({'status': 'success', 'id': customer.id}))
            if form.message:
                messages.add_message(request, messages.WARNING, '%s' % form.message)
            messages.add_message(
                request,
                messages.SUCCESS,
                'Customer <a href="%s">%s</a> updated successfully.' %
                (request.build_absolute_uri(
                    reverse(
                        'customer_update',
                        args=[form.instance.id])),
                form.instance))
            return render(request, 'core/customer_list.html',
                          {
                              'customer_list': request.user.profile.get_company_customers(),
                          })
        else:
            return render(request, self.template_name,
                          {
                              'form': form,
                              'verify_carrier': customer.company.verify_carrier,
                              'use_sellercloud': customer.company.use_sellercloud,
                              'request': request,
                              'sms_email_gateways': [(gateway.id, gateway.__unicode__())
                                                 for gateway in SmsEmailGateway.objects.all()],
                              'customers': request.user.profile.get_company_customers()
                          })


class CustomerExport(View):

    def get(self, request, *args, **kwargs):
        template = request.GET.get('template')
        response = HttpResponse(content_type='text/csv')
        writer = csv.writer(response)
        filename = 'customer_basic_import_template.csv'
        writer.writerow(['First Name',
                         'Middle Name',
                         'Last Name',
                         'Primary Email',
                         'Phone Numbers',
                         'SellerCloud Account ID',
                         'SMS Email',
                         'SMS Email Gateway',
                         'Address',
                         'City',
                         'State',
                         'Zip',
                         'Charge Type',
                         'Charge Gateway',
                         'Card Number',
                         'Authorize ID',
                         'USAePay customer ID',
                         'USAePay CustID',
                         'Selling Price Level',
                         'Customer Discount',
                         'Taxable',
                         'Precharge SMS',
                         'Email Successful Refill',
                         'Email Successful Charge',
                         'Send Status',
                         'Send Pin PreRefill',
                         'Group SMS',
                         'Enabled',
                         'Notes'
                         ])
        if template != 'true':
            filename = 'customer_export_{d.month}_{d.day}_{d.year}.csv'.format(d=datetime.datetime.now())
            customers = Customer.objects.filter(company=request.user.profile.company)
            for customer in customers:
                phone_numbers = ",".join([phone.number for phone in PhoneNumber.objects.filter(customer=customer)])
                writer.writerow([
                    customer.first_name,
                    customer.middle_name,
                    customer.last_name,
                    customer.primary_email,
                    phone_numbers,
                    customer.sc_account,
                    customer.address,
                    customer.city,
                    customer.state,
                    customer.zip,
                    customer.get_charge_type_display(),
                    customer.get_charge_getaway_display(),
                    customer.creditcard,
                    customer.authorize_id,
                    customer.usaepay_customer_id,
                    customer.usaepay_custid,
                    customer.selling_price_level,
                    customer.customer_discount,
                    customer.taxable,
                    customer.precharge_sms,
                    customer.email_success_refill,
                    customer.email_success_charge,
                    customer.get_send_status_display(),
                    customer.get_send_pin_prerefill_display(),
                    customer.group_sms,
                    customer.enabled,
                    customer.notes,
                ])
        response['Content-Disposition'] = 'attachment;filename=%s' % filename
        return response


class CustomerImport(View):
    template_name = 'core/customer_import.html'
    form_class = forms.GenericImportForm

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form, 'confirm': False})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)
        if not form.is_valid():
            return render(request, self.template_name, {'form': form, 'confirm': False})
        if form.cleaned_data['confirm'] == 'False':
            try:
                customers = ext_lib.import_csv(form.cleaned_data['file'])
                cache_id = str(uuid.uuid1())
                cache.add(key=cache_id, value={'customers': customers, 'user': request.user}, timeout=600)
                return render(request, self.template_name,
                              {'form': form, 'confirm': True, 'customers': customers, 'cache_id': cache_id})
            except Exception, e:
                messages.add_message(request, messages.ERROR,
                                     'Failed to read import file, please '
                                     'ensure it is a csv and that it '
                                     'follows the template.')
                logger.error(traceback.format_exc())
                return HttpResponseRedirect(reverse('customer_list'))
        else:
            cache_data = cache.get(form.cleaned_data['cache_id'])
            if cache_data:
                queue_customer_import.delay(cache_data)
                messages.add_message(request, messages.SUCCESS,
                                     'Customer import job has been added to '
                                     'queue, results will be mailed to you.')
            else:
                messages.add_message(request, messages.ERROR,
                                     'Server was inactive more than 10 minutes. '
                                     'Please, make import faster')
            return HttpResponseRedirect(reverse('customer_list'))


class CustomerDelete(DeleteView):
    model = Customer

    def get_success_url(self):
        return reverse('customer_list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        messages.add_message(self.request, messages.ERROR, 'Customer "%s" deleted successfully.' % self.object)
        return HttpResponseRedirect(self.get_success_url())


class PlanList(ListView):
    model = Plan


class PlanCreate(View):
    model = Plan
    form_class = forms.PlanForm
    template_name = 'core/plan_form.html'

    def get(self, request, *args, **kwargs):
        form = forms.PlanForm()
        up = Plan.objects.filter(universal=True)
        return render(request, self.template_name,
                      {
                          'form': form,
                          'up': up,
                      })

    def post(self, request, *args, **kwargs):
        form = forms.PlanForm(request.POST)
        up = Plan.objects.filter(universal=True)
        if form.is_valid():
            self.object = plan = form.save(commit=False)
            if plan.universal:
                plan.universal_plan = None
            plan.save()
            messages.add_message(self.request, messages.SUCCESS, 'Plan "%s" created successfully.' % form.instance)
            return render(request, 'core/plan_list.html',
                          {
                              'plan_list': Plan.objects.all(),
                          })
        else:
            logger.debug(form.errors)
            return render(request, self.template_name,
                          {
                              'form': form,
                              'up': up,
                          })


class PlanUpdate(View):
    model = Plan
    form_class = forms.PlanForm
    template_name = 'core/plan_form.html'

    def get(self, request, pk, *args, **kwargs):
        plan = get_object_or_404(Plan, pk=pk)
        up = Plan.objects.exclude(pk=pk).filter(universal=True)
        form = forms.PlanForm(instance=plan)
        can_deleted = False
        today = datetime.datetime.now(pytz.timezone('US/Eastern'))
        that_date = today.replace(day=07)
        if plan.created > that_date:
            can_deleted = True
        return render(request, self.template_name,
                      {
                          'form': form,
                          'up': up,
                          'plan': plan,
                          'can_deleted': can_deleted
                      })

    def post(self, request, pk, *args, **kwargs):
        plan = get_object_or_404(Plan, pk=pk)
        form = forms.PlanForm(request.POST, instance=plan)
        up = Plan.objects.exclude(pk=pk).filter(universal=True)
        if form.is_valid():
            self.object = plan = form.save(commit=False)
            if plan.universal:
                plan.universal_plan = None
            plan.save()
            messages.add_message(self.request, messages.SUCCESS, 'Plan "%s" updated successfully.' % form.instance)
            return render(request, 'core/plan_list.html',
                          {
                              'plan_list':  Plan.objects.all(),
                          })
        else:
            return render(request, self.template_name,
                          {
                              'form': form,
                              'up': up,
                              'plan': plan,
                          })


class PlanDelete(DeleteView):
    model = Plan

    def get_success_url(self):
        return reverse('plan_list')


class PlanExport(View):

    def get(self, request, *args, **kwargs):
        template = request.GET.get('template')
        response = HttpResponse(mimetype='text/csv')
        filename = 'plans_import_template.csv'
        writer = csv.writer(response)
        writer.writerow(['Plan ID', 'SC_SKU', 'API ID', 'Carrier', 'Plan Name', 'Plan Cost', 'Plan Type', 'Available', 'Universal', 'Universal Plan'])
        if template != 'true':
            filename = 'plan_export_{d.month}_{d.day}_{d.year}.csv'.format(d=datetime.datetime.now())
            plans = Plan.objects.order_by('carrier__name', 'plan_cost', '-universal')
            for plan in plans:
                writer.writerow([plan.plan_id, plan.sc_sku, plan.api_id, plan.carrier, plan.plan_name, plan.plan_cost, plan.get_plan_type_display(), plan.available, plan.universal, plan.universal_plan])
        response['Content-Disposition'] = 'attachment;filename=%s' % filename
        return response


class PlanImport(View):
    template_name = 'core/plan_import.html'
    form_class = forms.GenericImportForm

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form, 'confirm': False})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)
        if form.is_valid():
            if form.cleaned_data['confirm'] == 'False':
                try:
                    plans = ext_lib.import_csv(form.cleaned_data['file'])
                    cache_id = str(uuid.uuid1())
                    cache.add(key=cache_id, value={'plans': plans}, timeout=600)
                    return render(request, self.template_name,
                                  {'form': form,
                                   'confirm': True,
                                   'plans': plans,
                                   'cache_id': cache_id})
                except Exception, e:
                    messages.add_message(request, messages.ERROR, 'Failed to read import file, please ensure it is a csv and that it follows the template.')
                    logger.error("Exception: %s. Trace: %s." % (e, traceback.format_exc(limit=10)))
                    return HttpResponseRedirect(reverse('plan_list'))
            else:
                try:
                    cache_data = cache.get(form.cleaned_data['cache_id'])
                    universal_plans = dict()
                    plan_types = {ptype[1]: ptype[0] for ptype in Plan.PLAN_TYPE_CHOICES}
                    # carriers = Carrier.objects.all()
                    # carrier_log = CommandLog.objects.create(command='New Carriers', message='Carriers')
                    # plan_log = CommandLog.objects.create(command='New Plans', message='Plans')
                    for plan in cache_data['plans']:
                    #     # onetime import
                    #     # working with carrier
                    #     plan_carrier = None
                    #     plan['plan_cost'] = plan['plan_cost'].replace(',', '.')
                    #     carrier_name = plan['carrier'].upper()
                    #     plan_carriers = Carrier.objects.filter(name__contains=carrier_name)
                    #     if plan_carriers:
                    #         plan_carrier = plan_carriers[0]
                    #     else:
                    #         for carrier in carriers:
                    #             if carrier.name in carrier_name:
                    #                 plan_carrier = carrier
                    #                 break
                    #     if not plan_carrier:
                    #         plan_carrier = Carrier.objects.create(name=carrier_name)
                    #         carrier_log.message ='%s %s %s' % (carrier_log.message, carrier_name, request.build_absolute_uri(reverse('carrier_update', args=[plan_carrier.id])))
                    #         carrier_log.save()
                    #     # working with plan
                    #     plans = Plan.objects.filter(carrier=plan_carrier)
                    #     found_plan = None
                    #     # working with plan
                    #     for exist_plan in plans:
                    #         if exist_plan.plan_cost == decimal.Decimal(plan['plan_cost']) and (exist_plan.plan_name == plan['plan_name'] or exist_plan.plan_name == '%s%s' % (plan['carrier'], plan['plan_cost'])):
                    #             found_plan = exist_plan
                    #             break
                    #     if not found_plan:
                    #         if plan['plan_cost'] in plan['plan_name']:
                    #             plan_id = plan['plan_name']
                    #         else:
                    #             plan_id = '%s%sRTR' % (plan['plan_name'].replace('RTR', '').strip(), plan['plan_cost'])
                    #         found_plan = Plan.objects.create(carrier=plan_carrier,
                    #                                          plan_id=plan_id,
                    #                                          plan_name=plan['plan_name'],
                    #                                          plan_cost=plan['plan_cost'])
                    #         plan_log.message ='%s %s %s' % (plan_log.message, found_plan, request.build_absolute_uri(reverse('plan_update', args=[found_plan.id])))
                    #         plan_log.save()
                    #     plan['plan_type'] = plan_types[plan['plan_type']]
                    #     if not found_plan.plan_id:
                    #         found_plan.plan_id = plan_id
                    #     found_plan.api_id = plan['api_id']
                    #     found_plan.plan_type = plan['plan_type']
                    #     found_plan.save()
                        plan['carrier'] = Carrier.objects.get(name=plan['carrier'])
                        plan['plan_type'] = plan_types[plan['plan_type']]
                        if not plan['api_id']:
                            plan['api_id'] = ''
                        if not plan['sc_sku']:
                            plan['sc_sku'] = ''
                        if plan['available'] == 'False':
                            plan['available'] = False
                        else:
                            plan['available'] = True
                        if plan['universal'] == 'True':
                            plan['universal'] = True
                        else:
                            plan['universal'] = False
                            if plan['universal_plan']:
                                plan['universal_plan'] = universal_plans[plan['universal_plan']]

                        if Plan.objects.filter(plan_id=plan['plan_id']).exists():
                            # logger.debug('plan %s' % plan['plan_id'])
                            this_plan = Plan.objects.get(plan_id=plan['plan_id'])
                            for prop in plan:
                                setattr(this_plan, prop, plan[prop])
                        else:
                            this_plan = Plan(**plan)
                            this_plan.save()
                            logger.debug('new plan %s %s' % (this_plan.plan_id, this_plan.id))
                        if plan['universal'] == True:
                            universal_plans[plan['plan_id']] = this_plan
                        this_plan.save()
                    messages.add_message(request, messages.SUCCESS, 'Plans imported successfully.')
                except Exception, e:
                    logger.error("Exception: %s. Trace: %s." % (e, traceback.format_exc(limit=10)))
                    messages.add_message(request, messages.ERROR, 'Plan imported failed, please contact the administrator for furthur information')
                finally:
                    return HttpResponseRedirect(reverse('plan_list'))
        else:
            return render(request, self.template_name, {'form': form, 'confirm': False})


class PlanDiscountList(ListView):
    model = PlanDiscount

    def get_queryset(self):
        return PlanDiscount.objects.filter(company=self.request.user.profile.company)


class PlanDiscountCreate(CreateView):
    form_class = forms.PlanDiscountForm
    model = PlanDiscount

    def get_form_kwargs(self):
        kwargs = super(PlanDiscountCreate, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.company = self.request.user.profile.company
        return super(PlanDiscountCreate, self).form_valid(form)


class PlanDiscountUpdate(UpdateView):
    form_class = forms.PlanDiscountForm
    model = PlanDiscount

    def get_form_kwargs(self):
        kwargs = super(PlanDiscountUpdate, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs


class CarrierList(ListView):
    model = Carrier


class CarrierCreate(CreateView):
    model = Carrier
    form_class = forms.CarrierForm

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.company = self.request.user.profile.company
        return super(CarrierCreate, self).form_valid(form)


class CarrierUpdate(UpdateView):
    model = Carrier
    form_class = forms.CarrierForm


class CarrierDelete(DeleteView):
    model = Carrier

    def get_success_url(self):
        return reverse('carrier_list')


class CarrierExport(View):

    def get(self, request, *args, **kwargs):
        template = request.GET.get('template')
        response = HttpResponse(mimetype='text/csv')
        filename = 'carriers_import_template.csv'
        writer = csv.writer(response)
        writer.writerow(['Name', 'Recharge Number', 'Admin Site', 'Renew Days', 'Renew Months'])
        if template != 'true':
            filename = 'carrier_export_{d.month}_{d.day}_{d.year}.csv'.format(d=datetime.datetime.now())
            carriers = Carrier.objects.all()
            for carrier in carriers:
                writer.writerow([carrier.name, carrier.recharge_number, carrier.admin_site, carrier.renew_days, carrier.renew_months])
        response['Content-Disposition'] = 'attachment;filename=%s' % filename
        return response


class CarrierImport(View):
    template_name = 'core/carrier_import.html'
    form_class = forms.GenericImportForm

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form, 'confirm': False})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)
        if form.is_valid():
            if form.cleaned_data['confirm'] == 'False':
                try:
                    carriers = ext_lib.import_csv(form.cleaned_data['file'])
                    cache_id = str(uuid.uuid1())
                    cache.add(key=cache_id, value={'carriers': carriers}, timeout=600)
                    return render(request, self.template_name,
                                  {'form': form,
                                   'confirm': True,
                                   'carriers': carriers,
                                   'cache_id': cache_id})
                except Exception, e:
                    messages.add_message(request, messages.ERROR, 'Failed to read import file, please ensure it is a csv and that it follows the template.')
                    logger.error(traceback.format_exc())
                    return HttpResponseRedirect(reverse('carrier_list'))
            else:
                try:
                    cache_data = cache.get(str(form.cleaned_data['cache_id']))
                    for carrier in cache_data['carriers']:
                        if not carrier['recharge_number']:
                            carrier['recharge_number'] = ''
                        if not carrier['admin_site']:
                            carrier['admin_site'] = ''
                        if Carrier.objects.filter(name=carrier['name']).exists():
                            this_carrier = Carrier.objects.get(name=carrier['name'])
                            for prop in carrier:
                                setattr(this_carrier, prop, carrier[prop])
                        else:
                            this_carrier = Carrier(**carrier)
                        this_carrier.save()
                    messages.add_message(request, messages.SUCCESS, 'Carriers imported successfully.')
                except Exception, e:
                    messages.add_message(request, messages.ERROR, 'Carrier imported failed, please contact the administrator for furthur information')
                    logger.error(traceback.format_exc())
                finally:
                    return HttpResponseRedirect(reverse('carrier_list'))
        else:
            return render(request, self.template_name, {'form': form, 'confirm': False})


class CarrierAdminList(ListView):
    model = CarrierAdmin

    def get_queryset(self):
        return CarrierAdmin.objects.filter(company_id=self.request.user.profile.company_id)


class CarrierAdminCreate(CreateView):
    form_class = forms.CarrierAdminForm
    model = CarrierAdmin

    def get_form_kwargs(self):
        kwargs = super(CarrierAdminCreate, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        form.instance.company = self.request.user.profile.company
        return super(CarrierAdminCreate, self).form_valid(form)


class CarrierAdminUpdate(UpdateView):
    form_class = forms.CarrierAdminForm
    model = CarrierAdmin

    def get_form_kwargs(self):
        kwargs = super(CarrierAdminUpdate, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

# TODO: remove after Jacob approve
#back Customer Notification of Payment from 7/01/15
class BackCustomerNotification(View):

    def get(self, request, *args, **kwargs):
        back_from_logs.delay(request.user)
        return HttpResponseRedirect('/customer')


class AutoRefillList(ListView):
    model = AutoRefill

    def get_queryset(self):
        return AutoRefill.objects.filter(trigger="SC", company=self.request.user.profile.company)

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(AutoRefillList, self).get_context_data(**kwargs)
        # Add in the publisher
        context['schedule_allowed'] = self.request.user.profile.company.check_available_schedule_create()
        context['verify_carrier'] = self.request.user.profile.company.verify_carrier
        return context


class AutoRefillCreate(CreateView):
    form_class = forms.AutoRefillForm
    model = AutoRefill

    def get_form_kwargs(self):
        kwargs = super(AutoRefillCreate, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get(self, request, *args, **kwargs):
        if not request.user.profile.company.check_available_schedule_create():
            messages.error(request, 'Schedule limit has been reached. Please contact administrator.')
            return HttpResponseRedirect(reverse('autorefill_list'))
        self.object = None
        return super(AutoRefillCreate, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if not request.user.profile.company.check_available_schedule_create():
            messages.error(request, 'Schedule limit has been reached. Please contact administrator.')
            return HttpResponseRedirect(reverse('autorefill_list'))
        self.object = None
        return super(AutoRefillCreate, self).post(request, *args, **kwargs)

    def get_initial(self):
        data = {}
        if self.request.GET.get('cid'):
            data['customer'] = Customer.objects.get(id=self.request.GET['cid'])
        if self.request.GET.get('ph'):
            data['phone_number'] = self.request.GET['ph']
        return data

    def form_valid(self, form):
        self.object = auto_refill = form.save(commit=False)
        auto_refill.user = self.request.user
        auto_refill.company = self.request.user.profile.company
        auto_refill.trigger = "SC"
        auto_refill.refill_type = "FR"
        auto_refill.save()
        messages.add_message(self.request, messages.SUCCESS, 'AutoRefill <a href="%s">%s</a> was created successfully.' %
                             (self.request.build_absolute_uri(reverse('autorefill_update', args=[auto_refill.id])),
                              auto_refill))
        return super(AutoRefillCreate, self).form_valid(form)


    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(CreateView, self).get_context_data(**kwargs)
        context['verify_carrier'] = self.request.user.profile.company.verify_carrier
        return context


class AutoRefillUpdate(UpdateView):
    form_class = forms.AutoRefillForm
    model = AutoRefill

    def get_form_kwargs(self):
        kwargs = super(AutoRefillUpdate, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(UpdateView, self).get_context_data(**kwargs)
        # Add in the publisher0
        context['has_pin_intermediate_step'] = ''
        context['verify_carrier'] = self.request.user.profile.company.verify_carrier
        today = datetime.datetime.now(pytz.timezone('US/Eastern')).date()
        start_date = datetime.datetime.combine(today - datetime.timedelta(days=1), datetime.time(hour=11, minute=59))
        if Transaction.objects.filter(autorefill=self.get_object(), started__gt=start_date, paid=True):
            context['has_pin_intermediate_step'] = 'Please make sure to refund customer!'
        if Transaction.objects.filter(autorefill=self.get_object(), started__gt=start_date, pin__isnull=False):
            if context['has_pin_intermediate_step']:
                context['has_pin_intermediate_step'] = 'A pin was already taken! Please make sure to refund customer and add pin to unused!'
            else:
                context['has_pin_intermediate_step'] = 'A pin was already taken! Please make sure add pin to unused!'
        return context

    def post(self, request, pk, *args, **kwargs):
        autorefill = get_object_or_404(AutoRefill, pk=pk)
        messages.add_message(request, messages.SUCCESS, 'AutoRefill <a href="%s">%s</a> was updated successfully.' %
                             (request.build_absolute_uri(reverse('autorefill_update', args=[autorefill.id])),
                              autorefill))
        return super(AutoRefillUpdate, self).post(request, pk, *args, **kwargs)


class AutoRefillDelete(DeleteView):
    model = AutoRefill

    def get_success_url(self):
        return reverse('autorefill_list')


class AutoRefillExport(View):
    def get(self, request, *args, **kwargs):
        template = request.GET.get('template')
        response = HttpResponse(mimetype='text/csv')
        filename = 'scheduledrefills_import_template.csv'
        writer = csv.writer(response)
        writer.writerow(['Customer',
                         'Phone Number',
                         'Plan',
                         'Renewal Date',
                         'Renewal End Date',
                         'Renewal Interval',
                         'Schedule',
                         'Notes',
                         'Enabled'])
        if template != 'true':
            filename = 'scheduledrefills_export_{d.month}_{d.day}_{d.year}.csv'.format(d=datetime.datetime.now())
            autorefills = AutoRefill.objects.filter(user=self.request.user, trigger="SC")
            for autorefill in autorefills:
                writer.writerow([
                    autorefill.customer,
                    autorefill.phone_number,
                    autorefill.plan, autorefill.renewal_date,
                    autorefill.renewal_end_date,
                    autorefill.renewal_interval,
                    autorefill.get_schedule_display(),
                    autorefill.notes,
                    autorefill.enabled
                ])
        response['Content-Disposition'] = 'attachment;filename=%s' % filename
        return response


class AutoRefillImport(View):
    template_name = 'core/autorefill_import.html'
    form_class = forms.GenericImportForm

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form, 'confirm': False})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)
        if form.is_valid():
            if form.cleaned_data['confirm'] == 'False':
                try:
                    autorefills = ext_lib.import_csv(form.cleaned_data['file'])
                    checked_autorefills = []
                    for autorefill in autorefills:
                        autorefill['plan'] = Plan.objects.get(plan_id=autorefill['plan'])
                        autorefill['status'] = 'F'
                        # Verification for duplicated refills in imported file
                        if '%s-%s' % (autorefill['plan'], autorefill['phone_number']) in checked_autorefills:
                            autorefill['result'] = 'Autorefill already imported'
                        else:
                            customers = []
                            for customer in Customer.objects.filter(company=request.user.profile.company):
                                if PhoneNumber.objects.filter(company=request.user.profile.company, numbers__contains=autorefill['phone_number']):
                                    customers.append(customer)
                            # Verification for duplicated refills in system
                            if request.user.profile.company.block_duplicate_schedule:
                                ars = AutoRefill.objects.filter(
                                    trigger='SC',
                                    enabled=True,
                                    plan=autorefill['plan'],
                                    phone_number__contains=autorefill['phone_number'],
                                    company=request.user.profile.company)
                                if ars.count() > 0:
                                    message = []
                                    for ar in ars:
                                        message.append('<a href="%s">%s</a>' % (reverse('autorefill_update', args=[ar.id]), ar))
                                        autorefill['customer'] = ar.customer
                                    autorefill['result'] = 'Duplicated refills %s' % (', '.join(message))
                            # Searching customer by phone number
                            if 'result' not in autorefill:
                                if customers.count() > 1:
                                    autorefill['result'] = 'More than 1 customer has number "%s"' % autorefill['phone_number']
                                elif customers.count() < 1:
                                    autorefill['result'] = 'Nobody has number "%s"' % autorefill['phone_number']
                                else:
                                    autorefill['customer'] = customers[0]
                                    autorefill['result'] = 'Autorefill will be added'
                                    autorefill['status'] = 'S'
                                    checked_autorefills.append('%s-%s' % (autorefill['plan'], autorefill['phone_number']))
                            if autorefill['renewal_end_date'] and not re.findall(r'(19|20)\d\d-((0[1-9]|1[012])-(0[1-9]|[12]\d)|(0[13-9]|1[012])-30|(0[13578]|1[02])-31)', autorefill['renewal_end_date']):
                                autorefill['result'] = '%s "%s" value has an invalid date format. It must be in YYYY-MM-DD format.' % (autorefill['result'], autorefill['renewal_end_date'])
                                autorefill['renewal_end_date'] = None
                    cache_id = str(uuid.uuid1())
                    cache.add(key=cache_id, value={'autorefills': autorefills, 'user': request.user}, timeout=600)
                    return render(request, self.template_name,
                                  {
                                      'form': form, 'confirm': True,
                                      'autorefills': autorefills,
                                      'cache_id': cache_id
                                  })
                except Exception, e:
                    messages.add_message(request, messages.ERROR,
                                         'Failed to read import file, '
                                         'please ensure it is a csv and '
                                         'that it follows the template.')
                    logger.error(traceback.format_exc())
                    return HttpResponseRedirect(reverse('autorefill_list'))
            else:
                cache_data = cache.get(form.cleaned_data['cache_id'])
                queue_autorefill_import.delay(cache_data)
                messages.add_message(request, messages.SUCCESS,
                                     'Scheduled Refill import job has been '
                                     'added to queue, results will be mailed '
                                     'to you.')
                return HttpResponseRedirect(reverse('autorefill_list'))
        else:
            return render(request, self.template_name, {'form': form, 'confirm': False})


class ManualRefill(View):
    form_class = forms.ManualRefillForm
    template_name = 'core/manualrefill.html'

    def get(self, request, *args, **kwargs):
        init = dict()
        if request.GET.get('cid'):
            init['customer'] = Customer.objects.get(id=request.GET['cid'])
        if request.GET.get('ph'):
            init['phone_number'] = request.GET['ph']
        form = self.form_class(request.user, initial=init)
        return render(request, self.template_name, {'form': form,
                                                    'verify_carrier': self.request.user.profile.company.verify_carrier})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.user, data=request.POST)
        if form.is_valid():
            self.object = manual_refill = form.save(commit=False)
            manual_refill.company = request.user.profile.company
            manual_refill.user = request.user
            manual_refill.trigger = "MN"
            manual_refill.save()
            transaction = Transaction(
                user=request.user,
                autorefill=manual_refill,
                state="Q",
                pin=manual_refill.pin,
                company=request.user.profile.company,
                triggered_by=request.user.username
            )
            if 'already_paid' in form.data and form.data['already_paid']:
                transaction.paid = True
            transaction.save()
            if 'already_paid' in form.data and form.data['already_paid']:
                transaction.add_transaction_step(current_step='Mark paid',
                                                 action='mark_paid',
                                                 status='S',
                                                 adv_status='Transaction was marked paid before starting.')

            if 'created-from' in form.data and form.data['created-from']:
                # work with old transaction
                trans_id_from = int(form.data['created-from'])
                transaction_from = Transaction.objects.get(id=trans_id_from)
                transaction_from.add_transaction_step(
                    'create similar',
                    'Created similar transaction',
                    SUCCESS,
                    'Created similar transaction <a href="%s">%s</a> by user %s' %
                    (transaction.get_full_url(), transaction.id, request.user))
                transaction_from.status = Transaction.CR_NEW
                transaction_from.state = Transaction.COMPLETED
                transaction_from.save()
                # work with new transaction
                transaction.need_paid = transaction_from.need_paid
                if request.POST.get('original_trans_paid') == 'on':
                    transaction.paid = transaction_from.paid
                transaction.triggered_by = 'Created of old transaction ' \
                                           '<a href="%s">%s</a>' % \
                                           (transaction_from.get_full_url(),
                                            transaction_from.id)
                transaction.save()
                transaction.add_transaction_step(
                    'create',
                    'Created from existing transaction',
                    SUCCESS,
                    'Created from transaction <a href="%s">%s</a> by user %s' %
                    (transaction_from.get_full_url(), trans_id_from, request.user))
                # create related model M2M
                TransactionCreatedFromTo.objects.create(transaction_from=transaction_from,
                                                        transaction_to=transaction)
            # start transaction in set time and data
            if 'datetime_refill' in form.data and form.data["datetime_refill"]:
                time_format = "%d %B %Y %H:%M"
                time = datetime.datetime.strptime(form.data["datetime_refill"], time_format)
                eta = time - datetime.timedelta(minutes=int(form.data["datetime_refill_tzone"]))

                if eta > datetime.datetime.now():
                    transaction.state = Transaction.QUEUED
                    transaction.retry_interval = (eta - datetime.datetime.now()).total_seconds()
                    transaction.adv_status = 'Waiting of execution at ' + time.strftime(time_format)
                    transaction.status = Transaction.WAITING

                    transaction.save(update_fields=['retry_interval', 'adv_status', 'status', 'state'])

                    transaction.add_transaction_step('wait', 'Waiting of execution', WAITING, transaction.adv_status)

                    if request.POST.get('get_pin_now') == 'on':
                        transaction.get_pin_now = True
                        transaction.execution_time = eta.replace(tzinfo=pytz.UTC)
                        transaction.save(update_fields=['get_pin_now', 'execution_time'])

                        queue_refill.delay(transaction.id)
                    else:
                        queue_refill.apply_async(args=[transaction.id], eta=eta)
                else:
                    queue_refill.delay(transaction.id)
            else:
                queue_refill.delay(transaction.id)
            return HttpResponseRedirect(reverse('transaction_detail', args=[transaction.id]))
        else:
            return render(request, self.template_name, {'form': form,
                                                    'verify_carrier': self.request.user.profile.company.verify_carrier})

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.trigger = "MN"
        return super(ManualRefill, self).form_valid(form)


class UnusedPinList(ListView):
    model = UnusedPin

    def get_queryset(self):
        return UnusedPin.objects.filter(company=self.request.user.profile.company)


class UnusedPinCreate(CreateView):
    form_class = forms.UnusedPinForm
    model = UnusedPin

    def get_initial(self):
        data = {}
        if self.request.GET.get('pin'):
            data['pin'] = self.request.GET['pin']
        if self.request.GET.get('plan'):
            data['plan'] = Plan.objects.get(id=self.request.GET['plan'])
        return data

    def get_context_data(self, **kwargs):
        context = super(UnusedPinCreate, self).get_context_data(**kwargs)
        if self.request.GET.get('plan'):
            context['plan'] = Plan.objects.get(id=self.request.GET['plan'])
        return context

    def form_valid(self, form):
        self.object = unusedpin = form.save(commit=False)
        unusedpin.user = self.request.user
        unusedpin.company = self.request.user.profile.company
        for charge in Charge.objects.filter(pin=unusedpin.pin, pin_used=False):
            charge.pin_used = True
            charge.save()
            unusedpin.notes = "%s %s" % (unusedpin.notes, charge.get_full_url())
        return super(UnusedPinCreate, self).form_valid(form)


class UnusedPinUpdate(UpdateView):
    form_class = forms.UnusedPinForm
    model = UnusedPin


class UnusedPinDelete(DeleteView):
    model = UnusedPin

    def get_success_url(self):
        return reverse('unusedpin_list')


class UnusedPinImport(View):
    template_name = 'core/unusedpin_import.html'
    form_class = forms.UnusedPinImportForm

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form, 'confirm' : False})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)
        if form.is_valid():
            if form.cleaned_data['confirm'] == 'False':
                try:
                    pins = ext_lib.import_csv(form.cleaned_data['file'])
                    cache_id = str(uuid.uuid1())
                    plan = Plan.objects.get(id=form.cleaned_data['plan'])
                    cache.add(key=cache_id, value={'plan' : plan, 'pins': pins, 'notes': form.cleaned_data['notes']}, timeout=600)
                    return render(request, self.template_name, {'form': form, 'confirm': True, 'plan': plan, 'pins': pins, 'cache_id': cache_id})
                except Exception, e:
                    messages.add_message(self.request, messages.ERROR, 'Failed to read import file, please ensure it is a csv and that it follows the template.')
                    logger.error(traceback.format_exc())
                    return HttpResponseRedirect(reverse('unusedpin_list'))

            else:
                try:
                    cache_data = cache.get(form.cleaned_data['cache_id'])
                    for pin in cache_data['pins']:
                        unusedpin = UnusedPin(user=request.user, company=request.user.profile.company, plan=cache_data['plan'], pin=pin['pin'], used=False, notes=cache_data['notes'])
                        unusedpin.save()
                    messages.add_message(request, messages.SUCCESS, 'Successfully imported pins for plan "%s".'%cache_data['plan'])
                except Exception, e:
                    messages.add_message(self.request, messages.ERROR, 'Pin import failed, please contact the administrator for furthur information')
                    logger.error(traceback.format_exc())
                finally:
                    return HttpResponseRedirect(reverse('unusedpin_list'))
        else:
            return render(request, self.template_name, {'form': form, 'confirm': False})


class TransactionList(ListView):
    model = Transaction

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Transaction.objects.all()
        else:
            return Transaction.objects.filter(company=self.request.user.profile.company).order_by('ended')

    def get_context_data(self, **kwargs):
        context = super(TransactionList, self).get_context_data(**kwargs)
        context['user_list'] = User.objects.filter(is_superuser=False)
        return context


class TransactionDetail(DetailView):
    model = Transaction

    def get_context_data(self, **kwargs):
        context = super(TransactionDetail, self).get_context_data(**kwargs)
        autorefill = self.get_object().autorefill
        context['payment_gateway_cash'] = autorefill and self.get_object().customer.charge_getaway == Customer.CASH
        context['verify_carrier'] = self.get_object().company.verify_carrier
        return context


class ConfirmDPView(View):
    form_class = forms.ConfirmDPForm
    model = ConfirmDP
    template_name = 'core/confirm_dp.html'

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form, 'success': False})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            if form.cleaned_data['success'] == 'False':
                try:
                    login = form.cleaned_data['login']
                    password = form.cleaned_data['password']
                    s = requests.Session()
                    s.get('https://www.dollarphonepinless.com/sign-in',
                          auth=HTTPBasicAuth(login, password))
                    url_success = 'https://www.dollarphonepinless.com/dashboard'
                    r = s.get(url_success)
                    status_code = r.status_code
                    if status_code != 200:
                        logger.debug('Status code: %s Page: %s' % (status_code, r.text))
                        raise Exception("Failed to login to Dollar Phone, please check the credentials")
                    payload = {'user_authentication[delivery_method]': "email:%s" % login}
                    r = s.post('https://www.dollarphonepinless.com/user_authentication/authenticate', data=payload)
                    # messages.add_message(request, messages.SUCCESS, '%s %s' % (r.url, r.text))
                    cache_id = str(uuid.uuid1())
                    cache.add(key=cache_id, value={'session': s}, timeout=1200)
                    return render(request, self.template_name,
                                  {'form': form, 'success': True, 'cache_id': cache_id})
                except Exception, msg:
                    logger.error(traceback.format_exc())
                    # messages.add_message(request, messages.ERROR, '%s %s' % (r.url, r.text))
                    return render(request, self.template_name)
            else:
                cache_data = cache.get(form.cleaned_data['cache_id'])
                s = cache_data['session']
                payload = {'user_authentication[code]': form.cleaned_data['confirm']}
                r = s.post('https://www.dollarphonepinless.com/user_authentication/new', data=payload)
                messages.add_message(self.request, messages.ERROR, '%s %s' % (r.url, r.text))
                if r.url == 'https://www.dollarphonepinless.com/dashboard':
                    messages.add_message("Dollarphone account verified successfully")
                else:
                    messages.add_message(self.request, messages.ERROR, '%s %s' % (r.url, r.text))
                return render(request, self.template_name)
        else:
            return render(request, self.template_name, {'form': form, 'success': False})
                    # br = mechanize.Browser()
                    # cj = cookielib.LWPCookieJar()
                    # br.set_handle_equiv(True)
                    # br.set_handle_redirect(True)
                    # br.set_handle_referer(True)
                    # br.set_handle_robots(False)
                    # br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)
                    # br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
                    # br.open('https://www.dollarphonepinless.com/sign-in')
                    # br.select_form(nr=0)
                    # br.form['user_session[email]'] = form.cleaned_data['login']
                    # br.form['user_session[password]'] = form.cleaned_data['password']
                    # br.submit()
      ##              messages.add_message(self.request, messages.ERROR, '%s %s' % (br.geturl(), br.response().read()))
                    # br.select_form(nr=0)
                    # br.form['user_authentication[delivery_method]'] = ["email:%s" % form.cleaned_data['login']]
                    # br.submit()
    ##                messages.add_message(self.request, messages.ERROR, '%s %s' % (br.geturl(), br.response().read()))
                    # cache_id = str(uuid.uuid1())
                    # cache.add(key=cache_id, value={'session': br}, timeout=1200)
                    # return render(request, self.template_name,
                    #               {'form': form, 'success': True, 'cache_id': cache_id})
                # except Exception, msg:
                #     messages.add_message(self.request, messages.ERROR, '%s %s' % (br.geturl(), br.response().read()))
                #     return render(request, self.template_name)
            # else:
            #     cache_data = cache.get(form.cleaned_data['cache_id'])
            #     br = cache_data['session']
##                messages.add_message(self.request, messages.ERROR, '%s %s' % (br.geturl(), br.response().read()))
                # br.select_form(nr=0)
                # br.form['user_authentication[code]'] = form.cleaned_data['confirm']
                # br.submit()
  ##              messages.add_message(self.request, messages.ERROR, '%s %s' % (br.geturl(), br.response().read()))
                # if br.geturl() == 'https://www.dollarphonepinless.com/dashboard':
                #     messages.add_message("Dollarphone account verified successfully")
                # else:
                #     messages.add_message(self.request, messages.ERROR, '%s %s' % (br.geturl(), br.response().read()))
                # return render(request, self.template_name)
        # else:
        #     return render(request, self.template_name, {'form': form, 'success': False})


class PinReportList(ListView):
    model = PinReport

    def get_queryset(self):
        return PinReport.objects.filter(company=self.request.user.profile.company)


class PinReportDetail(DetailView):
    model = PinReport

    def get_context_data(self, **kwargs):
        context = super(PinReportDetail, self).get_context_data(**kwargs)
        pin_fields = PinField.objects.filter(pin_report=self.get_object())
        context['pin_fields'] = pin_fields
        return context


def pinreport_download(request, order_id):
    pinreport = PinReport.objects.get(id=order_id)
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment;filename=%s.csv' % pinreport.subject
    writer = csv.writer(response)
    writer.writerow(['Pin',
                     'Plan',
                     'Cost'
                     ])
    for pin_field in PinField.objects.filter(pin_report=pinreport):
        writer.writerow([
            pin_field.pin,
            pin_field.plan,
            pin_field.cost
        ])
    return response


class NewsDetail(DetailView):
    model = News


def news(request):
    return render(request, 'core/news.html')


def ajax_news(request):
    ajax_response = {"sEcho": request.GET['sEcho'], "aaData": [], 'iTotalRecords': 0}
    order = '-'
    if request.GET['sSortDir_0'] == 'desc':
        order = ''
    for news in News.objects.filter(title__icontains=request.GET['sSearch'],
                                    category__contains=request.GET['sSearch_0']).order_by(order + 'created').exclude(category='EZ'):
        ajax_response['iTotalRecords'] += 1
        ajax_response['aaData'].append(['<a href=\'%s' % (reverse('news_detail', args=[news.id])) +
                                        '\'>' + news.__unicode__() + '</a>',
                                        news.created.astimezone(timezone('US/Eastern')).strftime("%m/%d/%y"
                                                                                                 " %I:%M:%S%p")])
    ajax_response['iTotalDisplayRecords'] = len(ajax_response['aaData'])
    start = int(request.GET['iDisplayStart'])
    length = int(request.GET['iDisplayLength'])
    ajax_response['aaData'] = ajax_response['aaData'][start:start+length]
    json_data = json.dumps(ajax_response)
    return HttpResponse(json_data, content_type='application/json')


def ajax_refill_as_walk_in(request):
    if request.GET['number'].strip().isdigit() and len(request.GET['number'].strip()) == 10 and\
            not PhoneNumber.objects.filter(number=request.GET['number'].strip(),
                                           company=request.user.profile.company):
        charge_gateway = Customer.CASH
        if request.GET['gateway']:
            charge_gateway = Customer.CASH_PREPAYMENT
        customer = Customer.objects.create(company=request.user.profile.company, user=request.user, first_name='Walk',
                                           last_name='in', charge_type=Customer.CASH, charge_getaway=charge_gateway,
                                           primary_email='', zip='', usaepay_custid='',
                                           send_pin_prerefill=request.user.profile.company.send_pin_prerefill,
                                           send_status=request.user.profile.company.send_status)
        PhoneNumber.objects.create(company=request.user.profile.company, customer=customer,
                                   number=request.GET['number'])
        return HttpResponse(json.dumps({'valid': True, 'id': str(customer.id)}), content_type='application/json')
    else:
        return HttpResponse(json.dumps({'valid': False, 'error': 'Customer with that number already exist.'}), content_type='application/json')


def customer_transactions(request, pk):
    return render(request, 'core/customer_transactions.html', {'customer_transactions': pk,
                                                               'full_name': Customer.objects.get(id=pk).__unicode__()})


def ajax_customer_transactions(request):
    ajax_response = {"sEcho": request.GET['sEcho'], "aaData": [], 'iTotalRecords': 0}
    for transaction in Transaction.objects.filter(autorefill__customer__id=request.GET['customer_transactions'],
                                                  company=request.user.profile.company).order_by('-started'):
        ajax_response['iTotalRecords'] += 1
        started = ''
        if transaction.started:
            started = 'Started: <b>' +\
                    transaction.started.astimezone(timezone('US/Eastern')).strftime("%m/%d/%y %I:%M:%S%p") + '</b>'
        ended = ''
        if transaction.ended:
            ended = 'Ended: <b>' +\
                    transaction.ended.astimezone(timezone('US/Eastern')).strftime("%m/%d/%y %I:%M:%S%p") + '</b>'
        trigger = ''
        if transaction.autorefill:
            if transaction.autorefill.trigger == AutoRefill.TRIGGER_SC:
                trigger = '<span class=\"glyphicon glyphicon-time\" data-toggle=\"tooltip\" title=\"%s\"' \
                          ' aria-hidden=\"true\" style=\"cursor:pointer\"></span>' % 'Schedule'
            elif transaction.autorefill.trigger == AutoRefill.TRIGGER_MN:
                trigger = '<span class=\"glyphicon glyphicon-hand-up\" data-toggle=\"tooltip\" title=\"%s\"' \
                          ' aria-hidden=\"true\" style=\"cursor:pointer\"></span>' % 'Manual'
        else:
            if 'Sc' in transaction.trigger:
                trigger = '<span class=\"glyphicon glyphicon-time\" data-toggle=\"tooltip\" title=\"%s\"' \
                          ' aria-hidden=\"true\" style=\"cursor:pointer\"></span>' % 'Schedule'
            elif 'Ma' in transaction.trigger:
                trigger = '<span class=\"glyphicon glyphicon-hand-up\" data-toggle=\"tooltip\" title=\"%s\"' \
                          ' aria-hidden=\"true\" style=\"cursor:pointer\"></span>' % 'Manual'
        ajax_response['aaData'].append([type(transaction).__name__,
                                        '<a href=\'%s' % (reverse('transaction_detail', args=[transaction.id])) +
                                        '\'>Transaction #' + transaction.__unicode__() + '</a> (<b>'
                                        + str(transaction.get_status_display()) + '</b>) for <b>'
                                        + transaction.phone_number_str + '</b> (<b>' +
                                        str(transaction.get_state_display()) + '</b>) '
                                        + "Plan: <b>%s</b> " % transaction.plan_str + started + ' ' + ended + ' '
                                        + trigger])
    ajax_response['iTotalDisplayRecords'] = len(ajax_response['aaData'])
    start = int(request.GET['iDisplayStart'])
    length = int(request.GET['iDisplayLength'])
    ajax_response['aaData'] = ajax_response['aaData'][start:start+length]
    json_data = json.dumps(ajax_response)
    return HttpResponse(json_data, content_type='application/json')


def customer_autorefills(request, pk):
    return render(request, 'core/customer_autorefills.html', {'customer_autorefills': pk,
                                                              'full_name': Customer.objects.get(id=pk).__unicode__()})


def save_note_of_transaction(request, pk):
    transaction = Transaction.objects.filter(id=(pk))[0]
    note = request.GET.get('note')
    transaction.transaction_note = note
    transaction.save()
    return HttpResponse(json.dumps({'note': transaction.transaction_note}),
                        content_type='application/json')


def ajax_customer_autorefills(request):
    ajax_response = {"sEcho": request.GET['sEcho'], "aaData": [], 'iTotalRecords': 0}
    for autorefill in AutoRefill.objects.filter(customer__id=request.GET['customer_autorefills'],
                                                trigger='SC', company=request.user.profile.company):
        enabled = '</a><span class="fa fa-minus-circle text-danger"></span>'
        if autorefill.enabled:
            enabled = '</a><span class="fa fa-check-circle text-success"></span>'
        ajax_response['iTotalRecords'] += 1
        last_renewal = ''
        if autorefill.last_renewal_date:
            last_renewal = 'Last renewal: <b>' + str(autorefill.last_renewal_date) + '</b>'
        ajax_response['aaData'].append([type(autorefill).__name__,
                                        '<a href=\'%s' % (reverse('autorefill_update', args=[autorefill.id])) +
                                        '\'>Scheduled Refill #' + autorefill.__unicode__() + '</a> ' + enabled +
                                        ' for <b>' + autorefill.phone_number + '</b> Scheduled for: <b>'
                                        + str(autorefill.renewal_date) + '</b> ' + last_renewal + "Plan: <b>" + str(autorefill.plan) + '</b>'])
    ajax_response['iTotalDisplayRecords'] = len(ajax_response['aaData'])
    start = int(request.GET['iDisplayStart'])
    length = int(request.GET['iDisplayLength'])
    ajax_response['aaData'] = ajax_response['aaData'][start:start+length]
    json_data = json.dumps(ajax_response)
    return HttpResponse(json_data, content_type='application/json')


def customer_cc_charges(request, pk):
    return render(request, 'core/customer_cc_charges.html', {'customer_cc_charges': pk,
                                                             'full_name': Customer.objects.get(id=pk).__unicode__()})


def ajax_customer_cc_charges(request):
    ajax_response = {"sEcho": request.GET['sEcho'], "aaData": [], 'iTotalRecords': 0}
    for charge in Charge.objects.filter(customer__id=request.GET['customer_cc_charges'],
                                        company=request.user.profile.company).order_by('-created'):
        ajax_response['iTotalRecords'] += 1
        cc_last_four = ''
        used = '</a><span class="fa fa-minus-circle text-danger"></span>'
        used_for = ' used for '
        transaction = ''
        if charge.creditcard:
            cc_last_four = ' *' + charge.creditcard[-4:]
        if charge.used:
            used = '</a><span class="fa fa-check-circle text-success"></span>'
        if charge.autorefill:
            if charge.autorefill.phone_number:
                used_for += '<b>' + charge.autorefill.phone_number + '</b>'
        if TransactionCharge.objects.exclude(transaction=None).filter(charge=charge):
            transaction = ' Transaction : <b>' + str(TransactionCharge.objects.filter(charge=charge)[0].transaction.id)\
                          + '</b>'
        ajax_response['aaData'].append([type(charge).__name__,
                                        '<a href=\'%s' % (reverse('charge_detail', args=[charge.id])) +
                                        '\'>Credit Card Charge #' + charge.__unicode__() + cc_last_four + '</a> '
                                        + used + ' (<b>'
                                        + charge.get_status_display() + '</b>)' + used_for + ' Created: <b>' +
                                        charge.created.astimezone(timezone('US/Eastern')).strftime("%m/%d/%y "
                                                                                                   "%I:%M:%S%p") +
                                         '</b> for <b>$' + str(charge.amount) + '</b> (available amount <b>$'
                                         + str(charge.amount - charge.summ) + '</b>)' + transaction])
    ajax_response['iTotalDisplayRecords'] = len(ajax_response['aaData'])
    start = int(request.GET['iDisplayStart'])
    length = int(request.GET['iDisplayLength'])
    ajax_response['aaData'] = ajax_response['aaData'][start:start+length]
    json_data = json.dumps(ajax_response)
    return HttpResponse(json_data, content_type='application/json')


def ajax_check_manual_transaction_ended(request, pk):
    manual_refill = AutoRefill.objects.get(id=int(pk))
    if Transaction.objects.get(autorefill=manual_refill).ended and\
                    Transaction.objects.get(autorefill=manual_refill).state == 'C':
        return HttpResponse(json.dumps({'ended': True}), content_type='application/json')
    else:
        return HttpResponse(json.dumps({'ended': False}), content_type='application/json')


def ajax_schedule_monthly(request, pk):
    manual_refill = AutoRefill.objects.get(id=int(pk))
    type = request.GET.get('type')
    if request.user.profile.company.check_available_schedule_create():
        if manual_refill.customer.company == request.user.profile.company:
            if not (AutoRefill.objects.filter(customer=manual_refill.customer, trigger='SC',
                                              phone_number=manual_refill.phone_number) and
                    request.user.profile.company.block_duplicate_schedule):
                if type == 'carrier':
                    result = create_schedule_by_carrier(request.user,
                                                        manual_refill.phone_number,
                                                        manual_refill.customer)
                    if result['valid']:
                        return HttpResponse(
                            json.dumps({'valid': True,
                                        'id': str(result['autorefill'].id)}),
                                        content_type='application/json')
                    else:
                        return HttpResponse(
                            json.dumps({'valid': False,
                                        'error': result['message']}),
                                        content_type='application/json')
                else:
                    default_time = AutoRefill.MN
                    if manual_refill.plan.carrier.default_time:
                        default_time = manual_refill.plan.carrier.default_time
                    delta = datetime.timedelta()
                    if manual_refill.plan.carrier.renew_days:
                        delta = datetime.timedelta(
                            days=manual_refill.plan.carrier.renew_days)
                    elif manual_refill.plan.carrier.renew_months:
                        delta = relativedelta(
                            months=manual_refill.plan.carrier.renew_months)
                    if int(request.GET['ended']):
                        next_renewal_date = Transaction.objects.get(
                            autorefill=manual_refill).ended.date()
                    else:
                        next_renewal_date = Transaction.objects.get(
                            autorefill=manual_refill).started.date()
                    while next_renewal_date <= datetime.datetime.now(
                            pytz.timezone('US/Eastern')).date():
                        next_renewal_date += delta
                    scheduler_refill = AutoRefill.objects.create(
                        user=request.user,
                        company=request.user.profile.company,
                        customer=manual_refill.customer,
                        plan=manual_refill.plan,
                        phone_number=manual_refill.phone_number,
                        trigger='SC',
                        schedule=default_time,
                        renewal_date=next_renewal_date - datetime.timedelta(
                            days=int(request.GET['minus'])))
                    step_name = 'Schedule monthly'
                    if int(request.GET['minus']):
                        step_name = 'Schedule monthly if this refill' \
                                    ' was done when plan was already expired' \
                                    ' or a new activation refill'
                    Transaction.objects.get(id=request.GET['transaction_id']
                                            ).add_transaction_step(
                        'create new scheduled refill',
                        step_name,
                        'S',
                        'User ' + request.user.profile.__unicode__() +
                        ' created a new scheduled refill '
                        + '<a href=\"%s' %
                        (reverse('autorefill_update',
                                 args=[scheduler_refill.id])) + '\">'
                        + str(scheduler_refill.id) + '</a>')
            else:
                return HttpResponse(
                    json.dumps({'valid': False,
                                'error': 'Scheduler refill for this '
                                         'customer and this number '
                                         'already exists.'}),
                                    content_type='application/json')
            return HttpResponse(
                json.dumps({'valid': True,
                            'id': str(scheduler_refill.id)}),
                content_type='application/json')
        else:
            return HttpResponse(
                json.dumps({'valid': False,
                            'error': 'This user is not from your company.'}),
                            content_type='application/json')
    else:
        return HttpResponse(
            json.dumps({'valid': False,
                        'error': 'Schedule limit has been reached.'
                                 ' Please contact administrator.'}),
                        content_type='application/json')


def ajax_create_schedule_in_customer(request, pk):
    customer = Customer.objects.filter(id=int(pk))[0]
    company = request.user.profile.company
    phone_number = PhoneNumber.objects.filter(customer=customer,
                                              company=company,
                                              number=request.GET.get('phone_number'))
    if customer.company == request.user.profile.company:
        if request.user.profile.company.check_available_schedule_create():
            if phone_number:
                phone_number = phone_number[0]
                if not (
                    AutoRefill.objects.filter(customer=customer, trigger='SC',
                                              phone_number=phone_number) and
                    request.user.profile.company.block_duplicate_schedule):
                    result = create_schedule_by_carrier(request.user,
                                                        phone_number,
                                                        customer)
                    if result['valid']:
                        return HttpResponse(
                            json.dumps({'valid': True,
                                        'id': str(result['autorefill'].id)}),
                                        content_type='application/json')
                    else:
                        return HttpResponse(
                            json.dumps({'valid': False,
                                        'error': result['message']}),
                                        content_type='application/json')
                else:
                    return HttpResponse(
                        json.dumps({'valid': False,
                                    'error': 'Scheduler refill for this '
                                             'customer and this number '
                                             'already exists.'}),
                        content_type='application/json')
            else:
                return HttpResponse(
                    json.dumps({'valid': False,
                                'error': 'Error with number!'}),
                    content_type='application/json')
        else:
            return HttpResponse(
                json.dumps({'valid': False,
                            'error': 'Schedule limit has been reached.'
                                     ' Please contact administrator.'}),
                content_type='application/json')
    else:
        return HttpResponse(
            json.dumps({'valid': False,
                        'error': 'This user is not from your company.'}),
            content_type='application/json')


def create_schedule_by_carrier(user, phone_number, customer):
    if not user.profile.company.verify_carrier:
        return {'valid': False, 'message': "This option isn't available for you."}
    result = verify_carrier.get_mdn_number(str(phone_number), user.profile.company)
    if not result['valid_for_schedule']:
        return {'valid': False, 'message': result['error']}
    autorefill = AutoRefill.objects.create(user=user,
                                           company=user.profile.company,
                                           customer=customer,
                                           plan=result['plan'],
                                           phone_number=phone_number,
                                           schedule=result['schedule'],
                                           trigger='SC',
                                           renewal_date=result['renewal_date']
                                           )
    return {'valid': True,
            'autorefill': autorefill,
            'mdn_status': result['mdn_status']}


def ajax_last_transaction_data(request):
    if Transaction.objects.filter(phone_number_str=request.GET['phone_number']) and\
            Transaction.objects.filter(phone_number_str=request.GET['phone_number']).order_by('-id')[0].autorefill:
        return HttpResponse(json.dumps({'exist': True,
                                        'carrier': Transaction.objects.filter(phone_number_str=request.GET['phone_number']).order_by('-id')[0].autorefill.plan.carrier.id,
                                        'plan': Transaction.objects.filter(phone_number_str=request.GET['phone_number']).order_by('-id')[0].autorefill.plan.id,
                                        'refill_type': Transaction.objects.filter(phone_number_str=request.GET['phone_number']).order_by('-id')[0].autorefill.refill_type}),
                            content_type='application/json')
    else:
        return HttpResponse(json.dumps({'exist': False,
                                        'carrier': '',
                                        'plan': '',
                                        'refill_type': ''}),
                            content_type='application/json')


def ajax_skip_next_refill(request, pk):

    try:
        autorefill = AutoRefill.objects.get(id=pk)
        autorefill_dict = request.GET.dict()
        autorefill_dict['customer'] = Customer.objects.get(id=autorefill_dict['customer'])
        autorefill_dict['plan'] = Plan.objects.get(id=autorefill_dict['plan'])
        if autorefill_dict['renewal_date'] == '':
            autorefill_dict['renewal_date'] = None
        else:
            autorefill_dict['renewal_date'] = datetime.datetime.strptime(autorefill_dict['renewal_date'], '%m/%d/%Y')
        if autorefill_dict['renewal_end_date'] == '':
            autorefill_dict['renewal_end_date'] = None
        else:
            autorefill_dict['renewal_end_date'] = datetime.datetime.strptime(autorefill_dict['renewal_end_date'],
                                                                             '%m/%d/%Y')
        if autorefill_dict['renewal_interval'] == '':
            autorefill_dict['renewal_interval'] = None
        else:
            autorefill_dict['renewal_interval'] = int(autorefill_dict['renewal_interval'])
        if autorefill_dict['enabled'] == 'true':
            autorefill_dict['enabled'] = True
        else:
            autorefill_dict['enabled'] = False
        if autorefill_dict['pre_refill_sms'] == 'true':
            autorefill_dict['pre_refill_sms'] = True
        else:
            autorefill_dict['pre_refill_sms'] = False
        if autorefill_dict['need_buy_pins'] == 'true':
            autorefill_dict['need_buy_pins'] = True
        else:
            autorefill_dict['need_buy_pins'] = False
        for atr in autorefill_dict:
            setattr(autorefill, atr, autorefill_dict[atr])
        autorefill.save()
        autorefill.set_renewal_date_to_next(today=autorefill.renewal_date)
        data = {'valid': True}
        if autorefill.renewal_date:
            data['renewal_date'] = autorefill.renewal_date.strftime('%m/%d/%Y')
        if autorefill.renewal_end_date:
            data['end_renewal_date'] = autorefill.renewal_end_date.strftime('%m/%d/%Y')
        return HttpResponse(
            json.dumps(data),
            content_type='application/json'
        )
    except Exception, msg:
        return HttpResponse(
            json.dumps({'valid': False, 'error_message': '%s' % msg}),
            content_type='application/json'
        )


def compare_pins_with_dollarphone(request):
    company = request.user.profile.company
    if not company.dollar_user or not company.dollar_pass:
        message = "Dollarphone account is missing in company. Please correct one of these to proceed"
        messages.add_message(request, messages.ERROR, '%s' % message)
        return HttpResponseRedirect(reverse('pinreport_list'))
    queue_compare_pins_with_dollarphone.delay(company.id)
    messages.add_message(request, messages.SUCCESS, 'Compare started')
    return HttpResponseRedirect(reverse('pinreport_list'))


def ajax_unused_pins(request):
    ajax_response = {"sEcho": request.GET['sEcho'], "aaData": [], 'iTotalRecords': 0}
    filters = request.GET['sSearch'].split(' ')
    orders = [('6', 'created'), ('7', 'updated')]
    order_by = 'created'
    for order in orders:
        if order[0] == request.GET['iSortCol_0']:
            order_by = order[1]
            break
    direction = '-'
    if request.GET['sSortDir_0'] != 'desc':
        direction = ''
    pins = UnusedPin.objects.filter(reduce(operator.and_, (Q(pin__icontains=val) |
                                                           Q(notes__icontains=val)
                                                           for val in filters)),
                                    company=request.user.profile.company).order_by(direction+order_by)
    if request.GET['sSearch_5'] == '/pin-report':
        pins = pins.exclude(notes=None).exclude(notes='')
    if request.GET['sSearch_4'] == 'True':
        pins = pins.filter(used=True)
    if request.GET['sSearch_4'] == 'False':
        pins = pins.filter(used=False)
    if request.GET['sSearch_3']:
        pins = pins.filter(plan__id=long(request.GET['sSearch_3']))
    for pin in pins:
        customer = ''
        if pin.transaction and pin.transaction.autorefill:
            customer = '<a target="_blank" href=\'%s' % (reverse('customer_update', args=[pin.transaction.autorefill.customer.id])) +\
                       '\'>%s</a>' % pin.transaction.autorefill.customer.full_name
        ajax_response['iTotalRecords'] += 1
        ajax_response['aaData'].append(['<input type="hidden" class="pin_field" value="%s">' % pin.id +
                                        '<input class="selected_field" type="checkbox"/>',
                                        '<a target="_blank" href=\'%s' % (reverse('unusedpin_update', args=[pin.id])) +
                                        '\'>%s</a>' % pin.pin, pin.plan.__unicode__(), pin.used, customer, pin.notes,
                                        pin.created.astimezone(timezone('US/Eastern')).strftime("%m/%d/%y %H:%M"),
                                        pin.updated.astimezone(timezone('US/Eastern')).strftime("%m/%d/%y %H:%M")])
    ajax_response['iTotalDisplayRecords'] = len(ajax_response['aaData'])
    start = int(request.GET['iDisplayStart'])
    length = int(request.GET['iDisplayLength'])
    ajax_response['aaData'] = ajax_response['aaData'][start:start+length]
    json_data = json.dumps(ajax_response)
    return HttpResponse(json_data, content_type='application/json')


def ajax_log(request):
    ajax_response = {"sEcho": request.GET['sEcho'], "aaData": [],
                     'iTotalRecords': Log.objects.filter(company=request.user.profile.company).count(),
                     'iTotalDisplayRecords': Log.objects.filter(company=request.user.profile.company,
                                                                note__icontains=request.GET['sSearch']).count()}
    start = int(request.GET['iDisplayStart'])
    length = int(request.GET['iDisplayLength'])
    if request.GET['sSortDir_0'] == 'asc':
        count_up = start+1
        for log in Log.objects.filter(company=request.user.profile.company,
                                      note__icontains=request.GET['sSearch']).order_by('created')[start:start+length]:
            log_details = ''
            if len(log.note.split('\n')) > 1:
                log_details = log.note.split('\n')[1]
            ajax_response["aaData"].append([count_up,
                                        log.created.astimezone(timezone('US/Eastern')).strftime("%m/%d/%y %I:%M:%S%p"),
                                        '<div><div style=\"cursor: pointer; padding: 0px;\"'
                                        ' class=\"panel-heading accordion-toggle collapsed\"'
                                        ' data-toggle=\"collapse\" data-target=\"#collapse'+str(log.id)+'\">'
                                        +log.note.split('\n')[0]+'</div></div>'+'<div id=\"collapse'+str(log.id)+
                                        '\" class=\"panel-collapse collapse\">'+log_details+'</div>'])
            count_up += 1
    else:
        count_up = int(ajax_response['iTotalDisplayRecords'])-start
        for log in Log.objects.filter(company=request.user.profile.company,
                                      note__icontains=request.GET['sSearch']).order_by('-created')[start:start+length]:
            log_details = ''
            if len(log.note.split('\n')) > 1:
                log_details = log.note.split('\n')[1]
            ajax_response["aaData"].append([count_up,
                                        log.created.astimezone(timezone('US/Eastern')).strftime("%m/%d/%y %I:%M:%S%p"),
                                        '<div><div style=\"cursor: pointer; padding: 0px;\"'
                                        ' class=\"panel-heading accordion-toggle collapsed\"'
                                        ' data-toggle=\"collapse\" data-target=\"#collapse'+str(log.id)+'\">'
                                        +log.note.split('\n')[0]+'</div></div>'+'<div id=\"collapse'+str(log.id)+
                                        '\" class=\"panel-collapse collapse\">'+log_details+'</div>'])
            count_up -= 1
    json_data = json.dumps(ajax_response)
    return HttpResponse(json_data, content_type='application/json')


def ajax_carriers_list(request):
    orders = [('0', 'name'), ('1', 'recharge_number'), ('2', 'renew_days'),
              ('3', 'renew_months'), ('4', 'created'), ('5', 'updated')]
    order_by = 'name'
    for order in orders:
        if order[0] == request.GET['iSortCol_0']:
            order_by = order[1]
            break
    direction = ''
    if request.GET['sSortDir_0'] == 'desc':
        direction = '-'
    filters = request.GET['sSearch'].split(' ')
    filtered = Carrier.objects.filter(reduce(operator.and_, (Q(name__icontains=val) |
                                                             Q(recharge_number__icontains=val) |
                                                             Q(renew_days__icontains=val) |
                                                             Q(renew_months__icontains=val)
                                                             for val in filters)))
    ajax_response = {"sEcho": request.GET['sEcho'], "aaData": [],
                     'iTotalRecords': Carrier.objects.all().count(),
                     'iTotalDisplayRecords': filtered.count()}
    start = int(request.GET['iDisplayStart'])
    length = int(request.GET['iDisplayLength'])
    for carrier in filtered.order_by(direction+order_by)[start:start+length]:
        name = carrier.name
        if request.user.is_superuser:
            name = '<a href=\'%s' % (reverse('carrier_update', args=[carrier.id])) + '\'>' + carrier.name + '</a>'
        ajax_response['aaData'].append(['<img src=\"/static/img/' + slugify(carrier) + '.jpg\"'
                                        ' style=\"width:32px;\" >' + name, carrier.recharge_number, carrier.renew_days,
                                        carrier.renew_months,
                                        carrier.created.astimezone(timezone('US/Eastern')).strftime("%m/%d/%y %H:%M"),
                                        carrier.updated.astimezone(timezone('US/Eastern')).strftime("%m/%d/%y %H:%M")])
    return HttpResponse(json.dumps(ajax_response), content_type='application/json')


def ajax_customers_list(request):
    orders = [('0', 'first_name'), ('1', 'last_name'), ('7', 'charge_type'),
              ('8', 'charge_getaway'), ('9', 'enabled'), ('10', 'created'), ('11', 'updated')]
    order_by = 'first_name'
    for order in orders:
        if order[0] == request.GET['iSortCol_0']:
            order_by = order[1]
            break
    direction = ''
    if request.GET['sSortDir_0'] == 'desc':
        direction = '-'
    filters = request.GET['sSearch'].split(' ')
    filtered = Customer.objects.filter(reduce(operator.and_, (Q(first_name__icontains=val) |
                                                              Q(last_name__icontains=val) |
                                                              Q(primary_email__icontains=val) |
                                                              Q(city__icontains=val) |
                                                              Q(state__icontains=val) |
                                                              Q(zip__icontains=val)
                                                              for val in filters)),
                                       company=request.user.profile.company)
    for charge_getaway_choice in Customer.CHARGE_GETAWAY_CHOICES:
        if charge_getaway_choice[1] == request.GET['sSearch_8']:
            filtered = filtered.filter(charge_getaway=charge_getaway_choice[0])
            break
    if request.GET['sSearch_9'] == 'Enabled':
        filtered = filtered.filter(enabled=True)
    elif request.GET['sSearch_9'] == 'Disabled':
        filtered = filtered.filter(enabled=False)
    if bool(request.GET['sSearch_12']):
        filtered = filtered.filter(Q(usaepay_customer_id=None) | Q(usaepay_customer_id=''))
    ajax_response = {"sEcho": request.GET['sEcho'], "aaData": [],
                     'iTotalRecords': Customer.objects.filter(company=request.user.profile.company).count(),
                     'iTotalDisplayRecords': filtered.count()}
    start = int(request.GET['iDisplayStart'])
    length = int(request.GET['iDisplayLength'])
    for customer in filtered.order_by(direction+order_by)[start:start+length]:
        payment_type = ''
        for charge_type_choice in Customer.CHARGE_TYPE_CHOICES:
            if charge_type_choice[0] == customer.charge_type:
                payment_type = charge_type_choice[1]
                break
        payment_gateway = ''
        for charge_getaway_choice in Customer.CHARGE_GETAWAY_CHOICES:
            if charge_getaway_choice[0] == customer.charge_getaway:
                payment_gateway = charge_getaway_choice[1]
                break
        ajax_response['aaData'].append(['<a href=\'%s' % (reverse('customer_update', args=[customer.id])) + '\'>' +
                                        customer.first_name + '</a>', customer.last_name, customer.primary_email,
                                        customer.phone_numbers_list(), customer.city, customer.state, customer.zip,
                                        payment_type, payment_gateway, customer.enabled,
                                        customer.created.astimezone(timezone('US/Eastern')).strftime("%m/%d/%y %H:%M"),
                                        customer.updated.astimezone(timezone('US/Eastern')).strftime("%m/%d/%y %H:%M"),
                                        bool(customer.usaepay_customer_id),
                                        ])
    return HttpResponse(json.dumps(ajax_response), content_type='application/json')


def ajax_transactions_list(request):
    orders = [('1', 'customer_str'), ('3', 'plan_str'), ('4', 'refill_type_str'),
              ('6', 'state'), ('7', 'status'), ('9', 'completed'), ('11', 'started'), ('12', 'ended')]
    order_by = 'started'
    for order in orders:
        if order[0] == request.GET['iSortCol_0']:
            order_by = order[1]
            break
    direction = ''
    if request.GET['sSortDir_0'] == 'desc':
        direction = '-'
    filters = request.GET['sSearch'].split(' ')

    start_date = datetime.datetime.min
    end_date = datetime.datetime.max
    if request.GET['sSearch_10']:
        if request.GET['sSearch_10'].split(',')[0]:
            start_date = datetime.datetime.strptime(request.GET['sSearch_10'].split(',')[0], '%m/%d/%Y')
        if request.GET['sSearch_10'].split(',')[1]:
            end_date = datetime.datetime.strptime(request.GET['sSearch_10'].split(',')[1],
                                                  '%m/%d/%Y') + datetime.timedelta(hours=23, minutes=59, seconds=59)

    filtered = Transaction.objects.filter(reduce(operator.and_, (Q(id__icontains=val) |
                                                                 Q(customer_str__icontains=val) |
                                                                 Q(plan_str__icontains=val) |
                                                                 Q(refill_type_str__icontains=val) |
                                                                 Q(pin__icontains=val) |
                                                                 Q(phone_number_str__icontains=val)
                                                                 for val in filters)),
                                          status__icontains=request.GET['sSearch_7'],
                                          state__icontains=request.GET['sSearch_6'],
                                          started__gte=start_date,
                                          ended__lte=end_date)

    if not request.GET['sSearch_1']:
        pass
    else:
        filtered = filtered.filter(charge_getaway_name=request.GET['sSearch_1'])
    if request.GET['sSearch_4']:
        filtered = filtered.filter(refill_type_str__icontains=request.GET['sSearch_4'])
    if request.GET['sSearch_5'] == 'WP':
        filtered = filtered.exclude(pin__isnull=True).exclude(pin='')

    if request.GET['sSearch_5'] == 'WO':
        filtered = filtered.filter(Q(pin='') | Q(pin=None))

    if request.GET['sSearch_5'] == 'FDP':
        filtered = filtered.exclude(Q(pin__isnull=True) | Q(pin=''))
        filtered = filtered.filter(
            step__adv_status__icontains='extracted from Dollar Phone').distinct()

    if request.GET['sSearch_5'] == 'FUP':
        filtered = filtered.exclude(Q(pin__isnull=True) | Q(pin=''))
        filtered = filtered.filter(
            step__adv_status__icontains='unused-pin').distinct()

    if request.GET['sSearch_5'] == 'FME':
        filtered = filtered.exclude(Q(pin__isnull=True) | Q(pin=''))
        filtered = filtered.exclude(
            Q(step__adv_status__icontains='unused-pin') | Q(
                step__adv_status__icontains='extracted from Dollar Phone')).distinct()

    if not request.user.is_superuser:
        filtered = filtered.filter(company=request.user.profile.company)
    if request.GET['sSearch_8'] == 'True':
        filtered = filtered.filter(paid=True)
    elif request.GET['sSearch_8'] == 'False':
        filtered = filtered.filter(paid=False)
    if request.GET['sSearch_9'] == 'R':
        filtered = filtered.filter(completed='R')
    elif request.GET['sSearch_9'] == 'NA':
        filtered = filtered.filter(completed='NA')
    elif request.GET['sSearch_9'] == 'NR':
        filtered = filtered.filter(completed='NR')
    if request.GET['sSearch_2']:
        filtered = filtered.exclude(autorefill=None)
        if request.GET['sSearch_2'] == 'yes':
            filtered = filtered.filter(autorefill__need_buy_pins=True)
        elif request.GET['sSearch_2'] == 'no':
            filtered = filtered.filter(autorefill__need_buy_pins=False)
    if request.GET['sSearch_3'] == 'multi':
        filtered = filtered.filter(pin__icontains=',')
    elif request.GET['sSearch_3'] == 'one':
        filtered = filtered.exclude(pin='').exclude(pin__icontains=',')
    if request.GET['sSearch_0']:
        filtered = filtered.filter(Q(autorefill__isnull=False, autorefill__trigger__icontains=request.GET['sSearch_0']) |
                                   Q(trigger__icontains=request.GET['sSearch_0']))
    ajax_response = {"sEcho": request.GET['sEcho'], "aaData": [],
                     'iTotalRecords': Transaction.objects.filter(company=request.user.profile.company).count(),
                     'iTotalDisplayRecords': filtered.count()}
    start = int(request.GET['iDisplayStart'])
    length = int(request.GET['iDisplayLength'])
    for transaction in filtered.order_by(direction+order_by)[start:start+length]:
        customer = transaction.customer_str
        cc_charge = ''
        ended = ''
        if transaction.ended:
            ended = transaction.ended.astimezone(timezone('US/Eastern')).strftime("%m/%d/%y %H:%M")
        if transaction.autorefill:
            customer = '<a href=\'%s' % (reverse('customer_update', args=[transaction.autorefill.customer.id])) + '\'>' +\
                       transaction.customer_str + '</a>'
        if TransactionCharge.objects.filter(transaction=transaction):
            cc_charge = '<a href=\'%s' % (reverse('charge_detail',
                                                  args=[TransactionCharge.objects.filter(transaction=transaction)[0].charge.id])) + '\'>' +\
                        str(TransactionCharge.objects.filter(transaction=transaction)[0].charge.id) + '</a>'
        ajax_response['aaData'].append(['<a href=\'%s' % (reverse('transaction_detail', args=[transaction.id])) + '\'>' +
                                        str(transaction.id) + '</a>', customer, transaction.phone_number_str,
                                        transaction.plan_str, transaction.refill_type_str, transaction.pin,
                                        transaction.state, transaction.status, transaction.paid, transaction.completed,
                                        cc_charge,
                                        transaction.started.astimezone(timezone('US/Eastern')).strftime("%m/%d/%y %H:%M"),
                                        ended
                                        ])
    return HttpResponse(json.dumps(ajax_response), content_type='application/json')


def ajax_get_plan_selling_price(request):
    try:
        if not request.GET['plan_id'] or not request.GET['customer_id']:
            raise Exception('Plan or customer were not provided')
        plan = Plan.objects.get(id=long(request.GET['plan_id']))
        customer = Customer.objects.get(id=long(request.GET['customer_id']))
        count = 1
        if 'count' in request.GET:
            count = int(request.GET['count'])
        return HttpResponse(json.dumps({'success': True,
                                        'price': str(plan.get_plansellingprice(customer.company,
                                                                               customer.selling_price_level)*count)}),
                            content_type='application/json')
    except Exception, msg:
        return HttpResponse(json.dumps({'success': False, 'message': str(msg)}), content_type='application/json')


def ajax_transaction(request, pk):
    transaction = Transaction.objects.get(id=pk)
    steps = TransactionStep.objects.filter(transaction=pk).order_by('created')
    step_list = []
    url_pins = transaction.get_pin_url().split(', ')
    pins = transaction.pin.split(', ') if transaction.pin else ''
    rs_pins = {}

    for pin in pins:
        url_p = ''
        for url_pin in url_pins:
            if pin in url_pin and 'a href' in url_pin:
                url_p = url_pin
                url_p = url_p[url_p.find('href="')+len('href="'):url_p.rfind('">' + pin)]
                break

        rs_pins[pin] = {
            'unus_pin': url_p,
            'receipt': ''
        }

    charges = ''
    charge_status_to_display = {'S': ('#2DB951', 'Success'),
                                'E': ('red', 'Error'),
                                'R': ('#418661', 'Refund'),
                                'V': ('#D5B400', 'Void'),
                                '': ('#A4A0A0', 'No status')}
    for tc in TransactionCharge.objects.filter(transaction=transaction):
        charges += '<a style="background-color: %s; border-color: white;" class="btn btn-success btn-xs" target="_blank" href="%s">%s (%s)</a>' %\
                   (charge_status_to_display[tc.charge.status][0], tc.charge.get_full_url(), tc.charge.id,
                    charge_status_to_display[tc.charge.status][1])
    if transaction.retry_interval:
        eta_update = transaction.retry_interval - (datetime.datetime.now().replace(tzinfo=None) - transaction.ended.replace(tzinfo=None)).total_seconds()
    else:
        eta_update = ''
    for step in steps:
        if step.adv_status and 'receipt' in step.adv_status:
            if step.adv_status.find('Pin ') >= 0:
                pn = step.adv_status[step.adv_status.find('Pin ')+4:step.adv_status.rfind(' extracted')]
                if pn in rs_pins:
                    rs_pins[pn]['receipt'] = step.adv_status[step.adv_status.rfind('https://www.dollarphonepinless.com/ppm_orders/'):step.adv_status.rfind('">r')]

        step_obj = {
                'operation': step.operation,
                'action': step.action,
                'status': step.status,
                'status_str': step.get_status_display(),
                'adv_status': step.adv_status,
                'created': step.created.astimezone(timezone('US/Eastern')).strftime("%m/%d/%y %I:%M:%S%p"),
        }
        step_list.append(step_obj)

    price = ''
    plan_type = ''
    trigger = transaction.trigger
    if transaction.autorefill:
        if transaction.autorefill.plan:
            price = str(transaction.autorefill.plan.get_plansellingprice(transaction.company, transaction.customer.selling_price_level))
            plan_type = transaction.autorefill.plan.plan_type
        trigger = transaction.autorefill.trigger
    data = {
        'steps': step_list,
        'transaction': {
            'triggered_by': transaction.triggered_by,
            'user': transaction.user.id,
            'company': transaction.company.id,
            'customer': transaction.customer_str,
            'payment_type': transaction.charge_type_name,
            'payment_getaway': transaction.charge_getaway_name,
            'phone_number': transaction.phone_number_str,
            'plan': transaction.plan_str,
            'plan_type': plan_type,
            'refill_type': transaction.refill_type_str,
            'pin': rs_pins,
            'state': transaction.state,
            'state_str': transaction.get_state_display(),
            'status': transaction.status,
            'status_str': transaction.get_status_display(),
            'paid': transaction.paid,
            'completed': transaction.completed,
            'adv_status': transaction.adv_status,
            'current_step': transaction.current_step,
            'autorefill_trigger': trigger,
            'profit': str(transaction.profit),
            'started': transaction.started.astimezone(timezone('US/Eastern')).strftime("%m/%d/%y %H:%M:%S"),
            'ended': transaction.ended.astimezone(timezone('US/Eastern')).strftime("%m/%d/%y %H:%M:%S")
            if transaction.ended else '',
            'charge': charges,
            'price': price,
            'eta_update': eta_update if eta_update > 0 else 0

        },
    }
    return render_to_json_response(data)


def ajax_check_customer_cash(request, customer_id):
    customer = Customer.objects.get(id=customer_id)

    return render_to_json_response({
        'result': customer.charge_getaway == Customer.CASH if customer else None,
        'gateway': customer.charge_getaway
    })


def ajax_mark_transaction(request, pk):
    button = request.GET.get('button')
    transaction = Transaction.objects.get(id=int(pk))
    operation = ''
    adv_status = ''
    if button == 'paid':
        operation = 'Mark paid'
        adv_status = 'User %s marked transaction as paid.' % request.user
    if button == 'refund':
        operation = 'Mark refund'
        adv_status = 'User %s marked transaction as refund.' % request.user
    elif button == 'closed':
        operation = 'Closed'
        adv_status = 'User %s closed transaction.' % request.user
    elif button == 'restarted':
        operation = 'Restarted'
        adv_status = 'User %s restarted transaction.' % request.user
    elif button == 'completed':
        operation = 'Mark resolved'
        adv_status = 'User %s marked transaction as resolved.' % request.user
    elif button == 'completed-with-pin':
        pin = request.GET.get('pin')
        transaction.pin = pin
        operation = 'Mark completed with pin'
        adv_status = 'User %s marked transaction as completed with pin %s.' % (request.user, pin)
    elif button == 'enter_pin_and_update':
        pin = request.GET.get('pin')
        transaction.autorefill.set_renewal_date_to_next(today=transaction.autorefill.renewal_date)
        operation = 'Enter pin and update the next schedule refill date'
        adv_status = 'User %s changed pin from %s to %s.' % (
            request.user,
            transaction.pin,
            pin
        )
        transaction.pin = pin
    elif button == 'prerefill_restart':
        operation = 'Restarted charge and get pin'
        adv_status = 'User %s restarted transaction for charge and get pin steps.' % request.user
    elif button == 'restart-trns-and-charge':
        operation = 'Restart transaction and charge'
        adv_status = 'User %s restarted transaction and retry charge' % request.user
    elif button == 'retry-charge':
        operation = 'Retry charge'
        adv_status = 'User %s retried charge' % request.user
    elif button == 'retry-send-msg-pin':
        operation = 'Retry send message with pins'
        adv_status = 'User %s clicked to button "Retry send message with pins"' % request.user
    elif button == 'send-msg-pin':
        operation = 'send message with pins'
        adv_status = 'User %s clicked to button "Send message with pins"' % request.user
    transaction.add_transaction_step(operation,
                                     'button',
                                     SUCCESS,
                                     adv_status)
    if button == 'prerefill_restart':
        transaction.retry_count = 1
        transaction.state = Transaction.RETRY
        transaction.adv_status = 'prerefill restarted by user %s' % request.user
        transaction.save()
        queue_prerefill.delay(transaction.id)
        return HttpResponse()
    # restart transaction
    if button == 'restart-trns-and-charge':

        transaction.retry_count = 1
        transaction.state = Transaction.RETRY
        charge = transaction\
            .get_last_used_charge\
            .retry(request.user)
        transaction.was_retried_on_step = False
        queue_refill.delay(transaction.id)
        transaction.adv_status = 'Transaction and charge <a href="%s">%s</a> restarted by user %s'\
                                 % (charge.get_full_url(),
                                    charge.id,
                                    request.user)
        transaction.save()
        return HttpResponse()

    if button == 'send-msg-pin' or button == 'retry-send-msg-pin':
        from send_notifications import send_pins_to_customer
        send_pins_to_customer(transaction=transaction,
                              user=request.user)
        return HttpResponse()

    if button == 'retry-charge':
        charge = transaction\
            .get_last_used_charge\
            .retry(request.user)
        transaction.adv_status = 'Charge <a href="%s">%s</a> retried by user %s' \
                                 % (charge.get_full_url(),
                                    charge.id,
                                    request.user)
        return HttpResponse()

    if button == 'restarted':
        transaction.retry_count = 1
        transaction.bought_pins_retry_count_err_token = 0
        transaction.bought_pins_retry_count = 0
        transaction.state = Transaction.RETRY
        transaction.adv_status = 'Transaction restarted by user %s' % request.user
        transaction.was_retried_on_step = False
        transaction.save()
        queue_refill.delay(transaction.id)
        return HttpResponse()
    # pay transaction
    if button == 'paid':
        transaction.paid = True
        transaction.save()
        if transaction.company.use_sellercloud and transaction.sellercloud_order_id and \
            not (transaction.autorefill.refill_type == AutoRefill.REFILL_GP and
                 transaction.autorefill.trigger == AutoRefill.TRIGGER_MN):
            try:
                transaction.send_payment_to_sellercloud_order()
            except Exception, e:
                transaction.add_transaction_step('notification',
                                                 'SellerCloud',
                                                 ERROR,
                                                 u'%s' % e)
        return HttpResponse()
    if button == 'refund':
        transaction.paid = False
        transaction.save()
        if transaction.company.use_sellercloud and transaction.sellercloud_order_id and \
            not (transaction.autorefill.refill_type == AutoRefill.REFILL_GP and
                 transaction.autorefill.trigger == AutoRefill.TRIGGER_MN):
            try:
                transaction.send_payment_to_sellercloud_order()
            except Exception, e:
                transaction.add_transaction_step('notification',
                                                 'SellerCloud',
                                                 ERROR,
                                                 u'%s' % e)
        return HttpResponse()
    # close transaction
    transaction.state = Transaction.COMPLETED
    transaction.save()
    if button == 'closed':
        return HttpResponse()
    # complete transaction
    transaction.completed = 'R'
    transaction.status = Transaction.SUCCESS
    transaction.save()
    if transaction.company.use_asana:
        try:
            transaction.send_asana()
        except Exception, e:
            transaction.add_transaction_step('notification',
                                             'Asana',
                                             ERROR,
                                             u'%s' % e)
    if transaction.company.use_sellercloud:
        try:
            transaction.send_tratsaction_to_sellercloud()
            transaction.send_note_to_sellercloud_order()
            transaction.send_payment_to_sellercloud_order()
        except Exception, e:
            transaction.add_transaction_step('notification',
                                             'SellerCloud',
                                             ERROR,
                                             u'%s' % e)
    return HttpResponse()


def ajax_apply_send_pin_prerefill(request):
    CompanyProfile.objects.get(id=request.user.profile.company_id)\
        .set_customers_send_pin_prerefill(state=request.GET.get('send_pin_prerefill'))

    return HttpResponse()


def ajax_set_default_notification(request):
    CompanyProfile.objects.get(id=request.user.profile.company_id).set_default_notification()
    return HttpResponse()


def ajax_add_phone_number(request):
    data = 'Number added to customer'
    try:
        customer_id = request.GET.get('customer')
        customer = Customer.objects.get(id=customer_id)
        number = re.sub('\D', '', request.GET.get('number'))
        if number.isdigit() and len(number) == 10:
            new_phone = PhoneNumber(company=customer.company, number=number, customer=customer)
            new_phone.save()
        else:
            data = 'Number not added to customer, please enter 10 digit phone number'
    except Exception, e:
        logger.error('Add customer from REFILL form %s' % e)
        data = 'Number not added to customer'
    finally:
        return render_to_json_response(data)


def ajax_phone_numbers(request):
    data = []
    try:
        id = request.GET.get('id')
        if id:
            customer = Customer.objects.get(id=id)
            for phone in PhoneNumber.objects.filter(customer=customer):
                num = phone.number
                data.append({'text': num, 'value': num})
        return render_to_json_response(data)
    except Exception as e:
        return render_to_json_response(data)


def ajax_carrier_plans(request):
    id = request.GET.get('id')
    data = []
    if id:
        # if cache.get(key=id):
        #     return render_to_json_response(cache.get(key=id))
        for plan in Plan.objects.filter(carrier=id, enabled=True).order_by('plan_cost'):
                available = 'Not available'
                if plan.available:
                    available = 'available'
                obj = {
                    'pk': plan.id,
                    'id': plan.plan_id,
                    'name': plan.plan_name,
                    'cost': float(plan.plan_cost),
                    'type': plan.get_plan_type_display(),
                    'available': available,
                }
                data.append(obj)
    return render_to_json_response(data)


def ajax_carriers(request):
    # if cache.get(key='carriers'):
    #     return render_to_json_response(cache.get(key='carriers'))
    carriers = Carrier.objects.all().order_by('name')
    carrier_list = []
    for carrier in carriers:
        obj = {
            'pk': carrier.id,
            'name': carrier.name,
            'name_slug': slugify(carrier.name),
            'admin_site': carrier.admin_site
        }
        carrier_list.append(obj)
    # cache.set(key='carriers', value=carrier_list, timeout=6000)
    return render_to_json_response(carrier_list)


def ajax_carrier(request):
    carid = int(request.GET.get('carid'))
    carrier = Carrier.objects.get(id=carid)
    rs = {
        'name': carrier.name,
        'name_slug': slugify(carrier.name),
        'admin_site': carrier.admin_site,
        'default_time': carrier.default_time
    }
    return render_to_json_response(rs)


def ajax_unused_pins_plan_list(request):
    result = []
    for plan in UnusedPin.objects.filter(company=request.user.profile.company).values('plan__id').distinct():
        result.append({'id': plan['plan__id'], 'name': Plan.objects.get(id=long(plan['plan__id'])).plan_id})
    return render_to_json_response(result)


def ajax_transaction_summary(request):
    transaction_list = []
    today = django_tz.now()
    for day in range(1, today.day + 1):
        this_date = django_tz.make_aware((datetime.datetime.combine(today, datetime.time.min) - datetime.timedelta(days=(today.day-day))), timezone=timezone('US/Eastern'))
        next_date = django_tz.make_aware((datetime.datetime.combine(today, datetime.time.max) - datetime.timedelta(days=(today.day-day))), timezone=timezone('US/Eastern'))
        if request.user.is_superuser:
            obj = {
                'date': '{d.month}-{d.day}-{d.year}'.format(d=this_date),
                'Success': Transaction.objects.filter(started__range=[this_date, next_date], status='S').count(),
                'Failed': Transaction.objects.filter(started__range=[this_date, next_date], status='E').count(),
            }
        else:
            obj = {
                'date': '{d.month}-{d.day}-{d.year}'.format(d=this_date),
                'Success': Transaction.objects.filter(started__range=[this_date, next_date], status='S', company=request.user.profile.company).count(),
                'Failed': Transaction.objects.filter(started__range=[this_date, next_date], status='E', company=request.user.profile.company).count(),
            }
        transaction_list.append(obj)
    return render_to_json_response(transaction_list)


def ajax_pin_usage(request):
    today = datetime.date.today()
    month_days = calendar.monthrange(today.year,today.month)[1]
    start_month = datetime.date.today() - datetime.timedelta(days=(today.day-1))
    end_month = datetime.date.today() + datetime.timedelta(days=(month_days-today.day))
    if request.user.is_superuser:
        refills_done = AutoRefill.objects.filter(enabled=True, trigger=AutoRefill.TRIGGER_SC, last_renewal_date__range=[start_month, today]).count()
        refills_pending = AutoRefill.objects.filter(enabled=True, trigger=AutoRefill.TRIGGER_SC, renewal_date__range=[today, end_month]).count()
    else:
        refills_done = AutoRefill.objects.filter(company=request.user.profile.company, trigger=AutoRefill.TRIGGER_SC, enabled=True, last_renewal_date__range=[start_month, today]).count()
        refills_pending = AutoRefill.objects.filter(company=request.user.profile.company, trigger=AutoRefill.TRIGGER_SC, enabled=True, renewal_date__range=[today, end_month]).count()
    pin_usage = [
        {'label': "Used", 'value': refills_done},
        {'label': "Still Needed", 'value': refills_pending},
    ]
    if refills_pending == 0 and refills_done == 0:
        pin_usage = [
            {'label': 'None', 'value': 1}
        ]
    return render_to_json_response(pin_usage)


def ajax_customers(request):
    customers = Customer.objects.filter(company=request.user.profile.company, enabled=True).count()
    if request.user.is_superuser:
        customers = CompanyProfile.objects.filter(superuser_profile=False).count()
    return render_to_json_response({'result': customers})


def ajax_customer_getaway_and_last_of_cc(request):
    if request.GET['id']:
        customer = Customer.objects.get(id=request.GET['id'])
        if customer.charge_type == Customer.CREDITCARD:
            return render_to_json_response({'valid': True,
                                            'getaway': customer.get_charge_getaway_display(),
                                            'CC': customer.creditcard[-4:]})
        else:
            return render_to_json_response({'valid': True,
                                            'getaway': customer.get_charge_getaway_display()})
    return render_to_json_response({'valid': False})


def ajax_total_transactions(request):
    tot_trans = Transaction.objects.filter(company=request.user.profile.company, state='C').count()
    if request.user.is_superuser:
        tot_trans = Transaction.objects.filter(state='C').count()
    return render_to_json_response({'result': tot_trans})


def ajax_transaction_successrate(request):
    tot_trans = Transaction.objects.filter(company=request.user.profile.company, state=Transaction.COMPLETED).count()
    suc_trans = Transaction.objects.filter(company=request.user.profile.company, state=Transaction.COMPLETED, status=Transaction.SUCCESS).count()
    if request.user.is_superuser:
        tot_trans = Transaction.objects.filter(state=Transaction.COMPLETED).count()
        suc_trans = Transaction.objects.filter(state=Transaction.COMPLETED, status=Transaction.SUCCESS).count()
    if tot_trans > 0:
        success_rate = (float(suc_trans)/tot_trans)*100
    else:
        success_rate = 100
    return render_to_json_response({'result': int(success_rate)})


def ajax_transaction_profits(request):
    transactions = Transaction.objects.filter(company=request.user.profile.company, state='C', status='S')
    profits = 0
    for transaction in transactions:
        if transaction.profit:
            profits = transaction.profit + profits
    return render_to_json_response({'result': "{0:.2f}".format(profits)})


def ajax_need_pins_report(request):
    report = {}
    today = datetime.datetime.now(timezone('US/Eastern')).date()
    pin_for_day = {}
    pin_day_count = 0
    unused_pins = list(UnusedPin.objects.filter(company=request.user.profile.company, used=False))
    for i in range(0, 14):
        day_report = {}
        for autorefill in AutoRefill.objects.filter(company=request.user.profile.company,
                                                    enabled=True, trigger=AutoRefill.TRIGGER_SC,
                                                    renewal_date=today + datetime.timedelta(days=i)):
            if autorefill_has_pin(autorefill):
                continue
            pin = has_unused_pin(unused_pins, autorefill.plan)
            if pin:
                unused_pins.remove(pin)
                continue
            if autorefill.plan.plan_id in pin_for_day:
                pin_for_day[autorefill.plan.plan_id] += 1
            else:
                pin_for_day[autorefill.plan.plan_id] = 1
            pin_day_count += 1
        day_report['pin_count'] = pin_day_count
        day = []
        for key in pin_for_day.keys():
            day.append('<dt>%s:</dt><dd>%s</dd>' % (key, pin_for_day[key]))
        day_text = '<br/>'.join(day)
        day_report['pins'] = '<dl class="dl-horizontal">%s</dl>' % day_text
        report[i] = day_report
    return render_to_json_response({'result': report})


def ajax_dismiss_urgent(request):
    try:
        request.user.profile.show_urgent = False
        request.user.profile.save()
        return HttpResponse(json.dumps({'valid': True, 'message': 'Done!'}), content_type='application/json')
    except Exception, msg:
        return HttpResponse(json.dumps({'valid': False, 'message': 'Something went wrong!'}), content_type='application/json')


def ajax_verify_carrier(request):
    phone_number = request.GET.get('phone_number')
    transaction_id = request.GET.get('transaction_id')
    if not request.user.profile.company.verify_carrier:
        return render_to_json_response({'valid': False})
    if transaction_id and Transaction.objects.get(id=transaction_id):
        transaction = Transaction.objects.get(id=transaction_id)
        if transaction.company:
            company = transaction.company
        else:
            company = request.user.profile.company
    else:
        company = request.user.profile.company
    result = verify_carrier.get_mdn_number(phone_number, company)
    carrier = ''
    plan = ''
    renewal_date = ''
    message = ''
    url = ''
    if result['carrier']:
        carrier = result["carrier"].id
    if result['plan']:
        plan = result['plan'].id
    if result['renewal_date']:
        renewal_date = result['renewal_date'].strftime("%m/%d/%Y")
    if not result['valid_for_schedule']:
        message = result['error']
    if 'url' in result:
        url = result['url']
    return render_to_json_response({'valid': result['valid'],
                                    'carrier': carrier,
                                    'plan': plan,
                                    'renewal_date': renewal_date,
                                    'schedule': result['schedule'],
                                    'mdn_status': result['mdn_status'] + message,
                                    'message': message,
                                    'url': url})


def ajax_verify_scheduled_refills(request):
    company = request.user.profile.company
    if company.verify_carrier:
        if cache.get(key='verify_scheduled_refills_%s' % company.id)\
                and cache.get(key='verify_scheduled_refills_%s' % company.id)['run']:
            return render_to_json_response({'message': "Verify scheduled refills is already in process."})
        else:
            verify_scheduled_refills.delay(company)
            cache.add(key='verify_scheduled_refills_%s' % company.id, value={'run': True}, timeout=21600)
        return render_to_json_response({'message': "Scheduled refills will be check with verify carrier and updates. "
                            "Result will be sent on your company's email."})
    else:
        return render_to_json_response({'message': "This option is not enabled for you. Please, contact support to enable it for you."})


def ajax_get_pin_status(request):
    if not request.user.profile.company.verify_pin:
        return render_to_json_response({
                                       'message':
                                           'This option is not enabled for you.'
                                           ' Please, contact support to enable'
                                           ' it for you.'})
    else:
        if request.GET.get('type') == 'SINGLE':
            result = verify_carrier.get_status_of_pins(
                request.user.profile.company,
                [request.GET.get('pin')])
            if result['failed_login'] or result['result'][0]['invalid_login']:
                return render_to_json_response({'message':
                                                    'Failed login.'
                                                    ' Invalid Username or Password!'})
            else:
                return render_to_json_response({'message': '',
                                                'result': result['result'][0]})
        elif request.GET.get('type') == 'LIST':
            carrier = Carrier.objects.filter(name__icontains='RED POCKET')
            pin_list = UnusedPin.objects.filter(
                company=request.user.profile.company,
                plan__carrier=carrier)
            if pin_list:
                if request.user.profile.updates_email \
                        or request.user.profile.company.email_id:
                    notification_about_status_of_pin.delay(
                        pin_list, request.user.profile)
                    return render_to_json_response({'message':
                                                        "In Processing!\n"
                                                        "The result will"
                                                        " be sent on your e-mail or"
                                                        " your company's e-mail!"})
                else:
                    return render_to_json_response({'message':
                                                        "Result cann't will"
                                                        " send, because you "
                                                        "and your company "
                                                        "hasn't email. "
                                                        "Please to fill your"
                                                        " email or email of"
                                                        " your company and "
                                                        "try again."})
            else:
                return render_to_json_response({'message':
                                                    "You haven't stacked"
                                                    " pin of RedPocket!"})
        else:
            return render_to_json_response({'message': "Not active!"})


def has_unused_pin(unused_pins, plan):
    for unused_pin in unused_pins:
        if unused_pin.plan == plan:
            return unused_pin
    return False


def autorefill_has_pin(autorefill):
    today = datetime.datetime.now(timezone('US/Eastern')).date()
    start_transaction_date = datetime.datetime.combine(today - datetime.timedelta(days=1), datetime.time(hour=11, minute=59))
    start_charge_date = datetime.datetime.combine(today - datetime.timedelta(days=autorefill.company.authorize_precharge_days), datetime.time(hour=04, minute=00))
    for transaction in Transaction.objects.filter(autorefill=autorefill, started__gt=start_transaction_date):
        if transaction.pin:
            return True
    for charge in Charge.objects.filter(autorefill=autorefill, created__gt=start_charge_date):
        if charge.pin:
            return True
    return False


def twilio_request(request):
    '''
    :param request:
    :return: <Response>
                <Record action="http://127.0.0.1:8000/twilio-response/"
                    finishOnKey="#" maxLength="20" method="GET" timeout="20"/>
            </Response>
    '''

    response = etree.Element('Response')
    record = etree.Element('Record', timeout="20", maxLength="20", finishOnKey="#", action=request.build_absolute_uri(reverse('twilio_response')), method="GET")
    response.append(record)
    return HttpResponse(etree.tostring(response, encoding="utf-8", xml_declaration=True), content_type='application/xml')


def twilio_response(request):
    cache.set(key=request.GET['CallSid'], value=request.GET['RecordingUrl'], timeout=600)
    response = etree.Element('Response')
    return HttpResponse(etree.tostring(response, encoding="utf-8", xml_declaration=True), mimetype='application/xml')


def pparsb_response(request, pk):
    cache.set(key=pk, value=request.GET.dict(), timeout=600)
    logger.info('%s' % request.GET.dict())
    return HttpResponse("Done")


def render_to_json_response(context, **response_kwargs):
    data = json.dumps(context)
    response_kwargs['content_type'] = 'application/json'
    return HttpResponse(data, **response_kwargs)


class ImportLogView(ListView):
    model = ImportLog

    def get_queryset(self):
        return ImportLog.objects.order_by('-created').filter(company=self.request.user.profile.company)


def import_customers_from_usaepay(request):
    usaepay_account = request.GET.get('account')
    if not usaepay_account:
        usaepay_account = '1'
    company = request.user.profile.company
    if not company.usaepay_username or not company.usaepay_password:
        message = 'no USAePay username/password for API requests'
        messages.add_message(request, messages.ERROR, '%s' % message)
        return HttpResponseRedirect(reverse('customer_list'))
    if not company.usaepay_source_key or not company.usaepay_pin:
        message = 'no USAePay tokens for API requests'
        messages.add_message(request, messages.ERROR, '%s' % message)
        return HttpResponseRedirect(reverse('customer_list'))
    queue_import_customers_from_usaepay.delay(company, request.user, usaepay_account)
    messages.add_message(request, messages.SUCCESS, 'Your import starting now')
    return HttpResponseRedirect(reverse('customer_list'))


def import_customers_from_redfin(request):
    company = request.user.profile.company
    if cache.get(key='RedFin') and cache.get(key='RedFin')['company'] == company.id:
        messages.add_message(request, messages.SUCCESS, 'Process is already started')
    else:
        if not company.use_redfin:
            message = 'no RedFinNetwork credentials'
            messages.add_message(request, messages.ERROR, '%s' % message)
        else:
            cache.add(key='RedFin', value={'run': True, 'company': company.id}, timeout=1800)
            queue_import_customers_from_redfin.delay(company, request.user)
            messages.add_message(request, messages.SUCCESS, 'Your import starting now')
    return HttpResponseRedirect(reverse('customer_list'))


def restart_creating_schedule_for_customers_from_redfin(request):
    userprofile = request.user.profile
    restart_auto_creating_schedules_refill.delay(userprofile)
    messages.add_message(request, messages.SUCCESS, 'Auto creating schedule starting now')
    return HttpResponseRedirect(reverse('customer_list'))


class PhoneNumbersImport(View):
    template_name = 'core/phone_number_import.html'
    form_class = forms.PhoneNumberImportForm

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)
        if form.is_valid():
            workbook = xlrd.open_workbook(file_contents=form.cleaned_data['file'].read())
            worksheet = workbook.sheet_by_index(0)
            # Change this depending on how many header rows are present
            # Set to 0 if you want to include the header data.
            offset = 0

            rows = []
            for i, row in enumerate(range(worksheet.nrows)):
                if i <= offset:  # (Optionally) skip headers
                    continue
                r = []
                for j, col in enumerate(range(worksheet.ncols)):
                    r.append(worksheet.cell_value(i, j))
                rows.append(r)
            queue_import_phone_numbers.delay(request.user.profile.company, rows)
            messages.add_message(self.request, messages.SUCCESS,
                                 'Import phone numbers job has been added to queue')
            return HttpResponseRedirect(reverse('customer_list'))
        else:
            return render(request, self.template_name, {'form': form, 'confirm': False})


def close_updates(request):
    company = request.user.profile.company
    company.show_updates = False
    company.save()
    return HttpResponse()


def change_user(request):
    user_profile = request.user.profile
    if request.GET['news_email'] == '':
        user_profile.updates_email = request.GET['news_email']
        user_profile.save()
        return HttpResponse(json.dumps({'valid': True}), content_type='application/json')
    try:
        emails = [email.strip(' ') for email in request.GET['news_email'].split(',') if email != '']
        email_on_save = ''
        for email in emails:
            validate_email(email)
            email_on_save += email + ','
        user_profile.updates_email = email_on_save
        user_profile.save()
        return HttpResponse(json.dumps({'valid': True}), content_type='application/json')
    except ValidationError:
        return HttpResponse(json.dumps({'valid': False}), content_type='application/json')


def ajax_check_for_similar_scheduled_refill(request):
    if request.user.profile.company.block_duplicate_schedule and\
            AutoRefill.objects.exclude(id=request.GET['id']).filter(trigger='SC', enabled=True,
                                                                    phone_number=request.GET['phone'],
                                                                    company=request.user.profile.company):
        message = ''
        for refill in AutoRefill.objects.exclude(id=request.GET['id']).filter(trigger='SC', enabled=True,
                                                                              phone_number=request.GET['phone'],
                                                                              company=request.user.profile.company):
            message += '<a target=\"_blank\" style=\"color: blue;\" href=\"%s\">' % reverse('autorefill_update', args=[refill.id]) + str(refill.id) + '</a>, '
        return HttpResponse(json.dumps({'similar': True, 'message': message}), content_type='application/json')
    return HttpResponse(json.dumps({'similar': False}), content_type='application/json')


def ajax_check_duplicate_number(request):
    pns = []
    numbers = request.GET['phone_numbers'].split(',')
    company = request.user.profile.company
    for number in numbers:
        if request.GET['id']:
            phone_numbers = PhoneNumber.objects.exclude(customer=None).exclude(customer_id=request.GET['id']).filter(number=number, company=company)
        if phone_numbers.exists():
            pns.append(phone_numbers)
    if len(pns) > 0 and company.block_duplicate_phone_number:
        msg = ''
        for phone_numbers in pns:
            for phone_number in phone_numbers:
                msg += "Number '%s' already exist at <a style=\"color:blue;\" href=\"%s\">%s</a></br>" % (phone_number.number,
                                                                                                          reverse('customer_update',
                                                                                                          args=[phone_number.customer.id]),
                                                                                                          phone_number.customer)
        return HttpResponse(json.dumps({'error': True, 'message': msg}), content_type='application/json')

    if request.GET['id']:
        phones = PhoneNumber.objects.filter(customer_id=request.GET['id'])
        deleted_phones = map(str, phones.exclude(number__in=numbers).values_list('number', flat=True))
        if deleted_phones:
            prerefiled_days = company.authorize_precharge_days or 0  # 0 if company.authorize_precharge_days is Blank
            prerefiled = AutoRefill.objects.exclude(enabled=False).\
                filter(phone_number__in=deleted_phones, renewal_date__gt=datetime.datetime.now()
                                                                         - datetime.timedelta(days=prerefiled_days),
                       customer_id=request.GET['id'])
            if prerefiled:
                msg = ''
                for phone in prerefiled:
                    msg += "Cannot delete number %s because it can has precharge before top up</br>"\
                           % phone.phone_number
                return HttpResponse(json.dumps({'error': True, 'message': msg}), content_type='application/json')

    return HttpResponse(json.dumps({'error': False}), content_type='application/json')


def ajax_transaction_duplicates(request):
    phone_number = request.GET.get('pn')
    if Transaction.objects.filter(Q(started__gte=datetime.datetime.now() - datetime.timedelta(hours=12)) |
                                  Q(started__gte=datetime.datetime.now() - datetime.timedelta(hours=1), completed='R'),
                                  phone_number_str__icontains=phone_number, company=request.user.profile.company):
        return render_to_json_response({'duplicated': True})
    return render_to_json_response({'duplicated': False})


def ajax_move_number_to_another_customer(request):
    try:
        if Customer.objects.get(id=long(request.GET['current_customer_id'])).company.id !=\
                request.user.profile.company.id or \
                        Customer.objects.get(id=long(request.GET['customer_id'])).company.id !=\
                        request.user.profile.company.id:
            raise Exception('Customer is not from your company.')
        if request.GET['number'] and request.GET['sms_gateway'] and request.GET['sms_email'] and\
                request.GET['number'].isdigit() and len(request.GET['number']) == 10 and\
                SmsEmailGateway.objects.filter(id=request.GET['sms_gateway']).exists():
            use_for_sms_email = True
            if request.GET['sms_email'] == 'false':
                use_for_sms_email = False
            number = PhoneNumber(number=request.GET['number'], title=request.GET['title'],
                                 sms_gateway_id=int(request.GET['sms_gateway']), use_for_sms_email=use_for_sms_email,
                                 company=request.user.profile.company)
            if not Customer.objects.filter(id=long(request.GET['customer_id'])).exists():
                raise Exception('Customer you are trying to move number to was deleted.')
            if PhoneNumber.objects.filter(number=request.GET['number'], title=request.GET['title'],
                                          sms_gateway__id=int(request.GET['sms_gateway']),
                                          use_for_sms_email=use_for_sms_email, company=request.user.profile.company,
                                          customer__id=long(request.GET['current_customer_id'])).exists():
                number = PhoneNumber.objects.get(number=request.GET['number'], title=request.GET['title'],
                                                 sms_gateway__id=int(request.GET['sms_gateway']),
                                                 use_for_sms_email=use_for_sms_email,
                                                 company=request.user.profile.company,
                                                 customer__id=long(request.GET['current_customer_id']))
                for scheduled_refill in AutoRefill.objects.filter(phone_number=number.number, customer=number.customer,
                                                                  trigger=AutoRefill.TRIGGER_SC):
                    scheduled_refill.customer = Customer.objects.get(id=long(request.GET['customer_id']))
                    scheduled_refill.save()
            customer_to_delete = number.customer
            number.customer = Customer.objects.get(id=long(request.GET['customer_id']))
            number.save()
            if not PhoneNumber.objects.filter(customer__id=long(request.GET['current_customer_id'])).exists():
                customer_to_delete.delete()
            return render_to_json_response({'valid': True})
        else:
            raise Exception('Wrong number data')
    except Exception, msg:
        return render_to_json_response({'valid': False, 'message': str(msg)})


def ajax_add_pin_to_unused(request, transaction_id):
    transaction = Transaction.objects.get(id=transaction_id)
    pin = request.GET.get('pin')
    if transaction.autorefill:
        plan = transaction.autorefill.plan
    else:
        plan = Plan.objects.filter(plan_id__icontains=transaction.plan_str).first()
    if not plan.available and plan.universal_plan:
            plan = plan.universal_plan

    unused_pin, created = UnusedPin.objects.get_or_create(
        company=transaction.company,
        plan=plan,
        pin=pin,
        defaults={'user': transaction.user,
                  'used': False,
                  'notes': 'Pin bought from transaction %s' % transaction.get_full_url()})
    if created:
        transaction.add_transaction_step('button', 'clicked', SUCCESS,
                                         'User "%s" add pin %s (%s, %s) to unused <a href="%s">%s</a>' %
                                         (request.user, pin, plan.carrier.name, plan.plan_name, unused_pin.get_full_url(),
                                          unused_pin))

    return HttpResponse()


def ajax_mark_pin_field(request):
    pin_id = int(request.GET.get('pin_id'))
    if pin_id:
        button = request.GET.get('button')
        note = request.GET.get('note')
        pin_field = PinField.objects.get(id=pin_id)
        if note:
            pin_field.note = note
        if button == 'used':
            pin_field.used = True
        elif button == 'unused':
            pin_field.used = False
        pin_field.save()
    return HttpResponse()


def ajax_mark_pinreport(request):
    pinreport_id = int(request.GET.get('pinreport_id'))
    if pinreport_id:
        button = request.GET.get('button')
        note = request.GET.get('note')
        for pin_field in PinField.objects.filter(pin_report__id=pinreport_id):
            if note:
                pin_field.note = note
            if button == 'used':
                pin_field.used = True
            elif button == 'unused':
                pin_field.used = False
            pin_field.save()
    return HttpResponse()


def ajax_mark_unusedpin(request):
    unusedpin_id = int(request.GET.get('pin_id'))
    if unusedpin_id:
        button = request.GET.get('button')
        note = request.GET.get('note')
        unusedpin = UnusedPin.objects.get(id=unusedpin_id)
        if note:
            unusedpin.notes = note
        if button == 'used':
            unusedpin.used = True
        elif button == 'unused':
            unusedpin.used = False
        unusedpin.save()
    return HttpResponse()


def get_workers_status(request):
    d = {'ERROR': 'Ok.'}
    try:
        from celery.task.control import ping
        d['ping'] = ping()
        if d['ping']:
            d['ok'] = True
            return render_to_json_response(d)
        else:
            d['ok'] = False
            d['ERROR'] = 'Celery is not running.'
            return render_to_json_response(d)
    except ImportError as e:
        d['ok'] = False
        d['ERROR'] = str(e)
        return render_to_json_response(d)

    # return render_to_json_response(d)
    # ERROR_KEY = "ERROR"
    # try:
    #     from celery.task.control import inspect
    #     insp = inspect()
    #     d = insp.stats()
    #     if not d:
    #         d = {ERROR_KEY: 'No running Celery workers were found.'}
    #         d['ok'] = False
    #         return render_to_json_response(d)
    # except IOError as e:
    #     from errno import errorcode
    #     msg = "Error connecting to the backend: " + str(e)
    #     if len(e.args) > 0 and errorcode.get(e.args[0]) == 'ECONNREFUSED':
    #         msg += ' Check that the RabbitMQ server is running.'
    #     d = {ERROR_KEY: msg}
    #     d['ok'] = False
    #     return render_to_json_response(d)
    # except ImportError as e:
    #     d = {ERROR_KEY: str(e)}
    #     d['ok'] = False
    #     return render_to_json_response(d)
    # d['ok'] = True
    # return render_to_json_response(d)
