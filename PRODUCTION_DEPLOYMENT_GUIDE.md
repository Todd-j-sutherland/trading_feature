# Trading Microservices - Production Deployment Guide

## Quick Start Production Deployment

This guide provides step-by-step instructions for deploying the enhanced trading microservices to production.

## Prerequisites

### System Requirements
- **Operating System**: Ubuntu 20.04+ or CentOS 8+
- **Memory**: 4GB minimum, 8GB recommended
- **CPU**: 2 cores minimum, 4 cores recommended
- **Storage**: 20GB minimum, 50GB recommended
- **Network**: Stable internet connection

### Software Dependencies
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y redis-server python3 python3-pip python3-venv git sqlite3

# Install system monitoring tools
sudo apt install -y htop iotop nethogs
```

## Step 1: Environment Setup

### 1.1 Create Trading User
```bash
# Create dedicated user for trading services
sudo useradd -m -s /bin/bash trading
sudo usermod -aG sudo trading

# Switch to trading user
sudo su - trading
```

### 1.2 Setup Python Environment
```bash
# Create virtual environment
python3 -m venv /opt/trading_venv
source /opt/trading_venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install core dependencies
pip install redis asyncio aiofiles aiohttp psutil requests beautifulsoup4 sqlite3-utils
pip install pandas numpy scikit-learn python-dateutil pytz
```

### 1.3 Configure Redis
```bash
# Configure Redis for production
sudo cp /etc/redis/redis.conf /etc/redis/redis.conf.backup

# Update Redis configuration
sudo tee /etc/redis/redis.conf << EOF
# Memory and performance settings
maxmemory 1gb
maxmemory-policy allkeys-lru
timeout 300

# Persistence settings
save 900 1
save 300 10
save 60 10000

# Security settings
requirepass your_redis_password_here
bind 127.0.0.1

# Logging
loglevel notice
logfile /var/log/redis/redis-server.log

# Performance tuning
tcp-keepalive 300
tcp-backlog 511
databases 16
EOF

# Restart Redis
sudo systemctl restart redis-server
sudo systemctl enable redis-server

# Verify Redis is running
redis-cli ping
```

## Step 2: Service Deployment

### 2.1 Clone and Setup Repository
```bash
# Clone the repository (assuming you have your code ready)
cd /opt
sudo git clone your-trading-repo.git trading_services
sudo chown -R trading:trading /opt/trading_services

# Set up directories
sudo mkdir -p /var/log/trading /tmp/trading_sockets
sudo chown trading:trading /var/log/trading /tmp/trading_sockets
sudo chmod 755 /var/log/trading /tmp/trading_sockets
```

### 2.2 Install Python Dependencies
```bash
cd /opt/trading_services
source /opt/trading_venv/bin/activate

# Install requirements (create if needed)
cat > requirements.txt << EOF
redis>=4.5.0
aiofiles>=23.0.0
aiohttp>=3.8.0
psutil>=5.9.0
requests>=2.28.0
beautifulsoup4>=4.11.0
pandas>=1.5.0
numpy>=1.24.0
scikit-learn>=1.2.0
python-dateutil>=2.8.0
pytz>=2023.3
sqlite3-utils>=3.34
asyncio-mqtt>=0.13.0
pydantic>=1.10.0
cryptography>=40.0.0
EOF

pip install -r requirements.txt
```

### 2.3 Deploy Services
```bash
# Use the deployment manager
cd /opt/trading_services
source /opt/trading_venv/bin/activate

# Deploy all services
python tools/deployment_manager.py --deploy --environment production

# Or deploy manually with systemd files
sudo cp config/systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload
```

## Step 3: Service Configuration

### 3.1 Create Production Configuration
```bash
# Create production configuration
cat > /opt/trading_services/config/production.json << EOF
{
  "environment": "production",
  "redis": {
    "url": "redis://localhost:6379/0",
    "password": "your_redis_password_here",
    "max_connections": 10,
    "retry_attempts": 3
  },
  "databases": {
    "trading_predictions": "/opt/trading_services/data/trading_predictions.db",
    "paper_trading": "/opt/trading_services/data/paper_trading.db",
    "sentiment_analysis": "/opt/trading_services/data/sentiment_analysis.db"
  },
  "services": {
    "socket_base_path": "/tmp/trading_",
    "timeout": 30,
    "retry_attempts": 3,
    "max_connections": 50
  },
  "logging": {
    "level": "INFO",
    "file": "/var/log/trading/trading.log",
    "max_size": "100MB",
    "backup_count": 5
  },
  "security": {
    "hmac_secret": "your_hmac_secret_here",
    "rate_limit": {
      "requests_per_minute": 100,
      "burst_size": 20
    },
    "audit_logging": true
  },
  "performance": {
    "cache_ttl": 1800,
    "connection_pool_size": 10,
    "memory_limit_mb": 512,
    "cpu_limit_percent": 80
  },
  "external_apis": {
    "alpha_vantage": {
      "api_key": "your_alpha_vantage_key",
      "rate_limit": 5
    },
    "news_api": {
      "api_key": "your_news_api_key",
      "rate_limit": 100
    }
  }
}
EOF

