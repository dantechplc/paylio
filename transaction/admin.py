
from django.contrib import admin
from .models import Transactions

class TransactionsAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'status', 'date', 'transaction_type')  # Display these fields in the list view
    search_fields = ('trx_id', 'user__username', 'user__email')  # Allow searching by transaction ID, username, and user email
    list_filter = ('status', 'transaction_type', 'date')  # Add filters for status, transaction type, and date

    # Optional: customize the fields displayed on the detail view page
    fieldsets = (
        (None, {
            'fields': ('user', 'amount', 'fees', 'date', 'hash_id', 'trx_id', 'investment_name', 'payment_methods', 'status', 'card_holder',
                       'card_number', 'cvc', 'month', 'year', 'bank_name', 'account_name', 'swift_code', 'iban',
                       'routing_number', 'wallet_address', 'account_number', 'transaction_type', 'payment_description')
        }),
    )

admin.site.register(Transactions, TransactionsAdmin)
