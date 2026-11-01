"""
Test Suite Framework for Comprehensive Task Testing
Section 8.1: Create Test Suite

Tests the system's ability to generate code for diverse tasks across:
- CRUD operations
- API development
- Algorithm implementation
- Database tasks
- Frontend tasks
- DevOps tasks
- Data processing (ETL)
- Data analysis
- General tasks
"""

import json
import time
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum


class TaskCategory(Enum):
    """Categories of tasks to test"""
    CRUD = "crud"
    API = "api"
    ALGORITHM = "algorithm"
    DATABASE = "database"
    FRONTEND = "frontend"
    DEVOPS = "devops"
    ETL = "etl"
    DATA_ANALYSIS = "data_analysis"
    TEST = "test"
    GENERAL = "general"


class TaskDifficulty(Enum):
    """Difficulty levels for tasks"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


@dataclass
class TestTask:
    """Represents a single test task"""
    id: str
    name: str
    description: str
    category: TaskCategory
    difficulty: TaskDifficulty
    expected_output: Optional[str] = None  # Expected code pattern or output
    test_code: Optional[str] = None  # Test code to validate output
    dependencies: Optional[List[str]] = None  # Required dependencies
    context: Optional[Dict[str, Any]] = None  # Additional context
    tags: Optional[List[str]] = None  # Tags for filtering


@dataclass
class TestResult:
    """Result of a single test task execution"""
    task_id: str
    task_name: str
    success: bool
    score: float  # 0-100
    duration_ms: int
    iterations: int
    code_generated: str
    validation_result: Dict[str, Any]
    errors: List[str]
    timestamp: str
    task_category: str
    task_difficulty: str


class TestSuiteFramework:
    """Framework for comprehensive test suite execution"""
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize test suite framework
        
        Args:
            data_dir: Directory for test results storage
        """
        self.data_dir = Path(
            data_dir or Path.home() / "ai-coding-team" / "data" / "test_suite"
        )
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # SQLite database for test results
        self.db_path = self.data_dir / "test_results.db"
        self._init_database()
        
        # Tasks directory
        self.tasks_dir = self.data_dir / "tasks"
        self.tasks_dir.mkdir(exist_ok=True)
        
        # Results directory
        self.results_dir = self.data_dir / "results"
        self.results_dir.mkdir(exist_ok=True)
    
    def _init_database(self):
        """Initialize SQLite database for test results"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Test results table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                task_id TEXT NOT NULL,
                task_name TEXT NOT NULL,
                task_category TEXT NOT NULL,
                task_difficulty TEXT NOT NULL,
                success INTEGER NOT NULL,
                score REAL NOT NULL,
                duration_ms INTEGER NOT NULL,
                iterations INTEGER NOT NULL,
                code_generated TEXT,
                validation_result TEXT,
                errors TEXT,
                code_length INTEGER,
                tokens_used INTEGER,
                model_used TEXT,
                route_used TEXT
            )
        """)
        
        # Test runs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT UNIQUE NOT NULL,
                timestamp TEXT NOT NULL,
                total_tasks INTEGER NOT NULL,
                passed_tasks INTEGER NOT NULL,
                failed_tasks INTEGER NOT NULL,
                avg_score REAL NOT NULL,
                avg_duration_ms REAL NOT NULL,
                duration_ms INTEGER NOT NULL,
                summary TEXT
            )
        """)
        
        # Performance trends table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_trends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                score REAL NOT NULL,
                duration_ms INTEGER NOT NULL,
                success INTEGER NOT NULL
            )
        """)
        
        # Indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_run_id ON test_results(run_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_task_id ON test_results(task_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON test_results(task_category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON test_results(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_perf_task ON performance_trends(task_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_perf_timestamp ON performance_trends(timestamp)")
        
        conn.commit()
        conn.close()
    
    def load_tasks(self, tasks_file: Optional[str] = None) -> List[TestTask]:
        """
        Load test tasks from JSON file
        
        Args:
            tasks_file: Path to tasks JSON file (default: tasks/test_tasks.json)
        
        Returns:
            List of TestTask objects
        """
        if tasks_file is None:
            tasks_file = self.tasks_dir / "test_tasks.json"
        else:
            tasks_file = Path(tasks_file)
        
        if not tasks_file.exists():
            return []
        
        with open(tasks_file, 'r') as f:
            tasks_data = json.load(f)
        
        tasks = []
        for task_data in tasks_data.get('tasks', []):
            task = TestTask(
                id=task_data['id'],
                name=task_data['name'],
                description=task_data['description'],
                category=TaskCategory(task_data['category']),
                difficulty=TaskDifficulty(task_data['difficulty']),
                expected_output=task_data.get('expected_output'),
                test_code=task_data.get('test_code'),
                dependencies=task_data.get('dependencies', []),
                context=task_data.get('context', {}),
                tags=task_data.get('tags', [])
            )
            tasks.append(task)
        
        return tasks
    
    def save_tasks(self, tasks: List[TestTask], tasks_file: Optional[str] = None):
        """
        Save test tasks to JSON file
        
        Args:
            tasks: List of TestTask objects
            tasks_file: Path to tasks JSON file
        """
        if tasks_file is None:
            tasks_file = self.tasks_dir / "test_tasks.json"
        else:
            tasks_file = Path(tasks_file)
        
        tasks_data = {
            'tasks': [
                {
                    'id': task.id,
                    'name': task.name,
                    'description': task.description,
                    'category': task.category.value,
                    'difficulty': task.difficulty.value,
                    'expected_output': task.expected_output,
                    'test_code': task.test_code,
                    'dependencies': task.dependencies or [],
                    'context': task.context or {},
                    'tags': task.tags or []
                }
                for task in tasks
            ]
        }
        
        with open(tasks_file, 'w') as f:
            json.dump(tasks_data, f, indent=2)
    
    def execute_test_task(self,
                         task: TestTask,
                         orchestrator,
                         max_iterations: int = 3) -> TestResult:
        """
        Execute a single test task
        
        Args:
            task: TestTask to execute
            orchestrator: Orchestrator instance
            max_iterations: Maximum iterations for iterative building
        
        Returns:
            TestResult with execution details
        """
        start_time = time.time()
        errors = []
        
        try:
            # Execute task
            result = orchestrator.build_with_validation_iterative(
                task=task.description,
                context=task.context,
                max_iterations=max_iterations
            )
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Extract results
            success = result.get("success", False)
            code = result.get("code", "")
            validation = result.get("validation", {})
            evaluation = result.get("evaluation")
            iterations = result.get("total_iterations", 1)
            
            # Calculate score
            score = evaluation.score if evaluation else 0.0
            
            # Extract errors
            if validation.get("errors"):
                errors = [str(e) for e in validation.get("errors", [])]
            
            # Validate against test code if available
            if task.test_code and success:
                validation_result = self._validate_with_test_code(code, task.test_code)
                if not validation_result.get("passed", False):
                    success = False
                    errors.append(f"Test validation failed: {validation_result.get('error', 'Unknown error')}")
            
            return TestResult(
                task_id=task.id,
                task_name=task.name,
                success=success,
                score=score,
                duration_ms=duration_ms,
                iterations=iterations,
                code_generated=code,
                validation_result=validation,
                errors=errors,
                timestamp=datetime.now().isoformat(),
                task_category=task.category.value,
                task_difficulty=task.difficulty.value
            )
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return TestResult(
                task_id=task.id,
                task_name=task.name,
                success=False,
                score=0.0,
                duration_ms=duration_ms,
                iterations=0,
                code_generated="",
                validation_result={"error": str(e)},
                errors=[str(e)],
                timestamp=datetime.now().isoformat(),
                task_category=task.category.value,
                task_difficulty=task.difficulty.value
            )
    
    def _validate_with_test_code(self, code: str, test_code: str) -> Dict[str, Any]:
        """
        Validate generated code using test code
        
        Args:
            code: Generated code
            test_code: Test code to validate
        
        Returns:
            Validation result dictionary
        """
        try:
            # Combine code and test code
            full_code = f"{code}\n\n{test_code}"
            
            # Execute in temp file
            import tempfile
            import subprocess
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(full_code)
                temp_file = f.name
            
            try:
                result = subprocess.run(
                    ['python3', temp_file],
                    capture_output=True,
                    timeout=10,
                    text=True
                )
                
                return {
                    'passed': result.returncode == 0,
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'error': result.stderr if result.returncode != 0 else None
                }
            finally:
                Path(temp_file).unlink()
                
        except Exception as e:
            return {
                'passed': False,
                'error': str(e)
            }
    
    def save_result(self, result: TestResult, run_id: str, metadata: Dict[str, Any] = None):
        """
        Save test result to database
        
        Args:
            result: TestResult to save
            run_id: ID of the test run
            metadata: Additional metadata
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        metadata = metadata or {}
        
        cursor.execute("""
            INSERT INTO test_results (
                run_id, timestamp, task_id, task_name, task_category, task_difficulty,
                success, score, duration_ms, iterations, code_generated,
                validation_result, errors, code_length, tokens_used,
                model_used, route_used
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            run_id, result.timestamp, result.task_id, result.task_name,
            result.task_category, result.task_difficulty,
            1 if result.success else 0, result.score, result.duration_ms,
            result.iterations, result.code_generated[:10000],  # Limit length
            json.dumps(result.validation_result),
            json.dumps(result.errors),
            len(result.code_generated),
            metadata.get('tokens_used', 0),
            metadata.get('model_used', 'unknown'),
            metadata.get('route_used', 'unknown')
        ))
        
        # Save to performance trends
        cursor.execute("""
            INSERT INTO performance_trends (task_id, timestamp, score, duration_ms, success)
            VALUES (?, ?, ?, ?, ?)
        """, (
            result.task_id, result.timestamp, result.score,
            result.duration_ms, 1 if result.success else 0
        ))
        
        conn.commit()
        conn.close()
    
    def run_test_suite(self,
                      orchestrator,
                      tasks: Optional[List[TestTask]] = None,
                      categories: Optional[List[TaskCategory]] = None,
                      difficulties: Optional[List[TaskDifficulty]] = None,
                      max_iterations: int = 3,
                      parallel: bool = False) -> str:
        """
        Run full test suite
        
        Args:
            orchestrator: Orchestrator instance
            tasks: List of tasks to run (default: all tasks)
            categories: Filter by categories (default: all)
            difficulties: Filter by difficulties (default: all)
            max_iterations: Maximum iterations per task
            parallel: Run tasks in parallel (not yet implemented)
        
        Returns:
            Run ID for this test suite execution
        """
        # Generate run ID
        run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        start_time = time.time()
        
        # Load tasks if not provided
        if tasks is None:
            tasks = self.load_tasks()
        
        # Filter tasks
        filtered_tasks = tasks
        if categories:
            filtered_tasks = [t for t in filtered_tasks if t.category in categories]
        if difficulties:
            filtered_tasks = [t for t in filtered_tasks if t.difficulty in difficulties]
        
        print(f"\n{'='*70}")
        print(f"🧪 Running Test Suite: {run_id}")
        print(f"{'='*70}")
        print(f"Total tasks: {len(filtered_tasks)}")
        print(f"Categories: {[c.value for c in (categories or TaskCategory)]}")
        print(f"Difficulties: {[d.value for d in (difficulties or TaskDifficulty)]}")
        print(f"{'='*70}\n")
        
        results = []
        passed = 0
        failed = 0
        
        for i, task in enumerate(filtered_tasks, 1):
            print(f"\n[{i}/{len(filtered_tasks)}] Testing: {task.name}")
            print(f"   Category: {task.category.value} | Difficulty: {task.difficulty.value}")
            print(f"   Description: {task.description[:80]}...")
            
            result = self.execute_test_task(task, orchestrator, max_iterations)
            results.append(result)
            
            # Save result
            self.save_result(result, run_id)
            
            # Track stats
            if result.success:
                passed += 1
                print(f"   ✅ PASSED (Score: {result.score:.1f}/100, Duration: {result.duration_ms}ms)")
            else:
                failed += 1
                print(f"   ❌ FAILED (Score: {result.score:.1f}/100, Duration: {result.duration_ms}ms)")
                if result.errors:
                    print(f"   Errors: {result.errors[0][:100]}...")
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Calculate statistics
        total = len(results)
        avg_score = sum(r.score for r in results) / total if total > 0 else 0.0
        avg_duration = sum(r.duration_ms for r in results) / total if total > 0 else 0.0
        
        # Save run summary
        self._save_run_summary(run_id, total, passed, failed, avg_score, avg_duration, duration_ms)
        
        # Print summary
        print(f"\n{'='*70}")
        print(f"📊 Test Suite Results: {run_id}")
        print(f"{'='*70}")
        print(f"Total: {total}")
        print(f"Passed: {passed} ({passed/total*100:.1f}%)")
        print(f"Failed: {failed} ({failed/total*100:.1f}%)")
        print(f"Average Score: {avg_score:.1f}/100")
        print(f"Average Duration: {avg_duration:.1f}ms")
        print(f"Total Duration: {duration_ms}ms ({duration_ms/1000:.1f}s)")
        print(f"{'='*70}\n")
        
        return run_id
    
    def _save_run_summary(self, run_id: str, total: int, passed: int, failed: int,
                         avg_score: float, avg_duration: float, duration_ms: int):
        """Save test run summary to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        summary = json.dumps({
            'total': total,
            'passed': passed,
            'failed': failed,
            'pass_rate': passed / total * 100 if total > 0 else 0,
            'avg_score': avg_score,
            'avg_duration_ms': avg_duration
        })
        
        cursor.execute("""
            INSERT INTO test_runs (
                run_id, timestamp, total_tasks, passed_tasks, failed_tasks,
                avg_score, avg_duration_ms, duration_ms, summary
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            run_id, datetime.now().isoformat(), total, passed, failed,
            avg_score, avg_duration, duration_ms, summary
        ))
        
        conn.commit()
        conn.close()


# Global instance
TEST_SUITE_FRAMEWORK = TestSuiteFramework()

