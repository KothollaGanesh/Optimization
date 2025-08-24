from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, ValidationError, validate
from app.models import (
    db, User, UserRole, MedicalRecord, Prescription, LabOrder,
    Patient, Doctor, Appointment
)
from app.utils import (
    medical_staff_required, staff_required, generate_record_number,
    generate_prescription_number, generate_lab_order_number, paginate_query
)

medical_records_bp = Blueprint('medical_records', __name__)

class CreateMedicalRecordSchema(Schema):
    patient_id = fields.Int(required=True)
    appointment_id = fields.Int()
    chief_complaint = fields.Str()
    history_of_present_illness = fields.Str()
    past_medical_history = fields.Str()
    family_history = fields.Str()
    social_history = fields.Str()
    allergies = fields.Str()
    current_medications = fields.Str()
    vital_signs = fields.Dict()
    physical_examination = fields.Str()
    diagnosis_primary = fields.Str()
    diagnosis_secondary = fields.Str()
    assessment = fields.Str()
    treatment_plan = fields.Str()
    follow_up_instructions = fields.Str()
    follow_up_date = fields.Date()
    is_confidential = fields.Bool(missing=False)

class UpdateMedicalRecordSchema(Schema):
    chief_complaint = fields.Str()
    history_of_present_illness = fields.Str()
    past_medical_history = fields.Str()
    family_history = fields.Str()
    social_history = fields.Str()
    allergies = fields.Str()
    current_medications = fields.Str()
    vital_signs = fields.Dict()
    physical_examination = fields.Str()
    diagnosis_primary = fields.Str()
    diagnosis_secondary = fields.Str()
    assessment = fields.Str()
    treatment_plan = fields.Str()
    follow_up_instructions = fields.Str()
    follow_up_date = fields.Date()
    is_confidential = fields.Bool()

class CreatePrescriptionSchema(Schema):
    medical_record_id = fields.Int(required=True)
    medication_name = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    dosage = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    frequency = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    duration = fields.Str(validate=validate.Length(max=100))
    quantity = fields.Str(validate=validate.Length(max=50))
    instructions = fields.Str()
    special_instructions = fields.Str()

class CreateLabOrderSchema(Schema):
    medical_record_id = fields.Int(required=True)
    test_name = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    test_code = fields.Str(validate=validate.Length(max=50))
    urgency = fields.Str(validate=validate.OneOf(['routine', 'urgent', 'stat']))
    clinical_notes = fields.Str()
    special_instructions = fields.Str()

@medical_records_bp.route('/', methods=['GET'])
@jwt_required()
def get_medical_records():
    """Get medical records based on user role and filters."""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    patient_id = request.args.get('patient_id', type=int)
    
    # Build base query
    query = MedicalRecord.query
    
    # Apply role-based filtering
    if current_user.role == UserRole.PATIENT:
        # Patients can only see their own records and family members'
        patient = Patient.query.filter_by(user_id=current_user_id).first()
        if patient:
            family_patient_ids = [patient.id]
            family_patient_ids.extend([fm.id for fm in patient.get_family_members()])
            query = query.filter(MedicalRecord.patient_id.in_(family_patient_ids))
        else:
            return jsonify({'medical_records': []}), 200
    
    elif current_user.role == UserRole.DOCTOR:
        # Doctors can see records they created or for their current patients
        doctor = Doctor.query.filter_by(user_id=current_user_id).first()
        if doctor:
            query = query.filter(MedicalRecord.doctor_id == doctor.id)
        else:
            return jsonify({'medical_records': []}), 200
    
    # Apply additional filters
    if patient_id and current_user.role in [UserRole.ADMIN, UserRole.DOCTOR, UserRole.RECEPTIONIST]:
        query = query.filter(MedicalRecord.patient_id == patient_id)
    
    # Order by visit date
    query = query.order_by(MedicalRecord.visit_date.desc())
    
    # Paginate
    result = paginate_query(query, page, per_page)
    result['items'] = [record.to_dict() for record in result['items']]
    
    return jsonify(result), 200

