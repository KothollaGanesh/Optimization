from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from marshmallow import Schema, fields, ValidationError, validate
from datetime import datetime, time
from app.models import (
    db, User, UserRole, Doctor, Department, Specialization, 
    DoctorSchedule
)
from app.utils import (
    admin_required, staff_required, generate_doctor_id, 
    paginate_query, parse_time
)

doctors_bp = Blueprint('doctors', __name__)

class CreateDoctorSchema(Schema):
    # User fields
    email = fields.Email(required=True)
    first_name = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    last_name = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    phone = fields.Str(validate=validate.Length(max=20))
    date_of_birth = fields.Date()
    gender = fields.Str(validate=validate.OneOf(['male', 'female', 'other']))
    address = fields.Str(validate=validate.Length(max=500))
    
    # Doctor-specific fields
    license_number = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    department_id = fields.Int(required=True)
    qualification = fields.Str(validate=validate.Length(max=200))
    experience_years = fields.Int(validate=validate.Range(min=0))
    consultation_fee = fields.Decimal(validate=validate.Range(min=0))
    biography = fields.Str()
    consultation_duration = fields.Int(validate=validate.Range(min=15, max=120))
    specialization_ids = fields.List(fields.Int())

class UpdateDoctorSchema(Schema):
    # User fields
    first_name = fields.Str(validate=validate.Length(min=1, max=50))
    last_name = fields.Str(validate=validate.Length(min=1, max=50))
    phone = fields.Str(validate=validate.Length(max=20))
    date_of_birth = fields.Date()
    gender = fields.Str(validate=validate.OneOf(['male', 'female', 'other']))
    address = fields.Str(validate=validate.Length(max=500))
    
    # Doctor-specific fields
    license_number = fields.Str(validate=validate.Length(min=1, max=50))
    department_id = fields.Int()
    qualification = fields.Str(validate=validate.Length(max=200))
    experience_years = fields.Int(validate=validate.Range(min=0))
    consultation_fee = fields.Decimal(validate=validate.Range(min=0))
    biography = fields.Str()
    consultation_duration = fields.Int(validate=validate.Range(min=15, max=120))
    is_available = fields.Bool()
    specialization_ids = fields.List(fields.Int())

class CreateScheduleSchema(Schema):
    date = fields.Date()  # For specific date
    day_of_week = fields.Int(validate=validate.Range(min=0, max=6))  # For recurring
    is_recurring = fields.Bool(missing=False)
    start_time = fields.Str(required=True)
    end_time = fields.Str(required=True)
    break_start_time = fields.Str()
    break_end_time = fields.Str()
    max_appointments = fields.Int(validate=validate.Range(min=1))
    is_available = fields.Bool(missing=True)

class CreateDepartmentSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    description = fields.Str()
    head_doctor_id = fields.Int()

class CreateSpecializationSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    description = fields.Str()

