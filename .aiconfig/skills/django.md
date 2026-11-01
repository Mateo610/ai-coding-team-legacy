# Django Web Framework Patterns

Expert guidance for building production-quality Django applications.

## Core Django Principles

### 1. Project Structure

Organize Django projects properly:

```
project_name/
├── manage.py
├── project_name/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── users/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   ├── admin.py
│   │   └── tests.py
│   └── api/
└── requirements.txt
```

### 2. Models

Write proper Django models with validation:

```python
from django.db import models
from django.core.validators import MinLengthValidator, EmailValidator
from django.contrib.auth.models import AbstractUser
from typing import Optional
from datetime import datetime

class User(models.Model):
    """
    User model.
    
    Fields:
        username: Unique username (3-50 chars)
        email: Unique email address
        age: Optional age (0-150)
        created_at: Creation timestamp
    """
    username = models.CharField(
        max_length=50,
        unique=True,
        validators=[MinLengthValidator(3)],
        help_text="Username must be 3-50 characters"
    )
    email = models.EmailField(
        unique=True,
        validators=[EmailValidator()],
        help_text="Valid email address"
    )
    age = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[models.MinValueValidator(0), models.MaxValueValidator(150)],
        help_text="Age between 0 and 150"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['username']),
            models.Index(fields=['email']),
        ]
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self) -> str:
        return f'{self.username} ({self.email})'
    
    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'age': self.age,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
```

### 3. Views

Write clean, maintainable views:

```python
from django.shortcuts import get_object_or_404
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.core.paginator import Paginator
from typing import Dict, Any
import json

# Function-based views
@require_http_methods(["GET"])
def get_user(request, user_id: int) -> JsonResponse:
    """
    Get user by ID.
    
    Args:
        request: HTTP request
        user_id: User identifier
    
    Returns:
        JSON response with user data
    """
    try:
        user = get_object_or_404(User, id=user_id)
        return JsonResponse({
            'success': True,
            'data': user.to_dict()
        })
    except Http404:
        return JsonResponse({
            'success': False,
            'error': f'User with ID {user_id} not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)

# Class-based views
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

class UserListView(ListView):
    """List view for users with pagination."""
    model = User
    template_name = 'users/list.html'
    context_object_name = 'users'
    paginate_by = 10
    
    def get_queryset(self):
        """Filter queryset based on query parameters."""
        queryset = User.objects.all()
        
        # Filter by username
        username = self.request.GET.get('username')
        if username:
            queryset = queryset.filter(username__icontains=username)
        
        # Filter by email
        email = self.request.GET.get('email')
        if email:
            queryset = queryset.filter(email__icontains=email)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        """Add pagination context."""
        context = super().get_context_data(**kwargs)
        context['total'] = self.get_queryset().count()
        return context

# API views with Django REST Framework
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for user operations.
    
    list: Get all users
    create: Create new user
    retrieve: Get user by ID
    update: Update user (full)
    partial_update: Update user (partial)
    destroy: Delete user
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter queryset based on query parameters."""
        queryset = User.objects.all()
        
        username = self.request.query_params.get('username')
        if username:
            queryset = queryset.filter(username__icontains=username)
        
        email = self.request.query_params.get('email')
        if email:
            queryset = queryset.filter(email__icontains=email)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate user."""
        user = self.get_object()
        user.is_active = True
        user.save()
        return Response({'status': 'User activated'})
```

### 4. Serializers

Use Django REST Framework serializers:

