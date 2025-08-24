from datetime import datetime
from enum import Enum
from .user import db

class AppointmentStatus(Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    RESCHEDULED = "rescheduled"

class AppointmentType(Enum):
    CONSULTATION = "consultation"
    FOLLOW_UP = "follow_up"
    EMERGENCY = "emergency"
    ROUTINE_CHECKUP = "routine_checkup"
    SPECIALIST = "specialist"

class Appointment(db.Model):
    __tablename__ = 'appointments'
    
    id = db.Column(db.Integer, primary_key=True)
    appointment_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    
    # Core appointment details
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'))
    
    # Schedule information
    appointment_date = db.Column(db.Date, nullable=False)
    appointment_time = db.Column(db.Time, nullable=False)
    duration_minutes = db.Column(db.Integer, default=30)
    
    # Appointment details
    appointment_type = db.Column(db.Enum(AppointmentType), default=AppointmentType.CONSULTATION)
    status = db.Column(db.Enum(AppointmentStatus), default=AppointmentStatus.SCHEDULED)
    priority = db.Column(db.Enum('low', 'normal', 'high', 'emergency', name='priority_enum'), default='normal')
    
    # Patient information
    chief_complaint = db.Column(db.Text)  # Why patient is visiting
    notes = db.Column(db.Text)  # Additional notes
    
    # System tracking
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # Who created the appointment
    checked_in_at = db.Column(db.DateTime)
    checked_out_at = db.Column(db.DateTime)
    
    # Follow-up information
    follow_up_appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'))
    parent_appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'))
    
    # Cancellation/Rescheduling
    cancellation_reason = db.Column(db.Text)
    cancelled_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    cancelled_at = db.Column(db.DateTime)
    
    # System fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    created_by = db.relationship('User', foreign_keys=[created_by_user_id], backref='created_appointments')
    cancelled_by = db.relationship('User', foreign_keys=[cancelled_by_user_id], backref='cancelled_appointments')
    follow_up_appointment = db.relationship('Appointment', remote_side=[id], backref='original_appointment', foreign_keys=[follow_up_appointment_id])
    parent_appointment = db.relationship('Appointment', remote_side=[id], backref='child_appointments', foreign_keys=[parent_appointment_id])
    medical_record = db.relationship('MedicalRecord', backref='appointment', uselist=False)
    
    def __init__(self, appointment_number, patient_id, doctor_id, appointment_date, appointment_time, **kwargs):
        self.appointment_number = appointment_number
        self.patient_id = patient_id
        self.doctor_id = doctor_id
        self.appointment_date = appointment_date
        self.appointment_time = appointment_time
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    @property
    def appointment_datetime(self):
        """Combine date and time into datetime object."""
        return datetime.combine(self.appointment_date, self.appointment_time)
    
    def can_be_cancelled(self):
        """Check if appointment can be cancelled."""
        return self.status in [AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED]
    
    def can_be_rescheduled(self):
        """Check if appointment can be rescheduled."""
        return self.status in [AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED]
    
    def check_in(self):
        """Mark appointment as checked in."""
        if self.status == AppointmentStatus.CONFIRMED:
            self.status = AppointmentStatus.IN_PROGRESS
            self.checked_in_at = datetime.utcnow()
            return True
        return False
    
    def check_out(self):
        """Mark appointment as checked out."""
        if self.status == AppointmentStatus.IN_PROGRESS:
            self.status = AppointmentStatus.COMPLETED
            self.checked_out_at = datetime.utcnow()
            return True
        return False
    
    def cancel(self, reason, cancelled_by_user_id):
        """Cancel the appointment."""
        if self.can_be_cancelled():
            self.status = AppointmentStatus.CANCELLED
            self.cancellation_reason = reason
            self.cancelled_by_user_id = cancelled_by_user_id
            self.cancelled_at = datetime.utcnow()
            return True
        return False
    
    def reschedule(self, new_date, new_time, reason=None):
        """Reschedule the appointment."""
        if self.can_be_rescheduled():
            self.appointment_date = new_date
            self.appointment_time = new_time
            self.status = AppointmentStatus.RESCHEDULED
            if reason:
                self.notes = f"{self.notes or ''}\nRescheduled: {reason}".strip()
            return True
        return False
    
    def to_dict(self, include_patient=True, include_doctor=True, include_service=True):
        """Convert to dictionary."""
        result = {
            'id': self.id,
            'appointment_number': self.appointment_number,
            'patient_id': self.patient_id,
            'doctor_id': self.doctor_id,
            'service_id': self.service_id,
            'appointment_date': self.appointment_date.isoformat(),
            'appointment_time': self.appointment_time.strftime('%H:%M'),
            'appointment_datetime': self.appointment_datetime.isoformat(),
            'duration_minutes': self.duration_minutes,
            'appointment_type': self.appointment_type.value,
            'status': self.status.value,
            'priority': self.priority,
            'chief_complaint': self.chief_complaint,
            'notes': self.notes,
            'created_by_user_id': self.created_by_user_id,
            'checked_in_at': self.checked_in_at.isoformat() if self.checked_in_at else None,
            'checked_out_at': self.checked_out_at.isoformat() if self.checked_out_at else None,
            'follow_up_appointment_id': self.follow_up_appointment_id,
            'parent_appointment_id': self.parent_appointment_id,
            'cancellation_reason': self.cancellation_reason,
            'cancelled_by_user_id': self.cancelled_by_user_id,
            'cancelled_at': self.cancelled_at.isoformat() if self.cancelled_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
        if include_patient and self.patient:
            result['patient'] = self.patient.to_dict(include_user=True)
        
        if include_doctor and self.doctor:
            result['doctor'] = self.doctor.to_dict(include_user=True, include_department=True)
        
        if include_service and self.service:
            result['service'] = self.service.to_dict()
        
        return result
    
    def __repr__(self):
        return f'<Appointment {self.appointment_number} - {self.patient.full_name} with {self.doctor.full_name}>'