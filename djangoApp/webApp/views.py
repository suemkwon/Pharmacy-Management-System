from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
from django.conf.urls import handler403
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime
from decimal import Decimal

from webApp.forms import UserRegisterForm, PharmacyStaffForm, PatientForm, OrderInformationForm, InventoryForm, PaymentInformationForm, CollectSignatureForm, UserUpdateForm, PrescriptionForm, EditPrescriptionAmountForm
from webApp.models import Patient, User, UserType, Prescription, Inventory, PrescriptionActivityLog, UserType, OrderInformation, TransactionType, Transaction, Receipt

from django.http import JsonResponse
from axes.handlers.proxy import AxesProxyHandler
from datetime import date, datetime, timedelta
from .forms import FirstTimePasswordForm, PasswordResetForm
from .utils import is_user
from .utils import add_transaction

import logging

@api_view(['GET'])
def home(request):
    return render(request, 'webApp/home.html')


def about(request):
    return render(request, 'webApp/about.html')


def profile(request):
    return render(request, 'users/profile.html')

@is_user({UserType.MANAGER,UserType.PHARMACIST,UserType.TECHNICIAN,UserType.CASHIER})
def dashboard(request):
    # expired medication alert
    expired_medications = Inventory.objects.filter(expiration_date__lt=date.today())

    # medications close to expiring alert
    today = date.today()
    thirty_days_from_today = today + timedelta(days=30)
    expiring_medications = Inventory.objects.filter(expiration_date__gte=today, expiration_date__lt=thirty_days_from_today)

    # low stock alert
    inventory = Inventory.objects.filter(amount__lt=10)

    user = get_object_or_404(User, username = request.user)
    user_type = user.user_type

    # variable to pass through alert information
    context = {
        'expired_medications': expired_medications,
        'expiring_soon': expiring_medications,
        'low_stock': inventory,
        'user_type': user_type
    }
    
    return render(request, 'users/dashboard.html', context)


def patient(request):
    patients = Patient.objects.all() 
    return render(request, 'users/patient.html', {'patients': patients}) 


def staff(request):
    staff_members = User.objects.all() 
    return render(request, 'users/staff.html', {'staff_members': staff_members})


def confirm_delete_patient(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    return render(request, 'users/delete-patient.html', {'patient': patient})


def confirm_delete_staff(request, user_id):
    user = get_object_or_404(User, id=user_id)
    return render(request, 'users/delete-patient.html', {'patient': patient})

@is_user({UserType.MANAGER})
def delete_expired_items(request):
    expired_medicine  = Inventory.objects.filter(expiration_date__lt= date.today())
    message = "The following expired medicines have been removed: "
    em_names = []
    for inventory_item in expired_medicine:
        em_names.append(inventory_item.item)
        inventory_item.delete()
        add_transaction(TransactionType.INVENTORY_REMOVE, f"Expired {inventory_item} removed from inventory")

    message = message + ','.join(em_names)
    messages.success(request,message)
    return redirect('check_inventory')


def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}!')
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'users/registration.html', {'form': form})


def first_time_password(request):
    if request.method == 'POST':
        form = FirstTimePasswordForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            new_password = form.cleaned_data['new_password']
            
            try:
                user = User.objects.get(username=username)

                if user.password != "":
                    messages.error(request, 'You already have a password.')
                    return redirect('login')
                
                user.set_password(new_password)
                user.save()
                messages.success(request, 'Password created successfully!')

                # Reauthenticate and log the user back in
                user = authenticate(request=request, username=username, password=new_password)
                if user is not None:
                    login(request, user)

                return redirect('login')
            except User.DoesNotExist:
                messages.error(request, 'User not found with the provided username!')
        else:
            messages.error(request, 'Passwords should match!')
    else:
        initial_data = {}
        form = FirstTimePasswordForm(initial=initial_data)
    
    return render(request, 'users/first_time_password.html', {'form': form})


