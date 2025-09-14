# Multi-Region Trading System - Quick Start Guide

This guide provides step-by-step instructions for deploying the multi-region trading microservices system on a new Ubuntu/Debian machine.

## Prerequisites

- Ubuntu 20.04+ or Debian 11+ server
- Minimum 4GB RAM (8GB recommended)
- 20GB+ available disk space
- Root or sudo access
- Internet connection for package downloads

## Quick Deployment (5 Minutes)

### Step 1: Transfer Files to Target Machine

```bash
# On source machine (where files are prepared)
tar -czf trading_multi_region.tar.gz \
  scripts/ \
  services/ \
  app/config/ \
  validate_multi_region.py \
  multi_region_manager.py \
  QUICK_START_MULTI_REGION.md \
  requirements.txt

scp trading_multi_region.tar.gz user@target-server:~/

# On target machine
cd ~
tar -xzf trading_multi_region.tar.gz
cd trading_feature  # or your extracted directory
```

### Step 2: Run Automated Deployment

```bash
# Make deployment script executable
chmod +x scripts/deploy_multi_region.sh

# Run automated deployment (will prompt for sudo password)
./scripts/deploy_multi_region.sh

# This script will:
# - Install all system dependencies (Redis, Python, systemd tools)
# - Create trading user and directories
# - Set up Python virtual environment
# - Install Python packages
# - Deploy all microservices as systemd services
# - Configure Redis for multi-region support
# - Start all services
# - Run initial validation tests
```

### Step 3: Verify Deployment

```bash
# Check service status
sudo systemctl status trading-*

# Run comprehensive validation
python3 validate_multi_region.py

# Start management dashboard
python3 multi_region_manager.py
```

If all services show "active (running)" and validation passes, your system is ready!

## Detailed Setup Instructions

### Manual Deployment Process

If you prefer manual control or the automated script fails:

#### 1. System Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y \
  redis-server \
  python3 \
  python3-pip \
  python3-venv \
  systemd \
  curl \
  wget \
  git \
  htop \
  sqlite3

# Verify Redis is running
sudo systemctl enable redis-server
sudo systemctl start redis-server
redis-cli ping  # Should return "PONG"
```

#### 2. User and Directory Setup

```bash
# Create trading user
sudo useradd -m -s /bin/bash trading
sudo usermod -aG sudo trading

# Create service directories
sudo mkdir -p /opt/trading_services
sudo mkdir -p /var/log/trading
sudo mkdir -p /tmp/trading_sockets
sudo mkdir -p /etc/trading

# Set permissions
sudo chown -R trading:trading /opt/trading_services
sudo chown -R trading:trading /var/log/trading
sudo chown -R trading:trading /tmp/trading_sockets
sudo chmod 755 /tmp/trading_sockets
```

#### 3. Python Environment Setup

```bash
# Switch to trading user
sudo su - trading

# Create Python virtual environment
cd /opt/trading_services
python3 -m venv trading_venv
source trading_venv/bin/activate

# Install Python packages
pip install --upgrade pip
pip install redis aiofiles psutil aiohttp requests pandas numpy scikit-learn beautifulsoup4 lxml

