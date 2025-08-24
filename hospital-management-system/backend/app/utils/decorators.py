from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from app.models import User, UserRole

def role_required(*allowed_roles):
    """
    Decorator to check if user has required role.
    Usage: @role_required(UserRole.ADMIN, UserRole.DOCTOR)
    """
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            if not user.is_active:
                return jsonify({'error': 'Account is deactivated'}), 403
            
            if user.role not in allowed_roles:
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            return f(current_user=user, *args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """Decorator for admin-only endpoints."""
    return role_required(UserRole.ADMIN)(f)

def doctor_required(f):
    """Decorator for doctor-only endpoints."""
    return role_required(UserRole.DOCTOR)(f)

def patient_required(f):
    """Decorator for patient-only endpoints."""
    return role_required(UserRole.PATIENT)(f)

def receptionist_required(f):
    """Decorator for receptionist-only endpoints."""
    return role_required(UserRole.RECEPTIONIST)(f)

def medical_staff_required(f):
    """Decorator for medical staff (doctors and admin)."""
    return role_required(UserRole.ADMIN, UserRole.DOCTOR)(f)

def staff_required(f):
    """Decorator for staff members (admin, doctors, receptionists)."""
    return role_required(UserRole.ADMIN, UserRole.DOCTOR, UserRole.RECEPTIONIST)(f)

def permission_required(resource, action):
    """
    Decorator to check specific permissions.
    Usage: @permission_required('patient', 'read')
    """
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            if not user.is_active:
                return jsonify({'error': 'Account is deactivated'}), 403
            
            if not user.can_access(resource, action):
                return jsonify({'error': f'Permission denied: cannot {action} {resource}'}), 403
            
            return f(current_user=user, *args, **kwargs)
        return decorated_function
    return decorator