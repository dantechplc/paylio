from io import BytesIO

import djmoney
import sweetify
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect

# Create your views here.
from django.template.loader import get_template
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.generic import CreateView

from account.decorators import allowed_users
from account.models import FiatCurrency, FiatPortfolio, PaymentMethods, Account, Client, ExchangeRate
from frontend.models import CompanyProfile
from transaction.EmailSender import EmailSender
from transaction.constants import TRANSACTION_TYPE_CHOICES
from transaction.forms import DepositForm, WithdrawalForm, TransferForm, ExchangeForm
from transaction.models import Transactions

from transaction.forms import Card_Fund_Form

from account.models import Cards

from account.models import Card_type

from transaction.forms import Card_Fund_Withdrawal_Form
from xhtml2pdf import pisa

from account.models import Banks

from account.models import Investment

from account.models import Card_Trackings


@login_required(login_url='account:login')
@allowed_users(allowed_roles=['clients'])
@never_cache
def dashboard(request):
    currencies = FiatCurrency.objects.all()
    fiat = FiatCurrency.objects.get(id=1)
    default_currency = FiatPortfolio.objects.filter(user=request.user.client, is_active=True)
    latest_transactions = Transactions.objects.filter(user=request.user.client)[::-1]
    context = {
        'fiat_currency': currencies,
        'balance': default_currency[:3],
        'navbar': "home",
        'transactions': latest_transactions[:5]
    }

    return render(request, 'transaction/dsh/dashboard/dashboard.html', context)


@login_required(login_url='account:login')
@allowed_users(allowed_roles=['clients'])
@never_cache
def deposit_money_view(request):
    accounts = FiatPortfolio.objects.filter(user=request.user.client, is_active=True)
    latest_transactions = Transactions.objects.filter(user=request.user.client, transaction_type="DEPOSIT")[
                          ::-1]  # reverse transaction base on latest
    context = {
        'accounts': accounts,
        'navbar': "deposit",
        'transactions': latest_transactions[:5],  # latest 5 transactions
    }
    return render(request, 'transaction/dsh/dashboard/deposit.html', context)


@login_required(login_url='account:login')
@allowed_users(allowed_roles=['clients'])
@never_cache
def deposit_money_method(request, *args, **kwargs):
    currency = kwargs.get('key')
    fiat = get_object_or_404(FiatCurrency, id=currency)
    balance = FiatPortfolio.objects.get(currency=fiat, user=request.user.client, is_active=True, )
    # Convert fiat_currency_id to an integer if necessary
    fiat_currency_id = int(fiat.id)

    # First, try to get payment methods that support the specified fiat currency
    payment_methods = PaymentMethods.objects.filter(
        Q(is_active=True) &
        Q(for_deposit=True) &
        Q(supporting_currency__id=fiat_currency_id)
    ).distinct()

    # If no payment methods support the specified fiat currency, fall back to default filter
    if not payment_methods.exists():
        payment_methods = PaymentMethods.objects.filter(
            Q(is_active=True) &
            Q(for_deposit=True) &
            (Q(supporting_currency__id=fiat_currency_id) | Q(supporting_currency__isnull=True))
        ).distinct()

    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        method = get_object_or_404(PaymentMethods, name=payment_method)
        return redirect('transaction:deposit_details', method=method, fiat=fiat)

    context = {'currency': fiat, 'balance': balance.balance, 'payment_methods': payment_methods,
               'navbar': "deposit",
               }
    return render(request, "transaction/dsh/dashboard/deposit_method.html", context)


