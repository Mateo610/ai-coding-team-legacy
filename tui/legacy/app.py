"""
AI Coding Team - Text User Interface (TUI)
Main interface for users to interact with the system

Built with Textual (Textualize)
"""

import sys
import asyncio
from pathlib import Path
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from textual.app import App, ComposeResult
    from textual.containers import Container, Horizontal, Vertical, ScrollableContainer, Grid
    from textual.widgets import (
        Header, Footer, Button, Input, TextArea, Static, Tabs, Tab,
        DataTable, Label, Log, Markdown, Tree, DirectoryTree, Select,
        Checkbox, Collapsible
    )
    from textual.binding import Binding
    from textual.reactive import reactive
    from textual.screen import Screen, ModalScreen
    from textual.message import Message
    from textual.widget import Widget
    TEXTUAL_AVAILABLE = True
except ImportError as e:
    TEXTUAL_AVAILABLE = False
    print("⚠️  Textual library not installed or wrong version")
    print(f"Import error: {e}")
    print("\nThe apt-installed version (0.1.13) is too old.")
    print("Please install the modern version with:")
    print("  pip3 install --user --upgrade --break-system-packages textual")
    print("\nOr use a virtual environment:")
    print("  python3 -m venv venv")
    print("  source venv/bin/activate")
    print("  pip install textual")

if TEXTUAL_AVAILABLE:
    from agents.orchestrator import Orchestrator
    from learning.metrics_tracker import MetricsTracker
    from learning.error_patterns import ERROR_PATTERN_DB, EnhancedErrorAnalyzer
    from learning.feedback_collector import FEEDBACK_COLLECTOR, FeedbackType
    from agents.routing_optimizer import ROUTING_OPTIMIZER
    from agents.complexity_predictor import ComplexityPredictor


if not TEXTUAL_AVAILABLE:
    # Provide a fallback if textual is not available
    class FallbackApp:
        def run(self):
            print("Textual library is required. Please install it first.")
            sys.exit(1)


