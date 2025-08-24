# MedCare Hospital Management System

A comprehensive hospital management system built with Flask (backend) and Angular (frontend), implementing role-based access control for managing patients, doctors, appointments, medical records, and billing.

## 🏥 Features

### Role-Based Access Control (RBAC)
- **Admin**: Complete system control and management
- **Doctor**: Patient care, medical records, prescriptions
- **Patient**: Personal health records, family management, appointments
- **Receptionist**: Patient registration, appointment management, billing

### Core Modules
- **User Management**: Authentication, authorization, user profiles
- **Patient Management**: Registration, family members, medical history
- **Doctor Management**: Profiles, specializations, schedules
- **Appointment System**: Booking, scheduling, status tracking
- **Medical Records**: Consultations, prescriptions, lab orders
- **Billing System**: Invoicing, payments, insurance handling
- **Administrative Tools**: Reports, system management, analytics

## 🛠 Technology Stack

### Backend
- **Flask 2.3.3**: Web framework
- **SQLAlchemy**: ORM for database operations
- **MySQL**: Primary database
- **JWT**: Token-based authentication
- **Flask-CORS**: Cross-origin resource sharing
- **Marshmallow**: Data serialization/validation
- **Flask-Migrate**: Database migrations

### Frontend
- **Angular 17**: Frontend framework
- **Angular Material**: UI component library
- **Bootstrap 5**: CSS framework
- **TypeScript**: Programming language
- **RxJS**: Reactive programming
- **Chart.js**: Data visualization

## 📋 Prerequisites

- Python 3.8+
- Node.js 18+
- MySQL 8.0+
- npm or yarn

## 🚀 Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd hospital-management-system
```

### 2. Backend Setup

#### Create Virtual Environment
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### Install Dependencies
```bash
pip install -r requirements.txt
```

#### Configure Environment
```bash
cp .env.example .env
# Edit .env with your database credentials and settings
```

#### Setup Database
```bash
# Create database
python create_db.py

# Seed with initial data
python run.py seed_db
```

### 3. Frontend Setup

#### Install Dependencies
```bash
cd frontend
npm install
```

#### Configure Environment
```bash
# Update proxy.conf.json if needed for backend URL
```

## 🏃‍♂️ Running the Application

### Start Backend Server
```bash
cd backend
source venv/bin/activate
python run.py
```
Backend will run on `http://localhost:5000`

### Start Frontend Server
```bash
cd frontend
npm run serve
```
Frontend will run on `http://localhost:4200`

## 🔐 Default User Accounts

After seeding the database, the following accounts are available:

| Role | Email | Password | Access Level |
|------|-------|----------|--------------|
| Admin | admin@hospital.com | Admin123! | Full system access |
| Doctor | doctor@hospital.com | Doctor123! | Medical operations |
| Receptionist | receptionist@hospital.com | Receptionist123! | Administrative operations |
| Patient | patient@example.com | Patient123! | Personal records |

## 📊 System Architecture

### Database Schema
The system uses a comprehensive relational database schema with the following main entities:

- **Users**: Base user authentication and profile information
- **Patients**: Patient-specific data and family relationships
- **Doctors**: Doctor profiles, specializations, and schedules
- **Appointments**: Appointment booking and management
- **Medical Records**: Consultation notes, prescriptions, lab orders
- **Billing**: Bills, payments, and financial transactions
- **Departments**: Hospital departments and services

### API Architecture
RESTful API with the following main endpoints:

- `/api/auth/*`: Authentication and authorization
- `/api/users/*`: User management
- `/api/patients/*`: Patient operations
- `/api/doctors/*`: Doctor operations
- `/api/appointments/*`: Appointment management
- `/api/medical-records/*`: Medical record operations
- `/api/billing/*`: Billing and payment operations
- `/api/admin/*`: Administrative functions

## 🔒 Security Features

### Authentication & Authorization
- JWT-based authentication
- Role-based access control (RBAC)
- Secure password hashing with bcrypt
- Token refresh mechanism
- Session management

### Data Security
- Input validation and sanitization
- SQL injection prevention
- XSS protection
- CORS configuration
- Encrypted sensitive data storage

### HIPAA Compliance Features
- Access logging and audit trails
- Data encryption at rest and in transit
- Role-based data access restrictions
- Secure user authentication
- Patient data anonymization options

## 📱 User Interfaces

### Admin Dashboard
- System overview and statistics
- User management and role assignment
- Department and service configuration
- Financial reports and analytics
- System health monitoring

### Doctor Dashboard
- Appointment schedule view
- Patient list and medical records
- Prescription management
- Treatment plan documentation
- Performance metrics

### Patient Portal
- Personal health dashboard
- Family member management
- Appointment booking system
- Medical history access
- Billing and payment view

### Receptionist Interface
- Patient check-in/check-out
- Appointment scheduling
- Payment processing
- Insurance verification
- Report generation

## 🧪 Testing

### Backend Testing
```bash
cd backend
python -m pytest tests/
```

### Frontend Testing
```bash
cd frontend
npm run test
```

## 🐳 Docker Deployment

### Using Docker Compose
```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 📈 Monitoring and Logging

### Application Logs
- Structured logging with rotation
- Error tracking and alerting
- Performance monitoring
- User activity logging

### Health Checks
- Database connectivity monitoring
- API endpoint health checks
- System resource monitoring
- Automated backup verification

## 🔧 Configuration

### Environment Variables

#### Backend (.env)
```env
FLASK_ENV=development
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret
DB_HOST=localhost
DB_PORT=3306
DB_NAME=hospital_management
DB_USER=root
DB_PASSWORD=password
```

#### Frontend (environment.ts)
```typescript
export const environment = {
  production: false,
  apiUrl: 'http://localhost:5000/api'
};
```

## 📝 API Documentation

### Authentication Endpoints
- `POST /api/auth/login`: User login
- `POST /api/auth/register/patient`: Patient registration
- `POST /api/auth/logout`: User logout
- `POST /api/auth/refresh`: Token refresh
- `GET /api/auth/profile`: User profile
- `POST /api/auth/change-password`: Password change

### Patient Management
- `GET /api/patients`: List patients
- `POST /api/patients`: Create patient
- `GET /api/patients/{id}`: Get patient details
- `PUT /api/patients/{id}`: Update patient
- `POST /api/patients/family-member`: Add family member

### Appointment Management
- `GET /api/appointments`: List appointments
- `POST /api/appointments`: Create appointment
- `PUT /api/appointments/{id}`: Update appointment
- `POST /api/appointments/{id}/cancel`: Cancel appointment
- `GET /api/appointments/available-slots`: Get available slots

[Full API documentation available in `/docs/api.md`]

## 🚀 Deployment

### Production Deployment

#### Backend (Flask)
```bash
# Using Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 run:app

# Using Docker
docker build -t hospital-backend .
docker run -p 5000:5000 hospital-backend
```

#### Frontend (Angular)
```bash
# Build for production
npm run build

# Serve with nginx
nginx -g 'daemon off;'
```

### Environment Setup
1. Configure production database
2. Set environment variables
3. Configure SSL certificates
4. Set up reverse proxy (nginx)
5. Configure monitoring and logging

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For support and questions:
- Create an issue on GitHub
- Email: support@medcare-hms.com
- Documentation: [docs/](docs/)

## 🔮 Future Enhancements

- Mobile application (React Native/Flutter)
- Telemedicine integration
- AI-powered diagnostics
- Insurance claim automation
- Multi-language support
- Advanced reporting and analytics
- Integration with medical devices
- Pharmacy management module

---

**Note**: This is a demonstration system. For production use, ensure proper security audits, compliance verification, and testing.