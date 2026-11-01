# Pandas Data Analysis Patterns

Expert guidance for efficient data manipulation and analysis with pandas.

## Core Pandas Principles

### 1. Reading Data

Read data efficiently:

```python
import pandas as pd
from typing import Optional, Union
from pathlib import Path

# Read CSV
def read_csv_file(filepath: Union[str, Path], **kwargs) -> pd.DataFrame:
    """
    Read CSV file with error handling.
    
    Args:
        filepath: Path to CSV file
        **kwargs: Additional arguments for pd.read_csv
    
    Returns:
        DataFrame
    
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format is invalid
    """
    filepath = Path(filepath)
    
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    
    try:
        df = pd.read_csv(
            filepath,
            dtype=str,  # Read all as string initially for flexibility
            na_values=['', 'NA', 'N/A', 'NULL'],
            **kwargs
        )
        return df
    except Exception as e:
        raise ValueError(f"Failed to read CSV file: {str(e)}")

# Read Excel
def read_excel_file(filepath: Union[str, Path], sheet_name: Optional[str] = None) -> pd.DataFrame:
    """Read Excel file."""
    return pd.read_excel(filepath, sheet_name=sheet_name, engine='openpyxl')

# Read JSON
def read_json_file(filepath: Union[str, Path]) -> pd.DataFrame:
    """Read JSON file."""
    return pd.read_json(filepath, orient='records')
```

### 2. Data Cleaning

Clean data properly:

```python
from typing import List, Optional

def clean_dataframe(df: pd.DataFrame, 
                   drop_na: bool = False,
                   fill_na: Optional[dict] = None,
                   remove_duplicates: bool = False) -> pd.DataFrame:
    """
    Clean DataFrame.
    
    Args:
        df: Input DataFrame
        drop_na: Drop rows with NaN values
        fill_na: Dictionary mapping columns to fill values
        remove_duplicates: Remove duplicate rows
    
    Returns:
        Cleaned DataFrame
    """
    df = df.copy()
    
    # Remove duplicates
    if remove_duplicates:
        df = df.drop_duplicates()
    
    # Fill NaN values
    if fill_na:
        for column, value in fill_na.items():
            if column in df.columns:
                df[column] = df[column].fillna(value)
    
    # Drop NaN rows
    if drop_na:
        df = df.dropna()
    
    return df

def convert_types(df: pd.DataFrame, type_map: dict) -> pd.DataFrame:
    """
    Convert column types.
    
    Args:
        df: Input DataFrame
        type_map: Dictionary mapping column names to types
    
    Returns:
        DataFrame with converted types
    """
    df = df.copy()
    
    for column, dtype in type_map.items():
        if column in df.columns:
            try:
                df[column] = df[column].astype(dtype)
            except (ValueError, TypeError) as e:
                print(f"Warning: Failed to convert {column} to {dtype}: {e}")
    
    return df
```

### 3. Data Filtering

Filter data efficiently:

```python
def filter_dataframe(df: pd.DataFrame, 
                    filters: dict) -> pd.DataFrame:
    """
    Filter DataFrame with multiple conditions.
    
    Args:
        df: Input DataFrame
        filters: Dictionary of filter conditions
                 Example: {'age': ('>', 18), 'status': ('==', 'active')}
    
    Returns:
        Filtered DataFrame
    """
    mask = pd.Series([True] * len(df))
    
    for column, (operator, value) in filters.items():
        if column not in df.columns:
            continue
        
        if operator == '==':
            mask &= (df[column] == value)
        elif operator == '!=':
            mask &= (df[column] != value)
        elif operator == '>':
            mask &= (df[column] > value)
        elif operator == '>=':
            mask &= (df[column] >= value)
        elif operator == '<':
            mask &= (df[column] < value)
        elif operator == '<=':
            mask &= (df[column] <= value)
        elif operator == 'in':
            mask &= df[column].isin(value)
        elif operator == 'contains':
            mask &= df[column].str.contains(value, na=False)
    
    return df[mask]
```

### 4. Data Aggregation

Perform aggregations efficiently:

```python
from typing import Dict, List, Optional

def aggregate_data(df: pd.DataFrame,
                  group_by: List[str],
                  agg_dict: Dict[str, List[str]]) -> pd.DataFrame:
    """
    Aggregate data by groups.
    
    Args:
        df: Input DataFrame
        group_by: List of columns to group by
        agg_dict: Dictionary mapping columns to aggregation functions
                  Example: {'age': ['mean', 'max'], 'salary': ['sum']}
    
    Returns:
        Aggregated DataFrame
    """
    return df.groupby(group_by).agg(agg_dict).reset_index()

def pivot_table(df: pd.DataFrame,
               index: str,
               columns: str,
               values: str,
               aggfunc: str = 'mean') -> pd.DataFrame:
    """
    Create pivot table.
    
    Args:
        df: Input DataFrame
        index: Column to use as index
        columns: Column to use as columns
        values: Column to aggregate
        aggfunc: Aggregation function
    
    Returns:
        Pivot table
    """
    return pd.pivot_table(
        df,
        index=index,
        columns=columns,
        values=values,
        aggfunc=aggfunc
    )
```

### 5. Data Transformation

Transform data efficiently:

