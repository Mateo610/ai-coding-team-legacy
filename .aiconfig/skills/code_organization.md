# Code Organization Patterns

Comprehensive patterns for organizing and structuring Python projects.

## Project Structure

### 1. Standard Python Project Structure

**Follow standard project layout:**

```
project_name/
├── README.md                 # Project description and setup instructions
├── LICENSE                   # License file
├── requirements.txt          # Python dependencies
├── setup.py                  # Package setup (if distributable)
├── pyproject.toml            # Modern Python project config
├── .gitignore                # Git ignore patterns
├── .env.example              # Example environment variables
├── src/                      # Source code
│   ├── __init__.py
│   ├── main.py              # Entry point
│   ├── config.py            # Configuration
│   ├── utils/               # Utility modules
│   │   ├── __init__.py
│   │   ├── helpers.py
│   │   └── validators.py
│   ├── models/              # Data models
│   │   ├── __init__.py
│   │   └── user.py
│   ├── services/            # Business logic
│   │   ├── __init__.py
│   │   └── user_service.py
│   └── api/                 # API endpoints (if applicable)
│       ├── __init__.py
│       └── routes.py
├── tests/                    # Test code
│   ├── __init__.py
│   ├── conftest.py          # Pytest configuration
│   ├── test_utils.py
│   ├── test_models.py
│   └── test_services.py
├── docs/                     # Documentation
│   ├── api/
│   └── guides/
└── scripts/                  # Utility scripts
    └── setup.sh
```

**Key Principles:**
- Separate source code from tests
- Group related functionality
- Use packages (directories with `__init__.py`)
- Clear naming conventions
- Minimal top-level files

### 2. Package Organization

**Organize code into logical packages:**

```python
# utils/__init__.py
"""
Utility functions and helpers.

This package provides various utility functions for common operations.
"""

from .helpers import validate_email, format_currency
from .validators import is_valid_input, sanitize_string

__all__ = [
    'validate_email',
    'format_currency',
    'is_valid_input',
    'sanitize_string',
]

# utils/helpers.py
"""Helper functions for common operations."""

def validate_email(email: str) -> bool:
    """Validate email format."""
    ...

def format_currency(amount: float) -> str:
    """Format amount as currency."""
    ...

# utils/validators.py
"""Input validation utilities."""

def is_valid_input(value: Any) -> bool:
    """Check if input is valid."""
    ...

def sanitize_string(text: str) -> str:
    """Sanitize string input."""
    ...
```

**Package Guidelines:**
- Use `__init__.py` to expose public API
- Use `__all__` to define public exports
- Group related functionality
- Keep packages focused and cohesive

## Module Organization

### 3. Module Structure

**Organize modules logically:**

```python
"""
Module for user management.

This module provides classes and functions for managing users,
including creation, validation, and querying.
"""

# Standard library imports (alphabetically)
import json
import os
from pathlib import Path
from typing import Dict, List, Optional

# Third-party imports (alphabetically)
import requests
from dataclasses import dataclass

# Local imports (grouped by distance)
from .models import User
from .utils import validate_email
from ..config import DATABASE_URL

# Module-level constants (UPPER_CASE)
DEFAULT_AGE = 18
MAX_USERNAME_LENGTH = 50

# Module-level variables
_active_users: List[User] = []

# Classes
@dataclass
class UserManager:
    """Manages user operations."""
    ...

# Functions
def create_user(name: str, email: str) -> User:
    """Create new user."""
    ...

# Module-level code (if any)
if __name__ == "__main__":
    # Code for when module is run directly
    pass
```

**Module Structure Order:**
1. Module docstring
2. Standard library imports
3. Third-party imports
4. Local imports
5. Constants
6. Variables
7. Classes
8. Functions
9. Module-level code

### 4. Import Organization

**Organize imports clearly:**

```python
# Standard library imports (alphabetical)
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Third-party imports (alphabetical)
import requests
from dataclasses import dataclass
from flask import Flask, request

# Local imports (grouped by relative path depth)
from .models import User
from .utils import validate_email
from ..config import settings

# Bad: Mixed imports
import os
from .models import User
import json
from typing import Dict

# Good: Organized imports
import json
import os
from typing import Dict
from .models import User
```

**Import Guidelines:**
- Group imports: stdlib, third-party, local
- Sort alphabetically within groups
- Use absolute imports when possible
- Use relative imports sparingly (within package)

## Function Organization

### 5. Function Grouping

**Group related functions together:**

```python
# utils/validators.py
"""Input validation utilities."""

# Email validation functions
def validate_email(email: str) -> bool:
    """Validate email format."""
    ...

def validate_email_domain(email: str) -> bool:
    """Validate email domain exists."""
    ...

# String validation functions
def validate_string(text: str, min_length: int = 1) -> bool:
    """Validate string length."""
    ...

def sanitize_string(text: str) -> str:
    """Sanitize string input."""
    ...

# Number validation functions
def validate_number(value: Any, min_val: float = None, max_val: float = None) -> bool:
    """Validate number range."""
    ...
```

**Grouping Principles:**
- Group by functionality
- Put public functions first
- Put helper functions after
- Use comments to separate groups

### 6. Class Organization

**Organize classes with consistent structure:**

