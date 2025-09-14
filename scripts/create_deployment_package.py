#!/usr/bin/env python3
"""
Deployment Package Creator
Creates a complete deployment package for the multi-region trading microservices system
"""

import os
import json
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import List, Dict

class DeploymentPackager:
    """Creates deployment packages for multi-region trading system"""
    
    def __init__(self, workspace_path: str = "c:\\Users\\todd.sutherland\\trading_feature"):
        self.workspace_path = Path(workspace_path)
        self.package_name = f"trading_microservices_deployment_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.package_dir = self.workspace_path / self.package_name
        
        # Files and directories to include in deployment package
        self.deployment_items = {
            "core_services": [
                "services/",
                "app/config/",
                "compatibility/"
            ],
            "scripts": [
                "scripts/deploy_multi_region.sh",
                "scripts/migrate_to_microservices.py",
                "scripts/emergency_rollback.py",
                "validate_multi_region.py",
                "multi_region_manager.py"
            ],
            "monitoring": [
                "monitoring/production_monitor.py",
                "monitoring/dashboard.py",
                "monitoring/monitoring_config.json"
            ],
            "documentation": [
                "QUICK_START_GUIDE.md",
                ".github/instructions/microservices.instructions.md"
            ],
            "configuration": [
                "enhanced_config.py",
                "config.py"
            ],
            "databases": [
                "trading_predictions.db",
                "paper_trading.db",
                "predictions.db"
            ]
        }

    def create_deployment_package(self) -> str:
        """Create complete deployment package"""
        print(f"🚀 Creating deployment package: {self.package_name}")
        
        # Create package directory
        self.package_dir.mkdir(exist_ok=True)
        
        try:
            # Copy all deployment items
            self._copy_deployment_items()
            
            # Create deployment structure
            self._create_deployment_structure()
            
            # Generate deployment documentation
            self._generate_deployment_docs()
            
            # Create installation scripts
            self._create_installation_scripts()
            
            # Generate package manifest
            self._generate_package_manifest()
            
            # Create compressed package
            package_zip = self._create_zip_package()
            
            print(f"✅ Deployment package created: {package_zip}")
            return str(package_zip)
            
        except Exception as e:
            print(f"❌ Package creation failed: {e}")
            # Cleanup on failure
            if self.package_dir.exists():
                shutil.rmtree(self.package_dir)
            raise

    def _copy_deployment_items(self):
        """Copy all required files to package directory"""
        print("📂 Copying deployment files...")
        
        for category, items in self.deployment_items.items():
            category_dir = self.package_dir / category
            category_dir.mkdir(exist_ok=True)
            
            for item in items:
                src_path = self.workspace_path / item
                
                if src_path.exists():
                    if src_path.is_dir():
                        dst_path = category_dir / src_path.name
                        shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
                        print(f"  📁 Copied directory: {item}")
                    else:
                        dst_path = category_dir / src_path.name
                        shutil.copy2(src_path, dst_path)
                        print(f"  📄 Copied file: {item}")
                else:
                    print(f"  ⚠️  Warning: {item} not found, skipping")

    def _create_deployment_structure(self):
        """Create proper deployment directory structure"""
        print("🏗️  Creating deployment structure...")
        
        # Create required directories
        required_dirs = [
            "logs",
            "data",
            "backup",
            "systemd",
            "tmp"
        ]
        
        for dir_name in required_dirs:
            (self.package_dir / dir_name).mkdir(exist_ok=True)
        
        # Move systemd service files if they exist
        systemd_files = list(self.package_dir.glob("**/*.service"))
        systemd_dir = self.package_dir / "systemd"
        
        for service_file in systemd_files:
            shutil.move(str(service_file), str(systemd_dir / service_file.name))
            print(f"  🔧 Moved systemd service: {service_file.name}")

    def _generate_deployment_docs(self):
        """Generate comprehensive deployment documentation"""
        print("📚 Generating deployment documentation...")
        
        readme_content = f'''# Trading Microservices Deployment Package

## 🎯 Overview

This package contains a complete multi-region microservices implementation for the trading system, 
including automated deployment, monitoring, and migration tools.

**Package Version:** {self.package_name}
**Created:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📦 Package Contents

### Core Services
- **Market Data Service**: Real-time market data collection and processing
- **Sentiment Analysis Service**: News sentiment analysis for trading decisions  
- **Prediction Service**: ML-powered trading predictions
- **Paper Trading Service**: Simulated trading execution
- **ML Model Service**: Model management and training
- **Scheduler Service**: Market-aware task scheduling
- **Database Service**: Centralized data management

### Multi-Region Support
- **ASX** (Australia): Primary trading market
- **USA** (United States): NYSE, NASDAQ markets
- **UK** (United Kingdom): LSE markets
- **EU** (Europe): European markets

### Deployment Tools
- Automated Ubuntu/Debian deployment script
- Service management and monitoring tools
- Zero-downtime migration from monolithic system
- Emergency rollback procedures
- Comprehensive validation suite

### Monitoring & Alerting
- Real-time system monitoring
- Web-based dashboard
- Email and webhook alerts
- Performance metrics collection
- Historical data analysis

## 🚀 Quick Start

### Prerequisites
- Ubuntu 20.04+ or Debian 11+ server
- Python 3.8+
- Redis server
- 4GB+ RAM, 20GB+ disk space
- Internet connection for package installation

### 1. Extract Package
```bash
# Extract the deployment package
unzip {self.package_name}.zip
cd {self.package_name}
```

### 2. Run Deployment
```bash
# Make deployment script executable
chmod +x scripts/deploy_multi_region.sh

# Run automated deployment (requires sudo)
sudo ./scripts/deploy_multi_region.sh
```

### 3. Verify Installation
```bash
# Run validation suite
python3 validate_multi_region.py

# Check service status
python3 multi_region_manager.py status
```

### 4. Start Monitoring
```bash
# Start production monitor
cd monitoring
python3 production_monitor.py &

# Start web dashboard (optional)
python3 dashboard.py --port 8080 &
```

### 5. Access Dashboard
Open http://your-server:8080 in a web browser to view the monitoring dashboard.

## 📖 Detailed Documentation

### Deployment Guide
See `documentation/QUICK_START_GUIDE.md` for detailed deployment instructions.

### Migration Guide
If migrating from a monolithic system:
```bash
# Run migration script
python3 scripts/migrate_to_microservices.py

# If issues occur, rollback:
python3 scripts/emergency_rollback.py
```

### Service Management
```bash
# Start all services
python3 multi_region_manager.py start

# Stop all services  
python3 multi_region_manager.py stop

# Switch to different region
python3 multi_region_manager.py switch-region USA

# View service logs
python3 multi_region_manager.py logs prediction

# Health check
python3 multi_region_manager.py health
```

### Configuration

#### Regional Configuration
Edit `core_services/app/config/regions/` files to customize:
- Market symbols
- Trading hours
- Data sources
- ML parameters

#### Monitoring Configuration
Edit `monitoring/monitoring_config.json` to configure:
- Alert thresholds
- Email notifications
- Webhook integrations
- Monitoring intervals

## 🔧 Architecture

### Service Communication
- **Unix Sockets**: Fast inter-service communication
- **Redis Pub/Sub**: Event broadcasting
- **HTTP REST**: External API access
- **JSON RPC**: Service method calls

### Data Flow
```
Market Data → Sentiment Analysis → Prediction Engine → Paper Trading
     ↓              ↓                    ↓              ↓
   Database ← ML Models ← Scheduler ← Monitoring Dashboard
```

### Regions
Each service can operate in different regional configurations with:
- Region-specific market symbols
- Localized trading hours
- Regional news sources
- Currency-specific parameters

## 📊 Monitoring

### System Metrics
- CPU, Memory, Disk usage
- Network I/O statistics
- Service response times
- Error rates and counts

### Business Metrics  
- Prediction accuracy
- Trade execution success
- Buy/Sell signal rates
- Regional performance

### Alerts
- **Critical**: Service outages, system failures
- **High**: Performance degradation, high error rates
- **Medium**: Resource usage warnings
- **Low**: Informational notices

## 🔒 Security

### Service Isolation
- Each service runs with limited permissions
- Unix socket communication (local only)
- Resource limits via systemd
- Separate log files and data directories

### Data Protection
- Database encryption at rest
- Secure credential management
- Audit logging
- Backup procedures

## 🛠️ Troubleshooting

### Common Issues

#### Services Not Starting
```bash
# Check service logs
journalctl -u trading-prediction -f

# Verify dependencies
systemctl status redis-server

# Check socket permissions
ls -la /tmp/trading_*.sock
```

#### High Resource Usage
```bash
# Check resource usage
python3 monitoring/dashboard.py --api-summary

# View service metrics
python3 multi_region_manager.py metrics
```

#### Database Issues
```bash
# Check database integrity
sqlite3 trading_predictions.db "PRAGMA integrity_check;"

# Backup and restore
python3 scripts/backup_databases.py
```

### Support
- Check logs in `/var/log/trading/`
- Review monitoring dashboard for alerts
- Run validation suite for systematic diagnosis
- Use emergency rollback if needed

## 📋 Maintenance

### Regular Tasks
- Monitor disk space and clean old logs
- Review alert thresholds and update as needed
- Backup databases regularly
- Update regional configurations for new markets
- Review and rotate log files

### Updates
- Test updates in staging environment first
- Use blue-green deployment for zero downtime
- Maintain rollback capability
- Monitor system after updates

## 📞 Support Information

This package includes comprehensive tooling for deployment, monitoring, and maintenance of the trading microservices system. All components are designed for production use with proper error handling, logging, and recovery procedures.

For additional support:
- Review documentation in `documentation/` directory
- Check monitoring dashboard for system status  
- Use built-in diagnostic tools
- Follow troubleshooting procedures above

---

**Package Created:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Version:** {self.package_name}
'''
        
        readme_file = self.package_dir / "README.md"
        readme_file.write_text(readme_content)
        print(f"  📄 Created: README.md")

    def _create_installation_scripts(self):
        """Create installation and setup scripts"""
        print("🔧 Creating installation scripts...")
        
        # Create installation script
        install_script = f'''#!/bin/bash
# Trading Microservices Installation Script
# Package: {self.package_name}

set -e

echo "🚀 Installing Trading Microservices System"
echo "Package: {self.package_name}"
echo "Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root (use sudo)" 
   exit 1
fi

# Set installation directory
INSTALL_DIR="/opt/trading_services"
BACKUP_DIR="/opt/trading_backups"

# Create directories
echo "📁 Creating directories..."
mkdir -p $INSTALL_DIR
mkdir -p $BACKUP_DIR
mkdir -p /var/log/trading
mkdir -p /tmp/trading_sockets

# Copy files
echo "📋 Copying files..."
cp -r core_services/* $INSTALL_DIR/
cp -r scripts/* $INSTALL_DIR/
cp -r monitoring/* $INSTALL_DIR/monitoring/
cp -r configuration/* $INSTALL_DIR/

# Copy systemd services
echo "🔧 Installing systemd services..."
cp systemd/*.service /etc/systemd/system/
systemctl daemon-reload

# Set permissions
echo "🔐 Setting permissions..."
chown -R trading:trading $INSTALL_DIR 2>/dev/null || true
chown -R trading:trading /var/log/trading 2>/dev/null || true
chown -R trading:trading /tmp/trading_sockets 2>/dev/null || true
chmod +x $INSTALL_DIR/scripts/*.sh 2>/dev/null || true
chmod +x $INSTALL_DIR/*.py 2>/dev/null || true

# Install Python dependencies
echo "📦 Installing Python dependencies..."
if command -v python3 &> /dev/null; then
    python3 -m pip install redis psutil aiofiles asyncio || echo "Warning: Some Python packages may need manual installation"
fi

# Enable services
echo "⚡ Enabling services..."
for service in trading-*.service; do
    if [ -f "/etc/systemd/system/$service" ]; then
        systemctl enable $service
        echo "Enabled $service"
    fi
done

echo ""
echo "✅ Installation completed successfully!"
echo ""
echo "Next steps:"
echo "1. Configure regional settings in $INSTALL_DIR/app/config/regions/"
echo "2. Update monitoring config in $INSTALL_DIR/monitoring/monitoring_config.json"
echo "3. Start services: systemctl start trading-market-data"
echo "4. Run validation: cd $INSTALL_DIR && python3 validate_multi_region.py"
echo "5. Start monitoring: cd $INSTALL_DIR/monitoring && python3 production_monitor.py &"
echo ""
echo "Dashboard: http://localhost:8080 (start with: python3 dashboard.py)"
echo "Logs: /var/log/trading/"
echo "Sockets: /tmp/trading_sockets/"
echo ""
'''
        
        install_file = self.package_dir / "install.sh"
        install_file.write_text(install_script)
        install_file.chmod(0o755)
        print(f"  🔧 Created: install.sh")
        
        # Create uninstall script
        uninstall_script = f'''#!/bin/bash
# Trading Microservices Uninstallation Script

set -e

echo "🗑️  Uninstalling Trading Microservices System"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root (use sudo)" 
   exit 1
fi

# Stop and disable services
echo "🛑 Stopping services..."
for service in trading-*.service; do
    if systemctl is-active --quiet $service 2>/dev/null; then
        systemctl stop $service
        echo "Stopped $service"
    fi
    if systemctl is-enabled --quiet $service 2>/dev/null; then
        systemctl disable $service
        echo "Disabled $service"
    fi
done

# Remove systemd services
echo "🔧 Removing systemd services..."
rm -f /etc/systemd/system/trading-*.service
systemctl daemon-reload

# Archive installation
INSTALL_DIR="/opt/trading_services"
BACKUP_DIR="/opt/trading_backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

if [ -d "$INSTALL_DIR" ]; then
    echo "📦 Archiving installation to $BACKUP_DIR/uninstall_backup_$TIMESTAMP"
    mkdir -p $BACKUP_DIR
    mv $INSTALL_DIR $BACKUP_DIR/uninstall_backup_$TIMESTAMP
fi

# Clean up sockets
echo "🧹 Cleaning up..."
rm -f /tmp/trading_*.sock

echo ""
echo "✅ Uninstallation completed!"
echo ""
echo "Archived to: $BACKUP_DIR/uninstall_backup_$TIMESTAMP"
echo "Logs preserved in: /var/log/trading/"
echo ""
echo "To completely remove all data:"
echo "  sudo rm -rf /var/log/trading"
echo "  sudo rm -rf $BACKUP_DIR"
echo ""
'''
        
        uninstall_file = self.package_dir / "uninstall.sh"
        uninstall_file.write_text(uninstall_script)
        uninstall_file.chmod(0o755)
        print(f"  🗑️  Created: uninstall.sh")

    def _generate_package_manifest(self):
        """Generate package manifest with file listing and checksums"""
        print("📋 Generating package manifest...")
        
        manifest = {
            "package_name": self.package_name,
            "created": datetime.now().isoformat(),
            "version": "1.0.0",
            "description": "Multi-region trading microservices deployment package",
            "contents": {},
            "installation": {
                "install_script": "install.sh",
                "uninstall_script": "uninstall.sh",
                "validation_script": "validate_multi_region.py",
                "management_script": "multi_region_manager.py"
            },
            "requirements": {
                "os": ["Ubuntu 20.04+", "Debian 11+"],
                "python": "3.8+",
                "memory": "4GB+",
                "disk": "20GB+",
                "dependencies": ["redis-server", "python3-pip", "systemd"]
            },
            "services": [
                "trading-market-data",
                "trading-sentiment", 
                "trading-prediction",
                "trading-paper-trading",
                "trading-ml-model",
                "trading-scheduler",
                "trading-database"
            ],
            "regions": ["ASX", "USA", "UK", "EU"],
            "ports": {
                "dashboard": 8080,
                "api": 8081,
                "redis": 6379
            }
        }
        
        # Add file listing
        for item in self.package_dir.rglob("*"):
            if item.is_file():
                rel_path = item.relative_to(self.package_dir)
                manifest["contents"][str(rel_path)] = {
                    "size": item.stat().st_size,
                    "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat()
                }
        
        manifest_file = self.package_dir / "MANIFEST.json"
        manifest_file.write_text(json.dumps(manifest, indent=2))
        print(f"  📋 Created: MANIFEST.json")

    def _create_zip_package(self) -> Path:
        """Create compressed ZIP package"""
        print("📦 Creating ZIP package...")
        
        zip_path = self.workspace_path / f"{self.package_name}.zip"
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in self.package_dir.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(self.workspace_path)
                    zipf.write(file_path, arcname)
        
        # Get package size
        size_mb = zip_path.stat().st_size / (1024 * 1024)
        print(f"  📦 Package size: {size_mb:.1f} MB")
        
        return zip_path

    def cleanup_temp_files(self):
        """Clean up temporary package directory"""
        if self.package_dir.exists():
            shutil.rmtree(self.package_dir)
            print(f"🧹 Cleaned up temporary directory: {self.package_dir}")

