#!/usr/bin/env python3
"""
Continuous Integration Test Pipeline

This module provides automated testing pipeline for continuous integration,
including test execution, coverage reporting, and quality gates.

Author: Trading System Testing Team  
Date: September 14, 2025
"""

import os
import sys
import subprocess
import time
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import tempfile
import shutil

class CITestPipeline:
    """Continuous Integration test pipeline for trading microservices"""
    
    def __init__(self, workspace_dir: str = None):
        self.workspace_dir = workspace_dir or os.getcwd()
        self.test_dir = os.path.join(self.workspace_dir, "tests")
        self.reports_dir = os.path.join(self.workspace_dir, "test_reports")
        self.results = {}
        
        # Ensure reports directory exists
        os.makedirs(self.reports_dir, exist_ok=True)
        
    def run_full_test_suite(self) -> Dict[str, Any]:
        """Run complete test suite with reporting"""
        print("🚀 Starting Continuous Integration Test Pipeline")
        print("=" * 80)
        
        pipeline_start = time.time()
        overall_success = True
        
        # Test execution order
        test_phases = [
            ("lint", self.run_linting),
            ("unit", self.run_unit_tests),
            ("integration", self.run_integration_tests),
            ("performance", self.run_performance_tests),
            ("security", self.run_security_tests),
            ("coverage", self.run_coverage_analysis)
        ]
        
        for phase_name, phase_func in test_phases:
            print(f"\n📋 Phase: {phase_name.upper()}")
            print("-" * 40)
            
            phase_start = time.time()
            
            try:
                result = phase_func()
                phase_duration = time.time() - phase_start
                
                self.results[phase_name] = {
                    **result,
                    "duration": phase_duration,
                    "timestamp": datetime.now().isoformat()
                }
                
                if result.get("success", False):
                    print(f"✅ {phase_name.upper()} passed ({phase_duration:.2f}s)")
                else:
                    print(f"❌ {phase_name.upper()} failed ({phase_duration:.2f}s)")
                    overall_success = False
                    
                    # Stop on critical failures
                    if phase_name in ["lint", "unit"] and not result.get("success"):
                        print(f"💥 Critical failure in {phase_name}, stopping pipeline")
                        break
                        
            except Exception as e:
                phase_duration = time.time() - phase_start
                print(f"💥 {phase_name.upper()} crashed: {e}")
                
                self.results[phase_name] = {
                    "success": False,
                    "error": str(e),
                    "duration": phase_duration,
                    "timestamp": datetime.now().isoformat()
                }
                
                overall_success = False
                break
                
        # Generate final report
        pipeline_duration = time.time() - pipeline_start
        final_report = self.generate_final_report(overall_success, pipeline_duration)
        
        print("\n" + "=" * 80)
        print("CI PIPELINE SUMMARY")
        print("=" * 80)
        
        self.print_summary_report(final_report)
        
        return final_report
        
    def run_linting(self) -> Dict[str, Any]:
        """Run code linting and style checks"""
        lint_results = {
            "success": True,
            "checks": {},
            "issues": []
        }
        
        # Check if pylint is available
        try:
            subprocess.run(["pylint", "--version"], 
                         capture_output=True, check=True)
            has_pylint = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            has_pylint = False
            
        # Check if flake8 is available
        try:
            subprocess.run(["flake8", "--version"], 
                         capture_output=True, check=True)
            has_flake8 = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            has_flake8 = False
            
        # Run pylint if available
        if has_pylint:
            try:
                services_dir = os.path.join(self.workspace_dir, "services")
                if os.path.exists(services_dir):
                    result = subprocess.run([
                        "pylint", services_dir,
                        "--output-format=json",
                        "--disable=C0103,C0111,R0903,R0913"  # Disable some warnings
                    ], capture_output=True, text=True)
                    
                    if result.stdout:
                        pylint_issues = json.loads(result.stdout)
                        critical_issues = [issue for issue in pylint_issues 
                                         if issue.get("type") in ["error", "fatal"]]
                        
                        lint_results["checks"]["pylint"] = {
                            "total_issues": len(pylint_issues),
                            "critical_issues": len(critical_issues),
                            "passed": len(critical_issues) == 0
                        }
                        
                        if critical_issues:
                            lint_results["success"] = False
                            lint_results["issues"].extend(critical_issues)
                    else:
                        lint_results["checks"]["pylint"] = {"passed": True}
                        
            except Exception as e:
                lint_results["checks"]["pylint"] = {"error": str(e), "passed": False}
                
        # Run flake8 if available
        if has_flake8:
            try:
                services_dir = os.path.join(self.workspace_dir, "services")
                if os.path.exists(services_dir):
                    result = subprocess.run([
                        "flake8", services_dir,
                        "--max-line-length=120",
                        "--ignore=E402,W503"  # Ignore some warnings
                    ], capture_output=True, text=True)
                    
                    flake8_issues = result.stdout.strip()
                    
                    lint_results["checks"]["flake8"] = {
                        "issues_found": len(flake8_issues.split('\n')) if flake8_issues else 0,
                        "passed": not flake8_issues
                    }
                    
                    if flake8_issues:
                        lint_results["success"] = False
                        lint_results["issues"].append({"tool": "flake8", "output": flake8_issues})
                        
            except Exception as e:
                lint_results["checks"]["flake8"] = {"error": str(e), "passed": False}
                
        # Basic Python syntax check
        syntax_issues = []
        services_dir = os.path.join(self.workspace_dir, "services")
        
        if os.path.exists(services_dir):
            for py_file in Path(services_dir).glob("**/*.py"):
                try:
                    with open(py_file, 'r') as f:
                        compile(f.read(), py_file, 'exec')
                except SyntaxError as e:
                    syntax_issues.append({
                        "file": str(py_file),
                        "line": e.lineno,
                        "error": str(e)
                    })
                    
        lint_results["checks"]["syntax"] = {
            "files_checked": len(list(Path(services_dir).glob("**/*.py"))) if os.path.exists(services_dir) else 0,
            "syntax_errors": len(syntax_issues),
            "passed": len(syntax_issues) == 0
        }
        
        if syntax_issues:
            lint_results["success"] = False
            lint_results["issues"].extend(syntax_issues)
            
        return lint_results
        
    def run_unit_tests(self) -> Dict[str, Any]:
        """Run unit tests"""
        unit_test_file = os.path.join(self.test_dir, "test_unit.py")
        
        if not os.path.exists(unit_test_file):
            return {
                "success": False,
                "error": "Unit test file not found",
                "tests_run": 0,
                "failures": 0,
                "errors": 0
            }
            
        try:
            # Run unit tests
            result = subprocess.run([
                sys.executable, "-m", "unittest", "tests.test_unit", "-v"
            ], capture_output=True, text=True, cwd=self.workspace_dir)
            
            # Parse test results
            output_lines = result.stderr.split('\n')
            
            tests_run = 0
            failures = 0
            errors = 0
            
            for line in output_lines:
                if "Ran " in line and " test" in line:
                    tests_run = int(line.split()[1])
                elif "FAILED (failures=" in line:
                    # Parse failures and errors
                    parts = line.split('(')[1].split(')')[0]
                    for part in parts.split(', '):
                        if 'failures=' in part:
                            failures = int(part.split('=')[1])
                        elif 'errors=' in part:
                            errors = int(part.split('=')[1])
                            
            success = result.returncode == 0
            
            return {
                "success": success,
                "tests_run": tests_run,
                "failures": failures,
                "errors": errors,
                "output": result.stderr,
                "return_code": result.returncode
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "tests_run": 0,
                "failures": 0,
                "errors": 1
            }
            
    def run_integration_tests(self) -> Dict[str, Any]:
        """Run integration tests"""
        integration_test_file = os.path.join(self.test_dir, "test_integration.py")
        
        if not os.path.exists(integration_test_file):
            return {
                "success": False,
                "error": "Integration test file not found",
                "tests_run": 0,
                "failures": 0,
                "errors": 0
            }
            
        try:
            # Run integration tests
            result = subprocess.run([
                sys.executable, integration_test_file
            ], capture_output=True, text=True, cwd=self.workspace_dir)
            
            # Parse output for test results
            success = result.returncode == 0
            output = result.stdout + result.stderr
            
            return {
                "success": success,
                "output": output,
                "return_code": result.returncode,
                "tests_run": output.count("test_") if success else 0,
                "failures": output.count("FAIL") if not success else 0,
                "errors": output.count("ERROR") if not success else 0
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "tests_run": 0,
                "failures": 0,
                "errors": 1
            }
            
    def run_performance_tests(self) -> Dict[str, Any]:
        """Run performance tests"""
        performance_test_file = os.path.join(self.test_dir, "test_performance.py")
        
        if not os.path.exists(performance_test_file):
            return {
                "success": True,
                "warning": "Performance test file not found - skipping",
                "tests_run": 0
            }
            
        try:
            # Run performance tests with timeout
            result = subprocess.run([
                sys.executable, performance_test_file
            ], capture_output=True, text=True, cwd=self.workspace_dir, timeout=300)  # 5 min timeout
            
            success = result.returncode == 0
            output = result.stdout + result.stderr
            
            return {
                "success": success,
                "output": output,
                "return_code": result.returncode,
                "tests_run": output.count("test_") if success else 0,
                "performance_issues": output.count("FAIL") if not success else 0
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Performance tests timed out (300s)",
                "tests_run": 0,
                "performance_issues": 1
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "tests_run": 0,
                "performance_issues": 1
            }
            
    def run_security_tests(self) -> Dict[str, Any]:
        """Run security tests"""
        security_results = {
            "success": True,
            "checks": {},
            "vulnerabilities": []
        }
        
        # Check for bandit (security linter)
        try:
            subprocess.run(["bandit", "--version"], 
                         capture_output=True, check=True)
            has_bandit = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            has_bandit = False
            
        if has_bandit:
            try:
                services_dir = os.path.join(self.workspace_dir, "services")
                if os.path.exists(services_dir):
                    result = subprocess.run([
                        "bandit", "-r", services_dir, "-f", "json"
                    ], capture_output=True, text=True)
                    
                    if result.stdout:
                        bandit_report = json.loads(result.stdout)
                        high_severity = [issue for issue in bandit_report.get("results", [])
                                       if issue.get("issue_severity") == "HIGH"]
                        
                        security_results["checks"]["bandit"] = {
                            "total_issues": len(bandit_report.get("results", [])),
                            "high_severity": len(high_severity),
                            "passed": len(high_severity) == 0
                        }
                        
                        if high_severity:
                            security_results["success"] = False
                            security_results["vulnerabilities"].extend(high_severity)
                            
            except Exception as e:
                security_results["checks"]["bandit"] = {"error": str(e), "passed": False}
                
        # Basic security checks
        security_patterns = [
            ("hardcoded_passwords", r"password\s*=\s*['\"][^'\"]+['\"]"),
            ("hardcoded_keys", r"(api_key|secret_key)\s*=\s*['\"][^'\"]+['\"]"),
            ("sql_injection", r"execute\s*\(\s*['\"].*%.*['\"]"),
            ("shell_injection", r"os\.system\s*\(.*\+.*\)")
        ]
        
        basic_issues = []
        services_dir = os.path.join(self.workspace_dir, "services")
        
        if os.path.exists(services_dir):
            import re
            
            for py_file in Path(services_dir).glob("**/*.py"):
                try:
                    with open(py_file, 'r') as f:
                        content = f.read()
                        
                    for pattern_name, pattern in security_patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        if matches:
                            basic_issues.append({
                                "file": str(py_file),
                                "pattern": pattern_name,
                                "matches": len(matches)
                            })
                            
                except Exception:
                    pass
                    
        security_results["checks"]["basic_patterns"] = {
            "files_checked": len(list(Path(services_dir).glob("**/*.py"))) if os.path.exists(services_dir) else 0,
            "issues_found": len(basic_issues),
            "passed": len(basic_issues) == 0
        }
        
        if basic_issues:
            security_results["success"] = False
            security_results["vulnerabilities"].extend(basic_issues)
            
        return security_results
        
    def run_coverage_analysis(self) -> Dict[str, Any]:
        """Run test coverage analysis"""
        # Check if coverage is available
        try:
            subprocess.run(["coverage", "--version"], 
                         capture_output=True, check=True)
            has_coverage = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            has_coverage = False
            
        if not has_coverage:
            return {
                "success": True,
                "warning": "Coverage tool not available - skipping",
                "coverage_percentage": 0
            }
            
        try:
            # Run tests with coverage
            subprocess.run([
                "coverage", "run", "-m", "unittest", "discover", "tests"
            ], cwd=self.workspace_dir, capture_output=True)
            
            # Generate coverage report
            result = subprocess.run([
                "coverage", "report", "--show-missing"
            ], cwd=self.workspace_dir, capture_output=True, text=True)
            
            # Parse coverage percentage
            coverage_percentage = 0
            for line in result.stdout.split('\n'):
                if "TOTAL" in line:
                    parts = line.split()
                    if len(parts) >= 4 and '%' in parts[-1]:
                        coverage_percentage = int(parts[-1].replace('%', ''))
                        break
                        
            # Generate HTML report
            subprocess.run([
                "coverage", "html", "-d", os.path.join(self.reports_dir, "coverage")
            ], cwd=self.workspace_dir, capture_output=True)
            
            return {
                "success": coverage_percentage >= 70,  # 70% minimum coverage
                "coverage_percentage": coverage_percentage,
                "report_output": result.stdout,
                "html_report": os.path.join(self.reports_dir, "coverage", "index.html")
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "coverage_percentage": 0
            }
            
    def generate_final_report(self, success: bool, duration: float) -> Dict[str, Any]:
        """Generate final CI pipeline report"""
        report = {
            "pipeline_success": success,
            "pipeline_duration": duration,
            "timestamp": datetime.now().isoformat(),
            "phases": self.results,
            "summary": {
                "total_phases": len(self.results),
                "passed_phases": sum(1 for r in self.results.values() if r.get("success", False)),
                "failed_phases": sum(1 for r in self.results.values() if not r.get("success", False))
            }
        }
        
        # Save report to file
        report_file = os.path.join(self.reports_dir, f"ci_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        report["report_file"] = report_file
        
        return report
        
    def print_summary_report(self, report: Dict[str, Any]):
        """Print summary report to console"""
        success_icon = "✅" if report["pipeline_success"] else "❌"
        
        print(f"{success_icon} Pipeline Status: {'PASSED' if report['pipeline_success'] else 'FAILED'}")
        print(f"⏱️  Total Duration: {report['pipeline_duration']:.2f} seconds")
        print(f"📊 Phases: {report['summary']['passed_phases']}/{report['summary']['total_phases']} passed")
        
        print("\nPhase Results:")
        for phase_name, phase_result in report["phases"].items():
            icon = "✅" if phase_result.get("success", False) else "❌"
            duration = phase_result.get("duration", 0)
            
            print(f"  {icon} {phase_name.upper():<15} ({duration:.2f}s)")
            
            # Show specific metrics
            if phase_name == "unit" and "tests_run" in phase_result:
                print(f"      Tests: {phase_result['tests_run']}, Failures: {phase_result.get('failures', 0)}")
            elif phase_name == "coverage" and "coverage_percentage" in phase_result:
                print(f"      Coverage: {phase_result['coverage_percentage']}%")
            elif phase_name == "lint" and "checks" in phase_result:
                checks_passed = sum(1 for c in phase_result['checks'].values() if c.get('passed', False))
                print(f"      Checks: {checks_passed}/{len(phase_result['checks'])} passed")
                
        print(f"\n📄 Full Report: {report.get('report_file', 'Not saved')}")

def main():
    """Main CI pipeline entry point"""
    parser = argparse.ArgumentParser(description="Trading Microservices CI Pipeline")
    parser.add_argument("--workspace", "-w", help="Workspace directory", default=None)
    parser.add_argument("--phase", "-p", help="Run specific phase only", 
                       choices=["lint", "unit", "integration", "performance", "security", "coverage"])
    parser.add_argument("--strict", "-s", action="store_true", 
                       help="Strict mode - fail on warnings")
    
    args = parser.parse_args()
    
    # Initialize pipeline
    pipeline = CITestPipeline(args.workspace)
    
    if args.phase:
        # Run specific phase
        print(f"🎯 Running specific phase: {args.phase.upper()}")
        
        phase_methods = {
            "lint": pipeline.run_linting,
            "unit": pipeline.run_unit_tests,
            "integration": pipeline.run_integration_tests,
            "performance": pipeline.run_performance_tests,
            "security": pipeline.run_security_tests,
            "coverage": pipeline.run_coverage_analysis
        }
        
        if args.phase in phase_methods:
            result = phase_methods[args.phase]()
            success = result.get("success", False)
            
            print(f"\n{'✅' if success else '❌'} Phase {args.phase.upper()}: {'PASSED' if success else 'FAILED'}")
            
            if not success:
                print(f"Error: {result.get('error', 'Unknown error')}")
                
            sys.exit(0 if success else 1)
        else:
            print(f"❌ Unknown phase: {args.phase}")
            sys.exit(1)
    else:
        # Run full pipeline
        report = pipeline.run_full_test_suite()
        
        # Exit with appropriate code
        sys.exit(0 if report["pipeline_success"] else 1)

if __name__ == "__main__":
    main()