```python
class User:
    """User model class."""
    
    # Class constants
    MIN_AGE = 0
    MAX_AGE = 150
    
    # Class variables
    total_users = 0
    
    def __init__(self, name: str, email: str, age: int):
        """Initialize user."""
        ...
    
    # Public methods
    def get_display_name(self) -> str:
        """Get display name."""
        ...
    
    def activate(self) -> None:
        """Activate user account."""
        ...
    
    # Private methods
    def _validate_age(self, age: int) -> bool:
        """Validate age (private)."""
        ...
    
    # Class methods
    @classmethod
    def from_dict(cls, data: dict) -> 'User':
        """Create user from dictionary."""
        ...
    
    # Static methods
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Check if email is valid."""
        ...
    
    # Properties
    @property
    def is_active(self) -> bool:
        """Check if user is active."""
        ...
    
    # Magic methods
    def __str__(self) -> str:
        """String representation."""
        ...
    
    def __repr__(self) -> str:
        """Developer representation."""
        ...
```

**Class Organization Order:**
1. Class docstring
2. Class constants
3. Class variables
4. `__init__`
5. Public methods
6. Protected methods (single underscore)
7. Private methods (double underscore)
8. Class methods
9. Static methods
10. Properties
11. Magic methods (`__str__`, `__repr__`, etc.)

## Configuration Management

### 7. Configuration Organization

**Separate configuration from code:**

```python
# config.py
"""Application configuration."""

import os
from pathlib import Path
from typing import Optional

class Config:
    """Application configuration class."""
    
    # Database settings
    DATABASE_URL: str = os.getenv('DATABASE_URL', 'sqlite:///default.db')
    DB_POOL_SIZE: int = int(os.getenv('DB_POOL_SIZE', '10'))
    
    # API settings
    API_BASE_URL: str = os.getenv('API_BASE_URL', 'http://localhost:8000')
    API_TIMEOUT: int = int(os.getenv('API_TIMEOUT', '30'))
    
    # Application settings
    DEBUG: bool = os.getenv('DEBUG', 'False').lower() == 'true'
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'default-secret-key')
    
    # Path settings
    DATA_DIR: Path = Path(os.getenv('DATA_DIR', './data'))
    
    @classmethod
    def validate(cls) -> None:
        """Validate configuration."""
        if not cls.SECRET_KEY or cls.SECRET_KEY == 'default-secret-key':
            raise ValueError("SECRET_KEY must be set in environment")

# Create instance
config = Config()

# Usage in other modules
from config import config

database_url = config.DATABASE_URL
```

**Configuration Best Practices:**
- Use environment variables
- Provide sensible defaults
- Validate configuration on startup
- Separate by category
- Document all settings

## Error Handling Organization

### 8. Error Handling Structure

**Organize error handling consistently:**

```python
# errors.py
"""Custom exception classes."""

class AppError(Exception):
    """Base exception for application errors."""
    pass

class ValidationError(AppError):
    """Raised when validation fails."""
    pass

class DatabaseError(AppError):
    """Raised when database operation fails."""
    pass

class ConfigurationError(AppError):
    """Raised when configuration is invalid."""
    pass

# usage.py
from errors import ValidationError, DatabaseError

def process_data(data: dict) -> dict:
    """Process data with proper error handling."""
    try:
        # Validate input
        if not data:
            raise ValidationError("Data cannot be empty")
        
        # Process data
        result = _process_internal(data)
        
        # Save to database
        try:
            save_to_database(result)
        except Exception as e:
            raise DatabaseError(f"Failed to save data: {e}") from e
        
        return result
    except ValidationError:
        # Re-raise validation errors (caller should handle)
        raise
    except DatabaseError:
        # Re-raise database errors (caller should handle)
        raise
    except Exception as e:
        # Log unexpected errors and raise
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise AppError("An unexpected error occurred") from e
```

## Code Organization Best Practices

### 9. Keep Functions Small and Focused

**One function = one responsibility:**

```python
# Bad: Too many responsibilities
def process_user_data(data: dict) -> dict:
    """Process user data - does too much."""
    # Validate
    if not data.get('name'):
        raise ValueError("Name required")
    # Format
    data['name'] = data['name'].title()
    # Save
    save_to_database(data)
    # Send email
    send_welcome_email(data['email'])
    # Return
    return data

# Good: Single responsibility
def validate_user_data(data: dict) -> None:
    """Validate user data."""
    if not data.get('name'):
        raise ValueError("Name required")
    if not data.get('email'):
        raise ValueError("Email required")

def format_user_data(data: dict) -> dict:
    """Format user data."""
    formatted = data.copy()
    formatted['name'] = data['name'].title()
    return formatted

def process_user_data(data: dict) -> dict:
    """Process user data (orchestrates other functions)."""
    validate_user_data(data)
    formatted = format_user_data(data)
    save_to_database(formatted)
    send_welcome_email(formatted['email'])
    return formatted
```

### 10. Use Descriptive Names

**Names should be self-documenting:**

```python
# Bad: Unclear names
def proc(d, f):
    """Process data."""
    ...

# Good: Descriptive names
def process_user_data(user_data: dict, format_options: dict) -> dict:
    """Process user data with formatting options."""
    ...

# Bad: Abbreviations
def calc_tot(items, disc):
    """Calculate total."""
    ...

# Good: Full words
def calculate_total(items: list, discount: float) -> float:
    """Calculate total price with discount."""
    ...
```

## Best Practices Summary

1. **Follow standard structure** - Use established project layout
2. **Organize into packages** - Group related functionality
3. **Structure modules consistently** - Docstring, imports, constants, classes, functions
4. **Group related functions** - Put related code together
5. **Order class elements** - Constants, variables, methods, properties
6. **Separate configuration** - Use config files/environment variables
7. **Organize error handling** - Custom exceptions, consistent patterns
8. **Keep functions focused** - Single responsibility principle
9. **Use descriptive names** - Self-documenting code
10. **Maintain consistency** - Follow patterns throughout project

