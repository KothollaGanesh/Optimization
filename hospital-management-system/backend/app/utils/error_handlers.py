from flask import jsonify
from werkzeug.exceptions import HTTPException
from sqlalchemy.exc import IntegrityError, ValidationError
from marshmallow import ValidationError as MarshmallowValidationError

def register_error_handlers(app):
    """Register error handlers for the Flask app."""
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'error': 'Bad Request',
            'message': error.description or 'The request was invalid'
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            'error': 'Unauthorized',
            'message': 'Authentication required'
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            'error': 'Forbidden',
            'message': 'Access denied'
        }), 403
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'Not Found',
            'message': 'The requested resource was not found'
        }), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            'error': 'Method Not Allowed',
            'message': 'The request method is not allowed for this endpoint'
        }), 405
    
    @app.errorhandler(409)
    def conflict(error):
        return jsonify({
            'error': 'Conflict',
            'message': error.description or 'A conflict occurred'
        }), 409
    
    @app.errorhandler(422)
    def unprocessable_entity(error):
        return jsonify({
            'error': 'Unprocessable Entity',
            'message': error.description or 'The request was well-formed but contains semantic errors'
        }), 422
    
    @app.errorhandler(500)
    def internal_server_error(error):
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }), 500
    
    @app.errorhandler(IntegrityError)
    def handle_integrity_error(error):
        """Handle database integrity errors."""
        error_message = str(error.orig)
        
        # Common integrity error patterns
        if 'Duplicate entry' in error_message:
            if 'email' in error_message:
                message = 'Email address already exists'
            elif 'patient_id' in error_message:
                message = 'Patient ID already exists'
            elif 'doctor_id' in error_message:
                message = 'Doctor ID already exists'
            elif 'employee_id' in error_message:
                message = 'Employee ID already exists'
            else:
                message = 'Duplicate entry detected'
        elif 'foreign key constraint' in error_message.lower():
            message = 'Referenced record does not exist'
        else:
            message = 'Database constraint violation'
        
        return jsonify({
            'error': 'Data Integrity Error',
            'message': message
        }), 409
    
    @app.errorhandler(MarshmallowValidationError)
    def handle_marshmallow_validation_error(error):
        """Handle Marshmallow validation errors."""
        return jsonify({
            'error': 'Validation Error',
            'message': 'Input validation failed',
            'details': error.messages
        }), 422
    
    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        """Handle SQLAlchemy validation errors."""
        return jsonify({
            'error': 'Validation Error',
            'message': str(error)
        }), 422
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        """Handle other HTTP exceptions."""
        return jsonify({
            'error': error.name,
            'message': error.description
        }), error.code
    
    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        """Handle unexpected errors."""
        # Log the error for debugging
        app.logger.error(f"Unexpected error: {str(error)}")
        
        # Return generic error message in production
        if app.config.get('DEBUG'):
            return jsonify({
                'error': 'Unexpected Error',
                'message': str(error),
                'type': type(error).__name__
            }), 500
        else:
            return jsonify({
                'error': 'Internal Server Error',
                'message': 'An unexpected error occurred'
            }), 500