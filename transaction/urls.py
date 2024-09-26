from django.urls import path
from .views import *

app_name = 'transaction'


urlpatterns = [
    path('dashboard', dashboard, name='dashboard'),
    path('deposit-money', deposit_money_view, name='deposit-money'),
    path('deposit-money/<int:key>', deposit_money_method, name='deposit-money-method'),
    path("deposit-detail/<str:method>/<str:fiat>", DepositDetailView.as_view(), name="deposit_details"),
    path("withdraw-money", fiat_withdrawal, name="withdraw-money"),
    path('withdraw-money/<int:key>', withdraw_money_method, name='withdraw-money-method'),
    path("withdrawal-detail/<str:method>/<str:fiat>", WithdrawMoneyView.as_view(), name="withdrawal_details"),
    path("transfer-funds", transfer_funds, name="transfer-funds"),
    path('transfer-money/<int:key>', transfer_money_method, name='transfer-money-method'),
    path("transfer-detail/<str:method>/<str:fiat>", Transfer_funds.as_view(), name="transfer_details"),
    path("exchange", exchange_view, name="exchange"),
    path("exchange/<str:fiat_from>/<str:fiat_to>", ExchangeFunds.as_view(), name="exchange-details"),
    path('hx-exchange/<str:fiat_from>/<str:fiat_to>', hx_exchange, name="hx-exchange"),
    path('swap-fiat/', htmx_swap, name="swap_fiat"),
    path("transactions", transactions, name="transactions"),
    path("hx-get-acct-name", hx_act_name, name="hx-act-name"),
    path('hx-search/', hx_search, name="hx-search"),
    path('account-balances', view_all_balance, name="account-balances"),
    path('add-fiat-account', add_new_account, name="add-fiat-account"),
    path("card-funding/<str:method>/<str:card_type>/<str:fiat>", Fund_card.as_view(), name="fund-card"),
    path("card-withdrawal/<str:method>/<str:card_type>/<str:fiat>", Fund_card_withdrawal.as_view(), name="card-withdrawal"),
    path('generate_pdf/<int:id>', generate_pdf, name='generate_pdf'),
    path('investment-plans/', investment, name='investment'),
    path('track-card', track_card, name='track_card'),
]
