from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from .models import *


# Register your models here.

class UserAdmin(UserAdmin):
    """Define admin model for custom User model with no username field."""
    fieldsets = (
        (_('password'), {'fields': ('password',)}),
        (_('Personal info'), {'fields': ('email', 'name')}),
        (_('Permissions'), {'fields': ('is_active', 'is_client', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    list_display = ('email', 'is_client', 'is_staff',)
    search_fields = ('email',)
    ordering = ('email',)


admin.site.register(get_user_model(), UserAdmin)
admin.site.register(Client)
admin.site.register(KYC)
admin.site.register(next_of_kin)
admin.site.register(Account)
admin.site.register(JointAccount)
admin.site.register(Joint_Account_KYC)
admin.site.register(ExchangeRate)
admin.site.register(FiatCurrency)
admin.site.register(Investment)
admin.site.register(Investment_profile)
admin.site.register(PaymentMethods)
admin.site.register(Banks)
admin.site.register(Id_ME)
admin.site.register(AuthorizationToken)
admin.site.register(Cards)
admin.site.register(Card_type)
admin.site.register(OTP)


@admin.register(Card_Trackings)
class Tracking(admin.ModelAdmin):
    list_display = ('client', 'track_no', 'status', 'delivery_date')
    search_fields = ('client', 'track_no', 'status', 'delivery_date')


admin.site.register(CardTrackingHistory)

@admin.register(FiatPortfolio)
class FiatPortfolioAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance')
    search_fields = ('user__username', 'user__email')