# Copy source files
cp -r ~/trading_feature/* /opt/trading_services/
```

#### 4. Service Configuration

```bash
# Copy systemd service files
sudo cp /opt/trading_services/scripts/systemd/*.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable services
sudo systemctl enable trading-market-data
sudo systemctl enable trading-sentiment  
sudo systemctl enable trading-prediction
sudo systemctl enable trading-ml-model
sudo systemctl enable trading-scheduler
sudo systemctl enable trading-paper-trading
```

#### 5. Start Services

```bash
# Start services in dependency order
sudo systemctl start trading-market-data
sleep 5
sudo systemctl start trading-sentiment
sleep 5
sudo systemctl start trading-prediction
sleep 5
sudo systemctl start trading-ml-model
sudo systemctl start trading-scheduler
sudo systemctl start trading-paper-trading

# Check all services are running
sudo systemctl status trading-*
```

## Post-Deployment Configuration

### 1. Region Configuration

```bash
# Switch to trading user and activate environment
sudo su - trading
cd /opt/trading_services
source trading_venv/bin/activate

# Test region switching
python3 -c "
from app.config.regions.config_manager import ConfigManager
cm = ConfigManager()
print('Current region:', cm.get_current_region())
print('Available regions:', cm.get_available_regions())

# Test switching regions
for region in ['ASX', 'USA', 'UK', 'EU']:
    cm.switch_region(region)
    print(f'Switched to {region}: {cm.get_current_region()}')
"
```

### 2. Initial Testing

```bash
# Test market data service
python3 -c "
import asyncio
from services.base.base_service import BaseService

async def test():
    service = BaseService('test')
    result = await service.call_service('market-data', 'health')
    print('Market Data Health:', result)
    
    result = await service.call_service('market-data', 'get_market_data', symbol='CBA.AX')
    print('Market Data Sample:', result)

asyncio.run(test())
"

# Test prediction service
python3 -c "
import asyncio
from services.base.base_service import BaseService

async def test():
    service = BaseService('test')
    result = await service.call_service('prediction', 'generate_single_prediction', symbol='CBA.AX')
    print('Prediction Sample:', result)

asyncio.run(test())
"
```

### 3. Configure Monitoring

```bash
# Run comprehensive validation
python3 validate_multi_region.py --output-format json > validation_report.json

# View validation results
cat validation_report.json | python3 -m json.tool

# Start monitoring dashboard (in screen/tmux session)
screen -S trading-monitor
python3 multi_region_manager.py
# Press Ctrl+A, D to detach from screen
```

## Daily Operations

### Service Management

```bash
# Check service status
sudo systemctl status trading-*

# Restart all services
sudo systemctl restart trading-*

# View service logs
sudo journalctl -u trading-prediction -f

# Stop all services
sudo systemctl stop trading-*

# Start all services
sudo systemctl start trading-*
```

### Region Switching

```bash
# Use management dashboard
python3 multi_region_manager.py
# Select option 4 (Switch Region) and choose target region

# Or use direct API calls
python3 -c "
import asyncio
from services.base.base_service import BaseService

async def switch_region():
    service = BaseService('admin')
    
    # Switch all services to USA region
    services = ['market-data', 'sentiment', 'prediction']
    for svc in services:
        result = await service.call_service(svc, 'switch_region', region='USA')
        print(f'{svc}: {result}')

asyncio.run(switch_region())
"
```

### Health Monitoring

```bash
# Quick health check
curl -X POST --unix-socket /tmp/trading_prediction.sock \
  -H "Content-Type: application/json" \
  -d '{"method": "health", "params": {}}' \
  http://localhost/

# Comprehensive validation
python3 validate_multi_region.py --quick

# Performance monitoring
htop  # System resources
sudo journalctl -u trading-* --since "1 hour ago"  # Recent logs
```

## Troubleshooting

### Common Issues

#### Services Won't Start

```bash
# Check logs
sudo journalctl -u trading-prediction -n 50

# Check socket permissions
ls -la /tmp/trading_*

# Check Python environment
sudo su - trading
cd /opt/trading_services
source trading_venv/bin/activate
python3 -c "import redis; print('Redis available')"
```

#### Redis Connection Issues

```bash
# Check Redis status
sudo systemctl status redis-server

# Test Redis connection
redis-cli ping

# Check Redis configuration
sudo cat /etc/redis/redis.conf | grep bind
```

#### Memory Issues

```bash
# Check memory usage
free -h
sudo systemctl status trading-*

# Reduce memory usage by stopping non-essential services
sudo systemctl stop trading-ml-model  # Temporarily if needed
```

#### Socket Permission Issues

```bash
# Fix socket permissions
sudo chown -R trading:trading /tmp/trading_sockets
sudo chmod 755 /tmp/trading_sockets
sudo systemctl restart trading-*
```

### Recovery Procedures

#### Complete Service Restart

```bash
# Stop all services
sudo systemctl stop trading-*

# Clear socket files
sudo rm -f /tmp/trading_*.sock

# Restart Redis
sudo systemctl restart redis-server

# Start services in order
sudo systemctl start trading-market-data
sleep 5
sudo systemctl start trading-sentiment
sleep 5
sudo systemctl start trading-prediction
sleep 5
sudo systemctl start trading-ml-model
sudo systemctl start trading-scheduler
sudo systemctl start trading-paper-trading

# Validate
python3 validate_multi_region.py
```

#### Reset to Clean State

```bash
# Stop all services
sudo systemctl stop trading-*

# Clear logs (optional)
sudo rm -f /var/log/trading/*.log

# Clear Redis data (caution: removes all cached data)
redis-cli FLUSHALL

# Restart all services
sudo systemctl start trading-*
```

## Performance Tuning

### Memory Optimization

```bash
# Edit service files to add memory limits
sudo systemctl edit trading-prediction
# Add:
# [Service]
# MemoryMax=512M

sudo systemctl daemon-reload
sudo systemctl restart trading-prediction
```

### CPU Optimization

```bash
# Limit CPU usage
sudo systemctl edit trading-ml-model
# Add:
# [Service]
# CPUQuota=50%

sudo systemctl daemon-reload
sudo systemctl restart trading-ml-model
```

## Advanced Configuration

### Custom Region Configuration

```bash
# Add custom region
cd /opt/trading_services/app/config/regions
cp asx.py custom.py

# Edit custom.py with your settings
nano custom.py

# Test custom region
python3 -c "
from app.config.regions.config_manager import ConfigManager
cm = ConfigManager()
cm.switch_region('CUSTOM')
print('Custom config loaded:', cm.get_config())
"
```

### API Integration

```bash
# Test external API connectivity
python3 -c "
import requests
# Test your API endpoints
print('API connectivity verified')
"
```

## Backup and Recovery

### Create Backup

```bash
# Create system backup
tar -czf trading_backup_$(date +%Y%m%d_%H%M%S).tar.gz \
  /opt/trading_services \
  /var/log/trading \
  /etc/systemd/system/trading-*.service

# Backup databases
sudo -u trading redis-cli BGSAVE
cp /var/lib/redis/dump.rdb trading_redis_backup_$(date +%Y%m%d_%H%M%S).rdb
```

### Restore from Backup

```bash
# Stop services
sudo systemctl stop trading-*

# Restore files
tar -xzf trading_backup_YYYYMMDD_HHMMSS.tar.gz -C /

# Restore Redis data
sudo systemctl stop redis-server
sudo cp trading_redis_backup_YYYYMMDD_HHMMSS.rdb /var/lib/redis/dump.rdb
sudo chown redis:redis /var/lib/redis/dump.rdb
sudo systemctl start redis-server

# Restart services
sudo systemctl start trading-*
```

## Security Considerations

### Service Security

```bash
# Ensure proper file permissions
sudo chown -R trading:trading /opt/trading_services
sudo chmod 750 /opt/trading_services
sudo chmod 640 /opt/trading_services/app/config/regions/*.py

# Secure Redis
sudo sed -i 's/^# requirepass/requirepass/' /etc/redis/redis.conf
sudo systemctl restart redis-server
```

### Network Security

```bash
# Configure firewall (if needed)
sudo ufw allow 22    # SSH
sudo ufw deny 6379   # Redis (internal only)
sudo ufw enable

# Monitor connections
sudo netstat -tulpn | grep redis
```

## Integration with Existing Systems

### Cron Job Migration

```bash
# Disable old cron jobs (backup first)
crontab -l > cron_backup.txt
crontab -r

# Services will handle scheduling via trading-scheduler service
sudo systemctl status trading-scheduler
```

### Database Migration

```bash
# The system will use existing databases in place
# Verify database access
sqlite3 trading_predictions.db "SELECT COUNT(*) FROM predictions;"
```

## Support and Monitoring

### Log Locations

- Service logs: `/var/log/trading/`
- System logs: `sudo journalctl -u trading-*`
- Redis logs: `/var/log/redis/redis-server.log`

### Monitoring Commands

```bash
# Service status overview
sudo systemctl status trading-* | grep -E "(Active|Main PID|Memory)"

# Resource usage
htop
df -h
free -h

# Network connectivity
sudo ss -tulpn | grep -E "(redis|trading)"
```

### Getting Help

1. Check logs: `sudo journalctl -u trading-prediction -f`
2. Run validation: `python3 validate_multi_region.py`
3. Use management dashboard: `python3 multi_region_manager.py`
4. Check system resources: `htop`, `free -h`, `df -h`

---

## Success Checklist

After deployment, verify these items:

- [ ] All services show "active (running)": `sudo systemctl status trading-*`
- [ ] Redis is accessible: `redis-cli ping`
- [ ] Socket files exist: `ls -la /tmp/trading_*.sock`
- [ ] Validation passes: `python3 validate_multi_region.py`
- [ ] Management dashboard works: `python3 multi_region_manager.py`
- [ ] Region switching works for all regions: ASX, USA, UK, EU
- [ ] Services can communicate: Test prediction generation
- [ ] Logs are being written: `ls -la /var/log/trading/`
- [ ] System resources are reasonable: Memory < 80%, CPU < 50%

When all items are checked, your multi-region trading system is ready for production use!
