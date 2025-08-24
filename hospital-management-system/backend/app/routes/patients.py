from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, ValidationError, validate
from app.models import db, User, UserRole, Patient
from app.utils import (
    staff_required, patient_required, generate_patient_id, 
    paginate_query, validate_email
)

patients_bp = Blueprint('patients', __name__)

class CreatePatientSchema(Schema):
    # User fields
    email = fields.Email(required=True)
    first_name = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    last_name = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    phone = fields.Str(validate=validate.Length(max=20))
    date_of_birth = fields.Date()
    gender = fields.Str(validate=validate.OneOf(['male', 'female', 'other']))
    address = fields.Str(validate=validate.Length(max=500))
    
    # Patient-specific fields
    blood_group = fields.Str(validate=validate.Length(max=5))
    allergies = fields.Str()
    chronic_conditions = fields.Str()
    emergency_contact_name = fields.Str(validate=validate.Length(max=100))
    emergency_contact_phone = fields.Str(validate=validate.Length(max=20))
    emergency_contact_relation = fields.Str(validate=validate.Length(max=50))
    insurance_provider = fields.Str(validate=validate.Length(max=100))
    insurance_policy_number = fields.Str(validate=validate.Length(max=50))
    insurance_group_number = fields.Str(validate=validate.Length(max=50))
    insurance_expiry_date = fields.Date()

class UpdatePatientSchema(Schema):
    # User fields
    first_name = fields.Str(validate=validate.Length(min=1, max=50))
    last_name = fields.Str(validate=validate.Length(min=1, max=50))
    phone = fields.Str(validate=validate.Length(max=20))
    date_of_birth = fields.Date()
    gender = fields.Str(validate=validate.OneOf(['male', 'female', 'other']))
    address = fields.Str(validate=validate.Length(max=500))
    
    # Patient-specific fields
    blood_group = fields.Str(validate=validate.Length(max=5))
    allergies = fields.Str()
    chronic_conditions = fields.Str()
    emergency_contact_name = fields.Str(validate=validate.Length(max=100))
    emergency_contact_phone = fields.Str(validate=validate.Length(max=20))
    emergency_contact_relation = fields.Str(validate=validate.Length(max=50))
    insurance_provider = fields.Str(validate=validate.Length(max=100))
    insurance_policy_number = fields.Str(validate=validate.Length(max=50))
    insurance_group_number = fields.Str(validate=validate.Length(max=50))
    insurance_expiry_date = fields.Date()

class AddFamilyMemberSchema(Schema):
    first_name = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    last_name = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    relationship = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    date_of_birth = fields.Date()
    gender = fields.Str(validate=validate.OneOf(['male', 'female', 'other']))
    blood_group = fields.Str(validate=validate.Length(max=5))
    allergies = fields.Str()

