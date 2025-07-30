#!/usr/bin/env python3
"""
App.main Dependencies Analysis
Traces all files used by each app.main command to identify redundant files
"""

import os
import re
import ast
from pathlib import Path
from typing import Dict, List, Set
from collections import defaultdict

class DependencyAnalyzer:
    """Analyze file dependencies for app.main commands"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.dependencies = defaultdict(set)
        self.all_files = set()
        self.archive_files = set()
        self.legacy_files = set()
        
    def find_all_files(self):
        """Find all Python files in the project"""
        for path in self.project_root.rglob("*.py"):
            relative_path = path.relative_to(self.project_root)
            self.all_files.add(str(relative_path))
            
            # Check if it's in archive/legacy folders
            if any(part in ['archive', 'legacy', 'legacy_enhanced'] for part in relative_path.parts):
                if 'archive' in relative_path.parts:
                    self.archive_files.add(str(relative_path))
                else:
                    self.legacy_files.add(str(relative_path))
    
    def extract_imports_from_file(self, file_path: Path) -> Set[str]:
        """Extract import statements from a Python file"""
        imports = set()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST to get imports
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.add(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            imports.add(node.module)
            except SyntaxError:
                pass
            
            # Also check for dynamic imports and subprocess calls
            import_patterns = [
                r'from\s+([a-zA-Z_][a-zA-Z0-9_.]*)\s+import',
                r'import\s+([a-zA-Z_][a-zA-Z0-9_.]*)',
                r'subprocess\.run\(\s*\["([^"]+)"',
                r'subprocess\.call\(\s*\["([^"]+)"',
                r'__import__\(\s*["\']([^"\']+)["\']',
            ]
            
            for pattern in import_patterns:
                matches = re.findall(pattern, content)
                imports.update(matches)
                
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            
        return imports
    
    def trace_command_dependencies(self, command: str, starting_files: List[str]) -> Set[str]:
        """Trace all dependencies for a specific command"""
        visited = set()
        dependencies = set()
        to_visit = starting_files.copy()
        
        while to_visit:
            current_file = to_visit.pop()
            if current_file in visited:
                continue
                
            visited.add(current_file)
            dependencies.add(current_file)
            
            # Find the actual file
            file_path = self.project_root / current_file
            if not file_path.exists():
                # Try with .py extension
                file_path = self.project_root / f"{current_file}.py"
                if not file_path.exists():
                    continue
            
            # Extract imports from this file
            imports = self.extract_imports_from_file(file_path)
            
            # Convert imports to file paths
            for imp in imports:
                potential_files = self.resolve_import_to_files(imp)
                for pf in potential_files:
                    if pf not in visited and pf in self.all_files:
                        to_visit.append(pf)
        
        return dependencies
    
    def resolve_import_to_files(self, import_name: str) -> List[str]:
        """Convert import statement to potential file paths"""
        potential_files = []
        
        # Handle app.* imports
        if import_name.startswith('app.'):
            module_path = import_name.replace('.', '/')
            potential_files.extend([
                f"{module_path}.py",
                f"{module_path}/__init__.py",
            ])
        
        # Handle enhanced_ml_system imports
        if import_name.startswith('enhanced_ml_system'):
            module_path = import_name.replace('.', '/')
            potential_files.extend([
                f"{module_path}.py",
                f"{module_path}/__init__.py",
            ])
        
        # Handle direct file references
        if '/' in import_name or '\\' in import_name:
            potential_files.append(import_name.replace('\\', '/'))
        
        # Handle root level modules
        potential_files.extend([
            f"{import_name}.py",
            f"{import_name}/__init__.py",
        ])
        
        return potential_files
    
    def analyze_main_commands(self) -> Dict[str, Set[str]]:
        """Analyze dependencies for all app.main commands"""
        
        # Define the command mappings based on app/main.py analysis
        command_mappings = {
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
            'divergence': [],  # Defined in main.py itself
            'economic': [],   # Defined in main.py itself
            'ml-scores': ['app/core/ml/trading_manager.py'],
            'ml-trading': ['app/core/ml/trading_manager.py'],
            'pre-trade': ['app/core/ml/trading_manager.py'],
            'alpaca-setup': ['app/core/trading/alpaca_simulator.py'],
            'alpaca-test': ['app/core/trading/alpaca_integration.py'],
            'start-trading': [],  # Defined in main.py itself
            'trading-history': [],  # Uses database directly
            'ml-analyze': ['app/core/ml/trading_manager.py'],
            'ml-trade': ['app/core/ml/trading_manager.py'],
            'ml-status': [],  # Defined in main.py itself
            'ml-dashboard': [],  # Defined in main.py itself
        }
        
        results = {}
        
        for command, starting_files in command_mappings.items():
            print(f"Analyzing command: {command}")
            if starting_files:
                dependencies = self.trace_command_dependencies(command, starting_files)
            else:
                # Commands defined directly in main.py
                dependencies = self.trace_command_dependencies(command, ['app/main.py'])
            
            results[command] = dependencies
            
        return results
    
    def find_unused_files(self, command_dependencies: Dict[str, Set[str]]) -> Dict[str, List[str]]:
        """Find files that are not used by any app.main command"""
        
        # Get all files used by any command
        used_files = set()
        for deps in command_dependencies.values():
            used_files.update(deps)
        
        # Find unused files (excluding already archived/legacy files)
        unused_files = self.all_files - used_files - self.archive_files - self.legacy_files
        
        # Categorize unused files
        categories = {
            'analyzers': [],
            'data_collectors': [],
            'ml_models': [],
            'dashboard_files': [],
            'scripts': [],
            'other': []
        }
        
        for file in unused_files:
            if 'analyzer' in file.lower():
                categories['analyzers'].append(file)
            elif 'collector' in file.lower() or 'data' in file.lower():
                categories['data_collectors'].append(file)
            elif 'ml' in file.lower() or 'model' in file.lower():
                categories['ml_models'].append(file)
            elif 'dashboard' in file.lower() or 'streamlit' in file.lower():
                categories['dashboard_files'].append(file)
            elif file.endswith('.py') and '/' not in file:
                categories['scripts'].append(file)
            else:
                categories['other'].append(file)
                
        return categories
    
    def generate_report(self):
        """Generate comprehensive analysis report"""
        print("🔍 APP.MAIN DEPENDENCY ANALYSIS")
        print("=" * 50)
        
        # Find all files
        self.find_all_files()
        print(f"📁 Total Python files found: {len(self.all_files)}")
        print(f"📦 Already archived: {len(self.archive_files)}")
        print(f"🏛️ Already in legacy: {len(self.legacy_files)}")
        
        # Analyze commands
        command_deps = self.analyze_main_commands()
        
        print(f"\n📊 COMMAND DEPENDENCY SUMMARY")
        print("-" * 30)
        for command, deps in sorted(command_deps.items()):
            print(f"{command:20} {len(deps):3} files")
        
        # Find unused files
        unused_files = self.find_unused_files(command_deps)
        
        print(f"\n🗑️ FILES NOT USED BY ANY APP.MAIN COMMAND")
        print("-" * 40)
        
        total_unused = sum(len(files) for files in unused_files.values())
        print(f"Total unused files: {total_unused}")
        
        for category, files in unused_files.items():
            if files:
                print(f"\n📂 {category.upper()} ({len(files)} files):")
                for file in sorted(files)[:10]:  # Show first 10
                    print(f"   • {file}")
                if len(files) > 10:
                    print(f"   ... and {len(files) - 10} more")
        
        return {
            'command_dependencies': command_deps,
            'unused_files': unused_files,
            'total_files': len(self.all_files),
            'archived_files': len(self.archive_files),
            'legacy_files': len(self.legacy_files)
        }

if __name__ == "__main__":
    project_root = "/Users/toddsutherland/Repos/trading_feature"
    analyzer = DependencyAnalyzer(project_root)
    results = analyzer.generate_report()
    
    # Generate archive recommendations
    print(f"\n🏗️ ARCHIVE RECOMMENDATIONS")
    print("-" * 30)
    
    archive_candidates = []
    for category, files in results['unused_files'].items():
        archive_candidates.extend(files)
    
    if archive_candidates:
        print(f"✅ Safe to archive: {len(archive_candidates)} files")
        print("\n📋 Recommended archive commands:")
        print("mkdir -p archive/unused_by_main")
        
        for file in sorted(archive_candidates)[:20]:  # Show first 20
            print(f"mv {file} archive/unused_by_main/")
        
        if len(archive_candidates) > 20:
            print(f"# ... and {len(archive_candidates) - 20} more files")
    else:
        print("✅ No obvious candidates for archiving found")
