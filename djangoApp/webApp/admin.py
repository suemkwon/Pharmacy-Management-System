from django import forms
from django.contrib import admin

from webApp.models import User, Transaction


class UserAdmin(admin.ModelAdmin):
    # List the fields you want to display in the admin
    list_display = (
        'id',
        'username',
        'first_name',
        'last_name',
        'email',
        'password',
        'is_superuser',
        'is_staff',
        'is_active',
        'user_type',
        'phone_number',
        'store_name',
        'date_joined',
        'last_login',
    )


admin.site.register(User, UserAdmin)

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_type', 'details', 'created_at','amount','quantity')
    list_filter = ('transaction_type',)
    fields = ('transaction_type', 'details', 'amount', 'quantity', 'created_at')
