"""
AI Coding Team - Text User Interface (TUI)
Main interface for users to interact with the system

Built with Textual (Textualize)
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from textual.app import App, ComposeResult
    from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
    from textual.widgets import (
        Header, Footer, Button, Input, TextArea, Static, Tabs, Tab,
        DataTable, Label, Log, Markdown, Tree, DirectoryTree, Select
    )
    from textual.binding import Binding
    from textual.reactive import reactive
    from textual.screen import Screen, ModalScreen
    import asyncio
except ImportError:
    print("❌ Error: Textual library not installed")
    print("Install it with: pip install textual")
    sys.exit(1)

from agents.orchestrator import Orchestrator
from learning.metrics_tracker import MetricsTracker
from learning.error_patterns import ERROR_PATTERN_DB
from learning.feedback_collector import FEEDBACK_COLLECTOR
from agents.routing_optimizer import ROUTING_OPTIMIZER


class TaskInputScreen(Screen):
    """Screen for task input and execution"""
    
    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("ctrl+r", "run_task", "Run Task"),
        Binding("ctrl+d", "show_dashboard", "Dashboard"),
        Binding("ctrl/s", "show_settings", "Settings"),
    ]
    
    def compose(self) -> ComposeResult:
        """Compose the screen layout"""
        yield Header(show_clock=True)
        
        with Container(id="main-container"):
            with Vertical(id="left-panel"):
                yield Static("📝 Task Input", classes="section-title")
                yield TextArea(
                    placeholder="Enter your task here...\n\nExample: Create a REST API endpoint with authentication",
                    id="task-input",
                    language="markdown"
                )
                with Horizontal(id="task-controls"):
                    yield Button("▶ Run Task", id="run-btn", variant="primary")
                    yield Button("📊 View Metrics", id="metrics-btn")
                    yield Button("⚙️ Settings", id="settings-btn")
            
            with Vertical(id="right-panel"):
                yield Static("📊 Results", classes="section-title")
                yield ScrollableContainer(id="results-container")
                yield Log(id="output-log", max_lines=100)
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Called when screen is mounted"""
        self.app.sub_title = "Task Execution"
        task_input = self.query_one("#task-input", TextArea)
        task_input.focus()
    
    async def action_run_task(self) -> None:
        """Run the task"""
        task_input = self.query_one("#task-input", TextArea)
        task = task_input.text.strip()
        
        if not task:
            self.app.notify("Please enter a task first", severity="warning")
            return
        
        output_log = self.query_one("#output-log", Log)
        results_container = self.query_one("#results-container", ScrollableContainer)
        
        # Clear previous results
        results_container.remove_children()
        output_log.clear()
        
        output_log.write("🚀 Starting task execution...")
        output_log.write(f"Task: {task}")
        
        try:
            # Get orchestrator from app
            orchestrator = self.app.orchestrator
            
            # Run task in background
            self.app.run_task(self.execute_task, task, output_log, results_container)
            
        except Exception as e:
            output_log.write(f"❌ Error: {str(e)}")
            self.app.notify(f"Error: {str(e)}", severity="error")
    
    async def execute_task(self, task: str, output_log: Log, results_container: ScrollableContainer) -> None:
        """Execute task asynchronously"""
        try:
            output_log.write("📊 Analyzing complexity...")
            
            orchestrator = self.app.orchestrator
            result = orchestrator.build_with_validation_iterative(
                task=task,
                max_iterations=3
            )
            
            output_log.write("✅ Task execution complete!")
            
            # Display results
            if result.get("success"):
                output_log.write(f"✅ Success! Score: {result.get('evaluation', {}).score if result.get('evaluation') else 'N/A'}/100")
                
                # Show code in results
                code = result.get("code", "")
                if code:
                    code_viewer = Static(
                        f"```python\n{code[:1000]}{'...' if len(code) > 1000 else ''}\n```",
                        id="code-result"
                    )
                    results_container.mount(code_viewer)
                
                # Show validation results
                validation = result.get("validation", {})
                if validation:
                    validation_text = "Validation Results:\n"
                    if validation.get("syntax_valid"):
                        validation_text += "✅ Syntax: Valid\n"
                    if validation.get("execution_success"):
                        validation_text += "✅ Execution: Success\n"
                    
                    validation_view = Static(validation_text, id="validation-result")
                    results_container.mount(validation_view)
            else:
                output_log.write("❌ Task execution failed")
                
                errors = result.get("validation", {}).get("errors", [])
                if errors:
                    error_text = "Errors:\n" + "\n".join(f"- {str(e)}" for e in errors[:5])
                    error_view = Static(error_text, id="error-result")
                    results_container.mount(error_view)
            
        except Exception as e:
            output_log.write(f"❌ Error during execution: {str(e)}")
            self.app.notify(f"Execution error: {str(e)}", severity="error")
    
    def action_show_dashboard(self) -> None:
        """Switch to dashboard screen"""
        self.app.push_screen("dashboard")
    
    def action_show_settings(self) -> None:
        """Switch to settings screen"""
        self.app.push_screen("settings")


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
    
    def on_tabs_changed(self, event: Tabs.Changed) -> None:
        """Handle tab change"""
        content = self.query_one("#dashboard-content", ScrollableContainer)
        content.remove_children()
        
        tab_id = event.tab.id
        
        if tab_id == "metrics-tab":
            self.show_metrics(content)
        elif tab_id == "errors-tab":
            self.show_errors(content)
        elif tab_id == "routing-tab":
            self.show_routing(content)
        elif tab_id == "feedback-tab":
            self.show_feedback(content)
        elif tab_id == "tests-tab":
            self.show_tests(content)
    
    def show_metrics(self, container: ScrollableContainer) -> None:
        """Show metrics dashboard"""
        try:
            tracker = MetricsTracker()
            stats = tracker.get_metrics_summary(days=30)
            
            metrics_text = f"""
# 📊 Metrics Dashboard

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
                for task_type, data in stats['by_task_type'].items():
                    metrics_text += f"\n### {task_type.upper()}\n"
                    metrics_text += f"- Count: {data['count']}\n"
                    metrics_text += f"- Accuracy: {data['accuracy']:.1f}%\n"
                    metrics_text += f"- Test Pass Rate: {data['test_pass_rate']:.1f}%\n"
            
            markdown = Markdown(metrics_text)
            container.mount(markdown)
        except Exception as e:
            container.mount(Static(f"Error loading metrics: {str(e)}"))
    
    def show_errors(self, container: ScrollableContainer) -> None:
        """Show error patterns dashboard"""
        try:
            insights = ERROR_PATTERN_DB.get_pattern_insights(days=30)
            stats = insights['statistics']
            
            errors_text = f"""
