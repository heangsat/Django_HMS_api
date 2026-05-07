from datetime import date
from typing import List, Optional
from django.shortcuts import get_object_or_404
from django.http import Http404
from ninja import NinjaAPI, Schema
from django.core.exceptions import ValidationError as DjangoValidationError
import logging

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

# Import utility modules
from .serializers import serialize_model_instance, serialize_model_queryset
from .error_handlers import (
    NotFoundError, ValidationError, DatabaseError, create_success_response, 
    create_error_response, format_error_response, safe_operation
)
from .debug_utils import PerformanceMonitor, log_request_details, log_response_details

# Authentication
from ninja.security import APIKeyCookie
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password

logger = logging.getLogger("hospital_api")


class GlobleAuth(APIKeyCookie):
    param: str = 'sessionid'

    def authenticate(self, request, key):
        if request.user.is_authenticated:
            return request.user
        return None


auth_gateKepper = GlobleAuth()

api = NinjaAPI(auth=auth_gateKepper)


def safe_get_object(model_class, error_name: str, **kwargs):
    """Safely get an object and raise NotFoundError if not found."""
    try:
        return model_class.objects.get(**kwargs)
    except model_class.DoesNotExist:
        raise NotFoundError(error_name, kwargs.get('pk') or kwargs.get(f'{model_class.__name__.lower()}id'))
    except Exception as e:
        logger.error(f"Failed to fetch {error_name}: {str(e)}", exc_info=True)
        raise DatabaseError(f"Failed to fetch {error_name}")


# ============================================================================
# SCHEMAS
# ============================================================================

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


class DoctorSchema(Schema):
    doctorid: int
    firstname: str
    lastname: str
    gender: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    deptid: Optional[int] = None
    specialization: Optional[str] = None


class CreateDoctorSchema(Schema):
    firstname: str
    lastname: str
    gender: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    deptid: Optional[int] = None
    specialization: Optional[str] = None


class AppointmentSchema(Schema):
    appointmentid: int
    patientid: int
    doctorid: int
    appointmentdate: Optional[date] = None
    appointmenttime: Optional[str] = None
    status: Optional[str] = None
    remarks: Optional[str] = None


class CreateAppointmentSchema(Schema):
    patientid: int
    doctorid: int
    appointmentdate: Optional[date] = None
    appointmenttime: Optional[str] = None
    status: Optional[str] = None
    remarks: Optional[str] = None


class BillSchema(Schema):
    billid: int
    patientid: int
    appointmentid: Optional[int] = None
    admissionid: Optional[int] = None
    billdate: Optional[date] = None
    totalamount: Optional[float] = None
    status: Optional[str] = None


class CreateBillSchema(Schema):
    patientid: int
    appointmentid: Optional[int] = None
    admissionid: Optional[int] = None
    billdate: Optional[date] = None
    totalamount: Optional[float] = None
    status: Optional[str] = None


class InpatientSchema(Schema):
    admissionid: int
    patientid: int
    roomid: int
    admissiondate: Optional[date] = None
    dischargedate: Optional[date] = None


class CreateInpatientSchema(Schema):
    patientid: int
    roomid: int
    admissiondate: Optional[date] = None
    dischargedate: Optional[date] = None


class MedicalRecordSchema(Schema):
    recordid: int
    patientid: int
    doctorid: int
    visitdate: Optional[date] = None
    diagnosis: Optional[str] = None
    treatment: Optional[str] = None
    allergies: Optional[str] = None
    notes: Optional[str] = None


class CreateMedicalRecordSchema(Schema):
    patientid: int
    doctorid: int
    visitdate: Optional[date] = None
    diagnosis: Optional[str] = None
    treatment: Optional[str] = None
    allergies: Optional[str] = None
    notes: Optional[str] = None


class MedicineSchema(Schema):
    medicineid: int
    medicinename: str
    genericname: Optional[str] = None
    stockquantity: Optional[int] = None
    unitprice: Optional[float] = None
    expirydate: Optional[date] = None


class CreateMedicineSchema(Schema):
    medicinename: str
    genericname: Optional[str] = None
    stockquantity: Optional[int] = None
    unitprice: Optional[float] = None
    expirydate: Optional[date] = None


class PrescriptionSchema(Schema):
    prescriptionid: int
    recordid: int
    prescriptiondate: Optional[date] = None


class CreatePrescriptionSchema(Schema):
    recordid: int
    prescriptiondate: Optional[date] = None


class PrescriptionDetailSchema(Schema):
    prescriptionid: int
    medicineid: int
    dosage: Optional[str] = None
    duration: Optional[str] = None


class CreatePrescriptionDetailSchema(Schema):
    prescriptionid: int
    medicineid: int
    dosage: Optional[str] = None
    duration: Optional[str] = None


class StaffSchema(Schema):
    staffid: int
    firstname: str
    lastname: str
    role: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    hiredate: Optional[date] = None


class CreateStaffSchema(Schema):
    firstname: str
    lastname: str
    role: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    hiredate: Optional[date] = None


class WardSchema(Schema):
    roomid: int
    roomnumber: str
    roomtype: Optional[str] = None
    status: Optional[str] = None
    priceperday: Optional[float] = None


class CreateWardSchema(Schema):
    roomnumber: str
    roomtype: Optional[str] = None
    status: Optional[str] = None
    priceperday: Optional[float] = None

#create User
@api.post("auth/register", auth=None)
def register(request, payload: UserSchema):
    """Register a new user."""
    try:
        if User.objects.filter(username=payload.username).exists():
            return create_error_response("Username already exists", "USERNAME_EXISTS", 400)
        
        user = User.objects.create(
            username=payload.username,
            password=make_password(payload.password)
        )
        return create_success_response(
            {"user_id": user.id, "username": user.username},
            "User created successfully",
            201
        )
    except Exception as e:
        logger.error(f"Registration failed: {str(e)}", exc_info=True)
        return create_error_response("Registration failed", "REGISTRATION_ERROR", 500)


