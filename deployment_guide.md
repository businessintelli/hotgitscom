# Hotgigs.com Deployment Guide

## 🚀 Quick Start Deployment

This guide provides step-by-step instructions for deploying Hotgigs.com in various environments, from local development to production cloud deployment.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Docker Deployment](#docker-deployment)
4. [Cloud Deployment (AWS)](#cloud-deployment-aws)
5. [Cloud Deployment (Google Cloud)](#cloud-deployment-google-cloud)
6. [Cloud Deployment (Azure)](#cloud-deployment-azure)
7. [Static Hosting (Netlify/Vercel)](#static-hosting-netlifyvercel)
8. [Environment Configuration](#environment-configuration)
9. [Database Setup](#database-setup)
10. [SSL/TLS Configuration](#ssltls-configuration)
11. [Monitoring Setup](#monitoring-setup)
12. [Backup and Recovery](#backup-and-recovery)
13. [Scaling Considerations](#scaling-considerations)
14. [Troubleshooting](#troubleshooting)

## 🔧 Prerequisites

### System Requirements

#### Minimum Requirements
- **CPU**: 2 cores
- **RAM**: 4GB
- **Storage**: 20GB SSD
- **Network**: 100 Mbps

#### Recommended Requirements
- **CPU**: 4+ cores
- **RAM**: 8GB+
- **Storage**: 50GB+ SSD
- **Network**: 1 Gbps

### Software Dependencies

#### Backend Dependencies
- **Python**: 3.11 or higher
- **PostgreSQL**: 15 or higher
- **Redis**: 7 or higher (for caching)
- **Tesseract OCR**: For resume image processing

#### Frontend Dependencies
- **Node.js**: 18 or higher
- **npm**: 9 or higher

#### Development Tools
- **Git**: Version control
- **Docker**: Containerization (optional)
- **Docker Compose**: Multi-container orchestration

## 💻 Local Development Setup

### Step 1: Clone Repository

```bash
# Clone the repository
git clone https://github.com/your-org/hotgigs.git
cd hotgigs

# Verify directory structure
ls -la
# Should show: hotgigs-backend/ hotgigs-frontend/ README.md
```

### Step 2: Backend Setup

```bash
# Navigate to backend directory
cd hotgigs-backend

# Create and activate virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Install additional ML dependencies (optional)
pip install spacy scikit-learn
python -m spacy download en_core_web_sm

# Install system dependencies (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-eng

# Install system dependencies (macOS)
brew install tesseract

# Install system dependencies (Windows)
# Download and install Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki
```

### Step 3: Database Setup

```bash
# Install PostgreSQL (Ubuntu/Debian)
sudo apt-get install postgresql postgresql-contrib

# Install PostgreSQL (macOS)
brew install postgresql
brew services start postgresql

# Create database and user
sudo -u postgres psql
```

```sql
-- In PostgreSQL shell
CREATE DATABASE hotgigs;
CREATE USER hotgigs_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE hotgigs TO hotgigs_user;
ALTER USER hotgigs_user CREATEDB;
\q
```

### Step 4: Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit environment variables
nano .env
```

```bash
# .env file content
DATABASE_URL=postgresql://hotgigs_user:your_secure_password@localhost:5432/hotgigs
SECRET_KEY=your-super-secret-key-change-this
JWT_SECRET_KEY=your-jwt-secret-key-change-this

# Email configuration (optional for development)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# File upload settings
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=10485760

# Development settings
FLASK_ENV=development
FLASK_DEBUG=True
```

### Step 5: Initialize Database

```bash
# Initialize database schema
python -c "
from src.main import create_app
from src.models.database import db
app = create_app()
with app.app_context():
    db.create_all()
    print('Database initialized successfully!')
"
```

### Step 6: Start Backend Server

```bash
# Start the backend server
python src/main.py

# Server should start on http://localhost:5002
# You should see: "Running on http://0.0.0.0:5002"
```

### Step 7: Frontend Setup

```bash
# Open new terminal and navigate to frontend
cd ../hotgigs-frontend

# Install dependencies
npm install

# Create environment file
cp .env.example .env.local
```

```bash
# .env.local content
VITE_API_BASE_URL=http://localhost:5002
VITE_APP_NAME=Hotgigs.com
```

### Step 8: Start Frontend Server

```bash
# Start the frontend development server
npm run dev

# Server should start on http://localhost:5173
# Open browser and navigate to http://localhost:5173
```

### Step 9: Verify Installation

1. **Frontend**: Open http://localhost:5173
2. **Backend API**: Test http://localhost:5002/api/health
3. **Database**: Check connection in backend logs

## 🐳 Docker Deployment

### Step 1: Install Docker

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# macOS
brew install docker docker-compose

# Windows
# Download Docker Desktop from https://www.docker.com/products/docker-desktop
```

### Step 2: Create Docker Configuration

**docker-compose.yml**
```yaml
version: '3.8'

services:
  database:
    image: postgres:15
    environment:
      POSTGRES_DB: hotgigs
      POSTGRES_USER: hotgigs_user
      POSTGRES_PASSWORD: secure_password_123
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U hotgigs_user -d hotgigs"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

  backend:
    build: 
      context: ./hotgigs-backend
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: postgresql://hotgigs_user:secure_password_123@database:5432/hotgigs
      SECRET_KEY: docker-secret-key-change-in-production
      JWT_SECRET_KEY: docker-jwt-secret-change-in-production
      REDIS_URL: redis://redis:6379/0
    depends_on:
      database:
        condition: service_healthy
      redis:
        condition: service_started
    ports:
      - "5002:5000"
    volumes:
      - ./uploads:/app/uploads
      - ./logs:/app/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build:
      context: ./hotgigs-frontend
      dockerfile: Dockerfile
      args:
        VITE_API_BASE_URL: http://localhost:5002
    ports:
      - "3000:80"
    depends_on:
      backend:
        condition: service_healthy

volumes:
  postgres_data:
  redis_data:
```

### Step 3: Create Dockerfiles

**Backend Dockerfile (hotgigs-backend/Dockerfile)**
```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model
RUN python -m spacy download en_core_web_sm

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads logs

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Run application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "src.main:app"]
```

**Frontend Dockerfile (hotgigs-frontend/Dockerfile)**
```dockerfile
# Build stage
FROM node:18-alpine as build

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci --only=production

# Copy source code
COPY . .

# Build arguments
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

# Build application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built files
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Create non-root user
RUN addgroup -g 1000 -S appgroup && \
    adduser -u 1000 -S appuser -G appgroup

# Set permissions
RUN chown -R appuser:appgroup /usr/share/nginx/html && \
    chown -R appuser:appgroup /var/cache/nginx && \
    chown -R appuser:appgroup /var/log/nginx && \
    chown -R appuser:appgroup /etc/nginx/conf.d

# Switch to non-root user
USER appuser

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### Step 4: Deploy with Docker

```bash
# Build and start all services
docker-compose up --build -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Access application
# Frontend: http://localhost:3000
# Backend: http://localhost:5002
```

### Step 5: Docker Management Commands

```bash
# Stop services
docker-compose down

# Update services
docker-compose pull
docker-compose up --build -d

# View resource usage
docker stats

# Clean up unused resources
docker system prune -a
```

## ☁️ Cloud Deployment (AWS)

### Step 1: AWS Prerequisites

```bash
# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Configure AWS credentials
aws configure
# Enter: Access Key ID, Secret Access Key, Region, Output format

# Install Terraform (optional)
wget https://releases.hashicorp.com/terraform/1.5.0/terraform_1.5.0_linux_amd64.zip
unzip terraform_1.5.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/
```

### Step 2: Create AWS Infrastructure

**terraform/main.tf**
```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# VPC Configuration
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "hotgigs-vpc"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "hotgigs-igw"
  }
}

# Public Subnets
resource "aws_subnet" "public" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 1}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]
  
  map_public_ip_on_launch = true

  tags = {
    Name = "hotgigs-public-subnet-${count.index + 1}"
  }
}

# Private Subnets
resource "aws_subnet" "private" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 10}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "hotgigs-private-subnet-${count.index + 1}"
  }
}

# RDS Database
resource "aws_db_instance" "main" {
  identifier     = "hotgigs-db"
  engine         = "postgres"
  engine_version = "15.3"
  instance_class = "db.t3.micro"
  
  allocated_storage     = 20
  max_allocated_storage = 100
  storage_encrypted     = true
  
  db_name  = "hotgigs"
  username = var.db_username
  password = var.db_password
  
  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
  
  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  skip_final_snapshot = false
  final_snapshot_identifier = "hotgigs-db-final-snapshot"
  
  tags = {
    Name = "hotgigs-database"
  }
}

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "hotgigs-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name = "hotgigs-cluster"
  }
}

# Application Load Balancer
resource "aws_lb" "main" {
  name               = "hotgigs-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets           = aws_subnet.public[*].id

  enable_deletion_protection = false

  tags = {
    Name = "hotgigs-alb"
  }
}
```

### Step 3: Deploy to AWS ECS

```bash
# Initialize Terraform
cd terraform
terraform init

# Plan deployment
terraform plan

# Apply infrastructure
terraform apply

# Build and push Docker images to ECR
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-west-2.amazonaws.com

# Tag and push backend image
docker build -t hotgigs-backend ./hotgigs-backend
docker tag hotgigs-backend:latest 123456789012.dkr.ecr.us-west-2.amazonaws.com/hotgigs-backend:latest
docker push 123456789012.dkr.ecr.us-west-2.amazonaws.com/hotgigs-backend:latest

# Tag and push frontend image
docker build -t hotgigs-frontend ./hotgigs-frontend
docker tag hotgigs-frontend:latest 123456789012.dkr.ecr.us-west-2.amazonaws.com/hotgigs-frontend:latest
docker push 123456789012.dkr.ecr.us-west-2.amazonaws.com/hotgigs-frontend:latest
```

### Step 4: Configure ECS Services

**ecs-task-definition.json**
```json
{
  "family": "hotgigs-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::123456789012:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "hotgigs-backend",
      "image": "123456789012.dkr.ecr.us-west-2.amazonaws.com/hotgigs-backend:latest",
      "portMappings": [
        {
          "containerPort": 5000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DATABASE_URL",
          "value": "postgresql://username:password@rds-endpoint:5432/hotgigs"
        }
      ],
      "secrets": [
        {
          "name": "SECRET_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-west-2:123456789012:secret:hotgigs/secret-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/hotgigs-backend",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:5000/api/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

## 🌐 Static Hosting (Netlify/Vercel)

### Netlify Deployment

#### Step 1: Build Frontend for Production

```bash
cd hotgigs-frontend

# Install dependencies
npm install

# Create production environment file
cat > .env.production << EOF
VITE_API_BASE_URL=https://your-backend-api.com
VITE_APP_NAME=Hotgigs.com
EOF

# Build for production
npm run build

# Test build locally
npm run preview
```

#### Step 2: Deploy to Netlify

**Option A: Netlify CLI**
```bash
# Install Netlify CLI
npm install -g netlify-cli

# Login to Netlify
netlify login

# Deploy to Netlify
netlify deploy --prod --dir=dist

# Configure environment variables
netlify env:set VITE_API_BASE_URL https://your-backend-api.com
```

**Option B: Git Integration**
1. Push code to GitHub/GitLab
2. Connect repository to Netlify
3. Configure build settings:
   - **Build command**: `npm run build`
   - **Publish directory**: `dist`
   - **Environment variables**: Add VITE_API_BASE_URL

**netlify.toml**
```toml
[build]
  command = "npm run build"
  publish = "dist"

[build.environment]
  NODE_VERSION = "18"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200

[[headers]]
  for = "/*"
  [headers.values]
    X-Frame-Options = "DENY"
    X-XSS-Protection = "1; mode=block"
    X-Content-Type-Options = "nosniff"
    Referrer-Policy = "strict-origin-when-cross-origin"
```

### Vercel Deployment

#### Step 1: Deploy with Vercel CLI

```bash
# Install Vercel CLI
npm install -g vercel

# Login to Vercel
vercel login

# Deploy from frontend directory
cd hotgigs-frontend
vercel

# Follow prompts:
# - Set up and deploy? Yes
# - Which scope? Your account
# - Link to existing project? No
# - Project name: hotgigs-frontend
# - Directory: ./
# - Override settings? No
```

#### Step 2: Configure Environment Variables

```bash
# Set environment variables
vercel env add VITE_API_BASE_URL production
# Enter: https://your-backend-api.com

# Redeploy with environment variables
vercel --prod
```

**vercel.json**
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "framework": "vite",
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ],
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "X-Frame-Options",
          "value": "DENY"
        },
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        }
      ]
    }
  ]
}
```

## ⚙️ Environment Configuration

### Production Environment Variables

#### Backend (.env)
```bash
# Database Configuration
DATABASE_URL=postgresql://username:password@host:5432/hotgigs
SQLALCHEMY_DATABASE_URI=postgresql://username:password@host:5432/hotgigs

