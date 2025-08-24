# Hospital Management System - Deployment Guide

This guide provides detailed instructions for deploying the MedCare Hospital Management System in various environments.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Development Setup](#development-setup)
3. [Production Deployment](#production-deployment)
4. [Docker Deployment](#docker-deployment)
5. [Cloud Deployment](#cloud-deployment)
6. [Security Configuration](#security-configuration)
7. [Monitoring and Maintenance](#monitoring-and-maintenance)
8. [Troubleshooting](#troubleshooting)

## 🔧 Prerequisites

### System Requirements

#### Minimum Requirements
- **CPU**: 2 cores
- **RAM**: 4GB
- **Storage**: 20GB SSD
- **OS**: Ubuntu 20.04+ / CentOS 8+ / Windows 10+

#### Recommended Requirements
- **CPU**: 4+ cores
- **RAM**: 8GB+
- **Storage**: 50GB+ SSD
- **OS**: Ubuntu 22.04 LTS

### Software Requirements

- **Python**: 3.8+
- **Node.js**: 18+
- **MySQL**: 8.0+
- **Docker**: 20.10+ (for containerized deployment)
- **Docker Compose**: 2.0+
- **Nginx**: 1.20+ (for reverse proxy)

## 🚀 Development Setup

### Quick Setup

```bash
# Clone the repository
git clone <repository-url>
cd hospital-management-system

# Run the development setup script
./scripts/setup-dev.sh
```

### Manual Setup

#### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Setup database
python create_db.py
python run.py seed_db

# Start development server
python run.py
```

#### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run serve
```

#### 3. Access the Application

- **Frontend**: http://localhost:4200
- **Backend API**: http://localhost:5000
- **Database**: localhost:3306

## 🏭 Production Deployment

### 1. Server Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3 python3-pip python3-venv nodejs npm mysql-server nginx certbot

# Configure MySQL
sudo mysql_secure_installation
```

### 2. Application Deployment

#### Backend Production Setup

```bash
# Create application user
sudo useradd -m -s /bin/bash hospital
sudo su - hospital

# Clone and setup application
git clone <repository-url> hospital-management-system
cd hospital-management-system/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install production dependencies
pip install -r requirements.txt gunicorn

# Configure production environment
cp .env.example .env
# Edit .env for production settings

# Setup database
python create_db.py
python run.py seed_db
```

#### Frontend Production Build

```bash
cd ../frontend

# Install dependencies
npm ci --only=production

# Build for production
npm run build

# Copy build files to web server
sudo cp -r dist/hospital-frontend/* /var/www/html/
```

### 3. System Service Configuration

#### Gunicorn Service

```bash
# Create service file
sudo tee /etc/systemd/system/hospital-backend.service > /dev/null <<EOF
[Unit]
Description=Hospital Management System Backend
After=network.target

[Service]
User=hospital
Group=hospital
WorkingDirectory=/home/hospital/hospital-management-system/backend
Environment=PATH=/home/hospital/hospital-management-system/backend/venv/bin
ExecStart=/home/hospital/hospital-management-system/backend/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:5000 run:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable hospital-backend
sudo systemctl start hospital-backend
```

#### Nginx Configuration

```bash
# Create nginx configuration
sudo tee /etc/nginx/sites-available/hospital-management > /dev/null <<EOF
server {
    listen 80;
    server_name your-domain.com;
    
    root /var/www/html;
    index index.html;
    
    # Frontend
    location / {
        try_files \$uri \$uri/ /index.html;
    }
    
    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/hospital-management /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 4. SSL Certificate Setup

```bash
# Install Certbot SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## 🐳 Docker Deployment

### 1. Using Docker Compose

```bash
# Clone repository
git clone <repository-url>
cd hospital-management-system

# Build and deploy
./scripts/deploy.sh --init-db --ssl

# Or manually
docker-compose up -d
```

### 2. Production Docker Setup

```bash
# Create production environment
cp .env.example .env.production

# Edit production configuration
nano .env.production

# Deploy with production settings
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 3. Docker Service Management

```bash
# View logs
docker-compose logs -f

# Check status
docker-compose ps

# Restart services
docker-compose restart

# Update and redeploy
git pull
docker-compose build --no-cache
docker-compose up -d
```

## ☁️ Cloud Deployment

### AWS Deployment

#### 1. EC2 Instance Setup

```bash
# Launch EC2 instance (t3.medium or larger)
# Configure security groups (80, 443, 22, 3306, 5000)

# Connect and setup
ssh -i your-key.pem ubuntu@your-instance-ip

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Deploy application
git clone <repository-url>
cd hospital-management-system
./scripts/deploy.sh --init-db
```

#### 2. RDS Database Setup

```bash
# Create RDS MySQL instance
# Update .env with RDS endpoint
DB_HOST=your-rds-endpoint.amazonaws.com
DB_USER=your-username
DB_PASSWORD=your-password
```

#### 3. Load Balancer & Auto Scaling

```bash
# Create Application Load Balancer
# Configure target groups
# Setup auto scaling group
# Configure CloudWatch monitoring
```

### Google Cloud Platform

#### 1. Cloud Run Deployment

```bash
# Build and push to Container Registry
gcloud builds submit --tag gcr.io/PROJECT-ID/hospital-backend backend/
gcloud builds submit --tag gcr.io/PROJECT-ID/hospital-frontend frontend/

# Deploy to Cloud Run
gcloud run deploy hospital-backend \
  --image gcr.io/PROJECT-ID/hospital-backend \
  --platform managed \
  --region us-central1

gcloud run deploy hospital-frontend \
  --image gcr.io/PROJECT-ID/hospital-frontend \
  --platform managed \
  --region us-central1
```

#### 2. Cloud SQL Setup

```bash
# Create Cloud SQL instance
gcloud sql instances create hospital-db \
  --database-version=MYSQL_8_0 \
  --tier=db-f1-micro \
  --region=us-central1

# Create database
gcloud sql databases create hospital_management --instance=hospital-db
```

### Azure Deployment

#### 1. Container Instances

```bash
# Create resource group
az group create --name hospital-rg --location eastus

# Deploy containers
az container create \
  --resource-group hospital-rg \
  --name hospital-backend \
  --image your-registry/hospital-backend:latest \
  --ports 5000

az container create \
  --resource-group hospital-rg \
  --name hospital-frontend \
  --image your-registry/hospital-frontend:latest \
  --ports 80
```

#### 2. Azure Database for MySQL

```bash
# Create MySQL server
az mysql server create \
  --resource-group hospital-rg \
  --name hospital-mysql \
  --location eastus \
  --admin-user hospital \
  --admin-password YourPassword123! \
  --sku-name GP_Gen5_2
```

## 🔒 Security Configuration

### 1. Database Security

```sql
-- Create application user
CREATE USER 'hospital_app'@'%' IDENTIFIED BY 'strong_password';
GRANT SELECT, INSERT, UPDATE, DELETE ON hospital_management.* TO 'hospital_app'@'%';
FLUSH PRIVILEGES;

-- Configure SSL
ALTER USER 'hospital_app'@'%' REQUIRE SSL;
```

### 2. Application Security

```bash
# Generate secure keys
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Configure firewall
sudo ufw enable
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

### 3. SSL/TLS Configuration

```nginx
# Strong SSL configuration
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
ssl_prefer_server_ciphers off;
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;

# Security headers
add_header Strict-Transport-Security "max-age=63072000" always;
add_header X-Frame-Options DENY always;
add_header X-Content-Type-Options nosniff always;
```

## 📊 Monitoring and Maintenance

### 1. Application Monitoring

```bash
# Install monitoring tools
sudo apt install htop iotop nethogs

# Setup log rotation
sudo tee /etc/logrotate.d/hospital-app > /dev/null <<EOF
/home/hospital/hospital-management-system/backend/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 0644 hospital hospital
}
EOF
```

### 2. Database Monitoring

```sql
-- Monitor database performance
SHOW PROCESSLIST;
SHOW ENGINE INNODB STATUS;

-- Check database size
SELECT 
    table_schema AS 'Database',
    ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS 'Size (MB)'
FROM information_schema.tables 
WHERE table_schema = 'hospital_management';
```

### 3. Backup Strategy

```bash
# Database backup script
#!/bin/bash
BACKUP_DIR="/backup/mysql"
DATE=$(date +"%Y%m%d_%H%M%S")
mysqldump -u backup_user -p hospital_management > "$BACKUP_DIR/hospital_backup_$DATE.sql"

# Compress and upload to cloud storage
gzip "$BACKUP_DIR/hospital_backup_$DATE.sql"
aws s3 cp "$BACKUP_DIR/hospital_backup_$DATE.sql.gz" s3://your-backup-bucket/

# Cron job for daily backups
0 2 * * * /usr/local/bin/backup-hospital-db.sh
```

### 4. Health Checks

```bash
# Application health check script
#!/bin/bash
if curl -f http://localhost:5000/api/health > /dev/null 2>&1; then
    echo "Backend: OK"
else
    echo "Backend: FAILED"
    # Send alert or restart service
fi

if curl -f http://localhost/health > /dev/null 2>&1; then
    echo "Frontend: OK"
else
    echo "Frontend: FAILED"
fi
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Database Connection Issues

```bash
# Check MySQL status
sudo systemctl status mysql

# Check connections
mysql -u root -p -e "SHOW PROCESSLIST;"

# Check error logs
sudo tail -f /var/log/mysql/error.log
```

#### 2. Application Errors

```bash
# Check backend logs
sudo journalctl -u hospital-backend -f

# Check application logs
tail -f backend/logs/app.log

# Check nginx logs
sudo tail -f /var/log/nginx/error.log
```

#### 3. Performance Issues

```bash
# Monitor system resources
htop

# Check database performance
mysqladmin -u root -p processlist

# Monitor network
netstat -tulpn
```

#### 4. Memory Issues

```bash
# Check memory usage
free -h

# Monitor Python processes
ps aux | grep python

# Check for memory leaks
valgrind --tool=memcheck python run.py
```

### Maintenance Tasks

#### Daily
- Check application logs for errors
- Monitor system resources
- Verify backup completion

#### Weekly
- Update system packages
- Review security logs
- Performance optimization

#### Monthly
- Update application dependencies
- Database maintenance and optimization
- Security audit

## 📞 Support

For deployment support:
- Check the troubleshooting section
- Review application logs
- Contact system administrator
- Create GitHub issue for bugs

---

**Note**: Always test deployments in a staging environment before production deployment.