@api.post("auth/login", auth=None)
def login_user(request, payload: UserSchema):
    """Authenticate user and create session."""
    try:
        user = authenticate(request, username=payload.username, password=payload.password)
        if user is not None:
            login(request, user)
            return create_success_response(
                {"user_id": user.id, "username": user.username},
                "Login successful",
                200
            )
        else:
            return create_error_response("Invalid credentials", "INVALID_CREDENTIALS", 401)
    except Exception as e:
        logger.error(f"Login failed: {str(e)}", exc_info=True)
        return create_error_response("Login failed", "LOGIN_ERROR", 500)


@api.post("auth/logout", auth=None)
def logout_user(request):
    """Logout user and clear session."""
    try:
        logout(request)
        response = api.create_response(request, create_success_response(None, "Logout successful"), status=200)
        response.delete_cookie(settings.SESSION_COOKIE_NAME)
        response.delete_cookie(settings.CSRF_COOKIE_NAME)
        return response
    except Exception as e:
        logger.error(f"Logout failed: {str(e)}", exc_info=True)
        return create_error_response("Logout failed", "LOGOUT_ERROR", 500)


# ============================================================================
# EXCEPTION HANDLERS
# ============================================================================

@api.exception_handler(ValidationError)
def handle_validation_error(request, exc):
    return api.create_response(
        request,
        create_error_response(exc.message, exc.error_code, 400),
        status=400,
    )


@api.exception_handler(NotFoundError)
def handle_not_found_error(request, exc):
    return api.create_response(
        request,
        create_error_response(exc.message, exc.error_code, 404),
        status=404,
    )


@api.exception_handler(DatabaseError)
def handle_database_error(request, exc):
    logger.error(f"Database error: {exc.message}", exc_info=True)
    return api.create_response(
        request,
        create_error_response(exc.message, exc.error_code, 500),
        status=500,
    )


@api.exception_handler(Exception)
def handle_generic_exception(request, exc):
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return api.create_response(
        request,
        create_error_response("An unexpected error occurred", "INTERNAL_SERVER_ERROR", 500),
        status=500,
    )




# ============================================================================
# PATIENT ENDPOINTS
# ============================================================================

@api.get("/patients", response=List[PatientSchema], auth=None)
def get_patients(request):
    """Get all patients."""
    try:
        with PerformanceMonitor("GET /patients"):
            patients = Patient.objects.all()
            return list(patients)
    except Exception as e:
        logger.error(f"Failed to fetch patients: {str(e)}", exc_info=True)
        raise DatabaseError("Failed to fetch patients")


@api.get("/patients/{patientid}", response=PatientSchema, auth=None)
def get_patient(request, patientid: int):
    """Get patient by ID."""
    try:
        with PerformanceMonitor(f"GET /patients/{patientid}"):
            patient = get_object_or_404(Patient, patientid=patientid)
            return patient
    except Exception as e:
        if "404" in str(e):
            raise NotFoundError("Patient", patientid)
        logger.error(f"Failed to fetch patient: {str(e)}", exc_info=True)
        raise DatabaseError("Failed to fetch patient")


@api.post("/patients", auth=None)
def create_patient(request, payload: CreatePatientSchema):
    """Create a new patient."""
    try:
        with PerformanceMonitor("POST /patients"):
            patient = Patient.objects.create(**payload.dict())
            return create_success_response(
                {"patientid": patient.patientid},
                "Patient created successfully",
                201
            )
    except Exception as e:
        logger.error(f"Failed to create patient: {str(e)}", exc_info=True)
        raise DatabaseError("Failed to create patient")


@api.put("/patients/{patientid}", auth=None)
@api.post("/patients/{patientid}", auth=None)
def update_patient(request, patientid: int, payload: CreatePatientSchema):
    """Update patient information."""
    try:
        with PerformanceMonitor(f"PUT/POST /patients/{patientid}"):
            patient = get_object_or_404(Patient, patientid=patientid)
            for key, value in payload.dict().items():
                setattr(patient, key, value)
            patient.save()
            return create_success_response(
                {"patientid": patient.patientid},
                "Patient updated successfully"
            )
    except Exception as e:
        if "404" in str(e):
            raise NotFoundError("Patient", patientid)
        logger.error(f"Failed to update patient: {str(e)}", exc_info=True)
        raise DatabaseError("Failed to update patient")


@api.delete("/patients/{patientid}", auth=None)
def delete_patient(request, patientid: int):
    """Delete a patient."""
    try:
        with PerformanceMonitor(f"DELETE /patients/{patientid}"):
            patient = get_object_or_404(Patient, patientid=patientid)
            patient.delete()
            return create_success_response(
                {"patientid": patientid},
                "Patient deleted successfully"
            )
    except Exception as e:
        if "404" in str(e):
            raise NotFoundError("Patient", patientid)
        logger.error(f"Failed to delete patient: {str(e)}", exc_info=True)
        raise DatabaseError("Failed to delete patient")


# ============================================================================
# DOCTOR ENDPOINTS
# ============================================================================

@api.get("/doctors", response=List[DoctorSchema], auth=None)
def get_doctors(request):
    """Get all doctors."""
    try:
        with PerformanceMonitor("GET /doctors"):
            doctors = Doctor.objects.all()
            result = []
            for doctor in doctors:
                result.append({
                    'doctorid': doctor.doctorid,
                    'firstname': doctor.firstname,
                    'lastname': doctor.lastname,
                    'gender': doctor.gender,
                    'phone': doctor.phone,
                    'email': doctor.email,
                    'deptid': doctor.deptid_id,
                    'specialization': doctor.specialization,
                })
            return result
    except Exception as e:
        logger.error(f"Failed to fetch doctors: {str(e)}", exc_info=True)
        raise DatabaseError("Failed to fetch doctors")


