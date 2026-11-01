#!/usr/bin/env python3
"""
Test orchestrator directly without GUI
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.orchestrator import Orchestrator

def test_orchestrator_direct(task: str):
    """Test orchestrator directly without GUI"""
    print("=" * 60)
    print("🧪 Direct Orchestrator Test (No GUI)")
    print("=" * 60)
    print(f"\nTask: {task}\n")
    
    try:
        # Initialize orchestrator
        print("Initializing Orchestrator...")
        orchestrator = Orchestrator()
        print("✅ Orchestrator initialized\n")
        
        # Execute the task
        print("Executing task with build_with_validation_iterative...")
        print("-" * 60)
        result = orchestrator.build_with_validation_iterative(
            task=task,
            max_iterations=3
        )
        print("-" * 60)
        
        print("\n" + "=" * 60)
        print("✅ Result Summary:")
        print("=" * 60)
        print(f"Success: {result.get('success', False)}")
        print(f"Has code: {bool(result.get('code'))}")
        print(f"Code length: {len(result.get('code', ''))} characters")
        print(f"Has error: {bool(result.get('error'))}")
        if result.get('error'):
            print(f"Error: {result.get('error')}")
        
        # Check validation
        validation = result.get('validation', {})
        if validation:
            print("\nValidation Results:")
            syntax = validation.get('syntax_check', {})
            print(f"  Syntax: {'✓' if syntax.get('success') else '✗'}")
            if not syntax.get('success'):
                print(f"    Error: {syntax.get('error', 'Unknown')}")
            
            execution = validation.get('execution', {})
            if execution:
                print(f"  Execution: {'✓' if execution.get('success') else '✗'}")
                if not execution.get('success'):
                    print(f"    Error: {execution.get('error', 'Unknown')}")
            
            tests = validation.get('tests_run', {})
            if tests and tests.get('metadata'):
                test_meta = tests['metadata']
                passed = test_meta.get('passed', 0)
                total = test_meta.get('total', 0)
                print(f"  Tests: {passed}/{total} passed")
        
        # Check evaluation
        evaluation = result.get('evaluation')
        if evaluation:
            if hasattr(evaluation, 'score'):
                print(f"\nEvaluation Score: {evaluation.score}/100")
                print(f"  Passed tests: {evaluation.passed_tests}")
                print(f"  Total tests: {evaluation.total_tests}")
            elif isinstance(evaluation, dict):
                print(f"\nEvaluation Score: {evaluation.get('score', 0)}/100")
        
        # Show code preview
        code = result.get('code', '')
        if code:
            print("\n" + "=" * 60)
            print("📄 Generated Code Preview (first 500 chars):")
            print("=" * 60)
            print(code[:500])
            if len(code) > 500:
                print(f"\n... ({len(code) - 500} more characters)")
        
        return result
        
    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # Test with tic tac toe game
    task = "lets make a tic tac toe game"
    
    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])
    
    test_orchestrator_direct(task)