# 🔍 Error Patterns Dashboard

## Statistics
- **Total Errors**: {stats['total_errors']}
- **Total Patterns**: {stats['total_patterns']}
- **Fix Success Rate**: {stats['fix_success_rate']:.1f}%

## Top Error Patterns
"""
            for pattern in insights['top_patterns'][:10]:
                errors_text += f"\n### {pattern.error_type.upper()}\n"
                errors_text += f"- Frequency: {pattern.frequency}\n"
                errors_text += f"- Pattern: {pattern.error_message_pattern[:100]}...\n"
                errors_text += f"- Task Type: {pattern.task_type}\n"
            
            markdown = Markdown(errors_text)
            container.mount(markdown)
        except Exception as e:
            container.mount(Static(f"Error loading error patterns: {str(e)}"))
    
    def show_routing(self, container: ScrollableContainer) -> None:
        """Show routing statistics"""
        try:
            stats = ROUTING_OPTIMIZER.get_routing_stats(days=30)
            
            routing_text = """
# 🚦 Routing Statistics

## Overall Routing
"""
            if stats['overall']:
                for route, data in stats['overall'].items():
                    routing_text += f"\n### {route.upper()}\n"
                    routing_text += f"- Count: {data['count']}\n"
                    routing_text += f"- Avg Score: {data['avg_score']:.1f}/100\n"
                    routing_text += f"- Avg Duration: {data['avg_duration']:.1f}ms\n"
                    routing_text += f"- Success Rate: {data['success_rate']:.1f}%\n"
            
            routing_text += f"\n## Prediction Accuracy\n"
            routing_text += f"- Avg Prediction Error: {stats['avg_prediction_error']:.2f} points\n"
            
            markdown = Markdown(routing_text)
            container.mount(markdown)
        except Exception as e:
            container.mount(Static(f"Error loading routing stats: {str(e)}"))
    
    def show_feedback(self, container: ScrollableContainer) -> None:
        """Show feedback dashboard"""
        try:
            stats = FEEDBACK_COLLECTOR.get_feedback_statistics(days=30)
            
            feedback_text = f"""
