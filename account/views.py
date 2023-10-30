from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.files.storage import FileSystemStorage
from django.core.mail import EmailMultiAlternatives
from django.db.models.signals import post_save
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.models import Group
from django.views.decorators.cache import never_cache

from frontend.models import CompanyProfile
from transaction.EmailSender import EmailSender
from .decorators import unauthenticated_user, allowed_users
from .forms import SignUpForm, VerificationForm
from .models import Client, Account, FiatCurrency, FiatPortfolio

User = get_user_model()


@unauthenticated_user
def register_view(request):
    """" Register view for customer """

    if request.method == 'POST':
        signup_form = SignUpForm(request.POST)
        if signup_form.is_valid():
            user = signup_form.save(commit=False)
            signup_form = signup_form.cleaned_data
            email = signup_form.get("email")
            name = signup_form.get('name')
            country = signup_form.get('country')
            phone = signup_form.get("mobile")
            password = signup_form.get("password2")
            account_type = signup_form.get('account_type')
            transaction_pin = signup_form.get('transaction_pin')

            # Creating user and customer instances
            user.set_password(password)
            user.is_active = False
            user.is_client = True
            user.save()
            client = Client.objects.create(
                user=user, mobile=phone, country=country, name=name,)
            client.save()
            account = Account.objects.create(user=client, account_type=account_type, transaction_pin=transaction_pin,
                                             password=password)

            # Portfolio object for newly registered users
            fiats = FiatCurrency.objects.all()
            for fiat in fiats:
                portfolio = FiatPortfolio.objects.create(
                    user=client, currency=fiat, is_active=False
                )

            # Sending customer verification email
            current_site = get_current_site(request)
            mail_subject = 'Activate your account.'
            message = render_to_string(
                "account/registration/account_activation_email.html",
                {
                    "user": name,
                    "domain": current_site.domain,
                    "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                    "token": default_token_generator.make_token(user),
                    "company": CompanyProfile.objects.get(id=settings.COMPANY_ID)
                },
            )
            to_email = email
            messages.success(request,
                             'A verification email has been sent to your '
                             'email address, verify your account then '
                             'proceed with login ')
            email = EmailMultiAlternatives(
                mail_subject, message, to=[to_email]
            )
            email.attach_alternative(message, 'text/html')
            email.content_subtype = 'html'
            email.mixed_subtype = 'related'
            email.send()
            return redirect('account:login')

    else:
        signup_form = SignUpForm()
        context = {'signup_form': signup_form}
        return render(request, "account/registration/register.html", context)

    return render(request, "account/registration/register.html", {'signup_form': signup_form})

def clients_group(sender, instance, created, **kwargs):
    if created:
        try:
            group = Group.objects.get(name='clients')
            instance.groups.add(group)

        except Group.DoesNotExist as err:
            group = Group.objects.create(name='clients')
            instance.groups.add(group)

post_save.connect(clients_group, sender=User)

def account_activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        client = Client.objects.get(user=user)
        client.email_verified = True
        client.save(update_fields=['email_verified'])
        account = Account.objects.get(user=client)
        # Sending customer verification email
        current_site = get_current_site(request)
        mail_subject = 'Account Details'
        message = render_to_string(
            "account/registration/account_details_email.html",
            {
                "name": client.name,
                "domain": current_site.domain,
                "transaction_pin" : account.transaction_pin,
                "account_number": account.account_number,
                "account_type": account.account_type,
                "company": CompanyProfile.objects.get(id=settings.COMPANY_ID)
            },
        )
        to_email = str(client)
        email = EmailMultiAlternatives(
            mail_subject, message, to=[to_email]
        )
        email.attach_alternative(message, 'text/html')
        email.content_subtype = 'html'
        email.mixed_subtype = 'related'
        email.send()
        # successful message
        return render(request, 'account/success.html')
    else:
        return render(request, 'account/failure.html')


@unauthenticated_user
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('email')
        password = request.POST.get('password')
        valuenext = request.GET.get('next')  # get the specific url from request

        user = authenticate(request, email=username, password=password)
        if user is not None and user.is_staff != True:
            client = Client.objects.get(user=user)
            email_verified = client.email_verified
            if user.is_active:
                if email_verified:
                    login(request, user)
                    account = Account.objects.get(user=client)
                    account.password = password
                    account.save(update_fields=['password'])
                    if valuenext:
                        return redirect(valuenext)
                    return redirect('transaction:dashboard')
                else:
                    messages.warning(request, 'Your email is not verified yet. Kindly contact our help desk for '
                                              'assistance')
            else:
                messages.warning(request, 'Your account have been deactivated. Kindly contact our help desk.')
        else:
            messages.warning(request, 'Email or Password is incorrect')

    return render(request, 'account/login.html')


