"""
Metrics Dashboard - View and analyze system metrics
Section 7.2: Success Metrics Implementation
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from learning.metrics_tracker import MetricsTracker, METRICS_TRACKER


def print_metrics_dashboard(days: int = 7):
    """Print a formatted metrics dashboard"""
    tracker = METRICS_TRACKER
    summary = tracker.get_metrics_summary(days=days)
    goals = tracker.check_goals()
    
    print("\n" + "="*70)
    print("📊 METRICS DASHBOARD")
    print("="*70)
    print(f"\nPeriod: Last {days} days")
    print(f"Total Interactions: {summary['total_interactions']}")
    
    if summary['total_interactions'] == 0:
        print("\n⚠️  No interactions recorded yet. Run some tasks to see metrics.")
        return
    
    print("\n" + "-"*70)
    print("🎯 KEY METRICS")
    print("-"*70)
    
    # Code Generation Accuracy
    accuracy = summary['code_generation_accuracy']
    accuracy_status = "✅" if accuracy >= 90 else "⚠️" if accuracy >= 70 else "❌"
    print(f"{accuracy_status} Code Generation Accuracy: {accuracy:.1f}% (Target: ≥90%)")
    
    # Test Pass Rate
    test_pass = summary['test_pass_rate']
    test_status = "✅" if test_pass >= 85 else "⚠️" if test_pass >= 60 else "❌"
    print(f"{test_status} Test Pass Rate: {test_pass:.1f}% (Target: ≥85%)")
    
    # First Gen Test Pass Rate
    first_gen = summary['first_gen_test_pass_rate']
    first_gen_status = "✅" if first_gen >= 85 else "⚠️" if first_gen >= 60 else "❌"
    print(f"{first_gen_status} First Gen Test Pass Rate: {first_gen:.1f}% (Target: ≥85%)")
    
    # Error Rate
    error_rate = summary['error_rate']
    error_status = "✅" if error_rate <= 5 else "⚠️" if error_rate <= 10 else "❌"
    print(f"{error_status} Error Rate: {error_rate:.1f}% (Target: ≤5%)")
    
    # Success Rate
    success_rate = summary['success_rate']
    success_status = "✅" if success_rate >= 80 else "⚠️" if success_rate >= 60 else "❌"
    print(f"{success_status} Success Rate: {success_rate:.1f}%")
    
    # Performance
    print(f"\n⚡ Performance:")
    print(f"   Avg Response Time: {summary['avg_response_time_ms']:.0f}ms")
    print(f"   Avg Tokens Used: {summary['avg_tokens_used']:.0f}")
    
    # Goals Progress
    print("\n" + "-"*70)
    print("🎯 GOALS PROGRESS")
    print("-"*70)
    
    overall_progress = goals['overall_progress']
    print(f"Overall Progress: {overall_progress:.1f}%")
    print()
    
    for goal_name, goal_data in goals['goals'].items():
        target = goal_data['target']
        current = goal_data['current']
        met = goal_data['met']
        gap = goal_data['gap']
        
        status = "✅ MET" if met else f"⚠️  {gap:.1f}% gap"
        print(f"   {status} - {goal_name.replace('_', ' ').title()}: {current:.1f}% (Target: {target}%)")
    
    # By Task Type
    if summary['by_task_type']:
        print("\n" + "-"*70)
        print("📋 BY TASK TYPE")
        print("-"*70)
        
        for task_type, metrics in sorted(summary['by_task_type'].items(), key=lambda x: x[1]['count'], reverse=True):
            print(f"\n   {task_type.upper()}:")
            print(f"      Count: {metrics['count']}")
            print(f"      Accuracy: {metrics['accuracy']:.1f}%")
            print(f"      Test Pass Rate: {metrics['test_pass_rate']:.1f}%")
            print(f"      Error Rate: {metrics['error_rate']:.1f}%")
    
    # By Route
    if summary['by_route']:
        print("\n" + "-"*70)
        print("🛣️  BY ROUTE")
        print("-"*70)
        
        for route, metrics in sorted(summary['by_route'].items(), key=lambda x: x[1]['count'], reverse=True):
            print(f"\n   {route.upper()}:")
            print(f"      Count: {metrics['count']}")
            print(f"      Accuracy: {metrics['accuracy']:.1f}%")
            print(f"      Test Pass Rate: {metrics['test_pass_rate']:.1f}%")
            print(f"      Avg Time: {metrics['avg_time_ms']:.0f}ms")
    
    print("\n" + "="*70)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="View system metrics dashboard")
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days to analyze (default: 7)"
    )
    
    args = parser.parse_args()
    print_metrics_dashboard(days=args.days)


if __name__ == "__main__":
    main()