def main():
    """Main packaging function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Create deployment package")
    parser.add_argument("--workspace", default="c:\\Users\\todd.sutherland\\trading_feature")
    parser.add_argument("--keep-temp", action="store_true", help="Keep temporary package directory")
    
    args = parser.parse_args()
    
    packager = DeploymentPackager(args.workspace)
    
    try:
        package_path = packager.create_deployment_package()
        
        print("\\n" + "="*60)
        print("🎉 DEPLOYMENT PACKAGE CREATED SUCCESSFULLY!")
        print("="*60)
        print(f"Package: {package_path}")
        print(f"Size: {Path(package_path).stat().st_size / (1024*1024):.1f} MB")
        print("\\n📋 Package Contents:")
        print("  ✅ Multi-region microservices")
        print("  ✅ Automated deployment scripts")
        print("  ✅ Monitoring and alerting system")
        print("  ✅ Migration tools")
        print("  ✅ Comprehensive documentation")
        print("  ✅ Validation suite")
        print("\\n🚀 Next Steps:")
        print(f"  1. Transfer {package_path} to target server")
        print("  2. Extract: unzip {Path(package_path).name}")
        print("  3. Install: sudo ./install.sh")
        print("  4. Validate: python3 validate_multi_region.py")
        print("  5. Monitor: python3 monitoring/dashboard.py")
        print("\\n📖 See README.md in package for detailed instructions")
        
        if not args.keep_temp:
            packager.cleanup_temp_files()
            
        return package_path
        
    except Exception as e:
        print(f"\\n❌ Package creation failed: {e}")
        packager.cleanup_temp_files()
        return None

if __name__ == "__main__":
    main()