@api.get("/doctors/{doctorid}", response=DoctorSchema, auth=None)
def get_doctor(request, doctorid: int):
    """Get doctor by ID."""
    try:
        with PerformanceMonitor(f"GET /doctors/{doctorid}"):
            doctor = get_object_or_404(Doctor, doctorid=doctorid)
            return {
                'doctorid': doctor.doctorid,
                'firstname': doctor.firstname,
                'lastname': doctor.lastname,
                'gender': doctor.gender,
                'phone': doctor.phone,
                'email': doctor.email,
                'deptid': doctor.deptid_id,
                'specialization': doctor.specialization,
            }
    except Exception as e:
        if "404" in str(e):
            raise NotFoundError("Doctor", doctorid)
        logger.error(f"Failed to fetch doctor: {str(e)}", exc_info=True)
        raise DatabaseError("Failed to fetch doctor")


@api.post("/doctors", auth=None)
def create_doctor(request, payload: CreateDoctorSchema):
    """Create a new doctor."""
    try:
        with PerformanceMonitor("POST /doctors"):
            doctor = Doctor.objects.create(**payload.dict())
            return create_success_response(
                {"doctorid": doctor.doctorid},
                "Doctor created successfully",
                201
            )
    except Exception as e:
        logger.error(f"Failed to create doctor: {str(e)}", exc_info=True)
        raise DatabaseError("Failed to create doctor")


@api.put("/doctors/{doctorid}", auth=None)
@api.post("/doctors/{doctorid}", auth=None)
def update_doctor(request, doctorid: int, payload: CreateDoctorSchema):
    """Update doctor information."""
    try:
        with PerformanceMonitor(f"PUT/POST /doctors/{doctorid}"):
            doctor = get_object_or_404(Doctor, doctorid=doctorid)
            for key, value in payload.dict().items():
                setattr(doctor, key, value)
            doctor.save()
            return create_success_response(
                {"doctorid": doctor.doctorid},
                "Doctor updated successfully"
            )
    except Exception as e:
        if "404" in str(e):
            raise NotFoundError("Doctor", doctorid)
        logger.error(f"Failed to update doctor: {str(e)}", exc_info=True)
        raise DatabaseError("Failed to update doctor")


@api.delete("/doctors/{doctorid}", auth=None)
def delete_doctor(request, doctorid: int):
    """Delete a doctor."""
    try:
        with PerformanceMonitor(f"DELETE /doctors/{doctorid}"):
            doctor = get_object_or_404(Doctor, doctorid=doctorid)
            doctor.delete()
            return create_success_response(
                {"doctorid": doctorid},
                "Doctor deleted successfully"
            )
    except Exception as e:
        if "404" in str(e):
            raise NotFoundError("Doctor", doctorid)
        logger.error(f"Failed to delete doctor: {str(e)}", exc_info=True)
        raise DatabaseError("Failed to delete doctor")


# ============================================================================
# APPOINTMENT ENDPOINTS
# ============================================================================

@api.get("/appointments", response=List[AppointmentSchema], auth=None)
def get_appointments(request):
    """Get all appointments."""
    try:
        with PerformanceMonitor("GET /appointments"):
            appointments = Appointment.objects.all()
            return list(appointments)
    except Exception as e:
        logger.error(f"Failed to fetch appointments: {str(e)}", exc_info=True)
        raise DatabaseError("Failed to fetch appointments")


@api.get("/appointments/{appointmentid}", response=AppointmentSchema, auth=None)
def get_appointment(request, appointmentid: int):
    """Get appointment by ID."""
    try:
        with PerformanceMonitor(f"GET /appointments/{appointmentid}"):
            appointment = get_object_or_404(Appointment, appointmentid=appointmentid)
            return appointment
    except Exception as e:
        if "404" in str(e):
            raise NotFoundError("Appointment", appointmentid)
        logger.error(f"Failed to fetch appointment: {str(e)}", exc_info=True)
        raise DatabaseError("Failed to fetch appointment")


@api.post("/appointments", auth=None)
def create_appointment(request, payload: CreateAppointmentSchema):
    """Create a new appointment."""
    try:
        with PerformanceMonitor("POST /appointments"):
            appointment = Appointment.objects.create(**payload.dict())
            return create_success_response(
                {"appointmentid": appointment.appointmentid},
                "Appointment created successfully",
                201
            )
    except Exception as e:
        logger.error(f"Failed to create appointment: {str(e)}", exc_info=True)
        raise DatabaseError("Failed to create appointment")


@api.put("/appointments/{appointmentid}", auth=None)
@api.post("/appointments/{appointmentid}", auth=None)
def update_appointment(request, appointmentid: int, payload: CreateAppointmentSchema):
    """Update appointment information."""
    try:
        with PerformanceMonitor(f"PUT/POST /appointments/{appointmentid}"):
            appointment = get_object_or_404(Appointment, appointmentid=appointmentid)
            for key, value in payload.dict().items():
                setattr(appointment, key, value)
            appointment.save()
            return create_success_response(
                {"appointmentid": appointment.appointmentid},
                "Appointment updated successfully"
            )
    except Exception as e:
        if "404" in str(e):
            raise NotFoundError("Appointment", appointmentid)
        logger.error(f"Failed to update appointment: {str(e)}", exc_info=True)
        raise DatabaseError("Failed to update appointment")


