"""
Application configuration
"""

import os
from pathlib import Path


class Config:
    """Base configuration"""
    # Get SECRET_KEY from environment (no default for security)
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        # Only use dev default if explicitly in development
        import os
        if os.getenv('AI_TEAM_ENV', 'development') == 'development':
            SECRET_KEY = 'dev-secret-key-change-in-production'
        else:
            raise ValueError("SECRET_KEY must be set in production environment")
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    DATA_DIR = Path(os.getenv('DATA_DIR', './data'))


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
