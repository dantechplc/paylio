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
    print("✅ Cron daily_roi ran at", today)

    investments = Investment_profile.objects.filter(status='Active')

    for investment in investments:
        print(f"Processing investment {investment.id} for {investment.user}, next payout: {investment.next_payout}, today: {today}")

        if investment.next_payout and investment.next_payout <= today:
            account_user = investment.user
            account_client = Client.objects.get(user=account_user.user)

            # Get fiat portfolio (assuming USD)
            fiat_currency = FiatCurrency.objects.get(name="USD")
            portfolio = FiatPortfolio.objects.get(user=account_client, currency=fiat_currency)

            # Add interest
            interest = investment.earning
            portfolio.balance += interest
            portfolio.save(update_fields=['balance'])

            # Update investment profile
            investment.amount_earned += interest
            investment.next_payout = Transactions.get_next_payout(today)  # define this helper
            investment.save(update_fields=['amount_earned', 'next_payout'])

            # Record transaction
            trx = Transactions.objects.create(
                user=account_client,
                amount=interest,
                status='Successful',
                investment_name=investment,
                transaction_type='ROI',
                date=today,
            )

            # Send ROI email
            EmailSender.roi_success_email(
                user=account_user.user,
                amount=interest,
                balance=portfolio.balance,
                date=today,
                plan=investment,
                trx_id=trx.trx_id,
            )


from django.utils import timezone
from django.core.mail import EmailMultiAlternatives

def investment_expired_check():
    qs = Investment_profile.objects.filter(expired=False, status='Active')

    for doc in qs:
        expected_amount = doc.expected_roi
        amount_earned = doc.amount_earned
        expiry_date = doc.expiry_date

        # Condition: ROI reached OR expiry date passed
        if amount_earned >= expected_amount :
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
