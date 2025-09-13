from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.utils import timezone
from account.models import *
from djmoney.money import Money


import datetime
import djmoney
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from account.models import Investment_profile, FiatCurrency, FiatPortfolio
from transaction.EmailSender import EmailSender
from transaction.models import Transactions


def daily_roi():
    today = timezone.now()
    investments = Investment_profile.objects.filter(status='Active')
    if investments is not None:
        for investment in investments:
            date = investment.next_payout
            if date <= today:
                accounts = Investment_profile.objects.filter(user=investment.user, status='Active')
                for account in accounts:
                    fiat_currency = FiatCurrency.objects.get(currency=Money(0, 'USD'))

                    interest = account.earning
                    account_user = User.objects.get(email=account)
                    account_client = Client.objects.get(user=account_user)
                    client_acct = FiatPortfolio.objects.get(user=account_client, currency=fiat_currency)
                    bal = client_acct.balance
                    new_bal = bal + interest
                    cl = FiatPortfolio.objects.get(user=account_client, currency=fiat_currency)
                    cl.save(update_fields=['balance'])

                    # Investment Profile
                    inv_pro = Investment_profile.objects.filter(status="Active", user=investment.user)
                    inv_amt = account.amount_earned + interest
                    next_payment = timezone.now() + relativedelta(days=1)
                    inv_pro.update(amount_earned=inv_amt, next_payout=next_payment)

                    # ROI email
                    mail_subject = "INVESTMENT INTEREST"
                    to_email = str(investment.user)
                    EmailSender.deposit_success_email(user=to_email, amount=interest,
                                               currency=fiat_currency,
                                              balance=cl.balance, date=timezone.now())



def investment_expired_check():

    qs = Investment_profile.objects.filter(expired=False, status='Active')
    for doc in qs:
        expected_amount = doc.expected_roi
        amount_earned = doc.amount_earned
        if amount_earned >= expected_amount:
            doc.expired = True
            doc.status = 'Expired'
            doc.save()
            print('Expired investment found for ', doc.user)
            trx = Transactions.objects.filter(pk=doc.trx_id)
            trx.update(status='Expired')
            email = 'chukwujidan@gmail.com'
            # message =
            mail_subject = "Expired Investment"
            to_email = str(email)
            message1 = f'Hello Admin. {doc.user} {doc.investment} Investment plan of {doc.amount_invested} expired ' \
                       f'today. '
            email = EmailMultiAlternatives(
                mail_subject, message1, to=[to_email]
            )
            email.attach_alternative(message1, 'text/html')
            email.content_subtype = 'html'
            email.mixed_subtype = 'related'
            email.send()