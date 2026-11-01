"""
Advanced prompt builder that creates context-aware, task-type-specific prompts.
Leverages ContextManager for structured context and creates optimized prompts.
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
from agents.context_manager import ContextManager, ContextConfig
from enum import Enum

# Import consolidated tools for cleaner prompts
try:
    from tools.consolidated import TOOL_REGISTRY_CONSOLIDATED
    CONSOLIDATED_TOOLS_AVAILABLE = True
except (ImportError, AttributeError):
    CONSOLIDATED_TOOLS_AVAILABLE = False
    TOOL_REGISTRY_CONSOLIDATED = None


class TaskType(Enum):
    """Task types for prompt customization"""
    CRUD = "crud"
    API = "api"
    ALGORITHM = "algorithm"
    TEST = "test"
    DATABASE = "database"
    FRONTEND = "frontend"
    DEVOPS = "devops"
    GENERAL = "general"


class PromptBuilder:
    """
    Builds optimized prompts for agents.
    Context-aware, task-type-specific, with few-shot examples.
    """
    
    def __init__(self, context_manager: Optional[ContextManager] = None):
        """
        Initialize prompt builder.
        
        Args:
            context_manager: ContextManager instance (default: creates new one)
        """
        self.context_manager = context_manager or ContextManager()
        self.task_type_examples = self._load_task_examples()
        
        # Cache examples for quick access
        self._examples_cache = {}
    
    def _load_task_examples(self) -> Dict[str, List[Dict[str, str]]]:
        """Load few-shot examples for different task types"""
        import json
        examples = {}
        examples_dir = Path('.aiconfig') / 'examples'
        
        if not examples_dir.exists():
            return examples
        
        # Load examples by task type
        for task_type in TaskType:
            task_type_dir = examples_dir / task_type.value
            if task_type_dir.exists():
                examples[task_type.value] = []
                
                # Load all JSON example files from directory
                for example_file in task_type_dir.glob('*.json'):
                    try:
                        with open(example_file, 'r', encoding='utf-8') as f:
                            example_data = json.load(f)
                            examples[task_type.value].append(example_data)
                    except (json.JSONDecodeError, IOError) as e:
                        # Skip invalid files
                        continue
        
        return examples
    
    def build_implementation_prompt(
        self,
        task: str,
        context: str,
        task_type: Optional[str] = None,
        agent_skills: Optional[str] = None
    ) -> str:
        """
        Build optimized prompt for Implementation Agent.
        
        Args:
            task: User task description
            context: Structured context from ContextManager
            task_type: Detected task type
            agent_skills: Agent's skill knowledge
        
        Returns:
            Optimized system prompt
        """
        # Detect task type if not provided
        if not task_type:
            task_type = self.context_manager.detect_task_type(task)
        
        # Parse context sections
        context_sections = self._parse_context_sections(context)
        
        # Build prompt parts
        parts = []
        
        # 1. ROLE & MISSION
        parts.append(self._build_role_section(agent_type='implementation', task_type=task_type))
        
        # 2. CONTEXT USAGE INSTRUCTIONS
        parts.append(self._build_context_usage_instructions(context_sections))
        
        # 3. TASK TYPE INFORMATION
        if task_type != 'general':
            parts.append(self._build_task_type_section(task_type))
        
        # 4. RELEVANT CONTEXT SECTIONS
        if context_sections:
            parts.append(self._build_context_reference(context_sections))
        
        # 5. SPECIALIZED KNOWLEDGE
        # Note: Skills are referenced but truncated to save tokens
        # Full skill files are loaded separately and model has access
        if agent_skills:
            # Only include a summary - full skills are already in system
            parts.append("SPECIALIZED KNOWLEDGE:\n[Knowledge base loaded - apply relevant patterns from: error handling, Python idioms, type hints, security, algorithms, design patterns, testing, documentation, code organization, performance, logging, API design]")
        
        # 6. FEW-SHOT EXAMPLES
        examples = self._get_task_examples(task_type)
        if examples:
            parts.append(self._build_examples_section(examples, task_type))
        
        # 7. OUTPUT REQUIREMENTS
        parts.append(self._build_output_requirements('implementation', task_type))
        
        # 8. QUALITY CHECKLIST
        quality_checklist = self._build_quality_checklist('implementation', task_type)
        if quality_checklist:
            parts.append(quality_checklist)
        
        return "\n\n".join(filter(None, parts))
    
    def build_test_generator_prompt(
        self,
        agent_name: str,
        agent_role: str,
        skill_content: Optional[str] = None,
        code_to_test: Optional[str] = None,
        context: Optional[str] = None,
        tools: Optional[Dict] = None,
        task_type: Optional[str] = None
    ) -> str:
        """
        Build optimized prompt for Test Generator Agent.
        
        Args:
            agent_name: Name of the agent
            agent_role: Role description of the agent
            skill_content: Agent's skill knowledge
            code_to_test: Code to generate tests for (optional, may be in context)
            context: Structured context (includes code to test if available)
            tools: Available tools
            task_type: Task type (detected if not provided)
        
        Returns:
            Optimized prompt for test generation
        """
        # Detect task type if not provided
        if not task_type and context:
            task_type = self.context_manager.detect_task_type(context[:500])
        task_type = task_type or 'test'
        
        parts = []
        
        # 1. ROLE & MISSION
        parts.append(f"""You are {agent_name}, {agent_role}

