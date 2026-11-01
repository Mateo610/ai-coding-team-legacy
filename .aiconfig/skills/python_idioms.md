# Python Idioms and Best Practices

Master these Python idioms to write idiomatic, efficient, and readable code.

## Idiom 1: List Comprehensions

**Use for:** Transforming sequences, filtering elements

```python
# Transform list
numbers = [1, 2, 3, 4, 5]
squares = [x ** 2 for x in numbers]  # [1, 4, 9, 16, 25]

# Filter elements
evens = [x for x in numbers if x % 2 == 0]  # [2, 4]

# Transform and filter
even_squares = [x ** 2 for x in numbers if x % 2 == 0]  # [4, 16]

# Nested comprehensions (use sparingly)
matrix = [[i * j for j in range(3)] for i in range(3)]
```

**When to use:**
- ✅ Simple transformations/filters
- ✅ Readable single-line operations
- ❌ Complex logic (use loops instead)
- ❌ Deeply nested (use loops for readability)

## Idiom 2: Generator Expressions

**Use for:** Large sequences, memory efficiency

```python
# Generator expression (lazy evaluation)
squares_gen = (x ** 2 for x in range(1000000))  # Memory efficient

# Convert to list only when needed
squares_list = list(squares_gen)

# Use in function calls directly
total = sum(x ** 2 for x in range(100))
```

**Benefits:**
- Memory efficient (only produces values when needed)
- Fast for large sequences
- Can be infinite sequences

## Idiom 3: Dictionary Comprehensions

**Use for:** Transforming dictionaries, filtering key-value pairs

```python
# Transform dictionary
data = {'a': 1, 'b': 2, 'c': 3}
doubled = {k: v * 2 for k, v in data.items()}  # {'a': 2, 'b': 4, 'c': 6}

# Filter dictionary
large_values = {k: v for k, v in data.items() if v > 1}  # {'b': 2, 'c': 3}

# Create dictionary from sequences
names = ['Alice', 'Bob', 'Charlie']
name_lengths = {name: len(name) for name in names}  # {'Alice': 5, 'Bob': 3, ...}
```

## Idiom 4: Enumerate

**Use for:** Getting index and value simultaneously

```python
# Old way (don't do this)
items = ['a', 'b', 'c']
for i in range(len(items)):
    print(i, items[i])

# Pythonic way
items = ['a', 'b', 'c']
for index, value in enumerate(items):
    print(index, value)

# With start index
for index, value in enumerate(items, start=1):
    print(index, value)  # Starts at 1
```

## Idiom 5: Zip

**Use for:** Iterating over multiple sequences simultaneously

```python
names = ['Alice', 'Bob', 'Charlie']
ages = [25, 30, 35]

# Pair up elements
for name, age in zip(names, ages):
    print(f"{name} is {age}")

# Create dictionary from two lists
name_age_dict = dict(zip(names, ages))  # {'Alice': 25, 'Bob': 30, ...}

# Zip multiple sequences
heights = [165, 180, 175]
for name, age, height in zip(names, ages, heights):
    print(f"{name}: age {age}, height {height}")
```

## Idiom 6: Context Managers (with statements)

**Use for:** Resource management (files, locks, connections)

```python
# File handling
with open('data.txt', 'r') as f:
    content = f.read()
# File automatically closed

# Multiple resources
with open('input.txt', 'r') as infile, open('output.txt', 'w') as outfile:
    data = infile.read()
    outfile.write(data.upper())

# Custom context manager
from contextlib import contextmanager

@contextmanager
def timer():
    start = time.time()
    try:
        yield
    finally:
        elapsed = time.time() - start
        print(f"Elapsed time: {elapsed:.2f} seconds")
```

## Idiom 7: Decorators

**Use for:** Adding functionality to functions (logging, caching, validation)

```python
from functools import wraps

def log_calls(func):
    """Decorator to log function calls."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        print(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
        result = func(*args, **kwargs)
        print(f"{func.__name__} returned {result}")
        return result
    return wrapper

@log_calls
def add(a: int, b: int) -> int:
    return a + b

# Built-in decorators
from functools import lru_cache

@lru_cache(maxsize=128)
def fibonacci(n: int) -> int:
    """Memoized fibonacci."""
    if n < 2:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
```

## Idiom 8: Unpacking

**Use for:** Destructuring tuples, lists, dictionaries

```python
# Tuple unpacking
point = (10, 20)
x, y = point

# Multiple assignment
a, b = 1, 2
a, b = b, a  # Swap values

# Extended unpacking
first, *middle, last = [1, 2, 3, 4, 5]  # first=1, middle=[2,3,4], last=5

# Dictionary unpacking
data = {'name': 'Alice', 'age': 25}
name, age = data.values()  # 'Alice', 25

# Function argument unpacking
def greet(name: str, age: int) -> str:
    return f"{name} is {age}"

person = ('Bob', 30)
greet(*person)  # Unpacks tuple

# Keyword argument unpacking
info = {'name': 'Charlie', 'age': 35}
greet(**info)  # Unpacks dictionary as keyword arguments
```

## Idiom 9: Default Arguments and None Pattern

