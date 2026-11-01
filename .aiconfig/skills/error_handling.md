# Error Handling Patterns

Master these error handling patterns to write robust, production-quality code.

## Pattern 1: Input Validation with Clear Error Messages

Always validate inputs and provide helpful error messages:

```python
def calculate_age(birth_year: int) -> int:
    """
    Calculate age from birth year.
    
    Args:
        birth_year: Year of birth (must be valid year)
    
    Returns:
        Age in years
    
    Raises:
        TypeError: If birth_year is not an integer
        ValueError: If birth_year is not a valid year
    """
    if not isinstance(birth_year, int):
        raise TypeError(f"birth_year must be an integer, got {type(birth_year).__name__}")
    
    current_year = 2024
    if birth_year < 1900 or birth_year > current_year:
        raise ValueError(f"birth_year must be between 1900 and {current_year}, got {birth_year}")
    
    return current_year - birth_year
```

**Key Points:**
- Check types explicitly with `isinstance()`
- Provide clear error messages with actual values
- Use appropriate exception types (TypeError, ValueError)
- Include valid ranges/constraints in error messages

## Pattern 2: Graceful Degradation

Handle errors gracefully with default values when appropriate:

```python
def safe_divide(a: float, b: float, default: float = 0.0) -> float:
    """
    Divide two numbers safely.
    
    Args:
        a: Numerator
        b: Denominator
        default: Value to return if division fails
    
    Returns:
        Result of division or default value
    """
    try:
        return a / b
    except ZeroDivisionError:
        return default
    except TypeError:
        return default
```

**Use When:**
- Operation can fail but shouldn't crash the program
- Default behavior is acceptable
- Errors are expected in normal operation

## Pattern 3: Specific Exception Handling

Catch and handle specific exceptions, not bare `except`:

```python
def read_config_file(filepath: str) -> dict:
    """
    Read configuration from JSON file.
    
    Args:
        filepath: Path to config file
    
    Returns:
        Configuration dictionary
    
    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file has invalid JSON
    """
    import json
    
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Config file not found: {filepath}")
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON in {filepath}: {e.msg}", e.doc, e.pos)
```

**Key Points:**
- Catch specific exceptions, not generic `Exception`
- Re-raise with context or handle appropriately
- Don't use bare `except:` - always specify exception types

## Pattern 4: Try-Except-Finally for Resource Cleanup

Always use finally for cleanup operations:

```python
def process_file(filepath: str) -> str:
    """
    Process file and ensure cleanup.
    
    Args:
        filepath: Path to file
    
    Returns:
        Processed content
    """
    file_handle = None
    try:
        file_handle = open(filepath, 'r')
        content = file_handle.read()
        # Process content...
        return content.upper()
    except IOError as e:
        raise IOError(f"Error reading file {filepath}: {e}")
    finally:
        if file_handle:
            file_handle.close()
```

**Better:** Use context managers (see Pattern 5)

## Pattern 5: Context Managers for Resources

Use `with` statements for automatic resource management:

```python
def process_file_safe(filepath: str) -> str:
    """
    Process file using context manager (automatic cleanup).
    
    Args:
        filepath: Path to file
    
    Returns:
        Processed content
    """
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            return content.upper()
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {filepath}")
    except IOError as e:
        raise IOError(f"Error reading {filepath}: {e}")
```

**Benefits:**
- Automatic cleanup
- More readable
- Handles exceptions properly
- Prevents resource leaks

## Pattern 6: Custom Exceptions

Create custom exceptions for domain-specific errors:

```python
class InvalidInputError(ValueError):
    """Raised when input validation fails."""
    pass

class ProcessingError(Exception):
    """Raised when processing fails."""
    pass

def validate_email(email: str) -> str:
    """
    Validate email address.
    
    Args:
        email: Email address to validate
    
    Returns:
        Validated email address
    
    Raises:
        InvalidInputError: If email format is invalid
    """
    import re
    
    if not isinstance(email, str):
        raise InvalidInputError(f"Email must be a string, got {type(email).__name__}")
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise InvalidInputError(f"Invalid email format: {email}")
    
    return email.lower()
```

**Key Points:**
- Inherit from appropriate base exception (ValueError, TypeError, Exception)
- Use descriptive names ending in "Error"
- Provide clear error messages

## Pattern 7: Chained Exceptions

Preserve original exception context:

