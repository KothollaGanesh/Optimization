from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, ValidationError, validate
from decimal import Decimal
from app.models import (
    db, User, UserRole, Bill, BillItem, Payment, BillStatus, PaymentMethod,
    Patient, Service, Appointment
)
from app.utils import (
    staff_required, generate_bill_number, paginate_query
)

billing_bp = Blueprint('billing', __name__)

class CreateBillSchema(Schema):
    patient_id = fields.Int(required=True)
    appointment_id = fields.Int()
    due_date = fields.Date()
    notes = fields.Str()
    items = fields.List(fields.Dict(), required=True)  # List of bill items

class BillItemSchema(Schema):
    description = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    service_id = fields.Int()
    quantity = fields.Int(validate=validate.Range(min=1), missing=1)
    unit_price = fields.Decimal(required=True, validate=validate.Range(min=0))
    discount_percentage = fields.Decimal(validate=validate.Range(min=0, max=100), missing=0)

class CreatePaymentSchema(Schema):
    bill_id = fields.Int(required=True)
    amount = fields.Decimal(required=True, validate=validate.Range(min=0.01))
    payment_method = fields.Str(required=True, validate=validate.OneOf([m.value for m in PaymentMethod]))
    reference_number = fields.Str(validate=validate.Length(max=100))
    notes = fields.Str()

class UpdateBillSchema(Schema):
    due_date = fields.Date()
    notes = fields.Str()
    tax_amount = fields.Decimal(validate=validate.Range(min=0))
    discount_amount = fields.Decimal(validate=validate.Range(min=0))

