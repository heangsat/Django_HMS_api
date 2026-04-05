# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Appointment(models.Model):
    appointmentid = models.AutoField(
        db_column="AppointmentID", primary_key=True
    )  # Field name made lowercase.
    patientid = models.ForeignKey(
        "Patient", models.DO_NOTHING, db_column="PatientID"
    )  # Field name made lowercase.
    doctorid = models.ForeignKey(
        "Doctor", models.DO_NOTHING, db_column="DoctorID"
    )  # Field name made lowercase.
    appointmentdate = models.DateField(
        db_column="AppointmentDate", blank=True, null=True
    )  # Field name made lowercase.
    appointmenttime = models.TimeField(
        db_column="AppointmentTime", blank=True, null=True
    )  # Field name made lowercase.
    status = models.CharField(
        db_column="Status", max_length=20, blank=True, null=True
    )  # Field name made lowercase.
    remarks = models.TextField(
        db_column="Remarks", blank=True, null=True
    )  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = "Appointment"


class Bill(models.Model):
    billid = models.AutoField(
        db_column="BillID", primary_key=True
    )  # Field name made lowercase.
    patientid = models.ForeignKey(
        "Patient", models.DO_NOTHING, db_column="PatientID"
    )  # Field name made lowercase.
    appointmentid = models.ForeignKey(
        Appointment, models.DO_NOTHING, db_column="AppointmentID", blank=True, null=True
    )  # Field name made lowercase.
    admissionid = models.ForeignKey(
        "Inpatient", models.DO_NOTHING, db_column="AdmissionID", blank=True, null=True
    )  # Field name made lowercase.
    billdate = models.DateField(
        db_column="BillDate", blank=True, null=True
    )  # Field name made lowercase.
    totalamount = models.DecimalField(
        db_column="TotalAmount", max_digits=12, decimal_places=2, blank=True, null=True
    )  # Field name made lowercase.
    status = models.CharField(
        db_column="Status", max_length=20, blank=True, null=True
    )  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = "Bill"


class Department(models.Model):
    objects = models.Manager()
    DoesNotExist: type[Exception]
    deptid = models.AutoField(
        db_column="DeptID", primary_key=True
    )  # Field name made lowercase.
    deptname = models.CharField(
        db_column="DeptName", max_length=50
    )  # Field name made lowercase.
    description = models.TextField(
        db_column="Description", blank=True, null=True
    )  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = "Department"


class Doctor(models.Model):
    doctorid = models.AutoField(
        db_column="DoctorID", primary_key=True
    )  # Field name made lowercase.
    firstname = models.CharField(
        db_column="FirstName", max_length=50
    )  # Field name made lowercase.
    lastname = models.CharField(
        db_column="LastName", max_length=50
    )  # Field name made lowercase.
    gender = models.CharField(
        db_column="Gender", max_length=10, blank=True, null=True
    )  # Field name made lowercase.
    phone = models.CharField(
        db_column="Phone", max_length=20, blank=True, null=True
    )  # Field name made lowercase.
    email = models.CharField(
        db_column="Email", max_length=100, blank=True, null=True
    )  # Field name made lowercase.
    deptid = models.ForeignKey(
        Department, models.DO_NOTHING, db_column="DeptID", blank=True, null=True
    )  # Field name made lowercase.
    specialization = models.CharField(
        db_column="Specialization", max_length=100, blank=True, null=True
    )  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = "Doctor"


class Inpatient(models.Model):
    admissionid = models.AutoField(
        db_column="AdmissionID", primary_key=True
    )  # Field name made lowercase.
    patientid = models.ForeignKey(
        "Patient", models.DO_NOTHING, db_column="PatientID"
    )  # Field name made lowercase.
    roomid = models.ForeignKey(
        "Ward", models.DO_NOTHING, db_column="RoomID"
    )  # Field name made lowercase.
    admissiondate = models.DateField(
        db_column="AdmissionDate", blank=True, null=True
    )  # Field name made lowercase.
    dischargedate = models.DateField(
        db_column="DischargeDate", blank=True, null=True
    )  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = "Inpatient"


class Medicalrecord(models.Model):
    recordid = models.AutoField(
        db_column="RecordID", primary_key=True
    )  # Field name made lowercase.
    patientid = models.ForeignKey(
        "Patient", models.DO_NOTHING, db_column="PatientID"
    )  # Field name made lowercase.
    doctorid = models.ForeignKey(
        Doctor, models.DO_NOTHING, db_column="DoctorID"
    )  # Field name made lowercase.
    visitdate = models.DateField(
        db_column="VisitDate", blank=True, null=True
    )  # Field name made lowercase.
    diagnosis = models.TextField(
        db_column="Diagnosis", blank=True, null=True
    )  # Field name made lowercase.
    treatment = models.TextField(
        db_column="Treatment", blank=True, null=True
    )  # Field name made lowercase.
    allergies = models.TextField(
        db_column="Allergies", blank=True, null=True
    )  # Field name made lowercase.
    notes = models.TextField(
        db_column="Notes", blank=True, null=True
    )  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = "MedicalRecord"


