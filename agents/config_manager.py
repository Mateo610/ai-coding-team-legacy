"""
Configuration management system for the AI software team.
Provides centralized configuration loading, validation, and environment-based configs.
"""

import os
import yaml
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass, field
from agents.exceptions import ConfigurationError


class Environment(Enum):
    """Deployment environment"""
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"


@dataclass
class ModelConfig:
    """Model configuration"""
    name: str
    temperature: float
    max_tokens: int
    
    def validate(self) -> List[str]:
        """Validate model configuration"""
        errors = []
        
        if not self.name or not isinstance(self.name, str):
            errors.append("Model name must be a non-empty string")
        
        if not isinstance(self.temperature, (int, float)) or not (0 <= self.temperature <= 2):
            errors.append(f"Temperature must be between 0 and 2, got {self.temperature}")
        
        if not isinstance(self.max_tokens, int) or self.max_tokens <= 0:
            errors.append(f"Max tokens must be a positive integer, got {self.max_tokens}")
        
        return errors


@dataclass
class RoutingConfig:
    """Routing configuration"""
    complexity_threshold: int
    weights: Dict[str, int] = field(default_factory=dict)
    
    def validate(self) -> List[str]:
        """Validate routing configuration"""
        errors = []
        
        if not isinstance(self.complexity_threshold, int) or not (0 <= self.complexity_threshold <= 10):
            errors.append(f"Complexity threshold must be between 0 and 10, got {self.complexity_threshold}")
        
        if not isinstance(self.weights, dict):
            errors.append("Routing weights must be a dictionary")
        
        return errors


@dataclass
class ClaudeConfig:
    """Claude API configuration"""
    model: str
    max_tokens: int
    
    def validate(self) -> List[str]:
        """Validate Claude configuration"""
        errors = []
        
        if not self.model or not isinstance(self.model, str):
            errors.append("Claude model must be a non-empty string")
        
        if not isinstance(self.max_tokens, int) or self.max_tokens <= 0:
            errors.append(f"Claude max_tokens must be a positive integer, got {self.max_tokens}")
        
        return errors


