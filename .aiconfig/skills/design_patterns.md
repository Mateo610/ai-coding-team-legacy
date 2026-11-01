# Design Patterns

Common design patterns for Python code organization and reusability.

## Pattern 1: Factory Pattern

**Use for:** Creating objects based on runtime conditions.

```python
from typing import Dict, Any, Protocol

class Shape(Protocol):
    """Shape protocol."""
    def area(self) -> float:
        """Calculate area."""
        ...
    
    def perimeter(self) -> float:
        """Calculate perimeter."""
        ...

class Circle:
    """Circle shape."""
    def __init__(self, radius: float):
        self.radius = radius
    
    def area(self) -> float:
        import math
        return math.pi * self.radius ** 2
    
    def perimeter(self) -> float:
        import math
        return 2 * math.pi * self.radius

class Rectangle:
    """Rectangle shape."""
    def __init__(self, width: float, height: float):
        self.width = width
        self.height = height
    
    def area(self) -> float:
        return self.width * self.height
    
    def perimeter(self) -> float:
        return 2 * (self.width + self.height)

# Factory function
def create_shape(shape_type: str, **kwargs) -> Shape:
    """
    Create shape based on type.
    
    Args:
        shape_type: Type of shape ('circle', 'rectangle')
        **kwargs: Shape-specific parameters
    
    Returns:
        Shape instance
    
    Raises:
        ValueError: If shape_type is invalid
    """
    shapes = {
        'circle': lambda: Circle(kwargs.get('radius', 1.0)),
        'rectangle': lambda: Rectangle(
            kwargs.get('width', 1.0),
            kwargs.get('height', 1.0)
        )
    }
    
    if shape_type not in shapes:
        raise ValueError(f"Unknown shape type: {shape_type}")
    
    return shapes[shape_type]()

# Usage
circle = create_shape('circle', radius=5.0)
rectangle = create_shape('rectangle', width=10.0, height=5.0)
```

## Pattern 2: Singleton Pattern

**Use for:** Ensuring only one instance of a class exists.

```python
class Singleton:
    """Singleton pattern implementation."""
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """Create or return existing instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize only once."""
        if not self._initialized:
            self.data = {}
            Singleton._initialized = True
    
    def set_data(self, key: str, value: Any) -> None:
        """Set data."""
        self.data[key] = value
    
    def get_data(self, key: str) -> Any:
        """Get data."""
        return self.data.get(key)

# Better: Use module-level instance (more Pythonic)
class Config:
    """Configuration singleton (module-level)."""
    def __init__(self):
        self.settings = {}

_config = None

def get_config() -> Config:
    """Get configuration instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config
```

## Pattern 3: Strategy Pattern

**Use for:** Selecting algorithms at runtime.

```python
from typing import Protocol, List

class SortStrategy(Protocol):
    """Sorting strategy protocol."""
    def sort(self, items: List[int]) -> List[int]:
        """Sort items."""
        ...

class BubbleSort:
    """Bubble sort implementation."""
    def sort(self, items: List[int]) -> List[int]:
        """Sort using bubble sort."""
        items = items.copy()
        n = len(items)
        for i in range(n):
            for j in range(0, n - i - 1):
                if items[j] > items[j + 1]:
                    items[j], items[j + 1] = items[j + 1], items[j]
        return items

class QuickSort:
    """Quick sort implementation."""
    def sort(self, items: List[int]) -> List[int]:
        """Sort using quick sort."""
        if len(items) <= 1:
            return items
        pivot = items[len(items) // 2]
        left = [x for x in items if x < pivot]
        middle = [x for x in items if x == pivot]
        right = [x for x in items if x > pivot]
        return self.sort(left) + middle + self.sort(right)

class Sorter:
    """Sorter with strategy pattern."""
    def __init__(self, strategy: SortStrategy):
        """
        Initialize sorter with strategy.
        
        Args:
            strategy: Sorting strategy to use
        """
        self.strategy = strategy
    
    def sort(self, items: List[int]) -> List[int]:
        """Sort items using current strategy."""
        return self.strategy.sort(items)
    
    def set_strategy(self, strategy: SortStrategy) -> None:
        """Change sorting strategy."""
        self.strategy = strategy

# Usage
sorter = Sorter(BubbleSort())
result = sorter.sort([3, 1, 4, 1, 5, 9, 2, 6])

sorter.set_strategy(QuickSort())
result = sorter.sort([3, 1, 4, 1, 5, 9, 2, 6])
```

