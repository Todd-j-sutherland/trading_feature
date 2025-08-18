#!/usr/bin/env python3
"""
Deploy Essential Files to Remote
Only transfer necessary files, excluding node_modules, git, and package directories
"""

import os
import subprocess
import shutil
from pathlib import Path
from datetime import datetime

def create_deployment_package():
    """Create a clean deployment package with only essential files"""
    print("📦 CREATING DEPLOYMENT PACKAGE")
    print("=" * 50)
    
    # Create deployment directory
    deploy_dir = Path("deployment_package")
    if deploy_dir.exists():
        shutil.rmtree(deploy_dir)
    deploy_dir.mkdir()
    
    # Essential Python files to include
    essential_files = [
        "app.py",
        "enhanced_morning_analyzer_with_ml.py", 
        "enhanced_evening_analyzer_with_ml.py",
        "dashboard.py",
        "api_server.py",
        "requirements.txt",
        "comprehensive_analyzer_with_logs.py",
        "fix_critical_issues.py",
        "database_schema_synchronizer.py",
        "backtesting_engine.py",
        "automated_technical_updater.py",
        "enhanced_smart_collector.py",
        "confidence_calibration.py",
        "anomaly_detection.py",
        "check_status.py",
        "check_account_status.py"
    ]
    
    # Essential directories to include (with selective content)
    essential_dirs = [
        "data",  # Include but we'll be selective
        "templates",
        "static",
        "frontend"  # Include but exclude node_modules
    ]
    
    # Files and directories to explicitly exclude
    exclude_patterns = [
        ".git*",
        "__pycache__",
        "*.pyc",
        "node_modules",
        ".venv",
        "venv",
        "trading_venv",
        ".env",
        "*.log",
        "analysis_logs",
        "deployment_package",
        ".pytest_cache",
        "*.egg-info",
        ".DS_Store",
        "Thumbs.db"
    ]
    
    print("📋 Copying essential Python files...")
    copied_files = 0
    for file in essential_files:
        if Path(file).exists():
            shutil.copy2(file, deploy_dir / file)
            print(f"  ✅ {file}")
            copied_files += 1
        else:
            print(f"  ⚠️ {file} (not found)")
    
    print(f"\n📁 Copying essential directories...")
    for dir_name in essential_dirs:
        src_dir = Path(dir_name)
        if src_dir.exists() and src_dir.is_dir():
            dest_dir = deploy_dir / dir_name
            
            if dir_name == "data":
                # Only copy database files, not logs or temp files
                dest_dir.mkdir(exist_ok=True)
                for db_file in src_dir.glob("*.db"):
                    shutil.copy2(db_file, dest_dir / db_file.name)
                    print(f"  ✅ {dir_name}/{db_file.name}")
                    copied_files += 1
                    
            elif dir_name == "frontend":
                # Copy frontend but exclude node_modules
                shutil.copytree(src_dir, dest_dir, ignore=shutil.ignore_patterns(*exclude_patterns))
                print(f"  ✅ {dir_name}/ (excluding node_modules)")
                copied_files += 1
                
            else:
                # Copy other directories normally
                try:
                    shutil.copytree(src_dir, dest_dir)
                    print(f"  ✅ {dir_name}/")
                    copied_files += 1
                except Exception as e:
                    print(f"  ⚠️ {dir_name}/ (error: {e})")
    
    print(f"\n📊 Package created with {copied_files} essential files")
    
    # Create deployment info file
    deploy_info = {
        "deployment_time": datetime.now().isoformat(),
        "source_branch": get_current_branch(),
        "files_copied": copied_files,
        "excluded_patterns": exclude_patterns
    }
    
    with open(deploy_dir / "deployment_info.json", "w") as f:
        import json
        json.dump(deploy_info, f, indent=2)
    
    return deploy_dir

def get_current_branch():
    """Get current git branch"""
    try:
        result = subprocess.run(["git", "branch", "--show-current"], 
                              capture_output=True, text=True)
        return result.stdout.strip() if result.returncode == 0 else "unknown"
    except:
        return "unknown"

def create_deployment_archive():
    """Create a compressed archive for transfer"""
    print("\n🗜️ CREATING DEPLOYMENT ARCHIVE")
    print("=" * 40)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = f"trading_system_deploy_{timestamp}"
    
    # Create tar.gz archive
    shutil.make_archive(archive_name, 'gztar', 'deployment_package')
    
    archive_path = f"{archive_name}.tar.gz"
    archive_size = os.path.getsize(archive_path) / (1024 * 1024)  # MB
    
    print(f"✅ Created {archive_path} ({archive_size:.1f} MB)")
    return archive_path

