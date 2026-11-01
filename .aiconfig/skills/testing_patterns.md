# Testing Patterns

Comprehensive testing patterns and best practices for Python code.

## Testing Principles

### 1. Test-Driven Development (TDD)

**Write tests before implementation when possible:**

```python
import pytest
from typing import List

# Test first (TDD approach)
def test_calculate_average():
    """Test average calculation."""
    assert calculate_average([1, 2, 3, 4, 5]) == 3.0
    assert calculate_average([10, 20]) == 15.0
    assert calculate_average([5]) == 5.0

# Then implement
def calculate_average(numbers: List[float]) -> float:
    """Calculate average of numbers."""
    if not numbers:
        raise ValueError("Cannot calculate average of empty list")
    return sum(numbers) / len(numbers)
```

**Benefits:**
- Forces you to think about the API first
- Ensures tests are actually written
- Helps design better interfaces
- Provides immediate feedback

## Test Structure

### 2. Arrange-Act-Assert Pattern

**Structure tests clearly:**

```python
import pytest

def test_user_creation():
    """Test user creation with arrange-act-assert pattern."""
    # Arrange: Set up test data
    username = "test_user"
    email = "test@example.com"
    age = 25
    
    # Act: Execute the function
    user = create_user(username, email, age)
    
    # Assert: Verify the result
    assert user.username == username
    assert user.email == email
    assert user.age == age
    assert user.id is not None
```

**Key Points:**
- Arrange: Set up all necessary data
- Act: Call the function being tested
- Assert: Verify the expected outcome
- Keep tests focused on one behavior

### 3. Test Naming Conventions

**Use descriptive test names:**

```python
# Good test names
def test_calculate_total_with_empty_list():
    """Test total calculation with empty list."""
    ...

def test_calculate_total_with_negative_numbers():
    """Test total calculation with negative numbers."""
    ...

def test_calculate_total_raises_error_on_invalid_input():
    """Test that total calculation raises error on invalid input."""
    ...

# Bad test names
def test1():  # Not descriptive
    ...

def test_calculate():  # Too vague
    ...
```

**Conventions:**
- Use `test_` prefix
- Describe what is being tested
- Include expected behavior/outcome
- Use underscore separation
- Be specific and descriptive

### 4. Test Organization

**Organize tests by functionality:**

```python
# tests/test_calculator.py
import pytest
from calculator import Calculator

class TestCalculator:
    """Test suite for Calculator class."""
    
    def test_add_positive_numbers(self):
        """Test addition with positive numbers."""
        calc = Calculator()
        assert calc.add(2, 3) == 5
    
    def test_add_negative_numbers(self):
        """Test addition with negative numbers."""
        calc = Calculator()
        assert calc.add(-2, -3) == -5
    
    def test_add_zero(self):
        """Test addition with zero."""
        calc = Calculator()
        assert calc.add(5, 0) == 5
    
    def test_subtract_positive_numbers(self):
        """Test subtraction with positive numbers."""
        calc = Calculator()
        assert calc.subtract(5, 3) == 2
```

**Key Points:**
- Group related tests in classes
- Use descriptive class names (`TestFeatureName`)
- Keep tests independent
- One assertion per test when possible

## Test Types

### 5. Unit Tests

**Test individual functions/classes in isolation:**

```python
import pytest
from typing import List

def test_factorial_zero():
    """Test factorial of zero."""
    assert factorial(0) == 1

def test_factorial_one():
    """Test factorial of one."""
    assert factorial(1) == 1

def test_factorial_positive():
    """Test factorial of positive numbers."""
    assert factorial(5) == 120

def test_factorial_negative():
    """Test factorial raises error for negative numbers."""
    with pytest.raises(ValueError, match="Factorial not defined for negative numbers"):
        factorial(-1)
```

**Characteristics:**
- Fast execution
- Isolated from dependencies
- Test single units of code
- No external resources (files, network, etc.)

### 6. Integration Tests

**Test interaction between components:**

```python
import pytest
from pathlib import Path
import tempfile

def test_save_and_load_config():
    """Test saving and loading configuration."""
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        config_path = Path(f.name)
    
    try:
        # Save config
        config = {"key": "value", "number": 42}
        save_config(config, config_path)
        
        # Load config
        loaded_config = load_config(config_path)
        
        # Verify
        assert loaded_config == config
    finally:
        # Cleanup
        config_path.unlink()
```

**Characteristics:**
- Test component interactions
- May use external resources
- Slower than unit tests
- Verify integration works correctly

### 7. Test Fixtures

**Use pytest fixtures for setup/teardown:**

```python
import pytest
from pathlib import Path
import tempfile

@pytest.fixture
def temp_dir():
    """Create temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_data():
    """Provide sample data for tests."""
    return {
        "users": [
            {"name": "Alice", "age": 25},
            {"name": "Bob", "age": 30},
        ]
    }

def test_process_files(temp_dir, sample_data):
    """Test file processing with fixtures."""
    # Use temp_dir fixture
    file_path = temp_dir / "data.json"
    save_json(sample_data, file_path)
    
    # Test processing
    result = process_file(file_path)
    assert result is not None
```

