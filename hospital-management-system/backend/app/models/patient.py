from datetime import datetime
from .user import db

class Patient(db.Model):
    __tablename__ = 'patients'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    patient_id = db.Column(db.String(20), unique=True, nullable=False, index=True)  # Hospital patient ID
    
    # Medical Information
    blood_group = db.Column(db.String(5))
    allergies = db.Column(db.Text)
    chronic_conditions = db.Column(db.Text)
    emergency_contact_name = db.Column(db.String(100))
    emergency_contact_phone = db.Column(db.String(20))
    emergency_contact_relation = db.Column(db.String(50))
    
    # Insurance Information
    insurance_provider = db.Column(db.String(100))
    insurance_policy_number = db.Column(db.String(50))
    insurance_group_number = db.Column(db.String(50))
    insurance_expiry_date = db.Column(db.Date)
    
    # Family Information
    primary_patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'))  # For family members
    
    # System fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    family_members = db.relationship('Patient', backref=db.backref('primary_patient', remote_side=[id]))
    appointments = db.relationship('Appointment', backref='patient', lazy='dynamic', cascade='all, delete-orphan')
    medical_records = db.relationship('MedicalRecord', backref='patient', lazy='dynamic', cascade='all, delete-orphan')
    bills = db.relationship('Bill', backref='patient', lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, user_id, patient_id, **kwargs):
        self.user_id = user_id
        self.patient_id = patient_id
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    @property
    def full_name(self):
        return self.user.full_name if self.user else None
    
    @property
    def age(self):
        if self.user and self.user.date_of_birth:
            today = datetime.now().date()
            return today.year - self.user.date_of_birth.year - ((today.month, today.day) < (self.user.date_of_birth.month, self.user.date_of_birth.day))
        return None
    
    def is_family_member(self):
        """Check if this patient is a family member of another patient."""
        return self.primary_patient_id is not None
    
    def get_family_members(self):
        """Get all family members for this patient."""
        if self.is_family_member():
            # If this is a family member, get siblings and return primary patient's family
            return self.primary_patient.family_members
        else:
            # If this is a primary patient, return direct family members
            return self.family_members
    
    def to_dict(self, include_user=True):
        """Convert to dictionary."""
        result = {
            'id': self.id,
            'patient_id': self.patient_id,
            'blood_group': self.blood_group,
            'allergies': self.allergies,
            'chronic_conditions': self.chronic_conditions,
            'emergency_contact_name': self.emergency_contact_name,
            'emergency_contact_phone': self.emergency_contact_phone,
            'emergency_contact_relation': self.emergency_contact_relation,
            'insurance_provider': self.insurance_provider,
            'insurance_policy_number': self.insurance_policy_number,
            'insurance_group_number': self.insurance_group_number,
            'insurance_expiry_date': self.insurance_expiry_date.isoformat() if self.insurance_expiry_date else None,
            'primary_patient_id': self.primary_patient_id,
            'is_family_member': self.is_family_member(),
            'age': self.age,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
        if include_user and self.user:
            result['user'] = self.user.to_dict()
            result['full_name'] = self.full_name
        
        return result
    
    def __repr__(self):
        return f'<Patient {self.patient_id} - {self.full_name}>'