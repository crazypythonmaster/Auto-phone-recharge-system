import logging
from django import forms
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, View, DeleteView
from ppars.apps.accounts.forms import PparsStrengthUserCreationForm, \
    UserEditForm
from ppars.apps.core.models import UserProfile

logger = logging.getLogger('ppars')


def login_user(request):
    logout(request)
    username = password = ''
    if request.POST:
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                if UserProfile.objects.get(user=user).is_license_expiries():
                    login(request, user)
                    if 'next' in request.GET:
                        return HttpResponseRedirect(request.GET['next'])
                    return HttpResponseRedirect('/')
                else:
                    return render(request, 'registration/login.html', {'license_limit': True})
        else:
            return render(request, 'registration/login.html', {'error': True})
    if request.GET:
        return render(request, 'registration/login.html')
    return HttpResponseRedirect('/')


class UserList(ListView):
    model = User
    template_name = 'accounts/user_list.html'
    context_object_name = 'user_list'

    def get_queryset(self):
        return self.request.user.profile.get_company_users()


class UserCreate(View):
    form_class = PparsStrengthUserCreationForm
    model = User
    template_name = 'accounts/user_form.html'

    def get(self, request, *args, **kwargs):
        form = PparsStrengthUserCreationForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = PparsStrengthUserCreationForm(request.POST)
        if form.is_valid():
            self.object = added_user = form.save(commit=True)
            p = added_user.profile
            p.company = self.request.user.profile.company
            p.save()
            messages.add_message(self.request, messages.SUCCESS, 'User "%s" created successfully.'% added_user)
            return render(request, 'accounts/user_list.html',
                          {
                           'user_list': request.user.profile.get_company_users(),
                          })
        else:
            logger.debug(form.errors)
            return render(request, self.template_name, {'form': form})


class UserUpdate(View):
    form_class = UserEditForm
    model = User
    template_name = 'accounts/user_form_edit.html'

    def get(self, request, pk, *args, **kwargs):
        user = get_object_or_404(User, pk=pk)
        form = UserEditForm(initial={
            'login':  user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            })
        return render(request, self.template_name, {'form': form, 'object': user})

    def post(self, request, pk, *args, **kwargs):
        user = get_object_or_404(User, pk=pk)
        form = UserEditForm(request.POST)
        if form.is_valid():
            self.object = user = form.save()
            messages.add_message(self.request, messages.SUCCESS, 'User "%s" updated successfully.' % user)
            return render(request, 'accounts/user_list.html',
                          {
                           'user_list': request.user.profile.get_company_users(),
                          })
        else:
            logger.debug(form.errors)
            return render(request, self.template_name, {'form': form, 'object': user})


class UserDelete(DeleteView):
    model = User
    template_name = 'accounts/user_confirm_delete.html'

    def get_success_url(self):
        return reverse('user_list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        # rel = UserProfile.objects.get(user=self.object)
        # rel.company = None
        # rel.save()
        self.object.delete()
        messages.add_message(self.request, messages.ERROR, 'User "%s" deleted successfully.' % self.object)
        return HttpResponseRedirect(self.get_success_url())