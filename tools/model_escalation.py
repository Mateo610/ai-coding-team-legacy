"""
Model Escalation tools for agents to escalate complex tasks to flagship models
"""
import os
import json
import time
from typing import Dict, Any, Optional, List
from pathlib import Path

from tools.code_tools import ToolResult
from agents.timeout_config import TIMEOUT_CONFIG

# Try to import API clients
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

# DeepSeek might use OpenAI-compatible API or custom SDK
DEEPSEEK_AVAILABLE = False  # Will check based on API compatibility


class ModelEscalationTools:
    """Tools for escalating tasks to flagship models"""
    
    # Supported flagship models
    SUPPORTED_MODELS = {
        "deepseek": {
            "name": "DeepSeek",
            "api_base": "https://api.deepseek.com/v1",
            "available": False
        },
        "gpt4": {
            "name": "OpenAI GPT-4",
            "api_base": "https://api.openai.com/v1",
            "available": False
        },
        "claude": {
            "name": "Anthropic Claude",
            "api_base": "https://api.anthropic.com/v1",
            "available": False
        }
    }
    
    # Rate limiting (max 1 escalation per 30 seconds to prevent cost overruns)
    _last_escalation_time: float = 0
    _rate_limit_delay: float = 30.0
    
    # Cost tracking
    _escalation_count: int = 0
    _max_escalations: int = 10  # Max escalations per session
    
    @staticmethod
    def _check_rate_limit() -> tuple[bool, Optional[str]]:
        """Check if escalation rate limit allows"""
        current_time = time.time()
        time_since_last = current_time - ModelEscalationTools._last_escalation_time
        
        if time_since_last < ModelEscalationTools._rate_limit_delay:
            remaining = ModelEscalationTools._rate_limit_delay - time_since_last
            return False, f"Rate limit: wait {remaining:.1f}s before next escalation"
        
        if ModelEscalationTools._escalation_count >= ModelEscalationTools._max_escalations:
            return False, f"Max escalations ({ModelEscalationTools._max_escalations}) reached for this session"
        
        return True, None
    
    @staticmethod
    def _get_api_key(model_type: str) -> Optional[str]:
        """Get API key for flagship model from environment"""
        key_mapping = {
            "deepseek": ["DEEPSEEK_API_KEY", "FLAGSHIP_API_KEY"],
            "gpt4": ["OPENAI_API_KEY", "FLAGSHIP_API_KEY"],
            "claude": ["ANTHROPIC_API_KEY", "FLAGSHIP_API_KEY"]
        }
        
        keys_to_check = key_mapping.get(model_type, [])
        for key_name in keys_to_check:
            api_key = os.getenv(key_name)
            if api_key:
                return api_key
        
        return None
    
    @staticmethod
    def _call_deepseek_api(
        prompt: str,
        system_prompt: str = None,
        max_tokens: int = 4000
    ) -> tuple[bool, Optional[str], Optional[str]]:
        """Call DeepSeek API (OpenAI-compatible)"""
        try:
            api_key = ModelEscalationTools._get_api_key("deepseek")
            if not api_key:
                return False, None, "DeepSeek API key not found. Set DEEPSEEK_API_KEY environment variable."
            
            # DeepSeek uses OpenAI-compatible API
            if OPENAI_AVAILABLE:
                client = openai.OpenAI(
                    api_key=api_key,
                    base_url="https://api.deepseek.com/v1"
                )
                
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})
                
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=0.7
                )
                
                result = response.choices[0].message.content
                return True, result, None
            else:
                # Fallback: use requests directly
                import requests
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})
                
                data = {
                    "model": "deepseek-chat",
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": 0.7
                }
                
                response = requests.post(
                    "https://api.deepseek.com/v1/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()["choices"][0]["message"]["content"]
                    return True, result, None
                else:
                    return False, None, f"DeepSeek API error: {response.status_code} - {response.text[:200]}"
        
        except Exception as e:
            return False, None, f"Error calling DeepSeek API: {str(e)}"
    
    @staticmethod
    def _call_openai_api(
        prompt: str,
        system_prompt: str = None,
        max_tokens: int = 4000
    ) -> tuple[bool, Optional[str], Optional[str]]:
        """Call OpenAI GPT-4 API"""
        try:
            api_key = ModelEscalationTools._get_api_key("gpt4")
            if not api_key:
                return False, None, "OpenAI API key not found. Set OPENAI_API_KEY environment variable."
            
            if not OPENAI_AVAILABLE:
                return False, None, "OpenAI library not installed. Install with: pip install openai"
            
            client = openai.OpenAI(api_key=api_key)
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            result = response.choices[0].message.content
            return True, result, None
        
        except Exception as e:
            return False, None, f"Error calling OpenAI API: {str(e)}"
    
    @staticmethod
    def _call_claude_api(
        prompt: str,
        system_prompt: str = None,
        max_tokens: int = 4000
    ) -> tuple[bool, Optional[str], Optional[str]]:
        """Call Anthropic Claude API"""
        try:
            api_key = ModelEscalationTools._get_api_key("claude")
            if not api_key:
                return False, None, "Anthropic API key not found. Set ANTHROPIC_API_KEY environment variable."
            
            if not ANTHROPIC_AVAILABLE:
                return False, None, "Anthropic library not installed. Install with: pip install anthropic"
            
            client = anthropic.Anthropic(api_key=api_key)
            
            # Build messages
            system_msg = system_prompt if system_prompt else "You are a helpful coding assistant."
            message_content = prompt
            
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=max_tokens,
                system=system_msg,
                messages=[
                    {"role": "user", "content": message_content}
                ]
            )
            
            result = response.content[0].text
            return True, result, None
        
        except Exception as e:
            return False, None, f"Error calling Claude API: {str(e)}"
    
    @staticmethod
    def escalate_to_flagship(
        task: str,
        context: str = None,
        issue: str = None,
        attempts: str = None,
        model: str = "deepseek",
        system_prompt: str = None,
        max_tokens: int = 4000
    ) -> ToolResult:
        """
        Escalate task to flagship model for complex problems.
        
        Args:
            task: Original task description
            context: Relevant context (code, errors, etc.)
            issue: What's wrong or complex about this task
            attempts: What was already tried
            model: Flagship model to use ("deepseek", "gpt4", "claude") (default: "deepseek")
            system_prompt: Custom system prompt (optional)
            max_tokens: Maximum tokens for response (default: 4000)
        
        Returns:
            ToolResult with flagship model response
        """
        try:
            # Check if enabled
            enabled = os.getenv("FLAGSHIP_MODEL_ENABLED", "false").lower() == "true"
            if not enabled:
                return ToolResult(
                    success=False,
                    result=None,
                    error="Flagship model escalation is disabled. Set FLAGSHIP_MODEL_ENABLED=true to enable."
                )
            
            # Check rate limit
            can_escalate, error_msg = ModelEscalationTools._check_rate_limit()
            if not can_escalate:
                return ToolResult(
                    success=False,
                    result=None,
                    error=error_msg
                )
            
            # Build prompt for flagship model
            prompt_parts = []
            prompt_parts.append(f"Task: {task}")
            
            if context:
                prompt_parts.append(f"\nContext:\n{context}")
            
            if issue:
                prompt_parts.append(f"\nIssue:\n{issue}")
            
            if attempts:
                prompt_parts.append(f"\nPrevious Attempts:\n{attempts}")
            
            prompt_parts.append("\n\nPlease provide a complete solution to this task.")
            prompt = "\n".join(prompt_parts)
            
            # Default system prompt if not provided
            if not system_prompt:
                system_prompt = """You are an expert coding assistant. Provide clear, complete, and production-ready solutions.
Include code examples, explanations, and best practices. Be thorough and accurate."""
            
            # Normalize model name
            model = model.lower()
            if model not in ModelEscalationTools.SUPPORTED_MODELS:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Unsupported model: {model}. Supported: {list(ModelEscalationTools.SUPPORTED_MODELS.keys())}"
                )
            
            # Call appropriate API
            success = False
            result = None
            error = None
            
            if model == "deepseek":
                success, result, error = ModelEscalationTools._call_deepseek_api(
                    prompt, system_prompt, max_tokens
                )
            elif model == "gpt4":
                success, result, error = ModelEscalationTools._call_openai_api(
                    prompt, system_prompt, max_tokens
                )
            elif model == "claude":
                success, result, error = ModelEscalationTools._call_claude_api(
                    prompt, system_prompt, max_tokens
                )
            
            if not success:
                return ToolResult(
                    success=False,
                    result=None,
                    error=error or "Failed to call flagship model"
                )
            
            # Update rate limiting
            ModelEscalationTools._last_escalation_time = time.time()
            ModelEscalationTools._escalation_count += 1
            
            return ToolResult(
                success=True,
                result={
                    "solution": result,
                    "model": model,
                    "task": task,
                    "context": context,
                    "issue": issue
                },
                metadata={
                    "model": model,
                    "escalation_count": ModelEscalationTools._escalation_count,
                    "tokens_estimated": len(result) // 4  # Rough estimate
                }
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error escalating to flagship model: {str(e)}"
            )
    
    @staticmethod
    def check_complexity(
        task: str,
        context: str = None,
        error_history: List[str] = None
    ) -> ToolResult:
        """
        Check if task is too complex for current model.
        
        Args:
            task: Task description
            context: Relevant context
            error_history: List of errors encountered (optional)
        
        Returns:
            ToolResult with complexity assessment
        """
        try:
            # Simple heuristics for complexity detection
            complexity_indicators = {
                "complex_keywords": [
                    "architecture", "distributed", "microservices", "scalable",
                    "optimize", "performance", "concurrent", "parallel",
                    "advanced", "sophisticated", "enterprise", "production-grade"
                ],
                "error_patterns": [
                    "timeout", "memory", "performance", "race condition",
                    "deadlock", "concurrency", "scalability"
                ]
            }
            
            task_lower = task.lower()
            context_lower = (context or "").lower()
            combined_text = f"{task_lower} {context_lower}"
            
            # Count complexity indicators
            complexity_score = 0
            found_indicators = []
            
            for keyword in complexity_indicators["complex_keywords"]:
                if keyword in combined_text:
                    complexity_score += 1
                    found_indicators.append(keyword)
            
            # Check error history
            if error_history:
                for error in error_history:
                    error_lower = error.lower()
                    for pattern in complexity_indicators["error_patterns"]:
                        if pattern in error_lower:
                            complexity_score += 2  # Errors are stronger indicators
                            found_indicators.append(f"error:{pattern}")
            
            # Determine complexity level
            if complexity_score >= 5:
                complexity_level = "very_high"
                recommendation = "escalate"
            elif complexity_score >= 3:
                complexity_level = "high"
                recommendation = "consider_escalating"
            elif complexity_score >= 1:
                complexity_level = "medium"
                recommendation = "may_need_escalation"
            else:
                complexity_level = "low"
                recommendation = "no_escalation_needed"
            
            return ToolResult(
                success=True,
                result={
                    "complexity_level": complexity_level,
                    "complexity_score": complexity_score,
                    "indicators": list(set(found_indicators)),
                    "recommendation": recommendation
                },
                metadata={
                    "score": complexity_score,
                    "level": complexity_level
                }
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error checking complexity: {str(e)}"
            )
    
    @staticmethod
    def get_flagship_help(
        issue: str,
        context: str = None,
        model: str = "deepseek"
    ) -> ToolResult:
        """
        Get help from flagship model for specific issue.
        
        Args:
            issue: Specific issue or question
            context: Relevant context
            model: Flagship model to use (default: "deepseek")
        
        Returns:
            ToolResult with help/solution
        """
        prompt = f"I need help with: {issue}"
        if context:
            prompt += f"\n\nContext:\n{context}"
        
        prompt += "\n\nPlease provide a clear, helpful solution or explanation."
        
        return ModelEscalationTools.escalate_to_flagship(
            task=issue,
            context=context,
            model=model,
            system_prompt="You are a helpful coding assistant. Provide clear, concise, and accurate help."
        )
    
    @staticmethod
    def refine_with_flagship(
        solution: str,
        feedback: str = None,
        improvements: List[str] = None,
        model: str = "deepseek"
    ) -> ToolResult:
        """
        Refine solution using flagship model.
        
        Args:
            solution: Current solution to refine
            feedback: Feedback on current solution
            improvements: List of improvements to make
            model: Flagship model to use (default: "deepseek")
        
        Returns:
            ToolResult with refined solution
        """
        prompt = f"Current Solution:\n{solution}\n\n"
        
        if feedback:
            prompt += f"Feedback:\n{feedback}\n\n"
        
        if improvements:
            prompt += f"Improvements Needed:\n" + "\n".join(f"- {imp}" for imp in improvements) + "\n\n"
        
        prompt += "Please provide an improved, refined version of this solution."
        
        return ModelEscalationTools.escalate_to_flagship(
            task="Refine solution",
            context=solution,
            issue=feedback or "Improve solution",
            model=model,
            system_prompt="You are an expert code reviewer. Refine and improve solutions to be production-ready."
        )

