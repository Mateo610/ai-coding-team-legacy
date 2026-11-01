"""
Test script to evaluate Agent Specialization Enhancement improvements
"""
import sys
from pathlib import Path
from agents.orchestrator import Orchestrator
from agents.specialized_agent import ImplementationAgent, TestGeneratorAgent
from agents.error_analyzer import ErrorAnalyzer
from agents.context_manager import ContextManager
import time

def test_task_type_detection():
    """Test task type detection improvements"""
    print("=" * 70)
    print("🧪 Testing Task Type Detection")
    print("=" * 70)
    
    cm = ContextManager()
    
    test_cases = [
        ("Create a Flask REST API endpoint for user authentication", "api"),
        ("Create SQLAlchemy models for a blog post", "database"),
        ("Create a function to add two numbers", "algorithm"),
        ("Write tests for the user model", "test"),
        ("Create a user in the database", "crud"),
    ]
    
    print("\n1. Task Type Detection:")
    for task, expected in test_cases:
        detected = cm.detect_task_type(task)
        status = "✅" if detected == expected else "❌"
        print(f"   {status} Task: \"{task[:50]}...\"")
        print(f"      Detected: {detected} (Expected: {expected})")
    
    print("\n" + "=" * 70 + "\n")


def test_skill_selection():
    """Test dynamic skill selection"""
    print("=" * 70)
    print("🧪 Testing Skill Selection")
    print("=" * 70)
    
    from agents.skill_manager import SKILL_MANAGER
    
    test_cases = [
        ("Create a Flask REST API endpoint", "api"),
        ("Create SQLAlchemy models", "database"),
        ("Process data with pandas", "algorithm"),
    ]
    
    print("\n2. Skill Selection:")
    for task, task_type in test_cases:
        skill_names, tokens = SKILL_MANAGER.get_relevant_skills(
            task=task,
            task_type=task_type,
            max_tokens=8000
        )
        print(f"\n   Task: \"{task}\"")
        print(f"   ✅ Selected {len(skill_names)} skills: {skill_names[:5]}")
        print(f"   ✅ Total tokens: {tokens}")
        
        # Check for framework/library skills
        if "flask" in task.lower():
            print(f"   ✅ Flask skill included: {'flask' in skill_names}")
        elif "sqlalchemy" in task.lower():
            print(f"   ✅ SQLAlchemy skill included: {'sqlalchemy' in skill_names}")
        elif "pandas" in task.lower():
            print(f"   ✅ Pandas skill included: {'pandas' in skill_names}")
    
    print("\n" + "=" * 70 + "\n")


def test_implementation_agent_prompt():
    """Test ImplementationAgent prompt quality"""
    print("=" * 70)
    print("🧪 Testing ImplementationAgent Prompt Quality")
    print("=" * 70)
    
    agent = ImplementationAgent()
    
    test_tasks = [
        ("Create a function to add two numbers", "algorithm"),
        ("Create a Flask REST API endpoint for user authentication", "api"),
    ]
    
    print("\n3. ImplementationAgent Prompts:")
    for task, task_type in test_tasks:
        # Simulate skill loading
        task_type_detected = agent.prompt_builder.context_manager.detect_task_type(task)
        print(f"\n   Task: \"{task}\"")
        print(f"   Detected type: {task_type_detected}")
        
        # Get relevant skills
        skill_names, _ = agent.skill_manager.get_relevant_skills(
            task=task,
            task_type=task_type_detected,
            max_tokens=8000
        )
        print(f"   Skills selected: {len(skill_names)} skills")
        
        # Build prompt
        try:
            context = f"Task: {task}\nType: {task_type_detected}"
            prompt = agent.prompt_builder.build_implementation_prompt(
                task=task,
                context=context,
                task_type=task_type_detected,
                agent_skills=agent.skill
            )
            
            # Check for key elements
            checks = [
                ("production-ready", "production-ready"),
                ("type hints", "type hints"),
                ("docstrings", "docstrings"),
                ("error handling", "error handling"),
                ("QUALITY CHECKLIST", "quality checklist"),
                ("OUTPUT REQUIREMENTS", "output requirements"),
            ]
            
            print(f"   ✅ Prompt built ({len(prompt)} chars)")
            print(f"   Key elements:")
            for check_name, check_text in checks:
                found = check_text.lower() in prompt.lower()
                status = "✅" if found else "❌"
                print(f"      {status} {check_name}")
        
        except Exception as e:
            print(f"   ❌ Error building prompt: {e}")
    
    print("\n" + "=" * 70 + "\n")


def test_test_generator_prompt():
    """Test TestGeneratorAgent prompt quality"""
    print("=" * 70)
    print("🧪 Testing TestGeneratorAgent Prompt Quality")
    print("=" * 70)
    
    agent = TestGeneratorAgent()
    
    print("\n4. TestGeneratorAgent Prompts:")
    
    code_example = """def add_numbers(a: int, b: int) -> int:
    \"\"\"Add two numbers.\"\"\"
    return a + b"""
    
    try:
        context = f"Code to test:\n```python\n{code_example}\n```"
        prompt = agent.prompt_builder.build_test_generator_prompt(
            agent_name=agent.name,
            agent_role=agent.role,
            skill_content=agent.skill,
            context=context
        )
        
        # Check for key elements
        checks = [
            ("comprehensive tests", "comprehensive"),
            ("normal cases", "normal"),
            ("edge cases", "edge"),
            ("error cases", "error"),
            ("Arrange-Act-Assert", "arrange-act-assert"),
            ("test names", "descriptive"),
        ]
        
        print(f"   ✅ Prompt built ({len(prompt)} chars)")
        print(f"   Key elements:")
        for check_name, check_text in checks:
            found = check_text.lower() in prompt.lower()
            status = "✅" if found else "❌"
            print(f"      {status} {check_name}")
    
    except Exception as e:
        print(f"   ❌ Error building prompt: {e}")
    
    print("\n" + "=" * 70 + "\n")