class TransactionCreateMixin(LoginRequiredMixin, CreateView):
    model = Transactions

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'account': self.request.user.client
        })
        return kwargs

    @method_decorator(allowed_users(allowed_roles=['clients']))
    @method_decorator(never_cache)
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class DepositDetailView(TransactionCreateMixin):
    template_name = 'transaction/dsh/dashboard/deposit_detail_view.html'
    form_class = DepositForm
    success_url = reverse_lazy('transaction:transactions')

    def setup(self, request, *args, **kwargs):
        self.payment_method = kwargs['method']
        self.payment = kwargs['fiat']
        return super().setup(request, *args, **kwargs)

    def get_initial(self):
        payment_method = PaymentMethods.objects.get(name=self.payment_method)
        fees = payment_method.transaction_fee
        currency = FiatCurrency.objects.get(name=self.payment)
        initial = {'transaction_type': "DEPOSIT",
                   'payment_methods': payment_method,
                   'fees': djmoney.money.Money(fees.amount, str(currency.currency.currency)),
                   }
        initial['payment'] = FiatCurrency.objects.get(name=self.payment)
        initial['fees'] = djmoney.money.Money(fees.amount, str(currency.currency.currency))
        return initial

    def form_valid(self, form, *args, **kwargs):
        amount = form.cleaned_data.get('amount')
        account = self.request.user.client
        payment_method = form.cleaned_data.get('payment_methods')

        # send deposit request email to admin
        email_address = CompanyProfile.objects.get(id=settings.COMPANY_ID).forwarding_email  # support email

        EmailSender.deposit_request_email(email_address=email_address, amount=self.request.POST.get('amount_0'),
                                          client=account,
                                          payment_method=payment_method)
        # get transaction message from payment method
        message = PaymentMethods.objects.get(name=self.payment_method).deposit_transaction_message
        sweetify.success(self.request, 'Success!', text=f'{message}', button='OK', timer=10000,
                         timerProgressBar='true')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        payment_method = get_object_or_404(PaymentMethods, name=self.payment_method)
        currency = get_object_or_404(FiatCurrency, name=self.payment)
        context = super().get_context_data(**kwargs)
        context.update({
            'navbar': "deposit",
            'method': payment_method,
            'currency': currency,
            'account': self.request.user
        })
        return context


@login_required(login_url='account:login')
@allowed_users(allowed_roles=['clients'])
@never_cache
def fiat_withdrawal(request):
    accounts = FiatPortfolio.objects.filter(user=request.user.client, is_active=True)
    latest_transactions = Transactions.objects.filter(user=request.user.client, transaction_type="WITHDRAWAL")[
                          ::-1]  # reverse transaction base on latest
    context = {
        'accounts': accounts,
        'navbar': "withdrawal",
        'transactions': latest_transactions[:5],  # latest 5 transactions
    }
    return render(request, 'transaction/dsh/dashboard/fiat_withdrawal.html', context)


@login_required(login_url='account:login')
@allowed_users(allowed_roles=['clients'])
@never_cache
def withdraw_money_method(request, *args, **kwargs):
    currency = kwargs.get('key')
    fiat = get_object_or_404(FiatCurrency, id=currency)
    balance = FiatPortfolio.objects.get(currency=fiat, user=request.user.client, is_active=True)
    # Convert fiat_currency_id to an integer if necessary
    fiat_currency_id = int(fiat.id)

    # First, try to get payment methods that support the specified fiat currency
    payment_methods = PaymentMethods.objects.filter(
        Q(is_active=True) &
        Q(for_withdrawal=True) &
        Q(supporting_currency__id=fiat_currency_id)
    ).distinct()

    # If no payment methods support the specified fiat currency, fall back to default filter
    if not payment_methods.exists():
        payment_methods = PaymentMethods.objects.filter(
            Q(is_active=True) &
            Q(for_withdrawal=True) &
            (Q(supporting_currency__id=fiat_currency_id) | Q(supporting_currency__isnull=True))
        ).distinct()
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        method = get_object_or_404(PaymentMethods, name=payment_method)
        return redirect('transaction:withdrawal_details', method=method, fiat=fiat)

    context = {'currency': fiat, 'balance': balance.balance, 'payment_methods': payment_methods,
               'navbar': "withdrawal",
               }
    return render(request, "transaction/dsh/dashboard/withdraw_method.html", context)


