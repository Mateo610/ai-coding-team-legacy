"""
Secrets management system for the AI software team.
Ensures all secrets are loaded from environment variables, never hardcoded.
"""

import os
from pathlib import Path
from typing import Dict, Optional, List, Any
from dataclasses import dataclass
from dotenv import load_dotenv
from agents.exceptions import ConfigurationError


@dataclass
class Secret:
    """Secret configuration"""
    name: str
    required: bool
    description: str
    default: Optional[str] = None
    sensitive: bool = True  # Whether to redact in logs


class SecretsManager:
    """
    Secrets management system.
    Validates that all required secrets are available from environment variables.
    """
    
    DEFAULT_ENV_FILE = "config/.env"
    
    # Define all secrets used by the system
    SECRETS = [
        Secret(
            name="ANTHROPIC_API_KEY",
            required=False,  # Optional if only using local models
            description="Anthropic Claude API key",
            sensitive=True
        ),
        Secret(
            name="OLLAMA_BASE_URL",
            required=False,  # Has default
            description="Ollama service base URL",
            default="http://localhost:11434",
            sensitive=False
        ),
        Secret(
            name="DATA_DIR",
            required=False,  # Has default
            description="Data directory for logs and interactions",
            default="~/ai-coding-team/data",
            sensitive=False
        ),
        Secret(
            name="LOG_DIR",
            required=False,  # Has default
            description="Log directory for application logs",
            default="~/ai-coding-team/logs",
            sensitive=False
        ),
        Secret(
            name="LOG_LEVEL",
            required=False,  # Has default
            description="Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
            default="INFO",
            sensitive=False
        ),
        Secret(
            name="MAX_ITERATIONS",
            required=False,  # Has default
            description="Maximum iterations for iterative validation",
            default="3",
            sensitive=False
        ),
        Secret(
            name="AI_TEAM_ENV",
            required=False,  # Has default
            description="Environment (development, production, testing)",
            default="development",
            sensitive=False
        ),
    ]
    
    def __init__(self, env_file: str = None):
        """
        Initialize secrets manager.
        
        Args:
            env_file: Path to .env file (default: config/.env)
        """
        self.env_file = Path(env_file or self.DEFAULT_ENV_FILE)
        
        # Load environment variables from .env file if it exists
        if self.env_file.exists():
            load_dotenv(self.env_file)
        elif env_file:  # Only warn if explicitly provided
            print(f"⚠️  Warning: .env file not found at {self.env_file}")
            print(f"   Using environment variables only")
    
    def get(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get secret value from environment.
        
        Args:
            name: Secret name
            default: Default value if not found
        
        Returns:
            Secret value or default
        """
        # Find secret definition
        secret = next((s for s in self.SECRETS if s.name == name), None)
        
        # Get value from environment
        value = os.getenv(name, default)
        
        # Use secret default if no value found and secret has default
        if value is None and secret and secret.default is not None:
            value = secret.default
        
        return value
    
    def get_required(self, name: str) -> str:
        """
        Get required secret value, raising error if not found.
        
        Args:
            name: Secret name
        
        Returns:
            Secret value
        
        Raises:
            ConfigurationError: If secret is not found
        """
        secret = next((s for s in self.SECRETS if s.name == name), None)
        
        if not secret:
            raise ConfigurationError(
                f"Unknown secret: {name}",
                details={"secret_name": name}
            )
        
        value = self.get(name)
        
        if value is None:
            if secret.required:
                raise ConfigurationError(
                    f"Required secret not found: {name}",
                    details={
                        "secret_name": name,
                        "description": secret.description,
                        "hint": f"Set {name} in environment or {self.env_file}"
                    }
                )
            else:
                # Use default if available
                if secret.default is not None:
                    value = secret.default
                else:
                    raise ConfigurationError(
                        f"Secret not found and no default: {name}",
                        details={
                            "secret_name": name,
                            "description": secret.description
                        }
                    )
        
        return value
    
    def validate(self) -> Dict[str, List[str]]:
        """
        Validate that all required secrets are available.
        
        Returns:
            Dictionary with 'missing' and 'warnings' lists
        """
        missing = []
        warnings = []
        
        for secret in self.SECRETS:
            value = self.get(secret.name)
            
            if secret.required and value is None:
                missing.append(secret.name)
            elif value is None and secret.default is None:
                # Non-required but no default - warn
                warnings.append(secret.name)
        
        return {
            "missing": missing,
            "warnings": warnings
        }
    
    def check_all(self) -> bool:
        """
        Check if all required secrets are available.
        
        Returns:
            True if all required secrets are available
        """
        validation = self.validate()
        return len(validation["missing"]) == 0
    
    def get_all(self, include_defaults: bool = True) -> Dict[str, Optional[str]]:
        """
        Get all secrets.
        
        Args:
            include_defaults: Whether to include secrets with defaults
        
        Returns:
            Dictionary of all secrets
        """
        secrets = {}
        
        for secret in self.SECRETS:
            value = self.get(secret.name)
            
            if value is not None or (include_defaults and secret.default is not None):
                # Redact sensitive values
                if secret.sensitive and value:
                    secrets[secret.name] = self._redact(value)
                else:
                    secrets[secret.name] = value
        
        return secrets
    
    def _redact(self, value: str) -> str:
        """
        Redact sensitive value for logging.
        
        Args:
            value: Secret value
        
        Returns:
            Redacted value
        """
        if not value or len(value) < 8:
            return "***"
        
        # Show first 4 and last 4 characters
        return f"{value[:4]}...{value[-4:]}"
    
    def verify_no_hardcoded_secrets(self, directory: str = ".") -> List[str]:
        """
        Verify no hardcoded secrets in codebase.
        
        Args:
            directory: Directory to check
        
        Returns:
            List of potential hardcoded secrets found
        """
        suspicious_patterns = [
            r"api_key\s*=\s*['\"][^'\"]+['\"]",
            r"secret\s*=\s*['\"][^'\"]+['\"]",
            r"password\s*=\s*['\"][^'\"]+['\"]",
            r"token\s*=\s*['\"][^'\"]+['\"]",
            r"ANTHROPIC_API_KEY\s*=\s*['\"][^'\"]+['\"]",
        ]
        
        # This is a basic check - in production, use a proper secrets scanner
        findings = []
        
        # For now, just return empty list - this is a placeholder
        # In production, would scan files for suspicious patterns
        
        return findings
    
    def to_dict(self, redact_sensitive: bool = True) -> Dict[str, Any]:
        """
        Convert secrets to dictionary for logging/config display.
        
        Args:
            redact_sensitive: Whether to redact sensitive values
        
        Returns:
            Dictionary of secrets
        """
        result = {}
        
        for secret in self.SECRETS:
            value = self.get(secret.name)
            
            if redact_sensitive and secret.sensitive and value:
                result[secret.name] = self._redact(value)
            else:
                result[secret.name] = value
        
        return result


# Create singleton instance
SECRETS_MANAGER = SecretsManager()

