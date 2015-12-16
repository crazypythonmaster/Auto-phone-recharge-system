import re
import operator
import json

from pytz import timezone

from django.core.urlresolvers import reverse
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.db.models import Q

from ppars.apps.core.models import Customer, AutoRefill, PhoneNumber, Transaction, UnusedPin
from ppars.apps.charge.models import Charge


def search(request):
    if 'searchfor' in request.GET and request.GET['searchfor'] and '__' not in request.GET['searchfor']:
        search_string = re.sub('\D', '', request.GET['searchfor'])
        is_number = False
        is_phone_number = False
        if len(search_string.split(' ')) == 1 and search_string.isdigit():
            is_number = True
            if len(search_string) == 10:
                is_phone_number = True
        return render(request, 'core/search.html', {'searching_for': request.GET['searchfor'], 'is_number': is_number,
                                                    'number': search_string, 'is_phone_number': is_phone_number})
    else:
        return HttpResponseRedirect('/home')


def ajax_search_dropdown(request):
    filters = request.GET['text'].strip().split(' ')
    for i in range(len(filters)):
        if re.compile('\d').search(filters[i]):  # if filter word contains digits it's a phone number
            filters[i] = re.sub('\D', '', filters[i])  # so we remove all additional symbols for right filtering
        else:  # in case it's a name we also should remove all additional symbols
            just_number = False
            filters[i] = re.sub('[^a-zA-Z\,\.\']', '', filters[i])
    numbers = []
    names = []
    for fil in filters:
        if fil.isdigit():
            numbers.append(fil)
        else:
            names.append(fil)
    customers = []
    filtered_customers = []
    if numbers:
        for phone in PhoneNumber.objects.filter(reduce(operator.and_, (Q(number__icontains=number) for number in numbers)),
                                                company=request.user.profile.company).exclude(customer=None):
            customers.append((phone.customer, phone.number))
    if not customers:
        if names:
            for customer in Customer.objects.filter(reduce(operator.and_, (Q(first_name__icontains=name) |
                                                                           Q(middle_name__icontains=name) |
                                                                           Q(last_name__icontains=name)
                                                                           for name in names)),
                                                    company=request.user.profile.company):
                for phone in PhoneNumber.objects.filter(customer=customer):
                    filtered_customers.append((customer, phone.number))

    else:
        for customer in customers:
            append = True
            for name in names:
                if not name in customer[0].__unicode__():
                    append = False
                    break
            if append:
                filtered_customers.append((customer[0], customer[1]))
    if len(customers) > 29:
        filtered_customers = filtered_customers[:29]
    return HttpResponse(json.dumps([{'name': customer[0].__unicode__(), 'number': customer[1]}
                                    for customer in filtered_customers]),
                        content_type='application/json')


