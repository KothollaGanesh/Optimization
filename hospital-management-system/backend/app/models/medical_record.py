from datetime import datetime
from .user import db

class MedicalRecord(db.Model):
    __tablename__ = 'medical_records'
    
    id = db.Column(db.Integer, primary_key=True)
    record_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    
    # Core associations
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'))
    
    # Consultation details
    visit_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    chief_complaint = db.Column(db.Text)  # Patient's main concern
    history_of_present_illness = db.Column(db.Text)  # HPI
    past_medical_history = db.Column(db.Text)
    family_history = db.Column(db.Text)
    social_history = db.Column(db.Text)
    allergies = db.Column(db.Text)
    current_medications = db.Column(db.Text)
    
    # Physical examination
    vital_signs = db.Column(db.JSON)  # Store as JSON: {temperature, bp_systolic, bp_diastolic, pulse, resp_rate, weight, height}
    physical_examination = db.Column(db.Text)
    
    # Assessment and Plan
    diagnosis_primary = db.Column(db.Text)
    diagnosis_secondary = db.Column(db.Text)
    assessment = db.Column(db.Text)
    treatment_plan = db.Column(db.Text)
    
    # Follow-up
    follow_up_instructions = db.Column(db.Text)
    follow_up_date = db.Column(db.Date)
    
    # Status
    is_confidential = db.Column(db.Boolean, default=False, nullable=False)
    status = db.Column(db.Enum('draft', 'finalized', 'amended', name='record_status'), default='draft')
    
    # System fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    finalized_at = db.Column(db.DateTime)
    
    # Relationships
    prescriptions = db.relationship('Prescription', backref='medical_record', lazy='dynamic', cascade='all, delete-orphan')
    lab_orders = db.relationship('LabOrder', backref='medical_record', lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, record_number, patient_id, doctor_id, **kwargs):
        self.record_number = record_number
        self.patient_id = patient_id
        self.doctor_id = doctor_id
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def finalize_record(self):
        """Finalize the medical record."""
        if self.status == 'draft':
            self.status = 'finalized'
            self.finalized_at = datetime.utcnow()
            return True
        return False
    
    def can_be_edited(self, user):
        """Check if record can be edited by user."""
        # Only the creating doctor can edit draft records
        # Admins can edit any record
        if user.role.value == 'admin':
            return True
        if user.role.value == 'doctor' and self.doctor_id == user.doctor_profile.id:
            return self.status == 'draft'
        return False
    
    @property
    def bmi(self):
        """Calculate BMI from vital signs."""
        if self.vital_signs and 'weight' in self.vital_signs and 'height' in self.vital_signs:
            weight = float(self.vital_signs['weight'])  # in kg
            height = float(self.vital_signs['height']) / 100  # convert cm to m
            if height > 0:
                return round(weight / (height ** 2), 2)
        return None
    
    def to_dict(self, include_patient=True, include_doctor=True):
        """Convert to dictionary."""
        result = {
            'id': self.id,
            'record_number': self.record_number,
            'patient_id': self.patient_id,
            'doctor_id': self.doctor_id,
            'appointment_id': self.appointment_id,
            'visit_date': self.visit_date.isoformat(),
            'chief_complaint': self.chief_complaint,
            'history_of_present_illness': self.history_of_present_illness,
            'past_medical_history': self.past_medical_history,
            'family_history': self.family_history,
            'social_history': self.social_history,
            'allergies': self.allergies,
            'current_medications': self.current_medications,
            'vital_signs': self.vital_signs,
            'bmi': self.bmi,
            'physical_examination': self.physical_examination,
            'diagnosis_primary': self.diagnosis_primary,
            'diagnosis_secondary': self.diagnosis_secondary,
            'assessment': self.assessment,
            'treatment_plan': self.treatment_plan,
            'follow_up_instructions': self.follow_up_instructions,
            'follow_up_date': self.follow_up_date.isoformat() if self.follow_up_date else None,
            'is_confidential': self.is_confidential,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'finalized_at': self.finalized_at.isoformat() if self.finalized_at else None
        }
        
        if include_patient and self.patient:
            result['patient'] = self.patient.to_dict(include_user=True)
        
        if include_doctor and self.doctor:
            result['doctor'] = self.doctor.to_dict(include_user=True, include_department=True)
        
        return result
    
    def __repr__(self):
        return f'<MedicalRecord {self.record_number} - {self.patient.full_name if self.patient else "Unknown"}>'

class Prescription(db.Model):
    __tablename__ = 'prescriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    prescription_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    medical_record_id = db.Column(db.Integer, db.ForeignKey('medical_records.id'), nullable=False)
    
    # Medication details
    medication_name = db.Column(db.String(200), nullable=False)
    dosage = db.Column(db.String(100), nullable=False)  # e.g., "500mg"
    frequency = db.Column(db.String(100), nullable=False)  # e.g., "twice daily"
    duration = db.Column(db.String(100))  # e.g., "7 days"
    quantity = db.Column(db.String(50))  # e.g., "30 tablets"
    
    # Instructions
    instructions = db.Column(db.Text)
    special_instructions = db.Column(db.Text)
    
    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    filled_date = db.Column(db.DateTime)
    
    # System fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'prescription_number': self.prescription_number,
            'medical_record_id': self.medical_record_id,
            'medication_name': self.medication_name,
            'dosage': self.dosage,
            'frequency': self.frequency,
            'duration': self.duration,
            'quantity': self.quantity,
            'instructions': self.instructions,
            'special_instructions': self.special_instructions,
            'is_active': self.is_active,
            'filled_date': self.filled_date.isoformat() if self.filled_date else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def __repr__(self):
        return f'<Prescription {self.prescription_number} - {self.medication_name}>'

class LabOrder(db.Model):
    __tablename__ = 'lab_orders'
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    medical_record_id = db.Column(db.Integer, db.ForeignKey('medical_records.id'), nullable=False)
    
    # Test details
    test_name = db.Column(db.String(200), nullable=False)
    test_code = db.Column(db.String(50))
    urgency = db.Column(db.Enum('routine', 'urgent', 'stat', name='lab_urgency'), default='routine')
    
    # Instructions
    clinical_notes = db.Column(db.Text)
    special_instructions = db.Column(db.Text)
    
    # Status tracking
    status = db.Column(db.Enum('ordered', 'collected', 'processing', 'completed', 'cancelled', name='lab_status'), default='ordered')
    ordered_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    collection_date = db.Column(db.DateTime)
    result_date = db.Column(db.DateTime)
    
    # Results
    result = db.Column(db.Text)
    reference_range = db.Column(db.String(100))
    abnormal_flag = db.Column(db.Boolean, default=False)
    
    # System fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_number': self.order_number,
            'medical_record_id': self.medical_record_id,
            'test_name': self.test_name,
            'test_code': self.test_code,
            'urgency': self.urgency,
            'clinical_notes': self.clinical_notes,
            'special_instructions': self.special_instructions,
            'status': self.status,
            'ordered_date': self.ordered_date.isoformat(),
            'collection_date': self.collection_date.isoformat() if self.collection_date else None,
            'result_date': self.result_date.isoformat() if self.result_date else None,
            'result': self.result,
            'reference_range': self.reference_range,
            'abnormal_flag': self.abnormal_flag,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def __repr__(self):
        return f'<LabOrder {self.order_number} - {self.test_name}>'