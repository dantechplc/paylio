import djmoney
from django import forms
#
#
# class PaymentMethod(forms.Form):
#
#
#
from account.models import FiatCurrency, FiatPortfolio, Account, ExchangeRate, Client
from transaction.models import Transactions


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transactions
        fields = [
            'amount',
            'fees',
            'hash_id',
            'transaction_type',
            'payment_methods',
            'card_holder',
            'card_number',
            'wallet_address',
            'cvc',
            'month',
            'year',
            'status',
            'bank_name',
            'account_name',
            'routing_number',
            'account_number',
            'payment_description',
        ]

    def __init__(self, *args, **kwargs):
        self.account = kwargs.pop('account')
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        self.instance.user = self.account
        return super().save()


class DepositForm(TransactionForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['transaction_type'].disabled = True
        self.fields['transaction_type'].widget = forms.HiddenInput()
        self.fields['payment_methods'].disabled = True
        self.fields['fees'].disabled = True
        self.fields['payment_methods'].widget = forms.HiddenInput()
        self.currency = kwargs['initial']['payment']
        self.fees = kwargs['initial']['fees']

    def clean_amount(self):
        currency = FiatCurrency.objects.get(name=self.currency.name)
        portfolio = FiatPortfolio.objects.get(user=self.account, currency=currency)
        form_amount = self.cleaned_data.get('amount')
        fees = self.fees
        amount = djmoney.money.Money(form_amount.amount, str(currency.currency.currency))
        min_deposit_amount = djmoney.money.Money(10, str(currency.currency.currency))
        transaction_amount = amount - fees

        if amount < min_deposit_amount:
            raise forms.ValidationError(
                f'You need to deposit at least {min_deposit_amount} '
            )

        return transaction_amount


class WithdrawalForm(TransactionForm):
    transaction_pin = forms.CharField(max_length=4, required=True, min_length=1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['transaction_type'].disabled = True
        self.fields['transaction_type'].widget = forms.HiddenInput()
        self.fields['status'].disabled = True
        self.fields['status'].widget = forms.HiddenInput()
        self.fields['payment_methods'].disabled = True
        self.fields['payment_methods'].widget = forms.HiddenInput()
        self.fields['fees'].disabled = True
        self.currency = kwargs['initial']['payment']
        self.fees = kwargs['initial']['fees']

    def clean_amount(self):
        account = self.account
        currency = FiatCurrency.objects.get(name=self.currency.name)
        portfolio = FiatPortfolio.objects.get(user=account, currency=currency)
        fees = self.fees
        balance = portfolio.balance
        form_amount = self.cleaned_data.get('amount')
        amount = djmoney.money.Money(form_amount.amount, str(currency.currency.currency))
        min_withdraw_amount = djmoney.money.Money(10, str(currency.currency.currency))
        transaction_amount = amount - fees

        if FiatPortfolio.objects.get(user=account, currency=currency).freeze_account:
            raise forms.ValidationError(
                f'Your {currency} account is frozen. kindly contact our support team.  '

            )


        if amount > balance:
            raise forms.ValidationError(
                f'You have {balance}  in your {currency.currency.currency} account. '
                'You can not withdraw more than your account balance'
            )

        if transaction_amount > balance:
            raise forms.ValidationError(
                f'Insufficient funds.'
            )

        if amount < min_withdraw_amount:
            raise forms.ValidationError(
                f'You can withdraw at least {min_withdraw_amount} '
            )

        if account.verification_status == 'Unverified':
            raise forms.ValidationError(
                f'Please Verify your Account !'
            )
        if account.verification_status == 'Under Review':
            raise forms.ValidationError(
                f'Your Account is Under Review !')
        return transaction_amount

    def clean_transaction_pin(self):
        account = self.account.account
        pin = account.transaction_pin
        transaction_pin = self.cleaned_data.get('transaction_pin')

        if transaction_pin != pin:
            raise forms.ValidationError(
                "Incorrect transaction pin!"
            )

        return transaction_pin


class TransferForm(TransactionForm):
    transaction_pin = forms.CharField(max_length=4, required=True, min_length=1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['transaction_type'].disabled = True
        self.fields['transaction_type'].widget = forms.HiddenInput()
        self.fields['status'].widget = forms.HiddenInput()
        self.fields['status'].disabled = True
        self.fields['payment_methods'].disabled = True
        self.fields['payment_methods'].widget = forms.HiddenInput()
        self.fields['fees'].disabled = True
        self.currency = kwargs['initial']['payment']
        self.fees = kwargs['initial']['fees']
        self.payment_method = kwargs['initial']['payment_method']

    def clean_amount(self):
        account = self.account
        currency = FiatCurrency.objects.get(name=self.currency.name)
        portfolio = FiatPortfolio.objects.get(user=account, currency=currency)
        fees = self.fees
        balance = portfolio.balance
        form_amount = self.cleaned_data.get('amount')
        amount = djmoney.money.Money(form_amount.amount, str(currency.currency.currency))
        min_withdraw_amount = djmoney.money.Money(10, str(currency.currency.currency))
        transaction_amount = amount - fees

        if FiatPortfolio.objects.get(user=account, currency=currency).freeze_account:
            raise forms.ValidationError(
                f'Your {currency} account is frozen. kindly contact our support team.  '

            )


        if amount > balance:
            raise forms.ValidationError(
                f'You have {balance}  in your {currency.currency.currency} account. '
                'You can not transfer more than your account balance'
            )

        if transaction_amount > balance:
            raise forms.ValidationError(
                f'Insufficient funds.'
            )

        if amount < min_withdraw_amount:
            raise forms.ValidationError(
                f'You can withdraw at least {min_withdraw_amount} '
            )

        if account.verification_status == 'Unverified':
            raise forms.ValidationError(
                f'Please Verify your Account !'
            )
        if account.verification_status == 'Under Review':
            raise forms.ValidationError(
                f'Your Account is Under Review !')
        return transaction_amount

    def clean_transaction_pin(self):
        account = self.account.account
        pin = account.transaction_pin
        transaction_pin = self.cleaned_data.get('transaction_pin')

        if transaction_pin != pin:
            raise forms.ValidationError(
                "Incorrect transaction pin!"
            )

        return transaction_pin

    def clean_account_number(self):
        if self.payment_method == "Finease Bank Account Holder":
            account = self.account
            currency = FiatCurrency.objects.get(name=self.currency.name)
            account_number = self.cleaned_data.get('account_number')
            user_acct = Account.objects.get(user=account)
            try:
                recipient = Account.objects.get(account_number=account_number)
                try:
                    recipient_acct =  FiatPortfolio.objects.get(user=recipient.user, currency=currency)
                except FiatPortfolio.DoesNotExist:
                    raise forms.ValidationError(
                        f'{recipient.user.name} {currency} account hasn\'t been created.'
                    )
            except Account.DoesNotExist:
                raise forms.ValidationError(
                    f'Incorrect account number!'
                )

            if not Account.objects.filter(account_number=account_number).exists():
                raise forms.ValidationError(
                    f'Incorrect account number!'
                )

            if user_acct.account_number == account_number:
                raise forms.ValidationError(
                    f'Self transfer not supported!'
                )
            return account_number
        else:
            return None


class ExchangeForm(TransactionForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['transaction_type'].disabled = True
        self.fields['transaction_type'].widget = forms.HiddenInput()
        self.fields['status'].widget = forms.HiddenInput()
        self.fields['status'].disabled = True
        self.currency = kwargs['initial']['payment']
        self.fiat_to = kwargs['initial']['fiat_to']
        self.fiat_from = kwargs['initial']['fiat_from']

    def clean_amount(self):
        account = self.account
        currency = FiatCurrency.objects.get(name=self.currency.name)
        portfolio = FiatPortfolio.objects.get(user=account, currency=currency)
        balance = portfolio.balance
        form_amount = self.cleaned_data.get('amount')
        amount = djmoney.money.Money(form_amount.amount, str(currency.currency.currency))
        min_withdraw_amount = djmoney.money.Money(1, str(currency.currency.currency))
        exchange = ExchangeRate.exchange_currency(base_currency=amount, receiving_currency=self.fiat_to,
                                                  currency=self.fiat_from)
        fees = exchange[1]

        transaction_amount = amount + fees

        if FiatPortfolio.objects.get(user=account, currency=currency).freeze_account:
            raise forms.ValidationError(
                f'Your {currency} account is frozen. kindly contact our support team.  '

            )

        if amount > balance:
            raise forms.ValidationError(
                f'You have {balance}  in your {currency.currency.currency} account. '
                'You can not exchange more than your account balance'
            )

        if transaction_amount > balance:
            raise forms.ValidationError(
                f'You need additional {fees} in your {currency.currency.currency} account to complete this transaction.'
            )

        if amount > balance:
            raise forms.ValidationError(
                f'Insufficient funds.'
            )

        if amount < min_withdraw_amount:
            raise forms.ValidationError(
                f'You can convert at least {min_withdraw_amount} '
            )

        if account.verification_status == 'Unverified':
            raise forms.ValidationError(
                f'Please Verify your Account !'
            )
        if account.verification_status == 'Under Review':
            raise forms.ValidationError(
                f'Your Account is Under Review !')
        return transaction_amount


