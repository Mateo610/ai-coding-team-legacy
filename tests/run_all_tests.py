"""
COMPREHENSIVE TEST RUNNER - PHASE 6
Runs all test suites and generates comprehensive report

This is the main entry point for running all Phase 6 comprehensive tests.
"""

import sys
import os
import time
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class ComprehensiveTestRunner:
    """Runs all comprehensive test suites and generates reports"""
    
    def __init__(self):
        self.test_suites: List[Tuple[str, callable]] = []
        self.results: Dict[str, Dict] = {}
        self.start_time = None
        self.end_time = None
        
    def register_test_suite(self, name: str, test_func: callable):
        """Register a test suite"""
        self.test_suites.append((name, test_func))
    
    def run_all_tests(self) -> Dict:
        """Run all registered test suites"""
        print("\n" + "="*70)
        print("COMPREHENSIVE TEST SUITE RUNNER - PHASE 6")
        print("="*70)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        self.start_time = time.time()
        
        total_passed = 0
        total_failed = 0
        total_tests = 0
        
        # Run each test suite
        for suite_name, test_func in self.test_suites:
            print(f"\n{'─'*70}")
            print(f"Running Test Suite: {suite_name}")
            print(f"{'─'*70}")
            
            suite_start = time.time()
            
            try:
                # Run test suite (assumes it returns True/False for overall success)
                result = test_func()
                
                suite_end = time.time()
                suite_duration = suite_end - suite_start
                
                # Store results
                self.results[suite_name] = {
                    "success": result if isinstance(result, bool) else True,
                    "duration": suite_duration,
                    "timestamp": datetime.now().isoformat()
                }
                
                status = "✅ PASSED" if result else "❌ FAILED"
                print(f"\n{status} - {suite_name} ({suite_duration:.2f}s)")
                
            except Exception as e:
                suite_end = time.time()
                suite_duration = suite_end - suite_start
                
                self.results[suite_name] = {
                    "success": False,
                    "duration": suite_duration,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                
                print(f"\n❌ FAILED - {suite_name}: {str(e)}")
                import traceback
                traceback.print_exc()
        
        self.end_time = time.time()
        total_duration = self.end_time - self.start_time
        
        # Generate summary
        passed_suites = sum(1 for r in self.results.values() if r.get("success", False))
        failed_suites = len(self.results) - passed_suites
        
        print("\n" + "="*70)
        print("COMPREHENSIVE TEST RESULTS SUMMARY")
        print("="*70)
        print(f"\n📊 Test Suite Summary:")
        print(f"   Total suites: {len(self.results)}")
        print(f"   Passed: {passed_suites}")
        print(f"   Failed: {failed_suites}")
        print(f"   Success rate: {(passed_suites/len(self.results)*100):.1f}%")
        print(f"   Total duration: {total_duration:.2f}s")
        print(f"   Average duration: {(total_duration/len(self.results)):.2f}s per suite")
        
        print(f"\n📋 Test Suite Results:")
        for suite_name, result in self.results.items():
            status = "✅" if result.get("success", False) else "❌"
            duration = result.get("duration", 0)
            print(f"   {status} {suite_name:40s} ({duration:.2f}s)")
            if "error" in result:
                print(f"      Error: {result['error'][:80]}")
        
        print(f"\n{'='*70}")
        if passed_suites == len(self.results):
            print("✅ ALL TEST SUITES PASSED!")
        else:
            print(f"⚠️  {failed_suites} TEST SUITE(S) FAILED")
        print("="*70)
        
        return {
            "total_suites": len(self.results),
            "passed_suites": passed_suites,
            "failed_suites": failed_suites,
            "success_rate": (passed_suites/len(self.results)*100) if self.results else 0,
            "total_duration": total_duration,
            "results": self.results
        }
    
    def generate_json_report(self, output_file: str = "test_results.json"):
        """Generate JSON report"""
        import json
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_duration": (self.end_time - self.start_time) if self.end_time and self.start_time else 0,
            "results": self.results,
            "summary": {
                "total_suites": len(self.results),
                "passed_suites": sum(1 for r in self.results.values() if r.get("success", False)),
                "failed_suites": sum(1 for r in self.results.values() if not r.get("success", False)),
            }
        }
        
        output_path = Path(__file__).parent.parent / output_file
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 JSON report saved to: {output_path}")
        return output_path


def main():
    """Main entry point - run all comprehensive tests"""
    runner = ComprehensiveTestRunner()
    
    # Import test suites
    try:
        from tests.test_consolidated_tools_comprehensive import ComprehensiveTestSuite
        from tests.test_all_modes_comprehensive import ModeTestSuite
        from tests.test_migration_comprehensive import MigrationTestSuite
        from tests.test_agent_tool_integration import test_tool_migration, test_tool_availability, test_agent_tool_integration, test_prompt_tools
        
        # Register test suites
        print("Registering test suites...")
        
        # Test Suite 1: Consolidated Tools Comprehensive
        def run_consolidated_tests():
            suite = ComprehensiveTestSuite()
            suite.setup()
            suite.run_all_tests()
            suite.teardown()
            return suite.generate_report()
        
        runner.register_test_suite("Consolidated Tools Comprehensive", run_consolidated_tests)
        
        # Test Suite 2: All Modes Comprehensive
        def run_mode_tests():
            suite = ModeTestSuite()
            return suite.test_all_modes()
        
        runner.register_test_suite("All Modes Comprehensive", run_mode_tests)
        
        # Test Suite 3: Migration Comprehensive
        def run_migration_tests():
            suite = MigrationTestSuite()
            return suite.test_all_migrations()
        
        runner.register_test_suite("Migration Comprehensive", run_migration_tests)
        
        # Test Suite 4: Agent Integration
        def run_agent_tests():
            print("\nAgent Integration Tests:")
            all_passed = True
            tests = [
                ("Tool Migration", test_tool_migration),
                ("Tool Availability", test_tool_availability),
                ("Agent Integration", test_agent_tool_integration),
                ("Prompt Tools", test_prompt_tools),
            ]
            
            for test_name, test_func in tests:
                try:
                    result = test_func()
                    if not result:
                        all_passed = False
                except Exception as e:
                    print(f"   ❌ {test_name}: {str(e)}")
                    all_passed = False
            
            return all_passed
        
        runner.register_test_suite("Agent Integration", run_agent_tests)
        
    except ImportError as e:
        print(f"⚠️  Warning: Could not import all test suites: {e}")
        print("   Running available tests only...")
    
    # Run all tests
    results = runner.run_all_tests()
    
    # Generate JSON report
    try:
        runner.generate_json_report()
    except Exception as e:
        print(f"⚠️  Could not generate JSON report: {e}")
    
    # Return success status
    return results.get("failed_suites", 0) == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

