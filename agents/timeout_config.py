"""
Timeout configuration and management for the AI software team.
"""

import os
import yaml
from typing import Dict, Optional
from pathlib import Path


class TimeoutConfig:
    """Centralized timeout configuration management"""
    
    DEFAULT_TIMEOUTS = {
        "model_request": 180,  # Model API request timeout (seconds)
        "model_streaming": 300,  # Max time for streaming response collection
        "tool_execution": 30,  # Tool execution timeout
        "code_execution": 10,  # Code execution timeout
        "test_execution": 60,  # Test execution timeout
        "health_check": 5,  # Health check timeout
        "file_operations": 10,  # File operations timeout
    }
    
    def __init__(self, config_path: str = "config/models.yaml"):
        """
        Initialize timeout configuration.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.timeouts = self._load_timeouts()
    
    def _load_timeouts(self) -> Dict[str, int]:
        """
        Load timeout configuration from config file.
        
        Returns:
            Dictionary of timeout values
        """
        timeouts = self.DEFAULT_TIMEOUTS.copy()
        
        try:
            config_file = Path(self.config_path)
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config = yaml.safe_load(f)
                
                if config and 'timeouts' in config:
                    # Override defaults with config values
                    for key, value in config['timeouts'].items():
                        if isinstance(value, (int, float)) and value > 0:
                            timeouts[key] = int(value)
        except Exception as e:
            # Use defaults if config can't be loaded
            print(f"⚠️  Warning: Could not load timeout config: {e}")
            print(f"   Using default timeouts")
        
        return timeouts
    
    def get_timeout(self, operation: str, default: Optional[int] = None) -> int:
        """
        Get timeout value for an operation.
        
        Args:
            operation: Operation name (e.g., 'model_request', 'tool_execution')
            default: Default timeout if not found
        
        Returns:
            Timeout value in seconds
        """
        timeout = self.timeouts.get(operation, default)
        
        if timeout is None:
            # Use appropriate default based on operation type
            if 'model' in operation.lower():
                timeout = self.DEFAULT_TIMEOUTS['model_request']
            elif 'tool' in operation.lower():
                timeout = self.DEFAULT_TIMEOUTS['tool_execution']
            elif 'test' in operation.lower():
                timeout = self.DEFAULT_TIMEOUTS['test_execution']
            elif 'execution' in operation.lower() or 'code' in operation.lower():
                timeout = self.DEFAULT_TIMEOUTS['code_execution']
            elif 'health' in operation.lower():
                timeout = self.DEFAULT_TIMEOUTS['health_check']
            else:
                timeout = 30  # Generic default
        
        return timeout
    
    def get_model_request_timeout(self) -> int:
        """Get timeout for model API requests"""
        return self.get_timeout("model_request")
    
    def get_model_streaming_timeout(self) -> int:
        """Get timeout for streaming response collection"""
        return self.get_timeout("model_streaming")
    
    def get_tool_execution_timeout(self) -> int:
        """Get timeout for tool execution"""
        return self.get_timeout("tool_execution")
    
    def get_code_execution_timeout(self) -> int:
        """Get timeout for code execution"""
        return self.get_timeout("code_execution")
    
    def get_test_execution_timeout(self) -> int:
        """Get timeout for test execution"""
        return self.get_timeout("test_execution")
    
    def get_health_check_timeout(self) -> int:
        """Get timeout for health checks"""
        return self.get_timeout("health_check")
    
    def get_file_operations_timeout(self) -> int:
        """Get timeout for file operations"""
        return self.get_timeout("file_operations")
    
    def update_timeout(self, operation: str, timeout: int) -> None:
        """
        Update timeout for an operation.
        
        Args:
            operation: Operation name
            timeout: Timeout value in seconds
        """
        if timeout > 0:
            self.timeouts[operation] = timeout
        else:
            raise ValueError(f"Timeout must be positive, got {timeout}")
    
    def get_all_timeouts(self) -> Dict[str, int]:
        """Get all timeout configurations"""
        return self.timeouts.copy()


# Create singleton instance
TIMEOUT_CONFIG = TimeoutConfig()