**Fixture Scope:**
- `function`: Run once per test (default)
- `class`: Run once per test class
- `module`: Run once per module
- `session`: Run once per test session

### 8. Parametrized Tests

**Test multiple inputs with parametrize:**

```python
import pytest

@pytest.mark.parametrize("input,expected", [
    (0, 0),
    (1, 1),
    (2, 4),
    (3, 9),
    (4, 16),
])
def test_square(input, expected):
    """Test square function with multiple inputs."""
    assert square(input) == expected

@pytest.mark.parametrize("a,b,expected", [
    (2, 3, 5),
    (0, 0, 0),
    (-1, 1, 0),
    (10, -5, 5),
])
def test_add(a, b, expected):
    """Test add function with multiple inputs."""
    assert add(a, b) == expected
```

**Benefits:**
- Reduce code duplication
- Test multiple cases easily
- Clear test cases
- Better coverage

## Edge Cases and Error Handling

### 9. Test Edge Cases

**Always test boundary conditions:**

```python
import pytest

def test_divide_by_zero():
    """Test division by zero raises error."""
    with pytest.raises(ZeroDivisionError):
        divide(10, 0)

def test_empty_list():
    """Test handling of empty list."""
    assert process_list([]) == []

def test_none_input():
    """Test handling of None input."""
    with pytest.raises(TypeError):
        process_value(None)

def test_maximum_values():
    """Test with maximum values."""
    assert calculate(999999, 999999) == 1999998

def test_minimum_values():
    """Test with minimum values."""
    assert calculate(0, 0) == 0
```

**Edge Cases to Consider:**
- Empty collections (list, dict, string)
- None values
- Zero values
- Maximum/minimum values
- Negative numbers (if applicable)
- Very large numbers
- Special characters (strings)

### 10. Exception Testing

**Test that exceptions are raised correctly:**

```python
import pytest

def test_invalid_input_raises_value_error():
    """Test that invalid input raises ValueError."""
    with pytest.raises(ValueError, match="Invalid input"):
        process_input("invalid")

def test_file_not_found():
    """Test that missing file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        read_file(Path("nonexistent.txt"))

def test_type_error_on_wrong_type():
    """Test that wrong type raises TypeError."""
    with pytest.raises(TypeError, match="Expected int"):
        calculate("not a number", 5)
```

**Exception Testing Patterns:**
- Use `pytest.raises()` context manager
- Verify exception type
- Optionally verify exception message
- Test that exceptions are raised at right time

## Mocking and Patching

### 11. Mocking External Dependencies

**Mock external services and dependencies:**

```python
import pytest
from unittest.mock import Mock, patch, MagicMock
import requests

@patch('requests.get')
def test_fetch_data(mock_get):
    """Test data fetching with mocked HTTP request."""
    # Set up mock response
    mock_response = Mock()
    mock_response.json.return_value = {"data": "test"}
    mock_response.status_code = 200
    mock_get.return_value = mock_response
    
    # Test function
    result = fetch_data("http://api.example.com/data")
    
    # Verify
    assert result == {"data": "test"}
    mock_get.assert_called_once_with("http://api.example.com/data")

@patch('os.path.exists')
def test_file_exists_check(mock_exists):
    """Test file existence check with mocked os.path.exists."""
    mock_exists.return_value = True
    
    assert check_file_exists("test.txt") is True
    mock_exists.assert_called_once_with("test.txt")
```

**When to Mock:**
- External APIs
- Database calls
- File system operations
- Network requests
- Time-dependent code
- Random number generation

### 12. Mocking with Fixtures

**Use fixtures for common mocks:**

```python
import pytest
from unittest.mock import Mock, patch

@pytest.fixture
def mock_api():
    """Mock API client."""
    with patch('api_client.APIClient') as mock:
        mock_instance = Mock()
        mock.return_value = mock_instance
        yield mock_instance

def test_api_call(mock_api):
    """Test API call with mocked client."""
    mock_api.get_data.return_value = {"result": "success"}
    
    result = use_api_client()
    assert result == {"result": "success"}
    mock_api.get_data.assert_called_once()
```

## Test Coverage

### 13. Coverage Guidelines

**Aim for comprehensive coverage:**

```python
# Test all branches
def test_conditional_logic():
    """Test all branches of conditional logic."""
    # Test True branch
    assert process_value(10) == "high"
    
    # Test False branch
    assert process_value(5) == "medium"
    
    # Test edge case
    assert process_value(0) == "low"

# Test all exception paths
def test_all_error_cases():
    """Test all error handling paths."""
    # Invalid input
    with pytest.raises(ValueError):
        process("invalid")
    
    # Missing input
    with pytest.raises(TypeError):
        process(None)
    
    # Out of range
    with pytest.raises(ValueError):
        process(1000)
```

