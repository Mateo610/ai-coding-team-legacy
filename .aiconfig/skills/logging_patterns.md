# Logging Patterns

Comprehensive patterns for structured logging in Python.

## Logging Principles

### 1. Use Structured Logging

**Use the logging module, not print():**

```python
import logging
from typing import Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Create logger
logger = logging.getLogger(__name__)

def process_data(data: list) -> dict:
    """Process data with logging."""
    logger.info(f"Processing {len(data)} items")
    
    try:
        result = _process_internal(data)
        logger.info(f"Successfully processed {len(result)} items")
        return result
    except Exception as e:
        logger.error(f"Failed to process data: {e}", exc_info=True)
        raise
```

**Benefits:**
- Configurable log levels
- Structured format
- Can write to files
- Supports multiple handlers
- Thread-safe

### 2. Log Levels

**Use appropriate log levels:**

```python
import logging

logger = logging.getLogger(__name__)

# DEBUG: Detailed information for debugging
logger.debug("Processing item: %s", item_id)

# INFO: General information about program execution
logger.info("Processing started with %d items", item_count)

# WARNING: Warning about unexpected conditions
logger.warning("Deprecated function used: %s", function_name)

# ERROR: Error that doesn't stop program
logger.error("Failed to process item %s: %s", item_id, error_message)

# CRITICAL: Serious error that may stop program
logger.critical("Database connection failed: %s", error_message)
```

**Log Level Guidelines:**
- DEBUG: Detailed debugging information
- INFO: General informational messages
- WARNING: Warning messages (non-critical issues)
- ERROR: Error messages (function failures)
- CRITICAL: Critical errors (may stop program)

### 3. Structured Logging with Context

**Include context in log messages:**

```python
import logging
from typing import Any

logger = logging.getLogger(__name__)

def process_user(user_id: int, action: str) -> None:
    """Process user action with contextual logging."""
    # Include context in log message
    logger.info(
        "Processing user action",
        extra={
            'user_id': user_id,
            'action': action,
            'timestamp': time.time()
        }
    )
    
    try:
        _process_action(user_id, action)
        logger.info(
            "Action completed successfully",
            extra={'user_id': user_id, 'action': action}
        )
    except Exception as e:
        logger.error(
            "Action failed",
            extra={'user_id': user_id, 'action': action, 'error': str(e)},
            exc_info=True
        )
```

## Logging Configuration

### 4. Logging Configuration

**Configure logging properly:**

```python
import logging
import sys
from pathlib import Path

def setup_logging(log_level: str = "INFO", log_file: Path = None) -> None:
    """Configure logging with file and console handlers."""
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Prevent duplicate logs
    logger.propagate = False

# Usage
setup_logging(log_level="DEBUG", log_file=Path("app.log"))
```

### 5. Module-Level Loggers

**Create logger for each module:**

```python
import logging

# At module level
logger = logging.getLogger(__name__)

def process_data(data: list) -> dict:
    """Process data with module logger."""
    logger.info("Processing data")
    # Use logger throughout module
    logger.debug(f"Data size: {len(data)}")
    return processed_data

class DataProcessor:
    """Data processor with logging."""
    
    def __init__(self):
        # Use module logger
        self.logger = logging.getLogger(__name__)
    
    def process(self, data: list) -> dict:
        """Process data with instance logger."""
        self.logger.info("Processing with DataProcessor")
        return processed_data
```

**Logger Best Practices:**
- Create logger at module level
- Use `__name__` for logger name
- Use module logger throughout module
- Create instance logger if needed for classes

## Error Logging

### 6. Log Exceptions Properly

**Log exceptions with context:**

```python
import logging

logger = logging.getLogger(__name__)

def process_file(filepath: Path) -> str:
    """Process file with exception logging."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        return process_content(content)
    except FileNotFoundError:
        logger.warning(f"File not found: {filepath}")
        raise
    except PermissionError:
        logger.error(f"Permission denied: {filepath}", exc_info=True)
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error processing {filepath}: {e}",
            exc_info=True,  # Include stack trace
            extra={'filepath': str(filepath), 'error_type': type(e).__name__}
        )
        raise
```

