from django.contrib.auth.models import AbstractUser, User
from django.db import models
from django.utils.timezone import now


# Create your models here.
class Patient(models.Model):
    # Patient name
    name = models.CharField(max_length=255)

    # Date of birth
    date_of_birth = models.DateField()

    # Address
    address = models.TextField()

    # Phone number
    phone_number = models.CharField(max_length=15)

    # Email address
    email_address = models.EmailField()

    # Insurance information
    insurance_information = models.TextField()

    def __str__(self):
        return self.name

class Prescription(models.Model):
    STATUS_CHOICES = (
        ('not_filled', 'Not Filled'),
        ('filled', 'Filled'),
        ('picked_up', 'Picked Up'),
    )

    # Foreign key to link to the Patient model
    patient = models.ForeignKey(Patient, on_delete=models.SET_NULL, null=True, blank=True, related_name='prescriptions')

    # Medication name
    medication = models.CharField(max_length=255)

    # Medication amount
    medication_amount = models.CharField(max_length=100)  # Adjust based on your requirements

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    # Prescription number
    prescription_number = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return f"Prescription #{self.prescription_number} for {self.patient.name}"

class Inventory(models.Model):
    # Medicine name
    item = models.CharField(max_length=255)

    # Amount available
    amount = models.PositiveIntegerField()  # Use PositiveIntegerField for non-negative values

    # Expiration date
    expiration_date = models.DateField()

    # Prescription/ Non-Prescription
    PRESCRIPTION_CHOICES = [
        ('prescription', 'Prescription'),
        ('non-prescription', 'Non-Prescription'),
    ]

    prescription_type = models.CharField(max_length=60, choices=PRESCRIPTION_CHOICES, default="prescription")  # Prescription or Non-Prescription

    def __str__(self):
        return f"{self.item} - {self.amount} units"

class UserType(models.TextChoices):
    MANAGER = 'M', 'Manager'
    PHARMACIST = 'P', 'Pharmacist'
    TECHNICIAN = 'T', 'Technician'
    CASHIER = 'C', 'Cashier'

class User(AbstractUser):
    user_type = models.CharField(max_length=2, choices=UserType.choices)

    # Optional additional fields
    phone_number = models.CharField(max_length=15, blank=True)
    store_name = models.CharField(max_length=255, blank=True)  # For owners

    def __str__(self):
        return self.username
    
class OrderInformation(models.Model):
    PRESCRIPTION_CHOICES = [
        ('prescription', 'Prescription'),
        ('non-prescription', 'Non-Prescription'),
    ]

    product_name = models.CharField(max_length=200)
    product_id = models.ForeignKey(Inventory, on_delete=models.SET_NULL, null=True, blank=True)  # Allow null values
    product_amount = models.DecimalField(max_digits=10, decimal_places=2)  # Amount or price
    product_quantity = models.PositiveIntegerField()  # Quantity of the product ordered
    prescription_type = models.CharField(max_length=60, choices=PRESCRIPTION_CHOICES)  # Prescription or Non-Prescription

    def __str__(self):
        return f"Order for {self.product_quantity} of {self.product_name} ({self.prescription_type})"

    class Meta:
        verbose_name = "Order Information"
        verbose_name_plural = "Order Information"

class TransactionType(models.TextChoices):
        LOGIN = 'login'
        LOGOUT = 'logout'
        LOGIN_FAIL = 'login_fail'
        PURCHASE = 'purchase'
        INVENTORY_ADD = 'inventory_add'
        INVENTORY_REMOVE = 'inventory_remove'
        INVENTORY_UPDATE = 'inventory_update'

class Transaction(models.Model):
    transaction_type = models.CharField(max_length=40, choices=TransactionType.choices)
    details = models.CharField(max_length=500)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    quantity = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(default=now)

class PrescriptionActivityLog(models.Model):
    pharmacist_name = models.CharField(max_length=100)
    prescription_number = models.CharField(max_length=50, unique=True)
    patient = models.ForeignKey(Patient, on_delete=models.SET_NULL, null=True, blank=True)  # ForeignKey to Patient
    medication = models.ForeignKey(Inventory, on_delete=models.SET_NULL, null=True, blank=True)
    medication_amount = models.PositiveIntegerField() #Use positive integers as medication should never go negative
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp for when the record is created
    updated_at = models.DateTimeField(auto_now=True)  # Timestamp for when the record is updated
    order_number = models.ForeignKey(OrderInformation, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.prescription_number} - {self.patient.name} - {self.date} {self.time}"

    class Meta:
        verbose_name = "Prescription Activity Log"
        verbose_name_plural = "Prescription Activity Logs"
        ordering = ['created_at']

class Receipt(models.Model):
    order_data = models.JSONField()  # Store cart details as JSON
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Associate receipt with a user
    payment_method = models.CharField(max_length=50)  # e.g., "cash" or "card"
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)  # Total paid
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Receipt #{self.id} for {self.user.username}"