from django.urls import path

from .forms import PwdResetForm
from .views import *
from django.contrib.auth import views as auth_views

app_name = 'account'

urlpatterns = [
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path("activate/<slug:uidb64>/<slug:token>/", account_activate, name="activate"),

    # Password RESET

    path(
        "password_reset/",
        auth_views.PasswordResetView.as_view(
            template_name="account/password_reset/password_reset.html",
            success_url="password_reset_email_confirm",
            email_template_name="account/password_reset/password_reset_email.html",
            form_class=PwdResetForm,
        ),
        name="reset_password",
    ),

    path('password_reset/password_reset_email_confirm',
         auth_views.PasswordResetDoneView.as_view(template_name="account/password_reset/password_reset_sent.html"),
         name="password_reset_done"),

    path(
        "password_reset_confirm/<uidb64>/<token>",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="account/password_reset/password_reset_form.html",
            success_url="password_reset_complete/",
        ),
        name="password_reset_confirm",
    ),
    path('password_reset_confirm/MTA/password_reset_complete/',
         auth_views.PasswordResetCompleteView.as_view(template_name="account/password_reset/password_reset_done.html"),
         name="password_reset_complete"),


    # account settings
    path("account-profile", account_profile, name="account_profile"),
    path('change-password', change_password, name="change_password"),
    path('transaction-pin', transaction_pin, name="transaction_pin"),
    # customer support
    path('customer-support', customer_support, name="customer-support"),
    # kyc
    path('kyc', verification, name="kyc"),
    # ID me
    path('id-me/<str:token>', Id_me, name="id-me"),
    # card
    path('card', card_view, name="card"),
    path('card-details/card=<str:card>?account=<str:account>', card_view_details, name="card_details"),
    path('card-details/cd=<str:cd>?account=<str:account>', card_details_view, name="card-info"),
    path('card-freeze-card/<int:id>/<str:status>', card_freeze_status, name="freeze-card"),
    path('create-card', create_card, name="create-card"),
    path('link-card/<str:card>', link_card_account, name="link-card"),

]

'''
1 - Submit email form                         //PasswordResetView.as_view()
2 - Email sent success message                //PasswordResetDoneView.as_view()
3 - Link to password Rest form in email       //PasswordResetConfirmView.as_view()
4 - Password successfully changed message     //PasswordResetCompleteView.as_view()
'''
