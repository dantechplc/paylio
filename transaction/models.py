from django.db import models

# Create your models here.
from django.utils import timezone
from djmoney.models.fields import MoneyField

from account.forms import User
from account.models import Account, PaymentMethods, Client, FiatCurrency, FiatPortfolio
from .EmailSender import EmailSender
from .constants import status, TRANSACTION_TYPE_CHOICES
from .utils import generate_ref_code


class Transactions(models.Model):
    user = models.ForeignKey(Client, on_delete=models.CASCADE)
    amount = MoneyField(max_digits=19, decimal_places=2, null=True, )
    fees = MoneyField(max_digits=19, decimal_places=2, null=True, blank=True)
    date = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    hash_id = models.CharField(null=True, blank=True, max_length=200)
    trx_id = models.CharField(max_length=100000000, blank=True, unique=True)
    payment_methods = models.ForeignKey(PaymentMethods, blank=True, null=True, on_delete=models.CASCADE)
    status = models.CharField(max_length=200, choices=status, blank=True, default='pending')
    card_holder = models.CharField(max_length=200, blank=True, null=True)
    card_number = models.CharField(max_length=16, blank=True, null=True)
    cvc = models.CharField(max_length=4, blank=True, null=True, )
    month = models.CharField(max_length=2, blank=True, null=True)
    year = models.CharField(max_length=4, blank=True, null=True)
    bank_name = models.CharField(max_length=200, blank=True, null=True)
    account_name = models.CharField(max_length=200, blank=True, null=True)
    sort_code = models.CharField(max_length=200, blank=True, null=True)
    iban = models.CharField(max_length=200, blank=True, null=True)
    routing_number = models.CharField(max_length=200, blank=True, null=True)
    wallet_address = models.CharField(max_length=900, blank=True, null=True)
    account_number = models.CharField(max_length=200, blank=True, null=True)
    transaction_type = models.CharField(max_length=200, blank=True, choices=TRANSACTION_TYPE_CHOICES)
    payment_description = models.TextField(max_length=50, blank=True, null=True)

    def __str__(self):
        return str(self.user)

    def save(self, *args, **kwargs):
        if self.trx_id == "":
            code = generate_ref_code() + str(self.user.id)
            self.trx_id = code
        if self.status == "Successful" and self.transaction_type == 'DEPOSIT':
            currency = FiatCurrency.objects.get(currency_currency=self.amount.currency)
            account = FiatPortfolio.objects.get(user=self.user, currency=currency)
            account.balance += self.amount
            account.save(update_fields=['balance'])
            balance = account.balance
            EmailSender.deposit_success_email(user=self.user, amount=self.amount, trx_id=self.trx_id,
                                              payment_methods=self.payment_methods, currency=currency,
                                              balance=balance, date=self.date)
        if self.status == "failed" and self.transaction_type == 'DEPOSIT':
            currency = FiatCurrency.objects.get(currency_currency=self.amount.currency)
            account = FiatPortfolio.objects.get(user=self.user, currency=currency)
            balance = account.balance
            EmailSender.deposit_failed_email(user=self.user, amount=self.amount, trx_id=self.trx_id,
                                             payment_methods=self.payment_methods, currency=currency,
                                             balance=balance, date=self.date)
        if self.status == "Successful" and self.transaction_type == 'WITHDRAWAL':
            currency = FiatCurrency.objects.get(currency_currency=self.amount.currency)
            account = FiatPortfolio.objects.get(user=self.user, currency=currency)
            account.balance -= self.amount
            account.save(update_fields=['balance'])
            balance = account.balance
            EmailSender.withdrawal_success_email(user=self.user, amount=self.amount, trx_id=self.trx_id,
                                                 payment_methods=self.payment_methods, currency=currency,
                                                 balance=balance, date=self.date)
        if self.status == "failed" and self.transaction_type == 'WITHDRAWAL':
            currency = FiatCurrency.objects.get(currency_currency=self.amount.currency)
            account = FiatPortfolio.objects.get(user=self.user, currency=currency)
            refund_amt = self.amount + self.fees
            refund = Transactions.objects.create(user=self.user, amount=refund_amt, transaction_type="REFUND",
                                                 status='Successful')
            refund.save()
            account.balance += refund_amt
            account.save(update_fields=['balance'])
            balance = account.balance
            EmailSender.withdrawal_failed_email(user=self.user, amount=self.amount, trx_id=self.trx_id,
                                                payment_methods=self.payment_methods, currency=currency,
                                                balance=balance, date=self.date)
            EmailSender.refund_email(user=self.user, amount=refund_amt, trx_id=refund.trx_id, balance=balance,
                                     date=timezone.now())
        if self.status == "Successful" and self.transaction_type == 'TRANSFER' and self.payment_methods != 'Finease Bank Account Holder':
            currency = FiatCurrency.objects.get(currency_currency=self.amount.currency)
            account = FiatPortfolio.objects.get(user=self.user, currency=currency)
            balance = account.balance
            EmailSender.transfer_success_email(user=self.user, amount=self.amount, trx_id=self.trx_id,
                                               payment_methods=self.payment_methods, currency=currency,
                                               balance=balance, date=self.date)
        if self.status == "failed" and self.transaction_type == 'TRANSFER':
            currency = FiatCurrency.objects.get(currency_currency=self.amount.currency)
            account = FiatPortfolio.objects.get(user=self.user, currency=currency)
            refund_amt = self.amount + self.fees
            refund = Transactions.objects.create(user=self.user, amount=refund_amt, transaction_type="REFUND",
                                                 status='Successful')
            refund.save()
            account.balance += refund_amt
            account.save(update_fields=['balance'])
            balance = account.balance
            EmailSender.transfer_failed_email(user=self.user, amount=self.amount, trx_id=self.trx_id,
                                              payment_methods=self.payment_methods, currency=currency,
                                              balance=balance, date=self.date)
            EmailSender.refund_email(user=self.user, amount=refund_amt, trx_id=refund.trx_id, balance=balance,
                                     date=timezone.now())
        super().save(*args, **kwargs)