## Pattern 4: Observer Pattern

**Use for:** Notifying multiple objects when state changes.

```python
from typing import Protocol, List, Any

class Observer(Protocol):
    """Observer protocol."""
    def update(self, data: Any) -> None:
        """Update with new data."""
        ...

class Subject:
    """Subject that notifies observers."""
    def __init__(self):
        self._observers: List[Observer] = []
        self._state = None
    
    def attach(self, observer: Observer) -> None:
        """Attach observer."""
        if observer not in self._observers:
            self._observers.append(observer)
    
    def detach(self, observer: Observer) -> None:
        """Detach observer."""
        if observer in self._observers:
            self._observers.remove(observer)
    
    def notify(self) -> None:
        """Notify all observers."""
        for observer in self._observers:
            observer.update(self._state)
    
    def set_state(self, state: Any) -> None:
        """Set state and notify observers."""
        self._state = state
        self.notify()

class Logger(Observer):
    """Observer that logs updates."""
    def update(self, data: Any) -> None:
        """Log update."""
        print(f"Logger: State changed to {data}")

class EmailNotifier(Observer):
    """Observer that sends email."""
    def update(self, data: Any) -> None:
        """Send email notification."""
        print(f"Email: Sending notification about {data}")

# Usage
subject = Subject()
subject.attach(Logger())
subject.attach(EmailNotifier())

subject.set_state("new_data")  # Both observers notified
```

## Pattern 5: Builder Pattern

**Use for:** Constructing complex objects step by step.

```python
from typing import Optional, List

class QueryBuilder:
    """SQL query builder."""
    def __init__(self):
        self._select: List[str] = []
        self._from_table: Optional[str] = None
        self._where: List[str] = []
        self._order_by: Optional[str] = None
    
    def select(self, *columns: str) -> 'QueryBuilder':
        """Add SELECT columns."""
        self._select.extend(columns)
        return self
    
    def from_table(self, table: str) -> 'QueryBuilder':
        """Set FROM table."""
        self._from_table = table
        return self
    
    def where(self, condition: str) -> 'QueryBuilder':
        """Add WHERE condition."""
        self._where.append(condition)
        return self
    
    def order_by(self, column: str) -> 'QueryBuilder':
        """Set ORDER BY column."""
        self._order_by = column
        return self
    
    def build(self) -> str:
        """Build SQL query."""
        if not self._select:
            raise ValueError("SELECT clause required")
        if not self._from_table:
            raise ValueError("FROM clause required")
        
        query = f"SELECT {', '.join(self._select)} FROM {self._from_table}"
        
        if self._where:
            query += f" WHERE {' AND '.join(self._where)}"
        
        if self._order_by:
            query += f" ORDER BY {self._order_by}"
        
        return query

# Usage
query = (QueryBuilder()
    .select('name', 'email')
    .from_table('users')
    .where('age > 18')
    .where('active = TRUE')
    .order_by('name')
    .build())
# "SELECT name, email FROM users WHERE age > 18 AND active = TRUE ORDER BY name"
```

## Pattern 6: Decorator Pattern

**Use for:** Adding functionality to objects dynamically.

```python
from typing import Protocol, Callable

class Component(Protocol):
    """Component protocol."""
    def operation(self) -> str:
        """Perform operation."""
        ...

class ConcreteComponent:
    """Concrete component."""
    def operation(self) -> str:
        """Base operation."""
        return "ConcreteComponent"

class Decorator:
    """Base decorator."""
    def __init__(self, component: Component):
        self._component = component
    
    def operation(self) -> str:
        """Delegate to component."""
        return self._component.operation()

class ConcreteDecoratorA(Decorator):
    """Concrete decorator A."""
    def operation(self) -> str:
        """Add behavior before and after."""
        return f"DecoratorA({self._component.operation()})"

class ConcreteDecoratorB(Decorator):
    """Concrete decorator B."""
    def operation(self) -> str:
        """Add behavior before and after."""
        return f"DecoratorB({self._component.operation()})"

# Usage
component = ConcreteComponent()
decorated = ConcreteDecoratorB(ConcreteDecoratorA(component))
result = decorated.operation()  # "DecoratorB(DecoratorA(ConcreteComponent))"
```

