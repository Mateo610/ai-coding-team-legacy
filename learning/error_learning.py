"""
Error Learning System - Learn from errors and improve prompts/examples
Section 7.1: Error Analysis Enhancement

Automatically updates prompts and examples based on common error patterns.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from learning.error_patterns import ErrorPatternDatabase, ErrorPattern


class ErrorLearningSystem:
    """Learns from errors and suggests prompt/example improvements"""
    
    def __init__(self, error_db: Optional[ErrorPatternDatabase] = None):
        """
        Initialize error learning system
        
        Args:
            error_db: ErrorPatternDatabase instance
        """
        self.error_db = error_db or ErrorPatternDatabase()
        self.examples_dir = Path('.aiconfig') / 'examples'
        self.examples_dir.mkdir(parents=True, exist_ok=True)
    
    def analyze_errors_for_improvements(self, 
                                       error_type: Optional[str] = None,
                                       task_type: Optional[str] = None,
                                       min_frequency: int = 3,
                                       days: int = 30) -> Dict[str, Any]:
        """
        Analyze error patterns and suggest prompt/example improvements
        
        Returns:
            Dictionary with improvement suggestions
        """
        patterns = self.error_db.get_common_patterns(
            error_type=error_type,
            task_type=task_type,
            min_frequency=min_frequency,
            days=days
        )
        
        suggestions = {
            'prompt_improvements': [],
            'example_additions': [],
            'skill_updates': [],
            'pattern_insights': []
        }
        
        for pattern in patterns:
            # Analyze each pattern
            insight = self._analyze_pattern(pattern)
            
            if insight['needs_prompt_improvement']:
                suggestions['prompt_improvements'].append({
                    'task_type': pattern.task_type,
                    'error_type': pattern.error_type,
                    'pattern': pattern.error_message_pattern,
                    'frequency': pattern.frequency,
                    'suggestion': insight['prompt_suggestion']
                })
            
            if insight['needs_example']:
                suggestions['example_additions'].append({
                    'task_type': pattern.task_type,
                    'error_type': pattern.error_type,
                    'example_content': insight['example_content'],
                    'frequency': pattern.frequency
                })
            
            suggestions['pattern_insights'].append(insight)
        
        return suggestions
    
    def _analyze_pattern(self, pattern: ErrorPattern) -> Dict[str, Any]:
        """Analyze a single error pattern and suggest improvements"""
        insight = {
            'error_type': pattern.error_type,
            'pattern': pattern.error_message_pattern,
            'frequency': pattern.frequency,
            'needs_prompt_improvement': False,
            'prompt_suggestion': '',
            'needs_example': False,
            'example_content': None
        }
        
        # Determine if pattern suggests prompt improvements needed
        if pattern.frequency >= 5:
            insight['needs_prompt_improvement'] = True
            insight['prompt_suggestion'] = self._generate_prompt_suggestion(pattern)
        
        # Determine if pattern needs an example
        if pattern.frequency >= 3 and not pattern.code_examples:
            insight['needs_example'] = True
            insight['example_content'] = self._generate_example_content(pattern)
        
        return insight
    
    def _generate_prompt_suggestion(self, pattern: ErrorPattern) -> str:
        """Generate prompt improvement suggestion based on pattern"""
        suggestions = []
        
        if pattern.error_type == 'syntax':
            if 'unexpected EOF' in pattern.error_message_pattern:
                suggestions.append("Add explicit reminder to close all brackets, parentheses, and code blocks")
            elif 'invalid syntax' in pattern.error_message_pattern:
                suggestions.append("Emphasize proper Python syntax and keyword usage")
            elif 'indentation' in pattern.error_message_pattern.lower():
                suggestions.append("Add explicit reminder about proper indentation (4 spaces)")
        
        elif pattern.error_type == 'runtime':
            if 'TypeError' in pattern.error_message_pattern:
                suggestions.append("Emphasize type checking and conversion in prompts")
            elif 'AttributeError' in pattern.error_message_pattern:
                suggestions.append("Add reminder to verify object attributes exist before access")
            elif 'NameError' in pattern.error_message_pattern:
                suggestions.append("Emphasize variable definition before use")
        
        elif pattern.error_type == 'test_failure':
            if 'AssertionError' in pattern.error_message_pattern:
                suggestions.append("Add reminder to verify expected vs actual values in tests")
            elif pattern.task_type in ['api', 'database']:
                suggestions.append(f"For {pattern.task_type} tasks, emphasize proper test assertions")
        
        if not suggestions:
            suggestions.append(f"Consider adding specific guidance for {pattern.error_type} errors")
        
        return " | ".join(suggestions)
    
    def _generate_example_content(self, pattern: ErrorPattern) -> Dict[str, str]:
        """Generate example content showing how to avoid this error"""
        example = {
            'task': f"Example task that previously caused: {pattern.error_type}",
            'code': f"# Code example showing correct approach\n# Previously caused: {pattern.error_message_pattern[:100]}",
            'explanation': f"This example demonstrates how to avoid {pattern.error_type}"
        }
        
        # Task-specific examples
        if pattern.error_type == 'syntax':
            example['code'] = """# Correct syntax example
