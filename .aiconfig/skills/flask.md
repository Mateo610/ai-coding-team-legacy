# Flask Web Framework Patterns

Expert guidance for building production-quality Flask applications.

## Core Flask Principles

### 1. Application Factory Pattern

Always use application factory pattern for better testability and configuration:

```python
from flask import Flask
from config import Config

def create_app(config_class=Config):
    """
    Application factory function.
    
    Args:
        config_class: Configuration class to use
    
    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Register blueprints
    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Initialize extensions
    from app.extensions import db, migrate
    db.init_app(app)
    migrate.init_app(app, db)
    
    return app
```

### 2. Blueprint Organization

Organize routes using blueprints for modularity:

```python
from flask import Blueprint, jsonify, request
from typing import Dict, Any, Optional

bp = Blueprint('users', __name__)

@bp.route('/users', methods=['GET'])
def get_users() -> Dict[str, Any]:
    """
    Get all users.
    
    Returns:
        JSON response with users list
    """
    try:
        # Logic here
        users = get_all_users()
        return jsonify({
            'success': True,
            'data': users,
            'count': len(users)
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id: int) -> Dict[str, Any]:
    """
    Get user by ID.
    
    Args:
        user_id: User identifier
    
    Returns:
        JSON response with user data
    """
    if user_id <= 0:
        return jsonify({
            'success': False,
            'error': 'Invalid user ID'
        }), 400
    
    user = get_user_by_id(user_id)
    if not user:
        return jsonify({
            'success': False,
            'error': 'User not found'
        }), 404
    
    return jsonify({
        'success': True,
        'data': user
    }), 200
```

### 3. Request Validation

Always validate request data:

```python
from flask import request, jsonify
from typing import Dict, Any, Optional

def validate_user_data(data: Optional[Dict]) -> Tuple[bool, Optional[str], Optional[Dict]]:
    """
    Validate user creation data.
    
    Args:
        data: Request JSON data
    
    Returns:
        Tuple of (is_valid, error_message, validated_data)
    """
    if not data:
        return False, "Missing request body", None
    
    # Required fields
    required_fields = ['username', 'email']
    for field in required_fields:
        if field not in data or not data[field]:
            return False, f"Missing required field: {field}", None
    
    # Validate email format
    email = data.get('email', '')
    if '@' not in email:
        return False, "Invalid email format", None
    
    # Validate username
    username = data.get('username', '')
    if len(username) < 3:
        return False, "Username must be at least 3 characters", None
    
    validated_data = {
        'username': username.strip(),
        'email': email.strip().lower(),
        'age': data.get('age')  # Optional
    }
    
    return True, None, validated_data

@bp.route('/users', methods=['POST'])
def create_user() -> Dict[str, Any]:
    """Create a new user."""
    if not request.is_json:
        return jsonify({
            'success': False,
            'error': 'Content-Type must be application/json'
        }), 400
    
    is_valid, error, validated_data = validate_user_data(request.get_json())
    if not is_valid:
        return jsonify({
            'success': False,
            'error': error
        }), 400
    
    try:
        user = create_user_in_db(validated_data)
        return jsonify({
            'success': True,
            'data': user
        }), 201
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500
```

### 4. Error Handling

Implement comprehensive error handling:

```python
from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

def register_error_handlers(app: Flask):
    """Register error handlers for the application."""
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'success': False,
            'error': 'Bad request',
            'message': str(error)
        }), 400
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': 'Resource not found',
            'message': str(error)
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': 'An unexpected error occurred'
        }), 500
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        return jsonify({
            'success': False,
            'error': error.name,
            'message': str(error.description)
        }), error.code
```

### 5. Database Integration (SQLAlchemy)

Use Flask-SQLAlchemy properly:

```python
from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from typing import Optional
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    """User model."""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat()
        }
    
    def __repr__(self) -> str:
        return f'<User {self.username}>'

# Usage in route
@bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id: int):
    """Get user by ID."""
    user = User.query.get_or_404(user_id)
    return jsonify({
        'success': True,
        'data': user.to_dict()
    }), 200
```

### 6. Authentication & Authorization

Implement proper authentication:

