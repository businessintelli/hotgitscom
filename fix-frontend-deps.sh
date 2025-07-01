#!/bin/bash

# Quick fix script for frontend dependency issues
# This script resolves common npm dependency conflicts

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

log_info "🔧 Fixing frontend dependency issues..."

# Check if we're in the right directory
if [[ ! -d "hotgigs-frontend" ]]; then
    log_error "Please run this script from the project root directory"
    exit 1
fi

cd hotgigs-frontend

log_info "Cleaning existing dependencies..."
rm -rf node_modules package-lock.json pnpm-lock.yaml yarn.lock

log_info "Attempting to install dependencies..."

# Try different installation methods
if npm install; then
    log_success "✅ Dependencies installed successfully with npm install"
elif npm install --legacy-peer-deps; then
    log_success "✅ Dependencies installed successfully with --legacy-peer-deps"
elif npm install --force; then
    log_warning "⚠️ Dependencies installed with --force (may have conflicts)"
else
    log_error "❌ All installation methods failed"
    echo ""
    echo "Manual fix options:"
    echo "1. Try: npm install --legacy-peer-deps"
    echo "2. Try: npm install --force"
    echo "3. Check package.json for version conflicts"
    echo "4. Consider using yarn: yarn install"
    exit 1
fi

log_info "Verifying installation..."
if [[ -d "node_modules" ]] && [[ -f "package-lock.json" ]]; then
    log_success "🎉 Frontend dependencies fixed successfully!"
    echo ""
    echo "You can now run:"
    echo "  cd hotgigs-frontend"
    echo "  npm run dev"
else
    log_error "Installation verification failed"
    exit 1
fi

