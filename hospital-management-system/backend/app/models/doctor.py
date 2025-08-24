from datetime import datetime, time
from .user import db

class Department(db.Model):
    __tablename__ = 'departments'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    head_doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'))
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    doctors = db.relationship('Doctor', backref='department', lazy='dynamic')
    services = db.relationship('Service', backref='department', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'head_doctor_id': self.head_doctor_id,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def __repr__(self):
        return f'<Department {self.name}>'

class Specialization(db.Model):
    __tablename__ = 'specializations'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat()
        }
    
    def __repr__(self):
        return f'<Specialization {self.name}>'

# Association table for many-to-many relationship between doctors and specializations
doctor_specializations = db.Table('doctor_specializations',
    db.Column('doctor_id', db.Integer, db.ForeignKey('doctors.id'), primary_key=True),
    db.Column('specialization_id', db.Integer, db.ForeignKey('specializations.id'), primary_key=True)
)

class Doctor(db.Model):
    __tablename__ = 'doctors'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    doctor_id = db.Column(db.String(20), unique=True, nullable=False, index=True)  # Hospital doctor ID
    license_number = db.Column(db.String(50), unique=True, nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    
    # Professional Information
    qualification = db.Column(db.String(200))
    experience_years = db.Column(db.Integer)
    consultation_fee = db.Column(db.Decimal(10, 2))
    biography = db.Column(db.Text)
    
    # Schedule Information
    is_available = db.Column(db.Boolean, default=True, nullable=False)
    consultation_duration = db.Column(db.Integer, default=30)  # in minutes
    
    # System fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    specializations = db.relationship('Specialization', secondary=doctor_specializations, lazy='subquery',
                                    backref=db.backref('doctors', lazy=True))
    schedules = db.relationship('DoctorSchedule', backref='doctor', lazy='dynamic', cascade='all, delete-orphan')
    appointments = db.relationship('Appointment', backref='doctor', lazy='dynamic')
    medical_records = db.relationship('MedicalRecord', backref='doctor', lazy='dynamic')
    
    # Back reference for department head
    headed_department = db.relationship('Department', backref='head_doctor', foreign_keys=[Department.head_doctor_id])
    
    def __init__(self, user_id, doctor_id, license_number, department_id, **kwargs):
        self.user_id = user_id
        self.doctor_id = doctor_id
        self.license_number = license_number
        self.department_id = department_id
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    @property
    def full_name(self):
        return f"Dr. {self.user.full_name}" if self.user else None
    
    def get_availability_for_date(self, date):
        """Get doctor's availability for a specific date."""
        schedule = self.schedules.filter_by(date=date).first()
        if schedule:
            return schedule.to_dict()
        
        # Return default weekly schedule if no specific date schedule exists
        weekday = date.weekday()  # 0 = Monday, 6 = Sunday
        weekly_schedule = self.schedules.filter_by(day_of_week=weekday, is_recurring=True).first()
        return weekly_schedule.to_dict() if weekly_schedule else None
    
    def to_dict(self, include_user=True, include_department=True):
        """Convert to dictionary."""
        result = {
            'id': self.id,
            'doctor_id': self.doctor_id,
            'license_number': self.license_number,
            'department_id': self.department_id,
            'qualification': self.qualification,
            'experience_years': self.experience_years,
            'consultation_fee': float(self.consultation_fee) if self.consultation_fee else None,
            'biography': self.biography,
            'is_available': self.is_available,
            'consultation_duration': self.consultation_duration,
            'specializations': [spec.to_dict() for spec in self.specializations],
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
        return f'<Doctor {self.doctor_id} - {self.full_name}>'

class DoctorSchedule(db.Model):
    __tablename__ = 'doctor_schedules'
    
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    
    # Schedule can be for specific date or recurring weekly
    date = db.Column(db.Date)  # Specific date (null for recurring)
    day_of_week = db.Column(db.Integer)  # 0-6 for Monday-Sunday (null for specific date)
    is_recurring = db.Column(db.Boolean, default=False, nullable=False)
    
    # Time slots
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    
    # Availability
    is_available = db.Column(db.Boolean, default=True, nullable=False)
    max_appointments = db.Column(db.Integer, default=10)
    
    # Break times
    break_start_time = db.Column(db.Time)
    break_end_time = db.Column(db.Time)
    
    # System fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'doctor_id': self.doctor_id,
            'date': self.date.isoformat() if self.date else None,
            'day_of_week': self.day_of_week,
            'is_recurring': self.is_recurring,
            'start_time': self.start_time.strftime('%H:%M') if self.start_time else None,
            'end_time': self.end_time.strftime('%H:%M') if self.end_time else None,
            'is_available': self.is_available,
            'max_appointments': self.max_appointments,
            'break_start_time': self.break_start_time.strftime('%H:%M') if self.break_start_time else None,
            'break_end_time': self.break_end_time.strftime('%H:%M') if self.break_end_time else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def __repr__(self):
        return f'<DoctorSchedule {self.doctor_id} - {self.date or f"Day {self.day_of_week}"}>'