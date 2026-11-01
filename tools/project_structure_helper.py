"""
Project Structure Helper

Detects project type and generates appropriate folder structure and boilerplate files.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, field


class ProjectType(Enum):
    """Supported project types."""
    CLI = "cli"
    WEB_APP = "web_app"
    API = "api"
    LIBRARY = "library"
    SCRIPT = "script"
    UNKNOWN = "unknown"


@dataclass
class ProjectStructure:
    """Represents a project structure configuration."""
    project_type: ProjectType
    project_name: str
    directories: List[str] = field(default_factory=list)
    files: Dict[str, str] = field(default_factory=dict)
    description: str = ""


class ProjectStructureHelper:
    """Helper for generating project structures based on project type."""
    
    # Keywords for project type detection
    CLI_KEYWORDS = [
        'cli', 'command line', 'command-line', 'terminal', 'console',
        'script', 'tool', 'utility', 'command', 'interactive'
    ]
    
    WEB_APP_KEYWORDS = [
        'web app', 'webapp', 'web application', 'website', 'frontend',
        'browser', 'html', 'css', 'javascript', 'react', 'vue', 'angular',
        'django', 'flask', 'fastapi', 'web server'
    ]
    
    API_KEYWORDS = [
        'api', 'rest api', 'restful', 'endpoint', 'http server',
        'microservice', 'backend service', 'json api', 'graphql',
        'flask', 'fastapi', 'django rest', 'express'
    ]
    
    LIBRARY_KEYWORDS = [
        'library', 'module', 'package', 'sdk', 'framework',
        'reusable', 'distributable', 'pip install'
    ]
    
    def __init__(self):
        """Initialize the project structure helper."""
        pass
    
    def detect_project_type(self, task_description: str) -> ProjectType:
        """
        Detect project type from task description.
        
        Args:
            task_description: Description of the project/task
        
        Returns:
            Detected ProjectType
        """
        description_lower = task_description.lower()
        
        # Check for API keywords
        if any(keyword in description_lower for keyword in self.API_KEYWORDS):
            # If it mentions web app too, prefer API if it's clearly API-focused
            if 'rest' in description_lower or 'api' in description_lower:
                return ProjectType.API
        
        # Check for web app keywords
        if any(keyword in description_lower for keyword in self.WEB_APP_KEYWORDS):
            return ProjectType.WEB_APP
        
        # Check for library keywords
        if any(keyword in description_lower for keyword in self.LIBRARY_KEYWORDS):
            return ProjectType.LIBRARY
        
        # Check for CLI keywords
        if any(keyword in description_lower for keyword in self.CLI_KEYWORDS):
            return ProjectType.CLI
        
        # Default to script for simple tasks
        if 'function' in description_lower or 'calculate' in description_lower:
            return ProjectType.SCRIPT
        
        return ProjectType.UNKNOWN
    
    def extract_project_name(self, task_description: str, default: str = "project") -> str:
        """
        Extract project name from task description.
        
        Args:
            task_description: Description of the project/task
            default: Default name if none can be extracted
        
        Returns:
            Project name (sanitized)
        """
        # Try to find quoted name
        quoted_match = re.search(r'["\']([^"\']+)["\']', task_description)
        if quoted_match:
            name = quoted_match.group(1)
        else:
            # Try to find "called/named X"
            called_match = re.search(r'(?:called|named|for)\s+([a-zA-Z][a-zA-Z0-9_]*)', task_description, re.IGNORECASE)
            if called_match:
                name = called_match.group(1)
            else:
                # Try to find "create/build/make a/an/the X"
                create_match = re.search(r'(?:create|build|make|generate)\s+(?:a|an|the)?\s*([a-zA-Z][a-zA-Z0-9_]*)', task_description, re.IGNORECASE)
                if create_match:
                    name = create_match.group(1)
                else:
                    # Extract last meaningful word from task
                    words = [w for w in task_description.lower().split() if len(w) > 3]
                    if words:
                        # Skip common stop words
                        stop_words = {'create', 'build', 'make', 'generate', 'write', 'tool', 'app', 'api', 'application'}
                        meaningful_words = [w for w in words if w not in stop_words]
                        if meaningful_words:
                            name = meaningful_words[-1]  # Take last meaningful word
                        else:
                            name = words[-1]
                    else:
                        # Use default
                        name = default
        
        # Sanitize name
        name = re.sub(r'[^a-z0-9_]', '_', name.lower())
        name = re.sub(r'_+', '_', name).strip('_')
        
        return name or default
    
    def generate_structure(self, project_type: ProjectType, project_name: str) -> ProjectStructure:
        """
        Generate project structure for given type.
        
        Args:
            project_type: Type of project
            project_name: Name of the project
        
        Returns:
            ProjectStructure configuration
        """
        if project_type == ProjectType.CLI:
            return self._generate_cli_structure(project_name)
        elif project_type == ProjectType.WEB_APP:
            return self._generate_web_app_structure(project_name)
        elif project_type == ProjectType.API:
            return self._generate_api_structure(project_name)
        elif project_type == ProjectType.LIBRARY:
            return self._generate_library_structure(project_name)
        elif project_type == ProjectType.SCRIPT:
            return self._generate_script_structure(project_name)
        else:
            return self._generate_default_structure(project_name)
    
    def _generate_cli_structure(self, project_name: str) -> ProjectStructure:
        """Generate structure for CLI application."""
        return ProjectStructure(
            project_type=ProjectType.CLI,
            project_name=project_name,
            directories=[
                f"{project_name}",
                f"{project_name}/commands",
                "tests",
                "docs"
            ],
            files={
                "setup.py": self._generate_setup_py(project_name, "Command-line tool"),
                "README.md": self._generate_readme(project_name, "CLI", "Command-line interface application"),
                "requirements.txt": self._generate_requirements_txt(["click>=8.0.0"]),
                ".gitignore": self._generate_gitignore(),
                "pyproject.toml": self._generate_pyproject_toml(project_name),
                f"{project_name}/__init__.py": self._generate_init_py(),
                f"{project_name}/cli.py": self._generate_cli_main(project_name),
                f"{project_name}/commands/__init__.py": self._generate_init_py(),
                "tests/__init__.py": self._generate_init_py(),
                "tests/test_cli.py": self._generate_test_cli(project_name),
                ".env.example": self._generate_env_example(),
            },
            description="Command-line interface application"
        )
    
    def _generate_web_app_structure(self, project_name: str) -> ProjectStructure:
        """Generate structure for web application."""
        return ProjectStructure(
            project_type=ProjectType.WEB_APP,
            project_name=project_name,
            directories=[
                f"{project_name}",
                f"{project_name}/templates",
                f"{project_name}/static",
                f"{project_name}/static/css",
                f"{project_name}/static/js",
                f"{project_name}/static/images",
                "tests",
                "docs"
            ],
            files={
                "setup.py": self._generate_setup_py(project_name, "Web application"),
                "README.md": self._generate_readme(project_name, "Web App", "Web application"),
                "requirements.txt": self._generate_requirements_txt(["flask>=2.0.0", "gunicorn>=20.0.0"]),
                ".gitignore": self._generate_gitignore(),
                "pyproject.toml": self._generate_pyproject_toml(project_name),
                f"{project_name}/__init__.py": self._generate_init_py(),
                f"{project_name}/app.py": self._generate_flask_app(project_name),
                f"{project_name}/config.py": self._generate_config_py(),
                "tests/__init__.py": self._generate_init_py(),
                "tests/test_app.py": self._generate_test_web_app(project_name),
                ".env.example": self._generate_env_example(),
            },
            description="Web application with Flask"
        )
    
    def _generate_api_structure(self, project_name: str) -> ProjectStructure:
        """Generate structure for REST API."""
        return ProjectStructure(
            project_type=ProjectType.API,
            project_name=project_name,
            directories=[
                f"{project_name}",
                f"{project_name}/routes",
                f"{project_name}/models",
                f"{project_name}/services",
                "tests",
                "docs"
            ],
            files={
                "setup.py": self._generate_setup_py(project_name, "REST API"),
                "README.md": self._generate_readme(project_name, "API", "REST API service"),
                "requirements.txt": self._generate_requirements_txt(["fastapi>=0.100.0", "uvicorn>=0.23.0", "pydantic>=2.0.0"]),
                ".gitignore": self._generate_gitignore(),
                "pyproject.toml": self._generate_pyproject_toml(project_name),
                f"{project_name}/__init__.py": self._generate_init_py(),
                f"{project_name}/main.py": self._generate_fastapi_main(project_name),
                f"{project_name}/config.py": self._generate_config_py(),
                f"{project_name}/routes/__init__.py": self._generate_init_py(),
                f"{project_name}/models/__init__.py": self._generate_init_py(),
                f"{project_name}/services/__init__.py": self._generate_init_py(),
                "tests/__init__.py": self._generate_init_py(),
                "tests/test_api.py": self._generate_test_api(project_name),
                ".env.example": self._generate_env_example(),
            },
            description="REST API service with FastAPI"
        )
    
    def _generate_library_structure(self, project_name: str) -> ProjectStructure:
        """Generate structure for Python library."""
        return ProjectStructure(
            project_type=ProjectType.LIBRARY,
            project_name=project_name,
            directories=[
                f"{project_name}",
                "tests",
                "docs",
                "examples"
            ],
            files={
                "setup.py": self._generate_setup_py(project_name, "Python library"),
                "README.md": self._generate_readme(project_name, "Library", "Python library"),
                "requirements.txt": self._generate_requirements_txt([]),
                "requirements-dev.txt": self._generate_requirements_txt(["pytest>=7.0.0", "black>=23.0.0"]),
                ".gitignore": self._generate_gitignore(),
                "pyproject.toml": self._generate_pyproject_toml(project_name),
                f"{project_name}/__init__.py": self._generate_library_init(project_name),
                "tests/__init__.py": self._generate_init_py(),
                "tests/test_main.py": self._generate_test_library(project_name),
                "LICENSE": self._generate_license(),
            },
            description="Python library package"
        )
    
    def _generate_script_structure(self, project_name: str) -> ProjectStructure:
        """Generate structure for simple script."""
        return ProjectStructure(
            project_type=ProjectType.SCRIPT,
            project_name=project_name,
            directories=[],
            files={
                f"{project_name}.py": self._generate_script_file(project_name),
                "README.md": self._generate_readme(project_name, "Script", "Python script"),
                "requirements.txt": self._generate_requirements_txt([]),
                ".gitignore": self._generate_gitignore(),
            },
            description="Simple Python script"
        )
    
    def _generate_default_structure(self, project_name: str) -> ProjectStructure:
        """Generate default project structure."""
        return ProjectStructure(
            project_type=ProjectType.UNKNOWN,
            project_name=project_name,
            directories=[
                f"{project_name}",
                "tests"
            ],
            files={
                "README.md": self._generate_readme(project_name, "Project", "Python project"),
                "requirements.txt": self._generate_requirements_txt([]),
                ".gitignore": self._generate_gitignore(),
                f"{project_name}/__init__.py": self._generate_init_py(),
                "tests/__init__.py": self._generate_init_py(),
            },
            description="Default Python project structure"
        )
    
    # File generation methods
    
    def _generate_setup_py(self, project_name: str, description: str) -> str:
        """Generate setup.py content."""
        return f'''"""
