"""
Health check system for monitoring system status.
"""

import os
import requests
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
from agents.exceptions import ConfigurationError
from agents.timeout_config import TIMEOUT_CONFIG


class HealthStatus(Enum):
    """Health check status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of a health check"""
    component: str
    status: HealthStatus
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    response_time_ms: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "component": self.component,
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "response_time_ms": self.response_time_ms,
        }


class HealthChecker:
    """Health check system for monitoring components"""
    
    def __init__(self, base_url: str = None, data_dir: str = None):
        """
        Initialize health checker.
        
        Args:
            base_url: Ollama base URL (default: from env)
            data_dir: Data directory for logging (default: from env)
        """
        self.base_url = base_url or os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        self.data_dir = Path(data_dir or os.getenv('DATA_DIR', '~/ai-coding-team/data'))
        self.data_dir = self.data_dir.expanduser()
    
    def check_model_availability(self, model_name: str = None) -> HealthCheckResult:
        """
        Check if Ollama model is available and responding.
        
        Args:
            model_name: Optional model name to check (if None, checks if Ollama is accessible)
        
        Returns:
            HealthCheckResult with model status
        """
        start_time = time.time()
        component = f"model_{model_name}" if model_name else "ollama_service"
        
        try:
            # Get timeout from config
            timeout = TIMEOUT_CONFIG.get_health_check_timeout()
            
            # Check if Ollama is accessible
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=timeout
            )
            response.raise_for_status()
            
            # Check if specific model is available
            if model_name:
                models_data = response.json()
                available_models = [m.get('name', '') for m in models_data.get('models', [])]
                
                if model_name not in available_models:
                    response_time_ms = int((time.time() - start_time) * 1000)
                    return HealthCheckResult(
                        component=component,
                        status=HealthStatus.DEGRADED,
                        message=f"Model '{model_name}' not found in Ollama",
                        details={
                            "available_models": available_models,
                            "requested_model": model_name,
                        },
                        response_time_ms=response_time_ms,
                    )
                
                response_time_ms = int((time.time() - start_time) * 1000)
                return HealthCheckResult(
                    component=component,
                    status=HealthStatus.HEALTHY,
                    message=f"Model '{model_name}' is available",
                    details={
                        "model": model_name,
                        "available_models": len(available_models),
                    },
                    response_time_ms=response_time_ms,
                )
            else:
                # Just check if Ollama is accessible
                response_time_ms = int((time.time() - start_time) * 1000)
                return HealthCheckResult(
                    component=component,
                    status=HealthStatus.HEALTHY,
                    message="Ollama service is accessible",
                    details={
                        "base_url": self.base_url,
                    },
                    response_time_ms=response_time_ms,
                )
                
        except requests.exceptions.ConnectionError:
            response_time_ms = int((time.time() - start_time) * 1000)
            return HealthCheckResult(
                component=component,
                status=HealthStatus.UNHEALTHY,
                message=f"Cannot connect to Ollama at {self.base_url}",
                details={
                    "base_url": self.base_url,
                    "error_type": "ConnectionError",
                },
                response_time_ms=response_time_ms,
            )
        except requests.exceptions.Timeout:
            response_time_ms = int((time.time() - start_time) * 1000)
            return HealthCheckResult(
                component=component,
                status=HealthStatus.UNHEALTHY,
                message=f"Ollama request timed out",
                details={
                    "base_url": self.base_url,
                    "error_type": "Timeout",
                },
                response_time_ms=response_time_ms,
            )
        except requests.exceptions.HTTPError as e:
            response_time_ms = int((time.time() - start_time) * 1000)
            return HealthCheckResult(
                component=component,
                status=HealthStatus.UNHEALTHY,
                message=f"Ollama HTTP error: {e.response.status_code}",
                details={
                    "base_url": self.base_url,
                    "status_code": e.response.status_code,
                    "error_type": "HTTPError",
                },
                response_time_ms=response_time_ms,
            )
        except Exception as e:
            response_time_ms = int((time.time() - start_time) * 1000)
            return HealthCheckResult(
                component=component,
                status=HealthStatus.UNKNOWN,
                message=f"Unknown error checking Ollama: {str(e)}",
                details={
                    "base_url": self.base_url,
                    "error_type": type(e).__name__,
                },
                response_time_ms=response_time_ms,
            )
    
    def check_logging_status(self) -> HealthCheckResult:
        """
        Check if logging directory is accessible and writable.
        
        Returns:
            HealthCheckResult with logging status
        """
        start_time = time.time()
        component = "logging"
        
        try:
            # Check if data directory exists
            if not self.data_dir.exists():
                # Try to create it
                try:
                    self.data_dir.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    response_time_ms = int((time.time() - start_time) * 1000)
                    return HealthCheckResult(
                        component=component,
                        status=HealthStatus.UNHEALTHY,
                        message=f"Cannot create data directory: {str(e)}",
                        details={
                            "data_dir": str(self.data_dir),
                            "error_type": type(e).__name__,
                        },
                        response_time_ms=response_time_ms,
                    )
            
            # Check if directory is writable
            test_file = self.data_dir / ".health_check_test"
            try:
                test_file.write_text("test")
                test_file.unlink()
                
                response_time_ms = int((time.time() - start_time) * 1000)
                return HealthCheckResult(
                    component=component,
                    status=HealthStatus.HEALTHY,
                    message="Logging directory is accessible and writable",
                    details={
                        "data_dir": str(self.data_dir),
                        "writable": True,
                    },
                    response_time_ms=response_time_ms,
                )
            except PermissionError:
                response_time_ms = int((time.time() - start_time) * 1000)
                return HealthCheckResult(
                    component=component,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Data directory is not writable: {self.data_dir}",
                    details={
                        "data_dir": str(self.data_dir),
                        "writable": False,
                    },
                    response_time_ms=response_time_ms,
                )
                
        except Exception as e:
            response_time_ms = int((time.time() - start_time) * 1000)
            return HealthCheckResult(
                component=component,
                status=HealthStatus.UNKNOWN,
                message=f"Error checking logging status: {str(e)}",
                details={
                    "data_dir": str(self.data_dir),
                    "error_type": type(e).__name__,
                },
                response_time_ms=response_time_ms,
            )
    
    def check_configuration(self, config_path: str = "config/models.yaml") -> HealthCheckResult:
        """
        Check if configuration is valid.
        
        Args:
            config_path: Path to configuration file
        
        Returns:
            HealthCheckResult with configuration status
        """
        start_time = time.time()
        component = "configuration"
        
        try:
            import yaml
            
            config_file = Path(config_path)
            
            if not config_file.exists():
                response_time_ms = int((time.time() - start_time) * 1000)
                return HealthCheckResult(
                    component=component,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Configuration file not found: {config_path}",
                    details={
                        "config_path": config_path,
                    },
                    response_time_ms=response_time_ms,
                )
            
            # Try to load and validate config
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            # Check required sections
            required_sections = ['models', 'routing']
            missing_sections = [s for s in required_sections if s not in config]
            
            if missing_sections:
                response_time_ms = int((time.time() - start_time) * 1000)
                return HealthCheckResult(
                    component=component,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Configuration missing required sections: {missing_sections}",
                    details={
                        "config_path": config_path,
                        "missing_sections": missing_sections,
                    },
                    response_time_ms=response_time_ms,
                )
            
            # Check if models section has required keys
            models = config.get('models', {})
            required_models = ['orchestrator', 'implementation']
            missing_models = [m for m in required_models if m not in models]
            
            if missing_models:
                response_time_ms = int((time.time() - start_time) * 1000)
                return HealthCheckResult(
                    component=component,
                    status=HealthStatus.DEGRADED,
                    message=f"Configuration missing required models: {missing_models}",
                    details={
                        "config_path": config_path,
                        "missing_models": missing_models,
                    },
                    response_time_ms=response_time_ms,
                )
            
            response_time_ms = int((time.time() - start_time) * 1000)
            return HealthCheckResult(
                component=component,
                status=HealthStatus.HEALTHY,
                message="Configuration is valid",
                details={
                    "config_path": config_path,
                    "models_configured": list(models.keys()),
                },
                response_time_ms=response_time_ms,
            )
            
        except yaml.YAMLError as e:
            response_time_ms = int((time.time() - start_time) * 1000)
            return HealthCheckResult(
                component=component,
                status=HealthStatus.UNHEALTHY,
                message=f"Invalid YAML in configuration: {str(e)}",
                details={
                    "config_path": config_path,
                    "error_type": "YAMLError",
                },
                response_time_ms=response_time_ms,
            )
        except Exception as e:
            response_time_ms = int((time.time() - start_time) * 1000)
            return HealthCheckResult(
                component=component,
                status=HealthStatus.UNKNOWN,
                message=f"Error checking configuration: {str(e)}",
                details={
                    "config_path": config_path,
                    "error_type": type(e).__name__,
                },
                response_time_ms=response_time_ms,
            )
    
    def check_models(self, config_path: str = "config/models.yaml") -> List[HealthCheckResult]:
        """
        Check all configured models.
        
        Args:
            config_path: Path to configuration file
        
        Returns:
            List of HealthCheckResult for each model
        """
        try:
            import yaml
            
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            models = config.get('models', {})
            results = []
            
            for model_key, model_config in models.items():
                model_name = model_config.get('name', '')
                if model_name:
                    result = self.check_model_availability(model_name)
                    result.component = f"model_{model_key}"
                    results.append(result)
            
            return results
            
        except Exception:
            # Return empty list if config can't be loaded
            return []
    
    def check_all(self, config_path: str = "config/models.yaml") -> Dict[str, Any]:
        """
        Run all health checks and return comprehensive status.
        
        Args:
            config_path: Path to configuration file
        
        Returns:
            Dictionary with overall status and component results
        """
        start_time = time.time()
        
        results = {
            "timestamp": time.time(),
            "overall_status": HealthStatus.HEALTHY.value,
            "components": {},
        }
        
        # Check Ollama service
        ollama_result = self.check_model_availability()
        results["components"]["ollama_service"] = ollama_result.to_dict()
        
        # Check logging
        logging_result = self.check_logging_status()
        results["components"]["logging"] = logging_result.to_dict()
        
        # Check configuration
        config_result = self.check_configuration(config_path)
        results["components"]["configuration"] = config_result.to_dict()
        
        # Check all models
        model_results = self.check_models(config_path)
        for model_result in model_results:
            results["components"][model_result.component] = model_result.to_dict()
        
        # Determine overall status
        component_statuses = [HealthStatus(r["status"]) for r in results["components"].values()]
        
        if all(s == HealthStatus.HEALTHY for s in component_statuses):
            results["overall_status"] = HealthStatus.HEALTHY.value
        elif any(s == HealthStatus.UNHEALTHY for s in component_statuses):
            results["overall_status"] = HealthStatus.UNHEALTHY.value
        elif any(s == HealthStatus.DEGRADED for s in component_statuses):
            results["overall_status"] = HealthStatus.DEGRADED.value
        else:
            results["overall_status"] = HealthStatus.UNKNOWN.value
        
        results["response_time_ms"] = int((time.time() - start_time) * 1000)
        results["total_components"] = len(results["components"])
        
        healthy_count = sum(1 for r in results["components"].values() if r["status"] == "healthy")
        results["healthy_components"] = healthy_count
        
        return results
    
    def get_health_summary(self, config_path: str = "config/models.yaml") -> str:
        """
        Get human-readable health summary.
        
        Args:
            config_path: Path to configuration file
        
        Returns:
            Human-readable health summary string
        """
        health = self.check_all(config_path)
        
        status_icon = {
            "healthy": "✅",
            "degraded": "⚠️",
            "unhealthy": "❌",
            "unknown": "❓",
        }
        
        lines = [
            f"System Health: {status_icon.get(health['overall_status'], '❓')} {health['overall_status'].upper()}",
            f"Components: {health['healthy_components']}/{health['total_components']} healthy",
            f"Response time: {health['response_time_ms']}ms",
            "",
            "Component Details:",
        ]
        
        for component_name, component_data in health["components"].items():
            icon = status_icon.get(component_data["status"], "❓")
            lines.append(f"  {icon} {component_name}: {component_data['status']}")
            if component_data.get("response_time_ms"):
                lines.append(f"     Response: {component_data['response_time_ms']}ms")
            if component_data.get("message"):
                lines.append(f"     {component_data['message']}")
        
        return "\n".join(lines)


# Create singleton instance
HEALTH_CHECKER = HealthChecker()

