"""
View test suite results and performance trends
Section 8.1: Create Test Suite

Dashboard for viewing test results, trends, and regression detection
"""

import sys
import sqlite3
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from collections import defaultdict
import argparse

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.test_suite_framework import TEST_SUITE_FRAMEWORK


def print_test_results_dashboard(run_id: Optional[str] = None, days: int = 30):
    """Print formatted test results dashboard"""
    framework = TEST_SUITE_FRAMEWORK
    conn = sqlite3.connect(framework.db_path)
    cursor = conn.cursor()
    
    print("\n" + "="*70)
    print("📊 TEST SUITE RESULTS DASHBOARD")
    print("="*70)
    
    # Get run summary
    if run_id:
        cursor.execute("""
            SELECT run_id, timestamp, total_tasks, passed_tasks, failed_tasks,
                   avg_score, avg_duration_ms, duration_ms, summary
            FROM test_runs
            WHERE run_id = ?
        """, (run_id,))
        run = cursor.fetchone()
        
        if run:
            print(f"\n🎯 Test Run: {run[0]}")
            print(f"   Timestamp: {run[1]}")
            print(f"   Total Tasks: {run[2]}")
            print(f"   Passed: {run[3]} ({run[3]/run[2]*100:.1f}%)")
            print(f"   Failed: {run[4]} ({run[4]/run[2]*100:.1f}%)")
            print(f"   Average Score: {run[5]:.1f}/100")
            print(f"   Average Duration: {run[6]:.1f}ms")
            print(f"   Total Duration: {run[7]}ms ({run[7]/1000:.1f}s)")
        else:
            print(f"\n❌ Run ID '{run_id}' not found")
            return
    else:
        # Get latest run
        cursor.execute("""
            SELECT run_id, timestamp, total_tasks, passed_tasks, failed_tasks,
                   avg_score, avg_duration_ms, duration_ms
            FROM test_runs
            ORDER BY timestamp DESC
            LIMIT 1
        """)
        run = cursor.fetchone()
        
        if run:
            print(f"\n🎯 Latest Test Run: {run[0]}")
            print(f"   Timestamp: {run[1]}")
            print(f"   Total Tasks: {run[2]}")
            print(f"   Passed: {run[3]} ({run[3]/run[2]*100:.1f}%)")
            print(f"   Failed: {run[4]} ({run[4]/run[2]*100:.1f}%)")
            print(f"   Average Score: {run[5]:.1f}/100")
            print(f"   Average Duration: {run[6]:.1f}ms")
            run_id = run[0]
        else:
            print("\n❌ No test runs found")
            return
    
    # Get detailed results for this run
    print(f"\n{'='*70}")
    print("📋 DETAILED RESULTS")
    print(f"{'='*70}")
    
    cursor.execute("""
        SELECT task_id, task_name, task_category, task_difficulty, success, score,
               duration_ms, iterations, errors
        FROM test_results
        WHERE run_id = ?
        ORDER BY task_category, task_id
    """, (run_id,))
    
    results = cursor.fetchall()
    
    # Group by category
    by_category = defaultdict(lambda: {'total': 0, 'passed': 0, 'failed': 0, 'avg_score': 0.0})
    by_difficulty = defaultdict(lambda: {'total': 0, 'passed': 0, 'failed': 0, 'avg_score': 0.0})
    
    print(f"\n{'Task ID':<15} {'Category':<12} {'Difficulty':<10} {'Status':<8} {'Score':<8} {'Duration':<10}")
    print("-" * 70)
    
    for result in results:
        task_id, name, category, difficulty, success, score, duration, iterations, errors = result
        
        status = "✅ PASS" if success else "❌ FAIL"
        score_str = f"{score:.1f}/100"
        
        print(f"{task_id:<15} {category:<12} {difficulty:<10} {status:<8} {score_str:<8} {duration}ms")
        
        # Track statistics
        by_category[category]['total'] += 1
        by_difficulty[difficulty]['total'] += 1
        if success:
            by_category[category]['passed'] += 1
            by_difficulty[difficulty]['passed'] += 1
        else:
            by_category[category]['failed'] += 1
            by_difficulty[difficulty]['failed'] += 1
        
        by_category[category]['avg_score'] += score
        by_difficulty[difficulty]['avg_score'] += score
    
    # Calculate averages
    for cat in by_category:
        total = by_category[cat]['total']
        if total > 0:
            by_category[cat]['avg_score'] /= total
    
    for diff in by_difficulty:
        total = by_difficulty[diff]['total']
        if total > 0:
            by_difficulty[diff]['avg_score'] /= total
    
    # Print statistics
    print(f"\n{'='*70}")
    print("📈 STATISTICS BY CATEGORY")
    print(f"{'='*70}")
    
    for category in sorted(by_category.keys()):
        stats = by_category[category]
        pass_rate = stats['passed'] / stats['total'] * 100 if stats['total'] > 0 else 0
        print(f"\n{category}:")
        print(f"   Total: {stats['total']}")
        print(f"   Passed: {stats['passed']} ({pass_rate:.1f}%)")
        print(f"   Failed: {stats['failed']}")
        print(f"   Avg Score: {stats['avg_score']:.1f}/100")
    
    print(f"\n{'='*70}")
    print("📊 STATISTICS BY DIFFICULTY")
    print(f"{'='*70}")
    
    for difficulty in sorted(by_difficulty.keys()):
        stats = by_difficulty[difficulty]
        pass_rate = stats['passed'] / stats['total'] * 100 if stats['total'] > 0 else 0
        print(f"\n{difficulty}:")
        print(f"   Total: {stats['total']}")
        print(f"   Passed: {stats['passed']} ({pass_rate:.1f}%)")
        print(f"   Failed: {stats['failed']}")
        print(f"   Avg Score: {stats['avg_score']:.1f}/100")
    
    # Performance trends
    print(f"\n{'='*70}")
    print("📉 PERFORMANCE TRENDS (Last 30 days)")
    print(f"{'='*70}")
    
    cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
    
    cursor.execute("""
        SELECT task_id, AVG(score) as avg_score, AVG(duration_ms) as avg_duration,
               SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as pass_rate
        FROM performance_trends
        WHERE timestamp >= ?
        GROUP BY task_id
        ORDER BY pass_rate ASC, avg_score ASC
        LIMIT 10
    """, (cutoff_date,))
    
    worst_performers = cursor.fetchall()
    
    if worst_performers:
        print("\n⚠️  Worst Performing Tasks (Need Attention):")
        print(f"{'Task ID':<15} {'Avg Score':<12} {'Avg Duration':<15} {'Pass Rate':<12}")
        print("-" * 70)
        for task_id, avg_score, avg_duration, pass_rate in worst_performers:
            print(f"{task_id:<15} {avg_score:<12.1f} {avg_duration:<15.1f} {pass_rate:<12.1f}%")
    else:
        print("\n✅ No trend data available yet")
    
    conn.close()
    
    print(f"\n{'='*70}")