@patients_bp.route('/', methods=['GET'])
@staff_required
def get_patients(current_user):
    """Get list of patients with pagination and filtering."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search')
    
    # Build query
    query = Patient.query.join(User)
    
    # Apply search filter
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            db.or_(
                User.first_name.ilike(search_term),
                User.last_name.ilike(search_term),
                User.email.ilike(search_term),
                Patient.patient_id.ilike(search_term)
            )
        )
    
    # Order by creation date
    query = query.order_by(Patient.created_at.desc())
    
    # Paginate
    result = paginate_query(query, page, per_page)
    result['items'] = [patient.to_dict() for patient in result['items']]
    
    return jsonify(result), 200

@patients_bp.route('/', methods=['POST'])
@staff_required
def create_patient(current_user):
    """Create a new patient (staff only)."""
    schema = CreatePatientSchema()
    
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'details': err.messages}), 400
    
    # Check if email already exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 409
    
    try:
        # Create user with temporary password
        user = User(
            email=data['email'],
            password='TempPass123!',  # Patient will need to change this
            role=UserRole.PATIENT,
            first_name=data['first_name'],
            last_name=data['last_name'],
            phone=data.get('phone'),
            date_of_birth=data.get('date_of_birth'),
            gender=data.get('gender'),
            address=data.get('address')
        )
        
        db.session.add(user)
        db.session.flush()  # Get user ID
        
        # Create patient profile
        patient = Patient(
            user_id=user.id,
            patient_id=generate_patient_id(),
            blood_group=data.get('blood_group'),
            allergies=data.get('allergies'),
            chronic_conditions=data.get('chronic_conditions'),
            emergency_contact_name=data.get('emergency_contact_name'),
            emergency_contact_phone=data.get('emergency_contact_phone'),
            emergency_contact_relation=data.get('emergency_contact_relation'),
            insurance_provider=data.get('insurance_provider'),
            insurance_policy_number=data.get('insurance_policy_number'),
            insurance_group_number=data.get('insurance_group_number'),
            insurance_expiry_date=data.get('insurance_expiry_date')
        )
        
        db.session.add(patient)
        db.session.commit()
        
        return jsonify({
            'message': 'Patient created successfully',
            'patient': patient.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create patient', 'details': str(e)}), 500

@patients_bp.route('/<int:patient_id>', methods=['GET'])
@jwt_required()
def get_patient(patient_id):
    """Get specific patient by ID."""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    patient = Patient.query.get_or_404(patient_id)
    
    # Check permissions
    if current_user.role == UserRole.PATIENT:
        # Patients can only view their own profile or family members
        if patient.user_id != current_user_id:
            # Check if it's a family member
            current_patient = Patient.query.filter_by(user_id=current_user_id).first()
            if not current_patient or patient.primary_patient_id != current_patient.id:
                return jsonify({'error': 'Access denied'}), 403
    elif current_user.role not in [UserRole.ADMIN, UserRole.DOCTOR, UserRole.RECEPTIONIST]:
        return jsonify({'error': 'Access denied'}), 403
    
    return jsonify({'patient': patient.to_dict()}), 200

@patients_bp.route('/<int:patient_id>', methods=['PUT'])
@jwt_required()
def update_patient(patient_id):
    """Update patient information."""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    patient = Patient.query.get_or_404(patient_id)
    
    # Check permissions
    if current_user.role == UserRole.PATIENT:
        if patient.user_id != current_user_id:
            return jsonify({'error': 'Can only update your own profile'}), 403
    elif current_user.role not in [UserRole.ADMIN, UserRole.RECEPTIONIST]:
        return jsonify({'error': 'Access denied'}), 403
    
    schema = UpdatePatientSchema()
    
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'details': err.messages}), 400
    
    # Update user fields
    user_fields = ['first_name', 'last_name', 'phone', 'date_of_birth', 'gender', 'address']
    for field in user_fields:
        if field in data:
            setattr(patient.user, field, data[field])
    
    # Update patient fields
    patient_fields = [
        'blood_group', 'allergies', 'chronic_conditions', 'emergency_contact_name',
        'emergency_contact_phone', 'emergency_contact_relation', 'insurance_provider',
        'insurance_policy_number', 'insurance_group_number', 'insurance_expiry_date'
    ]
    for field in patient_fields:
        if field in data:
            setattr(patient, field, data[field])
    
    db.session.commit()
    
    return jsonify({
        'message': 'Patient updated successfully',
        'patient': patient.to_dict()
    }), 200

@patients_bp.route('/my-family', methods=['GET'])
@patient_required
def get_my_family(current_user):
    """Get current patient's family members."""
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    if not patient:
        return jsonify({'error': 'Patient profile not found'}), 404
    
    family_members = patient.get_family_members()
    
    return jsonify({
        'family_members': [member.to_dict() for member in family_members]
    }), 200

@patients_bp.route('/family-member', methods=['POST'])
@patient_required
def add_family_member(current_user):
    """Add a family member."""
    schema = AddFamilyMemberSchema()
    
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'details': err.messages}), 400
    
    # Get current patient
    primary_patient = Patient.query.filter_by(user_id=current_user.id).first()
    if not primary_patient:
        return jsonify({'error': 'Patient profile not found'}), 404
    
    try:
        # Create user for family member (no login credentials)
        family_user = User(
            email=f"family_{generate_patient_id()}@temp.local",  # Temporary email
            password='NoLogin123!',  # No login allowed
            role=UserRole.PATIENT,
            first_name=data['first_name'],
            last_name=data['last_name'],
            date_of_birth=data.get('date_of_birth'),
            gender=data.get('gender'),
            is_active=False  # Family members don't have login access
        )
        
        db.session.add(family_user)
        db.session.flush()
        
        # Create family member patient profile
        family_patient = Patient(
            user_id=family_user.id,
            patient_id=generate_patient_id(),
            primary_patient_id=primary_patient.id,
            blood_group=data.get('blood_group'),
            allergies=data.get('allergies')
        )
        
        db.session.add(family_patient)
        db.session.commit()
        
        return jsonify({
            'message': 'Family member added successfully',
            'family_member': family_patient.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to add family member', 'details': str(e)}), 500

@patients_bp.route('/search', methods=['GET'])
@staff_required
def search_patients(current_user):
    """Search patients by various criteria."""
    query_param = request.args.get('q', '').strip()
    
    if not query_param:
        return jsonify({'patients': []}), 200
    
    # Search in multiple fields
    search_term = f"%{query_param}%"
    patients = Patient.query.join(User).filter(
        db.or_(
            User.first_name.ilike(search_term),
            User.last_name.ilike(search_term),
            User.email.ilike(search_term),
            Patient.patient_id.ilike(search_term)
        )
    ).limit(10).all()
    
    return jsonify({
        'patients': [patient.to_dict() for patient in patients]
    }), 200