@api.delete("/appointments/{appointmentid}", auth=None)
def delete_appointment(request, appointmentid: int):
    """Delete an appointment."""
    try:
        with PerformanceMonitor(f"DELETE /appointments/{appointmentid}"):
            appointment = get_object_or_404(Appointment, appointmentid=appointmentid)
            appointment.delete()
            return create_success_response(
                {"appointmentid": appointmentid},
                "Appointment deleted successfully"
            )
    except Exception as e:
        if "404" in str(e):
            raise NotFoundError("Appointment", appointmentid)
        logger.error(f"Failed to delete appointment: {str(e)}", exc_info=True)
        raise DatabaseError("Failed to delete appointment")


# ============================================================================
# BILL ENDPOINTS
# ============================================================================

@api.get("/bills", response=List[BillSchema], auth=None)
def get_bills(request):
    """Get all bills."""
    try:
        with PerformanceMonitor("GET /bills"):
            bills = Bill.objects.all()
            return list(bills)
    except Exception as e:
        logger.error(f"Failed to fetch bills: {str(e)}", exc_info=True)
        raise DatabaseError("Failed to fetch bills")


@api.get("/bills/{billid}", response=BillSchema, auth=None)
def get_bill(request, billid: int):
    """Get bill by ID."""
    try:
        with PerformanceMonitor(f"GET /bills/{billid}"):
            bill = get_object_or_404(Bill, billid=billid)
            return bill
    except Exception as e:
        if "404" in str(e):
            raise NotFoundError("Bill", billid)
        logger.error(f"Failed to fetch bill: {str(e)}", exc_info=True)
        raise DatabaseError("Failed to fetch bill")


@api.post("/bills", auth=None)
def create_bill(request, payload: CreateBillSchema):
    """Create a new bill."""
    try:
        with PerformanceMonitor("POST /bills"):
            bill = Bill.objects.create(**payload.dict())
            return create_success_response(
                {"billid": bill.billid},
                "Bill created successfully",
                201
            )
    except Exception as e:
        logger.error(f"Failed to create bill: {str(e)}", exc_info=True)
        raise DatabaseError("Failed to create bill")


@api.put("/bills/{billid}", auth=None)
@api.post("/bills/{billid}", auth=None)
def update_bill(request, billid: int, payload: CreateBillSchema):
    """Update bill information."""
    try:
        with PerformanceMonitor(f"PUT/POST /bills/{billid}"):
            bill = get_object_or_404(Bill, billid=billid)
            for key, value in payload.dict().items():
                setattr(bill, key, value)
            bill.save()
            return create_success_response(
                {"billid": bill.billid},
                "Bill updated successfully"
            )
    except Exception as e:
        if "404" in str(e):
            raise NotFoundError("Bill", billid)
        logger.error(f"Failed to update bill: {str(e)}", exc_info=True)
        raise DatabaseError("Failed to update bill")


@api.delete("/bills/{billid}", auth=None)
def delete_bill(request, billid: int):
    """Delete a bill."""
    try:
        with PerformanceMonitor(f"DELETE /bills/{billid}"):
            bill = get_object_or_404(Bill, billid=billid)
            bill.delete()
            return create_success_response(
                {"billid": billid},
                "Bill deleted successfully"
            )
    except Exception as e:
        if "404" in str(e):
            raise NotFoundError("Bill", billid)
        logger.error(f"Failed to delete bill: {str(e)}", exc_info=True)
        raise DatabaseError("Failed to delete bill")


# ============================================================================
# INPATIENT ENDPOINTS
# ============================================================================

@api.get("/inpatients", response=List[InpatientSchema], auth=None)
def get_inpatients(request):
    """Get all inpatients."""
    try:
        with PerformanceMonitor("GET /inpatients"):
            inpatients = Inpatient.objects.all()
            return list(inpatients)
    except Exception as e:
        logger.error(f"Failed to fetch inpatients: {str(e)}", exc_info=True)
        raise DatabaseError("Failed to fetch inpatients")


@api.get("/inpatients/{admissionid}", response=InpatientSchema, auth=None)
def get_inpatient(request, admissionid: int):
    """Get inpatient by admission ID."""
    try:
        with PerformanceMonitor(f"GET /inpatients/{admissionid}"):
            inpatient = get_object_or_404(Inpatient, admissionid=admissionid)
            return inpatient
    except Exception as e:
        if "404" in str(e):
            raise NotFoundError("Inpatient", admissionid)
        logger.error(f"Failed to fetch inpatient: {str(e)}", exc_info=True)
        raise DatabaseError("Failed to fetch inpatient")


@api.post("/inpatients", auth=None)
def create_inpatient(request, payload: CreateInpatientSchema):
    """Create a new inpatient admission."""
    try:
        with PerformanceMonitor("POST /inpatients"):
            inpatient = Inpatient.objects.create(**payload.dict())
            return create_success_response(
                {"admissionid": inpatient.admissionid},
                "Inpatient admission created successfully",
                201
            )
    except Exception as e:
        logger.error(f"Failed to create inpatient: {str(e)}", exc_info=True)
        raise DatabaseError("Failed to create inpatient admission")


@api.put("/inpatients/{admissionid}", auth=None)
@api.post("/inpatients/{admissionid}", auth=None)
def update_inpatient(request, admissionid: int, payload: CreateInpatientSchema):
    """Update inpatient information."""
    try:
        with PerformanceMonitor(f"PUT/POST /inpatients/{admissionid}"):
            inpatient = get_object_or_404(Inpatient, admissionid=admissionid)
            for key, value in payload.dict().items():
                setattr(inpatient, key, value)
            inpatient.save()
            return create_success_response(
                {"admissionid": inpatient.admissionid},
                "Inpatient updated successfully"
            )
    except Exception as e:
        if "404" in str(e):
            raise NotFoundError("Inpatient", admissionid)
        logger.error(f"Failed to update inpatient: {str(e)}", exc_info=True)
        raise DatabaseError("Failed to update inpatient")