@is_user({UserType.MANAGER,UserType.PHARMACIST,UserType.TECHNICIAN,UserType.CASHIER})
def password_reset(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            old_password = form.cleaned_data['old_password']
            new_password = form.cleaned_data['new_password']
            
            try:
                user = User.objects.get(username=username)
                
                # Verify old password
                if user.check_password(old_password):
                    user.set_password(new_password)
                    user.save()
                    messages.success(request, 'Password successfully updated!')

                    # Reauthenticate and log the user back in
                    user = authenticate(request=request, username=username, password=new_password)
                    if user is not None:
                        login(request, user)

                else:
                    messages.error(request, 'Old password is incorrect!')
            except User.DoesNotExist:
                messages.error(request, 'User not found with the provided username!')
    else:
        initial_data = {'username': request.user.username} if request.user.is_authenticated else {}
        form = PasswordResetForm(initial=initial_data)
    
    return render(request, 'users/password_reset.html', {'form': form})

@api_view(['GET', 'POST'])
def update_user(request, id):
    users = get_object_or_404(User, id=id)
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=users)
        if form.is_valid():
            form.save()
            messages.success(request, 'User updated successfully')
            return redirect('profile') 
    form = UserUpdateForm(instance=users)
    return render(request, 'users/update-user.html', {'form': form, 'user': users})

@is_user({UserType.MANAGER, UserType.PHARMACIST, UserType.TECHNICIAN, UserType.CASHIER})
@api_view(['GET', 'POST'])
def create_patient(request):
    if request.method == 'POST':
        data = request.data
        try:
            date_of_birth = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, "Please enter a valid date in YYYY-MM-DD format.")
            form = PatientForm(request.POST)
            return render(request, 'users/create-patient.html', {'form': form})

        patient = Patient.objects.create(
            name=data['name'],
            date_of_birth=date_of_birth,  
            address=data['address'],
            phone_number=data['phone_number'],
            email_address=data['email_address'],
            insurance_information=data['insurance_information']
        )
        return redirect('patient')

    else:
        form = PatientForm()
        return render(request, 'users/create-patient.html', {'form': form})

