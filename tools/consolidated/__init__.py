"""
Consolidated Tool Registry
Registers all 26 macro-tools that replace the original 97 tools

This is the main entry point for consolidated tools.
All agents should use tools from TOOL_REGISTRY_CONSOLIDATED.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tools.code_tools import ToolResult

# Import all consolidated tool classes
from tools.consolidated.fs_tools import FSTools
from tools.consolidated.project_tools import ProjectTools
from tools.consolidated.code_quality_tools import CodeQualityTools
from tools.consolidated.quality_tools import QualityTools
from tools.consolidated.git_consolidated import GitConsolidated
from tools.consolidated.db_tools import DBTools
from tools.consolidated.api_consolidated import APIConsolidated
from tools.consolidated.runtime_tools import RuntimeTools
from tools.consolidated.doc_tools import DocTools
from tools.consolidated.web_tools import WebTools
from tools.consolidated.escalation_tools import EscalationTools


# Consolidated Tool Registry - Only 26 tools (down from 97)
TOOL_REGISTRY_CONSOLIDATED = {
    # File System Tools (3 tools)
    "fs_read": {
        "function": FSTools.fs_read,
        "description": "Read file content or check existence. Modes: 'read' (default) or 'exists'. Usage: fs_read('path/to/file.py', mode='read')"
    },
    "fs_write": {
        "function": FSTools.fs_write,
        "description": "Write files or create directories. Modes: 'write' (default), 'save', or 'directory'. Usage: fs_write('path/to/file.py', content='# code', mode='write')"
    },
    "fs_list": {
        "function": FSTools.fs_list,
        "description": "Enumerate directories, search for patterns, list logs. Modes: 'directory' (default), 'files', or 'logs'. Usage: fs_list('src/', mode='directory')"
    },
    
    # Project & Code Search Tools (2 tools)
    "project_scan": {
        "function": ProjectTools.project_scan,
        "description": "Detect project structure, configs, test suites, env files. Modes: 'full' (default), 'entrypoints', 'configs', 'tests', or 'env'. Usage: project_scan('.', mode='full')"
    },
    "code_search": {
        "function": ProjectTools.code_search,
        "description": "Search codebase by text, symbols, TODOs, imports. Modes: 'text' (default), 'usages', 'definitions', 'todos', or 'imports'. Usage: code_search('MyClass', mode='usages')"
    },
    
    # Code Quality & Execution Tools (3 tools)
    "code_check": {
        "function": CodeQualityTools.code_check,
        "description": "Validate syntax, types, and static complexity. Modes: 'syntax' (default), 'types', or 'complexity'. Usage: code_check(code, mode='syntax')"
    },
    "code_format": {
        "function": CodeQualityTools.code_format,
        "description": "Run formatters, organize imports, apply quality fixes. Modes: 'format' (default), 'imports', or 'quality'. Usage: code_format(code, mode='format')"
    },
    "code_execute": {
        "function": CodeQualityTools.code_execute,
        "description": "Run code safely inside a sandbox. Usage: code_execute(code, timeout=10)"
    },
    
    # Testing & Linting Tools (2 tools)
    "test_run": {
        "function": QualityTools.test_run,
        "description": "Uniform test execution across languages. Framework: 'auto' (default), 'pytest', 'npm_test', or 'vitest'. Usage: test_run(framework='auto', test_path='tests')"
    },
    "lint_run": {
        "function": QualityTools.lint_run,
        "description": "Lint/format code in any language. Modes: 'lint' (default), 'format', or 'fix'. Usage: lint_run('src/main.py', mode='lint', language='python')"
    },
    
    # Git Tools (2 tools)
    "git_inspect": {
        "function": GitConsolidated.git_inspect,
        "description": "Read-only Git inspection. Modes: 'status' (default), 'diff', 'log', 'show', or 'branch'. Usage: git_inspect(mode='status')"
    },
    "git_modify": {
        "function": GitConsolidated.git_modify,
        "description": "Guarded write operations (requires confirmation). Actions: 'add' or 'commit'. Usage: git_modify(action='add', files=['src/main.py'])"
    },
    
    # Database Tools (2 tools)
    "db_introspect": {
        "function": DBTools.db_introspect,
        "description": "Query schema-level database info. Modes: 'schema' (default) or 'tables'. Usage: db_introspect('sqlite:///test.db', mode='schema')"
    },
    "db_query": {
        "function": DBTools.db_query,
        "description": "Read-only SQL execution with limit guardrails. Usage: db_query('sqlite:///test.db', 'SELECT * FROM users LIMIT 10')"
    },
    
    # API Tools (2 tools)
    "api_control": {
        "function": APIConsolidated.api_control,
        "description": "Control dev APIs locally. Actions: 'start' or 'stop'. Usage: api_control(action='start', server_file='app.py', port=5000)"
    },
    "api_test": {
        "function": APIConsolidated.api_test,
        "description": "Test HTTP endpoints, validate responses, inspect docs. Modes: 'test' (default), 'validate', 'auth', or 'spec'. Usage: api_test('http://localhost:5000/api/users', mode='test')"
    },
    
    # Runtime Infrastructure Tools (4 tools)
    "task_run": {
        "function": RuntimeTools.task_run,
        "description": "Unified task runner (npm, make, poetry, alembic). Modes: 'run' (default), 'list', or 'validate'. Usage: task_run('npm run dev', mode='run')"
    },
    "docker_inspect": {
        "function": RuntimeTools.docker_inspect,
        "description": "Inspect local Docker state/services. Modes: 'ps' (default), 'compose', 'status', or 'health'. Usage: docker_inspect(mode='ps')"
    },
    "docker_logs": {
        "function": RuntimeTools.docker_logs,
        "description": "Get logs from containers. Usage: docker_logs('container_name', lines=50)"
    },
    "log_inspect": {
        "function": RuntimeTools.log_inspect,
        "description": "Inspect, search, filter log files. Modes: 'read' (default), 'tail', 'search', or 'filter'. Usage: log_inspect('logs/app.log', mode='read')"
    },
    
    # Documentation, Dependencies & Security Tools (3 tools)
    "docs_generate": {
        "function": DocTools.docs_generate,
        "description": "Documentation generation. Modes: 'readme' (default), 'api_docs', 'comments', 'changelog', or 'architecture'. Usage: docs_generate(mode='readme')"
    },
    "deps_manage": {
        "function": DocTools.deps_manage,
        "description": "Manage and audit dependencies. Modes: 'check' (default), 'security', 'update', 'list', 'add', 'remove', or 'license'. Usage: deps_manage(mode='check')"
    },
    "security_scan": {
        "function": DocTools.security_scan,
        "description": "General and targeted security scanning. Modes: 'general' (default), 'secrets', 'dependencies', 'sql_injection', 'xss', or 'audit'. Usage: security_scan(mode='general')"
    },
    
    # Web Research Tools (2 tools)
    "web_get": {
        "function": WebTools.web_get,
        "description": "Fetch web content or assets. Modes: 'read' (default), 'documentation', or 'assets'. Usage: web_get('https://example.com', mode='read')"
    },
    "web_analyze": {
        "function": WebTools.web_analyze,
        "description": "Analyze web pages for info or design patterns. Modes: 'extract' (default), 'summary', 'scrape', 'design_elements', 'structure', or 'design'. Usage: web_analyze('https://example.com', mode='extract', info_type='version')"
    },
    
    # Model Escalation Tools (1 tool)
    "model_escalate": {
        "function": EscalationTools.model_escalate,
        "description": "Delegate hard subtasks to Claude / DeepSeek / GPT-4. Modes: 'consult' (default), 'check_complexity', 'help', or 'refine'. Usage: model_escalate('Complex task', mode='consult', model='deepseek')"
    },
}


def get_tool_registry():
    """Get the consolidated tool registry"""
    return TOOL_REGISTRY_CONSOLIDATED


def get_tool_count():
    """Get the number of tools in the consolidated registry"""
    return len(TOOL_REGISTRY_CONSOLIDATED)


def list_all_tools():
    """List all tools with descriptions"""
    tools_list = []
    for tool_name, tool_info in TOOL_REGISTRY_CONSOLIDATED.items():
        tools_list.append({
            "name": tool_name,
            "description": tool_info["description"]
        })
    return tools_list


# Export registry and functions
__all__ = [
    "TOOL_REGISTRY_CONSOLIDATED",
    "get_tool_registry",
    "get_tool_count",
    "list_all_tools",
]

