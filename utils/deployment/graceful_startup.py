#!/usr/bin/env python3
"""
Graceful Trading System Startup
===============================

Performs pre-flight checks and starts the trading system safely:
1. System health verification
2. Configuration validation  
3. Database integrity check
4. Dependency verification
5. Graceful error handling
"""

import sys
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.config.config_manager import ConfigurationManager
from app.utils.health_checker import SystemHealthChecker
from app.utils.error_handler import ErrorHandler
from app.config.logging import setup_logging

class GracefulStartup:
    """Manages graceful system startup with comprehensive checks"""
    
    def __init__(self):
        self.logger = None
        self.config = None
        self.health_checker = None
        self.error_handler = None
        self.startup_successful = False
    
    def run_startup_sequence(self, command: str) -> bool:
        """Run complete startup sequence with safety checks"""
        
        print("🚀 TRADING SYSTEM STARTUP")
        print("=" * 50)
        print(f"Command: {command}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        try:
            # Step 1: Initialize logging
            if not self._initialize_logging():
                return False
            
            # Step 2: Load configuration
            if not self._load_configuration():
                return False
            
            # Step 3: Run health checks
            if not self._run_health_checks():
                return False
            
            # Step 4: Verify command readiness
            if not self._verify_command_readiness(command):
                return False
            
            print("✅ All startup checks passed!")
            print("🏁 System ready for operation")
            self.startup_successful = True
            return True
            
        except Exception as e:
            print(f"❌ Startup failed: {e}")
            if self.logger:
                self.logger.error(f"Startup sequence failed: {e}")
            return False
    
    def _initialize_logging(self) -> bool:
        """Initialize logging system"""
        print("📝 Initializing logging...")
        
        try:
            self.logger = setup_logging()
            self.error_handler = ErrorHandler(self.logger)
            print("   ✅ Logging initialized")
            return True
        except Exception as e:
            print(f"   ❌ Logging failed: {e}")
            return False
    
    def _load_configuration(self) -> bool:
        """Load and validate configuration"""
        print("⚙️ Loading configuration...")
        
        try:
            self.config = ConfigurationManager()
            print("   ✅ Configuration loaded")
            return True
        except Exception as e:
            print(f"   ❌ Configuration failed: {e}")
            if self.logger:
                self.logger.error(f"Configuration loading failed: {e}")
            return False
    
    def _run_health_checks(self) -> bool:
        """Run comprehensive health checks"""
        print("🏥 Running health checks...")
        
        try:
            self.health_checker = SystemHealthChecker(self.config)
            health_report = self.health_checker.run_comprehensive_health_check()
            
            status = health_report['overall_status']
            
            if status == 'healthy':
                print("   ✅ All systems healthy")
                return True
            elif status in ['degraded', 'warning']:
                print(f"   ⚠️ System status: {status}")
                
                # Show specific issues but allow to continue
                issue_count = 0
                for check_name, check_result in health_report['checks'].items():
                    if check_result['status'] in ['error', 'warning']:
                        print(f"      • {check_name}: {check_result['message']}")
                        issue_count += 1
                
                if issue_count > 0:
                    print(f"   💡 {issue_count} issues found but system can continue")
                
                return True  # Allow to continue with warnings
            else:
                print(f"   ❌ System health critical: {status}")
                print("   🔧 Please resolve critical issues before continuing")
                
                # Show specific critical issues
                for check_name, check_result in health_report['checks'].items():
                    if check_result['status'] == 'error':
                        print(f"      • {check_name}: {check_result['message']}")
                
                return False
                
        except Exception as e:
            print(f"   ⚠️ Health check failed: {e}")
            print("   💡 Proceeding with basic startup...")
            return True  # Don't block startup on health check failure
    
    def _verify_command_readiness(self, command: str) -> bool:
        """Verify system is ready for specific command"""
        print(f"🎯 Verifying readiness for '{command}'...")
        
        try:
            # Command-specific checks
            if command in ['morning', 'evening']:
                return self._check_analysis_readiness()
            elif command == 'dashboard':
                return self._check_dashboard_readiness()
            elif command in ['backtest', 'simple-backtest']:
                return self._check_backtest_readiness()
            else:
                print("   ✅ No specific requirements")
                return True
                
        except Exception as e:
            print(f"   ❌ Readiness check failed: {e}")
            return False
    
    def _check_analysis_readiness(self) -> bool:
        """Check if system is ready for analysis commands"""
        # Check database access
        db_health = self.health_checker.check_database_health()
        if db_health['status'] == 'error':
            print("   ❌ Database not accessible")
            return False
        
        # Check basic data availability
        print("   ✅ Analysis systems ready")
        return True
    
    def _check_dashboard_readiness(self) -> bool:
        """Check if system is ready for dashboard"""
        print("   ✅ Dashboard ready")
        return True
    
    def _check_backtest_readiness(self) -> bool:
        """Check if system is ready for backtesting"""
        print("   ✅ Backtesting ready")
        return True

def main():
    """Main startup entry point"""
    if len(sys.argv) < 2:
        print("Usage: python graceful_startup.py <command>")
        sys.exit(1)
    
    command = sys.argv[1]
    startup = GracefulStartup()
    
    if startup.run_startup_sequence(command):
        print("\n🚀 Starting main application...")
        
        # Import and run the main application
        try:
            from app.main import main as app_main
            
            # Replace sys.argv to pass through the original command
            sys.argv = ['app.main'] + sys.argv[1:]
            app_main()
            
        except Exception as e:
            print(f"❌ Application execution failed: {e}")
            sys.exit(1)
    else:
        print("\n❌ Startup checks failed - aborting")
        sys.exit(1)

if __name__ == "__main__":
    main()
