"""
User Feedback Collection System
Section 7.3: User Feedback

Collects and analyzes user feedback to improve the system
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum


class FeedbackType(Enum):
    """Types of feedback"""
    RATING = "rating"
    CORRECTION = "correction"
    SUGGESTION = "suggestion"
    BUG_REPORT = "bug_report"
    FEATURE_REQUEST = "feature_request"
    GENERAL = "general"


@dataclass
class Feedback:
    """Represents a user feedback entry"""
    id: Optional[int]
    timestamp: str
    interaction_id: Optional[str]
    task: str
    task_type: str
    feedback_type: FeedbackType
    rating: Optional[int]  # 1-5 scale
    comment: Optional[str]
    corrections: Optional[Dict[str, str]]  # {original: corrected}
    suggestions: Optional[List[str]]
    user_id: Optional[str]
    metadata: Optional[Dict[str, Any]]


class FeedbackCollector:
    """Collects and manages user feedback"""
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize feedback collector
        
        Args:
            data_dir: Directory for feedback storage
        """
        self.data_dir = Path(
            data_dir or Path.home() / "ai-coding-team" / "data" / "feedback"
        )
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # SQLite database for feedback
        self.db_path = self.data_dir / "feedback.db"
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database for feedback storage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Feedback table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                interaction_id TEXT,
                task TEXT NOT NULL,
                task_type TEXT NOT NULL,
                feedback_type TEXT NOT NULL,
                rating INTEGER,
                comment TEXT,
                corrections TEXT,
                suggestions TEXT,
                user_id TEXT,
                metadata TEXT,
                processed INTEGER DEFAULT 0
            )
        """)
        
        # Feedback insights table (processed feedback)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback_insights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                task_type TEXT NOT NULL,
                feedback_type TEXT NOT NULL,
                insight TEXT NOT NULL,
                action_taken TEXT,
                priority TEXT
            )
        """)
        
        # Indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_interaction_id ON feedback(interaction_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_task_type ON feedback(task_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_type ON feedback(feedback_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON feedback(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rating ON feedback(rating)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_processed ON feedback(processed)")
        
        conn.commit()
        conn.close()
    
    def submit_feedback(self,
                       task: str,
                       task_type: str,
                       feedback_type: FeedbackType,
                       rating: Optional[int] = None,
                       comment: Optional[str] = None,
                       corrections: Optional[Dict[str, str]] = None,
                       suggestions: Optional[List[str]] = None,
                       interaction_id: Optional[str] = None,
                       user_id: Optional[str] = None,
                       metadata: Optional[Dict[str, Any]] = None) -> int:
        """
        Submit user feedback
        
        Args:
            task: Task description
            task_type: Type of task
            feedback_type: Type of feedback
            rating: Rating (1-5, optional)
            comment: Feedback comment (optional)
            corrections: Dictionary of corrections {original: corrected} (optional)
            suggestions: List of suggestions (optional)
            interaction_id: Associated interaction ID (optional)
            user_id: User identifier (optional)
            metadata: Additional metadata (optional)
        
        Returns:
            Feedback ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Validate rating
        if rating is not None:
            rating = max(1, min(5, rating))
        
        corrections_json = json.dumps(corrections) if corrections else None
        suggestions_json = json.dumps(suggestions) if suggestions else None
        metadata_json = json.dumps(metadata, default=str) if metadata else None
        
        cursor.execute("""
            INSERT INTO feedback (
                timestamp, interaction_id, task, task_type, feedback_type,
                rating, comment, corrections, suggestions, user_id, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(), interaction_id, task, task_type,
            feedback_type.value, rating, comment, corrections_json,
            suggestions_json, user_id, metadata_json
        ))
        
        feedback_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        return feedback_id
    
    def get_feedback(self,
                    feedback_id: Optional[int] = None,
                    interaction_id: Optional[str] = None,
                    task_type: Optional[str] = None,
                    feedback_type: Optional[FeedbackType] = None,
                    days: Optional[int] = None,
                    min_rating: Optional[int] = None) -> List[Feedback]:
        """
        Retrieve feedback entries
        
        Args:
            feedback_id: Specific feedback ID
            interaction_id: Filter by interaction ID
            task_type: Filter by task type
            feedback_type: Filter by feedback type
            days: Filter by last N days
            min_rating: Minimum rating (filter low ratings)
        
        Returns:
            List of Feedback objects
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Build query
        query = "SELECT * FROM feedback WHERE 1=1"
        params = []
        
        if feedback_id:
            query += " AND id = ?"
            params.append(feedback_id)
        
        if interaction_id:
            query += " AND interaction_id = ?"
            params.append(interaction_id)
        
        if task_type:
            query += " AND task_type = ?"
            params.append(task_type)
        
        if feedback_type:
            query += " AND feedback_type = ?"
            params.append(feedback_type.value)
        
        if days:
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            query += " AND timestamp >= ?"
            params.append(cutoff)
        
        if min_rating:
            query += " AND rating >= ?"
            params.append(min_rating)
        
        query += " ORDER BY timestamp DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        feedback_list = []
        for row in rows:
            feedback = Feedback(
                id=row[0],
                timestamp=row[1],
                interaction_id=row[2],
                task=row[3],
                task_type=row[4],
                feedback_type=FeedbackType(row[5]),
                rating=row[6],
                comment=row[7],
                corrections=json.loads(row[8]) if row[8] else None,
                suggestions=json.loads(row[9]) if row[9] else None,
                user_id=row[10],
                metadata=json.loads(row[11]) if row[11] else None
            )
            feedback_list.append(feedback)
        
        conn.close()
        return feedback_list
    
    def get_feedback_statistics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get feedback statistics
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Dictionary with feedback statistics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        
        # Overall statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                AVG(rating) as avg_rating,
                SUM(CASE WHEN rating >= 4 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as satisfaction_rate
            FROM feedback
            WHERE timestamp >= ? AND rating IS NOT NULL
        """, (cutoff,))
        
        overall = cursor.fetchone()
        
        # By feedback type
        cursor.execute("""
            SELECT 
                feedback_type,
                COUNT(*) as count,
                AVG(rating) as avg_rating
            FROM feedback
            WHERE timestamp >= ?
            GROUP BY feedback_type
        """, (cutoff,))
        
        by_type = {
            row[0]: {'count': row[1], 'avg_rating': row[2]}
            for row in cursor.fetchall()
        }
        
        # By task type
        cursor.execute("""
            SELECT 
                task_type,
                COUNT(*) as count,
                AVG(rating) as avg_rating
            FROM feedback
            WHERE timestamp >= ?
            GROUP BY task_type
        """, (cutoff,))
        
        by_task_type = {
            row[0]: {'count': row[1], 'avg_rating': row[2]}
            for row in cursor.fetchall()
        }
        
        # Rating distribution
        cursor.execute("""
            SELECT 
                rating,
                COUNT(*) as count
            FROM feedback
            WHERE timestamp >= ? AND rating IS NOT NULL
            GROUP BY rating
            ORDER BY rating
        """, (cutoff,))
        
        rating_distribution = {
            row[0]: row[1]
            for row in cursor.fetchall()
        }
        
        # Common suggestions
        cursor.execute("""
            SELECT suggestions
            FROM feedback
            WHERE timestamp >= ? AND suggestions IS NOT NULL
        """, (cutoff,))
        
        all_suggestions = []
        for row in cursor.fetchall():
            if row[0]:
                suggestions = json.loads(row[0])
                if isinstance(suggestions, list):
                    all_suggestions.extend(suggestions)
        
        # Common corrections
        cursor.execute("""
            SELECT corrections
            FROM feedback
            WHERE timestamp >= ? AND corrections IS NOT NULL
        """, (cutoff,))
        
        all_corrections = {}
        for row in cursor.fetchall():
            if row[0]:
                corrections = json.loads(row[0])
                if isinstance(corrections, dict):
                    all_corrections.update(corrections)
        
        conn.close()
        
        return {
            'period_days': days,
            'overall': {
                'total': overall[0] if overall else 0,
                'avg_rating': overall[1] if overall and overall[1] else 0.0,
                'satisfaction_rate': overall[2] if overall and overall[2] else 0.0
            },
            'by_feedback_type': by_type,
            'by_task_type': by_task_type,
            'rating_distribution': rating_distribution,
            'total_suggestions': len(all_suggestions),
            'total_corrections': len(all_corrections)
        }
    
    def mark_processed(self, feedback_id: int):
        """Mark feedback as processed"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE feedback
            SET processed = 1
            WHERE id = ?
        """, (feedback_id,))
        
        conn.commit()
        conn.close()


# Global instance
FEEDBACK_COLLECTOR = FeedbackCollector()

