# Create your models here.
import uuid
from datetime import datetime
from io import BytesIO

import djmoney
import qrcode
import requests
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.core.files.base import ContentFile
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField
from djmoney.models.fields import MoneyField
from imagekit.models import ImageSpecField
from pilkit.processors import ResizeToFill

from account.constants import *
from account.manager import UserManager
from helpers.models import TrackingModel
from transaction.EmailSender import EmailSender


class User(AbstractBaseUser, PermissionsMixin, TrackingModel):
    email = models.EmailField(_('email address'), unique=True)
    name = models.CharField(max_length=150, blank=True)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_client = models.BooleanField(default=False)
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def str(self):
        return str(self.email)


class Client(TrackingModel, models.Model):
    user = models.OneToOneField(User, verbose_name="Client", related_name='client', on_delete=models.CASCADE)
    name = models.CharField(max_length=250, blank=True, null=True)
    mobile = models.CharField(max_length=150)
    country = CountryField(blank_label='(select country)', blank=True, null=True)
    email_verified = models.BooleanField(default=False)
    profile_pic = models.ImageField(upload_to='client/profile_pic', default='avatars/avatar.jpg', blank=True)
    profile_pic_thumbnail = ImageSpecField(source='profile_pic',
                                           processors=[ResizeToFill(80, 80)],
                                           format="JPEG",
                                           options={'quality': 60})
    verification_status = models.CharField(max_length=200, choices=verification_status, blank=True,
                                           default='Unverified')

    class Meta:
        verbose_name = "Client"

    def __str__(self):
        return str(self.user)

    def save(self, *args, **kwargs):
        if self.verification_status == 'Verified':
            EmailSender.kyc_verified_email(self.user,  *args, **kwargs)
        super().save(*args, **kwargs)


