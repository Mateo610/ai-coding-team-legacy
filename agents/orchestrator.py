"""
Main orchestrator - routes tasks and coordinates agents
"""

import os
import yaml
import requests
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from datetime import datetime
import time

from agents.complexity_predictor import ComplexityPredictor
from agents.routing_optimizer import RoutingOptimizer, ROUTING_OPTIMIZER
from agents.specialized_agent import (
    ImplementationAgent,
    ValidationAgent,
    TestGeneratorAgent,
)
from agents.error_analyzer import ErrorAnalyzer
from agents.exceptions import (
    AITeamError,
    AgentError,
    ModelConnectionError,
    ModelTimeoutError,
    ValidationError,
    ConfigurationError,
    ProjectStructureError,
    RetryableError,
    NonRetryableError,
)
from agents.retry_handler import RetryHandler, retry_on_failure
from agents.health_check import HealthChecker
from agents.timeout_config import TIMEOUT_CONFIG
from agents.config_manager import CONFIG_MANAGER, ConfigManager
from agents.structured_logger import STRUCTURED_LOGGER, StructuredLogger
from agents.secrets_manager import SECRETS_MANAGER
from agents.context_manager import ContextManager, ContextConfig
from learning.logger import InteractionLogger
from learning.evaluator import SuccessEvaluator
from learning.metrics_tracker import MetricsTracker
from learning.error_patterns import EnhancedErrorAnalyzer, ERROR_PATTERN_DB
from tools.project_structure_helper import PROJECT_HELPER, ProjectType

load_dotenv('config/.env')

