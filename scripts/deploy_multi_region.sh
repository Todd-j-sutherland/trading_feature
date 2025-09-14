#!/bin/bash
# Multi-Region Trading System Deployment Script
# Automated deployment for Ubuntu/Debian systems

set -e  # Exit on any error

echo "🚀 Starting Multi-Region Trading System Deployment"
echo "================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="/opt/trading_services"
LOG_DIR="/var/log/trading"
SOCKET_DIR="/tmp/trading_sockets"
VENV_DIR="/opt/trading_venv"
SERVICE_USER="trading"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_error "This script should not be run as root. Please run as a regular user with sudo privileges."
        exit 1
    fi
}

# Check system requirements
check_requirements() {
    print_step "Checking system requirements..."
    
    # Check Ubuntu/Debian
    if ! command -v apt &> /dev/null; then
        print_error "This script is designed for Ubuntu/Debian systems with apt package manager"
        exit 1
    fi
    
    # Check sudo access
    if ! sudo -n true 2>/dev/null; then
        print_error "This script requires sudo privileges"
        exit 1
    fi
    
    print_status "System requirements met"
}

# Install system dependencies
install_dependencies() {
    print_step "Installing system dependencies..."
    
    sudo apt update
    sudo apt install -y \
        python3 \
        python3-pip \
        python3-venv \
        redis-server \
        git \
        curl \
        systemd \
        psmisc \
        htop
    
    print_status "System dependencies installed"
}

# Create system user
create_user() {
    print_step "Creating trading service user..."
    
    if id "$SERVICE_USER" &>/dev/null; then
        print_warning "User $SERVICE_USER already exists"
    else
        sudo useradd -r -s /bin/bash -d $INSTALL_DIR $SERVICE_USER
        print_status "Created user: $SERVICE_USER"
    fi
}

# Setup directories
setup_directories() {
    print_step "Setting up directories..."
    
    # Create directories
    sudo mkdir -p $INSTALL_DIR
    sudo mkdir -p $LOG_DIR
    sudo mkdir -p $SOCKET_DIR
    sudo mkdir -p /etc/trading
    
    # Set ownership
    sudo chown -R $SERVICE_USER:$SERVICE_USER $INSTALL_DIR
    sudo chown -R $SERVICE_USER:$SERVICE_USER $LOG_DIR
    sudo chown -R $SERVICE_USER:$SERVICE_USER $SOCKET_DIR
    
    # Set permissions
    sudo chmod 755 $INSTALL_DIR
    sudo chmod 755 $LOG_DIR
    sudo chmod 777 $SOCKET_DIR  # Allow all services to create sockets
    
    print_status "Directories created and configured"
}

# Setup Python environment
setup_python_env() {
    print_step "Setting up Python virtual environment..."
    
    # Create virtual environment
    sudo -u $SERVICE_USER python3 -m venv $VENV_DIR
    
    # Install Python packages
    sudo -u $SERVICE_USER $VENV_DIR/bin/pip install --upgrade pip
    sudo -u $SERVICE_USER $VENV_DIR/bin/pip install \
        redis \
        aiofiles \
        psutil \
        numpy \
        pandas \
        scikit-learn \
        requests \
        beautifulsoup4 \
        feedparser \
        python-dateutil \
        pytz \
        asyncio \
        aiohttp
    
    print_status "Python environment configured"
}

# Copy application files
copy_application() {
    print_step "Copying application files..."
    
    # Copy application structure
    sudo -u $SERVICE_USER cp -r app/ $INSTALL_DIR/
    sudo -u $SERVICE_USER cp -r services/ $INSTALL_DIR/
    
    # Copy configuration files
    if [ -f "enhanced_efficient_system_market_aware.py" ]; then
        sudo -u $SERVICE_USER cp enhanced_efficient_system_market_aware.py $INSTALL_DIR/
    fi
    
    # Copy any additional Python files needed
    for file in *.py; do
        if [ -f "$file" ]; then
            sudo -u $SERVICE_USER cp "$file" $INSTALL_DIR/
        fi
    done
    
    print_status "Application files copied"
}

