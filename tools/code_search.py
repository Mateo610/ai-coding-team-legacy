"""
Code Search tools for agents to search codebase for patterns, usages, definitions
"""
import re
import ast
from pathlib import Path
from typing import Dict, Any, Optional, List, Set
from collections import defaultdict

from tools.code_tools import ToolResult
from tools.file_tools import FileTools


class CodeSearchTools:
    """Tools for searching codebase for patterns, usages, definitions"""
    
    # Common file patterns for code search
    CODE_FILE_PATTERNS = [
        "*.py", "*.js", "*.ts", "*.jsx", "*.tsx",
        "*.go", "*.rs", "*.cpp", "*.c", "*.h",
        "*.java", "*.kt", "*.scala",
    ]
    
    # Ignore patterns (similar to .gitignore)
    IGNORE_PATTERNS = [
        "__pycache__", ".git", ".venv", "venv", "env",
        "node_modules", ".pytest_cache", ".mypy_cache",
        "dist", "build", "*.pyc", "*.pyo",
    ]
    
    @staticmethod
    def _is_safe_path(filepath: str) -> tuple[bool, Optional[str]]:
        """Check if filepath is safe to access (delegates to FileTools)"""
        return FileTools._is_safe_path(filepath)
    
    @staticmethod
    def _should_ignore(path: Path) -> bool:
        """Check if path should be ignored (gitignore-like)"""
        path_str = str(path)
        for pattern in CodeSearchTools.IGNORE_PATTERNS:
            if pattern in path_str:
                return True
        return False
    
    @staticmethod
    def _get_code_files(path: Path, file_pattern: str = "*.py") -> List[Path]:
        """Get all code files matching pattern"""
        code_files = []
        
        try:
            if path.is_file():
                if file_pattern == "*" or path.match(file_pattern):
                    if not CodeSearchTools._should_ignore(path):
                        code_files.append(path)
            elif path.is_dir():
                for file_path in path.rglob(file_pattern):
                    if not CodeSearchTools._should_ignore(file_path):
                        code_files.append(file_path)
        except Exception:
            pass
        
        return code_files[:500]  # Limit to 500 files for performance
    
    @staticmethod
    def search_code(
        pattern: str,
        path: str = ".",
        file_pattern: str = "*.py",
        context_lines: int = 3
    ) -> ToolResult:
        """
        Search for string/regex across repo.
        
        Returns: file:line:snippet for each match
        
        Args:
            pattern: Search pattern (string or regex)
            path: Path to search (default: current directory)
            file_pattern: File pattern to search (default: "*.py")
            context_lines: Number of context lines around match (default: 3)
        
        Returns:
            ToolResult with search results
        """
        try:
            # Validate path
            is_safe, error = CodeSearchTools._is_safe_path(path)
            if not is_safe:
                return ToolResult(
                    success=False,
                    result=None,
                    error=error or "Path is not safe to access"
                )
            
            search_path = Path(path).resolve()
            if not search_path.exists():
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Path does not exist: {path}"
                )
            
            # Get code files
            code_files = CodeSearchTools._get_code_files(search_path, file_pattern)
            
            if not code_files:
                return ToolResult(
                    success=True,
                    result={
                        "matches": [],
                        "count": 0
                    },
                    metadata={
                        "path": str(search_path),
                        "pattern": pattern,
                        "file_pattern": file_pattern,
                        "files_searched": 0
                    }
                )
            
            matches = []
            
            # Try regex search first, fallback to simple string search
            try:
                regex = re.compile(pattern, re.IGNORECASE | re.MULTILINE)
                is_regex = True
            except re.error:
                # If regex fails, treat as literal string
                regex = None
                is_regex = False
            
            # Search in files
            for file_path in code_files:
                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    lines = content.split('\n')
                    
                    # Search each line
                    for line_num, line in enumerate(lines, 1):
                        match_found = False
                        
                        if is_regex and regex:
                            if regex.search(line):
                                match_found = True
                        else:
                            if pattern.lower() in line.lower():
                                match_found = True
                        
                        if match_found:
                            # Get context lines
                            start_line = max(1, line_num - context_lines)
                            end_line = min(len(lines), line_num + context_lines + 1)
                            context = lines[start_line - 1:end_line]
                            context_text = '\n'.join(context)
                            
                            match_info = {
                                "file": str(file_path.relative_to(search_path)),
                                "line": line_num,
                                "snippet": line.strip(),
                                "context": context_text,
                                "match_line": line_num - start_line + 1  # Line in context
                            }
                            matches.append(match_info)
                            
                            # Limit matches per file
                            file_matches = sum(1 for m in matches if m["file"] == match_info["file"])
                            if file_matches >= 20:
                                break
                    
                    # Limit total matches
                    if len(matches) >= 100:
                        break
                
                except Exception:
                    continue  # Skip files that can't be read
            
            return ToolResult(
                success=True,
                result={
                    "matches": matches,
                    "count": len(matches)
                },
                metadata={
                    "path": str(search_path),
                    "pattern": pattern,
                    "file_pattern": file_pattern,
                    "files_searched": len(code_files),
                    "is_regex": is_regex
                }
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error searching code: {str(e)}"
            )
    
    @staticmethod
    def find_usages(symbol: str, path: str = ".") -> ToolResult:
        """
        Find where symbol (function/variable) is used.
        
        Args:
            symbol: Symbol name to search for
            path: Path to search (default: current directory)
        
        Returns:
            ToolResult with usage locations
        """
        try:
            # Validate path
            is_safe, error = CodeSearchTools._is_safe_path(path)
            if not is_safe:
                return ToolResult(
                    success=False,
                    result=None,
                    error=error or "Path is not safe to access"
                )
            
            search_path = Path(path).resolve()
            if not search_path.exists():
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Path does not exist: {path}"
                )
            
            # Use search_code to find usages
            # Search for symbol usage patterns
            patterns = [
                f"{symbol}(",  # Function call
                f"{symbol}[",  # Array/object access
                f".{symbol}",  # Method access
                f"={symbol}",  # Assignment
                f" {symbol} ",  # Variable reference
                f"{symbol}.",  # Object property
            ]
            
            all_matches = []
            
            for pattern in patterns:
                result = CodeSearchTools.search_code(pattern, str(search_path), "*.py", context_lines=2)
                if result.success and result.result:
                    matches = result.result.get("matches", [])
                    for match in matches:
                        # Avoid duplicates
                        if not any(
                            m["file"] == match["file"] and m["line"] == match["line"]
                            for m in all_matches
                        ):
                            all_matches.append(match)
            
            # Also do direct symbol search
            direct_result = CodeSearchTools.search_code(symbol, str(search_path), "*.py", context_lines=2)
            if direct_result.success and direct_result.result:
                matches = direct_result.result.get("matches", [])
                for match in matches:
                    # Avoid duplicates
                    if not any(
                        m["file"] == match["file"] and m["line"] == match["line"]
                        for m in all_matches
                    ):
                        all_matches.append(match)
            
            # Limit results
            all_matches = all_matches[:50]
            
            return ToolResult(
                success=True,
                result={
                    "usages": all_matches,
                    "count": len(all_matches)
                },
                metadata={
                    "path": str(search_path),
                    "symbol": symbol,
                    "count": len(all_matches)
                }
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error finding usages: {str(e)}"
            )
    
    @staticmethod
    def find_definitions(symbol: str, path: str = ".") -> ToolResult:
        """
        Find where symbol (function/class) is defined.
        
        Args:
            symbol: Symbol name to search for
            path: Path to search (default: current directory)
        
        Returns:
            ToolResult with definition locations
        """
        try:
            # Validate path
            is_safe, error = CodeSearchTools._is_safe_path(path)
            if not is_safe:
                return ToolResult(
                    success=False,
                    result=None,
                    error=error or "Path is not safe to access"
                )
            
            search_path = Path(path).resolve()
            if not search_path.exists():
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Path does not exist: {path}"
                )
            
            definitions = []
            
            # Search for definition patterns
            definition_patterns = [
                f"def {symbol}(",
                f"class {symbol}",
                f"def {symbol}(",
                f"const {symbol} =",
                f"let {symbol} =",
                f"var {symbol} =",
                f"function {symbol}(",
            ]
            
            for pattern in definition_patterns:
                result = CodeSearchTools.search_code(pattern, str(search_path), "*.py", context_lines=5)
                if result.success and result.result:
                    matches = result.result.get("matches", [])
                    for match in matches:
                        # Check if it's actually a definition (not a comment)
                        snippet = match.get("snippet", "")
                        if not snippet.strip().startswith("#"):
                            match["type"] = "definition"
                            # Avoid duplicates
                            if not any(
                                d["file"] == match["file"] and d["line"] == match["line"]
                                for d in definitions
                            ):
                                definitions.append(match)
            
            # For Python, also parse AST to find definitions
            code_files = CodeSearchTools._get_code_files(search_path, "*.py")
            for file_path in code_files[:50]:  # Limit to 50 files
                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    tree = ast.parse(content, filename=str(file_path))
                    
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef) and node.name == symbol:
                            # Found function definition
                            def_info = {
                                "file": str(file_path.relative_to(search_path)),
                                "line": node.lineno,
                                "snippet": content.split('\n')[node.lineno - 1].strip(),
                                "type": "function",
                                "name": node.name
                            }
                            # Avoid duplicates
                            if not any(
                                d["file"] == def_info["file"] and d["line"] == def_info["line"]
                                for d in definitions
                            ):
                                definitions.append(def_info)
                        
                        elif isinstance(node, ast.ClassDef) and node.name == symbol:
                            # Found class definition
                            def_info = {
                                "file": str(file_path.relative_to(search_path)),
                                "line": node.lineno,
                                "snippet": content.split('\n')[node.lineno - 1].strip(),
                                "type": "class",
                                "name": node.name
                            }
                            # Avoid duplicates
                            if not any(
                                d["file"] == def_info["file"] and d["line"] == def_info["line"]
                                for d in definitions
                            ):
                                definitions.append(def_info)
                
                except Exception:
                    continue  # Skip files that can't be parsed
            
            # Limit results
            definitions = definitions[:20]
            
            return ToolResult(
                success=True,
                result={
                    "definitions": definitions,
                    "count": len(definitions)
                },
                metadata={
                    "path": str(search_path),
                    "symbol": symbol,
                    "count": len(definitions)
                }
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error finding definitions: {str(e)}"
            )
    
    @staticmethod
    def find_todos(path: str = ".") -> ToolResult:
        """
        Find TODO/FIXME comments.
        
        Args:
            path: Path to search (default: current directory)
        
        Returns:
            ToolResult with TODO/FIXME locations
        """
        try:
            # Validate path
            is_safe, error = CodeSearchTools._is_safe_path(path)
            if not is_safe:
                return ToolResult(
                    success=False,
                    result=None,
                    error=error or "Path is not safe to access"
                )
            
            search_path = Path(path).resolve()
            if not search_path.exists():
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Path does not exist: {path}"
                )
            
            # Search for TODO/FIXME patterns
            todo_patterns = [
                r"TODO:?\s*(.+)",
                r"FIXME:?\s*(.+)",
                r"XXX:?\s*(.+)",
                r"HACK:?\s*(.+)",
                r"NOTE:?\s*(.+)",
                r"BUG:?\s*(.+)",
            ]
            
            all_todos = []
            
            for pattern in todo_patterns:
                result = CodeSearchTools.search_code(pattern, str(search_path), "*", context_lines=2)
                if result.success and result.result:
                    matches = result.result.get("matches", [])
                    for match in matches:
                        # Extract TODO text
                        snippet = match.get("snippet", "")
                        todo_type = "TODO"
                        if "FIXME" in snippet.upper():
                            todo_type = "FIXME"
                        elif "XXX" in snippet.upper():
                            todo_type = "XXX"
                        elif "HACK" in snippet.upper():
                            todo_type = "HACK"
                        elif "BUG" in snippet.upper():
                            todo_type = "BUG"
                        elif "NOTE" in snippet.upper():
                            todo_type = "NOTE"
                        
                        todo_info = {
                            "file": match["file"],
                            "line": match["line"],
                            "type": todo_type,
                            "text": snippet.strip(),
                            "context": match.get("context", "")
                        }
                        
                        # Avoid duplicates
                        if not any(
                            t["file"] == todo_info["file"] and t["line"] == todo_info["line"]
                            for t in all_todos
                        ):
                            all_todos.append(todo_info)
            
            # Limit results
            all_todos = all_todos[:50]
            
            return ToolResult(
                success=True,
                result={
                    "todos": all_todos,
                    "count": len(all_todos)
                },
                metadata={
                    "path": str(search_path),
                    "count": len(all_todos)
                }
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error finding TODOs: {str(e)}"
            )
    
    @staticmethod
    def find_imports(module: str, path: str = ".") -> ToolResult:
        """
        Find imports of a module.
        
        Args:
            module: Module name to search for
            path: Path to search (default: current directory)
        
        Returns:
            ToolResult with import locations
        """
        try:
            # Validate path
            is_safe, error = CodeSearchTools._is_safe_path(path)
            if not is_safe:
                return ToolResult(
                    success=False,
                    result=None,
                    error=error or "Path is not safe to access"
                )
            
            search_path = Path(path).resolve()
            if not search_path.exists():
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Path does not exist: {path}"
                )
            
            # Search for import patterns
            import_patterns = [
                f"from {module} import",
                f"import {module}",
                f"require('{module}')",
                f'require("{module}")',
                f"import.*{module}",
            ]
            
            all_imports = []
            
            for pattern in import_patterns:
                result = CodeSearchTools.search_code(pattern, str(search_path), "*", context_lines=2)
                if result.success and result.result:
                    matches = result.result.get("matches", [])
                    for match in matches:
                        import_info = {
                            "file": match["file"],
                            "line": match["line"],
                            "snippet": match.get("snippet", "").strip(),
                            "context": match.get("context", "")
                        }
                        
                        # Avoid duplicates
                        if not any(
                            i["file"] == import_info["file"] and i["line"] == import_info["line"]
                            for i in all_imports
                        ):
                            all_imports.append(import_info)
            
            # For Python, also parse AST
            code_files = CodeSearchTools._get_code_files(search_path, "*.py")
            for file_path in code_files[:50]:  # Limit to 50 files
                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    tree = ast.parse(content, filename=str(file_path))
                    
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                if module in alias.name:
                                    import_info = {
                                        "file": str(file_path.relative_to(search_path)),
                                        "line": node.lineno,
                                        "snippet": content.split('\n')[node.lineno - 1].strip(),
                                        "type": "import"
                                    }
                                    # Avoid duplicates
                                    if not any(
                                        i["file"] == import_info["file"] and i["line"] == import_info["line"]
                                        for i in all_imports
                                    ):
                                        all_imports.append(import_info)
                        
                        elif isinstance(node, ast.ImportFrom):
                            if node.module and module in node.module:
                                import_info = {
                                    "file": str(file_path.relative_to(search_path)),
                                    "line": node.lineno,
                                    "snippet": content.split('\n')[node.lineno - 1].strip(),
                                    "type": "from_import"
                                }
                                # Avoid duplicates
                                if not any(
                                    i["file"] == import_info["file"] and i["line"] == import_info["line"]
                                    for i in all_imports
                                ):
                                    all_imports.append(import_info)
                
                except Exception:
                    continue  # Skip files that can't be parsed
            
            # Limit results
            all_imports = all_imports[:50]
            
            return ToolResult(
                success=True,
                result={
                    "imports": all_imports,
                    "count": len(all_imports)
                },
                metadata={
                    "path": str(search_path),
                    "module": module,
                    "count": len(all_imports)
                }
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error finding imports: {str(e)}"
            )

