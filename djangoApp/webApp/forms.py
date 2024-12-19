from django.contrib.auth.forms import UserCreationForm

from django import forms

from webApp.models import User, Patient, UserType, OrderInformation, Inventory, Prescription

from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password

from webApp.models import User

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username','email','password1','password2','user_type','phone_number']

class InventoryForm(forms.ModelForm):
    class Meta:
        model = Inventory
        fields = '__all__'
        widgets = {
            'expiration_date': forms.DateInput(attrs={'type':'date'})
        }

class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ['name', 'date_of_birth', 'address', 'phone_number', 'email_address', 'insurance_information']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type':'date'})
        }

class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = ['patient', 'medication', 'medication_amount', 'status']
        widgets = {
            'status': forms.TextInput(attrs={'readonly': 'readonly'}),  # Make the field readonly
        }

    def __init__(self, *args, **kwargs):
        super(PrescriptionForm, self).__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['status'].initial = 'not_filled'

class EditPrescriptionAmountForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = ['patient', 'medication', 'medication_amount', 'status']
        widgets = {
            'patient': forms.TextInput(attrs={'readonly': 'readonly'}),  # Make the field readonly
            'medication': forms.TextInput(attrs={'readonly': 'readonly'}),
            'status': forms.TextInput(attrs={'readonly': 'readonly'}),
        }

class PharmacyStaffForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'phone_number', 'store_name', 'user_type']

    def __init__(self, *args, **kwargs):
        super(PharmacyStaffForm, self).__init__(*args, **kwargs)
        self.fields['store_name'].required = False 
        self.fields['user_type'].choices = UserType.choices  

    def clean(self):
        cleaned_data = super().clean()
        user_type = cleaned_data.get('user_type')
        store_name = cleaned_data.get('store_name')


        if user_type == UserType.MANAGER and not store_name:
            self.add_error('store_name', 'Store name is required for managers.')
        
        return cleaned_data


class PasswordResetForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'readonly': 'readonly'}) # Prevent user modification
    )
    old_password = forms.CharField(widget=forms.PasswordInput)
    new_password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if new_password and confirm_password:
            if new_password != confirm_password:
                raise forms.ValidationError("New passwords don't match!")
        
        return cleaned_data

class FirstTimePasswordForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput
    )
    new_password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if new_password and confirm_password:
            if new_password != confirm_password:
                raise forms.ValidationError("New passwords don't match!")
        
        return cleaned_data
    
class UserUpdateForm(forms.ModelForm):
    phone_number = forms.CharField(required=False)
    store_name = forms.CharField(required=False)

    class Meta:
        model = User
        fields = ['username', 'phone_number', 'store_name', 'user_type']

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if phone_number == '':
            return self.instance.phone_number
        return phone_number

    def clean_store_name(self):
        store_name = self.cleaned_data.get('store_name')
        if store_name == '':
            return self.instance.store_name
        return store_name


class OrderInformationForm(forms.ModelForm):
    class Meta:
        model = OrderInformation
        fields = ['product_name', 'product_amount', 'product_quantity', 'prescription_type']
        widgets = {
            'product_name': forms.TextInput(attrs={'readonly': 'readonly'}),
            'prescription_type': forms.TextInput(attrs={'readonly': 'readonly'})  # Make the field readonly
        }


class PaymentInformationForm(forms.Form):
    first_name = forms.CharField(max_length=100, label='Cardholder First Name')
    last_name = forms.CharField(max_length=100, label='Cardholder Last Name')
    card_number = forms.CharField(max_length=16, label='Card Number', widget=forms.TextInput(attrs={'placeholder': '1234 5678 9012 3456'}))
    expiration_date = forms.CharField(max_length=5, label='Expiration Date (MM/YY)', widget=forms.TextInput(attrs={'placeholder': 'MM/YY'}))
    cvv = forms.CharField(max_length=3, label='CVV', widget=forms.TextInput(attrs={'placeholder': '123'})) 


class CollectSignatureForm(forms.Form):
    signature = forms.CharField(
        max_length=255,
        required=True,
        error_messages={'required': 'This field is required.'},
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your name as signature'
        }),
        label="Please type your signature below:"
    )