def ajax_search(request):
    # self explaining
    dropdown = request.GET['sSearch_0']
    company = request.user.profile.company
    # for special cases of search, when input starts with one of those
    delimiters = ('*', '/')
    delimiter = ''
    if request.GET['search_for'][0] in delimiters:
        delimiter = request.GET['search_for'][0]

    # json for DataTable
    ajax_response = {"sEcho": request.GET['sEcho'], "aaData": [], 'iTotalRecords': 0}

    filters = request.GET['search_for'].strip().split(' ')

    names = []
    numbers = []

    for i in range(len(filters)):
        if re.compile('\d').search(filters[i]):  # if filter word contains digits it's a phone number
            filters[i] = re.sub('\D', '', filters[i])  # so we remove all additional symbols for right filtering
            numbers.append(filters[i])
        else:  # in case it's a name we also should remove all additional symbols
            filters[i] = re.sub('[^a-zA-Z\,\.\']', '', filters[i])
            names.append(filters[i])
    for i in range(len(filters)):
        if re.compile('\d').search(filters[i]):  # if one of filter words contains digits it's a phone number
            filters[i] = re.sub('\D', '', filters[i])  # so we remove all additional symbols for right filtering

    # then there is only phone numbers ending with numbers after '/'
    if delimiter == '/':
        # adding phone numbers to search result
        phone_numbers, total_records_plus = search_phone_numbers_filter(numbers, names, company, dropdown, delimiter)
        ajax_response['aaData'] += phone_numbers
        ajax_response['iTotalRecords'] += total_records_plus
    # then there is only charges and customers witch credit card is ending with numbers after '*'
    elif delimiter == '*':
        # adding customers to search result
        customers, total_records_plus = search_customers_filter(numbers, names, company, dropdown, delimiter)
        ajax_response['aaData'] += customers
        ajax_response['iTotalRecords'] += total_records_plus
        # adding charges to search result
        charges, total_records_plus = search_charges_filter(numbers, names, company, dropdown, delimiter)
        ajax_response['aaData'] += charges
        ajax_response['iTotalRecords'] += total_records_plus
    # regular search
    else:
        # adding phone numbers to search result
        phone_numbers, total_records_plus = search_phone_numbers_filter(numbers, names, company, dropdown, delimiter)
        ajax_response['aaData'] += phone_numbers
        ajax_response['iTotalRecords'] += total_records_plus
        # adding customers to search result
        customers, total_records_plus = search_customers_filter(numbers, names, company, dropdown, delimiter)
        ajax_response['aaData'] += customers
        ajax_response['iTotalRecords'] += total_records_plus
        # adding autorefills to search result
        autorefills, total_records_plus = search_autorefills_filter(numbers, names, company, dropdown, delimiter)
        ajax_response['aaData'] += autorefills
        ajax_response['iTotalRecords'] += total_records_plus
        # adding transactions to search result
        transactions, total_records_plus = search_transactions_filter(numbers, names, company, dropdown, delimiter)
        ajax_response['aaData'] += transactions
        ajax_response['iTotalRecords'] += total_records_plus
        # adding charges to search result
        charges, total_records_plus = search_charges_filter(numbers, names, company, dropdown, delimiter)
        ajax_response['aaData'] += charges
        ajax_response['iTotalRecords'] += total_records_plus
        # adding charges to search result
        unused_pins, total_records_plus = search_unused_pins_filter(numbers, names, company, dropdown, delimiter)
        ajax_response['aaData'] += unused_pins
        ajax_response['iTotalRecords'] += total_records_plus
        # adding last 4 of cc to search result
        last_4_of_cc, total_records_plus = search_last4ofcc_filter(numbers, names, company, dropdown, delimiter)
        ajax_response['aaData'] += last_4_of_cc
        ajax_response['iTotalRecords'] += total_records_plus
    ajax_response['iTotalDisplayRecords'] = len(ajax_response['aaData'])
    start = int(request.GET['iDisplayStart'])
    length = int(request.GET['iDisplayLength'])
    ajax_response['aaData'] = ajax_response['aaData'][start:start+length]
    json_data = json.dumps(ajax_response)
    return HttpResponse(json_data, content_type='application/json')


# Don't go below


# Dude...


# Seriously, u don't want to go there.


# I have warned u!


# Are u even listening to me?


# YOU ARE NOT PREPARED!


# Search cases:

