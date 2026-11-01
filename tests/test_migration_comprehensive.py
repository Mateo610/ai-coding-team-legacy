"""
COMPREHENSIVE MIGRATION LAYER TESTING
Phase 6: Testing all 95 old tools migrate correctly to 26 new tools

This test suite verifies that all old tool names correctly migrate to new consolidated tools.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.consolidated.migration import (
    OLD_TO_NEW_MAPPING,
    migrate_tool_call,
    is_old_tool,
    get_migration_stats
)


class MigrationTestSuite:
    """Comprehensive migration layer testing"""
    
    def __init__(self):
        self.results: List[Tuple[str, bool, str]] = []
        
    def test_all_migrations(self):
        """Test that all old tools migrate correctly"""
        print("\n" + "="*70)
        print("COMPREHENSIVE MIGRATION LAYER TESTING")
        print("="*70)
        
        stats = get_migration_stats()
        print(f"\n📊 Migration Statistics:")
        print(f"   Old tools: {stats['old_tools']}")
        print(f"   New tools: {stats['new_tools']}")
        print(f"   Reduction: {stats['reduction']} tools ({stats['reduction_percent']}%)")
        
        print(f"\n{'─'*70}")
        print(f"Testing all {len(OLD_TO_NEW_MAPPING)} old tool migrations")
        print(f"{'─'*70}")
        
        total_tests = 0
        passed_tests = 0
        failed_migrations: List[str] = []
        
        # Group by new tool to see consolidation
        new_tool_counts: Dict[str, int] = {}
        
        for old_name in sorted(OLD_TO_NEW_MAPPING.keys()):
            total_tests += 1
            
            try:
                # Test migration
                new_name, new_kwargs = migrate_tool_call(old_name, test_param="test")
                
                # Verify migration worked
                if new_name and new_name != old_name:
                    # Migration successful
                    passed_tests += 1
                    
                    # Track consolidation
                    if new_name not in new_tool_counts:
                        new_tool_counts[new_name] = 0
                    new_tool_counts[new_name] += 1
                    
                    # Store mode if present
                    mode = new_kwargs.get("mode", "N/A")
                    self.results.append((old_name, True, f"→ {new_name} (mode: {mode})"))
                elif new_name == old_name:
                    # Tool not in migration mapping (shouldn't happen)
                    failed_migrations.append(f"{old_name} (not migrated)")
                    self.results.append((old_name, False, "Not migrated"))
                else:
                    # Migration failed
                    failed_migrations.append(f"{old_name} (no new name)")
                    self.results.append((old_name, False, "Migration returned None"))
                    
            except Exception as e:
                failed_migrations.append(f"{old_name} (error: {str(e)[:50]})")
                self.results.append((old_name, False, f"Exception: {str(e)[:80]}"))
        
        # Print consolidation summary
        print(f"\n{'─'*70}")
        print(f"Consolidation Summary ({len(new_tool_counts)} new tools)")
        print(f"{'─'*70}")
        
        for new_tool, count in sorted(new_tool_counts.items(), key=lambda x: x[1], reverse=True):
            old_tools_list = [old for old, (new, _, _) in OLD_TO_NEW_MAPPING.items() if new == new_tool]
            print(f"   {new_tool:20s} ← {count:2d} old tools")
            if count <= 5:  # Show details for small consolidations
                for old_tool in old_tools_list[:3]:
                    print(f"      • {old_tool}")
                if count > 3:
                    print(f"      • ... and {count - 3} more")
        
        # Print test results
        if len(self.results) > 0:
            print(f"\n{'─'*70}")
            print(f"Sample Migration Results (first 20)")
            print(f"{'─'*70}")
            
            for old_name, passed, message in self.results[:20]:
                status = "✅" if passed else "❌"
                print(f"   {status} {old_name:25s} {message}")
            
            if len(self.results) > 20:
                print(f"   ... and {len(self.results) - 20} more")
        
        # Generate report
        print("\n" + "="*70)
        print("MIGRATION TESTING REPORT")
        print("="*70)
        
        failed_tests = total_tests - passed_tests
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n📊 Summary:")
        print(f"   Total migrations tested: {total_tests}")
        print(f"   Successful migrations: {passed_tests}")
        print(f"   Failed migrations: {failed_tests}")
        print(f"   Pass rate: {pass_rate:.1f}%")
        print(f"   Consolidation: {stats['old_tools']} → {stats['new_tools']} tools")
        
        if failed_tests > 0:
            print(f"\n❌ Failed Migrations:")
            for failure in failed_migrations[:10]:
                print(f"   • {failure}")
            if len(failed_migrations) > 10:
                print(f"   ... and {len(failed_migrations) - 10} more")
        
        print("\n" + "="*70)
        if passed_tests == total_tests:
            print("✅ ALL MIGRATIONS SUCCESSFUL!")
        else:
            print(f"⚠️  {failed_tests} MIGRATION(S) FAILED")
        print("="*70)
        
        return passed_tests == total_tests
    
    def test_specific_migrations(self):
        """Test specific high-value migrations"""
        print(f"\n{'─'*70}")
        print("Testing Specific High-Value Migrations")
        print(f"{'─'*70}")
        
        test_cases = [
            ("read_file", {"file_path": "test.py"}, "fs_read", {"mode": "read"}),
            ("write_file", {"file_path": "test.py", "content": "code"}, "fs_write", {"mode": "write"}),
            ("git_status", {}, "git_inspect", {"mode": "status"}),
            ("git_add", {"files": ["test.py"]}, "git_modify", {"action": "add"}),
            ("run_tests", {"test_path": "tests"}, "test_run", {"framework": "auto"}),
            ("scan_project", {"path": "."}, "project_scan", {"mode": "full"}),
            ("check_syntax", {"code": "def f(): pass"}, "code_check", {"mode": "syntax"}),
        ]
        
        all_passed = True
        for old_name, old_kwargs, expected_new, expected_kwargs in test_cases:
            new_name, new_kwargs = migrate_tool_call(old_name, **old_kwargs)
            
            if new_name == expected_new:
                # Check mode/action matches
                matches = True
                for key, value in expected_kwargs.items():
                    if new_kwargs.get(key) != value:
                        matches = False
                        break
                
                if matches:
                    print(f"   ✅ {old_name:20s} → {new_name:20s} ✓")
                else:
                    print(f"   ⚠️  {old_name:20s} → {new_name:20s} (kwargs mismatch)")
                    all_passed = False
            else:
                print(f"   ❌ {old_name:20s} → {new_name:20s} (expected {expected_new})")
                all_passed = False
        
        return all_passed


def main():
    """Main entry point"""
    suite = MigrationTestSuite()
    
    # Test all migrations
    all_passed = suite.test_all_migrations()
    
    # Test specific migrations
    specific_passed = suite.test_specific_migrations()
    
    return all_passed and specific_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

