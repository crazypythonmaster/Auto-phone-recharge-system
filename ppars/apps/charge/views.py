import json
import decimal
import logging
import traceback
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponse
from django.views.generic import DetailView, ListView
import operator
from pytz import timezone
from ppars.apps.charge.models import Charge, ChargeStep, TransactionCharge, Transaction
from ppars.apps.core.models import Customer
from ppars.apps.core.send_notifications import successful_precharge_restart_customer_notification

logger = logging.getLogger('ppars')


class ChargeList(ListView):
    model = Charge

    def get_queryset(self):
        return Charge.objects.filter(company_id=self.request.user.profile.company_id)

    def get_context_data(self, **kwargs):
        context = super(ChargeList, self).get_context_data(**kwargs)
        context['customers'] = Customer.objects.filter(company_id=self.request.user.profile.company_id).exclude(charge_getaway=Customer.DOLLARPHONE).order_by('first_name')
        return context


class ChargeDetail(DetailView):
    model = Charge


def ajax_charge_steps(request, pk):
    steps = ChargeStep.objects.filter(charge=pk).order_by('created')
    step_list = []
    for step in steps:
        step_obj = {
                'action': step.action,
                'status': step.status,
                'status_str': step.get_status_display(),
                'adv_status': step.adv_status,
                'created': step.created.astimezone(timezone('US/Eastern')).strftime("%m/%d/%y %I:%M:%S%p"),
        }
        step_list.append(step_obj)
    data = {
        'steps': step_list,
    }
    return render_to_json_response(data)


def ajax_mark_charge(request):
    id = request.GET.get('id')
    button = request.GET.get('button')
    charge = Charge.objects.get(id=id)
    amount = decimal.Decimal(request.GET.get('amount'))

    # Mark charge used
    if button == 'used':
        if not amount:
            amount = charge.amount
        charge.summ = charge.summ + amount

    # Mark charge unused
    elif button == 'unused':
        if not amount:
            amount = charge.summ
        charge.summ = charge.summ - amount

    if charge.summ == charge.amount:
        charge.used = True
    else:
        charge.used = False

    charge.save()
    charge.add_charge_step('mark %s' % button, Charge.SUCCESS,
                           'User %s mark $%s as %s.' % (
                               request.user, amount, button)
                           )
    return HttpResponse()


def ajax_cc_retry(request):
    charge_id = request.GET.get('id')
    action = 'retry charging'
    if charge_id:
        old_cc = Charge.objects.get(id=charge_id)
        try:
            if old_cc.payment_getaway in [Charge.AUTHORIZE] and old_cc.atransaction:
                old_cc.status = Charge.SUCCESS
                old_cc.save()
                old_cc.add_charge_step(action, Charge.SUCCESS, 'User "%s" started retry.Previous charge was successfully. Restart canceled' % request.user)
            else:
                old_cc = old_cc.check_getaway()
                old_cc.make_charge(retry=True)
                old_cc.add_charge_step(action, Charge.SUCCESS, 'User "%s" started retry. Charge retry ended successfully' % request.user)
                if old_cc.customer.email_success_charge:
                    successful_precharge_restart_customer_notification(old_cc)
        except Exception, e:
            logger.error("Exception: %s. Trace: %s." % (e, traceback.format_exc(limit=10)))
            old_cc.add_charge_step(action, Charge.ERROR, 'User "%s" started retry. Charge retry ended with error: "%s"' % (request.user, e))
        finally:
            return HttpResponse("Done")


def ajax_cc_retry_and_trans_restart(request):
    charge_id = request.GET.get('id')
    action = 'retry charging'
    if charge_id:
        old_cc = Charge.objects.get(id=charge_id)
        try:
            if old_cc.payment_getaway in [Charge.AUTHORIZE] and old_cc.atransaction:
                old_cc.status = Charge.SUCCESS
                old_cc.save()
                old_cc.add_charge_step(action, Charge.SUCCESS, 'User "%s" started retry.Previous charge was successfully. Restart canceled' % request.user)
            else:
                old_cc = old_cc.check_getaway()
                old_cc.make_charge(retry=True)
                old_cc.add_charge_step(action, Charge.SUCCESS, 'User "%s" started retry. Charge retry ended successfully' % request.user)
                if old_cc.customer.email_success_charge:
                    successful_precharge_restart_customer_notification(old_cc)

            transaction = old_cc.get_last_transaction
            transaction.retry_count = 1
            transaction.state = Transaction.RETRY
            transaction.adv_status = 'Transaction restarted by user %s' % request.user
            transaction.add_transaction_step('Restarted',
                                             'button',
                                             Transaction.SUCCESS,
                                             'User %s restarted transaction.' % request.user)
            transaction.save()
            from ppars.apps.core.tasks import queue_refill
            transaction.was_retried_on_step = False
            queue_refill.delay(transaction.id)
        except Exception, e:
            logger.error("Exception: %s. Trace: %s." % (e, traceback.format_exc(limit=10)))
            old_cc.add_charge_step(action, Charge.ERROR, 'User "%s" started retry. Charge retry ended with error: "%s"' % (request.user, e))
        finally:
            return HttpResponse("Done")