@api.delete("/inpatients/{admissionid}", auth=None)
def delete_inpatient(request, admissionid: int):
    """Delete an inpatient admission."""
    try:
        with PerformanceMonitor(f"DELETE /inpatients/{admissionid}"):
            inpatient = get_object_or_404(Inpatient, admissionid=admissionid)
            inpatient.delete()
            return create_success_response(
                {"admissionid": admissionid},
                "Inpatient deleted successfully"
            )
    except Exception as e:
        if "404" in str(e):
            raise NotFoundError("Inpatient", admissionid)
        logger.error(f"Failed to delete inpatient: {str(e)}", exc_info=True)
        raise DatabaseError("Failed to delete inpatient")


# ============================================================================
# MEDICAL RECORD ENDPOINTS
# ============================================================================

@api.get("/medical-records", response=List[MedicalRecordSchema], auth=None)
def get_medical_records(request):
    """Get all medical records."""
    try:
        with PerformanceMonitor("GET /medical-records"):
            records = Medicalrecord.objects.all()
            return list(records)
    except Exception as e:
        logger.error(f"Failed to fetch medical records: {str(e)}", exc_info=True)
        raise DatabaseError("Failed to fetch medical records")


@api.get("/medical-records/{recordid}", response=MedicalRecordSchema, auth=None)
def get_medical_record(request, recordid: int):
    """Get medical record by ID."""
    try:
        with PerformanceMonitor(f"GET /medical-records/{recordid}"):
            record = get_object_or_404(Medicalrecord, recordid=recordid)
            return record
    except Exception as e:
        if "404" in str(e):
            raise NotFoundError("Medical Record", recordid)
        logger.error(f"Failed to fetch medical record: {str(e)}", exc_info=True)
        raise DatabaseError("Failed to fetch medical record")


@api.post("/medical-records", auth=None)
def create_medical_record(request, payload: CreateMedicalRecordSchema):
    """Create a new medical record."""
    try:
        with PerformanceMonitor("POST /medical-records"):
            record = Medicalrecord.objects.create(**payload.dict())
            return create_success_response(
                {"recordid": record.recordid},
                "Medical record created successfully",
                201
            )
    except Exception as e:
        logger.error(f"Failed to create medical record: {str(e)}", exc_info=True)
        raise DatabaseError("Failed to create medical record")


@api.put("/medical-records/{recordid}", auth=None)
@api.post("/medical-records/{recordid}", auth=None)
def update_medical_record(request, recordid: int, payload: CreateMedicalRecordSchema):
    """Update medical record."""
    try:
        with PerformanceMonitor(f"PUT/POST /medical-records/{recordid}"):
            record = get_object_or_404(Medicalrecord, recordid=recordid)
            for key, value in payload.dict().items():
                setattr(record, key, value)
            record.save()
            return create_success_response(
                {"recordid": record.recordid},
                "Medical record updated successfully"
            )
    except Exception as e:
        if "404" in str(e):
            raise NotFoundError("Medical Record", recordid)
        logger.error(f"Failed to update medical record: {str(e)}", exc_info=True)
        raise DatabaseError("Failed to update medical record")


@api.delete("/medical-records/{recordid}", auth=None)
def delete_medical_record(request, recordid: int):
    """Delete a medical record."""
    try:
        with PerformanceMonitor(f"DELETE /medical-records/{recordid}"):
            record = get_object_or_404(Medicalrecord, recordid=recordid)
            record.delete()
            return create_success_response(
                {"recordid": recordid},
                "Medical record deleted successfully"
            )
    except Exception as e:
        if "404" in str(e):
            raise NotFoundError("Medical Record", recordid)
        logger.error(f"Failed to delete medical record: {str(e)}", exc_info=True)
        raise DatabaseError("Failed to delete medical record")


# ============================================================================
# MEDICINE ENDPOINTS
# ============================================================================

@api.get("/medicines", response=List[MedicineSchema], auth=None)
def get_medicines(request):
    """Get all medicines."""
    try:
        with PerformanceMonitor("GET /medicines"):
            medicines = Medicine.objects.all()
            return list(medicines)
    except Exception as e:
        logger.error(f"Failed to fetch medicines: {str(e)}", exc_info=True)
        raise DatabaseError("Failed to fetch medicines")


@api.get("/medicines/{medicineid}", response=MedicineSchema, auth=None)
def get_medicine(request, medicineid: int):
    """Get medicine by ID."""
    try:
        with PerformanceMonitor(f"GET /medicines/{medicineid}"):
            medicine = get_object_or_404(Medicine, medicineid=medicineid)
            return medicine
    except Exception as e:
        if "404" in str(e):
            raise NotFoundError("Medicine", medicineid)
        logger.error(f"Failed to fetch medicine: {str(e)}", exc_info=True)
        raise DatabaseError("Failed to fetch medicine")


@api.post("/medicines", auth=None)
def create_medicine(request, payload: CreateMedicineSchema):
    """Create a new medicine."""
    try:
        with PerformanceMonitor("POST /medicines"):
            medicine = Medicine.objects.create(**payload.dict())
            return create_success_response(
                {"medicineid": medicine.medicineid},
                "Medicine created successfully",
                201
            )
    except Exception as e:
        logger.error(f"Failed to create medicine: {str(e)}", exc_info=True)
        raise DatabaseError("Failed to create medicine")


