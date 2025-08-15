#!/usr/bin/env python3
"""
Folder Structure Cleanup Tool
============================

Organizes the workspace by archiving unused folders and consolidating
utility scripts into a proper structure.
"""

import os
import shutil
from datetime import datetime
import json

class FolderCleanupManager:
    def __init__(self):
        self.archive_dir = "archive_cleanup"
        self.optional_features_dir = "optional_features"
        self.cleanup_report = {
            "cleanup_date": datetime.now().isoformat(),
            "archived_folders": [],
            "moved_folders": [],
            "organized_utils": [],
            "errors": []
        }
    
    def create_directories(self):
        """Create necessary directories for cleanup"""
        # Archive directory for old/unused code
        os.makedirs(self.archive_dir, exist_ok=True)
        
        # Optional features directory
        os.makedirs(self.optional_features_dir, exist_ok=True)
        
        # Utils organization structure
        utils_dirs = [
            "utils/data_quality",
            "utils/temporal_protection", 
            "utils/ml_validation",
            "utils/deployment",
            "utils/monitoring"
        ]
        
        for util_dir in utils_dirs:
            os.makedirs(util_dir, exist_ok=True)
        
        print("📁 Created organizational directories")
    
    def archive_folder(self, folder_path, reason="Unused"):
        """Archive a folder to the archive directory"""
        if not os.path.exists(folder_path):
            return False
        
        folder_name = os.path.basename(folder_path)
        archive_path = os.path.join(self.archive_dir, f"{folder_name}_{datetime.now().strftime('%Y%m%d')}")
        
        try:
            shutil.move(folder_path, archive_path)
            print(f"📦 Archived: {folder_path} -> {archive_path} ({reason})")
            self.cleanup_report["archived_folders"].append({
                "original": folder_path,
                "archived_to": archive_path,
                "reason": reason
            })
            return True
        except Exception as e:
            print(f"❌ Failed to archive {folder_path}: {e}")
            self.cleanup_report["errors"].append(f"Archive failed: {folder_path} - {e}")
            return False
    
    def move_to_optional_features(self, folder_path):
        """Move a folder to optional features"""
        if not os.path.exists(folder_path):
            return False
        
        folder_name = os.path.basename(folder_path)
        target_path = os.path.join(self.optional_features_dir, folder_name)
        
        try:
            shutil.move(folder_path, target_path)
            print(f"🔧 Moved to optional features: {folder_path} -> {target_path}")
            self.cleanup_report["moved_folders"].append({
                "original": folder_path,
                "moved_to": target_path,
                "category": "optional_features"
            })
            return True
        except Exception as e:
            print(f"❌ Failed to move {folder_path}: {e}")
            self.cleanup_report["errors"].append(f"Move failed: {folder_path} - {e}")
            return False
    
    def organize_standalone_files(self):
        """Organize standalone utility files into proper structure"""
        
        # Data quality files
        data_quality_files = [
            "data_quality_diagnostic.py",
            "data_quality_repair.py", 
            "real_time_quality_monitor.py",
            "quick_quality_check.py",
            "intelligent_data_quality_analyzer.py",
            "smart_data_quality_fixer.py",
            "ml_data_quality_monitor.py"
        ]
        
        self._move_files_to_utils(data_quality_files, "data_quality", "Data quality tools")
        
        # Temporal protection files
        temporal_files = [
            "morning_temporal_guard.py",
            "evening_temporal_fixer.py",
            "temporal_protection_examples.py",
            "setup_temporal_protection.py",
            "evening_temporal_guard.py"
        ]
        
        self._move_files_to_utils(temporal_files, "temporal_protection", "Temporal protection system")
        
        # ML validation files
        ml_validation_files = [
            "test_model_loading.py",
            "test_action_logic.py",
            "test_bugfix_validation.py",
            "validate_fix.py",
            "view_ml_trends.py",
            "enhanced_outcomes_evaluator.py",
            "historical_reevaluator.py"
        ]
        
        self._move_files_to_utils(ml_validation_files, "ml_validation", "ML testing and validation")
        
        # Deployment files
        deployment_files = [
            "remote_cleanup_and_run.py",
            "remote_evening_data_fixer.py", 
            "remote_database_fixer.py",
            "remote_timestamp_sync.py",
            "deploy_fix.sh",
            "deploy_remote_evening_fix.sh",
            "deploy_remote_fixer.sh"
        ]
        
        self._move_files_to_utils(deployment_files, "deployment", "Remote deployment tools")
        
        # Monitoring files
        monitoring_files = [
            "morning_data_analysis.py",
            "data_flow_analysis.py",
            "evening_ml_check.py",
            "evening_ml_check_with_history.py",
            "final_verification.py",
            "final_success_verification.py"
        ]
        
        self._move_files_to_utils(monitoring_files, "monitoring", "System monitoring tools")
    
    def _move_files_to_utils(self, file_list, category, description):
        """Move a list of files to a utils subdirectory"""
        target_dir = f"utils/{category}"
        moved_count = 0
        
        for filename in file_list:
            if os.path.exists(filename):
                target_path = os.path.join(target_dir, filename)
                try:
                    shutil.move(filename, target_path)
                    moved_count += 1
                except Exception as e:
                    print(f"⚠️ Failed to move {filename}: {e}")
                    self.cleanup_report["errors"].append(f"File move failed: {filename} - {e}")
        
        if moved_count > 0:
            print(f"📋 Organized {moved_count} {description} files into {target_dir}")
            self.cleanup_report["organized_utils"].append({
                "category": category,
                "description": description,
                "files_moved": moved_count,
                "target_dir": target_dir
            })
    
    def clean_temporary_files(self):
        """Remove temporary and outdated files"""
        patterns_to_remove = [
            "trading_data_export_*.txt",
            "fix_prediction_saving*.py", 
            "prediction_method.py",
            "*.log",
            "*_test.log",
            "*.backup",
            "*_backup_*.json"
        ]
        
        import glob
        removed_count = 0
        
        for pattern in patterns_to_remove:
            for file_path in glob.glob(pattern):
                if os.path.isfile(file_path):
                    try:
                        os.remove(file_path)
                        removed_count += 1
                        print(f"🗑️ Removed: {file_path}")
                    except Exception as e:
                        print(f"⚠️ Failed to remove {file_path}: {e}")
        
        if removed_count > 0:
            print(f"🧹 Removed {removed_count} temporary/outdated files")
    
    def consolidate_documentation(self):
        """Move documentation files to docs folder"""
        os.makedirs("docs/reports", exist_ok=True)
        os.makedirs("docs/guides", exist_ok=True)
        
        # Guide files
        guide_files = [
            "TEMPORAL_PROTECTION_SYSTEM.md",
            "TEMPORAL_PROTECTION_SUMMARY.md", 
            "TEMPORAL_PROTECTION_COMPLETE.md",
            "EVENING_PROTECTION_SUMMARY.md",
            "EVENING_PROTECTION_COMPLETE.md",
            "REMOTE_DEPLOYMENT_SUMMARY.md",
            "ML_MODEL_TESTING_GUIDE.md",
            "DATA_QUALITY_MANAGEMENT_GUIDE.md"
        ]
        
        # Report files
        report_files = [
            "COMPREHENSIVE_DATA_ANALYSIS.md",
            "DASHBOARD_DATA_INCONSISTENCY_ANALYSIS.md",
            "DASHBOARD_ENHANCEMENT_SUMMARY.md",
            "REMOTE_EVENING_FIX_COMPLETE.md",
            "REMOTE_EVENING_FIX_GUIDE.md",
            "TECHNICAL_ANALYSIS_INTEGRATION_COMPLETE.md",
            "ML_PIPELINE_BUGFIX_SUMMARY.md"
        ]
        
        # Move guides
        for guide in guide_files:
            if os.path.exists(guide):
                try:
                    shutil.move(guide, f"docs/guides/{guide}")
                    print(f"📚 Moved guide: {guide}")
                except Exception as e:
                    print(f"⚠️ Failed to move guide {guide}: {e}")
        
        # Move reports
        for report in report_files:
            if os.path.exists(report):
                try:
                    shutil.move(report, f"docs/reports/{report}")
                    print(f"📊 Moved report: {report}")
                except Exception as e:
                    print(f"⚠️ Failed to move report {report}: {e}")
    
    def run_folder_cleanup(self):
        """Run the complete folder cleanup process"""
        print("🗂️  STARTING FOLDER STRUCTURE CLEANUP")
        print("="*50)
        
        # Create organizational directories
        self.create_directories()
        
        # Archive unused folders
        print("\\n📦 Archiving unused folders...")
        self.archive_folder("legacy_enhanced", "Legacy code")
        self.archive_folder("new_achieve", "Unclear purpose")
        self.archive_folder("quick_exports", "Temporary exports")
        self.archive_folder("metrics_exports", "Temporary metrics")
        self.archive_folder("backend", "Appears unused")
        
        # Move to optional features
        print("\\n🔧 Moving optional features...")
        self.move_to_optional_features("email_alerts")
        self.move_to_optional_features("mcp_server")
        
        # Organize standalone files
        print("\\n📋 Organizing utility files...")
        self.organize_standalone_files()
        
        # Clean temporary files
        print("\\n🧹 Cleaning temporary files...")
        self.clean_temporary_files()
        
        # Consolidate documentation
        print("\\n📚 Consolidating documentation...")
        self.consolidate_documentation()
        
        # Generate report
        self._generate_report()
        
        print("\\n🎉 Folder cleanup completed!")
        self._print_new_structure()
    
    def _generate_report(self):
        """Generate cleanup report"""
        report_path = "folder_cleanup_report.json"
        with open(report_path, 'w') as f:
            json.dump(self.cleanup_report, f, indent=2)
        print(f"\\n📄 Cleanup report saved: {report_path}")
    
    def _print_new_structure(self):
        """Print the recommended new structure"""
        print("\\n" + "="*50)
        print("📁 RECOMMENDED NEW STRUCTURE")
        print("="*50)
        print("""
├── app/                    # Core application (MAIN FOCUS)
├── enhanced_ml_system/     # Active ML components  
├── data/                   # Essential data storage
├── frontend/               # UI components
├── tests/                  # Testing framework
├── docs/                   # Documentation
│   ├── guides/            # Technical guides
│   └── reports/           # Analysis reports
├── utils/                  # Organized utilities
│   ├── data_quality/      # Data quality tools
│   ├── temporal_protection/ # Temporal protection
│   ├── ml_validation/     # ML testing tools
│   ├── deployment/        # Remote deployment
│   └── monitoring/        # System monitoring
├── optional_features/      # Optional components
│   ├── email_alerts/      # Email notifications
│   └── mcp_server/        # MCP server
└── archive_cleanup/        # Archived old code
        """)

def main():
    cleanup_manager = FolderCleanupManager()
    cleanup_manager.run_folder_cleanup()

if __name__ == "__main__":
    main()
