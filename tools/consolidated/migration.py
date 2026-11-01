"""
Migration Layer - Maps old tool names to new consolidated tools

This provides backward compatibility during migration by automatically
translating old tool calls to new consolidated tool calls with appropriate modes.
"""

from typing import Dict, Tuple, Any, Optional
from tools.code_tools import ToolResult


# Mapping from old tool names to (new_tool_name, default_mode, additional_params)
OLD_TO_NEW_MAPPING: Dict[str, Tuple[str, Optional[str], Dict[str, Any]]] = {
    # File Tools → fs_read, fs_write, fs_list
    "read_file": ("fs_read", "read", {}),
    "file_exists": ("fs_read", "exists", {}),
    "write_file": ("fs_write", "write", {}),
    "save_file": ("fs_write", "save", {}),
    "create_directory": ("fs_write", "directory", {}),
    "list_directory": ("fs_list", "directory", {}),
    "find_files": ("fs_list", "files", {}),
    "list_logs": ("fs_list", "logs", {}),
    
    # Project & Code Search Tools → project_scan, code_search
    "scan_project": ("project_scan", "full", {}),
    "find_entrypoints": ("project_scan", "entrypoints", {}),
    "list_configs": ("project_scan", "configs", {}),
    "find_tests": ("project_scan", "tests", {}),
    "find_env_files": ("project_scan", "env", {}),
    "search_code": ("code_search", "text", {}),
    "find_usages": ("code_search", "usages", {}),
    "find_definitions": ("code_search", "definitions", {}),
    "find_todos": ("code_search", "todos", {}),
    "find_imports": ("code_search", "imports", {}),
    
    # Code Quality Tools → code_check, code_format, code_execute
    "check_syntax": ("code_check", "syntax", {}),
    "check_types": ("code_check", "types", {}),
    "analyze_complexity": ("code_check", "complexity", {}),
    "format_code": ("code_format", "format", {}),
    "organize_imports": ("code_format", "imports", {}),
    "apply_code_quality": ("code_format", "quality", {}),
    "execute_code": ("code_execute", None, {}),
    
    # Testing & Linting Tools → test_run, lint_run
    "run_tests": ("test_run", None, {"framework": "auto"}),
    "run_pytest": ("test_run", None, {"framework": "pytest"}),
    "run_npm_test": ("test_run", None, {"framework": "npm_test"}),
    "run_vitest": ("test_run", None, {"framework": "vitest"}),
    "get_test_summary": ("test_run", None, {"framework": "auto"}),
    "run_linter": ("lint_run", "lint", {}),
    "run_formatter": ("lint_run", "format", {}),
    "fix_code": ("lint_run", "fix", {}),
    "lint_python": ("lint_run", "lint", {"language": "python"}),
    "lint_javascript": ("lint_run", "lint", {"language": "javascript"}),
    "show_lint_diff": ("lint_run", "format", {"show_diff": True}),
    
    # Git Tools → git_inspect, git_modify
    "git_status": ("git_inspect", "status", {}),
    "git_diff": ("git_inspect", "diff", {}),
    "git_log": ("git_inspect", "log", {}),
    "git_show": ("git_inspect", "show", {}),
    "git_branch": ("git_inspect", "branch", {}),
    "git_add": ("git_modify", None, {"action": "add"}),
    "git_commit": ("git_modify", None, {"action": "commit"}),
    
    # Database Tools → db_introspect, db_query
    "db_get_schema": ("db_introspect", "schema", {}),
    "db_list_tables": ("db_introspect", "tables", {}),
    "db_query": ("db_query", None, {}),  # No change, just renamed
    
    # API Tools → api_control, api_test
    "api_start_server": ("api_control", None, {"action": "start"}),
    "api_stop_server": ("api_control", None, {"action": "stop"}),
    "api_test_endpoint": ("api_test", "test", {}),
    "api_validate_response": ("api_test", "validate", {}),
    "api_test_auth": ("api_test", "auth", {}),
    "extract_api_spec": ("api_test", "spec", {}),
    
    # Runtime Infrastructure Tools → task_run, docker_inspect, docker_logs, log_inspect
    "run_task": ("task_run", "run", {}),
    "list_tasks": ("task_run", "list", {}),
    "validate_task": ("task_run", "validate", {}),
    "docker_ps": ("docker_inspect", "ps", {}),
    "docker_compose_ps": ("docker_inspect", "compose", {}),
    "docker_status": ("docker_inspect", "status", {}),
    "docker_health": ("docker_inspect", "health", {}),
    "docker_logs": ("docker_logs", None, {}),  # No change, just renamed
    "read_log": ("log_inspect", "read", {}),
    "tail_log": ("log_inspect", "tail", {}),
    "search_log": ("log_inspect", "search", {}),
    "filter_log": ("log_inspect", "filter", {}),
    
    # Documentation Tools → docs_generate
    "generate_readme": ("docs_generate", "readme", {}),
    "generate_api_docs": ("docs_generate", "api_docs", {}),
    "generate_code_comments": ("docs_generate", "comments", {}),
    "update_changelog": ("docs_generate", "changelog", {}),
    "generate_architecture_doc": ("docs_generate", "architecture", {}),
    
    # Dependency Management Tools → deps_manage
    "check_dependencies": ("deps_manage", "check", {}),
    "check_security": ("deps_manage", "security", {}),
    "update_dependencies": ("deps_manage", "update", {}),
    "list_dependencies": ("deps_manage", "list", {}),
    "add_dependency": ("deps_manage", "add", {}),
    "remove_dependency": ("deps_manage", "remove", {}),
    "check_license": ("deps_manage", "license", {}),
    
    # Security Tools → security_scan
    "scan_security": ("security_scan", "general", {}),
    "check_secrets": ("security_scan", "secrets", {}),
    "analyze_dependencies": ("security_scan", "dependencies", {}),
    "check_sql_injection": ("security_scan", "sql_injection", {}),
    "check_xss": ("security_scan", "xss", {}),
    "security_audit": ("security_scan", "audit", {}),
    
    # Web Research Tools → web_get, web_analyze
    "read_web_page": ("web_get", "read", {}),
    "read_documentation": ("web_get", "documentation", {}),
    "download_assets": ("web_get", "assets", {}),
    "extract_information": ("web_analyze", "extract", {}),
    "get_web_summary": ("web_analyze", "summary", {}),
    "scrape_website": ("web_analyze", "scrape", {}),
    "extract_design_elements": ("web_analyze", "design_elements", {}),
    "extract_structure": ("web_analyze", "structure", {}),
    "analyze_design": ("web_analyze", "design", {}),
    
    # Model Escalation Tools → model_escalate
    "check_complexity": ("model_escalate", "check_complexity", {}),
    "escalate_to_flagship": ("model_escalate", "consult", {}),
    "get_flagship_help": ("model_escalate", "help", {}),
    "refine_with_flagship": ("model_escalate", "refine", {}),
}


