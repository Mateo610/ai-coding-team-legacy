"""
Skill Manager - Handles dynamic loading and prioritization of skill files.
Loads only relevant skills based on task type, frameworks, and context.
"""

import json
import re
from pathlib import Path
import re
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum


class SkillCategory(Enum):
    """Skill file categories"""
    CORE = "core"
    FRAMEWORK = "framework"
    LIBRARY = "library"
    LANGUAGE = "language"
    PATTERN = "pattern"
    PRACTICE = "practice"


class SkillPriority(Enum):
    """Skill priority levels"""
    HIGH = "high"  # Always load if applicable
    MEDIUM = "medium"  # Load for relevant tasks
    LOW = "low"  # Load only when specifically needed


@dataclass
class SkillMetadata:
    """Metadata for a skill file"""
    name: str
    file_path: Path
    category: SkillCategory
    priority: SkillPriority
    task_types: List[str] = field(default_factory=list)  # crud, api, algorithm, etc.
    frameworks: List[str] = field(default_factory=list)  # django, flask, fastapi
    libraries: List[str] = field(default_factory=list)  # pandas, numpy, sqlalchemy
    keywords: List[str] = field(default_factory=list)  # Keywords that trigger this skill
    dependencies: List[str] = field(default_factory=list)  # Required skill files
    description: str = ""
    token_estimate: int = 0  # Estimated tokens for this skill