Your mission:
- Write comprehensive, production-quality pytest tests
- Cover normal cases, edge cases, and error scenarios
- Use clear, descriptive test names following naming conventions
- Follow Arrange-Act-Assert pattern for test structure
- Ensure proper test isolation and independence
- Write 5-8 test functions minimum for comprehensive coverage""")
        
        # 2. SKILL CONTENT (testing patterns)
        if skill_content:
            # Truncate skill content to fit within token limits
            skill_preview = skill_content[:3000] if len(skill_content) > 3000 else skill_content
            parts.append(f"""TESTING KNOWLEDGE:
{skill_preview}""")
        
        # 3. CONTEXT USAGE (includes code to test if available)
        if context:
            parts.append(f"""CONTEXT:
{context}

Use the code in the context above to generate comprehensive tests.""")
        
        # 4. TEST REQUIREMENTS
        parts.append("""
TEST REQUIREMENTS:

1. **Coverage Requirements**:
   - Normal/happy path cases (typical usage scenarios)
   - Edge cases (empty inputs, boundary values, None, zero, max values)
   - Error cases (invalid inputs, exceptions, error handling)
   - Multiple test functions (5-8 tests minimum)

2. **Test Quality Standards**:
   - Clear, descriptive test names: test_<what>_<expected_behavior>
   - Use Arrange-Act-Assert pattern:
     * Arrange: Set up test data and preconditions
     * Act: Execute the function being tested
     * Assert: Verify the expected outcome
   - One assertion per test when possible (or clearly related assertions)
   - Proper test isolation (no shared state between tests)

3. **Test Types**:
   - Unit tests for individual functions
   - Include parameterized tests if applicable (@pytest.mark.parametrize)
   - Test both positive and negative scenarios

4. **Code Format**:
   - Include the original function/class definition above your tests
   - Import pytest if needed
   - Wrap complete code in ```python block
   - Ensure all assert statements are complete (no truncated lines)
   - Valid Python syntax only

5. **Naming Convention**:
   - Use descriptive names: test_normal_case_typical_usage(), test_edge_case_with_zero()
   - Include docstrings explaining what each test verifies""")
        
        # 5. TEST EXAMPLES
        test_examples = self._get_test_examples(task_type)
        if test_examples:
            parts.append(self._build_test_examples_section(test_examples))
        else:
            # Provide default example structure
            parts.append("""
EXAMPLE TEST STRUCTURE:
```python
def function_to_test(arg1, arg2):
    return arg1 + arg2

import pytest

def test_normal_case_typical_usage():
    \"\"\"Test normal/happy path scenario.\"\"\"
    # Arrange
    input1, input2 = 2, 3
    expected = 5
    
    # Act
    result = function_to_test(input1, input2)
    
    # Assert
    assert result == expected

def test_edge_case_with_zero():
    \"\"\"Test edge case with zero values.\"\"\"
    assert function_to_test(0, 0) == 0

def test_edge_case_with_negative_numbers():
    \"\"\"Test edge case with negative numbers.\"\"\"
    assert function_to_test(-1, -2) == -3

def test_error_case_invalid_input():
    \"\"\"Test error handling for invalid input.\"\"\"
    with pytest.raises(ValueError):
        function_to_test(None, None)
