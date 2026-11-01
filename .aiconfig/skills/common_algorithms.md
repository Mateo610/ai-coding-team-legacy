# Common Algorithms and Data Structure Patterns

Essential algorithms and patterns every Python developer should know.

## Sorting Algorithms

### Built-in Sorting (Preferred)

```python
# List sorting (in-place)
numbers = [3, 1, 4, 1, 5, 9, 2, 6]
numbers.sort()  # [1, 1, 2, 3, 4, 5, 6, 9]

# Sort with key function
words = ['apple', 'pie', 'banana', 'cake']
words.sort(key=len)  # ['pie', 'cake', 'apple', 'banana']

# Sort in reverse
numbers.sort(reverse=True)

# Sorted function (creates new list)
sorted_numbers = sorted([3, 1, 4, 1, 5])
sorted_by_length = sorted(words, key=len)
```

### Custom Sorting

```python
# Sort objects by attribute
class Person:
    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age

people = [Person("Alice", 25), Person("Bob", 30), Person("Charlie", 20)]
people.sort(key=lambda p: p.age)  # Sort by age

# Sort by multiple criteria
people.sort(key=lambda p: (p.age, p.name))  # Age first, then name
```

## Searching Patterns

### Linear Search

```python
def linear_search(items: list, target: Any) -> int:
    """
    Find index of target in items using linear search.
    
    Args:
        items: List to search
        target: Item to find
    
    Returns:
        Index of target, or -1 if not found
    """
    for i, item in enumerate(items):
        if item == target:
            return i
    return -1
```

### Binary Search (for sorted lists)

```python
from typing import Any

def binary_search(items: list, target: Any) -> int:
    """
    Find index of target in sorted list using binary search.
    
    Args:
        items: Sorted list to search
        target: Item to find
    
    Returns:
        Index of target, or -1 if not found
    """
    left, right = 0, len(items) - 1
    
    while left <= right:
        mid = (left + right) // 2
        if items[mid] == target:
            return mid
        elif items[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    
    return -1

# Or use bisect module
import bisect
sorted_list = [1, 3, 5, 7, 9]
index = bisect.bisect_left(sorted_list, 5)  # Returns 2
```

## Counting and Frequency Patterns

### Count Occurrences

```python
from collections import Counter

# Using Counter (most Pythonic)
items = ['a', 'b', 'a', 'c', 'b', 'a']
counts = Counter(items)  # Counter({'a': 3, 'b': 2, 'c': 1})
most_common = counts.most_common(2)  # [('a', 3), ('b', 2)]

# Manual counting
counts = {}
for item in items:
    counts[item] = counts.get(item, 0) + 1

# Using defaultdict
from collections import defaultdict
counts = defaultdict(int)
for item in items:
    counts[item] += 1
```

## Grouping Patterns

### Group by Category

```python
from collections import defaultdict

# Group items by category
items = [('apple', 'fruit'), ('carrot', 'vegetable'), ('banana', 'fruit')]
grouped = defaultdict(list)
for item, category in items:
    grouped[category].append(item)
# grouped = {'fruit': ['apple', 'banana'], 'vegetable': ['carrot']}

# Using itertools.groupby (requires sorted input)
from itertools import groupby
sorted_items = sorted(items, key=lambda x: x[1])
for category, group in groupby(sorted_items, key=lambda x: x[1]):
    items_in_category = [item[0] for item in group]
    print(f"{category}: {items_in_category}")
```

## Dictionary Patterns

### Default Values

```python
from collections import defaultdict

# Set default for missing keys
data = defaultdict(int)  # Default is 0
data['count'] += 1

# Custom default factory
data = defaultdict(list)  # Default is []
data['items'].append('apple')

# Using dict.get()
value = my_dict.get('key', 'default_value')
```

### Dictionary Merging

```python
# Python 3.5+
dict1 = {'a': 1, 'b': 2}
dict2 = {'c': 3, 'd': 4}
merged = {**dict1, **dict2}  # {'a': 1, 'b': 2, 'c': 3, 'd': 4}

# Python 3.9+
merged = dict1 | dict2  # Same result

# Update in place
dict1.update(dict2)
```