@doctors_bp.route('/', methods=['GET'])
@jwt_required()
def get_doctors():
    """Get list of doctors with pagination and filtering."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    department_id = request.args.get('department_id', type=int)
    specialization_id = request.args.get('specialization_id', type=int)
    search = request.args.get('search')
    is_available = request.args.get('is_available', type=bool)
    
    # Build query
    query = Doctor.query.join(User)
    
    # Apply filters
    if department_id:
        query = query.filter(Doctor.department_id == department_id)
    
    if specialization_id:
        query = query.join(Doctor.specializations).filter(
            Specialization.id == specialization_id
        )
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            db.or_(
                User.first_name.ilike(search_term),
                User.last_name.ilike(search_term),
                Doctor.doctor_id.ilike(search_term),
                Doctor.qualification.ilike(search_term)
            )
        )
    
    if is_available is not None:
        query = query.filter(Doctor.is_available == is_available)
    
    # Order by name
    query = query.order_by(User.first_name, User.last_name)
    
    # Paginate
    result = paginate_query(query, page, per_page)
    result['items'] = [doctor.to_dict() for doctor in result['items']]
    
    return jsonify(result), 200

@doctors_bp.route('/', methods=['POST'])
@admin_required
def create_doctor(current_user):
    """Create a new doctor (admin only)."""
    schema = CreateDoctorSchema()
    
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'details': err.messages}), 400
    
    # Check if email or license already exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 409
    
    if Doctor.query.filter_by(license_number=data['license_number']).first():
        return jsonify({'error': 'License number already exists'}), 409
    
    # Verify department exists
    department = Department.query.get(data['department_id'])
    if not department:
        return jsonify({'error': 'Department not found'}), 404
    
    try:
        # Create user
        user = User(
            email=data['email'],
            password='TempPass123!',  # Doctor will need to change this
            role=UserRole.DOCTOR,
            first_name=data['first_name'],
            last_name=data['last_name'],
            phone=data.get('phone'),
            date_of_birth=data.get('date_of_birth'),
            gender=data.get('gender'),
            address=data.get('address')
        )
        
        db.session.add(user)
        db.session.flush()  # Get user ID
        
        # Create doctor profile
        doctor = Doctor(
            user_id=user.id,
            doctor_id=generate_doctor_id(),
            license_number=data['license_number'],
            department_id=data['department_id'],
            qualification=data.get('qualification'),
            experience_years=data.get('experience_years'),
            consultation_fee=data.get('consultation_fee'),
            biography=data.get('biography'),
            consultation_duration=data.get('consultation_duration', 30)
        )
        
        db.session.add(doctor)
        db.session.flush()  # Get doctor ID
        
        # Add specializations
        if data.get('specialization_ids'):
            specializations = Specialization.query.filter(
                Specialization.id.in_(data['specialization_ids'])
            ).all()
            doctor.specializations.extend(specializations)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Doctor created successfully',
            'doctor': doctor.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create doctor', 'details': str(e)}), 500

@doctors_bp.route('/<int:doctor_id>', methods=['GET'])
@jwt_required()
def get_doctor(doctor_id):
    """Get specific doctor by ID."""
    doctor = Doctor.query.get_or_404(doctor_id)
    return jsonify({'doctor': doctor.to_dict()}), 200

@doctors_bp.route('/<int:doctor_id>', methods=['PUT'])
@staff_required
def update_doctor(current_user, doctor_id):
    """Update doctor information."""
    doctor = Doctor.query.get_or_404(doctor_id)
    
    # Only admin or the doctor themselves can update
    if (current_user.role != UserRole.ADMIN and 
        current_user.doctor_profile and 
        current_user.doctor_profile.id != doctor_id):
        return jsonify({'error': 'Access denied'}), 403
    
    schema = UpdateDoctorSchema()
    
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'details': err.messages}), 400
    
    # Check license number uniqueness
    if 'license_number' in data:
        existing = Doctor.query.filter(
            Doctor.license_number == data['license_number'],
            Doctor.id != doctor_id
        ).first()
        if existing:
            return jsonify({'error': 'License number already exists'}), 409
    
    # Update user fields
    user_fields = ['first_name', 'last_name', 'phone', 'date_of_birth', 'gender', 'address']
    for field in user_fields:
        if field in data:
            setattr(doctor.user, field, data[field])
    
    # Update doctor fields
    doctor_fields = [
        'license_number', 'department_id', 'qualification', 'experience_years',
        'consultation_fee', 'biography', 'consultation_duration', 'is_available'
    ]
    for field in doctor_fields:
        if field in data:
            setattr(doctor, field, data[field])
    
    # Update specializations
    if 'specialization_ids' in data:
        specializations = Specialization.query.filter(
            Specialization.id.in_(data['specialization_ids'])
        ).all()
        doctor.specializations = specializations
    
    db.session.commit()
    
    return jsonify({
        'message': 'Doctor updated successfully',
        'doctor': doctor.to_dict()
    }), 200

@doctors_bp.route('/<int:doctor_id>/schedule', methods=['GET'])
@jwt_required()
def get_doctor_schedule(doctor_id):
    """Get doctor's schedule."""
    doctor = Doctor.query.get_or_404(doctor_id)
    
    date_str = request.args.get('date')
    if date_str:
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            schedule = doctor.get_availability_for_date(date_obj)
            return jsonify({'schedule': schedule}), 200
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    
    # Get all schedules
    schedules = DoctorSchedule.query.filter_by(doctor_id=doctor_id).all()
    return jsonify({
        'schedules': [schedule.to_dict() for schedule in schedules]
    }), 200

