"""
Additional TUI Screens for advanced features
Model controls, agent configuration, etc.
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from textual.app import ComposeResult
    from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
    from textual.widgets import (
        Header, Footer, Button, Input, Static, Select, Checkbox, TextArea,
        DataTable, Log, Markdown, Collapsible, Label
    )
    from textual.binding import Binding
    from textual.screen import Screen, ModalScreen
    from textual.widget import Widget
    TEXTUAL_AVAILABLE = True
except ImportError:
    TEXTUAL_AVAILABLE = False

if TEXTUAL_AVAILABLE:
    from agents.config_manager import CONFIG_MANAGER
    from agents.orchestrator import Orchestrator
    from learning.feedback_collector import FEEDBACK_COLLECTOR, FeedbackType


if TEXTUAL_AVAILABLE:
    class ModelConfigScreen(Screen):
        """Screen for model configuration"""
        
        BINDINGS = [
            Binding("escape", "app.pop_screen", "Back"),
            Binding("ctrl+s", "save_config", "Save"),
        ]
        
        def compose(self) -> ComposeResult:
            """Compose model configuration screen"""
            yield Header(show_clock=True)
            
            with Container(id="model-config-container"):
                yield Static("🤖 Model Configuration", classes="section-title")
                
                with ScrollableContainer(id="config-content"):
                    # Routing Configuration
                    yield Static("Routing Configuration", classes="subsection-title")
                    yield Label("Complexity Threshold:")
                    yield Input(value="8", id="complexity-threshold", type="number")
                    
                    yield Static("\nModel Configuration", classes="subsection-title")
                    
                    # Implementation Agent
                    yield Label("Implementation Agent:")
                    yield Input(value="qwen2.5-coder:7b", id="impl-model")
                    yield Label("Max Tokens:")
                    yield Input(value="3000", id="impl-max-tokens", type="number")
                    yield Label("Temperature:")
                    yield Input(value="0.2", id="impl-temperature", type="number")
                    
                    # Test Generator
                    yield Label("\nTest Generator:")
                    yield Input(value="qwen2.5-coder:14b", id="test-model")
                    yield Label("Max Tokens:")
                    yield Input(value="3000", id="test-max-tokens", type="number")
                    yield Label("Temperature:")
                    yield Input(value="0.2", id="test-temperature", type="number")
                    
                    # Validation Agent
                    yield Label("\nValidation Agent:")
                    yield Input(value="qwen2.5-coder:7b", id="validation-model")
                    
                    yield Button("💾 Save Configuration", id="save-config-btn", variant="primary")
                    yield Button("🔄 Reset to Default", id="reset-config-btn")
            
            yield Footer()
        
        def on_mount(self) -> None:
            """Called when screen is mounted"""
            self.app.sub_title = "Model Configuration"
            self.load_config()
        
        def load_config(self) -> None:
            """Load current configuration"""
            try:
                config_manager = CONFIG_MANAGER
                
                # Load routing config
                routing_config = config_manager.get_routing_config()
                if routing_config:
                    threshold_input = self.query_one("#complexity-threshold", Input)
                    threshold_input.value = str(routing_config.complexity_threshold)
                
                # Load model configs
                impl_config = config_manager.get_model_config("implementation")
                if impl_config:
                    self.query_one("#impl-model", Input).value = impl_config.name
                    self.query_one("#impl-max-tokens", Input).value = str(impl_config.max_tokens)
                    self.query_one("#impl-temperature", Input).value = str(impl_config.temperature)
                
                test_config = config_manager.get_model_config("test_generator")
                if test_config:
                    self.query_one("#test-model", Input).value = test_config.name
                    self.query_one("#test-max-tokens", Input).value = str(test_config.max_tokens)
                    self.query_one("#test-temperature", Input).value = str(test_config.temperature)
                    
            except Exception as e:
                self.app.notify(f"Error loading config: {str(e)}", severity="warning")
        
        def action_save_config(self) -> None:
            """Save configuration"""
            try:
                # For now, just notify - full config saving can be implemented later
                self.app.notify("Configuration save functionality coming soon", severity="information")
                # TODO: Implement config saving to models.yaml
            except Exception as e:
                self.app.notify(f"Error saving config: {str(e)}", severity="error")
    
    
    class FeedbackModal(ModalScreen):
        """Modal screen for submitting feedback"""
        
        BINDINGS = [
            Binding("escape", "dismiss", "Cancel"),
            Binding("ctrl+s", "submit_feedback", "Submit"),
        ]
        
        def __init__(self, task: str = "", task_type: str = "general", interaction_id: Optional[str] = None):
            super().__init__()
            self.task = task
            self.task_type = task_type
            self.interaction_id = interaction_id
        
        def compose(self) -> ComposeResult:
            """Compose feedback modal"""
            yield Header()
            
            with Container(id="feedback-modal-container"):
                yield Static("💬 Submit Feedback", classes="section-title")
                
                with ScrollableContainer(id="feedback-form"):
                    yield Label("Rating (1-5):")
                    yield Select(
                        options=[("1", 1), ("2", 2), ("3", 3), ("4", 4), ("5", 5)],
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
                    yield TextArea(placeholder="Enter your feedback...", id="feedback-comment")
                    
                    with Horizontal():
                        yield Button("✅ Submit", id="submit-btn", variant="primary")
                        yield Button("❌ Cancel", id="cancel-btn")
            
            yield Footer()
        
        def on_button_pressed(self, event: Button.Pressed) -> None:
            """Handle button press"""
            if event.button.id == "submit-btn":
                self.submit_feedback()
            elif event.button.id == "cancel-btn":
                self.dismiss()
        
        def submit_feedback(self) -> None:
            """Submit feedback"""
            try:
                rating_select = self.query_one("#rating-select", Select)
                feedback_type_select = self.query_one("#feedback-type-select", Select)
                comment_area = self.query_one("#feedback-comment", TextArea)
                
                rating = rating_select.value
                feedback_type = feedback_type_select.value
                comment = comment_area.text.strip()
                
                FEEDBACK_COLLECTOR.submit_feedback(
                    task=self.task,
                    task_type=self.task_type,
                    feedback_type=feedback_type,
                    rating=rating,
                    comment=comment if comment else None,
                    interaction_id=self.interaction_id
                )
                
                self.app.notify("✅ Feedback submitted successfully!", severity="success")
                self.dismiss()
                
            except Exception as e:
                self.app.notify(f"Error submitting feedback: {str(e)}", severity="error")
        
        def action_dismiss(self) -> None:
            """Dismiss modal"""
            self.dismiss()


    class AgentStatusScreen(Screen):
        """Screen for viewing agent status and configuration"""
        
        BINDINGS = [
            Binding("escape", "app.pop_screen", "Back"),
        ]
        
        def compose(self) -> ComposeResult:
            """Compose agent status screen"""
            yield Header(show_clock=True)
            
            with Container(id="agent-status-container"):
                yield Static("🤖 Agent Status", classes="section-title")
                
                with ScrollableContainer(id="agent-status-content"):
                    # Implementation Agent
                    yield Static("Implementation Agent", classes="subsection-title")
                    yield Static("Model: qwen2.5-coder:7b", id="impl-status")
                    yield Static("Status: Active", id="impl-status-info")
                    
                    # Test Generator Agent
                    yield Static("\nTest Generator Agent", classes="subsection-title")
                    yield Static("Model: qwen2.5-coder:14b", id="test-status")
                    yield Static("Status: Active", id="test-status-info")
                    
                    # Validation Agent
                    yield Static("\nValidation Agent", classes="subsection-title")
                    yield Static("Model: qwen2.5-coder:7b", id="validation-status")
                    yield Static("Status: Active", id="validation-status-info")
                    
                    # System Components
                    yield Static("\nSystem Components", classes="subsection-title")
                    yield Static("✅ Metrics Tracker: Active", id="metrics-status")
                    yield Static("✅ Error Learning: Active", id="error-status")
                    yield Static("✅ Routing Optimizer: Active", id="routing-status")
                    yield Static("✅ Feedback Collector: Active", id="feedback-status")
                    yield Static("✅ Test Suite: Active", id="test-suite-status")
            
            yield Footer()
        
        def on_mount(self) -> None:
            """Called when screen is mounted"""
            self.app.sub_title = "Agent Status"
            self.update_status()
        
        def update_status(self) -> None:
            """Update agent status information"""
            try:
                config_manager = CONFIG_MANAGER
                
                # Update Implementation Agent
                impl_config = config_manager.get_model_config("implementation")
                if impl_config:
                    impl_status = self.query_one("#impl-status", Static)
                    impl_status.update(f"Model: {impl_config.name} | Tokens: {impl_config.max_tokens} | Temp: {impl_config.temperature}")
                
                # Update Test Generator
                test_config = config_manager.get_model_config("test_generator")
                if test_config:
                    test_status = self.query_one("#test-status", Static)
                    test_status.update(f"Model: {test_config.name} | Tokens: {test_config.max_tokens} | Temp: {test_config.temperature}")
                
                # Update Validation Agent
                validation_config = config_manager.get_model_config("validation")
                if validation_config:
                    validation_status = self.query_one("#validation-status", Static)
                    validation_status.update(f"Model: {validation_config.name} | Tokens: {validation_config.max_tokens} | Temp: {validation_config.temperature}")
                
                # Update system components
                try:
                    from tests.test_suite_framework import TEST_SUITE_FRAMEWORK
                    tasks = TEST_SUITE_FRAMEWORK.load_tasks()
                    test_suite_status = self.query_one("#test-suite-status", Static)
                    test_suite_status.update(f"✅ Test Suite: Active ({len(tasks)} tasks)")
                except:
                    pass
                    
            except Exception as e:
                self.app.notify(f"Error updating status: {str(e)}", severity="warning")

