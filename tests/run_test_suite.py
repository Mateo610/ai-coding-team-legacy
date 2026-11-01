"""
Run comprehensive test suite
Section 8.1: Create Test Suite

Automated test execution with performance tracking
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.test_suite_framework import (
    TestSuiteFramework, TaskCategory, TaskDifficulty, TEST_SUITE_FRAMEWORK
)
from agents.orchestrator import Orchestrator


def main():
    """Main entry point for test suite execution"""
    parser = argparse.ArgumentParser(description="Run comprehensive test suite")
    parser.add_argument(
        "--categories",
        nargs="+",
        choices=[cat.value for cat in TaskCategory],
        help="Filter by task categories"
    )
    parser.add_argument(
        "--difficulties",
        nargs="+",
        choices=[diff.value for diff in TaskDifficulty],
        help="Filter by difficulty levels"
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=3,
        help="Maximum iterations per task (default: 3)"
    )
    parser.add_argument(
        "--tasks-file",
        type=str,
        help="Path to tasks JSON file (default: auto-generated)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of tasks to run (for testing)"
    )
    
    args = parser.parse_args()
    
    # Initialize orchestrator
    print("Initializing orchestrator...")
    orchestrator = Orchestrator()
    
    # Load tasks
    framework = TEST_SUITE_FRAMEWORK
    if args.tasks_file:
        tasks = framework.load_tasks(args.tasks_file)
    else:
        tasks = framework.load_tasks()
    
    if not tasks:
        print("No tasks found! Generate tasks first with: python3 tests/generate_test_tasks.py")
        return 1
    
    # Filter categories
    categories = None
    if args.categories:
        categories = [TaskCategory(cat) for cat in args.categories]
    
    # Filter difficulties
    difficulties = None
    if args.difficulties:
        difficulties = [TaskDifficulty(diff) for diff in args.difficulties]
    
    # Limit tasks if specified
    if args.limit:
        tasks = tasks[:args.limit]
    
    # Run test suite
    run_id = framework.run_test_suite(
        orchestrator=orchestrator,
        tasks=tasks,
        categories=categories,
        difficulties=difficulties,
        max_iterations=args.max_iterations,
        parallel=False  # Not yet implemented
    )
    
    print(f"\n✅ Test suite completed! Run ID: {run_id}")
    print(f"View results: python3 tests/view_test_results.py --run-id {run_id}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