```""")
        
        # 6. OUTPUT REQUIREMENTS
        parts.append("""
OUTPUT REQUIREMENTS:
- Output ONLY complete, runnable pytest test code
- No explanations outside code blocks
- Every test function must have complete assert statements
- Ensure all imports are included
- Follow the structure and patterns shown in examples above""")
        
        # 7. Add tools if available - prefer consolidated tools for cleaner prompts
        if tools:
            # Use consolidated tools if available (cleaner, fewer tokens)
            tools_to_show = tools
            if CONSOLIDATED_TOOLS_AVAILABLE and TOOL_REGISTRY_CONSOLIDATED:
                tools_to_show = TOOL_REGISTRY_CONSOLIDATED
            
            tool_list = "\n".join(f"- {name}: {info['description']}" 
                                 for name, info in tools_to_show.items())
            parts.append(f"""
AVAILABLE TOOLS:
{tool_list}

Note: You typically won't need tools for test generation, but they're available if needed.
Note: Old tool names are automatically migrated to new consolidated tools during execution.""")
        
        return "\n\n".join(filter(None, parts))
    
    def build_validation_prompt(
        self,
        code: str,
        task: str,
        context: Optional[str] = None
    ) -> str:
        """
        Build optimized prompt for Validation Agent.
        
        Args:
            code: Code to validate
            task: Original task
            context: Structured context
        
        Returns:
            Optimized validation prompt
        """
        parts = []
        
        # 1. ROLE & MISSION
        parts.append(self._build_role_section(agent_type='validation', task_type=None))
        
        # 2. CODE TO REVIEW
        parts.append(self._build_code_section(code))
        
        # 3. CONTEXT USAGE
        if context:
            context_sections = self._parse_context_sections(context)
            if context_sections:
                parts.append(self._build_context_usage_instructions(context_sections, focus='validation'))
        
        # 4. VALIDATION CRITERIA
        parts.append(self._build_validation_criteria())
        
        # 5. OUTPUT FORMAT
        parts.append(self._build_validation_output_format())
        
        return "\n\n".join(filter(None, parts))
    
    def _parse_context_sections(self, context: str) -> Dict[str, str]:
        """
        Parse context string into sections.
        
        Args:
            context: Structured context string
        
        Returns:
            Dictionary of section name -> content
        """
        sections = {}
        current_section = None
        current_content = []
        
        for line in context.split('\n'):
            # Check if line is a section header
            if line.endswith(':') and line.isupper():
                # Save previous section
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                
                # Start new section
                current_section = line.rstrip(':').lower()
                current_content = []
            else:
                if current_section:
                    current_content.append(line)
        
        # Save last section
        if current_section and current_content:
            sections[current_section] = '\n'.join(current_content).strip()
        
        return sections
    
    def _build_role_section(self, agent_type: str, task_type: Optional[str] = None) -> str:
        """Build role and mission section"""
        roles = {
            'implementation': """You are a senior software engineer specializing in writing production-quality, maintainable Python code.

Your mission:
- Write complete, runnable code that works correctly on first try
- Follow all project rules and conventions strictly
- Include comprehensive error handling and input validation
- Use type hints consistently for all function parameters and return types
- Add comprehensive docstrings for all functions, classes, and modules
- Consider edge cases and error scenarios
- Write code that is maintainable, well-documented, and follows PEP 8
- Use appropriate design patterns when beneficial
- Optimize for readability and maintainability over cleverness
- Include comments for complex logic or non-obvious decisions""",
            
            'test_generator': """You are a QA engineer specializing in writing comprehensive, production-quality tests.

Your mission:
- Write complete pytest test suites that verify correctness
- Test normal cases, edge cases, and error cases
- Ensure tests are maintainable and clearly named
- Follow project testing conventions
- Write tests that help catch bugs early""",
            
            'validation': """You are a senior code reviewer specializing in comprehensive code quality assessment.

Your mission:
- Identify all code quality issues systematically
- Check for security vulnerabilities, logic errors, and best practice violations
- Provide specific, actionable feedback
- Prioritize issues by severity
- Help improve code quality through constructive feedback"""
        }
        
        base_role = roles.get(agent_type, roles['implementation'])
        
        if task_type and task_type != 'general' and agent_type == 'implementation':
            task_specific = self._get_task_type_instructions(task_type)
            return f"{base_role}\n\n{task_specific}"
        
        return base_role
    
    def _build_context_usage_instructions(
        self,
        context_sections: Dict[str, str],
        focus: str = 'implementation'
    ) -> str:
        """Build instructions on how to use context sections"""
        instructions = ["CONTEXT USAGE INSTRUCTIONS:", ""]
        
        priority_map = {
            'project_rules': "HIGHEST PRIORITY - Follow these rules strictly",
            'relevant_code': "HIGH PRIORITY - Use these patterns and conventions",
            'current_file': "HIGH PRIORITY - Match the style of existing code",
            'architecture': "MEDIUM PRIORITY - Understand system design",
            'project_info': "MEDIUM PRIORITY - Context about the project",
            'dependencies': "REFERENCE - Available libraries and packages",
            'examples': "GUIDANCE - Examples of similar implementations",
        }
        
        for section_name, priority in priority_map.items():
            if section_name in context_sections:
                instructions.append(f"- {section_name.upper().replace('_', ' ')}: {priority}")
        
        instructions.append("")
        instructions.append("When generating code:")
        instructions.append("1. First, check PROJECT RULES section for requirements")
        instructions.append("2. Review RELEVANT CODE section for patterns to follow")
        instructions.append("3. Reference ARCHITECTURE section for system design")
        instructions.append("4. Use EXAMPLES section as guidance for similar tasks")
        instructions.append("5. Follow the style and conventions shown in these sections")
        
        return "\n".join(instructions)
    
    def _build_task_type_section(self, task_type: str) -> str:
        """Build task-type-specific instructions with detailed guidance"""
        instructions = {
            'crud': """TASK TYPE: CRUD Operations

CRITICAL REQUIREMENTS:
1. **Input Validation**:
   - Validate all input types (isinstance checks)
   - Validate input ranges and constraints
   - Check for required vs optional fields
   - Sanitize string inputs (trim whitespace, etc.)

2. **Error Handling**:
   - Use specific exceptions (ValueError, TypeError, KeyError)
   - Provide clear error messages with actual values
   - Handle database errors appropriately (connection errors, constraint violations)
   - Return None or raise exception based on pattern in PROJECT RULES

3. **Function Signatures**:
   - Use descriptive parameter names
   - Include type hints for all parameters and return values
   - Use Optional[] for nullable parameters
   - Document all parameters and return values in docstrings

4. **Return Values**:
   - Create operations: Return created object/dict with generated ID
   - Read operations: Return object/dict or None if not found
   - Update operations: Return updated object/dict
   - Delete operations: Return success boolean or deleted count

5. **Database Patterns** (if applicable):
   - Use parameterized queries (never string concatenation)
   - Handle transactions appropriately
   - Use context managers for database connections
   - Follow ORM patterns if project uses one

6. **Edge Cases**:
   - Empty inputs (empty string, empty dict, empty list)
   - None values
   - Boundary values (max int, zero, negative)
   - Duplicate creation attempts
   - Non-existent IDs for read/update/delete""",
            
            'api': """TASK TYPE: API Development

CRITICAL REQUIREMENTS:
1. **RESTful Design**:
   - Use appropriate HTTP methods (GET, POST, PUT, PATCH, DELETE)
   - Use resource-based URLs (/api/users/{id}, not /api/get_user)
   - Follow REST conventions for URL structure
   - Use proper HTTP status codes (200, 201, 400, 404, 500, etc.)

2. **Request Validation**:
   - Validate Content-Type headers (expect application/json)
   - Validate required fields in request body
   - Validate data types and formats
   - Check authentication/authorization if needed

3. **Response Format**:
   - Consistent JSON structure across endpoints
   - Include 'success' boolean field
   - Include 'data' field for successful responses
   - Include 'error' and 'message' fields for errors
   - Proper HTTP status codes in response

4. **Error Handling**:
   - 400 Bad Request: Invalid input/validation errors
   - 401 Unauthorized: Authentication required
   - 403 Forbidden: Insufficient permissions
   - 404 Not Found: Resource doesn't exist
   - 409 Conflict: Resource conflicts (e.g., duplicate)
   - 500 Internal Server Error: Unexpected server errors
   - Always return JSON error responses, never HTML

5. **Documentation**:
   - Document endpoint in docstring (method, path, parameters, returns)
   - Include example requests and responses
   - Document status codes returned
   - Document authentication requirements

6. **Edge Cases**:
   - Missing request body
   - Invalid JSON in request body
   - Missing required fields
   - Invalid data types
   - Out of range values
   - Concurrent modifications""",
            
            'algorithm': """TASK TYPE: Algorithm Implementation

CRITICAL REQUIREMENTS:
1. **Correctness**:
   - Implement algorithm logic correctly
   - Verify algorithm matches problem requirements
   - Handle all edge cases (empty inputs, single elements, etc.)
   - Test with boundary conditions

2. **Complexity Analysis**:
   - Consider time complexity (O notation)
   - Consider space complexity
   - Optimize if necessary but prioritize correctness
   - Document complexity in docstring

3. **Data Structures**:
   - Choose appropriate data structures (list, dict, set, deque, etc.)
   - Use efficient operations (set lookup vs list iteration)
   - Consider memory usage for large inputs
   - Use generators for large sequences when possible

4. **Edge Cases**:
   - Empty inputs (empty list, empty string, etc.)
   - Single element inputs
   - Already sorted/unsorted inputs
   - Duplicate elements
   - Very large inputs
   - Boundary values (zero, negative, max int)
   - None values

5. **Documentation**:
   - Explain algorithm approach in docstring
   - Document time and space complexity
   - Provide example usage
   - Explain any optimizations or special cases

6. **Validation**:
   - Validate input types
   - Validate input constraints (sorted array for binary search, etc.)
   - Raise appropriate exceptions for invalid inputs
   - Provide clear error messages""",
            
            'test': """TASK TYPE: Test Generation

CRITICAL REQUIREMENTS:
1. **Test Coverage**:
   - Normal/expected cases (happy path)
   - Edge cases (empty inputs, None, boundaries)
   - Error cases (invalid inputs, exceptions)
   - Multiple scenarios if function handles different cases

2. **Test Structure**:
   - Use descriptive test names (test_normal_case, test_empty_input, etc.)
   - One concept per test function
   - Group related tests together
   - Use fixtures for setup/teardown if needed

3. **Assertions**:
   - Use clear, specific assertions
   - Test return values, side effects, and exceptions
   - Use pytest.raises() for exception testing
   - Verify error messages when applicable

4. **Test Quality**:
   - Tests should be independent (no shared state)
   - Tests should be fast and focused
   - Tests should be maintainable and clear
   - Follow pytest conventions

5. **Edge Cases to Test**:
   - Empty inputs (empty list, empty string, empty dict)
   - None values
   - Boundary values (zero, negative, max values)
   - Invalid types (string instead of int, etc.)
   - Out of range values
   - Duplicate values
   - Single element inputs""",
            
            'database': """TASK TYPE: Database Operations

CRITICAL REQUIREMENTS:
1. **Query Safety**:
   - ALWAYS use parameterized queries (never string concatenation)
   - Use ORM methods if project uses ORM
   - Prevent SQL injection vulnerabilities
   - Validate all input before using in queries

2. **Transaction Handling**:
   - Use transactions for multi-step operations
   - Handle rollback on errors
   - Use context managers (with statement) for connections
   - Commit only on success, rollback on error

3. **Error Handling**:
   - Handle connection errors gracefully
   - Handle constraint violations (unique, foreign key)
   - Handle query errors (syntax, missing table)
   - Provide user-friendly error messages

4. **Data Validation**:
   - Validate data before database operations
   - Check required fields
   - Validate data types and formats
   - Check constraints (lengths, ranges, etc.)

5. **Connection Management**:
   - Use connection pooling if applicable
   - Close connections properly
   - Use context managers for automatic cleanup
   - Handle connection timeouts

6. **Performance**:
   - Use appropriate indexes (mention in comments if creating)
   - Avoid N+1 queries
   - Use batch operations when possible
   - Consider query performance for large datasets""",
            
            'frontend': """TASK TYPE: Frontend Development

CRITICAL REQUIREMENTS:
1. **Component Structure**:
   - Clear component hierarchy
   - Reusable components when appropriate
   - Proper separation of concerns
   - Follow project's component patterns

2. **State Management**:
   - Use appropriate state management (local, context, redux)
   - Minimize unnecessary re-renders
   - Handle async state updates correctly
   - Clear state on unmount when needed

3. **User Experience**:
   - Handle loading states
   - Handle error states with user-friendly messages
   - Provide feedback for user actions
   - Ensure responsive design (if applicable)

4. **Validation**:
   - Client-side form validation
   - Display validation errors clearly
   - Prevent invalid form submissions
   - Sanitize user input

5. **Error Handling**:
   - Catch and handle API errors
   - Display user-friendly error messages
   - Log errors appropriately
   - Handle network failures

6. **Accessibility**:
   - Use semantic HTML
   - Include ARIA labels when needed
   - Ensure keyboard navigation works
   - Follow accessibility best practices""",
            
            'devops': """TASK TYPE: DevOps/Automation

CRITICAL REQUIREMENTS:
1. **Script Structure**:
   - Clear script purpose and usage
   - Command-line argument parsing
   - Help/usage documentation
   - Exit codes for success/failure

2. **Error Handling**:
   - Handle file operations errors
   - Handle network/API errors
   - Provide clear error messages
   - Exit with appropriate codes

3. **Safety**:
   - Validate file paths (prevent path traversal)
   - Confirm destructive operations
   - Use safe file operations
   - Handle permissions properly

4. **Logging**:
   - Log important operations
   - Use appropriate log levels
   - Include timestamps
   - Log errors with context

5. **Configuration**:
   - Use environment variables for secrets
   - Use config files for settings
   - Support different environments (dev, prod)
   - Validate configuration on startup

6. **Idempotency**:
   - Scripts should be idempotent when possible
   - Check state before making changes
   - Handle already-configured states
   - Document idempotency behavior""",
        }
        
        return instructions.get(task_type, "")
    
    def _build_context_reference(self, context_sections: Dict[str, str]) -> str:
        """Build reference to context sections"""
        parts = ["RELEVANT CONTEXT SECTIONS:", ""]
        
        # List available sections
        for section_name in context_sections.keys():
            parts.append(f"- {section_name.upper().replace('_', ' ')} is available in context")
        
        parts.append("")
        parts.append("The context provided below contains these sections.")
        parts.append("Pay special attention to PROJECT RULES and RELEVANT CODE sections.")
        
        return "\n".join(parts)
    
    def _build_skills_section(self, skills: str) -> str:
        """Build skills/knowledge section"""
        # Limit skills to first 2000 chars to avoid token overflow
        # Skills should be reference - detailed patterns are in skill files
        truncated_skills = skills[:2000] if len(skills) > 2000 else skills
        if len(skills) > 2000:
            truncated_skills += "\n\n[Additional knowledge in skill files - apply relevant patterns as needed]"
        
        return f"""SPECIALIZED KNOWLEDGE:

{truncated_skills}

Apply this knowledge when writing code. Follow the patterns and best practices described above.
Refer to skill files for detailed patterns if needed."""
    
    def _build_examples_section(self, examples: List[Dict[str, str]], task_type: str) -> str:
        """Build few-shot examples section"""
        if not examples:
            return ""
        
        parts = ["FEW-SHOT EXAMPLES:", ""]
        parts.append("Here are examples of similar tasks. Use these as guidance for structure and style:")
        parts.append("")
        
        for i, example in enumerate(examples[:2], 1):  # Limit to 2 examples to save tokens
            task = example.get('task', '')
            solution = example.get('solution', '')
            description = example.get('description', '')
            
            parts.append(f"Example {i} - {description}:")
            parts.append(f"Task: {task}")
            parts.append("")
            parts.append("Solution:")
            parts.append(f"```python\n{solution}\n```")
            parts.append("")
        
        return "\n".join(parts)
    
    def _build_output_requirements(self, agent_type: str, task_type: Optional[str] = None) -> str:
        """Build output format requirements"""
        if agent_type == 'implementation':
            return """OUTPUT REQUIREMENTS:

1. **Output Format**:
   - Output ONLY valid Python code in markdown code blocks
   - Use ```python to start code blocks
   - Include ALL necessary imports
   - No explanations outside code blocks (code should be self-documenting)