**Exception Logging Guidelines:**
- Use `exc_info=True` to include stack trace
- Include context (filepath, user_id, etc.)
- Log before raising (preserve exception)
- Use appropriate log level

### 7. Sensitive Data Handling

**Never log sensitive information:**

```python
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

SENSITIVE_FIELDS = {'password', 'token', 'api_key', 'secret', 'ssn', 'credit_card'}

def sanitize_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Remove sensitive fields from data for logging."""
    sanitized = {}
    for key, value in data.items():
        if key.lower() in SENSITIVE_FIELDS:
            sanitized[key] = '***REDACTED***'
        elif isinstance(value, dict):
            sanitized[key] = sanitize_data(value)
        else:
            sanitized[key] = value
    return sanitized

def log_user_data(user_data: Dict[str, Any]) -> None:
    """Log user data with sensitive fields redacted."""
    sanitized = sanitize_data(user_data)
    logger.info(f"Processing user: {sanitized}")

# Usage
user_data = {
    'name': 'Alice',
    'email': 'alice@example.com',
    'password': 'secret123',  # Will be redacted
    'token': 'abc123'  # Will be redacted
}
log_user_data(user_data)  # Password and token redacted in logs
```

## Performance Logging

### 8. Log Performance Metrics

**Log performance information:**

```python
import logging
import time
from functools import wraps
from typing import Callable

logger = logging.getLogger(__name__)

def log_performance(func: Callable) -> Callable:
    """Decorator to log function performance."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start
            logger.info(
                f"{func.__name__} completed in {duration:.4f}s",
                extra={
                    'function': func.__name__,
                    'duration_ms': duration * 1000,
                    'success': True
                }
            )
            return result
        except Exception as e:
            duration = time.time() - start
            logger.error(
                f"{func.__name__} failed after {duration:.4f}s: {e}",
                extra={
                    'function': func.__name__,
                    'duration_ms': duration * 1000,
                    'success': False,
                    'error': str(e)
                },
                exc_info=True
            )
            raise
    return wrapper

@log_performance
def process_large_dataset(data: list) -> list:
    """Process large dataset (performance logged)."""
    return [item * 2 for item in data]
```

## Logging Best Practices

### 9. Logging Guidelines

**Follow these logging best practices:**

```python
import logging

logger = logging.getLogger(__name__)

# Good: Structured messages
logger.info("User logged in", extra={'user_id': user_id, 'ip': ip_address})

# Bad: Unstructured messages
logger.info(f"User {user_id} logged in from {ip_address}")

# Good: Use % formatting for lazy evaluation
logger.debug("Processing item: %s", item_id)

# Bad: f-strings evaluated even if level is higher
logger.debug(f"Processing item: {item_id}")

# Good: Include context
logger.info(
    "Processing order",
    extra={
        'order_id': order_id,
        'customer_id': customer_id,
        'total': total
    }
)

# Good: Appropriate log level
logger.error("Database query failed", exc_info=True)  # ERROR level
logger.warning("Using deprecated API")  # WARNING level
logger.info("Processing started")  # INFO level
logger.debug("Variable value: %s", value)  # DEBUG level
```

**Best Practices:**
- Use structured logging (extra dict)
- Use % formatting for lazy evaluation
- Include context in log messages
- Use appropriate log levels
- Never log sensitive data
- Log exceptions with `exc_info=True`
- Use module-level loggers

## Best Practices Summary

1. **Use logging module** - Not print()
2. **Use appropriate log levels** - DEBUG, INFO, WARNING, ERROR, CRITICAL
3. **Include context** - User ID, request ID, etc.
4. **Log exceptions properly** - Use `exc_info=True`
5. **Never log sensitive data** - Passwords, tokens, secrets
6. **Use structured logging** - Extra dictionary for context
7. **Configure properly** - Set up handlers and formatters
8. **Use module loggers** - `logger = logging.getLogger(__name__)`
9. **Log performance** - Include timing information
10. **Use % formatting** - For lazy evaluation

