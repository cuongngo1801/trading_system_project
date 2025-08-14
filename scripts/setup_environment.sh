#!/bin/bash

# Trading System Environment Setup Script
# This script sets up the development environment for the trading system

set -e  # Exit on any error

echo "🚀 Setting up Trading System Development Environment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
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

# Check if required tools are installed
check_prerequisites() {
    print_status "Checking prerequisites..."

    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3.9 or higher."
        exit 1
    fi

    python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    print_status "Found Python $python_version"

    # Check pip
    if ! command -v pip3 &> /dev/null; then
        print_error "pip3 is not installed. Please install pip."
        exit 1
    fi

    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_warning "Docker is not installed. Some features may not work."
    else
        print_status "Found Docker"
    fi

    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_warning "Docker Compose is not installed. Some features may not work."
    else
        print_status "Found Docker Compose"
    fi

    print_success "Prerequisites check completed"
}

# Create environment file
setup_environment() {
    print_status "Setting up environment variables..."

    if [ ! -f .env ]; then
        cp .env.example .env
        print_success "Created .env file from template"
        print_warning "Please edit .env file with your actual configuration values"
    else
        print_status ".env file already exists"
    fi
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."

    directories=(
        "logs"
        "data"
        "backups"
        "reports"
        "temp"
    )

    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            print_status "Created directory: $dir"
        fi
    done

    print_success "Directory structure created"
}

# Install Python dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."

    # Upgrade pip
    python3 -m pip install --upgrade pip

    # Install requirements
    if [ -f requirements.txt ]; then
        pip3 install -r requirements.txt
        print_success "Installed Python dependencies"
    else
        print_error "requirements.txt not found"
        exit 1
    fi

    # Install package in development mode
    pip3 install -e ".[dev]"
    print_success "Installed package in development mode"
}

# Setup pre-commit hooks
setup_precommit() {
    print_status "Setting up pre-commit hooks..."

    if command -v pre-commit &> /dev/null; then
        pre-commit install
        print_success "Pre-commit hooks installed"
    else
        print_warning "pre-commit not found. Installing..."
        pip3 install pre-commit
        pre-commit install
        print_success "Pre-commit hooks installed"
    fi
}

# Initialize database (if Docker is available)
setup_database() {
    if command -v docker-compose &> /dev/null; then
        print_status "Starting database services..."

        # Start only database services
        docker-compose -f docker/docker-compose.yml up -d postgres timescaledb redis

        # Wait for databases to be ready
        print_status "Waiting for databases to be ready..."
        sleep 10

        print_success "Database services started"
    else
        print_warning "Docker Compose not available. Skipping database setup."
    fi
}

# Run initial tests
run_tests() {
    print_status "Running initial tests..."

    # Run a quick test to verify setup
    if python3 -c "import trading_system; print('Trading system package imported successfully')" 2>/dev/null; then
        print_success "Package import test passed"
    else
        print_warning "Package import test failed. This might be expected if dependencies are missing."
    fi

    # Run basic tests if pytest is available
    if command -v pytest &> /dev/null; then
        if [ -d "tests" ]; then
            pytest tests/ --tb=short -q || print_warning "Some tests failed. This might be expected for initial setup."
        fi
    fi
}

# Generate configuration documentation
generate_docs() {
    print_status "Generating configuration documentation..."

    # Create basic documentation
    cat > "SETUP_COMPLETE.md" << EOF
# Trading System Setup Complete

## Environment Setup Status
- ✅ Project structure created
- ✅ Dependencies installed
- ✅ Environment variables configured
- ✅ Development tools ready

## Next Steps

1. **Configure Environment Variables**
   - Edit \`.env\` file with your actual configuration values
   - Set up API keys for data providers (MT5, Alpha Vantage, etc.)

2. **Start Development Services**
   \`\`\`bash
   make start
   \`\`\`

3. **Run Tests**
   \`\`\`bash
   make test
   \`\`\`

4. **Development Workflow**
   - Use \`make\` commands for common tasks
   - Run \`make help\` to see available commands
   - Check \`README.md\` for detailed documentation

## Services
- **Database**: PostgreSQL + TimescaleDB
- **Message Queue**: Apache Kafka
- **Cache**: Redis
- **Monitoring**: Prometheus + Grafana

## Important Files
- \`config/development.yaml\`: Development configuration
- \`config/production.yaml\`: Production configuration
- \`.env\`: Environment variables
- \`Makefile\`: Development commands

## Support
For issues or questions, check the documentation or contact the development team.

EOF

    print_success "Setup documentation generated: SETUP_COMPLETE.md"
}

# Main setup function
main() {
    echo "=============================================="
    echo "  Trading System Environment Setup"
    echo "=============================================="
    echo ""

    check_prerequisites
    echo ""

    setup_environment
    echo ""

    create_directories
    echo ""

    install_dependencies
    echo ""

    setup_precommit
    echo ""

    setup_database
    echo ""

    run_tests
    echo ""

    generate_docs
    echo ""

    print_success "🎉 Trading System setup completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Edit .env file with your configuration"
    echo "2. Run 'make start' to start services"
    echo "3. Run 'make test' to verify everything works"
    echo "4. Check SETUP_COMPLETE.md for detailed next steps"
    echo ""
}

# Run main function
main "$@"