def get_new_tool_name(old_tool_name: str) -> Optional[Tuple[str, Optional[str], Dict[str, Any]]]:
    """
    Get new tool name and default mode for old tool name.
    
    Args:
        old_tool_name: Name of old tool
    
    Returns:
        Tuple of (new_tool_name, default_mode, additional_params) or None if not found
    """
    return OLD_TO_NEW_MAPPING.get(old_tool_name)


def migrate_tool_call(old_tool_name: str, **kwargs) -> Tuple[str, Dict[str, Any]]:
    """
    Migrate old tool call to new consolidated tool call.
    
    Args:
        old_tool_name: Name of old tool
        **kwargs: Original tool arguments
    
    Returns:
        Tuple of (new_tool_name, new_kwargs)
    
    Example:
        new_name, new_kwargs = migrate_tool_call("read_file", file_path="main.py")
        # Returns: ("fs_read", {"file_path": "main.py", "mode": "read"})
    """
    mapping = get_new_tool_name(old_tool_name)
    
    if not mapping:
        # Tool not found in mapping - return as-is
        return old_tool_name, kwargs
    
    new_tool_name, default_mode, additional_params = mapping
    
    # Build new kwargs
    new_kwargs = {**additional_params, **kwargs}
    
    # Add mode if default_mode is provided and mode not already in kwargs
    if default_mode and "mode" not in new_kwargs:
        new_kwargs["mode"] = default_mode
    
    # Special handling for some tools
    if old_tool_name == "git_add":
        # git_add(files=...) → git_modify(action="add", files=...)
        if "files" in kwargs:
            new_kwargs["files"] = kwargs["files"]
    
    elif old_tool_name == "git_commit":
        # git_commit(message=...) → git_modify(action="commit", message=...)
        if "message" in kwargs:
            new_kwargs["message"] = kwargs["message"]
        if "files" in kwargs:
            new_kwargs["files"] = kwargs["files"]
    
    elif old_tool_name == "api_start_server":
        # api_start_server(app_file=..., port=...) → api_control(action="start", server_file=..., port=...)
        if "app_file" in kwargs:
            new_kwargs["server_file"] = kwargs["app_file"]
        if "port" in kwargs:
            new_kwargs["port"] = kwargs["port"]
    
    elif old_tool_name == "generate_code_comments":
        # generate_code_comments(code_file=...) → docs_generate(mode="comments", code_file=...)
        if "code_file" in kwargs:
            new_kwargs["code_file"] = kwargs["code_file"]
    
    elif old_tool_name == "update_changelog":
        # update_changelog(version=..., changes=...) → docs_generate(mode="changelog", version=..., changes=...)
        if "version" in kwargs:
            new_kwargs["version"] = kwargs["version"]
        if "changes" in kwargs:
            new_kwargs["changes"] = kwargs["changes"]
    
    elif old_tool_name == "add_dependency":
        # add_dependency(package_name=..., version=...) → deps_manage(mode="add", package_name=..., version=...)
        if "package_name" in kwargs:
            new_kwargs["package_name"] = kwargs["package_name"]
        if "version" in kwargs:
            new_kwargs["version"] = kwargs["version"]
    
    elif old_tool_name == "remove_dependency":
        # remove_dependency(package_name=...) → deps_manage(mode="remove", package_name=...)
        if "package_name" in kwargs:
            new_kwargs["package_name"] = kwargs["package_name"]
    
    elif old_tool_name == "extract_information":
        # extract_information(url=..., info_type=...) → web_analyze(url=..., mode="extract", info_type=...)
        if "info_type" in kwargs:
            new_kwargs["info_type"] = kwargs["info_type"]
    
    elif old_tool_name == "escalate_to_flagship":
        # escalate_to_flagship(task=..., context=..., model=...) → model_escalate(task=..., mode="consult", context=..., model=...)
        if "context" in kwargs:
            new_kwargs["context"] = kwargs["context"]
        if "issue" in kwargs:
            new_kwargs["issue"] = kwargs["issue"]
        if "attempts" in kwargs:
            new_kwargs["attempts"] = kwargs["attempts"]
        if "model" in kwargs:
            new_kwargs["model"] = kwargs["model"]
    
    elif old_tool_name == "refine_with_flagship":
        # refine_with_flagship(solution=..., feedback=..., model=...) → model_escalate(mode="refine", solution=..., feedback=..., model=...)
        if "solution" in kwargs:
            new_kwargs["solution"] = kwargs["solution"]
        if "feedback" in kwargs:
            new_kwargs["feedback"] = kwargs["feedback"]
        if "improvements" in kwargs:
            new_kwargs["improvements"] = kwargs["improvements"]
        if "model" in kwargs:
            new_kwargs["model"] = kwargs["model"]
    
    return new_tool_name, new_kwargs


def is_old_tool(tool_name: str) -> bool:
    """Check if tool name is from old registry"""
    return tool_name in OLD_TO_NEW_MAPPING


def get_migration_stats() -> Dict[str, int]:
    """Get migration statistics"""
    return {
        "old_tools": len(OLD_TO_NEW_MAPPING),
        "new_tools": 26,  # Consolidated tools
        "reduction": len(OLD_TO_NEW_MAPPING) - 26,
        "reduction_percent": round((1 - 26 / len(OLD_TO_NEW_MAPPING)) * 100, 1)
    }


# Export functions
__all__ = [
    "OLD_TO_NEW_MAPPING",
    "get_new_tool_name",
    "migrate_tool_call",
    "is_old_tool",
    "get_migration_stats",
]