class KYC(TrackingModel, models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(Client, verbose_name=_("Client"), on_delete=models.CASCADE, related_name='kyc')
    first_name = models.CharField(_("First Name"), max_length=150)
    last_name = models.CharField(_("last Name"), max_length=150)
    dob = models.DateField(verbose_name='Date of Birth')
    gender = models.CharField(max_length=100, choices=GENDER_CHOICE, null=True)
    postcode = models.CharField(_("Postcode/Zipcode"), max_length=50)
    address = models.CharField(_("Address"), max_length=255)
    town_city = models.CharField(_("Town/City"), max_length=150)
    state = models.CharField(_("State"), max_length=150)
    document_type = models.CharField(max_length=50, choices=ID, null=True)
    id_front_view = models.FileField(upload_to="kyc/%Y-%m-%d/", null=True)
    id_back_view = models.FileField(upload_to="kyc/%Y-%m-%d/", blank=True, null=True)
    ssn = models.FileField(upload_to="kyc/%Y-%m-%d/", blank=True, null=True)

    class Meta:
        verbose_name = "KYC"
        verbose_name_plural = "KYCs"

    def __str__(self):
        return str(self.client)


class Account(models.Model):
    user = models.OneToOneField(Client, related_name="account", on_delete=models.CASCADE)
    account_number = models.CharField(max_length=100, null=True, blank=True, unique=True)
    account_type = models.CharField(max_length=200, blank=True, null=True, choices=account_type)
    transaction_pin = models.CharField(max_length=6, null=True, blank=True, default='0000')
    two_factor_auth = models.BooleanField(default=False, blank=True, null=True)
    password = models.CharField(max_length=225, blank=True, null=True)
    

    def __str__(self):
        return str(self.user)

    def generate_account_number(self):
        account_number_prefix = int(39232145)
        new_account_number = account_number_prefix + int(self.user.id)
        return new_account_number

    def save(self, *args, **kwargs):
        if not self.account_number:
            self.account_number = self.generate_account_number()
        super().save(*args, **kwargs)


class FiatCurrency(models.Model):
    name = models.CharField(max_length=20)
    currency = MoneyField(max_digits=19, decimal_places=2, default=0, blank=True, null=True)
    image = models.ImageField(upload_to='fiat_images', blank=True, null=True)
    image_thumbnail = ImageSpecField(source='image',
                                           processors=[ResizeToFill(50, 30)],
                                           format="PNG",
                                           options={'quality': 60})
    transaction_fee = MoneyField(max_digits=19, decimal_places=2, default=0, blank=True, null=True)
    is_active = models.BooleanField(default=False, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Fiat Currencies"

    @classmethod
    def get_default_currency(cls):
        code = "USD"
        amt = djmoney.money.Money(0, code)
        currency = cls.objects.get(currency=amt)
        return currency

    @classmethod
    def get_base_currency(cls, *args, **kwargs):  # used for getting the base currency for exchange rate calculations
        name = kwargs.get('currency')
        currency = cls.objects.get(name=name)
        return currency


class FiatPortfolio(models.Model):
    user = models.ForeignKey(Client, on_delete=models.CASCADE, null=True)
    currency = models.ForeignKey(FiatCurrency, null=True, related_name="fiat_portfolio", on_delete=models.CASCADE)
    balance = MoneyField(max_digits=19, decimal_places=2, default=0, blank=True, null=True, )
    is_active = models.BooleanField(default=True, blank=True, null=True)
    freeze_account = models.BooleanField(default=False, null=True, blank=True)


    def __str__(self):
        return f"{self.user} {self.currency.name} account"

    def save(self, *args, **kwargs):
        if self.currency:
            self.balance = djmoney.money.Money(self.balance.amount, str(self.currency.currency.currency))
        super().save(*args, **kwargs)


class PaymentMethods(models.Model):
    name = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    is_crypto = models.BooleanField(default=False)
    for_deposit = models.BooleanField(default=False)
    transfer_access = models.BooleanField(default=False)
    for_withdrawal = models.BooleanField(default=False)
    wallet_address = models.CharField(max_length=300, blank=True, null=True)
    wallet_qrcode = models.ImageField(blank=True, null=True)
    transaction_fee = MoneyField(max_digits=19, decimal_places=2, default=0, blank=True, null=True)
    deposit_transaction_message = models.TextField(blank=True, null=True)
    withdrawal_transaction_message = models.TextField(blank=True, null=True)

    def __str__(self):
        return str(self.name)

    def generate_qr_code(self):
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(self.wallet_address)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buffer = BytesIO()
        img.save(buffer, format='PNG')
        image_binary = buffer.getvalue()
        buffer.close()

        file_name = f"{self.name}.png"
        self.wallet_qrcode.save(file_name, ContentFile(image_binary), save=False)

    class Meta:
        verbose_name_plural = 'Payment Methods'

    def save(self, *args, **kwargs):
        self.generate_qr_code()
        super().save(*args, **kwargs)


class ExchangeRate(models.Model):
    base_currency = models.ForeignKey(FiatCurrency, related_name='base_currency', on_delete=models.CASCADE)
    receiving_currency = models.ForeignKey(FiatCurrency, related_name='receiving_currency', on_delete=models.CASCADE)
    exchange_value = MoneyField(max_digits=19, decimal_places=2, default=0, blank=True, null=True)
    exchange_fee_percentage = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=12)

    def __str__(self):
        return f"{self.base_currency} to {self.receiving_currency} - {self.exchange_value}"

    @classmethod
    def exchange_currency(cls, *args, **kwargs):
        base_currency_amount = kwargs.get('base_currency')
        receiving_currency = FiatCurrency.get_base_currency(currency=kwargs.get('receiving_currency'))
        default_currency = FiatCurrency.objects.filter(currency_currency='USD')[0]
        get_base_currency = FiatCurrency.get_base_currency(currency=kwargs.get('currency'))
        if get_base_currency != default_currency:
            usd_to_base = cls.objects.get(base_currency=default_currency,
                                          receiving_currency=get_base_currency)
            equivalent_amt = 1 / usd_to_base.exchange_value.amount  # converting usd to 1 base amount required for exchange
            current_amt = base_currency_amount.amount * equivalent_amt  # converting from base amount to USD
            usd_to_receive = cls.objects.get(base_currency=default_currency,
                                             receiving_currency=receiving_currency)  # exchange rate to receive
            exchange_value = current_amt * usd_to_receive.exchange_value
            exchange_after_fee_deduct = (base_currency_amount.amount) * ((usd_to_base.exchange_fee_percentage)/100)
            returned_amount = base_currency_amount.amount + exchange_after_fee_deduct
            final_amount = djmoney.money.Money(returned_amount, str(get_base_currency.currency.currency))
            exchange_fee = djmoney.money.Money(exchange_after_fee_deduct, str(get_base_currency.currency.currency))
            return [exchange_value, round(exchange_fee, 2), round(final_amount, 2)]
        else:
            usd_to_currency = cls.objects.get(base_currency=default_currency, receiving_currency=receiving_currency)
            if base_currency_amount == 1:
                fee_rate =  1*(usd_to_currency.exchange_fee_percentage/100)
                fee = 1 + fee_rate
                return [usd_to_currency, round(fee_rate, 2), round(fee, 2)]
            else:
                value = base_currency_amount.amount * usd_to_currency.exchange_value
                fee_percentage = base_currency_amount * (usd_to_currency.exchange_fee_percentage/100)
                fee =  base_currency_amount + fee_percentage
                return [value, round(fee_percentage, 2), round(fee, 2)]

    def save(self, *args, **kwargs):
        if self.receiving_currency:
            self.exchange_value = djmoney.money.Money(self.exchange_value.amount,
                                                      str(self.receiving_currency.currency.currency))

        super().save(*args, **kwargs)
