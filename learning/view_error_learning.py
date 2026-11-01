"""
Error Learning Dashboard - View error-based improvement recommendations
Section 7.1: Error Analysis Enhancement
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from learning.error_patterns import ERROR_PATTERN_DB, EnhancedErrorAnalyzer
from learning.error_learning import ErrorLearningSystem, ERROR_LEARNING


def print_error_learning_dashboard(days: int = 30):
    """Print formatted error learning dashboard"""
    analyzer = EnhancedErrorAnalyzer(ERROR_PATTERN_DB)
    learning_system = ErrorLearningSystem(ERROR_PATTERN_DB)
    
    # Get insights
    insights = analyzer.get_pattern_insights(days=days)
    improvements = learning_system.get_improvement_recommendations(days=days)
    
    print("\n" + "="*70)
    print("🧠 ERROR LEARNING DASHBOARD")
    print("="*70)
    print(f"\nPeriod: Last {days} days")
    
    stats = insights['statistics']
    if stats['total_errors'] == 0:
        print("\n✅ No errors recorded yet. System performing well!")
        return
    
    print(f"Total Errors: {stats['total_errors']}")
    print(f"Total Patterns: {improvements['total_patterns']}")
    
    # Recommendations
    print("\n" + "-"*70)
    print("💡 IMPROVEMENT RECOMMENDATIONS")
    print("-"*70)
    
    recs = improvements['recommendations']
    
    # Priority recommendations
    if recs['priority']:
        print("\n🔥 HIGH PRIORITY:")
        for priority in recs['priority']:
            print(f"\n   {priority['message']}")
            for pattern in priority['patterns'][:3]:
                print(f"      • {pattern['error_type']} ({pattern['frequency']}x) - {pattern['task_type']}")
    
    # Prompt updates needed
    if recs['prompt_updates_needed']:
        print("\n📝 PROMPT UPDATES NEEDED:")
        grouped_by_task = {}
        for update in recs['prompt_updates_needed']:
            task_type = update['task_type']
            if task_type not in grouped_by_task:
                grouped_by_task[task_type] = []
            grouped_by_task[task_type].append(update)
        
        for task_type, updates in grouped_by_task.items():
            print(f"\n   Task Type: {task_type}")
            for update in updates[:3]:
                print(f"      • {update['error_type']} ({update['frequency']}x)")
                print(f"        Pattern: {update['pattern'][:80]}...")
                print(f"        Suggestion: {update['suggestion']}")
    
    # Examples needed
    if recs['examples_needed']:
        print("\n📚 EXAMPLES NEEDED:")
        grouped_by_task = {}
        for example in recs['examples_needed']:
            task_type = example['task_type']
            if task_type not in grouped_by_task:
                grouped_by_task[task_type] = []
            grouped_by_task[task_type].append(example)
        
        for task_type, examples in grouped_by_task.items():
            print(f"\n   Task Type: {task_type}")
            for example in examples[:3]:
                print(f"      • {example['error_type']} ({example['frequency']}x)")
                print(f"        Example type: Error prevention example")
    
    # General recommendations
    if insights['recommendations']:
        print("\n" + "-"*70)
        print("📊 ANALYSIS RECOMMENDATIONS")
        print("-"*70)
        
        for i, rec in enumerate(insights['recommendations'], 1):
            print(f"\n   {i}. {rec}")
    
    print("\n" + "="*70)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="View error learning dashboard")
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of days to analyze (default: 30)"
    )
    
    args = parser.parse_args()
    print_error_learning_dashboard(days=args.days)


if __name__ == "__main__":
    main()

