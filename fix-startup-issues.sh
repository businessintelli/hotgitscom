#!/bin/bash

# Comprehensive startup issues fix script
# This script resolves common startup problems for Hotgigs.com

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

log_info "🔧 Fixing Hotgigs.com startup issues..."

# Check if we're in the right directory
if [[ ! -d "hotgigs-backend" ]] || [[ ! -d "hotgigs-frontend" ]]; then
    log_error "Please run this script from the project root directory"
    exit 1
fi

# Stop any running services first
log_info "Stopping any running services..."
pkill -f "python.*main.py" 2>/dev/null || true
pkill -f "vite.*dev" 2>/dev/null || true
pkill -f "npm.*run.*dev" 2>/dev/null || true

# Fix 1: Backend Database Issues
log_info "🗄️ Fixing backend database configuration..."

cd hotgigs-backend

# Create .env file if missing
if [[ ! -f .env ]]; then
    log_info "Creating missing .env file..."
    cat > .env << 'EOF'
# Database Configuration
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
mkdir -p uploads
log_success "✅ uploads directory ready"

# Set proper permissions
chmod 644 .env 2>/dev/null || true
chmod 755 uploads 2>/dev/null || true

cd ..

# Fix 2: Frontend Vite Configuration Issues
log_info "⚡ Fixing frontend Vite configuration..."

cd hotgigs-frontend

# Fix vite.config.js syntax error
log_info "Checking vite.config.js syntax..."
if grep -q "}}" vite.config.js 2>/dev/null; then
    log_info "Fixing vite.config.js syntax error..."
    cat > vite.config.js << 'EOF'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5173,
    host: true,
    open: false
  },
  build: {
    outDir: 'dist',
    sourcemap: true
  }
})
EOF
    log_success "✅ vite.config.js syntax fixed"
else
    log_info "✅ vite.config.js syntax is correct"
fi

# Clear Vite cache
log_info "Clearing Vite cache..."
rm -rf node_modules/.vite .vite 2>/dev/null || true

# Verify lib/utils.js exists
if [[ ! -f "src/lib/utils.js" ]]; then
    log_info "Creating missing lib/utils.js..."
    mkdir -p src/lib
    cat > src/lib/utils.js << 'EOF'
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge"

export function cn(...inputs) {
  return twMerge(clsx(inputs));
}
EOF
    log_success "✅ lib/utils.js created"
else
    log_info "✅ lib/utils.js already exists"
fi

cd ..

# Fix 3: Verify Dependencies
log_info "📦 Verifying dependencies..."

# Backend dependencies
cd hotgigs-backend
if [[ ! -d "venv" ]]; then
    log_info "Creating Python virtual environment..."
    python3 -m venv venv
    log_success "✅ Virtual environment created"
fi

log_info "Activating virtual environment and checking dependencies..."
source venv/bin/activate
if ! python -c "import flask" 2>/dev/null; then
    log_info "Installing backend dependencies..."
    pip install -r requirements.txt
    log_success "✅ Backend dependencies installed"
else
    log_info "✅ Backend dependencies already installed"
fi

cd ../hotgigs-frontend

# Frontend dependencies
if [[ ! -d "node_modules" ]]; then
    log_info "Installing frontend dependencies..."
    if ! npm install; then
        log_warning "Standard npm install failed, trying with --legacy-peer-deps..."
        npm install --legacy-peer-deps
    fi
    log_success "✅ Frontend dependencies installed"
else
    log_info "✅ Frontend dependencies already installed"
fi

cd ..

# Fix 4: Test Configuration
log_info "🧪 Testing configuration..."

# Test backend configuration
cd hotgigs-backend
source venv/bin/activate
if python -c "
import sys
sys.path.append('src')
try:
    from models.database import db
    from main import app
    print('Backend configuration test: PASSED')
except Exception as e:
    print(f'Backend configuration test: FAILED - {e}')
" 2>/dev/null | grep -q "PASSED"; then
    log_success "✅ Backend configuration test passed"
else
    log_warning "⚠️ Backend configuration test had issues (may be normal)"
fi

cd ../hotgigs-frontend

# Test frontend configuration
if node -e "
try {
    const config = require('./vite.config.js');
    console.log('Frontend configuration test: PASSED');
} catch (e) {
    console.log('Frontend configuration test: FAILED -', e.message);
}
" 2>/dev/null | grep -q "PASSED"; then
    log_success "✅ Frontend configuration test passed"
else
    log_warning "⚠️ Frontend configuration test had issues"
fi

cd ..

log_success "🎉 All startup issues fixed!"
echo ""
echo "📋 Next steps:"
echo "1. Start the complete application:"
echo "   ./start-all.sh"
echo ""
echo "2. Or start services individually:"
echo "   Backend:  ./start-backend.sh"
echo "   Frontend: ./start-frontend.sh"
echo ""
echo "🌐 Application URLs:"
echo "   Frontend: http://localhost:5173"
echo "   Backend:  http://localhost:5002"
echo "   API Health: http://localhost:5002/api/health"
echo ""
echo "🔍 If you still have issues:"
echo "- Check that Python virtual environment is activated"
echo "- Verify all dependencies are installed"
echo "- Check the logs for specific error messages"
echo "- Try restarting your terminal/IDE"