@billing_bp.route('/bills', methods=['GET'])
@staff_required
def get_bills(current_user):
    """Get list of bills with pagination and filtering."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')
    patient_id = request.args.get('patient_id', type=int)
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    # Build query
    query = Bill.query
    
    # Apply filters
    if status:
        try:
            status_enum = BillStatus(status)
            query = query.filter(Bill.status == status_enum)
        except ValueError:
            return jsonify({'error': f'Invalid status: {status}'}), 400
    
    if patient_id:
        query = query.filter(Bill.patient_id == patient_id)
    
    if date_from:
        try:
            from datetime import datetime
            from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
            query = query.filter(Bill.bill_date >= from_date)
        except ValueError:
            return jsonify({'error': 'Invalid date_from format. Use YYYY-MM-DD'}), 400
    
    if date_to:
        try:
            from datetime import datetime
            to_date = datetime.strptime(date_to, '%Y-%m-%d').date()
            query = query.filter(Bill.bill_date <= to_date)
        except ValueError:
            return jsonify({'error': 'Invalid date_to format. Use YYYY-MM-DD'}), 400
    
    # Order by bill date
    query = query.order_by(Bill.bill_date.desc())
    
    # Paginate
    result = paginate_query(query, page, per_page)
    result['items'] = [bill.to_dict() for bill in result['items']]
    
    return jsonify(result), 200

@billing_bp.route('/bills', methods=['POST'])
@staff_required
def create_bill(current_user):
    """Create a new bill."""
    schema = CreateBillSchema()
    
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'details': err.messages}), 400
    
    # Verify patient exists
    patient = Patient.query.get(data['patient_id'])
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    
    # Verify appointment if provided
    if data.get('appointment_id'):
        appointment = Appointment.query.get(data['appointment_id'])
        if not appointment:
            return jsonify({'error': 'Appointment not found'}), 404
    
    # Validate bill items
    item_schema = BillItemSchema()
    validated_items = []
    
    for item_data in data['items']:
        try:
            validated_item = item_schema.load(item_data)
            validated_items.append(validated_item)
        except ValidationError as err:
            return jsonify({'error': 'Item validation failed', 'details': err.messages}), 400
    
    if not validated_items:
        return jsonify({'error': 'At least one bill item is required'}), 400
    
    try:
        # Create bill
        bill = Bill(
            bill_number=generate_bill_number(),
            patient_id=data['patient_id'],
            appointment_id=data.get('appointment_id'),
            due_date=data.get('due_date'),
            notes=data.get('notes'),
            created_by_user_id=current_user.id
        )
        
        db.session.add(bill)
        db.session.flush()  # Get bill ID
        
        # Create bill items
        for item_data in validated_items:
            bill_item = BillItem(
                bill_id=bill.id,
                description=item_data['description'],
                service_id=item_data.get('service_id'),
                quantity=item_data['quantity'],
                unit_price=item_data['unit_price'],
                discount_percentage=item_data['discount_percentage']
            )
            bill_item.calculate_total()
            db.session.add(bill_item)
        
        # Calculate bill totals
        bill.calculate_totals()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Bill created successfully',
            'bill': bill.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create bill', 'details': str(e)}), 500

@billing_bp.route('/bills/<int:bill_id>', methods=['GET'])
@jwt_required()
def get_bill(bill_id):
    """Get specific bill by ID."""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    bill = Bill.query.get_or_404(bill_id)
    
    # Check permissions
    if current_user.role == UserRole.PATIENT:
        patient = Patient.query.filter_by(user_id=current_user_id).first()
        if not patient or bill.patient_id != patient.id:
            return jsonify({'error': 'Access denied'}), 403
    elif current_user.role not in [UserRole.ADMIN, UserRole.RECEPTIONIST, UserRole.DOCTOR]:
        return jsonify({'error': 'Access denied'}), 403
    
    return jsonify({'bill': bill.to_dict()}), 200

@billing_bp.route('/bills/<int:bill_id>', methods=['PUT'])
@staff_required
def update_bill(current_user, bill_id):
    """Update bill."""
    bill = Bill.query.get_or_404(bill_id)
    
    if bill.status == BillStatus.PAID:
        return jsonify({'error': 'Cannot update paid bill'}), 400
    
    schema = UpdateBillSchema()
    
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'details': err.messages}), 400
    
    # Update fields
    for field, value in data.items():
        if hasattr(bill, field):
            setattr(bill, field, value)
    
    # Recalculate totals
    bill.calculate_totals()
    
    db.session.commit()
    
    return jsonify({
        'message': 'Bill updated successfully',
        'bill': bill.to_dict()
    }), 200

@billing_bp.route('/bills/<int:bill_id>/cancel', methods=['POST'])
@staff_required
def cancel_bill(current_user, bill_id):
    """Cancel bill."""
    bill = Bill.query.get_or_404(bill_id)
    
    if bill.status == BillStatus.PAID:
        return jsonify({'error': 'Cannot cancel paid bill'}), 400
    
    if bill.paid_amount > 0:
        return jsonify({'error': 'Cannot cancel bill with payments. Process refund instead.'}), 400
    
    bill.status = BillStatus.CANCELLED
    db.session.commit()
    
    return jsonify({
        'message': 'Bill cancelled successfully',
        'bill': bill.to_dict()
    }), 200

# Payment endpoints
@billing_bp.route('/payments', methods=['GET'])
@staff_required
def get_payments(current_user):
    """Get list of payments with pagination and filtering."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    bill_id = request.args.get('bill_id', type=int)
    payment_method = request.args.get('payment_method')
    
    # Build query
    query = Payment.query
    
    # Apply filters
    if bill_id:
        query = query.filter(Payment.bill_id == bill_id)
    
    if payment_method:
        try:
            method_enum = PaymentMethod(payment_method)
            query = query.filter(Payment.payment_method == method_enum)
        except ValueError:
            return jsonify({'error': f'Invalid payment method: {payment_method}'}), 400
    
    # Order by payment date
    query = query.order_by(Payment.payment_date.desc())
    
    # Paginate
    result = paginate_query(query, page, per_page)
    result['items'] = [payment.to_dict() for payment in result['items']]
    
    return jsonify(result), 200

