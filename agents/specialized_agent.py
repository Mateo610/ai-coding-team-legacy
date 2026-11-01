"""
Base class for specialized agents (Implementation, Validation, etc.)
"""

import os
import yaml
import requests
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from tools.code_tools import TOOL_REGISTRY, get_tool
from tools.consolidated import TOOL_REGISTRY_CONSOLIDATED, get_tool_registry as get_consolidated_registry
from tools.consolidated.migration import migrate_tool_call, is_old_tool
from agents.exceptions import (
    AgentError,
    ModelConnectionError,
    ModelTimeoutError,
    ToolExecutionError,
    RetryableError,
    ConfigurationError,
)
from agents.timeout_config import TIMEOUT_CONFIG
from agents.config_manager import CONFIG_MANAGER, ConfigManager
from agents.prompt_builder import PromptBuilder
from agents.skill_manager import SKILL_MANAGER, SkillManager

load_dotenv('config/.env')

class SpecializedAgent:
    """
    Base agent that can be specialized with skills
    """
    
    def __init__(self, 
                 name: str,
                 role: str,
                 model_config_key: str = 'implementation',
                 skill_file: Optional[str] = None,
                 additional_skills: Optional[list] = None,
                 config_manager: ConfigManager = None):
        """
        Args:
            name: Agent name
            role: Agent role description
            model_config_key: Key in models.yaml
            skill_file: Path to primary skill file in .aiconfig/skills/
            additional_skills: List of additional skill files to load
            config_manager: Optional ConfigManager instance (default: uses CONFIG_MANAGER)
        """
        
        self.name = name
        self.role = role
        
        # Use provided config manager or singleton
        self.config_manager = config_manager or CONFIG_MANAGER
        
        # Get model configuration
        model_config_obj = self.config_manager.get_model_config(model_config_key)
        if not model_config_obj:
            raise ConfigurationError(f"Model configuration '{model_config_key}' not found")
        
        self.model = model_config_obj.name
        self.temperature = model_config_obj.temperature
        self.max_tokens = model_config_obj.max_tokens
        
        self.base_url = self.config_manager.get_ollama_base_url()
        
        # Store skill configuration for static loading (backward compatibility)
        self.primary_skill_file = skill_file
        self.additional_skill_files = additional_skills or []
        
        # Load primary skill statically (for backward compatibility)
        if skill_file:
            self.primary_skill = self._load_skill(skill_file)
        else:
            self.primary_skill = ""
        
        # Initialize skill manager and prompt builder
        self.skill_manager = SKILL_MANAGER
        self.prompt_builder = PromptBuilder()
        
        # Dynamic skills will be loaded per task in execute()
        self.current_skills = None
        self.skill = None  # Will be set dynamically
    
    def _load_skill(self, skill_file: str) -> str:
        """Load specialized knowledge from skill file"""
        skill_path = Path('.aiconfig') / 'skills' / skill_file
        
        if skill_path.exists():
            return skill_path.read_text()
        return ""
    
    def _calculate_dynamic_max_tokens(self, task_type: Optional[str], base_max_tokens: int) -> int:
        """
        Calculate dynamic max_tokens based on task type and complexity.
        
        Complex tasks (API, database, crud) need more tokens for complete code generation.
        Simple tasks (algorithm, general) can use base limits.
        
        Args:
            task_type: Detected task type (crud, api, algorithm, database, etc.)
            base_max_tokens: Base token limit from model config
            
        Returns:
            Adjusted max_tokens for this task
        """
        # Token multipliers for different task types
        # Complex tasks typically generate more code (multiple functions, classes, etc.)
        token_multipliers = {
            'api': 2.5,        # API endpoints often need multiple routes, validation, auth
            'database': 2.5,    # Database models need models, relationships, migrations
            'crud': 2.0,       # CRUD operations need multiple functions
            'etl': 2.5,        # ETL pipelines need extract, transform, load functions
            'data_analysis': 2.0,  # Data analysis tasks need multiple processing steps
            'frontend': 2.0,   # Frontend code can be verbose (HTML, CSS, JS)
            'devops': 2.0,     # DevOps configs can be long (Docker, CI/CD, etc.)
            'algorithm': 1.2,  # Algorithms are usually single functions
            'test': 1.5,       # Tests need multiple test cases
            'general': 1.0,    # General tasks use base limit
        }
        
        # Get multiplier for this task type
        multiplier = token_multipliers.get(task_type or 'general', 1.0)
        
        # Calculate adjusted tokens
        adjusted_tokens = int(base_max_tokens * multiplier)
        
        # Cap at reasonable maximum (avoid excessive tokens)
        max_allowed = 12000  # Maximum tokens for any task
        min_allowed = base_max_tokens  # Never go below base
        
        final_tokens = max(min_allowed, min(adjusted_tokens, max_allowed))
        
        return final_tokens
    
    def execute(self,
                task: str,
                context: str = "",
                use_tools: bool = True,
                task_type: Optional[str] = None,
                context_dict: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Execute agent's task with optional tool usage
        
        Args:
            task: Task description
            context: Context string (structured context from ContextManager)
            use_tools: Whether to enable tools
            task_type: Detected task type (crud, api, algorithm, etc.)
            context_dict: Optional context dictionary for SkillManager
        
        Returns:
            {
                'output': str,
                'tool_calls': list,
                'tokens_used': int
            }
        """

        print(f"\n👤 {self.name} working...")

        # Load skills dynamically based on task
        try:
            # Detect task type if not provided
            if not task_type:
                task_type = self.prompt_builder.context_manager.detect_task_type(task)
            
            # Extract dependencies from context if available
            context_dict = context_dict or {}
            
            # Calculate dynamic max_tokens based on task type
            effective_max_tokens = self._calculate_dynamic_max_tokens(task_type, self.max_tokens)
            if effective_max_tokens != self.max_tokens:
                print(f"   🔧 Adjusted max_tokens: {self.max_tokens} → {effective_max_tokens} (task_type: {task_type})")
            
            # Get relevant skills from SkillManager
            # Reserve tokens: primary skill + dynamic skills within budget
            primary_skill_tokens = len(self.primary_skill) // 4 if self.primary_skill else 0
            max_dynamic_tokens = 8000 - primary_skill_tokens  # Reserve space for primary skill
            
            relevant_skill_names, skill_tokens = self.skill_manager.get_relevant_skills(
                task=task,
                task_type=task_type,
                context=context_dict,
                max_tokens=max_dynamic_tokens
            )
            
            # Load dynamic skills
            dynamic_skills_content = self.skill_manager.load_skills(relevant_skill_names)
            
            # Combine primary skill + dynamic skills
            all_skills = []
            if self.primary_skill:
                all_skills.append(self.primary_skill)
            if dynamic_skills_content:
                all_skills.append(dynamic_skills_content)
            
            self.skill = "\n\n".join(filter(None, all_skills))
            self.current_skills = relevant_skill_names
            
            if relevant_skill_names:
                print(f"   📚 Loaded {len(relevant_skill_names)} relevant skills: {', '.join(relevant_skill_names[:3])}{'...' if len(relevant_skill_names) > 3 else ''}")
            
        except Exception as e:
            # Fallback to static skill loading on error
            print(f"   ⚠️  Dynamic skill loading failed, using static skills: {e}")
            skills = []
            if self.primary_skill:
                skills.append(self.primary_skill)
            if self.additional_skill_files:
                for skill_file in self.additional_skill_files:
                    skill_content = self._load_skill(skill_file)
                    if skill_content:
                        skills.append(skill_content)
            self.skill = "\n\n".join(filter(None, skills))
            # Use base max_tokens if dynamic calculation failed
            effective_max_tokens = self.max_tokens

        # Pass tools if enabled - prefer consolidated tools for cleaner prompts
        if use_tools:
            # Use consolidated tools for prompts (cleaner, fewer tokens)
            # Old tools still work via migration layer in execution
            try:
                tools = TOOL_REGISTRY_CONSOLIDATED.copy()
            except (ImportError, AttributeError):
                # Fallback to full registry if consolidated tools unavailable
                tools = TOOL_REGISTRY.copy()
        else:
            tools = None

        try:
            # Build system prompt
            try:
                system_prompt = self._build_system_prompt(context, tools)
            except Exception as e:
                raise AgentError(f"Failed to build system prompt: {str(e)}")

            # Get timeout from configuration
            model_timeout = TIMEOUT_CONFIG.get_model_request_timeout()
            streaming_timeout = TIMEOUT_CONFIG.get_model_streaming_timeout()
            
            # Call model with streaming to get complete output
            try:
                response = requests.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": task},
                        ],
                        "stream": True,  # Enable streaming
                        "options": {
                            "temperature": self.temperature,
                            "num_predict": effective_max_tokens,  # Use dynamic token limit
                        },
                    },
                    stream=True,  # Enable streaming
                    timeout=model_timeout
                )
                response.raise_for_status()  # Raise exception for HTTP errors
            except requests.exceptions.Timeout:
                raise ModelTimeoutError(f"Model request timed out after {model_timeout}s")
            except requests.exceptions.ConnectionError as e:
                raise ModelConnectionError(f"Failed to connect to model at {self.base_url}: {str(e)}")
            except requests.exceptions.HTTPError as e:
                raise ModelConnectionError(f"HTTP error from model: {str(e)}")
            except requests.exceptions.RequestException as e:
                raise ModelConnectionError(f"Request error: {str(e)}")

            # Collect streamed response - ensure we get everything
            full_output = ""
            done = False
            streaming_start_time = time.time()
            
            try:
                for line in response.iter_lines(decode_unicode=True):
                    # Check streaming timeout
                    elapsed = time.time() - streaming_start_time
                    if elapsed > streaming_timeout:
                        raise ModelTimeoutError(f"Streaming collection timed out after {streaming_timeout}s")
                    
                    if not line or done:
                        continue
                    try:
                        chunk = json.loads(line)
                    except json.JSONDecodeError:
                        # Skip invalid JSON chunks
                        continue

                    # Collect content from message chunks
                    if "message" in chunk:
                        content = chunk["message"].get("content", "")
                        if content:
                            full_output += content
                    
                    # Check if this is the final chunk
                    if chunk.get("done", False):
                        # Get final content if present
                        if "message" in chunk and "content" in chunk["message"]:
                            full_output += chunk["message"]["content"]
                        done = True
                        break
            except ModelTimeoutError:
                # Re-raise timeout errors
                raise
            except Exception as e:
                # If streaming fails, log but continue with what we have
                print(f"      ⚠️  Streaming issue: {e}")
                if not full_output:
                    raise AgentError(f"Streaming failed and no output collected: {str(e)}")

            output = full_output
            
            # Parse tool calls if any
            try:
                tool_calls = self._parse_tool_calls(output, tools)
            except Exception as e:
                print(f"      ⚠️  Tool parsing failed: {str(e)}")
                tool_calls = []
            
            # Execute tools (non-critical, continue on error)
            tool_results = []
            if tool_calls and tools:
                try:
                    tool_results = self._execute_tools(tool_calls, tools)
                    
                    # Add tool results to output
                    if tool_results:
                        output += "\n\nTOOL RESULTS:\n" + "\n".join(
                            f"- {r['tool']}: {r.get('result', 'N/A')}" for r in tool_results
                        )
                except Exception as e:
                    print(f"      ⚠️  Tool execution failed: {str(e)}")
                    # Continue without tool results
            
            print(f"   ✓ {self.name} complete")
            
            return {
                "output": output,
                "tool_calls": tool_results,
                "tokens_used": 0,
                "metadata": {
                    "agent": self.name,
                    "model": self.model,
                },
            }
            
        except (ModelConnectionError, ModelTimeoutError, AgentError):
            # Re-raise known exceptions
            raise
        except Exception as e:
            # Wrap unexpected errors
            raise AgentError(f"{self.name} execution failed: {str(e)}", details={
                "agent": self.name,
                "model": self.model,
                "error_type": type(e).__name__,
            })
    
    def _build_system_prompt(self, context: str, tools: Optional[Dict]) -> str:
        """
        Build optimized system prompt using PromptBuilder.
        Falls back to simple prompt if PromptBuilder fails or for non-implementation agents.
        """
        try:
            # Use PromptBuilder for Implementation Agent
            if self.name == "Implementation Agent":
                # Detect task type from context or task (if available)
                task_type = None
                if context:
                    # Try to detect task type from context
                    task_type = self.prompt_builder.context_manager.detect_task_type(context[:500])
                
                # Build optimized prompt
                prompt = self.prompt_builder.build_implementation_prompt(
                    task="",  # Task will be in user message
                    context=context,
                    task_type=task_type,
                    agent_skills=self.skill
                )
                
                # Add tools if available
                if tools:
                    prompt = self._add_tools_to_prompt(prompt, tools)
                
                return prompt
            
            elif self.name == "Test Generator":
                # Use PromptBuilder for TestGeneratorAgent
                return self.prompt_builder.build_test_generator_prompt(
                    agent_name=self.name,
                    agent_role=self.role,
                    skill_content=self.skill,
                    context=context,
                    tools=tools
                )
            
            elif self.name == "Validation Agent":
                # For validation, use enhanced simple prompt
                return self._build_enhanced_simple_prompt(context, tools)
            
            else:
                # For other agents, use enhanced simple prompt
                return self._build_enhanced_simple_prompt(context, tools)
                
        except Exception as e:
            # Fallback to simple prompt on error
            print(f"   ⚠️  Prompt builder failed, using simple prompt: {e}")
            return self._build_enhanced_simple_prompt(context, tools)
    
    def _build_enhanced_simple_prompt(self, context: str, tools: Optional[Dict]) -> str:
        """Build enhanced simple prompt (fallback)"""
        parts = [f"You are {self.role}."]
        
        # Add skill if available
        if self.skill:
            parts.append(f"\nSPECIALIZED KNOWLEDGE:\n{self.skill}")
        
        # Add context with structure awareness
        if context:
            # Check if context has sections
            if "PROJECT RULES:" in context or "ARCHITECTURE:" in context:
                parts.append(f"\nCONTEXT:\n{context}")
                parts.append("\nIMPORTANT: Follow PROJECT RULES section strictly. Use RELEVANT CODE section for patterns.")
            else:
                parts.append(f"\nCONTEXT:\n{context}")
        
        # Add tool instructions - prefer consolidated tools
        if tools:
            # Use consolidated tools if available for cleaner prompts
            tools_to_show = tools
            try:
                if TOOL_REGISTRY_CONSOLIDATED:
                    tools_to_show = TOOL_REGISTRY_CONSOLIDATED
            except (NameError, AttributeError):
                pass  # Use provided tools if consolidated not available
            
            tool_list = "\n".join(f"- {name}: {info['description']}" 
                                 for name, info in tools_to_show.items())
            parts.append(f"\nAVAILABLE TOOLS:\n{tool_list}")
            parts.append("""
To use a tool, output:
TOOL: tool_name
INPUT: {"param1": "value1", "param2": "value2"}

You can use multiple tools by repeating this format.
Note: Old tool names are automatically migrated to new consolidated tools during execution.""")
        
        return "\n".join(parts)
    
    def _add_tools_to_prompt(self, prompt: str, tools: Dict) -> str:
        """Add tool instructions to prompt (prefers consolidated tools)"""
        # Use consolidated tools if available for cleaner prompts
        tools_to_show = tools
        try:
            if TOOL_REGISTRY_CONSOLIDATED:
                tools_to_show = TOOL_REGISTRY_CONSOLIDATED
        except (NameError, AttributeError):
            pass  # Use provided tools if consolidated not available
        
        tool_list = "\n".join(f"- {name}: {info['description']}" 
                             for name, info in tools_to_show.items())
        tool_instructions = f"""

AVAILABLE TOOLS:
{tool_list}

To use a tool, output:
TOOL: tool_name
INPUT: {{"param1": "value1", "param2": "value2"}}

You can use multiple tools by repeating this format.
Note: Old tool names are automatically migrated to new consolidated tools during execution."""
        
        return prompt + tool_instructions
    
    def _parse_tool_calls(self, output: str, tools: Optional[Dict]) -> list:
        """Parse tool calls from agent output"""
        
        if not tools or "TOOL:" not in output:
            return []
        
        tool_calls = []
        lines = output.split('\n')
        
        i = 0
        while i < len(lines):
            if lines[i].startswith('TOOL:'):
                tool_name = lines[i].replace('TOOL:', '').strip()
                tool_input = ""
                
                # Get input on next line
                if i + 1 < len(lines) and lines[i + 1].startswith('INPUT:'):
                    tool_input = lines[i + 1].replace('INPUT:', '').strip()
                
                if tool_name in tools:
                    tool_calls.append({
                        'tool': tool_name,
                        'input': tool_input
                    })
                
                i += 2
            else:
                i += 1
        
        return tool_calls
    
    def _execute_tools(self, tool_calls: list, tools: Dict) -> list:
        """
        Execute tool calls and return results.
        Automatically migrates old tool names to new consolidated tools.
        """
        
        results = []
        
        for call in tool_calls:
            tool_name = call['tool']
            tool_input = call['input']
            
            # Parse tool input (could be string or dict)
            if isinstance(tool_input, str):
                # Try to parse as JSON if it looks like JSON
                import json
                try:
                    tool_input = json.loads(tool_input)
                except (json.JSONDecodeError, ValueError):
                    # Not JSON, treat as string parameter
                    tool_input = {"file_path": tool_input} if tool_input else {}
            elif not isinstance(tool_input, dict):
                tool_input = {}
            
            print(f"   🔧 Using tool: {tool_name}")
            
            try:
                # Check if this is an old tool name - migrate if needed
                if is_old_tool(tool_name):
                    new_name, new_kwargs = migrate_tool_call(tool_name, **tool_input)
                    print(f"      → Migrated to: {new_name}")
                    tool_name = new_name
                    tool_input = new_kwargs
                
                # Get tool function (supports both old and new names)
                tool_func = get_tool(tool_name)
                
                if tool_func is None:
                    # Try direct registry lookup
                    if tool_name in TOOL_REGISTRY:
                        tool_func = TOOL_REGISTRY[tool_name]['function']
                    elif tool_name in TOOL_REGISTRY_CONSOLIDATED:
                        tool_func = TOOL_REGISTRY_CONSOLIDATED[tool_name]['function']
                    else:
                        raise ValueError(f"Tool '{tool_name}' not found")
                
                # Execute tool with parsed input
                if isinstance(tool_input, dict) and tool_input:
                    result = tool_func(**tool_input)
                else:
                    # Fallback: try as single argument
                    result = tool_func(tool_input if tool_input else "")
                
                results.append({
                    'tool': tool_name,
                    'input': tool_input,
                    'result': result,
                    'success': True
                })
            except Exception as e:
                results.append({
                    'tool': tool_name,
                    'input': tool_input,
                    'result': str(e),
                    'success': False
                })
        
        return results


class ImplementationAgent(SpecializedAgent):
    """Agent specialized in writing code"""
    
    def __init__(self):
        super().__init__(
            name="Implementation Agent",
            role="a senior software engineer who writes clean, well-tested code",
            model_config_key='implementation',
            skill_file='implementation.md',
            additional_skills=[
                'error_handling.md',
                'python_idioms.md',
                'type_hints_patterns.md',
                'security_best_practices.md',
                'common_algorithms.md',
                'design_patterns.md',
                'testing_patterns.md',
                'documentation_patterns.md',
                'code_organization.md',
                'performance_optimization.md',
                'logging_patterns.md',
                'api_design.md'
            ]
        )


class ValidationAgent(SpecializedAgent):
    """Agent specialized in code review and testing"""
    
    def __init__(self):
        super().__init__(
            name="Validation Agent",
            role="a senior code reviewer who checks for bugs, security issues, and best practices",
            model_config_key='validation',
            skill_file='validation.md',
            additional_skills=[
                'error_handling.md',
                'security_best_practices.md',
                'type_hints_patterns.md',
                'python_idioms.md',
                'testing_patterns.md',
                'documentation_patterns.md',
                'code_organization.md',
                'debugging_patterns.md',
                'performance_optimization.md',
                'logging_patterns.md'
            ]
        )


class TestGeneratorAgent(SpecializedAgent):
    """Agent specialized in generating and running tests"""

    def __init__(self):
        super().__init__(
            name="Test Generator",
            role="a QA engineer who writes comprehensive tests",
            model_config_key="orchestrator",  # Use 14B model
            additional_skills=[
                'error_handling.md',
                'python_idioms.md',
                'common_algorithms.md',
                'testing_patterns.md',
                'documentation_patterns.md',
                'debugging_patterns.md'
            ]
        )
        # Override max_tokens for test generation (need more tokens for complete tests)
        self.max_tokens = 8000  # Increased for complete test generation
    
    def _validate_test_completeness(self, test_code: str):
        """
        Validate that generated test code is complete.
        Returns: (is_complete, error_message)
        """
        from tools.code_tools import CodeTools
        
        extracted = CodeTools._extract_code(test_code)
        lines = extracted.split('\n')
        
        # Check for incomplete assert statements
        for i, line in enumerate(lines):
            stripped = line.strip()
            # Check if assert statement is incomplete
            if stripped.startswith('assert ') and not (stripped.endswith(':') or stripped.endswith(',')):
                # Check if next line continues the assert
                if i + 1 < len(lines):
                    next_stripped = lines[i + 1].strip()
                    if not next_stripped or next_stripped.startswith('#'):
                        # Check if assert looks incomplete
                        if stripped.count('(') > stripped.count(')'):
                            return False, f"Incomplete assert statement at line {i+1}: {stripped[:50]}"
                        # Check if assert ends with comparison operator
                        if any(stripped.endswith(op) for op in ['==', '!=', '<', '>', '<=', '>=', 'in', 'not']):
                            return False, f"Incomplete assert statement at line {i+1}: {stripped[:50]}"
                else:
                    # Last line is an incomplete assert
                    if any(stripped.endswith(op) for op in ['==', '!=', '<', '>', '<=', '>=', 'in', 'not']):
                        return False, f"Incomplete assert statement at end: {stripped[:50]}"
        
        # Check syntax
        syntax_check = CodeTools.check_syntax(extracted)
        if not syntax_check.success:
            return False, f"Syntax error: {syntax_check.error}"
        
        # Check that test functions have at least one assert
        import ast
        try:
            tree = ast.parse(extracted)
            test_functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name.startswith('test_')]
            
            for func in test_functions:
                has_assert = any(isinstance(node, ast.Assert) for node in ast.walk(func))
                if not has_assert:
                    return False, f"Test function '{func.name}' has no assert statements"
        except:
            pass  # If AST parsing fails, syntax check already caught it
        
        # Check for incomplete function definitions
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('def test_'):
                # Check if function body is empty
                if i + 1 < len(lines):
                    next_stripped = lines[i + 1].strip()
                    # Check if function is just a signature with no body
                    if next_stripped and not (next_stripped.startswith(' ') or next_stripped.startswith('\t') or next_stripped.startswith('#')):
                        # Next line at module level - function has no body
                        return False, f"Test function at line {i+1} has no body: {stripped[:50]}"
        
        return True, ""
    

    def validate_code(self, code: str, original_task: str) -> Dict[str, Any]:
        """
        Validate code by:
        1. Checking syntax
        2. Running the code
        3. Generating tests
        4. Running tests
        """
        from tools.code_tools import CodeTools

        print(f"\n🧪 {self.name} validating code...")

        results = {
            "syntax_check": None,
            "execution": None,
            "tests_generated": None,
            "tests_run": None,
            "overall_success": False,
        }

        # Step 1: Syntax check
        print("   📝 Checking syntax...")
        syntax_result = CodeTools.check_syntax(code)
        results["syntax_check"] = syntax_result.to_dict()

        if not syntax_result.success:
            print(f"      ✗ Syntax invalid: {syntax_result.error}")
            return results
        print("      ✓ Syntax valid")

        # Step 2: Try to execute
        print("   ▶️  Executing code...")
        exec_result = CodeTools.execute_code(code)
        results["execution"] = exec_result.to_dict()

        if exec_result.success:
            print("      ✓ Executed successfully")
        else:
            print(f"      ⚠️  Execution issues: {exec_result.error[:100]}")

        # Step 3: Generate tests
        print("   🧪 Generating tests...")
        function_code = CodeTools._extract_code(code)
        
        test_task = f"""Write complete pytest tests for this Python function. CRITICAL: Output ONLY valid Python code, no explanations, no markdown except code blocks.

Function to test:
```python
{function_code}
```

REQUIREMENTS:
1. Include the original function definition
2. Write 3-5 complete test functions with names starting with "test_"
3. Each test must have complete assert statements (no incomplete lines)
4. Import pytest if needed
5. Output format: wrap code in ```python block

Example format:
```python
{function_code}

import pytest

def test_normal_case():
    assert function_name(2, 3) == 5

def test_edge_case():
    assert function_name(0, 0) == 0

def test_negative():
    assert function_name(-1, -2) == -3
```

Write tests for: {original_task}"""

        test_response = self.execute(
            task=test_task,
            context="You are a QA engineer. Output ONLY complete, runnable pytest test code. No explanations outside code blocks.",
            use_tools=False,  # Don't need tools for generation
        )

        test_code = test_response["output"]

        # Validate and potentially retry for complete test code
        max_retries = 2
        retry_count = 0
        
        while True:
            test_count = test_code.count("def test_")
            
            # Validate completeness
            is_complete, completeness_error = self._validate_test_completeness(test_code)
            extracted_test = CodeTools._extract_code(test_code)
            syntax_check = CodeTools.check_syntax(extracted_test)
            
            print(f"\n   DEBUG - Generated tests:\n{test_code[:800]}\n")
            print(f"   DEBUG - Found {test_count} test functions")
            
            # Check if we have issues
            if test_count == 0:
                if retry_count < max_retries:
                    print(f"      ⚠️  No tests generated (attempt {retry_count + 1}/{max_retries + 1}), retrying...")
                    retry_task = f"""Write 2 simple pytest test functions for this code. Output complete runnable Python code only.

```python
{function_code}
```

Output format:
```python
{function_code}

def test_basic():
    assert function_name(arg1, arg2) == expected

def test_edge():
    assert function_name(edge_arg1, edge_arg2) == expected
```"""
                    retry_response = self.execute(
                        task=retry_task,
                        context="Output ONLY complete Python code with tests. No explanations.",
                        use_tools=False,
                    )
                    test_code = retry_response["output"]
                    retry_count += 1
                    continue
                else:
                    print("      ✗ Failed to generate tests after retries")
            elif not is_complete or not syntax_check.success:
                if retry_count < max_retries:
                    error_msg = completeness_error if not is_complete else syntax_check.error
                    print(f"      ⚠️  Incomplete/invalid tests detected: {error_msg[:100]} (attempt {retry_count + 1}/{max_retries + 1}), retrying...")
                    
                    # Retry with emphasis on completeness - but only if we have NO valid tests
                    if test_count == 0:
                        # No tests at all - retry
                        retry_task = f"""Fix and complete the pytest tests. The generated code was incomplete.

Function to test:
```python
{function_code}
```

Previous attempt had issues: {error_msg[:200]}

Write COMPLETE pytest tests. Each test function must:
1. Have a complete assert statement (no incomplete lines)
2. Be syntactically valid
3. Start with 'def test_'

Output complete runnable Python code only."""
                        retry_response = self.execute(
                            task=retry_task,
                            context="Output ONLY complete, syntactically valid pytest test code. Every assert must be complete.",
                            use_tools=False,
                        )
                        test_code = retry_response["output"]
                        retry_count += 1
                        continue
                    else:
                        # We have some tests, just some are incomplete - accept partial results
                        print(f"      ⚠️  Some tests incomplete, but have {test_count} test functions. Proceeding with available tests.")
                        break  # Exit retry loop - proceed with what we have
                elif retry_count >= max_retries:
                    # Max retries reached
                    print(f"      ⚠️  Tests still incomplete after {max_retries} retries, proceeding with what we have")
                    break  # Exit retry loop - proceed with what we have
                else:
                    # Should retry but haven't yet - this shouldn't happen, but break anyway
                    break
            else:
                # Tests look good!
                if not syntax_check.success:
                    # Try to fix by extracting just the code
                    extracted_test = CodeTools._extract_code(test_code)
                    syntax_check = CodeTools.check_syntax(extracted_test)
                    if syntax_check.success:
                        test_code = extracted_test
                        print("      ✓ Fixed by extracting code from markdown")
                break  # Success - exit retry loop
        
        # Final validation
        is_complete, _ = self._validate_test_completeness(test_code)
        
        results["tests_generated"] = {
            "code": test_code,
            "test_count": test_count,
            "syntax_valid": syntax_check.success,
            "is_complete": is_complete,
            "retries": retry_count,
        }
        print("      ✓ Tests generated")

        # Step 4: Run tests
        print("   🏃 Running tests...")
        test_result = CodeTools.run_tests(code, test_code)
        results["tests_run"] = test_result.to_dict()
        
        # Show detailed error if tests failed to run
        if not test_result.success:
            error_msg = test_result.error or ""
            metadata = test_result.metadata or {}
            
            # Show comprehensive error information
            if metadata.get("pytest_missing"):
                print(f"      ⚠️  pytest is not installed!")
                if metadata.get("install_hint"):
                    print(f"      💡 Install with: {metadata['install_hint']}")
                if error_msg:
                    print(f"      Error: {error_msg[:200]}")
            elif metadata.get("collection_error") or metadata.get("no_tests") or metadata.get("syntax_error"):
                print(f"      ⚠️  Test execution issue:")
                if error_msg:
                    # Show first 10 lines of error
                    error_lines = [line for line in error_msg.split('\n') if line.strip()][:10]
                    for line in error_lines:
                        print(f"         {line[:120]}")
            
            # Show full pytest output if available
            if metadata.get("full_output"):
                full_output = metadata["full_output"]
                # Extract key error lines
                output_lines = full_output.split('\n')
                
                # Find error/traceback sections
                error_start = None
                for i, line in enumerate(output_lines):
                    if 'ERROR' in line or 'Error' in line or 'Traceback' in line:
                        error_start = i
                        break
                
                if error_start:
                    print(f"      🔍 Error details:")
                    # Show error section (next 15 lines)
                    for line in output_lines[error_start:error_start + 15]:
                        if line.strip():
                            print(f"         {line[:120]}")
                else:
                    # Show last 10 lines if no clear error marker
                    print(f"      🔍 Last output:")
                    for line in output_lines[-10:]:
                        if line.strip():
                            print(f"         {line[:120]}")
            
            # Show summary
            passed = metadata.get("passed", 0)
            failed = metadata.get("failed", 0)
            total = metadata.get("total", 0)
            if passed == 0 and failed == 0 and total == 0:
                print(f"      ⚠️  No tests were collected or executed (0/0). Check test file syntax and pytest installation.")

        if test_result.success:
            print(f"      ✓ All tests passed: {test_result.result}")
            results["overall_success"] = True
        else:
            print(f"      ✗ Some tests failed: {test_result.result}")

        return results