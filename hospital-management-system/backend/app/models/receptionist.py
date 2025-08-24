from datetime import datetime
from .user import db

class Receptionist(db.Model):
    __tablename__ = 'receptionists'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    employee_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    
    # Work information
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    shift = db.Column(db.Enum('morning', 'afternoon', 'night', 'rotating', name='shift_enum'), default='morning')
    hire_date = db.Column(db.Date, nullable=False)
    
    # Contact and emergency information
    emergency_contact_name = db.Column(db.String(100))
    emergency_contact_phone = db.Column(db.String(20))
    emergency_contact_relation = db.Column(db.String(50))
    
    # Permissions and access
    can_manage_appointments = db.Column(db.Boolean, default=True, nullable=False)
    can_process_payments = db.Column(db.Boolean, default=True, nullable=False)
    can_access_medical_records = db.Column(db.Boolean, default=False, nullable=False)
    can_manage_patient_registration = db.Column(db.Boolean, default=True, nullable=False)
    
    # System fields
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    department = db.relationship('Department', backref='receptionists')
    
    def __init__(self, user_id, employee_id, hire_date, **kwargs):
        self.user_id = user_id
        self.employee_id = employee_id
        self.hire_date = hire_date
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    @property
    def full_name(self):
        return self.user.full_name if self.user else None
    
    @property
    def years_of_service(self):
        """Calculate years of service."""
        if self.hire_date:
            today = datetime.now().date()
            return today.year - self.hire_date.year - ((today.month, today.day) < (self.hire_date.month, self.hire_date.day))
        return 0
    
    def can_perform_action(self, action):
        """Check if receptionist can perform specific action."""
        permissions = {
            'manage_appointments': self.can_manage_appointments,
            'process_payments': self.can_process_payments,
            'access_medical_records': self.can_access_medical_records,
            'manage_patient_registration': self.can_manage_patient_registration
        }
        return permissions.get(action, False)
    
    def to_dict(self, include_user=True, include_department=True):
        """Convert to dictionary."""
        result = {
            'id': self.id,
            'employee_id': self.employee_id,
            'department_id': self.department_id,
            'shift': self.shift,
            'hire_date': self.hire_date.isoformat(),
            'years_of_service': self.years_of_service,
            'emergency_contact_name': self.emergency_contact_name,
            'emergency_contact_phone': self.emergency_contact_phone,
            'emergency_contact_relation': self.emergency_contact_relation,
            'can_manage_appointments': self.can_manage_appointments,
            'can_process_payments': self.can_process_payments,
            'can_access_medical_records': self.can_access_medical_records,
            'can_manage_patient_registration': self.can_manage_patient_registration,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
        if include_user and self.user:
            result['user'] = self.user.to_dict()
            result['full_name'] = self.full_name
        
        if include_department and self.department:
            result['department'] = self.department.to_dict()
        
        return result
    
    def __repr__(self):
        return f'<Receptionist {self.employee_id} - {self.full_name}>'