# Set secure permissions
chmod 600 /opt/trading_services/config/production.json
```

### 3.2 Setup Environment Variables
```bash
# Create environment file for services
sudo tee /etc/environment << EOF
# Trading Services Environment
TRADING_ENV=production
TRADING_CONFIG=/opt/trading_services/config/production.json
PYTHONPATH=/opt/trading_services
TRADING_LOG_LEVEL=INFO
EOF

# Source environment
source /etc/environment
```

## Step 4: Start Services

### 4.1 Enable and Start Services
```bash
# Enable all trading services
sudo systemctl enable trading-market-data
sudo systemctl enable trading-sentiment
sudo systemctl enable trading-prediction
sudo systemctl enable trading-scheduler
sudo systemctl enable trading-paper-trading
sudo systemctl enable trading-monitoring

# Start services in dependency order
sudo systemctl start trading-market-data
sleep 5
sudo systemctl start trading-sentiment
sleep 5
sudo systemctl start trading-prediction
sleep 5
sudo systemctl start trading-scheduler
sudo systemctl start trading-paper-trading
sudo systemctl start trading-monitoring
```

### 4.2 Verify Service Status
```bash
# Check all service status
cd /opt/trading_services
python scripts/service_manager.py status

# Check individual services
sudo systemctl status trading-prediction
sudo systemctl status trading-market-data

# Check service health
python scripts/service_manager.py health
```

## Step 5: Validation & Testing

### 5.1 Run Health Checks
```bash
cd /opt/trading_services
source /opt/trading_venv/bin/activate

# Run comprehensive health check
python tests/run_all_tests.py --types integration

# Test individual service communication
python -c "
import asyncio
from services.base_service import BaseService

async def test():
    service = BaseService('test-client')
    result = await service.call_service('prediction', 'health')
    print('Prediction service health:', result)

asyncio.run(test())
"
```

### 5.2 Performance Validation
```bash
# Run performance tests
python tests/test_performance.py

# Monitor system resources
htop

# Check Redis status
redis-cli info memory
redis-cli info stats
```

### 5.3 Generate Test Predictions
```bash
# Test prediction generation
python -c "
import asyncio
from services.base_service import BaseService

async def test_prediction():
    service = BaseService('test-client')
    result = await service.call_service('prediction', 'generate_predictions', 
                                       symbols=['CBA.AX', 'ANZ.AX'])
    print('Predictions generated:', result['status'])
    print('BUY rate:', result['result']['summary']['buy_rate'], '%')

asyncio.run(test_prediction())
"
```

## Step 6: Monitoring Setup

### 6.1 Start Monitoring Dashboard
```bash
# Start monitoring service (if not already started)
sudo systemctl start trading-monitoring

# Access monitoring dashboard
python services/monitoring_service.py --dashboard

