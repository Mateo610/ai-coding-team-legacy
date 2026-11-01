# Type Hints Patterns

Comprehensive type hinting patterns for Python code.

## Basic Type Hints

### Function Annotations

```python
# Basic types
def add(a: int, b: int) -> int:
    """Add two integers."""
    return a + b

def greet(name: str) -> str:
    """Return greeting message."""
    return f"Hello, {name}!"

def calculate_price(price: float, discount: float = 0.0) -> float:
    """Calculate price with discount."""
    return price * (1 - discount)
```

### Common Built-in Types

```python
from typing import Any, Optional, Union, List, Dict, Tuple, Set

# Optional (can be None)
def find_item(items: list, target: Any) -> Optional[int]:
    """Find item index, return None if not found."""
    try:
        return items.index(target)
    except ValueError:
        return None

# Union (multiple types)
def process_value(value: Union[int, str]) -> str:
    """Process integer or string value."""
    return str(value)

# List, Dict, Tuple, Set
def process_items(items: List[str]) -> List[int]:
    """Process list of strings, return list of lengths."""
    return [len(item) for item in items]

def build_mapping(keys: List[str], values: List[int]) -> Dict[str, int]:
    """Build dictionary from keys and values."""
    return dict(zip(keys, values))

def get_coordinates() -> Tuple[float, float]:
    """Return (x, y) coordinates."""
    return (10.5, 20.3)

def unique_items(items: List[str]) -> Set[str]:
    """Return unique items."""
    return set(items)
```

## Advanced Type Hints

### Generic Types

```python
from typing import TypeVar, Generic, Optional

# Type variables
T = TypeVar('T')

def get_first(items: List[T]) -> Optional[T]:
    """Get first item from list."""
    return items[0] if items else None

# Generic classes
class Stack(Generic[T]):
    """Generic stack implementation."""
    def __init__(self) -> None:
        self._items: List[T] = []
    
    def push(self, item: T) -> None:
        """Push item onto stack."""
        self._items.append(item)
    
    def pop(self) -> Optional[T]:
        """Pop item from stack."""
        return self._items.pop() if self._items else None
    
    def peek(self) -> Optional[T]:
        """Peek at top item."""
        return self._items[-1] if self._items else None
```

### Callable Types

```python
from typing import Callable, Optional

# Function as parameter
def apply_function(func: Callable[[int], int], value: int) -> int:
    """Apply function to value."""
    return func(value)

# More complex callable
def filter_items(
    items: List[str],
    predicate: Callable[[str], bool]
) -> List[str]:
    """Filter items using predicate function."""
    return [item for item in items if predicate(item)]

# Callable with multiple parameters
def combine(
    func: Callable[[int, int], int],
    a: int,
    b: int
) -> int:
    """Combine two values using function."""
    return func(a, b)

# Example usage
result = combine(lambda x, y: x + y, 5, 3)  # 8
```

### Protocol Types (Structural Typing)

```python
from typing import Protocol

class Readable(Protocol):
    """Protocol for objects that can be read."""
    def read(self) -> str:
        """Read content."""
        ...

class FileHandler:
    """File handler implementing Readable protocol."""
    def __init__(self, filepath: str):
        self.filepath = filepath
    
    def read(self) -> str:
        """Read file content."""
        with open(self.filepath, 'r') as f:
            return f.read()

def process_readable(obj: Readable) -> str:
    """Process any object that implements read() method."""
    return obj.read().upper()

# Works with any object that has read() method
file_handler = FileHandler("data.txt")
content = process_readable(file_handler)
```

## Collection Types

### List, Dict, Tuple Hints

```python
from typing import List, Dict, Tuple, Set, Optional

# Lists
def process_numbers(numbers: List[int]) -> List[float]:
    """Convert integers to floats."""
    return [float(n) for n in numbers]

# Dictionaries
def build_user_info(name: str, age: int, email: str) -> Dict[str, Union[str, int]]:
    """Build user information dictionary."""
    return {
        'name': name,
        'age': age,
        'email': email
    }

# Tuples
def get_person() -> Tuple[str, int, str]:
    """Return (name, age, email) tuple."""
    return ("Alice", 25, "alice@example.com")

# Named tuples (better than regular tuples)
from collections import namedtuple
from typing import NamedTuple

class Person(NamedTuple):
    """Person with named fields."""
    name: str
    age: int
    email: str

def get_person_named() -> Person:
    """Return Person named tuple."""
    return Person("Alice", 25, "alice@example.com")

# Sets
def get_unique_tags(items: List[Dict[str, List[str]]]) -> Set[str]:
    """Extract unique tags from items."""
    tags = set()
    for item in items:
        tags.update(item.get('tags', []))
    return tags
```

### Advanced Collections

```python
from typing import DefaultDict, OrderedDict, Counter
from collections import defaultdict, OrderedDict, Counter

def count_items(items: List[str]) -> Dict[str, int]:
    """Count item occurrences."""
    counts: DefaultDict[str, int] = defaultdict(int)
    for item in items:
        counts[item] += 1
    return dict(counts)
```

## Type Aliases

