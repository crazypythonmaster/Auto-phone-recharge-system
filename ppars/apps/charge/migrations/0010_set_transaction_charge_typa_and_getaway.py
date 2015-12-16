# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):

    depends_on = (
        ("core", "0101_auto__add_field_transaction_charge_type_name__add_field_transaction_ch"),
    )

    def forwards(self, orm):

        "Write your forwards methods here."
        # Note: Don't use "from appname.models import ModelName". 
        # Use orm.ModelName to refer to models in this application,
        # and orm['appname.ModelName'] for models in other applications.
        CHARGE_TYPE_CHOICES = (
            ('CA', 'Cash'),
            ('CC', 'Credit Card'),
        )
        CHARGE_GETAWAY_CHOICES = (
            ('A', 'Authorize'),
            ('U', 'USAePay'),
            ('RF', 'RedFinNetwork'),
            ('DP', 'DollarPhone'),
            ('CA', 'Cash'),
            ('CP', 'Cash(PrePayment)'),
        )
        for transaction_charge in orm.TransactionCharge.objects.all():
                # Just to be sure it's not fail
                if transaction_charge.transaction and transaction_charge.charge and transaction_charge.charge.customer:

                    for charge_type in CHARGE_TYPE_CHOICES:
                        if charge_type[0] == transaction_charge.charge.customer.charge_type:
                            transaction_charge.transaction.charge_type_name = charge_type[1]
                    for charge_getaway in CHARGE_GETAWAY_CHOICES:
                        if charge_getaway[0] == transaction_charge.charge.customer.charge_getaway:
                            transaction_charge.transaction.charge_getaway_name = charge_getaway[1]
                    transaction_charge.transaction.save()

    def backwards(self, orm):
        "Write your backwards methods here."

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
            'adv_status': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'amount': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '5', 'decimal_places': '2'}),
            'atransaction': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'autorefill': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['core.AutoRefill']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            'company': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['core.CompanyProfile']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            'company_informed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creditcard': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'customer': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['core.Customer']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            'id': ('ppars.apps.core.fields.BigAutoField', [], {'primary_key': 'True'}),
            'note': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': "''"}),
            'payment_getaway': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            'pin': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'pin_used': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'refund_id': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'refund_status': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'refunded': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '3', 'blank': 'True'}),
            'summ': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '5', 'decimal_places': '2'}),
            'tax': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '5', 'decimal_places': '2'}),
            'used': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'used_payment_getaways': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'})
        },
        u'charge.chargeerror': {
            'Meta': {'object_name': 'ChargeError'},
            'charge': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['charge.Charge']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'step': ('django.db.models.fields.CharField', [], {'max_length': '50'})
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
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
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
            'customer': ('ppars.apps.core.fields.BigForeignKey', [], {'related_name': "'autorefill'", 'to': u"orm['core.Customer']"}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('ppars.apps.core.fields.BigAutoField', [], {'primary_key': 'True'}),
            'last_renewal_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'last_renewal_status': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'need_buy_pins': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'need_buy_pins_count': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'notes': ('django.db.models.fields.CharField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            'phone_number': ('django.db.models.fields.CharField', [], {'max_length': '12'}),
            'pin': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'plan': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['core.Plan']"}),
            'pre_refill_sms': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'pre_refill_sms_number': ('django.db.models.fields.CharField', [], {'max_length': '12', 'null': 'True', 'blank': 'True'}),
            'refill_type': ('django.db.models.fields.CharField', [], {'default': "'FR'", 'max_length': '2'}),
            'renewal_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'renewal_end_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'renewal_interval': ('django.db.models.fields.IntegerField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'schedule': ('django.db.models.fields.CharField', [], {'default': "'MN'", 'max_length': '11', 'null': 'True', 'blank': 'True'}),
            'send_bought_pins': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'trigger': ('django.db.models.fields.CharField', [], {'max_length': '2', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True', 'on_delete': 'models.SET_NULL'})
        },
        u'core.carrier': {
            'Meta': {'object_name': 'Carrier'},
            'admin_site': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'default_time': ('django.db.models.fields.CharField', [], {'max_length': '11', 'blank': 'True'}),
            'id': ('ppars.apps.core.fields.BigAutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'recharge_number': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'renew_days': ('django.db.models.fields.IntegerField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'renew_months': ('django.db.models.fields.IntegerField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'core.companyprofile': {
            'Meta': {'object_name': 'CompanyProfile'},
            'able_change_send_pin_prerefill': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'admin_email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'asana_api_key': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'asana_project_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'asana_user': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'asana_workspace': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'authorize_api_login_id': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'authorize_precharge_days': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'authorize_transaction_key': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'auto_changing_payment_processing': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'blank_usaepay_description': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'block_duplicate_phone_number': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'block_duplicate_schedule': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'can_swipe_card_in_customer': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'can_swipe_card_in_search': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'cccharge_type': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'company_name': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'date_limit_license_expiries': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'deathbycaptcha_count': ('django.db.models.fields.IntegerField', [], {'default': '5000', 'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'deathbycaptcha_current_count': ('django.db.models.fields.IntegerField', [], {'default': '0', 'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'deathbycaptcha_email_balance': ('django.db.models.fields.IntegerField', [], {'default': '70', 'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'deathbycaptcha_emailed': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'deathbycaptcha_pass': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'deathbycaptcha_user': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'default_zip': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '10', 'blank': 'True'}),
            'deposit_amount_notification': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'dollar_pass': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'dollar_type': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'dollar_user': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'email_id': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True', 'blank': 'True'}),
            'email_success': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('ppars.apps.core.fields.BigAutoField', [], {'primary_key': 'True'}),
            'insufficient_funds_notification': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'license_expiries': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'long_retry_interval': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'long_retry_limit': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'mandrill_email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True', 'blank': 'True'}),
            'mandrill_key': ('django.db.models.fields.CharField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            'pageplus_refillmethod': ('django.db.models.fields.CharField', [], {'default': "'TW'", 'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'pin_error': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'precharge_failed_email': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'precharge_notification_type': ('django.db.models.fields.CharField', [], {'default': "'SE'", 'max_length': '2', 'blank': 'True'}),
            'redfin_password': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'redfin_username': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'redfin_vendor': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'sales_agent_email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'sc_company_id': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'sc_email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True', 'blank': 'True'}),
            'sc_password': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'schedule_limit': ('django.db.models.fields.IntegerField', [], {'default': '0', 'blank': 'True'}),
            'send_pin_prerefill': ('django.db.models.fields.CharField', [], {'default': "'NO'", 'max_length': '2'}),
            'send_status': ('django.db.models.fields.CharField', [], {'default': "'NO'", 'max_length': '2'}),
            'short_retry_interval': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'short_retry_limit': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'show_updates': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'superuser_profile': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'tax': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '7', 'decimal_places': '4'}),
            'twilio_auth_token': ('django.db.models.fields.CharField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            'twilio_number': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'twilio_sid': ('django.db.models.fields.CharField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            'unused_charge_notification': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'updated': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'usaepay_password': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'usaepay_pin': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'usaepay_source_key': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'usaepay_username': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'use_asana': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'use_redfin': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'use_sellercloud': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        u'core.customer': {
            'Meta': {'object_name': 'Customer'},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            'authorize_id': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'charge_getaway': ('django.db.models.fields.CharField', [], {'max_length': '3', 'blank': 'True'}),
            'charge_type': ('django.db.models.fields.CharField', [], {'default': "'CA'", 'max_length': '2'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'company': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['core.CompanyProfile']", 'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creditcard': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'customer_discount': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '5', 'decimal_places': '2', 'blank': 'True'}),
            'email_success_charge': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'email_success_refill': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'group_sms': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('ppars.apps.core.fields.BigAutoField', [], {'primary_key': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'middle_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'precharge_sms': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'primary_email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'primary_email_lowercase': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'redfin_cc_info_key': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'redfin_customer_key': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'sc_account': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'selling_price_level': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['price.SellingPriceLevel']"}),
            'send_pin_prerefill': ('django.db.models.fields.CharField', [], {'default': "'NO'", 'max_length': '2'}),
            'send_status': ('django.db.models.fields.CharField', [], {'default': "'NO'", 'max_length': '2'}),
            'sms_email': ('django.db.models.fields.CommaSeparatedIntegerField', [], {'max_length': '500', 'blank': 'True'}),
            'sms_gateway': ('django.db.models.fields.related.ForeignKey', [], {'default': '1', 'to': u"orm['notification.SmsEmailGateway']"}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'taxable': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'usaepay_custid': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'usaepay_customer_id': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'user': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            'zip': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        u'core.plan': {
            'Meta': {'object_name': 'Plan'},
            'api_id': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'available': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'carrier': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['core.Carrier']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('ppars.apps.core.fields.BigAutoField', [], {'primary_key': 'True'}),
            'plan_cost': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '5', 'decimal_places': '2'}),
            'plan_id': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'plan_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'plan_type': ('django.db.models.fields.CharField', [], {'default': "'PI'", 'max_length': '2'}),
            'rate_plan': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'sc_sku': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'universal': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'universal_plan': ('ppars.apps.core.fields.BigForeignKey', [], {'blank': 'True', 'related_name': "'plan'", 'null': 'True', 'to': u"orm['core.Plan']"}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'core.transaction': {
            'Meta': {'object_name': 'Transaction'},
            'adv_status': ('django.db.models.fields.CharField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            'autorefill': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['core.AutoRefill']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            'bought_pins': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'bought_pins_retry_count': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'bought_pins_retry_count_err_token': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'charge_getaway_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '50', 'blank': 'True'}),
            'charge_type_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '50', 'blank': 'True'}),
            'company': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['core.CompanyProfile']", 'null': 'True', 'blank': 'True'}),
            'completed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'cost': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '5', 'decimal_places': '2'}),
            'create_asana_ticket': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'current_step': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'customer_confirmation': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'customer_str': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True'}),
            'ended': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'execution_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'get_pin_now': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('ppars.apps.core.fields.BigAutoField', [], {'primary_key': 'True'}),
            'locked': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'need_paid': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '5', 'decimal_places': '2'}),
            'paid': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'phone_number_str': ('django.db.models.fields.CharField', [], {'max_length': '12', 'null': 'True'}),
            'pin': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'pin_error': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'plan_str': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True'}),
            'profit': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '5', 'decimal_places': '2'}),
            'refill_type_str': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True'}),
            'retry_count': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'retry_interval': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'sellercloud_note_id': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'sellercloud_order_id': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'sellercloud_payment_id': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'started': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '3', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'trigger': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '50', 'blank': 'True'}),
            'triggered_by': ('django.db.models.fields.CharField', [], {'default': "'System'", 'max_length': '128'}),
            'user': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True', 'on_delete': 'models.SET_NULL'})
        },
        u'notification.smsemailgateway': {
            'Meta': {'object_name': 'SmsEmailGateway'},
            'gateway': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'price.sellingpricelevel': {
            'Meta': {'object_name': 'SellingPriceLevel'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'level': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['charge']
    symmetrical = True
