"""
Consolidated Git Tools
Replaces: git_status, git_diff, git_log, git_show, git_branch, git_add, git_commit
"""

import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tools.code_tools import ToolResult
from tools.git_tools import GitTools


class GitConsolidated:
    """Consolidated Git tools with mode-based operations"""
    
    @staticmethod
    def git_inspect(mode: str = "status", **kwargs) -> ToolResult:
        """
        Read-only Git inspection.
        
        Replaces: git_status, git_diff, git_log, git_show, git_branch
        
        Args:
            mode: Operation mode:
                - "status" (default): Show git status
                - "diff": Show git diff
                - "log": Show git log
                - "show": Show commit details
                - "branch": List branches
            **kwargs: Additional arguments for specific modes:
                - diff: file_path (optional)
                - log: limit (optional), author (optional)
                - show: commit_hash (required)
                - branch: all (optional, default: False)
        
        Returns:
            ToolResult with Git information based on mode
        
        Examples:
            git_inspect(mode="status")  # Show git status
            git_inspect(mode="diff", file_path="src/main.py")  # Show diff for file
            git_inspect(mode="log", limit=10)  # Show last 10 commits
            git_inspect(mode="show", commit_hash="abc123")  # Show commit details
            git_inspect(mode="branch")  # List branches
        """
        try:
            if mode == "status":
                # Use GitTools.git_status
                result = GitTools.git_status()
                return result
            elif mode == "diff":
                # Use GitTools.git_diff
                file_path = kwargs.get("file_path")
                result = GitTools.git_diff(file_path=file_path)
                return result
            elif mode == "log":
                # Use GitTools.git_log
                limit = kwargs.get("limit")
                author = kwargs.get("author")
                result = GitTools.git_log(limit=limit, author=author)
                return result
            elif mode == "show":
                # Use GitTools.git_show
                commit_hash = kwargs.get("commit_hash")
                if not commit_hash:
                    return ToolResult(
                        success=False,
                        result=None,
                        error="commit_hash required for mode='show'"
                    )
                result = GitTools.git_show(commit_hash)
                return result
            elif mode == "branch":
                # Use GitTools.git_branch (doesn't support 'all' param, uses -a flag internally)
                result = GitTools.git_branch()
                return result
            else:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Invalid mode: {mode}. Supported modes: 'status', 'diff', 'log', 'show', 'branch'"
                )
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error in git_inspect with mode '{mode}': {str(e)}"
            )
    
    @staticmethod
    def git_modify(action: str, files: List[str] = None, message: str = None, **kwargs) -> ToolResult:
        """
        Guarded write operations (requires confirmation).
        
        Replaces: git_add, git_commit
        
        Args:
            action: Operation - "add" or "commit"
            files: List of files to add/commit (required for add, optional for commit)
            message: Commit message (required for commit)
            **kwargs: Additional arguments:
                - add: force (optional, default: False)
                - commit: amend (optional, default: False)
        
        Returns:
            ToolResult with operation result
        
        Examples:
            git_modify(action="add", files=["src/main.py"])  # Add files
            git_modify(action="commit", message="Initial commit")  # Commit changes
        """
        try:
            if action == "add":
                # Use GitTools.git_add
                if not files:
                    return ToolResult(
                        success=False,
                        result=None,
                        error="files required for action='add'"
                    )
                force = kwargs.get("force", False)
                result = GitTools.git_add(files=files, force=force)
                return result
            elif action == "commit":
                # Use GitTools.git_commit
                if not message:
                    return ToolResult(
                        success=False,
                        result=None,
                        error="message required for action='commit'"
                    )
                amend = kwargs.get("amend", False)
                result = GitTools.git_commit(message=message, files=files, amend=amend)
                return result
            else:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Invalid action: {action}. Supported actions: 'add', 'commit'"
                )
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error in git_modify with action '{action}': {str(e)}"
            )