# filtering out Last4OfCC
def search_last4ofcc_filter(numbers, names, company, dropdown, delimiter):
    response = []
    if dropdown == 'Last4ofCC':
        for customer in Customer.objects.filter(creditcard__endswith=numbers[0]):
            unused_charges_amount = 0
            for charge in Charge.objects.filter(used=False, customer=customer):
                unused_charges_amount += charge.amount-charge.summ
            charge_type = ''
            if customer.charge_type == Customer.CASH:
                charge_type = ' <i data-toggle="tooltip" title="%s" class="fa fa-money"> (%s)' % (customer.get_charge_getaway_display(), customer.get_charge_getaway_display())
            elif customer.charge_type == Customer.CREDITCARD:
                charge_type = ' <i data-toggle="tooltip" title="%s" class="fa fa-credit-card"> (%s)' % (customer.get_charge_getaway_display(), customer.get_charge_getaway_display())
            response.append([type(customer).__name__,
                             '<a href=\'%s' % (reverse('customer_update', args=[customer.id])) +
                             '\'>' + customer.__unicode__() + '</a>' +
                             '<a href=\"/search/?searchfor=' + customer.__unicode__().replace(' ',
                                                                                              '+')
                             + '\" data-toggle=\"tooltip\" title=\"Show all records for this name.\">' +
                             '<span class=\"glyphicon glyphicon-user\" aria-hidden=\"true\"></span>' + '</a>' +
                             charge_type + ' credit: <b>$' +
                             str(unused_charges_amount) + '</b>'])
        for charge in Charge.objects.filter(creditcard__endswith=numbers[0], company=company).order_by('-created'):
            cc_last_four = ''
            used = '</a><span class="fa fa-minus-circle text-danger"></span>'
            used_for = ' used for '
            if charge.creditcard:
                cc_last_four = ' *' + charge.creditcard[-4:]
            if charge.used:
                used = '</a><span class="fa fa-check-circle text-success"></span>'
            if charge.autorefill:
                if charge.autorefill.phone_number:
                    used_for += '<b>' + charge.autorefill.phone_number + '</b>'
            response.append([type(charge).__name__,
                             '<a href=\'%s' % (reverse('charge_detail', args=[charge.id])) +
                             '\'>Credit Card Charge #' + charge.__unicode__() + cc_last_four + '</a> '
                             + used + ' (<b>'
                             + charge.get_status_display() + '</b>)' + used_for + ' Created: <b>' +
                             charge.created.astimezone(timezone('US/Eastern')).strftime("%m/%d/%y "
                                                                                        "%I:%M:%S%p") +
                             '</b> for <b>$' + str(charge.amount) + '</b> (available amount <b>$'
                             + str(charge.amount - charge.summ) + '</b>)'])
    return response, len(response)


# filtering out unused pins
def search_unused_pins_filter(numbers, names, company, dropdown, delimiter):
    response = []
    if dropdown == '' or dropdown == 'All' or dropdown == 'UnusedPins':
        for unused_pin in UnusedPin.objects.filter(reduce(operator.and_, (Q(pin__icontains=fil) for fil in numbers+names)),
                                                   company=company):
            used = '<span class="fa fa-minus-circle text-danger"></span>'
            transaction = ''
            if unused_pin.used:
                used = '<span class="fa fa-check-circle text-success"></span>'
            if unused_pin.transaction:
                transaction = ' Transaction: ' + '<a href=\'%s' % (reverse('transaction_detail',
                                                                           args=[unused_pin.transaction.id]))\
                              + '\'>' + unused_pin.transaction.__unicode__() + '</a>'
            response.append([type(unused_pin).__name__,
                             '<a href=\'%s' % (reverse('unusedpin_update', args=[unused_pin.id])) +
                             '\'>Unused Pin #' + unused_pin.__unicode__() +
                             ' </a>' + used + transaction + ' Created: <b>'
                             + unused_pin.created.astimezone(timezone('US/Eastern')).strftime("%m/%d/%y "
                                                                                              "%I:%M:%S%p")
                             + '</b> Updated: <b>'
                             + unused_pin.updated.astimezone(timezone('US/Eastern')).strftime("%m/%d/%y "
                                                                                              "%I:%M:%S%p")
                             + '</b>'])
    return response, len(response)


