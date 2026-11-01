"""
Custom exception classes for the AI software team system.
"""


class AITeamError(Exception):
    """Base exception for AI software team errors."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self):
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


class AgentError(AITeamError):
    """Raised when an agent fails to execute."""
    pass


class ModelConnectionError(AgentError):
    """Raised when connection to model fails."""
    pass


class ModelTimeoutError(AgentError):
    """Raised when model request times out."""
    pass


class ValidationError(AITeamError):
    """Raised when validation fails."""
    pass


class ConfigurationError(AITeamError):
    """Raised when configuration is invalid."""
    pass


class ToolExecutionError(AITeamError):
    """Raised when tool execution fails."""
    pass


class ProjectStructureError(AITeamError):
    """Raised when project structure generation fails."""
    pass


class RetryableError(AITeamError):
    """Raised for errors that can be retried."""
    pass


class NonRetryableError(AITeamError):
    """Raised for errors that should not be retried."""
    pass

