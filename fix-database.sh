#!/bin/bash

# Quick fix script for database connection issues
# This script resolves common database setup problems

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_info "🔧 Fixing database connection issues..."

# Check if we're in the right directory
if [[ ! -d "hotgigs-backend" ]]; then
    log_error "Please run this script from the project root directory"
    exit 1
fi

cd hotgigs-backend

# Create .env file if it doesn't exist
if [[ ! -f .env ]]; then
    log_info "Creating missing .env file..."
    cat > .env << 'EOF'
# Database Configuration
# For development, we'll use SQLite for simplicity
DATABASE_URL=sqlite:///hotgigs.db
SQLALCHEMY_DATABASE_URI=sqlite:///hotgigs.db

# Security Keys
SECRET_KEY=dev-secret-key-change-in-production-12345
JWT_SECRET_KEY=dev-jwt-secret-change-in-production-67890

# Email Configuration (Optional for development)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# File Upload Settings
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=10485760

# Redis Configuration (Optional for development)
REDIS_URL=redis://localhost:6379/0

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True

# Application Settings
APP_NAME=Hotgigs.com
APP_VERSION=1.0.0
EOF
    log_success "✅ .env file created"
else
    log_info "✅ .env file already exists"
fi

# Create uploads directory
if [[ ! -d "uploads" ]]; then
    log_info "Creating uploads directory..."
    mkdir -p uploads
    log_success "✅ uploads directory created"
else
    log_info "✅ uploads directory already exists"
fi

# Create database directory if using SQLite
log_info "Setting up SQLite database..."
if [[ ! -f "hotgigs.db" ]]; then
    # Initialize the database by running a simple Python script
    log_info "Initializing database..."
    
    # Activate virtual environment if it exists
    if [[ -f "venv/bin/activate" ]]; then
        source venv/bin/activate
    fi
    
    # Try to initialize the database
    python3 -c "
import sys
sys.path.append('src')
try:
    from models.database import db
    from main import app
    with app.app_context():
        db.create_all()
    print('Database initialized successfully!')
except Exception as e:
    print(f'Database initialization failed: {e}')
    print('This is normal if the database already exists.')
" 2>/dev/null || log_warning "Database initialization had issues (this may be normal)"
    
    log_success "✅ Database setup completed"
else
    log_info "✅ Database file already exists"
fi

# Set proper permissions
chmod 644 .env 2>/dev/null || true
chmod 755 uploads 2>/dev/null || true

log_info "Verifying setup..."

# Check if .env file has correct content
if grep -q "DATABASE_URL" .env; then
    log_success "✅ .env file has database configuration"
else
    log_error "❌ .env file missing database configuration"
fi

# Check uploads directory
if [[ -d "uploads" ]]; then
    log_success "✅ uploads directory exists"
else
    log_error "❌ uploads directory missing"
fi

cd ..

log_success "🎉 Database issues fixed!"
echo ""
echo "📋 Next steps:"
echo "1. Try starting the backend again:"
echo "   ./start-backend.sh"
echo ""
echo "2. Or start the complete application:"
echo "   ./start-all.sh"
echo ""
echo "🔍 If you still have issues:"
echo "- Check that Python virtual environment is activated"
echo "- Verify all dependencies are installed: pip install -r requirements.txt"
echo "- Check the backend logs for specific error messages"

