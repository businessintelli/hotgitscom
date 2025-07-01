#!/bin/bash

# Hotgigs.com - macOS Local Development Setup Script
# This script sets up the complete development environment on macOS

set -e  # Exit on any error

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

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    log_error "This script is designed for macOS only!"
    exit 1
fi

log_info "🚀 Starting Hotgigs.com macOS Setup..."

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install Homebrew
install_homebrew() {
    if ! command_exists brew; then
        log_info "Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        
        # Add Homebrew to PATH for Apple Silicon Macs
        if [[ $(uname -m) == "arm64" ]]; then
            echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
            eval "$(/opt/homebrew/bin/brew shellenv)"
        fi
        
        log_success "Homebrew installed successfully!"
    else
        log_info "Homebrew already installed, updating..."
        brew update
    fi
}

# Function to install Python 3.11
install_python() {
    if ! command_exists python3.11; then
        log_info "Installing Python 3.11..."
        brew install python@3.11
        
        # Create symlink for python3.11
        if [[ $(uname -m) == "arm64" ]]; then
            ln -sf /opt/homebrew/bin/python3.11 /opt/homebrew/bin/python3.11
        else
            ln -sf /usr/local/bin/python3.11 /usr/local/bin/python3.11
        fi
        
        log_success "Python 3.11 installed successfully!"
    else
        log_info "Python 3.11 already installed"
    fi
    
    # Verify Python version
    python3.11 --version
}

# Function to install Node.js
install_nodejs() {
    if ! command_exists node; then
        log_info "Installing Node.js 18..."
        brew install node@18
        
        # Link Node.js 18
        brew link node@18 --force
        
        log_success "Node.js 18 installed successfully!"
    else
        local node_version=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
        if [[ $node_version -lt 18 ]]; then
            log_warning "Node.js version is less than 18, upgrading..."
            brew install node@18
            brew link node@18 --force
        else
            log_info "Node.js 18+ already installed"
        fi
    fi
    
    # Verify Node.js version
    node --version
    npm --version
}

# Function to install PostgreSQL
install_postgresql() {
    if ! command_exists psql; then
        log_info "Installing PostgreSQL 15..."
        brew install postgresql@15
        
        # Start PostgreSQL service
        brew services start postgresql@15
        
        # Add PostgreSQL to PATH
        if [[ $(uname -m) == "arm64" ]]; then
            echo 'export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"' >> ~/.zprofile
            export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"
        else
            echo 'export PATH="/usr/local/opt/postgresql@15/bin:$PATH"' >> ~/.bash_profile
            export PATH="/usr/local/opt/postgresql@15/bin:$PATH"
        fi
        
        log_success "PostgreSQL 15 installed successfully!"
    else
        log_info "PostgreSQL already installed"
        # Ensure PostgreSQL is running
        brew services start postgresql@15 2>/dev/null || true
    fi
}

# Function to install Redis
install_redis() {
    if ! command_exists redis-server; then
        log_info "Installing Redis..."
        brew install redis
        
        # Start Redis service
        brew services start redis
        
        log_success "Redis installed successfully!"
    else
        log_info "Redis already installed"
        # Ensure Redis is running
        brew services start redis 2>/dev/null || true
    fi
}

# Function to install additional dependencies
install_dependencies() {
    log_info "Installing additional dependencies..."
    
    # Install Git (usually pre-installed on macOS)
    if ! command_exists git; then
        brew install git
    fi
    
    # Install Tesseract for OCR
    if ! command_exists tesseract; then
        log_info "Installing Tesseract OCR..."
        brew install tesseract
        log_success "Tesseract OCR installed!"
    fi
    
    # Install curl and wget
    brew install curl wget
    
    log_success "Additional dependencies installed!"
}

