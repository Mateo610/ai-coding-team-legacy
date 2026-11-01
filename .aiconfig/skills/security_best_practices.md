# Security Best Practices

Critical security patterns to prevent vulnerabilities in your code.

## Principle 1: Input Validation

**Always validate and sanitize inputs from external sources.**

```python
import re
from typing import Any

def validate_email(email: str) -> str:
    """
    Validate and sanitize email address.
    
    Args:
        email: Email address to validate
    
    Returns:
        Sanitized email address
    
    Raises:
        ValueError: If email is invalid
    """
    if not isinstance(email, str):
        raise TypeError("Email must be a string")
    
    # Sanitize: strip whitespace, convert to lowercase
    email = email.strip().lower()
    
    # Validate format
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise ValueError(f"Invalid email format: {email}")
    
    # Check length limits (prevent DoS)
    if len(email) > 254:  # RFC 5321 limit
        raise ValueError("Email address too long")
    
    return email
```

**Key Points:**
- Validate type first
- Sanitize input (strip, normalize)
- Check format with regex
- Enforce length limits
- Never trust user input

## Principle 2: Never Use eval() or exec()

**These functions are extremely dangerous. NEVER use them with user input.**

```python
# ❌ NEVER DO THIS
user_input = input("Enter expression: ")
result = eval(user_input)  # SECURITY VULNERABILITY!

# ❌ ALSO DANGEROUS
code = input("Enter code: ")
exec(code)  # SECURITY VULNERABILITY!

# ✅ Safe alternatives
import operator
import ast

# For simple arithmetic (if absolutely needed)
operators = {
    '+': operator.add,
    '-': operator.sub,
    '*': operator.mul,
    '/': operator.truediv
}

def safe_calculate(a: float, op: str, b: float) -> float:
    """Safe calculation without eval()."""
    if op not in operators:
        raise ValueError(f"Invalid operator: {op}")
    if op == '/' and b == 0:
        raise ValueError("Division by zero")
    return operators[op](a, b)

# Use ast.literal_eval() for safe literal evaluation ONLY
import ast
safe_result = ast.literal_eval('[1, 2, 3]')  # OK for literals
# But still validate the input first!
```

## Principle 3: SQL Injection Prevention

**Use parameterized queries, never string concatenation.**

```python
# ❌ VULNERABLE: SQL Injection
def get_user_unsafe(username: str) -> dict:
    query = f"SELECT * FROM users WHERE username = '{username}'"
    # If username = "admin' OR '1'='1", this breaks!
    return execute_query(query)

# ✅ SAFE: Parameterized queries
def get_user_safe(username: str) -> dict:
    query = "SELECT * FROM users WHERE username = ?"
    return execute_query(query, (username,))

# Using database libraries properly
import sqlite3

def get_user_db(username: str) -> dict:
    """Safe database query with parameterization."""
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Parameterized query (safe)
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    
    conn.close()
    return result
```

## Principle 4: Path Traversal Prevention

**Validate and sanitize file paths to prevent directory traversal attacks.**

```python
from pathlib import Path
import os

# ❌ VULNERABLE: Path traversal
def read_file_unsafe(filename: str) -> str:
    filepath = f"/data/{filename}"
    # If filename = "../../etc/passwd", this reads system files!
    with open(filepath, 'r') as f:
        return f.read()

# ✅ SAFE: Path validation
def read_file_safe(filename: str, base_dir: Path = Path("/data")) -> str:
    """
    Safely read file with path validation.
    
    Args:
        filename: Filename to read
        base_dir: Base directory (default: /data)
    
    Returns:
        File contents
    
    Raises:
        ValueError: If path is invalid or outside base_dir
    """
    # Validate filename
    if not filename or '/' in filename or '\\' in filename:
        raise ValueError(f"Invalid filename: {filename}")
    
    # Build path and resolve (prevents .. traversal)
    filepath = (base_dir / filename).resolve()
    
    # Ensure file is within base directory
    try:
        filepath.relative_to(base_dir.resolve())
    except ValueError:
        raise ValueError(f"Path outside base directory: {filename}")
    
    # Check if file exists
    if not filepath.is_file():
        raise FileNotFoundError(f"File not found: {filename}")
    
    with open(filepath, 'r') as f:
        return f.read()
```