**Use for:** Optional parameters with mutable defaults

```python
# WRONG: Mutable default argument
def add_item(item, items=[]):  # BUG: shared list!
    items.append(item)
    return items

# RIGHT: Use None pattern
def add_item(item, items=None) -> list:
    """Add item to list, creating new list if needed."""
    if items is None:
        items = []
    items.append(item)
    return items

# Modern way with type hints
from typing import Optional

def process_data(data: list, prefix: Optional[str] = None) -> list:
    """Process data with optional prefix."""
    if prefix is None:
        prefix = "default_"
    return [f"{prefix}{item}" for item in data]
```

## Idiom 10: Walrus Operator (Python 3.8+)

**Use for:** Assignment within expressions

```python
# Read lines until empty line
with open('data.txt') as f:
    while (line := f.readline().strip()):
        process(line)

# List comprehension with assignment
data = [1, 2, 3, 4, 5]
squares = [y for x in data if (y := x ** 2) > 10]  # [16, 25]

# Pattern matching in conditions
if (n := len(items)) > 10:
    print(f"Too many items: {n}")
```

## Idiom 11: String Formatting

**Use for:** Creating formatted strings

```python
# f-strings (preferred, Python 3.6+)
name = "Alice"
age = 25
message = f"{name} is {age} years old"

# Expressions in f-strings
print(f"Next year: {age + 1}")

# Format specifications
pi = 3.14159
print(f"Pi to 2 decimals: {pi:.2f}")  # 3.14

# .format() method (Python 3.0+)
message = "{} is {} years old".format(name, age)
message = "{name} is {age} years old".format(name=name, age=age)
```

## Idiom 12: Property Decorators

**Use for:** Computed attributes, validation

```python
class Circle:
    def __init__(self, radius: float):
        self._radius = radius
    
    @property
    def radius(self) -> float:
        """Get radius."""
        return self._radius
    
    @radius.setter
    def radius(self, value: float) -> None:
        """Set radius with validation."""
        if value < 0:
            raise ValueError("Radius must be non-negative")
        self._radius = value
    
    @property
    def area(self) -> float:
        """Calculate area (computed property)."""
        import math
        return math.pi * self._radius ** 2

# Usage
circle = Circle(5)
print(circle.area)  # Computed automatically
circle.radius = 10  # Uses setter (validates)
```

## Idiom 13: Dataclasses (Python 3.7+)

**Use for:** Simple data containers

```python
from dataclasses import dataclass, field
from typing import List

@dataclass
class Person:
    name: str
    age: int
    email: str = ""
    tags: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate after initialization."""
        if self.age < 0:
            raise ValueError("Age must be non-negative")

# Usage
person = Person("Alice", 25, "alice@example.com")
print(person)  # Auto-generated __repr__
```

## Idiom 14: Slice Operations

**Use for:** Extracting parts of sequences

```python
items = [0, 1, 2, 3, 4, 5]

# Basic slicing
first_three = items[:3]      # [0, 1, 2]
last_two = items[-2:]        # [4, 5]
middle = items[2:4]          # [2, 3]

# Step slicing
every_other = items[::2]     # [0, 2, 4]
reversed_list = items[::-1]  # [5, 4, 3, 2, 1, 0]

# String slicing
text = "Hello, World!"
first_word = text[:5]        # "Hello"
last_word = text[-6:-1]      # "World"
```

## Idiom 15: Any() and All()

**Use for:** Checking conditions on sequences

```python
numbers = [2, 4, 6, 8, 10]

# Check if any item is true
has_odd = any(n % 2 == 1 for n in numbers)  # False

# Check if all items are true
all_even = all(n % 2 == 0 for n in numbers)  # True

# Practical example
passwords = ["weak", "strong123!", "ok"]
has_strong = any(len(p) >= 8 and any(c.isupper() for c in p) for p in passwords)
```

## Best Practices Summary

1. **Prefer comprehensions** - More readable than loops for simple operations
2. **Use generators** - For memory efficiency with large sequences
3. **Use enumerate()** - Don't use `range(len())` when you need indices
4. **Use zip()** - For iterating over multiple sequences
5. **Use context managers** - Always use `with` for resource management
6. **Use f-strings** - Preferred string formatting method
7. **Use None pattern** - For optional mutable default arguments
8. **Use property decorators** - For computed attributes and validation
9. **Use dataclasses** - For simple data containers
10. **Use any()/all()** - For checking conditions on sequences

## Anti-Patterns to Avoid

❌ **Using range(len()) instead of enumerate():**
```python
for i in range(len(items)):  # Not Pythonic
    print(i, items[i])
```

✅ **Use enumerate():**
```python
for i, item in enumerate(items):  # Pythonic
    print(i, item)
```

❌ **Mutable default arguments:**
```python
def func(items=[]):  # BUG!
    ...
```

✅ **Use None pattern:**
```python
def func(items=None):
    if items is None:
        items = []
    ...
```

❌ **String concatenation in loops:**
```python
result = ""
for item in items:
    result += str(item)  # Inefficient
```

✅ **Use join() or f-strings:**
```python
result = "".join(str(item) for item in items)
# or
result = f"{items}"
```

