from django.urls import path
from .views import *

urlpatterns = [
    path('', home, name='home'),
    path('freelancer-payment', freelancer, name='freelancer'),
    path('subscription', subscription, name='subscription'),
    path('security', security, name='security'),
    path('fees', fees, name='fees'),
    path('business-account', business_acct, name='business_acct'),
    path('corporate-card', cooperate_card, name='corporate-card'),
    path('expense-management', expense_mgt, name='expense_mgt'),
    path('budgeting', budgeting, name='budgeting'),
    path('invoice', invoice, name='invoice'),
    path('reward', reward, name='reward'),
    path('about-us', about, name='about'),
    path('careers', career, name='career'),
    path('help-center', help_center, name='help_center'),
    path('terms-and-conditions', terms_conditions, name='terms')

]