class ConfigManager:
    """
    Centralized configuration management system.
    Supports environment-based configs, validation, and hot-reload.
    """
    
    DEFAULT_CONFIG_PATH = "config/models.yaml"
    DEFAULT_ENV_FILE = "config/.env"
    
    # Default values
    DEFAULT_VALUES = {
        "ollama_base_url": "http://localhost:11434",
        "data_dir": "~/ai-coding-team/data",
        "log_level": "INFO",
        "complexity_threshold": 8,
        "max_iterations": 3,
    }
    
    def __init__(self, config_path: str = None, env: Environment = None, validate: bool = True):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Path to configuration file (default: config/models.yaml)
            env: Environment (default: auto-detect from ENV)
            validate: Whether to validate configuration on load
        """
        self.config_path = Path(config_path or self.DEFAULT_CONFIG_PATH)
        self.env_file = Path(self.DEFAULT_ENV_FILE)
        self.env = env or self._detect_environment()
        self.validate = validate
        
        # Track config file modification time for hot-reload
        self._config_mtime = None
        
        # Load configuration
        self.config: Dict[str, Any] = {}
        self.models: Dict[str, ModelConfig] = {}
        self.routing: Optional[RoutingConfig] = None
        self.claude: Optional[ClaudeConfig] = None
        self.timeouts: Dict[str, int] = {}
        
        # Load environment variables
        self._load_env_vars()
        
        # Load configuration file
        self.reload()
    
    def _detect_environment(self) -> Environment:
        """Detect environment from environment variables"""
        env_str = os.getenv("AI_TEAM_ENV", "").lower()
        
        if env_str == "production":
            return Environment.PRODUCTION
        elif env_str == "testing":
            return Environment.TESTING
        else:
            return Environment.DEVELOPMENT
    
    def _load_env_vars(self) -> None:
        """Load environment variables (including from .env file if exists)"""
        from dotenv import load_dotenv
        
        # Load .env file if it exists
        if self.env_file.exists():
            load_dotenv(self.env_file)
    
    def reload(self) -> None:
        """Reload configuration from file"""
        if not self.config_path.exists():
            raise ConfigurationError(
                f"Configuration file not found: {self.config_path}",
                details={"config_path": str(self.config_path)}
            )
        
        try:
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise ConfigurationError(
                f"Invalid YAML in configuration file: {str(e)}",
                details={"config_path": str(self.config_path), "error": str(e)}
            )
        except Exception as e:
            raise ConfigurationError(
                f"Failed to load configuration: {str(e)}",
                details={"config_path": str(self.config_path), "error": str(e)}
            )
        
        # Update modification time
        self._config_mtime = self.config_path.stat().st_mtime
        
        # Parse configuration sections
        self._parse_models()
        self._parse_routing()
        self._parse_claude()
        self._parse_timeouts()
        
        # Validate if requested
        if self.validate:
            self._validate_config()
    
    def _parse_models(self) -> None:
        """Parse models configuration"""
        self.models = {}
        
        models_config = self.config.get("models", {})
        
        for key, model_data in models_config.items():
            if not isinstance(model_data, dict):
                continue
            
            model_config = ModelConfig(
                name=model_data.get("name", ""),
                temperature=float(model_data.get("temperature", 0.2)),
                max_tokens=int(model_data.get("max_tokens", 2000))
            )
            
            self.models[key] = model_config
    
    def _parse_routing(self) -> None:
        """Parse routing configuration"""
        routing_config = self.config.get("routing", {})
        
        self.routing = RoutingConfig(
            complexity_threshold=int(routing_config.get("complexity_threshold", 8)),
            weights=routing_config.get("weights", {})
        )
    
    def _parse_claude(self) -> None:
        """Parse Claude configuration"""
        claude_config = self.config.get("claude", {})
        
        if claude_config:
            self.claude = ClaudeConfig(
                model=claude_config.get("model", ""),
                max_tokens=int(claude_config.get("max_tokens", 4000))
            )
    
    def _parse_timeouts(self) -> None:
        """Parse timeout configuration"""
        timeouts_config = self.config.get("timeouts", {})
        self.timeouts = {
            key: int(value)
            for key, value in timeouts_config.items()
            if isinstance(value, (int, float)) and value > 0
        }
    
    def _validate_config(self) -> None:
        """Validate entire configuration"""
        errors = []
        
        # Validate models
        if not self.models:
            errors.append("No models configured")
        
        required_models = ["orchestrator", "implementation"]
        for model_key in required_models:
            if model_key not in self.models:
                errors.append(f"Required model '{model_key}' not found")
            else:
                model_errors = self.models[model_key].validate()
                errors.extend([f"Model '{model_key}': {e}" for e in model_errors])
        
        # Validate routing
        if not self.routing:
            errors.append("Routing configuration not found")
        else:
            routing_errors = self.routing.validate()
            errors.extend([f"Routing: {e}" for e in routing_errors])
        
        # Validate Claude (optional)
        if self.claude:
            claude_errors = self.claude.validate()
            errors.extend([f"Claude: {e}" for e in claude_errors])
        
        # Raise if validation failed
        if errors:
            raise ConfigurationError(
                f"Configuration validation failed: {len(errors)} error(s)",
                details={"errors": errors}
            )
    
    def get_model_config(self, key: str) -> Optional[ModelConfig]:
        """Get model configuration by key"""
        return self.models.get(key)
    
    def get_routing_config(self) -> Optional[RoutingConfig]:
        """Get routing configuration"""
        return self.routing
    
    def get_claude_config(self) -> Optional[ClaudeConfig]:
        """Get Claude configuration"""
        return self.claude
    
    def get_timeout(self, operation: str, default: int = None) -> int:
        """Get timeout for an operation"""
        return self.timeouts.get(operation, default)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key path.
        
        Args:
            key: Configuration key (e.g., 'models.orchestrator.name')
            default: Default value if not found
        
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_env_var(self, key: str, default: Any = None) -> str:
        """
        Get environment variable value.
        
        Args:
            key: Environment variable name
            default: Default value if not set
        
        Returns:
            Environment variable value or default
        """
        return os.getenv(key, default)
    
    def get_ollama_base_url(self) -> str:
        """Get Ollama base URL (from env or default)"""
        return self.get_env_var("OLLAMA_BASE_URL", self.DEFAULT_VALUES["ollama_base_url"])
    
    def get_data_dir(self) -> Path:
        """Get data directory (from env or default)"""
        data_dir = self.get_env_var("DATA_DIR", self.DEFAULT_VALUES["data_dir"])
        return Path(data_dir).expanduser()
    
    def get_log_level(self) -> str:
        """Get log level (from env or default)"""
        return self.get_env_var("LOG_LEVEL", self.DEFAULT_VALUES["log_level"]).upper()
    
    def get_max_iterations(self) -> int:
        """Get max iterations for iterative validation"""
        return int(self.get_env_var("MAX_ITERATIONS", self.DEFAULT_VALUES["max_iterations"]))
    
    def needs_reload(self) -> bool:
        """
        Check if configuration file has been modified.
        
        Returns:
            True if configuration should be reloaded
        """
        if not self.config_path.exists():
            return False
        
        current_mtime = self.config_path.stat().st_mtime
        return self._config_mtime is None or current_mtime > self._config_mtime
    
    def hot_reload(self) -> bool:
        """
        Reload configuration if file has been modified.
        
        Returns:
            True if configuration was reloaded
        """
        if self.needs_reload():
            try:
                self.reload()
                return True
            except ConfigurationError:
                # Don't reload if validation fails
                return False
        
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            "environment": self.env.value,
            "config_path": str(self.config_path),
            "models": {
                key: {
                    "name": model.name,
                    "temperature": model.temperature,
                    "max_tokens": model.max_tokens
                }
                for key, model in self.models.items()
            },
            "routing": {
                "complexity_threshold": self.routing.complexity_threshold,
                "weights": self.routing.weights
            } if self.routing else None,
            "claude": {
                "model": self.claude.model,
                "max_tokens": self.claude.max_tokens
            } if self.claude else None,
            "timeouts": self.timeouts,
            "env_vars": {
                "OLLAMA_BASE_URL": self.get_ollama_base_url(),
                "DATA_DIR": str(self.get_data_dir()),
                "LOG_LEVEL": self.get_log_level(),
                "MAX_ITERATIONS": self.get_max_iterations(),
            }
        }


# Create singleton instance
CONFIG_MANAGER = ConfigManager()

