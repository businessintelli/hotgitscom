#!/bin/bash

# Hotgigs.com - Stop All Services Script
# This script stops all running Hotgigs.com services and related processes

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

log_info "🛑 Stopping Hotgigs.com Services..."

# Function to kill processes by name
kill_process() {
    local process_name="$1"
    local description="$2"
    
    local pids=$(pgrep -f "$process_name" 2>/dev/null || true)
    
    if [[ -n "$pids" ]]; then
        log_info "Stopping $description..."
        echo "$pids" | xargs kill -TERM 2>/dev/null || true
        sleep 2
        
        # Force kill if still running
        local remaining_pids=$(pgrep -f "$process_name" 2>/dev/null || true)
        if [[ -n "$remaining_pids" ]]; then
            log_warning "Force killing $description..."
            echo "$remaining_pids" | xargs kill -KILL 2>/dev/null || true
        fi
        
        log_success "$description stopped"
    else
        log_info "$description not running"
    fi
}

# Function to stop services by port
kill_port() {
    local port="$1"
    local description="$2"
    
    local pid=$(lsof -ti:$port 2>/dev/null || true)
    
    if [[ -n "$pid" ]]; then
        log_info "Stopping $description on port $port..."
        kill -TERM $pid 2>/dev/null || true
        sleep 2
        
        # Force kill if still running
        local remaining_pid=$(lsof -ti:$port 2>/dev/null || true)
        if [[ -n "$remaining_pid" ]]; then
            log_warning "Force killing $description on port $port..."
            kill -KILL $remaining_pid 2>/dev/null || true
        fi
        
        log_success "$description stopped"
    else
        log_info "$description not running on port $port"
    fi
}

# Stop Hotgigs.com specific processes
log_info "Stopping Hotgigs.com application processes..."

# Stop backend processes
kill_process "python.*main.py" "Hotgigs Backend"
kill_process "python.*src/main.py" "Hotgigs Backend (alternative path)"
kill_process "flask.*run" "Flask Development Server"

# Stop frontend processes
kill_process "vite.*dev" "Vite Development Server"
kill_process "npm.*run.*dev" "NPM Development Server"
kill_process "node.*vite" "Node Vite Process"

# Stop by specific ports
kill_port "5000" "Backend API (port 5000)"
kill_port "5001" "Backend API (port 5001)"
kill_port "5002" "Backend API (port 5002)"
kill_port "5173" "Frontend Development Server"
kill_port "3000" "Alternative Frontend Server"

# Stop any Python processes in hotgigs directories
log_info "Stopping Python processes in hotgigs directories..."
kill_process "python.*hotgigs" "Hotgigs Python Processes"

# Stop any Node processes in hotgigs directories
log_info "Stopping Node processes in hotgigs directories..."
kill_process "node.*hotgigs" "Hotgigs Node Processes"

# Optional: Stop database and Redis services (commented out by default)
# Uncomment these lines if you want to stop PostgreSQL and Redis as well

# log_info "Stopping database services..."
# if command -v brew >/dev/null 2>&1; then
#     # macOS with Homebrew
#     brew services stop postgresql@15 2>/dev/null || brew services stop postgresql 2>/dev/null || true
#     brew services stop redis 2>/dev/null || true
#     log_info "Database services stopped (if they were running)"
# elif command -v systemctl >/dev/null 2>&1; then
#     # Linux with systemd
#     sudo systemctl stop postgresql 2>/dev/null || true
#     sudo systemctl stop redis 2>/dev/null || true
#     log_info "Database services stopped (if they were running)"
# fi

# Clean up any remaining processes
log_info "Cleaning up any remaining processes..."

# Kill any processes listening on our ports
for port in 5000 5001 5002 5173 3000; do
    kill_port "$port" "Process on port $port"
done

# Verify all processes are stopped
log_info "Verifying all services are stopped..."

# Check for any remaining Hotgigs processes
remaining_processes=$(ps aux | grep -E "(hotgigs|main\.py|vite.*dev)" | grep -v grep | grep -v "stop-all.sh" || true)

if [[ -n "$remaining_processes" ]]; then
    log_warning "Some processes may still be running:"
    echo "$remaining_processes"
    echo ""
    log_info "You can manually kill them with:"
    echo "  kill -9 <PID>"
else
    log_success "All Hotgigs.com services stopped successfully!"
fi

# Check port availability
log_info "Checking port availability..."
for port in 5000 5001 5002 5173; do
    if lsof -i:$port >/dev/null 2>&1; then
        log_warning "Port $port is still in use"
    else
        log_success "Port $port is available"
    fi
done

echo ""
log_success "🎉 Hotgigs.com services shutdown complete!"
echo ""
echo "📋 To restart services:"
echo "   ./start-all.sh"
echo ""
echo "🔍 To check running processes:"
echo "   ps aux | grep -E '(hotgigs|main\.py|vite)'"
echo ""
echo "🌐 To check port usage:"
echo "   lsof -i :5002 -i :5173"

