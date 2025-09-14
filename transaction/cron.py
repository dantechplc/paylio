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
                    next_payment = Transactions.get_next_payout(timezone.now())
                    inv_pro.update(amount_earned=inv_amt, next_payout=next_payment)

                    # transaction

                    trx = Transactions.objects.create(
                        user=account_client,
                        amount = interest,
                        investment_name = inv_pro.investment_name,
                        status='Successful',
                        transaction_type = 'ROI',
                        date=timezone.now()

                    )
                    trx.save()

                    # ROI email
                    mail_subject = "INVESTMENT INTEREST"
                    to_email = str(investment.user)
                    EmailSender.roi_success_email(user=to_email, amount=interest,
                                                  investment_plan=inv_pro.investment_name,
                                              balance=cl.balance, date=timezone.now(),
                                            trx_id=trx.trx_id)


from django.utils import timezone
from django.core.mail import EmailMultiAlternatives

def investment_expired_check():
    qs = Investment_profile.objects.filter(expired=False, status='Active')

    for doc in qs:
        expected_amount = doc.expected_roi
        amount_earned = doc.amount_earned
        expiry_date = doc.expiry_date

        # Condition: ROI reached OR expiry date passed
        if amount_earned >= expected_amount or timezone.now().date() >= expiry_date:
            doc.expired = True
            doc.status = 'Expired'
            doc.save()

            print('Expired investment found for', doc.user)

            # Update related transaction
            Transactions.objects.filter(pk=doc.trx_id).update(status='Expired')

            # Notify admin
            email = 'chukwujidan@gmail.com'
            mail_subject = "Expired Investment"
            to_email = str(email)
            message1 = (
                f'Hello Admin. {doc.user} {doc.investment} Investment plan of '
                f'{doc.amount_invested} has expired today.'
            )
            email = EmailMultiAlternatives(mail_subject, message1, to=[to_email])
            email.attach_alternative(message1, 'text/html')
            email.content_subtype = 'html'
            email.mixed_subtype = 'related'
            email.send()
