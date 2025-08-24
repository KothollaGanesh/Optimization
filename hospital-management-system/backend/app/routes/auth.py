from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token, jwt_required,
    get_jwt_identity, get_jwt
)
from marshmallow import Schema, fields, ValidationError, validate
from app.models import db, User, UserRole, Patient, Doctor, Receptionist
from app.utils import (
    validate_email, validate_password_strength, generate_patient_id,
    generate_doctor_id, generate_employee_id
)

auth_bp = Blueprint('auth', __name__)

# Validation Schemas
class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=1))

class RegisterPatientSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=8))
    first_name = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    last_name = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    phone = fields.Str(validate=validate.Length(max=20))
    date_of_birth = fields.Date()
    gender = fields.Str(validate=validate.OneOf(['male', 'female', 'other']))
    address = fields.Str(validate=validate.Length(max=500))
    
    # Patient-specific fields
    blood_group = fields.Str(validate=validate.Length(max=5))
    allergies = fields.Str()
    emergency_contact_name = fields.Str(validate=validate.Length(max=100))
    emergency_contact_phone = fields.Str(validate=validate.Length(max=20))
    emergency_contact_relation = fields.Str(validate=validate.Length(max=50))
    insurance_provider = fields.Str(validate=validate.Length(max=100))
    insurance_policy_number = fields.Str(validate=validate.Length(max=50))

class ChangePasswordSchema(Schema):
    current_password = fields.Str(required=True)
    new_password = fields.Str(required=True, validate=validate.Length(min=8))

@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate user and return access token."""
    schema = LoginSchema()
    
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'details': err.messages}), 400
    
    # Find user by email
    user = User.query.filter_by(email=data['email']).first()
    
    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Invalid email or password'}), 401
    
    if not user.is_active:
        return jsonify({'error': 'Account is deactivated'}), 403
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.session.commit()
    
    # Create tokens
    access_token = create_access_token(
        identity=user.id,
        expires_delta=timedelta(hours=24)
    )
    refresh_token = create_refresh_token(identity=user.id)
    
    # Get role-specific profile
    profile = None
    if user.role == UserRole.PATIENT and user.patient_profile:
        profile = user.patient_profile.to_dict(include_user=False)
    elif user.role == UserRole.DOCTOR and user.doctor_profile:
        profile = user.doctor_profile.to_dict(include_user=False)
    elif user.role == UserRole.RECEPTIONIST and user.receptionist_profile:
        profile = user.receptionist_profile.to_dict(include_user=False)
    
    return jsonify({
        'message': 'Login successful',
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': user.to_dict(),
        'profile': profile
    }), 200

@auth_bp.route('/register/patient', methods=['POST'])
def register_patient():
    """Register a new patient."""
    schema = RegisterPatientSchema()
    
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'details': err.messages}), 400
    
    # Validate password strength
    is_strong, message = validate_password_strength(data['password'])
    if not is_strong:
        return jsonify({'error': message}), 400
    
    # Check if email already exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 409
    
    try:
        # Create user
        user = User(
            email=data['email'],
            password=data['password'],
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
            emergency_contact_name=data.get('emergency_contact_name'),
            emergency_contact_phone=data.get('emergency_contact_phone'),
            emergency_contact_relation=data.get('emergency_contact_relation'),
            insurance_provider=data.get('insurance_provider'),
            insurance_policy_number=data.get('insurance_policy_number')
        )
        
        db.session.add(patient)
        db.session.commit()
        
        return jsonify({
            'message': 'Patient registered successfully',
            'user': user.to_dict(),
            'patient': patient.to_dict(include_user=False)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Registration failed', 'details': str(e)}), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user or not user.is_active:
        return jsonify({'error': 'User not found or inactive'}), 404
    
    new_access_token = create_access_token(
        identity=current_user_id,
        expires_delta=timedelta(hours=24)
    )
    
    return jsonify({
        'access_token': new_access_token
    }), 200

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout user (token will be blacklisted)."""
    # In a production system, you would add the token to a blacklist
    # For now, we'll just return success
    return jsonify({'message': 'Successfully logged out'}), 200

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user profile."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Get role-specific profile
    profile = None
    if user.role == UserRole.PATIENT and user.patient_profile:
        profile = user.patient_profile.to_dict(include_user=False)
    elif user.role == UserRole.DOCTOR and user.doctor_profile:
        profile = user.doctor_profile.to_dict(include_user=False)
    elif user.role == UserRole.RECEPTIONIST and user.receptionist_profile:
        profile = user.receptionist_profile.to_dict(include_user=False)
    
    return jsonify({
        'user': user.to_dict(),
        'profile': profile
    }), 200

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user password."""
    schema = ChangePasswordSchema()
    
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'details': err.messages}), 400
    
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Verify current password
    if not user.check_password(data['current_password']):
        return jsonify({'error': 'Current password is incorrect'}), 400
    
    # Validate new password strength
    is_strong, message = validate_password_strength(data['new_password'])
    if not is_strong:
        return jsonify({'error': message}), 400
    
    # Update password
    user.set_password(data['new_password'])
    db.session.commit()
    
    return jsonify({'message': 'Password changed successfully'}), 200

@auth_bp.route('/verify-token', methods=['POST'])
@jwt_required()
def verify_token():
    """Verify if token is valid and get user info."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user or not user.is_active:
        return jsonify({'error': 'Invalid token or inactive user'}), 401
    
    return jsonify({
        'valid': True,
        'user': user.to_dict()
    }), 200