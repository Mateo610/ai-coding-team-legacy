"""
Docker tools for agents to check service health and debug issues
"""
import subprocess
import json
import re
from pathlib import Path
from typing import Dict, Any, Optional, List

from tools.code_tools import ToolResult
from tools.file_tools import FileTools
from agents.timeout_config import TIMEOUT_CONFIG


class DockerTools:
    """Tools for Docker operations (read-only for security)"""
    
    @staticmethod
    def _is_safe_path(filepath: str) -> tuple[bool, Optional[str]]:
        """Check if filepath is safe to access (delegates to FileTools)"""
        return FileTools._is_safe_path(filepath)
    
    @staticmethod
    def _run_docker_command(command: List[str], timeout: int = 10) -> tuple[int, str, str]:
        """
        Run docker command and return (returncode, stdout, stderr).
        
        Security: Only allows read-only operations.
        """
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return 1, "", f"Command timed out after {timeout}s"
        except FileNotFoundError:
            return 1, "", "Docker not found. Is Docker installed?"
        except Exception as e:
            return 1, "", str(e)
    
    @staticmethod
    def docker_ps(path: str = ".") -> ToolResult:
        """
        List running Docker containers (read-only).
        
        Args:
            path: Project path (default: current directory)
        
        Returns:
            ToolResult with container list
        """
        try:
            # Validate path
            is_safe, error = DockerTools._is_safe_path(path)
            if not is_safe:
                return ToolResult(
                    success=False,
                    result=None,
                    error=error or "Path is not safe to access"
                )
            
            # Run docker ps
            command = ["docker", "ps", "--format", "json"]
            returncode, stdout, stderr = DockerTools._run_docker_command(command, timeout=10)
            
            if returncode != 0:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Docker ps failed: {stderr}"
                )
            
            # Parse JSON output
            containers = []
            for line in stdout.strip().split('\n'):
                if not line.strip():
                    continue
                try:
                    container = json.loads(line)
                    containers.append({
                        "id": container.get("ID", ""),
                        "name": container.get("Names", ""),
                        "image": container.get("Image", ""),
                        "status": container.get("Status", ""),
                        "ports": container.get("Ports", "")
                    })
                except json.JSONDecodeError:
                    continue
            
            return ToolResult(
                success=True,
                result={
                    "containers": containers,
                    "count": len(containers)
                },
                metadata={
                    "path": str(Path(path).resolve()),
                    "count": len(containers)
                }
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error listing containers: {str(e)}"
            )
    
    @staticmethod
    def docker_compose_ps(compose_file: str = "docker-compose.yml", path: str = ".") -> ToolResult:
        """
        List docker-compose services (read-only).
        
        Args:
            compose_file: Docker compose file (default: "docker-compose.yml")
            path: Project path (default: current directory)
        
        Returns:
            ToolResult with service list
        """
        try:
            # Validate path
            is_safe, error = DockerTools._is_safe_path(path)
            if not is_safe:
                return ToolResult(
                    success=False,
                    result=None,
                    error=error or "Path is not safe to access"
                )
            
            project_path = Path(path).resolve()
            compose_path = project_path / compose_file
            
            if not compose_path.exists():
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Docker compose file not found: {compose_file}"
                )
            
            # Run docker-compose ps
            command = ["docker-compose", "-f", str(compose_path), "ps", "--format", "json"]
            returncode, stdout, stderr = DockerTools._run_docker_command(command, timeout=10)
            
            if returncode != 0:
                # Try alternative: docker compose (v2)
                command = ["docker", "compose", "-f", str(compose_path), "ps", "--format", "json"]
                returncode, stdout, stderr = DockerTools._run_docker_command(command, timeout=10)
            
            if returncode != 0:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Docker compose ps failed: {stderr}"
                )
            
            # Parse JSON output
            services = []
            for line in stdout.strip().split('\n'):
                if not line.strip():
                    continue
                try:
                    service = json.loads(line)
                    services.append({
                        "name": service.get("Name", ""),
                        "service": service.get("Service", ""),
                        "state": service.get("State", ""),
                        "ports": service.get("Ports", "")
                    })
                except json.JSONDecodeError:
                    continue
            
            return ToolResult(
                success=True,
                result={
                    "services": services,
                    "count": len(services)
                },
                metadata={
                    "path": str(project_path),
                    "compose_file": compose_file,
                    "count": len(services)
                }
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error listing docker-compose services: {str(e)}"
            )
    
    @staticmethod
    def docker_logs(
        service: str,
        tail: int = 100,
        path: str = ".",
        compose_file: str = None
    ) -> ToolResult:
        """
        Get container logs (read-only).
        
        Args:
            service: Container name or service name
            tail: Number of lines to show (default: 100)
            path: Project path (default: current directory)
            compose_file: Docker compose file (optional, for service names)
        
        Returns:
            ToolResult with log output
        """
        try:
            # Validate path
            is_safe, error = DockerTools._is_safe_path(path)
            if not is_safe:
                return ToolResult(
                    success=False,
                    result=None,
                    error=error or "Path is not safe to access"
                )
            
            project_path = Path(path).resolve()
            
            # Build command
            if compose_file:
                compose_path = project_path / compose_file
                if compose_path.exists():
                    command = ["docker-compose", "-f", str(compose_path), "logs", "--tail", str(tail), service]
                    returncode, stdout, stderr = DockerTools._run_docker_command(command, timeout=15)
                    
                    if returncode != 0:
                        # Try docker compose v2
                        command = ["docker", "compose", "-f", str(compose_path), "logs", "--tail", str(tail), service]
                        returncode, stdout, stderr = DockerTools._run_docker_command(command, timeout=15)
                else:
                    # Fallback to docker logs
                    command = ["docker", "logs", "--tail", str(tail), service]
                    returncode, stdout, stderr = DockerTools._run_docker_command(command, timeout=15)
            else:
                # Use docker logs directly
                command = ["docker", "logs", "--tail", str(tail), service]
                returncode, stdout, stderr = DockerTools._run_docker_command(command, timeout=15)
            
            if returncode != 0:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Docker logs failed: {stderr}"
                )
            
            return ToolResult(
                success=True,
                result={
                    "logs": stdout,
                    "service": service,
                    "lines": len(stdout.split('\n'))
                },
                metadata={
                    "path": str(project_path),
                    "service": service,
                    "tail": tail
                }
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error getting docker logs: {str(e)}"
            )
    
    @staticmethod
    def docker_health(service: str, path: str = ".") -> ToolResult:
        """
        Check container health (read-only).
        
        Args:
            service: Container name
            path: Project path (default: current directory)
        
        Returns:
            ToolResult with health status
        """
        try:
            # Validate path
            is_safe, error = DockerTools._is_safe_path(path)
            if not is_safe:
                return ToolResult(
                    success=False,
                    result=None,
                    error=error or "Path is not safe to access"
                )
            
            # Get container inspect
            command = ["docker", "inspect", "--format", "{{.State.Health.Status}}", service]
            returncode, stdout, stderr = DockerTools._run_docker_command(command, timeout=10)
            
            if returncode != 0:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Docker inspect failed: {stderr}"
                )
            
            health_status = stdout.strip()
            
            # Get container status
            command = ["docker", "inspect", "--format", "{{.State.Status}}", service]
            returncode, status_stdout, status_stderr = DockerTools._run_docker_command(command, timeout=10)
            
            container_status = status_stdout.strip() if returncode == 0 else "unknown"
            
            return ToolResult(
                success=True,
                result={
                    "service": service,
                    "health_status": health_status,
                    "container_status": container_status,
                    "healthy": health_status == "healthy"
                },
                metadata={
                    "path": str(Path(path).resolve()),
                    "service": service,
                    "health_status": health_status
                }
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error checking container health: {str(e)}"
            )
    
    @staticmethod
    def docker_status(path: str = ".") -> ToolResult:
        """
        Overall Docker status (read-only).
        
        Args:
            path: Project path (default: current directory)
        
        Returns:
            ToolResult with Docker status summary
        """
        try:
            # Validate path
            is_safe, error = DockerTools._is_safe_path(path)
            if not is_safe:
                return ToolResult(
                    success=False,
                    result=None,
                    error=error or "Path is not safe to access"
                )
            
            # Check Docker daemon
            command = ["docker", "info"]
            returncode, stdout, stderr = DockerTools._run_docker_command(command, timeout=5)
            
            if returncode != 0:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Docker daemon not accessible: {stderr}"
                )
            
            # Get running containers count
            ps_result = DockerTools.docker_ps(path)
            container_count = ps_result.result.get("count", 0) if ps_result.success else 0
            
            # Get docker-compose services if available
            project_path = Path(path).resolve()
            compose_file = project_path / "docker-compose.yml"
            service_count = 0
            if compose_file.exists():
                compose_result = DockerTools.docker_compose_ps("docker-compose.yml", path)
                if compose_result.success:
                    service_count = compose_result.result.get("count", 0)
            
            return ToolResult(
                success=True,
                result={
                    "docker_running": True,
                    "containers_running": container_count,
                    "services_running": service_count,
                    "status": "healthy" if returncode == 0 else "unhealthy"
                },
                metadata={
                    "path": str(project_path),
                    "containers": container_count,
                    "services": service_count
                }
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error getting Docker status: {str(e)}"
            )

