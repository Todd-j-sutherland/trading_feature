#!/usr/bin/env python3
"""
Complete Test Runner for Trading Microservices

This is the main test runner that orchestrates all testing activities,
provides comprehensive test reporting, and manages test execution.

Author: Trading System Testing Team
Date: September 14, 2025
"""

import sys
import os
import argparse
import time
import json
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import test modules
try:
    from tests.test_framework import TestRunner
    from tests.test_fixtures import setup_complete_test_environment, cleanup_test_environment
    from tests.ci_pipeline import CITestPipeline
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure all test modules are available")
    sys.exit(1)

class ComprehensiveTestRunner:
    """Main test runner for all trading microservices tests"""
    
    def __init__(self, workspace_dir: str = None):
        self.workspace_dir = workspace_dir or str(project_root)
        self.test_env = None
        self.results = {}
        
    def run_all_tests(self, test_types: list = None, verbose: bool = True) -> dict:
        """Run all tests with comprehensive reporting"""
        
        print("🚀 Trading Microservices - Comprehensive Test Suite")
        print("=" * 80)
        print(f"Workspace: {self.workspace_dir}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print("=" * 80)
        
        start_time = time.time()
        overall_success = True
        
        # Default test types
        if test_types is None:
            test_types = ["unit", "integration", "performance", "ci"]
            
        # Setup test environment
        print("\n🔧 Setting up test environment...")
        try:
            self.test_env = setup_complete_test_environment()
            print("✅ Test environment ready")
        except Exception as e:
            print(f"❌ Failed to setup test environment: {e}")
            return {"success": False, "error": "Environment setup failed"}
            
        try:
            # Run each test type
            for test_type in test_types:
                print(f"\n📋 Running {test_type.upper()} tests...")
                print("-" * 40)
                
                test_start = time.time()
                
                if test_type == "unit":
                    result = self._run_unit_tests(verbose)
                elif test_type == "integration":
                    result = self._run_integration_tests(verbose)
                elif test_type == "performance":
                    result = self._run_performance_tests(verbose)
                elif test_type == "ci":
                    result = self._run_ci_pipeline(verbose)
                else:
                    print(f"⚠️  Unknown test type: {test_type}")
                    continue
                    
                test_duration = time.time() - test_start
                result["duration"] = test_duration
                
                self.results[test_type] = result
                
                if result.get("success", False):
                    print(f"✅ {test_type.upper()} tests passed ({test_duration:.2f}s)")
                else:
                    print(f"❌ {test_type.upper()} tests failed ({test_duration:.2f}s)")
                    overall_success = False
                    
        finally:
            # Cleanup test environment
            if self.test_env:
                print("\n🧹 Cleaning up test environment...")
                cleanup_test_environment(self.test_env)
                print("✅ Cleanup complete")
                
        # Generate final report
        total_duration = time.time() - start_time
        final_report = self._generate_final_report(overall_success, total_duration)
        
        print("\n" + "=" * 80)
        print("COMPREHENSIVE TEST SUMMARY")
        print("=" * 80)
        self._print_final_summary(final_report)
        
        return final_report
        
    def _run_unit_tests(self, verbose: bool = True) -> dict:
        """Run unit tests using test framework"""
        try:
            from tests.test_unit import run_unit_tests
            
            # Redirect stdout/stderr to capture test output
            import io
            import contextlib
            
            output_buffer = io.StringIO()
            
            with contextlib.redirect_stdout(output_buffer), contextlib.redirect_stderr(output_buffer):
                result = run_unit_tests()
                
            output = output_buffer.getvalue()
            
            if verbose and output:
                print(output)
                
            success = result.wasSuccessful() if hasattr(result, 'wasSuccessful') else True
            
            return {
                "success": success,
                "tests_run": getattr(result, 'testsRun', 0),
                "failures": len(getattr(result, 'failures', [])),
                "errors": len(getattr(result, 'errors', [])),
                "output": output
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "tests_run": 0,
                "failures": 0,
                "errors": 1
            }
            
    def _run_integration_tests(self, verbose: bool = True) -> dict:
        """Run integration tests"""
        try:
            from tests.test_integration import run_integration_tests
            
            import io
            import contextlib
            
            output_buffer = io.StringIO()
            
            with contextlib.redirect_stdout(output_buffer), contextlib.redirect_stderr(output_buffer):
                result = run_integration_tests()
                
            output = output_buffer.getvalue()
            
            if verbose and output:
                print(output)
                
            success = result.wasSuccessful() if hasattr(result, 'wasSuccessful') else True
            
            return {
                "success": success,
                "tests_run": getattr(result, 'testsRun', 0),
                "failures": len(getattr(result, 'failures', [])),
                "errors": len(getattr(result, 'errors', [])),
                "output": output
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "tests_run": 0,
                "failures": 0,
                "errors": 1
            }
            
    def _run_performance_tests(self, verbose: bool = True) -> dict:
        """Run performance tests"""
        try:
            from tests.test_performance import run_performance_tests
            
            import io
            import contextlib
            
            output_buffer = io.StringIO()
            
            with contextlib.redirect_stdout(output_buffer), contextlib.redirect_stderr(output_buffer):
                result = run_performance_tests()
                
            output = output_buffer.getvalue()
            
            if verbose and output:
                print(output)
                
            success = result.wasSuccessful() if hasattr(result, 'wasSuccessful') else True
            
            return {
                "success": success,
                "tests_run": getattr(result, 'testsRun', 0),
                "failures": len(getattr(result, 'failures', [])),
                "errors": len(getattr(result, 'errors', [])),
                "output": output
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "tests_run": 0,
                "failures": 0,
                "errors": 1
            }
            
    def _run_ci_pipeline(self, verbose: bool = True) -> dict:
        """Run CI pipeline tests"""
        try:
            pipeline = CITestPipeline(self.workspace_dir)
            
            # Run specific CI phases (excluding full pipeline to avoid recursion)
            phases = ["lint", "security"]
            
            ci_results = {}
            overall_success = True
            
            for phase in phases:
                if phase == "lint":
                    result = pipeline.run_linting()
                elif phase == "security":
                    result = pipeline.run_security_tests()
                else:
                    continue
                    
                ci_results[phase] = result
                
                if not result.get("success", False):
                    overall_success = False
                    
                if verbose:
                    print(f"  {phase.upper()}: {'PASSED' if result.get('success') else 'FAILED'}")
                    
            return {
                "success": overall_success,
                "phases": ci_results,
                "phases_run": len(phases)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "phases": {},
                "phases_run": 0
            }
            
    def _generate_final_report(self, success: bool, duration: float) -> dict:
        """Generate comprehensive final report"""
        
        # Calculate summary statistics
        total_tests = sum(r.get("tests_run", 0) for r in self.results.values())
        total_failures = sum(r.get("failures", 0) for r in self.results.values())
        total_errors = sum(r.get("errors", 0) for r in self.results.values())
        
        test_types_run = len(self.results)
        test_types_passed = sum(1 for r in self.results.values() if r.get("success", False))
        
        report = {
            "overall_success": success,
            "total_duration": duration,
            "timestamp": datetime.now().isoformat(),
            "workspace": self.workspace_dir,
            "summary": {
                "test_types_run": test_types_run,
                "test_types_passed": test_types_passed,
                "test_types_failed": test_types_run - test_types_passed,
                "total_tests": total_tests,
                "total_failures": total_failures,
                "total_errors": total_errors,
                "success_rate": (test_types_passed / test_types_run * 100) if test_types_run > 0 else 0
            },
            "detailed_results": self.results,
            "environment": {
                "test_env_setup": self.test_env is not None,
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                "platform": sys.platform
            }
        }
        
        # Save report to file
        reports_dir = os.path.join(self.workspace_dir, "test_reports")
        os.makedirs(reports_dir, exist_ok=True)
        
        report_file = os.path.join(reports_dir, f"comprehensive_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        try:
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            report["report_file"] = report_file
        except Exception as e:
            report["report_save_error"] = str(e)
            
        return report
        
    def _print_final_summary(self, report: dict):
        """Print comprehensive final summary"""
        
        success_icon = "✅" if report["overall_success"] else "❌"
        summary = report["summary"]
        
        print(f"{success_icon} Overall Status: {'PASSED' if report['overall_success'] else 'FAILED'}")
        print(f"⏱️  Total Duration: {report['total_duration']:.2f} seconds")
        print(f"🎯 Success Rate: {summary['success_rate']:.1f}%")
        
        print(f"\n📊 Test Type Summary:")
        print(f"   Total Test Types: {summary['test_types_run']}")
        print(f"   Passed: {summary['test_types_passed']}")
        print(f"   Failed: {summary['test_types_failed']}")
        
        print(f"\n🧪 Individual Test Summary:")
        print(f"   Total Tests: {summary['total_tests']}")
        print(f"   Failures: {summary['total_failures']}")
        print(f"   Errors: {summary['total_errors']}")
        
        print(f"\nDetailed Results:")
        for test_type, result in report["detailed_results"].items():
            icon = "✅" if result.get("success", False) else "❌"
            duration = result.get("duration", 0)
            
            print(f"  {icon} {test_type.upper():<15} ({duration:.2f}s)")
            
            if "tests_run" in result:
                print(f"      Tests: {result['tests_run']}, Failures: {result.get('failures', 0)}, Errors: {result.get('errors', 0)}")
            elif "phases" in result:
                phases_passed = sum(1 for p in result['phases'].values() if p.get('success', False))
                print(f"      Phases: {phases_passed}/{result.get('phases_run', 0)} passed")
                
            if "error" in result:
                print(f"      Error: {result['error']}")
                
        print(f"\n📄 Report File: {report.get('report_file', 'Not saved')}")
        
        # Quality gates
        print(f"\n🚦 Quality Gates:")
        
        if summary['success_rate'] >= 100:
            print("   ✅ All test types passed")
        elif summary['success_rate'] >= 80:
            print("   ⚠️  Most test types passed (>= 80%)")
        else:
            print("   ❌ Too many test types failed (< 80%)")
            
        if summary['total_failures'] == 0 and summary['total_errors'] == 0:
            print("   ✅ No test failures or errors")
        elif summary['total_failures'] + summary['total_errors'] <= 2:
            print("   ⚠️  Minimal test failures")
        else:
            print("   ❌ Multiple test failures detected")
            
        if report['total_duration'] <= 300:  # 5 minutes
            print("   ✅ Test execution time acceptable (<= 5 min)")
        else:
            print("   ⚠️  Test execution time longer than expected (> 5 min)")

def main():
    """Main entry point for comprehensive test runner"""
    
    parser = argparse.ArgumentParser(description="Comprehensive Trading Microservices Test Runner")
    
    parser.add_argument("--workspace", "-w", help="Workspace directory", default=None)
    parser.add_argument("--types", "-t", nargs="+", 
                       choices=["unit", "integration", "performance", "ci"],
                       help="Test types to run", default=None)
    parser.add_argument("--quiet", "-q", action="store_true", help="Quiet mode - minimal output")
    parser.add_argument("--json", "-j", help="Save results to JSON file")
    
    args = parser.parse_args()
    
    # Initialize test runner
    runner = ComprehensiveTestRunner(args.workspace)
    
    # Run tests
    verbose = not args.quiet
    report = runner.run_all_tests(args.types, verbose)
    
    # Save JSON output if requested
    if args.json:
        try:
            with open(args.json, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"\n💾 Results saved to: {args.json}")
        except Exception as e:
            print(f"\n❌ Failed to save JSON results: {e}")
    
    # Exit with appropriate code
    exit_code = 0 if report["overall_success"] else 1
    
    if not args.quiet:
        print(f"\n🎯 Exiting with code: {exit_code}")
        
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
