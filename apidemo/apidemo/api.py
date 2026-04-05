from datetime import date
from typing import List
from ninja.errors import HttpError
from django.shortcuts import get_object_or_404
from ninja import NinjaAPI, Schema
from .models import (
    Appointment,
    Bill,
    Department,
    Doctor,
    Inpatient,
    Medicalrecord,
    Medicine,
    Patient,
    Prescription,
    Prescriptiondetail,
    Staff,
    Ward,
)

#authentication
from ninja.security import APIKeyCookie
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password

class GlobleAuth(APIKeyCookie):
    param : str = 'sessionid'  # This is the default cookie name for Django sessions

    def authenticate(self, request, key):
        if request.user.is_authenticated:
            return request.user
        return None

auth_gateKepper = GlobleAuth()

api = NinjaAPI(auth=auth_gateKepper)  # Disable CSRF for API endpoints, adjust as needed

class UserSchema(Schema):
    username: str
    password: str


class PatientSchema(Schema):
    patientid: int
    firstname: str
    lastname: str
    gender: str
    dateofbirth: date
    phone: str
    email: str
    address: str
    bloodgroup: str
    registrationdate: date


class CreatePatientSchema(Schema):
    firstname: str
    lastname: str
    gender: str
    dateofbirth: date
    phone: str
    email: str
    address: str
    bloodgroup: str
    registrationdate: date


class DepartmentSchema(Schema):
    deptid: int
    deptname: str
    description: str


class DepartmentCreate(Schema):
    deptname: str
    description: str
#create User
@api.post("auth/register",auth=None)  # No auth required for registration
def register(request, payload: UserSchema):
    if User.objects.filter(username = payload.username).exists():
        return {"error": "Username already exists"}
    user = User.objects.create(
        username = payload.username,
        password = make_password(payload.password)
    )
    return {"message": "User created successfully", "user_id": user.id}

#login user 
@api.post("auth/login",auth=None)  # No auth required for login
def login_user(request,payload: UserSchema):
    user = authenticate(request, username=payload.username, password =payload.password)
    if user is not None:
        login(request,user)
        return {"message": "Login successful"}
    else:
        return {"error": "Invalid credentials"}

#logout user
@api.post("auth/logout", auth=None)
def logout_user(request):
    # Flush the Django session and explicitly expire auth cookies.
    # Some clients can keep sending stale cookies unless the server clears them.
    logout(request)
    response = api.create_response(request, {"message": "Logout successful"}, status=200)
    response.delete_cookie(settings.SESSION_COOKIE_NAME)
    response.delete_cookie(settings.CSRF_COOKIE_NAME)
    return response
    
#handle HttpError globally
@api.exception_handler(HttpError)
def handle_http_error(request, exc):
    return api.create_response(
        request,
        {"Internal Server Error": str(exc)},
        status=500,
    )


def serialize_instance(instance):
    data = {}
    for field in instance._meta.fields:
        key = field.name
        if field.is_relation:
            data[key] = getattr(instance, field.attname)
        else:
            data[key] = getattr(instance, key)
    return data


def serialize_queryset(queryset):
    return [serialize_instance(obj) for obj in queryset]


@api.get("/appointments", auth=None)
def get_appointments(request):
    return serialize_queryset(Appointment.objects.all())


@api.get("/appointments/{appointmentid}", auth=None)
def get_appointment_by_id(request, appointmentid: int):
    appointment = get_object_or_404(Appointment, appointmentid=appointmentid)
    return serialize_instance(appointment)


@api.get("/bills", auth=None)
def get_bills(request):
    return serialize_queryset(Bill.objects.all())


@api.get("/bills/{billid}", auth=None)
def get_bill_by_id(request, billid: int):
    bill = get_object_or_404(Bill, billid=billid)
    return serialize_instance(bill)


@api.get("/doctors", auth=None)
def get_doctors(request):
    return serialize_queryset(Doctor.objects.all())


@api.get("/doctors/{doctorid}", auth=None)
def get_doctor_by_id(request, doctorid: int):
    doctor = get_object_or_404(Doctor, doctorid=doctorid)
    return serialize_instance(doctor)


@api.get("/inpatients", auth=None)
def get_inpatients(request):
    return serialize_queryset(Inpatient.objects.all())


@api.get("/inpatients/{admissionid}", auth=None)
def get_inpatient_by_id(request, admissionid: int):
    inpatient = get_object_or_404(Inpatient, admissionid=admissionid)
    return serialize_instance(inpatient)


@api.get("/medical-records", auth=None)
def get_medical_records(request):
    return serialize_queryset(Medicalrecord.objects.all())


