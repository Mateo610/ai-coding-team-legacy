"""
Error Pattern Database & Learning System
Section 7.1: Error Analysis Enhancement

Tracks common error patterns and learns from them to improve prompts and examples.
"""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import re


@dataclass
class ErrorPattern:
    """Represents a recurring error pattern"""
    error_type: str
    error_message_pattern: str
    task_type: str
    frequency: int
    first_seen: str
    last_seen: str
    fix_suggestions: List[str]
    code_examples: List[str]
    common_context: str  # Common task/context where this occurs


class ErrorPatternDatabase:
    """Database for tracking and learning from error patterns"""
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize error pattern database
        
        Args:
            data_dir: Directory for database (default: ~/ai-coding-team/data/errors)
        """
        self.data_dir = Path(
            data_dir or Path.home() / "ai-coding-team" / "data" / "errors"
        )
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # SQLite database
        self.db_path = self.data_dir / "error_patterns.db"
        self._init_database()
        
        # Pattern cache for quick access
        self._pattern_cache: Optional[Dict[str, List[ErrorPattern]]] = None
        self._cache_timestamp: Optional[datetime] = None
    
    def _init_database(self):
        """Initialize SQLite database for error patterns"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Error patterns table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS error_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                error_type TEXT NOT NULL,
                error_message_pattern TEXT NOT NULL,
                task_type TEXT,
                frequency INTEGER DEFAULT 1,
                first_seen TEXT NOT NULL,
                last_seen TEXT NOT NULL,
                fix_suggestions TEXT,  -- JSON array
                code_examples TEXT,  -- JSON array
                common_context TEXT,
                UNIQUE(error_type, error_message_pattern, task_type)
            )
        """)
        
        # Individual errors table (for pattern matching)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS errors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                error_type TEXT NOT NULL,
                error_message TEXT NOT NULL,
                task_type TEXT,
                task_hash TEXT,
                fix_applied INTEGER DEFAULT 0,  -- 1 if fix was successful
                metadata TEXT  -- JSON
            )
        """)
        
        # Indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_error_type ON errors(error_type)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_task_type ON errors(task_type)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp ON errors(timestamp)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_pattern_type ON error_patterns(error_type, task_type)
        """)
        
        conn.commit()
        conn.close()
    
    def record_error(self, 
                     error_type: str,
                     error_message: str,
                     task_type: str = "general",
                     task_hash: str = "",
                     fix_applied: bool = False,
                     metadata: Dict[str, Any] = None) -> int:
        """
        Record an individual error occurrence
        
        Args:
            error_type: Type of error (syntax, runtime, test_failure, etc.)
            error_message: Error message
            task_type: Task type where error occurred
            task_hash: Hash of the task for grouping
            fix_applied: Whether a fix was successfully applied
            metadata: Additional metadata
        
        Returns:
            Error ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        metadata_json = json.dumps(metadata or {}, default=str)
        
        cursor.execute("""
            INSERT INTO errors (
                timestamp, error_type, error_message, task_type, 
                task_hash, fix_applied, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp, error_type, error_message[:500], task_type,
            task_hash, 1 if fix_applied else 0, metadata_json
        ))
        
        error_id = cursor.lastrowid
        
        # Update or create error pattern
        pattern = self._normalize_error_message(error_message)
        self._update_pattern(
            cursor, error_type, pattern, task_type, error_message
        )
        
        conn.commit()
        conn.close()
        
        # Invalidate cache
        self._pattern_cache = None
        
        return error_id
    
    def _normalize_error_message(self, error_msg: str) -> str:
        """
        Normalize error message to create pattern
        
        Examples:
        - "NameError: name 'x' is not defined" → "NameError: name '*' is not defined"
        - "SyntaxError: invalid syntax (test.py, line 5)" → "SyntaxError: invalid syntax (*, line *)"
        """
        pattern = error_msg
        
        # Replace variable names with *
        pattern = re.sub(r"name '[\w_]+'", "name '*'", pattern)
        
        # Replace file paths with *
        pattern = re.sub(r"\([^,]+\.py, line \d+\)", "(*, line *)", pattern)
        
        # Replace line numbers
        pattern = re.sub(r"line \d+", "line *", pattern)
        
        # Replace specific values in assertions
        pattern = re.sub(r"assert .+ == .+", "assert * == *", pattern)
        
        return pattern
    
    def _update_pattern(self, 
                       cursor: sqlite3.Cursor,
                       error_type: str,
                       pattern: str,
                       task_type: str,
                       original_message: str):
        """Update or create error pattern"""
        # Check if pattern exists
        cursor.execute("""
            SELECT id, frequency, fix_suggestions, code_examples, common_context
            FROM error_patterns
            WHERE error_type = ? AND error_message_pattern = ? AND task_type = ?
        """, (error_type, pattern, task_type))
        
        row = cursor.fetchone()
        
        if row:
            # Update existing pattern
            pattern_id, frequency, fix_suggestions_json, code_examples_json, common_context = row
            
            # Increment frequency
            frequency += 1
            
            # Update last_seen
            cursor.execute("""
                UPDATE error_patterns
                SET frequency = ?, last_seen = ?
                WHERE id = ?
            """, (frequency, datetime.now().isoformat(), pattern_id))
        else:
            # Create new pattern
            cursor.execute("""
                INSERT INTO error_patterns (
                    error_type, error_message_pattern, task_type,
                    frequency, first_seen, last_seen,
                    fix_suggestions, code_examples, common_context
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                error_type, pattern, task_type,
                1, datetime.now().isoformat(), datetime.now().isoformat(),
                json.dumps([]), json.dumps([]), ""
            ))
    
    def get_common_patterns(self,
                           error_type: Optional[str] = None,
                           task_type: Optional[str] = None,
                           min_frequency: int = 2,
                           days: int = 30) -> List[ErrorPattern]:
        """
        Get common error patterns
        
        Args:
            error_type: Filter by error type (optional)
            task_type: Filter by task type (optional)
            min_frequency: Minimum frequency to include
            days: Look back N days
        
        Returns:
            List of ErrorPattern objects sorted by frequency
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff = datetime.now() - timedelta(days=days)
        
        query = """
            SELECT error_type, error_message_pattern, task_type, frequency,
                   first_seen, last_seen, fix_suggestions, code_examples, common_context
            FROM error_patterns
            WHERE last_seen >= ? AND frequency >= ?
        """
        params = [cutoff.isoformat(), min_frequency]
        
        if error_type:
            query += " AND error_type = ?"
            params.append(error_type)
        
        if task_type:
            query += " AND task_type = ?"
            params.append(task_type)
        
        query += " ORDER BY frequency DESC, last_seen DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        patterns = []
        for row in rows:
            patterns.append(ErrorPattern(
                error_type=row[0],
                error_message_pattern=row[1],
                task_type=row[2] or "general",
                frequency=row[3],
                first_seen=row[4],
                last_seen=row[5],
                fix_suggestions=json.loads(row[6]) if row[6] else [],
                code_examples=json.loads(row[7]) if row[7] else [],
                common_context=row[8] or ""
            ))
        
        return patterns
    
    def get_error_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get error statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff = datetime.now() - timedelta(days=days)
        
        # Total errors
        cursor.execute("""
            SELECT COUNT(*) FROM errors WHERE timestamp >= ?
        """, (cutoff.isoformat(),))
        total_errors = cursor.fetchone()[0]
        
        # Errors by type
        cursor.execute("""
            SELECT error_type, COUNT(*) as count
            FROM errors
            WHERE timestamp >= ?
            GROUP BY error_type
            ORDER BY count DESC
        """, (cutoff.isoformat(),))
        by_type = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Errors by task type
        cursor.execute("""
            SELECT task_type, COUNT(*) as count
            FROM errors
            WHERE timestamp >= ?
            GROUP BY task_type
            ORDER BY count DESC
        """, (cutoff.isoformat(),))
        by_task_type = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Fix success rate
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(fix_applied) as fixed
            FROM errors
            WHERE timestamp >= ?
        """, (cutoff.isoformat(),))
        row = cursor.fetchone()
        fix_success_rate = (row[1] / row[0] * 100) if row[0] > 0 else 0.0
        
        conn.close()
        
        return {
            'total_errors': total_errors,
            'by_type': by_type,
            'by_task_type': by_task_type,
            'fix_success_rate': fix_success_rate,
            'period_days': days
        }
    
    def get_fix_suggestions(self,
                           error_type: str,
                           error_message: str,
                           task_type: str = "general") -> Dict[str, Any]:
        """
        Get fix suggestions based on error pattern matching
        
        Returns:
            Dictionary with fix suggestions, code examples, and pattern frequency
        """
        pattern = self._normalize_error_message(error_message)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Find matching pattern
        cursor.execute("""
            SELECT fix_suggestions, code_examples, frequency, common_context
            FROM error_patterns
            WHERE error_type = ? AND error_message_pattern = ? AND task_type = ?
            ORDER BY frequency DESC
            LIMIT 1
        """, (error_type, pattern, task_type))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'fix_suggestions': json.loads(row[0]) if row[0] else [],
                'code_examples': json.loads(row[1]) if row[1] else [],
                'frequency': row[2],
                'common_context': row[3] or "",
                'pattern_matched': True
            }
        else:
            return {
                'fix_suggestions': [],
                'code_examples': [],
                'frequency': 0,
                'common_context': "",
                'pattern_matched': False
            }