# Security Keys (Generate new ones for production)
SECRET_KEY=your-super-secure-secret-key-for-production-change-this
JWT_SECRET_KEY=your-jwt-secret-key-for-production-change-this

# Email Configuration
MAIL_SERVER=smtp.sendgrid.net
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=apikey
MAIL_PASSWORD=your-sendgrid-api-key

# File Upload Configuration
UPLOAD_FOLDER=/app/uploads
MAX_CONTENT_LENGTH=10485760  # 10MB

# AI Services
OPENAI_API_KEY=your-openai-api-key
OCR_SPACE_API_KEY=your-ocr-space-api-key

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Monitoring and Logging
SENTRY_DSN=your-sentry-dsn
NEW_RELIC_LICENSE_KEY=your-new-relic-key

# Application Settings
FLASK_ENV=production
FLASK_DEBUG=False
```

#### Frontend (.env.production)
```bash
# API Configuration
VITE_API_BASE_URL=https://api.hotgigs.com
VITE_APP_NAME=Hotgigs.com
VITE_APP_VERSION=1.0.0

# Analytics
VITE_GOOGLE_ANALYTICS_ID=GA_MEASUREMENT_ID
VITE_HOTJAR_ID=your-hotjar-id

# Feature Flags
VITE_ENABLE_CHAT=true
VITE_ENABLE_ANALYTICS=true
VITE_ENABLE_AI_MATCHING=true

