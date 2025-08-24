from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt

# Initialize extensions
db = SQLAlchemy()
jwt = JWTManager()
cors = CORS()
migrate = Migrate()
bcrypt = Bcrypt()

def create_app(config_name='default'):
    """Application factory pattern."""
    app = Flask(__name__)
    
    # Load configuration
    from config.config import config
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(app, origins=app.config['CORS_ORIGINS'])
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    
    # Import models to ensure they are registered with SQLAlchemy
    from app.models import (
        User, Patient, Doctor, Department, Specialization, DoctorSchedule,
        Appointment, Service, ServiceCategory, MedicalRecord, Prescription,
        LabOrder, Bill, BillItem, Payment, Receptionist
    )
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.users import users_bp
    from app.routes.patients import patients_bp
    from app.routes.doctors import doctors_bp
    from app.routes.appointments import appointments_bp
    from app.routes.medical_records import medical_records_bp
    from app.routes.billing import billing_bp
    from app.routes.admin import admin_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(patients_bp, url_prefix='/api/patients')
    app.register_blueprint(doctors_bp, url_prefix='/api/doctors')
    app.register_blueprint(appointments_bp, url_prefix='/api/appointments')
    app.register_blueprint(medical_records_bp, url_prefix='/api/medical-records')
    app.register_blueprint(billing_bp, url_prefix='/api/billing')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    
    # Error handlers
    from app.utils.error_handlers import register_error_handlers
    register_error_handlers(app)
    
    # JWT handlers
    from app.utils.jwt_handlers import register_jwt_handlers
    register_jwt_handlers(jwt)
    
    @app.route('/api/health')
    def health_check():
        return {'status': 'healthy', 'message': 'Hospital Management System API is running'}
    
    return app