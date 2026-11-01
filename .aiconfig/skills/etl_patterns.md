# ETL (Extract, Transform, Load) Patterns

You are an expert data engineer specializing in building robust ETL pipelines for data processing, transformation, and validation.

## Core Principles

### 1. Extract Phase
- **Data Sources**: Handle multiple data sources (files, databases, APIs, streams)
- **Error Handling**: Gracefully handle missing files, connection failures, timeouts
- **Validation**: Validate source data formats and schemas before processing
- **Incremental Loading**: Support incremental/delta loading where possible

### 2. Transform Phase
- **Data Cleaning**: Remove duplicates, handle missing values, normalize formats
- **Type Conversion**: Convert data types appropriately (strings to dates, numbers, etc.)
- **Data Enrichment**: Join with reference data, calculate derived fields
- **Business Rules**: Apply business logic and transformations
- **Validation**: Validate transformed data meets quality standards

### 3. Load Phase
- **Idempotency**: Ensure pipeline can be rerun safely without duplicates
- **Error Handling**: Log failures, dead letter queues for bad data
- **Performance**: Batch inserts, bulk operations, parallel processing
- **Monitoring**: Track record counts, processing times, error rates

## Best Practices

### Data Validation
```python
def validate_data(data: List[Dict], schema: Dict) -> Tuple[List[Dict], List[str]]:
    """
    Validate data against schema, return valid records and errors.
    
    Args:
        data: List of records to validate
        schema: Schema definition with field types and constraints
    
    Returns:
        Tuple of (valid_records, error_messages)
    """
    valid = []
    errors = []
    
    for i, record in enumerate(data):
        record_errors = []
        valid_record = {}
        
        for field, field_schema in schema.items():
            value = record.get(field)
            
            # Type validation
            expected_type = field_schema.get('type')
            if value is not None and not isinstance(value, expected_type):
                record_errors.append(f"Field '{field}' expected {expected_type.__name__}, got {type(value).__name__}")
                continue
            
            # Required field validation
            if field_schema.get('required', False) and value is None:
                record_errors.append(f"Required field '{field}' is missing")
                continue
            
            # Constraint validation (min, max, pattern, etc.)
            if value is not None:
                if 'min' in field_schema and value < field_schema['min']:
                    record_errors.append(f"Field '{field}' value {value} below minimum {field_schema['min']}")
                if 'max' in field_schema and value > field_schema['max']:
                    record_errors.append(f"Field '{field}' value {value} above maximum {field_schema['max']}")
                if 'pattern' in field_schema:
                    import re
                    if not re.match(field_schema['pattern'], str(value)):
                        record_errors.append(f"Field '{field}' value doesn't match pattern")
            
            valid_record[field] = value
        
        if record_errors:
            errors.append(f"Record {i}: {', '.join(record_errors)}")
        else:
            valid.append(valid_record)
    
    return valid, errors
```

### Error Handling and Logging
```python
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class ETLError(Exception):
    """Base exception for ETL pipeline errors"""
    pass

def process_batch(data: List[Dict], batch_id: int) -> Dict[str, Any]:
    """
    Process a batch of data with comprehensive error handling.
    
    Returns:
        Dictionary with processing statistics
    """
    stats = {
        'total': len(data),
        'processed': 0,
        'failed': 0,
        'errors': []
    }
    
    for i, record in enumerate(data):
        try:
            # Transform record
            transformed = transform_record(record)
            
            # Validate transformed record
            if not validate_record(transformed):
                raise ValueError("Transformed record failed validation")
            
            # Load record
            load_record(transformed)
            
            stats['processed'] += 1
            
        except Exception as e:
            stats['failed'] += 1
            error_msg = f"Record {i} failed: {str(e)}"
            stats['errors'].append(error_msg)
            logger.error(error_msg, exc_info=True)
            
            # Send to dead letter queue or error log
            send_to_dead_letter_queue(record, str(e))
    
    logger.info(f"Batch {batch_id}: {stats['processed']}/{stats['total']} processed, {stats['failed']} failed")
    return stats
```

### Incremental Loading
```python
from datetime import datetime
from typing import Optional

def get_last_processed_timestamp(table: str) -> Optional[datetime]:
    """Get last processed timestamp from metadata table"""
    # Query metadata table for last processed timestamp
    pass

def load_incremental(source: str, target: str, timestamp_field: str = 'updated_at'):
    """
    Load only new or updated records since last run.
    
    Args:
        source: Source table/query
        target: Target table
        timestamp_field: Field to use for incremental loading
    """
    last_timestamp = get_last_processed_timestamp(target)
    
    if last_timestamp:
        query = f"SELECT * FROM {source} WHERE {timestamp_field} > '{last_timestamp}'"
    else:
        query = f"SELECT * FROM {source}"
    
    # Process incremental records
    new_records = execute_query(query)
    load_records(new_records, target)
    
    # Update metadata with current timestamp
    update_last_processed_timestamp(target, datetime.now())
```

