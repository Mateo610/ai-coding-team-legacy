# SQLAlchemy ORM Patterns

Expert guidance for building production-quality database code with SQLAlchemy.

## Core SQLAlchemy Principles

### 1. Model Definitions

Define models properly with relationships:

```python
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import func
from typing import Optional, List
from datetime import datetime

Base = declarative_base()

class User(Base):
    """
    User model.
    
    Attributes:
        id: Primary key
        username: Unique username
        email: Unique email address
        age: Optional age
        created_at: Creation timestamp
        posts: Related posts (one-to-many)
    """
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    age = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    posts = relationship("Post", back_populates="author", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}')>"
    
    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'age': self.age,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Post(Base):
    """Post model with foreign key relationship."""
    __tablename__ = 'posts'
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(String(5000), nullable=False)
    author_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Relationships
    author = relationship("User", back_populates="posts")
    
    def __repr__(self) -> str:
        return f"<Post(id={self.id}, title='{self.title[:50]}...')>"
```

### 2. Session Management

Use proper session management:

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator

# Create engine
engine = create_engine(
    'postgresql://user:password@localhost/dbname',
    echo=True,  # Log SQL queries (disable in production)
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True  # Verify connections before using
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@contextmanager
def get_db() -> Generator[Session, None, None]:
    """
    Database session context manager.
    
    Usage:
        with get_db() as db:
            users = db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

# For dependency injection (FastAPI)
def get_db_dependency() -> Generator[Session, None, None]:
    """Database session dependency for FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### 3. CRUD Operations

Implement CRUD operations properly:

```python
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional, List
from fastapi import HTTPException, status

# Create
def create_user(db: Session, username: str, email: str, age: Optional[int] = None) -> User:
    """
    Create a new user.
    
    Args:
        db: Database session
        username: Username
        email: Email address
        age: Optional age
    
    Returns:
        Created user
    
    Raises:
        HTTPException: If user already exists
    """
    # Check if username exists
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Username '{username}' already exists"
        )
    
    # Check if email exists
    existing_email = db.query(User).filter(User.email == email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Email '{email}' already exists"
        )
    
    # Create user
    db_user = User(username=username, email=email, age=age)
    db.add(db_user)
    
    try:
        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create user due to integrity constraint"
        )

# Read
def get_user(db: Session, user_id: int) -> Optional[User]:
    """Get user by ID."""
    return db.query(User).filter(User.id == user_id).first()

def get_users(db: Session, skip: int = 0, limit: int = 10) -> List[User]:
    """Get users with pagination."""
    return db.query(User).offset(skip).limit(limit).all()

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get user by username."""
    return db.query(User).filter(User.username == username).first()

# Update
def update_user(db: Session, user_id: int, **kwargs) -> Optional[User]:
    """
    Update user.
    
    Args:
        db: Database session
        user_id: User ID
        **kwargs: Fields to update
    
    Returns:
        Updated user or None
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None
    
    for key, value in kwargs.items():
        if hasattr(user, key) and value is not None:
            setattr(user, key, value)
    
    try:
        db.commit()
        db.refresh(user)
        return user
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update user due to integrity constraint"
        )

# Delete
def delete_user(db: Session, user_id: int) -> bool:
    """
    Delete user.
    
    Args:
        db: Database session
        user_id: User ID
    
    Returns:
        True if deleted, False if not found
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False
    
    db.delete(user)
    db.commit()
    return True
```

### 4. Query Patterns

Use efficient query patterns:

```python
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy import and_, or_, desc, asc

# Eager loading to avoid N+1 queries
def get_user_with_posts(db: Session, user_id: int) -> Optional[User]:
    """Get user with posts (eager loading)."""
    return db.query(User).options(joinedload(User.posts)).filter(User.id == user_id).first()

# Filtering
def search_users(db: Session, search_term: str) -> List[User]:
    """Search users by username or email."""
    return db.query(User).filter(
        or_(
            User.username.contains(search_term),
            User.email.contains(search_term)
        )
    ).all()

# Sorting
def get_users_sorted(db: Session, sort_by: str = 'created_at', order: str = 'desc') -> List[User]:
    """Get users with sorting."""
    query = db.query(User)
    
    if hasattr(User, sort_by):
        column = getattr(User, sort_by)
        if order == 'desc':
            query = query.order_by(desc(column))
        else:
            query = query.order_by(asc(column))
    
    return query.all()

# Aggregations
from sqlalchemy import func

def get_user_statistics(db: Session) -> dict:
    """Get user statistics."""
    total = db.query(func.count(User.id)).scalar()
    avg_age = db.query(func.avg(User.age)).scalar()
    oldest = db.query(func.max(User.age)).scalar()
    
    return {
        'total_users': total or 0,
        'average_age': float(avg_age) if avg_age else None,
        'oldest_age': int(oldest) if oldest else None
    }
```

### 5. Transactions

Use transactions properly:

```python
from sqlalchemy.orm import Session

def create_user_with_posts(db: Session, username: str, email: str, posts_data: List[dict]) -> User:
    """
    Create user with posts in a transaction.
    
    Args:
        db: Database session
        username: Username
        email: Email address
        posts_data: List of post data dictionaries
    
    Returns:
        Created user with posts
    """
    try:
        # Create user
        user = User(username=username, email=email)
        db.add(user)
        db.flush()  # Flush to get user.id
        
        # Create posts
        for post_data in posts_data:
            post = Post(
                title=post_data['title'],
                content=post_data['content'],
                author_id=user.id
            )
            db.add(post)
        
        db.commit()
        db.refresh(user)
        return user
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user with posts: {str(e)}"
        )
```

### 6. Relationships

Handle relationships properly:

```python
# One-to-Many (User -> Posts)
user = db.query(User).options(joinedload(User.posts)).filter(User.id == 1).first()
posts = user.posts  # Access related posts

# Many-to-One (Post -> User)
post = db.query(Post).options(joinedload(Post.author)).filter(Post.id == 1).first()
author = post.author  # Access author

# Many-to-Many (example)
class Tag(Base):
    __tablename__ = 'tags'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True)
    posts = relationship("Post", secondary=post_tags, back_populates="tags")

post_tags = Table(
    'post_tags',
    Base.metadata,
    Column('post_id', Integer, ForeignKey('posts.id')),
    Column('tag_id', Integer, ForeignKey('tags.id'))
)
```

### 7. Best Practices Checklist

When using SQLAlchemy:

- ✅ Use declarative_base for models
- ✅ Define proper relationships
- ✅ Use session context managers
- ✅ Handle transactions properly
- ✅ Use eager loading to avoid N+1 queries
- ✅ Use indexes for frequently queried columns
- ✅ Validate data before database operations
- ✅ Use proper error handling
- ✅ Close sessions properly
- ✅ Use connection pooling
- ✅ Enable query logging in development
- ✅ Use database migrations (Alembic)
- ✅ Test database operations
- ✅ Use type hints consistently

## Common Patterns

### Pattern 1: Pagination

```python
from sqlalchemy import func

def paginate_query(query, page: int = 1, per_page: int = 10):
    """Paginate query results."""
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    
    return {
        'items': items,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page
    }
```

### Pattern 2: Soft Deletes

```python
class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True)
    deleted_at = Column(DateTime, nullable=True)
    
    @property
    def is_deleted(self) -> bool:
        """Check if user is soft-deleted."""
        return self.deleted_at is not None
    
    def soft_delete(self):
        """Soft delete user."""
        from datetime import datetime
        self.deleted_at = datetime.utcnow()

# Filter out deleted records
def get_active_users(db: Session):
    """Get only active (non-deleted) users."""
    return db.query(User).filter(User.deleted_at.is_(None)).all()
```

Remember: SQLAlchemy provides powerful ORM features - use them wisely to write clean, maintainable database code.