@medical_records_bp.route('/', methods=['POST'])
@medical_staff_required
def create_medical_record(current_user):
    """Create a new medical record (doctors and admin only)."""
    schema = CreateMedicalRecordSchema()
    
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'details': err.messages}), 400
    
    # Verify patient exists
    patient = Patient.query.get(data['patient_id'])
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    
    # Get doctor
    doctor = None
    if current_user.role == UserRole.DOCTOR:
        doctor = Doctor.query.filter_by(user_id=current_user.id).first()
        if not doctor:
            return jsonify({'error': 'Doctor profile not found'}), 404
    
    # Verify appointment if provided
    appointment = None
    if data.get('appointment_id'):
        appointment = Appointment.query.get(data['appointment_id'])
        if not appointment:
            return jsonify({'error': 'Appointment not found'}), 404
    
    try:
        # Create medical record
        medical_record = MedicalRecord(
            record_number=generate_record_number(),
            patient_id=data['patient_id'],
            doctor_id=doctor.id if doctor else None,
            appointment_id=data.get('appointment_id'),
            chief_complaint=data.get('chief_complaint'),
            history_of_present_illness=data.get('history_of_present_illness'),
            past_medical_history=data.get('past_medical_history'),
            family_history=data.get('family_history'),
            social_history=data.get('social_history'),
            allergies=data.get('allergies'),
            current_medications=data.get('current_medications'),
            vital_signs=data.get('vital_signs'),
            physical_examination=data.get('physical_examination'),
            diagnosis_primary=data.get('diagnosis_primary'),
            diagnosis_secondary=data.get('diagnosis_secondary'),
            assessment=data.get('assessment'),
            treatment_plan=data.get('treatment_plan'),
            follow_up_instructions=data.get('follow_up_instructions'),
            follow_up_date=data.get('follow_up_date'),
            is_confidential=data.get('is_confidential', False)
        )
        
        db.session.add(medical_record)
        db.session.commit()
        
        return jsonify({
            'message': 'Medical record created successfully',
            'medical_record': medical_record.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create medical record', 'details': str(e)}), 500

@medical_records_bp.route('/<int:record_id>', methods=['GET'])
@jwt_required()
def get_medical_record(record_id):
    """Get specific medical record by ID."""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    medical_record = MedicalRecord.query.get_or_404(record_id)
    
    # Check permissions
    can_view = False
    
    if current_user.role in [UserRole.ADMIN]:
        can_view = True
    elif current_user.role == UserRole.DOCTOR:
        doctor = Doctor.query.filter_by(user_id=current_user_id).first()
        if doctor and medical_record.doctor_id == doctor.id:
            can_view = True
    elif current_user.role == UserRole.PATIENT:
        patient = Patient.query.filter_by(user_id=current_user_id).first()
        if patient:
            family_patient_ids = [patient.id]
            family_patient_ids.extend([fm.id for fm in patient.get_family_members()])
            if medical_record.patient_id in family_patient_ids:
                can_view = True
    elif current_user.role == UserRole.RECEPTIONIST:
        # Receptionists can view non-confidential records
        if not medical_record.is_confidential:
            can_view = True
    
    if not can_view:
        return jsonify({'error': 'Access denied'}), 403
    
    return jsonify({'medical_record': medical_record.to_dict()}), 200

@medical_records_bp.route('/<int:record_id>', methods=['PUT'])
@medical_staff_required
def update_medical_record(current_user, record_id):
    """Update medical record."""
    medical_record = MedicalRecord.query.get_or_404(record_id)
    
    # Check if user can edit this record
    if not medical_record.can_be_edited(current_user):
        return jsonify({'error': 'Cannot edit this medical record'}), 403
    
    schema = UpdateMedicalRecordSchema()
    
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'details': err.messages}), 400
    
    # Update fields
    for field, value in data.items():
        if hasattr(medical_record, field):
            setattr(medical_record, field, value)
    
    db.session.commit()
    
    return jsonify({
        'message': 'Medical record updated successfully',
        'medical_record': medical_record.to_dict()
    }), 200

@medical_records_bp.route('/<int:record_id>/finalize', methods=['POST'])
@medical_staff_required
def finalize_medical_record(current_user, record_id):
    """Finalize medical record."""
    medical_record = MedicalRecord.query.get_or_404(record_id)
    
    # Check if user can edit this record
    if not medical_record.can_be_edited(current_user):
        return jsonify({'error': 'Cannot finalize this medical record'}), 403
    
    if medical_record.finalize_record():
        db.session.commit()
        return jsonify({
            'message': 'Medical record finalized successfully',
            'medical_record': medical_record.to_dict()
        }), 200
    else:
        return jsonify({'error': 'Cannot finalize this record'}), 400

