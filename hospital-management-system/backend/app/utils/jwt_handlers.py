from flask import jsonify
from datetime import datetime
from app.models import User

def register_jwt_handlers(jwt):
    """Register JWT handlers for the Flask-JWT-Extended instance."""
    
    @jwt.user_identity_loader
    def user_identity_lookup(user):
        """Define how to get user identity from user object."""
        if isinstance(user, User):
            return user.id
        return user
    
    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        """Define how to load user from JWT payload."""
        identity = jwt_data["sub"]
        return User.query.filter_by(id=identity).one_or_none()
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        """Handle expired tokens."""
        return jsonify({
            'error': 'Token Expired',
            'message': 'The token has expired'
        }), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        """Handle invalid tokens."""
        return jsonify({
            'error': 'Invalid Token',
            'message': 'The token is invalid'
        }), 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        """Handle missing tokens."""
        return jsonify({
            'error': 'Authorization Required',
            'message': 'Request does not contain an access token'
        }), 401
    
    @jwt.needs_fresh_token_loader
    def token_not_fresh_callback(jwt_header, jwt_payload):
        """Handle non-fresh tokens when fresh token is required."""
        return jsonify({
            'error': 'Fresh Token Required',
            'message': 'A fresh token is required'
        }), 401
    
    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        """Handle revoked tokens."""
        return jsonify({
            'error': 'Token Revoked',
            'message': 'The token has been revoked'
        }), 401
    
    @jwt.token_verification_failed_loader
    def token_verification_failed_callback(jwt_header, jwt_payload):
        """Handle token verification failures."""
        return jsonify({
            'error': 'Token Verification Failed',
            'message': 'Token verification failed'
        }), 401
    
    @jwt.additional_claims_loader
    def add_claims_to_jwt(identity):
        """Add additional claims to JWT payload."""
        user = User.query.get(identity)
        if user:
            return {
                'role': user.role.value,
                'email': user.email,
                'is_active': user.is_active,
                'last_login': user.last_login.isoformat() if user.last_login else None
            }
        return {}
    
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        """Check if token is in blocklist (for token revocation)."""
        # Implement token blocklist logic here if needed
        # For now, we'll check if user is still active
        user_id = jwt_payload['sub']
        user = User.query.get(user_id)
        return user is None or not user.is_active