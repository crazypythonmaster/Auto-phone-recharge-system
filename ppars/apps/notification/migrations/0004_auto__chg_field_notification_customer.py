# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'Notification.customer'
        db.alter_column(u'notification_notification', 'customer_id', self.gf('ppars.apps.core.fields.BigForeignKey')(to=orm['core.Customer'], null=True))

    def backwards(self, orm):

        # User chose to not deal with backwards NULL issues for 'Notification.customer'
        # raise RuntimeError("Cannot reverse this migration. 'Notification.customer' and its values cannot be restored.")
        
        # The following code is provided here to aid in writing a correct migration
        # Changing field 'Notification.customer'
        db.alter_column(u'notification_notification', 'customer_id', self.gf('ppars.apps.core.fields.BigForeignKey')(to=orm['core.Customer']))

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
            'save_to_local': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'save_to_usaepay': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'sc_account': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'selling_price_level': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['price.SellingPriceLevel']"}),
            'send_status': ('django.db.models.fields.CharField', [], {'default': "'NO'", 'max_length': '2'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'taxable': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'usaepay_custid': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'usaepay_customer_id': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'user': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['auth.User']"}),
            'zip': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        u'notification.notification': {
            'Meta': {'object_name': 'Notification'},
            'adv_status': ('django.db.models.fields.TextField', [], {}),
            'body': ('django.db.models.fields.TextField', [], {}),
            'company': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['core.CompanyProfile']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'customer': ('ppars.apps.core.fields.BigForeignKey', [], {'to': u"orm['core.Customer']", 'null': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'phone_number': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'send_with': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True'}),
            'subject': ('django.db.models.fields.TextField', [], {})
        },
        u'price.sellingpricelevel': {
            'Meta': {'object_name': 'SellingPriceLevel'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'level': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['notification']