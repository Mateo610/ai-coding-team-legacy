"""
Error Pattern Dashboard - View and analyze error patterns
Section 7.1: Error Analysis Enhancement
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from learning.error_patterns import ERROR_PATTERN_DB, EnhancedErrorAnalyzer


def print_error_patterns_dashboard(days: int = 30):
    """Print formatted error patterns dashboard"""
    analyzer = EnhancedErrorAnalyzer(ERROR_PATTERN_DB)
    insights = analyzer.get_pattern_insights(days=days)
    
    stats = insights['statistics']
    patterns = insights['top_patterns']
    recommendations = insights['recommendations']
    
    print("\n" + "="*70)
    print("🔍 ERROR PATTERNS DASHBOARD")
    print("="*70)
    print(f"\nPeriod: Last {days} days")
    print(f"Total Errors: {stats['total_errors']}")
    
    if stats['total_errors'] == 0:
        print("\n✅ No errors recorded yet. System performing well!")
        return
    
    # Error Statistics
    print("\n" + "-"*70)
    print("📊 ERROR STATISTICS")
    print("-"*70)
    
    print(f"\nTotal Errors: {stats['total_errors']}")
    print(f"Fix Success Rate: {stats['fix_success_rate']:.1f}%")
    
    # Errors by Type
    if stats['by_type']:
        print(f"\n📋 Errors by Type:")
        for error_type, count in sorted(stats['by_type'].items(), key=lambda x: x[1], reverse=True):
            percentage = (count / stats['total_errors'] * 100) if stats['total_errors'] > 0 else 0
            print(f"   {error_type:20s}: {count:3d} ({percentage:5.1f}%)")
    
    # Errors by Task Type
    if stats['by_task_type']:
        print(f"\n📋 Errors by Task Type:")
        for task_type, count in sorted(stats['by_task_type'].items(), key=lambda x: x[1], reverse=True):
            percentage = (count / stats['total_errors'] * 100) if stats['total_errors'] > 0 else 0
            print(f"   {task_type:20s}: {count:3d} ({percentage:5.1f}%)")
    
    # Top Patterns
    if patterns:
        print("\n" + "-"*70)
        print("🔁 TOP ERROR PATTERNS (Frequency ≥3)")
        print("-"*70)
        
        for i, pattern in enumerate(patterns, 1):
            print(f"\n   {i}. {pattern['error_type']} ({pattern['frequency']}x)")
            print(f"      Pattern: {pattern['pattern']}")
            print(f"      Task Type: {pattern['task_type']}")
    
    # Recommendations
    print("\n" + "-"*70)
    print("💡 RECOMMENDATIONS")
    print("-"*70)
    
    for i, rec in enumerate(recommendations, 1):
        print(f"\n   {i}. {rec}")
    
    print("\n" + "="*70)


def print_error_analysis(validation_results: Dict[str, Any]):
    """Print detailed error analysis for validation results"""
    analyzer = EnhancedErrorAnalyzer(ERROR_PATTERN_DB)
    analysis = analyzer.analyze(validation_results)
    
    if not analysis['has_errors']:
        print("✅ No errors detected!")
        return
    
    print("\n" + "="*70)
    print("🔍 ERROR ANALYSIS")
    print("="*70)
    
    print(f"\nError Type: {analysis['error_type']}")
    print(f"Summary: {analysis['error_summary']}")
    
    if analysis['specific_errors']:
        print(f"\nSpecific Errors ({len(analysis['specific_errors'])}):")
        for i, error in enumerate(analysis['specific_errors'], 1):
            print(f"   {i}. {error[:200]}")
    
    if analysis['code_locations']:
        print(f"\nCode Locations:")
        for loc in analysis['code_locations']:
            print(f"   • {loc['file']}, line {loc.get('line', '?')}")
    
    if analysis['fix_suggestions']:
        print(f"\nFix Suggestions:")
        print(analysis['fix_suggestions'])
    
    print("\n" + "="*70)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="View error patterns dashboard")
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of days to analyze (default: 30)"
    )
    
    args = parser.parse_args()
    print_error_patterns_dashboard(days=args.days)


if __name__ == "__main__":
    from typing import Dict, Any
    main()

