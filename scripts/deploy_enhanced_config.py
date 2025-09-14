#!/usr/bin/env python3
"""
Enhanced Configuration Integration Deployment Script
Deploys enhanced microservices with complete settings.py and ml_config.yaml integration
"""
import subprocess
import json
import time
import os
import sys
import shutil
from pathlib import Path
from typing import Dict, List

class EnhancedConfigurationDeployment:
    """Deploy enhanced microservices with comprehensive configuration integration"""

    def __init__(self):
        self.enhanced_services = [
            "enhanced-config",
            "enhanced-market-data", 
            "enhanced-ml-model",
            "enhanced-news-scraper",
            "enhanced-sentiment",
            "enhanced-prediction"
        ]
        
        self.original_services = [
            "market-data",
            "ml-model", 
            "sentiment",
            "prediction"
        ]
        
        self.config_files = [
            "app/config/settings.py",
            "app/config/ml_config.yaml",
            "settings.py",
            "ml_config.yaml"
        ]

    def verify_configuration_files(self) -> Dict[str, bool]:
        """Verify that configuration files exist"""
        config_status = {}
        
        for config_file in self.config_files:
            config_status[config_file] = os.path.exists(config_file)
            
        print("Configuration Files Status:")
        for file, exists in config_status.items():
            status = "✅ Found" if exists else "❌ Missing"
            print(f"  {status}: {file}")
        
        return config_status

    def create_enhanced_systemd_services(self):
        """Create systemd service files for enhanced services"""
        systemd_dir = Path("/etc/systemd/system")
        
        # Enhanced Configuration Service
        enhanced_config_service = """[Unit]
Description=Enhanced Trading Configuration Service
Documentation=file:///opt/trading_services/ENHANCED_CONFIG_INTEGRATION.md
After=network.target redis.service
Wants=redis.service
Requires=network.target

[Service]
Type=simple
User=trading
Group=trading
WorkingDirectory=/opt/trading_services
Environment=PYTHONPATH=/opt/trading_services
Environment=PYTHONUNBUFFERED=1
ExecStart=/opt/trading_venv/bin/python services/config/enhanced_configuration_service.py
ExecStop=/bin/kill -TERM $MAINPID
TimeoutStopSec=30
Restart=always
RestartSec=5
StartLimitInterval=300
StartLimitBurst=5

# Resource limits
MemoryMax=256M
CPUQuota=50%
TasksMax=25

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=enhanced-config

# Security
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/log/trading /tmp/trading_sockets

[Install]
WantedBy=multi-user.target
"""

        # Enhanced Market Data Service
        enhanced_market_data_service = """[Unit]
Description=Enhanced Trading Market Data Service
Documentation=file:///opt/trading_services/ENHANCED_CONFIG_INTEGRATION.md
After=network.target enhanced-config.service
Wants=enhanced-config.service
Requires=network.target

[Service]
Type=simple
User=trading
Group=trading
WorkingDirectory=/opt/trading_services
Environment=PYTHONPATH=/opt/trading_services
Environment=PYTHONUNBUFFERED=1
ExecStart=/opt/trading_venv/bin/python services/market-data/enhanced_market_data_service.py
ExecStop=/bin/kill -TERM $MAINPID
TimeoutStopSec=30
Restart=always
RestartSec=5
StartLimitInterval=300
StartLimitBurst=5

# Resource limits
MemoryMax=512M
CPUQuota=100%
TasksMax=50

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=enhanced-market-data

# Security
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/log/trading /tmp/trading_sockets

[Install]
WantedBy=multi-user.target
"""

        # Enhanced ML Model Service
        enhanced_ml_service = """[Unit]
Description=Enhanced Trading ML Model Service
Documentation=file:///opt/trading_services/ENHANCED_CONFIG_INTEGRATION.md
After=network.target enhanced-config.service
Wants=enhanced-config.service
Requires=network.target

[Service]
Type=simple
User=trading
Group=trading
WorkingDirectory=/opt/trading_services
Environment=PYTHONPATH=/opt/trading_services
Environment=PYTHONUNBUFFERED=1
ExecStart=/opt/trading_venv/bin/python services/ml-model/enhanced_ml_model_service.py
ExecStop=/bin/kill -TERM $MAINPID
TimeoutStopSec=30
Restart=always
RestartSec=5
StartLimitInterval=300
StartLimitBurst=5

# Resource limits
MemoryMax=1G
CPUQuota=150%
TasksMax=75

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=enhanced-ml-model

# Security
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/log/trading /tmp/trading_sockets /opt/trading_services/models

[Install]
WantedBy=multi-user.target
"""

        service_files = {
            "enhanced-config.service": enhanced_config_service,
            "enhanced-market-data.service": enhanced_market_data_service,
            "enhanced-ml-model.service": enhanced_ml_service
        }

        print("Creating enhanced systemd service files...")
        
        for service_name, service_content in service_files.items():
            service_path = f"/tmp/{service_name}"  # Write to tmp first for safety
            
            with open(service_path, 'w') as f:
                f.write(service_content)
            
            print(f"✅ Created {service_path}")
        
        print("📝 Service files created in /tmp/. Copy to /etc/systemd/system/ with:")
        print("   sudo cp /tmp/enhanced-*.service /etc/systemd/system/")
        print("   sudo systemctl daemon-reload")

    def create_deployment_validation_script(self):
        """Create script to validate enhanced configuration integration"""
        validation_script = '''#!/usr/bin/env python3
"""
Enhanced Configuration Integration Validation Script
Tests that all configuration files are properly integrated
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.base_service import BaseService

async def test_configuration_integration():
    """Test that enhanced configuration service works correctly"""
    print("🔍 Testing Enhanced Configuration Integration...")
    
    try:
        # Create test service client
        test_client = BaseService("config-test-client")
        
        # Test enhanced config service
        print("\\n1. Testing Enhanced Configuration Service...")
        
        # Test settings.py integration
        settings_config = await test_client.call_service("enhanced-config", "get_settings")
        if settings_config and "BANK_SYMBOLS" in settings_config:
            print("   ✅ settings.py integration working")
            print(f"   📊 Found {len(settings_config.get('BANK_SYMBOLS', []))} bank symbols")
        else:
            print("   ❌ settings.py integration failed")
        
        # Test ml_config.yaml integration
        ml_config = await test_client.call_service("enhanced-config", "get_ml_config")
        if ml_config and ("models" in ml_config or "model_settings" in ml_config):
            print("   ✅ ml_config.yaml integration working")
            if "enhanced_models" in ml_config:
                print(f"   🤖 Found {len(ml_config['enhanced_models'])} enhanced model configs")
        else:
            print("   ❌ ml_config.yaml integration failed")
        
        # Test news sources configuration
        news_config = await test_client.call_service("enhanced-config", "get_news_sources")
        if news_config and "sources" in news_config:
            print("   ✅ News sources configuration working")
            print(f"   📰 Found {len(news_config['sources'])} news sources")
            if "quality_scores" in news_config:
                print(f"   ⭐ Quality scoring system configured")
        else:
            print("   ❌ News sources configuration failed")
        
        # Test bank profiles
        bank_profiles = await test_client.call_service("enhanced-config", "get_bank_profiles")
        if bank_profiles:
            print("   ✅ Bank profiles configuration working")
            print(f"   🏦 Found {len(bank_profiles)} bank profiles")
            
            # Check for enhanced profiles
            for symbol, profile in bank_profiles.items():
                if "technical_indicators" in profile:
                    print(f"   📈 Enhanced profile for {symbol} includes technical indicators")
                    break
        else:
            print("   ❌ Bank profiles configuration failed")
        
        print("\\n2. Testing Service Integration...")
        
        # Test market data service integration
        try:
            market_status = await test_client.call_service("enhanced-market-data", "get_market_status")
            if market_status and "config_loaded" in market_status:
                print(f"   ✅ Enhanced market data service: config_loaded={market_status['config_loaded']}")
            else:
                print("   ❌ Enhanced market data service not responding")
        except Exception as e:
            print(f"   ⚠️  Enhanced market data service not available: {e}")
        
        # Test ML model service integration
        try:
            ml_status = await test_client.call_service("enhanced-ml-model", "model_health_check")
            if ml_status and "config_loaded" in ml_status:
                print(f"   ✅ Enhanced ML model service: config_loaded={ml_status['config_loaded']}")
            else:
                print("   ❌ Enhanced ML model service not responding")
        except Exception as e:
            print(f"   ⚠️  Enhanced ML model service not available: {e}")
        
        print("\\n3. Configuration Validation Summary...")
        
        # Validate configuration completeness
        validation_result = await test_client.call_service("enhanced-config", "validate_config")
        if validation_result:
            print(f"   📋 Configuration validation completed")
            if validation_result.get("issues"):
                print(f"   ❌ Found {len(validation_result['issues'])} issues:")
                for issue in validation_result["issues"]:
                    print(f"      - {issue}")
            if validation_result.get("warnings"):
                print(f"   ⚠️  Found {len(validation_result['warnings'])} warnings:")
                for warning in validation_result["warnings"]:
                    print(f"      - {warning}")
            
            if not validation_result.get("issues") and not validation_result.get("warnings"):
                print("   ✅ All configuration validations passed!")
        
        print("\\n🎉 Enhanced Configuration Integration Test Complete!")
        
    except Exception as e:
        print(f"❌ Configuration integration test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(test_configuration_integration())
'''

        with open("scripts/validate_enhanced_config.py", 'w') as f:
            f.write(validation_script)
        
        # Make executable
        os.chmod("scripts/validate_enhanced_config.py", 0o755)
        
        print("✅ Created configuration validation script: scripts/validate_enhanced_config.py")

    def create_migration_guide(self):
        """Create migration guide for enhanced configuration"""
        migration_guide = """# Enhanced Configuration Integration Migration Guide

## Overview
This migration enhances your microservices to fully utilize the comprehensive configurations from:
- `settings.py` with NEWS_SOURCES, BANK_PROFILES, TECHNICAL_INDICATORS, etc.
- `ml_config.yaml` with model settings, performance thresholds, feature engineering

## Migration Steps

### 1. Deploy Enhanced Configuration Service
```bash
# Start the enhanced configuration service first
sudo systemctl start enhanced-config.service
sudo systemctl enable enhanced-config.service

# Verify it's working
sudo systemctl status enhanced-config.service
```

### 2. Deploy Enhanced Services
```bash
# Deploy enhanced market data service
sudo systemctl start enhanced-market-data.service
sudo systemctl enable enhanced-market-data.service

# Deploy enhanced ML model service  
sudo systemctl start enhanced-ml-model.service
sudo systemctl enable enhanced-ml-model.service
```

### 3. Validate Configuration Integration
```bash
# Run the validation script
python scripts/validate_enhanced_config.py

# Check service health
python scripts/service_manager.py health
```

### 4. Update Existing Services (Optional)
The enhanced services can run alongside existing services. To migrate:

```bash
# Stop old services
sudo systemctl stop market-data.service
sudo systemctl stop ml-model.service

# Start enhanced services
sudo systemctl start enhanced-market-data.service
sudo systemctl start enhanced-ml-model.service

# Update any dependent services to use enhanced- prefixes
```

## Configuration Files Integration

### settings.py Integration
- ✅ NEWS_SOURCES with 4-tier Australian financial sources
- ✅ BANK_PROFILES with dividend months and financial metrics  
- ✅ TECHNICAL_INDICATORS with RSI/MACD/Bollinger parameters
- ✅ MARKET_HOURS with ASX trading times
- ✅ RISK_PARAMETERS with volatility and volume thresholds

### ml_config.yaml Integration
- ✅ Model settings with training parameters
- ✅ Performance thresholds for model validation
- ✅ Feature engineering configuration
- ✅ Training configuration with cross-validation
- ✅ Model monitoring and retraining triggers

## Enhanced Features

### News Sources
- 4-tier quality scoring system (Government -> Financial Media -> Major Outlets -> Specialized)
- Update frequency configuration per tier
- Source quality scoring for weighted sentiment analysis

### Bank Profiles
- Technical indicator preferences per bank
- ML model preferences with weights
- Bank-specific prediction parameters
- Enhanced metadata with dividend and financial metrics

### ML Configuration
- Comprehensive model configuration from YAML
- Enhanced feature engineering with market context
- Performance monitoring and alerting
- Bank-specific model loading and preferences

## Validation Checklist

- [ ] Enhanced configuration service starts successfully
- [ ] Settings.py configurations are loaded
- [ ] ml_config.yaml configurations are loaded  
- [ ] News sources include all 4 tiers with quality scores
- [ ] Bank profiles include enhanced technical indicators
- [ ] ML models load with enhanced configuration
- [ ] All configuration validation passes
- [ ] Services can communicate with enhanced-config service

## Rollback Plan

If issues occur, revert to original services:
```bash
# Stop enhanced services
sudo systemctl stop enhanced-config.service
sudo systemctl stop enhanced-market-data.service
sudo systemctl stop enhanced-ml-model.service

# Start original services
sudo systemctl start market-data.service
sudo systemctl start ml-model.service
sudo systemctl start sentiment.service
sudo systemctl start prediction.service
```

## Performance Impact

### Resource Usage
- Enhanced Config Service: ~50MB RAM, minimal CPU
- Enhanced Market Data: Same as original + config caching
- Enhanced ML Model: +100MB RAM for enhanced model management

### Benefits
- Comprehensive configuration integration
- Better news source quality management
- Enhanced ML model configuration
- Bank-specific optimization
- Centralized configuration management
"""

        with open("ENHANCED_CONFIG_MIGRATION_GUIDE.md", 'w') as f:
            f.write(migration_guide)
        
        print("✅ Created migration guide: ENHANCED_CONFIG_MIGRATION_GUIDE.md")

    def run_deployment(self):
        """Run the complete enhanced configuration deployment"""
        print("🚀 Enhanced Configuration Integration Deployment")
        print("=" * 60)
        
        # 1. Verify configuration files
        print("\n1. Verifying Configuration Files...")
        config_status = self.verify_configuration_files()
        
        settings_available = any(config_status[f] for f in config_status if "settings.py" in f)
        ml_config_available = any(config_status[f] for f in config_status if "ml_config.yaml" in f)
        
        if not settings_available:
            print("⚠️  Warning: settings.py not found. Services will use fallback configuration.")
        
        if not ml_config_available:
            print("⚠️  Warning: ml_config.yaml not found. Services will use fallback configuration.")
        
        # 2. Create systemd service files
        print("\n2. Creating Enhanced Systemd Services...")
        self.create_enhanced_systemd_services()
        
        # 3. Create validation script
        print("\n3. Creating Validation Script...")
        os.makedirs("scripts", exist_ok=True)
        self.create_deployment_validation_script()
        
        # 4. Create migration guide
        print("\n4. Creating Migration Guide...")
        self.create_migration_guide()
        
        # 5. Final instructions
        print("\n" + "=" * 60)
        print("🎉 Enhanced Configuration Integration Deployment Complete!")
        print("\nNext Steps:")
        print("1. Copy systemd files: sudo cp /tmp/enhanced-*.service /etc/systemd/system/")
        print("2. Reload systemd: sudo systemctl daemon-reload")
        print("3. Start enhanced-config: sudo systemctl start enhanced-config.service")
        print("4. Start other enhanced services: sudo systemctl start enhanced-market-data.service")
        print("5. Validate: python scripts/validate_enhanced_config.py")
        print("\nDocumentation:")
        print("- Migration Guide: ENHANCED_CONFIG_MIGRATION_GUIDE.md")
        print("- Validation Script: scripts/validate_enhanced_config.py")

def main():
    deployment = EnhancedConfigurationDeployment()
    deployment.run_deployment()

if __name__ == "__main__":
    main()