@api.put("/medicines/{medicineid}", auth=None)
@api.post("/medicines/{medicineid}", auth=None)
def update_medicine(request, medicineid: int, payload: CreateMedicineSchema):
    """Update medicine information."""
    try:
        with PerformanceMonitor(f"PUT/POST /medicines/{medicineid}"):
            medicine = get_object_or_404(Medicine, medicineid=medicineid)
            for key, value in payload.dict().items():
                setattr(medicine, key, value)
            medicine.save()
            return create_success_response(
                {"medicineid": medicine.medicineid},
                "Medicine updated successfully"
            )
    except Exception as e:
        if "404" in str(e):
            raise NotFoundError("Medicine", medicineid)
        logger.error(f"Failed to update medicine: {str(e)}", exc_info=True)
        raise DatabaseError("Failed to update medicine")


@api.delete("/medicines/{medicineid}", auth=None)
def delete_medicine(request, medicineid: int):
    """Delete a medicine."""
    try:
        with PerformanceMonitor(f"DELETE /medicines/{medicineid}"):
            medicine = get_object_or_404(Medicine, medicineid=medicineid)
            medicine.delete()
            return create_success_response(
                {"medicineid": medicineid},
                "Medicine deleted successfully"
            )
    except Exception as e:
        if "404" in str(e):
            raise NotFoundError("Medicine", medicineid)
        logger.error(f"Failed to delete medicine: {str(e)}", exc_info=True)
        raise DatabaseError("Failed to delete medicine")


# ============================================================================
# PRESCRIPTION ENDPOINTS
# ============================================================================

@api.get("/prescriptions", response=List[PrescriptionSchema], auth=None)
def get_prescriptions(request):
    """Get all prescriptions."""
    try:
        with PerformanceMonitor("GET /prescriptions"):
            prescriptions = Prescription.objects.all()
            return list(prescriptions)
    except Exception as e:
        logger.error(f"Failed to fetch prescriptions: {str(e)}", exc_info=True)
        raise DatabaseError("Failed to fetch prescriptions")


@api.get("/prescriptions/{prescriptionid}", response=PrescriptionSchema, auth=None)
def get_prescription(request, prescriptionid: int):
    """Get prescription by ID."""
    try:
        with PerformanceMonitor(f"GET /prescriptions/{prescriptionid}"):
            prescription = get_object_or_404(Prescription, prescriptionid=prescriptionid)
            return prescription
    except Exception as e:
        if "404" in str(e):
            raise NotFoundError("Prescription", prescriptionid)
        logger.error(f"Failed to fetch prescription: {str(e)}", exc_info=True)
        raise DatabaseError("Failed to fetch prescription")


@api.post("/prescriptions", auth=None)
def create_prescription(request, payload: CreatePrescriptionSchema):
    """Create a new prescription."""
    try:
        with PerformanceMonitor("POST /prescriptions"):
            prescription = Prescription.objects.create(**payload.dict())
            return create_success_response(
                {"prescriptionid": prescription.prescriptionid},
                "Prescription created successfully",
                201
            )
    except Exception as e:
        logger.error(f"Failed to create prescription: {str(e)}", exc_info=True)
        raise DatabaseError("Failed to create prescription")


@api.put("/prescriptions/{prescriptionid}", auth=None)
@api.post("/prescriptions/{prescriptionid}", auth=None)
def update_prescription(request, prescriptionid: int, payload: CreatePrescriptionSchema):
    """Update prescription information."""
    try:
        with PerformanceMonitor(f"PUT/POST /prescriptions/{prescriptionid}"):
            prescription = get_object_or_404(Prescription, prescriptionid=prescriptionid)
            for key, value in payload.dict().items():
                setattr(prescription, key, value)
            prescription.save()
            return create_success_response(
                {"prescriptionid": prescription.prescriptionid},
                "Prescription updated successfully"
            )
    except Exception as e:
        if "404" in str(e):
            raise NotFoundError("Prescription", prescriptionid)
        logger.error(f"Failed to update prescription: {str(e)}", exc_info=True)
        raise DatabaseError("Failed to update prescription")


@api.delete("/prescriptions/{prescriptionid}", auth=None)
def delete_prescription(request, prescriptionid: int):
    """Delete a prescription."""
    try:
        with PerformanceMonitor(f"DELETE /prescriptions/{prescriptionid}"):
            prescription = get_object_or_404(Prescription, prescriptionid=prescriptionid)
            prescription.delete()
            return create_success_response(
                {"prescriptionid": prescriptionid},
                "Prescription deleted successfully"
            )
    except Exception as e:
        if "404" in str(e):
            raise NotFoundError("Prescription", prescriptionid)
        logger.error(f"Failed to delete prescription: {str(e)}", exc_info=True)
        raise DatabaseError("Failed to delete prescription")


# ============================================================================
# PRESCRIPTION DETAIL ENDPOINTS
# ============================================================================

@api.get("/prescription-details", response=List[PrescriptionDetailSchema], auth=None)
def get_prescription_details(request):
    """Get all prescription details."""
    try:
        with PerformanceMonitor("GET /prescription-details"):
            details = Prescriptiondetail.objects.all()
            return list(details)
    except Exception as e:
        logger.error(f"Failed to fetch prescription details: {str(e)}", exc_info=True)
        raise DatabaseError("Failed to fetch prescription details")


@api.get("/prescription-details/{prescriptionid}/{medicineid}", response=PrescriptionDetailSchema, auth=None)
def get_prescription_detail(request, prescriptionid: int, medicineid: int):
    """Get prescription detail by IDs."""
    try:
        with PerformanceMonitor(f"GET /prescription-details/{prescriptionid}/{medicineid}"):
            detail = get_object_or_404(
                Prescriptiondetail,
                prescriptionid_id=prescriptionid,
                medicineid_id=medicineid
            )
            return detail
    except Exception as e:
        if "404" in str(e):
            raise NotFoundError("Prescription Detail", f"{prescriptionid}/{medicineid}")
        logger.error(f"Failed to fetch prescription detail: {str(e)}", exc_info=True)
        raise DatabaseError("Failed to fetch prescription detail")


