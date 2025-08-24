#!/bin/bash

# Hospital Management System Development Setup Script
# This script sets up the development environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        error "Python 3 is not installed. Please install Python 3.8+ first."
    fi
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        error "Node.js is not installed. Please install Node.js 18+ first."
    fi
    
    # Check MySQL
    if ! command -v mysql &> /dev/null; then
        warning "MySQL client not found. Please ensure MySQL server is available."
    fi
    
    success "Prerequisites check completed"
}

# Setup backend
setup_backend() {
    log "Setting up backend..."
    
    cd backend
    
    # Create virtual environment
    if [ ! -d "venv" ]; then
        log "Creating Python virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies
    log "Installing Python dependencies..."
    pip install -r requirements.txt
    
    # Setup environment file
    if [ ! -f ".env" ]; then
        log "Creating environment configuration..."
        cp .env.example .env
        warning "Please update .env with your database credentials"
    fi
    
    cd ..
    success "Backend setup completed"
}

# Setup frontend
setup_frontend() {
    log "Setting up frontend..."
    
    cd frontend
    
    # Install dependencies
    log "Installing Node.js dependencies..."
    npm install
    
    cd ..
    success "Frontend setup completed"
}

# Setup database
setup_database() {
    log "Setting up database..."
    
    # Check if database exists
    read -p "Do you want to create and seed the database? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cd backend
        source venv/bin/activate
        
        log "Creating database..."
        python create_db.py
        
        log "Seeding database..."
        python run.py seed_db
        
        cd ..
        success "Database setup completed"
    else
        warning "Database setup skipped"
    fi
}

# Create development configuration
create_dev_config() {
    log "Creating development configuration..."
    
    # Backend development config
    cat > backend/.env.development << EOF
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=dev-secret-key-change-in-production
JWT_SECRET_KEY=dev-jwt-secret-key-change-in-production

# Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_NAME=hospital_management_dev
DB_USER=root
DB_PASSWORD=password

# Security
BCRYPT_LOG_ROUNDS=4

# CORS Configuration
CORS_ORIGINS=http://localhost:4200
EOF

    # Frontend development config
    mkdir -p frontend/src/environments
    cat > frontend/src/environments/environment.ts << EOF
export const environment = {
  production: false,
  apiUrl: 'http://localhost:5000/api',
  appName: 'MedCare HMS - Development'
};
EOF

    cat > frontend/src/environments/environment.prod.ts << EOF
export const environment = {
  production: true,
  apiUrl: '/api',
  appName: 'MedCare HMS'
};
EOF

    success "Development configuration created"
}

# Create helper scripts
create_scripts() {
    log "Creating helper scripts..."
    
    # Backend start script
    cat > scripts/start-backend.sh << 'EOF'
#!/bin/bash
cd backend
source venv/bin/activate
export FLASK_ENV=development
python run.py
EOF
    chmod +x scripts/start-backend.sh
    
    # Frontend start script
    cat > scripts/start-frontend.sh << 'EOF'
#!/bin/bash
cd frontend
npm run serve
EOF
    chmod +x scripts/start-frontend.sh
    
    # Database reset script
    cat > scripts/reset-database.sh << 'EOF'
#!/bin/bash
cd backend
source venv/bin/activate
python create_db.py
python run.py seed_db
echo "Database reset and seeded successfully!"
EOF
    chmod +x scripts/reset-database.sh
    
    success "Helper scripts created"
}

# Show development information
show_dev_info() {
    echo ""
    echo "======================================"
    echo "   Development Setup Complete"
    echo "======================================"
    echo ""
    echo "🚀 Quick Start:"
    echo "   Backend:  ./scripts/start-backend.sh"
    echo "   Frontend: ./scripts/start-frontend.sh"
    echo ""
    echo "🌐 URLs:"
    echo "   Frontend: http://localhost:4200"
    echo "   Backend:  http://localhost:5000"
    echo ""
    echo "🗄️ Database:"
    echo "   Reset DB: ./scripts/reset-database.sh"
    echo ""
    echo "📚 Documentation:"
    echo "   API Docs: http://localhost:5000/api/docs"
    echo "   README:   ./README.md"
    echo ""
    echo "🔧 Configuration:"
    echo "   Backend:  backend/.env"
    echo "   Frontend: frontend/src/environments/"
    echo ""
    echo "📊 Default Accounts:"
    echo "   Admin:        admin@hospital.com / Admin123!"
    echo "   Doctor:       doctor@hospital.com / Doctor123!"
    echo "   Receptionist: receptionist@hospital.com / Receptionist123!"
    echo "   Patient:      patient@example.com / Patient123!"
    echo ""
    echo "======================================"
}

# Main setup logic
main() {
    echo "🏥 Hospital Management System - Development Setup"
    echo "================================================="
    echo ""
    
    check_prerequisites
    setup_backend
    setup_frontend
    create_dev_config
    create_scripts
    setup_database
    
    show_dev_info
    
    success "Development environment setup completed!"
    echo ""
    echo "Next steps:"
    echo "1. Update backend/.env with your database credentials"
    echo "2. Start the backend: ./scripts/start-backend.sh"
    echo "3. Start the frontend: ./scripts/start-frontend.sh"
    echo "4. Visit http://localhost:4200 to access the application"
}

# Run main function
main "$@"