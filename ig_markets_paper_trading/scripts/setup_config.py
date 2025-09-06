#!/usr/bin/env python3
"""
Configuration Setup Script for IG Markets Paper Trading System
Helps migrate credentials from existing system or set up new configuration.
"""

import os
import sys
import json
import sqlite3
from pathlib import Path


def find_existing_ig_config():
    """Find existing IG Markets configuration in the workspace."""
    workspace_root = Path(__file__).parent.parent.parent
    
    # Common config file patterns
    config_patterns = [
        'ig_config.json',
        'ig_markets_config.json',
        'config/ig_config.json',
        'config/ig_markets_config.json',
        '**/ig*config*.json'
    ]
    
    found_configs = []
    for pattern in config_patterns:
        for config_file in workspace_root.glob(pattern):
            if config_file.exists() and config_file.is_file():
                found_configs.append(config_file)
    
    return found_configs


def find_existing_predictions_db():
    """Find existing predictions database."""
    workspace_root = Path(__file__).parent.parent.parent
    
    # Common database patterns
    db_patterns = [
        'predictions.db',
        'trading.db',
        '**/predictions*.db',
        '**/trading*.db'
    ]
    
    found_dbs = []
    for pattern in db_patterns:
        for db_file in workspace_root.glob(pattern):
            if db_file.exists() and db_file.is_file():
                found_dbs.append(db_file)
    
    return found_dbs


def extract_ig_credentials(config_file):
    """Extract IG Markets credentials from existing config."""
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        # Try different key patterns
        credentials = {}
        
        # API Key
        for key in ['api_key', 'apikey', 'key', 'ig_api_key']:
            if key in config:
                credentials['api_key'] = config[key]
                break
        
        # Username
        for key in ['username', 'user', 'ig_username', 'account_name']:
            if key in config:
                credentials['username'] = config[key]
                break
        
        # Password
        for key in ['password', 'pass', 'ig_password']:
            if key in config:
                credentials['password'] = config[key]
                break
        
        # Account ID
        for key in ['account_id', 'accountid', 'account', 'ig_account_id']:
            if key in config:
                credentials['account_id'] = config[key]
                break
        
        # Tokens (if available)
        for key in ['cst_token', 'cst', 'session_token']:
            if key in config:
                credentials['cst_token'] = config[key]
                break
        
        for key in ['x_security_token', 'security_token', 'x_security']:
            if key in config:
                credentials['x_security_token'] = config[key]
                break
        
        return credentials
        
    except Exception as e:
        print(f"❌ Error reading {config_file}: {e}")
        return {}


def setup_ig_config():
    """Set up IG Markets configuration."""
    config_dir = Path(__file__).parent.parent / 'config'
    config_file = config_dir / 'ig_markets_config.json'
    
    print("🔐 Setting up IG Markets Configuration")
    print("=" * 40)
    
    # Check for existing configurations
    existing_configs = find_existing_ig_config()
    
    if existing_configs:
        print(f"📁 Found {len(existing_configs)} existing IG config(s):")
        for i, config in enumerate(existing_configs):
            print(f"   {i+1}. {config}")
        
        choice = input("\nWould you like to import from an existing config? (y/n): ").lower()
        
        if choice == 'y':
            if len(existing_configs) == 1:
                selected_config = existing_configs[0]
            else:
                try:
                    idx = int(input(f"Select config (1-{len(existing_configs)}): ")) - 1
                    selected_config = existing_configs[idx]
                except (ValueError, IndexError):
                    print("❌ Invalid selection, creating new config")
                    selected_config = None
            
            if selected_config:
                print(f"📋 Importing from: {selected_config}")
                credentials = extract_ig_credentials(selected_config)
                
                if credentials:
                    # Create config with imported credentials
                    config = {
                        "api_key": credentials.get('api_key', ''),
                        "username": credentials.get('username', ''),
                        "password": credentials.get('password', ''),
                        "account_id": credentials.get('account_id', ''),
                        "base_url": "https://demo-api.ig.com/gateway/deal",
                        "cst_token": credentials.get('cst_token', ''),
                        "x_security_token": credentials.get('x_security_token', '')
                    }
                    
                    with open(config_file, 'w') as f:
                        json.dump(config, f, indent=2)
                    
                    print("✅ Configuration imported successfully")
                    return True
    
    # Manual configuration
    print("⌨️ Manual configuration setup:")
    
    config = {
        "api_key": input("Enter your IG Markets demo API key: ").strip(),
        "username": input("Enter your IG Markets demo username: ").strip(),
        "password": input("Enter your IG Markets demo password: ").strip(),
        "account_id": input("Enter your IG Markets demo account ID: ").strip(),
        "base_url": "https://demo-api.ig.com/gateway/deal",
        "cst_token": "",
        "x_security_token": ""
    }
    
    # Validate required fields
    required_fields = ['api_key', 'username', 'password', 'account_id']
    missing_fields = [field for field in required_fields if not config[field]]
    
    if missing_fields:
        print(f"❌ Missing required fields: {', '.join(missing_fields)}")
        return False
    
    # Save configuration
    config_dir.mkdir(exist_ok=True)
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print("✅ Configuration saved successfully")
    return True