@api.post("/prescription-details", auth=None)
def create_prescription_detail(request, payload: CreatePrescriptionDetailSchema):
    """Create a new prescription detail."""
    try:
        with PerformanceMonitor("POST /prescription-details"):
            detail = Prescriptiondetail.objects.create(**payload.dict())
            return create_success_response(
                {"prescriptionid": detail.prescriptionid_id, "medicineid": detail.medicineid_id},
                "Prescription detail created successfully",
                201
            )
    except Exception as e:
        logger.error(f"Failed to create prescription detail: {str(e)}", exc_info=True)
        raise DatabaseError("Failed to create prescription detail")


@api.put("/prescription-details/{prescriptionid}/{medicineid}", auth=None)
@api.post("/prescription-details/{prescriptionid}/{medicineid}", auth=None)
def update_prescription_detail(request, prescriptionid: int, medicineid: int, payload: CreatePrescriptionDetailSchema):
    """Update prescription detail."""
    try:
        with PerformanceMonitor(f"PUT/POST /prescription-details/{prescriptionid}/{medicineid}"):
            detail = get_object_or_404(
                Prescriptiondetail,
                prescriptionid_id=prescriptionid,
                medicineid_id=medicineid
            )
            for key, value in payload.dict().items():
                if key not in ['prescriptionid', 'medicineid']:
                    setattr(detail, key, value)
            detail.save()
            return create_success_response(
                {"prescriptionid": detail.prescriptionid_id, "medicineid": detail.medicineid_id},
                "Prescription detail updated successfully"
            )
    except Exception as e:
        if "404" in str(e):
            raise NotFoundError("Prescription Detail", f"{prescriptionid}/{medicineid}")
        logger.error(f"Failed to update prescription detail: {str(e)}", exc_info=True)
        raise DatabaseError("Failed to update prescription detail")


@api.delete("/prescription-details/{prescriptionid}/{medicineid}", auth=None)
def delete_prescription_detail(request, prescriptionid: int, medicineid: int):
    """Delete a prescription detail."""
    try:
        with PerformanceMonitor(f"DELETE /prescription-details/{prescriptionid}/{medicineid}"):
            detail = get_object_or_404(
                Prescriptiondetail,
                prescriptionid_id=prescriptionid,
                medicineid_id=medicineid
            )
            detail.delete()
            return create_success_response(
                {"prescriptionid": prescriptionid, "medicineid": medicineid},
                "Prescription detail deleted successfully"
            )
    except Exception as e:
        if "404" in str(e):
            raise NotFoundError("Prescription Detail", f"{prescriptionid}/{medicineid}")
        logger.error(f"Failed to delete prescription detail: {str(e)}", exc_info=True)
        raise DatabaseError("Failed to delete prescription detail")


# ============================================================================
# STAFF ENDPOINTS
# ============================================================================

@api.get("/staff", response=List[StaffSchema], auth=None)
def get_staff(request):
    """Get all staff members."""
    try:
        with PerformanceMonitor("GET /staff"):
            staff = Staff.objects.all()
            return list(staff)
    except Exception as e:
        logger.error(f"Failed to fetch staff: {str(e)}", exc_info=True)
        raise DatabaseError("Failed to fetch staff")


@api.get("/staff/{staffid}", response=StaffSchema, auth=None)
def get_staff_member(request, staffid: int):
    """Get staff member by ID."""
    try:
        with PerformanceMonitor(f"GET /staff/{staffid}"):
            staff = get_object_or_404(Staff, staffid=staffid)
            return staff
    except Http404:
        raise NotFoundError("Staff", staffid)
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch staff: {str(e)}", exc_info=True)
        raise DatabaseError("Failed to fetch staff")


@api.post("/staff", auth=None)
def create_staff(request, payload: CreateStaffSchema):
    """Create a new staff member."""
    try:
        with PerformanceMonitor("POST /staff"):
            staff = Staff.objects.create(**payload.dict())
            return create_success_response(
                {"staffid": staff.staffid},
                "Staff member created successfully",
                201
            )
    except Exception as e:
        logger.error(f"Failed to create staff: {str(e)}", exc_info=True)
        raise DatabaseError("Failed to create staff member")


@api.put("/staff/{staffid}", auth=None)
@api.post("/staff/{staffid}", auth=None)
def update_staff(request, staffid: int, payload: CreateStaffSchema):
    """Update staff member information."""
    try:
        with PerformanceMonitor(f"PUT/POST /staff/{staffid}"):
            staff = get_object_or_404(Staff, staffid=staffid)
            for key, value in payload.dict().items():
                setattr(staff, key, value)
            staff.save()
            return create_success_response(
                {"staffid": staff.staffid},
                "Staff member updated successfully"
            )
    except Exception as e:
        if "404" in str(e):
            raise NotFoundError("Staff", staffid)
        logger.error(f"Failed to update staff: {str(e)}", exc_info=True)
        raise DatabaseError("Failed to update staff member")


@api.delete("/staff/{staffid}", auth=None)
def delete_staff(request, staffid: int):
    """Delete a staff member."""
    try:
        with PerformanceMonitor(f"DELETE /staff/{staffid}"):
            staff = get_object_or_404(Staff, staffid=staffid)
            staff.delete()
            return create_success_response(
                {"staffid": staffid},
                "Staff member deleted successfully"
            )
    except Exception as e:
        if "404" in str(e):
            raise NotFoundError("Staff", staffid)
        logger.error(f"Failed to delete staff: {str(e)}", exc_info=True)
        raise DatabaseError("Failed to delete staff member")