class Orchestrator:
    """
    Routes tasks between local agents and Claude
    Coordinates execution and logs everything
    """
    
    def __init__(self, config_path: str = None, config_manager: ConfigManager = None):
        """
        Initialize orchestrator.
        
        Args:
            config_path: Optional path to config file (default: uses CONFIG_MANAGER)
            config_manager: Optional ConfigManager instance (default: uses CONFIG_MANAGER singleton)
        """
        # Use provided config manager or singleton
        self.config_manager = config_manager or CONFIG_MANAGER
        
        # Reload config if path provided (for testing/override)
        if config_path and config_path != str(self.config_manager.config_path):
            self.config_manager = ConfigManager(config_path=config_path)
        
        # Get configuration
        self.config = self.config_manager.config
        orchestrator_config = self.config_manager.get_model_config("orchestrator")
        
        if not orchestrator_config:
            raise ConfigurationError("Orchestrator model configuration not found")
        
        self.model = orchestrator_config.name
        self.base_url = self.config_manager.get_ollama_base_url()
        
        routing_config = self.config_manager.get_routing_config()
        if not routing_config:
            raise ConfigurationError("Routing configuration not found")
        
        self.complexity_threshold = routing_config.complexity_threshold

        # Initialize structured logger
        self.log = StructuredLogger(
            name="orchestrator",
            log_dir=str(self.config_manager.get_data_dir().parent / "logs"),
            log_level=self.config_manager.get_log_level(),
            console_output=True,
            json_format=True
        )
        
        # Initialize components
        self.complexity_predictor = ComplexityPredictor(use_learning=True)
        self.routing_optimizer = ROUTING_OPTIMIZER
        self.logger = InteractionLogger(str(self.config_manager.get_data_dir()))
        self.evaluator = SuccessEvaluator()
        # Use enhanced error analyzer with pattern learning
        self.error_analyzer = EnhancedErrorAnalyzer(ERROR_PATTERN_DB)
        self.metrics_tracker = MetricsTracker()
        
        # Initialize context manager
        self.context_manager = ContextManager()
        
        # Log initialization
        self.log.info("Orchestrator initialized", component="orchestrator", details={
            "model": self.model,
            "base_url": self.base_url,
            "complexity_threshold": self.complexity_threshold
        })

        # Initialize agents
        self.implementation_agent = ImplementationAgent()
        self.test_generator = TestGeneratorAgent()
        
        # Initialize project structure helper
        self.project_helper = PROJECT_HELPER
        
        # Initialize health checker
        self.health_checker = HealthChecker(
            base_url=self.base_url,
            data_dir=os.getenv("DATA_DIR")
        )

        # Load .aiconfig if exists
        self.project_config = self._load_aiconfig()

    def build_with_validation(
        self, task: str, context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Full pipeline with comprehensive error handling:
        1. Project structure detection (if needed)
        2. Route decision
        3. Implementation
        4. Validation with tests
        5. Log everything
        """
        start_time = time.time()
        context = context or {}
        
        # Initialize result with defaults
        default_result = {
            "success": False,
            "interaction_id": None,
            "code": "",
            "validation": {},
            "evaluation": None,
            "duration_ms": 0,
            "error": None,
            "error_type": None,
        }
        
        try:
            print(f"\n{'='*60}")
            print(f"🤖 Building with validation: {task[:60]}...")
            print(f"{'='*60}\n")

            # Step 0: Check if project structure is needed
            project_info = None
            try:
                if self._needs_project_structure(task):
                    print("📁 Detected new project creation...")
                    project_type = self.project_helper.detect_project_type(task)
                    project_name = self.project_helper.extract_project_name(task)
                    
                    print(f"   Project type: {project_type.value}")
                    print(f"   Project name: {project_name}")
                    
                    base_path = context.get('project_path', Path.cwd())
                    if isinstance(base_path, str):
                        base_path = Path(base_path)
                    
                    project_info = self.project_helper.create_project(task, base_path)
                    
                    print(f"   ✅ Created project structure at: {base_path}")
                    print(f"      Directories: {len(project_info['created_directories'])}")
                    print(f"      Files: {len(project_info['created_files'])}")
                    print()
                    
                    context['project_info'] = project_info
                    context['project_path'] = str(base_path)
            except Exception as e:
                error_msg = f"Failed to create project structure: {str(e)}"
                print(f"   ⚠️  {error_msg}")
                # Continue execution - project structure is optional

            # Step 1: Complexity & routing
            try:
                print("📊 Analyzing complexity...")
                
                # Detect task type first (needed for improved complexity prediction)
                task_type = self.context_manager.detect_task_type(task)
                context['task_type'] = task_type
                
                # Predict complexity with task type
                complexity = self.complexity_predictor.predict(task, context, task_type)
                print(f"   Complexity: {complexity}/10")
                print(f"   Task Type: {task_type}")
            except Exception as e:
                print(f"   ⚠️  Complexity prediction failed: {str(e)}")
                complexity = 5  # Default to medium complexity
                task_type = context.get('task_type', 'general')
                print(f"   Using default complexity: {complexity}/10")

            # Use routing optimizer for optimal route selection
            task_hash = hashlib.md5(task.encode()).hexdigest()[:8]
            route, route_reason = self.routing_optimizer.get_optimal_route(
                task_type=task_type,
                predicted_complexity=complexity,
                complexity_threshold=self.complexity_threshold,
                use_learning=True
            )
            
            print(f"   Route: {route} ({route_reason})")
            print()

            # Step 2: Build context using ContextManager
            try:
                
                # Create context config based on task type
                context_config = ContextConfig()
                
                # Adjust config based on task type
                if task_type in ['crud', 'database', 'api']:
                    context_config.include_project_info = True
                    context_config.include_architecture = True
                    context_config.include_dependencies = True
                
                if task_type == 'test':
                    context_config.include_relevant_code = True
                    context_config.include_current_file = True
                
                # Build optimized context
                enriched_context = self.context_manager.build_context(
                    task=task,
                    context_dict=context,
                    config=context_config,
                    agent_type='implementation'
                )
                
                self.log.debug(
                    f"Context built for task type: {task_type}",
                    component="orchestrator",
                    details={
                        "task_type": task_type,
                        "context_length": len(enriched_context),
                        "sections_included": [
                            'project_rules' if context_config.include_project_rules else None,
                            'architecture' if context_config.include_architecture else None,
                            'project_info' if context_config.include_project_info else None,
                        ]
                    }
                )
            except Exception as e:
                print(f"   ⚠️  Context building failed: {str(e)}")
                self.log.warning(
                    f"Context building failed: {str(e)}",
                    component="orchestrator",
                    details={"error": str(e)}
                )
                # Fallback to basic context
                enriched_context = self._build_context_fallback(task, context)

            # Step 3: Generate code with retry logic for transient failures
            impl_result = None
            try:
                if route == "claude":
                    # Try Claude with retry
                    impl_result = RetryHandler.execute_with_retry(
                        self._execute_claude,
                        max_attempts=2,  # Fewer retries for Claude (fallback available)
                        base_delay=2.0,
                        task=task,
                        context=enriched_context
                    )
                else:
                    # Try local with retry
                    print("💻 Implementation Agent coding...")
                    impl_result = RetryHandler.execute_with_retry(
                        lambda: self.implementation_agent.execute(
                            task=task,
                            context=enriched_context,
                            use_tools=True,
                            task_type=task_type,
                            context_dict=context,
                        ),
                        max_attempts=3,
                        base_delay=1.0,
                    )
                
                if not impl_result:
                    raise AgentError("Agent execution returned no result")
                    
            except (ModelConnectionError, ModelTimeoutError) as e:
                # Transient errors - try fallback
                print(f"   ⚠️  {e.message}")
                if route == "claude":
                    print("   💡 Falling back to local model...")
                    try:
                        impl_result = RetryHandler.execute_with_retry(
                            lambda: self.implementation_agent.execute(
                                task=task,
                                context=enriched_context,
                                use_tools=True,
                                task_type=task_type,
                                context_dict=context,
                            ),
                            max_attempts=2,  # Fewer retries for fallback
                            base_delay=1.0,
                        )
                        route = "local"  # Update route to reflect fallback
                    except Exception as fallback_error:
                        print(f"   ❌ Fallback also failed: {str(fallback_error)}")
                        raise AgentError(
                            f"Both Claude and local model failed. Original: {e.message}, Fallback: {str(fallback_error)}"
                        )
                else:
                    raise
            except AgentError:
                # Re-raise agent errors
                raise
            except Exception as e:
                # Other agent errors - wrap in AgentError
                raise AgentError(f"Agent execution failed: {str(e)}", details={"route": route})

            generated_code = impl_result.get("output", "") if impl_result else ""

            # Step 3.5: Apply code quality improvements (non-critical, continue on error)
            if generated_code:
                try:
                    from tools.code_tools import CodeTools
                    print("✨ Applying code quality improvements...")
                    quality_result = CodeTools.apply_code_quality(generated_code)
                    
                    if quality_result.success:
                        generated_code = quality_result.result
                        improvements = quality_result.metadata.get("improvements", [])
                        if improvements:
                            print(f"   ✓ {' | '.join(improvements)}")
                        
                        type_check = quality_result.error
                        if type_check and not type_check.startswith("⚠️"):
                            print(f"   ⚠️  {type_check[:100]}")
                    else:
                        print(f"   ⚠️  Code quality tools unavailable: {quality_result.error[:100]}")
                except Exception as e:
                    print(f"   ⚠️  Code quality improvement failed: {str(e)}")
                    # Continue with original code

            # Step 4: Validate with tests
            validation_results = {}
            try:
                validation_results = self.test_generator.validate_code(
                    code=generated_code, original_task=task
                )
            except Exception as e:
                print(f"   ⚠️  Validation failed: {str(e)}")
                validation_results = {
                    "syntax_check": {"success": False, "error": str(e)},
                    "execution": None,
                    "tests_run": None,
                    "overall_success": False,
                }

            # Step 5: Evaluate
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Build interaction data
            interaction_data = {
                "agent": "orchestrator",
                "task": task,
                "context": str(enriched_context),
                "output": generated_code,
                "complexity": {"predicted": complexity, "actual": complexity},
                "route": route,
                "duration_ms": duration_ms,
                "metadata": {
                    **(impl_result.get("metadata", {}) if impl_result else {}),
                    "validation": validation_results,
                    "tool_calls": impl_result.get("tool_calls", []) if impl_result else [],
                },
            }

            # Step 6: Evaluate (non-critical, continue on error)
            # Extract test results from validation for evaluator
            test_results_for_eval = {}
            tests_run = validation_results.get('tests_run')
            if tests_run and isinstance(tests_run, dict) and tests_run.get('metadata'):
                test_meta = tests_run['metadata']
                test_results_for_eval = {
                    'passed': test_meta.get('passed', 0),
                    'total': test_meta.get('total', 0)
                }
            # Add test_results to metadata for evaluator
            interaction_data['metadata']['test_results'] = test_results_for_eval
            
            evaluation = None
            try:
                evaluation = self.evaluator.evaluate(interaction_data)
                # Ensure evaluation has test counts from validation if evaluator didn't get them
                if evaluation.passed_tests == 0 and evaluation.total_tests == 0:
                    if test_results_for_eval:
                        evaluation.passed_tests = test_results_for_eval.get('passed', 0)
                        evaluation.total_tests = test_results_for_eval.get('total', 0)
            except Exception as e:
                print(f"   ⚠️  Evaluation failed: {str(e)}")
                import traceback
                traceback.print_exc()
                from learning.evaluator import EvaluationResult
                passed_tests = test_results_for_eval.get('passed', 0)
                total_tests = test_results_for_eval.get('total', 0)
                evaluation = EvaluationResult(
                    score=0, 
                    breakdown={}, 
                    errors=[f"Evaluation failed: {str(e)}"], 
                    passed_tests=passed_tests,
                    total_tests=total_tests
                )

            # Step 7: Log (non-critical, continue on error)
            interaction_id = None
            try:
                interaction_id = self.logger.log_interaction(
                    agent="orchestrator",
                    task=task,
                    context=str(enriched_context),
                    output=generated_code,
                    complexity_pred=complexity,
                    complexity_actual=complexity,
                    route=route,
                    success_score=evaluation.score if evaluation and hasattr(evaluation, 'score') else (evaluation.get('score', 0) if evaluation and isinstance(evaluation, dict) else 0),
                    tokens_used=impl_result.get("tokens_used", 0) if impl_result else 0,
                    duration_ms=duration_ms,
                    metadata=interaction_data["metadata"],
                )
            except Exception as e:
                print(f"   ⚠️  Logging failed: {str(e)}")
                # Continue without logging
            
            # Step 8: Record metrics (non-critical, continue on error)
            try:
                # Extract test results
                test_results = {}
                tests_run = validation_results.get("tests_run")
                if tests_run and isinstance(tests_run, dict) and tests_run.get("metadata"):
                    test_meta = tests_run["metadata"]
                    test_results = {
                        "passed": test_meta.get("passed", 0),
                        "total": test_meta.get("total", 0),
                        "pass_rate": (test_meta.get("passed", 0) / test_meta.get("total", 1) * 100) if test_meta.get("total", 0) > 0 else 0.0
                    }
                
                # Extract errors
                errors = []
                syntax_check = validation_results.get("syntax_check")
                if syntax_check and isinstance(syntax_check, dict) and syntax_check.get("success") == False:
                    errors.append({"type": "syntax", "message": syntax_check.get("error", "")})
                execution = validation_results.get("execution")
                if execution and isinstance(execution, dict) and execution.get("success") == False:
                    errors.append({"type": "execution", "message": execution.get("error", "")})
                if test_results.get("total", 0) > 0 and test_results.get("pass_rate", 100) < 100:
                    errors.append({"type": "test_failure", "message": f"{test_results.get('total', 0) - test_results.get('passed', 0)} tests failed"})
                
                # Record metrics
                metrics_data = {
                    "interaction_id": interaction_id or f"interaction_{int(time.time())}",
                    "timestamp": datetime.now().isoformat(),
                    "agent": "orchestrator",
                    "task_type": task_type,
                    "route": route,
                    "task_hash": task_hash,
                    "evaluation": evaluation,
                    "test_results": test_results,
                    "syntax_valid": validation_results.get("syntax_check", {}).get("success", False) if validation_results.get("syntax_check") and isinstance(validation_results.get("syntax_check"), dict) else False,
                    "execution_success": validation_results.get("execution", {}).get("success", False) if validation_results.get("execution") and isinstance(validation_results.get("execution"), dict) else False,
                    "tokens_used": impl_result.get("tokens_used", 0) if impl_result else 0,
                    "duration_ms": duration_ms,
                    "errors": errors,
                    "complexity": {"predicted": complexity, "actual": complexity},
                    "metadata": interaction_data["metadata"]
                }
                
                self.metrics_tracker.record_interaction(metrics_data)
                
                # Record routing decision for learning
                try:
                    self.routing_optimizer.record_decision(
                        task_type=task_type,
                        task_hash=task_hash,
                        predicted_complexity=complexity,
                        route_used=route,
                        success_score=evaluation.score if evaluation and hasattr(evaluation, 'score') else (evaluation.get('score', 0) if evaluation and isinstance(evaluation, dict) else 0),
                        duration_ms=duration_ms,
                        actual_complexity=complexity,  # Could be improved with actual complexity assessment
                        tokens_used=impl_result.get("tokens_used", 0) if impl_result else 0,
                        model_used=route,
                        metadata={"task": task[:200]}  # Truncated task for reference
                    )
                except Exception as e:
                    print(f"   ⚠️  Routing decision recording failed: {str(e)}")
                    # Continue without recording
            except Exception as e:
                print(f"   ⚠️  Metrics recording failed: {str(e)}")
                # Continue without metrics

            tests_passed = 0
            tests_run = validation_results.get("tests_run")
            if tests_run and isinstance(tests_run, dict) and tests_run.get("metadata"):
                tests_passed = tests_run["metadata"].get("passed", 0)

            print(f"\n{'='*60}")
            print("✅ Complete!")
            eval_score = 0
            if evaluation:
                if hasattr(evaluation, 'score'):
                    eval_score = evaluation.score
                elif isinstance(evaluation, dict):
                    eval_score = evaluation.get('score', 0)
            print(f"   Success score: {eval_score}/100")
            print(f"   Tests: {tests_passed} passed")
            print(f"   Duration: {duration_ms}ms")
            print(f"{'='*60}\n")

            result = {
                "success": validation_results.get("overall_success", False),
                "interaction_id": interaction_id,
                "code": generated_code,
                "validation": validation_results,
                "evaluation": evaluation,
                "duration_ms": duration_ms,
            }
            
            if project_info:
                result["project_info"] = project_info
            
            return result
            
        except AITeamError as e:
            # Custom exceptions - provide detailed error
            duration_ms = int((time.time() - start_time) * 1000)
            error_result = default_result.copy()
            error_result.update({
                "error": str(e),
                "error_type": type(e).__name__,
                "duration_ms": duration_ms,
            })
            
            # Log error
            self.log.error(
                f"Build failed: {e.message}",
                component="orchestrator",
                details={
                    "error_type": type(e).__name__,
                    "error_details": e.details,
                    "duration_ms": duration_ms
                },
                exc_info=True
            )
            
            print(f"\n{'='*60}")
            print(f"❌ Error: {e.message}")
            if e.details:
                print(f"   Details: {e.details}")
            print(f"   Duration: {duration_ms}ms")
            print(f"{'='*60}\n")
            
            return error_result
            
        except Exception as e:
            # Unexpected errors - log and return error result
            duration_ms = int((time.time() - start_time) * 1000)
            error_result = default_result.copy()
            error_result.update({
                "error": f"Unexpected error: {str(e)}",
                "error_type": type(e).__name__,
                "duration_ms": duration_ms,
            })
            
            print(f"\n{'='*60}")
            print(f"❌ Unexpected error: {type(e).__name__}")
            print(f"   {str(e)}")
            print(f"   Duration: {duration_ms}ms")
            print(f"{'='*60}\n")
            
            # Log error if logger is available
            try:
                self.logger.log_interaction(
                    agent="orchestrator",
                    task=task,
                    context=str(context),
                    output="",
                    complexity_pred=0,
                    complexity_actual=0,
                    route="error",
                    success_score=0,
                    tokens_used=0,
                    duration_ms=duration_ms,
                    metadata={"error": str(e), "error_type": type(e).__name__},
                )
            except:
                pass  # Ignore logging errors
            
            return error_result
    
    def _needs_project_structure(self, task: str) -> bool:
        """
        Check if task needs project structure generation.
        
        Args:
            task: Task description
        
        Returns:
            True if project structure should be generated
        """
        task_lower = task.lower()
        
        # Keywords that suggest new project creation
        project_keywords = [
            'create a new project',
            'build a new',
            'make a new',
            'set up a new',
            'initialize a new',
            'start a new',
            'create project',
            'new project',
            'project structure',
            'project setup',
        ]
        
        # Check for project creation keywords
        if any(keyword in task_lower for keyword in project_keywords):
            return True
        
        # Check if task mentions creating CLI/web app/API/library (new projects)
        create_patterns = [
            'create.*cli',
            'create.*web app',
            'create.*web application',
            'create.*rest api',
            'create.*api',
            'create.*library',
            'create.*package',
            'make.*cli',
            'make.*web app',
            'make.*web application',
            'build.*cli',
            'build.*web app',
            'build.*rest api',
            'build.*api',
        ]
        
        import re
        for pattern in create_patterns:
            if re.search(pattern, task_lower):
                return True
        
        # Check for project type keywords (CLI, web app, API)
        project_type_keywords = ['cli tool', 'command line', 'web application', 'rest api', 'microservice']
        for keyword in project_type_keywords:
            if keyword in task_lower and ('create' in task_lower or 'build' in task_lower or 'make' in task_lower):
                return True
        
        return False
    
    def check_health(self, config_path: str = "config/models.yaml") -> Dict[str, Any]:
        """
        Check system health status.
        
        Args:
            config_path: Path to configuration file
        
        Returns:
            Dictionary with health status and component results
        """
        return self.health_checker.check_all(config_path)
    
    def get_health_summary(self, config_path: str = "config/models.yaml") -> str:
        """
        Get human-readable health summary.
        
        Args:
            config_path: Path to configuration file
        
        Returns:
            Human-readable health summary string
        """
        return self.health_checker.get_health_summary(config_path)
    
    def build_with_validation_iterative(
        self, task: str, context: Optional[Dict] = None, max_iterations: int = 3
    ) -> Dict[str, Any]:
        """
        Build with validation + iterative improvement
        
        Automatically fixes code until tests pass or max_iterations reached
        
        Args:
            task: Original task description
            context: Optional context dict
            max_iterations: Maximum number of fix attempts (default: 3)
        
        Returns:
            Result dict with final code, validation, and iteration history
        """
        start_time = time.time()
        original_task = task
        iteration_history = []
        
        # Detect task type once at the start (needed for error analysis)
        task_type = self.context_manager.detect_task_type(task)
        
        print(f"\n{'='*60}")
        print(f"🔄 Iterative Building: {task[:60]}...")
        print(f"   Max iterations: {max_iterations}")
        print(f"{'='*60}\n")
        
        for iteration in range(1, max_iterations + 1):
            print(f"\n{'─'*60}")
            print(f"🔄 Iteration {iteration}/{max_iterations}")
            print(f"{'─'*60}\n")
            
            # Build with validation
            result = self.build_with_validation(task, context)
            
            # Track iteration
            evaluation = result.get("evaluation")
            eval_score = 0
            if evaluation:
                if hasattr(evaluation, 'score'):
                    eval_score = evaluation.score
                elif isinstance(evaluation, dict):
                    eval_score = evaluation.get('score', 0)
            
            iteration_info = {
                "iteration": iteration,
                "success": result.get("success", False),
                "code": result.get("code", ""),
                "validation": result.get("validation", {}),
                "evaluation_score": eval_score,
            }
            iteration_history.append(iteration_info)
            
            # Check if successful
            if result.get("success", False):
                duration_ms = int((time.time() - start_time) * 1000)
                
                # Get evaluation score safely
                evaluation = result.get("evaluation")
                eval_score = 0
                if evaluation:
                    if hasattr(evaluation, 'score'):
                        eval_score = evaluation.score
                    elif isinstance(evaluation, dict):
                        eval_score = evaluation.get('score', 0)
                
                print(f"\n{'='*60}")
                print(f"✅ SUCCESS after {iteration} iteration(s)!")
                print(f"   Final score: {eval_score}/100")
                print(f"   Total duration: {duration_ms}ms")
                print(f"{'='*60}\n")
                
                result["iterations"] = iteration_history
                result["total_iterations"] = iteration
                result["duration_ms"] = duration_ms
                return result
            
            # If not successful and not last iteration, analyze errors and retry
            if iteration < max_iterations:
                validation_results = result.get("validation", {})
                # Pass task_type to error analyzer for pattern matching
                validation_results_with_type = validation_results.copy()
                validation_results_with_type['task_type'] = task_type
                error_analysis = self.error_analyzer.analyze(validation_results_with_type)
                
                # Record errors for pattern learning (before generating fix prompt)
                if error_analysis.get("has_errors"):
                    # Use ERROR_PATTERN_DB if available
                    try:
                        error_pattern_db = ERROR_PATTERN_DB
                        for error_msg in error_analysis.get("specific_errors", [])[:3]:  # Top 3 errors
                            error_id = error_pattern_db.record_error(
                                error_type=error_analysis.get("error_type", "unknown"),
                                error_message=error_msg,
                                task_type=task_type,
                                fix_applied=False
                            )
                            # Store error_id for metrics tracking
                            if 'error_ids' not in locals():
                                error_ids = []
                            error_ids.append(error_id)
                    except (AttributeError, NameError):
                        # If error_pattern_db not available, skip recording
                        pass
                
                if error_analysis.get("has_errors"):
                    print(f"\n🔍 Analyzing errors...")
                    print(f"   Error type: {error_analysis.get('error_type')}")
                    print(f"   Summary: {error_analysis.get('error_summary')}")
                    
                    # Generate improved task with error context
                    task = self.error_analyzer.generate_fix_prompt(
                        error_analysis, result.get("code", ""), original_task
                    )
                    
                    print(f"\n💡 Attempting fix...")
                    print(f"   Fix suggestions:")
                    suggestions = error_analysis.get("fix_suggestions", "").split("\n")
                    for suggestion in suggestions[:3]:  # Show top 3
                        if suggestion.strip():
                            print(f"      - {suggestion.strip()}")
                    
                    # Continue to next iteration
                    continue
            
            # Last iteration or no errors to fix
            break
        
        # If we get here, all iterations failed
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Get evaluation score safely
        evaluation = result.get("evaluation")
        eval_score = 0
        if evaluation:
            if hasattr(evaluation, 'score'):
                eval_score = evaluation.score
            elif isinstance(evaluation, dict):
                eval_score = evaluation.get('score', 0)
        
        print(f"\n{'='*60}")
        print(f"⚠️  Completed {max_iterations} iterations, but issues remain")
        print(f"   Final score: {eval_score}/100")
        print(f"   Total duration: {duration_ms}ms")
        print(f"{'='*60}\n")
        
        result["iterations"] = iteration_history
        result["total_iterations"] = max_iterations
        result["duration_ms"] = duration_ms
        result["success"] = False
        
        return result
    
    def _load_aiconfig(self) -> Dict[str, str]:
        """Load project configuration from .aiconfig/"""
        config = {}
        
        aiconfig_dir = Path('.aiconfig')
        if not aiconfig_dir.exists():
            return config
        
        # Load rules
        rules_file = aiconfig_dir / 'rules.md'
        if rules_file.exists():
            config['rules'] = rules_file.read_text()
        
        # Load architecture docs
        arch_file = aiconfig_dir / 'context' / 'architecture.md'
        if arch_file.exists():
            config['architecture'] = arch_file.read_text()
        
        return config
    
    def process_request(self, task: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Main entry point - processes user request
        
        Flow:
        1. Predict complexity
        2. Route to local or Claude
        3. Execute
        4. Evaluate
        5. Log
        """
        
        start_time = time.time()
        context = context or {}
        
        print(f"\n{'='*60}")
        print(f"🤖 Processing: {task[:80]}...")
        print(f"{'='*60}\n")
        
        # Step 1: Predict complexity
        print("📊 Analyzing complexity...")
        complexity = self.complexity_predictor.predict(task, context)
        print(f"   Complexity score: {complexity}/10")
        
        # Step 2: Route decision
        if complexity >= self.complexity_threshold:
            route = "claude"
            print(f"   🧠 Routing to Claude (complex task)\n")
        else:
            route = "local"
            print(f"   💻 Routing to local agents (standard task)\n")
        
        # Step 3: Build context using ContextManager
        task_type = self.context_manager.detect_task_type(task)
        context_config = ContextConfig()
        enriched_context = self.context_manager.build_context(
            task=task,
            context_dict=context,
            config=context_config,
            agent_type=None  # General context for orchestrator
        )
        
        # Step 4: Execute
        if route == "claude":
            result = self._execute_claude(task, enriched_context)
        else:
            result = self._execute_local(task, enriched_context)
        
        # Step 5: Evaluate
        duration_ms = int((time.time() - start_time) * 1000)
        
        interaction_data = {
            'agent': 'orchestrator',
            'task': task,
            'context': str(enriched_context),
            'output': result.get('output', ''),
            'complexity': {
                'predicted': complexity,
                'actual': complexity  # Will be updated by evaluator
            },
            'route': route,
            'duration_ms': duration_ms,
            'metadata': result.get('metadata', {})
        }
        
        evaluation = self.evaluator.evaluate(interaction_data)
        
        # Get evaluation score safely
        eval_score = 0
        if evaluation:
            if hasattr(evaluation, 'score'):
                eval_score = evaluation.score
            elif isinstance(evaluation, dict):
                eval_score = evaluation.get('score', 0)
        
        print(f"\n{'='*60}")
        print(f"✅ Complete!")
        print(f"   Success score: {eval_score}/100")
        print(f"   Duration: {duration_ms}ms")
        print(f"   Route: {route}")
        if evaluation and hasattr(evaluation, 'errors') and evaluation.errors:
            print(f"   ⚠️  Issues: {', '.join(evaluation.errors)}")
        print(f"{'='*60}\n")
        
        # Step 6: Log
        interaction_id = self.logger.log_interaction(
            agent='orchestrator',
            task=task,
            context=str(enriched_context),
            output=result.get('output', ''),
            complexity_pred=complexity,
            complexity_actual=complexity,
            route=route,
            success_score=eval_score,
            tokens_used=result.get('tokens_used', 0),
            duration_ms=duration_ms,
            metadata={
                **result.get('metadata', {}),
                'evaluation': evaluation.breakdown
            }
        )
        
        return {
            'success': True,
            'interaction_id': interaction_id,
            'route': route,
            'complexity': complexity,
            'output': result.get('output'),
            'evaluation': evaluation,
            'duration_ms': duration_ms
        }
    
    def _build_context_fallback(self, task: str, context: Dict) -> str:
        """
        Fallback context builder (simple version).
        Used when ContextManager fails.
        """
        parts = []
        
        # Add project rules if available
        if 'rules' in self.project_config:
            parts.append("PROJECT RULES:")
            parts.append(self.project_config['rules'])
            parts.append("")
        
        # Add architecture context
        if 'architecture' in self.project_config:
            parts.append("ARCHITECTURE:")
            parts.append(self.project_config['architecture'])
            parts.append("")
        
        # Add any provided context
        if context:
            parts.append("ADDITIONAL CONTEXT:")
            parts.append(str(context))
            parts.append("")
        
        return "\n".join(parts)
    
    def _execute_local(self, task: str, context: str) -> Dict[str, Any]:
        """Execute with local Qwen model"""
        
        print("💭 Thinking with local model...")
        
        system_prompt = f"""You are an expert software engineer orchestrating a coding task.

{context}

Break down the task and provide implementation guidance."""

        # Get timeout from configuration
        model_timeout = TIMEOUT_CONFIG.get_model_request_timeout()
        
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": task}
                    ],
                    "stream": False
                },
                timeout=model_timeout
            )
            response.raise_for_status()
        except requests.exceptions.Timeout:
            raise ModelTimeoutError(f"Local model request timed out after {model_timeout}s")
        except requests.exceptions.RequestException as e:
            raise ModelConnectionError(f"Failed to connect to local model: {str(e)}")
        
        result = response.json()
        output = result['message']['content']
        
        print(f"\n📝 Response:\n{output[:500]}...")
        
        return {
            'output': output,
            'tokens_used': result.get('eval_count', 0),
            'metadata': {
                'model': self.model,
                'prompt_tokens': result.get('prompt_eval_count', 0)
            }
        }
    
    def _execute_claude(self, task: str, context: str) -> Dict[str, Any]:
        """Execute with Claude API"""
        
        print("🧠 Calling Claude API...")
        
        try:
            import anthropic
            
            # Get API key from secrets manager
            api_key = SECRETS_MANAGER.get('ANTHROPIC_API_KEY')
            if not api_key:
                raise ConfigurationError(
                    "ANTHROPIC_API_KEY not found. Set it in environment or config/.env",
                    details={"hint": "Get your API key from https://console.anthropic.com/"}
                )
            
            client = anthropic.Anthropic(
                api_key=api_key
            )
            
            claude_config = self.config_manager.get_claude_config()
            if not claude_config:
                raise ConfigurationError("Claude configuration not found")
            
            message = client.messages.create(
                model=claude_config.model,
                max_tokens=claude_config.max_tokens,
                messages=[
                    {
                        "role": "user",
                        "content": f"{context}\n\nTask: {task}"
                    }
                ]
            )
            
            output = message.content[0].text
            
            print(f"\n📝 Claude response:\n{output[:500]}...")
            
            return {
                'output': output,
                'tokens_used': message.usage.input_tokens + message.usage.output_tokens,
                'metadata': {
                    'model': self.config['claude']['model'],
                    'input_tokens': message.usage.input_tokens,
                    'output_tokens': message.usage.output_tokens
                }
            }
            
        except Exception as e:
            print(f"❌ Claude API error: {e}")
            print("   Falling back to local model...")
            return self._execute_local(task, context)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get session statistics"""
        return self.logger.get_stats()