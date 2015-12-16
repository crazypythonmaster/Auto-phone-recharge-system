# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Charge'
        db.create_table(u'charge_charge', (
            ('id', self.gf('ppars.apps.core.fields.BigAutoField')(primary_key=True)),
            ('company', self.gf('ppars.apps.core.fields.BigForeignKey')(to=orm['core.CompanyProfile'], null=True, blank=True)),
            ('autorefill', self.gf('ppars.apps.core.fields.BigForeignKey')(to=orm['core.AutoRefill'])),
            ('customer', self.gf('ppars.apps.core.fields.BigForeignKey')(to=orm['core.Customer'], null=True)),
            ('creditcard', self.gf('django.db.models.fields.CharField')(max_length=20, null=True, blank=True)),
            ('used', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('amount', self.gf('django.db.models.fields.DecimalField')(default='0', max_digits=5, decimal_places=2)),
            ('tax', self.gf('django.db.models.fields.DecimalField')(default='0', max_digits=5, decimal_places=2)),
            ('summ', self.gf('django.db.models.fields.DecimalField')(default='0', max_digits=5, decimal_places=2)),
            ('atransaction', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('payment_getaway', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('status', self.gf('django.db.models.fields.CharField')(max_length=3)),
            ('refund_id', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('refund_status', self.gf('django.db.models.fields.CharField')(max_length=1, blank=True)),
            ('refunded', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('adv_status', self.gf('django.db.models.fields.CharField')(max_length=500, null=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal(u'charge', ['Charge'])

        # Adding model 'TransactionCharge'
        db.create_table(u'charge_transactioncharge', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('charge', self.gf('ppars.apps.core.fields.BigForeignKey')(to=orm['charge.Charge'])),
            ('transaction', self.gf('ppars.apps.core.fields.BigForeignKey')(to=orm['core.Transaction'], null=True)),
            ('amount', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=5, decimal_places=2)),
            ('created', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal(u'charge', ['TransactionCharge'])

        # Adding model 'ChargeStep'
        db.create_table(u'charge_chargestep', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('charge', self.gf('ppars.apps.core.fields.BigForeignKey')(to=orm['charge.Charge'])),
            ('action', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('status', self.gf('django.db.models.fields.CharField')(max_length=3)),
            ('adv_status', self.gf('django.db.models.fields.CharField')(max_length=500, null=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'charge', ['ChargeStep'])


    def backwards(self, orm):
        # Deleting model 'Charge'
        db.delete_table(u'charge_charge')

        # Deleting model 'TransactionCharge'
        db.delete_table(u'charge_transactioncharge')

        # Deleting model 'ChargeStep'
        db.delete_table(u'charge_chargestep')


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
        u'charge.charge': {
            'Meta': {'object_name': 'Charge'},
            'adv_status': ('django.db.models.fields.CharField', [], {'max_length': '500', 'null': 'True'}),
            'amount': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '5', 'decimal_places': '2'}),
            'atransaction': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'autorefill': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['core.AutoRefill']"}),
            'company': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['core.CompanyProfile']", 'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            'creditcard': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'customer': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['core.Customer']", 'null': 'True'}),
            'id': ('ppars.apps.core.fields.BigAutoField', [], {'primary_key': 'True'}),
            'payment_getaway': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'refund_id': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'refund_status': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'refunded': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            'summ': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '5', 'decimal_places': '2'}),
            'tax': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '5', 'decimal_places': '2'}),
            'used': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        u'charge.chargestep': {
            'Meta': {'object_name': 'ChargeStep'},
            'action': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'adv_status': ('django.db.models.fields.CharField', [], {'max_length': '500', 'null': 'True'}),
            'charge': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['charge.Charge']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '3'})
        },
        u'charge.transactioncharge': {
            'Meta': {'object_name': 'TransactionCharge'},
            'amount': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '5', 'decimal_places': '2'}),
            'charge': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['charge.Charge']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'transaction': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['core.Transaction']", 'null': 'True'})
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
            'pre_refill_sms': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
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
            'block_duplicate_schedule': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
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
            'precharge_failed_email': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'sc_company_id': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'sc_email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True', 'blank': 'True'}),
            'sc_password': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'short_retry_interval': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'short_retry_limit': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'superuser_profile': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'tax': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '5', 'decimal_places': '2'}),
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
            'amount': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '5', 'decimal_places': '2'}),
            'amount2': ('django.db.models.fields.FloatField', [], {}),
            'atransaction': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'autorefill': ('ppars.apps.core.fields.BigForeignKey', [], {'related_name': "'core_autorefill'", 'to': u"orm['core.AutoRefill']"}),
            'company': ('ppars.apps.core.fields.BigForeignKey', [], {'blank': 'True', 'related_name': "'core_company'", 'null': 'True', 'to': u"orm['core.CompanyProfile']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creditcard': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'customer': ('ppars.apps.core.fields.BigForeignKey', [], {'related_name': "'core_customer'", 'null': 'True', 'to': u"orm['core.Customer']"}),
            'id': ('ppars.apps.core.fields.BigAutoField', [], {'primary_key': 'True'}),
            'payment_getaway': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'refund_id': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'refund_status': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'refunded': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            'summ': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '5', 'decimal_places': '2'}),
            'tax': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '5', 'decimal_places': '2'}),
            'used': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'user': ('ppars.apps.core.fields.BigForeignKey', [], {'related_name': "'core_user'", 'to': u"orm['auth.User']"})
        },
        u'core.customer': {
            'Meta': {'object_name': 'Customer'},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            'authorize_id': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'charge_getaway': ('django.db.models.fields.CharField', [], {'default': "'A'", 'max_length': '3', 'blank': 'True'}),
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
            'primary_email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True', 'blank': 'True'}),
            'primary_email_lowercase': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True', 'blank': 'True'}),
            'save_to_authorize': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'save_to_usaepay': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'sc_account': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'selling_price_level': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['price.SellingPriceLevel']", 'null': 'True'}),
            'send_status': ('django.db.models.fields.CharField', [], {'default': "'NO'", 'max_length': '2'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'taxable': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
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
        u'core.pinreport': {
            'Meta': {'object_name': 'PinReport'},
            'company': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['core.CompanyProfile']", 'null': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'report': ('django.db.models.fields.TextField', [], {})
        },
        u'core.plan': {
            'Meta': {'object_name': 'Plan'},
            'api_id': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'available': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'carrier': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['core.Carrier']"}),
            'company': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['core.CompanyProfile']", 'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('ppars.apps.core.fields.BigAutoField', [], {'primary_key': 'True'}),
            'plan_cost': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '5', 'decimal_places': '2'}),
            'plan_id': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'plan_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'plan_type': ('django.db.models.fields.CharField', [], {'default': "'PI'", 'max_length': '2'}),
            'sc_sku': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '60', 'null': 'True', 'blank': 'True'}),
            'universal': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'universal_plan': ('ppars.apps.core.fields.BigForeignKey', [], {'blank': 'True', 'related_name': "'plan'", 'null': 'True', 'to': u"orm['core.Plan']"}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'core.plandiscount': {
            'Meta': {'object_name': 'PlanDiscount'},
            'carrier': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['core.Carrier']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'discount': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '5', 'decimal_places': '2'}),
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
            'adv_status': ('django.db.models.fields.CharField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            'autorefill': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['core.AutoRefill']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            'company': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['core.CompanyProfile']", 'null': 'True', 'blank': 'True'}),
            'completed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'cost': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '5', 'decimal_places': '2'}),
            'create_asana_ticket': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'current_step': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'customer_str': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True'}),
            'ended': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'id': ('ppars.apps.core.fields.BigAutoField', [], {'primary_key': 'True'}),
            'locked': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'need_paid': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '5', 'decimal_places': '2'}),
            'paid': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'phone_number_str': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True'}),
            'pin': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'pin_error': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'plan_str': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True'}),
            'profit': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '5', 'decimal_places': '2'}),
            'refill_type_str': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True'}),
            'retry_count': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sellercloud_note_id': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'sellercloud_order_id': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'sellercloud_payment_id': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'started': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '3', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'user': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['auth.User']"})
        },
        u'core.transactioncharge': {
            'Meta': {'object_name': 'TransactionCharge'},
            'amount': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '5', 'decimal_places': '2'}),
            'charge': ('ppars.apps.core.fields.BigForeignKey', [], {'related_name': "'core_creditcardcharge'", 'to': u"orm['core.CreditCardCharge']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'transaction': ('ppars.apps.core.fields.BigForeignKey', [], {'related_name': "'core_transaction'", 'null': 'True', 'to': u"orm['core.Transaction']"})
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
        },
        u'price.sellingpricelevel': {
            'Meta': {'object_name': 'SellingPriceLevel'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'level': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['core', 'charge']