def print_regression_analysis(days: int = 7):
    """Detect and report regressions"""
    framework = TEST_SUITE_FRAMEWORK
    conn = sqlite3.connect(framework.db_path)
    cursor = conn.cursor()
    
    print("\n" + "="*70)
    print("🔍 REGRESSION ANALYSIS")
    print("="*70)
    
    # Compare recent runs with baseline
    cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
    
    # Get baseline (average from before cutoff)
    cursor.execute("""
        SELECT task_id, AVG(score) as baseline_score, AVG(duration_ms) as baseline_duration,
               SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as baseline_pass_rate
        FROM performance_trends
        WHERE timestamp < ?
        GROUP BY task_id
    """, (cutoff_date,))
    
    baseline = {row[0]: {'score': row[1], 'duration': row[2], 'pass_rate': row[3]} 
                for row in cursor.fetchall()}
    
    # Get recent performance
    cursor.execute("""
        SELECT task_id, AVG(score) as recent_score, AVG(duration_ms) as recent_duration,
               SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as recent_pass_rate
        FROM performance_trends
        WHERE timestamp >= ?
        GROUP BY task_id
    """, (cutoff_date,))
    
    recent = {row[0]: {'score': row[1], 'duration': row[2], 'pass_rate': row[3]} 
              for row in cursor.fetchall()}
    
    # Detect regressions
    regressions = []
    for task_id in recent:
        if task_id in baseline:
            recent_stats = recent[task_id]
            baseline_stats = baseline[task_id]
            
            score_drop = baseline_stats['score'] - recent_stats['score']
            pass_rate_drop = baseline_stats['pass_rate'] - recent_stats['pass_rate']
            duration_increase = recent_stats['duration'] - baseline_stats['duration']
            
            # Significant regression: >10% score drop or >20% pass rate drop
            if score_drop > 10 or pass_rate_drop > 20:
                regressions.append({
                    'task_id': task_id,
                    'score_drop': score_drop,
                    'pass_rate_drop': pass_rate_drop,
                    'duration_increase': duration_increase,
                    'baseline_score': baseline_stats['score'],
                    'recent_score': recent_stats['score']
                })
    
    if regressions:
        print(f"\n⚠️  Detected {len(regressions)} Regression(s):")
        print(f"{'Task ID':<15} {'Score Drop':<12} {'Pass Rate Drop':<15} {'Duration Increase':<18}")
        print("-" * 70)
        
        for reg in sorted(regressions, key=lambda x: x['score_drop'], reverse=True):
            print(f"{reg['task_id']:<15} {reg['score_drop']:<12.1f} {reg['pass_rate_drop']:<15.1f}% {reg['duration_increase']:<18.1f}ms")
            print(f"   Baseline: {reg['baseline_score']:.1f}/100 → Recent: {reg['recent_score']:.1f}/100")
    else:
        print("\n✅ No regressions detected!")
    
    conn.close()
    print(f"\n{'='*70}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="View test suite results")
    parser.add_argument(
        "--run-id",
        type=str,
        help="Specific run ID to view (default: latest)"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of days for trend analysis (default: 30)"
    )
    parser.add_argument(
        "--regressions",
        action="store_true",
        help="Show regression analysis"
    )
    
    args = parser.parse_args()
    
    if args.regressions:
        print_regression_analysis(days=args.days)
    else:
        print_test_results_dashboard(run_id=args.run_id, days=args.days)


if __name__ == "__main__":
    main()

