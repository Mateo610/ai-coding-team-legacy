"""
Automatic success evaluation
No human input required
"""

import ast
import subprocess
from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class EvaluationResult:
    score: int  # 0-100
    breakdown: Dict[str, int]
    errors: list
    passed_tests: int
    total_tests: int

class SuccessEvaluator:
    """Automatically scores interaction quality"""
    
    MAX_SCORE = 100
    
    @staticmethod
    def evaluate(interaction: Dict[str, Any]) -> EvaluationResult:
        """
        Automatic quality scoring
        
        Breakdown:
        - Syntax (10pts)
        - Execution (15pts)
        - Tests (15pts)
        - Style (10pts)
        - Efficiency (10pts)
        - Routing (10pts)
        - Tool usage (10pts)
        - Security (10pts)
        - Pattern match (10pts)
        """
        
        breakdown = {}
        errors = []
        output = interaction.get('output', '')
        
        # 1. Syntax Check (10 points)
        syntax_score = SuccessEvaluator._check_syntax(output)
        breakdown['syntax'] = syntax_score
        if syntax_score < 10:
            errors.append("Syntax errors detected")
        
        # 2. Execution (15 points)
        exec_score = SuccessEvaluator._check_execution(output)
        breakdown['execution'] = exec_score
        # Only add error if execution completely failed (0 points)
        # Partial credit (10) for interactive code is acceptable
        if exec_score == 0:
            errors.append("Code doesn't execute")
        elif exec_score < 15 and 'input(' in output:
            # Interactive code gets partial credit - don't flag as error
            pass
        
        # 3. Tests (15 points)
        test_results = interaction.get('metadata', {}).get('test_results', {})
        test_score = SuccessEvaluator._evaluate_tests(test_results)
        breakdown['tests'] = test_score
        
        # 4. Style compliance (10 points)
        style_score = SuccessEvaluator._check_style(output, interaction.get('context', ''))
        breakdown['style'] = style_score
        
        # 5. Efficiency (10 points)
        duration = interaction.get('duration_ms', 0)
        efficiency_score = 10 if duration < 5000 else max(0, 10 - (duration - 5000) // 1000)
        breakdown['efficiency'] = efficiency_score
        
        # 6. Routing accuracy (10 points)
        complexity_pred = interaction.get('complexity', {}).get('predicted', 5)
        complexity_actual = interaction.get('complexity', {}).get('actual', 5)
        routing_score = 10 if abs(complexity_pred - complexity_actual) <= 2 else 5
        breakdown['routing'] = routing_score
        
        # 7. Tool usage (10 points)
        tool_score = SuccessEvaluator._evaluate_tools(interaction.get('metadata', {}))
        breakdown['tools'] = tool_score
        
        # 8. Security (10 points)
        security_score = SuccessEvaluator._check_security(output)
        breakdown['security'] = security_score
        if security_score < 10:
            errors.append("Security concerns detected")
        
        # 9. Pattern matching (10 points)
        pattern_score = SuccessEvaluator._check_patterns(output, interaction.get('context', ''))
        breakdown['patterns'] = pattern_score
        
        total_score = sum(breakdown.values())
        
        return EvaluationResult(
            score=total_score,
            breakdown=breakdown,
            errors=errors,
            passed_tests=test_results.get('passed', 0),
            total_tests=test_results.get('total', 0)
        )
    
    @staticmethod
    def _check_syntax(code: str) -> int:
        """Check if code is syntactically valid"""
        # Extract code blocks
        if "```python" in code:
            code = code.split("```python")[1].split("```")[0]
        elif "```" in code:
            code = code.split("```")[1].split("```")[0]
        
        try:
            ast.parse(code)
            return 10
        except SyntaxError:
            return 0
    
    @staticmethod
    def _check_execution(code: str) -> int:
        """Try to execute code"""
        # Extract code
        if "```python" in code:
            code = code.split("```python")[1].split("```")[0]
        
        # Check if code contains interactive elements
        has_input = 'input(' in code or 'raw_input(' in code
        
        try:
            # Save to temp file
            with open('/tmp/test_eval.py', 'w') as f:
                f.write(code)
            
            # Try to run
            result = subprocess.run(
                ['python3', '/tmp/test_eval.py'],
                capture_output=True,
                timeout=2,
                input='\n' * 10,  # Provide dummy input for interactive code
                text=True
            )
            
            return 15 if result.returncode == 0 else 5
        except subprocess.TimeoutExpired:
            # Timeout might indicate interactive code waiting for input
            if has_input:
                # Interactive code with valid syntax gets partial credit
                try:
                    ast.parse(code)
                    return 10  # Partial credit for valid interactive code
                except SyntaxError:
                    return 0
            return 0
        except Exception:
            # Other exceptions - check if it's interactive code with valid syntax
            if has_input:
                try:
                    ast.parse(code)
                    return 10  # Partial credit for valid interactive code
                except SyntaxError:
                    return 0
            return 0
    
    @staticmethod
    def _evaluate_tests(test_results: Dict) -> int:
        """Score based on test pass rate"""
        if not test_results:
            return 5  # No tests is better than failing tests
        
        passed = test_results.get('passed', 0)
        total = test_results.get('total', 1)
        
        pass_rate = passed / total
        return int(15 * pass_rate)
    
    @staticmethod
    def _check_style(code: str, context: str) -> int:
        """Check style compliance"""
        score = 10
        
        # Basic checks
        if 'TODO' in code or 'FIXME' in code:
            score -= 2
        if len(code.split('\n')) > 200:  # Very long
            score -= 2
        if '# type: ignore' in code:
            score -= 1
        
        return max(0, score)
    
    @staticmethod
    def _evaluate_tools(metadata: Dict) -> int:
        """Score tool usage"""
        tool_calls = metadata.get('tool_calls', [])
        
        if not tool_calls:
            return 5  # Didn't use tools when maybe should have
        
        # Check if tools were used appropriately
        score = 10
        for tool_call in tool_calls:
            if not tool_call.get('success'):
                score -= 2
        
        return max(0, score)
    
    @staticmethod
    def _check_security(code: str) -> int:
        """Basic security checks"""
        score = 10
        
        dangerous_patterns = [
            'eval(', 'exec(', '__import__',
            'os.system', 'subprocess.call',
            'pickle.loads', 'yaml.load'
        ]
        
        for pattern in dangerous_patterns:
            if pattern in code:
                score -= 3
        
        return max(0, score)
    
    @staticmethod
    def _check_patterns(code: str, context: str) -> int:
        """Check if code matches project patterns"""
        # Placeholder - will improve with RAG
        return 8  # Assume mostly good