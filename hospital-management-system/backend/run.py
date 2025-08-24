import os
from app import create_app
from app.models import db

# Create Flask application
app = create_app(os.environ.get('FLASK_ENV', 'development'))

@app.cli.command()
def init_db():
    """Initialize the database."""
    db.create_all()
    print("Database initialized!")

@app.cli.command()
def seed_db():
    """Seed the database with initial data."""
    from app.models import (
        User, UserRole, Department, Specialization, Service, Patient, Doctor
    )
    from app.utils import generate_patient_id, generate_doctor_id
    
    # Create departments
    departments_data = [
        {'name': 'Cardiology', 'description': 'Heart and cardiovascular care'},
        {'name': 'Neurology', 'description': 'Brain and nervous system care'},
        {'name': 'Orthopedics', 'description': 'Bone and joint care'},
        {'name': 'Pediatrics', 'description': 'Children healthcare'},
        {'name': 'Emergency', 'description': 'Emergency medical care'},
        {'name': 'General Medicine', 'description': 'General healthcare services'},
    ]
    
    departments = {}
    for dept_data in departments_data:
        dept = Department.query.filter_by(name=dept_data['name']).first()
        if not dept:
            dept = Department(**dept_data)
            db.session.add(dept)
            db.session.flush()
        departments[dept_data['name']] = dept
    
    # Create specializations
    specializations_data = [
        {'name': 'Interventional Cardiology', 'description': 'Heart procedures and interventions'},
        {'name': 'Pediatric Neurology', 'description': 'Pediatric brain and nervous system'},
        {'name': 'Sports Medicine', 'description': 'Sports-related injuries and care'},
        {'name': 'Emergency Medicine', 'description': 'Emergency and trauma care'},
        {'name': 'Family Medicine', 'description': 'Comprehensive family healthcare'},
        {'name': 'Internal Medicine', 'description': 'Adult internal medicine'},
    ]
    
    specializations = {}
    for spec_data in specializations_data:
        spec = Specialization.query.filter_by(name=spec_data['name']).first()
        if not spec:
            spec = Specialization(**spec_data)
            db.session.add(spec)
            db.session.flush()
        specializations[spec_data['name']] = spec
    
    # Create services
    services_data = [
        {
            'name': 'General Consultation', 'service_code': 'GEN001',
            'base_price': 150.00, 'insurance_price': 120.00,
            'department_id': departments['General Medicine'].id, 'category': 'consultation'
        },
        {
            'name': 'Cardiac Consultation', 'service_code': 'CAR001',
            'base_price': 250.00, 'insurance_price': 200.00,
            'department_id': departments['Cardiology'].id, 'category': 'consultation'
        },
        {
            'name': 'Emergency Consultation', 'service_code': 'EMR001',
            'base_price': 300.00, 'insurance_price': 250.00,
            'department_id': departments['Emergency'].id, 'category': 'emergency',
            'is_emergency_service': True, 'requires_appointment': False
        },
        {
            'name': 'Pediatric Checkup', 'service_code': 'PED001',
            'base_price': 180.00, 'insurance_price': 150.00,
            'department_id': departments['Pediatrics'].id, 'category': 'consultation'
        },
    ]
    
    for service_data in services_data:
        service = Service.query.filter_by(service_code=service_data['service_code']).first()
        if not service:
            service = Service(**service_data)
            db.session.add(service)
    
    # Create admin user
    admin_user = User.query.filter_by(email='admin@hospital.com').first()
    if not admin_user:
        admin_user = User(
            email='admin@hospital.com',
            password='Admin123!',
            role=UserRole.ADMIN,
            first_name='System',
            last_name='Administrator',
            phone='(555) 000-0001'
        )
        db.session.add(admin_user)
    
    # Create sample doctor
    doctor_user = User.query.filter_by(email='doctor@hospital.com').first()
    if not doctor_user:
        doctor_user = User(
            email='doctor@hospital.com',
            password='Doctor123!',
            role=UserRole.DOCTOR,
            first_name='John',
            last_name='Smith',
            phone='(555) 000-0002'
        )
        db.session.add(doctor_user)
        db.session.flush()
        
        doctor = Doctor(
            user_id=doctor_user.id,
            doctor_id=generate_doctor_id(),
            license_number='MD123456',
            department_id=departments['General Medicine'].id,
            qualification='MD, Internal Medicine',
            experience_years=10,
            consultation_fee=150.00,
            biography='Experienced general practitioner with 10 years of practice.'
        )
        db.session.add(doctor)
        db.session.flush()
        
        # Add specialization
        doctor.specializations.append(specializations['Internal Medicine'])
    
    # Create sample receptionist
    receptionist_user = User.query.filter_by(email='receptionist@hospital.com').first()
    if not receptionist_user:
        from app.models import Receptionist
        from app.utils import generate_employee_id
        from datetime import date
        
        receptionist_user = User(
            email='receptionist@hospital.com',
            password='Receptionist123!',
            role=UserRole.RECEPTIONIST,
            first_name='Jane',
            last_name='Doe',
            phone='(555) 000-0003'
        )
        db.session.add(receptionist_user)
        db.session.flush()
        
        receptionist = Receptionist(
            user_id=receptionist_user.id,
            employee_id=generate_employee_id(),
            department_id=departments['General Medicine'].id,
            hire_date=date.today()
        )
        db.session.add(receptionist)
    
    # Create sample patient
    patient_user = User.query.filter_by(email='patient@example.com').first()
    if not patient_user:
        patient_user = User(
            email='patient@example.com',
            password='Patient123!',
            role=UserRole.PATIENT,
            first_name='Alice',
            last_name='Johnson',
            phone='(555) 000-0004',
            gender='female'
        )
        db.session.add(patient_user)
        db.session.flush()
        
        patient = Patient(
            user_id=patient_user.id,
            patient_id=generate_patient_id(),
            blood_group='A+',
            emergency_contact_name='Bob Johnson',
            emergency_contact_phone='(555) 000-0005',
            emergency_contact_relation='Spouse'
        )
        db.session.add(patient)
    
    db.session.commit()
    print("Database seeded with initial data!")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)