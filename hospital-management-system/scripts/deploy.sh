#!/bin/bash

# Hospital Management System Deployment Script
# This script handles the deployment of the complete HMS application

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="hospital-management-system"
BACKUP_DIR="./backups"
LOG_FILE="./deploy.log"

# Functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed. Please install Docker first."
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed. Please install Docker Compose first."
    fi
    
    # Check if ports are available
    if lsof -Pi :80 -sTCP:LISTEN -t >/dev/null 2>&1; then
        warning "Port 80 is already in use. This may cause conflicts."
    fi
    
    if lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null 2>&1; then
        warning "Port 5000 is already in use. This may cause conflicts."
    fi
    
    success "Prerequisites check completed"
}

# Create backup
create_backup() {
    if [ "$1" = "true" ]; then
        log "Creating backup..."
        
        mkdir -p "$BACKUP_DIR"
        BACKUP_NAME="backup_$(date +'%Y%m%d_%H%M%S')"
        
        # Backup database if running
        if docker-compose ps | grep -q hospital_db; then
            log "Backing up database..."
            docker-compose exec -T database mysqldump -u root -prootpassword hospital_management > "$BACKUP_DIR/${BACKUP_NAME}_database.sql"
        fi
        
        # Backup configuration files
        tar -czf "$BACKUP_DIR/${BACKUP_NAME}_config.tar.gz" docker-compose.yml backend/.env frontend/src/environments/ 2>/dev/null || true
        
        success "Backup created: $BACKUP_NAME"
    fi
}

# Build and deploy
deploy() {
    log "Starting deployment..."
    
    # Stop existing containers
    log "Stopping existing containers..."
    docker-compose down || true
    
    # Remove old images if requested
    if [ "$1" = "clean" ]; then
        log "Removing old images..."
        docker-compose down --rmi all --volumes --remove-orphans || true
        docker system prune -af || true
    fi
    
    # Build and start services
    log "Building and starting services..."
    docker-compose build --no-cache
    docker-compose up -d
    
    # Wait for services to be ready
    log "Waiting for services to be ready..."
    sleep 30
    
    # Check service health
    check_health
    
    success "Deployment completed successfully!"
}

# Check service health
check_health() {
    log "Checking service health..."
    
    # Check database
    if docker-compose exec -T database mysqladmin ping -h localhost --silent; then
        success "Database is healthy"
    else
        error "Database is not responding"
    fi
    
    # Check backend
    if curl -f http://localhost:5000/api/health >/dev/null 2>&1; then
        success "Backend is healthy"
    else
        error "Backend is not responding"
    fi
    
    # Check frontend
    if curl -f http://localhost:80/health >/dev/null 2>&1; then
        success "Frontend is healthy"
    else
        warning "Frontend may not be fully ready yet"
    fi
}

# Setup SSL certificates
setup_ssl() {
    log "Setting up SSL certificates..."
    
    mkdir -p nginx/ssl
    
    # Generate self-signed certificate for development
    if [ ! -f nginx/ssl/server.crt ]; then
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout nginx/ssl/server.key \
            -out nginx/ssl/server.crt \
            -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
        
        success "SSL certificates generated"
    else
        log "SSL certificates already exist"
    fi
}

# Initialize database
init_database() {
    log "Initializing database..."
    
    # Wait for database to be ready
    sleep 20
    
    # Run database initialization
    docker-compose exec backend python create_db.py
    docker-compose exec backend python run.py seed_db
    
    success "Database initialized with sample data"
}

# Show deployment information
show_info() {
    echo ""
    echo "======================================"
    echo "   Deployment Information"
    echo "======================================"
    echo ""
    echo "🌐 Frontend URL: http://localhost"
    echo "🔧 Backend API: http://localhost:5000"
    echo "🗄️  Database: localhost:3306"
    echo ""
    echo "📊 Default Accounts:"
    echo "   Admin: admin@hospital.com / Admin123!"
    echo "   Doctor: doctor@hospital.com / Doctor123!"
    echo "   Receptionist: receptionist@hospital.com / Receptionist123!"
    echo "   Patient: patient@example.com / Patient123!"
    echo ""
    echo "🔍 Monitoring:"
    echo "   docker-compose logs -f"
    echo "   docker-compose ps"
    echo ""
    echo "🛑 To stop:"
    echo "   docker-compose down"
    echo ""
    echo "======================================"
}

# Main deployment logic
main() {
    echo "🏥 Hospital Management System Deployment"
    echo "========================================"
    echo ""
    
    # Parse command line arguments
    BACKUP=false
    CLEAN=false
    INIT_DB=false
    SSL=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --backup)
                BACKUP=true
                shift
                ;;
            --clean)
                CLEAN=true
                shift
                ;;
            --init-db)
                INIT_DB=true
                shift
                ;;
            --ssl)
                SSL=true
                shift
                ;;
            --help)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --backup    Create backup before deployment"
                echo "  --clean     Clean build (remove old images)"
                echo "  --init-db   Initialize database with sample data"
                echo "  --ssl       Setup SSL certificates"
                echo "  --help      Show this help message"
                echo ""
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                ;;
        esac
    done
    
    # Start deployment process
    check_prerequisites
    create_backup $BACKUP
    
    if [ "$SSL" = "true" ]; then
        setup_ssl
    fi
    
    if [ "$CLEAN" = "true" ]; then
        deploy clean
    else
        deploy
    fi
    
    if [ "$INIT_DB" = "true" ]; then
        init_database
    fi
    
    show_info
    
    success "Hospital Management System deployed successfully!"
}

# Run main function
main "$@"