class Medicine(models.Model):
    medicineid = models.AutoField(
        db_column="MedicineID", primary_key=True
    )  # Field name made lowercase.
    medicinename = models.CharField(
        db_column="MedicineName", max_length=100
    )  # Field name made lowercase.
    genericname = models.CharField(
        db_column="GenericName", max_length=100, blank=True, null=True
    )  # Field name made lowercase.
    stockquantity = models.IntegerField(
        db_column="StockQuantity", blank=True, null=True
    )  # Field name made lowercase.
    unitprice = models.DecimalField(
        db_column="UnitPrice", max_digits=10, decimal_places=2, blank=True, null=True
    )  # Field name made lowercase.
    expirydate = models.DateField(
        db_column="ExpiryDate", blank=True, null=True
    )  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = "Medicine"


class Patient(models.Model):
    objects = models.Manager()
    DoesNotExist: type[Exception]
    patientid = models.AutoField(
        db_column="PatientID", primary_key=True
    )  # Field name made lowercase.
    firstname = models.CharField(
        db_column="FirstName", max_length=50
    )  # Field name made lowercase.
    lastname = models.CharField(
        db_column="LastName", max_length=50
    )  # Field name made lowercase.
    gender = models.CharField(
        db_column="Gender", max_length=10, blank=True, null=True
    )  # Field name made lowercase.
    dateofbirth = models.DateField(
        db_column="DateOfBirth", blank=True, null=True
    )  # Field name made lowercase.
    phone = models.CharField(
        db_column="Phone", max_length=20, blank=True, null=True
    )  # Field name made lowercase.
    email = models.CharField(
        db_column="Email", max_length=100, blank=True, null=True
    )  # Field name made lowercase.
    address = models.TextField(
        db_column="Address", blank=True, null=True
    )  # Field name made lowercase.
    bloodgroup = models.CharField(
        db_column="BloodGroup", max_length=5, blank=True, null=True
    )  # Field name made lowercase.
    registrationdate = models.DateField(
        db_column="RegistrationDate", blank=True, null=True
    )  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = "Patient"


class Prescription(models.Model):
    prescriptionid = models.AutoField(
        db_column="PrescriptionID", primary_key=True
    )  # Field name made lowercase.
    recordid = models.ForeignKey(
        Medicalrecord, models.DO_NOTHING, db_column="RecordID"
    )  # Field name made lowercase.
    prescriptiondate = models.DateField(
        db_column="PrescriptionDate", blank=True, null=True
    )  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = "Prescription"


class Prescriptiondetail(models.Model):
    pk = models.CompositePrimaryKey("prescriptionid", "medicineid")
    prescriptionid = models.ForeignKey(
        Prescription, models.DO_NOTHING, db_column="PrescriptionID"
    )  # Field name made lowercase.
    medicineid = models.ForeignKey(
        Medicine, models.DO_NOTHING, db_column="MedicineID"
    )  # Field name made lowercase.
    dosage = models.CharField(
        db_column="Dosage", max_length=100, blank=True, null=True
    )  # Field name made lowercase.
    duration = models.CharField(
        db_column="Duration", max_length=50, blank=True, null=True
    )  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = "PrescriptionDetail"


class Staff(models.Model):
    staffid = models.AutoField(
        db_column="StaffID", primary_key=True
    )  # Field name made lowercase.
    firstname = models.CharField(
        db_column="FirstName", max_length=50
    )  # Field name made lowercase.
    lastname = models.CharField(
        db_column="LastName", max_length=50
    )  # Field name made lowercase.
    role = models.CharField(
        db_column="Role", max_length=50, blank=True, null=True
    )  # Field name made lowercase.
    phone = models.CharField(
        db_column="Phone", max_length=20, blank=True, null=True
    )  # Field name made lowercase.
    email = models.CharField(
        db_column="Email", max_length=100, blank=True, null=True
    )  # Field name made lowercase.
    hiredate = models.DateField(
        db_column="HireDate", blank=True, null=True
    )  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = "Staff"


class Ward(models.Model):
    roomid = models.AutoField(
        db_column="RoomID", primary_key=True
    )  # Field name made lowercase.
    roomnumber = models.CharField(
        db_column="RoomNumber", max_length=10
    )  # Field name made lowercase.
    roomtype = models.CharField(
        db_column="RoomType", max_length=20, blank=True, null=True
    )  # Field name made lowercase.
    status = models.CharField(
        db_column="Status", max_length=20, blank=True, null=True
    )  # Field name made lowercase.
    priceperday = models.DecimalField(
        db_column="PricePerDay", max_digits=10, decimal_places=2, blank=True, null=True
    )  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = "Ward"