def setup_trading_config():
    """Set up trading parameters configuration."""
    config_dir = Path(__file__).parent.parent / 'config'
    config_file = config_dir / 'trading_parameters.json'
    
    print("\n💰 Setting up Trading Parameters")
    print("=" * 40)
    
    # Default configuration
    config = {
        "initial_balance": 10000.0,
        "max_position_size": 0.1,
        "risk_percentage": 0.02,
        "stop_loss_percentage": 0.05,
        "take_profit_percentage": 0.1,
        "max_daily_trades": 5,
        "min_confidence": 0.6
    }
    
    print("📋 Default trading parameters:")
    for key, value in config.items():
        print(f"   {key}: {value}")
    
    use_defaults = input("\nUse default parameters? (y/n): ").lower()
    
    if use_defaults != 'y':
        print("⌨️ Enter custom parameters (press Enter to keep default):")
        
        for key, default_value in config.items():
            user_input = input(f"{key} ({default_value}): ").strip()
            if user_input:
                try:
                    if isinstance(default_value, float):
                        config[key] = float(user_input)
                    elif isinstance(default_value, int):
                        config[key] = int(user_input)
                    else:
                        config[key] = user_input
                except ValueError:
                    print(f"❌ Invalid value for {key}, using default")
    
    # Save configuration
    config_dir.mkdir(exist_ok=True)
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print("✅ Trading parameters saved successfully")
    return True


def check_predictions_connection():
    """Check connection to predictions database."""
    print("\n🗄️ Checking Predictions Database Connection")
    print("=" * 40)
    
    # Find existing predictions database
    existing_dbs = find_existing_predictions_db()
    
    if not existing_dbs:
        print("⚠️ No predictions database found in workspace")
        print("   The system will work without historical predictions")
        return True
    
    print(f"📁 Found {len(existing_dbs)} database(s):")
    for i, db in enumerate(existing_dbs):
        print(f"   {i+1}. {db}")
        
        # Try to connect and check schema
        try:
            conn = sqlite3.connect(db)
            cursor = conn.cursor()
            
            # Check for predictions table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='predictions'")
            if cursor.fetchone():
                cursor.execute("SELECT COUNT(*) FROM predictions")
                count = cursor.fetchone()[0]
                print(f"      ✅ Contains {count} predictions")
            else:
                print("      ⚠️ No predictions table found")
            
            conn.close()
            
        except Exception as e:
            print(f"      ❌ Error reading database: {e}")
    
    return True


def main():
    """Main setup function."""
    print("🚀 IG Markets Paper Trading System Setup")
    print("=" * 50)
    
    # Check if already configured
    config_dir = Path(__file__).parent.parent / 'config'
    ig_config = config_dir / 'ig_markets_config.json'
    trading_config = config_dir / 'trading_parameters.json'
    
    if ig_config.exists() and trading_config.exists():
        print("⚙️ Configuration files already exist")
        overwrite = input("Overwrite existing configuration? (y/n): ").lower()
        if overwrite != 'y':
            print("✅ Setup cancelled - using existing configuration")
            return
    
    # Setup configurations
    success = True
    
    # IG Markets credentials
    if not setup_ig_config():
        success = False
    
    # Trading parameters
    if not setup_trading_config():
        success = False
    
    # Check predictions database
    check_predictions_connection()
    
    if success:
        print("\n✅ Setup completed successfully!")
        print("\n🎯 Next steps:")
        print("   1. Run: python3 scripts/run_paper_trader.py")
        print("   2. Monitor: tail -f logs/paper_trading.log")
        print("   3. Reports: python3 scripts/performance_report.py")
    else:
        print("\n❌ Setup failed - please check configuration")
        sys.exit(1)


if __name__ == '__main__':
    main()
