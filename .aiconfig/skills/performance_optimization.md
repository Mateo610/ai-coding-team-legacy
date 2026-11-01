# Performance Optimization Patterns

Comprehensive patterns for profiling and optimizing Python code.

## Performance Principles

### 1. Measure Before Optimizing

**Always profile code before optimizing:**

```python
import time
import cProfile
import pstats
from io import StringIO

def profile_function(func):
    """Profile function execution time."""
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        print(f"{func.__name__} took {duration:.4f} seconds")
        return result
    return wrapper

# Use cProfile for detailed profiling
def profile_with_cprofile(func):
    """Profile function with cProfile."""
    profiler = cProfile.Profile()
    profiler.enable()
    result = func(*args, **kwargs)
    profiler.disable()
    
    s = StringIO()
    stats = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    stats.print_stats()
    print(s.getvalue())
    
    return result

@profile_function
def process_large_dataset(data: list) -> list:
    """Process large dataset."""
    return [item * 2 for item in data]
```

**Key Points:**
- Measure before optimizing
- Use profiling tools (cProfile, line_profiler)
- Focus on bottlenecks
- Verify improvements

## Algorithm Optimization

### 2. Choose Efficient Algorithms

**Select appropriate algorithms for the problem:**

```python
# Bad: O(n²) algorithm
def find_duplicates_slow(items: list) -> list:
    """Find duplicates (inefficient)."""
    duplicates = []
    for i, item in enumerate(items):
        if item in items[i+1:]:  # O(n) lookup in slice
            if item not in duplicates:
                duplicates.append(item)
    return duplicates

# Good: O(n) algorithm
def find_duplicates_fast(items: list) -> list:
    """Find duplicates (efficient)."""
    seen = set()
    duplicates = set()
    for item in items:  # O(n) iteration
        if item in seen:  # O(1) lookup
            duplicates.add(item)
        else:
            seen.add(item)
    return list(duplicates)
```

**Algorithm Complexity:**
- O(1): Constant time (dict lookup, set operations)
- O(log n): Logarithmic (binary search)
- O(n): Linear (single loop)
- O(n log n): Linearithmic (sorting)
- O(n²): Quadratic (nested loops) - avoid when possible

### 3. Use Efficient Data Structures

**Choose appropriate data structures:**

```python
# Use sets for membership testing (O(1))
valid_ids = {1, 2, 3, 4, 5}
if user_id in valid_ids:  # Fast: O(1)
    process_user(user_id)

# Use lists for ordered sequences
items = [1, 2, 3, 4, 5]
for item in items:  # Fast iteration
    process(item)

# Use dicts for key-value lookups (O(1))
user_cache = {user_id: user_data for user_id in user_ids}
user_data = user_cache.get(user_id)  # Fast: O(1)

# Use deque for fast appends/pops from both ends
from collections import deque
queue = deque()
queue.appendleft(item)  # Fast: O(1)
item = queue.pop()  # Fast: O(1)
```

## Memory Optimization

### 4. Use Generators for Large Sequences

**Generate values lazily instead of storing all:**

```python
# Bad: Stores all values in memory
def read_file_lines_bad(filepath: str) -> list:
    """Read all lines into memory."""
    with open(filepath, 'r') as f:
        lines = f.readlines()  # Loads entire file
    return lines

# Good: Generates lines on demand
def read_file_lines_good(filepath: str):
    """Generate lines on demand (generator)."""
    with open(filepath, 'r') as f:
        for line in f:  # Reads one line at a time
            yield line.strip()

# Usage
for line in read_file_lines_good('large_file.txt'):
    process(line)  # Processes one line at a time
```

**Generator Benefits:**
- Memory efficient (lazy evaluation)
- Fast startup (no pre-processing)
- Can be infinite sequences
- Composable (generator pipelines)

### 5. Avoid Unnecessary Copies

**Minimize data copying:**

```python
# Bad: Unnecessary list copy
def process_data_bad(data: list) -> list:
    """Process data with unnecessary copy."""
    processed = data.copy()  # Unnecessary copy
    for i in range(len(processed)):
        processed[i] = processed[i] * 2
    return processed

# Good: Generator comprehension (no copy)
def process_data_good(data: list):
    """Process data without copying."""
    return (item * 2 for item in data)  # Generator, no copy

# If modification needed, modify in place
def process_data_inplace(data: list) -> None:
    """Process data in place (modifies original)."""
    for i in range(len(data)):
        data[i] = data[i] * 2  # Modify in place
```

## Caching and Memoization

### 6. Use Caching for Expensive Operations

