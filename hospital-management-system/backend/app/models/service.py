from datetime import datetime
from .user import db

class Service(db.Model):
    __tablename__ = 'services'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    service_code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    
    # Pricing
    base_price = db.Column(db.Decimal(10, 2), nullable=False)
    insurance_price = db.Column(db.Decimal(10, 2))  # Different price for insurance patients
    
    # Service details
    duration_minutes = db.Column(db.Integer, default=30)
    category = db.Column(db.String(50))  # consultation, diagnostic, treatment, emergency
    subcategory = db.Column(db.String(50))
    
    # Department association
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    
    # Availability
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    requires_appointment = db.Column(db.Boolean, default=True, nullable=False)
    is_emergency_service = db.Column(db.Boolean, default=False, nullable=False)
    
    # Prerequisites
    requires_referral = db.Column(db.Boolean, default=False, nullable=False)
    preparation_instructions = db.Column(db.Text)
    
    # System fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    appointments = db.relationship('Appointment', backref='service', lazy='dynamic')
    
    def __init__(self, name, service_code, base_price, department_id, **kwargs):
        self.name = name
        self.service_code = service_code
        self.base_price = base_price
        self.department_id = department_id
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def get_price_for_patient(self, patient):
        """Get appropriate price based on patient's insurance status."""
        if patient.insurance_provider and self.insurance_price:
            return self.insurance_price
        return self.base_price
    
    @property
    def formatted_duration(self):
        """Return formatted duration string."""
        hours = self.duration_minutes // 60
        minutes = self.duration_minutes % 60
        if hours > 0:
            return f"{hours}h {minutes}m" if minutes > 0 else f"{hours}h"
        return f"{minutes}m"
    
    def to_dict(self, include_department=True):
        """Convert to dictionary."""
        result = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'service_code': self.service_code,
            'base_price': float(self.base_price),
            'insurance_price': float(self.insurance_price) if self.insurance_price else None,
            'duration_minutes': self.duration_minutes,
            'formatted_duration': self.formatted_duration,
            'category': self.category,
            'subcategory': self.subcategory,
            'department_id': self.department_id,
            'is_active': self.is_active,
            'requires_appointment': self.requires_appointment,
            'is_emergency_service': self.is_emergency_service,
            'requires_referral': self.requires_referral,
            'preparation_instructions': self.preparation_instructions,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
        if include_department and self.department:
            result['department'] = self.department.to_dict()
        
        return result
    
    def __repr__(self):
        return f'<Service {self.service_code} - {self.name}>'

class ServiceCategory(db.Model):
    __tablename__ = 'service_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.Text)
    icon = db.Column(db.String(50))  # For UI display
    color = db.Column(db.String(7))  # Hex color code
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'icon': self.icon,
            'color': self.color,
            'created_at': self.created_at.isoformat()
        }
    
    def __repr__(self):
        return f'<ServiceCategory {self.name}>'