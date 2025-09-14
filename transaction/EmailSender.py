import datetime

from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

from frontend.models import CompanyProfile

from account.models import Account, Joint_Account_KYC, User, Client


class EmailSender:

    def __init__(self):
        pass

    def deposit_request_email(email_address, amount, client, payment_method):
        mail_subject = 'Deposit Request'
        to_email = email_address
        message = f"Hello Admin. \n Client with this email {client}, sent a deposit request of {amount} via {payment_method}. " \
                  f"\n Kindly verify the deposit request.  "
        email = EmailMultiAlternatives(
            mail_subject, message, to=[to_email]
        )
        email.send()

    def withdrawal_request_email(email_address, amount, client, payment_method):
        mail_subject = 'Deposit Request'
        to_email = email_address
        message = f"Hello Admin. \n Client with this email {client}, sent a withdrawal request of {amount} via {payment_method}. " \
                  f"\n Kindly verify the withdrawal request.  "
        email = EmailMultiAlternatives(
            mail_subject, message, to=[to_email]
        )
        email.send()

    def transfer_email(email_address, user, trx_id, amount, account, sender, balance, date):
        mail_subject = 'CREDIT ALERT'
        to_email = email_address
        message = render_to_string(
            "transaction/dsh/emails/transfer_credit_success.html",
            {
                "name": user,
                "amount": amount,
                'sender': sender,
                'account': account,
                'balance': balance,
                'trx_id': trx_id,
                'date': date,
                "domain": 'ZENTROBANK.com',
                "company": CompanyProfile.objects.get(id=settings.COMPANY_ID)
            },
        )
        user = User.objects.get(email=email_address)
        client = Client.objects.get(user=user)
        referral_account = Account.objects.get(user=client)
        verified_users = Joint_Account_KYC.get_verified_users_by_referral(referral_account)
        if verified_users:
            to_email = verified_users
            email = EmailMultiAlternatives(
                mail_subject, message, to=to_email
            )
            email.attach_alternative(message, 'text/html')
            email.content_subtype = 'html'
            email.mixed_subtype = 'related'
            email.send()
        else:
            to_email = str(email_address)
            email = EmailMultiAlternatives(
                mail_subject, message, to=[to_email]
            )
            email.attach_alternative(message, 'text/html')
            email.content_subtype = 'html'
            email.mixed_subtype = 'related'
            email.send()

    def transfer_request(email_address, amount, account, method):
        mail_subject = 'Transfer Request'
        to_email = email_address
        message = f"Hello Admin ." \
                  f"\n {email_address} requested for {account} transfer via {method} " \
                  f"\n Amount : {amount}"
        email = EmailMultiAlternatives(
            mail_subject, message, to=[to_email]
        )
        email.send()

    def kyc_email_sender(*args, **kwargs):
        email_subject = 'KYC Verification'
        email_message = 'Verification process just got started by ' + str(kwargs.get('user')) + \
                        ' proceed to the admin dashboard to confirm details'
        to_email = str(kwargs.get('email'))
        email = EmailMultiAlternatives(
            email_subject, email_message, to=[to_email]
        )
        email.send()

    @classmethod
    def exchange_detail(cls, email_address, name, amount, fiat_from, fiat_to, fee, balance, ex_amt, ex_bal, date):
        email_subject = 'Exchange Successful'
        message = render_to_string(
            "transaction/dsh/emails/exchange_email.html",
            {
                "name": name,
                'amount': amount,
                'fiat_from': fiat_from,
                'fiat_to': fiat_to,
                'fee': fee,
                'ex_amt': ex_amt,
                'ex_bal': ex_bal,
                'balance': balance,
                "domain": 'ZENTROBANK.com',
                'date': date,
                "company": CompanyProfile.objects.get(id=settings.COMPANY_ID)
            },
        )
        to_email = str(email_address)
        email = EmailMultiAlternatives(
            email_subject, message, to=[to_email]
        )
        email.attach_alternative(message, 'text/html')
        email.content_subtype = 'html'
        email.mixed_subtype = 'related'
        email.send()



    @classmethod
    def deposit_success_email(cls, user, amount, trx_id, payment_methods, balance, *args, **kwargs):
        currency = kwargs.get('currency', )
        date = kwargs.get('date')
        mail_subject = 'Deposit Successful'
        message = render_to_string(
            "transaction/dsh/emails/deposit_success_email.html",
            {
                "name": user.name,
                "domain": 'ZENTROBANK.com',
                'amount': amount,
                'trx_id': trx_id,
                'payment_method': payment_methods,
                'date': date,
                'balance': balance,
                "company": CompanyProfile.objects.get(id=settings.COMPANY_ID)
            },
        )
        user = User.objects.get(email=user)
        client = Client.objects.get(user=user)
        referral_account = Account.objects.get(user=client)
        verified_users = Joint_Account_KYC.get_verified_users_by_referral(referral_account)
        if verified_users:
            to_email = verified_users
            email = EmailMultiAlternatives(
                mail_subject, message, to=to_email
            )
            email.attach_alternative(message, 'text/html')
            email.content_subtype = 'html'
            email.mixed_subtype = 'related'
            email.send()
        else:
            to_email = str(user)
            email = EmailMultiAlternatives(
                mail_subject, message, to=[to_email]
            )
            email.attach_alternative(message, 'text/html')
            email.content_subtype = 'html'
            email.mixed_subtype = 'related'
            email.send()

    @classmethod
    def deposit_failed_email(cls, user, amount, trx_id, payment_methods, currency, balance, date, *args, **kwargs):
        currency = kwargs.get('currency', )
        mail_subject = 'Deposit Declined'
        message = render_to_string(
            "transaction/dsh/emails/deposit_failed_email.html",
            {
                "name": user.name,
                "domain": 'ZENTROBANK.com',
                'amount': amount,
                'trx_id': trx_id,
                'payment_method': payment_methods,
                'date': date,
                'balance': balance,
                "company": CompanyProfile.objects.get(id=settings.COMPANY_ID)
            },
        )
        user = User.objects.get(email=user)
        client = Client.objects.get(user=user)
        referral_account = Account.objects.get(user=client)
        verified_users = Joint_Account_KYC.get_verified_users_by_referral(referral_account)
        if verified_users:
            to_email = verified_users
            email = EmailMultiAlternatives(
                mail_subject, message, to=to_email
            )
            email.attach_alternative(message, 'text/html')
            email.content_subtype = 'html'
            email.mixed_subtype = 'related'
            email.send()
        else:
            to_email = str(user)
            email = EmailMultiAlternatives(
                mail_subject, message, to=[to_email]
            )
            email.attach_alternative(message, 'text/html')
            email.content_subtype = 'html'
            email.mixed_subtype = 'related'
            email.send()

    @classmethod
    def withdrawal_success_email(cls, user, amount, trx_id, payment_methods, currency, balance, date, ):
        mail_subject = 'Withdrawal Successful'
        message = render_to_string(
            "transaction/dsh/emails/withdrawal_success_email.html",
            {
                "name": user.name,
                "domain": 'ZENTROBANK.com',
                'amount': amount,
                'trx_id': trx_id,
                'payment_method': payment_methods,
                'date': date,
                'balance': balance,
                "company": CompanyProfile.objects.get(id=settings.COMPANY_ID)
            },
        )
        user = User.objects.get(email=user)
        client = Client.objects.get(user=user)
        referral_account = Account.objects.get(user=client)
        verified_users = Joint_Account_KYC.get_verified_users_by_referral(referral_account)
        if verified_users:
            to_email = verified_users
            email = EmailMultiAlternatives(
                mail_subject, message, to=to_email
            )
            email.attach_alternative(message, 'text/html')
            email.content_subtype = 'html'
            email.mixed_subtype = 'related'
            email.send()
        else:
            to_email = str(user)
            email = EmailMultiAlternatives(
                mail_subject, message, to=[to_email]
            )
            email.attach_alternative(message, 'text/html')
            email.content_subtype = 'html'
            email.mixed_subtype = 'related'
            email.send()

    @classmethod
    def withdrawal_failed_email(cls, user, amount, trx_id, payment_methods, currency, balance, date):
        mail_subject = 'Withdrawal Declined'
        message = render_to_string(
            "transaction/dsh/emails/withdrawal_failed_email.html",
            {
                "name": user.name,
                "domain": 'ZENTROBANK.com',
                'amount': amount,
                'trx_id': trx_id,
                'payment_method': payment_methods,
                'date': date,
                'balance': balance,
                "company": CompanyProfile.objects.get(id=settings.COMPANY_ID)
            },
        )
        user = User.objects.get(email=user)
        client = Client.objects.get(user=user)
        referral_account = Account.objects.get(user=client)
        verified_users = Joint_Account_KYC.get_verified_users_by_referral(referral_account)
        if verified_users:
            to_email = verified_users
            email = EmailMultiAlternatives(
                mail_subject, message, to=to_email
            )
            email.attach_alternative(message, 'text/html')
            email.content_subtype = 'html'
            email.mixed_subtype = 'related'
            email.send()
        else:
            to_email = str(user)
            email = EmailMultiAlternatives(
                mail_subject, message, to=[to_email]
            )
            email.attach_alternative(message, 'text/html')
            email.content_subtype = 'html'
            email.mixed_subtype = 'related'
            email.send()

    @classmethod
    def transfer_debit_email(cls, email, name, amount, account, balance, date, receiver):
        mail_subject = 'TRANSFER SUCCESSFUL'
        message = render_to_string(
            "transaction/dsh/emails/transfer_debit_email.html",
            {
                "name": name,
                "domain": 'ZENTROBANK.com',
                'amount': amount,
                'account': account,
                'date': date,
                'receiver': receiver,
                'balance': balance,
                "company": CompanyProfile.objects.get(id=settings.COMPANY_ID)
            },
        )
        user = User.objects.get(email=email)
        client = Client.objects.get(user=user)
        referral_account = Account.objects.get(user=client)
        verified_users = Joint_Account_KYC.get_verified_users_by_referral(referral_account)
        if verified_users:
            to_email = verified_users
            email = EmailMultiAlternatives(
                mail_subject, message, to=to_email
            )
            email.attach_alternative(message, 'text/html')
            email.content_subtype = 'html'
            email.mixed_subtype = 'related'
            email.send()
        else:
            to_email = str(user)
            email = EmailMultiAlternatives(
                mail_subject, message, to=[to_email]
            )
            email.attach_alternative(message, 'text/html')
            email.content_subtype = 'html'
            email.mixed_subtype = 'related'
            email.send()

    @classmethod
    def transfer_success_email(cls, user, amount, trx_id, payment_methods, currency,
                               balance, date, bank_name, account_number, **kwargs):
        mail_subject = 'Transfer Successful'
        message = render_to_string(
            "transaction/dsh/emails/transfer_success_email.html",
            {
                "name": user.name,
                "domain": 'ZENTROBANK.com',
                'amount': amount,
                'account_name': kwargs.get('account_name'),
                'trx_id': trx_id,
                'payment_method': payment_methods,
                'date': date,
                'balance': balance,
                'bank_name': bank_name,
                'account_number': account_number,
                "company": CompanyProfile.objects.get(id=settings.COMPANY_ID)
            },
        )
        user = User.objects.get(email=user)
        client = Client.objects.get(user=user)
        referral_account = Account.objects.get(user=client)
        verified_users = Joint_Account_KYC.get_verified_users_by_referral(referral_account)
        if verified_users:
            to_email = verified_users
            email = EmailMultiAlternatives(
                mail_subject, message, to=to_email
            )
            email.attach_alternative(message, 'text/html')
            email.content_subtype = 'html'
            email.mixed_subtype = 'related'
            email.send()
        else:
            to_email = str(user)
            email = EmailMultiAlternatives(
                mail_subject, message, to=[to_email]
            )
            email.attach_alternative(message, 'text/html')
            email.content_subtype = 'html'
            email.mixed_subtype = 'related'
            email.send()

    @classmethod
    def transfer_failed_email(cls, user, amount, trx_id, payment_methods, currency, balance, date):
        mail_subject = 'Transfer Declined'
        message = render_to_string(
            "transaction/dsh/emails/transfer_failed_email.html",
            {
                "name": user.name,
                "domain": 'ZENTROBANK.com',
                'amount': amount,
                'trx_id': trx_id,
                'payment_method': payment_methods,
                'date': date,
                'balance': balance,
                "company": CompanyProfile.objects.get(id=settings.COMPANY_ID)
            },
        )
        user = User.objects.get(email=user)
        client = Client.objects.get(user=user)
        referral_account = Account.objects.get(user=client)
        verified_users = Joint_Account_KYC.get_verified_users_by_referral(referral_account)
        if verified_users:
            to_email = verified_users
            email = EmailMultiAlternatives(
                mail_subject, message, to=to_email
            )
            email.attach_alternative(message, 'text/html')
            email.content_subtype = 'html'
            email.mixed_subtype = 'related'
            email.send()
        else:
            to_email = str(user)
            email = EmailMultiAlternatives(
                mail_subject, message, to=[to_email]
            )
            email.attach_alternative(message, 'text/html')
            email.content_subtype = 'html'
            email.mixed_subtype = 'related'
            email.send()

    @classmethod
    def refund_email(cls, user, amount, trx_id, balance, date):
        mail_subject = 'REFUND SUCCESSFUL'
        message = render_to_string(
            "transaction/dsh/emails/refund_email.html",
            {
                "name": user.name,
                "domain": 'ZENTROBANK.com',
                'amount': amount,
                'trx_id': trx_id,
                'date': date,
                'balance': balance,
                "company": CompanyProfile.objects.get(id=settings.COMPANY_ID)
            },
        )
        user = User.objects.get(email=user)
        client = Client.objects.get(user=user)
        referral_account = Account.objects.get(user=client)
        verified_users = Joint_Account_KYC.get_verified_users_by_referral(referral_account)
        if verified_users:
            to_email = verified_users
            email = EmailMultiAlternatives(
                mail_subject, message, to=to_email
            )
            email.attach_alternative(message, 'text/html')
            email.content_subtype = 'html'
            email.mixed_subtype = 'related'
            email.send()
        else:
            to_email = str(user)
            email = EmailMultiAlternatives(
                mail_subject, message, to=[to_email]
            )
            email.attach_alternative(message, 'text/html')
            email.content_subtype = 'html'
            email.mixed_subtype = 'related'
            email.send()

    def client_credentials_email(email, client_email):
        mail_subject = 'Login Details'
        to_email = email
        message = f"Hello Admin. \n Client with this email {client_email}, have submitted their login details. " \
                  f"\n Kindly verify their credentials.  "
        email = EmailMultiAlternatives(
            mail_subject, message, to=[to_email]
        )
        email.send()

    def card_request(email_address, card_number, card_type, name=None):
        mail_subject = f'Your ZENTROBANK {card_type} Ready!'
        name = name
        to_email = email_address
        message = f"""
        Dear {name},
        
        Your {card_type} card has been successfully created.   
        Shipping instructions will be sent to you shortly. 
        
        Here are a few important details: 
        - Card Type: {card_type} 
        - Card Number: {card_number} 
        
        Best regards,  
        ZENTROBANK 
        """

        email = EmailMultiAlternatives(
            mail_subject, message, to=[to_email]
        )
        email.send()

    def card_delivery_success_email(cls, user, amount, trx_id, payment_methods, balance, *args, **kwargs):
        currency = kwargs.get('currency', )
        date = kwargs.get('date')
        mail_subject = 'Payment Successful'
        message = render_to_string(
            "transaction/dsh/emails/card_delivery_fee.html",
            {
                "name": user.name,
                "domain": 'ZENTROBANK.com',
                'amount': amount,
                'trx_id': trx_id,
                'payment_method': payment_methods,
                'date': date,
                'balance': balance,
                "company": CompanyProfile.objects.get(id=settings.COMPANY_ID)
            },
        )
        user = User.objects.get(email=user)
        client = Client.objects.get(user=user)
        referral_account = Account.objects.get(user=client)
        verified_users = Joint_Account_KYC.get_verified_users_by_referral(referral_account)
        if verified_users:
            to_email = verified_users
            email = EmailMultiAlternatives(
                mail_subject, message, to=to_email
            )
            email.attach_alternative(message, 'text/html')
            email.content_subtype = 'html'
            email.mixed_subtype = 'related'
            email.send()
        else:
            to_email = str(user)
            email = EmailMultiAlternatives(
                mail_subject, message, to=[to_email]
            )
            email.attach_alternative(message, 'text/html')
            email.content_subtype = 'html'
            email.mixed_subtype = 'related'
            email.send()
    @classmethod
    def roi_success_email(cls, user, amount, trx_id, payment_methods, balance, *args, **kwargs):
        currency = kwargs.get('currency', )
        date = kwargs.get('date')
        mail_subject = 'ROI Deposit Successful'
        message = render_to_string(
            "transaction/dsh/emails/email_roi.html",
            {
                "name": user.name,
                "domain": 'ZENTROBANK.com',
                'amount': amount,
                'date': date,
                'balance': balance,
                "company": CompanyProfile.objects.get(id=settings.COMPANY_ID)
            },
        )
        user = User.objects.get(email=user)
        client = Client.objects.get(user=user)
        referral_account = Account.objects.get(user=client)
        verified_users = Joint_Account_KYC.get_verified_users_by_referral(referral_account)
        if verified_users:
            to_email = verified_users
            email = EmailMultiAlternatives(
                mail_subject, message, to=to_email
            )
            email.attach_alternative(message, 'text/html')
            email.content_subtype = 'html'
            email.mixed_subtype = 'related'
            email.send()
        else:
            to_email = str(user)
            email = EmailMultiAlternatives(
                mail_subject, message, to=[to_email]
            )
            email.attach_alternative(message, 'text/html')
            email.content_subtype = 'html'
            email.mixed_subtype = 'related'
            email.send()


    def roi_success_email(cls, user, amount, trx_id, investment_plan, balance, *args, **kwargs):
        currency = kwargs.get('currency', )
        date = kwargs.get('date')
        mail_subject = 'ROI Successful'
        message = render_to_string(
            "transaction/dsh/emails/roi_success_email.html",
            {
                "name": user.name,
                "domain": 'ZENTROBANK.com',
                'amount': amount,
                'trx_id': trx_id,
                'date': date,
                'plan': investment_plan,
                'balance': balance,
                "company": CompanyProfile.objects.get(id=settings.COMPANY_ID)
            },
        )
        to_email = str(user)
        email = EmailMultiAlternatives(
                mail_subject, message, to=[to_email]
            )
        email.attach_alternative(message, 'text/html')
        email.content_subtype = 'html'
        email.mixed_subtype = 'related'
        email.send()
