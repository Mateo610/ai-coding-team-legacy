"""
User Feedback Dashboard
Section 7.3: User Feedback

View feedback statistics, analysis, and improvement suggestions
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from learning.feedback_collector import FEEDBACK_COLLECTOR, FeedbackType
from learning.feedback_processor import FEEDBACK_PROCESSOR


def print_feedback_dashboard(days: int = 30):
    """Print formatted feedback dashboard"""
    stats = FEEDBACK_COLLECTOR.get_feedback_statistics(days=days)
    
    print("\n" + "="*70)
    print("💬 USER FEEDBACK DASHBOARD")
    print("="*70)
    print(f"\nPeriod: Last {days} days")
    
    if stats['overall']['total'] == 0:
        print("\n⚠️  No feedback collected yet")
        print("\nTo submit feedback:")
        print("  from learning.feedback_collector import FEEDBACK_COLLECTOR, FeedbackType")
        print("  FEEDBACK_COLLECTOR.submit_feedback(...)")
        return
    
    # Overall statistics
    overall = stats['overall']
    print(f"\n{'='*70}")
    print("📊 OVERALL STATISTICS")
    print(f"{'='*70}")
    print(f"\nTotal Feedback: {overall['total']}")
    print(f"Average Rating: {overall['avg_rating']:.1f}/5.0")
    print(f"Satisfaction Rate: {overall['satisfaction_rate']:.1f}%")
    
    # Rating distribution
    if stats['rating_distribution']:
        print(f"\n{'='*70}")
        print("⭐ RATING DISTRIBUTION")
        print(f"{'='*70}")
        print(f"\n{'Rating':<10} {'Count':<10} {'Bar'}")
        print("-" * 70)
        
        for rating in sorted(stats['rating_distribution'].keys()):
            count = stats['rating_distribution'][rating]
            bar = "█" * (count // 2)  # Simple bar chart
            print(f"{rating:<10} {count:<10} {bar}")
    
    # By feedback type
    if stats['by_feedback_type']:
        print(f"\n{'='*70}")
        print("📝 FEEDBACK BY TYPE")
        print(f"{'='*70}")
        print(f"\n{'Type':<20} {'Count':<10} {'Avg Rating':<12}")
        print("-" * 70)
        
        for feedback_type, data in sorted(stats['by_feedback_type'].items()):
            avg_rating = data['avg_rating'] if data['avg_rating'] else 0.0
            print(f"{feedback_type:<20} {data['count']:<10} {avg_rating:<12.1f}")
    
    # By task type
    if stats['by_task_type']:
        print(f"\n{'='*70}")
        print("📋 FEEDBACK BY TASK TYPE")
        print(f"{'='*70}")
        print(f"\n{'Task Type':<20} {'Count':<10} {'Avg Rating':<12}")
        print("-" * 70)
        
        for task_type, data in sorted(stats['by_task_type'].items()):
            avg_rating = data['avg_rating'] if data['avg_rating'] else 0.0
            print(f"{task_type:<20} {data['count']:<10} {avg_rating:<12.1f}")
    
    # Analysis and recommendations
    print(f"\n{'='*70}")
    print("🔍 ANALYSIS & RECOMMENDATIONS")
    print(f"{'='*70}")
    
    analysis = FEEDBACK_PROCESSOR.analyze_feedback(days=days)
    
    if analysis['improvement_areas']:
        print("\n⚠️  IMPROVEMENT AREAS:")
        for area in analysis['improvement_areas']:
            print(f"\n   {area['task_type'].upper()} (Priority: {area['priority']})")
            print(f"      Low Ratings: {area['count']}")
            print(f"      Avg Rating: {area['avg_rating']:.1f}/5.0")
    
    if analysis['recommendations']:
        print("\n💡 RECOMMENDATIONS:")
        for i, rec in enumerate(analysis['recommendations'], 1):
            print(f"\n   {i}. {rec}")
    
    if analysis['common_suggestions']:
        print("\n📝 COMMON SUGGESTIONS:")
        for suggestion_data in analysis['common_suggestions'][:5]:
            print(f"   • {suggestion_data['suggestion']} (mentioned {suggestion_data['count']} times)")
    
    print(f"\n{'='*70}")
    
    # Generate improvement report
    report = FEEDBACK_PROCESSOR.generate_improvement_report(days=days)
    print("\n" + report)


def submit_sample_feedback():
    """Submit sample feedback for testing"""
    from learning.feedback_collector import FEEDBACK_COLLECTOR, FeedbackType
    
    # Sample ratings
    FEEDBACK_COLLECTOR.submit_feedback(
        task="Create a REST API endpoint",
        task_type="api",
        feedback_type=FeedbackType.RATING,
        rating=4,
        comment="Good code quality, but missing error handling"
    )
    
    # Sample correction
    FEEDBACK_COLLECTOR.submit_feedback(
        task="Create a user model",
        task_type="crud",
        feedback_type=FeedbackType.CORRECTION,
        rating=3,
        corrections={
            "class User:\n    def __init__(self, name):\n        self.name = name": 
            "class User:\n    def __init__(self, name: str, email: str):\n        self.name = name\n        self.email = email"
        }
    )
    
    # Sample suggestion
    FEEDBACK_COLLECTOR.submit_feedback(
        task="Implement authentication",
        task_type="api",
        feedback_type=FeedbackType.SUGGESTION,
        rating=4,
        suggestions=["Add rate limiting", "Include refresh token support"]
    )
    
    print("✅ Sample feedback submitted")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="View user feedback dashboard")
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of days to analyze (default: 30)"
    )
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Submit sample feedback for testing"
    )
    
    args = parser.parse_args()
    
    if args.sample:
        submit_sample_feedback()
    else:
        print_feedback_dashboard(days=args.days)


if __name__ == "__main__":
    main()