# Prescription endpoints
@medical_records_bp.route('/prescriptions', methods=['POST'])
@medical_staff_required
def create_prescription(current_user):
    """Create a new prescription."""
    schema = CreatePrescriptionSchema()
    
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'details': err.messages}), 400
    
    # Verify medical record exists and user can edit it
    medical_record = MedicalRecord.query.get(data['medical_record_id'])
    if not medical_record:
        return jsonify({'error': 'Medical record not found'}), 404
    
    if not medical_record.can_be_edited(current_user):
        return jsonify({'error': 'Cannot add prescription to this medical record'}), 403
    
    try:
        prescription = Prescription(
            prescription_number=generate_prescription_number(),
            medical_record_id=data['medical_record_id'],
            medication_name=data['medication_name'],
            dosage=data['dosage'],
            frequency=data['frequency'],
            duration=data.get('duration'),
            quantity=data.get('quantity'),
            instructions=data.get('instructions'),
            special_instructions=data.get('special_instructions')
        )
        
        db.session.add(prescription)
        db.session.commit()
        
        return jsonify({
            'message': 'Prescription created successfully',
            'prescription': prescription.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create prescription', 'details': str(e)}), 500

@medical_records_bp.route('/prescriptions/<int:prescription_id>', methods=['GET'])
@jwt_required()
def get_prescription(prescription_id):
    """Get specific prescription by ID."""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    prescription = Prescription.query.get_or_404(prescription_id)
    medical_record = prescription.medical_record
    
    # Check permissions (same as medical record permissions)
    can_view = False
    
    if current_user.role in [UserRole.ADMIN]:
        can_view = True
    elif current_user.role == UserRole.DOCTOR:
        doctor = Doctor.query.filter_by(user_id=current_user_id).first()
        if doctor and medical_record.doctor_id == doctor.id:
            can_view = True
    elif current_user.role == UserRole.PATIENT:
        patient = Patient.query.filter_by(user_id=current_user_id).first()
        if patient and medical_record.patient_id == patient.id:
            can_view = True
    
    if not can_view:
        return jsonify({'error': 'Access denied'}), 403
    
    return jsonify({'prescription': prescription.to_dict()}), 200

# Lab Order endpoints
@medical_records_bp.route('/lab-orders', methods=['POST'])
@medical_staff_required
def create_lab_order(current_user):
    """Create a new lab order."""
    schema = CreateLabOrderSchema()
    
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'details': err.messages}), 400
    
    # Verify medical record exists and user can edit it
    medical_record = MedicalRecord.query.get(data['medical_record_id'])
    if not medical_record:
        return jsonify({'error': 'Medical record not found'}), 404
    
    if not medical_record.can_be_edited(current_user):
        return jsonify({'error': 'Cannot add lab order to this medical record'}), 403
    
    try:
        lab_order = LabOrder(
            order_number=generate_lab_order_number(),
            medical_record_id=data['medical_record_id'],
            test_name=data['test_name'],
            test_code=data.get('test_code'),
            urgency=data.get('urgency', 'routine'),
            clinical_notes=data.get('clinical_notes'),
            special_instructions=data.get('special_instructions')
        )
        
        db.session.add(lab_order)
        db.session.commit()
        
        return jsonify({
            'message': 'Lab order created successfully',
            'lab_order': lab_order.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create lab order', 'details': str(e)}), 500

@medical_records_bp.route('/lab-orders/<int:order_id>', methods=['GET'])
@staff_required
def get_lab_order(current_user, order_id):
    """Get specific lab order by ID."""
    lab_order = LabOrder.query.get_or_404(order_id)
    return jsonify({'lab_order': lab_order.to_dict()}), 200

@medical_records_bp.route('/patient/<int:patient_id>/summary', methods=['GET'])
@staff_required
def get_patient_medical_summary(current_user, patient_id):
    """Get patient's medical summary."""
    patient = Patient.query.get_or_404(patient_id)
    
    # Get recent medical records
    recent_records = MedicalRecord.query.filter_by(patient_id=patient_id)\
        .order_by(MedicalRecord.visit_date.desc()).limit(5).all()
    
    # Get active prescriptions
    active_prescriptions = Prescription.query.join(MedicalRecord)\
        .filter(MedicalRecord.patient_id == patient_id, Prescription.is_active == True)\
        .order_by(Prescription.created_at.desc()).limit(10).all()
    
    # Get pending lab orders
    pending_lab_orders = LabOrder.query.join(MedicalRecord)\
        .filter(MedicalRecord.patient_id == patient_id, 
                LabOrder.status.in_(['ordered', 'collected', 'processing']))\
        .order_by(LabOrder.ordered_date.desc()).all()
    
    return jsonify({
        'patient': patient.to_dict(),
        'recent_records': [record.to_dict(include_patient=False, include_doctor=True) 
                          for record in recent_records],
        'active_prescriptions': [prescription.to_dict() for prescription in active_prescriptions],
        'pending_lab_orders': [order.to_dict() for order in pending_lab_orders]
    }), 200