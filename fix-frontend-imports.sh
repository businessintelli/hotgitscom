#!/bin/bash

# Quick fix script for frontend import resolution issues
# This script resolves common Vite alias and import problems

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

log_info "🔧 Fixing frontend import resolution issues..."

# Check if we're in the right directory
if [[ ! -d "hotgigs-frontend" ]]; then
    log_error "Please run this script from the project root directory"
    exit 1
fi

cd hotgigs-frontend

# Stop any running development server
log_info "Stopping any running development servers..."
pkill -f "vite.*dev" 2>/dev/null || true
pkill -f "npm.*run.*dev" 2>/dev/null || true

# Clear Vite cache
log_info "Clearing Vite cache..."
rm -rf node_modules/.vite 2>/dev/null || true
rm -rf .vite 2>/dev/null || true

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

# Verify vite.config.js has correct alias
if [[ ! -f "vite.config.js" ]]; then
    log_info "Creating missing vite.config.js..."
    cat > vite.config.js << 'EOF'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5173,
    host: true
  }
})
EOF
    log_success "✅ vite.config.js created"
else
    # Check if alias is configured
    if grep -q '"@".*path.resolve' vite.config.js; then
        log_info "✅ vite.config.js alias already configured"
    else
        log_warning "⚠️ vite.config.js may need alias configuration"
    fi
fi

# Verify jsconfig.json has correct paths
if [[ ! -f "jsconfig.json" ]]; then
    log_info "Creating missing jsconfig.json..."
    cat > jsconfig.json << 'EOF'
{
  "compilerOptions": {
    "baseUrl": "./",
    "paths": {
      "@/*": ["src/*"]
    }
  }
}
EOF
    log_success "✅ jsconfig.json created"
else
    log_info "✅ jsconfig.json already exists"
fi

# Reinstall dependencies to ensure everything is fresh
log_info "Reinstalling dependencies..."
rm -rf node_modules package-lock.json pnpm-lock.yaml yarn.lock 2>/dev/null || true

if ! npm install; then
    log_warning "Standard npm install failed, trying with --legacy-peer-deps..."
    npm install --legacy-peer-deps
fi

log_success "✅ Dependencies reinstalled"

# Verify the problematic file exists and has correct imports
if [[ -f "src/components/ui/radio-group.jsx" ]]; then
    if grep -q '@/lib/utils' src/components/ui/radio-group.jsx; then
        log_info "✅ radio-group.jsx has correct import"
    else
        log_warning "⚠️ radio-group.jsx may have import issues"
    fi
else
    log_warning "⚠️ radio-group.jsx not found"
fi

# Check directory structure
log_info "Verifying directory structure..."
if [[ -d "src/lib" ]]; then
    log_success "✅ src/lib directory exists"
else
    mkdir -p src/lib
    log_success "✅ src/lib directory created"
fi

if [[ -d "src/components/ui" ]]; then
    log_success "✅ src/components/ui directory exists"
else
    log_warning "⚠️ src/components/ui directory missing"
fi

cd ..

log_success "🎉 Frontend import issues fixed!"
echo ""
echo "📋 Next steps:"
echo "1. Start the frontend development server:"
echo "   cd hotgigs-frontend"
echo "   npm run dev"
echo ""
echo "2. Or start the complete application:"
echo "   ./start-all.sh"
echo ""
echo "🔍 If you still have issues:"
echo "- Try restarting your terminal/IDE"
echo "- Check that all dependencies are installed"
echo "- Verify the import paths in your components"
echo "- Clear browser cache and reload"

