#!/usr/bin/env python3
"""
Refined App.main Dependencies Analysis
Focus on actual project files, excluding venv, __pycache__, etc.
"""

import os
import re
import ast
from pathlib import Path
from typing import Dict, List, Set
from collections import defaultdict

class RefinedDependencyAnalyzer:
    """Analyze file dependencies for app.main commands - project files only"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.dependencies = defaultdict(set)
        self.project_files = set()
        self.archive_files = set()
        self.legacy_files = set()
        
        # Exclude patterns
        self.exclude_patterns = [
            'venv/', 'dashboard_venv/', '__pycache__/', '.git/', 
            'node_modules/', '.pytest_cache/', '.vscode/',
            'frontend/', 'mcp_server/', 'tests/', 'docs/', 'logs/',
            'data/', 'metrics_exports/', 'reports/', 'utils/',
            '.py~', '.bak', '.tmp'
        ]
        
    def should_exclude_file(self, file_path: str) -> bool:
        """Check if file should be excluded from analysis"""
        for pattern in self.exclude_patterns:
            if pattern in file_path or file_path.startswith(pattern):
                return True
        return False
        
    def find_project_files(self):
        """Find all Python files in the project (excluding venv, cache, etc.)"""
        for path in self.project_root.rglob("*.py"):
            relative_path = path.relative_to(self.project_root)
            relative_str = str(relative_path)
            
            # Skip excluded files
            if self.should_exclude_file(relative_str):
                continue
                
            self.project_files.add(relative_str)
            
            # Check if it's in archive/legacy folders
            if any(part in ['archive', 'legacy', 'legacy_enhanced'] for part in relative_path.parts):
                if 'archive' in relative_path.parts:
                    self.archive_files.add(relative_str)
                else:
                    self.legacy_files.add(relative_str)
    
    def get_direct_imports(self, file_path: Path) -> Set[str]:
        """Get direct imports from a file"""
        imports = set()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for project-specific imports
            patterns = [
                r'from\s+(app\.[a-zA-Z0-9_.]+)\s+import',
                r'import\s+(app\.[a-zA-Z0-9_.]+)',
                r'from\s+(enhanced_ml_system\.[a-zA-Z0-9_.]+)\s+import',
                r'import\s+(enhanced_ml_system\.[a-zA-Z0-9_.]+)',
                r'from\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+import',  # Root level imports
                r'import\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    # Only include project modules
                    if (match.startswith('app.') or 
                        match.startswith('enhanced_ml_system.') or
                        not '.' in match):
                        imports.add(match)
                        
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            
        return imports
    
    def resolve_import_to_file(self, import_name: str) -> str:
        """Convert import to actual file path"""
        # Handle app.* imports
        if import_name.startswith('app.'):
            module_path = import_name.replace('.', '/')
            potential_file = f"{module_path}.py"
            if potential_file in self.project_files:
                return potential_file
        
        # Handle enhanced_ml_system imports
        if import_name.startswith('enhanced_ml_system.'):
            module_path = import_name.replace('.', '/')
            potential_file = f"{module_path}.py"
            if potential_file in self.project_files:
                return potential_file
        
        # Handle root level files
        potential_file = f"{import_name}.py"
        if potential_file in self.project_files:
            return potential_file
            
        return None
    
    def trace_dependencies(self, start_file: str, max_depth: int = 3) -> Set[str]:
        """Trace dependencies starting from a file"""
        dependencies = set()
        visited = set()
        to_visit = [(start_file, 0)]
        
        while to_visit:
            current_file, depth = to_visit.pop(0)
            
            if current_file in visited or depth > max_depth:
                continue
                
            visited.add(current_file)
            dependencies.add(current_file)
            
            # Find the actual file path
            file_path = self.project_root / current_file
            if not file_path.exists():
                continue
            
            # Get imports from this file
            imports = self.get_direct_imports(file_path)
            
            # Add imported files to visit list
            for imp in imports:
                dep_file = self.resolve_import_to_file(imp)
                if dep_file and dep_file not in visited:
                    to_visit.append((dep_file, depth + 1))
        
        return dependencies
    
    def analyze_commands(self) -> Dict[str, Dict]:
        """Analyze each app.main command"""
        
        # Core files used by commands (manually identified)
        command_entry_points = {
            'morning': ['app/services/daily_manager.py'],
            'evening': ['app/services/daily_manager.py', 'enhanced_ml_system/analyzers/enhanced_evening_analyzer_with_ml.py'],
            'status': ['app/services/daily_manager.py'],
            'weekly': ['app/services/daily_manager.py'],
            'restart': ['app/services/daily_manager.py'],
            'test': ['app/services/daily_manager.py'],
            'dashboard': ['app/dashboard/enhanced_main.py'],
            'enhanced-dashboard': ['app/dashboard/enhanced_main.py'],
            'professional-dashboard': ['app/dashboard/pages/professional.py'],
            'news': ['app/services/daily_manager.py'],
            'ml-scores': ['app/core/ml/trading_manager.py'],
            'ml-trading': ['app/core/ml/trading_manager.py'],
            'pre-trade': ['app/core/ml/trading_manager.py'],
            'alpaca-setup': ['app/core/trading/alpaca_simulator.py'],
            'alpaca-test': ['app/core/trading/alpaca_integration.py'],
        }
        
        results = {}
        
        for command, entry_files in command_entry_points.items():
            print(f"Analyzing {command}...")
            dependencies = set()
            
            for entry_file in entry_files:
                if entry_file in self.project_files:
                    deps = self.trace_dependencies(entry_file)
                    dependencies.update(deps)
            
            results[command] = {
                'entry_points': entry_files,
                'dependencies': dependencies,
                'total_files': len(dependencies)
            }
        
        return results
    
    def find_redundant_files(self, command_analysis: Dict) -> Dict[str, List[str]]:
        """Find files not used by any app.main command"""
        
        # Get all used files
        used_files = set()
        for cmd_info in command_analysis.values():
            used_files.update(cmd_info['dependencies'])
        
        # Add core system files that are always needed
        core_files = {
            'app/main.py',
            'app/config/settings.py',
            'app/config/logging.py',
            'app/utils/graceful_shutdown.py',
        }
        used_files.update(core_files)
        
        # Find unused files
        unused_files = self.project_files - used_files - self.archive_files - self.legacy_files
        
        # Categorize unused files
        categories = {
            'root_scripts': [],
            'analyzers': [],
            'collectors': [],
            'ml_files': [],
            'dashboard_components': [],
            'api_files': [],
            'other_app_files': []
        }
        
        for file in sorted(unused_files):
            if '/' not in file and file.endswith('.py'):
                categories['root_scripts'].append(file)
            elif 'analyzer' in file.lower():
                categories['analyzers'].append(file)
            elif 'collector' in file.lower():
                categories['collectors'].append(file)
            elif 'ml' in file.lower() or 'model' in file.lower():
                categories['ml_files'].append(file)
            elif 'dashboard' in file.lower():
                categories['dashboard_components'].append(file)
            elif 'api' in file.lower():
                categories['api_files'].append(file)
            elif file.startswith('app/'):
                categories['other_app_files'].append(file)
                
        return categories
    
    def generate_report(self):
        """Generate analysis report"""
        print("🔍 REFINED APP.MAIN DEPENDENCY ANALYSIS")
        print("=" * 50)
        
        # Find project files
        self.find_project_files()
        print(f"📁 Project Python files: {len(self.project_files)}")
        print(f"📦 Already archived: {len(self.archive_files)}")
        print(f"🏛️ Already in legacy: {len(self.legacy_files)}")
        
        # Analyze commands
        command_analysis = self.analyze_commands()
        
        print(f"\n📊 COMMAND USAGE ANALYSIS")
        print("-" * 30)
        for command, info in sorted(command_analysis.items()):
            print(f"{command:20} {info['total_files']:3} files")
        
        # Find redundant files
        redundant_files = self.find_redundant_files(command_analysis)
        
        print(f"\n🗑️ REDUNDANT FILES (Safe to Archive)")
        print("-" * 40)
        
        total_redundant = sum(len(files) for files in redundant_files.values())
        print(f"Total redundant files: {total_redundant}")
        
        archive_commands = []
        
        for category, files in redundant_files.items():
            if files:
                print(f"\n📂 {category.upper().replace('_', ' ')} ({len(files)} files):")
                for file in files:
                    print(f"   • {file}")
                    archive_commands.append(f"mv {file} archive/unused_by_main/")
        
        # Generate archive script
        if archive_commands:
            print(f"\n🏗️ ARCHIVE SCRIPT")
            print("-" * 20)
            print("#!/bin/bash")
            print("# Archive redundant files")
            print("mkdir -p archive/unused_by_main")
            print()
            for cmd in archive_commands[:30]:  # Show first 30
                print(cmd)
            if len(archive_commands) > 30:
                print(f"# ... and {len(archive_commands) - 30} more files")
        
        return {
            'command_analysis': command_analysis,
            'redundant_files': redundant_files,
            'total_redundant': total_redundant
        }

if __name__ == "__main__":
    project_root = "/Users/toddsutherland/Repos/trading_feature"
    analyzer = RefinedDependencyAnalyzer(project_root)
    results = analyzer.generate_report()
