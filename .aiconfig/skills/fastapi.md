# FastAPI Web Framework Patterns

Expert guidance for building production-quality FastAPI applications with type safety and async support.

## Core FastAPI Principles

### 1. Type Safety & Pydantic Models

Use Pydantic models for request/response validation:

```python
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    """Schema for creating a user."""
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    email: EmailStr = Field(..., description="Valid email address")
    age: Optional[int] = Field(None, ge=0, le=150, description="User age")
    
    @validator('username')
    def username_alphanumeric(cls, v):
        """Validate username is alphanumeric."""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username must be alphanumeric (underscores/hyphens allowed)')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "username": "johndoe",
                "email": "john@example.com",
                "age": 30
            }
        }

class UserResponse(BaseModel):
    """Schema for user response."""
    id: int
    username: str
    email: str
    age: Optional[int]
    created_at: datetime
    
    class Config:
        orm_mode = True  # For SQLAlchemy models
```

### 2. Route Definitions

Define routes with proper typing and dependency injection:

```python
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from typing import List, Optional
from sqlalchemy.orm import Session

app = FastAPI(
    title="User API",
    description="API for user management",
    version="1.0.0"
)

@app.post("/users", 
          response_model=UserResponse,
          status_code=status.HTTP_201_CREATED,
          summary="Create a new user",
          tags=["users"])
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
) -> UserResponse:
    """
    Create a new user.
    
    - **username**: Must be unique, 3-50 characters, alphanumeric
    - **email**: Must be valid email format
    - **age**: Optional, must be between 0 and 150
    """
    # Check if username exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Username '{user_data.username}' already exists"
        )
    
    # Check if email exists
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Email '{user_data.email}' already exists"
        )
    
    # Create user
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        age=user_data.age
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@app.get("/users/{user_id}",
         response_model=UserResponse,
         summary="Get user by ID",
         tags=["users"])
async def get_user(
    user_id: int = Path(..., gt=0, description="User ID"),
    db: Session = Depends(get_db)
) -> UserResponse:
    """
    Get user by ID.
    
    - **user_id**: Must be positive integer
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    return user

@app.get("/users",
         response_model=List[UserResponse],
         summary="Get all users",
         tags=["users"])
async def get_users(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
) -> List[UserResponse]:
    """
    Get all users with pagination.
    
    - **skip**: Number of records to skip (default: 0)
    - **limit**: Maximum number of records (default: 10, max: 100)
    """
    users = db.query(User).offset(skip).limit(limit).all()
    return users
```

### 3. Dependency Injection

Use dependencies for database sessions, authentication, etc.:

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Generator
from database import SessionLocal

# Database dependency
def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency.
    
    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Authentication dependency
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user.
    
    Args:
        token: OAuth2 token
        db: Database session
    
    Returns:
        Current user
    
    Raises:
        HTTPException: If token is invalid
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    
    return user

# Protected route example
@app.get("/users/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """Get current authenticated user's information."""
    return current_user
```

### 4. Error Handling

Implement comprehensive error handling:

```python
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

app = FastAPI()

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": "Validation error",
            "details": exc.errors()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    # Log error
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "Internal server error",
            "message": "An unexpected error occurred"
        }
    )
```

### 5. Async Database Operations

Use async database operations properly:

```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator

# Async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    future=True
)

# Async session
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session."""
    async with AsyncSessionLocal() as session:
        yield session

@app.get("/users/{user_id}")
async def get_user_async(
    user_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """Get user using async database session."""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )
    
    return user
```

### 6. Response Models & Status Codes

Use proper response models and status codes:

```python
from fastapi import status
from fastapi.responses import JSONResponse
from typing import Generic, TypeVar, Optional

T = TypeVar('T')

class APIResponse(BaseModel, Generic[T]):
    """Standard API response wrapper."""
    success: bool
    data: Optional[T] = None
    message: Optional[str] = None
    error: Optional[str] = None

@app.post("/users",
          response_model=APIResponse[UserResponse],
          status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreate) -> APIResponse[UserResponse]:
    """Create user with proper response format."""
    user = create_user_in_db(user_data)
    
    return APIResponse(
        success=True,
        data=user,
        message="User created successfully"
    )
```

### 7. Query Parameters & Pagination

Implement proper query parameters and pagination:

```python
from fastapi import Query
from typing import Optional

class PaginationParams:
    """Pagination parameters."""
    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(10, ge=1, le=100, description="Items per page")
    ):
        self.page = page
        self.page_size = page_size
        self.skip = (page - 1) * page_size

@app.get("/users")
async def get_users(
    pagination: PaginationParams = Depends(),
    search: Optional[str] = Query(None, description="Search term"),
    db: Session = Depends(get_db)
):
    """Get users with pagination and search."""
    query = db.query(User)
    
    if search:
        query = query.filter(
            (User.username.contains(search)) |
            (User.email.contains(search))
        )
    
    total = query.count()
    users = query.offset(pagination.skip).limit(pagination.page_size).all()
    
    return {
        "success": True,
        "data": users,
        "pagination": {
            "page": pagination.page,
            "page_size": pagination.page_size,
            "total": total,
            "pages": (total + pagination.page_size - 1) // pagination.page_size
        }
    }
```

### 8. Testing

Write testable FastAPI code:

```python
from fastapi.testclient import TestClient
import pytest

@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)

def test_create_user(client: TestClient):
    """Test user creation."""
    response = client.post(
        "/users",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "age": 25
        }
    )
    
    assert response.status_code == 201
    assert response.json()["success"] is True
    assert response.json()["data"]["username"] == "testuser"

def test_get_user_not_found(client: TestClient):
    """Test getting non-existent user."""
    response = client.get("/users/99999")
    
    assert response.status_code == 404
    assert response.json()["error"] is not None
```

### 9. Best Practices Checklist

When building FastAPI applications:

- ✅ Use Pydantic models for validation
- ✅ Add comprehensive type hints
- ✅ Use dependency injection for database sessions
- ✅ Implement proper error handling
- ✅ Use appropriate HTTP status codes
- ✅ Add OpenAPI documentation
- ✅ Use async/await for I/O operations
- ✅ Implement authentication properly
- ✅ Add request/response models
- ✅ Use query parameters for filtering/pagination
- ✅ Write comprehensive docstrings
- ✅ Add input validation with validators
- ✅ Write tests for all endpoints
- ✅ Use environment variables for configuration

## Common Patterns

### Pattern 1: CRUD Operations

```python
# Create
@app.post("/users", status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create user."""
    db_user = User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Read
@app.get("/users/{user_id}")
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# Update
@app.put("/users/{user_id}")
async def update_user(user_id: int, user_data: UserUpdate, db: Session = Depends(get_db)):
    """Update user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    for key, value in user_data.dict(exclude_unset=True).items():
        setattr(user, key, value)
    
    db.commit()
    db.refresh(user)
    return user

# Delete
@app.delete("/users/{user_id}")
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Delete user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(user)
    db.commit()
    return {"success": True, "message": "User deleted"}
```

### Pattern 2: Background Tasks

```python
from fastapi import BackgroundTasks

@app.post("/users/{user_id}/send-email")
async def send_email(
    user_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Send email to user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    background_tasks.add_task(send_welcome_email, user.email)
    
    return {"success": True, "message": "Email queued for sending"}
```

Remember: FastAPI's strength is in type safety and async support - leverage these features for production-quality APIs.

