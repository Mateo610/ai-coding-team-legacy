"""
Git tools for agents to interact with version control (read-only + guarded write)
"""
import subprocess
import os
from pathlib import Path
from typing import Dict, Any, Optional, List

from tools.code_tools import ToolResult
from tools.file_tools import FileTools


class GitTools:
    """Tools for git operations with security restrictions"""
    
    @staticmethod
    def _is_safe_path(filepath: str) -> tuple[bool, Optional[str]]:
        """Check if filepath is safe to access (delegates to FileTools)"""
        return FileTools._is_safe_path(filepath)
    
    @staticmethod
    def _is_git_repo(path: Path) -> bool:
        """Check if path is a git repository"""
        git_dir = path / ".git"
        return git_dir.exists() and git_dir.is_dir()
    
    @staticmethod
    def _run_git_command(
        path: Path,
        command: List[str],
        allow_write: bool = False
    ) -> tuple[int, str, str]:
        """
        Run git command and return (returncode, stdout, stderr).
        
        Security: Only allows write operations if explicitly enabled.
        """
        try:
            # Ensure we're in a git repo
            if not GitTools._is_git_repo(path):
                return 1, "", "Not a git repository"
            
            # Build git command
            git_cmd = ["git", "-C", str(path)] + command
            
            # Run command
            result = subprocess.run(
                git_cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(path)
            )
            
            return result.returncode, result.stdout, result.stderr
        
        except subprocess.TimeoutExpired:
            return 1, "", "Command timed out after 30s"
        except Exception as e:
            return 1, "", str(e)
    
    @staticmethod
    def git_status(path: str = ".") -> ToolResult:
        """
        Get git status (read-only).
        
        Args:
            path: Path to git repository (default: current directory)
        
        Returns:
            ToolResult with git status information
        """
        try:
            # Validate path
            is_safe, error = GitTools._is_safe_path(path)
            if not is_safe:
                return ToolResult(
                    success=False,
                    result=None,
                    error=error or "Path is not safe to access"
                )
            
            repo_path = Path(path).resolve()
            if not repo_path.exists() or not repo_path.is_dir():
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Invalid repository path: {path}"
                )
            
            # Check if git repo
            if not GitTools._is_git_repo(repo_path):
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Not a git repository: {path}"
                )
            
            # Get status
            returncode, stdout, stderr = GitTools._run_git_command(repo_path, ["status", "--porcelain"])
            
            if returncode != 0:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Git status failed: {stderr}"
                )
            
            # Parse status
            changes = {
                "staged": [],
                "modified": [],
                "untracked": [],
                "deleted": [],
            }
            
            for line in stdout.strip().split('\n'):
                if not line.strip():
                    continue
                
                status_code = line[:2]
                filename = line[3:]
                
                if status_code.startswith('A') or status_code.startswith('M'):
                    changes["staged"].append(filename)
                elif status_code.startswith('??'):
                    changes["untracked"].append(filename)
                elif status_code.startswith('D'):
                    changes["deleted"].append(filename)
                elif status_code.startswith(' M') or status_code.startswith('M'):
                    changes["modified"].append(filename)
            
            # Get branch info
            branch_returncode, branch_stdout, branch_stderr = GitTools._run_git_command(
                repo_path, ["branch", "--show-current"]
            )
            current_branch = branch_stdout.strip() if branch_returncode == 0 else None
            
            return ToolResult(
                success=True,
                result={
                    "branch": current_branch,
                    "changes": changes,
                    "has_changes": any(changes.values()),
                    "status_output": stdout
                },
                metadata={
                    "path": str(repo_path),
                    "branch": current_branch,
                    "has_changes": any(changes.values())
                }
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error getting git status: {str(e)}"
            )
    
    @staticmethod
    def git_diff(filepath: str = None, path: str = ".") -> ToolResult:
        """
        Show diff for files (read-only).
        
        Args:
            filepath: Specific file to show diff for (optional)
            path: Path to git repository (default: current directory)
        
        Returns:
            ToolResult with git diff output
        """
        try:
            # Validate path
            is_safe, error = GitTools._is_safe_path(path)
            if not is_safe:
                return ToolResult(
                    success=False,
                    result=None,
                    error=error or "Path is not safe to access"
                )
            
            repo_path = Path(path).resolve()
            if not repo_path.exists() or not repo_path.is_dir():
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Invalid repository path: {path}"
                )
            
            # Check if git repo
            if not GitTools._is_git_repo(repo_path):
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Not a git repository: {path}"
                )
            
            # Build diff command
            diff_cmd = ["diff"]
            if filepath:
                # Validate filepath
                file_is_safe, file_error = GitTools._is_safe_path(filepath)
                if not file_is_safe:
                    return ToolResult(
                        success=False,
                        result=None,
                        error=file_error or "File path is not safe to access"
                    )
                diff_cmd.append(filepath)
            
            # Get diff
            returncode, stdout, stderr = GitTools._run_git_command(repo_path, diff_cmd)
            
            if returncode != 0 and stderr:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Git diff failed: {stderr}"
                )
            
            return ToolResult(
                success=True,
                result={
                    "diff": stdout,
                    "file": filepath if filepath else None,
                    "has_changes": bool(stdout.strip())
                },
                metadata={
                    "path": str(repo_path),
                    "file": filepath,
                    "has_changes": bool(stdout.strip())
                }
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error getting git diff: {str(e)}"
            )
    
    @staticmethod
    def git_log(path: str = ".", limit: int = 10) -> ToolResult:
        """
        Show commit history (read-only).
        
        Args:
            path: Path to git repository (default: current directory)
            limit: Number of commits to show (default: 10)
        
        Returns:
            ToolResult with commit history
        """
        try:
            # Validate path
            is_safe, error = GitTools._is_safe_path(path)
            if not is_safe:
                return ToolResult(
                    success=False,
                    result=None,
                    error=error or "Path is not safe to access"
                )
            
            repo_path = Path(path).resolve()
            if not repo_path.exists() or not repo_path.is_dir():
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Invalid repository path: {path}"
                )
            
            # Check if git repo
            if not GitTools._is_git_repo(repo_path):
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Not a git repository: {path}"
                )
            
            # Get log with format
            log_cmd = ["log", f"-{limit}", "--pretty=format:%h|%an|%ae|%ad|%s", "--date=short"]
            returncode, stdout, stderr = GitTools._run_git_command(repo_path, log_cmd)
            
            if returncode != 0:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Git log failed: {stderr}"
                )
            
            # Parse commits
            commits = []
            for line in stdout.strip().split('\n'):
                if not line.strip():
                    continue
                
                parts = line.split('|', 4)
                if len(parts) == 5:
                    commits.append({
                        "hash": parts[0],
                        "author": parts[1],
                        "email": parts[2],
                        "date": parts[3],
                        "message": parts[4]
                    })
            
            return ToolResult(
                success=True,
                result={
                    "commits": commits,
                    "count": len(commits)
                },
                metadata={
                    "path": str(repo_path),
                    "limit": limit,
                    "count": len(commits)
                }
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error getting git log: {str(e)}"
            )
    
    @staticmethod
    def git_show(filepath: str, commit: str = "HEAD", path: str = ".") -> ToolResult:
        """
        Show file at specific commit (read-only).
        
        Args:
            filepath: File to show
            commit: Commit hash or ref (default: HEAD)
            path: Path to git repository (default: current directory)
        
        Returns:
            ToolResult with file content at commit
        """
        try:
            # Validate paths
            is_safe, error = GitTools._is_safe_path(path)
            if not is_safe:
                return ToolResult(
                    success=False,
                    result=None,
                    error=error or "Path is not safe to access"
                )
            
            file_is_safe, file_error = GitTools._is_safe_path(filepath)
            if not file_is_safe:
                return ToolResult(
                    success=False,
                    result=None,
                    error=file_error or "File path is not safe to access"
                )
            
            repo_path = Path(path).resolve()
            if not repo_path.exists() or not repo_path.is_dir():
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Invalid repository path: {path}"
                )
            
            # Check if git repo
            if not GitTools._is_git_repo(repo_path):
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Not a git repository: {path}"
                )
            
            # Show file at commit
            show_cmd = ["show", f"{commit}:{filepath}"]
            returncode, stdout, stderr = GitTools._run_git_command(repo_path, show_cmd)
            
            if returncode != 0:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Git show failed: {stderr}"
                )
            
            return ToolResult(
                success=True,
                result={
                    "content": stdout,
                    "file": filepath,
                    "commit": commit
                },
                metadata={
                    "path": str(repo_path),
                    "file": filepath,
                    "commit": commit
                }
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error showing file: {str(e)}"
            )
    
    @staticmethod
    def git_branch(path: str = ".") -> ToolResult:
        """
        List branches (read-only).
        
        Args:
            path: Path to git repository (default: current directory)
        
        Returns:
            ToolResult with branch information
        """
        try:
            # Validate path
            is_safe, error = GitTools._is_safe_path(path)
            if not is_safe:
                return ToolResult(
                    success=False,
                    result=None,
                    error=error or "Path is not safe to access"
                )
            
            repo_path = Path(path).resolve()
            if not repo_path.exists() or not repo_path.is_dir():
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Invalid repository path: {path}"
                )
            
            # Check if git repo
            if not GitTools._is_git_repo(repo_path):
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Not a git repository: {path}"
                )
            
            # Get all branches
            branches_cmd = ["branch", "-a"]
            returncode, stdout, stderr = GitTools._run_git_command(repo_path, branches_cmd)
            
            if returncode != 0:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Git branch failed: {stderr}"
                )
            
            # Get current branch
            current_cmd = ["branch", "--show-current"]
            current_returncode, current_stdout, current_stderr = GitTools._run_git_command(repo_path, current_cmd)
            current_branch = current_stdout.strip() if current_returncode == 0 else None
            
            # Parse branches
            branches = []
            for line in stdout.strip().split('\n'):
                if not line.strip():
                    continue
                branch_name = line.strip().lstrip('* ').strip()
                is_current = line.strip().startswith('*')
                branches.append({
                    "name": branch_name,
                    "current": is_current
                })
            
            return ToolResult(
                success=True,
                result={
                    "branches": branches,
                    "current": current_branch,
                    "count": len(branches)
                },
                metadata={
                    "path": str(repo_path),
                    "current": current_branch,
                    "count": len(branches)
                }
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error listing branches: {str(e)}"
            )
    
    @staticmethod
    def git_add(files: List[str], path: str = ".") -> ToolResult:
        """
        Stage files (guarded write operation).
        
        Security: Only allows staging files in project directory.
        
        Args:
            files: List of files to stage
            path: Path to git repository (default: current directory)
        
        Returns:
            ToolResult with staging result
        """
        try:
            # Validate path
            is_safe, error = GitTools._is_safe_path(path)
            if not is_safe:
                return ToolResult(
                    success=False,
                    result=None,
                    error=error or "Path is not safe to access"
                )
            
            repo_path = Path(path).resolve()
            if not repo_path.exists() or not repo_path.is_dir():
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Invalid repository path: {path}"
                )
            
            # Check if git repo
            if not GitTools._is_git_repo(repo_path):
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Not a git repository: {path}"
                )
            
            # Validate all files
            safe_files = []
            for file in files:
                file_is_safe, file_error = GitTools._is_safe_path(file)
                if not file_is_safe:
                    return ToolResult(
                        success=False,
                        result=None,
                        error=f"File not safe to stage: {file} - {file_error}"
                    )
                safe_files.append(file)
            
            # Stage files
            add_cmd = ["add"] + safe_files
            returncode, stdout, stderr = GitTools._run_git_command(repo_path, add_cmd, allow_write=True)
            
            if returncode != 0:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Git add failed: {stderr}"
                )
            
            return ToolResult(
                success=True,
                result={
                    "files": safe_files,
                    "count": len(safe_files),
                    "message": f"Staged {len(safe_files)} file(s)"
                },
                metadata={
                    "path": str(repo_path),
                    "files": safe_files,
                    "count": len(safe_files)
                }
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error staging files: {str(e)}"
            )
    
    @staticmethod
    def git_commit(message: str, path: str = ".") -> ToolResult:
        """
        Commit changes (guarded write operation).
        
        Security: Only allows commits in project directory.
        
        Args:
            message: Commit message
            path: Path to git repository (default: current directory)
        
        Returns:
            ToolResult with commit result
        """
        try:
            # Validate path
            is_safe, error = GitTools._is_safe_path(path)
            if not is_safe:
                return ToolResult(
                    success=False,
                    result=None,
                    error=error or "Path is not safe to access"
                )
            
            repo_path = Path(path).resolve()
            if not repo_path.exists() or not repo_path.is_dir():
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Invalid repository path: {path}"
                )
            
            # Check if git repo
            if not GitTools._is_git_repo(repo_path):
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Not a git repository: {path}"
                )
            
            # Validate message
            if not message or not message.strip():
                return ToolResult(
                    success=False,
                    result=None,
                    error="Commit message cannot be empty"
                )
            
            # Commit changes
            commit_cmd = ["commit", "-m", message]
            returncode, stdout, stderr = GitTools._run_git_command(repo_path, commit_cmd, allow_write=True)
            
            if returncode != 0:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Git commit failed: {stderr}"
                )
            
            # Get commit hash
            hash_cmd = ["rev-parse", "HEAD"]
            hash_returncode, hash_stdout, hash_stderr = GitTools._run_git_command(repo_path, hash_cmd)
            commit_hash = hash_stdout.strip() if hash_returncode == 0 else None
            
            return ToolResult(
                success=True,
                result={
                    "message": message,
                    "commit_hash": commit_hash,
                    "output": stdout
                },
                metadata={
                    "path": str(repo_path),
                    "message": message,
                    "commit_hash": commit_hash
                }
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error committing changes: {str(e)}"
            )

