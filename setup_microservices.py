#!/usr/bin/env python3
"""
Microservices Setup and Initialization Script

Purpose:
This script sets up the complete microservices environment for the trading system,
including directory creation, permission setup, dependency installation, and
initial configuration. It prepares the system for microservices deployment.

Setup Tasks:
- Create required directories and set permissions
- Install Python dependencies for microservices
- Setup Redis configuration for inter-service communication
- Initialize databases and schemas
- Create service configuration files
- Setup logging directories and rotation
- Validate system requirements

Prerequisites:
- Python 3.8+ with pip
- Redis server installed
- SQLite3 available
- Unix-like environment with socket support

Usage:
python setup_microservices.py --install-deps --create-dirs --init-db --test

Options:
--install-deps: Install Python package dependencies
--create-dirs: Create required directories with proper permissions
--init-db: Initialize databases and schemas
--test: Run basic functionality tests
--redis-setup: Configure Redis for microservices
--full: Run complete setup (all options)

Integration:
- Works with service_manager.py for service lifecycle
- Prepares environment for all trading microservices
- Sets up monitoring and logging infrastructure
"""

import os
import sys
import subprocess
import sqlite3
import json
import argparse
from pathlib import Path
from datetime import datetime

class MicroservicesSetup:
    """Setup and initialization for trading microservices"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.services_dir = self.project_root / "services"
        self.logs_dir = Path("/var/log/trading")
        self.sockets_dir = Path("/tmp/trading_sockets")
        
        # Required directories
        self.required_dirs = [
            self.logs_dir,
            self.sockets_dir,
            self.project_root / "data",
            self.project_root / "models",
            self.project_root / "backups"
        ]
        
        # Python dependencies for microservices
        self.python_deps = [
            "redis>=4.0.0",
            "aiofiles>=0.8.0", 
            "psutil>=5.8.0",
            "pandas>=1.3.0",
            "numpy>=1.21.0",
            "yfinance>=0.1.70",
            "requests>=2.25.0",
            "pytz>=2021.1",
            "scikit-learn>=1.0.0"
        ]
        
        # Database schemas
        self.database_schemas = {
            "trading_predictions.db": [
                '''CREATE TABLE IF NOT EXISTS predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    prediction_date TEXT NOT NULL,
                    confidence REAL,
                    action TEXT,
                    technical_score REAL,
                    sentiment_score REAL,
                    volume_score REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )''',
                '''CREATE INDEX IF NOT EXISTS idx_predictions_symbol_date 
                   ON predictions(symbol, prediction_date)'''
            ],
            "paper_trading.db": [
                '''CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trade_id TEXT UNIQUE NOT NULL,
                    symbol TEXT NOT NULL,
                    action TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    price REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    status TEXT NOT NULL,
                    pnl REAL DEFAULT 0,
                    commission REAL DEFAULT 0,
                    signal_source TEXT,
                    confidence REAL
                )''',
                '''CREATE TABLE IF NOT EXISTS positions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    position_id TEXT UNIQUE NOT NULL,
                    symbol TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    entry_price REAL NOT NULL,
                    current_price REAL,
                    pnl REAL DEFAULT 0,
                    open_time TEXT NOT NULL,
                    close_time TEXT,
                    status TEXT NOT NULL,
                    stop_loss REAL,
                    take_profit REAL
                )''',
                '''CREATE TABLE IF NOT EXISTS portfolio_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    total_value REAL NOT NULL,
                    cash_balance REAL NOT NULL,
                    daily_pnl REAL DEFAULT 0,
                    total_pnl REAL DEFAULT 0,
                    open_positions INTEGER DEFAULT 0
                )'''
            ]
        }
    
    def install_dependencies(self):
        """Install Python dependencies"""
        print("📦 Installing Python dependencies...")
        
        try:
            # Upgrade pip first
            subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
                         check=True, capture_output=True)
            
            # Install each dependency
            for dep in self.python_deps:
                print(f"Installing {dep}...")
                subprocess.run([sys.executable, "-m", "pip", "install", dep], 
                             check=True, capture_output=True)
            
            print("✅ All dependencies installed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            return False
    
    def create_directories(self):
        """Create required directories with proper permissions"""
        print("📁 Creating required directories...")
        
        success = True
        
        for directory in self.required_dirs:
            try:
                directory.mkdir(parents=True, exist_ok=True)
                
                # Set permissions (readable/writable by owner and group)
                if directory.exists():
                    os.chmod(directory, 0o755)
                    print(f"✅ Created: {directory}")
                else:
                    print(f"❌ Failed to create: {directory}")
                    success = False
                    
            except PermissionError:
                print(f"⚠️  Permission denied for: {directory}")
                print(f"   Try: sudo mkdir -p {directory} && sudo chown $USER:$USER {directory}")
                success = False
            except Exception as e:
                print(f"❌ Error creating {directory}: {e}")
                success = False
        
        return success
    
    def initialize_databases(self):
        """Initialize databases with required schemas"""
        print("🗄️  Initializing databases...")
        
        success = True
        
        for db_name, schemas in self.database_schemas.items():
            try:
                db_path = self.project_root / db_name
                print(f"Initializing {db_name}...")
                
                with sqlite3.connect(db_path) as conn:
                    for schema in schemas:
                        conn.execute(schema)
                    conn.commit()
                
                print(f"✅ {db_name} initialized")
                
            except Exception as e:
                print(f"❌ Failed to initialize {db_name}: {e}")
                success = False
        
        return success
    
    def setup_redis_config(self):
        """Setup Redis configuration for microservices"""
        print("⚙️  Configuring Redis for microservices...")
        
        try:
            # Test Redis connection
            import redis
            r = redis.Redis(host='localhost', port=6379, decode_responses=True)
            r.ping()
            
            # Configure Redis for microservices use
            r.config_set('maxmemory-policy', 'allkeys-lru')
            r.config_set('timeout', '300')
            
            # Create microservices namespaces
            r.hset("microservices:config", "initialized", datetime.now().isoformat())
            r.hset("microservices:config", "version", "1.0")
            
            print("✅ Redis configured successfully")
            return True
            
        except ImportError:
            print("⚠️  Redis Python package not installed")
            return False
        except Exception as e:
            print(f"❌ Redis configuration failed: {e}")
            print("   Make sure Redis server is running: sudo systemctl start redis")
            return False
    
    def create_service_configs(self):
        """Create configuration files for services"""
        print("⚙️  Creating service configuration files...")
        
        # Create main config file
        main_config = {
            "services": {
                "redis_url": "redis://localhost:6379",
                "log_level": "INFO",
                "socket_timeout": 30,
                "health_check_interval": 60
            },
            "trading": {
                "default_symbols": ["CBA.AX", "ANZ.AX", "NAB.AX", "WBC.AX"],
                "position_size_pct": 0.05,
                "max_daily_loss": 5000,
                "stop_loss_pct": 0.05
            },
            "market_data": {
                "cache_ttl": 300,
                "refresh_interval": 900
            },
            "sentiment": {
                "cache_ttl": 1800,
                "confidence_threshold": 0.6
            }
        }
        
        config_path = self.project_root / "microservices_config.json"
        try:
            with open(config_path, 'w') as f:
                json.dump(main_config, f, indent=2)
            print(f"✅ Main config created: {config_path}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to create config file: {e}")
            return False
    
    def setup_logging(self):
        """Setup logging configuration"""
        print("📝 Setting up logging...")
        
        try:
            # Create log directory if it doesn't exist
            self.logs_dir.mkdir(parents=True, exist_ok=True)
            
            # Create logrotate configuration (if on Linux)
            logrotate_config = f"""
{self.logs_dir}/*.log {{
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}}
"""
            
            logrotate_path = Path("/etc/logrotate.d/trading-microservices")
            if os.name == 'posix':  # Unix-like system
                try:
                    with open(logrotate_path, 'w') as f:
                        f.write(logrotate_config)
                    print(f"✅ Logrotate config created: {logrotate_path}")
                except PermissionError:
                    print(f"⚠️  Cannot create logrotate config (needs sudo)")
                    print(f"   Manual setup: sudo tee {logrotate_path} <<< '{logrotate_config.strip()}'")
            
            print("✅ Logging setup completed")
            return True
            
        except Exception as e:
            print(f"❌ Logging setup failed: {e}")
            return False
    
    def test_microservices_setup(self):
        """Test basic microservices functionality"""
        print("🧪 Testing microservices setup...")
        
        tests_passed = 0
        total_tests = 5
        
        # Test 1: Directory access
        print("Test 1: Directory access...")
        if all(d.exists() and os.access(d, os.W_OK) for d in self.required_dirs):
            print("✅ Directory access test passed")
            tests_passed += 1
        else:
            print("❌ Directory access test failed")
        
        # Test 2: Database access
        print("Test 2: Database access...")
        try:
            test_db = self.project_root / "test_microservices.db"
            with sqlite3.connect(test_db) as conn:
                conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")
                conn.execute("INSERT INTO test (id) VALUES (1)")
                result = conn.execute("SELECT id FROM test").fetchone()
                if result[0] == 1:
                    print("✅ Database access test passed")
                    tests_passed += 1
                else:
                    print("❌ Database access test failed")
            test_db.unlink(missing_ok=True)
        except Exception as e:
            print(f"❌ Database access test failed: {e}")
        
        # Test 3: Redis connection
        print("Test 3: Redis connection...")
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, decode_responses=True)
            r.ping()
            r.set("microservices:test", "ok")
            if r.get("microservices:test") == "ok":
                print("✅ Redis connection test passed")
                tests_passed += 1
                r.delete("microservices:test")
            else:
                print("❌ Redis connection test failed")
        except Exception as e:
            print(f"❌ Redis connection test failed: {e}")
        
        # Test 4: Socket creation
        print("Test 4: Unix socket creation...")
        try:
            import socket
            test_socket_path = self.sockets_dir / "test_socket.sock"
            test_socket_path.unlink(missing_ok=True)
            
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.bind(str(test_socket_path))
            sock.listen(1)
            sock.close()
            test_socket_path.unlink(missing_ok=True)
            
            print("✅ Unix socket test passed")
            tests_passed += 1
        except Exception as e:
            print(f"❌ Unix socket test failed: {e}")
        
        # Test 5: Import dependencies
        print("Test 5: Import dependencies...")
        try:
            import redis
            import pandas
            import numpy
            import yfinance
            import requests
            import psutil
            print("✅ Dependencies import test passed")
            tests_passed += 1
        except ImportError as e:
            print(f"❌ Dependencies import test failed: {e}")
        
        # Results
        print(f"\n🧪 Test Results: {tests_passed}/{total_tests} tests passed")
        
        if tests_passed == total_tests:
            print("✅ All tests passed! Microservices environment is ready.")
            return True
        else:
            print("⚠️  Some tests failed. Please review and fix issues before proceeding.")
            return False
    
    def create_startup_script(self):
        """Create convenient startup script"""
        print("📜 Creating startup script...")
        
        startup_script = f"""#!/bin/bash
# Trading Microservices Startup Script
# Generated by setup_microservices.py

set -e

echo "🚀 Starting Trading Microservices..."

# Check Redis
if ! redis-cli ping > /dev/null 2>&1; then
    echo "❌ Redis is not running. Please start Redis first:"
    echo "   sudo systemctl start redis"
    exit 1
fi

# Start services using service manager
cd {self.project_root}
python services/management/service_manager.py start

echo "✅ Trading microservices started successfully!"
echo "💡 Monitor with: python services/management/service_manager.py dashboard"
"""
        
        script_path = self.project_root / "start_microservices.sh"
        try:
            with open(script_path, 'w') as f:
                f.write(startup_script)
            os.chmod(script_path, 0o755)  # Make executable
            
            print(f"✅ Startup script created: {script_path}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create startup script: {e}")
            return False
    
    def run_full_setup(self):
        """Run complete setup process"""
        print("🔧 Running complete microservices setup...\n")
        
        steps = [
            ("Creating directories", self.create_directories),
            ("Installing dependencies", self.install_dependencies),
            ("Initializing databases", self.initialize_databases),
            ("Configuring Redis", self.setup_redis_config),
            ("Creating service configs", self.create_service_configs),
            ("Setting up logging", self.setup_logging),
            ("Creating startup script", self.create_startup_script),
            ("Testing setup", self.test_microservices_setup)
        ]
        
        failed_steps = []
        
        for step_name, step_func in steps:
            print(f"\n📋 {step_name}...")
            try:
                if not step_func():
                    failed_steps.append(step_name)
            except Exception as e:
                print(f"❌ {step_name} failed with exception: {e}")
                failed_steps.append(step_name)
        
        print("\n" + "="*60)
        print("MICROSERVICES SETUP SUMMARY")
        print("="*60)
        
        if not failed_steps:
            print("🎉 Complete setup successful!")
            print("\nNext steps:")
            print("1. Start Redis: sudo systemctl start redis")
            print("2. Start services: ./start_microservices.sh")
            print("3. Monitor: python services/management/service_manager.py dashboard")
            return True
        else:
            print(f"⚠️  Setup completed with {len(failed_steps)} issues:")
            for step in failed_steps:
                print(f"   - {step}")
            print("\nPlease review and fix the issues above before starting services.")
            return False

def main():
    parser = argparse.ArgumentParser(description="Setup Trading Microservices Environment")
    parser.add_argument("--install-deps", action="store_true", help="Install Python dependencies")
    parser.add_argument("--create-dirs", action="store_true", help="Create required directories")
    parser.add_argument("--init-db", action="store_true", help="Initialize databases")
    parser.add_argument("--redis-setup", action="store_true", help="Configure Redis")
    parser.add_argument("--test", action="store_true", help="Run functionality tests")
    parser.add_argument("--full", action="store_true", help="Run complete setup")
    
    args = parser.parse_args()
    
    setup = MicroservicesSetup()
    
    # If no specific args, run full setup
    if not any([args.install_deps, args.create_dirs, args.init_db, args.redis_setup, args.test]):
        args.full = True
    
    if args.full:
        setup.run_full_setup()
    else:
        if args.create_dirs:
            setup.create_directories()
        if args.install_deps:
            setup.install_dependencies()
        if args.init_db:
            setup.initialize_databases()
        if args.redis_setup:
            setup.setup_redis_config()
        if args.test:
            setup.test_microservices_setup()

if __name__ == "__main__":
    main()
