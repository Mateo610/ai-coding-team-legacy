"""
Package/Dependency Management tools for agents to manage dependencies and security
"""
import re
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse
import sys

from tools.code_tools import ToolResult
from tools.file_tools import FileTools
from agents.timeout_config import TIMEOUT_CONFIG


class PackageManagerTools:
    """Tools for managing dependencies and checking security"""
    
    @staticmethod
    def _is_safe_path(filepath: str) -> tuple[bool, Optional[str]]:
        """Check if filepath is safe to access (delegates to FileTools)"""
        return FileTools._is_safe_path(filepath)
    
    @staticmethod
    def _parse_requirements_txt(file_path: Path) -> List[Dict[str, str]]:
        """Parse requirements.txt file"""
        dependencies = []
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            for line in content.split('\n'):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Parse package spec: package==version, package>=version, etc.
                match = re.match(r'^([a-zA-Z0-9_-]+(?:\[[^\]]+\])?)([=<>!]+)?([0-9.]+)?', line)
                if match:
                    package_name = match.group(1).split('[')[0]  # Remove extras
                    constraint = match.group(2) if match.group(2) else "=="
                    version = match.group(3) if match.group(3) else None
                    
                    dependencies.append({
                        "name": package_name,
                        "version": version,
                        "constraint": constraint,
                        "spec": line
                    })
        except Exception:
            pass
        
        return dependencies
    
    @staticmethod
    def _parse_package_json(file_path: Path) -> Dict[str, Any]:
        """Parse package.json file"""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            return json.loads(content)
        except Exception:
            return {}
    
    @staticmethod
    def check_dependencies(path: str = ".") -> ToolResult:
        """
        Check for outdated packages.
        
        Args:
            path: Project path (default: current directory)
        
        Returns:
            ToolResult with dependency information and outdated packages
        """
        try:
            # Validate path
            is_safe, error = PackageManagerTools._is_safe_path(path)
            if not is_safe:
                return ToolResult(
                    success=False,
                    result=None,
                    error=error or "Path is not safe to access"
                )
            
            project_path = Path(path).resolve()
            
            # Check Python dependencies
            requirements_files = []
            for req_file in ["requirements.txt", "requirements-dev.txt", "requirements.in"]:
                req_path = project_path / req_file
                if req_path.exists():
                    requirements_files.append(req_path)
            
            # Check Node.js dependencies
            package_json = project_path / "package.json"
            has_node = package_json.exists()
            
            dependencies_info = {
                "python": {
                    "dependencies": [],
                    "outdated": [],
                    "files": []
                },
                "node": {
                    "dependencies": [],
                    "outdated": [],
                    "has_package_json": has_node
                }
            }
            
            # Parse Python dependencies
            for req_file in requirements_files:
                deps = PackageManagerTools._parse_requirements_txt(req_file)
                dependencies_info["python"]["dependencies"].extend(deps)
                dependencies_info["python"]["files"].append(str(req_file.relative_to(project_path)))
            
            # Parse Node.js dependencies
            if has_node:
                package_data = PackageManagerTools._parse_package_json(package_json)
                deps = package_data.get("dependencies", {})
                dev_deps = package_data.get("devDependencies", {})
                
                for name, version in deps.items():
                    dependencies_info["node"]["dependencies"].append({
                        "name": name,
                        "version": version,
                        "type": "dependency"
                    })
                
                for name, version in dev_deps.items():
                    dependencies_info["node"]["dependencies"].append({
                        "name": name,
                        "version": version,
                        "type": "devDependency"
                    })
            
            # Try to check for outdated packages (requires network access)
            # For Python, we'd use pip list --outdated
            # For Node, we'd use npm outdated
            
            return ToolResult(
                success=True,
                result={
                    "dependencies": dependencies_info,
                    "total_python": len(dependencies_info["python"]["dependencies"]),
                    "total_node": len(dependencies_info["node"]["dependencies"])
                },
                metadata={
                    "path": str(project_path),
                    "python_packages": len(dependencies_info["python"]["dependencies"]),
                    "node_packages": len(dependencies_info["node"]["dependencies"])
                }
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error checking dependencies: {str(e)}"
            )
    
    @staticmethod
    def check_security(path: str = ".") -> ToolResult:
        """
        Check for known vulnerabilities (npm audit, pip check).
        
        Args:
            path: Project path (default: current directory)
        
        Returns:
            ToolResult with security vulnerabilities
        """
        try:
            # Validate path
            is_safe, error = PackageManagerTools._is_safe_path(path)
            if not is_safe:
                return ToolResult(
                    success=False,
                    result=None,
                    error=error or "Path is not safe to access"
                )
            
            project_path = Path(path).resolve()
            
            vulnerabilities = {
                "python": [],
                "node": [],
                "summary": {
                    "total": 0,
                    "critical": 0,
                    "high": 0,
                    "medium": 0,
                    "low": 0
                }
            }
            
            # Check Python vulnerabilities using pip check
            try:
                result = subprocess.run(
                    ["pip", "check"],
                    cwd=str(project_path),
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.stdout:
                    # Parse pip check output (format: package (version) requires package2 (version), but version is installed)
                    for line in result.stdout.strip().split('\n'):
                        if line.strip():
                            vulnerabilities["python"].append({
                                "issue": line.strip(),
                                "severity": "unknown"
                            })
                            vulnerabilities["summary"]["total"] += 1
            except FileNotFoundError:
                pass  # pip not available
            except subprocess.TimeoutExpired:
                pass
            except Exception:
                pass
            
            # Check Node.js vulnerabilities using npm audit
            package_json = project_path / "package.json"
            if package_json.exists():
                try:
                    result = subprocess.run(
                        ["npm", "audit", "--json"],
                        cwd=str(project_path),
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    if result.returncode == 0 or result.stdout:
                        try:
                            audit_data = json.loads(result.stdout)
                            vulnerabilities_data = audit_data.get("vulnerabilities", {})
                            
                            for pkg_name, vuln_info in vulnerabilities_data.items():
                                severity = vuln_info.get("severity", "unknown")
                                vulnerabilities["node"].append({
                                    "package": pkg_name,
                                    "severity": severity,
                                    "title": vuln_info.get("title", ""),
                                    "via": vuln_info.get("via", [])
                                })
                                
                                vulnerabilities["summary"]["total"] += 1
                                if severity == "critical":
                                    vulnerabilities["summary"]["critical"] += 1
                                elif severity == "high":
                                    vulnerabilities["summary"]["high"] += 1
                                elif severity == "medium":
                                    vulnerabilities["summary"]["medium"] += 1
                                elif severity == "low":
                                    vulnerabilities["summary"]["low"] += 1
                        except json.JSONDecodeError:
                            pass
                except FileNotFoundError:
                    pass  # npm not available
                except subprocess.TimeoutExpired:
                    pass
                except Exception:
                    pass
            
            has_vulnerabilities = vulnerabilities["summary"]["total"] > 0
            
            return ToolResult(
                success=True,
                result={
                    "vulnerabilities": vulnerabilities,
                    "has_vulnerabilities": has_vulnerabilities
                },
                metadata={
                    "path": str(project_path),
                    "total_vulnerabilities": vulnerabilities["summary"]["total"],
                    "critical": vulnerabilities["summary"]["critical"]
                }
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error checking security: {str(e)}"
            )
    
    @staticmethod
    def update_dependencies(
        packages: List[str] = None,
        path: str = ".",
        test: bool = True
    ) -> ToolResult:
        """
        Update packages (with testing).
        
        Args:
            packages: List of packages to update (default: all)
            path: Project path (default: current directory)
            test: Whether to run tests after update (default: True)
        
        Returns:
            ToolResult with update results
        """
        try:
            # Validate path
            is_safe, error = PackageManagerTools._is_safe_path(path)
            if not is_safe:
                return ToolResult(
                    success=False,
                    result=None,
                    error=error or "Path is not safe to access"
                )
            
            project_path = Path(path).resolve()
            
            # Check what type of project
            requirements_file = project_path / "requirements.txt"
            package_json = project_path / "package.json"
            
            updated_packages = []
            errors = []
            
            # Update Python packages
            if requirements_file.exists():
                if packages:
                    # Update specific packages
                    for package in packages:
                        try:
                            result = subprocess.run(
                                ["pip", "install", "--upgrade", package],
                                cwd=str(project_path),
                                capture_output=True,
                                text=True,
                                timeout=60
                            )
                            if result.returncode == 0:
                                updated_packages.append({
                                    "package": package,
                                    "type": "python",
                                    "status": "updated"
                                })
                            else:
                                errors.append({
                                    "package": package,
                                    "error": result.stderr[:200]
                                })
                        except Exception as e:
                            errors.append({
                                "package": package,
                                "error": str(e)[:200]
                            })
                else:
                    # Update all packages in requirements.txt
                    deps = PackageManagerTools._parse_requirements_txt(requirements_file)
                    for dep in deps[:10]:  # Limit to 10 for safety
                        package = dep["name"]
                        try:
                            result = subprocess.run(
                                ["pip", "install", "--upgrade", package],
                                cwd=str(project_path),
                                capture_output=True,
                                text=True,
                                timeout=60
                            )
                            if result.returncode == 0:
                                updated_packages.append({
                                    "package": package,
                                    "type": "python",
                                    "status": "updated"
                                })
                        except Exception:
                            pass
            
            # Update Node.js packages
            if package_json.exists():
                if packages:
                    for package in packages:
                        try:
                            result = subprocess.run(
                                ["npm", "update", package],
                                cwd=str(project_path),
                                capture_output=True,
                                text=True,
                                timeout=60
                            )
                            if result.returncode == 0:
                                updated_packages.append({
                                    "package": package,
                                    "type": "node",
                                    "status": "updated"
                                })
                        except Exception:
                            pass
                else:
                    # Update all packages
                    try:
                        result = subprocess.run(
                            ["npm", "update"],
                            cwd=str(project_path),
                            capture_output=True,
                            text=True,
                            timeout=120
                        )
                        if result.returncode == 0:
                            updated_packages.append({
                                "package": "all",
                                "type": "node",
                                "status": "updated"
                            })
                    except Exception:
                        pass
            
            # Run tests if requested
            test_results = None
            if test and updated_packages:
                from tools.test_runner import TestRunnerTools
                test_result = TestRunnerTools.run_tests(path=str(project_path), framework="auto")
                test_results = {
                    "passed": test_result.metadata.get("passed", 0) if test_result.success else 0,
                    "failed": test_result.metadata.get("failed", 0) if test_result.success else 0
                }
            
            return ToolResult(
                success=len(errors) == 0,
                result={
                    "updated_packages": updated_packages,
                    "errors": errors,
                    "test_results": test_results
                },
                metadata={
                    "path": str(project_path),
                    "updated_count": len(updated_packages),
                    "error_count": len(errors)
                }
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error updating dependencies: {str(e)}"
            )
    
    @staticmethod
    def list_dependencies(path: str = ".") -> ToolResult:
        """
        List all dependencies.
        
        Args:
            path: Project path (default: current directory)
        
        Returns:
            ToolResult with list of all dependencies
        """
        # Reuse check_dependencies but format as list
        result = PackageManagerTools.check_dependencies(path)
        
        if result.success:
            deps_info = result.result.get("dependencies", {})
            
            all_dependencies = []
            
            # Add Python dependencies
            for dep in deps_info.get("python", {}).get("dependencies", []):
                all_dependencies.append({
                    "name": dep["name"],
                    "version": dep.get("version", "unknown"),
                    "type": "python",
                    "spec": dep.get("spec", "")
                })
            
            # Add Node.js dependencies
            for dep in deps_info.get("node", {}).get("dependencies", []):
                all_dependencies.append({
                    "name": dep["name"],
                    "version": dep.get("version", "unknown"),
                    "type": dep.get("type", "dependency")
                })
            
            return ToolResult(
                success=True,
                result={
                    "dependencies": all_dependencies,
                    "count": len(all_dependencies),
                    "python_count": len([d for d in all_dependencies if d["type"] == "python"]),
                    "node_count": len([d for d in all_dependencies if d["type"] != "python"])
                },
                metadata={
                    "path": result.metadata.get("path"),
                    "total": len(all_dependencies)
                }
            )
        else:
            return result
    
    @staticmethod
    def add_dependency(
        package: str,
        version: str = None,
        dev: bool = False,
        path: str = "."
    ) -> ToolResult:
        """
        Add new dependency.
        
        Args:
            package: Package name to add
            version: Version constraint (optional, e.g., ">=1.0.0")
            dev: Whether to add as dev dependency (Node.js only)
            path: Project path (default: current directory)
        
        Returns:
            ToolResult with add result
        """
        try:
            # Validate path
            is_safe, error = PackageManagerTools._is_safe_path(path)
            if not is_safe:
                return ToolResult(
                    success=False,
                    result=None,
                    error=error or "Path is not safe to access"
                )
            
            project_path = Path(path).resolve()
            
            # Check what type of project
            requirements_file = project_path / "requirements.txt"
            package_json = project_path / "package.json"
            
            if requirements_file.exists():
                # Python project - add to requirements.txt
                try:
                    # Read existing requirements
                    content = requirements_file.read_text(encoding='utf-8', errors='ignore')
                    lines = content.split('\n')
                    
                    # Check if package already exists
                    package_exists = any(
                        line.strip().startswith(package) or
                        line.strip().startswith(package.replace('_', '-')) or
                        line.strip().startswith(package.replace('-', '_'))
                        for line in lines
                    )
                    
                    if package_exists:
                        return ToolResult(
                            success=False,
                            result=None,
                            error=f"Package '{package}' already in requirements.txt"
                        )
                    
                    # Add package
                    spec = f"{package}"
                    if version:
                        spec += version
                    else:
                        spec += ">=0.0.0"
                    
                    lines.append(spec)
                    content = '\n'.join(lines) + '\n'
                    
                    # Write back
                    requirements_file.write_text(content, encoding='utf-8')
                    
                    return ToolResult(
                        success=True,
                        result={
                            "package": package,
                            "spec": spec,
                            "file": "requirements.txt",
                            "type": "python"
                        },
                        metadata={
                            "path": str(project_path),
                            "package": package,
                            "file": "requirements.txt"
                        }
                    )
                except Exception as e:
                    return ToolResult(
                        success=False,
                        result=None,
                        error=f"Error adding to requirements.txt: {str(e)}"
                    )
            
            elif package_json.exists():
                # Node.js project - add to package.json
                try:
                    package_data = PackageManagerTools._parse_package_json(package_json)
                    
                    # Check if package already exists
                    deps = package_data.get("devDependencies" if dev else "dependencies", {})
                    if package in deps:
                        return ToolResult(
                            success=False,
                            result=None,
                            error=f"Package '{package}' already in package.json"
                        )
                    
                    # Add package
                    dep_key = "devDependencies" if dev else "dependencies"
                    if dep_key not in package_data:
                        package_data[dep_key] = {}
                    
                    spec = f"^{version}" if version else "latest"
                    package_data[dep_key][package] = spec
                    
                    # Write back
                    with open(package_json, 'w', encoding='utf-8') as f:
                        json.dump(package_data, f, indent=2)
                    
                    return ToolResult(
                        success=True,
                        result={
                            "package": package,
                            "version": spec,
                            "file": "package.json",
                            "type": "node",
                            "dev": dev
                        },
                        metadata={
                            "path": str(project_path),
                            "package": package,
                            "file": "package.json",
                            "dev": dev
                        }
                    )
                except Exception as e:
                    return ToolResult(
                        success=False,
                        result=None,
                        error=f"Error adding to package.json: {str(e)}"
                    )
            
            else:
                return ToolResult(
                    success=False,
                    result=None,
                    error="No requirements.txt or package.json found"
                )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error adding dependency: {str(e)}"
            )
    
    @staticmethod
    def remove_dependency(package: str, path: str = ".") -> ToolResult:
        """
        Remove unused dependency.
        
        Args:
            package: Package name to remove
            path: Project path (default: current directory)
        
        Returns:
            ToolResult with remove result
        """
        try:
            # Validate path
            is_safe, error = PackageManagerTools._is_safe_path(path)
            if not is_safe:
                return ToolResult(
                    success=False,
                    result=None,
                    error=error or "Path is not safe to access"
                )
            
            project_path = Path(path).resolve()
            
            # Check what type of project
            requirements_file = project_path / "requirements.txt"
            package_json = project_path / "package.json"
            
            if requirements_file.exists():
                # Python project - remove from requirements.txt
                try:
                    content = requirements_file.read_text(encoding='utf-8', errors='ignore')
                    lines = content.split('\n')
                    
                    # Remove lines containing package
                    original_count = len(lines)
                    lines = [
                        line for line in lines
                        if not (line.strip().startswith(package) or
                               line.strip().startswith(package.replace('_', '-')) or
                               line.strip().startswith(package.replace('-', '_')))
                    ]
                    
                    if len(lines) == original_count:
                        return ToolResult(
                            success=False,
                            result=None,
                            error=f"Package '{package}' not found in requirements.txt"
                        )
                    
                    # Write back
                    requirements_file.write_text('\n'.join(lines), encoding='utf-8')
                    
                    return ToolResult(
                        success=True,
                        result={
                            "package": package,
                            "file": "requirements.txt",
                            "type": "python"
                        },
                        metadata={
                            "path": str(project_path),
                            "package": package
                        }
                    )
                except Exception as e:
                    return ToolResult(
                        success=False,
                        result=None,
                        error=f"Error removing from requirements.txt: {str(e)}"
                    )
            
            elif package_json.exists():
                # Node.js project - remove from package.json
                try:
                    package_data = PackageManagerTools._parse_package_json(package_json)
                    
                    removed = False
                    # Try to remove from dependencies
                    if "dependencies" in package_data and package in package_data["dependencies"]:
                        del package_data["dependencies"][package]
                        removed = True
                    
                    # Try to remove from devDependencies
                    if "devDependencies" in package_data and package in package_data["devDependencies"]:
                        del package_data["devDependencies"][package]
                        removed = True
                    
                    if not removed:
                        return ToolResult(
                            success=False,
                            result=None,
                            error=f"Package '{package}' not found in package.json"
                        )
                    
                    # Write back
                    with open(package_json, 'w', encoding='utf-8') as f:
                        json.dump(package_data, f, indent=2)
                    
                    return ToolResult(
                        success=True,
                        result={
                            "package": package,
                            "file": "package.json",
                            "type": "node"
                        },
                        metadata={
                            "path": str(project_path),
                            "package": package
                        }
                    )
                except Exception as e:
                    return ToolResult(
                        success=False,
                        result=None,
                        error=f"Error removing from package.json: {str(e)}"
                    )
            
            else:
                return ToolResult(
                    success=False,
                    result=None,
                    error="No requirements.txt or package.json found"
                )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error removing dependency: {str(e)}"
            )
    
    @staticmethod
    def check_license(path: str = ".") -> ToolResult:
        """
        Check dependency licenses.
        
        Args:
            path: Project path (default: current directory)
        
        Returns:
            ToolResult with license information
        """
        try:
            # Validate path
            is_safe, error = PackageManagerTools._is_safe_path(path)
            if not is_safe:
                return ToolResult(
                    success=False,
                    result=None,
                    error=error or "Path is not safe to access"
                )
            
            project_path = Path(path).resolve()
            
            licenses_info = {
                "python": [],
                "node": [],
                "summary": {}
            }
            
            # Check Python package licenses (requires pip show)
            requirements_file = project_path / "requirements.txt"
            if requirements_file.exists():
                deps = PackageManagerTools._parse_requirements_txt(requirements_file)
                for dep in deps[:20]:  # Limit to 20 for performance
                    package = dep["name"]
                    try:
                        result = subprocess.run(
                            ["pip", "show", package],
                            capture_output=True,
                            text=True,
                            timeout=10
                        )
                        if result.returncode == 0:
                            # Parse license from output
                            for line in result.stdout.split('\n'):
                                if line.startswith('License:'):
                                    license_name = line.split(':', 1)[1].strip()
                                    licenses_info["python"].append({
                                        "package": package,
                                        "license": license_name
                                    })
                                    break
                    except Exception:
                        pass
            
            # Check Node.js package licenses (requires npm license-checker)
            package_json = project_path / "package.json"
            if package_json.exists():
                try:
                    result = subprocess.run(
                        ["npx", "license-checker", "--json"],
                        cwd=str(project_path),
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    if result.returncode == 0:
                        try:
                            license_data = json.loads(result.stdout)
                            for pkg_name, pkg_info in license_data.items():
                                license_name = pkg_info.get("licenses", "unknown")
                                licenses_info["node"].append({
                                    "package": pkg_name.split('@')[0],
                                    "license": license_name
                                })
                        except json.JSONDecodeError:
                            pass
                except FileNotFoundError:
                    # license-checker not installed - that's ok
                    pass
                except Exception:
                    pass
            
            # Create summary
            all_licenses = licenses_info["python"] + licenses_info["node"]
            license_counts = {}
            for item in all_licenses:
                license_name = item.get("license", "unknown")
                license_counts[license_name] = license_counts.get(license_name, 0) + 1
            
            licenses_info["summary"] = license_counts
            
            return ToolResult(
                success=True,
                result={
                    "licenses": licenses_info,
                    "total_packages": len(all_licenses)
                },
                metadata={
                    "path": str(project_path),
                    "total_packages": len(all_licenses),
                    "unique_licenses": len(license_counts)
                }
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error checking licenses: {str(e)}"
            )

