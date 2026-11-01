# NumPy Numerical Computing Patterns

Expert guidance for efficient numerical computing with NumPy.

## Core NumPy Principles

### 1. Array Creation

Create arrays efficiently:

```python
import numpy as np
from typing import List, Tuple, Optional, Union

def create_array_from_list(data: List[Union[int, float]]) -> np.ndarray:
    """
    Create NumPy array from list.
    
    Args:
        data: List of numbers
    
    Returns:
        NumPy array
    """
    return np.array(data, dtype=np.float64)

def create_zeros(shape: Tuple[int, ...], dtype: type = np.float64) -> np.ndarray:
    """Create array of zeros."""
    return np.zeros(shape, dtype=dtype)

def create_ones(shape: Tuple[int, ...], dtype: type = np.float64) -> np.ndarray:
    """Create array of ones."""
    return np.ones(shape, dtype=dtype)

def create_range(start: float, stop: float, step: float = 1.0) -> np.ndarray:
    """Create array with range of values."""
    return np.arange(start, stop, step)

def create_linspace(start: float, stop: float, num: int = 50) -> np.ndarray:
    """Create array with evenly spaced values."""
    return np.linspace(start, stop, num)
```

### 2. Array Operations

Perform array operations efficiently:

```python
def array_operations(a: np.ndarray, b: np.ndarray) -> dict:
    """
    Perform common array operations.
    
    Args:
        a: First array
        b: Second array
    
    Returns:
        Dictionary of operation results
    """
    return {
        'addition': a + b,
        'subtraction': a - b,
        'multiplication': a * b,
        'division': np.divide(a, b, out=np.zeros_like(a), where=b!=0),
        'dot_product': np.dot(a, b) if a.ndim == 1 and b.ndim == 1 else None,
        'matrix_multiply': np.matmul(a, b) if a.ndim == 2 and b.ndim == 2 else None
    }

def array_statistics(arr: np.ndarray) -> dict:
    """Calculate array statistics."""
    return {
        'mean': np.mean(arr),
        'std': np.std(arr),
        'min': np.min(arr),
        'max': np.max(arr),
        'median': np.median(arr),
        'sum': np.sum(arr),
        'percentile_25': np.percentile(arr, 25),
        'percentile_75': np.percentile(arr, 75)
    }
```

### 3. Array Indexing & Slicing

Use efficient indexing:

```python
def array_slicing(arr: np.ndarray,
                  start: Optional[int] = None,
                  stop: Optional[int] = None,
                  step: Optional[int] = None) -> np.ndarray:
    """
    Slice array efficiently.
    
    Args:
        arr: Input array
        start: Start index
        stop: Stop index
        step: Step size
    
    Returns:
        Sliced array
    """
    return arr[start:stop:step]

def boolean_indexing(arr: np.ndarray, condition: np.ndarray) -> np.ndarray:
    """Use boolean indexing for filtering."""
    return arr[condition]

def fancy_indexing(arr: np.ndarray, indices: np.ndarray) -> np.ndarray:
    """Use fancy indexing."""
    return arr[indices]
```

### 4. Array Broadcasting

Use broadcasting efficiently:

```python
def broadcasting_example():
    """Demonstrate broadcasting."""
    # Shape (3, 1) broadcasts with (1, 4) to (3, 4)
    a = np.array([[1], [2], [3]])  # Shape (3, 1)
    b = np.array([[1, 2, 3, 4]])   # Shape (1, 4)
    result = a + b  # Shape (3, 4)
    return result

def add_scalar_to_array(arr: np.ndarray, scalar: float) -> np.ndarray:
    """Add scalar to array using broadcasting."""
    return arr + scalar  # Broadcasting automatically applied
```

### 5. Mathematical Functions

Use NumPy mathematical functions:

