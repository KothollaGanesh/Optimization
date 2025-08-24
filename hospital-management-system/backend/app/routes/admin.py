from flask import Blueprint, request, jsonify
from marshmallow import Schema, fields, ValidationError, validate
from datetime import datetime, timedelta
from app.models import (
    db, User, UserRole, Patient, Doctor, Appointment, MedicalRecord,
    Bill, Payment, Department, Service, Receptionist
)
from app.utils import admin_required, generate_employee_id, validate_password_strength

admin_bp = Blueprint('admin', __name__)

class CreateUserSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=8))
    role = fields.Str(required=True, validate=validate.OneOf([r.value for r in UserRole]))
    first_name = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    last_name = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    phone = fields.Str(validate=validate.Length(max=20))
    date_of_birth = fields.Date()
    gender = fields.Str(validate=validate.OneOf(['male', 'female', 'other']))
    address = fields.Str(validate=validate.Length(max=500))

class CreateReceptionistSchema(Schema):
    user_data = fields.Nested(CreateUserSchema, required=True)
    department_id = fields.Int()
    shift = fields.Str(validate=validate.OneOf(['morning', 'afternoon', 'night', 'rotating']))
    hire_date = fields.Date(required=True)
    emergency_contact_name = fields.Str(validate=validate.Length(max=100))
    emergency_contact_phone = fields.Str(validate=validate.Length(max=20))
    emergency_contact_relation = fields.Str(validate=validate.Length(max=50))
    # Permissions
    can_manage_appointments = fields.Bool(missing=True)
    can_process_payments = fields.Bool(missing=True)
    can_access_medical_records = fields.Bool(missing=False)
    can_manage_patient_registration = fields.Bool(missing=True)

class CreateServiceSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    description = fields.Str()
    service_code = fields.Str(required=True, validate=validate.Length(min=1, max=20))
    base_price = fields.Decimal(required=True, validate=validate.Range(min=0))
    insurance_price = fields.Decimal(validate=validate.Range(min=0))
    duration_minutes = fields.Int(validate=validate.Range(min=1))
    category = fields.Str(validate=validate.Length(max=50))
    subcategory = fields.Str(validate=validate.Length(max=50))
    department_id = fields.Int(required=True)
    requires_appointment = fields.Bool(missing=True)
    is_emergency_service = fields.Bool(missing=False)
    requires_referral = fields.Bool(missing=False)
    preparation_instructions = fields.Str()

@admin_bp.route('/dashboard', methods=['GET'])
@admin_required
def get_admin_dashboard(current_user):
    """Get admin dashboard statistics."""
    # Calculate date ranges
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # User statistics
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    new_users_this_week = User.query.filter(User.created_at >= week_ago).count()
    
    # Patient statistics
    total_patients = Patient.query.count()
    new_patients_this_week = Patient.query.filter(Patient.created_at >= week_ago).count()
    
    # Doctor statistics
    total_doctors = Doctor.query.count()
    available_doctors = Doctor.query.filter_by(is_available=True).count()
    
    # Appointment statistics
    total_appointments = Appointment.query.count()
    appointments_today = Appointment.query.filter_by(appointment_date=today).count()
    appointments_this_week = Appointment.query.filter(Appointment.appointment_date >= week_ago).count()
    
    # Revenue statistics
    revenue_query = db.session.query(db.func.sum(Payment.amount)).filter(
        Payment.status == 'completed',
        Payment.payment_date >= month_ago
    )
    revenue_this_month = float(revenue_query.scalar() or 0)
    
    outstanding_query = db.session.query(db.func.sum(Bill.total_amount - Bill.paid_amount)).filter(
        Bill.status.in_(['pending', 'partial', 'overdue'])
    )
    total_outstanding = float(outstanding_query.scalar() or 0)
    
    # Department statistics
    departments = Department.query.filter_by(is_active=True).all()
    department_stats = []
    for dept in departments:
        dept_doctors = Doctor.query.filter_by(department_id=dept.id).count()
        dept_appointments = Appointment.query.join(Doctor).filter(
            Doctor.department_id == dept.id,
            Appointment.appointment_date >= week_ago
        ).count()
        
        department_stats.append({
            'department': dept.to_dict(),
            'doctor_count': dept_doctors,
            'appointments_this_week': dept_appointments
        })
    
    return jsonify({
        'user_statistics': {
            'total_users': total_users,
            'active_users': active_users,
            'inactive_users': total_users - active_users,
            'new_users_this_week': new_users_this_week
        },
        'patient_statistics': {
            'total_patients': total_patients,
            'new_patients_this_week': new_patients_this_week
        },
        'doctor_statistics': {
            'total_doctors': total_doctors,
            'available_doctors': available_doctors,
            'unavailable_doctors': total_doctors - available_doctors
        },
        'appointment_statistics': {
            'total_appointments': total_appointments,
            'appointments_today': appointments_today,
            'appointments_this_week': appointments_this_week
        },
        'financial_statistics': {
            'revenue_this_month': revenue_this_month,
            'total_outstanding': total_outstanding
        },
        'department_statistics': department_stats
    }), 200