2. **Code Structure**:
   - Complete, runnable functions/classes
   - All functions must have type hints
   - All functions must have docstrings
   - Include input validation and error handling

3. **Quality Standards**:
   - Follow PROJECT RULES section strictly
   - Match style from RELEVANT CODE section if available
   - Use patterns from SPECIALIZED KNOWLEDGE section
   - Handle all edge cases mentioned in task

4. **Completeness**:
   - Code must be immediately usable
   - No placeholders or TODOs
   - Include all necessary error handling
   - Consider all edge cases mentioned"""
        
        elif agent_type == 'test_generator':
            return """OUTPUT REQUIREMENTS:

1. **Output Format**:
   - Output ONLY valid Python pytest test code
   - Use ```python to start code blocks
   - Include all necessary imports (pytest, function being tested)
   - No explanations outside code blocks

2. **Test Structure**:
   - Import the function/class being tested
   - Write test functions starting with 'test_'
   - Use descriptive test names (test_normal_case, test_edge_case, etc.)
   - Group related tests together

3. **Test Coverage**:
   - Test normal/expected cases
   - Test edge cases (empty inputs, None, boundaries)
   - Test error cases (invalid inputs, exceptions)
   - Test multiple scenarios if applicable

4. **Test Quality**:
   - Use clear, descriptive assertions
   - One assert per concept being tested
   - Use pytest.raises() for exception testing
   - Keep tests simple and focused"""
        
        return ""
    
    def _build_quality_checklist(self, agent_type: str, task_type: Optional[str] = None) -> str:
        """Build comprehensive quality checklist"""
        if agent_type == 'implementation':
            base_checklist = [
                "✅ All functions have complete type hints (parameters and return types)",
                "✅ All functions have comprehensive docstrings (description, Args, Returns, Raises)",
                "✅ Input validation is present and correct (types, ranges, constraints)",
                "✅ Error handling covers all failure scenarios (try/except blocks, specific exceptions)",
                "✅ Code follows PROJECT RULES section strictly",
                "✅ Code style matches RELEVANT CODE section if available",
                "✅ Edge cases from task are handled (None, empty, boundaries, invalid inputs)",
                "✅ Code is complete and runnable (no placeholders or TODOs)",
                "✅ Imports are correct and necessary only (no unused imports)",
                "✅ Variable names are descriptive and clear (PEP 8 compliant)",
                "✅ Code follows PEP 8 style guide (spacing, line length, naming)",
                "✅ Comments are added for complex logic or non-obvious decisions",
                "✅ Functions are focused and single-purpose (single responsibility principle)",
                "✅ Code is production-ready (not just proof of concept)",
            ]
            
            # Task-specific checklist items
            task_specific = {
                'crud': [
                    "✅ CRUD operations include proper error handling for all failure modes",
                    "✅ Input validation is comprehensive (types, required fields, constraints)",
                    "✅ Return values are consistent and properly formatted",
                    "✅ Database operations use transactions where appropriate",
                    "✅ Validation errors return clear, actionable messages",
                ],
                'api': [
                    "✅ API endpoints return appropriate HTTP status codes",
                    "✅ Request/response validation is implemented (using Pydantic/models)",
                    "✅ Error responses are properly formatted and include error details",
                    "✅ Authentication/authorization is handled if required",
                    "✅ API follows RESTful conventions",
                    "✅ Response data is serialized correctly",
                ],
                'algorithm': [
                    "✅ Algorithm handles edge cases (empty inputs, single items, duplicates)",
                    "✅ Time/space complexity is reasonable for the problem",
                    "✅ Algorithm is well-documented with complexity analysis",
                    "✅ Edge cases are tested in implementation",
                    "✅ Algorithm uses appropriate data structures",
                ],
                'database': [
                    "✅ Database models have proper relationships and constraints",
                    "✅ Migrations are handled correctly",
                    "✅ Queries are optimized (avoid N+1 problems)",
                    "✅ Transactions are used for multi-step operations",
                    "✅ Error handling for database failures",
                ],
            }
            
            checklist = base_checklist + task_specific.get(task_type or 'general', [])
            
            return f"""QUALITY CHECKLIST:

Before outputting code, verify ALL of the following:
{chr(10).join(checklist)}

CRITICAL: Your code should be production-ready, not just a proof of concept.
This means comprehensive error handling, input validation, documentation, and following best practices."""
        
        return ""
    
    def _build_code_section(self, code: str) -> str:
        """Build code section for review/test generation"""
        return f"""CODE TO REVIEW/TEST:

```python
{code}
```

Analyze this code carefully. Generate comprehensive tests that verify correctness, handle edge cases, and test error conditions."""
    
    def _build_test_requirements(self, task_type: Optional[str] = None) -> str:
        """Build test requirements section"""
        requirements = """TEST REQUIREMENTS:

1. **Test Coverage**:
   - Normal/expected cases (happy path)
   - Edge cases (empty inputs, None, boundaries, max values)
   - Error cases (invalid inputs, exceptions, failure scenarios)
   - Multiple scenarios if function handles different cases

2. **Test Structure**:
   - Separate test functions for different scenarios
   - Use descriptive names: test_normal_case, test_empty_input, test_invalid_input, etc.
   - One concept per test function
   - Use pytest conventions

3. **Assertions**:
   - Use clear, specific assertions
   - Test return values, side effects, exceptions
   - Use pytest.raises() for exception testing
   - Verify error messages when applicable

4. **Test Quality**:
   - Tests should be independent (no shared state)
   - Tests should be fast and focused
   - Use fixtures if needed for setup
   - Follow testing best practices"""
        
        if task_type == 'api':
            requirements += "\n\n5. **API-Specific Tests**:\n   - Test different HTTP methods\n   - Test request validation\n   - Test response formats\n   - Test error responses\n   - Test status codes\n   - Test authentication/authorization if applicable"
        elif task_type == 'crud':
            requirements += "\n\n5. **CRUD-Specific Tests**:\n   - Test create operations\n   - Test read operations with various filters\n   - Test update operations\n   - Test delete operations\n   - Test error handling for each operation\n   - Test edge cases (empty inputs, None, boundaries)"
        elif task_type == 'database':
            requirements += "\n\n5. **Database-Specific Tests**:\n   - Test query correctness\n   - Test transaction handling\n   - Test error handling (connection errors, constraint violations)\n   - Test data validation\n   - Test with test fixtures/mocks"
        
        return requirements
    
    def _build_test_examples_section(self, examples: List[Dict[str, str]]) -> str:
        """Build test examples section"""
        if not examples:
            return ""
        
        parts = ["TEST EXAMPLES:", ""]
        parts.append("Here are examples of good test structure:")
        parts.append("")
        
        for i, example in enumerate(examples[:1], 1):  # Just one example
            description = example.get('description', '')
            test_code = example.get('test_code', example.get('solution', ''))
            
            parts.append(f"Example {i} - {description}:")
            parts.append(f"```python\n{test_code}\n```")
            parts.append("")
        
        return "\n".join(parts)
    
    def _build_validation_criteria(self) -> str:
        """Build validation criteria section"""
        return """VALIDATION CRITERIA:

Review the code for:

1. **Correctness**:
   - Logic is correct
   - Edge cases are handled
   - Algorithm is appropriate

2. **Security**:
   - Input validation present
   - No unsafe operations (eval, exec)
   - No SQL injection risks
   - Proper authentication/authorization

3. **Code Quality**:
   - Follows PEP 8
   - Type hints complete
   - Docstrings present
   - Error handling comprehensive

4. **Best Practices**:
   - Appropriate design patterns
   - Efficient algorithms
   - Clear, maintainable code
   - Follows project conventions"""
    
    def _build_validation_output_format(self) -> str:
        """Build validation output format"""
        return """OUTPUT FORMAT:

Provide structured feedback:

1. **Overall Assessment**: Brief summary and score (0-100)
2. **Critical Issues**: Must-fix issues (security, logic errors)
3. **Important Issues**: Should-fix issues (missing error handling, type hints)
4. **Minor Issues**: Nice-to-fix issues (style, naming)
5. **Suggestions**: Specific improvements with examples

For each issue, provide:
- Location (function/line)
- Issue description
- Impact explanation
- Fix suggestion with code example"""
    
    def _get_task_type_instructions(self, task_type: str) -> str:
        """Get task-type-specific instructions"""
        instructions = {
            'crud': """For this CRUD task:
- Implement proper data validation
- Use appropriate data structures
- Include clear error messages
- Follow database patterns if applicable""",
            
            'api': """For this API task:
- Design RESTful endpoints
- Use appropriate HTTP methods
- Include proper status codes
- Validate requests and format responses""",
            
            'algorithm': """For this algorithm task:
- Implement correct algorithm logic
- Consider time/space complexity
- Handle edge cases
- Document algorithm approach""",
        }
        
        return instructions.get(task_type, "")
    
    def _get_task_examples(self, task_type: str) -> List[Dict[str, str]]:
        """Get few-shot examples for task type"""
        # Check cache first
        if task_type in self._examples_cache:
            return self._examples_cache[task_type]
        
        # Load from task_type_examples
        examples = self.task_type_examples.get(task_type, [])
        
        # Cache results
        self._examples_cache[task_type] = examples
        
        # Return up to 2 examples to save tokens
        return examples[:2]
    
    def _get_test_examples(self, task_type: str) -> List[Dict[str, str]]:
        """Get test examples for task type"""
        # Get test examples from 'test' type
        test_examples = self.task_type_examples.get('test', [])
        
        # Also check if task_type has test-related examples
        if task_type in self.task_type_examples:
            # Filter for test examples in that task type
            type_examples = [ex for ex in self.task_type_examples[task_type] 
                           if 'test' in ex.get('tags', []) or 'test_code' in ex]
            test_examples.extend(type_examples)
        
        # Return up to 1 example to save tokens
        return test_examples[:1]

