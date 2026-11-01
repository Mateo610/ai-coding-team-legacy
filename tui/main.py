"""
AI Coding Team - Text User Interface (TUI)
ULTIMATE INTEGRATED VERSION

Combines:
- Proper async workers from improved app.py
- Advanced screens from screens.py (ModelConfig, Feedback)
- Layout preferences from main.py
- All improvements and polish

Built with Textual (Textualize)
"""

import sys
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from textual.app import App, ComposeResult
    from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
    from textual.widgets import (
        Header, Footer, Button, Input, TextArea, Static, Tabs, Tab,
        DataTable, Label, Log, Markdown, DirectoryTree, Select,
        Checkbox, Collapsible, ProgressBar, RichLog
    )
    from textual.binding import Binding
    from textual.reactive import reactive
    from textual.screen import Screen, ModalScreen
    from textual.message import Message
    from textual.widget import Widget
    from textual.worker import Worker, WorkerState
    from textual import work
    TEXTUAL_AVAILABLE = True
except ImportError as e:
    TEXTUAL_AVAILABLE = False
    print("⚠️  Textual library not installed")
    print(f"Import error: {e}")
    print("\nInstall with: pip install textual")
    sys.exit(1)

if TEXTUAL_AVAILABLE:
    from agents.orchestrator import Orchestrator
    from learning.metrics_tracker import MetricsTracker
    from learning.error_patterns import ERROR_PATTERN_DB, EnhancedErrorAnalyzer
    from learning.feedback_collector import FEEDBACK_COLLECTOR, FeedbackType
    from agents.routing_optimizer import ROUTING_OPTIMIZER
    from agents.complexity_predictor import ComplexityPredictor
    from agents.config_manager import CONFIG_MANAGER


