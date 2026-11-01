#!/usr/bin/env python3
"""
Direct model test - bypass GUI to test model output
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.specialized_agent import ImplementationAgent
from agents.config_manager import CONFIG_MANAGER

def test_model_direct(task: str):
    """Test model directly without GUI"""
    print("=" * 60)
    print("🧪 Direct Model Test (No GUI)")
    print("=" * 60)
    print(f"\nTask: {task}\n")
    
    try:
        # Initialize the implementation agent
        print("Initializing ImplementationAgent...")
        agent = ImplementationAgent()
        print(f"   Model: {agent.model}")
        print(f"   Base URL: {agent.base_url}")
        print()
        
        # Execute the task
        print("Executing task...")
        result = agent.execute(
            task=task,
            context="",
            use_tools=False,  # Disable tools for simpler test
            task_type="general"
        )
        
        print("\n" + "=" * 60)
        print("✅ Model Response:")
        print("=" * 60)
        output = result.get("output", "")
        print(output)
        print("=" * 60)
        
        # Check if output looks good
        if len(output) > 100:
            print(f"\n✓ Output length: {len(output)} characters")
        else:
            print(f"\n⚠️  Output seems short: {len(output)} characters")
        
        # Check for code blocks
        if "```python" in output or "```" in output:
            print("✓ Contains code blocks")
        else:
            print("⚠️  No code blocks detected")
        
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
    
    test_model_direct(task)

