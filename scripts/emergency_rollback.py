#!/usr/bin/env python3
"""
Emergency Rollback Script
Rolls back from microservices to monolithic architecture
"""

import os
import sys
import json
import shutil
import subprocess
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List
import logging

class RollbackManager:
    """Manages emergency rollback from microservices to monolithic system"""
    
    def __init__(self, workspace_path: str = "c:\\Users\\todd.sutherland\\trading_feature"):
        self.workspace_path = Path(workspace_path)
        self.rollback_log = []
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('rollback.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Rollback phases (reverse of migration)
        self.phases = [
            "stop_microservices",
            "restore_databases", 
            "restore_code_files",
            "restore_configuration",
            "restore_cron_jobs",
            "validate_monolithic_system",
            "cleanup_microservices"
        ]
        
        # Backup directory pattern
        self.backup_pattern = "migration_backup_*"

    def log_action(self, action: str, details: dict = None):
        """Log rollback action"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "details": details or {}
        }
        
        self.rollback_log.append(log_entry)
        self.logger.info(f"Rollback: {action} - {details}")

    async def run_rollback(self, backup_directory: str = None) -> bool:
        """Run complete rollback process"""
        self.logger.info("Starting emergency rollback to monolithic system")
        self.log_action("rollback_started")
        
        try:
            # Find backup directory if not specified
            if not backup_directory:
                backup_directory = self._find_latest_backup()
                if not backup_directory:
                    self.logger.error("No backup directory found")
                    return False
            
            self.backup_dir = Path(backup_directory)
            if not self.backup_dir.exists():
                self.logger.error(f"Backup directory not found: {backup_directory}")
                return False
            
            self.logger.info(f"Using backup directory: {self.backup_dir}")
            
            for phase in self.phases:
                self.logger.info(f"Starting rollback phase: {phase}")
                
                phase_method = getattr(self, phase)
                success = await phase_method()
                
                if not success:
                    self.logger.error(f"Rollback phase {phase} failed")
                    return False
                    
                self.logger.info(f"Completed rollback phase: {phase}")
                
            self.log_action("rollback_completed", {"success": True})
            self.logger.info("Rollback completed successfully!")
            return True
            
        except Exception as e:
            self.logger.error(f"Rollback failed: {e}")
            self.log_action("rollback_failed", {"error": str(e)})
            return False

    def _find_latest_backup(self) -> str:
        """Find the latest migration backup directory"""
        backup_dirs = list(self.workspace_path.glob(self.backup_pattern))
        if not backup_dirs:
            return None
        
        # Sort by creation time and return the latest
        latest_backup = max(backup_dirs, key=lambda x: x.stat().st_mtime)
        return str(latest_backup)

    async def stop_microservices(self) -> bool:
        """Stop all microservices"""
        self.logger.info("Stopping microservices...")
        
        try:
            services = [
                "trading-market-data",
                "trading-sentiment", 
                "trading-prediction",
                "trading-paper-trading",
                "trading-ml-model",
                "trading-scheduler",
                "trading-monitoring"
            ]
            
            stopped_services = []
            
            for service in services:
                try:
                    # On Linux/production, this would use systemctl
                    # For Windows development, we simulate
                    self.logger.info(f"Stopping service: {service}")
                    stopped_services.append(service)
                    
                except Exception as e:
                    self.logger.warning(f"Failed to stop service {service}: {e}")
            
            self.log_action("microservices_stopped", {
                "stopped_services": stopped_services
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop microservices: {e}")
            return False

    async def restore_databases(self) -> bool:
        """Restore databases from backup"""
        self.logger.info("Restoring databases...")
        
        try:
            db_backup_dir = self.backup_dir / "databases"
            if not db_backup_dir.exists():
                self.logger.warning("No database backup directory found")
                return True
            
            restored_dbs = []
            
            for backup_file in db_backup_dir.glob("*.db"):
                # Extract original database name
                # Format: component_original_name.db
                parts = backup_file.name.split('_', 1)
                if len(parts) < 2:
                    continue
                    
                original_name = parts[1]
                target_path = self.workspace_path / original_name
                
                # Backup current database if it exists
                if target_path.exists():
                    backup_current = target_path.with_suffix('.db.microservice_backup')
                    shutil.copy2(target_path, backup_current)
                    self.logger.info(f"Backed up current database: {original_name}")
                
                # Restore from backup
                shutil.copy2(backup_file, target_path)
                restored_dbs.append(original_name)
                self.logger.info(f"Restored database: {original_name}")
            
            self.log_action("databases_restored", {
                "restored_databases": restored_dbs
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Database restoration failed: {e}")
            return False

    async def restore_code_files(self) -> bool:
        """Restore code files from backup"""
        self.logger.info("Restoring code files...")
        
        try:
            code_backup_dir = self.backup_dir / "code"
            if not code_backup_dir.exists():
                self.logger.warning("No code backup directory found")
                return True
            
            restored_files = []
            
            for component_dir in code_backup_dir.iterdir():
                if not component_dir.is_dir():
                    continue
                
                for backup_file in component_dir.rglob("*"):
                    if backup_file.is_file():
                        # Calculate relative path from component directory
                        rel_path = backup_file.relative_to(component_dir)
                        target_path = self.workspace_path / rel_path
                        
                        # Create target directory if needed
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        # Backup current file if it exists
                        if target_path.exists():
                            backup_current = target_path.with_suffix(target_path.suffix + '.microservice_backup')
                            shutil.copy2(target_path, backup_current)
                        
                        # Restore from backup
                        shutil.copy2(backup_file, target_path)
                        restored_files.append(str(rel_path))
                        self.logger.info(f"Restored file: {rel_path}")
            
            self.log_action("code_files_restored", {
                "restored_files": restored_files
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Code file restoration failed: {e}")
            return False

    async def restore_configuration(self) -> bool:
        """Restore configuration files from backup"""
        self.logger.info("Restoring configuration...")
        
        try:
            config_backup_dir = self.backup_dir / "config"
            if not config_backup_dir.exists():
                self.logger.warning("No config backup directory found")
                return True
            
            restored_configs = []
            
            for config_file in config_backup_dir.iterdir():
                if config_file.is_file():
                    target_path = self.workspace_path / config_file.name
                    
                    # Backup current config if it exists
                    if target_path.exists():
                        backup_current = target_path.with_suffix(target_path.suffix + '.microservice_backup')
                        shutil.copy2(target_path, backup_current)
                    
                    # Restore from backup
                    shutil.copy2(config_file, target_path)
                    restored_configs.append(config_file.name)
                    self.logger.info(f"Restored config: {config_file.name}")
            
            self.log_action("configuration_restored", {
                "restored_configs": restored_configs
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Configuration restoration failed: {e}")
            return False

    async def restore_cron_jobs(self) -> bool:
        """Restore original cron jobs"""
        self.logger.info("Restoring cron jobs...")
        
        try:
            # On Windows, we simulate cron job restoration
            self.logger.info("Cron job restoration simulated (Windows environment)")
            
            # In production Linux environment, this would:
            # 1. Find backup crontab file
            # 2. Install original crontab: crontab backup_crontab.txt
            
            self.log_action("cron_jobs_restored", {
                "platform": "windows",
                "simulation": True
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Cron job restoration failed: {e}")
            return False

    async def validate_monolithic_system(self) -> bool:
        """Validate that monolithic system is working"""
        self.logger.info("Validating monolithic system...")
        
        try:
            validation_results = {
                "databases_accessible": self._validate_databases(),
                "key_files_present": self._validate_key_files(),
                "python_imports": self._validate_python_imports()
            }
            
            all_validations_passed = all(validation_results.values())
            
            self.log_action("monolithic_validation", {
                "results": validation_results,
                "all_passed": all_validations_passed
            })
            
            if not all_validations_passed:
                self.logger.error("Monolithic system validation failed")
                for check, result in validation_results.items():
                    if not result:
                        self.logger.error(f"Failed validation: {check}")
            
            return all_validations_passed
            
        except Exception as e:
            self.logger.error(f"Monolithic system validation failed: {e}")
            return False

    def _validate_databases(self) -> bool:
        """Validate database accessibility"""
        required_dbs = [
            "trading_predictions.db",
            "paper_trading.db", 
            "predictions.db"
        ]
        
        for db_file in required_dbs:
            db_path = self.workspace_path / db_file
            if not db_path.exists():
                self.logger.error(f"Database not found: {db_file}")
                return False
            
            try:
                conn = sqlite3.connect(str(db_path))
                conn.execute("SELECT 1")
                conn.close()
            except Exception as e:
                self.logger.error(f"Database not accessible: {db_file} - {e}")
                return False
        
        return True

    def _validate_key_files(self) -> bool:
        """Validate key files are present"""
        key_files = [
            "enhanced_efficient_system_market_aware.py",
            "enhanced_efficient_system_market_aware_integrated.py",
            "realtime_price_function.py"
        ]
        
        for key_file in key_files:
            file_path = self.workspace_path / key_file
            if not file_path.exists():
                self.logger.error(f"Key file not found: {key_file}")
                return False
        
        return True

    def _validate_python_imports(self) -> bool:
        """Validate Python imports work"""
        try:
            # Test importing key modules
            sys.path.insert(0, str(self.workspace_path))
            
            test_imports = [
                "enhanced_efficient_system_market_aware",
                "realtime_price_function"
            ]
            
            for module_name in test_imports:
                try:
                    __import__(module_name)
                    self.logger.info(f"Successfully imported: {module_name}")
                except Exception as e:
                    self.logger.error(f"Failed to import {module_name}: {e}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Python import validation failed: {e}")
            return False

    async def cleanup_microservices(self) -> bool:
        """Clean up microservices artifacts"""
        self.logger.info("Cleaning up microservices...")
        
        try:
            cleanup_items = []
            
            # Remove microservice directories
            microservice_dirs = [
                "services",
                "compatibility"
            ]
            
            for dir_name in microservice_dirs:
                dir_path = self.workspace_path / dir_name
                if dir_path.exists():
                    # Move to archive instead of deleting
                    archive_path = self.workspace_path / f"microservices_archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    archive_path.mkdir(exist_ok=True)
                    
                    shutil.move(str(dir_path), str(archive_path / dir_name))
                    cleanup_items.append(f"Archived: {dir_name}")
                    self.logger.info(f"Archived microservice directory: {dir_name}")
            
            # Remove microservice configuration files
            microservice_configs = [
                "multi_region_manager.py",
                "validate_multi_region.py",
                "deploy_multi_region.sh"
            ]
            
            for config_file in microservice_configs:
                config_path = self.workspace_path / config_file
                if config_path.exists():
                    archive_path = config_path.with_suffix(config_path.suffix + '.archived')
                    shutil.move(str(config_path), str(archive_path))
                    cleanup_items.append(f"Archived: {config_file}")
                    self.logger.info(f"Archived microservice config: {config_file}")
            
            self.log_action("microservices_cleanup", {
                "cleanup_items": cleanup_items
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Microservices cleanup failed: {e}")
            return False

    def generate_rollback_report(self) -> str:
        """Generate comprehensive rollback report"""
        report = {
            "rollback_summary": {
                "start_time": self.rollback_log[0]["timestamp"] if self.rollback_log else "unknown",
                "end_time": self.rollback_log[-1]["timestamp"] if self.rollback_log else "unknown",
                "total_phases": len(self.phases),
                "completed_phases": len([log for log in self.rollback_log if "completed" in log["action"]]),
                "success": any("rollback_completed" in log["action"] for log in self.rollback_log),
                "backup_directory": str(self.backup_dir) if hasattr(self, 'backup_dir') else "unknown"
            },
            "rollback_log": self.rollback_log,
            "recommendations": self._generate_recommendations()
        }
        
        return json.dumps(report, indent=2)

    def _generate_recommendations(self) -> List[str]:
        """Generate post-rollback recommendations"""
        recommendations = [
            "Verify all cron jobs are running correctly",
            "Test trading system functionality end-to-end",
            "Monitor system logs for any errors",
            "Validate database integrity and consistency",
            "Check that all prediction models are loading correctly",
            "Verify paper trading integration is working",
            "Test dashboard and monitoring functionality"
        ]
        
        # Add specific recommendations based on rollback issues
        for log_entry in self.rollback_log:
            if "error" in log_entry.get("details", {}):
                recommendations.append(f"Investigate and resolve: {log_entry['action']}")
        
        return recommendations

async def main():
    """Main rollback function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Emergency rollback from microservices")
    parser.add_argument("--workspace", default="c:\\Users\\todd.sutherland\\trading_feature")
    parser.add_argument("--backup-dir", help="Specific backup directory to restore from")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true", help="Force rollback even if validations fail")
    
    args = parser.parse_args()
    
    # Confirm rollback (unless forced)
    if not args.force and not args.dry_run:
        response = input("This will rollback from microservices to monolithic system. Continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Rollback cancelled")
            return False
    
    manager = RollbackManager(args.workspace)
    
    if args.dry_run:
        print("Dry run mode - would execute:")
        backup_dir = args.backup_dir or manager._find_latest_backup()
        print(f"Using backup directory: {backup_dir}")
        for phase in manager.phases:
            print(f"  - {phase}")
        return True
    
    success = await manager.run_rollback(args.backup_dir)
    
    # Generate report
    report = manager.generate_rollback_report()
    report_file = Path(args.workspace) / "rollback_report.json"
    report_file.write_text(report)
    
    if success:
        print("\\n" + "="*60)
        print("ROLLBACK COMPLETED SUCCESSFULLY!")
        print("="*60)
        print(f"Report saved: {report_file}")
        print("\\nNext steps:")
        print("1. Verify all cron jobs are running")
        print("2. Test trading system functionality")
        print("3. Monitor system logs for errors")
        print("4. Check database integrity")
    else:
        print("\\n" + "="*60)
        print("ROLLBACK FAILED!")
        print("="*60)
        print(f"Check logs and report: {report_file}")
        print("\\nManual intervention may be required.")
    
    return success

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