@billing_bp.route('/payments', methods=['POST'])
@staff_required
def create_payment(current_user):
    """Process a payment for a bill."""
    schema = CreatePaymentSchema()
    
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'details': err.messages}), 400
    
    # Verify bill exists
    bill = Bill.query.get(data['bill_id'])
    if not bill:
        return jsonify({'error': 'Bill not found'}), 404
    
    if bill.status == BillStatus.CANCELLED:
        return jsonify({'error': 'Cannot process payment for cancelled bill'}), 400
    
    # Check if payment amount is valid
    outstanding = bill.outstanding_amount
    if data['amount'] > outstanding:
        return jsonify({'error': f'Payment amount exceeds outstanding balance of ${outstanding}'}), 400
    
    try:
        # Create payment
        payment = Payment(
            bill_id=data['bill_id'],
            amount=data['amount'],
            payment_method=PaymentMethod(data['payment_method']),
            reference_number=data.get('reference_number'),
            notes=data.get('notes'),
            created_by_user_id=current_user.id
        )
        
        db.session.add(payment)
        
        # Update bill
        bill.paid_amount += data['amount']
        bill.calculate_totals()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Payment processed successfully',
            'payment': payment.to_dict(),
            'bill': bill.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to process payment', 'details': str(e)}), 500

@billing_bp.route('/payments/<int:payment_id>', methods=['GET'])
@staff_required
def get_payment(current_user, payment_id):
    """Get specific payment by ID."""
    payment = Payment.query.get_or_404(payment_id)
    return jsonify({'payment': payment.to_dict()}), 200

# Patient billing endpoints
@billing_bp.route('/my-bills', methods=['GET'])
@jwt_required()
def get_my_bills():
    """Get current patient's bills."""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    if current_user.role != UserRole.PATIENT:
        return jsonify({'error': 'Access denied'}), 403
    
    patient = Patient.query.filter_by(user_id=current_user_id).first()
    if not patient:
        return jsonify({'error': 'Patient profile not found'}), 404
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')
    
    # Build query for patient's bills
    query = Bill.query.filter_by(patient_id=patient.id)
    
    if status:
        try:
            status_enum = BillStatus(status)
            query = query.filter(Bill.status == status_enum)
        except ValueError:
            return jsonify({'error': f'Invalid status: {status}'}), 400
    
    # Order by bill date
    query = query.order_by(Bill.bill_date.desc())
    
    # Paginate
    result = paginate_query(query, page, per_page)
    result['items'] = [bill.to_dict() for bill in result['items']]
    
    return jsonify(result), 200

# Service pricing endpoints
@billing_bp.route('/services', methods=['GET'])
@jwt_required()
def get_services():
    """Get list of services with pricing."""
    services = Service.query.filter_by(is_active=True).all()
    return jsonify({
        'services': [service.to_dict() for service in services]
    }), 200

@billing_bp.route('/services/<int:service_id>/price', methods=['GET'])
@jwt_required()
def get_service_price(service_id):
    """Get service price for a specific patient."""
    patient_id = request.args.get('patient_id', type=int)
    
    service = Service.query.get_or_404(service_id)
    
    if patient_id:
        patient = Patient.query.get_or_404(patient_id)
        price = service.get_price_for_patient(patient)
    else:
        price = service.base_price
    
    return jsonify({
        'service': service.to_dict(),
        'price': float(price)
    }), 200

# Financial reports
@billing_bp.route('/reports/revenue', methods=['GET'])
@staff_required
def get_revenue_report(current_user):
    """Get revenue report."""
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    query = db.session.query(db.func.sum(Payment.amount)).filter(
        Payment.status == 'completed'
    )
    
    if date_from:
        try:
            from datetime import datetime
            from_date = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(Payment.payment_date >= from_date)
        except ValueError:
            return jsonify({'error': 'Invalid date_from format. Use YYYY-MM-DD'}), 400
    
    if date_to:
        try:
            from datetime import datetime
            to_date = datetime.strptime(date_to, '%Y-%m-%d')
            query = query.filter(Payment.payment_date <= to_date)
        except ValueError:
            return jsonify({'error': 'Invalid date_to format. Use YYYY-MM-DD'}), 400
    
    total_revenue = query.scalar() or 0
    
    # Get outstanding amounts
    outstanding_query = db.session.query(db.func.sum(Bill.total_amount - Bill.paid_amount)).filter(
        Bill.status.in_([BillStatus.PENDING, BillStatus.PARTIAL, BillStatus.OVERDUE])
    )
    
    total_outstanding = outstanding_query.scalar() or 0
    
    return jsonify({
        'total_revenue': float(total_revenue),
        'total_outstanding': float(total_outstanding),
        'date_from': date_from,
        'date_to': date_to
    }), 200