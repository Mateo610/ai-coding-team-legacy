"""
Enhanced Routing & Model Selection with Learning
Section 6: Routing & Model Selection Enhancement

Improves complexity prediction accuracy and optimizes model selection based on:
- Historical performance data
- Task type specific routing
- Learned patterns from metrics
"""

import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from collections import defaultdict
from dataclasses import dataclass


@dataclass
class RoutingDecision:
    """Represents a routing decision and its outcome"""
    task_type: str
    task_hash: str
    predicted_complexity: int
    actual_complexity: Optional[int]
    route_used: str  # 'local' or 'claude'
    success_score: float
    duration_ms: int
    timestamp: str


class RoutingOptimizer:
    """
    Optimizes routing decisions based on historical performance
    """
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize routing optimizer
        
        Args:
            data_dir: Directory for routing data storage
        """
        self.data_dir = Path(
            data_dir or Path.home() / "ai-coding-team" / "data" / "routing"
        )
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # SQLite database for routing decisions
        self.db_path = self.data_dir / "routing_decisions.db"
        self._init_database()
        
        # Learned task-type-specific routing preferences
        self._task_type_routing_prefs = None
        self._load_routing_preferences()
    
    def _init_database(self):
        """Initialize SQLite database for routing decisions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Routing decisions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS routing_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                task_type TEXT NOT NULL,
                task_hash TEXT NOT NULL,
                predicted_complexity INTEGER NOT NULL,
                actual_complexity INTEGER,
                route_used TEXT NOT NULL,
                success_score REAL NOT NULL,
                duration_ms INTEGER NOT NULL,
                tokens_used INTEGER,
                model_used TEXT,
                metadata TEXT
            )
        """)
        
        # Task type routing preferences (learned)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS task_type_routing (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_type TEXT UNIQUE NOT NULL,
                preferred_route TEXT NOT NULL,
                avg_success_score REAL NOT NULL,
                avg_duration_ms REAL NOT NULL,
                sample_count INTEGER NOT NULL,
                last_updated TEXT NOT NULL
            )
        """)
        
        # Indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_task_type ON routing_decisions(task_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON routing_decisions(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_task_hash ON routing_decisions(task_hash)")
        
        conn.commit()
        conn.close()
    
    def record_decision(self,
                       task_type: str,
                       task_hash: str,
                       predicted_complexity: int,
                       route_used: str,
                       success_score: float,
                       duration_ms: int,
                       actual_complexity: Optional[int] = None,
                       tokens_used: Optional[int] = None,
                       model_used: Optional[str] = None,
                       metadata: Optional[Dict[str, Any]] = None):
        """
        Record a routing decision and its outcome
        
        Args:
            task_type: Type of task
            task_hash: Hash of the task
            predicted_complexity: Predicted complexity (1-10)
            route_used: Route used ('local' or 'claude')
            success_score: Success score (0-100)
            duration_ms: Duration in milliseconds
            actual_complexity: Actual complexity (optional, for learning)
            tokens_used: Tokens used
            model_used: Model used
            metadata: Additional metadata
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        metadata_json = None
        if metadata:
            import json
            metadata_json = json.dumps(metadata, default=str)
        
        cursor.execute("""
            INSERT INTO routing_decisions (
                timestamp, task_type, task_hash, predicted_complexity, actual_complexity,
                route_used, success_score, duration_ms, tokens_used, model_used, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(), task_type, task_hash, predicted_complexity,
            actual_complexity, route_used, success_score, duration_ms,
            tokens_used, model_used, metadata_json
        ))
        
        # Update task type routing preferences
        self._update_task_type_routing(cursor, task_type, route_used, success_score, duration_ms)
        
        conn.commit()
        conn.close()
        
        # Invalidate cached preferences
        self._task_type_routing_prefs = None
    
    def _update_task_type_routing(self, cursor, task_type: str, route: str,
                                  success_score: float, duration_ms: int):
        """Update learned task type routing preferences"""
        # Get current stats for this task type and route
        cursor.execute("""
            SELECT AVG(success_score), AVG(duration_ms), COUNT(*)
            FROM routing_decisions
            WHERE task_type = ? AND route_used = ?
        """, (task_type, route))
        
        result = cursor.fetchone()
        if result and result[2] > 0:
            avg_score, avg_duration, count = result
            
            # Check if we have enough data to prefer a route
            if count >= 5:  # Need at least 5 samples
                # Compare with other route
                other_route = 'claude' if route == 'local' else 'local'
                cursor.execute("""
                    SELECT AVG(success_score), AVG(duration_ms), COUNT(*)
                    FROM routing_decisions
                    WHERE task_type = ? AND route_used = ?
                """, (task_type, other_route))
                
                other_result = cursor.fetchone()
                if other_result and other_result[2] >= 5:
                    other_avg_score, other_avg_duration, other_count = other_result
                    
                    # Determine preferred route based on score and duration
                    # Prefer route with higher score, or if similar, faster one
                    score_diff = avg_score - other_avg_score
                    
                    if score_diff > 5 or (abs(score_diff) <= 5 and avg_duration < other_avg_duration):
                        preferred_route = route
                        preferred_score = avg_score
                        preferred_duration = avg_duration
                        total_count = count + other_count
                    else:
                        preferred_route = other_route
                        preferred_score = other_avg_score
                        preferred_duration = other_avg_duration
                        total_count = count + other_count
                    
                    # Update or insert preference
                    cursor.execute("""
                        INSERT INTO task_type_routing (
                            task_type, preferred_route, avg_success_score,
                            avg_duration_ms, sample_count, last_updated
                        ) VALUES (?, ?, ?, ?, ?, ?)
                        ON CONFLICT(task_type) DO UPDATE SET
                            preferred_route = excluded.preferred_route,
                            avg_success_score = excluded.avg_success_score,
                            avg_duration_ms = excluded.avg_duration_ms,
                            sample_count = excluded.sample_count,
                            last_updated = excluded.last_updated
                    """, (
                        task_type, preferred_route, preferred_score,
                        preferred_duration, total_count, datetime.now().isoformat()
                    ))
    
    def _load_routing_preferences(self):
        """Load learned routing preferences from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT task_type, preferred_route, avg_success_score, sample_count
            FROM task_type_routing
        """)
        
        self._task_type_routing_prefs = {
            row[0]: {
                'preferred_route': row[1],
                'avg_success_score': row[2],
                'sample_count': row[3]
            }
            for row in cursor.fetchall()
        }
        
        conn.close()
    
    def get_optimal_route(self,
                         task_type: str,
                         predicted_complexity: int,
                         complexity_threshold: int = 8,
                         use_learning: bool = True) -> Tuple[str, str]:
        """
        Get optimal route for a task
        
        Args:
            task_type: Type of task
            predicted_complexity: Predicted complexity (1-10)
            complexity_threshold: Complexity threshold for routing (default: 8)
            use_learning: Whether to use learned preferences (default: True)
        
        Returns:
            Tuple of (route, reason) where route is 'local' or 'claude'
        """
        # Default routing based on complexity
        default_route = "claude" if predicted_complexity >= complexity_threshold else "local"
        default_reason = f"Complexity {predicted_complexity} {'>=' if predicted_complexity >= complexity_threshold else '<'} threshold {complexity_threshold}"
        
        if not use_learning:
            return default_route, default_reason
        
        # Load preferences if not cached
        if self._task_type_routing_prefs is None:
            self._load_routing_preferences()
        
        # Check if we have learned preference for this task type
        if task_type in self._task_type_routing_prefs:
            pref = self._task_type_routing_prefs[task_type]
            
            # Only use preference if we have enough samples and it differs from default
            if pref['sample_count'] >= 10 and pref['preferred_route'] != default_route:
                # Check if preference is significantly better (score diff > 10%)
                score_improvement = pref['avg_success_score'] - 70  # Baseline assumption
                
                if score_improvement > 5:  # At least 5% improvement
                    return pref['preferred_route'], \
                           f"Learned preference: {pref['preferred_route']} performs better " \
                           f"for {task_type} tasks (score: {pref['avg_success_score']:.1f}, " \
                           f"based on {pref['sample_count']} samples)"
        
        return default_route, default_reason
    
    def get_routing_stats(self, days: int = 30) -> Dict[str, Any]:
        """
        Get routing statistics for analysis
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Dictionary with routing statistics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        # Overall stats
        cursor.execute("""
            SELECT 
                route_used,
                COUNT(*) as count,
                AVG(success_score) as avg_score,
                AVG(duration_ms) as avg_duration,
                SUM(CASE WHEN success_score >= 80 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as success_rate
            FROM routing_decisions
            WHERE timestamp >= ?
            GROUP BY route_used
        """, (cutoff_date,))
        
        overall_stats = {
            row[0]: {
                'count': row[1],
                'avg_score': row[2],
                'avg_duration': row[3],
                'success_rate': row[4]
            }
            for row in cursor.fetchall()
        }
        
        # By task type
        cursor.execute("""
            SELECT 
                task_type,
                route_used,
                COUNT(*) as count,
                AVG(success_score) as avg_score,
                AVG(duration_ms) as avg_duration
            FROM routing_decisions
            WHERE timestamp >= ?
            GROUP BY task_type, route_used
        """, (cutoff_date,))
        
        by_task_type = defaultdict(lambda: {'local': {}, 'claude': {}})
        for row in cursor.fetchall():
            task_type, route, count, avg_score, avg_duration = row
            by_task_type[task_type][route] = {
                'count': count,
                'avg_score': avg_score,
                'avg_duration': avg_duration
            }
        
        # Routing accuracy (predicted vs actual complexity)
        cursor.execute("""
            SELECT 
                AVG(ABS(predicted_complexity - COALESCE(actual_complexity, predicted_complexity))) as avg_error
            FROM routing_decisions
            WHERE timestamp >= ? AND actual_complexity IS NOT NULL
        """, (cutoff_date,))
        
        accuracy_result = cursor.fetchone()
        avg_prediction_error = accuracy_result[0] if accuracy_result[0] else 0.0
        
        conn.close()
        
        return {
            'overall': overall_stats,
            'by_task_type': dict(by_task_type),
            'avg_prediction_error': avg_prediction_error,
            'days': days
        }


# Global instance
ROUTING_OPTIMIZER = RoutingOptimizer()

