# Debugging Patterns

Comprehensive patterns for debugging Python code effectively.

## Debugging Principles

### 1. Reproduce the Issue

**Always reproduce the issue before debugging:**

```python
def test_reproduction():
    """Test to reproduce the bug."""
    # Steps to reproduce
    data = [1, 2, 3, None, 5]
    result = process_data(data)
    
    # Expected vs actual
    assert result == [1, 2, 3, 0, 5]  # Expected
    # Actual: TypeError: unsupported operand type(s)
```

**Reproduction Steps:**
- Understand the issue
- Identify minimal reproduction case
- Create test case
- Verify the bug exists

### 2. Use Debugger

**Use debugger for systematic debugging:**

```python
# Use pdb (Python debugger)
import pdb

def process_data(data: list) -> list:
    """Process data with debugger."""
    pdb.set_trace()  # Breakpoint
    result = []
    for item in data:
        processed = item * 2
        result.append(processed)
    return result

# Use ipdb (improved pdb) for better experience
import ipdb

def process_data_improved(data: list) -> list:
    """Process data with ipdb."""
    ipdb.set_trace()  # Better breakpoint
    result = []
    for item in data:
        processed = item * 2
        result.append(processed)
    return result
```

**Debugger Commands:**
- `n` (next): Execute next line
- `s` (step): Step into function
- `c` (continue): Continue execution
- `l` (list): Show current code
- `p variable`: Print variable value
- `pp variable`: Pretty print variable
- `q` (quit): Quit debugger

### 3. Use Print Debugging Strategically

**Use print statements strategically:**

```python
def process_data(data: list) -> list:
    """Process data with strategic print statements."""
    print(f"DEBUG: Input data: {data}")  # Check input
    print(f"DEBUG: Data type: {type(data)}")
    print(f"DEBUG: Data length: {len(data)}")
    
    result = []
    for i, item in enumerate(data):
        print(f"DEBUG: Processing item {i}: {item} (type: {type(item)})")
        
        if item is None:
            print(f"DEBUG: Found None at index {i}")
            result.append(0)
        else:
            processed = item * 2
            print(f"DEBUG: Processed {item} -> {processed}")
            result.append(processed)
    
    print(f"DEBUG: Final result: {result}")
    return result
```

**Print Debugging Guidelines:**
- Include context (variable name, value, type)
- Use consistent prefix (DEBUG:)
- Remove debug prints before committing
- Consider using logging instead

## Systematic Debugging

### 4. Binary Search Debugging

**Narrow down the problem systematically:**

```python
def find_bug_with_binary_search(data: list) -> list:
    """Find bug using binary search approach."""
    print(f"DEBUG: Full data: {data}")
    
    # Test first half
    first_half = data[:len(data)//2]
    print(f"DEBUG: Testing first half: {first_half}")
    result_first = process_data(first_half)
    print(f"DEBUG: First half result: {result_first}")
    
    # Test second half
    second_half = data[len(data)//2:]
    print(f"DEBUG: Testing second half: {second_half}")
    result_second = process_data(second_half)
    print(f"DEBUG: Second half result: {result_second}")
    
    # Narrow down to problematic half
    # Continue until you find the issue
```

**Binary Search Approach:**
- Test half the input
- Identify which half has the bug
- Repeat with problematic half
- Narrow down to specific element

### 5. Assert for Debugging

**Use assertions to verify assumptions:**

```python
def process_data(data: list) -> list:
    """Process data with assertions."""
    assert data is not None, "Data cannot be None"
    assert isinstance(data, list), f"Expected list, got {type(data)}"
    assert len(data) > 0, "Data cannot be empty"
    
    result = []
    for i, item in enumerate(data):
        assert item is not None or i == 3, f"Unexpected None at index {i}"
        
        if item is None:
            result.append(0)
        else:
            assert isinstance(item, (int, float)), f"Invalid type at index {i}: {type(item)}"
            result.append(item * 2)
    
    assert len(result) == len(data), "Result length mismatch"
    return result
```

**Assertion Benefits:**
- Verify assumptions
- Catch bugs early
- Document expectations
- Can be disabled in production (if needed)

## Error Analysis

### 6. Analyze Error Messages

**Read error messages carefully:**

```python
def analyze_error():
    """Analyze error message structure."""
    try:
        result = process_data([1, 2, None, 4])
    except TypeError as e:
        # Error message structure:
        # TypeError: unsupported operand type(s) for *: 'NoneType' and 'int'
        print(f"Error type: {type(e).__name__}")  # TypeError
        print(f"Error message: {e}")  # unsupported operand type(s)...
        print(f"Error args: {e.args}")  # Error arguments
        
        # Extract useful information
        if "unsupported operand" in str(e):
            print("Issue: Trying to perform operation on incompatible types")
        if "NoneType" in str(e):
            print("Issue: None value not handled")
```