```python
def apply_transformations(df: pd.DataFrame,
                         transformations: List[dict]) -> pd.DataFrame:
    """
    Apply multiple transformations to DataFrame.
    
    Args:
        df: Input DataFrame
        transformations: List of transformation dictionaries
                        Example: [
                            {'type': 'rename', 'columns': {'old': 'new'}},
                            {'type': 'drop', 'columns': ['col1', 'col2']},
                            {'type': 'sort', 'by': 'column', 'ascending': True}
                        ]
    
    Returns:
        Transformed DataFrame
    """
    df = df.copy()
    
    for transform in transformations:
        transform_type = transform['type']
        
        if transform_type == 'rename':
            df = df.rename(columns=transform.get('columns', {}))
        
        elif transform_type == 'drop':
            columns = transform.get('columns', [])
            df = df.drop(columns=columns, errors='ignore')
        
        elif transform_type == 'sort':
            df = df.sort_values(
                by=transform['by'],
                ascending=transform.get('ascending', True)
            )
        
        elif transform_type == 'drop_duplicates':
            df = df.drop_duplicates(subset=transform.get('subset'))
        
        elif transform_type == 'fillna':
            df = df.fillna(transform.get('value'))
    
    return df
```

### 6. Performance Optimization

Optimize pandas operations:

```python
def optimize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Optimize DataFrame memory usage.
    
    Args:
        df: Input DataFrame
    
    Returns:
        Optimized DataFrame
    """
    df = df.copy()
    
    # Downcast numeric types
    for col in df.select_dtypes(include=['int64']).columns:
        df[col] = pd.to_numeric(df[col], downcast='integer')
    
    for col in df.select_dtypes(include=['float64']).columns:
        df[col] = pd.to_numeric(df[col], downcast='float')
    
    # Convert object columns to category if appropriate
    for col in df.select_dtypes(include=['object']).columns:
        if df[col].nunique() < len(df) * 0.5:  # If less than 50% unique values
            df[col] = df[col].astype('category')
    
    return df

# Use vectorized operations
def process_data_vectorized(df: pd.DataFrame) -> pd.DataFrame:
    """Use vectorized operations for better performance."""
    # Good: Vectorized operation
    df['total'] = df['price'] * df['quantity']
    
    # Bad: Loop (slow)
    # for i in range(len(df)):
    #     df.loc[i, 'total'] = df.loc[i, 'price'] * df.loc[i, 'quantity']
    
    return df
```

### 7. Data Validation

Validate data:

```python
def validate_dataframe(df: pd.DataFrame,
                      required_columns: List[str],
                      validations: Optional[dict] = None) -> tuple[bool, List[str]]:
    """
    Validate DataFrame structure and data.
    
    Args:
        df: Input DataFrame
        required_columns: List of required columns
        validations: Dictionary of validation rules
                    Example: {'age': ('>', 0, '<', 150)}
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Check required columns
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        errors.append(f"Missing required columns: {missing_columns}")
    
    # Apply validations
    if validations:
        for column, rules in validations.items():
            if column not in df.columns:
                continue
            
            # Simple range validation example
            if isinstance(rules, tuple) and len(rules) == 4:
                op1, val1, op2, val2 = rules
                if op1 == '>' and op2 == '<':
                    invalid = df[(df[column] <= val1) | (df[column] >= val2)]
                    if len(invalid) > 0:
                        errors.append(f"{column} has {len(invalid)} values outside range ({val1}, {val2})")
    
    return len(errors) == 0, errors
```

### 8. Best Practices Checklist

When using pandas:

- ✅ Use vectorized operations instead of loops
- ✅ Optimize data types to reduce memory
- ✅ Handle missing data explicitly
- ✅ Use appropriate methods (loc, iloc, at, iat)
- ✅ Avoid chained assignments
- ✅ Copy DataFrames when needed
- ✅ Use categorical types for repeated strings
- ✅ Read only necessary columns from files
- ✅ Use query() for complex filtering
- ✅ Leverage groupby for aggregations
- ✅ Use merge/join instead of loops
- ✅ Validate data before processing
- ✅ Handle errors gracefully
- ✅ Document data transformations

## Common Patterns

### Pattern 1: Data Pipeline

```python
def process_data_pipeline(filepath: str) -> pd.DataFrame:
    """Complete data processing pipeline."""
    # Read
    df = read_csv_file(filepath)
    
    # Clean
    df = clean_dataframe(df, remove_duplicates=True)
    
    # Transform
    df = convert_types(df, {'age': int, 'salary': float})
    df = df[df['age'] > 0]  # Filter invalid ages
    
    # Aggregate
    df = df.groupby('department').agg({
        'salary': 'mean',
        'age': 'mean'
    }).reset_index()
    
    # Optimize
    df = optimize_dataframe(df)
    
    return df
```

### Pattern 2: Time Series Operations

```python
def process_time_series(df: pd.DataFrame, date_column: str) -> pd.DataFrame:
    """Process time series data."""
    # Convert to datetime
    df[date_column] = pd.to_datetime(df[date_column])
    
    # Set as index
    df = df.set_index(date_column)
    
    # Resample
    df_resampled = df.resample('D').mean()  # Daily average
    
    # Rolling window
    df['rolling_mean'] = df['value'].rolling(window=7).mean()
    
    return df
```

Remember: Pandas is powerful but can be slow with large datasets - optimize operations and use appropriate methods for your data size.