def ajax_charges_list(request):
    orders = [('1', 'customer'), ('9', 'created')]
    order_by = 'created'
    for order in orders:
        if order[0] == request.GET['iSortCol_0']:
            order_by = order[1]
            break
    direction = ''
    if request.GET['sSortDir_0'] == 'desc':
        direction = '-'
    filters = request.GET['sSearch'].split(' ')
    filtered = Charge.objects.filter(reduce(operator.and_, (Q(id__icontains=val) |
                                                            Q(customer__first_name__icontains=val) |
                                                            Q(customer__middle_name__icontains=val) |
                                                            Q(customer__last_name__icontains=val) |
                                                            Q(autorefill__phone_number__icontains=val) |
                                                            Q(atransaction__icontains=val)
                                                            for val in filters)),
                                     company=request.user.profile.company, status__icontains=request.GET['sSearch_6'])
    if request.GET['sSearch_5'] != '':
        filtered = filtered.filter(payment_getaway=request.GET['sSearch_5'])
    if request.GET['sSearch_7'] == 'True':
        filtered = filtered.filter(used=True)
    elif request.GET['sSearch_7'] == 'False':
        filtered = filtered.filter(used=False)
    ajax_response = {"sEcho": request.GET['sEcho'], "aaData": [],
                     'iTotalRecords': Charge.objects.filter(company=request.user.profile.company).count(),
                     'iTotalDisplayRecords': filtered.count()}
    start = int(request.GET['iDisplayStart'])
    length = int(request.GET['iDisplayLength'])
    for charge in filtered.order_by(direction+order_by)[start:start+length]:
        phone_number = ''
        if charge.autorefill:
            phone_number = charge.autorefill.phone_number
        transaction = ''
        if TransactionCharge.objects.filter(charge=charge):
            if TransactionCharge.objects.filter(charge=charge)[0].transaction:
                transaction = '<a href=\'%s' % (reverse('transaction_detail',
                                                        args=[TransactionCharge.objects.filter(charge=charge)[0].transaction.id])) + '\'>' +\
                              str(TransactionCharge.objects.filter(charge=charge)[0].transaction.id) + '</a>'
        ajax_response['aaData'].append(['<a href=\'%s' % (reverse('charge_detail', args=[charge.id])) + '\'>' +
                                        str(charge.id) + '</a>',
                                        '<a href=\'%s' % (reverse('customer_update', args=[charge.customer.id])) + '\'>' +\
                                        charge.customer.full_name + '</a>', phone_number,
                                        charge.creditcard, '$'+str(charge.amount), charge.payment_getaway, charge.status,
                                        charge.used, transaction,
                                        charge.created.astimezone(timezone('US/Eastern')).strftime("%m/%d/%y %H:%M")
                                        ])
    return HttpResponse(json.dumps(ajax_response), content_type='application/json')


def ajax_change_charge_note(request):
    charge = Charge.objects.get(id=request.GET['id'])
    charge.note = request.GET['note']
    charge.save()
    return HttpResponse(json.dumps({}), content_type='application/json')


def ajax_cc_refund(request):
    charge_id = request.GET.get('id')
    if charge_id:
        old_cc = Charge.objects.get(id=charge_id)
        try:
            old_cc.make_refund(request.user)
        except Exception, e:
            logger.error("Exception: %s. Trace: %s." % (e, traceback.format_exc(limit=10)))
            old_cc.make_void(request.user)
        finally:
            return HttpResponse("Done")


def ajax_cc_void(request):
    charge_id = request.GET.get('id')
    if charge_id:
        old_cc = Charge.objects.get(id=charge_id)
        try:
            old_cc.make_void(request.user)
        except Exception, e:
            logger.error("Exception: %s. Trace: %s." % (e, traceback.format_exc(limit=10)))
            old_cc.make_refund(request.user)
        finally:
            return HttpResponse("Done")


def render_to_json_response(context, **response_kwargs):
    data = json.dumps(context)
    response_kwargs['content_type'] = 'application/json'
    return HttpResponse(data, **response_kwargs)


def ajax_charge_create(request):
    customer_id = request.POST.get('customer_id')
    amount = request.POST.get('amount')
    like_cash = request.POST.get('like_cash')
    note = request.POST.get('note')
    customer = Customer.objects.get(id=customer_id)
    charge_getaway = customer.charge_getaway
    if like_cash.upper() == 'TRUE':
        charge_getaway = Charge.CASH_PREPAYMENT
    adv_status = 'User %s created charge.' % request.user
    card_number = ''
    if customer.creditcard:
        card_number = customer.creditcard
    charge = Charge.objects.create(
        company=customer.company,
        customer=customer,
        amount=amount,
        creditcard=card_number,
        payment_getaway=charge_getaway,
        status=Charge.SUCCESS,
        adv_status=adv_status,
        note=note
    )
    charge.add_charge_step('create', ChargeStep.SUCCESS, adv_status)
    try:
        charge.make_charge()
        charge.add_charge_step('charge', ChargeStep.SUCCESS, 'Charge ended successfully')
    except Exception, e:
        logger.error("Exception: %s. Trace: %s." % (e, traceback.format_exc(limit=10)))
        charge.add_charge_step('charge', ChargeStep.ERROR, 'Charge ended with error: "%s"' % e)
    data = {
        'charge': charge.id
    }
    return render_to_json_response(data)
