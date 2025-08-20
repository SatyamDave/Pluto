#!/bin/bash

# =============================================================================
# AI Identity Platform - Setup Script
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    local missing_deps=()
    
    # Check Node.js
    if ! command_exists node; then
        missing_deps+=("Node.js (v18+)")
    else
        NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
        if [ "$NODE_VERSION" -lt 18 ]; then
            missing_deps+=("Node.js (v18+) - current: v$(node --version)")
        fi
    fi
    
    # Check npm
    if ! command_exists npm; then
        missing_deps+=("npm")
    fi
    
    # Check Python
    if ! command_exists python3; then
        missing_deps+=("Python 3.11+")
    else
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
        if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]); then
            missing_deps+=("Python 3.11+ - current: $PYTHON_VERSION")
        fi
    fi
    
    # Check pip
    if ! command_exists pip3; then
        missing_deps+=("pip3")
    fi
    
    # Check Docker (optional)
    if ! command_exists docker; then
        print_warning "Docker not found. You'll need to install it for production deployment."
    fi
    
    # Check Docker Compose (optional)
    if ! command_exists docker-compose; then
        print_warning "Docker Compose not found. You'll need to install it for production deployment."
    fi
    
    # Report missing dependencies
    if [ ${#missing_deps[@]} -ne 0 ]; then
        print_error "Missing required dependencies:"
        for dep in "${missing_deps[@]}"; do
            echo "  - $dep"
        done
        echo ""
        print_error "Please install the missing dependencies and run this script again."
        exit 1
    fi
    
    print_success "All prerequisites are satisfied!"
}

# Function to setup environment
setup_environment() {
    print_status "Setting up environment..."
    
    # Copy environment template
    if [ ! -f .env.local ]; then
        cp env.example .env.local
        print_success "Created .env.local from template"
        print_warning "Please edit .env.local with your configuration values"
    else
        print_status ".env.local already exists"
    fi
    
    # Create necessary directories
    mkdir -p logs
    mkdir -p data
    mkdir -p nginx/ssl
    mkdir -p nginx/logs
    
    print_success "Environment setup complete!"
}

# Function to install dependencies
install_dependencies() {
    print_status "Installing dependencies..."
    
    # Install Node.js dependencies
    print_status "Installing Node.js dependencies..."
    npm install
    
    # Install Python dependencies for API
    print_status "Installing Python dependencies for API..."
    cd apps/api
    pip3 install -r requirements.txt
    cd ../..
    
    # Install Python dependencies for AI Engine
    print_status "Installing Python dependencies for AI Engine..."
    cd packages/ai-engine
    pip3 install -r requirements.txt
    cd ../..
    
    print_success "Dependencies installed successfully!"
}

# Function to setup database
setup_database() {
    print_status "Setting up database..."
    
    # Check if PostgreSQL is running
    if command_exists pg_isready; then
        if pg_isready -q; then
            print_status "PostgreSQL is running"
        else
            print_warning "PostgreSQL is not running. Please start it manually or use Docker."
        fi
    else
        print_warning "pg_isready not found. Please ensure PostgreSQL is running."
    fi
    
    # Generate Prisma client
    print_status "Generating Prisma client..."
    cd packages/database
    npx prisma generate
    cd ../..
    
    print_success "Database setup complete!"
}

# Function to build the project
build_project() {
    print_status "Building the project..."
    
    # Build Next.js app
    print_status "Building Next.js app..."
    cd apps/web
    npm run build
    cd ../..
    
    print_success "Project built successfully!"
}

# Function to start development servers
start_development() {
    print_status "Starting development servers..."
    
    # Start all services in development mode
    npm run dev &
    
    print_success "Development servers started!"
    echo ""
    print_status "Services are running at:"
    echo "  - Frontend: http://localhost:3000"
    echo "  - API: http://localhost:8000"
    echo "  - AI Engine: http://localhost:8001"
    echo "  - API Docs: http://localhost:8000/docs"
    echo ""
    print_warning "Press Ctrl+C to stop all services"
    
    # Wait for user to stop
    wait
}

# Function to show help
show_help() {
    echo "AI Identity Platform - Setup Script"
    echo ""
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  check       Check prerequisites only"
    echo "  env         Setup environment only"
    echo "  deps        Install dependencies only"
    echo "  db          Setup database only"
    echo "  build       Build project only"
    echo "  dev         Start development servers"
    echo "  all         Run complete setup (default)"
    echo "  help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0          # Run complete setup"
    echo "  $0 check    # Check prerequisites"
    echo "  $0 dev      # Start development servers"
}

# Main function
main() {
    echo "=============================================================================="
    echo "AI Identity Platform - Setup Script"
    echo "=============================================================================="
    echo ""
    
    # Parse command line arguments
    case "${1:-all}" in
        "check")
            check_prerequisites
            ;;
        "env")
            setup_environment
            ;;
        "deps")
            install_dependencies
            ;;
        "db")
            setup_database
            ;;
        "build")
            build_project
            ;;
        "dev")
            start_development
            ;;
        "all")
            check_prerequisites
            setup_environment
            install_dependencies
            setup_database
            build_project
            print_success "Setup complete! Run '$0 dev' to start development servers."
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