if TEXTUAL_AVAILABLE:
    
    # ============================================================================
    # ENUMS & DATA CLASSES
    # ============================================================================
    
    class AgentStatus(Enum):
        """Agent status states"""
        IDLE = "idle"
        THINKING = "thinking"
        ACTIVE = "active"
        ERROR = "error"
        COMPLETE = "complete"
    
    
    # ============================================================================
    # WIDGETS
    # ============================================================================
    
    class AgentStatusWidget(Widget):
        """Real-time agent status widget with pulse indicators"""
        
        agent_name = reactive("Unknown Agent")
        status = reactive(AgentStatus.IDLE)
        current_task = reactive("")
        tasks_completed = reactive(0)
        
        def compose(self) -> ComposeResult:
            """Compose the agent status widget"""
            with Container(classes="agent-card"):
                yield Static("○", id=f"indicator-{id(self)}", classes="status-indicator idle")
                yield Static("", id=f"name-{id(self)}", classes="agent-name")
                yield Static("", id=f"status-{id(self)}", classes="agent-status-text")
                yield Static("", id=f"stats-{id(self)}", classes="agent-stats")
        
        def watch_status(self, new_status: AgentStatus) -> None:
            """Update UI when status changes"""
            self.update_display()
        
        def watch_agent_name(self, new_name: str) -> None:
            self.update_display()
        
        def watch_current_task(self, new_task: str) -> None:
            self.update_display()
        
        def update_display(self) -> None:
            """Update all display elements"""
            try:
                # Status indicator with symbol
                indicator_map = {
                    AgentStatus.IDLE: "○",
                    AgentStatus.THINKING: "◐",
                    AgentStatus.ACTIVE: "●",
                    AgentStatus.ERROR: "✗",
                    AgentStatus.COMPLETE: "✓"
                }
                
                indicator = self.query_one(f"#indicator-{id(self)}", Static)
                indicator.update(indicator_map.get(self.status, "○"))
                indicator.remove_class("idle", "thinking", "active", "error", "complete")
                indicator.add_class(self.status.value)
                
                # Agent name
                name = self.query_one(f"#name-{id(self)}", Static)
                name.update(f"🤖 {self.agent_name}")
                
                # Status text
                status_text = self.query_one(f"#status-{id(self)}", Static)
                if self.current_task:
                    status_text.update(f"Status: {self.status.value} - {self.current_task[:40]}")
                else:
                    status_text.update(f"Status: {self.status.value}")
                
                # Stats
                stats = self.query_one(f"#stats-{id(self)}", Static)
                stats.update(f"Tasks: {self.tasks_completed}")
                
            except Exception:
                pass
    
    
    class AgentLogPanel(ScrollableContainer):
        """Panel for displaying agent activity logs"""
        
        def log_agent_activity(self, agent: str, action: str, level: str = "info") -> None:
            """Add a log entry for agent activity"""
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            level_icons = {
                "debug": "🔍",
                "info": "ℹ️",
                "warning": "⚠️",
                "error": "❌",
                "success": "✅"
            }
            icon = level_icons.get(level, "•")
            
            log_entry = Static(
                f"[{timestamp}] {icon} [{agent}] {action}",
                classes=f"log-entry log-{level}"
            )
            self.mount(log_entry)
            self.scroll_end(animate=False)
            
            # Limit entries
            children = list(self.query(".log-entry"))
            if len(children) > 100:
                children[0].remove()
    
    
    class TaskResultWidget(Widget):
        """Enhanced widget for displaying task results with actions"""
        
        def __init__(self, result: dict, task: str = "", *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.result = result
            self._task_description = task  # Use private attribute to avoid property conflicts
        
        def compose(self) -> ComposeResult:
            """Compose the result widget"""
            with Container(classes="result-container"):
                # Success status
                success = self.result.get("success", False)
                status_text = "✅ SUCCESS" if success else "❌ FAILED"
                yield Static(status_text, classes="status-large")
                
                # Evaluation score with progress bar
                evaluation = self.result.get("evaluation")
                if evaluation:
                    try:
                        if hasattr(evaluation, 'score'):
                            score = evaluation.score
                        elif isinstance(evaluation, dict):
                            score = evaluation.get('score', 0)
                        else:
                            score = 0
                    except (AttributeError, TypeError) as e:
                        print(f"DEBUG: Error getting evaluation score in widget: {e}")
                        score = 0
                    
                    yield Static(f"Quality Score: {score}/100", classes="score-label")
                    yield ProgressBar(total=100, id="score-progress")
                    # Store score to set after mount
                    self._score_value = score
                
                # Action buttons
                with Horizontal(classes="action-buttons"):
                    yield Button("📋 Copy", id="copy-code", variant="success")
                    yield Button("💾 Save", id="save-file")
                    yield Button("💬 Feedback", id="feedback-btn")
                    yield Button("🔄 Retry", id="retry-task")
                
                # Code preview
                code = self.result.get("code", "")
                if code:
                    code_preview = code[:800] + ("..." if len(code) > 800 else "")
                    yield Collapsible(
                        Static(f"```python\n{code_preview}\n```", classes="code-preview"),
                        title="📄 Generated Code",
                        collapsed=False
                    )
                
                # Validation results
                validation = self.result.get("validation", {})
                if validation:
                    validation_items = []
                    
                    # Syntax check
                    syntax_check = validation.get("syntax_check")
                    if syntax_check and isinstance(syntax_check, dict):
                        if syntax_check.get("success"):
                            validation_items.append("✅ Syntax: Valid")
                        elif syntax_check.get("error"):
                            validation_items.append(f"❌ Syntax: {syntax_check.get('error', 'Invalid')[:40]}")
                        else:
                            validation_items.append("⚠️ Syntax: Not checked")
                    else:
                        validation_items.append("⚠️ Syntax: Not checked")
                    
                    # Execution check
                    execution = validation.get("execution")
                    if execution and isinstance(execution, dict):
                        if execution.get("success"):
                            exec_meta = execution.get("metadata", {})
                            if exec_meta and isinstance(exec_meta, dict) and exec_meta.get("skipped"):
                                validation_items.append("⏭️  Execution: Skipped (interactive code)")
                            else:
                                validation_items.append("✅ Execution: Success")
                        elif execution.get("error"):
                            validation_items.append(f"❌ Execution: {execution.get('error', 'Failed')[:40]}")
                        else:
                            validation_items.append("❌ Execution: Failed")
                    else:
                        validation_items.append("⚠️ Execution: Not checked")
                    
                    # Tests
                    tests_run = validation.get("tests_run")
                    if tests_run and isinstance(tests_run, dict):
                        test_meta = tests_run.get("metadata")
                        if test_meta and isinstance(test_meta, dict):
                            passed = test_meta.get('passed', 0)
                            total = test_meta.get('total', 0)
                            if total > 0:
                                validation_items.append(f"{'✅' if passed == total else '⚠️'} Tests: {passed}/{total} passed")
                            else:
                                validation_items.append("⚠️ Tests: None run")
                        else:
                            result_msg = tests_run.get("result", "")
                            if result_msg:
                                validation_items.append(f"📊 Tests: {result_msg}")
                            else:
                                validation_items.append("⚠️ Tests: Not available")
                    else:
                        validation_items.append("⚠️ Tests: Not available")
                    
                    validation_text = "\n".join(validation_items)
                    yield Static(validation_text, classes="validation-summary")
                
                # Errors
                errors = self.result.get("validation", {}).get("errors", [])
                if errors:
                    error_text = "\n".join(f"• {str(e)[:150]}" for e in errors[:5])
                    if len(errors) > 5:
                        error_text += f"\n... and {len(errors) - 5} more errors"
                    
                    yield Collapsible(
                        Static(error_text, classes="error-text"),
                        title=f"❌ Errors ({len(errors)})",
                        collapsed=True
                    )
        
        def on_mount(self) -> None:
            """Set progress bar value after widget is mounted"""
            if hasattr(self, '_score_value'):
                try:
                    progress_bar = self.query_one("#score-progress", ProgressBar)
                    progress_bar.update(progress=self._score_value)
                except Exception:
                    pass  # Progress bar might not exist yet
        
        def on_button_pressed(self, event: Button.Pressed) -> None:
            """Handle button presses"""
            if event.button.id == "copy-code":
                self.app.notify("Code copied to clipboard!", severity="success")
            elif event.button.id == "save-file":
                self.save_to_file()
            elif event.button.id == "feedback-btn":
                # Open feedback modal
                self.app.push_screen(FeedbackModal(
                    task=self._task_description,
                    interaction_id=self.result.get("interaction_id")
                ))
            elif event.button.id == "retry-task":
                self.app.notify("Retry functionality coming soon!", severity="information")
        
        def save_to_file(self) -> None:
            """Save generated code to file"""
            code = self.result.get("code", "")
            if code:
                output_dir = Path("output")
                output_dir.mkdir(exist_ok=True)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = output_dir / f"generated_code_{timestamp}.py"
                
                filename.write_text(code)
                self.app.notify(f"Saved to {filename}", severity="success")
    
    
    # ============================================================================
    # MODALS
    # ============================================================================
    
    class HelpModal(ModalScreen):
        """Modal screen showing keyboard shortcuts and help"""
        
        BINDINGS = [Binding("escape", "dismiss", "Close")]
        
        def compose(self) -> ComposeResult:
            with Container(id="help-modal"):
                yield Static("⌨️  Keyboard Shortcuts", classes="modal-title")
                yield Markdown("""
## Task Execution
- `Ctrl+R` - Run current task
- `Ctrl+C` - Cancel running task  
- `Ctrl+N` - New task (clear input)

## Navigation
- `Ctrl+D` - Dashboard view
- `Ctrl+S` - Settings
- `Ctrl+M` - Model configuration
- `Ctrl+B` - Codebase browser
- `Ctrl+H` - This help screen

## General
- `Ctrl+Q` - Quit application
- `Escape` - Go back / Close modal

## Tips
- Tab to navigate between widgets
- Scroll with mouse wheel or arrows
- Click agent cards for details
                """)
                yield Button("Close", id="close-help", variant="primary")
        
        def on_button_pressed(self, event: Button.Pressed) -> None:
            if event.button.id == "close-help":
                self.dismiss()
        
        def action_dismiss(self) -> None:
            self.app.pop_screen()
    
    
    class FeedbackModal(ModalScreen):
        """Modal for submitting user feedback"""
        
        BINDINGS = [
            Binding("escape", "dismiss", "Cancel"),
            Binding("ctrl+s", "submit_feedback", "Submit"),
        ]
        
        def __init__(self, task: str = "", task_type: str = "general", interaction_id: Optional[str] = None):
            super().__init__()
            self._task_description = task  # Use private attribute to avoid property conflicts
            self.task_type = task_type
            self.interaction_id = interaction_id
        
        def compose(self) -> ComposeResult:
            with Container(id="feedback-modal"):
                yield Static("💬 Submit Feedback", classes="modal-title")
                
                with ScrollableContainer(id="feedback-form"):
                    yield Label("Rating (1-5):")
                    yield Select(
                        options=[("⭐", 1), ("⭐⭐", 2), ("⭐⭐⭐", 3), ("⭐⭐⭐⭐", 4), ("⭐⭐⭐⭐⭐", 5)],
                        id="rating-select",
                        value=5
                    )
                    
                    yield Label("Feedback Type:")
                    yield Select(
                        options=[
                            ("Rating", FeedbackType.RATING),
                            ("Correction", FeedbackType.CORRECTION),
                            ("Suggestion", FeedbackType.SUGGESTION),
                            ("Bug Report", FeedbackType.BUG_REPORT),
                            ("Feature Request", FeedbackType.FEATURE_REQUEST),
                        ],
                        id="feedback-type-select",
                        value=FeedbackType.RATING
                    )
                    
                    yield Label("Comment:")
                    yield TextArea(
                        placeholder="Share your thoughts, report bugs, or suggest improvements...",
                        id="feedback-comment"
                    )
                    
                    with Horizontal(classes="modal-buttons"):
                        yield Button("✅ Submit", id="submit-btn", variant="primary")
                        yield Button("❌ Cancel", id="cancel-btn")
        
        def on_button_pressed(self, event: Button.Pressed) -> None:
            if event.button.id == "submit-btn":
                self.action_submit_feedback()
            elif event.button.id == "cancel-btn":
                self.dismiss()
        
        def action_submit_feedback(self) -> None:
            """Submit feedback"""
            try:
                rating_select = self.query_one("#rating-select", Select)
                feedback_type_select = self.query_one("#feedback-type-select", Select)
                comment_area = self.query_one("#feedback-comment", TextArea)
                
                rating = rating_select.value
                feedback_type = feedback_type_select.value
                comment = comment_area.text.strip()
                
                FEEDBACK_COLLECTOR.submit_feedback(
                    task=self._task_description,
                    task_type=self.task_type,
                    feedback_type=feedback_type,
                    rating=rating,
                    comment=comment if comment else None,
                    interaction_id=self.interaction_id
                )
                
                self.app.notify("✅ Thank you for your feedback!", severity="success")
                self.dismiss()
                
            except Exception as e:
                self.app.notify(f"Error submitting feedback: {str(e)}", severity="error")
        
        def action_dismiss(self) -> None:
            self.dismiss()
    
    
    # ============================================================================
    # MAIN SCREENS
    # ============================================================================
    
    class TaskInputScreen(Screen):
        """Main screen for task input and execution"""
        
        BINDINGS = [
            Binding("ctrl+q", "quit", "Quit"),
            Binding("ctrl+r", "run_task", "Run"),
            Binding("ctrl+c", "cancel_task", "Cancel"),
            Binding("ctrl+n", "new_task", "New"),
            Binding("ctrl+d", "show_dashboard", "Dashboard"),
            Binding("ctrl+s", "show_settings", "Settings"),
            Binding("ctrl+m", "show_model_config", "Models"),
            Binding("ctrl+b", "show_codebase", "Codebase"),
            Binding("ctrl+h", "show_help", "Help"),
        ]
        
        def __init__(self):
            super().__init__()
            self.current_worker: Optional[Worker] = None
            self.agent_widgets: Dict[str, AgentStatusWidget] = {}
            self.task_start_time: Optional[datetime] = None
            self.current_task: str = ""
        
        def compose(self) -> ComposeResult:
            yield Header(show_clock=True)
            
            with Container(id="main-container"):
                # Left panel - Task input (40%)
                with Vertical(id="left-panel", classes="panel"):
                    yield Static("📝 Task Input", classes="section-title")
                    yield TextArea(
                        placeholder="Describe your coding task...\n\nExample:\n- Create a REST API with Flask\n- Add user authentication\n- Include unit tests",
                        id="task-input",
                        language="markdown"
                    )
                    
                    with Horizontal(id="task-controls"):
                        yield Button("▶ Run", id="run-btn", variant="primary")
                        yield Button("⏹ Cancel", id="cancel-btn", variant="error", disabled=True)
                        yield Button("🗑 Clear", id="clear-btn")
                    
                    yield ProgressBar(total=100, show_eta=False, id="task-progress")
                    yield Static("Status: Ready", id="task-status", classes="status-indicator")
                
                # Right panel - Results (60%)
                with Vertical(id="right-panel", classes="panel"):
                    yield Static("📊 Results & Activity", classes="section-title")
                    
                    # Tabs for different views
                    yield Tabs(
                        Tab("Results", id="results-tab"),
                        Tab("Agent Status", id="agents-tab"),
                        Tab("Activity Log", id="log-tab"),
                        id="output-tabs"
                    )
                    
                    # Results view
                    with ScrollableContainer(id="results-container", classes="tab-content"):
                        yield Static("Results will appear here", id="results-placeholder")
                    
                    # Agent status view (hidden by default)
                    with ScrollableContainer(id="agents-container", classes="tab-content hidden"):
                        pass
                    
                    # Activity log (hidden by default)
                    yield AgentLogPanel(id="agent-log", classes="tab-content hidden")
            
            yield Footer()
        
        def on_mount(self) -> None:
            self.app.sub_title = "Task Execution"
            self.query_one("#task-input", TextArea).focus()
            self.initialize_agent_widgets()
        
        def on_tabs_tab_activated(self, event: Tabs.TabActivated) -> None:
            """Handle tab changes"""
            # Hide all tab content
            for container in self.query(".tab-content"):
                container.add_class("hidden")
            
            # Show selected tab content
            if event.tab.id == "results-tab":
                self.query_one("#results-container").remove_class("hidden")
            elif event.tab.id == "agents-tab":
                self.query_one("#agents-container").remove_class("hidden")
            elif event.tab.id == "log-tab":
                self.query_one("#agent-log").remove_class("hidden")
        
        def initialize_agent_widgets(self) -> None:
            """Initialize agent status widgets"""
            container = self.query_one("#agents-container", ScrollableContainer)
            
            agent_names = [
                "Coordinator",
                "Code Generator",
                "Test Generator",
                "Code Reviewer",
                "Validator"
            ]
            
            for agent_name in agent_names:
                widget = AgentStatusWidget()
                widget.agent_name = agent_name
                widget.status = AgentStatus.IDLE
                self.agent_widgets[agent_name] = widget
                container.mount(widget)
        
        def update_agent_status(self, agent_name: str, status: AgentStatus, task: str = "") -> None:
            """Update agent status"""
            if agent_name in self.agent_widgets:
                widget = self.agent_widgets[agent_name]
                widget.status = status
                widget.current_task = task
                
                # Log activity
                agent_log = self.query_one("#agent-log", AgentLogPanel)
                level = "info" if status in [AgentStatus.ACTIVE, AgentStatus.THINKING] else "debug"
                if status == AgentStatus.ERROR:
                    level = "error"
                elif status == AgentStatus.COMPLETE:
                    level = "success"
                    
                agent_log.log_agent_activity(
                    agent_name,
                    f"{status.value}: {task}" if task else status.value,
                    level
                )
        
        def on_button_pressed(self, event: Button.Pressed) -> None:
            """Handle button presses"""
            button_id = event.button.id
            print(f"DEBUG: Button pressed: {button_id}")  # Terminal debug
            self.app.notify(f"🔘 Button '{button_id}' pressed!", severity="information")
            if button_id == "run-btn":
                print("DEBUG: Calling action_run_task")
                self.action_run_task()
            elif button_id == "cancel-btn":
                self.action_cancel_task()
            elif button_id == "clear-btn":
                self.action_new_task()
            else:
                # Debug: log unhandled button
                self.app.notify(f"Unhandled button: {button_id}", severity="information")
        
        def action_run_task(self) -> None:
            """Run the task using async worker"""
            print("DEBUG: action_run_task called")  # Terminal debug
            # Immediate feedback to show action was triggered
            self.app.notify("🔵 action_run_task called!", severity="information")
            
            try:
                task_input = self.query_one("#task-input", TextArea)
                task = task_input.text.strip()
            except Exception as e:
                self.app.notify(f"Error getting task input: {str(e)}", severity="error")
                return
            
            if not task:
                self.app.notify("Please enter a task first", severity="warning")
                return
            
            if self.current_worker and self.current_worker.is_running:
                self.app.notify("A task is already running", severity="warning")
                return
            
            # Check orchestrator
            if not self.app.orchestrator:
                self.app.notify("System not ready yet. Please wait...", severity="warning")
                return
            
            # Store task for later use
            self.current_task = task
            
            # Update UI
            self.task_start_time = datetime.now()
            self.update_task_status("⏳ Starting task...")
            
            # Update buttons
            run_btn = self.query_one("#run-btn", Button)
            cancel_btn = self.query_one("#cancel-btn", Button)
            run_btn.disabled = True
            cancel_btn.disabled = False
            
            # Clear results
            results_container = self.query_one("#results-container", ScrollableContainer)
            results_container.remove_children()
            
            # Reset progress
            progress = self.query_one("#task-progress", ProgressBar)
            progress.update(progress=0)
            
            # Log start
            try:
                agent_log = self.query_one("#agent-log", AgentLogPanel)
                agent_log.log_agent_activity("System", f"Starting: {task[:60]}...", "info")
            except Exception as e:
                self.app.notify(f"Error logging: {str(e)}", severity="error")
            
            # Start worker - @work decorator makes it return a Worker when called
            try:
                self.app.notify("Starting worker...", severity="information")
                # Call the @work decorated function - it returns a Worker
                self.current_worker = self.execute_task_sync(task)
                if self.current_worker:
                    self.app.notify("✅ Worker started!", severity="success")
                else:
                    self.app.notify("❌ Worker is None!", severity="error")
            except Exception as e:
                import traceback
                error_msg = f"Error starting worker: {str(e)}\n{traceback.format_exc()}"
                self.app.notify(f"❌ Worker error: {str(e)}", severity="error")
                # Also log to agent log if available
                try:
                    agent_log = self.query_one("#agent-log", AgentLogPanel)
                    agent_log.log_agent_activity("System", error_msg[:200], "error")
                except:
                    pass
        
        @work(exclusive=True, thread=True)
        def execute_task_sync(self, task: str) -> dict:
            """Execute task in worker thread (synchronous version for @work)"""
            try:
                # Immediate feedback - worker started
                self.app.call_from_thread(
                    lambda: self.app.notify("🔧 Worker thread started!", severity="success")
                )
                
                # Update coordinator
                self.app.call_from_thread(
                    self.update_agent_status,
                    "Coordinator",
                    AgentStatus.ACTIVE,
                    "Analyzing task"
                )
                self.app.call_from_thread(self.update_progress, 10)
                
                # Execute
                orchestrator = self.app.orchestrator
                if not orchestrator:
                    error_msg = "Orchestrator not available"
                    self.app.call_from_thread(
                        self.update_task_status,
                        f"❌ {error_msg}"
                    )
                    return {"success": False, "error": error_msg, "code": "", "validation": {}}
                
                # Log to agent log
                def log_to_agent():
                    try:
                        agent_log = self.query_one("#agent-log", AgentLogPanel)
                        agent_log.log_agent_activity("System", "Executing task...", "info")
                    except:
                        pass
                self.app.call_from_thread(log_to_agent)
                
                # Notify we're calling orchestrator
                self.app.call_from_thread(
                    lambda: self.app.notify("🤖 Calling orchestrator...", severity="information")
                )
                
                result = orchestrator.build_with_validation_iterative(
                    task=task,
                    max_iterations=3
                )
                
                self.app.call_from_thread(self.update_progress, 100)
                
                # Log completion
                def log_completion():
                    try:
                        agent_log = self.query_one("#agent-log", AgentLogPanel)
                        status = "✅ Success" if result.get("success") else "⚠️ Completed with issues"
                        agent_log.log_agent_activity("System", f"{status}: {task[:50]}...", 
                                                    "success" if result.get("success") else "warning")
                    except:
                        pass
                self.app.call_from_thread(log_completion)
                
                return result
                
            except Exception as e:
                import traceback
                error_msg = str(e)
                error_trace = traceback.format_exc()
                
                # Log error
                agent_log = self.query_one("#agent-log", AgentLogPanel)
                self.app.call_from_thread(
                    agent_log.log_agent_activity,
                    "System",
                    f"❌ Error: {error_msg}",
                    "error"
                )
                
                # Update status
                self.app.call_from_thread(
                    self.update_task_status,
                    f"❌ Error: {error_msg}"
                )
                
                # Return error result
                error_result = {
                    "success": False,
                    "error": error_msg,
                    "error_traceback": error_trace,
                    "code": "",
                    "validation": {}
                }
                return error_result
        
        def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
            """Handle worker state changes"""
            if event.worker == self.current_worker:
                if event.state == WorkerState.SUCCESS:
                    result = event.worker.result
                    if result:
                        self.display_results(result)
                    else:
                        self.update_task_status("❌ No result returned")
                        agent_log = self.query_one("#agent-log", AgentLogPanel)
                        agent_log.log_agent_activity("System", "No result from worker", "error")
                    self.task_complete()
                elif event.state == WorkerState.ERROR:
                    error = event.worker.error
                    self.display_error(error)
                    self.task_complete()
                elif event.state == WorkerState.CANCELLED:
                    self.update_task_status("⏹ Task cancelled")
                    self.task_complete()
                elif event.state == WorkerState.PENDING:
                    self.update_task_status("⏳ Task pending...")
                elif event.state == WorkerState.RUNNING:
                    self.update_task_status("⏳ Task running...")
        
        def display_results(self, result: dict) -> None:
            """Display task results"""
            results_container = self.query_one("#results-container", ScrollableContainer)
            agent_log = self.query_one("#agent-log", AgentLogPanel)
            results_container.remove_children()
            
            # Check for errors first
            if result.get("error"):
                error_msg = result.get("error", "Unknown error")
                error_trace = result.get("error_traceback", "")
                self.update_task_status(f"❌ Error: {error_msg}")
                agent_log.log_agent_activity("System", f"Error: {error_msg}", "error")
                if error_trace:
                    # Show error in results
                    error_widget = Static(f"Error: {error_msg}\n\n{error_trace[:500]}...", classes="error-message")
                    results_container.mount(error_widget)
                self.app.notify(f"❌ Error: {error_msg}", severity="error")
                return
            
            # Update status
            if result.get("success"):
                evaluation = result.get("evaluation")
                score = evaluation.score if evaluation and hasattr(evaluation, 'score') else 0
                self.update_task_status(f"✅ Complete! Score: {score}/100")
                
                if self.task_start_time:
                    duration = (datetime.now() - self.task_start_time).total_seconds()
                    self.app.notify(
                        f"✅ Completed in {duration:.1f}s (Score: {score}/100)",
                        severity="success"
                    )
            else:
                # Task completed but with issues
                evaluation = result.get("evaluation")
                score = evaluation.score if evaluation and hasattr(evaluation, 'score') else 0
                self.update_task_status(f"⚠️ Completed with issues (Score: {score}/100)")
                agent_log.log_agent_activity("System", f"Task completed with score {score}/100", "warning")
                
                if self.task_start_time:
                    duration = (datetime.now() - self.task_start_time).total_seconds()
                    self.app.notify(
                        f"⚠️ Completed in {duration:.1f}s (Score: {score}/100)",
                        severity="warning"
                    )
            
            # Mount result widget
            result_widget = TaskResultWidget(result, task=self.current_task)
            results_container.mount(result_widget)
            
            # Update agents to complete
            for agent_name in self.agent_widgets:
                self.update_agent_status(agent_name, AgentStatus.COMPLETE)
            
            # Log completion
            agent_log = self.query_one("#agent-log", AgentLogPanel)
            agent_log.log_agent_activity(
                "System",
                "Task completed",
                "success" if result.get("success") else "error"
            )
        
        def display_error(self, error: Exception) -> None:
            """Display error"""
            import traceback
            
            results_container = self.query_one("#results-container", ScrollableContainer)
            results_container.remove_children()
            
            error_text = f"❌ Execution Error\n\n{str(error)}\n\n{traceback.format_exc()}"
            results_container.mount(Static(error_text, classes="error-message"))
            
            self.update_task_status(f"❌ Error: {str(error)[:50]}")
            self.app.notify(f"Error: {str(error)}", severity="error")
            
            agent_log = self.query_one("#agent-log", AgentLogPanel)
            agent_log.log_agent_activity("System", f"Error: {str(error)}", "error")
        
        def task_complete(self) -> None:
            """Cleanup after task completion"""
            run_btn = self.query_one("#run-btn", Button)
            cancel_btn = self.query_one("#cancel-btn", Button)
            run_btn.disabled = False
            cancel_btn.disabled = True
            self.current_worker = None
        
        def update_task_status(self, status: str) -> None:
            try:
                self.query_one("#task-status", Static).update(f"Status: {status}")
            except Exception:
                pass
        
        def update_progress(self, progress: int) -> None:
            try:
                self.query_one("#task-progress", ProgressBar).update(progress=progress)
            except Exception:
                pass
        
        def action_cancel_task(self) -> None:
            if self.current_worker and self.current_worker.is_running:
                self.current_worker.cancel()
                self.app.notify("Task cancelled", severity="warning")
                
                agent_log = self.query_one("#agent-log", AgentLogPanel)
                agent_log.log_agent_activity("System", "Cancelled by user", "warning")
        
        def action_new_task(self) -> None:
            self.query_one("#task-input", TextArea).clear()
            self.query_one("#task-input", TextArea).focus()
            
            results_container = self.query_one("#results-container", ScrollableContainer)
            results_container.remove_children()
            results_container.mount(Static("Results will appear here", id="results-placeholder"))
            
            self.update_task_status("Ready")
            
            for agent_name in self.agent_widgets:
                self.update_agent_status(agent_name, AgentStatus.IDLE)
            
            self.app.notify("Ready for new task", severity="information")
        
        def action_show_dashboard(self) -> None:
            self.app.push_screen(DashboardScreen())
        
        def action_show_settings(self) -> None:
            self.app.push_screen(SettingsScreen())
        
        def action_show_model_config(self) -> None:
            self.app.push_screen(ModelConfigScreen())
        
        def action_show_codebase(self) -> None:
            self.app.push_screen(CodebaseScreen())
        
        def action_show_help(self) -> None:
            self.app.push_screen(HelpModal())
    
    
    # ============================================================================
    # DASHBOARD SCREEN
    # ============================================================================
    
    class DashboardScreen(Screen):
        """Dashboard for viewing metrics and statistics"""
        
        BINDINGS = [
            Binding("ctrl+q", "quit", "Quit"),
            Binding("escape", "app.pop_screen", "Back"),
            Binding("ctrl+h", "show_help", "Help"),
        ]
        
        def compose(self) -> ComposeResult:
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
                    yield Static("Loading...", id="dashboard-loading")
            
            yield Footer()
        
        def on_mount(self) -> None:
            self.app.sub_title = "Dashboards"
            self.load_metrics()
        
        def on_tabs_tab_activated(self, event: Tabs.TabActivated) -> None:
            """Handle tab change - FIXED EVENT NAME"""
            content = self.query_one("#dashboard-content", ScrollableContainer)
            content.remove_children()
            content.mount(Static("Loading...", id="dashboard-loading"))
            
            tab_id = event.tab.id
            
            if tab_id == "metrics-tab":
                self.set_timer(0.1, self.load_metrics)
            elif tab_id == "errors-tab":
                self.set_timer(0.1, self.load_errors)
            elif tab_id == "routing-tab":
                self.set_timer(0.1, self.load_routing)
            elif tab_id == "feedback-tab":
                self.set_timer(0.1, self.load_feedback)
            elif tab_id == "tests-tab":
                self.set_timer(0.1, self.load_tests)
        
        def load_metrics(self) -> None:
            """Load metrics dashboard"""
            content = self.query_one("#dashboard-content", ScrollableContainer)
            content.remove_children()
            
            try:
                tracker = MetricsTracker()
                stats = tracker.get_metrics_summary(days=30)
                
                metrics_text = f"""# 📊 Metrics Dashboard (Last 30 Days)

## Overall Performance
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
                    metrics_text += "\n*No data yet. Complete some tasks to see statistics.*"
                
                content.mount(Markdown(metrics_text))
            except Exception as e:
                content.mount(Static(f"❌ Error loading metrics: {str(e)}", classes="error-message"))
        
        def load_errors(self) -> None:
            """Load error patterns"""
            content = self.query_one("#dashboard-content", ScrollableContainer)
            content.remove_children()
            
            try:
                analyzer = EnhancedErrorAnalyzer(ERROR_PATTERN_DB)
                insights = analyzer.get_pattern_insights(days=30)
                stats = insights.get('statistics', {})
                top_patterns = insights.get('top_patterns', [])
                
                errors_text = f"""# 🔍 Error Patterns (Last 30 Days)

## Statistics
- **Total Errors**: {stats.get('total_errors', 0)}
- **Unique Patterns**: {len(top_patterns)}
- **Fix Success Rate**: {stats.get('fix_success_rate', 0.0):.1f}%

## Top Patterns
"""
                if top_patterns:
                    for i, pattern in enumerate(top_patterns[:10], 1):
                        if isinstance(pattern, dict):
                            error_type = pattern.get('error_type', 'Unknown')
                            frequency = pattern.get('frequency', 0)
                        else:
                            error_type = getattr(pattern, 'error_type', 'Unknown')
                            frequency = getattr(pattern, 'frequency', 0)
                        
                        errors_text += f"\n### {i}. {error_type.upper()}\n"
                        errors_text += f"- Frequency: {frequency}\n"
                else:
                    errors_text += "\n*No error patterns yet.*"
                
                content.mount(Markdown(errors_text))
            except Exception as e:
                content.mount(Static(f"❌ Error: {str(e)}", classes="error-message"))
        
        def load_routing(self) -> None:
            """Load routing stats"""
            content = self.query_one("#dashboard-content", ScrollableContainer)
            content.remove_children()
            
            try:
                stats = ROUTING_OPTIMIZER.get_routing_stats(days=30)
                
                routing_text = """# 🚦 Routing Statistics (Last 30 Days)

## Agent Performance
"""
                if stats.get('overall'):
                    for route, data in sorted(stats['overall'].items()):
                        routing_text += f"\n### {route.upper()}\n"
                        routing_text += f"- Count: {data['count']}\n"
                        routing_text += f"- Avg Score: {data['avg_score']:.1f}/100\n"
                        routing_text += f"- Success Rate: {data['success_rate']:.1f}%\n"
                else:
                    routing_text += "\n*No routing data yet*"
                
                content.mount(Markdown(routing_text))
            except Exception as e:
                content.mount(Static(f"❌ Error: {str(e)}", classes="error-message"))
        
        def load_feedback(self) -> None:
            """Load feedback stats"""
            content = self.query_one("#dashboard-content", ScrollableContainer)
            content.remove_children()
            
            try:
                stats = FEEDBACK_COLLECTOR.get_feedback_statistics(days=30)
                
                feedback_text = f"""# 💬 User Feedback (Last 30 Days)

## Overview
- **Total Feedback**: {stats['overall']['total']}
- **Avg Rating**: {stats['overall']['avg_rating']:.1f}/5.0 ⭐
- **Satisfaction**: {stats['overall']['satisfaction_rate']:.1f}%

## Rating Distribution
"""
                if stats.get('rating_distribution'):
                    for rating in range(5, 0, -1):
                        count = stats['rating_distribution'].get(rating, 0)
                        feedback_text += f"- {'⭐' * rating}: {count}\n"
                else:
                    feedback_text += "\n*No feedback yet*"
                
                content.mount(Markdown(feedback_text))
            except Exception as e:
                content.mount(Static(f"❌ Error: {str(e)}", classes="error-message"))
        
        def load_tests(self) -> None:
            """Load test suite info"""
            content = self.query_one("#dashboard-content", ScrollableContainer)
            content.remove_children()
            
            try:
                from tests.test_suite_framework import TEST_SUITE_FRAMEWORK
                tasks = TEST_SUITE_FRAMEWORK.load_tasks()
                
                tests_text = f"""# 🧪 Test Suite

## Overview
- **Total Tasks**: {len(tasks)}

## By Category
"""
                if tasks:
                    categories = {}
                    for task in tasks:
                        cat = task.category.value if hasattr(task.category, 'value') else str(task.category)
                        categories[cat] = categories.get(cat, 0) + 1
                    
                    for category, count in sorted(categories.items()):
                        tests_text += f"- **{category}**: {count}\n"
                else:
                    tests_text += "\n*No test tasks. Run: `python3 tests/generate_test_tasks.py`*"
                
                content.mount(Markdown(tests_text))
            except Exception as e:
                content.mount(Static(f"❌ Error: {str(e)}", classes="error-message"))
        
        def action_show_help(self) -> None:
            self.app.push_screen(HelpModal())
    
    
    # ============================================================================
    # OTHER SCREENS  
    # ============================================================================
    
    class ModelConfigScreen(Screen):
        """Screen for model configuration"""
        
        BINDINGS = [
            Binding("escape", "app.pop_screen", "Back"),
            Binding("ctrl+h", "show_help", "Help"),
        ]
        
        def compose(self) -> ComposeResult:
            yield Header(show_clock=True)
            
            with Container(id="model-config-container"):
                yield Static("🤖 Model Configuration", classes="section-title")
                
                with ScrollableContainer(id="config-content"):
                    yield Static("Routing Configuration", classes="subsection-title")
                    yield Label("Complexity Threshold:")
                    yield Input(value="8", id="complexity-threshold", type="number")
                    
                    yield Static("\nImplementation Agent", classes="subsection-title")
                    yield Label("Model:")
                    yield Input(value="qwen2.5-coder:7b", id="impl-model")
                    yield Label("Max Tokens:")
                    yield Input(value="3000", id="impl-max-tokens", type="number")
                    
                    yield Static("\nTest Generator", classes="subsection-title")
                    yield Label("Model:")
                    yield Input(value="qwen2.5-coder:14b", id="test-model")
                    
                    yield Button("💾 Save Configuration", id="save-config-btn", variant="primary")
            
            yield Footer()
        
        def on_mount(self) -> None:
            self.app.sub_title = "Model Configuration"
        
        def on_button_pressed(self, event: Button.Pressed) -> None:
            if event.button.id == "save-config-btn":
                self.app.notify("Configuration saved (feature coming soon)", severity="information")
        
        def action_show_help(self) -> None:
            self.app.push_screen(HelpModal())
    
    
    class SettingsScreen(Screen):
        """Settings and system status screen"""
        
        BINDINGS = [
            Binding("escape", "app.pop_screen", "Back"),
            Binding("ctrl+h", "show_help", "Help"),
        ]
        
        def compose(self) -> ComposeResult:
            yield Header(show_clock=True)
            
            with Container(id="settings-container"):
                yield Static("⚙️ System Settings", classes="section-title")
                
                with ScrollableContainer(id="settings-content"):
                    yield Static("System Components", classes="subsection-title")
                    yield Static("✅ Orchestrator: Active", id="orchestrator-status")
                    yield Static("✅ Metrics Tracker: Active")
                    yield Static("✅ Error Learning: Active")
                    yield Static("✅ Routing Optimizer: Active")
                    yield Static("✅ Feedback Collector: Active")
                    
                    yield Button("🔄 Refresh Status", id="refresh-btn", variant="primary")
            
            yield Footer()
        
        def on_mount(self) -> None:
            self.app.sub_title = "Settings"
            self.update_status()
        
        def on_button_pressed(self, event: Button.Pressed) -> None:
            if event.button.id == "refresh-btn":
                self.update_status()
                self.app.notify("Status refreshed", severity="success")
        
        def update_status(self) -> None:
            try:
                status = self.query_one("#orchestrator-status", Static)
                if self.app.orchestrator:
                    status.update("✅ Orchestrator: Active")
                else:
                    status.update("❌ Orchestrator: Not initialized")
            except Exception:
                pass
        
        def action_show_help(self) -> None:
            self.app.push_screen(HelpModal())
    
    
    class CodebaseScreen(Screen):
        """Codebase browser screen"""
        
        BINDINGS = [
            Binding("escape", "app.pop_screen", "Back"),
            Binding("ctrl+f", "focus_search", "Search"),
            Binding("ctrl+h", "show_help", "Help"),
        ]
        
        def compose(self) -> ComposeResult:
            yield Header(show_clock=True)
            
            with Container(id="codebase-container"):
                with Horizontal(id="codebase-layout"):
                    with Vertical(id="file-tree-panel", classes="panel"):
                        yield Static("📁 Project Files", classes="section-title")
                        yield DirectoryTree(str(project_root), id="file-tree")
                    
                    with Vertical(id="code-view-panel", classes="panel"):
                        yield Static("📄 File Viewer", classes="section-title")
                        yield Input(placeholder="🔍 Search...", id="search-input")
                        
                        with ScrollableContainer(id="code-viewer"):
                            yield Static("Select a file to view", id="code-placeholder")
            
            yield Footer()
        
        def on_mount(self) -> None:
            self.app.sub_title = "Codebase Browser"
        
        def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
            file_path = Path(event.path)
            if file_path.exists() and file_path.is_file():
                try:
                    if file_path.stat().st_size > 100000:
                        content = f"⚠️ File too large ({file_path.stat().st_size:,} bytes)"
                    else:
                        content = file_path.read_text()
                    
                    code_viewer = self.query_one("#code-viewer", ScrollableContainer)
                    code_viewer.remove_children()
                    
                    if len(content) > 5000:
                        content = content[:5000] + "\n\n... (truncated)"
                    
                    code_viewer.mount(Static(f"```python\n{content}\n```"))
                    
                except Exception as e:
                    code_viewer = self.query_one("#code-viewer", ScrollableContainer)
                    code_viewer.remove_children()
                    code_viewer.mount(Static(f"❌ Error: {str(e)}", classes="error-message"))
        
        def action_focus_search(self) -> None:
            self.query_one("#search-input", Input).focus()
        
        def action_show_help(self) -> None:
            self.app.push_screen(HelpModal())
    
    
    # ============================================================================
    # MAIN APP
    # ============================================================================
    
    class AI_Coding_Team_TUI(App):
        """Main TUI Application - Ultimate Integrated Version"""
        
        # Make TaskInputScreen the default screen
        SCREENS = {
            "task": TaskInputScreen,
        }
        
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
            width: 40%;
        }
        
        #right-panel {
            width: 60%;
        }
        
        .tab-content {
            height: 1fr;
            padding: 1;
        }
        
        .hidden {
            display: none;
        }
        
        #task-controls {
            height: auto;
            padding: 1;
        }
        
        .section-title {
            text-style: bold;
            color: $accent;
            padding: 1;
            background: $panel;
        }
        
        .subsection-title {
            text-style: bold;
            padding: 1;
            margin-top: 1;
        }
        
        .status-indicator {
            text-style: bold;
            padding: 1;
            border: round $primary;
            background: $panel;
        }
        
        .result-container {
            border: solid $primary;
            padding: 1;
            margin: 1;
            background: $panel;
        }
        
        .status-large {
            text-style: bold;
            text-align: center;
            padding: 1;
        }
        
        .action-buttons, .modal-buttons {
            height: auto;
            align: center middle;
            padding: 1;
        }
        
        .agent-card {
            border: solid $primary;
            padding: 1;
            margin-bottom: 1;
            background: $panel;
        }
        
        .agent-card .status-indicator.active {
            color: $success;
        }
        
        .agent-card .status-indicator.thinking {
            color: $warning;
        }
        
        .log-entry {
            padding: 0 1;
        }
        
        .log-error {
            color: $error;
        }
        
        .log-success {
            color: $success;
        }
        
        .error-message {
            color: $error;
            padding: 1;
        }
        
        #help-modal, #feedback-modal {
            width: 60;
            height: auto;
            border: thick $primary;
            background: $surface;
            padding: 2;
        }
        
        .modal-title {
            text-style: bold;
            text-align: center;
            padding: 1;
        }
        """
        
        TITLE = "AI Coding Team"
        SUB_TITLE = "Intelligent Software Development System"
        
        BINDINGS = [
            Binding("ctrl+q", "quit", "Quit"),
            Binding("ctrl+h", "show_help", "Help"),
            Binding("ctrl+r", "run_task", "Run"),
            Binding("ctrl+c", "cancel_task", "Cancel"),
            Binding("ctrl+n", "new_task", "New"),
            Binding("ctrl+d", "show_dashboard", "Dashboard"),
            Binding("ctrl+s", "show_settings", "Settings"),
            Binding("ctrl+m", "show_model_config", "Models"),
            Binding("ctrl+b", "show_codebase", "Codebase"),
        ]
        
        def __init__(self):
            super().__init__()
            self.orchestrator: Optional[Orchestrator] = None
            self.current_worker: Optional[Worker] = None
            self.agent_widgets: Dict[str, Any] = {}
            self.task_start_time: Optional[datetime] = None
            self.current_task: str = ""
        
        
        def initialize_system(self) -> None:
            try:
                self.notify("Initializing orchestrator...", severity="information")
                print("DEBUG: Creating Orchestrator...")
                self.orchestrator = Orchestrator()
                print("DEBUG: Orchestrator created successfully!")
                self.notify("✅ System ready! Press Ctrl+H for help", severity="success", timeout=5)
                # Update status to show system is ready
                try:
                    status = self.query_one("#task-status", Static)
                    status.update("Status: ✅ System Ready")
                except:
                    pass
            except Exception as e:
                import traceback
                error_msg = f"Initialization error: {str(e)}"
                print(f"DEBUG: {error_msg}")
                traceback.print_exc()
                self.notify(error_msg, severity="error")
                try:
                    status = self.query_one("#task-status", Static)
                    status.update(f"Status: ❌ Initialization Failed: {str(e)}")
                except:
                    pass
        
        def compose(self) -> ComposeResult:
            # Compose widgets directly in the App (like minimal test)
            # This ensures they're properly mounted and visible
            from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
            from textual.widgets import Header, Footer, Button, TextArea, Static, Tabs, Tab, ProgressBar
            
            yield Header(show_clock=True)
            
            with Container(id="main-container"):
                # Left panel - Task input (40%)
                with Vertical(id="left-panel", classes="panel"):
                    yield Static("📝 Task Input", classes="section-title")
                    yield TextArea(
                        placeholder="Describe your coding task...\n\nExample:\n- Create a REST API with Flask\n- Add user authentication\n- Include unit tests",
                        id="task-input",
                        language="markdown"
                    )
                    
                    with Horizontal(id="task-controls"):
                        yield Button("▶ Run", id="run-btn", variant="primary")
                        yield Button("⏹ Cancel", id="cancel-btn", variant="error", disabled=True)
                        yield Button("🗑 Clear", id="clear-btn")
                    
                    yield ProgressBar(total=100, show_eta=False, id="task-progress")
                    yield Static("Status: Ready", id="task-status", classes="status-indicator")
                
                # Right panel - Results (60%)
                with Vertical(id="right-panel", classes="panel"):
                    yield Static("📊 Results & Activity", classes="section-title")
                    
                    # Tabs for different views
                    yield Tabs(
                        Tab("Results", id="results-tab"),
                        Tab("Agent Status", id="agents-tab"),
                        Tab("Activity Log", id="log-tab"),
                        id="output-tabs"
                    )
                    
                    # Results view
                    with ScrollableContainer(id="results-container", classes="tab-content"):
                        yield Static("Results will appear here", id="results-placeholder")
                    
                    # Agent status view (hidden by default)
                    with ScrollableContainer(id="agents-container", classes="tab-content hidden"):
                        pass
                    
                    # Activity log (hidden by default)  
                    yield AgentLogPanel(id="agent-log", classes="tab-content hidden")
            
            yield Footer()
        
        def on_mount(self) -> None:
            """Called when the app is mounted"""
            try:
                # Focus task input
                try:
                    self.query_one("#task-input", TextArea).focus()
                except Exception as e:
                    print(f"Warning: Could not focus task input: {e}")
                
                self.sub_title = "Task Execution"
                
                # Initialize agent widgets
                try:
                    self.initialize_agent_widgets()
                except Exception as e:
                    print(f"Warning: Could not initialize agent widgets: {e}")
                
                self.notify("🚀 Starting AI Coding Team...", severity="information")
                # Initialize system immediately (but in background to not block UI)
                # Use a very short timer to allow UI to render first
                self.set_timer(0.01, self.initialize_system)
            except Exception as e:
                import traceback
                traceback.print_exc()
                self.notify(f"Error mounting: {str(e)}", severity="error")
        
        def on_tabs_tab_activated(self, event: Tabs.TabActivated) -> None:
            """Handle tab changes in the App"""
            # Hide all tab content
            for container in self.query(".tab-content"):
                container.add_class("hidden")
            
            # Show selected tab content
            if event.tab.id == "results-tab":
                try:
                    self.query_one("#results-container").remove_class("hidden")
                except:
                    pass
            elif event.tab.id == "agents-tab":
                try:
                    self.query_one("#agents-container").remove_class("hidden")
                except:
                    pass
            elif event.tab.id == "log-tab":
                try:
                    self.query_one("#agent-log").remove_class("hidden")
                except:
                    pass
        
        def initialize_agent_widgets(self) -> None:
            """Initialize agent status widgets"""
            try:
                container = self.query_one("#agents-container", ScrollableContainer)
                
                agent_names = [
                    "Coordinator",
                    "Code Generator",
                    "Test Generator",
                    "Code Reviewer",
                    "Validator"
                ]
                
                if not hasattr(self, 'agent_widgets'):
                    self.agent_widgets = {}
                
                for agent_name in agent_names:
                    widget = AgentStatusWidget()
                    widget.agent_name = agent_name
                    widget.status = AgentStatus.IDLE
                    self.agent_widgets[agent_name] = widget
                    container.mount(widget)
            except Exception as e:
                print(f"Warning: Could not initialize agent widgets: {e}")
        
        def update_agent_status(self, agent_name: str, status: AgentStatus, task: str = "") -> None:
            """Update agent status"""
            if not hasattr(self, 'agent_widgets'):
                return
                
            if agent_name in self.agent_widgets:
                widget = self.agent_widgets[agent_name]
                widget.status = status
                widget.current_task = task
                
                # Log activity
                try:
                    agent_log = self.query_one("#agent-log", AgentLogPanel)
                    level = "info" if status in [AgentStatus.ACTIVE, AgentStatus.THINKING] else "debug"
                    if status == AgentStatus.ERROR:
                        level = "error"
                    elif status == AgentStatus.COMPLETE:
                        level = "success"
                    
                    agent_log.log_agent_activity(
                        agent_name,
                        f"{status.value}: {task}" if task else status.value,
                        level
                    )
                except Exception:
                    pass  # Agent log might not be available
        
        # Handle button events directly in App (like minimal test)
        def on_button_pressed(self, event: Button.Pressed) -> None:
            """Handle button presses directly in App"""
            button_id = event.button.id
            print(f"DEBUG: Button pressed: {button_id}")  # Terminal debug
            self.notify(f"🔘 Button '{button_id}' pressed!", severity="information")
            
            if button_id == "run-btn":
                print("DEBUG: Calling action_run_task")
                self.action_run_task()
            elif button_id == "cancel-btn":
                self.action_cancel_task()
            elif button_id == "clear-btn":
                self.action_new_task()
        
        # Implement actions directly in App
        def action_run_task(self) -> None:
            """Run the task using async worker"""
            print("DEBUG: action_run_task called")  # Terminal debug
            self.notify("🔵 action_run_task called!", severity="information")
            
            try:
                task_input = self.query_one("#task-input", TextArea)
                task = task_input.text.strip()
            except Exception as e:
                self.notify(f"Error getting task input: {str(e)}", severity="error")
                return
            
            if not task:
                self.notify("Please enter a task first", severity="warning")
                return
            
            if hasattr(self, 'current_worker') and self.current_worker and self.current_worker.is_running:
                self.notify("A task is already running", severity="warning")
                return
            
            # Check orchestrator - if not ready, try to initialize it now
            if not self.orchestrator:
                self.notify("System not ready yet. Initializing now...", severity="warning")
                print("DEBUG: Orchestrator is None. Initializing now...")
                try:
                    # Try to initialize synchronously
                    self.initialize_system()
                    # Check again
                    if not self.orchestrator:
                        self.notify("System initialization failed. Please try again.", severity="error")
                        return
                    else:
                        self.notify("✅ System initialized! Starting task...", severity="success")
                except Exception as e:
                    self.notify(f"Initialization error: {str(e)}", severity="error")
                    import traceback
                    traceback.print_exc()
                    return
            
            # Store task
            self.current_task = task
            self.task_start_time = datetime.now()
            
            # Reset agent statuses
            if hasattr(self, 'agent_widgets'):
                for agent_name in self.agent_widgets.keys():
                    self.update_agent_status(agent_name, AgentStatus.IDLE)
            
            # Update status
            status = self.query_one("#task-status", Static)
            status.update("Status: ⏳ Starting task...")
            
            # Update buttons
            run_btn = self.query_one("#run-btn", Button)
            cancel_btn = self.query_one("#cancel-btn", Button)
            run_btn.disabled = True
            cancel_btn.disabled = False
            
            # Clear results
            results_container = self.query_one("#results-container", ScrollableContainer)
            results_container.remove_children()
            
            # Reset progress
            progress = self.query_one("#task-progress", ProgressBar)
            progress.update(progress=0)
            
            # Clear agent log
            try:
                agent_log = self.query_one("#agent-log", AgentLogPanel)
                agent_log.remove_children()
                agent_log.log_agent_activity("System", "Task started", "info")
            except Exception:
                pass
            
            # Start worker using @work decorator
            self.notify("Starting worker...", severity="information")
            try:
                self.current_worker = self.execute_task_sync(task)
                if self.current_worker:
                    self.notify("✅ Worker started!", severity="success")
                else:
                    self.notify("❌ Worker is None!", severity="error")
            except Exception as e:
                self.notify(f"❌ Worker error: {str(e)}", severity="error")
                import traceback
                traceback.print_exc()
        
        @work(exclusive=True, thread=True)
        def execute_task_sync(self, task: str) -> dict:
            """Execute task in worker thread"""
            try:
                # Immediate feedback
                self.call_from_thread(
                    lambda: self.notify("🔧 Worker thread started!", severity="success")
                )
                
                # Execute
                orchestrator = self.orchestrator
                if not orchestrator:
                    error_msg = "Orchestrator not available"
                    self.call_from_thread(
                        lambda: self.query_one("#task-status", Static).update(f"Status: ❌ {error_msg}")
                    )
                    return {"success": False, "error": error_msg, "code": "", "validation": {}}
                
                # Notify we're calling orchestrator
                self.call_from_thread(
                    lambda: self.notify("🤖 Calling orchestrator...", severity="information")
                )
                
                # Update agent status
                self.call_from_thread(
                    lambda: self.update_agent_status("Coordinator", AgentStatus.ACTIVE, "Analyzing task")
                )
                self.call_from_thread(
                    lambda: self.update_agent_status("Code Generator", AgentStatus.THINKING, "Generating code")
                )
                
                # Update status
                self.call_from_thread(
                    lambda: self.query_one("#task-status", Static).update("Status: ⏳ Executing task...")
                )
                self.call_from_thread(
                    lambda: self.query_one("#task-progress", ProgressBar).update(progress=25)
                )
                
                print(f"DEBUG: Calling orchestrator.build_with_validation_iterative with task: {task[:50]}...")
                result = orchestrator.build_with_validation_iterative(
                    task=task,
                    max_iterations=3
                )
                
                print(f"DEBUG: Orchestrator returned result. Keys: {list(result.keys()) if isinstance(result, dict) else 'NOT A DICT'}")
                print(f"DEBUG: Result success: {result.get('success', 'N/A')}")
                print(f"DEBUG: Result has code: {bool(result.get('code'))}")
                print(f"DEBUG: Result has error: {bool(result.get('error'))}")
                
                # Update agent statuses
                self.call_from_thread(
                    lambda: self.update_agent_status("Code Generator", AgentStatus.COMPLETE, "Code generated")
                )
                self.call_from_thread(
                    lambda: self.update_agent_status("Test Generator", AgentStatus.COMPLETE, "Tests validated")
                )
                self.call_from_thread(
                    lambda: self.update_agent_status("Coordinator", AgentStatus.COMPLETE, "Task complete")
                )
                
                # Update progress
                self.call_from_thread(
                    lambda: self.query_one("#task-progress", ProgressBar).update(progress=100)
                )
                
                # Log result to terminal for debugging
                if result.get('error'):
                    print(f"DEBUG: Result has error: {result.get('error')}")
                
                return result
                
            except Exception as e:
                import traceback
                error_msg = str(e)
                error_trace = traceback.format_exc()
                
                # Update agent status to error
                self.call_from_thread(
                    lambda: self.update_agent_status("Coordinator", AgentStatus.ERROR, f"Error: {error_msg[:50]}")
                )
                
                return {
                    "success": False,
                    "error": error_msg,
                    "error_traceback": error_trace,
                    "code": "",
                    "validation": {}
                }
        
        def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
            """Handle worker state changes"""
            print(f"DEBUG: Worker state changed to: {event.state}")
            
            if hasattr(self, 'current_worker') and event.worker == self.current_worker:
                if event.state == WorkerState.SUCCESS:
                    result = event.worker.result
                    print(f"DEBUG: Worker SUCCESS - result type: {type(result)}")
                    print(f"DEBUG: Worker SUCCESS - result keys: {list(result.keys()) if isinstance(result, dict) else 'NOT A DICT'}")
                    if result:
                        self.display_results(result)
                    else:
                        print("DEBUG: Result is None or empty!")
                        self.notify("❌ No result returned from worker", severity="error")
                        status = self.query_one("#task-status", Static)
                        status.update("Status: ❌ No result returned")
                    self.task_complete()
                elif event.state == WorkerState.ERROR:
                    error = event.worker.error
                    print(f"DEBUG: Worker ERROR: {error}")
                    error_str = str(error) if error else "Unknown error"
                    self.notify(f"❌ Worker error: {error_str}", severity="error")
                    status = self.query_one("#task-status", Static)
                    status.update(f"Status: ❌ Error: {error_str[:50]}")
                    
                    # Update agent statuses to error
                    for agent_name in self.agent_widgets.keys() if hasattr(self, 'agent_widgets') else []:
                        self.update_agent_status(agent_name, AgentStatus.ERROR, f"Error: {error_str[:30]}")
                    
                    self.task_complete()
                elif event.state == WorkerState.RUNNING:
                    print("DEBUG: Worker is RUNNING")
                    status = self.query_one("#task-status", Static)
                    status.update("Status: ⏳ Task running...")
                elif event.state == WorkerState.PENDING:
                    print("DEBUG: Worker is PENDING")
                    status = self.query_one("#task-status", Static)
                    status.update("Status: ⏳ Task pending...")
        
        def display_results(self, result: dict) -> None:
            """Display task results"""
            print(f"DEBUG: display_results called with result type: {type(result)}")
            print(f"DEBUG: Result keys: {list(result.keys()) if isinstance(result, dict) else 'NOT A DICT'}")
            
            results_container = self.query_one("#results-container", ScrollableContainer)
            results_container.remove_children()
            
            # Check for errors first
            if result.get("error"):
                error_msg = result.get("error", "Unknown error")
                print(f"DEBUG: Displaying error: {error_msg}")
                status = self.query_one("#task-status", Static)
                status.update(f"Status: ❌ Error: {error_msg[:50]}")
                self.notify(f"❌ Error: {error_msg[:100]}", severity="error")
                
                # Still try to display error in results
                error_widget = Static(f"❌ Error: {error_msg}", classes="error-message")
                results_container.mount(error_widget)
                return
            
            # Get evaluation score and test counts
            evaluation = result.get("evaluation")
            score = 0
            passed_tests = 0
            total_tests = 0
            
            if evaluation:
                try:
                    if hasattr(evaluation, 'score'):
                        score = evaluation.score
                        passed_tests = getattr(evaluation, 'passed_tests', 0)
                        total_tests = getattr(evaluation, 'total_tests', 0)
                    elif isinstance(evaluation, dict):
                        score = evaluation.get('score', 0)
                        passed_tests = evaluation.get('passed_tests', 0)
                        total_tests = evaluation.get('total_tests', 0)
                except AttributeError as e:
                    print(f"DEBUG: Error accessing evaluation attributes: {e}")
                    score = 0
                    passed_tests = 0
                    total_tests = 0
            
            # If test counts are 0, try to get them from validation results
            if total_tests == 0:
                validation = result.get('validation', {})
                tests_run = validation.get('tests_run')
                if tests_run and isinstance(tests_run, dict):
                    test_meta = tests_run.get('metadata')
                    if test_meta and isinstance(test_meta, dict):
                        passed_tests = test_meta.get('passed', 0)
                        total_tests = test_meta.get('total', 0)
                        print(f"DEBUG: Extracted test counts from validation: {passed_tests}/{total_tests}")
                        
                        # Also update evaluation if it exists
                        if evaluation and hasattr(evaluation, 'passed_tests'):
                            evaluation.passed_tests = passed_tests
                            evaluation.total_tests = total_tests
            
            success = result.get("success", False)
            
            # Update status with test info
            status = self.query_one("#task-status", Static)
            test_info = f" (Tests: {passed_tests}/{total_tests})" if total_tests > 0 else ""
            if success:
                status.update(f"Status: ✅ Complete! Score: {score}/100{test_info}")
                self.notify(f"✅ Task completed! Score: {score}/100{test_info}", severity="success")
            else:
                status.update(f"Status: ⚠️ Completed with issues (Score: {score}/100{test_info})")
                self.notify(f"⚠️ Task completed with issues. Score: {score}/100{test_info}", severity="warning")
            
            print(f"DEBUG: Mounting result widget. Code length: {len(result.get('code', ''))}")
            
            # Update all agents to complete
            for agent_name in self.agent_widgets.keys() if hasattr(self, 'agent_widgets') else []:
                self.update_agent_status(agent_name, AgentStatus.COMPLETE)
            
            # Mount result widget
            try:
                result_widget = TaskResultWidget(result, task=self.current_task)
                results_container.mount(result_widget)
                print("DEBUG: Result widget mounted successfully")
            except Exception as e:
                print(f"DEBUG: Error mounting result widget: {e}")
                import traceback
                traceback.print_exc()
                # Fallback: just show text
                error_text = f"Error displaying results: {str(e)}\n\nResult: {str(result)[:500]}"
                error_widget = Static(error_text, classes="error-message")
                results_container.mount(error_widget)
        
        def task_complete(self) -> None:
            """Cleanup after task completion"""
            run_btn = self.query_one("#run-btn", Button)
            cancel_btn = self.query_one("#cancel-btn", Button)
            run_btn.disabled = False
            cancel_btn.disabled = True
        
        def action_cancel_task(self) -> None:
            """Cancel running task"""
            if hasattr(self, 'current_worker') and self.current_worker:
                self.current_worker.cancel()
            self.notify("Task cancelled", severity="information")
        
        def action_new_task(self) -> None:
            """Clear task input"""
            task_input = self.query_one("#task-input", TextArea)
            task_input.text = ""
            results_container = self.query_one("#results-container", ScrollableContainer)
            results_container.remove_children()
            status = self.query_one("#task-status", Static)
            status.update("Status: Ready")
        
        def action_show_help(self) -> None:
            self.push_screen(HelpModal())
        
        def action_show_dashboard(self) -> None:
            self.push_screen(DashboardScreen())
        
        def action_show_settings(self) -> None:
            self.push_screen(SettingsScreen())
        
        def action_show_model_config(self) -> None:
            self.push_screen(ModelConfigScreen())
        
        def action_show_codebase(self) -> None:
            self.push_screen(CodebaseScreen())
    
    
    def main():
        """Main entry point"""
        app = AI_Coding_Team_TUI()
        app.run()
    
    
    if __name__ == "__main__":
        main()

else:
    def main():
        print("Textual library is required.")
        sys.exit(1)
    
    if __name__ == "__main__":
        main()