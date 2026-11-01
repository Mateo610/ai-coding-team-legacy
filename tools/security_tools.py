"""
Security scanning tools for agents to scan code for security vulnerabilities
"""
import re
import json
import ast
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List, Set
from datetime import datetime

from tools.code_tools import ToolResult
from tools.file_tools import FileTools
from tools.code_search import CodeSearchTools


class SecurityTools:
    """Tools for scanning code for security vulnerabilities"""
    
    # Common secret patterns (simplified - real implementation would use more sophisticated patterns)
    SECRET_PATTERNS = [
        r'api[_-]?key["\s]*[:=]["\s]*([a-zA-Z0-9_-]{20,})',
        r'secret[_-]?key["\s]*[:=]["\s]*([a-zA-Z0-9_-]{20,})',
        r'password["\s]*[:=]["\s]*([a-zA-Z0-9_-]{10,})',
        r'aws[_-]?access[_-]?key["\s]*[:=]["\s]*([A-Z0-9]{20})',
        r'aws[_-]?secret[_-]?key["\s]*[:=]["\s]*([A-Za-z0-9/+=]{40})',
        r'github[_-]?token["\s]*[:=]["\s]*([a-zA-Z0-9_-]{20,})',
        r'private[_-]?key["\s]*[:=]["\s]*-----BEGIN',
        r'-----BEGIN\s+(RSA|EC|DSA|PRIVATE)\s+KEY-----',
        r'sk-[a-zA-Z0-9]{32,}',  # OpenAI API key
        r'AIza[0-9A-Za-z_-]{35}',  # Google API key
    ]
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r'execute\([^)]*\s*\+\s*[^)]+\)',  # String concatenation in execute
        r'query\([^)]*\s*%\s*[^)]+\)',  # String formatting in query
        r'format\([^)]*\s*\+\s*[^)]+\)',  # String formatting
        r'\.format\([^)]*\{.*\}',  # .format() with user input
        r'f["\'].*\{.*\}.*execute',  # f-strings in execute
    ]
    
    # XSS patterns
    XSS_PATTERNS = [
        r'innerHTML\s*=\s*[^;]+',  # Direct innerHTML assignment
        r'\.html\([^)]+\)',  # jQuery .html()
        r'eval\([^)]+\)',  # eval() usage
        r'document\.write\([^)]+\)',  # document.write()
    ]
    
    @staticmethod
    def _is_safe_path(filepath: str) -> tuple[bool, Optional[str]]:
        """Check if filepath is safe to access (delegates to FileTools)"""
        return FileTools._is_safe_path(filepath)
    
    @staticmethod
    def _scan_file_for_secrets(file_path: Path) -> List[Dict[str, Any]]:
        """Scan a file for exposed secrets"""
        secrets = []
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            lines = content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                for pattern in SecurityTools.SECRET_PATTERNS:
                    matches = re.finditer(pattern, line, re.IGNORECASE)
                    for match in matches:
                        # Mask the secret value
                        secret_value = match.group(0) if match.groups() else match.group(0)
                        masked_value = secret_value[:10] + "..." if len(secret_value) > 10 else secret_value
                        
                        secrets.append({
                            "line": line_num,
                            "type": "exposed_secret",
                            "pattern": pattern,
                            "snippet": line.strip()[:100],
                            "severity": "critical",
                            "value_masked": masked_value
                        })
        except Exception:
            pass
        
        return secrets
    
    @staticmethod
    def scan_security(
        path: str = ".",
        scan_types: List[str] = None
    ) -> ToolResult:
        """
        Scan for security vulnerabilities.
        
        Args:
            path: Project path (default: current directory)
            scan_types: Types of scans to perform (default: all)
                Options: "secrets", "sql_injection", "xss", "dependencies"
        
        Returns:
            ToolResult with security vulnerabilities
        """
        try:
            # Validate path
            is_safe, error = SecurityTools._is_safe_path(path)
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
            
            if scan_types is None:
                scan_types = ["secrets", "sql_injection", "xss", "dependencies"]
            
            vulnerabilities = {
                "secrets": [],
                "sql_injection": [],
                "xss": [],
                "dependencies": [],
                "summary": {
                    "total": 0,
                    "critical": 0,
                    "high": 0,
                    "medium": 0,
                    "low": 0
                }
            }
            
            # Scan for secrets
            if "secrets" in scan_types:
                for code_file in project_path.rglob("*.py"):
                    if "__pycache__" in str(code_file) or ".git" in str(code_file):
                        continue
                    
                    secrets = SecurityTools._scan_file_for_secrets(code_file)
                    for secret in secrets:
                        secret["file"] = str(code_file.relative_to(project_path))
                        vulnerabilities["secrets"].append(secret)
                        vulnerabilities["summary"]["total"] += 1
                        vulnerabilities["summary"]["critical"] += 1
                    
                    if len(vulnerabilities["secrets"]) >= 50:  # Limit to 50 secrets
                        break
            
            # Scan for SQL injection
            if "sql_injection" in scan_types:
                for code_file in project_path.rglob("*.py"):
                    if "__pycache__" in str(code_file) or ".git" in str(code_file):
                        continue
                    
                    try:
                        content = code_file.read_text(encoding='utf-8', errors='ignore')
                        lines = content.split('\n')
                        
                        for line_num, line in enumerate(lines, 1):
                            for pattern in SecurityTools.SQL_INJECTION_PATTERNS:
                                if re.search(pattern, line, re.IGNORECASE):
                                    vulnerabilities["sql_injection"].append({
                                        "file": str(code_file.relative_to(project_path)),
                                        "line": line_num,
                                        "type": "sql_injection",
                                        "snippet": line.strip()[:100],
                                        "severity": "high",
                                        "pattern": pattern
                                    })
                                    vulnerabilities["summary"]["total"] += 1
                                    vulnerabilities["summary"]["high"] += 1
                                    break
                    except Exception:
                        continue
                    
                    if len(vulnerabilities["sql_injection"]) >= 50:  # Limit to 50
                        break
            
            # Scan for XSS (JavaScript/HTML files)
            if "xss" in scan_types:
                for js_file in project_path.rglob("*.js"):
                    if "node_modules" in str(js_file) or ".git" in str(js_file):
                        continue
                    
                    try:
                        content = js_file.read_text(encoding='utf-8', errors='ignore')
                        lines = content.split('\n')
                        
                        for line_num, line in enumerate(lines, 1):
                            for pattern in SecurityTools.XSS_PATTERNS:
                                if re.search(pattern, line, re.IGNORECASE):
                                    vulnerabilities["xss"].append({
                                        "file": str(js_file.relative_to(project_path)),
                                        "line": line_num,
                                        "type": "xss",
                                        "snippet": line.strip()[:100],
                                        "severity": "high",
                                        "pattern": pattern
                                    })
                                    vulnerabilities["summary"]["total"] += 1
                                    vulnerabilities["summary"]["high"] += 1
                                    break
                    except Exception:
                        continue
                    
                    if len(vulnerabilities["xss"]) >= 50:  # Limit to 50
                        break
                
                # Also check HTML files
                for html_file in project_path.rglob("*.html"):
                    if ".git" in str(html_file):
                        continue
                    
                    try:
                        content = html_file.read_text(encoding='utf-8', errors='ignore')
                        lines = content.split('\n')
                        
                        for line_num, line in enumerate(lines, 1):
                            if re.search(r'<script[^>]*>.*<', line, re.IGNORECASE | re.DOTALL):
                                vulnerabilities["xss"].append({
                                    "file": str(html_file.relative_to(project_path)),
                                    "line": line_num,
                                    "type": "xss",
                                    "snippet": line.strip()[:100],
                                    "severity": "medium",
                                    "pattern": "inline_script"
                                })
                                vulnerabilities["summary"]["total"] += 1
                                vulnerabilities["summary"]["medium"] += 1
                    except Exception:
                        continue
                    
                    if len(vulnerabilities["xss"]) >= 50:  # Limit to 50
                        break
            
            # Scan dependencies
            if "dependencies" in scan_types:
                from tools.package_manager import PackageManagerTools
                dep_result = PackageManagerTools.check_security(path)
                if dep_result.success:
                    dep_vulns = dep_result.result.get("vulnerabilities", {})
                    vulnerabilities["dependencies"] = dep_vulns
                    vulnerabilities["summary"]["total"] += dep_vulns.get("summary", {}).get("total", 0)
            
            return ToolResult(
                success=True,
                result={
                    "vulnerabilities": vulnerabilities,
                    "has_vulnerabilities": vulnerabilities["summary"]["total"] > 0
                },
                metadata={
                    "path": str(project_path),
                    "total_vulnerabilities": vulnerabilities["summary"]["total"],
                    "critical": vulnerabilities["summary"]["critical"],
                    "high": vulnerabilities["summary"]["high"]
                }
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error scanning security: {str(e)}"
            )
    
    @staticmethod
    def check_secrets(path: str = ".") -> ToolResult:
        """
        Check for exposed secrets/API keys.
        
        Args:
            path: Project path (default: current directory)
        
        Returns:
            ToolResult with exposed secrets
        """
        result = SecurityTools.scan_security(path, scan_types=["secrets"])
        
        if result.success:
            return ToolResult(
                success=True,
                result={
                    "secrets": result.result.get("vulnerabilities", {}).get("secrets", []),
                    "count": len(result.result.get("vulnerabilities", {}).get("secrets", []))
                },
                metadata={
                    "path": result.metadata.get("path"),
                    "count": len(result.result.get("vulnerabilities", {}).get("secrets", []))
                }
            )
        else:
            return result
    
    @staticmethod
    def analyze_dependencies(path: str = ".") -> ToolResult:
        """
        Analyze dependency security.
        
        Args:
            path: Project path (default: current directory)
        
        Returns:
            ToolResult with dependency security analysis
        """
        try:
            from tools.package_manager import PackageManagerTools
            
            # Get dependency vulnerabilities
            security_result = PackageManagerTools.check_security(path)
            
            if not security_result.success:
                return security_result
            
            vulnerabilities = security_result.result.get("vulnerabilities", {})
            
            # Get dependency list
            deps_result = PackageManagerTools.check_dependencies(path)
            dependencies = []
            if deps_result.success:
                deps_info = deps_result.result.get("dependencies", {})
                dependencies = deps_info.get("python", {}).get("dependencies", []) + deps_info.get("node", {}).get("dependencies", [])
            
            return ToolResult(
                success=True,
                result={
                    "vulnerabilities": vulnerabilities,
                    "dependencies": dependencies,
                    "total_dependencies": len(dependencies),
                    "vulnerable_dependencies": len(vulnerabilities.get("python", [])) + len(vulnerabilities.get("node", []))
                },
                metadata={
                    "path": str(Path(path).resolve()),
                    "total_deps": len(dependencies),
                    "vulnerable_deps": len(vulnerabilities.get("python", [])) + len(vulnerabilities.get("node", []))
                }
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error analyzing dependencies: {str(e)}"
            )
    
    @staticmethod
    def check_sql_injection(path: str = ".") -> ToolResult:
        """
        Check for SQL injection risks.
        
        Args:
            path: Project path (default: current directory)
        
        Returns:
            ToolResult with SQL injection vulnerabilities
        """
        result = SecurityTools.scan_security(path, scan_types=["sql_injection"])
        
        if result.success:
            return ToolResult(
                success=True,
                result={
                    "sql_injection_risks": result.result.get("vulnerabilities", {}).get("sql_injection", []),
                    "count": len(result.result.get("vulnerabilities", {}).get("sql_injection", []))
                },
                metadata={
                    "path": result.metadata.get("path"),
                    "count": len(result.result.get("vulnerabilities", {}).get("sql_injection", []))
                }
            )
        else:
            return result
    
    @staticmethod
    def check_xss(path: str = ".") -> ToolResult:
        """
        Check for XSS vulnerabilities.
        
        Args:
            path: Project path (default: current directory)
        
        Returns:
            ToolResult with XSS vulnerabilities
        """
        result = SecurityTools.scan_security(path, scan_types=["xss"])
        
        if result.success:
            return ToolResult(
                success=True,
                result={
                    "xss_risks": result.result.get("vulnerabilities", {}).get("xss", []),
                    "count": len(result.result.get("vulnerabilities", {}).get("xss", []))
                },
                metadata={
                    "path": result.metadata.get("path"),
                    "count": len(result.result.get("vulnerabilities", {}).get("xss", []))
                }
            )
        else:
            return result
    
    @staticmethod
    def security_audit(path: str = ".") -> ToolResult:
        """
        Full security audit.
        
        Args:
            path: Project path (default: current directory)
        
        Returns:
            ToolResult with complete security audit
        """
        # Run all security scans
        result = SecurityTools.scan_security(path, scan_types=["secrets", "sql_injection", "xss", "dependencies"])
        
        if not result.success:
            return result
        
        vulnerabilities = result.result.get("vulnerabilities", {})
        summary = vulnerabilities.get("summary", {})
        
        # Generate audit report
        audit_report = {
            "timestamp": datetime.now().isoformat(),
            "path": str(Path(path).resolve()),
            "summary": summary,
            "vulnerabilities": {
                "secrets": vulnerabilities.get("secrets", [])[:10],  # Top 10
                "sql_injection": vulnerabilities.get("sql_injection", [])[:10],
                "xss": vulnerabilities.get("xss", [])[:10],
                "dependencies": vulnerabilities.get("dependencies", {})
            },
            "recommendations": []
        }
        
        # Generate recommendations
        if summary.get("critical", 0) > 0:
            audit_report["recommendations"].append(
                f"CRITICAL: {summary['critical']} critical vulnerabilities found. Review exposed secrets immediately."
            )
        
        if summary.get("high", 0) > 0:
            audit_report["recommendations"].append(
                f"HIGH: {summary['high']} high-severity vulnerabilities found. Address SQL injection and XSS risks."
            )
        
        if vulnerabilities.get("dependencies", {}).get("summary", {}).get("total", 0) > 0:
            audit_report["recommendations"].append(
                "Update dependencies with known vulnerabilities."
            )
        
        if not audit_report["recommendations"]:
            audit_report["recommendations"].append("No critical security issues found. Good job!")
        
        return ToolResult(
            success=True,
            result=audit_report,
            metadata={
                "path": str(Path(path).resolve()),
                "total_vulnerabilities": summary.get("total", 0),
                "critical": summary.get("critical", 0),
                "has_issues": summary.get("total", 0) > 0
            }
        )