**Cache results of expensive computations:**

```python
from functools import lru_cache
from typing import Dict

# Built-in caching (Python 3.2+)
@lru_cache(maxsize=128)
def fibonacci(n: int) -> int:
    """Calculate fibonacci number (cached)."""
    if n < 2:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Manual caching
_cache: Dict[str, Any] = {}

def expensive_computation(key: str) -> Any:
    """Expensive computation with manual caching."""
    if key in _cache:
        return _cache[key]
    
    # Expensive computation
    result = complex_calculation(key)
    _cache[key] = result
    return result

# Clear cache when needed
def clear_cache() -> None:
    """Clear computation cache."""
    _cache.clear()
```

**Caching Guidelines:**
- Cache expensive operations
- Set appropriate cache size
- Clear cache when data changes
- Monitor cache hit rates

## String Optimization

### 7. Efficient String Operations

**Use appropriate string methods:**

```python
# Bad: String concatenation in loop (creates new strings)
def build_string_bad(items: list) -> str:
    """Build string inefficiently."""
    result = ""
    for item in items:
        result += str(item)  # Creates new string each time
    return result

# Good: Use join() (creates string once)
def build_string_good(items: list) -> str:
    """Build string efficiently."""
    return "".join(str(item) for item in items)

# Bad: String formatting in loop
def format_strings_bad(templates: list, data: dict) -> list:
    """Format strings inefficiently."""
    results = []
    for template in templates:
        results.append(template.format(**data))
    return results

# Good: Use list comprehension
def format_strings_good(templates: list, data: dict) -> list:
    """Format strings efficiently."""
    return [template.format(**data) for template in templates]
```

## Loop Optimization

### 8. Optimize Loops

**Make loops as efficient as possible:**

```python
# Bad: Redundant calculations in loop
def process_items_bad(items: list) -> list:
    """Process items inefficiently."""
    results = []
    length = len(items)
    for i in range(len(items)):  # Calls len() each iteration
        if i < length:  # Redundant check
            results.append(items[i] * 2)
    return results

# Good: Optimized loop
def process_items_good(items: list) -> list:
    """Process items efficiently."""
    return [item * 2 for item in items]  # List comprehension

# Or use generator for memory efficiency
def process_items_generator(items: list):
    """Process items with generator (memory efficient)."""
    return (item * 2 for item in items)

# Avoid nested loops when possible
# Bad: O(n²)
def find_pairs_bad(items: list, target: int) -> list:
    """Find pairs inefficiently."""
    pairs = []
    for i in range(len(items)):
        for j in range(i+1, len(items)):
            if items[i] + items[j] == target:
                pairs.append((items[i], items[j]))
    return pairs

# Good: O(n) with set
def find_pairs_good(items: list, target: int) -> list:
    """Find pairs efficiently."""
    seen = set()
    pairs = []
    for item in items:
        complement = target - item
        if complement in seen:
            pairs.append((item, complement))
        seen.add(item)
    return pairs
```

## Database Optimization

### 9. Optimize Database Queries

**Use efficient database operations:**

```python
# Bad: N+1 query problem
def get_users_posts_bad(user_ids: list) -> dict:
    """Get user posts inefficiently."""
    result = {}
    for user_id in user_ids:  # N queries
        posts = db.query("SELECT * FROM posts WHERE user_id = ?", (user_id,))
        result[user_id] = posts
    return result

# Good: Single query with IN clause
def get_users_posts_good(user_ids: list) -> dict:
    """Get user posts efficiently."""
    placeholders = ",".join("?" * len(user_ids))
    query = f"SELECT * FROM posts WHERE user_id IN ({placeholders})"
    posts = db.query(query, tuple(user_ids))  # Single query
    
    # Group by user_id
    result = {}
    for post in posts:
        user_id = post['user_id']
        if user_id not in result:
            result[user_id] = []
        result[user_id].append(post)
    return result

# Use connection pooling
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    'postgresql://localhost/db',
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20
)
```

## Best Practices Summary

1. **Profile first** - Measure before optimizing
2. **Choose efficient algorithms** - Use appropriate time complexity
3. **Use efficient data structures** - Sets, dicts for O(1) operations
4. **Use generators** - For memory efficiency with large sequences
5. **Avoid unnecessary copies** - Modify in place when possible
6. **Cache expensive operations** - Use lru_cache or manual caching
7. **Optimize string operations** - Use join() instead of concatenation
8. **Optimize loops** - Use comprehensions, avoid nested loops
9. **Optimize database queries** - Avoid N+1 queries
10. **Monitor performance** - Track metrics over time

