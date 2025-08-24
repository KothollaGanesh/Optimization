from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from enum import Enum

db = SQLAlchemy()
bcrypt = Bcrypt()

class UserRole(Enum):
    ADMIN = "admin"
    DOCTOR = "doctor"
    PATIENT = "patient"
    RECEPTIONIST = "receptionist"

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.Enum(UserRole), nullable=False, default=UserRole.PATIENT)
    
    # Personal Information
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.Enum('male', 'female', 'other', name='gender_enum'))
    address = db.Column(db.Text)
    
    # System fields
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    patient_profile = db.relationship('Patient', backref='user', uselist=False, cascade='all, delete-orphan')
    doctor_profile = db.relationship('Doctor', backref='user', uselist=False, cascade='all, delete-orphan')
    receptionist_profile = db.relationship('Receptionist', backref='user', uselist=False, cascade='all, delete-orphan')
    
    def __init__(self, email, password, role, first_name, last_name, **kwargs):
        self.email = email
        self.set_password(password)
        self.role = role
        self.first_name = first_name
        self.last_name = last_name
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def set_password(self, password):
        """Hash and set password."""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        """Check password against hash."""
        return bcrypt.check_password_hash(self.password_hash, password)
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def has_role(self, role):
        """Check if user has specific role."""
        return self.role == role
    
    def can_access(self, resource, action):
        """Check if user can perform action on resource."""
        # This will be expanded based on specific RBAC requirements
        permissions = {
            UserRole.ADMIN: {'all': ['create', 'read', 'update', 'delete']},
            UserRole.DOCTOR: {
                'patient': ['read', 'update'],
                'appointment': ['read', 'update'],
                'medical_record': ['create', 'read', 'update'],
                'prescription': ['create', 'read', 'update']
            },
            UserRole.PATIENT: {
                'own_profile': ['read', 'update'],
                'family_member': ['create', 'read', 'update'],
                'appointment': ['create', 'read', 'update', 'delete'],
                'medical_record': ['read'],
                'bill': ['read']
            },
            UserRole.RECEPTIONIST: {
                'patient': ['create', 'read', 'update'],
                'appointment': ['create', 'read', 'update', 'delete'],
                'bill': ['create', 'read', 'update'],
                'payment': ['create', 'read', 'update']
            }
        }
        
        if self.role == UserRole.ADMIN:
            return True
        
        role_permissions = permissions.get(self.role, {})
        resource_permissions = role_permissions.get(resource, [])
        return action in resource_permissions or 'all' in resource_permissions
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'email': self.email,
            'role': self.role.value,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'phone': self.phone,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'gender': self.gender,
            'address': self.address,
            'is_active': self.is_active,
            'email_verified': self.email_verified,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def __repr__(self):
        return f'<User {self.email} ({self.role.value})>'