# External Services
VITE_STRIPE_PUBLISHABLE_KEY=pk_live_your_stripe_key
```

### Security Configuration

#### Generate Secure Keys
```bash
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate JWT_SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate database password
openssl rand -base64 32
```

#### SSL Certificate Setup
```bash
# Using Let's Encrypt with Certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d hotgigs.com -d www.hotgigs.com

# Auto-renewal setup
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## 🗄️ Database Setup

### PostgreSQL Production Setup

#### Step 1: Install PostgreSQL
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib

# Start and enable PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

#### Step 2: Configure PostgreSQL
```bash
# Switch to postgres user
sudo -u postgres psql

# Create production database and user
CREATE DATABASE hotgigs_prod;
CREATE USER hotgigs_prod_user WITH PASSWORD 'secure_production_password';
GRANT ALL PRIVILEGES ON DATABASE hotgigs_prod TO hotgigs_prod_user;
ALTER USER hotgigs_prod_user CREATEDB;

# Configure connection limits
ALTER USER hotgigs_prod_user CONNECTION LIMIT 20;

# Exit PostgreSQL
\q
```

#### Step 3: Optimize PostgreSQL Configuration
```bash
# Edit PostgreSQL configuration
sudo nano /etc/postgresql/15/main/postgresql.conf
```