# ============================================================================
# WARD ENDPOINTS
# ============================================================================

@api.get("/wards", response=List[WardSchema], auth=None)
def get_wards(request):
    """Get all wards/rooms."""
    try:
        with PerformanceMonitor("GET /wards"):
            wards = Ward.objects.all()
            return list(wards)
    except Exception as e:
        logger.error(f"Failed to fetch wards: {str(e)}", exc_info=True)
        raise DatabaseError("Failed to fetch wards")


@api.get("/wards/{roomid}", response=WardSchema, auth=None)
def get_ward(request, roomid: int):
    """Get ward/room by ID."""
    try:
        with PerformanceMonitor(f"GET /wards/{roomid}"):
            ward = get_object_or_404(Ward, roomid=roomid)
            return ward
    except Exception as e:
        if "404" in str(e):
            raise NotFoundError("Ward", roomid)
        logger.error(f"Failed to fetch ward: {str(e)}", exc_info=True)
        raise DatabaseError("Failed to fetch ward")


@api.post("/wards", auth=None)
def create_ward(request, payload: CreateWardSchema):
    """Create a new ward/room."""
    try:
        with PerformanceMonitor("POST /wards"):
            ward = Ward.objects.create(**payload.dict())
            return create_success_response(
                {"roomid": ward.roomid},
                "Ward created successfully",
                201
            )
    except Exception as e:
        logger.error(f"Failed to create ward: {str(e)}", exc_info=True)
        raise DatabaseError("Failed to create ward")


@api.put("/wards/{roomid}", auth=None)
@api.post("/wards/{roomid}", auth=None)
def update_ward(request, roomid: int, payload: CreateWardSchema):
    """Update ward/room information."""
    try:
        with PerformanceMonitor(f"PUT/POST /wards/{roomid}"):
            ward = get_object_or_404(Ward, roomid=roomid)
            for key, value in payload.dict().items():
                setattr(ward, key, value)
            ward.save()
            return create_success_response(
                {"roomid": ward.roomid},
                "Ward updated successfully"
            )
    except Exception as e:
        if "404" in str(e):
            raise NotFoundError("Ward", roomid)
        logger.error(f"Failed to update ward: {str(e)}", exc_info=True)
        raise DatabaseError("Failed to update ward")


@api.delete("/wards/{roomid}", auth=None)
def delete_ward(request, roomid: int):
    """Delete a ward/room."""
    try:
        with PerformanceMonitor(f"DELETE /wards/{roomid}"):
            ward = get_object_or_404(Ward, roomid=roomid)
            ward.delete()
            return create_success_response(
                {"roomid": roomid},
                "Ward deleted successfully"
            )
    except Exception as e:
        if "404" in str(e):
            raise NotFoundError("Ward", roomid)
        logger.error(f"Failed to delete ward: {str(e)}", exc_info=True)
        raise DatabaseError("Failed to delete ward")


# ============================================================================
# DEPARTMENT ENDPOINTS
# ============================================================================

@api.get("/departments", response=List[DepartmentSchema], auth=None)
def get_departments(request):
    """Get all departments."""
    try:
        with PerformanceMonitor("GET /departments"):
            departments = Department.objects.all()
            return list(departments)
    except Exception as e:
        logger.error(f"Failed to fetch departments: {str(e)}", exc_info=True)
        raise DatabaseError("Failed to fetch departments")


@api.get("/departments/{deptid}", response=DepartmentSchema, auth=None)
def get_department(request, deptid: int):
    """Get department by ID."""
    try:
        with PerformanceMonitor(f"GET /departments/{deptid}"):
            department = get_object_or_404(Department, deptid=deptid)
            return department
    except Exception as e:
        if "404" in str(e):
            raise NotFoundError("Department", deptid)
        logger.error(f"Failed to fetch department: {str(e)}", exc_info=True)
        raise DatabaseError("Failed to fetch department")


@api.post("/departments", auth=None)
def create_department(request, payload: DepartmentCreate):
    """Create a new department."""
    try:
        with PerformanceMonitor("POST /departments"):
            department = Department.objects.create(**payload.dict())
            return create_success_response(
                {"deptid": department.deptid},
                "Department created successfully",
                201
            )
    except Exception as e:
        logger.error(f"Failed to create department: {str(e)}", exc_info=True)
        raise DatabaseError("Failed to create department")


@api.put("/departments/{deptid}", auth=None)
@api.post("/departments/{deptid}", auth=None)
def update_department(request, deptid: int, payload: DepartmentCreate):
    """Update department information."""
    try:
        with PerformanceMonitor(f"PUT/POST /departments/{deptid}"):
            department = get_object_or_404(Department, deptid=deptid)
            for key, value in payload.dict().items():
                setattr(department, key, value)
            department.save()
            return create_success_response(
                {"deptid": department.deptid},
                "Department updated successfully"
            )
    except Exception as e:
        if "404" in str(e):
            raise NotFoundError("Department", deptid)
        logger.error(f"Failed to update department: {str(e)}", exc_info=True)
        raise DatabaseError("Failed to update department")


@api.delete("/departments/{deptid}", auth=None)
def delete_department(request, deptid: int):
    """Delete a department."""
    try:
        with PerformanceMonitor(f"DELETE /departments/{deptid}"):
            department = get_object_or_404(Department, deptid=deptid)
            department.delete()
            return create_success_response(
                {"deptid": deptid},
                "Department deleted successfully"
            )
    except Exception as e:
        if "404" in str(e):
            raise NotFoundError("Department", deptid)
        logger.error(f"Failed to delete department: {str(e)}", exc_info=True)
        raise DatabaseError("Failed to delete department")