**Error Message Analysis:**
- Error type (TypeError, ValueError, etc.)
- Error message (description of problem)
- Stack trace (where error occurred)
- Context (variables at error location)

### 7. Check Type and Value

**Verify variable types and values:**

```python
def debug_with_type_check(data: list) -> list:
    """Debug by checking types and values."""
    print(f"Type check - data: {type(data)}")
    print(f"Value check - data: {data}")
    print(f"Length check - data: {len(data)}")
    
    result = []
    for i, item in enumerate(data):
        print(f"\n--- Item {i} ---")
        print(f"Type: {type(item)}")
        print(f"Value: {item}")
        print(f"Is None: {item is None}")
        print(f"Is numeric: {isinstance(item, (int, float))}")
        
        # Check before processing
        if item is None:
            print("Skipping None value")
            result.append(0)
        else:
            print(f"Processing: {item} * 2")
            result.append(item * 2)
            print(f"Result: {result[-1]}")
    
    return result
```

## Logging for Debugging

### 8. Use Logging for Debugging

**Use logging instead of print for debugging:**

```python
import logging

# Configure debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def process_data(data: list) -> list:
    """Process data with debug logging."""
    logger.debug(f"Input data: {data}")
    logger.debug(f"Data type: {type(data)}, Length: {len(data)}")
    
    result = []
    for i, item in enumerate(data):
        logger.debug(f"Processing item {i}: {item} (type: {type(item)})")
        
        try:
            processed = item * 2
            logger.debug(f"Successfully processed: {processed}")
            result.append(processed)
        except Exception as e:
            logger.error(f"Error processing item {i}: {e}", exc_info=True)
            result.append(0)
    
    logger.debug(f"Final result: {result}")
    return result
```

**Logging Benefits:**
- Can be filtered by level
- Can write to files
- Includes timestamps
- Can be disabled easily

## Common Debugging Scenarios

### 9. Debug None Errors

**Handle None values properly:**

```python
def debug_none_errors(data: list) -> list:
    """Debug None-related errors."""
    result = []
    for i, item in enumerate(data):
        # Check for None explicitly
        if item is None:
            logger.warning(f"Found None at index {i}, using default value")
            result.append(0)
            continue
        
        # Check type before operations
        if not isinstance(item, (int, float)):
            logger.error(f"Invalid type at index {i}: {type(item)}")
            raise TypeError(f"Expected numeric type at index {i}, got {type(item)}")
        
        result.append(item * 2)
    return result
```

### 10. Debug Index Errors

**Handle index errors properly:**

```python
def debug_index_errors(data: list, indices: list) -> list:
    """Debug index-related errors."""
    result = []
    for idx in indices:
        # Check bounds
        if idx < 0:
            logger.warning(f"Negative index: {idx}, using 0")
            idx = 0
        elif idx >= len(data):
            logger.warning(f"Index {idx} out of bounds (max: {len(data)-1})")
            continue
        
        # Safe access
        try:
            value = data[idx]
            result.append(value)
        except IndexError as e:
            logger.error(f"Index error at {idx}: {e}")
            raise
    
    return result
```

## Debugging Tools

### 11. Use Python Debugger

**Use pdb or ipdb for interactive debugging:**

```python
# Set breakpoint
import pdb

def problematic_function(data: list) -> list:
    """Function with bug."""
    result = []
    pdb.set_trace()  # Breakpoint here
    
    for item in data:
        # Step through this loop
        processed = item * 2
        result.append(processed)
    
    return result

# Or use breakpoint() in Python 3.7+
def modern_debugging(data: list) -> list:
    """Use modern breakpoint()."""
    result = []
    breakpoint()  # Same as pdb.set_trace()
    
    for item in data:
        processed = item * 2
        result.append(processed)
    
    return result
```

### 12. Use IDE Debugger

**Use IDE debugger for visual debugging:**

```python
def use_ide_debugger(data: list) -> list:
    """
    Set breakpoints in IDE (VS Code, PyCharm, etc.).
    
    - Click left margin to set breakpoint
    - Run in debug mode
    - Step through code
    - Inspect variables
    - Evaluate expressions
    """
    result = []
    # Set breakpoint here in IDE
    
    for item in data:
        # Set breakpoint here to inspect loop
        processed = item * 2
        result.append(processed)
    
    # Set breakpoint here to inspect result
    return result
```

## Best Practices Summary

1. **Reproduce first** - Understand and reproduce the bug
2. **Use debugger** - Systematic debugging with pdb/ipdb
3. **Print strategically** - Use print for quick checks
4. **Use assertions** - Verify assumptions
5. **Analyze errors** - Read error messages carefully
6. **Check types/values** - Verify variable states
7. **Use logging** - Better than print for debugging
8. **Handle None** - Explicit None checks
9. **Check bounds** - Verify indices are valid
10. **Use IDE debugger** - Visual debugging when available