```conf
# Memory settings
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB

# Connection settings
max_connections = 100
listen_addresses = 'localhost'

# Performance settings
random_page_cost = 1.1
effective_io_concurrency = 200

# Logging
log_statement = 'all'
log_duration = on
log_min_duration_statement = 1000
```

#### Step 4: Initialize Production Database
```bash
# Run database migrations
cd hotgigs-backend
source venv/bin/activate

# Set production database URL
export DATABASE_URL=postgresql://hotgigs_prod_user:secure_production_password@localhost:5432/hotgigs_prod

# Initialize database
python -c "
from src.main import create_app
from src.models.database import db
app = create_app()
with app.app_context():
    db.create_all()
    print('Production database initialized!')
"
```

### Database Backup Strategy

#### Automated Backups
```bash
#!/bin/bash
# backup-database.sh

# Configuration
DB_NAME="hotgigs_prod"
DB_USER="hotgigs_prod_user"
BACKUP_DIR="/var/backups/postgresql"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/hotgigs_backup_$DATE.sql"

# Create backup directory
mkdir -p $BACKUP_DIR

# Create backup
pg_dump -U $DB_USER -h localhost $DB_NAME > $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

# Remove backups older than 30 days
find $BACKUP_DIR -name "hotgigs_backup_*.sql.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_FILE.gz"
```

