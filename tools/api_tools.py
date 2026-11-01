"""
API testing tools for agents to test endpoints, validate responses, and verify API functionality
"""
import subprocess
import time
import json
import requests
from typing import Dict, Any, Optional, List
from pathlib import Path
import tempfile
import os
import threading
import signal

from tools.code_tools import ToolResult
from agents.timeout_config import TIMEOUT_CONFIG


class APITools:
    """Tools for API testing with security restrictions"""
    
    # Track running test servers
    _test_servers: Dict[str, Dict[str, Any]] = {}
    
    @staticmethod
    def _start_test_server(
        app_file: str,
        port: int = 5000,
        host: str = "127.0.0.1",
        timeout: int = 10
    ) -> tuple[Optional[subprocess.Popen], Optional[str]]:
        """
        Start test server in background process.
        
        Args:
            app_file: Path to Flask/FastAPI application file
            port: Port to run server on
            host: Host to bind to
            timeout: Timeout for server startup
        
        Returns:
            Tuple of (process, error_message)
        """
        try:
            # Check if file exists
            app_path = Path(app_file)
            if not app_path.exists():
                return None, f"Application file not found: {app_file}"
            
            # Detect framework (Flask, FastAPI)
            content = app_path.read_text()
            is_flask = 'Flask' in content or 'from flask import' in content
            is_fastapi = 'FastAPI' in content or 'from fastapi import' in content
            
            if not (is_flask or is_fastapi):
                return None, "Application file must be Flask or FastAPI"
            
            # Start server based on framework
            if is_flask:
                # Flask: python app.py
                env = os.environ.copy()
                env['FLASK_ENV'] = 'testing'
                env['FLASK_DEBUG'] = '0'
                
                process = subprocess.Popen(
                    ['python3', str(app_path)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=env,
                    cwd=str(app_path.parent)
                )
            
            elif is_fastapi:
                # FastAPI: uvicorn app:app --host 127.0.0.1 --port 5000
                try:
                    import uvicorn
                    # Start uvicorn in subprocess
                    process = subprocess.Popen(
                        ['uvicorn', 'main:app', '--host', host, '--port', str(port)],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        cwd=str(app_path.parent)
                    )
                except ImportError:
                    return None, "uvicorn not installed. Install with: pip install uvicorn"
            
            # Wait for server to start
            time.sleep(2)  # Give server time to start
            
            # Check if process is still running
            if process.poll() is not None:
                # Process died, get error
                stdout, stderr = process.communicate()
                error_msg = stderr.decode('utf-8') if stderr else stdout.decode('utf-8')
                return None, f"Server failed to start: {error_msg[:200]}"
            
            return process, None
        
        except Exception as e:
            return None, f"Error starting server: {str(e)}"
    
    @staticmethod
    def start_test_server(
        app_file: str,
        port: int = 5000,
        host: str = "127.0.0.1"
    ) -> ToolResult:
        """
        Start test server in background.
        
        Security: Only binds to localhost (127.0.0.1).
        
        Usage from agent:
        TOOL: start_test_server
        INPUT: <app_file>\n<port>
        
        Args:
            app_file: Path to Flask/FastAPI application file
            port: Port to run server on (default: 5000)
            host: Host to bind to (default: 127.0.0.1, for security)
        
        Returns:
            ToolResult with server ID and status
        """
        try:
            # Security: Only allow localhost
            if host not in ['127.0.0.1', 'localhost']:
                return ToolResult(
                    success=False,
                    result=None,
                    error="Only localhost (127.0.0.1) is allowed for security",
                    metadata={"host": host}
                )
            
            # Start server
            process, error = APITools._start_test_server(app_file, port, host)
            
            if error:
                return ToolResult(
                    success=False,
                    result=None,
                    error=error,
                    metadata={"app_file": app_file, "port": port}
                )
            
            # Generate server ID
            server_id = f"{app_file}_{port}"
            
            # Store server info
            APITools._test_servers[server_id] = {
                "process": process,
                "port": port,
                "host": host,
                "app_file": app_file,
                "started_at": time.time()
            }
            
            # Wait a bit for server to fully start
            time.sleep(1)
            
            return ToolResult(
                success=True,
                result=f"Test server started on http://{host}:{port}",
                metadata={
                    "server_id": server_id,
                    "port": port,
                    "host": host,
                    "url": f"http://{host}:{port}"
                }
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error starting test server: {str(e)}",
                metadata={"app_file": app_file}
            )
    
    @staticmethod
    def stop_test_server(server_id: str) -> ToolResult:
        """
        Stop test server.
        
        Usage from agent:
        TOOL: stop_test_server
        INPUT: <server_id>
        
        Args:
            server_id: Server ID from start_test_server
        
        Returns:
            ToolResult with status
        """
        try:
            if server_id not in APITools._test_servers:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Server not found: {server_id}",
                    metadata={"server_id": server_id}
                )
            
            server_info = APITools._test_servers[server_id]
            process = server_info["process"]
            
            # Terminate process
            process.terminate()
            
            # Wait for termination
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill
                process.kill()
            
            # Remove from tracking
            del APITools._test_servers[server_id]
            
            return ToolResult(
                success=True,
                result=f"Test server stopped: {server_id}",
                metadata={"server_id": server_id}
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error stopping server: {str(e)}",
                metadata={"server_id": server_id}
            )
    
    @staticmethod
    def test_endpoint(
        url: str,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        body: Optional[Dict[str, Any]] = None,
        expected_status: int = 200,
        timeout: int = 10
    ) -> ToolResult:
        """
        Test API endpoint and return response.
        
        Security: Only allows requests to localhost (127.0.0.1).
        
        Usage from agent:
        TOOL: test_endpoint
        INPUT: <url>\n<method>\n<headers>\n<body>
        
        Args:
            url: Endpoint URL
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            headers: Request headers (dict)
            body: Request body (dict, will be JSON encoded)
            expected_status: Expected HTTP status code (default: 200)
            timeout: Request timeout in seconds
        
        Returns:
            ToolResult with response data
        """
        try:
            # Security: Only allow localhost
            if '127.0.0.1' not in url and 'localhost' not in url and not url.startswith('/'):
                return ToolResult(
                    success=False,
                    result=None,
                    error="Only localhost (127.0.0.1) URLs allowed for security",
                    metadata={"url": url}
                )
            
            # Ensure URL starts with http:// if it's a relative path
            if url.startswith('/'):
                url = f"http://127.0.0.1:5000{url}"
            
            # Prepare request
            request_kwargs = {
                "timeout": timeout,
                "headers": headers or {}
            }
            
            # Add body for methods that support it
            if method.upper() in ['POST', 'PUT', 'PATCH']:
                if body:
                    request_kwargs["json"] = body
                    if 'Content-Type' not in request_kwargs["headers"]:
                        request_kwargs["headers"]["Content-Type"] = "application/json"
            
            # Make request
            method_upper = method.upper()
            if method_upper == "GET":
                response = requests.get(url, **request_kwargs)
            elif method_upper == "POST":
                response = requests.post(url, **request_kwargs)
            elif method_upper == "PUT":
                response = requests.put(url, **request_kwargs)
            elif method_upper == "PATCH":
                response = requests.patch(url, **request_kwargs)
            elif method_upper == "DELETE":
                response = requests.delete(url, **request_kwargs)
            else:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Unsupported HTTP method: {method}",
                    metadata={"method": method}
                )
            
            # Parse response
            try:
                response_data = response.json()
            except:
                response_data = response.text
            
            # Check status
            status_match = response.status_code == expected_status
            
            return ToolResult(
                success=status_match,
                result={
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "data": response_data,
                    "expected_status": expected_status,
                    "status_match": status_match
                },
                error="" if status_match else f"Expected status {expected_status}, got {response.status_code}",
                metadata={
                    "url": url,
                    "method": method,
                    "status_code": response.status_code,
                    "expected_status": expected_status,
                    "response_size": len(str(response_data))
                }
            )
        
        except requests.exceptions.ConnectionError:
            return ToolResult(
                success=False,
                result=None,
                error=f"Connection failed. Is the server running at {url}?",
                metadata={"url": url}
            )
        except requests.exceptions.Timeout:
            return ToolResult(
                success=False,
                result=None,
                error=f"Request timed out after {timeout} seconds",
                metadata={"url": url, "timeout": timeout}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error testing endpoint: {str(e)}",
                metadata={"url": url}
            )
    
    @staticmethod
    def validate_response(
        response: Dict[str, Any],
        expected_schema: Dict[str, Any]
    ) -> ToolResult:
        """
        Validate API response matches expected schema.
        
        Usage from agent:
        TOOL: validate_response
        INPUT: <response_json>\n<schema_json>
        
        Args:
            response: API response (dict from test_endpoint)
            expected_schema: Expected schema (dict with keys and types)
        
        Returns:
            ToolResult with validation status
        """
        try:
            # Extract data from response if it's a full response object
            if isinstance(response, dict) and "data" in response:
                data = response["data"]
            else:
                data = response
            
            errors = []
            
            # Validate required fields
            required_fields = expected_schema.get("required", [])
            for field in required_fields:
                if field not in data:
                    errors.append(f"Missing required field: {field}")
            
            # Validate field types
            properties = expected_schema.get("properties", {})
            for field, expected_type in properties.items():
                if field in data:
                    value = data[field]
                    # Simple type checking
                    type_map = {
                        "string": str,
                        "integer": int,
                        "number": (int, float),
                        "boolean": bool,
                        "array": list,
                        "object": dict
                    }
                    
                    expected_python_type = type_map.get(expected_type, None)
                    if expected_python_type and not isinstance(value, expected_python_type):
                        errors.append(
                            f"Field '{field}' has wrong type. "
                            f"Expected {expected_type}, got {type(value).__name__}"
                        )
            
            if errors:
                return ToolResult(
                    success=False,
                    result=None,
                    error="Validation failed:\n" + "\n".join(f"- {e}" for e in errors),
                    metadata={"errors": errors, "schema": expected_schema}
                )
            
            return ToolResult(
                success=True,
                result="Response matches expected schema",
                metadata={"schema": expected_schema}
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error validating response: {str(e)}",
                metadata={"response": str(response)[:200]}
            )
    
    @staticmethod
    def test_authentication(
        url: str,
        token: str,
        method: str = "GET",
        timeout: int = 10
    ) -> ToolResult:
        """
        Test authentication on protected endpoint.
        
        Usage from agent:
        TOOL: test_authentication
        INPUT: <url>\n<token>
        
        Args:
            url: Protected endpoint URL
            token: Authentication token
            method: HTTP method (default: GET)
            timeout: Request timeout
        
        Returns:
            ToolResult with authentication test result
        """
        try:
            # Security: Only allow localhost
            if '127.0.0.1' not in url and 'localhost' not in url and not url.startswith('/'):
                return ToolResult(
                    success=False,
                    result=None,
                    error="Only localhost (127.0.0.1) URLs allowed for security",
                    metadata={"url": url}
                )
            
            # Ensure URL starts with http:// if it's a relative path
            if url.startswith('/'):
                url = f"http://127.0.0.1:5000{url}"
            
            # Test with token
            headers = {
                "Authorization": f"Bearer {token}"
            }
            
            result = APITools.test_endpoint(
                url=url,
                method=method,
                headers=headers,
                expected_status=200,
                timeout=timeout
            )
            
            if result.success:
                return ToolResult(
                    success=True,
                    result="Authentication successful",
                    metadata={
                        "url": url,
                        "status_code": result.metadata.get("status_code"),
                        "authenticated": True
                    }
                )
            else:
                # Try without token to verify it's protected
                result_no_token = APITools.test_endpoint(
                    url=url,
                    method=method,
                    expected_status=401,
                    timeout=timeout
                )
                
                if result_no_token.success:
                    return ToolResult(
                        success=False,
                        result=None,
                        error="Authentication failed. Endpoint requires authentication but token was rejected.",
                        metadata={
                            "url": url,
                            "authenticated": False,
                            "with_token_status": result.metadata.get("status_code"),
                            "without_token_status": result_no_token.metadata.get("status_code")
                        }
                    )
                else:
                    return ToolResult(
                        success=False,
                        result=None,
                        error="Endpoint may not be properly protected. Check authentication implementation.",
                        metadata={
                            "url": url,
                            "authenticated": False
                        }
                    )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error testing authentication: {str(e)}",
                metadata={"url": url}
            )

