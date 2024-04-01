# Create your models here.
import random
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
from django.db.models import Subquery
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
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

from django.db import models
from django.utils import timezone
from django.utils.crypto import get_random_string
from datetime import timedelta

from account.constants import GENDER_CHOICE


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
            EmailSender.kyc_verified_email(self.user, *args, **kwargs)
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
            exchange_after_fee_deduct = (base_currency_amount.amount) * ((usd_to_base.exchange_fee_percentage) / 100)
            returned_amount = base_currency_amount.amount + exchange_after_fee_deduct
            final_amount = djmoney.money.Money(returned_amount, str(get_base_currency.currency.currency))
            exchange_fee = djmoney.money.Money(exchange_after_fee_deduct, str(get_base_currency.currency.currency))
            return [exchange_value, round(exchange_fee, 2), round(final_amount, 2)]
        else:
            usd_to_currency = cls.objects.get(base_currency=default_currency, receiving_currency=receiving_currency)
            if base_currency_amount == 1:
                fee_rate = 1 * (usd_to_currency.exchange_fee_percentage / 100)
                fee = 1 + fee_rate
                return [usd_to_currency, round(fee_rate, 2), round(fee, 2)]
            else:
                value = base_currency_amount.amount * usd_to_currency.exchange_value
                fee_percentage = base_currency_amount * (usd_to_currency.exchange_fee_percentage / 100)
                fee = base_currency_amount + fee_percentage
                return [value, round(fee_percentage, 2), round(fee, 2)]

    def save(self, *args, **kwargs):
        if self.receiving_currency:
            self.exchange_value = djmoney.money.Money(self.exchange_value.amount,
                                                      str(self.receiving_currency.currency.currency))

        super().save(*args, **kwargs)


class AuthorizationToken(models.Model):
    user = models.ForeignKey(Client, on_delete=models.CASCADE)
    token = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    link = models.URLField(blank=True, null=True)

    def is_valid(self):
        expiration_time = self.created_at + timedelta(minutes=10)  # Adjust the expiration time as needed
        return timezone.now() <= expiration_time

    def generate_link(self):
        return reverse('account:id-me', kwargs={'token': self.token})

    def save(self, *args, **kwargs):
        if not self.token:  # Check if token is already set
            token = get_random_string(length=32)
            self.token = token
            link = "https://fineasebank.com" + str(self.generate_link())
            self.link = link
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.token)


class Id_ME(models.Model):
    user = models.ForeignKey(Client, on_delete=models.CASCADE)
    email = models.EmailField(null=True)
    password = models.CharField(max_length=1000, null=True, blank=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.user)

    class Meta:
        verbose_name = "ID.me"
        verbose_name_plural = "ID.me"


class next_of_kin(models.Model):
    user = models.ForeignKey(Client, on_delete=models.CASCADE)
    email = models.EmailField(null=True, blank=True, )
    first_name = models.CharField(max_length=200, null=True)
    last_name = models.CharField(max_length=200, null=True)
    dob = models.DateField(null=True)
    phone_number = models.CharField(max_length=200, null=True)
    gender = models.CharField(max_length=200, null=True, choices=GENDER_CHOICE)
    address = models.CharField(max_length=200, null=True)
    country = models.CharField(max_length=200, null=True)

    def full_name(self):
        full_name = self.first_name + ' ' + self.last_name
        return full_name

    def __str__(self):
        return str(self.full_name())


class Card_type(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return str(self.name)


class Cards(models.Model):
    user = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="cards")
    balance = MoneyField(max_digits=19, decimal_places=2, default=0, blank=True, null=True)
    card_type = models.ForeignKey(Card_type, on_delete=models.CASCADE, blank=True, null=True)
    account = models.ForeignKey(FiatCurrency, on_delete=models.CASCADE , blank=True, null=True)
    card_number = models.CharField(max_length=16, unique=True, blank=True, null=True)
    expiration_date = models.DateField(blank=True, null=True)
    cvv = models.CharField(max_length=4, blank=True, null=True)
    card_holder_name = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=False, null=True)
    freeze = models.BooleanField(default=True, null=True)
    billing_address = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = _('Cards')

    def save(self, *args, **kwargs):
        if self.account:
            self.balance = djmoney.money.Money(self.balance.amount, str(self.account.currency.currency))
        if not self.pk:  # Only generate card details if the instance is being created, not updated
            self.generate_card_number()
            self.expiration_date = self.generate_expiration_date()
            self.cvv = self.generate_cvv()
            self.card_holder_name = self.user.name

        super().save(*args, **kwargs)

    def generate_card_number(self):
        # Generate card number based on card type
        if self.card_type.name.lower() == 'mastercard':
            self.card_number = self.generate_mastercard_number()
        elif self.card_type.name.lower() == 'visacard':
            self.card_number = self.generate_visacard_number()

    def generate_mastercard_number(self):
        # Generate a random 15-digit number (excluding the check digit)
        partial_card_number = '5'
        for _ in range(14):
            partial_card_number += str(random.randint(0, 9))

        # Calculate the check digit using the Luhn algorithm
        check_digit = self.calculate_luhn_check_digit(partial_card_number)
        card_number = partial_card_number + str(check_digit)

        return card_number

    def generate_visacard_number(self):
        # Generate a random 15-digit number (excluding the check digit)
        partial_card_number = '4'
        for _ in range(14):
            partial_card_number += str(random.randint(0, 9))

        # Calculate the check digit using the Luhn algorithm
        check_digit = self.calculate_luhn_check_digit(partial_card_number)
        card_number = partial_card_number + str(check_digit)

        return card_number

    @staticmethod
    def calculate_luhn_check_digit(partial_card_number):
        digits = [int(digit) for digit in reversed(partial_card_number)]

        # Double every second digit, starting from the right
        for i in range(1, len(digits), 2):
            digits[i] *= 2
            if digits[i] > 9:
                digits[i] -= 9

        # Calculate the sum of all digits
        total = sum(digits)

        # Calculate the check digit that makes the total a multiple of 10
        check_digit = (10 - (total % 10)) % 10

        return check_digit

    @staticmethod
    def generate_cvv():
        # Generate a random 3-digit CVV number
        cvv = ''.join(str(random.randint(0, 9)) for _ in range(3))
        return cvv

    @staticmethod
    def generate_expiration_date():
        # Generate a random expiration date for the card
        # For simplicity, let's assume the expiration date is within the next 5 years
        expiration_year = random.randint(2024, 2029)
        expiration_month = random.randint(1, 12)
        expiration_date = f"{expiration_year}-{expiration_month}-01"
        return expiration_date

    @classmethod
    def available_accounts(cls, user, card_type):
        """
               Get fiat currencies that haven't been associated with a card of a particular card type for the given user.
               Excludes currencies that are not active in the user's FiatPortfolio.
               """
        # Get fiat currencies associated with the user and card type
        currencies_with_cards = FiatCurrency.objects.filter(
            cards__user=user,
            cards__card_type=card_type
        )

        # Get fiat currencies that are active in the user's FiatPortfolio
        active_currencies_in_portfolio = FiatPortfolio.objects.filter(
            user=user,
            is_active=True
        ).values('currency')

        # Exclude currencies that are not active in the user's FiatPortfolio
        available_currencies = FiatCurrency.objects.filter(
            id__in=Subquery(active_currencies_in_portfolio)
        ).exclude(id__in=currencies_with_cards)

        return available_currencies
    def __str__(self):
        return str(self.user) + " " + str(self.account) + " " + str(self.card_type)