```bash
# Make script executable
chmod +x backup-database.sh

# Add to crontab for daily backups at 2 AM
crontab -e
# Add: 0 2 * * * /path/to/backup-database.sh
```

## 🔒 SSL/TLS Configuration

### Nginx SSL Configuration

#### Step 1: Install Nginx
```bash
# Ubuntu/Debian
sudo apt-get install nginx

# Start and enable Nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

#### Step 2: Configure Nginx
```nginx
# /etc/nginx/sites-available/hotgigs.com
server {
    listen 80;
    server_name hotgigs.com www.hotgigs.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name hotgigs.com www.hotgigs.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/hotgigs.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/hotgigs.com/privkey.pem;
    
    # SSL Security
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:;" always;

    # Gzip Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

    # Frontend (React App)
    location / {
        root /var/www/hotgigs/frontend;
        try_files $uri $uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:5002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Buffer settings
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }

    # File uploads
    location /api/resume/upload {
        proxy_pass http://127.0.0.1:5002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Increase upload size limit
        client_max_body_size 10M;
        proxy_request_buffering off;
    }
}
```

#### Step 3: Enable Site
```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/hotgigs.com /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

## 📊 Monitoring Setup

### Application Monitoring

#### Step 1: Install Monitoring Tools
```bash
# Install Prometheus
wget https://github.com/prometheus/prometheus/releases/download/v2.40.0/prometheus-2.40.0.linux-amd64.tar.gz
tar xvfz prometheus-*.tar.gz
sudo mv prometheus-2.40.0.linux-amd64 /opt/prometheus

# Install Grafana
sudo apt-get install -y software-properties-common
sudo add-apt-repository "deb https://packages.grafana.com/oss/deb stable main"
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
sudo apt-get update
sudo apt-get install grafana
```

#### Step 2: Configure Prometheus
```yaml
# /opt/prometheus/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'hotgigs-backend'
    static_configs:
      - targets: ['localhost:5002']
    metrics_path: '/api/metrics'
    
  - job_name: 'nginx'
    static_configs:
      - targets: ['localhost:9113']
      
  - job_name: 'postgresql'
    static_configs:
      - targets: ['localhost:9187']
```

#### Step 3: Setup Health Checks
```python
# Add to backend (src/routes/monitoring.py)
from flask import Blueprint, jsonify
import psutil
import time

monitoring_bp = Blueprint('monitoring', __name__)

@monitoring_bp.route('/api/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': time.time(),
        'version': '1.0.0'
    })

@monitoring_bp.route('/api/metrics')
def metrics():
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    
    return jsonify({
        'cpu_usage_percent': cpu_percent,
        'memory_usage_percent': memory.percent,
        'memory_available_mb': memory.available / 1024 / 1024,
        'timestamp': time.time()
    })
```

### Log Management

#### Centralized Logging Setup
```bash
# Install ELK Stack (Elasticsearch, Logstash, Kibana)
wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add -
echo "deb https://artifacts.elastic.co/packages/8.x/apt stable main" | sudo tee /etc/apt/sources.list.d/elastic-8.x.list
sudo apt-get update

# Install Elasticsearch
sudo apt-get install elasticsearch

# Install Logstash
sudo apt-get install logstash

# Install Kibana
sudo apt-get install kibana
```

