"""
Test script for complex tasks to evaluate Agent Specialization Enhancement
"""
import sys
import re
from pathlib import Path
from agents.orchestrator import Orchestrator
from agents.specialized_agent import ImplementationAgent
from tools.code_tools import CodeTools
from agents.context_manager import ContextManager
from agents.skill_manager import SKILL_MANAGER
import json

class CodeQualityChecker:
    """Check code quality against enhanced requirements"""
    
    @staticmethod
    def check_code_quality(code: str, task_type: str = None) -> dict:
        """Check code against quality requirements"""
        checks = {
            'has_type_hints': False,
            'has_docstrings': False,
            'has_error_handling': False,
            'has_input_validation': False,
            'has_comprehensive_docstring': False,
            'follows_pep8': False,
            'production_ready': False,
            'task_specific': False,
        }
        
        # Extract code from markdown if present
        clean_code = CodeTools._extract_code(code)
        
        # Check for type hints
        if re.search(r'def\s+\w+\s*\([^)]*:.*\)\s*->', clean_code) or \
           re.search(r'->\s+\w+', clean_code) or \
           re.search(r':\s*(int|str|float|bool|list|dict|Optional|List|Dict)', clean_code):
            checks['has_type_hints'] = True
        
        # Check for docstrings
        if '"""' in clean_code or "'''" in clean_code:
            checks['has_docstrings'] = True
        
        # Check for comprehensive docstring (Args, Returns, Raises)
        if re.search(r'Args?:|Returns?:|Raises?:', clean_code, re.IGNORECASE):
            checks['has_comprehensive_docstring'] = True
        
        # Check for error handling
        if 'try' in clean_code and 'except' in clean_code:
            checks['has_error_handling'] = True
        
        # Check for input validation
        if 'isinstance' in clean_code or 'if not' in clean_code or 'validate' in clean_code.lower():
            checks['has_input_validation'] = True
        
        # Basic PEP 8 checks
        if not re.search(r'[a-z_][a-z0-9_]*\s*=\s*[A-Z]', clean_code):  # No uppercase variable names
            checks['follows_pep8'] = True
        
        # Check for production-ready patterns
        production_patterns = [
            'raise',  # Raises exceptions
            'return',  # Returns values
            'def ',  # Function definitions
        ]
        if any(pattern in clean_code for pattern in production_patterns):
            checks['production_ready'] = True
        
        # Task-specific checks
        if task_type == 'api':
            if 'app.' in clean_code or '@app.' in clean_code or 'FastAPI' in clean_code or \
               'flask' in clean_code.lower() or 'status_code' in clean_code or '200' in clean_code:
                checks['task_specific'] = True
        elif task_type == 'crud':
            if 'create' in clean_code.lower() or 'insert' in clean_code.lower() or \
               'save' in clean_code.lower() or 'add' in clean_code.lower():
                checks['task_specific'] = True
        elif task_type == 'database':
            if 'class' in clean_code and ('Column' in clean_code or 'relationship' in clean_code or \
               'sqlalchemy' in clean_code.lower() or 'db.' in clean_code):
                checks['task_specific'] = True
        elif task_type == 'algorithm':
            if 'def ' in clean_code and ('return' in clean_code or 'yield' in clean_code):
                checks['task_specific'] = True
        
        return checks


def test_complex_task(orchestrator, task: str, task_type: str, expected_checks: list):
    """Test a complex task and evaluate results"""
    print("\n" + "=" * 70)
    print(f"🧪 Testing: {task}")
    print("=" * 70)
    
    try:
        # Build context
        context = orchestrator.context_manager.build_context(
            task=task,
            context_dict={},
            agent_type='implementation'
        )
        
        # Get relevant skills
        agent = orchestrator.implementation_agent
        skill_names, skill_tokens = SKILL_MANAGER.get_relevant_skills(
            task=task,
            task_type=task_type,
            max_tokens=8000
        )
        
        print(f"\n📚 Skills selected: {len(skill_names)} skills")
        print(f"   Skills: {', '.join(skill_names[:5])}{'...' if len(skill_names) > 5 else ''}")
        print(f"   Tokens: {skill_tokens}")
        
        # Generate code
        print(f"\n💻 Generating code...")
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
        
        print(f"\n📄 Generated Code ({len(clean_code)} chars):")
        print("-" * 70)
        # Show first 500 chars
        print(clean_code[:500])
        if len(clean_code) > 500:
            print(f"\n... ({len(clean_code) - 500} more characters)")
        print("-" * 70)
        
        # Check code quality
        quality_checks = CodeQualityChecker.check_code_quality(clean_code, task_type)
        
        print(f"\n📊 Code Quality Assessment:")
        print("-" * 70)
        
        score = 0
        total = len(quality_checks)
        
        for check_name, passed in quality_checks.items():
            status = "✅" if passed else "❌"
            print(f"   {status} {check_name.replace('_', ' ').title()}")
            if passed:
                score += 1
        
        quality_score = (score / total) * 100
        print(f"\n   Quality Score: {quality_score:.1f}% ({score}/{total})")
        
        # Check expected requirements
        if expected_checks:
            print(f"\n📋 Expected Requirements:")
            print("-" * 70)
            for expected_check in expected_checks:
                check_passed = quality_checks.get(expected_check, False)
                status = "✅" if check_passed else "❌"
                print(f"   {status} {expected_check.replace('_', ' ').title()}")
        
        # Syntax check
        print(f"\n🔍 Syntax Validation:")
        print("-" * 70)
        syntax_result = CodeTools.check_syntax(clean_code)
        if syntax_result.success:
            print(f"   ✅ Syntax valid")
        else:
            print(f"   ❌ Syntax error: {syntax_result.error[:200]}")
        
        return {
            'task': task,
            'task_type': task_type,
            'code_length': len(clean_code),
            'quality_checks': quality_checks,
            'quality_score': quality_score,
            'syntax_valid': syntax_result.success,
            'skills_used': skill_names,
            'code': clean_code[:500]  # First 500 chars for summary
        }
        
    except Exception as e:
        print(f"\n❌ Error during task execution: {e}")
        import traceback
        traceback.print_exc()
        return {
            'task': task,
            'task_type': task_type,
            'error': str(e)
        }


