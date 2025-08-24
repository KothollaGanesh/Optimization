from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, ValidationError, validate
from datetime import datetime, date, time
from app.models import (
    db, User, UserRole, Appointment, AppointmentStatus, AppointmentType,
    Patient, Doctor, Service
)
from app.utils import (
    staff_required, patient_required, generate_appointment_number,
    paginate_query, parse_date, parse_time
)

appointments_bp = Blueprint('appointments', __name__)

class CreateAppointmentSchema(Schema):
    patient_id = fields.Int(required=True)
    doctor_id = fields.Int(required=True)
    service_id = fields.Int()
    appointment_date = fields.Date(required=True)
    appointment_time = fields.Str(required=True)
    appointment_type = fields.Str(validate=validate.OneOf([t.value for t in AppointmentType]))
    chief_complaint = fields.Str()
    notes = fields.Str()
    priority = fields.Str(validate=validate.OneOf(['low', 'normal', 'high', 'emergency']))

class UpdateAppointmentSchema(Schema):
    appointment_date = fields.Date()
    appointment_time = fields.Str()
    appointment_type = fields.Str(validate=validate.OneOf([t.value for t in AppointmentType]))
    status = fields.Str(validate=validate.OneOf([s.value for s in AppointmentStatus]))
    chief_complaint = fields.Str()
    notes = fields.Str()
    priority = fields.Str(validate=validate.OneOf(['low', 'normal', 'high', 'emergency']))

class CancelAppointmentSchema(Schema):
    reason = fields.Str(required=True, validate=validate.Length(min=1))

@appointments_bp.route('/', methods=['GET'])
@jwt_required()
def get_appointments():
    """Get appointments based on user role and filters."""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    patient_id = request.args.get('patient_id', type=int)
    doctor_id = request.args.get('doctor_id', type=int)
    
    # Build base query
    query = Appointment.query
    
    # Apply role-based filtering
    if current_user.role == UserRole.PATIENT:
        # Patients can only see their own appointments and family members'
        patient = Patient.query.filter_by(user_id=current_user_id).first()
        if patient:
            family_patient_ids = [patient.id]
            family_patient_ids.extend([fm.id for fm in patient.get_family_members()])
            query = query.filter(Appointment.patient_id.in_(family_patient_ids))
        else:
            return jsonify({'appointments': []}), 200
    
    elif current_user.role == UserRole.DOCTOR:
        # Doctors can only see their own appointments
        doctor = Doctor.query.filter_by(user_id=current_user_id).first()
        if doctor:
            query = query.filter(Appointment.doctor_id == doctor.id)
        else:
            return jsonify({'appointments': []}), 200
    
    # Apply additional filters
    if status:
        try:
            status_enum = AppointmentStatus(status)
            query = query.filter(Appointment.status == status_enum)
        except ValueError:
            return jsonify({'error': f'Invalid status: {status}'}), 400
    
    if date_from:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
            query = query.filter(Appointment.appointment_date >= from_date)
        except ValueError:
            return jsonify({'error': 'Invalid date_from format. Use YYYY-MM-DD'}), 400
    
    if date_to:
        try:
            to_date = datetime.strptime(date_to, '%Y-%m-%d').date()
            query = query.filter(Appointment.appointment_date <= to_date)
        except ValueError:
            return jsonify({'error': 'Invalid date_to format. Use YYYY-MM-DD'}), 400
    
    if patient_id and current_user.role in [UserRole.ADMIN, UserRole.RECEPTIONIST, UserRole.DOCTOR]:
        query = query.filter(Appointment.patient_id == patient_id)
    
    if doctor_id and current_user.role in [UserRole.ADMIN, UserRole.RECEPTIONIST]:
        query = query.filter(Appointment.doctor_id == doctor_id)
    
    # Order by appointment date and time
    query = query.order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc())
    
    # Paginate
    result = paginate_query(query, page, per_page)
    result['items'] = [appointment.to_dict() for appointment in result['items']]
    
    return jsonify(result), 200