## Set Operations

```python
set1 = {1, 2, 3, 4}
set2 = {3, 4, 5, 6}

# Union
union = set1 | set2  # {1, 2, 3, 4, 5, 6}

# Intersection
intersection = set1 & set2  # {3, 4}

# Difference
difference = set1 - set2  # {1, 2}

# Symmetric difference (elements in either set, but not both)
symmetric_diff = set1 ^ set2  # {1, 2, 5, 6}

# Check subset/superset
is_subset = {1, 2} <= set1  # True
is_superset = set1 >= {1, 2}  # True
```

## String Algorithms

### String Reversal

```python
text = "hello"
reversed_text = text[::-1]  # "olleh"

# Or using reversed()
reversed_text = "".join(reversed(text))
```

### Palindrome Check

```python
def is_palindrome(text: str) -> bool:
    """Check if string is palindrome."""
    text = text.lower().replace(" ", "")
    return text == text[::-1]
```

### Anagrams

```python
from collections import Counter

def are_anagrams(str1: str, str2: str) -> bool:
    """Check if two strings are anagrams."""
    return Counter(str1.lower()) == Counter(str2.lower())
```

## Mathematical Patterns

### GCD and LCM

```python
import math

# Greatest Common Divisor
gcd_value = math.gcd(48, 18)  # 6

# Least Common Multiple (Python 3.9+)
lcm_value = math.lcm(12, 8)  # 24

# Manual LCM if needed
def lcm(a: int, b: int) -> int:
    """Calculate LCM of two numbers."""
    return abs(a * b) // math.gcd(a, b)
```

### Factorial

```python
import math

# Built-in
fact = math.factorial(5)  # 120

# Manual (recursive)
def factorial(n: int) -> int:
    """Calculate factorial recursively."""
    if n < 0:
        raise ValueError("Factorial not defined for negative numbers")
    if n <= 1:
        return 1
    return n * factorial(n - 1)

# Manual (iterative - preferred for performance)
def factorial_iterative(n: int) -> int:
    """Calculate factorial iteratively."""
    if n < 0:
        raise ValueError("Factorial not defined for negative numbers")
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result
```

## Array/List Patterns

### Sliding Window

```python
def max_sum_window(arr: list, window_size: int) -> int:
    """
    Find maximum sum of any contiguous subarray of size window_size.
    
    Args:
        arr: Array of numbers
        window_size: Size of window
    
    Returns:
        Maximum sum
    """
    if len(arr) < window_size:
        return sum(arr)
    
    # Calculate sum of first window
    window_sum = sum(arr[:window_size])
    max_sum = window_sum
    
    # Slide window
    for i in range(window_size, len(arr)):
        window_sum = window_sum - arr[i - window_size] + arr[i]
        max_sum = max(max_sum, window_sum)
    
    return max_sum
```

### Two Pointers

```python
def find_pair_sum(arr: list, target: int) -> tuple:
    """
    Find two numbers that sum to target in sorted array.
    
    Args:
        arr: Sorted array
        target: Target sum
    
    Returns:
        Tuple of (index1, index2) or None if not found
    """
    left, right = 0, len(arr) - 1
    
    while left < right:
        current_sum = arr[left] + arr[right]
        if current_sum == target:
            return (left, right)
        elif current_sum < target:
            left += 1
        else:
            right -= 1
    
    return None
```

## Best Practices Summary

1. **Use built-in functions** - `sorted()`, `max()`, `min()`, `sum()` are optimized
2. **Use Counter** - For frequency counting
3. **Use defaultdict** - For grouping and default values
4. **Use set operations** - For set-related problems
5. **Prefer iterative** - Over recursive for performance
6. **Use generators** - For memory efficiency with large sequences
7. **Know time complexity** - Choose appropriate algorithm

## Time Complexity Reference

- **O(1)**: Dictionary lookup, set operations
- **O(log n)**: Binary search
- **O(n)**: Linear search, single loop
- **O(n log n)**: Sorting (most efficient sorts)
- **O(n²)**: Nested loops
- **O(2^n)**: Exponential (avoid if possible)