## Pattern 7: Template Method Pattern

**Use for:** Defining algorithm skeleton, letting subclasses fill steps.

```python
from typing import Protocol

class DataProcessor(Protocol):
    """Data processor template."""
    def read_data(self) -> str:
        """Read data (to be implemented by subclasses)."""
        ...
    
    def process_data(self, data: str) -> str:
        """Process data (to be implemented by subclasses)."""
        ...
    
    def save_data(self, data: str) -> None:
        """Save data (to be implemented by subclasses)."""
        ...
    
    def run(self) -> None:
        """Template method defining algorithm."""
        data = self.read_data()
        processed = self.process_data(data)
        self.save_data(processed)

class FileProcessor:
    """File-based data processor."""
    def __init__(self, input_file: str, output_file: str):
        self.input_file = input_file
        self.output_file = output_file
    
    def read_data(self) -> str:
        """Read from file."""
        with open(self.input_file, 'r') as f:
            return f.read()
    
    def process_data(self, data: str) -> str:
        """Process data."""
        return data.upper()
    
    def save_data(self, data: str) -> None:
        """Save to file."""
        with open(self.output_file, 'w') as f:
            f.write(data)
    
    def run(self) -> None:
        """Run file processing."""
        data = self.read_data()
        processed = self.process_data(data)
        self.save_data(processed)

# Usage
processor = FileProcessor('input.txt', 'output.txt')
processor.run()
```

## Pattern 8: Command Pattern

**Use for:** Encapsulating requests as objects.

```python
from typing import Protocol

class Command(Protocol):
    """Command protocol."""
    def execute(self) -> None:
        """Execute command."""
        ...
    
    def undo(self) -> None:
        """Undo command."""
        ...

class LightCommand:
    """Command to control light."""
    def __init__(self, light: 'Light'):
        self.light = light
        self.previous_state = False
    
    def execute(self) -> None:
        """Turn on light."""
        self.previous_state = self.light.is_on
        self.light.turn_on()
    
    def undo(self) -> None:
        """Restore previous state."""
        if self.previous_state:
            self.light.turn_on()
        else:
            self.light.turn_off()

class Light:
    """Light class."""
    def __init__(self):
        self.is_on = False
    
    def turn_on(self) -> None:
        self.is_on = True
    
    def turn_off(self) -> None:
        self.is_on = False

class RemoteControl:
    """Remote control with command pattern."""
    def __init__(self):
        self.command: Optional[Command] = None
        self.history: List[Command] = []
    
    def set_command(self, command: Command) -> None:
        """Set command."""
        self.command = command
    
    def press_button(self) -> None:
        """Execute command."""
        if self.command:
            self.command.execute()
            self.history.append(self.command)
    
    def undo(self) -> None:
        """Undo last command."""
        if self.history:
            last_command = self.history.pop()
            last_command.undo()

# Usage
light = Light()
command = LightCommand(light)
remote = RemoteControl()
remote.set_command(command)
remote.press_button()  # Light turns on
remote.undo()  # Light turns off
```

## Best Practices Summary

1. **Use Factory** - For object creation based on runtime conditions
2. **Use Singleton** - When only one instance is needed (use sparingly)
3. **Use Strategy** - For selecting algorithms at runtime
4. **Use Observer** - For notifying multiple objects of state changes
5. **Use Builder** - For constructing complex objects
6. **Use Decorator** - For adding functionality dynamically
7. **Use Template Method** - For defining algorithm skeleton
8. **Use Command** - For encapsulating requests as objects

## When to Use Patterns

- **Factory**: When object creation logic is complex or conditional
- **Singleton**: When exactly one instance is needed (be careful, can cause issues)
- **Strategy**: When multiple algorithms are interchangeable
- **Observer**: When multiple objects need to react to changes
- **Builder**: When constructing complex objects with many parameters
- **Decorator**: When adding features without subclassing
- **Template Method**: When algorithm structure is fixed but steps vary
- **Command**: When requests need to be queued, logged, or undone