# filtering out charges
def search_charges_filter(numbers, names, company, dropdown, delimiter):
    response = []
    if delimiter == '*' and len(numbers) == 1 and len(numbers[0]) == 4:
        for charge in Charge.objects.filter(creditcard__endswith=numbers[0], company=company).order_by('-created'):
            cc_last_four = ''
            used = '</a><span class="fa fa-minus-circle text-danger"></span>'
            used_for = ' used for '
            if charge.creditcard:
                cc_last_four = ' *' + charge.creditcard[-4:]
            if charge.used:
                used = '</a><span class="fa fa-check-circle text-success"></span>'
            if charge.autorefill:
                if charge.autorefill.phone_number:
                    used_for += '<b>' + charge.autorefill.phone_number + '</b>'
            response.append([type(charge).__name__,
                             '<a href=\'%s' % (reverse('charge_detail', args=[charge.id])) +
                             '\'>Credit Card Charge #' + charge.__unicode__() + cc_last_four + '</a> '
                             + used + ' (<b>'
                             + charge.get_status_display() + '</b>)' + used_for + ' Created: <b>' +
                             charge.created.astimezone(timezone('US/Eastern')).strftime("%m/%d/%y "
                                                                                        "%I:%M:%S%p") +
                             '</b> for <b>$' + str(charge.amount) + '</b> (available amount <b>$'
                             + str(charge.amount - charge.summ) + '</b>)'])
    elif dropdown == '' or dropdown == 'All' or dropdown == 'Charges':
        for charge in Charge.objects.filter(reduce(operator.and_, (Q(customer__first_name__icontains=fil) |
                                                                   Q(customer__middle_name__icontains=fil) |
                                                                   Q(customer__last_name__icontains=fil) |
                                                                   Q(autorefill__phone_number__icontains=fil) |
                                                                   Q(creditcard__endswith=fil)
                                                                   for fil in numbers+names)),
                                            company=company).order_by('-created'):
            cc_last_four = ''
            used = '</a><span class="fa fa-minus-circle text-danger"></span>'
            used_for = ' used for '
            if charge.creditcard:
                cc_last_four = ' *' + charge.creditcard[-4:]
            if charge.used:
                used = '</a><span class="fa fa-check-circle text-success"></span>'
            if charge.autorefill:
                if charge.autorefill.phone_number:
                    used_for += '<b>' + charge.autorefill.phone_number + '</b>'
            response.append([type(charge).__name__,
                             '<a href=\'%s' % (reverse('charge_detail', args=[charge.id])) +
                             '\'>Credit Card Charge #' + charge.__unicode__() + cc_last_four + '</a> '
                             + used + ' (<b>'
                             + charge.get_status_display() + '</b>)' + used_for + ' Created: <b>' +
                             charge.created.astimezone(timezone('US/Eastern')).strftime("%m/%d/%y "
                                                                                        "%I:%M:%S%p") +
                             '</b> for <b>$' + str(charge.amount) + '</b> (available amount <b>$'
                             + str(charge.amount - charge.summ) + '</b>)'])
    return response, len(response)


# filtering out transactions
def search_transactions_filter(numbers, names, company, dropdown, delimiter):
    response = []
    if dropdown == '' or dropdown == 'All' or dropdown == 'Transactions':
        for transaction in Transaction.objects.filter(reduce(operator.and_, (Q(customer_str__icontains=fil) |
                                                                             Q(phone_number_str__icontains=fil) |
                                                                             Q(pin__icontains=fil)
                                                                             for fil in numbers+names)),
                                                      company=company).order_by('-started'):

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
            response.append([type(transaction).__name__,
                             '<a href=\'%s' % (reverse('transaction_detail', args=[transaction.id])) +
                             '\'>Transaction #' + transaction.__unicode__() + '</a> (<b>'
                             + str(transaction.get_status_display()) + '</b>) for <b>'
                             + transaction.phone_number_str + '</b> (<b>' +
                             str(transaction.get_state_display()) + '</b>) Plan: <b>'
                             + transaction.plan_str + '</b> ' + started + ' ' + ended + ' ' + trigger])
    return response, len(response)


# filtering out autorefills
def search_autorefills_filter(numbers, names, company, dropdown, delimiter):
    response = []
    # regular search
    if dropdown == '' or dropdown == 'All' or dropdown == 'AutoRefills':
        for autorefill in AutoRefill.objects.filter(reduce(operator.and_, (Q(customer__first_name__icontains=fil) |
                                                                           Q(customer__middle_name__icontains=fil) |
                                                                           Q(customer__last_name__icontains=fil) |
                                                                           Q(phone_number__icontains=fil)
                                                                           for fil in numbers+names)),
                                                    Q(trigger=AutoRefill.TRIGGER_AP) | Q(trigger=AutoRefill.TRIGGER_SC),
                                                    company=company):
            last_renewal = ''
            if autorefill.last_renewal_date:
                last_renewal = 'Last renewal: <b>' + str(autorefill.last_renewal_date) + '</b>'
            enabled = '</a><span class="fa fa-minus-circle text-danger"></span>'
            if autorefill.enabled:
                enabled = '</a><span class="fa fa-check-circle text-success"></span>'
            response.append([type(autorefill).__name__,
                             '<a href=\'%s' % (reverse('autorefill_update', args=[autorefill.id])) +
                             '\'>Scheduled Refill #' + autorefill.__unicode__() + '</a> ' + enabled +
                             ' for <b>' + autorefill.phone_number + '</b> Plan: <b>'
                             + autorefill.plan.__unicode__() + '</b> Scheduled for: <b>'
                             + str(autorefill.renewal_date) + '</b> ' + last_renewal])
    return response, len(response)