```python
def apply_math_functions(arr: np.ndarray) -> dict:
    """Apply various mathematical functions."""
    return {
        'sin': np.sin(arr),
        'cos': np.cos(arr),
        'exp': np.exp(arr),
        'log': np.log(arr + 1e-10),  # Add small value to avoid log(0)
        'sqrt': np.sqrt(arr),
        'abs': np.abs(arr),
        'power': np.power(arr, 2)
    }

def normalize_array(arr: np.ndarray, method: str = 'min_max') -> np.ndarray:
    """
    Normalize array.
    
    Args:
        arr: Input array
        method: Normalization method ('min_max' or 'z_score')
    
    Returns:
        Normalized array
    """
    if method == 'min_max':
        min_val = np.min(arr)
        max_val = np.max(arr)
        return (arr - min_val) / (max_val - min_val + 1e-10)
    
    elif method == 'z_score':
        mean = np.mean(arr)
        std = np.std(arr)
        return (arr - mean) / (std + 1e-10)
    
    else:
        raise ValueError(f"Unknown normalization method: {method}")
```

### 6. Array Reshaping

Reshape arrays properly:

```python
def reshape_array(arr: np.ndarray, new_shape: Tuple[int, ...]) -> np.ndarray:
    """
    Reshape array.
    
    Args:
        arr: Input array
        new_shape: New shape tuple
    
    Returns:
        Reshaped array
    
    Raises:
        ValueError: If shape is incompatible
    """
    try:
        return arr.reshape(new_shape)
    except ValueError as e:
        raise ValueError(f"Cannot reshape array from {arr.shape} to {new_shape}: {e}")

def flatten_array(arr: np.ndarray) -> np.ndarray:
    """Flatten array to 1D."""
    return arr.flatten()

def transpose_array(arr: np.ndarray) -> np.ndarray:
    """Transpose array."""
    return arr.T
```

### 7. Performance Optimization

Optimize NumPy operations:

```python
def vectorized_operation(arr: np.ndarray) -> np.ndarray:
    """
    Use vectorized operations for better performance.
    
    Good: Vectorized operation
    """
    # Vectorized operation (fast)
    result = arr ** 2 + arr * 2 + 1
    
    # Bad: Loop (slow)
    # result = np.zeros_like(arr)
    # for i in range(len(arr)):
    #     result[i] = arr[i] ** 2 + arr[i] * 2 + 1
    
    return result

def use_inplace_operations(arr: np.ndarray):
    """Use in-place operations to save memory."""
    arr += 1  # In-place addition (modifies arr)
    arr *= 2  # In-place multiplication
    
    # Instead of:
    # arr = arr + 1  # Creates new array
    # arr = arr * 2  # Creates another new array
```

### 8. Best Practices Checklist

When using NumPy:

- ✅ Use vectorized operations instead of loops
- ✅ Choose appropriate data types (int32, float64, etc.)
- ✅ Use broadcasting when possible
- ✅ Pre-allocate arrays when size is known
- ✅ Avoid unnecessary array copies
- ✅ Use views instead of copies when possible
- ✅ Handle NaN and Inf values properly
- ✅ Use appropriate array shape for operations
- ✅ Leverage NumPy functions instead of Python loops
- ✅ Use in-place operations for memory efficiency
- ✅ Validate array shapes before operations
- ✅ Handle edge cases (empty arrays, single values)
- ✅ Document array shapes and dimensions

## Common Patterns

### Pattern 1: Array Processing Pipeline

```python
def process_array_pipeline(data: List[float]) -> np.ndarray:
    """Complete array processing pipeline."""
    # Create array
    arr = np.array(data, dtype=np.float64)
    
    # Remove NaN values
    arr = arr[~np.isnan(arr)]
    
    # Normalize
    arr = normalize_array(arr, method='z_score')
    
    # Apply transformations
    arr = np.sqrt(np.abs(arr))
    
    # Filter
    arr = arr[arr > 0]
    
    return arr
```

### Pattern 2: Matrix Operations

```python
def matrix_operations(A: np.ndarray, B: np.ndarray) -> dict:
    """Perform matrix operations."""
    return {
        'matrix_multiply': np.matmul(A, B),
        'element_wise_multiply': A * B,
        'matrix_inverse': np.linalg.inv(A) if A.shape[0] == A.shape[1] else None,
        'determinant': np.linalg.det(A) if A.shape[0] == A.shape[1] else None,
        'eigenvalues': np.linalg.eigvals(A) if A.shape[0] == A.shape[1] else None
    }
```

Remember: NumPy excels at numerical operations - use vectorization and avoid Python loops for optimal performance.

