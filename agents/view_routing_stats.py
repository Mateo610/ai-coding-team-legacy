"""
View routing statistics and optimization insights
Section 6: Routing & Model Selection Enhancement

Dashboard for viewing routing decisions, performance, and learned preferences
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.routing_optimizer import ROUTING_OPTIMIZER


def print_routing_dashboard(days: int = 30):
    """Print formatted routing statistics dashboard"""
    stats = ROUTING_OPTIMIZER.get_routing_stats(days=days)
    
    print("\n" + "="*70)
    print("🚦 ROUTING OPTIMIZATION DASHBOARD")
    print("="*70)
    print(f"\nPeriod: Last {days} days")
    
    # Overall statistics
    print(f"\n{'='*70}")
    print("📊 OVERALL ROUTING STATISTICS")
    print(f"{'='*70}")
    
    overall = stats['overall']
    if not overall:
        print("\n⚠️  No routing data available yet")
        return
    
    print(f"\n{'Route':<12} {'Count':<10} {'Avg Score':<12} {'Avg Duration':<15} {'Success Rate':<15}")
    print("-" * 70)
    
    for route in ['local', 'claude']:
        if route in overall:
            data = overall[route]
            print(f"{route:<12} {data['count']:<10} {data['avg_score']:<12.1f} {data['avg_duration']:<15.1f} {data['success_rate']:<15.1f}%")
    
    # Task type specific statistics
    print(f"\n{'='*70}")
    print("📈 ROUTING BY TASK TYPE")
    print(f"{'='*70}")
    
    by_task_type = stats['by_task_type']
    if by_task_type:
        for task_type in sorted(by_task_type.keys()):
            print(f"\n{task_type.upper()}:")
            task_data = by_task_type[task_type]
            
            for route in ['local', 'claude']:
                if route in task_data and task_data[route]:
                    route_data = task_data[route]
                    print(f"   {route}:")
                    print(f"      Count: {route_data['count']}")
                    print(f"      Avg Score: {route_data['avg_score']:.1f}/100")
                    print(f"      Avg Duration: {route_data['avg_duration']:.1f}ms")
    else:
        print("\n⚠️  No task type specific data available yet")
    
    # Learned preferences
    print(f"\n{'='*70}")
    print("🧠 LEARNED ROUTING PREFERENCES")
    print(f"{'='*70}")
    
    # Load preferences
    ROUTING_OPTIMIZER._load_routing_preferences()
    prefs = ROUTING_OPTIMIZER._task_type_routing_prefs
    
    if prefs:
        print(f"\n{'Task Type':<20} {'Preferred Route':<15} {'Avg Score':<12} {'Sample Count':<15}")
        print("-" * 70)
        
        for task_type, pref_data in sorted(prefs.items()):
            print(f"{task_type:<20} {pref_data['preferred_route']:<15} {pref_data['avg_success_score']:<12.1f} {pref_data['sample_count']:<15}")
    else:
        print("\n⚠️  No learned preferences yet (need at least 10 samples per task type)")
    
    # Prediction accuracy
    print(f"\n{'='*70}")
    print("🎯 COMPLEXITY PREDICTION ACCURACY")
    print(f"{'='*70}")
    
    avg_error = stats['avg_prediction_error']
    if avg_error > 0:
        print(f"\nAverage Prediction Error: {avg_error:.2f} points")
        if avg_error < 1.0:
            print("✅ Excellent prediction accuracy!")
        elif avg_error < 2.0:
            print("✅ Good prediction accuracy")
        elif avg_error < 3.0:
            print("⚠️  Moderate prediction accuracy - could be improved")
        else:
            print("❌ Poor prediction accuracy - needs improvement")
    else:
        print("\n⚠️  No prediction accuracy data available yet")
    
    # Recommendations
    print(f"\n{'='*70}")
    print("💡 RECOMMENDATIONS")
    print(f"{'='*70}")
    
    recommendations = []
    
    # Check for route performance differences
    if 'local' in overall and 'claude' in overall:
        local_score = overall['local']['avg_score']
        claude_score = overall['claude']['avg_score']
        score_diff = claude_score - local_score
        
        if score_diff > 10:
            recommendations.append(f"Claude performs significantly better (+{score_diff:.1f} points) - consider lowering threshold")
        elif score_diff < -10:
            recommendations.append(f"Local performs significantly better ({score_diff:.1f} points) - consider raising threshold")
    
    # Check for task type preferences
    if prefs:
        for task_type, pref_data in prefs.items():
            if pref_data['sample_count'] >= 20:  # Reliable preference
                recommendations.append(
                    f"Task type '{task_type}' prefers {pref_data['preferred_route']} "
                    f"(score: {pref_data['avg_success_score']:.1f} from {pref_data['sample_count']} samples)"
                )
    
    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            print(f"\n{i}. {rec}")
    else:
        print("\n✅ No specific recommendations at this time")
    
    print(f"\n{'='*70}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="View routing optimization statistics")
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of days to analyze (default: 30)"
    )
    
    args = parser.parse_args()
    print_routing_dashboard(days=args.days)


if __name__ == "__main__":
    main()

