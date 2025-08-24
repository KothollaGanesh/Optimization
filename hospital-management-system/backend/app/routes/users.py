from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from marshmallow import Schema, fields, ValidationError, validate
from app.models import db, User, UserRole
from app.utils import admin_required, staff_required, paginate_query

users_bp = Blueprint('users', __name__)

class UpdateUserSchema(Schema):
    first_name = fields.Str(validate=validate.Length(min=1, max=50))
    last_name = fields.Str(validate=validate.Length(min=1, max=50))
    phone = fields.Str(validate=validate.Length(max=20))
    date_of_birth = fields.Date()
    gender = fields.Str(validate=validate.OneOf(['male', 'female', 'other']))
    address = fields.Str(validate=validate.Length(max=500))
    is_active = fields.Bool()

@users_bp.route('/', methods=['GET'])
@staff_required
def get_users(current_user):
    """Get list of users with pagination and filtering."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    role = request.args.get('role')
    search = request.args.get('search')
    is_active = request.args.get('is_active', type=bool)
    
    # Build query
    query = User.query
    
    # Apply filters
    if role:
        try:
            role_enum = UserRole(role)
            query = query.filter(User.role == role_enum)
        except ValueError:
            return jsonify({'error': f'Invalid role: {role}'}), 400
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            db.or_(
                User.first_name.ilike(search_term),
                User.last_name.ilike(search_term),
                User.email.ilike(search_term)
            )
        )
    
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    # Order by creation date
    query = query.order_by(User.created_at.desc())
    
    # Paginate
    result = paginate_query(query, page, per_page)
    result['items'] = [user.to_dict() for user in result['items']]
    
    return jsonify(result), 200

@users_bp.route('/<int:user_id>', methods=['GET'])
@staff_required
def get_user(current_user, user_id):
    """Get specific user by ID."""
    user = User.query.get_or_404(user_id)
    
    # Include role-specific profile
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

@users_bp.route('/<int:user_id>', methods=['PUT'])
@staff_required
def update_user(current_user, user_id):
    """Update user information."""
    user = User.query.get_or_404(user_id)
    
    # Only admin can update other admins
    if user.role == UserRole.ADMIN and current_user.role != UserRole.ADMIN:
        return jsonify({'error': 'Insufficient permissions'}), 403
    
    schema = UpdateUserSchema()
    
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'details': err.messages}), 400
    
    # Update user fields
    for field, value in data.items():
        if hasattr(user, field):
            setattr(user, field, value)
    
    db.session.commit()
    
    return jsonify({
        'message': 'User updated successfully',
        'user': user.to_dict()
    }), 200

@users_bp.route('/<int:user_id>/activate', methods=['POST'])
@admin_required
def activate_user(current_user, user_id):
    """Activate user account."""
    user = User.query.get_or_404(user_id)
    
    if user.is_active:
        return jsonify({'error': 'User is already active'}), 400
    
    user.is_active = True
    db.session.commit()
    
    return jsonify({
        'message': 'User activated successfully',
        'user': user.to_dict()
    }), 200

@users_bp.route('/<int:user_id>/deactivate', methods=['POST'])
@admin_required
def deactivate_user(current_user, user_id):
    """Deactivate user account."""
    user = User.query.get_or_404(user_id)
    
    # Prevent deactivating self
    if user.id == current_user.id:
        return jsonify({'error': 'Cannot deactivate your own account'}), 400
    
    if not user.is_active:
        return jsonify({'error': 'User is already inactive'}), 400
    
    user.is_active = False
    db.session.commit()
    
    return jsonify({
        'message': 'User deactivated successfully',
        'user': user.to_dict()
    }), 200

@users_bp.route('/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(current_user, user_id):
    """Delete user account (soft delete by deactivating)."""
    user = User.query.get_or_404(user_id)
    
    # Prevent deleting self
    if user.id == current_user.id:
        return jsonify({'error': 'Cannot delete your own account'}), 400
    
    # Prevent deleting other admins unless you're a super admin
    if user.role == UserRole.ADMIN:
        return jsonify({'error': 'Cannot delete admin users'}), 403
    
    # Soft delete by deactivating
    user.is_active = False
    db.session.commit()
    
    return jsonify({'message': 'User deleted successfully'}), 200

@users_bp.route('/stats', methods=['GET'])
@staff_required
def get_user_stats(current_user):
    """Get user statistics."""
    total_users = User.query.count()
    active_users = User.query.filter(User.is_active == True).count()
    
    # Count by role
    role_counts = {}
    for role in UserRole:
        count = User.query.filter(User.role == role, User.is_active == True).count()
        role_counts[role.value] = count
    
    return jsonify({
        'total_users': total_users,
        'active_users': active_users,
        'inactive_users': total_users - active_users,
        'role_counts': role_counts
    }), 200