"""
Test a single complex task in detail
"""
import sys
from agents.orchestrator import Orchestrator
from tools.code_tools import CodeTools
import re

def test_single_task(task: str, task_type: str):
    """Test a single complex task with detailed output"""
    print("=" * 70)
    print("🧪 Testing Complex Task")
    print("=" * 70)
    
    print(f"\n📋 Task: {task}")
    print(f"📊 Task Type: {task_type}")
    
    try:
        orchestrator = Orchestrator()
        
        # Build context
        print(f"\n📚 Building context...")
        context = orchestrator.context_manager.build_context(
            task=task,
            context_dict={},
            agent_type='implementation'
        )
        
        # Get skills
        from agents.skill_manager import SKILL_MANAGER
        agent = orchestrator.implementation_agent
        skill_names, skill_tokens = SKILL_MANAGER.get_relevant_skills(
            task=task,
            task_type=task_type,
            max_tokens=8000
        )
        
        print(f"\n📚 Skills selected: {len(skill_names)}")
        print(f"   Skills: {', '.join(skill_names)}")
        print(f"   Tokens: {skill_tokens}")
        
        # Generate code
        print(f"\n💻 Generating code...")
        print("=" * 70)
        
        result = agent.execute(
            task=task,
            context=context,
            use_tools=True,
            task_type=task_type,
            context_dict={}
        )
        
        code = result.get('output', '')
        
        # Extract code from markdown if present
        clean_code = CodeTools._extract_code(code)
        
        print("\n" + "=" * 70)
        print("📄 Generated Code:")
        print("=" * 70)
        print(clean_code)
        print("=" * 70)
        
        # Syntax check
        print("\n🔍 Syntax Validation:")
        print("-" * 70)
        syntax_result = CodeTools.check_syntax(clean_code)
        if syntax_result.success:
            print("✅ Syntax valid")
        else:
            print(f"❌ Syntax error: {syntax_result.error}")
        
        # Check quality
        print("\n📊 Code Quality Checks:")
        print("-" * 70)
        
        checks = {
            'Type hints': re.search(r'def\s+\w+\s*\([^)]*:.*\)\s*->|->\s+\w+|:\s*(int|str|float|bool|list|dict|Optional)', clean_code) is not None,
            'Docstrings': '"""' in clean_code or "'''" in clean_code,
            'Comprehensive docstring': re.search(r'Args?:|Returns?:|Raises?:', clean_code, re.IGNORECASE) is not None,
            'Error handling': 'try' in clean_code and 'except' in clean_code,
            'Input validation': 'isinstance' in clean_code or 'validate' in clean_code.lower() or 'if not' in clean_code,
        }
        
        for check_name, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"   {status} {check_name}")
        
        score = sum(checks.values())
        total = len(checks)
        print(f"\n   Quality Score: {(score/total)*100:.1f}% ({score}/{total})")
        
        # Show code statistics
        print("\n📈 Code Statistics:")
        print("-" * 70)
        print(f"   Total length: {len(clean_code)} characters")
        print(f"   Lines: {len(clean_code.split(chr(10)))}")
        print(f"   Functions: {len(re.findall(r'def\s+\w+', clean_code))}")
        print(f"   Classes: {len(re.findall(r'class\s+\w+', clean_code))}")
        
        return {
            'success': syntax_result.success,
            'code': clean_code,
            'quality_score': (score/total)*100,
            'checks': checks
        }
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}


if __name__ == "__main__":
    # Test tasks - can modify these
    test_tasks = [
        {
            'task': 'Create a function to add two numbers with type hints, docstrings, and error handling',
            'type': 'algorithm'
        },
        {
            'task': 'Create a Flask REST API endpoint for user authentication with email and password validation, JWT token generation, and proper HTTP status codes',
            'type': 'api'
        },
        {
            'task': 'Create SQLAlchemy models for a blog post system with Post, Author, and Comment models including relationships and constraints',
            'type': 'database'
        },
    ]
    
    # Get task from command line or use first one
    if len(sys.argv) > 1:
        task_index = int(sys.argv[1]) - 1
        if 0 <= task_index < len(test_tasks):
            selected_task = test_tasks[task_index]
        else:
            print(f"Invalid task index. Use 1-{len(test_tasks)}")
            sys.exit(1)
    else:
        selected_task = test_tasks[0]
    
    print("\n" + "=" * 70)
    print("🧪 Complex Task Testing")
    print("=" * 70)
    print(f"\nAvailable tasks:")
    for i, task in enumerate(test_tasks, 1):
        marker = ">" if task == selected_task else " "
        print(f"   {marker} {i}. {task['task'][:60]}...")
    
    print(f"\n{'='*70}\n")
    
    result = test_single_task(selected_task['task'], selected_task['type'])
    
    print("\n" + "=" * 70)
    if result.get('success'):
        print("✅ Test Complete!")
    else:
        print("❌ Test Failed!")
    print("=" * 70)
    
    print(f"\n💡 To test other tasks, run:")
    print(f"   python3 test_single_complex_task.py <task_number>")
    print(f"   where task_number is 1-{len(test_tasks)}")