```python
from typing import List, Dict, Tuple

# Simple aliases
UserId = int
UserName = str
UserEmail = str

def get_user(user_id: UserId) -> Dict[str, Union[UserName, UserEmail]]:
    """Get user by ID."""
    ...

# Complex aliases
User = Dict[str, Union[str, int]]
UserList = List[User]

def get_all_users() -> UserList:
    """Get all users."""
    ...

# Better: Use TypedDict (Python 3.8+)
from typing import TypedDict

class UserDict(TypedDict):
    """Typed dictionary for user data."""
    name: str
    age: int
    email: str

def get_user_typed() -> UserDict:
    """Get user with typed dictionary."""
    return {
        'name': 'Alice',
        'age': 25,
        'email': 'alice@example.com'
    }
```

## Optional and Union

```python
from typing import Optional, Union

# Optional (shorthand for Union[T, None])
def find_index(items: List[str], target: str) -> Optional[int]:
    """Find index, return None if not found."""
    try:
        return items.index(target)
    except ValueError:
        return None

# Explicit Union with None
def get_value(key: str) -> Union[str, None]:
    """Get value, return None if not found."""
    ...

# Multiple types
def process_value(value: Union[int, str, float]) -> str:
    """Process different types."""
    return str(value)

# Python 3.10+: Use | instead of Union
def get_value_modern(key: str) -> str | None:  # Python 3.10+
    """Modern syntax for Optional."""
    ...

def process_value_modern(value: int | str | float) -> str:  # Python 3.10+
    """Modern syntax for Union."""
    ...
```

## Class Type Hints

```python
from typing import ClassVar, Optional

class User:
    """User class with type hints."""
    
    # Class variable
    count: ClassVar[int] = 0
    
    # Instance variables
    name: str
    age: int
    email: Optional[str] = None
    
    def __init__(self, name: str, age: int, email: Optional[str] = None) -> None:
        """Initialize user."""
        self.name = name
        self.age = age
        self.email = email
        User.count += 1
    
    def get_display_name(self) -> str:
        """Get display name."""
        return f"{self.name} ({self.age})"
    
    @classmethod
    def get_count(cls) -> int:
        """Get total user count."""
        return cls.count
```

## Type Hints with Defaults

```python
from typing import Optional, List

# Optional with default None
def get_config(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get configuration value."""
    ...

# List with default empty list (use None pattern!)
def process_items(items: Optional[List[str]] = None) -> List[str]:
    """Process items list."""
    if items is None:
        items = []
    return [item.upper() for item in items]

# Dict with default empty dict
def merge_dicts(
    dict1: Optional[Dict[str, int]] = None,
    dict2: Optional[Dict[str, int]] = None
) -> Dict[str, int]:
    """Merge two dictionaries."""
    if dict1 is None:
        dict1 = {}
    if dict2 is None:
        dict2 = {}
    return {**dict1, **dict2}
```

## Generators and Iterators

```python
from typing import Iterator, Generator, Iterable

# Generator function
def count_up_to(max: int) -> Generator[int, None, None]:
    """Count from 1 to max."""
    count = 1
    while count <= max:
        yield count
        count += 1

# Iterator
def squares(items: Iterable[int]) -> Iterator[int]:
    """Yield squares of items."""
    for item in items:
        yield item ** 2

# Generator with send/return
def accumulator() -> Generator[int, int, int]:
    """Accumulator that accepts values via send()."""
    total = 0
    while True:
        value = yield total
        if value is None:
            break
        total += value
    return total
```

## Type Checking Best Practices

```python
from typing import cast, Any

# Type narrowing with isinstance
def process_value(value: Union[int, str]) -> int:
    """Process value, return integer."""
    if isinstance(value, int):
        return value
    elif isinstance(value, str):
        return int(value)
    else:
        raise TypeError(f"Unexpected type: {type(value)}")

# Type casting (use carefully)
def get_first_item(items: List[Any]) -> int:
    """Get first item, cast to int."""
    if not items:
        raise ValueError("Empty list")
    return cast(int, items[0])

# Type guards
from typing import TypeGuard

def is_string_list(value: Any) -> TypeGuard[List[str]]:
    """Type guard to check if value is list of strings."""
    return isinstance(value, list) and all(isinstance(item, str) for item in value)

def process_strings(value: Any) -> List[str]:
    """Process value if it's a string list."""
    if is_string_list(value):
        return [s.upper() for s in value]  # Type checker knows value is List[str]
    raise TypeError("Expected list of strings")
```

## Best Practices Summary

1. **Always use type hints** - For function parameters and return types
2. **Use Optional** - For values that can be None
3. **Use Union** - For multiple allowed types
4. **Use List, Dict, Tuple** - For collections (not list, dict, tuple)
5. **Use TypedDict** - For dictionaries with known structure
6. **Use NamedTuple** - For structured data
7. **Use Generic types** - For reusable code
8. **Use Protocol** - For structural typing
9. **Document complex types** - With docstrings
10. **Run type checker** - Use mypy to verify types

## Common Patterns

```python
from typing import Optional, List, Dict, Callable

# Common pattern: Optional return
def find_item(items: List[str], target: str) -> Optional[int]:
    ...

# Common pattern: List of dictionaries
def process_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    ...

# Common pattern: Callback functions
def process_with_callback(
    items: List[str],
    callback: Callable[[str], str]
) -> List[str]:
    ...

# Common pattern: Default parameters
def create_user(
    name: str,
    age: int,
    tags: Optional[List[str]] = None
) -> Dict[str, Any]:
    if tags is None:
        tags = []
    ...
```