```python
from rest_framework import serializers
from django.contrib.auth.models import User
from typing import Dict, Any

class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'age', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'username': {'min_length': 3, 'max_length': 50},
            'email': {'required': True},
            'age': {'required': False, 'allow_null': True}
        }
    
    def validate_username(self, value: str) -> str:
        """Validate username."""
        if not value.replace('_', '').replace('-', '').isalnum():
            raise serializers.ValidationError(
                'Username must be alphanumeric (underscores/hyphens allowed)'
            )
        return value
    
    def validate_age(self, value: Optional[int]) -> Optional[int]:
        """Validate age."""
        if value is not None and (value < 0 or value > 150):
            raise serializers.ValidationError('Age must be between 0 and 150')
        return value
    
    def create(self, validated_data: Dict[str, Any]) -> User:
        """Create user."""
        # Check for duplicates
        if User.objects.filter(username=validated_data['username']).exists():
            raise serializers.ValidationError({'username': 'Username already exists'})
        
        if User.objects.filter(email=validated_data['email']).exists():
            raise serializers.ValidationError({'email': 'Email already exists'})
        
        return User.objects.create(**validated_data)
```

### 5. URLs

Organize URLs properly:

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'users'

# For viewsets
router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')

urlpatterns = [
    path('api/v1/', include(router.urls)),
    
    # Function-based views
    path('users/<int:user_id>/', views.get_user, name='user-detail'),
    
    # Class-based views
    path('users/', views.UserListView.as_view(), name='user-list'),
]
```

### 6. Admin

Configure Django admin properly:

```python
from django.contrib import admin
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Admin configuration for User model."""
    list_display = ['id', 'username', 'email', 'age', 'created_at']
    list_filter = ['created_at', 'age']
    search_fields = ['username', 'email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('username', 'email')
        }),
        ('Additional Info', {
            'fields': ('age',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
```

### 7. Testing

Write comprehensive tests:

```python
from django.test import TestCase, Client
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

class UserAPITestCase(APITestCase):
    """Test cases for User API."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'age': 25
        }
    
    def test_create_user(self):
        """Test user creation."""
        url = reverse('user-list')
        response = self.client.post(url, self.user_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().username, 'testuser')
    
    def test_get_user(self):
        """Test getting user."""
        user = User.objects.create(**self.user_data)
        url = reverse('user-detail', args=[user.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
    
    def test_update_user(self):
        """Test updating user."""
        user = User.objects.create(**self.user_data)
        url = reverse('user-detail', args=[user.id])
        update_data = {'age': 30}
        response = self.client.patch(url, update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(User.objects.get(id=user.id).age, 30)
```

### 8. Settings

Configure Django settings properly:

```python
# settings/base.py
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'apps.users',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'mydb'),
        'USER': os.environ.get('DB_USER', 'user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'password'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}
```

### 9. Best Practices Checklist

When building Django applications:

- ✅ Use apps to organize functionality
- ✅ Write proper models with validation
- ✅ Use class-based views when appropriate
- ✅ Use Django REST Framework for APIs
- ✅ Implement proper error handling
- ✅ Use database migrations
- ✅ Write comprehensive tests
- ✅ Use environment-based configuration
- ✅ Implement authentication properly
- ✅ Use pagination for list views
- ✅ Add proper logging
- ✅ Use Django admin effectively
- ✅ Follow Django conventions
- ✅ Optimize database queries

## Common Patterns

### Pattern 1: Query Optimization

```python
from django.db.models import Prefetch, Count

# Use select_related for ForeignKey
users = User.objects.select_related('profile').all()

# Use prefetch_related for ManyToMany or reverse ForeignKey
users = User.objects.prefetch_related('posts').all()

# Use annotate for aggregations
users = User.objects.annotate(post_count=Count('posts'))
```

### Pattern 2: Custom Manager

```python
from django.db import models

class UserManager(models.Manager):
    """Custom manager for User model."""
    def active(self):
        """Return only active users."""
        return self.filter(is_active=True)
    
    def by_age_range(self, min_age: int, max_age: int):
        """Return users in age range."""
        return self.filter(age__gte=min_age, age__lte=max_age)

class User(models.Model):
    # ... fields ...
    objects = UserManager()
```

Remember: Django is "the web framework for perfectionists with deadlines" - use its conventions and patterns for efficient development.