@admin_bp.route('/users', methods=['POST'])
@admin_required
def create_user(current_user):
    """Create a new user (any role)."""
    schema = CreateUserSchema()
    
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
        user = User(
            email=data['email'],
            password=data['password'],
            role=UserRole(data['role']),
            first_name=data['first_name'],
            last_name=data['last_name'],
            phone=data.get('phone'),
            date_of_birth=data.get('date_of_birth'),
            gender=data.get('gender'),
            address=data.get('address')
        )
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'message': 'User created successfully',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create user', 'details': str(e)}), 500

@admin_bp.route('/receptionists', methods=['POST'])
@admin_required
def create_receptionist(current_user):
    """Create a new receptionist."""
    schema = CreateReceptionistSchema()
    
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'details': err.messages}), 400
    
    user_data = data['user_data']
    
    # Validate password strength
    is_strong, message = validate_password_strength(user_data['password'])
    if not is_strong:
        return jsonify({'error': message}), 400
    
    # Check if email already exists
    if User.query.filter_by(email=user_data['email']).first():
        return jsonify({'error': 'Email already registered'}), 409
    
    # Verify department if provided
    if data.get('department_id'):
        department = Department.query.get(data['department_id'])
        if not department:
            return jsonify({'error': 'Department not found'}), 404
    
    try:
        # Create user
        user = User(
            email=user_data['email'],
            password=user_data['password'],
            role=UserRole.RECEPTIONIST,
            first_name=user_data['first_name'],
            last_name=user_data['last_name'],
            phone=user_data.get('phone'),
            date_of_birth=user_data.get('date_of_birth'),
            gender=user_data.get('gender'),
            address=user_data.get('address')
        )
        
        db.session.add(user)
        db.session.flush()  # Get user ID
        
        # Create receptionist profile
        receptionist = Receptionist(
            user_id=user.id,
            employee_id=generate_employee_id(),
            department_id=data.get('department_id'),
            shift=data.get('shift', 'morning'),
            hire_date=data['hire_date'],
            emergency_contact_name=data.get('emergency_contact_name'),
            emergency_contact_phone=data.get('emergency_contact_phone'),
            emergency_contact_relation=data.get('emergency_contact_relation'),
            can_manage_appointments=data.get('can_manage_appointments', True),
            can_process_payments=data.get('can_process_payments', True),
            can_access_medical_records=data.get('can_access_medical_records', False),
            can_manage_patient_registration=data.get('can_manage_patient_registration', True)
        )
        
        db.session.add(receptionist)
        db.session.commit()
        
        return jsonify({
            'message': 'Receptionist created successfully',
            'receptionist': receptionist.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create receptionist', 'details': str(e)}), 500

@admin_bp.route('/services', methods=['POST'])
@admin_required
def create_service(current_user):
    """Create a new service."""
    schema = CreateServiceSchema()
    
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'details': err.messages}), 400
    
    # Check if service code already exists
    if Service.query.filter_by(service_code=data['service_code']).first():
        return jsonify({'error': 'Service code already exists'}), 409
    
    # Verify department exists
    department = Department.query.get(data['department_id'])
    if not department:
        return jsonify({'error': 'Department not found'}), 404
    
    try:
        service = Service(
            name=data['name'],
            description=data.get('description'),
            service_code=data['service_code'],
            base_price=data['base_price'],
            insurance_price=data.get('insurance_price'),
            duration_minutes=data.get('duration_minutes', 30),
            category=data.get('category'),
            subcategory=data.get('subcategory'),
            department_id=data['department_id'],
            requires_appointment=data.get('requires_appointment', True),
            is_emergency_service=data.get('is_emergency_service', False),
            requires_referral=data.get('requires_referral', False),
            preparation_instructions=data.get('preparation_instructions')
        )
        
        db.session.add(service)
        db.session.commit()
        
        return jsonify({
            'message': 'Service created successfully',
            'service': service.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create service', 'details': str(e)}), 500

@admin_bp.route('/services/<int:service_id>', methods=['PUT'])
@admin_required
def update_service(current_user, service_id):
    """Update service."""
    service = Service.query.get_or_404(service_id)
    
    schema = CreateServiceSchema()
    
    try:
        data = schema.load(request.json, partial=True)
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'details': err.messages}), 400
    
    # Check service code uniqueness
    if 'service_code' in data:
        existing = Service.query.filter(
            Service.service_code == data['service_code'],
            Service.id != service_id
        ).first()
        if existing:
            return jsonify({'error': 'Service code already exists'}), 409
    
    # Update fields
    for field, value in data.items():
        if hasattr(service, field):
            setattr(service, field, value)
    
    db.session.commit()
    
    return jsonify({
        'message': 'Service updated successfully',
        'service': service.to_dict()
    }), 200

