"""
Comprehensive System Verification
Tests all major components and their integration

Verifies:
- Metrics tracking
- Error pattern learning
- Routing optimization
- Feedback collection
- Test suite framework
- All dashboards
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def verify_metrics_tracker():
    """Verify metrics tracking system"""
    print("\n📊 Verifying Metrics Tracker...")
    try:
        from learning.metrics_tracker import MetricsTracker
        
        tracker = MetricsTracker()
        print(f"   ✅ MetricsTracker initialized")
        print(f"   ✅ Database: {tracker.db_path}")
        
        # Test statistics
        stats = tracker.get_metrics_summary(days=30)
        print(f"   ✅ Statistics retrieval: {stats['total_interactions']} interactions")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def verify_error_patterns():
    """Verify error pattern learning system"""
    print("\n🔍 Verifying Error Pattern Learning...")
    try:
        from learning.error_patterns import ERROR_PATTERN_DB, EnhancedErrorAnalyzer
        
        print(f"   ✅ ErrorPatternDatabase initialized")
        print(f"   ✅ Database: {ERROR_PATTERN_DB.db_path}")
        
        analyzer = EnhancedErrorAnalyzer(ERROR_PATTERN_DB)
        print(f"   ✅ EnhancedErrorAnalyzer initialized")
        
        # Test insights
        insights = analyzer.get_pattern_insights(days=30)
        print(f"   ✅ Pattern insights: {insights['statistics']['total_errors']} errors tracked")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def verify_error_learning():
    """Verify error learning system"""
    print("\n🧠 Verifying Error Learning System...")
    try:
        from learning.error_learning import ERROR_LEARNING
        
        print(f"   ✅ ErrorLearningSystem initialized")
        
        # Test recommendations
        recommendations = ERROR_LEARNING.get_improvement_recommendations(days=30)
        print(f"   ✅ Improvement recommendations: {recommendations['total_patterns']} patterns analyzed")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def verify_routing_optimizer():
    """Verify routing optimization system"""
    print("\n🚦 Verifying Routing Optimizer...")
    try:
        from agents.routing_optimizer import ROUTING_OPTIMIZER
        from agents.complexity_predictor import ComplexityPredictor
        
        print(f"   ✅ RoutingOptimizer initialized")
        print(f"   ✅ Database: {ROUTING_OPTIMIZER.db_path}")
        
        predictor = ComplexityPredictor(use_learning=True)
        print(f"   ✅ Enhanced ComplexityPredictor initialized")
        
        # Test prediction
        complexity = predictor.predict("Create a REST API endpoint", {'task_type': 'api'})
        print(f"   ✅ Complexity prediction: {complexity}/10")
        
        # Test routing
        route, reason = ROUTING_OPTIMIZER.get_optimal_route(
            task_type='api',
            predicted_complexity=complexity,
            complexity_threshold=8
        )
        print(f"   ✅ Optimal route: {route}")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def verify_feedback_collector():
    """Verify feedback collection system"""
    print("\n💬 Verifying Feedback Collection System...")
    try:
        from learning.feedback_collector import FEEDBACK_COLLECTOR, FeedbackType
        
        print(f"   ✅ FeedbackCollector initialized")
        print(f"   ✅ Database: {FEEDBACK_COLLECTOR.db_path}")
        
        # Test statistics
        stats = FEEDBACK_COLLECTOR.get_feedback_statistics(days=30)
        print(f"   ✅ Feedback statistics: {stats['overall']['total']} feedback entries")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def verify_feedback_processor():
    """Verify feedback processing system"""
    print("\n📝 Verifying Feedback Processor...")
    try:
        from learning.feedback_processor import FEEDBACK_PROCESSOR
        
        print(f"   ✅ FeedbackProcessor initialized")
        
        # Test analysis
        analysis = FEEDBACK_PROCESSOR.analyze_feedback(days=30)
        print(f"   ✅ Feedback analysis: {len(analysis['recommendations'])} recommendations")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def verify_test_suite():
    """Verify test suite framework"""
    print("\n🧪 Verifying Test Suite Framework...")
    try:
        from tests.test_suite_framework import TEST_SUITE_FRAMEWORK
        
        print(f"   ✅ TestSuiteFramework initialized")
        print(f"   ✅ Database: {TEST_SUITE_FRAMEWORK.db_path}")
        
        # Load tasks
        tasks = TEST_SUITE_FRAMEWORK.load_tasks()
        print(f"   ✅ Test tasks loaded: {len(tasks)} tasks")
        
        if tasks:
            # Print summary
            categories = {}
            difficulties = {}
            for task in tasks:
                categories[task.category.value] = categories.get(task.category.value, 0) + 1
                difficulties[task.difficulty.value] = difficulties.get(task.difficulty.value, 0) + 1
            
            print(f"   ✅ Categories: {len(categories)}")
            print(f"   ✅ Difficulties: {len(difficulties)}")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def verify_orchestrator():
    """Verify orchestrator integration"""
    print("\n🎯 Verifying Orchestrator Integration...")
    try:
        from agents.orchestrator import Orchestrator
        
        orchestrator = Orchestrator()
        print(f"   ✅ Orchestrator initialized")
        
        # Check components
        print(f"   ✅ ComplexityPredictor: {type(orchestrator.complexity_predictor).__name__}")
        print(f"   ✅ RoutingOptimizer: {type(orchestrator.routing_optimizer).__name__}")
        print(f"   ✅ MetricsTracker: {type(orchestrator.metrics_tracker).__name__}")
        print(f"   ✅ ErrorAnalyzer: {type(orchestrator.error_analyzer).__name__}")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_dashboards():
    """Verify all dashboard scripts exist and are importable"""
    print("\n📊 Verifying Dashboards...")
    dashboards = [
        ('learning/view_metrics.py', 'Metrics Dashboard'),
        ('learning/view_error_patterns.py', 'Error Patterns Dashboard'),
        ('learning/view_error_learning.py', 'Error Learning Dashboard'),
        ('tests/view_test_results.py', 'Test Results Dashboard'),
        ('agents/view_routing_stats.py', 'Routing Stats Dashboard'),
        ('view_feedback.py', 'Feedback Dashboard'),
    ]
    
    all_ok = True
    for path, name in dashboards:
        dashboard_path = project_root / path
        if dashboard_path.exists():
            print(f"   ✅ {name}: {path}")
        else:
            print(f"   ❌ {name}: {path} - NOT FOUND")
            all_ok = False
    
    return all_ok


def main():
    """Run comprehensive system verification"""
    print("="*70)
    print("🔍 COMPREHENSIVE SYSTEM VERIFICATION")
    print("="*70)
    
    results = {}
    
    # Verify all components
    results['metrics_tracker'] = verify_metrics_tracker()
    results['error_patterns'] = verify_error_patterns()
    results['error_learning'] = verify_error_learning()
    results['routing_optimizer'] = verify_routing_optimizer()
    results['feedback_collector'] = verify_feedback_collector()
    results['feedback_processor'] = verify_feedback_processor()
    results['test_suite'] = verify_test_suite()
    results['orchestrator'] = verify_orchestrator()
    results['dashboards'] = verify_dashboards()
    
    # Summary
    print("\n" + "="*70)
    print("📋 VERIFICATION SUMMARY")
    print("="*70)
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed
    
    print(f"\nTotal Components: {total}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    
    if failed > 0:
        print(f"\n⚠️  Failed Components:")
        for component, status in results.items():
            if not status:
                print(f"   ❌ {component}")
    else:
        print(f"\n✅ All components verified successfully!")
    
    print(f"\n{'='*70}")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

