# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'CompanyProfile'
        db.create_table(u'core_companyprofile', (
            ('id', self.gf('ppars.apps.core.fields.BigAutoField')(primary_key=True)),
            ('updated', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('superuser_profile', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('company_name', self.gf('django.db.models.fields.CharField')(max_length=40, null=True, blank=True)),
            ('email_id', self.gf('django.db.models.fields.EmailField')(max_length=75, null=True, blank=True)),
            ('email_success', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('pin_error', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('short_retry_limit', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('short_retry_interval', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('long_retry_limit', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('long_retry_interval', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('twilio_number', self.gf('django.db.models.fields.CharField')(max_length=10, null=True, blank=True)),
            ('twilio_sid', self.gf('django.db.models.fields.CharField')(max_length=500, null=True, blank=True)),
            ('twilio_auth_token', self.gf('django.db.models.fields.CharField')(max_length=500, null=True, blank=True)),
            ('deathbycaptcha_user', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('deathbycaptcha_pass', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('deathbycaptcha_email_balance', self.gf('django.db.models.fields.IntegerField')(default=70, max_length=10, null=True, blank=True)),
            ('deathbycaptcha_count', self.gf('django.db.models.fields.IntegerField')(default=5000, max_length=10, null=True, blank=True)),
            ('deathbycaptcha_current_count', self.gf('django.db.models.fields.IntegerField')(default=0, max_length=10, null=True, blank=True)),
            ('deathbycaptcha_emailed', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('pageplus_refillmethod', self.gf('django.db.models.fields.CharField')(default='TW', max_length=3, null=True, blank=True)),
            ('dollar_type', self.gf('django.db.models.fields.CharField')(max_length=3, null=True, blank=True)),
            ('dollar_user', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('dollar_pass', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('mandrill_key', self.gf('django.db.models.fields.CharField')(max_length=500, null=True, blank=True)),
            ('mandrill_email', self.gf('django.db.models.fields.EmailField')(max_length=75, null=True, blank=True)),
            ('authorize_api_login_id', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('authorize_transaction_key', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('authorize_precharge_days', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('cccharge_type', self.gf('django.db.models.fields.CharField')(max_length=3, null=True, blank=True)),
            ('usaepay_source_key', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('usaepay_pin', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('usaepay_username', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('usaepay_password', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('use_sellercloud', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('sc_company_id', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('sc_password', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('sc_email', self.gf('django.db.models.fields.EmailField')(max_length=75, null=True, blank=True)),
            ('use_asana', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('asana_api_key', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('asana_workspace', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('asana_project_name', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('asana_user', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
        ))
        db.send_create_signal(u'core', ['CompanyProfile'])

        # Adding model 'UserProfile'
        db.create_table(u'core_userprofile', (
            ('id', self.gf('ppars.apps.core.fields.BigAutoField')(primary_key=True)),
            ('user', self.gf('ppars.apps.core.fields.BigOneToOneField')(blank=True, related_name='profile', unique=True, null=True, to=orm['auth.User'])),
            ('company', self.gf('ppars.apps.core.fields.BigForeignKey')(blank=True, related_name='user_profile', null=True, to=orm['core.CompanyProfile'])),
            ('superuser_profile', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'core', ['UserProfile'])

        # Adding model 'Customer'
        db.create_table(u'core_customer', (
            ('id', self.gf('ppars.apps.core.fields.BigAutoField')(primary_key=True)),
            ('user', self.gf('ppars.apps.core.fields.BigForeignKey')(to=orm['auth.User'])),
            ('company', self.gf('ppars.apps.core.fields.BigForeignKey')(to=orm['core.CompanyProfile'], null=True, blank=True)),
            ('first_name', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('middle_name', self.gf('django.db.models.fields.CharField')(max_length=30, null=True, blank=True)),
            ('last_name', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('primary_email', self.gf('django.db.models.fields.EmailField')(max_length=75, null=True, blank=True)),
            ('primary_email_lowercase', self.gf('django.db.models.fields.EmailField')(max_length=75, null=True, blank=True)),
            ('sc_account', self.gf('django.db.models.fields.CharField')(max_length=30, null=True, blank=True)),
            ('phone_numbers', self.gf('django.db.models.fields.CommaSeparatedIntegerField')(max_length=500, null=True)),
            ('address', self.gf('django.db.models.fields.CharField')(max_length=500, null=True, blank=True)),
            ('city', self.gf('django.db.models.fields.CharField')(max_length=30, null=True, blank=True)),
            ('state', self.gf('django.db.models.fields.CharField')(max_length=30, null=True, blank=True)),
            ('zip', self.gf('django.db.models.fields.CharField')(max_length=5, null=True, blank=True)),
            ('charge_type', self.gf('django.db.models.fields.CharField')(default='CA', max_length=2)),
            ('creditcard', self.gf('django.db.models.fields.CharField')(max_length=20, null=True, blank=True)),
            ('charge_getaway', self.gf('django.db.models.fields.CharField')(max_length=3, null=True, blank=True)),
            ('save_to_authorize', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('save_to_usaepay', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('authorize_id', self.gf('django.db.models.fields.CharField')(max_length=30, null=True, blank=True)),
            ('usaepay_customer_id', self.gf('django.db.models.fields.CharField')(max_length=30, null=True, blank=True)),
            ('price_level', self.gf('django.db.models.fields.CharField')(default='1', max_length=1)),
            ('customer_discount', self.gf('django.db.models.fields.DecimalField')(default='0', max_digits=5, decimal_places=2, blank=True)),
            ('send_status', self.gf('django.db.models.fields.CharField')(default='NO', max_length=2)),
            ('email_success', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('group_sms', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('enabled', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'core', ['Customer'])

        # Adding model 'PhoneNumber'
        db.create_table(u'core_phonenumber', (
            ('id', self.gf('ppars.apps.core.fields.BigAutoField')(primary_key=True)),
            ('company', self.gf('ppars.apps.core.fields.BigForeignKey')(to=orm['core.CompanyProfile'], null=True, blank=True)),
            ('customer', self.gf('ppars.apps.core.fields.BigForeignKey')(to=orm['core.Customer'], null=True, blank=True)),
            ('number', self.gf('django.db.models.fields.CharField')(max_length=10, null=True, blank=True)),
        ))
        db.send_create_signal(u'core', ['PhoneNumber'])

        # Adding model 'Carrier'
        db.create_table(u'core_carrier', (
            ('id', self.gf('ppars.apps.core.fields.BigAutoField')(primary_key=True)),
            ('company', self.gf('ppars.apps.core.fields.BigForeignKey')(to=orm['core.CompanyProfile'], null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('recharge_number', self.gf('django.db.models.fields.CharField')(max_length=10, null=True, blank=True)),
            ('admin_site', self.gf('django.db.models.fields.CharField')(max_length=500, null=True, blank=True)),
            ('renew_days', self.gf('django.db.models.fields.IntegerField')(max_length=3, null=True, blank=True)),
            ('renew_months', self.gf('django.db.models.fields.IntegerField')(max_length=3, null=True, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'core', ['Carrier'])

        # Adding model 'CarrierAdmin'
        db.create_table(u'core_carrieradmin', (
            ('id', self.gf('ppars.apps.core.fields.BigAutoField')(primary_key=True)),
            ('user', self.gf('ppars.apps.core.fields.BigForeignKey')(to=orm['auth.User'])),
            ('company', self.gf('ppars.apps.core.fields.BigForeignKey')(to=orm['core.CompanyProfile'], null=True, blank=True)),
            ('carrier', self.gf('ppars.apps.core.fields.BigForeignKey')(to=orm['core.Carrier'])),
            ('username', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('password', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'core', ['CarrierAdmin'])

        # Adding model 'Plan'
        db.create_table(u'core_plan', (
            ('id', self.gf('ppars.apps.core.fields.BigAutoField')(primary_key=True)),
            ('universal_plan', self.gf('ppars.apps.core.fields.BigForeignKey')(blank=True, related_name='plan', null=True, to=orm['core.Plan'])),
            ('universal', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('available', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('company', self.gf('ppars.apps.core.fields.BigForeignKey')(to=orm['core.CompanyProfile'], null=True, blank=True)),
            ('sc_sku', self.gf('django.db.models.fields.CharField')(default='', max_length=60, null=True, blank=True)),
            ('plan_id', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('api_id', self.gf('django.db.models.fields.CharField')(max_length=30, null=True, blank=True)),
            ('plan_type', self.gf('django.db.models.fields.CharField')(default='PI', max_length=2)),
            ('carrier', self.gf('ppars.apps.core.fields.BigForeignKey')(to=orm['core.Carrier'])),
            ('plan_name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('plan_cost', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('first_selling_price', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=5, decimal_places=2)),
            ('second_selling_price', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=5, decimal_places=2)),
            ('third_selling_price', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=5, decimal_places=2)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'core', ['Plan'])

        # Adding model 'PlanDiscount'
        db.create_table(u'core_plandiscount', (
            ('id', self.gf('ppars.apps.core.fields.BigAutoField')(primary_key=True)),
            ('user', self.gf('ppars.apps.core.fields.BigForeignKey')(to=orm['auth.User'])),
            ('carrier', self.gf('ppars.apps.core.fields.BigForeignKey')(to=orm['core.Carrier'])),
            ('plan', self.gf('ppars.apps.core.fields.BigForeignKey')(to=orm['core.Plan'], null=True, blank=True)),
            ('discount', self.gf('django.db.models.fields.FloatField')()),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'core', ['PlanDiscount'])

        # Adding model 'AutoRefill'
        db.create_table(u'core_autorefill', (
            ('id', self.gf('ppars.apps.core.fields.BigAutoField')(primary_key=True)),
            ('user', self.gf('ppars.apps.core.fields.BigForeignKey')(to=orm['auth.User'])),
            ('company', self.gf('ppars.apps.core.fields.BigForeignKey')(to=orm['core.CompanyProfile'], null=True, blank=True)),
            ('customer', self.gf('ppars.apps.core.fields.BigForeignKey')(to=orm['core.Customer'])),
            ('phone_number', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('plan', self.gf('ppars.apps.core.fields.BigForeignKey')(to=orm['core.Plan'])),
            ('refill_type', self.gf('django.db.models.fields.CharField')(max_length=2, blank=True)),
            ('renewal_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('renewal_end_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('renewal_interval', self.gf('django.db.models.fields.IntegerField')(max_length=3, null=True, blank=True)),
            ('last_renewal_status', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('last_renewal_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('schedule', self.gf('django.db.models.fields.CharField')(default='MN', max_length=6, null=True, blank=True)),
            ('notes', self.gf('django.db.models.fields.CharField')(max_length=500, null=True, blank=True)),
            ('trigger', self.gf('django.db.models.fields.CharField')(max_length=2, blank=True)),
            ('pin', self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True)),
            ('enabled', self.gf('django.db.models.fields.BooleanField')()),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'core', ['AutoRefill'])

        # Adding model 'Transaction'
        db.create_table(u'core_transaction', (
            ('id', self.gf('ppars.apps.core.fields.BigAutoField')(primary_key=True)),
            ('user', self.gf('ppars.apps.core.fields.BigForeignKey')(to=orm['auth.User'])),
            ('company', self.gf('ppars.apps.core.fields.BigForeignKey')(to=orm['core.CompanyProfile'], null=True, blank=True)),
            ('plan_str', self.gf('django.db.models.fields.CharField')(max_length=256, null=True)),
            ('phone_number_str', self.gf('django.db.models.fields.CharField')(max_length=10, null=True)),
            ('customer_str', self.gf('django.db.models.fields.CharField')(max_length=256, null=True)),
            ('refill_type_str', self.gf('django.db.models.fields.CharField')(max_length=256, null=True)),
            ('autorefill', self.gf('ppars.apps.core.fields.BigForeignKey')(to=orm['core.AutoRefill'], null=True, on_delete=models.SET_NULL)),
            ('locked', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('paid', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('completed', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('pin_error', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('state', self.gf('django.db.models.fields.CharField')(max_length=3)),
            ('status', self.gf('django.db.models.fields.CharField')(max_length=3, null=True)),
            ('current_step', self.gf('django.db.models.fields.CharField')(max_length=30, null=True)),
            ('adv_status', self.gf('django.db.models.fields.CharField')(max_length=500, null=True)),
            ('cost', self.gf('django.db.models.fields.FloatField')(null=True)),
            ('create_asana_ticket', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('profit', self.gf('django.db.models.fields.FloatField')(null=True)),
            ('pin', self.gf('django.db.models.fields.CharField')(max_length=256, null=True)),
            ('sellercloud_order_id', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('sellercloud_note_id', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('sellercloud_payment_id', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('retry_count', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('started', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('ended', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'core', ['Transaction'])

        # Adding model 'TransactionStep'
        db.create_table(u'core_transactionstep', (
            ('id', self.gf('ppars.apps.core.fields.BigAutoField')(primary_key=True)),
            ('transaction', self.gf('ppars.apps.core.fields.BigForeignKey')(to=orm['core.Transaction'])),
            ('operation', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('action', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('status', self.gf('django.db.models.fields.CharField')(max_length=3)),
            ('adv_status', self.gf('django.db.models.fields.CharField')(max_length=500, null=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'core', ['TransactionStep'])

        # Adding model 'CreditCardCharge'
        db.create_table(u'core_creditcardcharge', (
            ('id', self.gf('ppars.apps.core.fields.BigAutoField')(primary_key=True)),
            ('user', self.gf('ppars.apps.core.fields.BigForeignKey')(to=orm['auth.User'])),
            ('company', self.gf('ppars.apps.core.fields.BigForeignKey')(to=orm['core.CompanyProfile'], null=True, blank=True)),
            ('autorefill', self.gf('ppars.apps.core.fields.BigForeignKey')(to=orm['core.AutoRefill'])),
            ('creditcard', self.gf('django.db.models.fields.CharField')(max_length=20, null=True, blank=True)),
            ('used', self.gf('django.db.models.fields.BooleanField')()),
            ('amount', self.gf('django.db.models.fields.FloatField')(null=True)),
            ('atransaction', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('transaction', self.gf('ppars.apps.core.fields.BigOneToOneField')(blank=True, related_name='cc_charge', unique=True, null=True, to=orm['core.Transaction'])),
            ('usaepay_transaction_id', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('status', self.gf('django.db.models.fields.CharField')(max_length=3)),
            ('adv_status', self.gf('django.db.models.fields.CharField')(max_length=500, null=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'core', ['CreditCardCharge'])

        # Adding model 'UnusedPin'
        db.create_table(u'core_unusedpin', (
            ('id', self.gf('ppars.apps.core.fields.BigAutoField')(primary_key=True)),
            ('user', self.gf('ppars.apps.core.fields.BigForeignKey')(to=orm['auth.User'])),
            ('company', self.gf('ppars.apps.core.fields.BigForeignKey')(to=orm['core.CompanyProfile'], null=True, blank=True)),
            ('plan', self.gf('ppars.apps.core.fields.BigForeignKey')(to=orm['core.Plan'])),
            ('transaction', self.gf('ppars.apps.core.fields.BigForeignKey')(to=orm['core.Transaction'], null=True, blank=True)),
            ('pin', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('used', self.gf('django.db.models.fields.BooleanField')()),
            ('notes', self.gf('django.db.models.fields.CharField')(max_length=500, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'core', ['UnusedPin'])

        # Adding model 'Log'
        db.create_table(u'core_log', (
            ('id', self.gf('ppars.apps.core.fields.BigAutoField')(primary_key=True)),
            ('user', self.gf('ppars.apps.core.fields.BigForeignKey')(to=orm['auth.User'], null=True)),
            ('company', self.gf('ppars.apps.core.fields.BigForeignKey')(to=orm['core.CompanyProfile'], null=True)),
            ('note', self.gf('django.db.models.fields.CharField')(max_length=256, null=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'core', ['Log'])

        # Adding model 'SpamMessage'
        db.create_table(u'core_spammessage', (
            ('id', self.gf('ppars.apps.core.fields.BigAutoField')(primary_key=True)),
            ('company', self.gf('ppars.apps.core.fields.BigForeignKey')(to=orm['core.CompanyProfile'], null=True)),
            ('message', self.gf('django.db.models.fields.CharField')(max_length=500, null=True)),
            ('customer_type', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'core', ['SpamMessage'])

        # Adding model 'CaptchaLogs'
        db.create_table(u'core_captchalogs', (
            ('id', self.gf('ppars.apps.core.fields.BigAutoField')(primary_key=True)),
            ('user', self.gf('ppars.apps.core.fields.BigForeignKey')(to=orm['auth.User'], null=True, blank=True)),
            ('user_name', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('customer', self.gf('ppars.apps.core.fields.BigForeignKey')(to=orm['core.Customer'], null=True, on_delete=models.SET_NULL, blank=True)),
            ('customer_name', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('carrier', self.gf('ppars.apps.core.fields.BigForeignKey')(to=orm['core.Carrier'], null=True, blank=True)),
            ('carrier_name', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('plan', self.gf('ppars.apps.core.fields.BigForeignKey')(to=orm['core.Plan'], null=True, blank=True)),
            ('plan_name', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('refill_type', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('transaction', self.gf('ppars.apps.core.fields.BigForeignKey')(to=orm['core.Transaction'], null=True, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'core', ['CaptchaLogs'])

        # Adding model 'CommandLog'
        db.create_table(u'core_commandlog', (
            ('id', self.gf('ppars.apps.core.fields.BigAutoField')(primary_key=True)),
            ('command', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('message', self.gf('django.db.models.fields.TextField')()),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'core', ['CommandLog'])

        # Adding model 'ImportLog'
        db.create_table(u'core_importlog', (
            ('id', self.gf('ppars.apps.core.fields.BigAutoField')(primary_key=True)),
            ('company', self.gf('ppars.apps.core.fields.BigForeignKey')(to=orm['core.CompanyProfile'], null=True)),
            ('command', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('message', self.gf('django.db.models.fields.TextField')()),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'core', ['ImportLog'])

        # Adding model 'ConfirmDP'
        db.create_table(u'core_confirmdp', (
            ('id', self.gf('ppars.apps.core.fields.BigAutoField')(primary_key=True)),
            ('login', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('password', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('confirm', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'core', ['ConfirmDP'])


    def backwards(self, orm):
        # Deleting model 'CompanyProfile'
        db.delete_table(u'core_companyprofile')

        # Deleting model 'UserProfile'
        db.delete_table(u'core_userprofile')

        # Deleting model 'Customer'
        db.delete_table(u'core_customer')

        # Deleting model 'PhoneNumber'
        db.delete_table(u'core_phonenumber')

        # Deleting model 'Carrier'
        db.delete_table(u'core_carrier')

        # Deleting model 'CarrierAdmin'
        db.delete_table(u'core_carrieradmin')

        # Deleting model 'Plan'
        db.delete_table(u'core_plan')

        # Deleting model 'PlanDiscount'
        db.delete_table(u'core_plandiscount')

        # Deleting model 'AutoRefill'
        db.delete_table(u'core_autorefill')

        # Deleting model 'Transaction'
        db.delete_table(u'core_transaction')

        # Deleting model 'TransactionStep'
        db.delete_table(u'core_transactionstep')

        # Deleting model 'CreditCardCharge'
        db.delete_table(u'core_creditcardcharge')

        # Deleting model 'UnusedPin'
        db.delete_table(u'core_unusedpin')

        # Deleting model 'Log'
        db.delete_table(u'core_log')

        # Deleting model 'SpamMessage'
        db.delete_table(u'core_spammessage')

        # Deleting model 'CaptchaLogs'
        db.delete_table(u'core_captchalogs')

        # Deleting model 'CommandLog'
        db.delete_table(u'core_commandlog')

        # Deleting model 'ImportLog'
        db.delete_table(u'core_importlog')

        # Deleting model 'ConfirmDP'
        db.delete_table(u'core_confirmdp')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'core.autorefill': {
            'Meta': {'object_name': 'AutoRefill'},
            'company': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['core.CompanyProfile']", 'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'customer': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['core.Customer']"}),
            'enabled': ('django.db.models.fields.BooleanField', [], {}),
            'id': ('ppars.apps.core.fields.BigAutoField', [], {'primary_key': 'True'}),
            'last_renewal_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'last_renewal_status': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'notes': ('django.db.models.fields.CharField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            'phone_number': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'pin': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'plan': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['core.Plan']"}),
            'refill_type': ('django.db.models.fields.CharField', [], {'max_length': '2', 'blank': 'True'}),
            'renewal_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'renewal_end_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'renewal_interval': ('django.db.models.fields.IntegerField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'schedule': ('django.db.models.fields.CharField', [], {'default': "'MN'", 'max_length': '6', 'null': 'True', 'blank': 'True'}),
            'trigger': ('django.db.models.fields.CharField', [], {'max_length': '2', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['auth.User']"})
        },
        u'core.captchalogs': {
            'Meta': {'object_name': 'CaptchaLogs'},
            'carrier': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['core.Carrier']", 'null': 'True', 'blank': 'True'}),
            'carrier_name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'customer': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['core.Customer']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'customer_name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'id': ('ppars.apps.core.fields.BigAutoField', [], {'primary_key': 'True'}),
            'plan': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['core.Plan']", 'null': 'True', 'blank': 'True'}),
            'plan_name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'refill_type': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'transaction': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['core.Transaction']", 'null': 'True', 'blank': 'True'}),
            'user': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'user_name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        },
        u'core.carrier': {
            'Meta': {'object_name': 'Carrier'},
            'admin_site': ('django.db.models.fields.CharField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            'company': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['core.CompanyProfile']", 'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('ppars.apps.core.fields.BigAutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'recharge_number': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'renew_days': ('django.db.models.fields.IntegerField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'renew_months': ('django.db.models.fields.IntegerField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'core.carrieradmin': {
            'Meta': {'object_name': 'CarrierAdmin'},
            'carrier': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['core.Carrier']"}),
            'company': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['core.CompanyProfile']", 'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('ppars.apps.core.fields.BigAutoField', [], {'primary_key': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['auth.User']"}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'core.commandlog': {
            'Meta': {'object_name': 'CommandLog'},
            'command': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('ppars.apps.core.fields.BigAutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {})
        },
        u'core.companyprofile': {
            'Meta': {'object_name': 'CompanyProfile'},
            'asana_api_key': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'asana_project_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'asana_user': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'asana_workspace': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'authorize_api_login_id': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'authorize_precharge_days': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'authorize_transaction_key': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'cccharge_type': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'company_name': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'deathbycaptcha_count': ('django.db.models.fields.IntegerField', [], {'default': '5000', 'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'deathbycaptcha_current_count': ('django.db.models.fields.IntegerField', [], {'default': '0', 'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'deathbycaptcha_email_balance': ('django.db.models.fields.IntegerField', [], {'default': '70', 'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'deathbycaptcha_emailed': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'deathbycaptcha_pass': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'deathbycaptcha_user': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'dollar_pass': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'dollar_type': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'dollar_user': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'email_id': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True', 'blank': 'True'}),
            'email_success': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('ppars.apps.core.fields.BigAutoField', [], {'primary_key': 'True'}),
            'long_retry_interval': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'long_retry_limit': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'mandrill_email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True', 'blank': 'True'}),
            'mandrill_key': ('django.db.models.fields.CharField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            'pageplus_refillmethod': ('django.db.models.fields.CharField', [], {'default': "'TW'", 'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'pin_error': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'sc_company_id': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'sc_email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True', 'blank': 'True'}),
            'sc_password': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'short_retry_interval': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'short_retry_limit': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'superuser_profile': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'twilio_auth_token': ('django.db.models.fields.CharField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            'twilio_number': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'twilio_sid': ('django.db.models.fields.CharField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            'updated': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'usaepay_password': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'usaepay_pin': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'usaepay_source_key': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'usaepay_username': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'use_asana': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'use_sellercloud': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        u'core.confirmdp': {
            'Meta': {'object_name': 'ConfirmDP'},
            'confirm': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('ppars.apps.core.fields.BigAutoField', [], {'primary_key': 'True'}),
            'login': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '256'})
        },
        u'core.creditcardcharge': {
            'Meta': {'object_name': 'CreditCardCharge'},
            'adv_status': ('django.db.models.fields.CharField', [], {'max_length': '500', 'null': 'True'}),
            'amount': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'atransaction': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'autorefill': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['core.AutoRefill']"}),
            'company': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['core.CompanyProfile']", 'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creditcard': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'id': ('ppars.apps.core.fields.BigAutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            'transaction': ('ppars.apps.core.fields.BigOneToOneField', [], {'blank': 'True', 'related_name': "'cc_charge'", 'unique': 'True', 'null': 'True', 'to': u"orm['core.Transaction']"}),
            'usaepay_transaction_id': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'used': ('django.db.models.fields.BooleanField', [], {}),
            'user': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['auth.User']"})
        },
        u'core.customer': {
            'Meta': {'object_name': 'Customer'},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            'authorize_id': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'charge_getaway': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'charge_type': ('django.db.models.fields.CharField', [], {'default': "'CA'", 'max_length': '2'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'company': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['core.CompanyProfile']", 'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creditcard': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'customer_discount': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '5', 'decimal_places': '2', 'blank': 'True'}),
            'email_success': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'group_sms': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('ppars.apps.core.fields.BigAutoField', [], {'primary_key': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'middle_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'phone_numbers': ('django.db.models.fields.CommaSeparatedIntegerField', [], {'max_length': '500', 'null': 'True'}),
            'price_level': ('django.db.models.fields.CharField', [], {'default': "'1'", 'max_length': '1'}),
            'primary_email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True', 'blank': 'True'}),
            'primary_email_lowercase': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True', 'blank': 'True'}),
            'save_to_authorize': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'save_to_usaepay': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'sc_account': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'send_status': ('django.db.models.fields.CharField', [], {'default': "'NO'", 'max_length': '2'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'usaepay_customer_id': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'user': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['auth.User']"}),
            'zip': ('django.db.models.fields.CharField', [], {'max_length': '5', 'null': 'True', 'blank': 'True'})
        },
        u'core.importlog': {
            'Meta': {'object_name': 'ImportLog'},
            'command': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'company': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['core.CompanyProfile']", 'null': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('ppars.apps.core.fields.BigAutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {})
        },
        u'core.log': {
            'Meta': {'ordering': "['-created']", 'object_name': 'Log'},
            'company': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['core.CompanyProfile']", 'null': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('ppars.apps.core.fields.BigAutoField', [], {'primary_key': 'True'}),
            'note': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True'}),
            'user': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True'})
        },
        u'core.phonenumber': {
            'Meta': {'object_name': 'PhoneNumber'},
            'company': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['core.CompanyProfile']", 'null': 'True', 'blank': 'True'}),
            'customer': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['core.Customer']", 'null': 'True', 'blank': 'True'}),
            'id': ('ppars.apps.core.fields.BigAutoField', [], {'primary_key': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'})
        },
        u'core.plan': {
            'Meta': {'object_name': 'Plan'},
            'api_id': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'available': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'carrier': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['core.Carrier']"}),
            'company': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['core.CompanyProfile']", 'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'first_selling_price': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '5', 'decimal_places': '2'}),
            'id': ('ppars.apps.core.fields.BigAutoField', [], {'primary_key': 'True'}),
            'plan_cost': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'plan_id': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'plan_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'plan_type': ('django.db.models.fields.CharField', [], {'default': "'PI'", 'max_length': '2'}),
            'sc_sku': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '60', 'null': 'True', 'blank': 'True'}),
            'second_selling_price': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '5', 'decimal_places': '2'}),
            'third_selling_price': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '5', 'decimal_places': '2'}),
            'universal': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'universal_plan': ('ppars.apps.core.fields.BigForeignKey', [], {'blank': 'True', 'related_name': "'plan'", 'null': 'True', 'to': u"orm['core.Plan']"}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'core.plandiscount': {
            'Meta': {'object_name': 'PlanDiscount'},
            'carrier': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['core.Carrier']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'discount': ('django.db.models.fields.FloatField', [], {}),
            'id': ('ppars.apps.core.fields.BigAutoField', [], {'primary_key': 'True'}),
            'plan': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['core.Plan']", 'null': 'True', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['auth.User']"})
        },
        u'core.spammessage': {
            'Meta': {'object_name': 'SpamMessage'},
            'company': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['core.CompanyProfile']", 'null': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'customer_type': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'id': ('ppars.apps.core.fields.BigAutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.CharField', [], {'max_length': '500', 'null': 'True'})
        },
        u'core.transaction': {
            'Meta': {'object_name': 'Transaction'},
            'adv_status': ('django.db.models.fields.CharField', [], {'max_length': '500', 'null': 'True'}),
            'autorefill': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['core.AutoRefill']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            'company': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['core.CompanyProfile']", 'null': 'True', 'blank': 'True'}),
            'completed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'cost': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'create_asana_ticket': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'current_step': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True'}),
            'customer_str': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True'}),
            'ended': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'id': ('ppars.apps.core.fields.BigAutoField', [], {'primary_key': 'True'}),
            'locked': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'paid': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'phone_number_str': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True'}),
            'pin': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True'}),
            'pin_error': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'plan_str': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True'}),
            'profit': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'refill_type_str': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True'}),
            'retry_count': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'sellercloud_note_id': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'sellercloud_order_id': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'sellercloud_payment_id': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'started': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True'}),
            'user': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['auth.User']"})
        },
        u'core.transactionstep': {
            'Meta': {'object_name': 'TransactionStep'},
            'action': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'adv_status': ('django.db.models.fields.CharField', [], {'max_length': '500', 'null': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'id': ('ppars.apps.core.fields.BigAutoField', [], {'primary_key': 'True'}),
            'operation': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            'transaction': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['core.Transaction']"})
        },
        u'core.unusedpin': {
            'Meta': {'object_name': 'UnusedPin'},
            'company': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['core.CompanyProfile']", 'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('ppars.apps.core.fields.BigAutoField', [], {'primary_key': 'True'}),
            'notes': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'pin': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'plan': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['core.Plan']"}),
            'transaction': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['core.Transaction']", 'null': 'True', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'used': ('django.db.models.fields.BooleanField', [], {}),
            'user': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['auth.User']"})
        },
        u'core.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'company': ('ppars.apps.core.fields.BigForeignKey', [], {'blank': 'True', 'related_name': "'user_profile'", 'null': 'True', 'to': u"orm['core.CompanyProfile']"}),
            'id': ('ppars.apps.core.fields.BigAutoField', [], {'primary_key': 'True'}),
            'superuser_profile': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'user': ('ppars.apps.core.fields.BigOneToOneField', [], {'blank': 'True', 'related_name': "'profile'", 'unique': 'True', 'null': 'True', 'to': u"orm['auth.User']"})
        }
    }

    complete_apps = ['core']