@admin_bp.route('/system/backup', methods=['POST'])
@admin_required
def create_backup(current_user):
    """Create system backup (placeholder)."""
    # This would implement actual backup logic in production
    return jsonify({
        'message': 'Backup initiated successfully',
        'backup_id': f'backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
        'status': 'pending'
    }), 200

@admin_bp.route('/system/health', methods=['GET'])
@admin_required
def system_health_check(current_user):
    """Get system health status."""
    try:
        # Check database connectivity
        db.session.execute('SELECT 1')
        database_status = 'healthy'
    except Exception:
        database_status = 'unhealthy'
    
    # Get system metrics
    total_users = User.query.count()
    active_sessions = User.query.filter(
        User.last_login >= datetime.now() - timedelta(hours=24)
    ).count()
    
    return jsonify({
        'status': 'healthy' if database_status == 'healthy' else 'unhealthy',
        'database': database_status,
        'metrics': {
            'total_users': total_users,
            'active_sessions_24h': active_sessions,
            'uptime': '99.9%',  # This would be calculated from actual monitoring
            'response_time': '150ms'  # This would be from actual metrics
        },
        'timestamp': datetime.now().isoformat()
    }), 200

@admin_bp.route('/audit-logs', methods=['GET'])
@admin_required
def get_audit_logs(current_user):
    """Get audit logs (placeholder)."""
    # This would implement actual audit log retrieval in production
    return jsonify({
        'audit_logs': [
            {
                'id': 1,
                'user_id': current_user.id,
                'action': 'LOGIN',
                'resource': 'system',
                'timestamp': datetime.now().isoformat(),
                'ip_address': '192.168.1.1',
                'user_agent': 'Mozilla/5.0...'
            }
        ],
        'total': 1,
        'page': 1,
        'per_page': 20
    }), 200

@admin_bp.route('/reports/summary', methods=['GET'])
@admin_required
def get_summary_report(current_user):
    """Get comprehensive summary report."""
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    # Default to last 30 days if no dates provided
    if not date_from:
        date_from = (datetime.now() - timedelta(days=30)).date()
    else:
        date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
    
    if not date_to:
        date_to = datetime.now().date()
    else:
        date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
    
    # Appointment statistics
    appointments_count = Appointment.query.filter(
        Appointment.appointment_date.between(date_from, date_to)
    ).count()
    
    completed_appointments = Appointment.query.filter(
        Appointment.appointment_date.between(date_from, date_to),
        Appointment.status == 'completed'
    ).count()
    
    # Revenue statistics
    revenue = db.session.query(db.func.sum(Payment.amount)).filter(
        Payment.payment_date.between(date_from, date_to),
        Payment.status == 'completed'
    ).scalar() or 0
    
    # Patient statistics
    new_patients = Patient.query.filter(
        Patient.created_at.between(date_from, date_to)
    ).count()
    
    return jsonify({
        'report_period': {
            'from': date_from.isoformat(),
            'to': date_to.isoformat()
        },
        'appointments': {
            'total': appointments_count,
            'completed': completed_appointments,
            'completion_rate': (completed_appointments / appointments_count * 100) if appointments_count > 0 else 0
        },
        'revenue': {
            'total': float(revenue),
            'average_per_day': float(revenue) / ((date_to - date_from).days + 1)
        },
        'patients': {
            'new_registrations': new_patients
        }
    }), 200