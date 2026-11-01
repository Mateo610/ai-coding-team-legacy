"""
Consolidated API Tools
Replaces: api_start_server, api_stop_server, api_test_endpoint, api_validate_response, api_test_auth, extract_api_spec
"""

import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tools.code_tools import ToolResult
from tools.api_tools import APITools
from tools.documentation_tools import DocumentationTools


class APIConsolidated:
    """Consolidated API tools with mode-based operations"""
    
    @staticmethod
    def api_control(action: str, server_file: str = None, port: int = None) -> ToolResult:
        """
        Control dev APIs locally.
        
        Replaces: api_start_server, api_stop_server
        
        Args:
            action: Operation - "start" or "stop"
            server_file: Path to server file (required for start)
            port: Port number (optional, auto-detect if not provided)
        
        Returns:
            ToolResult with operation result
        
        Examples:
            api_control(action="start", server_file="app.py", port=5000)  # Start server
            api_control(action="stop")  # Stop server
        """
        try:
            if action == "start":
                # Use APITools.api_start_server
                if not server_file:
                    return ToolResult(
                        success=False,
                        result=None,
                        error="server_file required for action='start'"
                    )
                result = APITools.api_start_server(server_file, port=port)
                return result
            elif action == "stop":
                # Use APITools.api_stop_server
                result = APITools.api_stop_server()
                return result
            else:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Invalid action: {action}. Supported actions: 'start', 'stop'"
                )
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error in api_control with action '{action}': {str(e)}"
            )
    
    @staticmethod
    def api_test(url: str, method: str = "GET", mode: str = "test", headers: Dict = None, data: Any = None, expected_status: int = None, auth: Dict = None) -> ToolResult:
        """
        Test HTTP endpoints, validate responses, inspect docs.
        
        Replaces: api_test_endpoint, api_validate_response, api_test_auth, extract_api_spec
        
        Args:
            url: API endpoint URL
            method: HTTP method (default: "GET")
            mode: Operation mode:
                - "test" (default): Test endpoint
                - "validate": Validate response
                - "auth": Test authentication
                - "spec": Extract API specification
            headers: HTTP headers (optional)
            data: Request data (optional)
            expected_status: Expected HTTP status code (optional, for validate mode)
            auth: Authentication credentials (optional, for auth mode)
        
        Returns:
            ToolResult with test results based on mode
        
        Examples:
            api_test("http://localhost:5000/api/users", mode="test")  # Test endpoint
            api_test("http://localhost:5000/api/users", mode="validate", expected_status=200)  # Validate response
            api_test("http://localhost:5000/api/users", mode="auth", auth={"token": "..."})  # Test auth
            api_test("http://localhost:5000/docs", mode="spec")  # Extract API spec
        """
        try:
            if mode == "test":
                # Use APITools.api_test_endpoint
                result = APITools.api_test_endpoint(url, method=method, headers=headers, data=data)
                return result
            elif mode == "validate":
                # Use APITools.api_validate_response
                if expected_status is None:
                    expected_status = 200  # Default
                result = APITools.api_validate_response(url, method=method, expected_status=expected_status, headers=headers, data=data)
                return result
            elif mode == "auth":
                # Use APITools.api_test_auth
                result = APITools.api_test_auth(url, method=method, auth=auth, headers=headers, data=data)
                return result
            elif mode == "spec":
                # Use DocumentationTools.extract_api_spec
                result = DocumentationTools.extract_api_spec(url)
                return result
            else:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Invalid mode: {mode}. Supported modes: 'test', 'validate', 'auth', 'spec'"
                )
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error in api_test with mode '{mode}': {str(e)}"
            )