class EnhancedErrorAnalyzer:
    """Enhanced error analyzer with pattern learning"""
    
    def __init__(self, error_db: Optional[ErrorPatternDatabase] = None):
        """
        Initialize enhanced error analyzer
        
        Args:
            error_db: ErrorPatternDatabase instance (default: creates new one)
        """
        from agents.error_analyzer import ErrorAnalyzer
        
        # Use existing ErrorAnalyzer as base
        self.base_analyzer = ErrorAnalyzer()
        self.error_db = error_db or ErrorPatternDatabase()
    
    def generate_fix_prompt(self, analysis: Dict[str, Any], code: str, original_task: str) -> str:
        """
        Generate improved task prompt with error context and pattern-based fixes
        
        Returns a new task string that includes error information and learned fixes
        """
        # Use base analyzer's method first
        fix_task = self.base_analyzer.generate_fix_prompt(analysis, code, original_task)
        
        # Enhance with pattern-based fixes if available
        if analysis['has_errors']:
            error_type = analysis['error_type']
            task_type = analysis.get('task_type', 'general')
            
            # Get pattern-based suggestions
            for error_msg in analysis.get('specific_errors', [])[:2]:  # Top 2 errors
                pattern_info = self.error_db.get_fix_suggestions(
                    error_type=error_type,
                    error_message=error_msg,
                    task_type=task_type
                )
                
                if pattern_info['pattern_matched'] and pattern_info['fix_suggestions']:
                    # Add pattern-based fixes
                    pattern_section = f"""
=== Learned from Similar Errors ({pattern_info['frequency']} occurrences) ===
{chr(10).join('- ' + fix for fix in pattern_info['fix_suggestions'][:3])}
"""
                    fix_task += pattern_section
        
        return fix_task
    
    def analyze(self, validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze errors with enhanced categorization and pattern matching
        
        Returns:
            Enhanced error analysis with pattern-based suggestions
        """
        # Use base analyzer for initial analysis
        analysis = self.base_analyzer.analyze(validation_results)
        
        if not analysis['has_errors']:
            return analysis
        
        # Enhance with pattern matching
        error_type = analysis['error_type']
        task_type = validation_results.get('task_type', 'general')
        
        # Try to match patterns for each specific error
        enhanced_suggestions = []
        for error_msg in analysis['specific_errors']:
            pattern_info = self.error_db.get_fix_suggestions(
                error_type=error_type,
                error_message=error_msg,
                task_type=task_type
            )
            
            if pattern_info['pattern_matched'] and pattern_info['fix_suggestions']:
                # Add pattern-based suggestions (higher priority)
                enhanced_suggestions.extend(pattern_info['fix_suggestions'])
                if pattern_info['code_examples']:
                    analysis.setdefault('code_examples', []).extend(pattern_info['code_examples'])
        
        # Merge suggestions (pattern-based first, then general)
        if enhanced_suggestions:
            analysis['fix_suggestions'] = "\n".join([
                "=== Pattern-Based Fixes (from similar errors) ===",
                "\n".join(enhanced_suggestions),
                "\n=== General Fix Suggestions ===",
                analysis['fix_suggestions']
            ])
        
        # Record error for pattern learning
        for error_msg in analysis['specific_errors']:
            self.error_db.record_error(
                error_type=error_type,
                error_message=error_msg,
                task_type=task_type,
                metadata={
                    'code_locations': analysis.get('code_locations', []),
                    'has_fix_suggestions': bool(analysis.get('fix_suggestions'))
                }
            )
        
        return analysis
    
    def get_pattern_insights(self, days: int = 30) -> Dict[str, Any]:
        """Get insights from error patterns"""
        stats = self.error_db.get_error_statistics(days=days)
        patterns = self.error_db.get_common_patterns(min_frequency=3, days=days)
        
        return {
            'statistics': stats,
            'top_patterns': [
                {
                    'error_type': p.error_type,
                    'pattern': p.error_message_pattern[:100],
                    'frequency': p.frequency,
                    'task_type': p.task_type
                }
                for p in patterns[:10]
            ],
            'recommendations': self._generate_recommendations(stats, patterns)
        }
    
    def _generate_recommendations(self, 
                                 stats: Dict[str, Any],
                                 patterns: List[ErrorPattern]) -> List[str]:
        """Generate recommendations based on error patterns"""
        recommendations = []
        
        # Check most common error types
        if stats['by_type']:
            most_common = max(stats['by_type'].items(), key=lambda x: x[1])
            if most_common[1] > 5:
                recommendations.append(
                    f"Most common error: {most_common[0]} ({most_common[1]} occurrences). "
                    f"Consider adding examples or improving prompts for this error type."
                )
        
        # Check task types with most errors
        if stats['by_task_type']:
            most_problematic = max(stats['by_task_type'].items(), key=lambda x: x[1])
            if most_problematic[1] > 5:
                recommendations.append(
                    f"Task type '{most_problematic[0]}' has {most_problematic[1]} errors. "
                    f"May need improved task-specific prompts or examples."
                )
        
        # Check recurring patterns
        high_frequency_patterns = [p for p in patterns if p.frequency >= 5]
        if high_frequency_patterns:
            recommendations.append(
                f"{len(high_frequency_patterns)} error patterns occur frequently (≥5 times). "
                f"Consider updating prompts with fixes for these patterns."
            )
        
        # Check fix success rate
        if stats['fix_success_rate'] < 70:
            recommendations.append(
                f"Fix success rate is {stats['fix_success_rate']:.1f}%. "
                f"May need to improve fix suggestions or error categorization."
            )
        
        if not recommendations:
            recommendations.append("No significant error patterns detected. System performing well!")
        
        return recommendations


# Global instance
ERROR_PATTERN_DB = ErrorPatternDatabase()
ENHANCED_ERROR_ANALYZER = EnhancedErrorAnalyzer(ERROR_PATTERN_DB)

