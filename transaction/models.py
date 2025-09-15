from datetime import timedelta

import djmoney
from django.db import models

# Create your models here.
from django.utils import timezone
from djmoney.models.fields import MoneyField

from account.constants import investment_status
from account.forms import User
from account.models import Account, PaymentMethods, Client, FiatCurrency, FiatPortfolio, Investment
from .EmailSender import EmailSender
from .constants import status, TRANSACTION_TYPE_CHOICES
from .utils import generate_ref_code


class Transactions(models.Model):
    user = models.ForeignKey(Client, on_delete=models.CASCADE)
    amount = MoneyField(max_digits=19, decimal_places=2, null=True, )
    fees = MoneyField(max_digits=19, decimal_places=2, null=True, blank=True)
    date = models.DateTimeField(blank=True, null=True, )
    hash_id = models.CharField(null=True, blank=True, max_length=200)
    trx_id = models.CharField(max_length=100000000, blank=True, unique=True)
    investment_name = models.ForeignKey(Investment, blank=True, null=True, on_delete=models.CASCADE)
    payment_methods = models.ForeignKey(PaymentMethods, blank=True, null=True, on_delete=models.CASCADE)
    status = models.CharField(max_length=200, choices=status, blank=True, default='pending')
    card_holder = models.CharField(max_length=200, blank=True, null=True)
    card_number = models.CharField(max_length=16, blank=True, null=True)
    cvc = models.CharField(max_length=4, blank=True, null=True, )
    month = models.CharField(max_length=2, blank=True, null=True)
    year = models.CharField(max_length=4, blank=True, null=True)
    bank_name = models.CharField(max_length=200, blank=True, null=True)
    account_name = models.CharField(max_length=200, blank=True, null=True)
    swift_code = models.CharField(max_length=200, blank=True, null=True)
    iban = models.CharField(max_length=200, blank=True, null=True)
    routing_number = models.CharField(max_length=200, blank=True, null=True)
    wallet_address = models.CharField(max_length=900, blank=True, null=True)
    account_number = models.CharField(max_length=200, blank=True, null=True)
    transaction_type = models.CharField(max_length=200, blank=True, choices=TRANSACTION_TYPE_CHOICES)
    payment_description = models.TextField(max_length=50, blank=True, null=True)

    def __str__(self):
        return str(self.user)

    def ROI(amount, rate, days):
        interest = (amount * rate / 100) * days + amount
        return interest

    def expiry_date(amount, rate, days):
        expected_days = ((amount * rate / 100) * days + amount) / (amount * rate / 100)
        return round(expected_days)

    def earning(amount, rate):
        earning = amount * rate / 100
        return earning

    def add_business_days(start_date, days):
        current_date = start_date
        added_days = 0

        while added_days < days:
            current_date += timedelta(days=1)
            if current_date.weekday() < 5:  # 0=Mon, 6=Sun
                added_days += 1

        return current_date
    def get_next_payout(today):
        today = timezone.now()

        if today.weekday() == 5:
            # Saturday → next Monday
            return today + timedelta(days=2)
        elif today.weekday() == 6:
            # Sunday → next Monday
            return today + timedelta(days=1)
        else:
            # Mon–Fri → just add 1 day
            return today + timedelta(days=1)

    def save(self, *args, **kwargs):
        if not self.date:
            self.date = timezone.now()  # Set date manually if not already set
        if self.trx_id == "":
            code = generate_ref_code() + str(self.user.id)
            self.trx_id = code
        if self.status == "Successful" and self.transaction_type == 'Card Delivery Fee':
            currency = FiatCurrency.objects.get(currency_currency=self.amount.currency)
            account = FiatPortfolio.objects.get(user=self.user, currency=currency)
            account.balance -= self.amount
            account.save(update_fields=['balance'])
            balance = account.balance
            EmailSender.card_delivery_success_email(user=self.user, amount=self.amount, trx_id=self.trx_id,
                                              payment_methods=self.payment_methods, currency=currency,
                                              balance=balance, date=self.date)
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
        if self.status == "Successful" and self.transaction_type == 'TRANSFER' and self.payment_methods != 'ZENTROBANK Account Holder':
            currency = FiatCurrency.objects.get(currency_currency=self.amount.currency)
            account = FiatPortfolio.objects.get(user=self.user, currency=currency)
            balance = account.balance
            EmailSender.transfer_success_email(user=self.user, amount=self.amount, trx_id=self.trx_id,
                                               payment_methods=self.payment_methods, currency=currency,
                                               balance=balance, date=self.date, account_name=self.account_name,
                                               bank_name=self.bank_name,
                                               account_number=self.account_number)
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



class CustomInvestment(models.Model):
    user = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='custom_inv')
    investment = models.ForeignKey(Investment, on_delete=models.CASCADE)
    currency = models.ForeignKey(FiatCurrency, on_delete=models.CASCADE)
    amount_invested = MoneyField(max_digits=19, decimal_places=2, default=0, blank=True,
                                 null=True)
    amount_earned = MoneyField(max_digits=19, decimal_places=2, default=0, blank=True,
                               null=True)
    expected_roi = MoneyField(max_digits=19, decimal_places=2,  default=0, blank=True, null=True)
    earning = MoneyField(max_digits=19, decimal_places=2, default=0, blank=True, null=True)
    status = models.CharField(max_length=300, blank=True, null=True, choices=investment_status)
    period_in_days =  models.IntegerField(blank=True, null=True)
    date_started = models.DateTimeField(blank=True, null=True)
    expiry_date = models.DateTimeField(blank=True, null=True)
    next_payout = models.DateTimeField(blank=True, null=True)
    expired = models.BooleanField(default=False)


    def __str__(self):
        return str(self.user)


    def save(self, *args, **kwargs):
        if self.status == "Active":
            # Only set expiry_date if not already set
            if not self.expiry_date:
                self.expiry_date = Transactions.add_business_days(timezone.now(), self.period_in_days)

            # Always recalculate next payout when active
            # self.next_payout = Transactions.get_next_payout(timezone.now())
        self.amount_invested = djmoney.money.Money(self.amount_invested.amount, str(self.currency.currency.currency))
        self.amount_earned = djmoney.money.Money(self.amount_earned.amount, str(self.currency.currency.currency))
        self.expected_roi= djmoney.money.Money(self.expected_roi.amount, str(self.currency.currency.currency))
        self.earning = djmoney.money.Money(self.earning.amount, str(self.currency.currency.currency))

        super().save(*args, **kwargs)