# filtering out customers
def search_customers_filter(numbers, names, company, dropdown, delimiter):
    response = []
    if delimiter == '*' and len(numbers) == 1 and len(numbers[0]) == 4:
        for customer in Customer.objects.filter(creditcard__endswith=numbers[0]):
            unused_charges_amount = 0
            for charge in Charge.objects.filter(used=False, customer=customer):
                unused_charges_amount += charge.amount-charge.summ
            charge_type = ''
            if customer.charge_type == Customer.CASH:
                charge_type = ' <i data-toggle="tooltip" title="%s" class="fa fa-money"> (%s)' % (customer.get_charge_getaway_display(), customer.get_charge_getaway_display())
            elif customer.charge_type == Customer.CREDITCARD:
                charge_type = ' <i data-toggle="tooltip" title="%s" class="fa fa-credit-card"> (%s)' % (customer.get_charge_getaway_display(), customer.get_charge_getaway_display())
            response.append([type(customer).__name__,
                                 '<a href=\'%s' % (reverse('customer_update', args=[customer.id])) +
                                 '\'>' + customer.__unicode__() + '</a>' +
                                 '<a href=\"/search/?searchfor=' + customer.__unicode__().replace(' ',
                                                                                                  '+')
                                 + '\" data-toggle=\"tooltip\" title=\"Show all records for this name.\">' +
                                 '<span class=\"glyphicon glyphicon-user\" aria-hidden=\"true\"></span>' + '</a>' +
                                 charge_type + ' credit: <b>$' +
                                 str(unused_charges_amount) + '</b>'])
    elif delimiter == '/' and len(numbers) == 1 and len(numbers[0]) == 4:
        for phone_number in PhoneNumber.objects.filter(number__endswith=numbers[0]).exclude(customer=None):
            unused_charges_amount = 0
            for charge in Charge.objects.filter(used=False, customer=phone_number.customer):
                unused_charges_amount += charge.amount-charge.summ
            charge_type = ''
            if phone_number.customer.charge_type == Customer.CASH:
                charge_type = ' <i data-toggle="tooltip" title="%s" class="fa fa-money"> (%s)' % (phone_number.customer.get_charge_getaway_display(), phone_number.customer.get_charge_getaway_display())
            elif phone_number.customer.charge_type == Customer.CREDITCARD:
                charge_type = ' <i data-toggle="tooltip" title="%s" class="fa fa-credit-card"> (%s)' % (phone_number.customer.get_charge_getaway_display(), phone_number.customer.get_charge_getaway_display())
            response.append([type(phone_number.customer).__name__,
                             '<a href=\'%s' % (reverse('customer_update', args=[phone_number.customer.id])) +
                             '\'>' + phone_number.customer.__unicode__() + '</a>' +
                             '<a href=\"/search/?searchfor=' + phone_number.customer.__unicode__().replace(' ',
                                                                                                           '+')
                             + '\" data-toggle=\"tooltip\" title=\"Show all records for this name.\">' +
                             '<span class=\"glyphicon glyphicon-user\" aria-hidden=\"true\"></span>' + '</a>' +
                             charge_type + ' credit: <b>$'
                             + str(unused_charges_amount) + '</b>)'])
    # regular customer search
    elif dropdown == '' or dropdown == 'All' or dropdown == 'Customers':
        for id in PhoneNumber.objects.filter(reduce(operator.and_,
                                                    (Q(customer__first_name__icontains=fil) |
                                                     Q(customer__middle_name__icontains=fil) |
                                                     Q(customer__last_name__icontains=fil) |
                                                     Q(number__icontains=fil)
                                                     for fil in numbers+names)),
                                             company=company).exclude(customer=None).values_list('customer',
                                                                                                 flat=True).distinct():
            unused_charges_amount = 0
            charge_type = ''
            if Customer.objects.get(id=id).charge_type == Customer.CASH:
                charge_type = ' <i data-toggle="tooltip" title="%s" class="fa fa-money"> (%s)' % (Customer.objects.get(id=id).get_charge_getaway_display(), Customer.objects.get(id=id).get_charge_getaway_display())
            elif Customer.objects.get(id=id).charge_type == Customer.CREDITCARD:
                charge_type = ' <i data-toggle="tooltip" title="%s" class="fa fa-credit-card"> (%s)' % (Customer.objects.get(id=id).get_charge_getaway_display(), Customer.objects.get(id=id).get_charge_getaway_display())
            for charge in Charge.objects.filter(used=False, customer=Customer.objects.get(id=id)):
                unused_charges_amount += charge.amount-charge.summ
            if len(numbers) == 1 and len(names) == 0 and len(numbers[0]) == 10:
                response.append([type(Customer.objects.get(id=id)).__name__,
                                 '<a href=\'%s' % (reverse('customer_update', args=[id])) +
                                 '\'>' + Customer.objects.get(id=id).__unicode__() + '</a>'  +
                                 '<a href=\"/search/?searchfor=' + Customer.objects.get(id=id).__unicode__().replace(' ',
                                                                                                                     '+')
                                 + '\" data-toggle=\"tooltip\" title=\"Show all records for this name.\">' +
                                 '<span class=\"glyphicon glyphicon-user\" aria-hidden=\"true\"></span>' + '</a>' +
                                 charge_type
                                 + ' credit: <b>$' + str(unused_charges_amount)
                                 + '</b>' + ' <div style=\"float: right\">' + ' <a href=\'%s' %
                                 reverse('charge_list') + '?cid=' + str(Customer.objects.get(id=id).id) +
                                 '\' style=\"background-color: green\" class=\'btn '
                                 'btn-primary btn-xs\'>Add cash payment</a> '
                                 + ' <a href=\'%s' % reverse('manualrefill') + '?ph=' + numbers[0] + '&cid=' +
                                 str(Customer.objects.get(id=id).id) + '&lp=t' + '\' style=\"background-color: #366\"'
                                                              ' class=\'btn '
                                                              'btn-primary btn-xs\'>Recharge With Last'
                                                              ' Plan</a> ' + '<a href=\'%s' %
                                 reverse('manualrefill') + '?ph=' + numbers[0] + '&cid=' + str(Customer.objects.get(id=id).id) +
                                 '\' class=\'btn btn-primary btn-xs\'>Recharge Now</a>' +
                                 ' <a style=\"background-color: #4BA2B7;\" href=\'%s' %
                                 reverse('autorefill_create') + '?ph=' + numbers[0] +
                                 '&cid=' + str(Customer.objects.get(id=id).id) + '&lp=t' +
                                 '\' class=\'btn btn-info btn-xs\'' + '>' +
                                 'Schedule With Last Plan</a>' +
                                 ' <a href=\'%s' % reverse('autorefill_create') + '?ph=' + numbers[0] +
                                 '&cid=' + str(Customer.objects.get(id=id).id) + '\' class=\'btn btn-info btn-xs\''
                                                              + '>'
                                                              'Schedule Latter</a>' + '</div>'])
            else:
                response.append([type(Customer.objects.get(id=id)).__name__,
                                 '<a href=\'%s' % (reverse('customer_update', args=[id])) +
                                 '\'>' + Customer.objects.get(id=id).__unicode__() + '</a>' +
                                 '<a href=\"/search/?searchfor=' + Customer.objects.get(id=id).__unicode__().replace(' ',
                                                                                                                     '+')
                                 + '\" data-toggle=\"tooltip\" title=\"Show all records for this name.\">' +
                                 '<span class=\"glyphicon glyphicon-user\" aria-hidden=\"true\"></span>' + '</a>' +
                                 charge_type +
                                 ' credit: <b>$' + str(unused_charges_amount) + '</b>'])
        for customer in Customer.objects.filter(reduce(operator.and_,
                                                       (Q(creditcard__endswith=fil)
                                                       for fil in numbers+names)),
                                                company=company):
            unused_charges_amount = 0
            for charge in Charge.objects.filter(used=False, customer=customer):
                unused_charges_amount += charge.amount-charge.summ
            # if there is just a number in search input
            charge_type = ''
            if customer.charge_type == Customer.CASH:
                charge_type = ' <i data-toggle="tooltip" title="%s" class="fa fa-money"> (%s)' % (customer.get_charge_getaway_display(), customer.get_charge_getaway_display())
            elif customer.charge_type == Customer.CREDITCARD:
                charge_type = ' <i data-toggle="tooltip" title="%s" class="fa fa-credit-card"> (%s)' % (customer.get_charge_getaway_display(), customer.get_charge_getaway_display())
            if len(numbers) == 1 and len(names) == 0 and len(numbers[0]) == 10:
                response.append([type(customer).__name__,
                                 '<a href=\'%s' % (reverse('customer_update', args=[customer.id])) +
                                 '\'>' + customer.__unicode__() + '</a>' +
                                 '<a href=\"/search/?searchfor=' + customer.__unicode__().replace(' ',
                                                                                                  '+')
                                 + '\" data-toggle=\"tooltip\" title=\"Show all records for this name.\">' +
                                 '<span class=\"glyphicon glyphicon-user\" aria-hidden=\"true\"></span>' + '</a>' +
                                 charge_type
                                 + ' credit: <b>$' + str(unused_charges_amount)
                                 + '</b>' + ' <div style=\"float: right\">' + ' <a href=\'%s' %
                                 reverse('charge_list') + '?cid=' + str(customer.id) +
                                 '\' style=\"background-color: green\" class=\'btn '
                                 'btn-primary btn-xs\'>Add cash payment</a> '
                                 + ' <a href=\'%s' % reverse('manualrefill') + '?ph=' + numbers[0] + '&cid=' +
                                 str(customer.id) + '&lp=t' + '\' style=\"background-color: #366\"'
                                                              ' class=\'btn '
                                                              'btn-primary btn-xs\'>Recharge With Last'
                                                              ' Plan</a> ' + '<a href=\'%s' %
                                 reverse('manualrefill') + '?ph=' + numbers[0] + '&cid=' + str(customer.id) +
                                 '\' class=\'btn btn-primary btn-xs\'>Recharge Now</a>' +
                                 ' <a style=\"background-color: #4BA2B7;\" href=\'%s' %
                                 reverse('autorefill_create') + '?ph=' + numbers[0] +
                                 '&cid=' + str(customer.id) + '&lp=t' +
                                 '\' class=\'btn btn-info btn-xs\'' + '>' +
                                 'Schedule With Last Plan</a>' +
                                 ' <a href=\'%s' % reverse('autorefill_create') + '?ph=' + numbers[0] +
                                 '&cid=' + str(customer.id) + '\' class=\'btn btn-info btn-xs\''
                                                              + '>'
                                                              'Schedule Latter</a>' + '</div>'])
            else:
                response.append([type(customer).__name__,
                                 '<a href=\'%s' % (reverse('customer_update', args=[customer.id])) +
                                 '\'>' + customer.__unicode__() + '</a>' +
                                 '<a href=\"/search/?searchfor=' + customer.__unicode__().replace(' ',
                                                                                                  '+')
                                 + '\" data-toggle=\"tooltip\" title=\"Show all records for this name.\">' +
                                 '<span class=\"glyphicon glyphicon-user\" aria-hidden=\"true\"></span>' + '</a>' +
                                 charge_type +
                                 ' credit: <b>$' + str(unused_charges_amount) + '</b>'])
    return response, len(response)


