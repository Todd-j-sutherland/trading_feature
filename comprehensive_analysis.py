#!/usr/bin/env python3
"""
Comprehensive Application Analysis Script
Identifies redundant files, missing dependencies, and critical issues
"""

import os
import sys
import ast
import importlib.util
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Set, Tuple

def find_python_files(root_dir: str) -> List[str]:
    """Find all Python files in the project"""
    python_files = []
    for root, dirs, files in os.walk(root_dir):
        # Skip certain directories
        skip_dirs = {'.git', '__pycache__', 'venv', 'dashboard_venv', 'dashboard_test_venv', 'node_modules'}
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return python_files

def extract_imports(file_path: str) -> Set[str]:
    """Extract all imports from a Python file"""
    imports = set()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module)
                    # Also add specific imports
                    for alias in node.names:
                        full_import = f"{node.module}.{alias.name}"
                        imports.add(full_import)
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
    
    return imports

def analyze_app_main_commands() -> Dict[str, List[str]]:
    """Analyze app.main.py to identify command dependencies"""
    app_main_path = "app/main.py"
    commands = {}
    
    try:
        with open(app_main_path, 'r') as f:
            content = f.read()
        
        # Extract command choices from CLI setup
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call) and 
                hasattr(node.func, 'attr') and 
                node.func.attr == 'add_argument'):
                
                # Look for the command argument
                for arg in node.args:
                    if isinstance(arg, str) and arg == 'command':
                        # Find choices
                        for keyword in node.keywords:
                            if keyword.arg == 'choices':
                                if isinstance(keyword.value, ast.List):
                                    commands['available'] = [elt.s if hasattr(elt, 's') else str(elt.value) 
                                                           for elt in keyword.value.elts]
        
        # Extract imports used by each command by analyzing the main() function
        imports_by_command = defaultdict(list)
        
        # Manual analysis of command handlers (since dynamic import analysis is complex)
        command_handlers = {
            'morning': ['app.services.daily_manager'],
            'evening': ['app.services.daily_manager', 'enhanced_ml_system.analyzers.enhanced_evening_analyzer_with_ml'],
            'status': ['app.services.daily_manager'],
            'dashboard': ['app.dashboard.enhanced_main'],
            'enhanced-dashboard': ['app.dashboard.enhanced_main'],
            'professional-dashboard': ['app.dashboard.pages.professional'],
            'divergence': ['app.core.analysis.divergence', 'app.core.data.processors.news_processor'],
            'economic': ['app.core.analysis.economic'],
            'ml-trading': ['app.core.commands.ml_trading'],
            'ml-scores': ['app.core.commands.ml_trading'],
            'alpaca-setup': ['app.core.trading.alpaca_simulator'],
            'alpaca-test': ['app.core.trading.alpaca_simulator'],
            'pre-trade': ['app.core.ml.trading_manager', 'app.core.trading.alpaca_integration'],
        }
        
        return command_handlers
        
    except Exception as e:
        print(f"Error analyzing app.main.py: {e}")
        return {}

def check_file_exists(module_path: str) -> bool:
    """Check if a module file exists"""
    # Convert module path to file path
    file_path = module_path.replace('.', '/') + '.py'
    return os.path.exists(file_path)

def find_redundant_files(project_root: str) -> Dict[str, List[str]]:
    """Find files that are not used by app.main commands"""
    
    print("🔍 Analyzing project structure for redundant files...")
    
    # Get all Python files
    all_files = find_python_files(project_root)
    
    # Get app.main command dependencies
    command_deps = analyze_app_main_commands()
    
    # Build dependency tree from app.main
    used_files = set()
    
    # Add core app.main dependencies
    core_deps = [
        'app/main.py',
        'app/config/settings.py',
        'app/config/logging.py',
        'app/services/daily_manager.py',
        'app/utils/graceful_shutdown.py'
    ]
    
    for dep in core_deps:
        if os.path.exists(dep):
            used_files.add(os.path.abspath(dep))
    
    # Add command-specific dependencies
    for command, modules in command_deps.items():
        for module in modules:
            file_path = module.replace('.', '/') + '.py'
            if os.path.exists(file_path):
                used_files.add(os.path.abspath(file_path))
                
                # Also analyze dependencies of these files
                deps = extract_imports(file_path)
                for dep in deps:
                    if dep.startswith('app.') or dep.startswith('enhanced_ml_system.'):
                        dep_path = dep.replace('.', '/') + '.py'
                        if os.path.exists(dep_path):
                            used_files.add(os.path.abspath(dep_path))
    
    # Categorize all files
    redundant_categories = {
        'root_scripts': [],
        'dashboard_files': [],
        'ml_files': [],
        'trading_files': [],
        'test_files': [],
        'helper_files': [],
        'api_files': [],
        'collector_files': [],
        'other_files': []
    }
    
    for file_path in all_files:
        abs_path = os.path.abspath(file_path)
        if abs_path not in used_files:
            rel_path = os.path.relpath(file_path, project_root)
            
            # Categorize redundant files
            if rel_path.startswith('test') or 'test_' in rel_path:
                redundant_categories['test_files'].append(rel_path)
            elif rel_path.startswith('helper'):
                redundant_categories['helper_files'].append(rel_path)
            elif 'dashboard' in rel_path and not any(x in rel_path for x in ['enhanced_main.py', 'professional.py']):
                redundant_categories['dashboard_files'].append(rel_path)
            elif rel_path.startswith('app/core/ml') and not any(x in rel_path for x in ['enhanced_training_pipeline.py', 'trading_manager.py']):
                redundant_categories['ml_files'].append(rel_path)
            elif rel_path.startswith('app/core/trading') and not any(x in rel_path for x in ['alpaca_simulator.py', 'alpaca_integration.py']):
                redundant_categories['trading_files'].append(rel_path)
            elif rel_path.startswith('app/api'):
                redundant_categories['api_files'].append(rel_path)
            elif 'collector' in rel_path:
                redundant_categories['collector_files'].append(rel_path)
            elif not rel_path.startswith('app/'):
                redundant_categories['root_scripts'].append(rel_path)
            else:
                redundant_categories['other_files'].append(rel_path)
    
    return redundant_categories