**Coverage Goals:**
- Aim for >80% coverage
- Focus on critical paths
- Test error handling
- Test edge cases
- Don't obsess over 100% (diminishing returns)

## Test Best Practices

### 14. Test Independence

**Keep tests independent and isolated:**

```python
# Good: Independent tests
def test_create_user():
    """Test user creation (independent)."""
    user = create_user("test", "test@example.com")
    assert user.id is not None

def test_delete_user():
    """Test user deletion (independent)."""
    user = create_user("test2", "test2@example.com")
    delete_user(user.id)
    assert get_user(user.id) is None

# Bad: Dependent tests
user_id = None

def test_create_user_bad():
    """Test user creation (dependent)."""
    global user_id
    user = create_user("test", "test@example.com")
    user_id = user.id  # Shared state!

def test_delete_user_bad():
    """Test user deletion (dependent)."""
    global user_id
    delete_user(user_id)  # Depends on previous test!
```

**Key Points:**
- Tests should run in any order
- No shared state between tests
- Each test sets up its own data
- Tests don't depend on each other

### 15. Test Data Management

**Use factories and fixtures for test data:**

```python
import pytest
from dataclasses import dataclass

@dataclass
class User:
    """User data class."""
    name: str
    email: str
    age: int

@pytest.fixture
def user_factory():
    """Factory for creating test users."""
    def _create_user(name="Test User", email="test@example.com", age=25):
        return User(name=name, email=email, age=age)
    return _create_user

def test_user_processing(user_factory):
    """Test user processing with factory."""
    user = user_factory(name="Alice", age=30)
    result = process_user(user)
    assert result.name == "Alice"
```

## Performance Testing

### 16. Performance Test Patterns

**Test performance when needed:**

```python
import pytest
import time

def test_performance_threshold():
    """Test that function completes within time threshold."""
    start = time.time()
    result = process_large_dataset(range(10000))
    duration = time.time() - start
    
    assert duration < 1.0  # Should complete in < 1 second
    assert result is not None

@pytest.mark.slow
def test_large_dataset():
    """Test with large dataset (mark as slow)."""
    data = list(range(1000000))
    result = process_data(data)
    assert len(result) == 1000000
```

**Performance Testing:**
- Use `time` or `timeit` module
- Set reasonable thresholds
- Mark slow tests with `@pytest.mark.slow`
- Run separately from fast tests

## Test Organization Best Practices

### 17. Test File Structure

**Organize tests mirroring source structure:**

```
project/
├── src/
│   ├── calculator.py
│   ├── utils/
│   │   └── helpers.py
│   └── models/
│       └── user.py
└── tests/
    ├── test_calculator.py
    ├── utils/
    │   └── test_helpers.py
    └── models/
        └── test_user.py
```

**Conventions:**
- Mirror source structure
- One test file per source file
- Test classes for related tests
- Fixtures in `conftest.py`

### 18. Test Documentation

**Document tests clearly:**

```python
def test_calculate_total_with_discount():
    """
    Test total calculation with discount applied.
    
    Verifies that:
    - Discount is correctly calculated
    - Total includes discount
    - Edge cases (0% discount, 100% discount) are handled
    """
    items = [100, 50, 25]
    discount = 0.1  # 10%
    
    total = calculate_total(items, discount)
    
    expected = (100 + 50 + 25) * 0.9  # 175 * 0.9 = 157.5
    assert total == expected
```

**Documentation Guidelines:**
- Describe what is being tested
- List key behaviors being verified
- Explain complex test setup
- Note assumptions or prerequisites

## Best Practices Summary

1. **Write tests first** - Use TDD when possible
2. **Test independently** - No dependencies between tests
3. **Test edge cases** - Empty, None, boundaries
4. **Use descriptive names** - Clear test names
5. **Organize logically** - Group related tests
6. **Mock dependencies** - Isolate units under test
7. **Parametrize when useful** - Test multiple inputs
8. **Document tests** - Explain what is being tested
9. **Aim for coverage** - >80% for critical code
10. **Keep tests fast** - Use mocks, avoid slow operations

## Common Patterns

### Test Setup Pattern
```python
@pytest.fixture
def setup():
    """Common setup for tests."""
    # Setup code
    yield
    # Teardown code (if needed)

def test_with_setup(setup):
    """Test using setup fixture."""
    # Test code
    pass
```

### Test Exception Pattern
```python
def test_exception():
    """Test that exception is raised."""
    with pytest.raises(ExceptionType, match="error message"):
        function_that_raises()
```

### Test Mock Pattern
```python
@patch('module.function')
def test_with_mock(mock_function):
    """Test with mocked function."""
    mock_function.return_value = expected_value
    result = function_under_test()
    assert result == expected_value
    mock_function.assert_called_once()
```