# Function to setup database
setup_database() {
    log_info "Setting up PostgreSQL database..."
    
    # Wait for PostgreSQL to be ready
    sleep 3
    
    # Create database and user
    createdb hotgigs 2>/dev/null || log_warning "Database 'hotgigs' already exists"
    
    # Create user with password
    psql -d postgres -c "CREATE USER hotgigs_user WITH PASSWORD 'hotgigs_password';" 2>/dev/null || log_warning "User 'hotgigs_user' already exists"
    psql -d postgres -c "GRANT ALL PRIVILEGES ON DATABASE hotgigs TO hotgigs_user;" 2>/dev/null || true
    psql -d postgres -c "ALTER USER hotgigs_user CREATEDB;" 2>/dev/null || true
    
    log_success "Database setup completed!"
}

# Function to setup backend
setup_backend() {
    log_info "Setting up backend environment..."
    
    cd hotgigs-backend
    
    # Create virtual environment
    python3.11 -m venv venv
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install requirements
    if [[ -f requirements.txt ]]; then
        log_info "Installing Python dependencies..."
        pip install -r requirements.txt
        
        # Download spaCy model
        log_info "Downloading spaCy English model..."
        python -m spacy download en_core_web_sm
        
        log_success "Backend dependencies installed!"
        
        # Optional GPU setup
        log_info "For GPU acceleration (optional), run:"
        echo "   pip install -r requirements-gpu.txt"
    else
        log_error "requirements.txt not found in backend directory!"
        exit 1
    fi
    
    # Create .env file if it doesn't exist
    if [[ ! -f .env ]]; then
        log_info "Creating backend .env file..."
        cat > .env << EOF
# Database Configuration
DATABASE_URL=postgresql://hotgigs_user:hotgigs_password@localhost:5432/hotgigs
SQLALCHEMY_DATABASE_URI=postgresql://hotgigs_user:hotgigs_password@localhost:5432/hotgigs

# Security Keys
SECRET_KEY=dev-secret-key-change-in-production
JWT_SECRET_KEY=dev-jwt-secret-change-in-production

# Email Configuration (Optional for development)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# File Upload Settings
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=10485760

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Development Settings
FLASK_ENV=development
FLASK_DEBUG=True
EOF
        log_success "Backend .env file created!"
    fi
    
    # Initialize database
    log_info "Initializing database schema..."
    python -c "
from src.main import create_app
from src.models.database import db
app = create_app()
with app.app_context():
    db.create_all()
    print('Database schema initialized!')
" || log_warning "Database initialization failed - may already be initialized"
    
    cd ..
    log_success "Backend setup completed!"
}

# Function to setup frontend
setup_frontend() {
    log_info "Setting up frontend environment..."
    
    cd hotgigs-frontend
    
    # Install dependencies
    if [[ -f package.json ]]; then
        log_info "Installing Node.js dependencies..."
        
        # Clean any existing node_modules and lock files
        rm -rf node_modules package-lock.json pnpm-lock.yaml
        
        # Try npm install first
        if ! npm install; then
            log_warning "Standard npm install failed, trying with --legacy-peer-deps..."
            npm install --legacy-peer-deps
        fi
        
        log_success "Frontend dependencies installed!"
    else
        log_error "package.json not found in frontend directory!"
        exit 1
    fi
    
    # Create .env.local file if it doesn't exist
    if [[ ! -f .env.local ]]; then
        log_info "Creating frontend .env.local file..."
        cat > .env.local << EOF
# API Configuration
VITE_API_BASE_URL=http://localhost:5002
VITE_APP_NAME=Hotgigs.com
VITE_APP_VERSION=1.0.0

# Development Settings
VITE_NODE_ENV=development
EOF
        log_success "Frontend .env.local file created!"
    fi
    
    cd ..
    log_success "Frontend setup completed!"
}