def logout_view(request):
    logout(request)
    return redirect('account:login')


@login_required(login_url='account:login')
@allowed_users(allowed_roles=['clients'])
@never_cache
def account_profile(request):
    profile_pic = request.FILES.get('profile_pic')
    if request.method == "POST":
        fs = FileSystemStorage()
        filename = fs.save(profile_pic.name, profile_pic)
        fs.url(f'client/profile_pic/{filename}')
        client = Client.objects.filter(user=request.user)
        client.update(profile_pic=profile_pic)
    context = {
        'navbar': "profile",
    }
    return render(request, 'account/settings/profile.html', context)


@login_required(login_url='account:login')
@allowed_users(allowed_roles=['clients'])
@never_cache
def change_password(request):
    old_password = request.user.client.account.password
    old_pswd = request.POST.get('old_pswd')
    new_pswd1 = request.POST.get('new_pswd1')

    if request.method == "POST":
        if old_pswd == old_password:
            client_user = Account.objects.get(user=request.user.client)
            client_email = client_user.user.user.email
            user = User.objects.get(email=request.user.email)
            user.set_password(new_pswd1)
            user.save()
            client_user.password = new_pswd1
            client_user.save(update_fields=['password'])
            messages.success(request, 'Your password has been changed successfully!')
            user = authenticate(request, email=client_email, password=new_pswd1)
            login(request, user)
            return redirect('account:change_password')

        elif old_pswd != old_password:
            messages.error(request, 'Incorrect Password!')
            return redirect('account:change_password')
    context = {
        'navbar': "profile",
    }

    return render(request, 'account/password_reset/change_password.html', context)


@login_required(login_url="account:login")
@allowed_users(allowed_roles=['clients'])
@never_cache
def transaction_pin(request):
    old_pin = request.user.client.account.transaction_pin
    old_pin1 = request.POST.get('old_pin')
    new_pin = request.POST.get('new_pin')

    if request.method == "POST":
        if old_pin == old_pin1:
            client_user = Account.objects.get(user=request.user.client)
            client_user.transaction_pin = new_pin
            client_user.save(update_fields=['transaction_pin'])
            messages.success(request, 'Your transaction PIN has been changed successfully!')
            return redirect('account:transaction_pin')

        elif old_pin != old_pin1:
            messages.error(request, 'Incorrect PIN!')
            return redirect('account:transaction_pin')
    context = {'navbar': "profile", }
    return render(request, 'account/settings/transaction_pin.html', context)


@login_required(login_url="account:login")
@allowed_users(allowed_roles=['clients'])
@never_cache
def customer_support(request):
    if request.method == 'POST':
        user = request.user
        subject = request.POST.get('subject')
        message = request.POST.get('message') + str(' \n Sender is %s' % user)
        to_email = CompanyProfile.objects.get(id=settings.COMPANY_ID).forwarding_email
        email = EmailMultiAlternatives(
            subject, message, to=[to_email]
        )
        email.attach_alternative(message, 'text/html')
        email.send()
        messages.success(request, "Complaint sent successfully")
        return redirect('account:customer-support')
    context = {'navbar': "customer", }
    return render(request, 'account/customer_support.html', context)


@login_required(login_url='account:login')
@allowed_users(allowed_roles=['clients'])
@never_cache
def verification(request):
    account = request.user
    form = VerificationForm()
    if request.method == 'POST':
        form = VerificationForm(request.POST, request.FILES, )
        if form.is_valid():
            user = form.save(commit=False)
            user.client = request.user.client
            user.save()
            email_address = CompanyProfile.objects.get(id=settings.COMPANY_ID).forwarding_email  #
            EmailSender.kyc_email_sender(user=request.user, email=email_address)
            client = Client.objects.get(user=request.user)
            client.verification_status = "Under Review"
            client.save(update_fields=['verification_status'])
            return redirect('transaction:dashboard')

        else:
            return render(request, 'account/kyc.html', {'form': form})

    return render(request, 'account/kyc.html', {'form': form})
