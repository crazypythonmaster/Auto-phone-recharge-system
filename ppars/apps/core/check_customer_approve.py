from ppars.apps.core.models import Transaction


class CheckCustomerApprove:

    def __init__(self, id):
        self.transaction = Transaction.objects.get(id=id)

    def main(self):
        if self.transaction.autorefill.pre_refill_sms:
            if not self.transaction.customer_confirmation:
                if not self.transaction.check_sms_confirmation():
                    self.transaction.state = Transaction.COMPLETED
                    self.transaction.status = Transaction.ERROR
                    self.transaction.save()
                    return self.transaction
                else:
                    self.transaction.customer_confirmation = True
        else:
            self.transaction.add_transaction_step(
                'check sms confirmation',
                'check',
                Transaction.SUCCESS,
                'Transaction doesn`t need confirmed via SMS')
        self.transaction.status = Transaction.SUCCESS
        self.transaction.save()
        return self.transaction
