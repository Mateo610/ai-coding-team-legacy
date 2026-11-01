"""
Context management system for building optimal context for agents.
Focuses on relevance, structure, and token efficiency.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import os
import re


class ContextSection(Enum):
    """Types of context sections"""
    PROJECT_RULES = "project_rules"
    ARCHITECTURE = "architecture"
    PROJECT_INFO = "project_info"
    RELEVANT_CODE = "relevant_code"
    EXAMPLES = "examples"
    TASK_HISTORY = "task_history"
    CURRENT_FILE = "current_file"
    DEPENDENCIES = "dependencies"
    ERROR_CONTEXT = "error_context"


@dataclass
class ContextSectionData:
    """Data for a context section"""
    section_type: ContextSection
    content: str
    priority: int  # Higher priority = more important
    max_tokens: Optional[int] = None  # Max tokens for this section


@dataclass
class ContextConfig:
    """Configuration for context building"""
    max_total_tokens: int = 8000  # Maximum total context tokens
    include_project_rules: bool = True
    include_architecture: bool = True
    include_project_info: bool = True
    include_relevant_code: bool = True
    include_examples: bool = True
    include_task_history: bool = False
    include_current_file: bool = False
    include_dependencies: bool = False
    include_error_context: bool = False


class ContextManager:
    """
    Manages context building for agents with focus on:
    - Relevance: Only include relevant information
    - Structure: Organized, easy-to-parse format
    - Efficiency: Minimize token usage while maximizing value
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize context manager.
        
        Args:
            project_root: Root directory of the project (default: current directory)
        """
        self.project_root = project_root or Path.cwd()
        self.aiconfig_dir = self.project_root / '.aiconfig'
        self.project_config = self._load_project_config()
    
    def _load_project_config(self) -> Dict[str, str]:
        """Load project configuration from .aiconfig/"""
        config = {}
        
        if not self.aiconfig_dir.exists():
            return config
        
        # Load rules
        rules_file = self.aiconfig_dir / 'rules.md'
        if rules_file.exists():
            config['rules'] = rules_file.read_text()
        
        # Load architecture docs
        arch_file = self.aiconfig_dir / 'context' / 'architecture.md'
        if arch_file.exists():
            config['architecture'] = arch_file.read_text()
        
        return config
    
    def build_context(
        self,
        task: str,
        context_dict: Optional[Dict[str, Any]] = None,
        config: Optional[ContextConfig] = None,
        agent_type: Optional[str] = None
    ) -> str:
        """
        Build optimized context for agent.
        
        Args:
            task: User task description
            context_dict: Optional additional context dictionary
            config: Context configuration (default: ContextConfig())
            agent_type: Type of agent (implementation, test_generator, etc.)
        
        Returns:
            Structured context string
        """
        if config is None:
            config = ContextConfig()
        
        context_dict = context_dict or {}
        
        # Collect context sections
        sections = []
        
        # 1. Project Rules (highest priority)
        if config.include_project_rules and 'rules' in self.project_config:
            rules = self._truncate_content(
                self.project_config['rules'],
                max_tokens=1000  # Limit rules to 1000 tokens
            )
            sections.append(ContextSectionData(
                section_type=ContextSection.PROJECT_RULES,
                content=rules,
                priority=10,
                max_tokens=1000
            ))
        
        # 2. Project Info
        if config.include_project_info and 'project_info' in context_dict:
            project_info = context_dict.get('project_info', {})
            info_str = self._format_project_info(project_info)
            sections.append(ContextSectionData(
                section_type=ContextSection.PROJECT_INFO,
                content=info_str,
                priority=8,
                max_tokens=500
            ))
        
        # 3. Architecture
        if config.include_architecture and 'architecture' in self.project_config:
            arch = self._truncate_content(
                self.project_config['architecture'],
                max_tokens=1500
            )
            sections.append(ContextSectionData(
                section_type=ContextSection.ARCHITECTURE,
                content=arch,
                priority=7,
                max_tokens=1500
            ))
        
        # 4. Relevant Code (if available)
        if config.include_relevant_code and 'relevant_code' in context_dict:
            relevant_code = self._format_relevant_code(
                context_dict['relevant_code'],
                max_tokens=2000
            )
            sections.append(ContextSectionData(
                section_type=ContextSection.RELEVANT_CODE,
                content=relevant_code,
                priority=9,  # Very high priority
                max_tokens=2000
            ))
        
        # 5. Current File (if working on specific file)
        if config.include_current_file and 'current_file' in context_dict:
            current_file = self._format_current_file(
                context_dict['current_file'],
                max_tokens=1500
            )
            sections.append(ContextSectionData(
                section_type=ContextSection.CURRENT_FILE,
                content=current_file,
                priority=9,
                max_tokens=1500
            ))
        
        # 6. Dependencies (if needed)
        if config.include_dependencies:
            dependencies = self._extract_dependencies()
            if dependencies:
                deps_str = self._format_dependencies(dependencies)
                sections.append(ContextSectionData(
                    section_type=ContextSection.DEPENDENCIES,
                    content=deps_str,
                    priority=5,
                    max_tokens=300
                ))
        
        # 7. Examples (agent-specific)
        if config.include_examples and agent_type:
            examples = self._get_agent_examples(agent_type, task)
            if examples:
                examples_str = self._format_examples(examples)
                sections.append(ContextSectionData(
                    section_type=ContextSection.EXAMPLES,
                    content=examples_str,
                    priority=6,
                    max_tokens=1000
                ))
        
        # 8. Task History (for iterative improvements)
        if config.include_task_history and 'task_history' in context_dict:
            history = self._format_task_history(
                context_dict['task_history'],
                max_tokens=1000
            )
            sections.append(ContextSectionData(
                section_type=ContextSection.TASK_HISTORY,
                content=history,
                priority=4,
                max_tokens=1000
            ))
        
        # 9. Error Context (for fix iterations)
        if config.include_error_context and 'error_context' in context_dict:
            error_context = self._format_error_context(
                context_dict['error_context'],
                max_tokens=800
            )
            sections.append(ContextSectionData(
                section_type=ContextSection.ERROR_CONTEXT,
                content=error_context,
                priority=8,  # High priority for fixing
                max_tokens=800
            ))
        
        # Sort by priority (highest first)
        sections.sort(key=lambda s: s.priority, reverse=True)
        
        # Build final context with token limits
        final_context = self._assemble_context(sections, config.max_total_tokens)
        
        return final_context
    
    def _assemble_context(
        self,
        sections: List[ContextSectionData],
        max_tokens: int
    ) -> str:
        """
        Assemble context sections within token limit.
        
        Args:
            sections: List of context sections (sorted by priority)
            max_tokens: Maximum total tokens
        
        Returns:
            Assembled context string
        """
        parts = []
        current_tokens = 0
        
        for section in sections:
            # Estimate tokens (rough: 1 token ≈ 4 characters)
            section_tokens = len(section.content) // 4
            
            # Check if we can fit this section
            if current_tokens + section_tokens > max_tokens:
                # Try to truncate this section to fit
                remaining_tokens = max_tokens - current_tokens
                if remaining_tokens > 100:  # Only include if significant space
                    truncated = self._truncate_content(
                        section.content,
                        max_tokens=remaining_tokens
                    )
                    parts.append(self._format_section(section.section_type, truncated))
                break
            
            # Add full section
            parts.append(self._format_section(section.section_type, section.content))
            current_tokens += section_tokens
        
        return "\n\n".join(parts)
    
    def _format_section(self, section_type: ContextSection, content: str) -> str:
        """Format a context section with header"""
        headers = {
            ContextSection.PROJECT_RULES: "PROJECT RULES:",
            ContextSection.ARCHITECTURE: "ARCHITECTURE:",
            ContextSection.PROJECT_INFO: "PROJECT INFO:",
            ContextSection.RELEVANT_CODE: "RELEVANT CODE:",
            ContextSection.EXAMPLES: "EXAMPLES:",
            ContextSection.TASK_HISTORY: "TASK HISTORY:",
            ContextSection.CURRENT_FILE: "CURRENT FILE:",
            ContextSection.DEPENDENCIES: "DEPENDENCIES:",
            ContextSection.ERROR_CONTEXT: "ERROR CONTEXT:",
        }
        
        header = headers.get(section_type, "CONTEXT:")
        return f"{header}\n{content}"
    
    def _truncate_content(self, content: str, max_tokens: int) -> str:
        """
        Truncate content to fit within token limit.
        Tries to preserve structure (code blocks, sections).
        
        Args:
            content: Content to truncate
            max_tokens: Maximum tokens
        
        Returns:
            Truncated content
        """
        max_chars = max_tokens * 4  # Rough estimate
        
        if len(content) <= max_chars:
            return content
        
        # Try to truncate at a sensible boundary
        # Look for paragraph breaks, code blocks, or section headers
        truncate_at = max_chars - 100  # Leave some buffer
        
        # Try to find a good breaking point
        # Look for double newlines first
        last_break = content.rfind('\n\n', 0, truncate_at)
        if last_break > truncate_at * 0.8:  # If break is reasonably close
            return content[:last_break] + "\n\n[Content truncated...]"
        
        # Look for single newline
        last_newline = content.rfind('\n', 0, truncate_at)
        if last_newline > truncate_at * 0.8:
            return content[:last_newline] + "\n[Content truncated...]"
        
        # Fallback: hard truncate
        return content[:truncate_at] + "\n[Content truncated...]"
    
    def _format_project_info(self, project_info: Dict[str, Any]) -> str:
        """Format project information"""
        lines = []
        
        if 'name' in project_info:
            lines.append(f"Project Name: {project_info['name']}")
        
        if 'type' in project_info:
            lines.append(f"Project Type: {project_info['type']}")
        
        if 'structure' in project_info:
            lines.append(f"Project Structure: {project_info['structure']}")
        
        return "\n".join(lines)
    
    def _format_relevant_code(self, code_data: Any, max_tokens: int) -> str:
        """Format relevant code snippets"""
        if isinstance(code_data, str):
            return self._truncate_content(code_data, max_tokens)
        
        if isinstance(code_data, list):
            # Format as code blocks
            parts = []
            for item in code_data:
                if isinstance(item, dict):
                    file_path = item.get('file', '')
                    code = item.get('code', '')
                    parts.append(f"# From {file_path}\n```python\n{code}\n```")
                else:
                    parts.append(f"```python\n{item}\n```")
            
            combined = "\n\n".join(parts)
            return self._truncate_content(combined, max_tokens)
        
        return str(code_data)
    
    def _format_current_file(self, file_data: Dict[str, Any], max_tokens: int) -> str:
        """Format current file content"""
        file_path = file_data.get('path', 'unknown')
        content = file_data.get('content', '')
        
        # Include full file if small, otherwise truncate
        formatted = f"# Current File: {file_path}\n```python\n{content}\n```"
        return self._truncate_content(formatted, max_tokens)
    
    def _format_dependencies(self, dependencies: List[str]) -> str:
        """Format project dependencies"""
        return "Required packages:\n" + "\n".join(f"- {dep}" for dep in dependencies)
    
    def _format_examples(self, examples: List[Dict[str, str]]) -> str:
        """Format few-shot examples"""
        parts = []
        for i, example in enumerate(examples, 1):
            task = example.get('task', '')
            solution = example.get('solution', '')
            parts.append(f"Example {i}:\nTask: {task}\n\nSolution:\n```python\n{solution}\n```")
        
        return "\n\n".join(parts)
    
    def _format_task_history(self, history: List[Dict[str, Any]], max_tokens: int) -> str:
        """Format task history for iterative improvements"""
        parts = []
        for item in history[-3:]:  # Last 3 iterations
            iteration = item.get('iteration', '')
            task = item.get('task', '')
            result = item.get('result', '')
            parts.append(f"Iteration {iteration}: {task}\nResult: {result[:200]}...")
        
        combined = "\n\n".join(parts)
        return self._truncate_content(combined, max_tokens)
    
    def _format_error_context(self, error_data: Dict[str, Any], max_tokens: int) -> str:
        """Format error context for fixing"""
        error_type = error_data.get('error_type', 'Error')
        error_message = error_data.get('error_message', '')
        code = error_data.get('code', '')
        suggestions = error_data.get('suggestions', [])
        
        parts = [
            f"Error Type: {error_type}",
            f"Error Message: {error_message}",
            f"Code with error:\n```python\n{code}\n```"
        ]
        
        if suggestions:
            parts.append("Fix suggestions:")
            for suggestion in suggestions[:3]:  # Top 3 suggestions
                parts.append(f"- {suggestion}")
        
        combined = "\n\n".join(parts)
        return self._truncate_content(combined, max_tokens)
    
    def _extract_dependencies(self) -> List[str]:
        """Extract project dependencies from requirements.txt or similar"""
        dependencies = []
        
        # Check for requirements.txt
        req_file = self.project_root / 'requirements.txt'
        if req_file.exists():
            with open(req_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Extract package name (before ==, >=, etc.)
                        pkg = re.split(r'[>=<]', line)[0].strip()
                        dependencies.append(pkg)
        
        return dependencies
    
    def _get_agent_examples(self, agent_type: str, task: str) -> List[Dict[str, str]]:
        """
        Get relevant few-shot examples for agent type.
        
        Args:
            agent_type: Type of agent (implementation, test_generator, etc.)
            task: Current task
        
        Returns:
            List of example dictionaries
        """
        # For now, return empty list
        # Can be extended to load examples from files based on task type
        examples_dir = self.aiconfig_dir / 'examples' / agent_type
        if not examples_dir.exists():
            return []
        
        # TODO: Implement example loading based on task similarity
        # For now, return empty
        return []
    
    def detect_task_type(self, task: str) -> str:
        """
        Detect task type from task description.
        Improved detection with better keyword matching and priority ordering.
        
        Args:
            task: Task description
        
        Returns:
            Task type (e.g., 'crud', 'api', 'algorithm', 'test', etc.)
        """
        task_lower = task.lower()
        
        # Check in priority order (more specific types first)
        
        # 1. API tasks (check first - high priority for framework keywords)
        api_keywords = [
            'flask', 'fastapi', 'django rest', 'express', 'api endpoint',
            'rest api', 'rest endpoint', 'api route', 'http endpoint',
            'endpoint', 'route', 'graphql', 'webhook'
        ]
        if any(kw in task_lower for kw in api_keywords):
            return 'api'
        
        # 2. Database tasks (check before CRUD as they may overlap)
        database_keywords = [
            'sqlalchemy', 'django model', 'database model', 'orm model',
            'model for', 'migration', 'schema', 'database'
        ]
        if any(kw in task_lower for kw in database_keywords):
            return 'database'
        
        # 3. Test tasks
        test_keywords = ['test', 'testing', 'pytest', 'unittest', 'assert', 'test case', 'test for']
        if any(kw in task_lower for kw in test_keywords):
            return 'test'
        
        # 4. ETL/Data Processing tasks (check before CRUD/algorithm to catch data processing)
        etl_keywords = [
            'etl', 'extract transform load', 'data pipeline', 'data processing',
            'data transformation', 'data validation', 'data cleaning', 'data migration'
        ]
        if any(kw in task_lower for kw in etl_keywords):
            return 'etl'
        
        # 5. Data Analysis tasks (check before general tasks)
        data_analysis_keywords = [
            'data analysis', 'statistical analysis', 'data visualization',
            'data science', 'machine learning', 'data mining', 'analytics',
            'analyze', 'analysis', 'visualization'
        ]
        if any(kw in task_lower for kw in data_analysis_keywords):
            return 'data_analysis'
        
        # 6. Frontend tasks (check before CRUD to catch React/UI tasks)
        frontend_keywords = [
            'frontend', 'ui', 'user interface', 'react', 'vue', 'angular',
            'html', 'css', 'javascript', 'typescript', 'component', 'jsx',
            'responsive', 'web component', 'single page app', 'spa'
        ]
        if any(kw in task_lower for kw in frontend_keywords):
            return 'frontend'
        
        # 7. DevOps tasks (check before CRUD to catch infrastructure tasks)
        devops_keywords = [
            'deploy', 'docker', 'dockerfile', 'docker compose', 'ci/cd',
            'ci cd', 'github actions', 'gitlab ci', 'jenkins', 'kubernetes',
            'k8s', 'infrastructure', 'devops', 'deployment', 'pipeline',
            'terraform', 'ansible', 'cloudformation'
        ]
        if any(kw in task_lower for kw in devops_keywords):
            return 'devops'
        
        # 8. Algorithm tasks (before CRUD to catch math/compute operations)
        algorithm_keywords = [
            'algorithm', 'sort', 'search', 'binary', 'merge', 'quick',
            'calculate', 'compute', 'math', 'function to', 'add numbers'
        ]
        if any(kw in task_lower for kw in algorithm_keywords):
            return 'algorithm'
        
        # 9. CRUD tasks (check last - most generic)
        crud_keywords = ['create', 'read', 'update', 'delete', 'crud', 'add', 'remove']
        # Only match if not already matched as more specific task type
        if any(kw in task_lower for kw in crud_keywords):
            # Exclude if it's clearly a more specific task type
            if not any(kw in task_lower for kw in [
                'api', 'endpoint', 'route', 'model', 'database', 'sql',
                'etl', 'pipeline', 'data processing', 'analysis', 'react',
                'docker', 'deploy', 'ci/cd', 'algorithm', 'sort', 'search'
            ]):
                return 'crud'
        
        return 'general'
    
    def get_task_specific_context(
        self,
        task: str,
        context_dict: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Build context optimized for specific task type.
        
        Args:
            task: Task description
            context_dict: Optional additional context
        
        Returns:
            Optimized context string
        """
        task_type = self.detect_task_type(task)
        
        # Create config based on task type
        config = ContextConfig()
        
        # Adjust config based on task type
        if task_type == 'test':
            config.include_relevant_code = True  # Need code to test
            config.include_current_file = True
        
        if task_type == 'crud' or task_type == 'database':
            config.include_project_info = True
            config.include_architecture = True
        
        if task_type == 'api':
            config.include_relevant_code = True
            config.include_dependencies = True
        
        return self.build_context(task, context_dict, config, agent_type=None)

