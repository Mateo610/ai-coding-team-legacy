"""
Consolidated Model Escalation Tools
Replaces: check_complexity, escalate_to_flagship, get_flagship_help, refine_with_flagship
"""

import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tools.code_tools import ToolResult
from tools.model_escalation import ModelEscalationTools


class EscalationTools:
    """Consolidated model escalation tools with mode-based operations"""
    
    @staticmethod
    def model_escalate(task: str, mode: str = "consult", **kwargs) -> ToolResult:
        """
        Delegate hard subtasks to Claude / DeepSeek / GPT-4.
        
        Replaces: check_complexity, escalate_to_flagship, get_flagship_help, refine_with_flagship
        
        Args:
            task: Task description
            mode: Operation mode:
                - "consult" (default): Escalate task to flagship model
                - "check_complexity": Check if task is too complex
                - "help": Get help from flagship model
                - "refine": Refine solution using flagship model
            **kwargs: Additional arguments for specific modes:
                - consult: context (optional), issue (optional), attempts (optional), model (optional, default: "deepseek")
                - check_complexity: context (optional), error_history (optional)
                - help: context (optional), model (optional, default: "deepseek")
                - refine: solution (required), feedback (optional), improvements (optional), model (optional, default: "deepseek")
        
        Returns:
            ToolResult with escalation results based on mode
        
        Examples:
            model_escalate("Complex task", mode="consult")  # Escalate to flagship model
            model_escalate("Complex task", mode="check_complexity")  # Check complexity
            model_escalate("How to implement X?", mode="help")  # Get help
            model_escalate("Refine this", mode="refine", solution="# Code here")  # Refine solution
        """
        try:
            if mode == "consult":
                # Use ModelEscalationTools.escalate_to_flagship
                context = kwargs.get("context")
                issue = kwargs.get("issue")
                attempts = kwargs.get("attempts")
                model = kwargs.get("model", "deepseek")
                system_prompt = kwargs.get("system_prompt")
                max_tokens = kwargs.get("max_tokens", 4000)
                
                result = ModelEscalationTools.escalate_to_flagship(
                    task=task,
                    context=context,
                    issue=issue,
                    attempts=attempts,
                    model=model,
                    system_prompt=system_prompt,
                    max_tokens=max_tokens
                )
                return result
            elif mode == "check_complexity":
                # Use ModelEscalationTools.check_complexity
                context = kwargs.get("context")
                error_history = kwargs.get("error_history")
                result = ModelEscalationTools.check_complexity(
                    task=task,
                    context=context,
                    error_history=error_history
                )
                return result
            elif mode == "help":
                # Use ModelEscalationTools.get_flagship_help
                context = kwargs.get("context")
                model = kwargs.get("model", "deepseek")
                result = ModelEscalationTools.get_flagship_help(
                    issue=task,
                    context=context,
                    model=model
                )
                return result
            elif mode == "refine":
                # Use ModelEscalationTools.refine_with_flagship
                solution = kwargs.get("solution")
                if not solution:
                    return ToolResult(
                        success=False,
                        result=None,
                        error="solution required for mode='refine'"
                    )
                feedback = kwargs.get("feedback")
                improvements = kwargs.get("improvements")
                model = kwargs.get("model", "deepseek")
                
                result = ModelEscalationTools.refine_with_flagship(
                    solution=solution,
                    feedback=feedback,
                    improvements=improvements,
                    model=model
                )
                return result
            else:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Invalid mode: {mode}. Supported modes: 'consult', 'check_complexity', 'help', 'refine'"
                )
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error in model_escalate with mode '{mode}': {str(e)}"
            )