@api.get("/medical-records/{recordid}", auth=None)
def get_medical_record_by_id(request, recordid: int):
    record = get_object_or_404(Medicalrecord, recordid=recordid)
    return serialize_instance(record)


@api.get("/medicines", auth=None)
def get_medicines(request):
    return serialize_queryset(Medicine.objects.all())


@api.get("/medicines/{medicineid}", auth=None)
def get_medicine_by_id(request, medicineid: int):
    medicine = get_object_or_404(Medicine, medicineid=medicineid)
    return serialize_instance(medicine)


@api.get("/prescriptions", auth=None)
def get_prescriptions(request):
    return serialize_queryset(Prescription.objects.all())


@api.get("/prescriptions/{prescriptionid}", auth=None)
def get_prescription_by_id(request, prescriptionid: int):
    prescription = get_object_or_404(Prescription, prescriptionid=prescriptionid)
    return serialize_instance(prescription)


@api.get("/prescription-details", auth=None)
def get_prescription_details(request):
    return serialize_queryset(Prescriptiondetail.objects.all())


@api.get("/prescription-details/{prescriptionid}/{medicineid}", auth=None)
def get_prescription_detail_by_id(request, prescriptionid: int, medicineid: int):
    detail = get_object_or_404(
        Prescriptiondetail, prescriptionid_id=prescriptionid, medicineid_id=medicineid
    )
    return serialize_instance(detail)


@api.get("/staff", auth=None)
def get_staff(request):
    return serialize_queryset(Staff.objects.all())


@api.get("/staff/{staffid}", auth=None)
def get_staff_by_id(request, staffid: int):
    staff = get_object_or_404(Staff, staffid=staffid)
    return serialize_instance(staff)


@api.get("/wards", auth=None)
def get_wards(request):
    return serialize_queryset(Ward.objects.all())


@api.get("/wards/{roomid}", auth=None)
def get_ward_by_id(request, roomid: int):
    ward = get_object_or_404(Ward, roomid=roomid)
    return serialize_instance(ward)

@api.get("/patients", response=List[PatientSchema],auth=None)
def get_patients(request):
    return Patient.objects.all()


# FIXED: Added the 'def' line and fixed indentation
@api.get("/patients/{patientid}", response=PatientSchema)  
def get_patient(request, patientid: int):
    try:
        return Patient.objects.get(patientid=patientid)
    except Patient.DoesNotExist:
        # Note: If you return a dict here, the response
        # might fail Schema validation. I'll stick to your logic for now.
        return {"error": "Patient not found"}


# Post patient
@api.post("/patients")
def create_patient(request, payload: CreatePatientSchema):
    patient = Patient.objects.create(**payload.dict())
    return {"message": "Patient created successfully", "patient_id": patient.patientid}


# Update patient
# Keep POST for backward compatibility and support REST-style PUT/PATCH used by frontends.
@api.post("/patients/{patientid}", auth=None)
@api.put("/patients/{patientid}", auth=None)
@api.patch("/patients/{patientid}", auth=None)
def update_patient(request, patientid: int, payload: CreatePatientSchema):
    try:
        patient = Patient.objects.get(patientid=patientid)
        for key, value in payload.dict().items():
            setattr(patient, key, value)
        patient.save()
        return {
            "message": "Patient updated successfully",
            "patient_id": patient.patientid,
        }
    except Patient.DoesNotExist:
        return {"error": "Patient not found"}


# Delete patient
@api.delete("/patients/{patientid}",auth=None)
def delete_patient(request, patientid: int):
    try:
        patient = Patient.objects.get(patientid=patientid)
        patient.delete()
        return {"message": "Patient deleted successfully", "patient_id": patientid}
    except Patient.DoesNotExist:
        return {"error": "Patient not found"}


@api.get("/department", response=List[DepartmentSchema])
def get_department(request):
    return Department.objects.all()


@api.get("/department/{deptid}", response=DepartmentSchema)
def get_deptbyid(request, deptid: int):
    return get_object_or_404(Department, deptid=deptid)


@api.post("/department")
def create_department(request, payload: DepartmentCreate):
    department = Department.objects.create(**payload.dict())
    return {
        "message": "Patient created successfully",
        "departmen id ": department.deptid,
    }

# Update department
@api.post("/department/{deptid}")
def update_department(request, deptid: int, payload: DepartmentCreate):
    try :
        department = Department.objects.get(deptid=deptid)
        for key,value in payload.dict().items():
            setattr(department,key,value)
        department.save()
        return {
            "message": "Department updated successfully",
            "department id ": department.deptid,
        }
    except Department.DoesNotExist:
        return {"error": "Department not found"}