@appointments_bp.route('/', methods=['POST'])
@jwt_required()
def create_appointment():
    """Create a new appointment."""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    schema = CreateAppointmentSchema()
    
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'details': err.messages}), 400
    
    # Verify patient exists
    patient = Patient.query.get(data['patient_id'])
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    
    # Check if patient can book appointment (for patient role)
    if current_user.role == UserRole.PATIENT:
        current_patient = Patient.query.filter_by(user_id=current_user_id).first()
        if not current_patient:
            return jsonify({'error': 'Patient profile not found'}), 404
        
        # Can only book for self or family members
        if (patient.id != current_patient.id and 
            patient.primary_patient_id != current_patient.id):
            return jsonify({'error': 'Can only book appointments for yourself or family members'}), 403
    
    # Verify doctor exists and is available
    doctor = Doctor.query.get(data['doctor_id'])
    if not doctor:
        return jsonify({'error': 'Doctor not found'}), 404
    
    if not doctor.is_available:
        return jsonify({'error': 'Doctor is not available'}), 400
    
    # Verify service exists if provided
    service = None
    if data.get('service_id'):
        service = Service.query.get(data['service_id'])
        if not service:
            return jsonify({'error': 'Service not found'}), 404
    
    try:
        # Parse appointment time
        appointment_time = parse_time(data['appointment_time'])
        
        # Check for appointment conflicts
        appointment_datetime = datetime.combine(data['appointment_date'], appointment_time)
        
        # Check if appointment is in the future
        if appointment_datetime <= datetime.now():
            return jsonify({'error': 'Appointment must be scheduled for a future date and time'}), 400
        
        # Check for existing appointments at the same time
        existing = Appointment.query.filter(
            Appointment.doctor_id == data['doctor_id'],
            Appointment.appointment_date == data['appointment_date'],
            Appointment.appointment_time == appointment_time,
            Appointment.status.in_([AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED])
        ).first()
        
        if existing:
            return jsonify({'error': 'Doctor already has an appointment at this time'}), 409
        
        # Create appointment
        appointment = Appointment(
            appointment_number=generate_appointment_number(),
            patient_id=data['patient_id'],
            doctor_id=data['doctor_id'],
            service_id=data.get('service_id'),
            appointment_date=data['appointment_date'],
            appointment_time=appointment_time,
            appointment_type=AppointmentType(data.get('appointment_type', 'consultation')),
            chief_complaint=data.get('chief_complaint'),
            notes=data.get('notes'),
            priority=data.get('priority', 'normal'),
            created_by_user_id=current_user_id
        )
        
        db.session.add(appointment)
        db.session.commit()
        
        return jsonify({
            'message': 'Appointment created successfully',
            'appointment': appointment.to_dict()
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create appointment', 'details': str(e)}), 500

@appointments_bp.route('/<int:appointment_id>', methods=['GET'])
@jwt_required()
def get_appointment(appointment_id):
    """Get specific appointment by ID."""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    appointment = Appointment.query.get_or_404(appointment_id)
    
    # Check permissions
    if current_user.role == UserRole.PATIENT:
        patient = Patient.query.filter_by(user_id=current_user_id).first()
        if patient:
            family_patient_ids = [patient.id]
            family_patient_ids.extend([fm.id for fm in patient.get_family_members()])
            if appointment.patient_id not in family_patient_ids:
                return jsonify({'error': 'Access denied'}), 403
        else:
            return jsonify({'error': 'Access denied'}), 403
    
    elif current_user.role == UserRole.DOCTOR:
        doctor = Doctor.query.filter_by(user_id=current_user_id).first()
        if not doctor or appointment.doctor_id != doctor.id:
            return jsonify({'error': 'Access denied'}), 403
    
    return jsonify({'appointment': appointment.to_dict()}), 200

@appointments_bp.route('/<int:appointment_id>', methods=['PUT'])
@jwt_required()
def update_appointment(appointment_id):
    """Update appointment."""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    appointment = Appointment.query.get_or_404(appointment_id)
    
    # Check permissions
    can_update = False
    if current_user.role in [UserRole.ADMIN, UserRole.RECEPTIONIST]:
        can_update = True
    elif current_user.role == UserRole.PATIENT:
        patient = Patient.query.filter_by(user_id=current_user_id).first()
        if patient and appointment.patient_id == patient.id:
            can_update = True
    elif current_user.role == UserRole.DOCTOR:
        doctor = Doctor.query.filter_by(user_id=current_user_id).first()
        if doctor and appointment.doctor_id == doctor.id:
            can_update = True
    
    if not can_update:
        return jsonify({'error': 'Access denied'}), 403
    
    schema = UpdateAppointmentSchema()
    
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'details': err.messages}), 400
    
    try:
        # Handle rescheduling
        if 'appointment_date' in data or 'appointment_time' in data:
            if not appointment.can_be_rescheduled():
                return jsonify({'error': 'Appointment cannot be rescheduled'}), 400
            
            new_date = data.get('appointment_date', appointment.appointment_date)
            new_time = parse_time(data.get('appointment_time')) if 'appointment_time' in data else appointment.appointment_time
            
            # Check for conflicts
            existing = Appointment.query.filter(
                Appointment.doctor_id == appointment.doctor_id,
                Appointment.appointment_date == new_date,
                Appointment.appointment_time == new_time,
                Appointment.id != appointment_id,
                Appointment.status.in_([AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED])
            ).first()
            
            if existing:
                return jsonify({'error': 'Doctor already has an appointment at this time'}), 409
            
            appointment.reschedule(new_date, new_time, "Rescheduled by user")
        
        # Update other fields
        if 'appointment_type' in data:
            appointment.appointment_type = AppointmentType(data['appointment_type'])
        
        if 'status' in data and current_user.role in [UserRole.ADMIN, UserRole.RECEPTIONIST, UserRole.DOCTOR]:
            appointment.status = AppointmentStatus(data['status'])
        
        if 'chief_complaint' in data:
            appointment.chief_complaint = data['chief_complaint']
        
        if 'notes' in data:
            appointment.notes = data['notes']
        
        if 'priority' in data and current_user.role in [UserRole.ADMIN, UserRole.RECEPTIONIST, UserRole.DOCTOR]:
            appointment.priority = data['priority']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Appointment updated successfully',
            'appointment': appointment.to_dict()
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update appointment', 'details': str(e)}), 500