## Principle 5: Password Handling

**Never store passwords in plain text. Always use hashing.**

```python
import hashlib
import secrets

# ❌ NEVER: Store plain text passwords
def create_user_bad(username: str, password: str):
    db[username] = password  # INSECURE!

# ✅ CORRECT: Hash passwords
import hashlib
import secrets

def hash_password(password: str) -> tuple[str, str]:
    """
    Hash password with salt using secure method.
    
    Args:
        password: Plain text password
    
    Returns:
        Tuple of (hashed_password, salt)
    """
    # Generate random salt
    salt = secrets.token_hex(16)
    
    # Hash password with salt
    password_bytes = password.encode('utf-8')
    salt_bytes = salt.encode('utf-8')
    
    # Use SHA-256 (or bcrypt/argon2 for production)
    hasher = hashlib.sha256()
    hasher.update(password_bytes + salt_bytes)
    hashed = hasher.hexdigest()
    
    return hashed, salt

def verify_password(password: str, hashed: str, salt: str) -> bool:
    """
    Verify password against stored hash.
    
    Args:
        password: Plain text password to verify
        hashed: Stored hash
        salt: Stored salt
    
    Returns:
        True if password matches, False otherwise
    """
    password_bytes = password.encode('utf-8')
    salt_bytes = salt.encode('utf-8')
    
    hasher = hashlib.sha256()
    hasher.update(password_bytes + salt_bytes)
    computed_hash = hasher.hexdigest()
    
    return secrets.compare_digest(computed_hash, hashed)  # Constant-time comparison
```

**For Production:** Use `bcrypt` or `argon2` library:
```python
import bcrypt

def hash_password_bcrypt(password: str) -> str:
    """Hash password using bcrypt (recommended for production)."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password_bcrypt(password: str, hashed: str) -> bool:
    """Verify password using bcrypt."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
```

## Principle 6: Environment Variables for Secrets

**Never hardcode secrets. Use environment variables.**

```python
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ❌ NEVER: Hardcode secrets
API_KEY = "sk-1234567890abcdef"  # INSECURE!

# ✅ CORRECT: Use environment variables
API_KEY = os.getenv('API_KEY')
if not API_KEY:
    raise ValueError("API_KEY environment variable not set")

# For database credentials
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///default.db')

# For sensitive config
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("SECRET_KEY must be set in environment")

# Generate secret if not set (development only)
if not SECRET_KEY and os.getenv('ENV') == 'development':
    import secrets
    SECRET_KEY = secrets.token_hex(32)
    print("WARNING: Generated temporary SECRET_KEY for development")
```

## Principle 7: HTTPS and Secure Connections

**Always use HTTPS for external API calls. Verify SSL certificates.**

```python
import requests

# ✅ CORRECT: Verify SSL certificates (default)
def api_call_safe(url: str, data: dict) -> dict:
    """Make API call with SSL verification."""
    response = requests.post(
        url,
        json=data,
        verify=True,  # Verify SSL certificates
        timeout=10    # Set timeout
    )
    response.raise_for_status()  # Raise exception for bad status codes
    return response.json()

# ❌ INSECURE: Disabling SSL verification (only for testing!)
response = requests.post(url, verify=False)  # NEVER in production!

# For self-signed certificates (development only)
if os.getenv('ENV') == 'development':
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
```

## Principle 8: Rate Limiting

**Implement rate limiting to prevent abuse and DoS attacks.**

```python
from collections import defaultdict
from datetime import datetime, timedelta
import time

class RateLimiter:
    """Simple rate limiter to prevent abuse."""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)
    
    def is_allowed(self, identifier: str) -> bool:
        """
        Check if request is allowed.
        
        Args:
            identifier: Unique identifier (IP, user ID, etc.)
        
        Returns:
            True if allowed, False if rate limited
        """
        now = datetime.now()
        window_start = now - timedelta(seconds=self.window_seconds)
        
        # Clean old requests
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if req_time > window_start
        ]
        
        # Check limit
        if len(self.requests[identifier]) >= self.max_requests:
            return False
        
        # Record request
        self.requests[identifier].append(now)
        return True

# Usage
limiter = RateLimiter(max_requests=10, window_seconds=60)

def api_endpoint(request):
    client_ip = request.remote_addr
    if not limiter.is_allowed(client_ip):
        raise RateLimitError("Too many requests")
    # Process request...
```

