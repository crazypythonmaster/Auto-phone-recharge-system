import json
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, render
from django.views.generic import View, ListView, UpdateView
from django.views.generic.edit import CreateView
from models import SpamMessage, CustomPreChargeMessage, EzCloudNewsEmails, WelcomeEmail
from forms import SpamMessageForm, CustomPreChargeMessageForm, WelcomeEmailForm
from tasks import queue_send_sms
from django.core.validators import validate_email


class WelcomeEmailList(ListView):
    model = WelcomeEmail
    template_name = 'notification/welcome_email_list.html'
    context_object_name = 'welcome_emails'

    def get_queryset(self):
        return WelcomeEmail.objects.filter(company=self.request.user.profile.company)


class WelcomeEmailCreate(View):
    model = WelcomeEmail
    template_name = 'notification/welcome_email_create.html'
    form_class = WelcomeEmailForm

    def get(self, request, *args, **kwargs):
        form = WelcomeEmailForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = WelcomeEmailForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.company = request.user.profile.company
            if message.enabled:
                for email in WelcomeEmail.objects.filter(company=request.user.profile.company,
                                                         category=message.category):
                    email.enabled = False
                    email.save()
            message.save()
            return HttpResponseRedirect(reverse('welcome_email'))
        else:
            return render(request, self.template_name, {'form': form})


class WelcomeEmailEdit(View):
    model = WelcomeEmail
    template_name = 'notification/welcome_email_create.html'
    form_class = WelcomeEmailForm

    def get(self, request, pk, *args, **kwargs):
        obj = get_object_or_404(WelcomeEmail, id=pk)
        form = WelcomeEmailForm(instance=obj)
        return render(request, self.template_name, {'form': form})

    def post(self, request, pk, *args, **kwargs):
        obj = get_object_or_404(WelcomeEmail, id=pk)
        form = WelcomeEmailForm(request.POST, instance=obj)
        if form.is_valid():
            obj = form.save(commit=False)
            if obj.enabled:
                for email in WelcomeEmail.objects.filter(company=request.user.profile.company, category=obj.category):
                    email.enabled = False
                    email.save()
            obj.save()
            return HttpResponseRedirect(reverse('welcome_email'))
        else:
            return render(request, self.template_name, {'form': form})


def welcome_message_delete(request, pk):
    obj = get_object_or_404(WelcomeEmail, id=pk, company=request.user.profile.company)
    obj.delete()
    return HttpResponse()


class SpamMessageCreate(CreateView):
    model = SpamMessage
    form_class = SpamMessageForm

    def form_valid(self, form):
        self.object = spam_message = form.save(commit=False)
        spam_message.company = self.request.user.profile.company
        if not self.request.user.profile.company.twilio_sid or \
                not self.request.user.profile.company.twilio_auth_token or \
                not self.request.user.profile.company.twilio_number:
            messages.add_message(self.request, messages.ERROR,
                                 'Twilio account is missing in company')
        else:

            spam_message.save()
            queue_send_sms.delay(spam_message.id)
            messages.add_message(self.request, messages.SUCCESS,
                                 'Messages will be send.')
        return super(SpamMessageCreate, self).form_valid(form)


class CustomPreChargeMessageDetail(View):
    model = CustomPreChargeMessage
    form_class = CustomPreChargeMessageForm
    template_name = 'notification/customprechargemessage_form.html'
    context_object_name = 'custom_precharge_message'

    def get(self, request, *args, **kwargs):
        if CustomPreChargeMessage.objects.filter(company=request.user.profile.company).exists():
            m = get_object_or_404(CustomPreChargeMessage, company=request.user.profile.company)
            form = CustomPreChargeMessageForm(instance=m)
            return render(request, self.template_name,
                          {
                              'form': form,
                              'custom_precharge_message': m,
                          })
        else:
            form = CustomPreChargeMessageForm()
            return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        if CustomPreChargeMessage.objects.filter(company=request.user.profile.company).exists():
            m = get_object_or_404(CustomPreChargeMessage, company=request.user.profile.company)
            form = CustomPreChargeMessageForm(request.POST, instance=m)
            if form.is_valid():
                self.object = m = form.save()
                messages.add_message(self.request, messages.SUCCESS, 'Messege updated successfully.')
                return render(request, self.template_name,
                              {
                                  'form': form,
                                  'custom_precharge_message': m,
                              })
            else:
                return render(request, self.template_name,
                              {
                                  'form': form,
                                  'custom_precharge_message': m,
                              })
        else:
            form = CustomPreChargeMessageForm(request.POST)
            if form.is_valid():
                self.object = m = form.save()
                messages.add_message(self.request, messages.SUCCESS, 'Messege updated successfully.')
                return render(request, self.template_name,
                              {
                                  'form': form,
                              })
            else:
                return render(request, self.template_name, {'form': form})


def ez_cloud_news_emails(request):
    if request.user.is_superuser:
        emails = ''
        if EzCloudNewsEmails.objects.all():
            emails = EzCloudNewsEmails.objects.all()[0].emails
        return render(request, 'notification/ez_cloud_news_emails.html',
                      {'ez_news_emails': emails})
    else:
        return HttpResponseRedirect('/')


def change_ez_email_list(request):
    if request.user.is_superuser:
        if EzCloudNewsEmails.objects.all():
            ez_cloud_news_emails = EzCloudNewsEmails.objects.all()[0]
        else:
            ez_cloud_news_emails = EzCloudNewsEmails()
        if request.GET['news_emails'] == '':
            ez_cloud_news_emails.emails = request.GET['news_emails']
            ez_cloud_news_emails.save()
            return HttpResponse(json.dumps({'valid': True}), content_type='application/json')
        try:
            emails = [email.strip(' ') for email in request.GET['news_emails'].split(',') if email != '']
            email_on_save = ''
            for email in emails:
                validate_email(email)
                email_on_save += email + ','
            ez_cloud_news_emails.emails = email_on_save
            ez_cloud_news_emails.save()
            return HttpResponse(json.dumps({'valid': True}), content_type='application/json')
        except ValidationError:
            return HttpResponse(json.dumps({'valid': False}), content_type='application/json')
    else:
        return HttpResponseRedirect('/')