"""
Documentation tools for agents to generate and manage documentation
"""
import re
import ast
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from tools.code_tools import ToolResult
from tools.file_tools import FileTools
from tools.project_scanner import ProjectScanner


class DocumentationTools:
    """Tools for generating and managing documentation"""
    
    @staticmethod
    def _is_safe_path(filepath: str) -> tuple[bool, Optional[str]]:
        """Check if filepath is safe to access (delegates to FileTools)"""
        return FileTools._is_safe_path(filepath)
    
    @staticmethod
    def _extract_module_info(code: str) -> Dict[str, Any]:
        """Extract module information from Python code"""
        try:
            tree = ast.parse(code)
            module_info = {
                "module_docstring": ast.get_docstring(tree),
                "functions": [],
                "classes": [],
                "imports": []
            }
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_info = {
                        "name": node.name,
                        "docstring": ast.get_docstring(node),
                        "args": [arg.arg for arg in node.args.args],
                        "lineno": node.lineno
                    }
                    module_info["functions"].append(func_info)
                
                elif isinstance(node, ast.ClassDef):
                    class_info = {
                        "name": node.name,
                        "docstring": ast.get_docstring(node),
                        "methods": [],
                        "lineno": node.lineno
                    }
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            class_info["methods"].append({
                                "name": item.name,
                                "docstring": ast.get_docstring(item)
                            })
                    module_info["classes"].append(class_info)
                
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.ImportFrom):
                        module_info["imports"].append(f"from {node.module} import ...")
                    else:
                        for alias in node.names:
                            module_info["imports"].append(f"import {alias.name}")
            
            return module_info
        except Exception:
            return {
                "module_docstring": None,
                "functions": [],
                "classes": [],
                "imports": []
            }
    
    @staticmethod
    def generate_readme(path: str = ".") -> ToolResult:
        """
        Generate README.md from project structure.
        
        Args:
            path: Project path (default: current directory)
        
        Returns:
            ToolResult with generated README content
        """
        try:
            # Validate path
            is_safe, error = DocumentationTools._is_safe_path(path)
            if not is_safe:
                return ToolResult(
                    success=False,
                    result=None,
                    error=error or "Path is not safe to access"
                )
            
            project_path = Path(path).resolve()
            if not project_path.exists() or not project_path.is_dir():
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Invalid project path: {path}"
                )
            
            # Scan project to get structure
            scan_result = ProjectScanner.scan_project(str(project_path))
            if not scan_result.success:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Failed to scan project: {scan_result.error}"
                )
            
            structure = scan_result.result
            project_name = project_path.name
            
            # Get config info
            config_result = ProjectScanner.list_configs(str(project_path))
            configs = config_result.result.get("config_files", []) if config_result.success else []
            
            # Build README content
            readme_lines = [
                f"# {project_name}",
                "",
                "## Description",
                "",
                f"{project_name} is a Python project.",
                "",
                "## Installation",
                "",
                "```bash",
                "pip install -r requirements.txt",
                "```",
                "",
            ]
            
            # Add setup instructions if applicable
            if "requirements.txt" in configs:
                readme_lines.extend([
                    "## Requirements",
                    "",
                    "See `requirements.txt` for dependencies.",
                    "",
                ])
            
            # Add entry points
            if structure.get("entry_points"):
                readme_lines.extend([
                    "## Usage",
                    "",
                ])
                for entry_point in structure["entry_points"][:3]:  # Limit to 3
                    readme_lines.append(f"```bash\npython {entry_point}\n```")
                readme_lines.append("")
            
            # Add project structure
            if structure.get("source_directories"):
                readme_lines.extend([
                    "## Project Structure",
                    "",
                    "```",
                ])
                for src_dir in structure["source_directories"][:5]:  # Limit to 5
                    readme_lines.append(f"{src_dir}/")
                readme_lines.extend(["```", ""])
            
            # Add frameworks detected
            if structure.get("frameworks"):
                readme_lines.extend([
                    "## Frameworks",
                    "",
                    f"Built with: {', '.join(structure['frameworks'])}",
                    "",
                ])
            
            # Add testing section
            if structure.get("test_directories") or structure.get("test_files"):
                readme_lines.extend([
                    "## Testing",
                    "",
                    "```bash",
                    "pytest",
                    "```",
                    "",
                ])
            
            # Add license section
            readme_lines.extend([
                "## License",
                "",
                "MIT License",
                "",
            ])
            
            readme_content = "\n".join(readme_lines)
            
            return ToolResult(
                success=True,
                result={
                    "readme": readme_content,
                    "project_name": project_name
                },
                metadata={
                    "path": str(project_path),
                    "project_name": project_name,
                    "sections": len([s for s in readme_content.split("##")]) - 1
                }
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error generating README: {str(e)}"
            )
    
    @staticmethod
    def generate_api_docs(path: str = ".", output_format: str = "openapi") -> ToolResult:
        """
        Generate API documentation (OpenAPI/Swagger).
        
        Args:
            path: Project path (default: current directory)
            output_format: Output format ("openapi", "swagger") (default: "openapi")
        
        Returns:
            ToolResult with API documentation
        """
        try:
            # Validate path
            is_safe, error = DocumentationTools._is_safe_path(path)
            if not is_safe:
                return ToolResult(
                    success=False,
                    result=None,
                    error=error or "Path is not safe to access"
                )
            
            project_path = Path(path).resolve()
            
            # Find API files (Flask, FastAPI, Django)
            api_files = []
            for py_file in project_path.rglob("*.py"):
                try:
                    content = py_file.read_text(encoding='utf-8', errors='ignore')
                    # Detect Flask
                    if "Flask" in content or "from flask import" in content:
                        if "@app.route" in content:
                            api_files.append(("flask", py_file, content))
                    # Detect FastAPI
                    elif "FastAPI" in content or "from fastapi import" in content:
                        if "@app." in content or "@router." in content:
                            api_files.append(("fastapi", py_file, content))
                    # Detect Django
                    elif "from django.urls import" in content or "from rest_framework" in content:
                        if "urlpatterns" in content or "@api_view" in content:
                            api_files.append(("django", py_file, content))
                except Exception:
                    continue
                
                if len(api_files) >= 10:  # Limit to 10 files
                    break
            
            if not api_files:
                return ToolResult(
                    success=False,
                    result=None,
                    error="No API files found. Looking for Flask, FastAPI, or Django routes."
                )
            
            # Extract endpoints
            endpoints = []
            
            for framework, api_file, content in api_files:
                if framework == "flask":
                    # Extract Flask routes
                    route_pattern = r"@app\.route\(['\"]([^'\"]+)['\"].*?\)\s*\n\s*def\s+(\w+)"
                    matches = re.finditer(route_pattern, content, re.MULTILINE)
                    for match in matches:
                        endpoints.append({
                            "path": match.group(1),
                            "method": "GET",  # Default, could parse more
                            "function": match.group(2),
                            "file": str(api_file.relative_to(project_path)),
                            "framework": "flask"
                        })
                
                elif framework == "fastapi":
                    # Extract FastAPI routes
                    route_patterns = [
                        (r"@app\.(get|post|put|delete|patch)\(['\"]([^'\"]+)['\"]", "app"),
                        (r"@router\.(get|post|put|delete|patch)\(['\"]([^'\"]+)['\"]", "router")
                    ]
                    for pattern, decorator_type in route_patterns:
                        matches = re.finditer(pattern, content, re.MULTILINE)
                        for match in matches:
                            endpoints.append({
                                "path": match.group(2),
                                "method": match.group(1).upper(),
                                "function": "unknown",
                                "file": str(api_file.relative_to(project_path)),
                                "framework": "fastapi"
                            })
            
            # Generate OpenAPI spec
            project_name = project_path.name
            openapi_spec = {
                "openapi": "3.0.0",
                "info": {
                    "title": project_name,
                    "version": "1.0.0",
                    "description": f"API documentation for {project_name}"
                },
                "paths": {}
            }
            
            # Add endpoints to spec
            for endpoint in endpoints:
                path = endpoint["path"]
                method = endpoint["method"].lower()
                
                if path not in openapi_spec["paths"]:
                    openapi_spec["paths"][path] = {}
                
                openapi_spec["paths"][path][method] = {
                    "summary": f"{endpoint['function']}",
                    "operationId": endpoint['function'],
                    "responses": {
                        "200": {
                            "description": "Successful response",
                            "content": {
                                "application/json": {
                                    "schema": {"type": "object"}
                                }
                            }
                        }
                    }
                }
            
            if output_format.lower() == "swagger":
                # Convert to Swagger 2.0 if needed
                swagger_spec = {
                    "swagger": "2.0",
                    "info": openapi_spec["info"],
                    "paths": openapi_spec["paths"]
                }
                return ToolResult(
                    success=True,
                    result={
                        "spec": json.dumps(swagger_spec, indent=2),
                        "format": "swagger",
                        "endpoints": endpoints
                    },
                    metadata={
                        "path": str(project_path),
                        "format": "swagger",
                        "endpoint_count": len(endpoints)
                    }
                )
            else:
                return ToolResult(
                    success=True,
                    result={
                        "spec": json.dumps(openapi_spec, indent=2),
                        "format": "openapi",
                        "endpoints": endpoints
                    },
                    metadata={
                        "path": str(project_path),
                        "format": "openapi",
                        "endpoint_count": len(endpoints)
                    }
                )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error generating API docs: {str(e)}"
            )
    
    @staticmethod
    def generate_code_comments(
        filepath: str,
        path: str = ".",
        overwrite: bool = False
    ) -> ToolResult:
        """
        Add/improve code comments.
        
        Args:
            filepath: Python file to add comments to
            path: Project path (default: current directory)
            overwrite: Whether to overwrite existing comments (default: False)
        
        Returns:
            ToolResult with code with added comments
        """
        try:
            # Validate path
            is_safe, error = DocumentationTools._is_safe_path(filepath)
            if not is_safe:
                return ToolResult(
                    success=False,
                    result=None,
                    error=error or "File path is not safe to access"
                )
            
            project_path = Path(path).resolve()
            file_path = (project_path / filepath).resolve()
            
            if not file_path.exists() or not file_path.is_file():
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"File not found: {filepath}"
                )
            
            # Only process Python files
            if file_path.suffix != ".py":
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Only Python files are supported. Got: {file_path.suffix}"
                )
            
            # Read file
            original_content = file_path.read_text(encoding='utf-8', errors='ignore')
            
            # Extract module info
            module_info = DocumentationTools._extract_module_info(original_content)
            
            # Generate commented code
            lines = original_content.split('\n')
            commented_lines = []
            i = 0
            
            while i < len(lines):
                line = lines[i]
                stripped = line.strip()
                
                # Check if function or class definition
                if stripped.startswith('def ') and not overwrite:
                    # Check if already has docstring on next lines
                    has_docstring = False
                    j = i + 1
                    while j < len(lines) and (lines[j].strip().startswith('"""') or lines[j].strip().startswith("'''") or not lines[j].strip()):
                        if '"""' in lines[j] or "'''" in lines[j]:
                            has_docstring = True
                            break
                        if lines[j].strip() and not lines[j].strip().startswith('#'):
                            break
                        j += 1
                    
                    # Add comment if no docstring
                    if not has_docstring:
                        commented_lines.append(line)
                        # Extract function name
                        func_match = re.match(r'def\s+(\w+)', stripped)
                        if func_match:
                            func_name = func_match.group(1)
                            indent = len(line) - len(line.lstrip())
                            docstring = f'{" " * (indent + 4)}"""{func_name} - TODO: Add description"""'
                            commented_lines.append(docstring)
                            i += 1
                            continue
                
                # Check if class definition
                if stripped.startswith('class ') and not overwrite:
                    has_docstring = False
                    j = i + 1
                    while j < len(lines) and (lines[j].strip().startswith('"""') or lines[j].strip().startswith("'''") or not lines[j].strip()):
                        if '"""' in lines[j] or "'''" in lines[j]:
                            has_docstring = True
                            break
                        if lines[j].strip() and not lines[j].strip().startswith('#'):
                            break
                        j += 1
                    
                    if not has_docstring:
                        commented_lines.append(line)
                        class_match = re.match(r'class\s+(\w+)', stripped)
                        if class_match:
                            class_name = class_match.group(1)
                            indent = len(line) - len(line.lstrip())
                            docstring = f'{" " * (indent + 4)}"""{class_name} - TODO: Add description"""'
                            commented_lines.append(docstring)
                            i += 1
                            continue
                
                commented_lines.append(line)
                i += 1
            
            commented_content = '\n'.join(commented_lines)
            
            # Count comments added
            original_functions = len(module_info["functions"])
            original_classes = len(module_info["classes"])
            
            return ToolResult(
                success=True,
                result={
                    "commented_code": commented_content,
                    "original_code": original_content,
                    "functions_with_comments": original_functions,
                    "classes_with_comments": original_classes
                },
                metadata={
                    "path": str(project_path),
                    "file": filepath,
                    "functions": original_functions,
                    "classes": original_classes
                }
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error generating code comments: {str(e)}"
            )
    
    @staticmethod
    def extract_api_spec(path: str = ".") -> ToolResult:
        """
        Extract API specification from code.
        
        Args:
            path: Project path (default: current directory)
        
        Returns:
            ToolResult with extracted API specification
        """
        # This is similar to generate_api_docs but focuses on extraction
        result = DocumentationTools.generate_api_docs(path, output_format="openapi")
        
        if result.success:
            return ToolResult(
                success=True,
                result={
                    "api_spec": result.result.get("spec"),
                    "endpoints": result.result.get("endpoints", []),
                    "format": result.result.get("format")
                },
                metadata=result.metadata
            )
        else:
            return result
    
    @staticmethod
    def update_changelog(
        version: str = None,
        changes: List[str] = None,
        path: str = "."
    ) -> ToolResult:
        """
        Update CHANGELOG.md.
        
        Args:
            version: Version number (default: auto-detect from project)
            changes: List of changes (default: empty)
            path: Project path (default: current directory)
        
        Returns:
            ToolResult with updated changelog content
        """
        try:
            # Validate path
            is_safe, error = DocumentationTools._is_safe_path(path)
            if not is_safe:
                return ToolResult(
                    success=False,
                    result=None,
                    error=error or "Path is not safe to access"
                )
            
            project_path = Path(path).resolve()
            changelog_path = project_path / "CHANGELOG.md"
            
            # Get version if not provided
            if not version:
                version = datetime.now().strftime("%Y.%m.%d")
            
            if changes is None:
                changes = []
            
            # Read existing changelog if it exists
            existing_content = ""
            if changelog_path.exists():
                existing_content = changelog_path.read_text(encoding='utf-8', errors='ignore')
            
            # Generate new entry
            today = datetime.now().strftime("%Y-%m-%d")
            new_entry = [
                f"## [{version}] - {today}",
                ""
            ]
            
            if changes:
                new_entry.append("### Added")
                for change in changes:
                    new_entry.append(f"- {change}")
            else:
                new_entry.append("### Changed")
                new_entry.append("- Update changelog")
            
            new_entry.append("")
            
            # Combine with existing content
            if existing_content:
                # Try to find where to insert (after title if exists)
                lines = existing_content.split('\n')
                title_line = -1
                for i, line in enumerate(lines):
                    if line.strip().startswith('#') and 'changelog' in line.lower():
                        title_line = i
                        break
                
                if title_line >= 0:
                    # Insert after title and blank line
                    new_content = '\n'.join(lines[:title_line + 2]) + '\n' + '\n'.join(new_entry) + '\n'.join(lines[title_line + 2:])
                else:
                    new_content = '\n'.join(new_entry) + '\n' + existing_content
            else:
                # Create new changelog
                new_content = f"# Changelog\n\nAll notable changes to this project will be documented in this file.\n\n" + '\n'.join(new_entry)
            
            return ToolResult(
                success=True,
                result={
                    "changelog": new_content,
                    "version": version,
                    "changes": changes
                },
                metadata={
                    "path": str(project_path),
                    "version": version,
                    "changes_count": len(changes)
                }
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error updating changelog: {str(e)}"
            )
    
    @staticmethod
    def generate_architecture_doc(path: str = ".") -> ToolResult:
        """
        Generate architecture documentation.
        
        Args:
            path: Project path (default: current directory)
        
        Returns:
            ToolResult with architecture documentation
        """
        try:
            # Validate path
            is_safe, error = DocumentationTools._is_safe_path(path)
            if not is_safe:
                return ToolResult(
                    success=False,
                    result=None,
                    error=error or "Path is not safe to access"
                )
            
            project_path = Path(path).resolve()
            
            # Scan project
            scan_result = ProjectScanner.scan_project(str(project_path))
            if not scan_result.success:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Failed to scan project: {scan_result.error}"
                )
            
            structure = scan_result.result
            project_name = project_path.name
            
            # Build architecture doc
            doc_lines = [
                f"# {project_name} - Architecture Documentation",
                "",
                f"Generated on {datetime.now().strftime('%Y-%m-%d')}",
                "",
                "## Overview",
                "",
                f"This document describes the architecture of {project_name}.",
                "",
                "## Project Structure",
                "",
                "### Source Directories",
                ""
            ]
            
            # Add source directories
            if structure.get("source_directories"):
                for src_dir in structure["source_directories"]:
                    doc_lines.append(f"- `{src_dir}/`")
            else:
                doc_lines.append("- Root directory")
            
            doc_lines.extend(["", "### Entry Points", ""])
            
            # Add entry points
            if structure.get("entry_points"):
                for entry_point in structure["entry_points"]:
                    doc_lines.append(f"- `{entry_point}`")
            else:
                doc_lines.append("- No entry points found")
            
            doc_lines.extend(["", "## Frameworks & Technologies", ""])
            
            # Add frameworks
            if structure.get("frameworks"):
                doc_lines.append(f"Built with: {', '.join(structure['frameworks'])}")
            else:
                doc_lines.append("- No frameworks detected")
            
            doc_lines.extend(["", "## Modules", ""])
            
            # Add modules
            if structure.get("modules"):
                for module in structure["modules"][:10]:  # Limit to 10
                    doc_lines.append(f"- `{module}`")
            else:
                doc_lines.append("- No modules found")
            
            doc_lines.extend(["", "## Configuration", ""])
            
            # Add config files
            config_result = ProjectScanner.list_configs(str(project_path))
            if config_result.success:
                configs = config_result.result.get("config_files", [])
                for config in configs[:10]:  # Limit to 10
                    doc_lines.append(f"- `{config}`")
            
            doc_lines.extend(["", "## Testing", ""])
            
            # Add test info
            if structure.get("test_directories"):
                for test_dir in structure["test_directories"]:
                    doc_lines.append(f"- Tests in `{test_dir}/`")
            
            doc_lines.append("")
            
            architecture_content = "\n".join(doc_lines)
            
            return ToolResult(
                success=True,
                result={
                    "architecture_doc": architecture_content,
                    "project_name": project_name
                },
                metadata={
                    "path": str(project_path),
                    "project_name": project_name,
                    "sections": len([s for s in architecture_content.split("##")]) - 1
                }
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error generating architecture doc: {str(e)}"
            )

