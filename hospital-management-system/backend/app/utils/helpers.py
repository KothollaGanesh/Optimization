import random
import string
from datetime import datetime, date
import re

def generate_unique_id(prefix, length=8):
    """Generate a unique ID with prefix."""
    timestamp = datetime.now().strftime('%Y%m%d')
    random_part = ''.join(random.choices(string.digits, k=length-8))
    return f"{prefix}{timestamp}{random_part}"

def generate_patient_id():
    """Generate unique patient ID."""
    return generate_unique_id('P', 12)

def generate_doctor_id():
    """Generate unique doctor ID."""
    return generate_unique_id('D', 10)

def generate_employee_id():
    """Generate unique employee ID."""
    return generate_unique_id('E', 10)

def generate_appointment_number():
    """Generate unique appointment number."""
    return generate_unique_id('APT', 15)

def generate_record_number():
    """Generate unique medical record number."""
    return generate_unique_id('MR', 15)

def generate_bill_number():
    """Generate unique bill number."""
    return generate_unique_id('BILL', 15)

def generate_prescription_number():
    """Generate unique prescription number."""
    return generate_unique_id('RX', 12)

def generate_lab_order_number():
    """Generate unique lab order number."""
    return generate_unique_id('LAB', 12)

def validate_email(email):
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Validate phone number format."""
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone)
    # Check if it's 10 digits (US format) or starts with country code
    return len(digits_only) >= 10

def format_phone(phone):
    """Format phone number consistently."""
    digits_only = re.sub(r'\D', '', phone)
    if len(digits_only) == 10:
        return f"({digits_only[:3]}) {digits_only[3:6]}-{digits_only[6:]}"
    elif len(digits_only) == 11 and digits_only[0] == '1':
        return f"+1 ({digits_only[1:4]}) {digits_only[4:7]}-{digits_only[7:]}"
    return phone

def calculate_age(birth_date):
    """Calculate age from birth date."""
    if not birth_date:
        return None
    
    if isinstance(birth_date, str):
        birth_date = datetime.strptime(birth_date, '%Y-%m-%d').date()
    
    today = date.today()
    age = today.year - birth_date.year
    
    # Adjust if birthday hasn't occurred this year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1
    
    return age

def sanitize_string(text, max_length=None):
    """Sanitize string input."""
    if not text:
        return text
    
    # Remove excessive whitespace
    text = ' '.join(text.split())
    
    # Trim to max length if specified
    if max_length and len(text) > max_length:
        text = text[:max_length]
    
    return text

def parse_date(date_string):
    """Parse date string in various formats."""
    if not date_string:
        return None
    
    formats = ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S']
    
    for fmt in formats:
        try:
            return datetime.strptime(date_string, fmt).date()
        except ValueError:
            continue
    
    raise ValueError(f"Unable to parse date: {date_string}")

def parse_time(time_string):
    """Parse time string in various formats."""
    if not time_string:
        return None
    
    formats = ['%H:%M', '%H:%M:%S', '%I:%M %p', '%I:%M:%S %p']
    
    for fmt in formats:
        try:
            return datetime.strptime(time_string, fmt).time()
        except ValueError:
            continue
    
    raise ValueError(f"Unable to parse time: {time_string}")

def get_day_of_week(date_obj):
    """Get day of week as integer (0=Monday, 6=Sunday)."""
    if isinstance(date_obj, str):
        date_obj = parse_date(date_obj)
    return date_obj.weekday()

def is_business_day(date_obj):
    """Check if date is a business day (Monday-Friday)."""
    day_of_week = get_day_of_week(date_obj)
    return day_of_week < 5  # Monday=0 to Friday=4

def format_currency(amount):
    """Format amount as currency."""
    return f"${amount:,.2f}"

def validate_password_strength(password):
    """Validate password strength."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    
    return True, "Password is strong"

def paginate_query(query, page=1, per_page=20, max_per_page=100):
    """Paginate a SQLAlchemy query."""
    if per_page > max_per_page:
        per_page = max_per_page
    
    paginated = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    return {
        'items': paginated.items,
        'total': paginated.total,
        'page': paginated.page,
        'per_page': paginated.per_page,
        'pages': paginated.pages,
        'has_prev': paginated.has_prev,
        'has_next': paginated.has_next,
        'prev_num': paginated.prev_num,
        'next_num': paginated.next_num
    }