@doctors_bp.route('/<int:doctor_id>/schedule', methods=['POST'])
@staff_required
def create_doctor_schedule(current_user, doctor_id):
    """Create doctor schedule."""
    doctor = Doctor.query.get_or_404(doctor_id)
    
    schema = CreateScheduleSchema()
    
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'details': err.messages}), 400
    
    # Validate that either date or day_of_week is provided
    if not data.get('date') and data.get('day_of_week') is None:
        return jsonify({'error': 'Either date or day_of_week must be provided'}), 400
    
    try:
        # Parse times
        start_time = parse_time(data['start_time'])
        end_time = parse_time(data['end_time'])
        
        if start_time >= end_time:
            return jsonify({'error': 'End time must be after start time'}), 400
        
        # Parse break times if provided
        break_start_time = None
        break_end_time = None
        if data.get('break_start_time') and data.get('break_end_time'):
            break_start_time = parse_time(data['break_start_time'])
            break_end_time = parse_time(data['break_end_time'])
            
            if break_start_time >= break_end_time:
                return jsonify({'error': 'Break end time must be after break start time'}), 400
        
        # Create schedule
        schedule = DoctorSchedule(
            doctor_id=doctor_id,
            date=data.get('date'),
            day_of_week=data.get('day_of_week'),
            is_recurring=data.get('is_recurring', False),
            start_time=start_time,
            end_time=end_time,
            break_start_time=break_start_time,
            break_end_time=break_end_time,
            max_appointments=data.get('max_appointments', 10),
            is_available=data.get('is_available', True)
        )
        
        db.session.add(schedule)
        db.session.commit()
        
        return jsonify({
            'message': 'Schedule created successfully',
            'schedule': schedule.to_dict()
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create schedule', 'details': str(e)}), 500

# Department endpoints
@doctors_bp.route('/departments', methods=['GET'])
@jwt_required()
def get_departments():
    """Get all departments."""
    departments = Department.query.filter_by(is_active=True).all()
    return jsonify({
        'departments': [dept.to_dict() for dept in departments]
    }), 200

@doctors_bp.route('/departments', methods=['POST'])
@admin_required
def create_department(current_user):
    """Create a new department."""
    schema = CreateDepartmentSchema()
    
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'details': err.messages}), 400
    
    # Check if department name already exists
    if Department.query.filter_by(name=data['name']).first():
        return jsonify({'error': 'Department name already exists'}), 409
    
    department = Department(
        name=data['name'],
        description=data.get('description'),
        head_doctor_id=data.get('head_doctor_id')
    )
    
    db.session.add(department)
    db.session.commit()
    
    return jsonify({
        'message': 'Department created successfully',
        'department': department.to_dict()
    }), 201

# Specialization endpoints
@doctors_bp.route('/specializations', methods=['GET'])
@jwt_required()
def get_specializations():
    """Get all specializations."""
    specializations = Specialization.query.all()
    return jsonify({
        'specializations': [spec.to_dict() for spec in specializations]
    }), 200

@doctors_bp.route('/specializations', methods=['POST'])
@admin_required
def create_specialization(current_user):
    """Create a new specialization."""
    schema = CreateSpecializationSchema()
    
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'details': err.messages}), 400
    
    # Check if specialization name already exists
    if Specialization.query.filter_by(name=data['name']).first():
        return jsonify({'error': 'Specialization name already exists'}), 409
    
    specialization = Specialization(
        name=data['name'],
        description=data.get('description')
    )
    
    db.session.add(specialization)
    db.session.commit()
    
    return jsonify({
        'message': 'Specialization created successfully',
        'specialization': specialization.to_dict()
    }), 201