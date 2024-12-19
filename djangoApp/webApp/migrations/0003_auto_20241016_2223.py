# Generated by Django 5.1.2 on 2024-10-17 05:23

from django.db import migrations
from datetime import datetime

from webApp.models import Prescription, Inventory, OrderInformation, PrescriptionActivityLog


def populate_initial_data(apps, schema_editor):
    models = [
        'Patient',
        'Prescription',
        'Inventory',
        'OrderInformation',
        'PrescriptionActivityLog'
    ]
    Patient,Prescription,Inventory,OrderInformation,PrescriptionActivityLog = (apps.get_model('webApp',x) for x in models)

    new_patient = Patient(name="John Doe", date_of_birth="2000-01-01", address="1234 Patient Way",
                         phone_number="123-456-7890", email_address="example@email.com",
                         insurance_information="Blue Cross")
    new_patient.save()

    new_prescription = Prescription(patient=new_patient, medication="Ibuprofen", medication_amount="10 500mg doses",
                                      status="not_filled", prescription_number="Rx123456")
    new_prescription.save()

    new_inventory = Inventory(medicine="Ibuprofen", amount=100, expiration_date="2024-10-31")
    new_inventory.save()

    new_order = OrderInformation(product_name="Ibuprofen", product_id=new_inventory, product_amount=20.50,
                                   product_quantity=10, prescription_type="Prescription")
    new_order.save()

    new_log = PrescriptionActivityLog(pharmacist_name="Sharon ONeal", prescription_number="00001",
                                        patient=new_patient, medication=new_inventory, medication_amount=10,
                                        created_at=datetime.now(), updated_at=datetime.now(), order_number=new_order)
    new_log.save()


class Migration(migrations.Migration):

    dependencies = [
        ('webApp', '0002_orderinformation_prescriptionactivitylog'),
    ]

    operations = [
        migrations.RunPython(populate_initial_data)
    ]
