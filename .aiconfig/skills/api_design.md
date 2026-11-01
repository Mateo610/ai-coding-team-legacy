# API Design Patterns

Comprehensive patterns for designing clean and maintainable APIs.

## API Design Principles

### 1. Clear Function Names

**Use descriptive, action-oriented names:**

```python
# Good: Clear action-oriented names
def get_user_by_id(user_id: int) -> User:
    """Get user by ID."""
    ...

def create_user(name: str, email: str) -> User:
    """Create new user."""
    ...

def update_user_email(user_id: int, new_email: str) -> User:
    """Update user email address."""
    ...

def delete_user(user_id: int) -> None:
    """Delete user by ID."""
    ...

# Bad: Unclear or vague names
def user(user_id: int) -> User:  # What does it do?
    ...

def process(data: dict) -> dict:  # Too vague
    ...
```

**Naming Conventions:**
- Use verbs: `get`, `create`, `update`, `delete`, `process`
- Be specific: `get_user_by_id` not `get_user`
- Use consistent patterns: `create_X`, `update_X`, `delete_X`
- Avoid abbreviations: `get_user` not `get_usr`

### 2. Consistent Parameter Order

**Order parameters consistently:**

```python
# Good: Consistent parameter order (resource, filters, options)
def get_users(limit: int = 10, offset: int = 0, filters: dict = None) -> list:
    """Get users with pagination and filters."""
    ...

def get_user_by_id(user_id: int) -> User:
    """Get user by ID."""
    ...

def create_user(name: str, email: str, age: int = None) -> User:
    """Create new user."""
    ...

def update_user(user_id: int, **updates) -> User:
    """Update user with provided fields."""
    ...

# Consistent order: resource_id first, then data, then options
def update_user_email(user_id: int, new_email: str) -> User:
    """Update user email."""
    ...

def update_user_age(user_id: int, new_age: int) -> User:
    """Update user age."""
    ...
```

### 3. Return Types

**Always return consistent, predictable types:**

```python
from typing import Optional, List, Dict, Any

# Good: Always returns list (empty if none found)
def get_users() -> List[User]:
    """Get all users (returns empty list if none)."""
    ...

# Good: Returns Optional (None if not found)
def get_user_by_id(user_id: int) -> Optional[User]:
    """Get user by ID (returns None if not found)."""
    ...

# Good: Returns tuple for multiple values
def paginate_users(limit: int, offset: int) -> tuple[List[User], int]:
    """Get paginated users and total count."""
    # Returns: (users, total_count)
    ...

# Bad: Inconsistent return types
def get_user(user_id: int):  # Returns User or None or dict?
    ...
```

## Error Handling

### 4. API Error Handling

**Use exceptions for errors, not return values:**

```python
# Good: Raise exceptions for errors
def get_user_by_id(user_id: int) -> User:
    """Get user by ID."""
    if user_id < 1:
        raise ValueError(f"Invalid user_id: {user_id}")
    
    user = db.query_user(user_id)
    if user is None:
        raise NotFoundError(f"User not found: {user_id}")
    
    return user

# Bad: Return error values
def get_user_by_id_bad(user_id: int):  # Returns User, None, or error dict?
    """Get user by ID (bad pattern)."""
    if user_id < 1:
        return {"error": "Invalid user_id"}
    
    user = db.query_user(user_id)
    if user is None:
        return None  # Or {"error": "Not found"}?
    
    return user
```

**Exception Guidelines:**
- Raise exceptions for errors
- Use specific exception types (ValueError, NotFoundError)
- Include helpful error messages
- Document exceptions in docstrings

### 5. Custom Exceptions

**Create custom exceptions for API errors:**

```python
class APIError(Exception):
    """Base exception for API errors."""
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

class NotFoundError(APIError):
    """Raised when resource is not found."""
    def __init__(self, message: str):
        super().__init__(message, status_code=404)

class ValidationError(APIError):
    """Raised when validation fails."""
    def __init__(self, message: str):
        super().__init__(message, status_code=400)

class UnauthorizedError(APIError):
    """Raised when authentication fails."""
    def __init__(self, message: str):
        super().__init__(message, status_code=401)

# Usage
def get_user_by_id(user_id: int) -> User:
    """Get user by ID."""
    if user_id < 1:
        raise ValidationError(f"Invalid user_id: {user_id}")
    
    user = db.query_user(user_id)
    if user is None:
        raise NotFoundError(f"User not found: {user_id}")
    
    return user
```