### Data Transformation Patterns
```python
def clean_data(data: List[Dict]) -> List[Dict]:
    """
    Clean data: remove duplicates, handle missing values, normalize.
    
    Returns:
        Cleaned data
    """
    # Remove duplicates based on key field
    seen = set()
    deduplicated = []
    for record in data:
        key = record.get('id')
        if key and key not in seen:
            seen.add(key)
            deduplicated.append(record)
    
    # Handle missing values
    for record in deduplicated:
        for field in record:
            if record[field] is None or record[field] == '':
                # Use default value or skip field
                record[field] = None  # Or appropriate default
    
    return deduplicated

def transform_record(record: Dict) -> Dict:
    """
    Apply transformations to a single record.
    
    Returns:
        Transformed record
    """
    transformed = {}
    
    # Type conversions
    transformed['id'] = int(record.get('id', 0))
    transformed['created_at'] = parse_date(record.get('created_at'))
    transformed['amount'] = float(record.get('amount', 0))
    
    # Data normalization
    transformed['email'] = record.get('email', '').lower().strip()
    transformed['name'] = record.get('name', '').title()
    
    # Derived fields
    transformed['full_name'] = f"{record.get('first_name', '')} {record.get('last_name', '')}".strip()
    transformed['is_active'] = record.get('status', '').lower() == 'active'
    
    # Business logic
    if transformed['amount'] > 1000:
        transformed['tier'] = 'premium'
    else:
        transformed['tier'] = 'standard'
    
    return transformed
```

## Common ETL Tasks

### CSV Processing
```python
import csv
from typing import Iterator, Dict

def read_csv_file(filepath: str) -> Iterator[Dict]:
    """Read CSV file with error handling"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                yield row
    except FileNotFoundError:
        logger.error(f"File not found: {filepath}")
        raise
    except Exception as e:
        logger.error(f"Error reading CSV file {filepath}: {e}")
        raise

def process_csv_batch(filepath: str, batch_size: int = 1000) -> Dict[str, Any]:
    """Process CSV file in batches"""
    batch = []
    batch_num = 0
    stats = {'total': 0, 'processed': 0, 'failed': 0}
    
    for record in read_csv_file(filepath):
        batch.append(record)
        stats['total'] += 1
        
        if len(batch) >= batch_size:
            batch_stats = process_batch(batch, batch_num)
            stats['processed'] += batch_stats['processed']
            stats['failed'] += batch_stats['failed']
            batch = []
            batch_num += 1
    
    # Process remaining records
    if batch:
        batch_stats = process_batch(batch, batch_num)
        stats['processed'] += batch_stats['processed']
        stats['failed'] += batch_stats['failed']
    
    return stats
```

### Database ETL
```python
from sqlalchemy import create_engine, text
from typing import List, Dict

def extract_from_database(connection_string: str, query: str) -> List[Dict]:
    """Extract data from database"""
    engine = create_engine(connection_string)
    with engine.connect() as conn:
        result = conn.execute(text(query))
        return [dict(row) for row in result]

def load_to_database(records: List[Dict], target_table: str, connection_string: str):
    """Load records to database with batch insert"""
    engine = create_engine(connection_string)
    
    # Use bulk insert for performance
    with engine.connect() as conn:
        conn.execute(
            text(f"INSERT INTO {target_table} VALUES (...)"),
            records
        )
        conn.commit()
```

## Performance Optimization

### Parallel Processing
```python
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from typing import List, Dict

def process_in_parallel(data: List[Dict], num_workers: int = 4) -> List[Dict]:
    """Process data in parallel using thread pool"""
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        results = list(executor.map(transform_record, data))
    return results
```

### Batch Processing
```python
def process_in_batches(data: List[Dict], batch_size: int = 1000) -> Dict[str, Any]:
    """Process data in batches to manage memory"""
    total_batches = (len(data) + batch_size - 1) // batch_size
    all_stats = {'total': len(data), 'processed': 0, 'failed': 0}
    
    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        batch_num = i // batch_size + 1
        logger.info(f"Processing batch {batch_num}/{total_batches}")
        
        batch_stats = process_batch(batch, batch_num)
        all_stats['processed'] += batch_stats['processed']
        all_stats['failed'] += batch_stats['failed']
    
    return all_stats
```

## Quality Checklist

- ✅ All data sources validated before extraction
- ✅ Comprehensive error handling for each phase
- ✅ Data validation schema defined and enforced
- ✅ Transformations are idempotent and testable
- ✅ Load operations are idempotent (no duplicates on rerun)
- ✅ Logging for monitoring and debugging
- ✅ Dead letter queue for failed records
- ✅ Incremental loading where applicable
- ✅ Performance optimized (batching, parallel processing)
- ✅ Data quality metrics tracked