# Configure Redis
configure_redis() {
    print_step "Configuring Redis..."
    
    # Enable and start Redis
    sudo systemctl enable redis-server
    sudo systemctl start redis-server
    
    # Wait for Redis to start
    sleep 2
    
    # Test Redis connection
    if redis-cli ping | grep -q "PONG"; then
        print_status "Redis configured and running"
    else
        print_error "Redis configuration failed"
        exit 1
    fi
}

# Create systemd service files
create_systemd_services() {
    print_step "Creating systemd service files..."
    
    # Prediction Service
    sudo tee /etc/systemd/system/trading-prediction.service > /dev/null <<EOF
[Unit]
Description=Trading Prediction Service (Multi-Region)
Documentation=file://$INSTALL_DIR/COMPLETE_MULTI_REGION_IMPLEMENTATION_GUIDE.md
After=network.target redis.service
Wants=redis.service
Requires=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
Environment=PYTHONPATH=$INSTALL_DIR
Environment=PYTHONUNBUFFERED=1
Environment=TRADING_REGION=asx
ExecStart=$VENV_DIR/bin/python services/prediction/prediction_service.py
ExecStop=/bin/kill -TERM \$MAINPID
TimeoutStopSec=30
Restart=always
RestartSec=5
StartLimitInterval=300
StartLimitBurst=5

# Resource limits
MemoryMax=1G
CPUQuota=150%
TasksMax=100

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=trading-prediction

# Security
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$LOG_DIR $SOCKET_DIR

[Install]
WantedBy=multi-user.target
EOF

    # Market Data Service
    sudo tee /etc/systemd/system/trading-market-data.service > /dev/null <<EOF
[Unit]
Description=Trading Market Data Service (Multi-Region)
After=network.target redis.service
Wants=redis.service
Requires=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
Environment=PYTHONPATH=$INSTALL_DIR
Environment=PYTHONUNBUFFERED=1
Environment=TRADING_REGION=asx
ExecStart=$VENV_DIR/bin/python services/market-data/market_data_service.py
Restart=always
RestartSec=5
MemoryMax=512M
CPUQuota=100%
StandardOutput=journal
StandardError=journal
SyslogIdentifier=trading-market-data
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$LOG_DIR $SOCKET_DIR

[Install]
WantedBy=multi-user.target
EOF

    # Sentiment Service
    sudo tee /etc/systemd/system/trading-sentiment.service > /dev/null <<EOF
[Unit]
Description=Trading Sentiment Analysis Service (Multi-Region)
After=network.target redis.service
Wants=redis.service
Requires=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
Environment=PYTHONPATH=$INSTALL_DIR
Environment=PYTHONUNBUFFERED=1
Environment=TRADING_REGION=asx
ExecStart=$VENV_DIR/bin/python services/sentiment/sentiment_service.py
Restart=always
RestartSec=5
MemoryMax=512M
CPUQuota=100%
StandardOutput=journal
StandardError=journal
SyslogIdentifier=trading-sentiment
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$LOG_DIR $SOCKET_DIR

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd
    sudo systemctl daemon-reload
    
    print_status "Systemd services created"
}

# Enable services
enable_services() {
    print_step "Enabling services..."
    
    sudo systemctl enable trading-prediction
    sudo systemctl enable trading-market-data
    sudo systemctl enable trading-sentiment
    
    print_status "Services enabled"
}