#### Configure Application Logging
```python
# Enhanced logging configuration
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
            
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
            
        return json.dumps(log_entry)

# Configure logger
def setup_logging(app):
    handler = logging.FileHandler('/var/log/hotgigs/app.log')
    handler.setFormatter(JSONFormatter())
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)
```

## 💾 Backup and Recovery

### Automated Backup System

#### Database Backup Script
```bash
#!/bin/bash
# /opt/scripts/backup-system.sh

# Configuration
BACKUP_DIR="/var/backups/hotgigs"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Database backup
echo "Starting database backup..."
pg_dump -U hotgigs_prod_user -h localhost hotgigs_prod | gzip > "$BACKUP_DIR/db_backup_$DATE.sql.gz"

# Application files backup
echo "Starting application files backup..."
tar -czf "$BACKUP_DIR/app_backup_$DATE.tar.gz" /var/www/hotgigs /opt/hotgigs

# Upload logs backup
echo "Starting uploads backup..."
tar -czf "$BACKUP_DIR/uploads_backup_$DATE.tar.gz" /app/uploads

# Clean old backups
echo "Cleaning old backups..."
find $BACKUP_DIR -name "*_backup_*.gz" -mtime +$RETENTION_DAYS -delete

# Upload to S3 (optional)
if [ ! -z "$AWS_S3_BUCKET" ]; then
    echo "Uploading to S3..."
    aws s3 cp "$BACKUP_DIR/db_backup_$DATE.sql.gz" "s3://$AWS_S3_BUCKET/backups/"
    aws s3 cp "$BACKUP_DIR/app_backup_$DATE.tar.gz" "s3://$AWS_S3_BUCKET/backups/"
    aws s3 cp "$BACKUP_DIR/uploads_backup_$DATE.tar.gz" "s3://$AWS_S3_BUCKET/backups/"
fi

echo "Backup completed successfully!"
```

#### Recovery Procedures
```bash
#!/bin/bash
# /opt/scripts/restore-database.sh

# Usage: ./restore-database.sh backup_file.sql.gz

if [ $# -eq 0 ]; then
    echo "Usage: $0 <backup_file.sql.gz>"
    exit 1
fi

BACKUP_FILE=$1

# Stop application
sudo systemctl stop hotgigs-backend

# Drop and recreate database
sudo -u postgres psql -c "DROP DATABASE IF EXISTS hotgigs_prod;"
sudo -u postgres psql -c "CREATE DATABASE hotgigs_prod OWNER hotgigs_prod_user;"

# Restore database
gunzip -c $BACKUP_FILE | sudo -u postgres psql hotgigs_prod

# Start application
sudo systemctl start hotgigs-backend

echo "Database restored successfully!"
```

## 📈 Scaling Considerations

### Horizontal Scaling

#### Load Balancer Configuration
```nginx
# /etc/nginx/conf.d/upstream.conf
upstream hotgigs_backend {
    least_conn;
    server 127.0.0.1:5002 weight=1 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:5003 weight=1 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:5004 weight=1 max_fails=3 fail_timeout=30s;
}

server {
    # ... SSL configuration ...
    
    location /api/ {
        proxy_pass http://hotgigs_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Health checks
        proxy_next_upstream error timeout invalid_header http_500 http_502 http_503 http_504;
    }
}
```

#### Auto-scaling with Docker Swarm
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  backend:
    image: hotgigs-backend:latest
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
    networks:
      - hotgigs-network

  frontend:
    image: hotgigs-frontend:latest
    deploy:
      replicas: 2
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
    networks:
      - hotgigs-network

networks:
  hotgigs-network:
    driver: overlay
```

### Database Scaling

#### Read Replicas Setup
```bash
# Master database configuration
# /etc/postgresql/15/main/postgresql.conf
wal_level = replica
max_wal_senders = 3
wal_keep_segments = 64
archive_mode = on
archive_command = 'cp %p /var/lib/postgresql/15/main/archive/%f'

# /etc/postgresql/15/main/pg_hba.conf
host replication replicator 192.168.1.0/24 md5
```

#### Connection Pooling
```python
# Database connection pooling
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