# filtering out phone numbers numbers
def search_phone_numbers_filter(numbers, names, company, dropdown, delimiter):
    response = []
    # search only for numbers that is ending with input in search bar if there is '/' delimiter
    if delimiter == '/' and len(numbers) == 1 and len(numbers[0]) == 4:
        for phone_number in PhoneNumber.objects.filter(number__endswith=numbers[0],
                                                       company=company).exclude(customer=None):
            response.append([type(phone_number).__name__, 'Phone number: <b>' + phone_number.number + '</b>'
                                         ' for <a href=\'%s' % (reverse('customer_update', args=[phone_number.customer.id])) +
                                         '\'>' + phone_number.customer.__unicode__() + '</a> '
                                         + ' <div style=\"float: right\">' + ' <a href=\'%s' %
                                         reverse('charge_list') + '?cid=' + str(phone_number.customer.id) +
                                         '\' style=\"background-color: green\" class=\'btn '
                                         'btn-primary btn-xs\'>Add cash payment</a> '
                                         + ' <a href=\'%s' % reverse('manualrefill') + '?ph=' + phone_number.number + '&cid=' +
                                         str(phone_number.customer.id) + '&lp=t' + '\' style=\"background-color: #366\"'
                                                                      ' class=\'btn '
                                                                      'btn-primary btn-xs\'>Recharge With Last'
                                                                      ' Plan</a> ' + '<a href=\'%s' %
                                         reverse('manualrefill') + '?ph=' + phone_number.number + '&cid=' + str(phone_number.customer.id) +
                                         '\' class=\'btn btn-primary btn-xs\'>Recharge Now</a>' +
                                         ' <a style=\"background-color: #4BA2B7;\" href=\'%s' %
                                         reverse('autorefill_create') + '?ph=' + phone_number.number +
                                         '&cid=' + str(phone_number.customer.id) + '&lp=t' +
                                         '\' class=\'btn btn-info btn-xs\'' + '>' +
                                         'Schedule With Last Plan</a>' +
                                         ' <a href=\'%s' % reverse('autorefill_create') + '?ph=' + phone_number.number +
                                         '&cid=' + str(phone_number.customer.id) + '\' class=\'btn btn-info btn-xs\''
                                                                      + '>'
                                                                      'Schedule Latter</a>' + '</div>'])
    # regular number search
    elif dropdown == '' or dropdown == 'All' or dropdown == 'PhoneNumber':
        for phone_number in PhoneNumber.objects.filter(reduce(operator.and_,
                                                              (Q(number__icontains=fil) |
                                                               Q(customer__first_name__icontains=fil) |
                                                               Q(customer__middle_name__icontains=fil) |
                                                               Q(customer__last_name__icontains=fil)
                                                               for fil in numbers+names)),
                                                       company=company).exclude(customer=None):
            response.append([type(phone_number).__name__, 'Phone number: <b>' + phone_number.number + '</b>'
                                         ' for <a href=\'%s' % (reverse('customer_update', args=[phone_number.customer.id])) +
                                         '\'>' + phone_number.customer.__unicode__() + '</a> '
                                         + ' <div style=\"float: right\">' + ' <a href=\'%s' %
                                         reverse('charge_list') + '?cid=' + str(phone_number.customer.id) +
                                         '\' style=\"background-color: green\" class=\'btn '
                                         'btn-primary btn-xs\'>Add cash payment</a> '
                                         + ' <a href=\'%s' % reverse('manualrefill') + '?ph=' + phone_number.number + '&cid=' +
                                         str(phone_number.customer.id) + '&lp=t' + '\' style=\"background-color: #366\"'
                                                                      ' class=\'btn '
                                                                      'btn-primary btn-xs\'>Recharge With Last'
                                                                      ' Plan</a> ' + '<a href=\'%s' %
                                         reverse('manualrefill') + '?ph=' + phone_number.number + '&cid=' + str(phone_number.customer.id) +
                                         '\' class=\'btn btn-primary btn-xs\'>Recharge Now</a>' +
                                         ' <a style=\"background-color: #4BA2B7;\" href=\'%s' %
                                         reverse('autorefill_create') + '?ph=' + phone_number.number +
                                         '&cid=' + str(phone_number.customer.id) + '&lp=t' +
                                         '\' class=\'btn btn-info btn-xs\'' + '>' +
                                         'Schedule With Last Plan</a>' +
                                         ' <a href=\'%s' % reverse('autorefill_create') + '?ph=' + phone_number.number +
                                         '&cid=' + str(phone_number.customer.id) + '\' class=\'btn btn-info btn-xs\''
                                                                      + '>'
                                                                      'Schedule Latter</a>' + '</div>'])
    return response, len(response)