## Validation

### 6. Input Validation

**Validate all inputs at API boundaries:**

```python
def create_user(name: str, email: str, age: int = None) -> User:
    """
    Create new user with validation.
    
    Args:
        name: User's full name (must not be empty)
        email: User's email address (must be valid format)
        age: User's age in years (optional, must be positive if provided)
    
    Returns:
        Created User instance
    
    Raises:
        ValidationError: If any input is invalid
    """
    # Validate name
    if not name or not name.strip():
        raise ValidationError("Name cannot be empty")
    
    # Validate email
    if not email or not _is_valid_email(email):
        raise ValidationError(f"Invalid email format: {email}")
    
    # Validate age
    if age is not None:
        if not isinstance(age, int):
            raise ValidationError(f"Age must be integer, got {type(age)}")
        if age < 0:
            raise ValidationError(f"Age must be non-negative, got {age}")
    
    # All validation passed, create user
    return db.create_user(name=name.strip(), email=email.lower(), age=age)
```

**Validation Best Practices:**
- Validate at API boundaries
- Check types, ranges, formats
- Provide clear error messages
- Validate early (fail fast)

## Documentation

### 7. API Documentation

**Document all public APIs comprehensively:**

```python
def get_users(
    limit: int = 10,
    offset: int = 0,
    filters: dict = None,
    sort_by: str = 'name',
    order: str = 'asc'
) -> tuple[List[User], int]:
    """
    Get paginated list of users with optional filtering and sorting.
    
    Args:
        limit: Maximum number of users to return (default: 10, max: 100)
        offset: Number of users to skip (default: 0)
        filters: Optional dictionary of filters:
            - name (str): Filter by name (partial match)
            - email (str): Filter by email (partial match)
            - age_min (int): Minimum age
            - age_max (int): Maximum age
            - is_active (bool): Filter by active status
        sort_by: Field to sort by (default: 'name', options: 'name', 'email', 'age')
        order: Sort order (default: 'asc', options: 'asc', 'desc')
    
    Returns:
        Tuple containing:
            - List of User instances matching criteria
            - Total count of matching users (for pagination)
    
    Raises:
        ValueError: If limit is out of range or invalid sort_by/order
    
    Example:
        >>> users, total = get_users(limit=20, filters={'is_active': True})
        >>> len(users)
        20
        >>> total
        150
    """
    # Validate parameters
    if limit < 1 or limit > 100:
        raise ValueError(f"Limit must be between 1 and 100, got {limit}")
    if offset < 0:
        raise ValueError(f"Offset must be non-negative, got {offset}")
    if sort_by not in ['name', 'email', 'age']:
        raise ValueError(f"Invalid sort_by: {sort_by}")
    if order not in ['asc', 'desc']:
        raise ValueError(f"Invalid order: {order}")
    
    # Implementation...
    return users, total
```

## Versioning

### 8. API Versioning

**Support API versioning for backwards compatibility:**

```python
# v1 API
def get_user_v1(user_id: int) -> dict:
    """Get user (v1 API - returns dict)."""
    user = db.get_user(user_id)
    return {
        'id': user.id,
        'name': user.name,
        'email': user.email,
    }

# v2 API (newer, better)
def get_user_v2(user_id: int) -> User:
    """Get user (v2 API - returns User object)."""
    return db.get_user(user_id)

# Version router
def get_user(user_id: int, api_version: int = 2) -> Any:
    """Get user with version support."""
    if api_version == 1:
        return get_user_v1(user_id)
    elif api_version == 2:
        return get_user_v2(user_id)
    else:
        raise ValueError(f"Unsupported API version: {api_version}")
```

## Best Practices Summary

1. **Clear function names** - Action-oriented, descriptive
2. **Consistent parameter order** - Resource, filters, options
3. **Predictable return types** - Always same type
4. **Use exceptions** - Not return values for errors
5. **Custom exceptions** - For specific error types
6. **Validate inputs** - At API boundaries
7. **Document thoroughly** - All parameters, returns, exceptions
8. **Support versioning** - For backwards compatibility
9. **Fail fast** - Validate early
10. **Be consistent** - Follow patterns throughout API