# Master database (read/write)
master_engine = create_engine(
    MASTER_DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600
)

# Read replica (read-only)
replica_engine = create_engine(
    REPLICA_DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600
)

class DatabaseManager:
    def get_read_engine(self):
        return replica_engine
    
    def get_write_engine(self):
        return master_engine
```

## 🔧 Troubleshooting

### Common Deployment Issues

#### Issue: Backend Not Starting
```bash
# Check logs
docker-compose logs backend

# Common solutions:
# 1. Database connection issues
export DATABASE_URL=postgresql://user:pass@host:5432/db
python -c "from src.models.database import db; print('DB connection OK')"

# 2. Missing dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# 3. Port conflicts
sudo netstat -tlnp | grep :5002
sudo kill -9 <PID>
```

#### Issue: Frontend Build Failures
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install

# Check Node.js version
node --version  # Should be 18+

# Build with verbose output
npm run build -- --verbose

# Check environment variables
echo $VITE_API_BASE_URL
```

#### Issue: Database Connection Errors
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test connection
psql -h localhost -U hotgigs_user -d hotgigs -c "SELECT 1;"

# Check firewall
sudo ufw status
sudo ufw allow 5432/tcp

# Check PostgreSQL configuration
sudo nano /etc/postgresql/15/main/pg_hba.conf
# Add: host all all 0.0.0.0/0 md5
```

#### Issue: SSL Certificate Problems
```bash
# Renew Let's Encrypt certificate
sudo certbot renew

# Check certificate validity
openssl x509 -in /etc/letsencrypt/live/hotgigs.com/fullchain.pem -text -noout

# Test SSL configuration
curl -I https://hotgigs.com
```

### Performance Issues

#### High Memory Usage
```bash
# Monitor memory usage
htop
free -h

# Check for memory leaks
ps aux --sort=-%mem | head

# Optimize Python memory
export PYTHONOPTIMIZE=1
export PYTHONDONTWRITEBYTECODE=1
```

#### Slow Database Queries
```sql
-- Enable query logging
ALTER SYSTEM SET log_statement = 'all';
ALTER SYSTEM SET log_min_duration_statement = 1000;
SELECT pg_reload_conf();

-- Analyze slow queries
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

-- Add missing indexes
CREATE INDEX CONCURRENTLY idx_jobs_created_at ON jobs(created_at DESC);
```

### Monitoring and Alerts

#### System Health Monitoring
```bash
#!/bin/bash
# /opt/scripts/health-check.sh

# Check disk space
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "WARNING: Disk usage is ${DISK_USAGE}%"
fi

# Check memory usage
MEMORY_USAGE=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
if [ $MEMORY_USAGE -gt 80 ]; then
    echo "WARNING: Memory usage is ${MEMORY_USAGE}%"
fi

# Check application health
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5002/api/health)
if [ $HTTP_STATUS -ne 200 ]; then
    echo "ERROR: Application health check failed (HTTP $HTTP_STATUS)"
fi
```

---

## 🎯 Quick Reference

### Essential Commands

```bash
# Start development environment
docker-compose up -d

# View logs
docker-compose logs -f backend

# Restart services
docker-compose restart backend

# Update application
git pull
docker-compose build
docker-compose up -d

# Backup database
pg_dump -U user -h host database > backup.sql

# Restore database
psql -U user -h host database < backup.sql

# Check application health
curl http://localhost:5002/api/health

# Monitor resources
htop
docker stats
```

### Environment URLs

- **Development**: http://localhost:5173
- **Staging**: https://staging.hotgigs.com
- **Production**: https://hotgigs.com
- **API**: https://api.hotgigs.com

### Support Contacts

- **Technical Issues**: tech@hotgigs.com
- **Deployment Support**: devops@hotgigs.com
- **Emergency**: +1-800-HOTGIGS

---

*This deployment guide is regularly updated. For the latest version and additional resources, visit our documentation portal.*

**Last Updated**: June 30, 2025  
**Version**: 1.0  
**Maintainer**: DevOps Team