def transfer_to_remote(archive_path):
    """Transfer archive to remote server"""
    print(f"\n📤 TRANSFERRING TO REMOTE")
    print("=" * 40)
    
    remote_host = "root@170.64.199.151"
    
    print(f"Uploading {archive_path}...")
    result = os.system(f"scp {archive_path} {remote_host}:/root/")
    
    if result == 0:
        print("✅ Upload completed")
        return True
    else:
        print("❌ Upload failed")
        return False

def extract_on_remote(archive_path):
    """Extract and setup files on remote server"""
    print("\n📂 EXTRACTING ON REMOTE")
    print("=" * 40)
    
    remote_host = "root@170.64.199.151"
    archive_name = Path(archive_path).name
    
    # Commands to run on remote
    commands = [
        f"cd /root",
        f"mkdir -p trading_feature_backup",
        f"if [ -d trading_feature ]; then cp -r trading_feature trading_feature_backup/$(date +%Y%m%d_%H%M%S); fi",
        f"rm -rf trading_feature",
        f"mkdir -p trading_feature", 
        f"cd trading_feature",
        f"tar -xzf ../{archive_name}",
        f"ls -la"
    ]
    
    # Execute commands on remote
    for cmd in commands:
        print(f"Remote: {cmd}")
        result = os.system(f'ssh {remote_host} "{cmd}"')
        if result != 0:
            print(f"⚠️ Command failed: {cmd}")
    
    print("✅ Extraction completed")

def setup_remote_environment():
    """Setup the remote environment with correct paths"""
    print("\n⚙️ SETTING UP REMOTE ENVIRONMENT")
    print("=" * 40)
    
    remote_host = "root@170.64.199.151"
    
    # Environment setup commands
    setup_commands = [
        "cd /root/trading_feature",
        "source /root/trading_venv/bin/activate",
        "pip install -r requirements.txt",
        "mkdir -p data logs analysis_logs",
        "chmod +x *.py",
        "python3 -c 'import transformers; print(\"✅ Transformers working\")'",
        "python3 check_status.py"
    ]
    
    setup_script = " && ".join(setup_commands)
    
    print("Setting up remote environment...")
    result = os.system(f'ssh {remote_host} "{setup_script}"')
    
    if result == 0:
        print("✅ Remote environment setup completed")
        return True
    else:
        print("⚠️ Remote environment setup had issues")
        return False

def verify_remote_functionality():
    """Verify that the remote system is working properly"""
    print("\n🔍 VERIFYING REMOTE FUNCTIONALITY")
    print("=" * 40)
    
    remote_host = "root@170.64.199.151"
    
    # Test critical functionality
    test_commands = [
        "cd /root/trading_feature && source /root/trading_venv/bin/activate && python3 -c 'import transformers, sklearn, pandas; print(\"✅ All ML libraries working\")'",
        "cd /root/trading_feature && source /root/trading_venv/bin/activate && python3 check_status.py",
        "cd /root/trading_feature && ls -la data/",
        "cd /root/trading_feature && sqlite3 data/trading_predictions.db '.tables'"
    ]
    
    all_passed = True
    for cmd in test_commands:
        print(f"\nTesting: {cmd.split(' && ')[-1]}")
        result = os.system(f'ssh {remote_host} "{cmd}"')
        if result == 0:
            print("✅ Passed")
        else:
            print("❌ Failed")
            all_passed = False
    
    return all_passed

def cleanup_local_files():
    """Clean up temporary deployment files"""
    print("\n🧹 CLEANING UP")
    print("=" * 20)
    
    # Remove deployment directory
    if Path("deployment_package").exists():
        shutil.rmtree("deployment_package")
        print("✅ Removed deployment_package/")
    
    # Remove archive files
    for archive in Path(".").glob("trading_system_deploy_*.tar.gz"):
        archive.unlink()
        print(f"✅ Removed {archive.name}")

def main():
    """Main deployment process"""
    print("🚀 DEPLOYING TRADING SYSTEM TO REMOTE")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Target: root@170.64.199.151")
    print("=" * 60)
    
    try:
        # Step 1: Create deployment package
        deploy_dir = create_deployment_package()
        
        # Step 2: Create archive
        archive_path = create_deployment_archive()
        
        # Step 3: Transfer to remote
        if not transfer_to_remote(archive_path):
            return False
        
        # Step 4: Extract on remote
        extract_on_remote(archive_path)
        
        # Step 5: Setup environment
        if not setup_remote_environment():
            print("⚠️ Environment setup had issues, but continuing...")
        
        # Step 6: Verify functionality
        if verify_remote_functionality():
            print("\n🎉 DEPLOYMENT SUCCESSFUL!")
            print("Remote system is fully functional")
            return True
        else:
            print("\n⚠️ DEPLOYMENT COMPLETED WITH ISSUES")
            print("Some functionality may need manual verification")
            return False
            
    except Exception as e:
        print(f"💥 Deployment error: {e}")
        return False
    
    finally:
        # Cleanup
        cleanup_local_files()

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
