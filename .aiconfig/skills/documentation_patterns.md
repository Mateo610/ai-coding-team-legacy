# Documentation Patterns

Comprehensive documentation patterns for Python code.

## Documentation Principles

### 1. Docstring Standards

**Always write docstrings for all public functions, classes, and modules:**

```python
def calculate_total(items: list, discount: float = 0.0) -> float:
    """
    Calculate total price with optional discount.
    
    Args:
        items: List of item prices (must be positive numbers)
        discount: Discount percentage (0.0 to 1.0, default: 0.0)
    
    Returns:
        Total price after discount is applied
    
    Raises:
        ValueError: If items list is empty or discount is out of range
        TypeError: If items contains non-numeric values
    
    Example:
        >>> calculate_total([10.0, 20.0, 30.0], discount=0.1)
        54.0
    """
    if not items:
        raise ValueError("Items list cannot be empty")
    if not 0.0 <= discount <= 1.0:
        raise ValueError(f"Discount must be between 0.0 and 1.0, got {discount}")
    
    subtotal = sum(items)
    return subtotal * (1 - discount)
```

**Key Components:**
- Brief one-line summary
- Detailed description (if needed)
- Args: Parameters with types and descriptions
- Returns: Return value type and description
- Raises: All exceptions that may be raised
- Example: Usage example (optional)

## Docstring Formats

### 2. Google Style Docstrings

**Use Google-style docstrings (most readable):**

```python
def process_data(data: list, validate: bool = True) -> dict:
    """
    Process list of data items and return summary.
    
    This function processes a list of data items, optionally validates them,
    and returns a dictionary containing summary statistics.
    
    Args:
        data: List of data items to process (must not be empty)
        validate: Whether to validate data before processing (default: True)
    
    Returns:
        Dictionary containing:
            - count: Number of items processed
            - total: Sum of all item values
            - average: Average value
            - min: Minimum value
            - max: Maximum value
    
    Raises:
        ValueError: If data list is empty or contains invalid values
        TypeError: If data is not a list
    
    Example:
        >>> data = [1, 2, 3, 4, 5]
        >>> result = process_data(data)
        >>> result['count']
        5
        >>> result['average']
        3.0
    """
    if not isinstance(data, list):
        raise TypeError(f"Expected list, got {type(data).__name__}")
    if not data:
        raise ValueError("Data list cannot be empty")
    
    if validate:
        for item in data:
            if not isinstance(item, (int, float)):
                raise ValueError(f"Invalid data item: {item}")
    
    return {
        'count': len(data),
        'total': sum(data),
        'average': sum(data) / len(data),
        'min': min(data),
        'max': max(data),
    }
```

### 3. NumPy Style Docstrings

**Alternative: NumPy-style docstrings (more structured):**

```python
def analyze_data(data: list) -> dict:
    """
    Analyze data and return statistics.
    
    Parameters
    ----------
    data : list of float
        List of numeric values to analyze (must not be empty).
    validate : bool, optional
        Whether to validate data before processing (default: True).
    
    Returns
    -------
    dict
        Dictionary containing statistical information:
        - count (int): Number of items
        - total (float): Sum of values
        - average (float): Mean value
    
    Raises
    ------
    ValueError
        If data list is empty or contains invalid values.
    TypeError
        If data is not a list.
    
    Examples
    --------
    >>> analyze_data([1, 2, 3, 4, 5])
    {'count': 5, 'total': 15.0, 'average': 3.0}
    """
    ...
```

## Class Documentation

### 4. Class Docstrings

**Document classes with their purpose and usage:**

```python
class User:
    """
    Represents a user in the system.
    
    This class encapsulates user information and provides methods
    for user management and validation.
    
    Attributes:
        name: User's full name
        email: User's email address (must be valid format)
        age: User's age in years (must be positive)
        is_active: Whether the user account is active
    
    Example:
        >>> user = User("Alice", "alice@example.com", 25)
        >>> user.is_active
        True
        >>> user.get_display_name()
        'Alice (25)'
    """
    
    def __init__(self, name: str, email: str, age: int):
        """
        Initialize a new User instance.
        
        Args:
            name: User's full name (must not be empty)
            email: User's email address (must be valid format)
            age: User's age in years (must be positive)
        
        Raises:
            ValueError: If name is empty, email is invalid, or age is negative
        """
        if not name:
            raise ValueError("Name cannot be empty")
        if not self._validate_email(email):
            raise ValueError(f"Invalid email format: {email}")
        if age < 0:
            raise ValueError(f"Age must be non-negative, got {age}")
        
        self.name = name
        self.email = email
        self.age = age
        self.is_active = True
    
    def _validate_email(self, email: str) -> bool:
        """Validate email format (private method - no docstring required but helpful)."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def get_display_name(self) -> str:
        """
        Get formatted display name.
        
        Returns:
            Formatted string with name and age
        """
        return f"{self.name} ({self.age})"
```

## Module Documentation

### 5. Module Docstrings

**Document modules at the top of the file:**