@appointments_bp.route('/<int:appointment_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_appointment(appointment_id):
    """Cancel appointment."""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    appointment = Appointment.query.get_or_404(appointment_id)
    
    # Check permissions
    can_cancel = False
    if current_user.role in [UserRole.ADMIN, UserRole.RECEPTIONIST]:
        can_cancel = True
    elif current_user.role == UserRole.PATIENT:
        patient = Patient.query.filter_by(user_id=current_user_id).first()
        if patient and appointment.patient_id == patient.id:
            can_cancel = True
    
    if not can_cancel:
        return jsonify({'error': 'Access denied'}), 403
    
    schema = CancelAppointmentSchema()
    
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'details': err.messages}), 400
    
    if not appointment.can_be_cancelled():
        return jsonify({'error': 'Appointment cannot be cancelled'}), 400
    
    if appointment.cancel(data['reason'], current_user_id):
        db.session.commit()
        return jsonify({
            'message': 'Appointment cancelled successfully',
            'appointment': appointment.to_dict()
        }), 200
    else:
        return jsonify({'error': 'Failed to cancel appointment'}), 500

@appointments_bp.route('/<int:appointment_id>/check-in', methods=['POST'])
@staff_required
def check_in_appointment(current_user, appointment_id):
    """Check in patient for appointment."""
    appointment = Appointment.query.get_or_404(appointment_id)
    
    if appointment.check_in():
        db.session.commit()
        return jsonify({
            'message': 'Patient checked in successfully',
            'appointment': appointment.to_dict()
        }), 200
    else:
        return jsonify({'error': 'Cannot check in this appointment'}), 400

@appointments_bp.route('/<int:appointment_id>/check-out', methods=['POST'])
@staff_required
def check_out_appointment(current_user, appointment_id):
    """Check out patient from appointment."""
    appointment = Appointment.query.get_or_404(appointment_id)
    
    if appointment.check_out():
        db.session.commit()
        return jsonify({
            'message': 'Patient checked out successfully',
            'appointment': appointment.to_dict()
        }), 200
    else:
        return jsonify({'error': 'Cannot check out this appointment'}), 400

@appointments_bp.route('/available-slots', methods=['GET'])
@jwt_required()
def get_available_slots():
    """Get available appointment slots for a doctor on a specific date."""
    doctor_id = request.args.get('doctor_id', type=int)
    date_str = request.args.get('date')
    
    if not doctor_id or not date_str:
        return jsonify({'error': 'doctor_id and date are required'}), 400
    
    try:
        appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    
    doctor = Doctor.query.get_or_404(doctor_id)
    
    # Get doctor's schedule for the date
    schedule = doctor.get_availability_for_date(appointment_date)
    
    if not schedule or not schedule.get('is_available'):
        return jsonify({'available_slots': []}), 200
    
    # Get existing appointments for the date
    existing_appointments = Appointment.query.filter(
        Appointment.doctor_id == doctor_id,
        Appointment.appointment_date == appointment_date,
        Appointment.status.in_([AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED])
    ).all()
    
    booked_times = [apt.appointment_time for apt in existing_appointments]
    
    # Generate available slots (simplified - in production, this would be more sophisticated)
    available_slots = []
    start_time = datetime.strptime(schedule['start_time'], '%H:%M').time()
    end_time = datetime.strptime(schedule['end_time'], '%H:%M').time()
    duration = doctor.consultation_duration
    
    current_time = datetime.combine(appointment_date, start_time)
    end_datetime = datetime.combine(appointment_date, end_time)
    
    while current_time < end_datetime:
        if current_time.time() not in booked_times:
            available_slots.append(current_time.strftime('%H:%M'))
        current_time += timedelta(minutes=duration)
    
    return jsonify({'available_slots': available_slots}), 200