class SkillManager:
    """
    Manages skill files with dynamic loading based on task analysis.
    """
    
    def __init__(self, skills_dir: Path = Path(".aiconfig/skills")):
        """
        Initialize skill manager.
        
        Args:
            skills_dir: Directory containing skill files
        """
        self.skills_dir = skills_dir
        self.skill_index: Dict[str, SkillMetadata] = {}
        self._load_skill_index()
    
    def _load_skill_index(self):
        """Load and index all skill files with metadata"""
        if not self.skills_dir.exists():
            return
        
        # Map existing skill files to metadata
        skill_mappings = {
            # Core skills (always important)
            "error_handling.md": SkillMetadata(
                name="error_handling",
                file_path=self.skills_dir / "error_handling.md",
                category=SkillCategory.CORE,
                priority=SkillPriority.HIGH,
                task_types=["crud", "api", "algorithm", "general"],
                keywords=["error", "exception", "try", "except"],
                description="Error handling patterns and best practices",
            ),
            "security_best_practices.md": SkillMetadata(
                name="security",
                file_path=self.skills_dir / "security_best_practices.md",
                category=SkillCategory.PRACTICE,
                priority=SkillPriority.HIGH,
                task_types=["api", "crud", "database", "general"],
                keywords=["security", "auth", "authentication", "authorization", "sql injection"],
                description="Security best practices and vulnerabilities",
            ),
            "python_idioms.md": SkillMetadata(
                name="python_idioms",
                file_path=self.skills_dir / "python_idioms.md",
                category=SkillCategory.CORE,
                priority=SkillPriority.HIGH,
                task_types=["general", "algorithm"],
                keywords=["python", "idiom", "pattern"],
                description="Python idioms and best practices",
            ),
            "type_hints_patterns.md": SkillMetadata(
                name="type_hints",
                file_path=self.skills_dir / "type_hints_patterns.md",
                category=SkillCategory.CORE,
                priority=SkillPriority.HIGH,
                task_types=["general", "api", "crud"],
                keywords=["type", "hint", "annotation"],
                description="Type hinting patterns and best practices",
            ),
            
            # Testing skills
            "testing_patterns.md": SkillMetadata(
                name="testing",
                file_path=self.skills_dir / "testing_patterns.md",
                category=SkillCategory.PRACTICE,
                priority=SkillPriority.MEDIUM,
                task_types=["test"],
                keywords=["test", "pytest", "unittest", "assert"],
                description="Testing patterns and best practices",
            ),
            
            # Algorithm skills
            "common_algorithms.md": SkillMetadata(
                name="algorithms",
                file_path=self.skills_dir / "common_algorithms.md",
                category=SkillCategory.CORE,
                priority=SkillPriority.MEDIUM,
                task_types=["algorithm"],
                keywords=["algorithm", "sort", "search", "data structure"],
                description="Common algorithms and data structures",
            ),
            
            # Design patterns
            "design_patterns.md": SkillMetadata(
                name="design_patterns",
                file_path=self.skills_dir / "design_patterns.md",
                category=SkillCategory.PATTERN,
                priority=SkillPriority.MEDIUM,
                task_types=["general", "api", "crud"],
                keywords=["design pattern", "pattern", "architecture"],
                description="Design patterns and when to use them",
            ),
            
            # Documentation
            "documentation_patterns.md": SkillMetadata(
                name="documentation",
                file_path=self.skills_dir / "documentation_patterns.md",
                category=SkillCategory.PRACTICE,
                priority=SkillPriority.MEDIUM,
                task_types=["general"],
                keywords=["docstring", "documentation", "comment"],
                description="Documentation patterns and standards",
            ),
            
            # Code organization
            "code_organization.md": SkillMetadata(
                name="code_organization",
                file_path=self.skills_dir / "code_organization.md",
                category=SkillCategory.CORE,
                priority=SkillPriority.MEDIUM,
                task_types=["general"],
                keywords=["structure", "organization", "module", "package"],
                description="Code organization and structure",
            ),
            
            # Performance
            "performance_optimization.md": SkillMetadata(
                name="performance",
                file_path=self.skills_dir / "performance_optimization.md",
                category=SkillCategory.PRACTICE,
                priority=SkillPriority.LOW,
                task_types=["algorithm", "api"],
                keywords=["performance", "optimize", "efficient", "speed"],
                description="Performance optimization techniques",
            ),
            
            # Logging
            "logging_patterns.md": SkillMetadata(
                name="logging",
                file_path=self.skills_dir / "logging_patterns.md",
                category=SkillCategory.PRACTICE,
                priority=SkillPriority.MEDIUM,
                task_types=["api", "general"],
                keywords=["logging", "log", "logger"],
                description="Logging patterns and best practices",
            ),
            
            # Debugging
            "debugging_patterns.md": SkillMetadata(
                name="debugging",
                file_path=self.skills_dir / "debugging_patterns.md",
                category=SkillCategory.PRACTICE,
                priority=SkillPriority.LOW,
                task_types=["general"],
                keywords=["debug", "debugging", "troubleshoot"],
                description="Debugging techniques and patterns",
            ),
            
            # API design
            "api_design.md": SkillMetadata(
                name="api_design",
                file_path=self.skills_dir / "api_design.md",
                category=SkillCategory.PRACTICE,
                priority=SkillPriority.MEDIUM,
                task_types=["api"],
                keywords=["api", "rest", "endpoint", "route"],
                description="API design principles and best practices",
            ),
            # Framework skills
            "flask.md": SkillMetadata(
                name="flask",
                file_path=self.skills_dir / "flask.md",
                category=SkillCategory.FRAMEWORK,
                priority=SkillPriority.MEDIUM,
                task_types=["api"],
                frameworks=["flask"],
                keywords=["flask", "flask app", "flask route", "blueprint"],
                description="Flask web framework patterns",
            ),
            "fastapi.md": SkillMetadata(
                name="fastapi",
                file_path=self.skills_dir / "fastapi.md",
                category=SkillCategory.FRAMEWORK,
                priority=SkillPriority.MEDIUM,
                task_types=["api"],
                frameworks=["fastapi"],
                keywords=["fastapi", "fast api", "pydantic"],
                description="FastAPI web framework patterns",
            ),
            "django.md": SkillMetadata(
                name="django",
                file_path=self.skills_dir / "django.md",
                category=SkillCategory.FRAMEWORK,
                priority=SkillPriority.MEDIUM,
                task_types=["api", "crud"],
                frameworks=["django"],
                keywords=["django", "django app", "django model", "django view"],
                description="Django web framework patterns",
            ),
            
            # Library skills
            "sqlalchemy.md": SkillMetadata(
                name="sqlalchemy",
                file_path=self.skills_dir / "sqlalchemy.md",
                category=SkillCategory.LIBRARY,
                priority=SkillPriority.MEDIUM,
                task_types=["database", "crud"],
                libraries=["sqlalchemy"],
                keywords=["sqlalchemy", "orm", "database", "model", "session"],
                description="SQLAlchemy ORM patterns",
            ),
            "pandas.md": SkillMetadata(
                name="pandas",
                file_path=self.skills_dir / "pandas.md",
                category=SkillCategory.LIBRARY,
                priority=SkillPriority.MEDIUM,
                task_types=["algorithm", "data_analysis", "etl"],
                libraries=["pandas"],
                keywords=["pandas", "dataframe", "data analysis", "csv", "data processing"],
                description="Pandas data analysis patterns",
            ),
            "numpy.md": SkillMetadata(
                name="numpy",
                file_path=self.skills_dir / "numpy.md",
                category=SkillCategory.LIBRARY,
                priority=SkillPriority.LOW,
                task_types=["algorithm", "data_analysis"],
                libraries=["numpy"],
                keywords=["numpy", "array", "numerical", "matrix", "statistics"],
                description="NumPy numerical computing patterns",
            ),
            
            # ETL and Data Processing
            "etl_patterns.md": SkillMetadata(
                name="etl_patterns",
                file_path=self.skills_dir / "etl_patterns.md",
                category=SkillCategory.PATTERN,
                priority=SkillPriority.HIGH,
                task_types=["etl", "data_analysis"],
                keywords=["etl", "extract transform load", "data pipeline", "data processing", "data transformation", "data validation", "data cleaning", "data migration"],
                description="ETL pipeline patterns and best practices",
            ),
            "data_analysis.md": SkillMetadata(
                name="data_analysis",
                file_path=self.skills_dir / "data_analysis.md",
                category=SkillCategory.PATTERN,
                priority=SkillPriority.MEDIUM,
                task_types=["data_analysis"],
                keywords=["data analysis", "statistical analysis", "data visualization", "data science", "machine learning", "data mining", "analytics"],
                libraries=["pandas", "numpy", "matplotlib", "seaborn"],
                description="Data analysis and statistical patterns",
            ),
            
            # Primary skills (loaded separately, but indexed for completeness)
            "validation.md": SkillMetadata(
                name="validation",
                file_path=self.skills_dir / "validation.md",
                category=SkillCategory.CORE,
                priority=SkillPriority.HIGH,
                task_types=["test", "general"],
                description="Code validation and review patterns",
            ),
            
            # Implementation (primary skill, loaded separately)
            "implementation.md": SkillMetadata(
                name="implementation",
                file_path=self.skills_dir / "implementation.md",
                category=SkillCategory.CORE,
                priority=SkillPriority.HIGH,
                task_types=["general", "crud", "api", "algorithm"],
                description="General implementation guidance",
            ),
        }
        
        # Load metadata and estimate tokens
        for filename, metadata in skill_mappings.items():
            if metadata.file_path.exists():
                content = metadata.file_path.read_text()
                # Rough token estimate: ~4 chars per token
                metadata.token_estimate = len(content) // 4
                self.skill_index[metadata.name] = metadata
    
    def get_relevant_skills(
        self,
        task: str,
        task_type: str = "general",
        context: Optional[Dict] = None,
        max_tokens: int = 8000
    ) -> Tuple[List[str], int]:
        """
        Get relevant skill files based on task analysis.
        
        Args:
            task: Task description
            task_lower: Detected task type
            context: Optional context dictionary
            max_tokens: Maximum tokens for skills
        
        Returns:
            Tuple of (skill file names list, total token estimate)
        """
        context = context or {}
        task_lower = task.lower()
        
        # Analyze task for keywords and patterns
        selected_skills: Dict[str, SkillMetadata] = {}
        keyword_matched_skills: Dict[str, SkillMetadata] = {}  # Framework/library skills matched by keywords
        
        # Primary skills (implementation.md, validation.md) are loaded separately
        primary_skills = {'implementation', 'validation'}
        
        # Step 1: Check for framework/library keyword matches FIRST (before other skills)
        # This ensures framework-specific skills are prioritized when mentioned in task
        for skill_name, skill_meta in self.skill_index.items():
            if skill_name in primary_skills:
                continue
            
            # Check if any keyword matches (case-insensitive)
            for keyword in skill_meta.keywords:
                keyword_lower = keyword.lower()
                # Try word boundary match first (exact word)
                pattern = r'\b' + re.escape(keyword_lower) + r'\b'
                if re.search(pattern, task_lower, re.IGNORECASE):
                    keyword_matched_skills[skill_name] = skill_meta
                    break
                # Fall back to substring match
                elif keyword_lower in task_lower:
                    keyword_matched_skills[skill_name] = skill_meta
                    break
        
        # Step 2: Always include HIGH priority skills for task type (excluding primary skills)
        for skill_name, skill_meta in self.skill_index.items():
            if skill_name in primary_skills or skill_name in keyword_matched_skills:
                continue
            if (skill_meta.priority == SkillPriority.HIGH and 
                (not skill_meta.task_types or task_type in skill_meta.task_types)):
                selected_skills[skill_name] = skill_meta
        
        # Step 3: Add skills based on task type (excluding primary skills and keyword-matched)
        for skill_name, skill_meta in self.skill_index.items():
            if skill_name in primary_skills or skill_name in keyword_matched_skills or skill_name in selected_skills:
                continue
            if task_type in skill_meta.task_types:
                selected_skills[skill_name] = skill_meta
        
        # Step 4: Add keyword-matched skills (these take priority)
        selected_skills.update(keyword_matched_skills)
        
        # Step 4: Check context for frameworks/libraries
        dependencies = context.get('dependencies', [])
        project_type = context.get('project_type', '')
        
        if dependencies:
            for skill_name, skill_meta in self.skill_index.items():
                if skill_name in primary_skills or skill_name in selected_skills:
                    continue
                
                # Check if framework/library matches
                for dep in dependencies:
                    dep_lower = dep.lower()
                    if any(fw.lower() in dep_lower for fw in skill_meta.frameworks):
                        selected_skills[skill_name] = skill_meta
                        break
                    if any(lib.lower() in dep_lower for lib in skill_meta.libraries):
                        selected_skills[skill_name] = skill_meta
                        break
        
        # Step 5: Sort by priority with keyword-matched skills prioritized
        # Keyword-matched skills (framework/library) should be included first
        sorted_skills = sorted(
            selected_skills.values(),
            key=lambda s: (
                # Highest priority: keyword-matched skills (negative to sort first)
                -1 if s.name in keyword_matched_skills else 0,
                # Then by priority
                0 if s.priority == SkillPriority.HIGH else
                1 if s.priority == SkillPriority.MEDIUM else 2,
                s.token_estimate  # Prefer smaller skills when priority equal
            )
        )
        
        # Step 6: Select skills within token budget
        # Prioritize keyword-matched skills first
        selected = []
        total_tokens = 0
        
        # First, add keyword-matched skills
        keyword_skill_names = list(keyword_matched_skills.keys())
        for skill_name in keyword_skill_names:
            if skill_name in selected_skills:
                skill_meta = selected_skills[skill_name]
                if total_tokens + skill_meta.token_estimate <= max_tokens:
                    selected.append(skill_meta.name)
                    total_tokens += skill_meta.token_estimate
        
        # Then add other skills
        for skill_meta in sorted_skills:
            if skill_meta.name in selected:
                continue  # Skip already selected
            if total_tokens + skill_meta.token_estimate <= max_tokens:
                selected.append(skill_meta.name)
                total_tokens += skill_meta.token_estimate
        
        # Step 7: Load dependencies
        final_skills = set(selected)
        for skill_name in selected:
            skill_meta = self.skill_index[skill_name]
            for dep in skill_meta.dependencies:
                if dep in self.skill_index and dep not in final_skills:
                    dep_meta = self.skill_index[dep]
                    if total_tokens + dep_meta.token_estimate <= max_tokens:
                        final_skills.add(dep)
                        total_tokens += dep_meta.token_estimate
        
        return list(final_skills), total_tokens
    
    def load_skill(self, skill_name: str) -> str:
        """Load skill file content by name"""
        if skill_name not in self.skill_index:
            return ""
        
        skill_path = self.skill_index[skill_name].file_path
        if skill_path.exists():
            return skill_path.read_text()
        return ""
    
    def load_skills(self, skill_names: List[str]) -> str:
        """
        Load multiple skill files and combine them.
        
        Args:
            skill_names: List of skill names to load
        
        Returns:
            Combined skill content
        """
        contents = []
        for skill_name in skill_names:
            content = self.load_skill(skill_name)
            if content:
                contents.append(content)
        
        return "\n\n".join(contents)
    
    def get_skill_metadata(self, skill_name: str) -> Optional[SkillMetadata]:
        """Get metadata for a skill"""
        return self.skill_index.get(skill_name)


# Singleton instance
SKILL_MANAGER = SkillManager()

