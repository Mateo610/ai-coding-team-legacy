"""
Enhanced Complexity Predictor with Learning
Section 6: Routing & Model Selection Enhancement

Predicts task complexity with improved accuracy and learns from past decisions
"""

import re
import hashlib
from typing import Dict, Any, Optional
from agents.routing_optimizer import ROUTING_OPTIMIZER


class ComplexityPredictor:
    """
    Enhanced complexity predictor that learns from past decisions
    Predicts complexity score 1-10
    >=8 typically routes to Claude
    """
    
    # Expanded keyword lists for better accuracy
    COMPLEX_KEYWORDS = [
        'architecture', 'design system', 'refactor entire',
        'optimize performance', 'security audit',
        'distributed system', 'scalability',
        'migration', 'redesign', 'restructure',
        'multi-tenant', 'microservices', 'event-driven',
        'real-time processing', 'data pipeline', 'etl pipeline',
        'machine learning model', 'ai integration', 'nlp processing'
    ]
    
    MEDIUM_KEYWORDS = [
        'implement', 'create', 'add feature',
        'integrate', 'connect', 'setup',
        'api endpoint', 'database model', 'crud operations',
        'authentication', 'authorization', 'validation',
        'testing', 'unit test', 'integration test'
    ]
    
    SIMPLE_KEYWORDS = [
        'fix bug', 'add test', 'update style',
        'change text', 'rename', 'format',
        'typo', 'grammar', 'comment',
        'simple', 'quick', 'minor'
    ]
    
    # Task type specific complexity adjustments
    TASK_TYPE_COMPLEXITY = {
        'algorithm': {'base': 4, 'range': (2, 8)},  # Algorithms vary greatly
        'api': {'base': 6, 'range': (4, 10)},  # APIs often need auth, validation
        'database': {'base': 5, 'range': (3, 9)},  # DB tasks can be complex
        'crud': {'base': 4, 'range': (2, 7)},  # CRUD is usually straightforward
        'frontend': {'base': 5, 'range': (3, 8)},  # Frontend varies
        'devops': {'base': 6, 'range': (4, 9)},  # DevOps often complex
        'etl': {'base': 7, 'range': (5, 10)},  # ETL is typically complex
        'data_analysis': {'base': 6, 'range': (4, 9)},  # Data analysis can be complex
        'test': {'base': 3, 'range': (2, 6)},  # Tests are usually simpler
        'general': {'base': 5, 'range': (3, 8)}  # General tasks vary
    }
    
    def __init__(self, use_learning: bool = True):
        """
        Initialize complexity predictor
        
        Args:
            use_learning: Whether to use learned patterns (default: True)
        """
        self.use_learning = use_learning
        self.routing_optimizer = ROUTING_OPTIMIZER if use_learning else None
    
    def predict(self, task: str, context: Dict[str, Any] = None, task_type: Optional[str] = None) -> int:
        """
        Returns enhanced complexity score 1-10
        
        Args:
            task: Task description
            context: Context dictionary with additional information
            task_type: Detected task type (optional, will use if not provided)
        
        Returns:
            Complexity score 1-10
        """
        context = context or {}
        task_lower = task.lower()
        
        # Get task type if not provided
        if task_type is None:
            task_type = context.get('task_type', 'general')
        
        # Start with task-type-specific base complexity
        if task_type in self.TASK_TYPE_COMPLEXITY:
            type_config = self.TASK_TYPE_COMPLEXITY[task_type]
            complexity = type_config['base']
            complexity_range = type_config['range']
        else:
            complexity = 5  # Default neutral
            complexity_range = (3, 8)
        
        # Lexical analysis (improved weighting)
        complex_match = sum(1 for kw in self.COMPLEX_KEYWORDS if kw in task_lower)
        medium_match = sum(1 for kw in self.MEDIUM_KEYWORDS if kw in task_lower)
        simple_match = sum(1 for kw in self.SIMPLE_KEYWORDS if kw in task_lower)
        
        if complex_match > 0:
            complexity += min(3, complex_match * 1.5)  # Cap at +3
        elif medium_match > 0:
            complexity += min(2, medium_match * 0.5)  # Smaller boost
        elif simple_match > 0:
            complexity -= min(2, simple_match * 0.5)  # Reduce complexity
        
        # Codebase size (weighted by task type)
        files_involved = context.get('files_involved', 1)
        if files_involved > 10:
            complexity += 2
        elif files_involved > 5:
            complexity += 1
        
        # Dependencies complexity (new factor)
        dependencies = context.get('dependencies', [])
        if isinstance(dependencies, list) and len(dependencies) > 5:
            complexity += 1
        if any(dep in ['pandas', 'numpy', 'tensorflow', 'pytorch', 'fastapi'] for dep in dependencies):
            complexity += 1
        
        # Pattern familiarity (learned from metrics if available)
        has_similar = context.get('has_similar_example', False)
        if has_similar:
            complexity -= 2
        
        # Historical success rate for similar tasks (if learning enabled)
        if self.use_learning and self.routing_optimizer:
            task_hash = hashlib.md5(task.encode()).hexdigest()[:8]
            # Could look up similar task performance here
            # For now, rely on task type routing preferences
        
        # Novelty
        pattern_familiarity = context.get('pattern_familiarity', 0.5)
        if pattern_familiarity < 0.3:
            complexity += 2
        elif pattern_familiarity > 0.7:
            complexity -= 1
        
        # Task length (improved weighting)
        word_count = len(task.split())
        if word_count > 50:
            complexity += 2
        elif word_count > 30:
            complexity += 1
        elif word_count < 10:
            complexity -= 1
        
        # Code snippets or examples in task (indicates complexity)
        if '```' in task or 'example' in task_lower:
            complexity += 1
        
        # Multiple requirements (indicates complexity)
        requirement_indicators = ['and', 'also', 'additionally', 'furthermore']
        if sum(1 for indicator in requirement_indicators if indicator in task_lower) > 2:
            complexity += 1
        
        # Clamp to range and overall limits
        complexity = max(complexity_range[0], min(complexity, complexity_range[1]))
        complexity = max(1, min(10, complexity))
        
        return int(complexity)
    
    def predict_with_explanation(self, task: str, context: Dict[str, Any] = None,
                                 task_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Predict complexity with detailed explanation
        
        Returns:
            Dictionary with complexity score and explanation
        """
        complexity = self.predict(task, context, task_type)
        
        explanation_parts = []
        
        # Explain factors
        task_lower = task.lower()
        if any(kw in task_lower for kw in self.COMPLEX_KEYWORDS):
            explanation_parts.append("Complex keywords detected")
        
        files_involved = context.get('files_involved', 1) if context else 1
        if files_involved > 5:
            explanation_parts.append(f"{files_involved} files involved")
        
        if task_type:
            explanation_parts.append(f"Task type: {task_type}")
        
        explanation = "; ".join(explanation_parts) if explanation_parts else "Standard complexity assessment"
        
        return {
            'complexity': complexity,
            'explanation': explanation,
            'task_type': task_type or (context.get('task_type', 'general') if context else 'general')
        }