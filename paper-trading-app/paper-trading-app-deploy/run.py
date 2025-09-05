#!/usr/bin/env python3
"""
Paper Trading App Startup Script
"""

import subprocess
import sys
import os

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        'streamlit',
        'sqlalchemy', 
        'pandas',
        'yfinance',
        'plotly'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\nInstall them with:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True

def init_database():
    """Initialize database if needed"""
    if not os.path.exists("paper_trading.db"):
        print("🔄 Initializing database...")
        try:
            from database.init_db import main as init_db
            init_db()
        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
            return False
    else:
        print("✅ Database exists")
    
    return True

def start_dashboard():
    """Start the Streamlit dashboard"""
    print("🚀 Starting Paper Trading Dashboard...")
    print("📊 Dashboard will open in your browser")
    print("🛑 Press Ctrl+C to stop")
    
    try:
        subprocess.run([
            sys.executable, 
            "-m", "streamlit", "run", 
            "dashboard.py",
            "--server.port", "8501",
            "--server.headless", "false"
        ])
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped")
    except Exception as e:
        print(f"❌ Error starting dashboard: {e}")

def main():
    """Main startup function"""
    print("=" * 50)
    print("📈 Paper Trading App")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        return
    
    # Initialize database
    if not init_database():
        return
    
    # Start dashboard
    start_dashboard()

if __name__ == "__main__":
    main()
