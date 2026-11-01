"""
Project Scanner tools for agents to understand project structure and context
"""
import os
import re
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass

from tools.code_tools import ToolResult
from tools.file_tools import FileTools


class ProjectScanner:
    """Tools for scanning project structure and understanding context"""
    
    # Common entry point files
    ENTRY_POINT_FILES = [
        "main.py", "app.py", "application.py", "run.py", "server.py",
        "index.py", "__main__.py", "manage.py",
        "index.js", "app.js", "server.js", "main.js",
        "index.ts", "app.ts", "server.ts", "main.ts",
        "index.html", "index.htm",
        "main.go", "main.rs", "main.cpp", "main.c",
        "Cargo.toml", "package.json", "pom.xml", "build.gradle",
    ]
    
    # Common config files
    CONFIG_FILES = [
        "requirements.txt", "requirements-dev.txt", "requirements.in",
        "package.json", "package-lock.json", "yarn.lock",
        "pyproject.toml", "setup.py", "setup.cfg",
        "Pipfile", "Pipfile.lock", "poetry.lock",
        "go.mod", "go.sum", "Cargo.toml", "Cargo.lock",
        "pom.xml", "build.gradle", "build.sbt",
        "Dockerfile", "docker-compose.yml", ".dockerignore",
        "Makefile", "CMakeLists.txt",
        "config.yaml", "config.yml", "config.json",
        ".gitignore", ".gitattributes",
        "tsconfig.json", "webpack.config.js", "vite.config.js",
        ".eslintrc", ".prettierrc", ".editorconfig",
    ]
    
    # Common test patterns
    TEST_PATTERNS = [
        "test_*.py", "*_test.py", "tests.py",
        "*.test.js", "*.test.ts", "*.spec.js", "*.spec.ts",
        "*_test.go", "*_test.rs",
        "test/", "tests/", "__tests__/",
    ]
    
    # Environment file patterns
    ENV_FILE_PATTERNS = [
        ".env", ".env.local", ".env.development", ".env.production",
        ".env.test", ".env.example", ".env.template",
    ]
    
    # Framework detection patterns
    FRAMEWORK_PATTERNS = {
        "Flask": [r"from flask import", r"import flask", r"Flask\("],
        "FastAPI": [r"from fastapi import", r"import fastapi", r"FastAPI\("],
        "Django": [r"from django", r"import django", r"DJANGO_SETTINGS_MODULE"],
        "React": [r"react", r"ReactDOM", r"create-react-app"],
        "Vue": [r"vue", r"Vue\.", r"@vue"],
        "Express": [r"express", r"require\(['\"]express['\"]"],
        "Next.js": [r"next", r"NextConfig", r"next.config"],
        "Spring": [r"@SpringBootApplication", r"org.springframework"],
        "Rails": [r"Rails\.application", r"Gemfile"],
        "Rocket": [r"#\[rocket::", r"rocket::"],
    }
    
    @staticmethod
    def _is_safe_path(filepath: str) -> tuple[bool, Optional[str]]:
        """Check if filepath is safe to access (delegates to FileTools)"""
        return FileTools._is_safe_path(filepath)
    
    @staticmethod
    def _detect_frameworks(path: Path) -> List[str]:
        """Detect frameworks used in project"""
        detected = []
        
        # Check Python files
        for py_file in path.rglob("*.py"):
            try:
                content = py_file.read_text(encoding='utf-8', errors='ignore')
                for framework, patterns in ProjectScanner.FRAMEWORK_PATTERNS.items():
                    if framework not in detected:
                        for pattern in patterns:
                            if re.search(pattern, content, re.IGNORECASE):
                                detected.append(framework)
                                break
            except Exception:
                continue
            
            # Limit check to first 10 Python files for performance
            if py_file.stat().st_size > 0 and len(detected) >= 3:
                break
        
        # Check config files
        for config_file in ["package.json", "requirements.txt", "Pipfile", "Cargo.toml"]:
            config_path = path / config_file
            if config_path.exists():
                try:
                    content = config_path.read_text(encoding='utf-8', errors='ignore')
                    for framework, patterns in ProjectScanner.FRAMEWORK_PATTERNS.items():
                        if framework not in detected:
                            for pattern in patterns:
                                if re.search(pattern, content, re.IGNORECASE):
                                    detected.append(framework)
                                    break
                except Exception:
                    continue
        
        return detected
    
    @staticmethod
    def scan_project(path: str = ".") -> ToolResult:
        """
        Scan project directory and return structured summary.
        
        Returns:
            - Source directories
            - Entry points
            - Config files
            - Test directories
            - Environment files
            - Frameworks detected
            - Main services/modules
        
        Args:
            path: Path to project directory (default: current directory)
        
        Returns:
            ToolResult with project structure summary
        """
        try:
            # Validate and resolve path
            is_safe, error = ProjectScanner._is_safe_path(path)
            if not is_safe:
                return ToolResult(
                    success=False,
                    result=None,
                    error=error or "Path is not safe to access"
                )
            
            project_path = Path(path).resolve()
            if not project_path.exists():
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Path does not exist: {path}"
                )
            
            if not project_path.is_dir():
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Path is not a directory: {path}"
                )
            
            # Initialize result structure
            structure = {
                "path": str(project_path),
                "source_directories": [],
                "entry_points": [],
                "config_files": [],
                "test_directories": [],
                "test_files": [],
                "env_files": [],
                "frameworks": [],
                "modules": [],
                "main_files": []
            }
            
            # Find source directories (common Python/JS project structure)
            source_patterns = ["src/", "lib/", "app/", "apps/", "packages/"]
            for pattern in source_patterns:
                src_dir = project_path / pattern
                if src_dir.exists() and src_dir.is_dir():
                    structure["source_directories"].append(str(src_dir.relative_to(project_path)))
            
            # If no standard src dirs, check for top-level packages
            if not structure["source_directories"]:
                for item in project_path.iterdir():
                    if item.is_dir() and not item.name.startswith('.') and (item / "__init__.py").exists():
                        structure["source_directories"].append(item.name)
            
            # Find entry points
            for entry_file in ProjectScanner.ENTRY_POINT_FILES:
                entry_path = project_path / entry_file
                if entry_path.exists() and entry_path.is_file():
                    structure["entry_points"].append(entry_file)
            
            # Also check for entry points in common locations
            for src_dir in structure["source_directories"]:
                src_path = project_path / src_dir
                if src_path.exists():
                    for entry_file in ProjectScanner.ENTRY_POINT_FILES[:10]:  # Limit check
                        entry_path = src_path / entry_file
                        if entry_path.exists():
                            structure["entry_points"].append(str(entry_path.relative_to(project_path)))
            
            # Find config files
            for config_file in ProjectScanner.CONFIG_FILES:
                config_path = project_path / config_file
                if config_path.exists() and config_path.is_file():
                    structure["config_files"].append(config_file)
            
            # Find test directories and files
            test_dirs = ["test", "tests", "__tests__", "spec", "specs"]
            for test_dir in test_dirs:
                test_path = project_path / test_dir
                if test_path.exists() and test_path.is_dir():
                    structure["test_directories"].append(test_dir)
                    
                    # Count test files
                    test_files_count = 0
                    for pattern in ["test_*.py", "*_test.py", "*.test.js", "*.spec.js"]:
                        test_files_count += len(list(test_path.glob(pattern)))
                    if test_files_count > 0:
                        structure["test_files"].append(f"{test_dir}/ ({test_files_count} files)")
            
            # Also check for test files in root
            for pattern in ["test_*.py", "*_test.py"]:
                test_files = list(project_path.glob(pattern))
                if test_files:
                    structure["test_files"].extend([f.name for f in test_files[:5]])  # Limit
            
            # Find environment files
            for env_pattern in ProjectScanner.ENV_FILE_PATTERNS:
                env_path = project_path / env_pattern
                if env_path.exists() and env_path.is_file():
                    structure["env_files"].append(env_pattern)
            
            # Detect frameworks
            structure["frameworks"] = ProjectScanner._detect_frameworks(project_path)
            
            # Find main modules (Python packages with __init__.py)
            for item in project_path.iterdir():
                if item.is_dir() and not item.name.startswith('.') and not item.name.startswith('__'):
                    init_file = item / "__init__.py"
                    if init_file.exists():
                        structure["modules"].append(item.name)
            
            # Limit modules to first 20
            structure["modules"] = structure["modules"][:20]
            
            # Find main files (Python files that might be main entry points)
            for py_file in project_path.glob("*.py"):
                if py_file.name not in structure["entry_points"]:
                    try:
                        content = py_file.read_text(encoding='utf-8', errors='ignore')[:500]
                        if "if __name__" in content or "def main(" in content:
                            structure["main_files"].append(py_file.name)
                    except Exception:
                        continue
                    
                    if len(structure["main_files"]) >= 10:
                        break
            
            return ToolResult(
                success=True,
                result=structure,
                metadata={
                    "path": str(project_path),
                    "entry_points_count": len(structure["entry_points"]),
                    "config_files_count": len(structure["config_files"]),
                    "frameworks_count": len(structure["frameworks"]),
                    "modules_count": len(structure["modules"]),
                }
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error scanning project: {str(e)}"
            )
    
    @staticmethod
    def find_entrypoints(path: str = ".") -> ToolResult:
        """
        Find application entry points.
        
        Args:
            path: Path to project directory (default: current directory)
        
        Returns:
            ToolResult with list of entry points
        """
        try:
            # Validate path
            is_safe, error = ProjectScanner._is_safe_path(path)
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
            
            entry_points = []
            
            # Check common entry point files
            for entry_file in ProjectScanner.ENTRY_POINT_FILES:
                entry_path = project_path / entry_file
                if entry_path.exists() and entry_path.is_file():
                    entry_info = {
                        "file": entry_file,
                        "path": str(entry_path.relative_to(project_path)),
                        "absolute_path": str(entry_path)
                    }
                    
                    # Check if it's executable or has main block
                    try:
                        content = entry_path.read_text(encoding='utf-8', errors='ignore')
                        if "if __name__" in content or "def main(" in content:
                            entry_info["has_main"] = True
                        else:
                            entry_info["has_main"] = False
                    except Exception:
                        entry_info["has_main"] = None
                    
                    entry_points.append(entry_info)
            
            return ToolResult(
                success=True,
                result={
                    "entry_points": entry_points,
                    "count": len(entry_points)
                },
                metadata={
                    "path": str(project_path),
                    "count": len(entry_points)
                }
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error finding entry points: {str(e)}"
            )
    
    @staticmethod
    def list_configs(path: str = ".") -> ToolResult:
        """
        List configuration files in project.
        
        Args:
            path: Path to project directory (default: current directory)
        
        Returns:
            ToolResult with list of config files
        """
        try:
            # Validate path
            is_safe, error = ProjectScanner._is_safe_path(path)
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
            
            config_files = []
            
            # Check common config files
            for config_file in ProjectScanner.CONFIG_FILES:
                config_path = project_path / config_file
                if config_path.exists() and config_path.is_file():
                    config_info = {
                        "file": config_file,
                        "path": str(config_path.relative_to(project_path)),
                        "absolute_path": str(config_path),
                        "size": config_path.stat().st_size
                    }
                    
                    # Try to detect config type
                    if "requirements" in config_file or "Pipfile" in config_file:
                        config_info["type"] = "python_dependencies"
                    elif "package.json" in config_file or "yarn.lock" in config_file:
                        config_info["type"] = "javascript_dependencies"
                    elif "Dockerfile" in config_file or "docker-compose" in config_file:
                        config_info["type"] = "docker"
                    elif config_file.startswith(".env"):
                        config_info["type"] = "environment"
                    elif "config" in config_file.lower():
                        config_info["type"] = "application_config"
                    else:
                        config_info["type"] = "other"
                    
                    config_files.append(config_info)
            
            return ToolResult(
                success=True,
                result={
                    "config_files": config_files,
                    "count": len(config_files)
                },
                metadata={
                    "path": str(project_path),
                    "count": len(config_files)
                }
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error listing configs: {str(e)}"
            )
    
    @staticmethod
    def find_tests(path: str = ".") -> ToolResult:
        """
        Find test files and test directories.
        
        Args:
            path: Path to project directory (default: current directory)
        
        Returns:
            ToolResult with list of test files and directories
        """
        try:
            # Validate path
            is_safe, error = ProjectScanner._is_safe_path(path)
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
            
            test_directories = []
            test_files = []
            
            # Find test directories
            test_dir_patterns = ["test", "tests", "__tests__", "spec", "specs"]
            for pattern in test_dir_patterns:
                test_dir = project_path / pattern
                if test_dir.exists() and test_dir.is_dir():
                    test_dir_info = {
                        "directory": pattern,
                        "path": str(test_dir.relative_to(project_path))
                    }
                    
                    # Count test files in directory
                    test_count = 0
                    for test_file in test_dir.rglob("test_*.py"):
                        test_count += 1
                    for test_file in test_dir.rglob("*_test.py"):
                        test_count += 1
                    for test_file in test_dir.rglob("*.test.js"):
                        test_count += 1
                    for test_file in test_dir.rglob("*.spec.js"):
                        test_count += 1
                    
                    test_dir_info["test_files_count"] = test_count
                    test_directories.append(test_dir_info)
            
            # Find test files in root
            for pattern in ["test_*.py", "*_test.py", "*.test.js", "*.spec.js"]:
                for test_file in project_path.glob(pattern):
                    test_file_info = {
                        "file": test_file.name,
                        "path": str(test_file.relative_to(project_path))
                    }
                    test_files.append(test_file_info)
            
            return ToolResult(
                success=True,
                result={
                    "test_directories": test_directories,
                    "test_files": test_files,
                    "total_tests": len(test_files) + sum(d.get("test_files_count", 0) for d in test_directories)
                },
                metadata={
                    "path": str(project_path),
                    "directories_count": len(test_directories),
                    "files_count": len(test_files)
                }
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error finding tests: {str(e)}"
            )
    
    @staticmethod
    def find_env_files(path: str = ".") -> ToolResult:
        """
        Find environment files (.env, .env.example, etc.).
        
        Args:
            path: Path to project directory (default: current directory)
        
        Returns:
            ToolResult with list of environment files
        """
        try:
            # Validate path
            is_safe, error = ProjectScanner._is_safe_path(path)
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
            
            env_files = []
            
            # Find environment files
            for env_pattern in ProjectScanner.ENV_FILE_PATTERNS:
                env_path = project_path / env_pattern
                if env_path.exists() and env_path.is_file():
                    env_info = {
                        "file": env_pattern,
                        "path": str(env_path.relative_to(project_path)),
                        "absolute_path": str(env_path),
                        "size": env_path.stat().st_size
                    }
                    
                    # Determine if it's an example/template file
                    if ".example" in env_pattern or ".template" in env_pattern:
                        env_info["is_template"] = True
                    else:
                        env_info["is_template"] = False
                    
                    env_files.append(env_info)
            
            return ToolResult(
                success=True,
                result={
                    "env_files": env_files,
                    "count": len(env_files)
                },
                metadata={
                    "path": str(project_path),
                    "count": len(env_files)
                }
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error finding env files: {str(e)}"
            )