Setup configuration for {project_name}
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="{project_name}",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="{description}",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/{project_name}",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
)
'''
    
    def _generate_readme(self, project_name: str, project_type: str, description: str) -> str:
        """Generate README.md content."""
        main_file = project_name.split("/")[-1]
        return f'''# {project_name}

{description}

## Description

A Python {project_type.lower()} project.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python {project_name}/{main_file}.py
```

## Development

```bash
# Run tests
pytest

# Format code
black .
```

## License

MIT License
'''
    
    def _generate_requirements_txt(self, packages: List[str]) -> str:
        """Generate requirements.txt content."""
        lines = packages.copy()
        lines.append("")
        return "\n".join(lines)
    
    def _generate_gitignore(self) -> str:
        """Generate .gitignore content."""
        return '''# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Environment variables
.env
.env.local

# Testing
.pytest_cache/
.coverage
htmlcov/

# Logs
*.log

# OS
.DS_Store
Thumbs.db
'''
    
    def _generate_pyproject_toml(self, project_name: str) -> str:
        """Generate pyproject.toml content."""
        return f'''[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "{project_name}"
version = "0.1.0"
description = "Python project"
requires-python = ">=3.8"
dependencies = []

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "black>=23.0.0",
    "flake8>=6.0.0",
]

[tool.black]
line-length = 100
target-version = ['py38']

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
'''
    
    def _generate_init_py(self) -> str:
        """Generate __init__.py content."""
        return '''"""
Package initialization
"""

__version__ = "0.1.0"
'''
    
    def _generate_cli_main(self, project_name: str) -> str:
        """Generate CLI main file."""
        return f'''"""
Command-line interface for {project_name}
"""

import click
from typing import Optional


@click.group()
def cli():
    """{project_name} - Command-line tool"""
    pass


@cli.command()
@click.option('--name', default='World', help='Name to greet')
def hello(name: str):
    """Simple greeting command"""
    click.echo(f'Hello, {{name}}!')


if __name__ == '__main__':
    cli()
'''
    
    def _generate_flask_app(self, project_name: str) -> str:
        """Generate Flask app file."""
        return f'''"""
Flask application for {project_name}
"""

from flask import Flask, render_template, jsonify

app = Flask(__name__)


@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')


@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({{'status': 'healthy'}})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
'''
    
    def _generate_fastapi_main(self, project_name: str) -> str:
        """Generate FastAPI main file."""
        return f'''"""
FastAPI application for {project_name}
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="{project_name}",
    description="REST API service",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {{"message": "Welcome to {project_name} API"}}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {{"status": "healthy"}}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''
    
    def _generate_config_py(self) -> str:
        """Generate config.py file."""
        return '''"""
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
'''
    
    def _generate_test_cli(self, project_name: str) -> str:
        """Generate CLI test file."""
        return f'''"""
Tests for CLI commands
"""

import pytest
from click.testing import CliRunner
from {project_name}.cli import cli


def test_hello_command():
    """Test hello command"""
    runner = CliRunner()
    result = runner.invoke(cli, ['hello', '--name', 'Test'])
    assert result.exit_code == 0
    assert 'Hello, Test!' in result.output
'''
    
    def _generate_test_web_app(self, project_name: str) -> str:
        """Generate web app test file."""
        return f'''"""
Tests for web application
"""

import pytest
from {project_name}.app import app


@pytest.fixture
def client():
    """Test client fixture"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_index(client):
    """Test home page"""
    response = client.get('/')
    assert response.status_code == 200


def test_health(client):
    """Test health check endpoint"""
    response = client.get('/api/health')
    assert response.status_code == 200
    assert response.json['status'] == 'healthy'
'''
    
    def _generate_test_api(self, project_name: str) -> str:
        """Generate API test file."""
        return f'''"""
Tests for API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from {project_name}.main import app

client = TestClient(app)


def test_root():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_health():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
'''
    
    def _generate_test_library(self, project_name: str) -> str:
        """Generate library test file."""
        return f'''"""
Tests for {project_name} library
"""

import pytest
import {project_name}


def test_import():
    """Test that package can be imported"""
    assert {project_name} is not None


def test_version():
    """Test version is defined"""
    assert hasattr({project_name}, '__version__')
'''
    
    def _generate_library_init(self, project_name: str) -> str:
        """Generate library __init__.py."""
        return f'''"""
{project_name} - Python library
"""

__version__ = "0.1.0"

# Import main modules
# from {project_name}.module import Class, function
'''
    
    def _generate_script_file(self, project_name: str) -> str:
        """Generate simple script file."""
        return f'''"""
{project_name} - Python script
"""

def main():
    """Main function"""
    print("Hello, World!")


if __name__ == "__main__":
    main()
'''
    
    def _generate_env_example(self) -> str:
        """Generate .env.example file."""
        return '''# Environment variables
# Copy this file to .env and update values

SECRET_KEY=your-secret-key-here
DEBUG=True
DATA_DIR=./data
'''
    
    def _generate_license(self) -> str:
        """Generate MIT License file."""
        return '''MIT License

Copyright (c) 2024

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''
    
    def create_project(self, task_description: str, base_path: Path = None) -> Dict[str, Any]:
        """
        Create project structure from task description.
        
        Args:
            task_description: Description of the project/task
            base_path: Base directory to create project (default: current directory)
        
        Returns:
            Dictionary with project information and created files
        """
        if base_path is None:
            base_path = Path.cwd()
        
        # Detect project type and extract name
        project_type = self.detect_project_type(task_description)
        project_name = self.extract_project_name(task_description)
        
        # Generate structure
        structure = self.generate_structure(project_type, project_name)
        
        # Create directories and files
        created_files = []
        created_dirs = []
        
        # Create directories
        for directory in structure.directories:
            dir_path = base_path / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(dir_path))
        
        # Create files
        for file_path, content in structure.files.items():
            full_path = base_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content, encoding='utf-8')
            created_files.append(str(full_path))
        
        return {
            "project_name": project_name,
            "project_type": project_type.value,
            "description": structure.description,
            "base_path": str(base_path),
            "created_directories": created_dirs,
            "created_files": created_files,
            "structure": {
                "directories": structure.directories,
                "files": list(structure.files.keys())
            }
        }


# Create singleton instance
PROJECT_HELPER = ProjectStructureHelper()

