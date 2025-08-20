#!/usr/bin/env python3
"""
Comprehensive Workspace Cleanup Script
Implements the cleanup plan systematically and safely
"""

import os
import shutil
import glob
from pathlib import Path
from datetime import datetime, timedelta
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WorkspaceCleanup:
    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path).resolve()
        self.backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def phase2_organize_files(self):
        """Phase 2: Organize standalone utility files"""
        
        logger.info("🧹 PHASE 2: Organizing utility files...")
        
        # Data Quality files
        data_quality_files = [
            "data_quality_manager.py",
            "simple_data_fix.py",
            "comprehensive_database_cleanup.py",
            "database_cleanup_tool.py",
            "fix_database_references.py",
            "standardize_database_references.py",
            "update_database_schema.py"
        ]
        
        for file in data_quality_files:
            if (self.base_path / file).exists():
                self._move_file(file, "utils/data_quality/")
        
        # Temporal Protection files
        temporal_files = [
            "morning_routine_validator.py",
            "morning_routine_integration.py",
            "idempotent_morning_routine.py",
            "protected_morning_routine.py",
            "protected_morning_example.py",
            "protected_morning_cron.sh",
            "morning_script_template.py",
            "outcomes_temporal_fixer.py",
            "timestamp_synchronization_fixer.py"
        ]
        
        for file in temporal_files:
            if (self.base_path / file).exists():
                self._move_file(file, "utils/temporal_protection/")
        
        # ML Validation files
        ml_validation_files = [
            "test_dashboard_data_access.py",
            "test_dashboard_outcomes.py", 
            "test_dashboard_verification.py",
            "test_database_alignment.py",
            "test_outcomes_bugfix.py",
            "test_remote_enhanced_system.py",
            "test_technical_integration.py",
            "dashboard_data_verification.py"
        ]
        
        for file in ml_validation_files:
            if (self.base_path / file).exists():
                self._move_file(file, "utils/ml_validation/")
        
        # Deployment files
        deployment_files = [
            "check_remote_outcomes.py",
            "check_remote_status.py",
            "graceful_startup.py"
        ]
        
        for file in deployment_files:
            if (self.base_path / file).exists():
                self._move_file(file, "utils/deployment/")
        
        logger.info("✅ Phase 2 complete: Utility files organized")
    
    def phase3_archive_temp_files(self):
        """Phase 3: Archive temporary and export files"""
        
        logger.info("🗂️  PHASE 3: Archiving temporary files...")
        
        # Archive export files
        export_files = glob.glob(str(self.base_path / "*trading_data_export*.txt"))
        for file in export_files:
            self._move_file(Path(file).name, "archive/temp_exports/")
        
        # Archive report files
        report_files = [
            "app_stabilization_report.json",
            "complete_timestamp_sync_report.json", 
            "comprehensive_data_quality_report.json",
            "data_flow_analysis_results.json",
            "data_quality_fix_report.json",
            "evening_fix_report.json",
            "evening_guard_report.json",
            "morning_guard_report.json",
            "outcomes_temporal_fix_report.json",
            "timestamp_synchronization_report.json"
        ]
        
        for file in report_files:
            if (self.base_path / file).exists():
                self._move_file(file, "archive/temp_exports/")
        
        logger.info("✅ Phase 3 complete: Temporary files archived")
    
    def phase4_consolidate_docs(self):
        """Phase 4: Consolidate documentation"""
        
        logger.info("📚 PHASE 4: Consolidating documentation...")
        
        # Move large analysis docs to docs/
        analysis_docs = [
            "CLEANUP_AND_STABILIZATION_SUMMARY.md",
            "DATABASE_CLEANUP_COMPLETE.md", 
            "MAIN_SIMPLIFICATION_SUMMARY.md",
            "REMOTE_OUTCOMES_ANALYSIS.md"
        ]
        
        for doc in analysis_docs:
            if (self.base_path / doc).exists():
                self._move_file(doc, "docs/")
        
        logger.info("✅ Phase 4 complete: Documentation consolidated")
    
    def phase5_clean_redundant_tools(self):
        """Phase 5: Archive redundant/completed tools"""
        
        logger.info("🧰 PHASE 5: Archiving redundant tools...")
        
        # Tools that have completed their purpose
        completed_tools = [
            "app_stabilization_tool.py",
            "folder_cleanup_tool.py",
            "consolidate_databases.py",
            "trading_data_exporter.py"
        ]
        
        for tool in completed_tools:
            if (self.base_path / tool).exists():
                self._move_file(tool, "archive/legacy_files/")
        
        logger.info("✅ Phase 5 complete: Redundant tools archived")
    
    def create_organized_structure_summary(self):
        """Create a summary of the new organized structure"""
        
        summary = f"""
# 📁 WORKSPACE CLEANUP COMPLETE - {self.backup_timestamp}

## ✅ Organized Structure:

### 🎯 Core Application:
- `app/` - Main application code (FOCUS HERE)
- `enhanced_ml_system/` - Active ML components  
- `data/` - Database and data storage
- `frontend/` - UI components

### 🔧 Organized Utilities:
- `utils/data_quality/` - Data quality & database tools
- `utils/temporal_protection/` - Morning/evening protection scripts
- `utils/ml_validation/` - ML testing & validation tools
- `utils/deployment/` - Remote deployment utilities

### 📚 Documentation:
- `docs/` - Consolidated documentation
- `tests/` - Testing framework
- `Readme.md` - Main project readme

### 📦 Optional Features:
- `optional_features/` - Email alerts, MCP server, etc.

### 🗂️ Archives:
- `archive/legacy_files/` - Completed/redundant tools
- `archive/temp_exports/` - Temporary files and reports

## 🎯 Next Steps:
1. Focus development in `app/` folder
2. Use organized utilities from `utils/` subfolders
3. Add new features to appropriate `utils/` categories
4. Keep root directory clean

## 📊 Cleanup Stats:
- Files organized into logical categories
- Temporary files archived  
- Documentation consolidated
- Core application clearly defined
"""
        
        with open(self.base_path / "CLEANUP_COMPLETE.md", "w") as f:
            f.write(summary)
        
        logger.info("📋 Cleanup summary created: CLEANUP_COMPLETE.md")
    
    def _move_file(self, source: str, target_dir: str):
        """Safely move a file to target directory"""
        source_path = self.base_path / source
        target_path = self.base_path / target_dir / source
        
        if source_path.exists():
            # Create target directory if it doesn't exist
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Move the file
            shutil.move(str(source_path), str(target_path))
            logger.info(f"   📁 {source} → {target_dir}")
        else:
            logger.warning(f"   ⚠️ File not found: {source}")
    
    def run_full_cleanup(self):
        """Run the complete cleanup process"""
        logger.info("🚀 Starting comprehensive workspace cleanup...")
        logger.info(f"📂 Working directory: {self.base_path}")
        
        try:
            self.phase2_organize_files()
            self.phase3_archive_temp_files()
            self.phase4_consolidate_docs()
            self.phase5_clean_redundant_tools()
            self.create_organized_structure_summary()
            
            logger.info("🎉 CLEANUP COMPLETE!")
            logger.info("✅ Workspace is now organized and streamlined")
            logger.info("🎯 Focus on development in the `app/` folder")
            
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")
            raise

if __name__ == "__main__":
    cleanup = WorkspaceCleanup()
    cleanup.run_full_cleanup()
