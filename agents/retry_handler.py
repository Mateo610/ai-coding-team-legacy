"""
Retry handler for transient failures with exponential backoff.
"""

import time
from typing import Callable, Any, Optional, Type, Tuple
from functools import wraps
from agents.exceptions import RetryableError, NonRetryableError, ModelConnectionError, ModelTimeoutError


def retry_on_failure(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
    retryable_exceptions: Tuple[Type[Exception], ...] = (ModelConnectionError, ModelTimeoutError, RetryableError),
    non_retryable_exceptions: Tuple[Type[Exception], ...] = (NonRetryableError,),
):
    """
    Decorator to retry functions on transient failures.
    
    Args:
        max_attempts: Maximum number of retry attempts (default: 3)
        base_delay: Base delay in seconds (default: 1.0)
        max_delay: Maximum delay in seconds (default: 10.0)
        retryable_exceptions: Exception types that should trigger retry
        non_retryable_exceptions: Exception types that should not be retried
    
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except non_retryable_exceptions as e:
                    # Don't retry these exceptions
                    raise
                except retryable_exceptions as e:
                    # Retry these exceptions
                    last_exception = e
                    
                    if attempt < max_attempts:
                        # Calculate delay with exponential backoff
                        delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
                        
                        print(f"   ⚠️  Attempt {attempt}/{max_attempts} failed: {str(e)[:100]}")
                        print(f"   🔄 Retrying in {delay:.1f}s...")
                        
                        time.sleep(delay)
                    else:
                        # Last attempt failed
                        print(f"   ❌ All {max_attempts} attempts failed")
                        raise
                except Exception as e:
                    # Check if it's a retryable error based on error message
                    error_str = str(e).lower()
                    if any(keyword in error_str for keyword in ['timeout', 'connection', 'network', 'temporary']):
                        # Treat as retryable
                        last_exception = e
                        
                        if attempt < max_attempts:
                            delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
                            print(f"   ⚠️  Attempt {attempt}/{max_attempts} failed: {str(e)[:100]}")
                            print(f"   🔄 Retrying in {delay:.1f}s...")
                            time.sleep(delay)
                        else:
                            print(f"   ❌ All {max_attempts} attempts failed")
                            raise
                    else:
                        # Non-retryable error
                        raise
            
            # Should never reach here, but just in case
            if last_exception:
                raise last_exception
            
        return wrapper
    return decorator


class RetryHandler:
    """Handler for retrying operations with exponential backoff."""
    
    @staticmethod
    def execute_with_retry(
        func: Callable,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 10.0,
        retryable_exceptions: Tuple[Type[Exception], ...] = (ModelConnectionError, ModelTimeoutError, RetryableError),
        *args,
        **kwargs
    ) -> Any:
        """
        Execute function with retry logic.
        
        Args:
            func: Function to execute
            max_attempts: Maximum number of attempts
            base_delay: Base delay in seconds
            max_delay: Maximum delay in seconds
            retryable_exceptions: Exception types to retry
            *args, **kwargs: Arguments to pass to function
        
        Returns:
            Function result
        
        Raises:
            Last exception if all attempts fail
        """
        last_exception = None
        
        for attempt in range(1, max_attempts + 1):
            try:
                return func(*args, **kwargs)
            except retryable_exceptions as e:
                last_exception = e
                
                if attempt < max_attempts:
                    delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
                    print(f"   ⚠️  Attempt {attempt}/{max_attempts} failed: {str(e)[:100]}")
                    print(f"   🔄 Retrying in {delay:.1f}s...")
                    time.sleep(delay)
                else:
                    print(f"   ❌ All {max_attempts} attempts failed")
                    raise
            except NonRetryableError:
                # Don't retry non-retryable errors
                raise
            except Exception as e:
                # Check if error message suggests retryability
                error_str = str(e).lower()
                if any(keyword in error_str for keyword in ['timeout', 'connection', 'network', 'temporary']):
                    last_exception = e
                    if attempt < max_attempts:
                        delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
                        print(f"   ⚠️  Attempt {attempt}/{max_attempts} failed: {str(e)[:100]}")
                        print(f"   🔄 Retrying in {delay:.1f}s...")
                        time.sleep(delay)
                    else:
                        raise
                else:
                    # Non-retryable, raise immediately
                    raise
        
        # Should never reach here
        if last_exception:
            raise last_exception

