"""
Consolidated Documentation, Dependencies & Security Tools
Replaces: generate_readme, generate_api_docs, generate_code_comments, update_changelog, generate_architecture_doc, check_dependencies, check_security, update_dependencies, list_dependencies, add_dependency, remove_dependency, check_license, scan_security, check_secrets, analyze_dependencies, check_sql_injection, check_xss, security_audit
"""

import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tools.code_tools import ToolResult
from tools.documentation_tools import DocumentationTools
from tools.package_manager import PackageManagerTools
from tools.security_tools import SecurityTools


class DocTools:
    """Consolidated documentation, dependencies & security tools with mode-based operations"""
    
    @staticmethod
    def docs_generate(path: str = ".", mode: str = "readme", **kwargs) -> ToolResult:
        """
        Documentation generation.
        
        Replaces: generate_readme, generate_api_docs, generate_code_comments, update_changelog, generate_architecture_doc
        
        Args:
            path: Project path (default: current directory)
            mode: Operation mode:
                - "readme" (default): Generate README.md
                - "api_docs": Generate API documentation
                - "comments": Generate code comments
                - "changelog": Update CHANGELOG.md
                - "architecture": Generate architecture documentation
            **kwargs: Additional arguments for specific modes:
                - api_docs: api_file (optional)
                - comments: code_file (required)
                - changelog: version (optional), changes (optional)
                - architecture: output_file (optional)
        
        Returns:
            ToolResult with generated documentation based on mode
        
        Examples:
            docs_generate(mode="readme")  # Generate README
            docs_generate(mode="api_docs", api_file="app.py")  # Generate API docs
            docs_generate(mode="comments", code_file="main.py")  # Generate comments
            docs_generate(mode="changelog", version="1.0.0")  # Update changelog
            docs_generate(mode="architecture")  # Generate architecture doc
        """
        try:
            if mode == "readme":
                # Use DocumentationTools.generate_readme
                result = DocumentationTools.generate_readme(path=path)
                return result
            elif mode == "api_docs":
                # Use DocumentationTools.generate_api_docs
                api_file = kwargs.get("api_file")
                result = DocumentationTools.generate_api_docs(path=path, api_file=api_file)
                return result
            elif mode == "comments":
                # Use DocumentationTools.generate_code_comments
                code_file = kwargs.get("code_file")
                if not code_file:
                    return ToolResult(
                        success=False,
                        result=None,
                        error="code_file required for mode='comments'"
                    )
                result = DocumentationTools.generate_code_comments(code_file, path=path)
                return result
            elif mode == "changelog":
                # Use DocumentationTools.update_changelog
                version = kwargs.get("version")
                changes = kwargs.get("changes")
                result = DocumentationTools.update_changelog(path=path, version=version, changes=changes)
                return result
            elif mode == "architecture":
                # Use DocumentationTools.generate_architecture_doc
                output_file = kwargs.get("output_file")
                result = DocumentationTools.generate_architecture_doc(path=path, output_file=output_file)
                return result
            else:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Invalid mode: {mode}. Supported modes: 'readme', 'api_docs', 'comments', 'changelog', 'architecture'"
                )
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error in docs_generate with mode '{mode}': {str(e)}"
            )
    
    @staticmethod
    def deps_manage(path: str = ".", mode: str = "check", **kwargs) -> ToolResult:
        """
        Manage and audit dependencies.
        
        Replaces: check_dependencies, check_security, update_dependencies, list_dependencies, add_dependency, remove_dependency, check_license
        
        Args:
            path: Project path (default: current directory)
            mode: Operation mode:
                - "check" (default): Check dependency status
                - "security": Check security vulnerabilities
                - "update": Update dependencies
                - "list": List all dependencies
                - "add": Add dependency
                - "remove": Remove dependency
                - "license": Check package licenses
            **kwargs: Additional arguments for specific modes:
                - add: package_name (required), version (optional)
                - remove: package_name (required)
        
        Returns:
            ToolResult with dependency information based on mode
        
        Examples:
            deps_manage(mode="check")  # Check dependencies
            deps_manage(mode="security")  # Check security
            deps_manage(mode="list")  # List dependencies
            deps_manage(mode="add", package_name="flask")  # Add dependency
            deps_manage(mode="remove", package_name="flask")  # Remove dependency
            deps_manage(mode="license")  # Check licenses
        """
        try:
            if mode == "check":
                # Use PackageManagerTools.check_dependencies
                result = PackageManagerTools.check_dependencies(path=path)
                return result
            elif mode == "security":
                # Use PackageManagerTools.check_security
                result = PackageManagerTools.check_security(path=path)
                return result
            elif mode == "update":
                # Use PackageManagerTools.update_dependencies
                result = PackageManagerTools.update_dependencies(path=path)
                return result
            elif mode == "list":
                # Use PackageManagerTools.list_dependencies
                result = PackageManagerTools.list_dependencies(path=path)
                return result
            elif mode == "add":
                # Use PackageManagerTools.add_dependency
                package_name = kwargs.get("package_name")
                version = kwargs.get("version")
                if not package_name:
                    return ToolResult(
                        success=False,
                        result=None,
                        error="package_name required for mode='add'"
                    )
                result = PackageManagerTools.add_dependency(package_name, version=version, path=path)
                return result
            elif mode == "remove":
                # Use PackageManagerTools.remove_dependency
                package_name = kwargs.get("package_name")
                if not package_name:
                    return ToolResult(
                        success=False,
                        result=None,
                        error="package_name required for mode='remove'"
                    )
                result = PackageManagerTools.remove_dependency(package_name, path=path)
                return result
            elif mode == "license":
                # Use PackageManagerTools.check_license
                result = PackageManagerTools.check_license(path=path)
                return result
            else:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Invalid mode: {mode}. Supported modes: 'check', 'security', 'update', 'list', 'add', 'remove', 'license'"
                )
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error in deps_manage with mode '{mode}': {str(e)}"
            )
    
    @staticmethod
    def security_scan(path: str = ".", mode: str = "general", scan_types: List[str] = None) -> ToolResult:
        """
        General and targeted security scanning.
        
        Replaces: scan_security, check_secrets, analyze_dependencies, check_sql_injection, check_xss, security_audit
        
        Args:
            path: Project path (default: current directory)
            mode: Operation mode:
                - "general" (default): General security scan
                - "secrets": Check for exposed secrets
                - "dependencies": Analyze dependency security
                - "sql_injection": Check for SQL injection vulnerabilities
                - "xss": Check for XSS vulnerabilities
                - "audit": Comprehensive security audit
            scan_types: List of scan types (optional, for general mode)
        
        Returns:
            ToolResult with security scan results based on mode
        
        Examples:
            security_scan(mode="general")  # General security scan
            security_scan(mode="secrets")  # Check for secrets
            security_scan(mode="sql_injection")  # Check SQL injection
            security_scan(mode="xss")  # Check XSS
            security_scan(mode="audit")  # Comprehensive audit
        """
        try:
            if mode == "general":
                # Use SecurityTools.scan_security
                result = SecurityTools.scan_security(path=path, scan_types=scan_types)
                return result
            elif mode == "secrets":
                # Use SecurityTools.check_secrets
                result = SecurityTools.check_secrets(path=path)
                return result
            elif mode == "dependencies":
                # Use SecurityTools.analyze_dependencies
                result = SecurityTools.analyze_dependencies(path=path)
                return result
            elif mode == "sql_injection":
                # Use SecurityTools.check_sql_injection
                result = SecurityTools.check_sql_injection(path=path)
                return result
            elif mode == "xss":
                # Use SecurityTools.check_xss
                result = SecurityTools.check_xss(path=path)
                return result
            elif mode == "audit":
                # Use SecurityTools.security_audit
                result = SecurityTools.security_audit(path=path)
                return result
            else:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Invalid mode: {mode}. Supported modes: 'general', 'secrets', 'dependencies', 'sql_injection', 'xss', 'audit'"
                )
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error in security_scan with mode '{mode}': {str(e)}"
            )