```python
def fetch_user_data(user_id: int) -> dict:
    """
    Fetch user data from API.
    
    Args:
        user_id: User ID
    
    Returns:
        User data dictionary
    
    Raises:
        ConnectionError: If API connection fails
        ValueError: If user_id is invalid
    """
    if not isinstance(user_id, int) or user_id < 1:
        raise ValueError(f"Invalid user_id: {user_id}")
    
    try:
        # API call...
        response = requests.get(f"/api/users/{user_id}")
        return response.json()
    except requests.RequestException as e:
        raise ConnectionError(f"Failed to fetch user {user_id}") from e
```

**Benefits:**
- Preserves original error context
- Helps with debugging
- Shows full error chain

## Pattern 8: Validation Before Processing

Validate all inputs before any processing:

```python
def calculate_discount(price: float, discount_percent: float) -> float:
    """
    Calculate discounted price.
    
    Args:
        price: Original price (must be positive)
        discount_percent: Discount percentage (0-100)
    
    Returns:
        Discounted price
    
    Raises:
        TypeError: If inputs are not numbers
        ValueError: If inputs are out of valid range
    """
    # Validate types first
    if not isinstance(price, (int, float)):
        raise TypeError(f"price must be a number, got {type(price).__name__}")
    if not isinstance(discount_percent, (int, float)):
        raise TypeError(f"discount_percent must be a number, got {type(discount_percent).__name__}")
    
    # Validate ranges
    if price < 0:
        raise ValueError(f"price must be non-negative, got {price}")
    if not 0 <= discount_percent <= 100:
        raise ValueError(f"discount_percent must be between 0 and 100, got {discount_percent}")
    
    # Now safe to process
    return price * (1 - discount_percent / 100)
```

## Pattern 9: Logging Errors

Log errors for debugging while still raising exceptions:

```python
import logging

logger = logging.getLogger(__name__)

def process_data(data: list) -> dict:
    """
    Process data with error logging.
    
    Args:
        data: List of data items
    
    Returns:
        Processed data dictionary
    
    Raises:
        ValueError: If data is invalid
    """
    try:
        if not isinstance(data, list):
            raise TypeError("data must be a list")
        
        if len(data) == 0:
            raise ValueError("data cannot be empty")
        
        # Process data...
        return {"processed": len(data)}
        
    except (TypeError, ValueError) as e:
        logger.error(f"Data processing failed: {e}", exc_info=True)
        raise
```

**Key Points:**
- Log errors with context
- Use `exc_info=True` to include stack trace
- Still raise exceptions for callers to handle
- Use appropriate log levels (ERROR, WARNING, INFO)

## Pattern 10: Retry with Exponential Backoff

For transient errors, implement retry logic:

```python
import time
from typing import Callable, Any

def retry_with_backoff(
    func: Callable,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    exceptions: tuple = (Exception,)
) -> Any:
    """
    Retry function with exponential backoff.
    
    Args:
        func: Function to retry
        max_attempts: Maximum number of attempts
        base_delay: Base delay in seconds
        exceptions: Exception types to retry on
    
    Returns:
        Function result
    
    Raises:
        Last exception if all attempts fail
    """
    for attempt in range(max_attempts):
        try:
            return func()
        except exceptions as e:
            if attempt == max_attempts - 1:
                raise  # Last attempt failed, re-raise
            
            delay = base_delay * (2 ** attempt)
            time.sleep(delay)
    
    return None
```

## Best Practices Summary

1. **Always validate inputs** - Check types and ranges before processing
2. **Use specific exceptions** - Catch specific types, not generic Exception
3. **Provide clear error messages** - Include actual values and valid ranges
4. **Use context managers** - Prefer `with` statements for resources
5. **Create custom exceptions** - For domain-specific error conditions
6. **Preserve exception context** - Use `from` to chain exceptions
7. **Log before raising** - Help with debugging while maintaining error flow
8. **Fail fast** - Validate early, before expensive operations
9. **Never ignore errors** - At minimum, log them
10. **Document exceptions** - List all exceptions in docstrings

## Common Anti-Patterns to Avoid

❌ **Bare except clauses:**
```python
try:
    do_something()
except:  # Too broad!
    pass
```

✅ **Specific exceptions:**
```python
try:
    do_something()
except (ValueError, TypeError) as e:
    handle_error(e)
```

❌ **Silently ignoring errors:**
```python
try:
    process_data()
except:
    pass  # Silent failure!
```

✅ **Log or raise:**
```python
try:
    process_data()
except Exception as e:
    logger.error(f"Processing failed: {e}")
    raise
```

