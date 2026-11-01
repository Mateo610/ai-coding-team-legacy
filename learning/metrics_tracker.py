"""
Comprehensive Metrics Tracking System
Section 7.2: Success Metrics Implementation

Tracks:
- Code generation accuracy
- Test pass rate
- User satisfaction
- Response time
- Error rate
- And more...
"""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict


@dataclass
class MetricsSnapshot:
    """Snapshot of metrics at a point in time"""
    timestamp: str
    code_generation_accuracy: float  # 0-100
    test_pass_rate: float  # 0-100
    first_gen_test_pass_rate: float  # 0-100
    error_rate: float  # 0-100
    avg_response_time_ms: float
    avg_tokens_used: float
    total_interactions: int
    successful_interactions: int
    failed_interactions: int
    by_task_type: Dict[str, Dict[str, float]]  # task_type -> metrics
    by_route: Dict[str, Dict[str, float]]  # route -> metrics
    by_agent: Dict[str, Dict[str, float]]  # agent -> metrics


class MetricsTracker:
    """Comprehensive metrics tracking and analysis"""
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize metrics tracker
        
        Args:
            data_dir: Directory for metrics storage (default: ~/ai-coding-team/data/metrics)
        """
        self.data_dir = Path(
            data_dir or Path.home() / "ai-coding-team" / "data" / "metrics"
        )
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # SQLite database for metrics
        self.db_path = self.data_dir / "metrics.db"
        self._init_database()
        
        # JSON file for snapshots (for quick access)
        self.snapshots_file = self.data_dir / "snapshots.jsonl"
    
    def _init_database(self):
        """Initialize SQLite database for metrics storage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Interactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                interaction_id TEXT UNIQUE,
                agent TEXT,
                task_type TEXT,
                route TEXT,
                task_hash TEXT,
                success_score INTEGER,
                test_passed INTEGER,
                test_total INTEGER,
                test_pass_rate REAL,
                syntax_valid INTEGER,
                execution_success INTEGER,
                tokens_used INTEGER,
                duration_ms INTEGER,
                error_type TEXT,
                error_message TEXT,
                complexity_predicted INTEGER,
                complexity_actual INTEGER,
                metadata TEXT
            )
        """)
        
        # Metrics snapshots table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                snapshot_data TEXT NOT NULL
            )
        """)
        
        # Indexes for performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp ON interactions(timestamp)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_task_type ON interactions(task_type)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_route ON interactions(route)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_agent ON interactions(agent)
        """)
        
        conn.commit()
        conn.close()
    
    def record_interaction(self, interaction_data: Dict[str, Any]) -> str:
        """
        Record an interaction with comprehensive metrics
        
        Args:
            interaction_data: Dictionary containing interaction details
        
        Returns:
            interaction_id for reference
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Extract data
        interaction_id = interaction_data.get('interaction_id', '')
        timestamp = interaction_data.get('timestamp', datetime.now().isoformat())
        agent = interaction_data.get('agent', 'unknown')
        task_type = interaction_data.get('task_type', 'general')
        route = interaction_data.get('route', 'local')
        task_hash = interaction_data.get('task_hash', '')
        
        # Evaluation results
        evaluation = interaction_data.get('evaluation', {})
        success_score = evaluation.get('score', 0) if isinstance(evaluation, dict) else (evaluation.score if hasattr(evaluation, 'score') else 0)
        
        # Test results
        test_results = interaction_data.get('test_results', {})
        test_passed = test_results.get('passed', 0) if isinstance(test_results, dict) else (test_results.passed_tests if hasattr(test_results, 'passed_tests') else 0)
        test_total = test_results.get('total', 0) if isinstance(test_results, dict) else (test_results.total_tests if hasattr(test_results, 'total_tests') else 0)
        test_pass_rate = (test_passed / test_total * 100) if test_total > 0 else 0.0
        
        # Execution results
        syntax_valid = 1 if interaction_data.get('syntax_valid', False) else 0
        execution_success = 1 if interaction_data.get('execution_success', False) else 0
        
        # Performance
        tokens_used = interaction_data.get('tokens_used', 0)
        duration_ms = interaction_data.get('duration_ms', 0)
        
        # Errors
        errors = interaction_data.get('errors', [])
        error_type = errors[0].get('type', 'none') if errors and isinstance(errors[0], dict) else ('none' if not errors else 'unknown')
        error_message = errors[0].get('message', '') if errors and isinstance(errors[0], dict) else ('; '.join(str(e) for e in errors[:3]) if errors else '')
        
        # Complexity
        complexity = interaction_data.get('complexity', {})
        complexity_predicted = complexity.get('predicted', 5) if isinstance(complexity, dict) else 5
        complexity_actual = complexity.get('actual', complexity_predicted) if isinstance(complexity, dict) else complexity_predicted
        
        # Metadata as JSON
        metadata = json.dumps(interaction_data.get('metadata', {}), default=str)
        
        # Insert into database
        cursor.execute("""
            INSERT OR REPLACE INTO interactions (
                timestamp, interaction_id, agent, task_type, route, task_hash,
                success_score, test_passed, test_total, test_pass_rate,
                syntax_valid, execution_success, tokens_used, duration_ms,
                error_type, error_message, complexity_predicted, complexity_actual,
                metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp, interaction_id, agent, task_type, route, task_hash,
            success_score, test_passed, test_total, test_pass_rate,
            syntax_valid, execution_success, tokens_used, duration_ms,
            error_type, error_message, complexity_predicted, complexity_actual,
            metadata
        ))
        
        conn.commit()
        conn.close()
        
        return interaction_id
    
    def calculate_metrics(self, 
                          start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None,
                          task_type: Optional[str] = None,
                          route: Optional[str] = None) -> MetricsSnapshot:
        """
        Calculate comprehensive metrics for a time period
        
        Args:
            start_date: Start of time period (default: 7 days ago)
            end_date: End of time period (default: now)
            task_type: Filter by task type (optional)
            route: Filter by route (optional)
        
        Returns:
            MetricsSnapshot with all calculated metrics
        """
        if start_date is None:
            start_date = datetime.now() - timedelta(days=7)
        if end_date is None:
            end_date = datetime.now()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Build query
        query = "SELECT * FROM interactions WHERE timestamp >= ? AND timestamp <= ?"
        params = [start_date.isoformat(), end_date.isoformat()]
        
        if task_type:
            query += " AND task_type = ?"
            params.append(task_type)
        
        if route:
            query += " AND route = ?"
            params.append(route)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        if not rows:
            # Return empty snapshot
            return MetricsSnapshot(
                timestamp=end_date.isoformat(),
                code_generation_accuracy=0.0,
                test_pass_rate=0.0,
                first_gen_test_pass_rate=0.0,
                error_rate=0.0,
                avg_response_time_ms=0.0,
                avg_tokens_used=0.0,
                total_interactions=0,
                successful_interactions=0,
                failed_interactions=0,
                by_task_type={},
                by_route={},
                by_agent={}
            )
        
        # Calculate metrics
        total = len(rows)
        successful = sum(1 for row in rows if row[8] >= 80)  # success_score >= 80
        failed = total - successful
        
        # Code generation accuracy (syntax + execution success)
        syntax_valid_count = sum(1 for row in rows if row[11] == 1)
        execution_success_count = sum(1 for row in rows if row[12] == 1)
        code_generation_accuracy = ((syntax_valid_count + execution_success_count) / (total * 2)) * 100
        
        # Test pass rate
        test_pass_rates = [row[9] for row in rows if row[9] is not None]
        test_pass_rate = sum(test_pass_rates) / len(test_pass_rates) if test_pass_rates else 0.0
        
        # First generation test pass rate (approximate: test_total > 0 and test_pass_rate > 0)
        first_gen_tests = [row[9] for row in rows if row[7] > 0]  # test_total > 0
        first_gen_test_pass_rate = sum(first_gen_tests) / len(first_gen_tests) if first_gen_tests else 0.0
        
        # Error rate
        error_count = sum(1 for row in rows if row[15] != 'none' and row[15] is not None)
        error_rate = (error_count / total * 100) if total > 0 else 0.0
        
        # Response time
        durations = [row[13] for row in rows if row[13] is not None and row[13] > 0]
        avg_response_time_ms = sum(durations) / len(durations) if durations else 0.0
        
        # Tokens
        tokens = [row[12] for row in rows if row[12] is not None and row[12] > 0]
        avg_tokens_used = sum(tokens) / len(tokens) if tokens else 0.0
        
        # By task type
        by_task_type = defaultdict(lambda: {'count': 0, 'accuracy': 0.0, 'test_pass_rate': 0.0, 'error_rate': 0.0})
        for row in rows:
            tt = row[3] or 'general'
            by_task_type[tt]['count'] += 1
            if row[11] == 1 and row[12] == 1:
                by_task_type[tt]['accuracy'] += 1
            if row[9] is not None:
                by_task_type[tt]['test_pass_rate'] += row[9]
            if row[15] != 'none' and row[15] is not None:
                by_task_type[tt]['error_rate'] += 1
        
        for tt in by_task_type:
            count = by_task_type[tt]['count']
            by_task_type[tt]['accuracy'] = (by_task_type[tt]['accuracy'] / count * 100) if count > 0 else 0.0
            by_task_type[tt]['test_pass_rate'] = (by_task_type[tt]['test_pass_rate'] / count) if count > 0 else 0.0
            by_task_type[tt]['error_rate'] = (by_task_type[tt]['error_rate'] / count * 100) if count > 0 else 0.0
        
        # By route
        by_route = defaultdict(lambda: {'count': 0, 'accuracy': 0.0, 'test_pass_rate': 0.0, 'avg_time': 0.0})
        for row in rows:
            rt = row[4] or 'local'
            by_route[rt]['count'] += 1
            if row[11] == 1 and row[12] == 1:
                by_route[rt]['accuracy'] += 1
            if row[9] is not None:
                by_route[rt]['test_pass_rate'] += row[9]
            if row[13] is not None:
                by_route[rt]['avg_time'] += row[13]
        
        for rt in by_route:
            count = by_route[rt]['count']
            by_route[rt]['accuracy'] = (by_route[rt]['accuracy'] / count * 100) if count > 0 else 0.0
            by_route[rt]['test_pass_rate'] = (by_route[rt]['test_pass_rate'] / count) if count > 0 else 0.0
            by_route[rt]['avg_time'] = (by_route[rt]['avg_time'] / count) if count > 0 else 0.0
        
        # By agent
        by_agent = defaultdict(lambda: {'count': 0, 'accuracy': 0.0, 'test_pass_rate': 0.0})
        for row in rows:
            ag = row[2] or 'unknown'
            by_agent[ag]['count'] += 1
            if row[11] == 1 and row[12] == 1:
                by_agent[ag]['accuracy'] += 1
            if row[9] is not None:
                by_agent[ag]['test_pass_rate'] += row[9]
        
        for ag in by_agent:
            count = by_agent[ag]['count']
            by_agent[ag]['accuracy'] = (by_agent[ag]['accuracy'] / count * 100) if count > 0 else 0.0
            by_agent[ag]['test_pass_rate'] = (by_agent[ag]['test_pass_rate'] / count) if count > 0 else 0.0
        
        conn.close()
        
        snapshot = MetricsSnapshot(
            timestamp=end_date.isoformat(),
            code_generation_accuracy=code_generation_accuracy,
            test_pass_rate=test_pass_rate,
            first_gen_test_pass_rate=first_gen_test_pass_rate,
            error_rate=error_rate,
            avg_response_time_ms=avg_response_time_ms,
            avg_tokens_used=avg_tokens_used,
            total_interactions=total,
            successful_interactions=successful,
            failed_interactions=failed,
            by_task_type=dict(by_task_type),
            by_route=dict(by_route),
            by_agent=dict(by_agent)
        )
        
        # Save snapshot
        self._save_snapshot(snapshot)
        
        return snapshot
    
    def _save_snapshot(self, snapshot: MetricsSnapshot):
        """Save metrics snapshot to JSONL file"""
        with open(self.snapshots_file, 'a') as f:
            f.write(json.dumps(asdict(snapshot), default=str) + '\n')
    
    def get_recent_snapshots(self, days: int = 7) -> List[MetricsSnapshot]:
        """Get recent metrics snapshots"""
        snapshots = []
        cutoff = datetime.now() - timedelta(days=days)
        
        if not self.snapshots_file.exists():
            return snapshots
        
        with open(self.snapshots_file, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if datetime.fromisoformat(data['timestamp']) >= cutoff:
                        snapshots.append(MetricsSnapshot(**data))
                except:
                    continue
        
        return snapshots
    
    def get_metrics_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get summary of metrics for the last N days"""
        snapshot = self.calculate_metrics(
            start_date=datetime.now() - timedelta(days=days)
        )
        
        return {
            'period_days': days,
            'total_interactions': snapshot.total_interactions,
            'code_generation_accuracy': round(snapshot.code_generation_accuracy, 2),
            'test_pass_rate': round(snapshot.test_pass_rate, 2),
            'first_gen_test_pass_rate': round(snapshot.first_gen_test_pass_rate, 2),
            'error_rate': round(snapshot.error_rate, 2),
            'avg_response_time_ms': round(snapshot.avg_response_time_ms, 2),
            'avg_tokens_used': round(snapshot.avg_tokens_used, 2),
            'success_rate': round((snapshot.successful_interactions / snapshot.total_interactions * 100) if snapshot.total_interactions > 0 else 0, 2),
            'by_task_type': {
                k: {
                    'count': v['count'],
                    'accuracy': round(v['accuracy'], 2),
                    'test_pass_rate': round(v['test_pass_rate'], 2),
                    'error_rate': round(v['error_rate'], 2)
                }
                for k, v in snapshot.by_task_type.items()
            },
            'by_route': {
                k: {
                    'count': v['count'],
                    'accuracy': round(v['accuracy'], 2),
                    'test_pass_rate': round(v['test_pass_rate'], 2),
                    'avg_time_ms': round(v['avg_time'], 2)
                }
                for k, v in snapshot.by_route.items()
            }
        }
    
    def check_goals(self) -> Dict[str, Any]:
        """
        Check progress toward goals from MODEL_IMPROVEMENT_PLAN.md
        
        Goals:
        - Code Generation Accuracy: >90%
        - Test Pass Rate: >85% (first generation)
        - Error Rate: <5%
        - Task Coverage: >80%
        """
        snapshot = self.calculate_metrics()
        
        goals = {
            'code_generation_accuracy': {
                'target': 90.0,
                'current': snapshot.code_generation_accuracy,
                'met': snapshot.code_generation_accuracy >= 90.0,
                'gap': max(0, 90.0 - snapshot.code_generation_accuracy)
            },
            'first_gen_test_pass_rate': {
                'target': 85.0,
                'current': snapshot.first_gen_test_pass_rate,
                'met': snapshot.first_gen_test_pass_rate >= 85.0,
                'gap': max(0, 85.0 - snapshot.first_gen_test_pass_rate)
            },
            'error_rate': {
                'target': 5.0,
                'current': snapshot.error_rate,
                'met': snapshot.error_rate <= 5.0,
                'gap': max(0, snapshot.error_rate - 5.0)
            }
        }
        
        return {
            'goals': goals,
            'overall_progress': sum(1 for g in goals.values() if g['met']) / len(goals) * 100,
            'snapshot': snapshot
        }


# Global instance
METRICS_TRACKER = MetricsTracker()