# View real-time status
python scripts/service_manager.py dashboard
```

### 6.2 Setup Log Monitoring
```bash
# Monitor service logs
sudo tail -f /var/log/trading/*.log

# Monitor specific service
sudo journalctl -u trading-prediction -f

# Setup log rotation
sudo tee /etc/logrotate.d/trading << EOF
/var/log/trading/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 trading trading
    postrotate
        systemctl reload trading-* || true
    endscript
}
EOF
```

## Step 7: Security Hardening

### 7.1 Firewall Configuration
```bash
# Configure UFW firewall
sudo ufw enable
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH
sudo ufw allow ssh

# Allow Redis (local only)
sudo ufw allow from 127.0.0.1 to any port 6379

# Allow specific ports if needed for external access
# sudo ufw allow 8080/tcp  # For monitoring dashboard
```

### 7.2 Service Permissions
```bash
# Set proper file permissions
sudo chown -R trading:trading /opt/trading_services
sudo chmod -R 755 /opt/trading_services
sudo chmod 600 /opt/trading_services/config/production.json

# Set socket permissions
sudo chown -R trading:trading /tmp/trading_sockets
sudo chmod 755 /tmp/trading_sockets
```

## Step 8: Backup Configuration

### 8.1 Setup Automated Backups
```bash
# Create backup script
sudo tee /opt/trading_services/scripts/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/trading_services/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup databases
cp /opt/trading_services/data/*.db $BACKUP_DIR/
tar -czf $BACKUP_DIR/database_backup_$DATE.tar.gz $BACKUP_DIR/*.db

# Backup configurations
tar -czf $BACKUP_DIR/config_backup_$DATE.tar.gz /opt/trading_services/config/

# Clean old backups (keep 30 days)
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
EOF

chmod +x /opt/trading_services/scripts/backup.sh

# Setup cron job for automated backups
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/trading_services/scripts/backup.sh") | crontab -
```

## Step 9: Production Readiness Checklist

### ✅ Pre-Production Checklist

- [ ] **System Resources**
  - [ ] Adequate memory (4GB+)
  - [ ] Sufficient disk space (20GB+)
  - [ ] CPU capacity (2+ cores)
  - [ ] Network connectivity verified

- [ ] **Service Configuration**
  - [ ] Redis configured and running
  - [ ] All services deployed
  - [ ] Configuration files secured
  - [ ] Environment variables set

- [ ] **Security Setup**
  - [ ] Firewall configured
  - [ ] Service permissions set
  - [ ] HMAC secrets configured
  - [ ] API keys secured

- [ ] **Monitoring & Logging**
  - [ ] Log rotation configured
  - [ ] Monitoring dashboard accessible
  - [ ] Health checks passing
  - [ ] Alert notifications tested

- [ ] **Backup & Recovery**
  - [ ] Automated backups configured
  - [ ] Backup restoration tested
  - [ ] Recovery procedures documented

- [ ] **Testing & Validation**
  - [ ] All tests passing
  - [ ] Performance benchmarks met
  - [ ] Service communication verified
  - [ ] Prediction generation working

## Step 10: Go-Live & Operations

### 10.1 Final Go-Live Steps
```bash
# 1. Final system check
python tests/run_all_tests.py --quiet

# 2. Start all services
python scripts/service_manager.py start

# 3. Enable monitoring
python scripts/service_manager.py dashboard &

# 4. Verify predictions are generating
python -c "
import asyncio
from services.base_service import BaseService

async def final_test():
    service = BaseService('go-live-test')
    result = await service.call_service('prediction', 'generate_predictions')
    print('✅ System is live and generating predictions!')
    print(f'Generated {len(result[\"result\"][\"predictions\"])} predictions')

asyncio.run(final_test())
"
```

### 10.2 Post-Deployment Monitoring
```bash
# Monitor for first 24 hours
watch -n 30 'python scripts/service_manager.py health'

# Check system resources
watch -n 60 'free -h && df -h'

# Monitor logs for errors
sudo tail -f /var/log/trading/*.log | grep -i error
```

## Troubleshooting

### Common Issues

1. **Service Won't Start**
   ```bash
   # Check logs
   sudo journalctl -u trading-prediction -n 50
   
   # Check dependencies
   systemctl status redis-server
   
   # Verify permissions
   ls -la /tmp/trading_sockets/
   ```

2. **Redis Connection Issues**
   ```bash
   # Test Redis connectivity
   redis-cli ping
   
   # Check Redis logs
   sudo tail -f /var/log/redis/redis-server.log
   ```

3. **Performance Issues**
   ```bash
   # Monitor resources
   htop
   iotop -o
   
   # Check service performance
   python scripts/service_manager.py health
   ```

## Support & Maintenance

### Regular Maintenance Tasks

1. **Daily Checks**
   - Service health verification
   - Log review for errors
   - Performance monitoring

2. **Weekly Tasks**
   - Backup verification
   - Performance analysis
   - Security log review

3. **Monthly Tasks**
   - System updates
   - Performance optimization
   - Capacity planning review

### Emergency Procedures

1. **Service Restart**
   ```bash
   sudo systemctl restart trading-prediction
   ```

2. **Full System Restart**
   ```bash
   python scripts/service_manager.py stop
   sleep 10
   python scripts/service_manager.py start
   ```

3. **Emergency Shutdown**
   ```bash
   python tools/operational_runbooks.py emergency_shutdown
   ```

---

**Deployment Complete!** 🚀

Your trading microservices are now live and ready for production use. Monitor the system closely for the first 48 hours and refer to the operational runbooks for ongoing maintenance procedures.
