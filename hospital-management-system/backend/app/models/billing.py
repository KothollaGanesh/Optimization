from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from .user import db

class BillStatus(Enum):
    DRAFT = "draft"
    PENDING = "pending"
    PAID = "paid"
    PARTIAL = "partial"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class PaymentMethod(Enum):
    CASH = "cash"
    CARD = "card"
    INSURANCE = "insurance"
    BANK_TRANSFER = "bank_transfer"
    CHEQUE = "cheque"
    ONLINE = "online"

class Bill(db.Model):
    __tablename__ = 'bills'
    
    id = db.Column(db.Integer, primary_key=True)
    bill_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    
    # Core associations
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'))
    
    # Bill details
    bill_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    due_date = db.Column(db.Date, nullable=False)
    
    # Amounts
    subtotal = db.Column(db.Decimal(10, 2), nullable=False, default=0.00)
    tax_amount = db.Column(db.Decimal(10, 2), default=0.00)
    discount_amount = db.Column(db.Decimal(10, 2), default=0.00)
    total_amount = db.Column(db.Decimal(10, 2), nullable=False)
    paid_amount = db.Column(db.Decimal(10, 2), default=0.00)
    
    # Status and notes
    status = db.Column(db.Enum(BillStatus), default=BillStatus.PENDING)
    notes = db.Column(db.Text)
    
    # Insurance information
    insurance_claim_number = db.Column(db.String(50))
    insurance_approved_amount = db.Column(db.Decimal(10, 2))
    
    # System fields
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    bill_items = db.relationship('BillItem', backref='bill', lazy='dynamic', cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='bill', lazy='dynamic', cascade='all, delete-orphan')
    created_by = db.relationship('User', backref='created_bills')
    
    def __init__(self, bill_number, patient_id, **kwargs):
        self.bill_number = bill_number
        self.patient_id = patient_id
        self.due_date = kwargs.get('due_date', datetime.utcnow().date() + timedelta(days=30))
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    @property
    def outstanding_amount(self):
        """Calculate outstanding amount."""
        return self.total_amount - self.paid_amount
    
    @property
    def is_overdue(self):
        """Check if bill is overdue."""
        return self.due_date < datetime.utcnow().date() and self.outstanding_amount > 0
    
    def calculate_totals(self):
        """Calculate all totals based on bill items."""
        self.subtotal = sum(item.total_amount for item in self.bill_items)
        self.total_amount = self.subtotal + self.tax_amount - self.discount_amount
        
        # Update status based on payment
        if self.paid_amount >= self.total_amount:
            self.status = BillStatus.PAID
        elif self.paid_amount > 0:
            self.status = BillStatus.PARTIAL
        elif self.is_overdue:
            self.status = BillStatus.OVERDUE
        else:
            self.status = BillStatus.PENDING
    
    def add_payment(self, amount, payment_method, reference_number=None, notes=None):
        """Add a payment to this bill."""
        payment = Payment(
            bill_id=self.id,
            amount=amount,
            payment_method=payment_method,
            reference_number=reference_number,
            notes=notes
        )
        
        self.paid_amount += amount
        self.calculate_totals()
        
        return payment
    
    def to_dict(self, include_items=True, include_payments=True, include_patient=True):
        """Convert to dictionary."""
        result = {
            'id': self.id,
            'bill_number': self.bill_number,
            'patient_id': self.patient_id,
            'appointment_id': self.appointment_id,
            'bill_date': self.bill_date.isoformat(),
            'due_date': self.due_date.isoformat(),
            'subtotal': float(self.subtotal),
            'tax_amount': float(self.tax_amount),
            'discount_amount': float(self.discount_amount),
            'total_amount': float(self.total_amount),
            'paid_amount': float(self.paid_amount),
            'outstanding_amount': float(self.outstanding_amount),
            'status': self.status.value,
            'is_overdue': self.is_overdue,
            'notes': self.notes,
            'insurance_claim_number': self.insurance_claim_number,
            'insurance_approved_amount': float(self.insurance_approved_amount) if self.insurance_approved_amount else None,
            'created_by_user_id': self.created_by_user_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
        if include_items:
            result['items'] = [item.to_dict() for item in self.bill_items]
        
        if include_payments:
            result['payments'] = [payment.to_dict() for payment in self.payments]
        
        if include_patient and self.patient:
            result['patient'] = self.patient.to_dict(include_user=True)
        
        return result
    
    def __repr__(self):
        return f'<Bill {self.bill_number} - {self.patient.full_name if self.patient else "Unknown"}>'

class BillItem(db.Model):
    __tablename__ = 'bill_items'
    
    id = db.Column(db.Integer, primary_key=True)
    bill_id = db.Column(db.Integer, db.ForeignKey('bills.id'), nullable=False)
    
    # Item details
    description = db.Column(db.String(200), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'))
    
    # Pricing
    quantity = db.Column(db.Integer, default=1, nullable=False)
    unit_price = db.Column(db.Decimal(10, 2), nullable=False)
    total_amount = db.Column(db.Decimal(10, 2), nullable=False)
    
    # Discounts
    discount_percentage = db.Column(db.Decimal(5, 2), default=0.00)
    discount_amount = db.Column(db.Decimal(10, 2), default=0.00)
    
    # System fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    service = db.relationship('Service', backref='bill_items')
    
    def __init__(self, bill_id, description, unit_price, quantity=1, **kwargs):
        self.bill_id = bill_id
        self.description = description
        self.unit_price = unit_price
        self.quantity = quantity
        self.calculate_total()
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def calculate_total(self):
        """Calculate total amount after discounts."""
        gross_amount = self.unit_price * self.quantity
        if self.discount_percentage > 0:
            self.discount_amount = gross_amount * (self.discount_percentage / 100)
        self.total_amount = gross_amount - self.discount_amount
    
    def to_dict(self):
        return {
            'id': self.id,
            'bill_id': self.bill_id,
            'description': self.description,
            'service_id': self.service_id,
            'quantity': self.quantity,
            'unit_price': float(self.unit_price),
            'discount_percentage': float(self.discount_percentage),
            'discount_amount': float(self.discount_amount),
            'total_amount': float(self.total_amount),
            'created_at': self.created_at.isoformat()
        }
    
    def __repr__(self):
        return f'<BillItem {self.description} - ${self.total_amount}>'

class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    payment_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    bill_id = db.Column(db.Integer, db.ForeignKey('bills.id'), nullable=False)
    
    # Payment details
    amount = db.Column(db.Decimal(10, 2), nullable=False)
    payment_method = db.Column(db.Enum(PaymentMethod), nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Transaction details
    reference_number = db.Column(db.String(100))  # Check number, transaction ID, etc.
    notes = db.Column(db.Text)
    
    # Status
    status = db.Column(db.Enum('pending', 'completed', 'failed', 'refunded', name='payment_status'), default='completed')
    
    # System fields
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    created_by = db.relationship('User', backref='processed_payments')
    
    def __init__(self, bill_id, amount, payment_method, **kwargs):
        self.bill_id = bill_id
        self.amount = amount
        self.payment_method = payment_method
        self.payment_number = self.generate_payment_number()
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def generate_payment_number(self):
        """Generate unique payment number."""
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"PAY{timestamp}"
    
    def to_dict(self):
        return {
            'id': self.id,
            'payment_number': self.payment_number,
            'bill_id': self.bill_id,
            'amount': float(self.amount),
            'payment_method': self.payment_method.value,
            'payment_date': self.payment_date.isoformat(),
            'reference_number': self.reference_number,
            'notes': self.notes,
            'status': self.status,
            'created_by_user_id': self.created_by_user_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def __repr__(self):
        return f'<Payment {self.payment_number} - ${self.amount}>'