def test_error_analyzer():
    """Test ErrorAnalyzer improvements"""
    print("=" * 70)
    print("🧪 Testing ErrorAnalyzer Improvements")
    print("=" * 70)
    
    analyzer = ErrorAnalyzer()
    
    # Simulate test failure
    validation_results = {
        'tests_run': {
            'success': False,
            'error': 'Test failures occurred',
            'metadata': {
                'failed': 2,
                'passed': 1,
                'total': 3,
                'full_output': """
test_normal_case FAILED
AssertionError: assert 6 == 5
    assert add_numbers(2, 3) == 5
                        ^
test_edge_case FAILED
TypeError: unsupported operand type(s) for +: 'int' and 'NoneType'
    result = add_numbers(0, None)
                             ^
test_negative PASSED
""",
            }
        }
    }
    
    print("\n5. ErrorAnalyzer Analysis:")
    analysis = analyzer.analyze(validation_results)
    
    print(f"   ✅ Has errors: {analysis['has_errors']}")
    print(f"   ✅ Error type: {analysis['error_type']}")
    print(f"   ✅ Error summary: {analysis['error_summary']}")
    print(f"   ✅ Specific errors: {len(analysis['specific_errors'])} errors found")
    
    if analysis['specific_errors']:
        print(f"\n   Errors detected:")
        for i, error in enumerate(analysis['specific_errors'][:3], 1):
            print(f"      {i}. {error[:80]}...")
    
    print(f"\n   ✅ Fix suggestions:")
    suggestions = analysis['fix_suggestions'].split('\n')
    for suggestion in suggestions[:5]:
        if suggestion.strip():
            print(f"      • {suggestion}")
    
    print("\n" + "=" * 70 + "\n")


def run_simple_code_generation_test():
    """Test actual code generation with a simple task"""
    print("=" * 70)
    print("🧪 Testing Code Generation (Simple Task)")
    print("=" * 70)
    
    print("\n⚠️  Note: This will make actual API calls to Ollama")
    print("   Make sure Ollama is running and models are available\n")
    
    task = "Create a function to add two numbers with type hints and error handling"
    
    print(f"Task: \"{task}\"")
    print("\nStarting code generation...")
    
    try:
        orchestrator = Orchestrator()
        
        # Build context
        context = orchestrator.context_manager.build_context(
            task=task,
            context_dict={},
            agent_type='implementation'
        )
        
        # Use implementation agent directly
        agent = orchestrator.implementation_agent
        
        print("\n" + "=" * 70)
        result = agent.execute(
            task=task,
            context=context,
            use_tools=True,
            task_type='algorithm',
            context_dict={}
        )
        
        code = result.get('output', '')
        
        # Extract code from markdown if present
        if '```python' in code:
            import re
            match = re.search(r'```python\n(.*?)\n```', code, re.DOTALL)
            if match:
                code = match.group(1)
        
        print("\n" + "=" * 70)
        print("📄 Generated Code:")
        print("-" * 70)
        print(code[:1000])
        if len(code) > 1000:
            print(f"\n... ({len(code) - 1000} more characters)")
        print("-" * 70)
        
        # Check code quality
        print("\n📊 Code Quality Checks:")
        checks = [
            ("Type hints present", "def" in code and ("->" in code or ": int" in code or ": str" in code)),
            ("Docstring present", '"""' in code or "'''" in code),
            ("Error handling present", "try" in code or "if" in code),
            ("Function definition", "def " in code),
        ]
        
        for check_name, passed in checks:
            status = "✅" if passed else "❌"
            print(f"   {status} {check_name}")
        
        print("\n" + "=" * 70 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error during code generation: {e}")
        import traceback
        traceback.print_exc()
        print("\n" + "=" * 70 + "\n")


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("🧪 Testing Agent Specialization Enhancement Improvements")
    print("=" * 70)
    print("\nRunning comprehensive tests...\n")
    
    # Test 1: Task type detection
    test_task_type_detection()
    
    # Test 2: Skill selection
    test_skill_selection()
    
    # Test 3: ImplementationAgent prompts
    test_implementation_agent_prompt()
    
    # Test 4: TestGeneratorAgent prompts
    test_test_generator_prompt()
    
    # Test 5: ErrorAnalyzer
    test_error_analyzer()
    
    # Test 6: Actual code generation (optional - makes API calls)
    if len(sys.argv) > 1 and sys.argv[1] == "--run-code":
        run_simple_code_generation_test()
    else:
        print("=" * 70)
        print("💡 To test actual code generation, run:")
        print("   python3 test_agent_improvements.py --run-code")
        print("=" * 70)
    
    print("\n" + "=" * 70)
    print("✅ All Tests Complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()