```python
from functools import wraps
from flask import request, jsonify, g
from typing import Callable, Any

def token_required(f: Callable) -> Callable:
    """
    Decorator to require authentication token.
    
    Usage:
        @bp.route('/protected')
        @token_required
        def protected_route():
            # g.current_user is available
            return jsonify({'user': g.current_user.username})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]  # Bearer <token>
            except IndexError:
                return jsonify({
                    'success': False,
                    'error': 'Invalid token format'
                }), 401
        
        if not token:
            return jsonify({
                'success': False,
                'error': 'Token is missing'
            }), 401
        
        try:
            user = verify_token(token)
            if not user:
                return jsonify({
                    'success': False,
                    'error': 'Invalid or expired token'
                }), 401
            
            g.current_user = user
        except Exception as e:
            return jsonify({
                'success': False,
                'error': 'Token verification failed'
            }), 401
        
        return f(*args, **kwargs)
    
    return decorated_function
```

### 7. Response Formatting

Use consistent response format:

```python
from flask import jsonify
from typing import Any, Optional

def success_response(data: Any, status_code: int = 200, message: Optional[str] = None) -> tuple:
    """
    Create a success response.
    
    Args:
        data: Response data
        status_code: HTTP status code
        message: Optional message
    
    Returns:
        Tuple of (response, status_code)
    """
    response = {
        'success': True,
        'data': data
    }
    if message:
        response['message'] = message
    
    return jsonify(response), status_code

def error_response(error: str, status_code: int = 400, details: Optional[Dict] = None) -> tuple:
    """
    Create an error response.
    
    Args:
        error: Error message
        status_code: HTTP status code
        details: Optional error details
    
    Returns:
        Tuple of (response, status_code)
    """
    response = {
        'success': False,
        'error': error
    }
    if details:
        response['details'] = details
    
    return jsonify(response), status_code
```

### 8. Configuration Management

Use environment-based configuration:

```python
import os
from pathlib import Path

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_ECHO = True

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    SECRET_KEY = os.environ.get('SECRET_KEY')  # Must be set in production
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')  # Must be set

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
```

### 9. Testing Patterns

Write testable Flask code:

```python
import pytest
from flask import Flask
from your_app import create_app

@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app('testing')
    with app.app_context():
        yield app

@pytest.fixture
def client(app: Flask):
    """Create test client."""
    return app.test_client()

def test_create_user(client):
    """Test user creation."""
    response = client.post('/api/users', 
                          json={'username': 'testuser', 'email': 'test@example.com'},
                          content_type='application/json')
    
    assert response.status_code == 201
    assert response.json['success'] is True
    assert 'data' in response.json
```

### 10. Best Practices Checklist

When building Flask applications:

- ✅ Use application factory pattern
- ✅ Organize routes with blueprints
- ✅ Validate all request data
- ✅ Use consistent response format
- ✅ Implement proper error handling
- ✅ Use environment-based configuration
- ✅ Follow RESTful conventions
- ✅ Add type hints to functions
- ✅ Write comprehensive docstrings
- ✅ Use database migrations
- ✅ Implement authentication properly
- ✅ Add logging for important operations
- ✅ Write tests for all endpoints

## Common Patterns

### Pattern 1: Pagination

```python
@bp.route('/users', methods=['GET'])
def get_users():
    """Get paginated users."""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    
    pagination = User.query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    return jsonify({
        'success': True,
        'data': [user.to_dict() for user in pagination.items],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages
        }
    }), 200
```

### Pattern 2: Filtering & Sorting

```python
@bp.route('/users', methods=['GET'])
def get_users():
    """Get users with filtering and sorting."""
    query = User.query
    
    # Filter by username
    if 'username' in request.args:
        query = query.filter(User.username.contains(request.args['username']))
    
    # Sort
    sort_by = request.args.get('sort_by', 'id')
    order = request.args.get('order', 'asc')
    if hasattr(User, sort_by):
        if order == 'desc':
            query = query.order_by(getattr(User, sort_by).desc())
        else:
            query = query.order_by(getattr(User, sort_by))
    
    users = query.all()
    return jsonify({
        'success': True,
        'data': [user.to_dict() for user in users]
    }), 200
```

Remember: Flask is a microframework - keep it simple, but follow these patterns for production-quality applications.

