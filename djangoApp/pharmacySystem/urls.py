"""
URL configuration for pharmacySystem project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from webApp import views

urlpatterns = [
    path('',  views.home, name='home'),
    path('admin/', admin.site.urls),
    path('register/', views.register, name='register'),
    path('first-time-password/', views.first_time_password, name='first_time_password'),
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='users/logout.html'), name='logout'),
    path('password-reset/', views.password_reset, name='password_reset'),
    path('home/', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('profile/', views.profile, name='profile'),
    path('profile/update/<int:id>/', views.update_user, name='update_user'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('patient/', views.patient, name='patient'),
    path('staff/', views.staff, name='staff'),
    path('patient/create/', views.create_patient, name='create_patient'),
    path('staff/create/', views.create_pharmacy_staff, name='create_pharmacy_staff'),
    path('staff/update/<int:staff_id>/', views.update_pharmacy_staff, name='update_pharmacy_staff'),
    path('staff/delete/<int:staff_id>/', views.delete_pharmacy_staff, name='delete_pharmacy_staff'),
    path('patient/delete/<int:patient_id>/', views.delete_patient, name='delete_patient'),
    path('patient/confirm-delete-patient/<int:patient_id>/', views.confirm_delete_patient, name='confirm_delete_patient'),
    path('patient/update/<int:patient_id>', views.update_patient, name='update_patient'),   
    path('prescription_info/<int:patient_id>/', views.prescription_info, name='prescription_info'),
    path('unlock_account/',views.unlock_account, name='unlock_account'),
    path('prescription/', views.prescription, name='prescription'),
    path('prescription/new/', views.new_prescription, name='new_prescription'),
    path('prescription/update_amount/', views.update_medication_amount, name='update_medication_amount'),
    path('prescription/fill_prescription/<str:prescription_number>', views.fill_prescription, name='fill_prescription'),
    path('prescription/pick_up/<str:prescription_number>', views.pick_up_prescription, name='pick_up_prescription'),
    path('prescription/edit/<str:prescription_number>', views.edit_prescription, name='edit_prescription'),
    path('prescription/delete/<str:prescription_number>', views.delete_prescription, name='delete_prescription'),
    path('prescription-activity-log/', views.prescription_activity_log, name='prescription_activity_log'),
    path('inventory/', views.check_inventory, name='check_inventory'),
    path('inventory/add_inventory_item', views.add_inventory_item, name='add_inventory'),
    path('inventory/remove_expired_items', views.delete_expired_items, name='remove_expired_medicine'),
    path('order-medicine/', views.order_medicine, name='order_medicine'),
    path('order-success/', views.order_success, name='order_success'),
    path('add-to-cart/<int:item_id>/', views.add_to_cart, name='add_to_cart'),
    path('item-added-success/', views.item_added_success, name='item_added_success'),
    path('transactions/', views.TransactionListView.as_view(), name='list_transactions'),
    path('financial-report/', views.financial_report, name='financial_report'),
    path('checkout/', views.checkout, name='checkout'),
    path('payment/', views.payment, name='payment'),
    path('card-payment/', views.card_payment, name='card_payment'),
    path('cash-payment/', views.cash_payment, name='cash_payment'),
    path('payment-success/<int:receipt_id>/', views.payment_success, name='payment_success'),
    path('receipt/<int:receipt_id>/', views.generate_receipt, name='generate_receipt'),
    path('unlock-success/', views.unlock_success, name='unlock_success'),
    path('account-locked/', views.account_locked, name='account_locked'),
]
