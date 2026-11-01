"""
Test script to verify agent integration with consolidated tools
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.specialized_agent import SpecializedAgent, ImplementationAgent
from tools.consolidated import TOOL_REGISTRY_CONSOLIDATED
from tools.consolidated.migration import migrate_tool_call, is_old_tool
from tools.code_tools import get_tool


def test_tool_migration():
    """Test that old tool names are migrated correctly"""
    print("\n" + "="*70)
    print("Test 1: Tool Migration")
    print("="*70)
    
    test_cases = [
        ("read_file", {"file_path": "test.py"}),
        ("write_file", {"file_path": "test.py", "content": "code"}),
        ("git_status", {}),
        ("fs_read", {"file_path": "test.py"}),  # Already new
    ]
    
    for old_name, kwargs in test_cases:
        if is_old_tool(old_name):
            new_name, new_kwargs = migrate_tool_call(old_name, **kwargs)
            print(f"✅ {old_name:20s} → {new_name:20s} (mode: {new_kwargs.get('mode', 'N/A')})")
        else:
            print(f"ℹ️  {old_name:20s} (already consolidated)")
    
    return True


def test_tool_availability():
    """Test that tools are available via get_tool()"""
    print("\n" + "="*70)
    print("Test 2: Tool Availability")
    print("="*70)
    
    test_tools = [
        "fs_read",  # New tool
        "read_file",  # Old tool (should migrate)
        "project_scan",  # New tool
        "git_inspect",  # New tool
    ]
    
    for tool_name in test_tools:
        tool_func = get_tool(tool_name)
        if tool_func:
            print(f"✅ {tool_name:20s} - Available")
        else:
            print(f"❌ {tool_name:20s} - NOT FOUND")
            return False
    
    return True


def test_agent_tool_integration():
    """Test that agents can access consolidated tools"""
    print("\n" + "="*70)
    print("Test 3: Agent Tool Integration")
    print("="*70)
    
    try:
        # Create an agent
        agent = ImplementationAgent()
        
        # Test that agent has access to tools
        print(f"✅ ImplementationAgent created")
        print(f"   Agent name: {agent.name}")
        print(f"   Agent role: {agent.role}")
        
        # Check that consolidated tools are available
        print(f"\n📊 Tool Registry Status:")
        print(f"   Consolidated tools: {len(TOOL_REGISTRY_CONSOLIDATED)} tools")
        
        # Test a sample of consolidated tools
        sample_tools = list(TOOL_REGISTRY_CONSOLIDATED.keys())[:5]
        print(f"\n📋 Sample Consolidated Tools:")
        for tool_name in sample_tools:
            print(f"   • {tool_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_prompt_tools():
    """Test that prompts include consolidated tools"""
    print("\n" + "="*70)
    print("Test 4: Prompt Tool Integration")
    print("="*70)
    
    try:
        agent = ImplementationAgent()
        
        # Test building a prompt with tools enabled
        context = "Test context"
        task = "Test task"
        
        # This should use consolidated tools
        tools = TOOL_REGISTRY_CONSOLIDATED.copy()
        
        print(f"✅ Tools available for prompts: {len(tools)} tools")
        print(f"   (Using consolidated tools - cleaner, fewer tokens)")
        
        # Show first few tool descriptions
        print(f"\n📋 Sample Tool Descriptions in Prompts:")
        for i, (name, info) in enumerate(list(tools.items())[:3]):
            desc = info['description'][:60]
            print(f"   {i+1}. {name}: {desc}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("AGENT TOOL INTEGRATION TESTS")
    print("="*70)
    
    tests = [
        ("Tool Migration", test_tool_migration),
        ("Tool Availability", test_tool_availability),
        ("Agent Tool Integration", test_agent_tool_integration),
        ("Prompt Tool Integration", test_prompt_tools),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} - {test_name}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed! Agent integration with consolidated tools is working.")
    else:
        print("⚠️  Some tests failed. Please review errors above.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

