from django.contrib import admin

from transaction.models import *


@admin.register(Transactions)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("user", 'payment_methods', 'status', 'amount', 'date')