# Create management scripts
create_management_scripts() {
    print_step "Creating management scripts..."
    
    # Main management script
    sudo tee /usr/local/bin/trading-manage > /dev/null <<'EOF'
#!/bin/bash
# Trading System Management Script

SERVICES=("trading-prediction" "trading-market-data" "trading-sentiment")

case "$1" in
    start)
        echo "Starting trading services..."
        for service in "${SERVICES[@]}"; do
            echo "Starting $service..."
            sudo systemctl start "$service"
        done
        echo "All services started"
        ;;
    stop)
        echo "Stopping trading services..."
        for service in "${SERVICES[@]}"; do
            echo "Stopping $service..."
            sudo systemctl stop "$service"
        done
        echo "All services stopped"
        ;;
    restart)
        echo "Restarting trading services..."
        for service in "${SERVICES[@]}"; do
            echo "Restarting $service..."
            sudo systemctl restart "$service"
        done
        echo "All services restarted"
        ;;
    status)
        echo "Trading services status:"
        for service in "${SERVICES[@]}"; do
            status=$(systemctl is-active "$service")
            if [ "$status" = "active" ]; then
                echo "✅ $service: $status"
            else
                echo "❌ $service: $status"
            fi
        done
        ;;
    logs)
        service_name="${2:-trading-prediction}"
        echo "Showing logs for $service_name..."
        sudo journalctl -u "$service_name" -f
        ;;
    health)
        echo "Health check for trading services..."
        for service in "${SERVICES[@]}"; do
            if systemctl is-active --quiet "$service"; then
                echo "✅ $service: Running"
            else
                echo "❌ $service: Not running"
            fi
        done
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs [service]|health}"
        echo "Available services: ${SERVICES[*]}"
        exit 1
        ;;
esac
EOF

    sudo chmod +x /usr/local/bin/trading-manage
    
    print_status "Management scripts created"
}

# Verification
verify_installation() {
    print_step "Verifying installation..."
    
    # Check directories
    if [ -d "$INSTALL_DIR" ] && [ -d "$LOG_DIR" ] && [ -d "$SOCKET_DIR" ]; then
        print_status "✅ Directories created successfully"
    else
        print_error "❌ Directory creation failed"
        return 1
    fi
    
    # Check Python environment
    if [ -f "$VENV_DIR/bin/python" ]; then
        print_status "✅ Python virtual environment created"
    else
        print_error "❌ Python environment creation failed"
        return 1
    fi
    
    # Check Redis
    if systemctl is-active --quiet redis-server; then
        print_status "✅ Redis service running"
    else
        print_error "❌ Redis service not running"
        return 1
    fi
    
    # Check systemd services
    for service in "trading-prediction" "trading-market-data" "trading-sentiment"; do
        if [ -f "/etc/systemd/system/$service.service" ]; then
            print_status "✅ $service systemd file created"
        else
            print_error "❌ $service systemd file missing"
            return 1
        fi
    done
    
    print_status "✅ Installation verification completed successfully"
}

# Start services
start_services() {
    print_step "Starting trading services..."
    
    # Start services in dependency order
    sudo systemctl start trading-market-data
    sleep 2
    sudo systemctl start trading-sentiment
    sleep 2
    sudo systemctl start trading-prediction
    
    # Wait for services to start
    sleep 5
    
    # Check service status
    echo ""
    echo "Service Status:"
    echo "==============="
    trading-manage status
    
    print_status "Services started"
}

# Main execution
main() {
    echo "Multi-Region Trading System Deployment"
    echo "======================================"
    echo "This script will:"
    echo "1. Install system dependencies"
    echo "2. Create service user and directories" 
    echo "3. Setup Python environment"
    echo "4. Configure Redis"
    echo "5. Copy application files"
    echo "6. Create systemd services"
    echo "7. Start services"
    echo ""
    
    read -p "Continue with deployment? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Deployment cancelled"
        exit 0
    fi
    
    check_root
    check_requirements
    install_dependencies
    create_user
    setup_directories
    setup_python_env
    configure_redis
    copy_application
    create_systemd_services
    enable_services
    create_management_scripts
    verify_installation
    start_services
    
    echo ""
    echo "🎉 Deployment completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Run 'trading-manage status' to check service status"
    echo "2. Run 'python3 validate_multi_region.py' to test functionality"
    echo "3. Check logs with 'trading-manage logs [service-name]'"
    echo "4. Monitor system with 'python3 scripts/multi_region_dashboard.py'"
    echo ""
    echo "Management commands:"
    echo "- trading-manage start     # Start all services"
    echo "- trading-manage stop      # Stop all services"
    echo "- trading-manage restart   # Restart all services"
    echo "- trading-manage status    # Show service status"
    echo "- trading-manage health    # Health check"
    echo "- trading-manage logs      # Show logs"
}

# Run main function
main "$@"