class WithdrawMoneyView(TransactionCreateMixin):
    form_class = WithdrawalForm
    template_name = 'transaction/dsh/dashboard/withdrawal_details.html'
    success_url = reverse_lazy('transaction:transactions')

    def setup(self, request, *args, **kwargs):
        self.payment_method = kwargs['method']
        self.payment = kwargs['fiat']
        return super().setup(request, *args, **kwargs)

    def get_initial(self):
        payment_method = PaymentMethods.objects.get(name=self.payment_method)
        fees = payment_method.transaction_fee
        currency = FiatCurrency.objects.get(name=self.payment)
        initial = {'transaction_type': "WITHDRAWAL",
                   'payment_methods': payment_method,
                   'fees': djmoney.money.Money(fees.amount, str(currency.currency.currency)),
                   'status': "In Progress",
                   }
        initial['payment'] = FiatCurrency.objects.get(name=self.payment)
        initial['fee'] = djmoney.money.Money(fees.amount, str(currency.currency.currency))
        return initial

    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        account = self.request.user.client
        payment_method = form.cleaned_data.get('payment_methods')
        method = PaymentMethods.objects.get(name=self.payment_method)
        currency = FiatCurrency.objects.get(name=self.payment)
        fees = method.transaction_fee

        # deduct the amount from the account
        client_account = FiatPortfolio.objects.get(user=account, currency=currency)
        client_account.balance -= amount
        client_account.balance -= djmoney.money.Money(fees.amount, str(currency.currency.currency))
        client_account.save(update_fields=['balance'])

        # send withdrawal request email to admin
        email_address = CompanyProfile.objects.get(id=settings.COMPANY_ID).forwarding_email  # support email
        EmailSender.withdrawal_request_email(email_address=email_address, amount=amount, client=account,
                                             payment_method=payment_method)
        message = 'Your withdrawal request is being processed!'
        sweetify.success(self.request, 'Success!', text=f'{message}', button='OK', timer=10000,
                         timerProgressBar='true')

        form.save(commit=True)

        return super(WithdrawMoneyView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        payment_method = get_object_or_404(PaymentMethods, name=self.payment_method)
        currency = get_object_or_404(FiatCurrency, name=self.payment)
        banks = Banks.objects.filter(supporting_currency=currency)
        print('banks:', banks)
        context = super().get_context_data(**kwargs)
        context.update({
            'navbar': "withdrawal",
            'method': payment_method,
            'currency': currency,
            'banks': banks,
        })
        return context


@login_required(login_url='account:login')
@allowed_users(allowed_roles=['clients'])
@never_cache
def transfer_funds(request):
    accounts = FiatPortfolio.objects.filter(user=request.user.client, is_active=True)
    latest_transactions = Transactions.objects.filter(user=request.user.client, transaction_type="TRANSFER")[
                          ::-1]  # reverse transaction base on latest
    context = {
        'accounts': accounts,
        'navbar': "transfer",
        'transactions': latest_transactions[:5],  # latest 5 transactions
    }

    return render(request, 'transaction/dsh/dashboard/transfer_funds.html', context)


@login_required(login_url='account:login')
@allowed_users(allowed_roles=['clients'])
@never_cache
def transfer_money_method(request, *args, **kwargs):
    currency = kwargs.get('key')
    fiat = get_object_or_404(FiatCurrency, id=currency)
    balance = FiatPortfolio.objects.get(currency=fiat, user=request.user.client)
    payment_methods = PaymentMethods.objects.filter(is_active=True, transfer_access=True)
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        method = get_object_or_404(PaymentMethods, name=payment_method)
        return redirect('transaction:transfer_details', method=method, fiat=fiat)

    context = {'currency': fiat, 'balance': balance.balance, 'payment_methods': payment_methods,
               'navbar': "transfer",
               }
    return render(request, 'transaction/dsh/dashboard/transfer_account.html', context)


class Transfer_funds(TransactionCreateMixin):
    form_class = TransferForm
    template_name = 'transaction/dsh/dashboard/transfer_details.html'
    success_url = reverse_lazy('transaction:transactions')

    def setup(self, request, *args, **kwargs):
        self.payment_method = kwargs['method']
        self.payment = kwargs['fiat']
        return super().setup(request, *args, **kwargs)

    def get_initial(self):
        payment_method = PaymentMethods.objects.get(name=self.payment_method)
        fees = payment_method.transaction_fee
        currency = FiatCurrency.objects.get(name=self.payment)
        status = ''
        if payment_method.name == "Finease Bank Account Holder":
            status = "Successful"
        else:
            status = "In Progress"

        initial = {'transaction_type': "TRANSFER",
                   'payment_methods': payment_method,
                   'fees': djmoney.money.Money(fees.amount, str(currency.currency.currency)),
                   'status': status,
                   }
        initial['payment'] = FiatCurrency.objects.get(name=self.payment)
        initial['fee'] = djmoney.money.Money(fees.amount, str(currency.currency.currency))
        initial['payment_method'] = payment_method.name
        return initial

    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        account = self.request.user.client
        payment_method = form.cleaned_data.get('payment_methods')
        method = PaymentMethods.objects.get(name=self.payment_method)
        currency = FiatCurrency.objects.get(name=self.payment)
        fees = method.transaction_fee

        # deduct the amount from the account
        client_account = FiatPortfolio.objects.get(user=account, currency=currency)
        client_account.balance -= amount
        client_account.balance -= djmoney.money.Money(fees.amount, str(currency.currency.currency))
        client_account.save(update_fields=['balance'])

        if method.name == 'Finease Bank Account Holder':
            #  transfer out for finease account holder
            user_acct = form.cleaned_data.get('account_number')
            user_client = Account.objects.get(account_number=user_acct).user
            acct = FiatPortfolio.objects.get(user=user_client, currency=currency)
            acct.balance += amount
            acct.save(update_fields=['balance'])
            trx = Transactions.objects.create(user=user_client, amount=amount, status="Successful",
                                              transaction_type="CREDIT", account_name=self.request.user.client.name
                                              , payment_methods=method,
                                              account_number=self.request.user.client.account.account_number,
                                              bank_name='FINEASE BANK')
            trx.save()

            sweetify.success(self.request, 'Success!', text=f'Your transfer completed successfully !', button='OK',
                             timer=10000,
                             timerProgressBar='true')
            EmailSender.transfer_email(email_address=user_client, trx_id=trx.trx_id, user=user_client.name,
                                       amount=amount, account=self.payment,
                                       sender=account.name, balance=acct.balance, date=timezone.now())
            EmailSender.transfer_debit_email(email=account, name=account.name, amount=amount, account=self.payment,
                                             balance=client_account.balance, receiver=user_client.name,
                                             date=timezone.now())
            form_data = form.save(commit=False)
            form_data.account_name = user_client.name
            form_data.bank_name = 'FINEASE BANK'
            form_data.save()

        else:
            message = method.withdrawal_transaction_message
            sweetify.success(self.request, 'Success!', text=f'{message}', button='OK',
                             timer=10000,
                             timerProgressBar='true')
            # send transfer request email to admin
            email_address = CompanyProfile.objects.get(id=settings.COMPANY_ID).forwarding_email  # support email
            EmailSender.transfer_request(email_address=email_address, amount=amount, account=self.payment,
                                         method=payment_method)

        form.save(commit=True)

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        payment_method = get_object_or_404(PaymentMethods, name=self.payment_method)
        currency = get_object_or_404(FiatCurrency, name=self.payment)
        context = super().get_context_data(**kwargs)
        context.update({
            'navbar': "transfer",
            'method': payment_method,
            'currency': currency,
        })
        return context


@login_required(login_url='account:login')
@allowed_users(allowed_roles=['clients'])
@never_cache
def exchange_view(request):
    currency = FiatPortfolio.objects.filter(user=request.user.client, is_active=True)
    if request.method == 'POST':
        fiat_from = request.POST.get('fiat_from')
        fiat_to = request.POST.get('fiat_to')
        return redirect('transaction:exchange-details', fiat_from, fiat_to)

    context = {
        'navbar': 'exchange',
        'fiat': currency,
    }
    return render(request, 'transaction/dsh/dashboard/exchange_view.html', context)


@login_required(login_url='account:login')
@allowed_users(allowed_roles=['clients'])
@never_cache
def htmx_swap(request):
    fiat_name = request.GET.get('fiat_from')
    fiat = get_object_or_404(FiatCurrency, name=fiat_name)
    currency = FiatPortfolio.objects.filter(user=request.user.client, is_active=True).exclude(currency=fiat)
    print('currency', currency)
    context = {'currency': currency}
    return render(request, "transaction/dsh/dashboard/partials/swap_fiat.html", context)


class ExchangeFunds(TransactionCreateMixin):
    template_name = "transaction/dsh/dashboard/exchange.html"
    form_class = ExchangeForm

    success_url = reverse_lazy('transaction:transactions')

    def setup(self, request, *args, **kwargs):
        self.fiat_from = kwargs['fiat_from']
        self.fiat_to = kwargs['fiat_to']
        return super().setup(request, *args, **kwargs)

    def get_initial(self):
        initial = {'transaction_type': "EXCHANGE",
                   'status': "Successful",
                   }
        initial['payment'] = FiatCurrency.objects.get(name=self.fiat_from)
        initial['fiat_from'] = self.fiat_from
        initial['fiat_to'] = self.fiat_to
        return initial

    def form_valid(self, form):
        currency = FiatCurrency.objects.get(name=self.fiat_from)
        base_amount = form.cleaned_data.get('amount')
        receive_amount = form.cleaned_data.get('receive_amount')
        account = self.request.user
        # perform Exchange
        exchange = ExchangeRate.exchange_currency(
            base_currency=djmoney.money.Money(self.request.POST.get('amount_0'), str(currency.currency.currency)),
            receiving_currency=self.fiat_to,
            currency=self.fiat_from)
        fee = form.save(commit=False)
        fee.fees = exchange[1]
        payment_method = PaymentMethods.objects.get(name='Finease Bank Account Holder')
        fee.payment_methods = payment_method
        fee.save()

        #  deduction of money from exchange transaction
        currency = FiatCurrency.objects.get(name=self.fiat_from)
        fiat_wallet = FiatPortfolio.objects.get(user=self.request.user.client, currency=currency)
        exchange_fiat = FiatCurrency.objects.get(name=self.fiat_to)
        exchange_fiat_wallet = FiatPortfolio.objects.get(user=self.request.user.client, currency=exchange_fiat)
        fiat_wallet.balance -= base_amount
        fiat_wallet.save(update_fields=['balance'])
        exchange_fiat_balance = ExchangeRate.exchange_currency(
            base_currency=djmoney.money.Money(self.request.POST.get('amount_0'), str(currency.currency.currency)),
            receiving_currency=self.fiat_to,
            currency=self.fiat_from)
        exchange_fiat_wallet.balance += exchange_fiat_balance[0]
        exchange_fiat_wallet.save(update_fields=['balance'])
        amount = djmoney.money.Money(self.request.POST.get('amount_0'), str(currency.currency.currency))
        EmailSender.exchange_detail(email_address=account, name=account.name, amount=amount, fiat_from=self.fiat_from,
                                    fiat_to=self.fiat_to, ex_bal=exchange_fiat_wallet.balance,
                                    fee=exchange[1], balance=fiat_wallet.balance, ex_amt=exchange[0],
                                    date=timezone.now())

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        fiat = get_object_or_404(FiatCurrency, name=self.fiat_from)
        amount = djmoney.money.Money(1, str(fiat.currency.currency))
        exchange = ExchangeRate.exchange_currency(base_currency=amount, receiving_currency=self.fiat_to,
                                                  currency=self.fiat_from)
        fiat_wallet = get_object_or_404(FiatPortfolio, user=self.request.user.client, currency=fiat, is_active=True)
        swap_wallet = get_object_or_404(FiatCurrency, name=self.fiat_to)
        context = super().get_context_data(**kwargs)
        context.update({
            'navbar': "exchange",
            'currency': fiat_wallet,
            'swap_fiat': swap_wallet,
            'fiat_from': fiat,
            'exchange': exchange[0],
            'amount': 1,

        })
        return context


@login_required(login_url='account:login')
@allowed_users(allowed_roles=['clients'])
@never_cache
def hx_exchange(request, *args, **kwargs):
    fiat_from = kwargs.get('fiat_from')
    fiat = get_object_or_404(FiatCurrency, name=fiat_from)
    amount = djmoney.money.Money(request.GET.get('amount_0'), str(fiat.currency.currency))
    fiat_to = kwargs.get('fiat_to')
    exchange = ExchangeRate.exchange_currency(base_currency=amount, receiving_currency=fiat_to,
                                              currency=fiat_from)
    context = {'exchange': exchange[0], 'receive': exchange[1], 'result': exchange[2]}
    response = render(request, 'transaction/dsh/dashboard/partials/exchange.html', context)
    return response


@login_required(login_url='account:login')
@allowed_users(allowed_roles=['clients'])
@never_cache
def transactions(request):
    account = request.user.client
    trans = Transactions.objects.filter(user=account)[::-1]
    trans_list = []
    page = request.GET.get('page', 1)
    paginator = Paginator(trans, 10)
    try:
        users = paginator.page(page)
    except PageNotAnInteger:
        users = paginator.page(1)
    except EmptyPage:
        users = paginator.page(paginator.num_pages)
    for x in trans:
        trans_list.append(x)

    transaction = trans_list
    default_currency = FiatPortfolio.objects.filter(user=request.user.client, is_active=True)

    context = {'transaction': transaction,
               'transactions': users,
               'navbar': "transactions",
               'balance': default_currency,
               }

    return render(request, 'transaction/dsh/dashboard/transactions.html', context)


@login_required(login_url='account:login')
@allowed_users(allowed_roles=['clients'])
@never_cache
def hx_act_name(request):
    account_number = request.GET.get('account_number')
    acct_name = ''
    account = ''
    try:
        account_name = Account.objects.get(account_number=account_number)
        if account_name.account_type == 'Joint-checking Account':
            acct_name = account_name.account_name
        elif account_name.account_type == 'Business Account':
            acct_name = account_name.account_name
        else:
            acct_name = account_name.user.name
        account = account_name.user.profile_pic.url
    except Account.DoesNotExist:
        acct_name = 'Invalid Account Number'
    context = {'account_name': acct_name, 'user': account}
    return render(request, 'transaction/dsh/dashboard/partials/name.html', context)


@login_required(login_url='account:login')
@allowed_users(allowed_roles=['clients'])
@never_cache
def hx_search(request):
    account = request.user.client
    query = request.GET.get('q')
    if query:
        try:
            query_int = int(query)
        except ValueError:
            # if the query is not a valid integer, try to find the corresponding transaction type by name
            query_int = next((value for value, name in TRANSACTION_TYPE_CHOICES if name.lower() == query.lower()), None)
            if query_int is None:
                # if the transaction type name is not found, return an empty results
                results = Transactions.objects.filter(
                    Q(amount__icontains=query) |
                    Q(date__icontains=query) |
                    Q(trx_id=query) |
                    Q(status__icontains=query), user=account,
                )[::-1]
            else:
                results = Transactions.objects.filter(
                    Q(amount__icontains=query) |
                    Q(transaction_type=query_int) |
                    Q(date__icontains=query) |
                    Q(trx_id=query) |
                    Q(status__icontains=query), user=account,
                )[::-1]
        else:
            results = Transactions.objects.filter(
                Q(amount__icontains=query) |
                Q(transaction_type=query_int) |
                Q(date__icontains=query) |
                Q(trx_id=query) |
                Q(status__icontains=query), user=account,
            )[::-1]

    else:
        results = Transactions.objects.filter(user=account)[::-1]

    return render(request, 'transaction/dsh/dashboard/partials/transactions.html',
                  {'transactions': results, 'navbar': 'transactions'})


@login_required(login_url='account:login')
@allowed_users(allowed_roles=['clients'])
@never_cache
def view_all_balance(request):
    currencies = FiatPortfolio.objects.filter(user=request.user.client, is_active=True, )
    context = {'currency': currencies, 'navbar': 'home'}
    return render(request, 'transaction/dsh/dashboard/all_balance.html', context)


@login_required(login_url='account:login')
@allowed_users(allowed_roles=['clients'])
@never_cache
def add_new_account(request):
    client_account = FiatPortfolio.objects.filter(user=request.user.client).exclude(is_active=True)
    context = {'client_account': client_account, 'navbar': 'home'}
    if request.method == 'POST':
        account = request.POST.get('account')
        currency = FiatCurrency.objects.get(name=account)
        fiat_account = FiatPortfolio.objects.filter(user=request.user.client, currency=currency)
        fiat_account.update(is_active=True)
        messages.success(request, 'Fiat account created successfully!')
        return redirect('transaction:account-balances')
    return render(request, 'transaction/dsh/dashboard/add_new_account.html', context)


class Fund_card(TransactionCreateMixin):
    form_class = Card_Fund_Form
    template_name = 'transaction/dsh/dashboard/fund_card.html'
    success_url = reverse_lazy('transaction:transactions')

    def setup(self, request, *args, **kwargs):
        self.payment_method = kwargs['method']
        self.card_type = kwargs['card_type']
        self.payment = kwargs['fiat']
        return super().setup(request, *args, **kwargs)

    def get_initial(self):
        payment_method = PaymentMethods.objects.get(name=self.payment_method)
        fees = payment_method.transaction_fee
        currency = FiatCurrency.objects.get(name=self.payment)
        initial = {'transaction_type': "CARD FUNDING",
                   'payment_methods': payment_method,
                   'fees': djmoney.money.Money(fees.amount, str(currency.currency.currency)),
                   'status': "Successful",
                   }
        initial['payment'] = FiatCurrency.objects.get(name=self.payment)
        initial['fee'] = djmoney.money.Money(fees.amount, str(currency.currency.currency))
        return initial

    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        account = self.request.user.client
        payment_method = form.cleaned_data.get('payment_methods')
        method = PaymentMethods.objects.get(name=self.payment_method)
        currency = FiatCurrency.objects.get(name=self.payment)
        fees = method.transaction_fee

        # deduct the amount from the account
        client_account = FiatPortfolio.objects.get(user=account, currency=currency)
        client_account.balance -= amount
        client_account.balance -= djmoney.money.Money(fees.amount, str(currency.currency.currency))
        client_account.save(update_fields=['balance'])

        # fund card
        fiat = get_object_or_404(FiatCurrency, name=self.payment)
        card_type = get_object_or_404(Card_type, name=self.card_type)
        card_owner = get_object_or_404(Cards, user=account, account=fiat, card_type=card_type)
        card_owner.balance += amount
        card_owner.save(update_fields=['balance'])
        messages.success(self.request, f'Your card have been credited')

        form.save(commit=True)

        return super(Fund_card, self).form_valid(form)

    def get_context_data(self, **kwargs):
        payment_method = get_object_or_404(PaymentMethods, name=self.payment_method)
        currency = get_object_or_404(FiatCurrency, name=self.payment)
        fiat = get_object_or_404(FiatCurrency, name=self.payment)
        card_type = get_object_or_404(Card_type, name=self.card_type)
        card_owner = get_object_or_404(Cards, user=self.request.user.client, account=fiat, card_type=card_type)
        account = get_object_or_404(FiatPortfolio, user=self.request.user.client, currency=fiat, )
        context = super().get_context_data(**kwargs)
        context.update({
            'navbar': "card",
            'method': payment_method,
            'currency': currency,
            'card': card_owner,
            'account': account
        })
        return context


class Fund_card_withdrawal(TransactionCreateMixin):
    form_class = Card_Fund_Withdrawal_Form
    template_name = 'transaction/dsh/dashboard/card_withdrawal.html'
    success_url = reverse_lazy('transaction:transactions')

    def setup(self, request, *args, **kwargs):
        self.payment_method = kwargs['method']
        self.card_type = kwargs['card_type']
        self.payment = kwargs['fiat']
        return super().setup(request, *args, **kwargs)

    def get_initial(self):
        payment_method = PaymentMethods.objects.get(name=self.payment_method)
        fees = payment_method.transaction_fee
        currency = FiatCurrency.objects.get(name=self.payment)
        initial = {'transaction_type': "CARD WITHDRAWAL",
                   'payment_methods': payment_method,
                   'fees': djmoney.money.Money(fees.amount, str(currency.currency.currency)),
                   'status': "Successful",
                   'card_type': self.card_type
                   }
        initial['payment'] = FiatCurrency.objects.get(name=self.payment)
        initial['fee'] = djmoney.money.Money(fees.amount, str(currency.currency.currency))
        return initial

    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        account = self.request.user.client
        payment_method = form.cleaned_data.get('payment_methods')
        method = PaymentMethods.objects.get(name=self.payment_method)
        currency = FiatCurrency.objects.get(name=self.payment)
        fees = method.transaction_fee

        # deduct the amount from the account
        client_account = FiatPortfolio.objects.get(user=account, currency=currency)
        client_account.balance += amount
        client_account.balance += djmoney.money.Money(fees.amount, str(currency.currency.currency))
        client_account.save(update_fields=['balance'])

        # fund card
        fiat = get_object_or_404(FiatCurrency, name=self.payment)
        card_type = get_object_or_404(Card_type, name=self.card_type)
        card_owner = get_object_or_404(Cards, user=account, account=fiat, card_type=card_type)
        card_owner.balance -= amount
        card_owner.save(update_fields=['balance'])
        messages.success(self.request, f'Your {fiat} card have been credited')

        form.save(commit=True)

        return super(Fund_card_withdrawal, self).form_valid(form)

    def get_context_data(self, **kwargs):
        payment_method = get_object_or_404(PaymentMethods, name=self.payment_method)
        currency = get_object_or_404(FiatCurrency, name=self.payment)
        fiat = get_object_or_404(FiatCurrency, name=self.payment)
        card_type = get_object_or_404(Card_type, name=self.card_type)
        card_owner = get_object_or_404(Cards, user=self.request.user.client, account=fiat, card_type=card_type)
        account = get_object_or_404(FiatPortfolio, user=self.request.user.client, currency=fiat, )
        context = super().get_context_data(**kwargs)
        context.update({
            'navbar': "card",
            'method': payment_method,
            'currency': currency,
            'card_type': card_type,
            'card': card_owner,
            'account': account
        })
        return context


# views.py


def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None

@login_required(login_url='account:login')
@allowed_users(allowed_roles=['clients'])
def generate_pdf(request, id):
    account = request.user.client
    trans = Transactions.objects.get(user=account, id=id)

    context = {
        'transaction': trans
    }
    pdf = render_to_pdf('transaction/dsh/dashboard/transaction_receipt.html', context)
    if pdf and request.method == 'GET':
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{trans.transaction_type}/{trans.trx_id}.pdf"'
        return response
    return HttpResponse("Error generating PDF", status=500)

@login_required(login_url='login')
def investment(request):
    investment = Investment.objects.all()
    context = {
        'investment': investment,
        'navbar': 'investment'
    }
    if request.method == 'POST':
        investment_name = request.POST.get('investment_name')
        return redirect('transaction:investment_preview', investment_name)

    return render(request, "transaction/dsh/dashboard/new_investment.html", context)


def track_card(request):
    tracking_info = None
    if request.method == 'POST':
        track_no = request.POST.get('track_no')
        try:
            # Fetch the CardTracking instance using the tracking number
            tracking_info = Card_Trackings.objects.get(track_no=track_no)
        except Card_Trackings.DoesNotExist:
            tracking_info = None
    return render(request, 'transaction/dsh/dashboard/track_card.html', {'tracking_info': tracking_info})