# 💬 Feedback Dashboard

## Overall Statistics
- **Total Feedback**: {stats['overall']['total']}
- **Average Rating**: {stats['overall']['avg_rating']:.1f}/5.0
- **Satisfaction Rate**: {stats['overall']['satisfaction_rate']:.1f}%

## Rating Distribution
"""
            if stats.get('rating_distribution'):
                for rating, count in sorted(stats['rating_distribution'].items()):
                    feedback_text += f"- Rating {rating}: {count} feedback(s)\n"
            
            markdown = Markdown(feedback_text)
            container.mount(markdown)
        except Exception as e:
            container.mount(Static(f"Error loading feedback: {str(e)}"))
    
    def show_tests(self, container: ScrollableContainer) -> None:
        """Show test suite dashboard"""
        try:
            from tests.test_suite_framework import TEST_SUITE_FRAMEWORK
            
            tasks = TEST_SUITE_FRAMEWORK.load_tasks()
            
            tests_text = f"""
# 🧪 Test Suite Dashboard

## Test Tasks
- **Total Tasks**: {len(tasks)}

## By Category
"""
            categories = {}
            for task in tasks:
                categories[task.category.value] = categories.get(task.category.value, 0) + 1
            
            for category, count in sorted(categories.items()):
                tests_text += f"- **{category}**: {count} tasks\n"
            
            markdown = Markdown(tests_text)
            container.mount(markdown)
        except Exception as e:
            container.mount(Static(f"Error loading test suite: {str(e)}"))


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
                yield Static("Model Configuration", classes="subsection-title")
                yield Static("Routing Threshold: 8", id="routing-threshold")
                yield Static("Complexity Threshold: 8", id="complexity-threshold")
                
                yield Static("\nAgent Configuration", classes="subsection-title")
                yield Static("Implementation Agent: qwen2.5-coder:7b", id="impl-agent")
                yield Static("Test Generator: qwen2.5-coder:14b", id="test-agent")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Called when screen is mounted"""
        self.app.sub_title = "Settings"


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
    
    #left-panel {
        width: 50%;
        border-right: wide $primary;
        padding: 1;
    }
    
    #right-panel {
        width: 50%;
        padding: 1;
    }
    
    #task-controls {
        height: auto;
        padding: 1;
    }
    
    #results-container {
        height: 60%;
        border: solid $primary;
        padding: 1;
    }
    
    #output-log {
        height: 40%;
        border: solid $primary;
    }
    
    .section-title {
        text-style: bold;
        color: $accent;
        padding: 1;
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
    """
    
    TITLE = "AI Coding Team"
    SUB_TITLE = "Intelligent Software Development"
    
    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("ctrl+d", "show_dashboard", "Dashboard"),
        Binding("ctrl+s", "show_settings", "Settings"),
    ]
    
    def __init__(self):
        """Initialize the TUI app"""
        super().__init__()
        self.orchestrator = None
    
    def on_mount(self) -> None:
        """Called when app is mounted"""
        try:
            # Initialize orchestrator
            self.notify("Initializing system...", severity="information")
            self.orchestrator = Orchestrator()
            self.notify("System ready!", severity="success")
        except Exception as e:
            self.notify(f"Error initializing: {str(e)}", severity="error")
    
    def compose(self) -> ComposeResult:
        """Compose the main app layout"""
        # Start with task input screen
        yield from TaskInputScreen().compose()
    
    def action_show_dashboard(self) -> None:
        """Show dashboard screen"""
        self.push_screen(DashboardScreen())


def main():
    """Main entry point"""
    app = AI_Coding_Team_TUI()
    app.run()


if __name__ == "__main__":
    main()