```python
"""
Data processing utilities.

This module provides utilities for processing and analyzing data,
including validation, transformation, and statistical analysis.

Classes:
    DataProcessor: Main class for processing data
    DataValidator: Class for validating data formats

Functions:
    validate_data: Validate data format
    process_data: Process and transform data
    analyze_data: Perform statistical analysis

Example:
    >>> from data_utils import DataProcessor
    >>> processor = DataProcessor()
    >>> result = processor.process([1, 2, 3, 4, 5])
    >>> print(result)
    {'count': 5, 'total': 15}

Author: Your Name
Date: 2024-01-01
"""

from typing import List, Dict, Any

# Module code here...
```

## Comment Guidelines

### 6. When to Use Comments

**Use comments sparingly - code should be self-documenting:**

```python
# Good: Comment explains WHY, not WHAT
# Using binary search because the list is sorted and very large
index = binary_search(sorted_list, target)

# Bad: Comment restates what code does
# Increment count by 1
count += 1

# Good: Comment explains complex algorithm
# Apply Kadane's algorithm to find maximum subarray sum
max_sum = max_ending_here = 0
for num in array:
    max_ending_here = max(num, max_ending_here + num)
    max_sum = max(max_sum, max_ending_here)

# Good: Comment explains non-obvious behavior
# Note: This function modifies the list in-place for performance
def sort_list_in_place(items: list) -> None:
    items.sort()
```

**Comment Guidelines:**
- Explain WHY, not WHAT
- Document complex algorithms
- Explain non-obvious behavior
- Note workarounds or temporary fixes
- Don't state the obvious

### 7. Inline Comments

**Use inline comments for clarification:**

```python
def process_file(filepath: str) -> str:
    """Process file with error handling."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Remove blank lines and strip whitespace
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        
        # Convert to uppercase (requirement from spec)
        processed = '\n'.join(line.upper() for line in lines)
        
        return processed
    except FileNotFoundError:
        # Log error for debugging (file missing is expected in some cases)
        logger.warning(f"File not found: {filepath}")
        return ""
```

## Type Hint Documentation

### 8. Documenting Complex Types

**Document complex type hints with comments:**

```python
from typing import Dict, List, Tuple, Optional

def process_users(
    users: List[Dict[str, Any]],  # List of user dictionaries with 'name', 'email', 'age'
    filter_func: Optional[Callable[[Dict[str, Any]], bool]] = None  # Optional filter function
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Process users and group by category.
    
    Args:
        users: List of user dictionaries, each containing:
            - name (str): User's name
            - email (str): User's email
            - age (int): User's age
        filter_func: Optional function to filter users before processing
    
    Returns:
        Dictionary with keys as categories and values as filtered user lists
    """
    ...
```

## API Documentation

### 9. Public API Documentation

**Document all public APIs clearly:**

```python
class Database:
    """
    Database connection manager.
    
    Provides methods for connecting to, querying, and managing database connections.
    Uses connection pooling for efficiency.
    
    Attributes:
        connection_string: Database connection string
        pool_size: Maximum number of connections in pool
    
    Example:
        >>> db = Database("postgresql://localhost/mydb")
        >>> results = db.query("SELECT * FROM users WHERE age > ?", (18,))
        >>> db.close()
    """
    
    def query(self, sql: str, params: tuple = None) -> list:
        """
        Execute SQL query and return results.
        
        Args:
            sql: SQL query string (use ? for parameter placeholders)
            params: Optional tuple of parameters for query
        
        Returns:
            List of dictionaries representing query results
        
        Raises:
            DatabaseError: If query execution fails
            ConnectionError: If database connection fails
        
        Example:
            >>> results = db.query("SELECT name FROM users WHERE id = ?", (1,))
            >>> results[0]['name']
            'Alice'
        """
        ...
```

## Documentation Best Practices

### 10. Keep Documentation Updated

**Update documentation when code changes:**

```python
# Bad: Documentation doesn't match implementation
def process_data(data: list) -> dict:
    """
    Process data and return count.
    
    Returns:
        Dictionary with 'count' key
    """
    # Implementation changed but docstring not updated
    return {'count': len(data), 'total': sum(data), 'average': sum(data) / len(data)}

# Good: Documentation matches implementation
def process_data(data: list) -> dict:
    """
    Process data and return statistics.
    
    Returns:
        Dictionary containing:
            - count: Number of items
            - total: Sum of values
            - average: Mean value
    """
    return {'count': len(data), 'total': sum(data), 'average': sum(data) / len(data)}
```

## Documentation Checklist

When writing documentation:

- [ ] All public functions have docstrings
- [ ] All public classes have docstrings
- [ ] All modules have docstrings
- [ ] Args section lists all parameters
- [ ] Returns section describes return value
- [ ] Raises section lists all exceptions
- [ ] Examples are provided for complex functions
- [ ] Type hints match docstring types
- [ ] Comments explain WHY, not WHAT
- [ ] Documentation is up-to-date with code

## Best Practices Summary

1. **Write docstrings** - For all public functions, classes, modules
2. **Use consistent format** - Google-style or NumPy-style
3. **Document parameters** - Type, description, defaults
4. **Document return values** - Type and description
5. **Document exceptions** - All exceptions that may be raised
6. **Provide examples** - For complex or non-obvious usage
7. **Keep updated** - Update docs when code changes
8. **Use comments sparingly** - Code should be self-documenting
9. **Explain WHY** - Not WHAT (in comments)
10. **Be concise** - But comprehensive