def main():
    """Run complex task tests"""
    print("=" * 70)
    print("🧪 Testing Agent Specialization Enhancement with Complex Tasks")
    print("=" * 70)
    
    print("\n⚠️  Note: This will make actual API calls to Ollama")
    print("   Make sure Ollama is running and models are available\n")
    
    try:
        orchestrator = Orchestrator()
    except Exception as e:
        print(f"\n❌ Failed to initialize orchestrator: {e}")
        print("   Make sure Ollama is running and models are configured")
        return
    
    # Define complex test tasks
    complex_tasks = [
        {
            'task': 'Create a Flask REST API endpoint for user authentication that accepts email and password, validates the input, authenticates the user, and returns a JWT token with proper error handling and HTTP status codes',
            'task_type': 'api',
            'expected_checks': ['has_type_hints', 'has_comprehensive_docstring', 'has_error_handling', 
                               'has_input_validation', 'task_specific', 'production_ready']
        },
        {
            'task': 'Create SQLAlchemy models for a blog post system with relationships between Post, Author, and Comment models, including proper constraints, indexes, and relationships',
            'task_type': 'database',
            'expected_checks': ['has_type_hints', 'has_docstrings', 'task_specific', 'production_ready']
        },
        {
            'task': 'Create a CRUD function to create a user in the database with validation for email format, password strength, and duplicate email checking, including proper error handling',
            'task_type': 'crud',
            'expected_checks': ['has_type_hints', 'has_comprehensive_docstring', 'has_error_handling',
                               'has_input_validation', 'task_specific', 'production_ready']
        },
        {
            'task': 'Implement a binary search algorithm with type hints, docstrings explaining time complexity, and proper error handling for edge cases like empty arrays and unsorted arrays',
            'task_type': 'algorithm',
            'expected_checks': ['has_type_hints', 'has_comprehensive_docstring', 'has_error_handling',
                               'has_input_validation', 'task_specific', 'production_ready']
        },
        {
            'task': 'Create a data processing function using pandas to clean and transform a DataFrame, including handling missing values, data type conversions, and validation with proper error handling',
            'task_type': 'algorithm',
            'expected_checks': ['has_type_hints', 'has_docstrings', 'has_error_handling',
                               'task_specific', 'production_ready']
        },
    ]
    
    results = []
    
    print(f"\n📋 Testing {len(complex_tasks)} complex tasks...\n")
    
    for i, task_config in enumerate(complex_tasks, 1):
        print(f"\n{'='*70}")
        print(f"Task {i}/{len(complex_tasks)}")
        print(f"{'='*70}")
        
        result = test_complex_task(
            orchestrator,
            task_config['task'],
            task_config['task_type'],
            task_config['expected_checks']
        )
        
        results.append(result)
        
        # Brief pause between tasks
        import time
        time.sleep(1)
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 Test Results Summary")
    print("=" * 70)
    
    successful_tasks = [r for r in results if 'error' not in r]
    failed_tasks = [r for r in results if 'error' in r]
    
    print(f"\n✅ Successful tasks: {len(successful_tasks)}/{len(results)}")
    print(f"❌ Failed tasks: {len(failed_tasks)}/{len(results)}")
    
    if successful_tasks:
        avg_quality = sum(r['quality_score'] for r in successful_tasks) / len(successful_tasks)
        avg_code_length = sum(r['code_length'] for r in successful_tasks) / len(successful_tasks)
        
        print(f"\n📈 Average Quality Score: {avg_quality:.1f}%")
        print(f"📏 Average Code Length: {avg_code_length:.0f} characters")
        
        print(f"\n📊 Quality Breakdown:")
        print("-" * 70)
        
        # Aggregate quality checks
        all_checks = {}
        for result in successful_tasks:
            for check_name, passed in result['quality_checks'].items():
                if check_name not in all_checks:
                    all_checks[check_name] = {'passed': 0, 'total': 0}
                all_checks[check_name]['passed'] += (1 if passed else 0)
                all_checks[check_name]['total'] += 1
        
        for check_name, stats in sorted(all_checks.items()):
            percentage = (stats['passed'] / stats['total']) * 100
            status = "✅" if percentage >= 80 else "⚠️" if percentage >= 50 else "❌"
            print(f"   {status} {check_name.replace('_', ' ').title()}: {percentage:.1f}% ({stats['passed']}/{stats['total']})")
        
        print(f"\n📋 Task-Specific Results:")
        print("-" * 70)
        for result in successful_tasks:
            status = "✅" if result['quality_score'] >= 80 else "⚠️"
            print(f"   {status} {result['task_type'].upper()}: {result['quality_score']:.1f}% quality")
            print(f"      Task: {result['task'][:60]}...")
    
    if failed_tasks:
        print(f"\n❌ Failed Tasks:")
        print("-" * 70)
        for result in failed_tasks:
            print(f"   ❌ {result['task_type'].upper()}: {result.get('error', 'Unknown error')}")
    
    print("\n" + "=" * 70)
    print("✅ Complex Task Testing Complete!")
    print("=" * 70)
    
    # Save results to file
    results_file = Path("test_results_complex_tasks.json")
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n💾 Results saved to: {results_file}")


if __name__ == "__main__":
    main()