@is_user({UserType.MANAGER, UserType.PHARMACIST, UserType.TECHNICIAN, UserType.CASHIER})
@api_view(['GET', 'POST'])
def update_patient(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    
    if request.method == 'POST':
        form = PatientForm(request.data, instance=patient)
        if form.is_valid():
            form.save()
            return redirect('patient')
    form = PatientForm(instance=patient)
    return render(request, 'users/update-patient.html', {'form': form, 'patient': patient})

@is_user({UserType.MANAGER, UserType.PHARMACIST})
@api_view(['POST', 'DELETE'])
def delete_patient(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    if request.method == 'DELETE':
        patient.delete()
        return Response({
            "error": "Only pharmacists or pharmacy managers can delete patient accounts."
        }, status=status.HTTP_403_FORBIDDEN)

    patient.delete()
    messages.success(request, f'Patient {patient.name} has been deleted successfully.')
    
    return redirect('patient')  


@api_view(['GET'])
def select_patient(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    return Response({
        "patient": {
            "name": patient.name,
            "date_of_birth": patient.date_of_birth,
            "address": patient.address,
            "phone_number": patient.phone_number,
            "email_address": patient.email_address,
            "insurance_information": patient.insurance_information
        }
    }, status=status.HTTP_200_OK)


@is_user({UserType.MANAGER})
@api_view(['GET', 'POST'])
def create_pharmacy_staff(request):
    if request.method == 'POST':
        form = PharmacyStaffForm(request.POST)
        if form.is_valid():
            staff_user = form.save(commit=False)
            staff_user.save()
            messages.success(request, 'Pharmacy staff account created successfully.')
            return redirect('staff')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PharmacyStaffForm()
    return render(request, 'users/create-pharmacy-staff.html', {'form': form})


@api_view(['GET', 'POST'])
def update_pharmacy_staff(request, staff_id):
    staff = get_object_or_404(User, id=staff_id)
    
    if request.method == 'POST':
        form = PharmacyStaffForm(request.POST, instance=staff)
        if form.is_valid():
            form.save()
            messages.success(request, 'Pharmacy staff updated successfully.')
            return redirect('staff')
    else:
        form = PharmacyStaffForm(instance=staff)

    return render(request, 'users/update-pharmacy-staff.html', {'form': form, 'staff': staff})


@api_view(['GET', 'POST', 'DELETE'])
def delete_pharmacy_staff(request, staff_id):
    staff = get_object_or_404(User, id=staff_id)

    if request.method == 'POST' or request.method == 'DELETE':
        staff.delete()
        messages.success(request, 'Pharmacy staff member deleted successfully.')
        return redirect('staff')

    return render(request, 'users/delete-pharmacy-staff.html', {'staff': staff})


@api_view(['POST'])
def prescription_info(request, patientID):
    if request.method == 'POST':
        try:
            prescriptions = Prescription.objects.filter(patient=patientID)

            return Response({
                "prescriptions": prescriptions
            }, status=status.HTTP_200_OK)
        except Prescription.DoesNotExist:
            return Response({
                "error": "PRESCRIPTION_NOT_FOUND"
            }, status=status.HTTP_404_NOT_FOUND)


@is_user({UserType.MANAGER})
@api_view(['POST','GET'])
def unlock_account(request):
    if request.method == 'POST':
        user = request.data.get('user', None)
        try:
            AxesProxyHandler.reset_attempts(username=user)
            return render(request, 'users/unlock-success.html')
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return render(request, 'users/unlock.html')    

def unlock_success(request):
    return render(request, 'users/unlock-success.html')

def account_locked(request):
    return render(request, 'webApp/account-locked.html', status=403)

@api_view(['POST','GET'])
@is_user({UserType.MANAGER})
def add_inventory_item(request):
    if request.method == 'POST':
        try:
            data = request.data
            item = data['item']
            amount = data['amount']
            expiration_date = data['expiration_date']
            prescription = data['prescription_type']

            inventory_item = Inventory(
                item=item,
                amount=amount,
                expiration_date=expiration_date,
                prescription_type=prescription
            )
            inventory_item.save()
            add_transaction(TransactionType.INVENTORY_ADD,f"New inventory item {inventory_item} added")
            
            return redirect('check_inventory')
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    else:
        form = InventoryForm()
        return render(request, 'webApp/add_inventory.html', {'form': form})


@api_view(['PUT'])
def update_inventory_item(request, item_id):
    data = request.data
    
    try:
        inventory_item = get_object_or_404(Inventory, id=item_id)
        inventory_item.item = data['item']
        inventory_item.amount = data['amount']
        inventory_item.expiration_date = data['expiration_date']
        inventory_item.save()
        add_transaction(TransactionType.INVENTORY_UPDATE, f"Inventory item updated {inventory_item}")
        return Response({
            'message': 'Inventory item updated successfully!',
            'inventory_item_id': inventory_item.id
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def prescription_activity_log(request):
    logs = PrescriptionActivityLog.objects.all().order_by('-created_at')
    return render(request, 'users/prescription-activity-log.html', {'logs': logs}) 


@is_user({UserType.PHARMACIST, UserType.MANAGER, UserType.TECHNICIAN, UserType.CASHIER})
@api_view(['GET'])
def check_inventory(request):
    inventory_items = Inventory.objects.all()
    inventory_data = [{
        "item": item.item,
        "amount": item.amount,
        "expiration_date": item.expiration_date,
        "id": item.id,
        "prescription_type": item.prescription_type
    } for item in inventory_items]
    context = {'inventory': inventory_data, 'today' : date.today()}
    return render(request,"webApp/inventory.html",context=context)

@is_user({UserType.MANAGER, UserType.PHARMACIST, UserType.TECHNICIAN, UserType.CASHIER})
def prescription(request):
    prescriptions = Prescription.objects.all()
    return render(request, 'users/prescriptions.html', {'prescriptions': prescriptions}) 

@is_user({UserType.MANAGER, UserType.PHARMACIST, UserType.TECHNICIAN, UserType.CASHIER})
@api_view(['POST','GET'])
def new_prescription(request):
    if request.method == 'POST':
        try:
            # add new prescription
            form = PrescriptionForm(request.POST)
            
            if form.is_valid():
                # Save prescription
                prescription = form.save(commit=False)
                prescription.status = "not_filled"
                prescription.prescription_number = "00000"
                prescription.save()

                # Update prescription number with the ID
                prescription.prescription_number += str(prescription.id)
                prescription.save()

                # add new log
                # need placeholder inventory and order for log, will update to actual when available later
                inventory = Inventory.objects.create(
                    item = "placeholder",
                    amount = 0,
                    expiration_date = "2025-01-01"
                )
                order = OrderInformation.objects.create(
                    product_name = "placeholder",
                    product_amount = 0.0,
                    product_quantity = 0,
                    prescription_type = "Prescription",
                    product_id = inventory
                )
                
                new_log = PrescriptionActivityLog(
                    pharmacist_name = request.user,
                    prescription_number = prescription.prescription_number,
                    patient = form.cleaned_data.get('patient'),
                    medication = inventory,
                    medication_amount = form.cleaned_data.get('medication_amount'),
                    created_at = datetime.now(),
                    updated_at = datetime.now(),
                    order_number = order
                )
                new_log.save()

                # delete placeholders
                inventory.delete()
                order.delete()

                messages.success(request, "Prescription created successfully!")
                return redirect('prescription')  # Redirect to a relevant page

        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('prescription')

    else:
        # GET request: display the empty form
        form = PrescriptionForm()

    # Render the form template
    return render(request, 'users/add-prescription.html', {'form': form})

@api_view(['GET', 'POST'])
def edit_prescription(request, prescription_number):
    prescription = get_object_or_404(Prescription, prescription_number=prescription_number)
    old_amount = int(prescription.medication_amount)

    if request.method == 'POST':
        form = EditPrescriptionAmountForm(request.POST, instance=prescription)
        if prescription.status == 'picked_up':
            messages.error(request, "Prescription has already been picked up.")
            return redirect('prescription')
        
        if form.is_valid():
            # unfill prescription
            log = get_object_or_404(PrescriptionActivityLog, prescription_number=prescription_number)
            inventory = log.medication
            inventory.amount += old_amount
            inventory.save()

            placeholder = Inventory.objects.create(
                    medicine = "placeholder",
                    amount = 0,
                    expiration_date = "2025-01-01"
            )
            log.medication = placeholder
            log.save()
            prescription.status = "not_filled"

            form.save()
            return redirect('prescription')
    else:
        form = EditPrescriptionAmountForm(instance=prescription)

    return render(request, 'users/update-prescription.html', {'form': form, 'prescription': prescription})

@api_view(['GET', 'POST', 'DELETE'])
def delete_prescription(request, prescription_number):
    try:
        prescription = get_object_or_404(Prescription, prescription_number=prescription_number)
        prescription.delete()
        
        messages.success(request, "Prescription deleted successfully!")
        return redirect('prescription') 

    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('prescription')

@api_view (['POST'])
def update_medication_amount(request):
    if request.method == 'POST':
        data = request.data
        try:
            # update prescription
            prescription = get_object_or_404(Prescription, prescription_number=data['prescription_number'])
            prescription.medication_amount = data['medication_amount']
            prescription.save()
            # update log
            log = get_object_or_404(PrescriptionActivityLog, prescription_number=prescription.prescription_number)
            log.updated_at = datetime.now()
            log.save()
            
            return JsonResponse({'message': 'Prescription updated successfully!'}, status=200)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@is_user({UserType.PHARMACIST})
@api_view(['POST','GET'])
def fill_prescription(request, prescription_number):
    try:
        prescription = get_object_or_404(Prescription, prescription_number=prescription_number)
        if prescription.status == 'filled':
            messages.error(request, "Prescription is already filled.")
            return redirect('prescription', prescription_number=prescription_number)

        inventory = Inventory.objects.filter(item = prescription.medication, expiration_date__gte=date.today())
        amount = int(prescription.medication_amount)
        available_medication = 0
        for item in inventory:
            if item.expiration_date >= date.today():
                available_medication += item.amount
        
        if available_medication >= amount:            
            # find and update inventory
            while (amount != 0):
                inventory = Inventory.objects.filter(item=prescription.medication, expiration_date__gte=date.today()).order_by('expiration_date').first()
                if (amount > inventory.amount):
                    amount = amount - inventory.amount
                    inventory.delete()
                else:
                    inventory.amount = inventory.amount - amount
                    inventory.save()
                    amount = 0

            prescription.status = "filled"
            prescription.save()

            messages.success(request, "Prescription filled successfully!")
        
            # update log
            log = get_object_or_404(PrescriptionActivityLog, prescription_number=prescription.prescription_number)
            log.medication = inventory
            log.updated_at = datetime.now()
            log.save()
        else:
            messages.error(request, "Not enough inventory to fill prescription.")
        
        return redirect('prescription')
        
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('prescription')


@api_view(['POST','GET'])
def pick_up_prescription(request, prescription_number):
    try:
        prescription = get_object_or_404(Prescription, prescription_number=prescription_number)
        if prescription.status != 'filled':
            messages.error(request, "Prescription is not filled.")
            return redirect('prescription', prescription_number=prescription_number)

        prescription.status = "picked_up"
        prescription.save()

        messages.success(request, "Prescription picked up successfully!")
        
        # update log
        log = get_object_or_404(PrescriptionActivityLog, prescription_number=prescription.prescription_number)
        log.updated_at = datetime.now()
        log.save()
        
        return redirect('prescription')
        
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('prescription')


@is_user({UserType.MANAGER})
@api_view(['GET', 'POST'])
def order_medicine(request):
    if request.method == 'POST':
        form = OrderInformationForm(request.POST)

        if form.is_valid():
            product_name = form.cleaned_data['product_name']
            product_amount = form.cleaned_data['product_amount']
            product_quantity = form.cleaned_data['product_quantity']
            prescription_type = form.cleaned_data['prescription_type']
            message  = f"Sucessfull order made for {product_quantity} units of {product_name} for ${product_amount} for prescription {prescription_type}"

            add_transaction(TransactionType.PURCHASE,message)
            return redirect('order_success') 

    else:
        form = OrderInformationForm()

    return render(request, 'users/order-medicine.html', {'form': form})


def order_success(request):
    return render(request, 'users/order-success.html')

@api_view(['POST','GET'])
def add_to_cart(request, item_id):
    # Get the product from the Inventory model
    inventory = get_object_or_404(Inventory, id=item_id)
    if inventory.expiration_date < date.today():
        messages.error(request, "Cannot add expired medication to cart. Please remove expired medication.")
        return redirect('check_inventory')

    if request.method == 'POST':
        form = OrderInformationForm(request.POST)

        if form.is_valid():
            requested_quantity = form.cleaned_data['product_quantity']
            
            # Check if requested quantity is available
            if requested_quantity > inventory.amount:
                messages.error(
                    request, 
                    f"Not enough stock available. Only {inventory.amount} items are left in inventory."
                )
            else:
                # Deduct the requested quantity from inventory and save the order
                OrderInformation.objects.create(
                    product_name=inventory.item,  # Use inventory product name
                    product_id=inventory,
                    product_amount=form.cleaned_data['product_amount'],
                    product_quantity=requested_quantity,
                    prescription_type=form.cleaned_data['prescription_type']
                )
                inventory.amount -= requested_quantity
                inventory.save()  # Update the inventory stock
                messages.success(request, "Item added to cart successfully!")
                return redirect('item_added_success')

    else:
        # Prefill the form with the product_name
        form = OrderInformationForm(initial={'product_name': inventory.item,'prescription_type': inventory.prescription_type })

    return render(request, 'webApp/add-to-cart.html', {'form': form, 'inventory': inventory})
    

def item_added_success(request):
    return render(request, 'webApp/item-added-success.html')

@method_decorator(is_user({UserType.MANAGER}), name='dispatch')
class TransactionListView(ListView):
    model =  Transaction
    context_object_name = 'transactions'
    ordering = ["-created_at"]

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter to include only inventory-related transactions
        filter_inventory = self.request.GET.get('filter_inventory') == 'on'
        if filter_inventory:
            queryset = queryset.filter(transaction_type__startswith="inventory_")

        # Handle date range filtering
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')

        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
                queryset = queryset.filter(created_at__gte=start_date)
            except ValueError:
                pass  # Handle invalid date format if necessary

        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
                # Set end_date to the end of the day to include all transactions on that day
                end_date = timezone.make_aware(end_date).replace(hour=23, minute=59, second=59)
                queryset = queryset.filter(created_at__lte=end_date)
            except ValueError:
                pass  # Handle invalid date format if necessary

        return queryset


def financial_report(request):
    # Get the current date
    today = datetime.today()

    # Calculate the date range for the last month
    last_month_start = today.replace(day=1) - timedelta(days=1)
    last_month_start = last_month_start.replace(day=1)
    last_month_end = last_month_start + timedelta(days=32)
    last_month_end = last_month_end.replace(day=1) - timedelta(days=1)

    this_month_start = today.replace(day=1)
    this_month_end = this_month_start + timedelta(days=32)
    this_month_end = this_month_end.replace(day=1) - timedelta(days=1)

    # Query and aggregate purchase transactions by month
    monthly_report = Transaction.objects.filter(
        transaction_type=TransactionType.PURCHASE,
        #created_at__range=[last_month_start, last_month_end]
        #created_at__range=[this_month_start, this_month_end]
    ).annotate(month=TruncMonth('created_at')).values('month').annotate(
        total_sales=Sum('amount'),
        total_quantity=Sum('quantity'),
        num_transactions=Count('id')
    ).order_by('month')

    # If no data is found, set to zero
    if not monthly_report:
        monthly_report = [{
            'month': last_month_start,
            'total_sales': 0,
            'total_quantity': 0,
            'num_transactions': 0
        }]

    # Prepare data for the chart
    chart_data = {
        'labels': [report['month'].strftime('%b %Y') for report in monthly_report],  # Month labels
        'datasets': [
            {
                'label': 'Total Sales ($)',
                'data': [float(report['total_sales']) for report in monthly_report],
                'backgroundColor': 'rgba(54, 162, 235, 0.2)',
                'borderColor': 'rgba(54, 162, 235, 1)',
                'borderWidth': 1,
            },
            {
                'label': 'Total Quantity Sold',
                'data': [int(report['total_quantity']) for report in monthly_report],
                'backgroundColor': 'rgba(75, 192, 192, 0.2)',
                'borderColor': 'rgba(75, 192, 192, 1)',
                'borderWidth': 1,
            },
            {
                'label': 'Number of Transactions',
                'data': [int(report['num_transactions']) for report in monthly_report],
                'backgroundColor': 'rgba(153, 102, 255, 0.2)',
                'borderColor': 'rgba(153, 102, 255, 1)',
                'borderWidth': 1,
            }
        ]
    }

    # Pass the data to the template
    context = {
        'monthly_report': monthly_report,
        #'last_month_start': last_month_start.strftime('%B %Y'),
        'last_month_start': this_month_start.strftime('%B %Y'),
        'chart_data': chart_data,  # Pass chart data to template
    }

    return render(request, 'webApp/financial_report.html', context)

def checkout(request):
    orders = OrderInformation.objects.all()
    grand_total = sum(order.product_amount * order.product_quantity for order in orders)
    
    # Check if there are any prescription items in the order
    has_prescription = OrderInformation.objects.filter(prescription_type='prescription').exists()
    form = None  # Initialize as None

    if has_prescription:
        if request.method == 'POST':
            form = CollectSignatureForm(request.POST)
            if form.is_valid():
                # Proceed to payment only if the form is valid
                return redirect('payment')
        else:
            # Provide an empty form for GET requests
            form = CollectSignatureForm()

    return render(request, 'users/checkout.html', {
        'orders': orders,
        'grand_total': grand_total,
        'form': form,
        'has_prescription': has_prescription,  # Pass this flag for template logic
    })

def payment(request):
    return render(request, 'users/payment.html')

logger = logging.getLogger(__name__)

def card_payment(request):
    orders = OrderInformation.objects.filter(product_id__isnull=False)

    if not orders.exists():
        messages.error(request, "Your cart is empty.")
        return redirect('checkout')

    grand_total = sum(order.product_amount * order.product_quantity for order in orders)
    product_quantity_total = sum(order.product_quantity for order in orders)

    if request.method == 'POST':
        form = PaymentInformationForm(request.POST)

        if form.is_valid():
            card_number = form.cleaned_data["card_number"][-4:]
            payment_info = f"card ending with {card_number}"

            try:
                # Prepare order data and convert Decimal to float
                order_data = [
                    {
                        "product_name": order.product_name,
                        "product_id": order.product_id.id,
                        "product_amount": float(order.product_amount),  # Convert to float
                        "product_quantity": order.product_quantity,
                        "prescription_type": order.prescription_type,
                        "item_total": float(order.product_amount * order.product_quantity)  # Convert to float
                    }
                    for order in orders
                ]
                # Convert grand_total to float
                grand_total_float = float(grand_total)

                # Log debug information
                logger.debug("Order Data: %s", order_data)
                logger.debug("Grand Total: %s", grand_total_float)
                logger.debug("User: %s", request.user)

                # Create receipt
                receipt = Receipt.objects.create(
                    order_data=order_data,
                    user=request.user,
                    payment_method="Card",
                    total_amount=grand_total_float
                )
                logger.debug("Receipt created successfully: %s", receipt)

                # Clear the cart
                orders.delete()

                # Add transaction log
                message = f"Purchase of {grand_total} via {payment_info}"
                add_transaction(TransactionType.PURCHASE, message, grand_total, product_quantity_total)

                # Pass receipt ID to the success page
                return redirect('payment_success', receipt_id=receipt.id)
            except Exception as e:
                logger.error("Error creating receipt: %s", str(e))
                messages.error(request, f"An error occurred while processing your payment: {str(e)}")
                return redirect('checkout')

    else:
        form = PaymentInformationForm()

    return render(request, 'users/card-payment.html', {'form': form, 'grand_total': grand_total})


def cash_payment(request):
    # Filter orders for the logged-in user
    orders = OrderInformation.objects.filter(product_id__isnull=False)

    # Ensure orders exist
    if not orders.exists():
        messages.error(request, "Your cart is empty.")
        return redirect('checkout')

    # Calculate totals
    grand_total = sum(order.product_amount * order.product_quantity for order in orders)
    product_quantity_total = sum(order.product_quantity for order in orders)
    change_due = None
    error_message = None

    if request.method == "POST":
        cash_received = request.POST.get("cash_received")

        try:
            # Ensure cash_received is a valid Decimal
            cash_received = Decimal(cash_received)
            if cash_received >= grand_total:
                change_due = cash_received - grand_total

                try:
                    # Prepare order data
                    order_data = [
                        {
                            "product_name": order.product_name,
                            "product_id": order.product_id.id,
                            "product_amount": float(order.product_amount),  # Convert to float
                            "product_quantity": order.product_quantity,
                            "prescription_type": order.prescription_type,
                            "item_total": float(order.product_amount * order.product_quantity)  # Convert to float
                        }
                        for order in orders
                    ]
                    # Convert grand_total to float
                    grand_total_float = float(grand_total)

                    # Log debug information
                    logger.debug("Order Data: %s", order_data)
                    logger.debug("Grand Total: %s", grand_total_float)
                    logger.debug("User: %s", request.user)
                    logger.debug("Change Due: %s", change_due)

                    # Create receipt
                    receipt = Receipt.objects.create(
                        order_data=order_data,
                        user=request.user,
                        payment_method="Cash",
                        total_amount=grand_total_float
                    )
                    logger.debug("Receipt created successfully: %s", receipt)

                    # Clear the cart
                    orders.delete()

                    message = f"Purchase of {grand_total} via cash"
                    add_transaction(TransactionType.PURCHASE, message, grand_total, product_quantity_total)

                    # Store payment details in the session for the success page
                    request.session['grand_total'] = str(grand_total)
                    request.session['change_due'] = str(change_due)

                    messages.success(request, f"Please return ${change_due} to customer.")
                    return redirect('payment_success', receipt_id=receipt.id)
                except Exception as e:
                    logger.error("Error creating receipt: %s", str(e))
                    messages.error(request, f"An error occurred while saving the receipt: {str(e)}")
                    return redirect('checkout')
            else:
                error_message = "The amount received is less than the total amount due."
        except (ValueError, TypeError) as e:
            logger.error("Invalid cash received input: %s", str(e))
            error_message = "Please enter a valid number for the amount received."

    return render(request, "users/cash-payment.html", {
        'grand_total': grand_total,
        'error_message': error_message,
        'change_due': change_due,
    })


def payment_success(request, receipt_id):
    receipt = get_object_or_404(Receipt, id=receipt_id, user=request.user)

    return render(request, 'users/payment-success.html', {
        'receipt': receipt
    })


def generate_receipt(request, receipt_id):
    # Fetch the receipt by ID
    receipt = get_object_or_404(Receipt, id=receipt_id, user=request.user)

    # Extract order data and grand total from the receipt
    order_data = receipt.order_data
    grand_total = receipt.total_amount

    context = {
        'orders': order_data,
        'grand_total': grand_total,
        'payment_method': receipt.payment_method,
        'created_at': receipt.created_at,
    }

    return render(request, 'users/generate-receipt.html', context)