def check_missing_imports() -> List[str]:
    """Check for missing imports referenced by app.main"""
    missing = []
    
    required_modules = [
        'app.config.settings',
        'app.config.logging',
        'app.services.daily_manager',
        'app.utils.graceful_shutdown',
        'app.core.analysis.divergence',
        'app.core.analysis.economic',
        'app.core.commands.ml_trading',
        'app.core.trading.alpaca_simulator',
        'app.core.trading.alpaca_integration',
        'app.core.ml.trading_manager',
        'app.dashboard.enhanced_main',
        'app.dashboard.pages.professional',
        'enhanced_ml_system.analyzers.enhanced_evening_analyzer_with_ml'
    ]
    
    for module in required_modules:
        file_path = module.replace('.', '/') + '.py'
        if not os.path.exists(file_path):
            missing.append(f"{module} -> {file_path}")
    
    return missing

def identify_critical_issues() -> List[str]:
    """Identify critical issues in the application"""
    issues = []
    
    # Check for duplicate files
    duplicates = [
        ('enhanced_evening_analyzer_with_ml.py', 'enhanced_ml_system/analyzers/enhanced_evening_analyzer_with_ml.py'),
        ('enhanced_morning_analyzer_with_ml.py', 'enhanced_ml_system/analyzers/enhanced_morning_analyzer_with_ml.py'),
        ('dashboard.py', 'app/dashboard/enhanced_main.py'),
    ]
    
    for root_file, system_file in duplicates:
        if os.path.exists(root_file) and os.path.exists(system_file):
            issues.append(f"DUPLICATE: {root_file} and {system_file} both exist")
    
    # Check for missing critical files
    critical_files = [
        'app/main.py',
        'app/services/daily_manager.py',
        'app/config/settings.py',
        'enhanced_ml_system/analyzers/enhanced_evening_analyzer_with_ml.py'
    ]
    
    for file in critical_files:
        if not os.path.exists(file):
            issues.append(f"MISSING CRITICAL: {file}")
    
    # Check for broken command references
    app_main_imports = [
        'app.core.trading.continuous_alpaca_trader',  # This doesn't exist
    ]
    
    for imp in app_main_imports:
        file_path = imp.replace('.', '/') + '.py'
        if not os.path.exists(file_path):
            issues.append(f"BROKEN IMPORT in app.main: {imp}")
    
    return issues

def main():
    """Main analysis function"""
    print("🔍 COMPREHENSIVE APPLICATION ANALYSIS")
    print("=" * 60)
    
    project_root = os.getcwd()
    
    # 1. Check missing imports
    print("\n📋 MISSING IMPORTS CHECK")
    print("-" * 30)
    missing = check_missing_imports()
    if missing:
        for item in missing:
            print(f"❌ {item}")
    else:
        print("✅ All required imports found")
    
    # 2. Identify critical issues
    print("\n🚨 CRITICAL ISSUES")
    print("-" * 20)
    issues = identify_critical_issues()
    if issues:
        for issue in issues:
            print(f"🚨 {issue}")
    else:
        print("✅ No critical issues found")
    
    # 3. Find redundant files
    print("\n🗑️ REDUNDANT FILES ANALYSIS")
    print("-" * 30)
    redundant = find_redundant_files(project_root)
    
    total_redundant = sum(len(files) for files in redundant.values())
    print(f"📊 Total redundant files: {total_redundant}")
    
    for category, files in redundant.items():
        if files:
            print(f"\n📁 {category.upper().replace('_', ' ')} ({len(files)} files):")
            for file in sorted(files)[:10]:  # Show first 10
                print(f"   • {file}")
            if len(files) > 10:
                print(f"   ... and {len(files) - 10} more")
    
    # 4. Generate recommendations
    print("\n💡 RECOMMENDATIONS")
    print("-" * 20)
    
    if issues:
        print("🔧 Fix Critical Issues First:")
        for issue in issues:
            if "BROKEN IMPORT" in issue:
                print(f"   • Remove or fix import: {issue.split(': ')[1]}")
            elif "DUPLICATE" in issue:
                print(f"   • Archive redundant file: {issue.split('and')[0].split(':')[1].strip()}")
            elif "MISSING CRITICAL" in issue:
                print(f"   • Create missing file: {issue.split(': ')[1]}")
    
    if total_redundant > 0:
        print(f"\n📦 Archive {total_redundant} redundant files:")
        print("   • Create archive/unused_by_main/ directory")
        print("   • Move redundant files to maintain structure")
        print("   • Test system after archiving")
    
    # 5. Generate cleanup script
    print("\n📝 CLEANUP SCRIPT RECOMMENDATION")
    print("-" * 35)
    
    print("Create and run this script to clean up the project:")
    print("""
#!/bin/bash
# cleanup_project.sh

echo "🧹 Cleaning up trading_feature project..."

# Create archive directory
mkdir -p archive/unused_by_main

# Move redundant root scripts""")
    
    if redundant['root_scripts']:
        for file in redundant['root_scripts'][:5]:  # Show first 5 as example
            print(f"# mv '{file}' archive/unused_by_main/")
    
    print("""
# Move redundant app files
# (Add specific mv commands for redundant app files)

echo "✅ Project cleanup complete!"
echo "🧪 Test the system: python -m app.main status"
""")

if __name__ == "__main__":
    main()
