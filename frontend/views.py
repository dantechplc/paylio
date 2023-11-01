from django.shortcuts import render


# Create your views here.
from account.decorators import unauthenticated_user


@unauthenticated_user
def home(request):  # Home page
    return render(request, 'frontend/home.html')

@unauthenticated_user
def freelancer(request):
    return render(request, 'frontend/freelancer_payment.html')

@unauthenticated_user
def terms_conditions(request):
    return render(request, 'frontend/t_c.html')

@unauthenticated_user
def subscription(request):
    return render(request, 'frontend/subscription.html')

@unauthenticated_user
def security(request):
    return render(request, 'frontend/security.html')

@unauthenticated_user
def fees(request):
    return render(request, 'frontend/fees.html')

@unauthenticated_user
def business_acct(request):
    return render(request, 'frontend/bussiness_acct.html')

@unauthenticated_user
def cooperate_card(request):
    return render(request, 'frontend/cooperate_card.html')

@unauthenticated_user
def expense_mgt(request):
    return render(request, 'frontend/expense_mgt.html')

@unauthenticated_user
def budgeting(request):
    return render(request, 'frontend/budgeting.html')


@unauthenticated_user
def invoice(request):
    return render(request, 'frontend/invoice.html')


@unauthenticated_user
def reward(request):
    return render(request, 'frontend/reward.html')


@unauthenticated_user
def about(request):
    return render(request, 'frontend/about.html')


@unauthenticated_user
def career(request):
    return render(request, 'frontend/career.html')

@unauthenticated_user
def help_center(request):
    return render(request, 'frontend/help_center.html')



def error_404_view(request, exception):
    return render(request, 'frontend/404.html')


def error_500_view(request):
    return render(request, 'frontend/500.html')


def error_403_view(request, exception):
    return render(request, 'frontend/403.html')