def example_function(param1: str, param2: int) -> str:
    \"\"\"
    Example function with proper syntax.
    
    Args:
        param1: String parameter
        param2: Integer parameter
    
    Returns:
        String result
    \"\"\"
    if param1 and param2 > 0:
        result = f"{param1}_{param2}"
        return result
    else:
        raise ValueError("Invalid parameters")
"""
        elif pattern.error_type == 'runtime' and 'TypeError' in pattern.error_message_pattern:
            example['code'] = """# Correct type handling
def process_data(value):
    \"\"\"Process data with proper type checking.\"\"\"
    if isinstance(value, str):
        return value.upper()
    elif isinstance(value, int):
        return str(value)
    else:
        raise TypeError(f"Unsupported type: {type(value)}")
"""
        
        return example
    
    def generate_improved_examples(self, 
                                   task_type: str,
                                   error_patterns: List[ErrorPattern]) -> List[Dict[str, Any]]:
        """Generate improved examples based on error patterns"""
        examples = []
        
        for pattern in error_patterns:
            if pattern.task_type == task_type and pattern.frequency >= 3:
                example_content = self._generate_example_content(pattern)
                examples.append({
                    'task_type': task_type,
                    'error_type': pattern.error_type,
                    'example': example_content,
                    'frequency': pattern.frequency
                })
        
        return examples
    
    def get_improvement_recommendations(self, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive improvement recommendations"""
        suggestions = self.analyze_errors_for_improvements(days=days)
        
        recommendations = {
            'priority': [],
            'examples_needed': [],
            'prompt_updates_needed': []
        }
        
        # High priority: frequent errors without good fixes
        high_freq = [s for s in suggestions['prompt_improvements'] if s['frequency'] >= 5]
        if high_freq:
            recommendations['priority'].append({
                'type': 'high',
                'message': f"{len(high_freq)} high-frequency error patterns need prompt improvements",
                'patterns': high_freq
            })
        
        # Examples needed
        if suggestions['example_additions']:
            recommendations['examples_needed'] = suggestions['example_additions']
        
        # Prompt updates needed
        if suggestions['prompt_improvements']:
            recommendations['prompt_updates_needed'] = suggestions['prompt_improvements']
        
        return {
            'recommendations': recommendations,
            'total_patterns': len(suggestions['pattern_insights']),
            'period_days': days
        }


class PromptImprovementGenerator:
    """Generates prompt improvements based on error patterns"""
    
    def __init__(self, error_learning: ErrorLearningSystem):
        """
        Initialize prompt improvement generator
        
        Args:
            error_learning: ErrorLearningSystem instance
        """
        self.error_learning = error_learning
    
    def generate_prompt_addition(self, 
                                task_type: str,
                                error_type: str,
                                pattern: str) -> str:
        """
        Generate prompt addition to prevent specific error pattern
        
        Returns:
            String to add to prompt for this task type
        """
        additions = []
        
        if error_type == 'syntax' and 'indentation' in pattern.lower():
            additions.append("CRITICAL: Use exactly 4 spaces for indentation. Never mix tabs and spaces.")
        
        elif error_type == 'runtime' and 'TypeError' in pattern:
            if task_type == 'api':
                additions.append("CRITICAL: Validate and convert request parameters to correct types before use.")
            elif task_type == 'database':
                additions.append("CRITICAL: Ensure database query parameters match expected types.")
            else:
                additions.append("CRITICAL: Check parameter types match function signatures before calling.")
        
        elif error_type == 'runtime' and 'AttributeError' in pattern:
            additions.append("CRITICAL: Verify objects are initialized and have expected attributes before access.")
        
        elif error_type == 'test_failure' and 'AssertionError' in pattern:
            if task_type == 'api':
                additions.append("CRITICAL: Test assertions must match actual API response format and status codes.")
            else:
                additions.append("CRITICAL: Verify expected values match actual function behavior before writing assertions.")
        
        if not additions:
            return ""
        
        return "\n".join(additions)
    
    def update_prompt_for_task_type(self,
                                   base_prompt: str,
                                   task_type: str,
                                   error_patterns: List[ErrorPattern]) -> str:
        """Update prompt with improvements based on error patterns"""
        improvements = []
        
        for pattern in error_patterns:
            if pattern.task_type == task_type and pattern.frequency >= 3:
                addition = self.generate_prompt_addition(
                    task_type=task_type,
                    error_type=pattern.error_type,
                    pattern=pattern.error_message_pattern
                )
                if addition:
                    improvements.append(addition)
        
        if improvements:
            improvements_section = "\n\n=== ERROR PREVENTION GUIDANCE ===\n"
            improvements_section += "\n".join(improvements)
            return base_prompt + improvements_section
        
        return base_prompt


# Global instance
ERROR_LEARNING = ErrorLearningSystem()

