from .auth import auth_bp
from .users import users_bp
from .patients import patients_bp
from .doctors import doctors_bp
from .appointments import appointments_bp
from .medical_records import medical_records_bp
from .billing import billing_bp
from .admin import admin_bp

__all__ = [
    'auth_bp', 'users_bp', 'patients_bp', 'doctors_bp',
    'appointments_bp', 'medical_records_bp', 'billing_bp', 'admin_bp'
]