if TEXTUAL_AVAILABLE:
    class TaskResultWidget(Widget):
        """Widget for displaying task results"""
        
        def __init__(self, result: dict, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.result = result
        
        def compose(self) -> ComposeResult:
            """Compose the result widget"""
            with Container(classes="result-container"):
                # Success status
                success = self.result.get("success", False)
                status_text = "✅ Success" if success else "❌ Failed"
                yield Static(status_text, classes="status")
                
                # Evaluation score
                evaluation = self.result.get("evaluation")
                if evaluation:
                    score = evaluation.score if hasattr(evaluation, 'score') else evaluation.get('score', 0)
                    yield Static(f"Score: {score}/100", classes="score")
                
                # Code preview
                code = self.result.get("code", "")
                if code:
                    code_preview = code[:500] + ("..." if len(code) > 500 else "")
                    yield Collapsible(
                        Static(f"```python\n{code_preview}\n```", classes="code-preview"),
                        title="Generated Code",
                        collapsed=True
                    )
                
                # Validation results
                validation = self.result.get("validation", {})
                if validation:
                    validation_text = "Validation:\n"
                    if validation.get("syntax_valid"):
                        validation_text += "✅ Syntax: Valid\n"
                    if validation.get("execution_success"):
                        validation_text += "✅ Execution: Success\n"
                    if validation.get("tests_run"):
                        tests = validation["tests_run"].get("metadata", {})
                        if tests:
                            validation_text += f"✅ Tests: {tests.get('passed', 0)}/{tests.get('total', 0)} passed\n"
                    
                    yield Static(validation_text, classes="validation")
                
                # Errors
                errors = self.result.get("validation", {}).get("errors", [])
                if errors:
                    error_text = "Errors:\n" + "\n".join(f"- {str(e)}" for e in errors[:5])
                    yield Static(error_text, classes="errors")
    
    
    class TaskInputScreen(Screen):
        """Screen for task input and execution"""
        
        BINDINGS = [
            Binding("ctrl+q", "quit", "Quit"),
            Binding("ctrl+r", "run_task", "Run Task"),
            Binding("ctrl+d", "show_dashboard", "Dashboard"),
            Binding("ctrl+s", "show_settings", "Settings"),
            Binding("ctrl+b", "show_codebase", "Codebase"),
        ]
        
        def compose(self) -> ComposeResult:
            """Compose the screen layout"""
            yield Header(show_clock=True)
            
            with Container(id="main-container"):
                with Vertical(id="left-panel", classes="panel"):
                    yield Static("📝 Task Input", classes="section-title")
                    yield TextArea(
                        placeholder="Enter your task here...\n\nExample: Create a REST API endpoint with authentication\nUse Flask, SQLAlchemy, and include validation.",
                        id="task-input",
                        language="markdown"
                    )
                    with Horizontal(id="task-controls"):
                        yield Button("▶ Run Task", id="run-btn", variant="primary")
                        yield Button("📊 Metrics", id="metrics-btn")
                        yield Button("⚙️ Settings", id="settings-btn")
                
                with Vertical(id="right-panel", classes="panel"):
                    yield Static("📊 Results", classes="section-title")
                    # Task status indicator
                    yield Static("Status: Ready", id="task-status", classes="status-indicator")
                    with ScrollableContainer(id="results-container", classes="results"):
                        yield Static("Results will appear here after task execution", id="results-placeholder")
                    yield Log(id="output-log", max_lines=50, classes="log")
            
            yield Footer()
        
        def on_mount(self) -> None:
            """Called when screen is mounted"""
            self.app.sub_title = "Task Execution"
            task_input = self.query_one("#task-input", TextArea)
            task_input.focus()
            self.result = None
        
        def on_button_pressed(self, event: Button.Pressed) -> None:
            """Handle button presses"""
            if event.button.id == "run-btn":
                self.action_run_task()
            elif event.button.id == "metrics-btn":
                self.action_show_dashboard()
            elif event.button.id == "settings-btn":
                self.action_show_settings()
        
        def action_run_task(self) -> None:
            """Run the task (called by button or Ctrl+R)"""
            task_input = self.query_one("#task-input", TextArea)
            task = task_input.text.strip()
            
            if not task:
                self.app.notify("Please enter a task first", severity="warning")
                return
            
            output_log = self.query_one("#output-log", Log)
            results_container = self.query_one("#results-container", ScrollableContainer)
            status_indicator = self.query_one("#task-status", Static)
            
            # Clear previous results
            results_container.remove_children()
            output_log.clear()
            
            # Update status indicator
            status_indicator.update("Status: ⏳ Running...")
            
            # Update UI in main thread
            output_log.write("🚀 Starting task execution...")
            output_log.write(f"📋 Task: {task[:100]}...")
            
            try:
                # Get orchestrator from app
                orchestrator = self.app.orchestrator
                
                if not orchestrator:
                    status_indicator.update("Status: ❌ Orchestrator not ready")
                    output_log.write("❌ Orchestrator not initialized. Please wait for system initialization...")
                    self.app.notify("Orchestrator not ready yet. Please wait.", severity="warning")
                    return
                
                # Disable run button while task is running
                try:
                    run_btn = self.query_one("#run-btn", Button)
                    run_btn.disabled = True
                    run_btn.label = "⏳ Running..."
                except Exception:
                    pass
                
                # Run task in background thread to avoid blocking UI
                import threading
                thread = threading.Thread(
                    target=self.execute_task_sync,
                    args=(task,),
                    daemon=True
                )
                thread.start()
                
            except Exception as e:
                status_indicator.update("Status: ❌ Error")
                output_log.write(f"❌ Error: {str(e)}")
                self.app.notify(f"Error: {str(e)}", severity="error")
        
        def execute_task_sync(self, task: str) -> None:
            """Execute task synchronously in background thread"""
            try:
                # Update log using thread-safe method
                self._safe_log("📊 Analyzing complexity...")
                
                orchestrator = self.app.orchestrator
                if not orchestrator:
                    self._safe_log("❌ Orchestrator not available")
                    self._enable_run_button()
                    return
                
                # Execute task (this may take a while)
                self._safe_log("🔄 Executing task...")
                self._safe_log("⏳ This may take a moment, please wait...")
                
                result = orchestrator.build_with_validation_iterative(
                    task=task,
                    max_iterations=3
                )
                
                self.result = result
                
                # Update UI from main thread
                self.app.call_from_thread(self._display_results, result)
                self._enable_run_button()
                
            except Exception as e:
                import traceback
                error_msg = f"❌ Error during execution: {str(e)}"
                error_trace = traceback.format_exc()
                
                # Update UI from main thread
                def show_error():
                    try:
                        self._write_log(error_msg)
                        self._write_log(error_trace)
                        self.app.notify(f"Execution error: {str(e)}", severity="error")
                        self._enable_run_button()
                    except Exception:
                        pass
                
                self.app.call_from_thread(show_error)
        
        def _safe_log(self, message: str) -> None:
            """Thread-safe log update"""
            self.app.call_from_thread(self._write_log, message)
        
        def _enable_run_button(self) -> None:
            """Re-enable run button"""
            def enable():
                try:
                    run_btn = self.query_one("#run-btn", Button)
                    run_btn.disabled = False
                    run_btn.label = "▶ Run Task"
                except Exception:
                    pass
            self.app.call_from_thread(enable)
        
        def _write_log(self, message: str) -> None:
            """Write to log (called from main thread)"""
            try:
                output_log = self.query_one("#output-log", Log)
                output_log.write(message)
                
                # Update status indicator based on message
                try:
                    status_indicator = self.query_one("#task-status", Static)
                    if "Starting" in message or "Analyzing" in message:
                        status_indicator.update("Status: ⏳ Starting...")
                    elif "Executing" in message:
                        status_indicator.update("Status: ⏳ Executing...")
                    elif "Analyzing complexity" in message:
                        status_indicator.update("Status: 📊 Analyzing complexity...")
                    elif "Error" in message or "❌" in message:
                        status_indicator.update("Status: ❌ Error")
                except Exception:
                    pass
            except Exception:
                pass
        
        def _display_results(self, result: dict) -> None:
            """Display results (called from main thread)"""
            try:
                output_log = self.query_one("#output-log", Log)
                results_container = self.query_one("#results-container", ScrollableContainer)
                status_indicator = self.query_one("#task-status", Static)
                
                # Clear previous results
                results_container.remove_children()
                
                output_log.write("✅ Task execution complete!")
                
                # Display results
                if result.get("success"):
                    evaluation = result.get("evaluation")
                    score = evaluation.score if evaluation and hasattr(evaluation, 'score') else 0
                    output_log.write(f"✅ Success! Score: {score}/100")
                    
                    # Update status
                    status_indicator.update(f"Status: ✅ Complete (Score: {score}/100)")
                    
                    # Show result widget
                    result_widget = TaskResultWidget(result)
                    results_container.mount(result_widget)
                    
                    self.app.notify(f"✅ Task completed! Score: {score}/100", severity="success")
                else:
                    output_log.write("❌ Task execution failed")
                    status_indicator.update("Status: ❌ Failed")
                    
                    errors = result.get("validation", {}).get("errors", [])
                    if errors:
                        error_text = "❌ Errors:\n" + "\n".join(f"- {str(e)[:100]}" for e in errors[:5])
                        error_view = Static(error_text, classes="error-message")
                        results_container.mount(error_view)
                    
                    # Still show partial results
                    result_widget = TaskResultWidget(result)
                    results_container.mount(result_widget)
                    
                    self.app.notify("❌ Task execution failed", severity="error")
                    
            except Exception as e:
                import traceback
                status_indicator = self.query_one("#task-status", Static)
                status_indicator.update("Status: ❌ Error displaying results")
                output_log.write(f"❌ Error displaying results: {str(e)}")
                output_log.write(traceback.format_exc())
        
        def action_show_dashboard(self) -> None:
            """Switch to dashboard screen"""
            self.app.push_screen("dashboard")
        
        def action_show_settings(self) -> None:
            """Switch to settings screen"""
            self.app.push_screen("settings")
        
        def action_show_codebase(self) -> None:
            """Switch to codebase screen"""
            self.app.push_screen("codebase")
    
    
    class DashboardScreen(Screen):
        """Screen for viewing dashboards"""
        
        BINDINGS = [
            Binding("ctrl+q", "quit", "Quit"),
            Binding("escape", "app.pop_screen", "Back"),
        ]
        
        def compose(self) -> ComposeResult:
            """Compose the dashboard screen"""
            yield Header(show_clock=True)
            
            with Container(id="dashboard-container"):
                yield Tabs(
                    Tab("📊 Metrics", id="metrics-tab"),
                    Tab("🔍 Errors", id="errors-tab"),
                    Tab("🚦 Routing", id="routing-tab"),
                    Tab("💬 Feedback", id="feedback-tab"),
                    Tab("🧪 Tests", id="tests-tab"),
                    id="dashboard-tabs"
                )
                
                with ScrollableContainer(id="dashboard-content"):
                    yield Static("Select a tab to view dashboard", id="dashboard-placeholder")
            
            yield Footer()
        
        def on_mount(self) -> None:
            """Called when screen is mounted"""
            self.app.sub_title = "Dashboards"
            # Load first tab by default
            self.load_metrics()
        
        def on_tabs_tab_activated(self, event: Tabs.TabActivated) -> None:
            """Handle tab change"""
            content = self.query_one("#dashboard-content", ScrollableContainer)
            content.remove_children()
            
            tab_id = event.tab.id

            if tab_id == "metrics-tab":
                self.load_metrics()
            elif tab_id == "errors-tab":
                self.load_errors()
            elif tab_id == "routing-tab":
                self.load_routing()
            elif tab_id == "feedback-tab":
                self.load_feedback()
            elif tab_id == "tests-tab":
                self.load_tests()
        
        def load_metrics(self) -> None:
            """Load metrics dashboard"""
            content = self.query_one("#dashboard-content", ScrollableContainer)
            try:
                tracker = MetricsTracker()
                stats = tracker.get_metrics_summary(days=30)
                
                metrics_text = f"""# 📊 Metrics Dashboard

## Overall Statistics
- **Total Interactions**: {stats['total_interactions']}
- **Code Generation Accuracy**: {stats['code_generation_accuracy']:.1f}%
- **Test Pass Rate**: {stats['test_pass_rate']:.1f}%
- **Error Rate**: {stats['error_rate']:.1f}%
- **Success Rate**: {stats['success_rate']:.1f}%
- **Avg Response Time**: {stats['avg_response_time_ms']:.1f}ms
- **Avg Tokens Used**: {stats['avg_tokens_used']:.1f}

## By Task Type
"""
                if stats.get('by_task_type'):
                    for task_type, data in sorted(stats['by_task_type'].items()):
                        metrics_text += f"\n### {task_type.upper()}\n"
                        metrics_text += f"- Count: {data['count']}\n"
                        metrics_text += f"- Accuracy: {data['accuracy']:.1f}%\n"
                        metrics_text += f"- Test Pass Rate: {data['test_pass_rate']:.1f}%\n"
                else:
                    metrics_text += "\n*No task type data available yet*"
                
                markdown = Markdown(metrics_text)
                content.mount(markdown)
            except Exception as e:
                content.mount(Static(f"Error loading metrics: {str(e)}"))
        
        def load_errors(self) -> None:
            """Load error patterns dashboard"""
            content = self.query_one("#dashboard-content", ScrollableContainer)
            try:
                analyzer = EnhancedErrorAnalyzer(ERROR_PATTERN_DB)
                insights = analyzer.get_pattern_insights(days=30)
                stats = insights.get('statistics', {})
                top_patterns = insights.get('top_patterns', [])
                
                # Calculate total patterns from the patterns list
                total_patterns = len(top_patterns)
                
                errors_text = f"""# 🔍 Error Patterns Dashboard

## Statistics
- **Total Errors**: {stats.get('total_errors', 0)}
- **Total Patterns**: {total_patterns}
- **Fix Success Rate**: {stats.get('fix_success_rate', 0.0):.1f}%

## Top Error Patterns
"""
                if top_patterns:
                    for pattern in top_patterns[:10]:
                        # Handle both dict and object patterns
                        if isinstance(pattern, dict):
                            error_type = pattern.get('error_type', 'Unknown')
                            frequency = pattern.get('frequency', 0)
                            pattern_text = pattern.get('pattern', 'N/A')
                            task_type = pattern.get('task_type', 'Unknown')
                        else:
                            error_type = getattr(pattern, 'error_type', 'Unknown')
                            frequency = getattr(pattern, 'frequency', 0)
                            pattern_text = getattr(pattern, 'error_message_pattern', 'N/A')[:80]
                            task_type = getattr(pattern, 'task_type', 'Unknown')
                            
                        errors_text += f"\n### {error_type.upper()}\n"
                        errors_text += f"- Frequency: {frequency}\n"
                        errors_text += f"- Pattern: {pattern_text}...\n"
                        errors_text += f"- Task Type: {task_type}\n"
                else:
                    errors_text += "\n*No error patterns recorded yet*"
                
                markdown = Markdown(errors_text)
                content.mount(markdown)
            except Exception as e:
                import traceback
                error_msg = f"Error loading error patterns: {str(e)}\n{traceback.format_exc()}"
                content.mount(Static(error_msg))
        
        def load_routing(self) -> None:
            """Load routing statistics"""
            content = self.query_one("#dashboard-content", ScrollableContainer)
            try:
                stats = ROUTING_OPTIMIZER.get_routing_stats(days=30)
                
                routing_text = """# 🚦 Routing Statistics

## Overall Routing
"""
                if stats.get('overall'):
                    for route, data in stats['overall'].items():
                        routing_text += f"\n### {route.upper()}\n"
                        routing_text += f"- Count: {data['count']}\n"
                        routing_text += f"- Avg Score: {data['avg_score']:.1f}/100\n"
                        routing_text += f"- Avg Duration: {data['avg_duration']:.1f}ms\n"
                        routing_text += f"- Success Rate: {data['success_rate']:.1f}%\n"
                else:
                    routing_text += "\n*No routing data available yet*"
                
                routing_text += f"\n## Prediction Accuracy\n"
                routing_text += f"- Avg Prediction Error: {stats['avg_prediction_error']:.2f} points\n"
                
                markdown = Markdown(routing_text)
                content.mount(markdown)
            except Exception as e:
                content.mount(Static(f"Error loading routing stats: {str(e)}"))
        
        def load_feedback(self) -> None:
            """Load feedback dashboard"""
            content = self.query_one("#dashboard-content", ScrollableContainer)
            try:
                stats = FEEDBACK_COLLECTOR.get_feedback_statistics(days=30)
                
                feedback_text = f"""# 💬 Feedback Dashboard

## Overall Statistics
- **Total Feedback**: {stats['overall']['total']}
- **Average Rating**: {stats['overall']['avg_rating']:.1f}/5.0
- **Satisfaction Rate**: {stats['overall']['satisfaction_rate']:.1f}%

## Rating Distribution
"""
                if stats.get('rating_distribution'):
                    for rating, count in sorted(stats['rating_distribution'].items()):
                        feedback_text += f"- Rating {rating}: {count} feedback(s)\n"
                else:
                    feedback_text += "\n*No feedback ratings yet*"
                
                markdown = Markdown(feedback_text)
                content.mount(markdown)
            except Exception as e:
                content.mount(Static(f"Error loading feedback: {str(e)}"))
        
        def load_tests(self) -> None:
            """Load test suite dashboard"""
            content = self.query_one("#dashboard-content", ScrollableContainer)
            try:
                from tests.test_suite_framework import TEST_SUITE_FRAMEWORK
                
                tasks = TEST_SUITE_FRAMEWORK.load_tasks()
                
                tests_text = f"""# 🧪 Test Suite Dashboard

## Test Tasks
- **Total Tasks**: {len(tasks)}

## By Category
"""
                if tasks:
                    categories = {}
                    difficulties = {}
                    for task in tasks:
                        categories[task.category.value] = categories.get(task.category.value, 0) + 1
                        difficulties[task.difficulty.value] = difficulties.get(task.difficulty.value, 0) + 1
                    
                    for category, count in sorted(categories.items()):
                        tests_text += f"- **{category}**: {count} tasks\n"
                    
                    tests_text += "\n## By Difficulty\n"
                    for difficulty, count in sorted(difficulties.items()):
                        tests_text += f"- **{difficulty}**: {count} tasks\n"
                else:
                    tests_text += "\n*No test tasks loaded. Run: python3 tests/generate_test_tasks.py*"
                
                markdown = Markdown(tests_text)
                content.mount(markdown)
            except Exception as e:
                content.mount(Static(f"Error loading test suite: {str(e)}"))


    class CodebaseScreen(Screen):
        """Screen for codebase interaction"""
        
        BINDINGS = [
            Binding("escape", "app.pop_screen", "Back"),
            Binding("ctrl+f", "search_codebase", "Search"),
        ]
        
        def compose(self) -> ComposeResult:
            """Compose the codebase screen"""
            yield Header(show_clock=True)
            
            with Container(id="codebase-container"):
                with Horizontal(id="codebase-layout"):
                    with Vertical(id="file-tree-panel", classes="panel"):
                        yield Static("📁 Project Structure", classes="section-title")
                        yield DirectoryTree(str(project_root), id="file-tree")
                    
                    with Vertical(id="code-view-panel", classes="panel"):
                        yield Static("📄 File Contents", classes="section-title")
                        with ScrollableContainer(id="code-viewer"):
                            yield Static("Select a file to view its contents", id="code-placeholder")
                        
                        yield Input(placeholder="Search codebase...", id="search-input")
                
                with Vertical(id="search-results-panel"):
                    yield Static("🔍 Search Results", classes="section-title")
                    with ScrollableContainer(id="search-results"):
                        yield Static("Search results will appear here", id="search-placeholder")
            
            yield Footer()
        
        def on_mount(self) -> None:
            """Called when screen is mounted"""
            self.app.sub_title = "Codebase Browser"
        
        def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
            """Handle file selection"""
            file_path = Path(event.path)
            if file_path.exists() and file_path.is_file():
                try:
                    # Limit file size to avoid loading huge files
                    if file_path.stat().st_size > 100000:  # 100KB limit
                        content = f"File too large ({file_path.stat().st_size} bytes). Use search instead."
                    else:
                        content = file_path.read_text()
                    
                    code_viewer = self.query_one("#code-viewer", ScrollableContainer)
                    code_viewer.remove_children()
                    
                    # Show file with syntax highlighting if possible
                    code_display = Static(f"```python\n{content[:2000]}{'...' if len(content) > 2000 else ''}\n```")
                    code_viewer.mount(code_display)
                    
                except Exception as e:
                    code_viewer = self.query_one("#code-viewer", ScrollableContainer)
                    code_viewer.remove_children()
                    code_viewer.mount(Static(f"Error reading file: {str(e)}"))


    class SettingsScreen(Screen):
        """Screen for settings and configuration"""
        
        BINDINGS = [
            Binding("escape", "app.pop_screen", "Back"),
        ]
        
        def compose(self) -> ComposeResult:
            """Compose the settings screen"""
            yield Header(show_clock=True)
            
            with Container(id="settings-container"):
                yield Static("⚙️ Settings", classes="section-title")
                
                with ScrollableContainer(id="settings-content"):
                    # Model Configuration
                    yield Static("Model Configuration", classes="subsection-title")
                    yield Static("Routing Threshold: 8", id="routing-threshold")
                    yield Static("Complexity Threshold: 8", id="complexity-threshold")
                    
                    # Agent Configuration
                    yield Static("Agent Configuration", classes="subsection-title")
                    yield Static("Implementation Agent: qwen2.5-coder:7b", id="impl-agent")
                    yield Static("Test Generator: qwen2.5-coder:14b", id="test-agent")
                    yield Static("Validation Agent: qwen2.5-coder:7b", id="validation-agent")
                    
                    # System Status
                    yield Static("System Status", classes="subsection-title")
                    yield Static("✅ Metrics Tracker: Active", id="metrics-status")
                    yield Static("✅ Error Learning: Active", id="error-status")
                    yield Static("✅ Routing Optimizer: Active", id="routing-status")
                    yield Static("✅ Feedback Collector: Active", id="feedback-status")
                    yield Static("✅ Test Suite: Active", id="test-status")
            
            yield Footer()
        
        def on_mount(self) -> None:
            """Called when screen is mounted"""
            self.app.sub_title = "Settings"
            
            # Update status dynamically
            try:
                # Check system status
                from tests.test_suite_framework import TEST_SUITE_FRAMEWORK
                tasks = TEST_SUITE_FRAMEWORK.load_tasks()
                
                test_status = self.query_one("#test-status", Static)
                test_status.update(f"✅ Test Suite: Active ({len(tasks)} tasks)")
            except Exception as e:
                pass


    class AI_Coding_Team_TUI(App):
        """Main TUI application"""
        
        CSS = """
        Screen {
            background: $surface;
        }
        
        #main-container {
            layout: horizontal;
            width: 100%;
            height: 100%;
        }
        
        .panel {
            border: solid $primary;
            margin: 1;
            padding: 1;
        }
        
        #left-panel {
            width: 50%;
            border-right: wide $primary;
        }
        
        #right-panel {
            width: 50%;
        }
        
        #task-controls {
            height: auto;
            align: center middle;
            padding: 1;
        }
        
        #results-container {
            height: 1fr;
            border: solid $primary;
            padding: 1;
        }
        
        #output-log {
            height: 15;
            border: solid $primary;
            padding: 1;
        }
        
        .section-title {
            text-style: bold;
            color: $accent;
            padding: 1;
            margin: 1;
        }
        
        .subsection-title {
            text-style: bold;
            padding: 1;
            margin-top: 1;
        }
        
        #dashboard-container {
            width: 100%;
            height: 100%;
        }
        
        #dashboard-content {
            height: 1fr;
            padding: 1;
        }
        
        .result-container {
            border: solid $primary;
            padding: 1;
            margin: 1;
        }
        
        .status {
            text-style: bold;
            padding: 1;
        }
        
        .code-preview {
            background: $panel;
            padding: 1;
        }
        
        .error-message {
            color: $error;
            padding: 1;
        }
        
        .status-indicator {
            text-style: bold;
            padding: 1;
            margin-bottom: 1;
            border: round $primary;
            background: $panel;
        }
        
        #codebase-container {
            layout: horizontal;
            width: 100%;
            height: 100%;
        }
        
        #file-tree-panel {
            width: 30%;
        }
        
        #code-view-panel {
            width: 70%;
        }
        """
        
        TITLE = "AI Coding Team"
        SUB_TITLE = "Intelligent Software Development"
        
        BINDINGS = [
            Binding("ctrl+q", "quit", "Quit"),
            Binding("ctrl+d", "show_dashboard", "Dashboard"),
            Binding("ctrl+s", "show_settings", "Settings"),
            Binding("ctrl+b", "show_codebase", "Codebase"),
        ]
        
        def __init__(self):
            """Initialize the TUI app"""
            super().__init__()
            self.orchestrator: Optional[Orchestrator] = None
        
        def on_mount(self) -> None:
            """Called when app is mounted"""
            try:
                # Initialize orchestrator in background
                self.set_timer(0.1, self.initialize_system)
            except Exception as e:
                self.notify(f"Error initializing: {str(e)}", severity="error")
        
        def initialize_system(self) -> None:
            """Initialize system components"""
            try:
                self.notify("Initializing system...", severity="information")
                self.orchestrator = Orchestrator()
                self.notify("✅ System ready!", severity="success")
            except Exception as e:
                self.notify(f"Error initializing: {str(e)}", severity="error")
        
        def compose(self) -> ComposeResult:
            """Compose the main app layout"""
            # Start with task input screen
            yield from TaskInputScreen().compose()
        
        def action_show_dashboard(self) -> None:
            """Show dashboard screen"""
            self.push_screen(DashboardScreen())
        
        def action_show_settings(self) -> None:
            """Show settings screen"""
            self.push_screen(SettingsScreen())
        
        def action_show_codebase(self) -> None:
            """Show codebase screen"""
            self.push_screen(CodebaseScreen())
    
    
    def main():
        """Main entry point"""
        if not TEXTUAL_AVAILABLE:
            print("❌ Textual library is required")
            print("Install it with: pip install textual")
            sys.exit(1)
        
        app = AI_Coding_Team_TUI()
        app.run()
    
    
    if __name__ == "__main__":
        main()

else:
    # Fallback if textual not available
    def main():
        print("Textual library is required. Please install it first.")
        sys.exit(1)
    
    if __name__ == "__main__":
        main()