## Principle 9: Output Encoding

**Encode output properly to prevent XSS attacks in web applications.**

```python
import html
import json

# ✅ SAFE: HTML escaping
def render_html(user_input: str) -> str:
    """Safely render user input in HTML."""
    # Escape HTML special characters
    safe_input = html.escape(user_input)
    return f"<p>{safe_input}</p>"

# ✅ SAFE: JSON encoding
def api_response(data: dict) -> str:
    """Safely encode JSON response."""
    return json.dumps(data)  # json.dumps automatically escapes

# For URL encoding
from urllib.parse import quote

def build_url(base: str, params: dict) -> str:
    """Build URL with safe parameter encoding."""
    query_string = "&".join(
        f"{quote(str(k))}={quote(str(v))}"
        for k, v in params.items()
    )
    return f"{base}?{query_string}"
```

## Principle 10: Logging Security

**Never log sensitive information (passwords, tokens, secrets).**

```python
import logging

logger = logging.getLogger(__name__)

# ❌ INSECURE: Logging passwords
def login_user(username: str, password: str):
    logger.info(f"Login attempt: {username}, password={password}")  # NEVER!

# ✅ SECURE: Sanitize logs
def login_user_safe(username: str, password: str):
    logger.info(f"Login attempt: username={username}")
    # Never log passwords, tokens, or secrets
    
# ✅ SECURE: Redact sensitive data
def log_data_safe(data: dict):
    """Log data with sensitive fields redacted."""
    sensitive_fields = {'password', 'token', 'api_key', 'secret', 'ssn'}
    safe_data = {
        k: '***REDACTED***' if k.lower() in sensitive_fields else v
        for k, v in data.items()
    }
    logger.info(f"Data: {safe_data}")
```

## Principle 11: Command Injection Prevention

**Never execute shell commands with user input. Use proper APIs instead.**

```python
import subprocess
import shlex

# ❌ VULNERABLE: Command injection
def process_file_unsafe(filename: str):
    command = f"cat {filename}"  # If filename = "; rm -rf /", this is dangerous!
    subprocess.run(command, shell=True)

# ✅ SAFE: Use subprocess properly
def process_file_safe(filename: str):
    """Safely process file without command injection."""
    # Validate filename
    if not filename or '/' in filename or '\\' in filename:
        raise ValueError(f"Invalid filename: {filename}")
    
    # Use subprocess without shell=True and with list of arguments
    subprocess.run(['cat', filename], check=True)

# Better: Use Python file operations
def process_file_python(filename: str) -> str:
    """Process file using Python (safest)."""
    with open(filename, 'r') as f:
        return f.read()
```

## Security Checklist

When writing code, ask yourself:

- [ ] Are all inputs validated?
- [ ] Are file paths sanitized?
- [ ] Are SQL queries parameterized?
- [ ] Are passwords hashed (never plain text)?
- [ ] Are secrets stored in environment variables?
- [ ] Is HTTPS used for external connections?
- [ ] Is rate limiting implemented?
- [ ] Is output properly encoded?
- [ ] Are sensitive values excluded from logs?
- [ ] Are shell commands avoided or properly sanitized?
- [ ] Is eval() or exec() never used with user input?

## Common Vulnerabilities to Avoid

1. **SQL Injection** - Use parameterized queries
2. **XSS (Cross-Site Scripting)** - Encode output
3. **Command Injection** - Don't use shell commands with user input
4. **Path Traversal** - Validate and sanitize file paths
5. **Authentication Bypass** - Proper password hashing and validation
6. **Information Disclosure** - Don't log sensitive data
7. **Insecure Deserialization** - Validate and sanitize input
8. **Insufficient Logging** - Log security events (but not secrets)

## Best Practices Summary

1. **Validate all inputs** - Never trust user input
2. **Use parameterized queries** - Prevent SQL injection
3. **Hash passwords** - Never store plain text
4. **Use environment variables** - For secrets and config
5. **Enable HTTPS** - For all external communications
6. **Implement rate limiting** - Prevent abuse
7. **Encode output** - Prevent XSS
8. **Sanitize logs** - Never log secrets
9. **Avoid eval/exec** - Never execute user code
10. **Use proper APIs** - Instead of shell commands