# Function to create startup scripts
create_startup_scripts() {
    log_info "Creating startup scripts..."
    
    # Create start-backend.sh
    cat > start-backend.sh << 'EOF'
#!/bin/bash
echo "🚀 Starting Hotgigs Backend..."
cd hotgigs-backend
source venv/bin/activate
python src/main.py
EOF
    chmod +x start-backend.sh
    
    # Create start-frontend.sh
    cat > start-frontend.sh << 'EOF'
#!/bin/bash
echo "🚀 Starting Hotgigs Frontend..."
cd hotgigs-frontend
npm run dev
EOF
    chmod +x start-frontend.sh
    
    # Create start-all.sh
    cat > start-all.sh << 'EOF'
#!/bin/bash
echo "🚀 Starting Hotgigs.com Complete Application..."

# Function to cleanup on exit
cleanup() {
    echo "🛑 Shutting down services..."
    kill $(jobs -p) 2>/dev/null || true
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM EXIT

# Start backend in background
echo "Starting backend..."
cd hotgigs-backend
source venv/bin/activate
python src/main.py &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 5

# Start frontend in background
echo "Starting frontend..."
cd hotgigs-frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo "✅ Application started successfully!"
echo "📱 Frontend: http://localhost:5173"
echo "🔧 Backend: http://localhost:5002"
echo "📊 API Health: http://localhost:5002/api/health"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for background processes
wait
EOF
    chmod +x start-all.sh
    
    log_success "Startup scripts created!"
}

# Function to verify installation
verify_installation() {
    log_info "Verifying installation..."
    
    # Check Python
    if python3.11 --version >/dev/null 2>&1; then
        log_success "✅ Python 3.11: $(python3.11 --version)"
    else
        log_error "❌ Python 3.11 not found"
    fi
    
    # Check Node.js
    if node --version >/dev/null 2>&1; then
        log_success "✅ Node.js: $(node --version)"
    else
        log_error "❌ Node.js not found"
    fi
    
    # Check PostgreSQL
    if psql --version >/dev/null 2>&1; then
        log_success "✅ PostgreSQL: $(psql --version | head -n1)"
    else
        log_error "❌ PostgreSQL not found"
    fi
    
    # Check Redis
    if redis-server --version >/dev/null 2>&1; then
        log_success "✅ Redis: $(redis-server --version | head -n1)"
    else
        log_error "❌ Redis not found"
    fi
    
    # Check database connection
    if psql -d hotgigs -U hotgigs_user -c "SELECT 1;" >/dev/null 2>&1; then
        log_success "✅ Database connection successful"
    else
        log_warning "⚠️  Database connection failed - check credentials"
    fi
    
    # Check backend dependencies
    if [[ -f hotgigs-backend/venv/bin/activate ]]; then
        log_success "✅ Backend virtual environment created"
    else
        log_error "❌ Backend virtual environment not found"
    fi
    
    # Check frontend dependencies
    if [[ -d hotgigs-frontend/node_modules ]]; then
        log_success "✅ Frontend dependencies installed"
    else
        log_error "❌ Frontend dependencies not found"
    fi
}

# Function to display final instructions
display_instructions() {
    echo ""
    echo "🎉 Hotgigs.com macOS Setup Complete!"
    echo "========================================"
    echo ""
    echo "📋 Next Steps:"
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
    echo "👤 Demo Credentials:"
    echo "   Candidate: candidate@demo.com / password123"
    echo "   Recruiter: recruiter@demo.com / password123"
    echo ""
    echo "📚 Documentation:"
    echo "   User Guide: user_documentation.md"
    echo "   Technical Docs: technical_documentation.md"
    echo "   Deployment Guide: deployment_guide.md"
    echo ""
    echo "🔧 Troubleshooting:"
    echo "   - Check logs in terminal output"
    echo "   - Verify database is running: brew services list | grep postgresql"
    echo "   - Verify Redis is running: brew services list | grep redis"
    echo "   - Check port availability: lsof -i :5002 -i :5173"
    echo ""
    echo "Happy coding! 🚀"
}

# Main execution
main() {
    log_info "Starting Hotgigs.com macOS setup..."
    
    # Check for required directories
    if [[ ! -d "hotgigs-backend" ]] || [[ ! -d "hotgigs-frontend" ]]; then
        log_error "Backend or frontend directory not found. Please run this script from the project root."
        exit 1
    fi
    
    # Install dependencies
    install_homebrew
    install_python
    install_nodejs
    install_postgresql
    install_redis
    install_dependencies
    
    # Setup database
    setup_database
    
    # Setup application
    setup_backend
    setup_frontend
    
    # Create startup scripts
    create_startup_scripts
    
    # Verify installation
    verify_installation
    
    # Display final instructions
    display_instructions
}

# Run main function
main "$@"

