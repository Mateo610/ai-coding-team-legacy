#!/usr/bin/env python3
"""
Basic test to verify orchestrator works and is connected correctly
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_orchestrator_initialization():
    """Test that orchestrator initializes correctly"""
    print("=" * 60)
    print("Test 1: Orchestrator Initialization")
    print("=" * 60)
    
    try:
        from agents.orchestrator import Orchestrator
        orchestrator = Orchestrator()
        print("✅ Orchestrator initialized successfully")
        
        # Check components
        assert orchestrator.complexity_predictor is not None, "Complexity predictor missing"
        print("✅ Complexity predictor available")
        
        assert orchestrator.implementation_agent is not None, "Implementation agent missing"
        print("✅ Implementation agent available")
        
        # Check if validation is available (via TestGeneratorAgent)
        assert hasattr(orchestrator, 'test_generator'), "Test generator missing"
        print("✅ Test generator available")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_simple_task():
    """Test a very simple task to see if orchestrator executes"""
    print("\n" + "=" * 60)
    print("Test 2: Simple Task Execution")
    print("=" * 60)
    
    try:
        from agents.orchestrator import Orchestrator
        orchestrator = Orchestrator()
        
        # Very simple task - create a Python file
        task = "Create a file called test_output.py with print('Hello World')"
        print(f"Task: {task}")
        print("Executing... (this may take a moment)")
        
        result = orchestrator.build_with_validation_iterative(
            task=task,
            max_iterations=2  # Limit iterations for testing
        )
        
        print(f"\n✅ Task completed!")
        print(f"Success: {result.get('success', False)}")
        print(f"Code length: {len(result.get('code', ''))}")
        print(f"Interaction ID: {result.get('interaction_id', 'N/A')}")
        
        if result.get('evaluation'):
            print(f"Score: {result['evaluation'].score}/100")
        
        return True
    except Exception as e:
        print(f"❌ Error during task execution: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_flask_task():
    """Test Flask app creation task"""
    print("\n" + "=" * 60)
    print("Test 3: Flask App Task")
    print("=" * 60)
    
    try:
        from agents.orchestrator import Orchestrator
        orchestrator = Orchestrator()
        
        task = "Create a Flask app that connects to localhost displaying hello world"
        print(f"Task: {task}")
        print("Executing... (this may take a moment)")
        
        result = orchestrator.build_with_validation_iterative(
            task=task,
            max_iterations=2
        )
        
        print(f"\n✅ Task completed!")
        print(f"Success: {result.get('success', False)}")
        print(f"Code length: {len(result.get('code', ''))}")
        
        if result.get('code'):
            print("\nFirst 500 chars of generated code:")
            print(result['code'][:500])
        
        if result.get('evaluation'):
            print(f"\nScore: {result['evaluation'].score}/100")
            print(f"Errors: {result['evaluation'].errors}")
        
        return True
    except Exception as e:
        print(f"❌ Error during Flask task: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_tui_worker_simulation():
    """Simulate what the TUI worker does"""
    print("\n" + "=" * 60)
    print("Test 4: TUI Worker Simulation")
    print("=" * 60)
    
    try:
        from agents.orchestrator import Orchestrator
        orchestrator = Orchestrator()
        
        task = "print('Hello from TUI simulation')"
        print(f"Task: {task}")
        print("Simulating TUI worker execution...")
        
        # This is what the TUI does
        result = orchestrator.build_with_validation_iterative(
            task=task,
            max_iterations=2
        )
        
        print(f"\n✅ Worker simulation completed!")
        print(f"Result keys: {list(result.keys())}")
        print(f"Success: {result.get('success', False)}")
        
        return result
    except Exception as e:
        print(f"❌ Error in worker simulation: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    print("\n🧪 Running Orchestrator Tests\n")
    
    results = []
    
    # Test 1: Initialization
    results.append(("Initialization", test_orchestrator_initialization()))
    
    # Test 2: Simple task
    results.append(("Simple Task", test_simple_task()))
    
    # Test 3: Flask task (same as user tried)
    results.append(("Flask Task", test_flask_task()))
    
    # Test 4: TUI simulation
    worker_result = test_tui_worker_simulation()
    results.append(("TUI Worker Simulation", worker_result is not None))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(r[1] for r in results)
    print("\n" + ("✅ All tests passed!" if all_passed else "❌ Some tests failed"))
    sys.exit(0 if all_passed else 1)

