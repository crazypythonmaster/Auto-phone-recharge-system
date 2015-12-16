from django.contrib.auth.models import User
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from ppars.apps.core.models import Plan, UserProfile, Customer,\
    CompanyProfile, PhoneNumber, Log, \
    Carrier, CarrierAdmin, PlanDiscount, AutoRefill, \
    Transaction, TransactionStep, UnusedPin, \
    CaptchaLogs, CommandLog, ImportLog


class UserResource(resources.ModelResource):

    class Meta:
        model = User


class UserAdmin(ImportExportModelAdmin):
    resource_class = UserResource


class CompanyProfileResource(resources.ModelResource):

    class Meta:
        model = CompanyProfile


class CompanyProfileAdmin(ImportExportModelAdmin):
    resource_class = CompanyProfileResource


class UserProfileResource(resources.ModelResource):

    class Meta:
        model = UserProfile


class UserProfileAdmin(ImportExportModelAdmin):
    resource_class = UserProfileResource


class CustomerResource(resources.ModelResource):

    class Meta:
        model = Customer


class CustomerAdmin(ImportExportModelAdmin):
    resource_class = CustomerResource


class PhoneNumberResource(resources.ModelResource):

    class Meta:
        model = PhoneNumber


class PhoneNumberAdmin(ImportExportModelAdmin):
    resource_class = PhoneNumberResource


class CarrierResource(resources.ModelResource):

    class Meta:
        model = Carrier


class CarrierResourceAdmin(ImportExportModelAdmin):
    resource_class = CarrierResource


class CarrierAdminResource(resources.ModelResource):

    class Meta:
        model = CarrierAdmin


class CarrierAdminResourceAdmin(ImportExportModelAdmin):
    resource_class = CarrierAdminResource


class PlanResource(resources.ModelResource):

    class Meta:
        model = Plan


class PlanAdmin(ImportExportModelAdmin):
    resource_class = PlanResource


class PlanDiscountResource(resources.ModelResource):

    class Meta:
        model = PlanDiscount


class PlanDiscountAdmin(ImportExportModelAdmin):
    resource_class = PlanDiscountResource


class AutoRefillResource(resources.ModelResource):

    class Meta:
        model = AutoRefill


class AutoRefillResourceAdmin(ImportExportModelAdmin):
    resource_class = AutoRefillResource


class TransactionResource(resources.ModelResource):

    class Meta:
        model = Transaction


class TransactionAdmin(ImportExportModelAdmin):
    resource_class = TransactionResource


class TransactionStepResource(resources.ModelResource):

    class Meta:
        model = TransactionStep


class TransactionStepAdmin(ImportExportModelAdmin):
    resource_class = TransactionStepResource





class UnusedPinResource(resources.ModelResource):

    class Meta:
        model = UnusedPin


class UnusedPinAdmin(ImportExportModelAdmin):
    resource_class = UnusedPinResource


class LogResource(resources.ModelResource):

    class Meta:
        model = Log


class LogAdmin(ImportExportModelAdmin):
    resource_class = LogResource


class CaptchaLogsResource(resources.ModelResource):

    class Meta:
        model = CaptchaLogs


class CaptchaLogsAdmin(ImportExportModelAdmin):
    resource_class = CaptchaLogsResource


class CommandLogResource(resources.ModelResource):

    class Meta:
        model = CommandLog


class CommandLogAdmin(ImportExportModelAdmin):
    resource_class = CommandLogResource


class ImportLogResource(resources.ModelResource):

    class Meta:
        model = ImportLog


class ImportLogAdmin(ImportExportModelAdmin):
    resource_class = ImportLogResource