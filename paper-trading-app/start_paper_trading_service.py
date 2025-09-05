#!/usr/bin/env python3
"""
Paper Trading Background Service Launcher
Simple script to start the background trading service
"""

import subprocess
import sys
import os
import time

def check_dependencies():
    """Check if required components are available"""
    print("🔍 Checking dependencies...")
    
    # Check if paper trading app exists
    paper_trading_path = os.path.join(os.path.dirname(__file__), 'paper-trading-app')
    if not os.path.exists(paper_trading_path):
        print("❌ paper-trading-app directory not found")
        return False
    
    # Check if predictions database exists
    predictions_db = os.path.join(os.path.dirname(__file__), 'predictions.db')
    if not os.path.exists(predictions_db):
        print("❌ predictions.db not found")
        print("💡 Run your morning analysis first to create predictions")
        return False
    
    print("✅ Dependencies check passed")
    return True

def start_background_service():
    """Start the paper trading background service"""
    print("🚀 Starting Paper Trading Background Service")
    print("=" * 50)
    print("📊 This service will:")
    print("   • Monitor predictions.db every 5 minutes")
    print("   • Execute paper trades automatically")
    print("   • Use Yahoo Finance for current prices")
    print("   • Run independently from your ML system")
    print("=" * 50)
    print("🔄 Starting service... Press Ctrl+C to stop")
    print()
    
    try:
        # Run the background service
        subprocess.run([
            sys.executable,
            "paper_trading_background_service.py",
            "--db", "predictions.db",
            "--interval", "300"  # 5 minutes
        ])
    except KeyboardInterrupt:
        print("\n🛑 Service stopped by user")
    except Exception as e:
        print(f"❌ Error running service: {e}")

def test_service():
    """Test the service without running continuously"""
    print("🧪 Testing Paper Trading Service...")
    
    try:
        result = subprocess.run([
            sys.executable,
            "paper_trading_background_service.py",
            "--test"
        ], capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
            
    except Exception as e:
        print(f"❌ Test error: {e}")

def show_help():
    """Show usage help"""
    print("📋 Paper Trading Background Service")
    print("=" * 40)
    print("Usage:")
    print("  python start_paper_trading_service.py [command]")
    print()
    print("Commands:")
    print("  start    - Start the background service (default)")
    print("  test     - Test the service configuration")
    print("  help     - Show this help message")
    print()
    print("What it does:")
    print("  • Monitors your predictions.db every 5 minutes")
    print("  • Automatically executes paper trades for new predictions")
    print("  • Uses Yahoo Finance for real-time prices")
    print("  • Runs completely separate from your ML analysis")
    print("  • Logs all activity to paper_trading_service.log")
    print()
    print("Files created:")
    print("  • paper_trading_service.log - Activity log")
    print("  • paper_trading_service_state.json - Processed predictions")
    print("  • paper-trading-app/paper_trading.db - Trading database")

def main():
    """Main launcher function"""
    command = sys.argv[1] if len(sys.argv) > 1 else "start"
    
    if command == "help":
        show_help()
        return
    
    if command == "test":
        if check_dependencies():
            test_service()
        return
    
    if command == "start":
        if check_dependencies():
            start_background_service()
        return
    
    print(f"❌ Unknown command: {command}")
    print("💡 Use 'python start_paper_trading_service.py help' for usage")

if __name__ == "__main__":
    main()
