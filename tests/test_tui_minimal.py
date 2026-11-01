#!/usr/bin/env python3
"""
Minimal TUI test to verify button clicks and events work
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from textual.app import App, ComposeResult
    from textual.widgets import Button, Header, Footer, Static
    from textual.binding import Binding
    TEXTUAL_AVAILABLE = True
except ImportError as e:
    print(f"❌ Textual not available: {e}")
    TEXTUAL_AVAILABLE = False
    sys.exit(1)

if TEXTUAL_AVAILABLE:
    class MinimalTestApp(App):
        """Minimal test app to verify button clicks work"""
        
        BINDINGS = [
            Binding("ctrl+r", "test_action", "Test Action"),
            Binding("ctrl+q", "quit", "Quit"),
        ]
        
        def compose(self) -> ComposeResult:
            yield Header(show_clock=False)
            yield Static("Minimal TUI Test", id="title")
            yield Button("Click Me!", id="test-btn", variant="primary")
            yield Static("Status: Ready", id="status")
            yield Footer()
        
        def on_button_pressed(self, event: Button.Pressed) -> None:
            """Handle button presses"""
            button_id = event.button.id
            print(f"✅ BUTTON PRESSED: {button_id}")
            
            if button_id == "test-btn":
                status = self.query_one("#status", Static)
                status.update("Status: ✅ Button clicked!")
                self.notify("✅ Button click detected!", severity="success")
        
        def action_test_action(self) -> None:
            """Test action for Ctrl+R"""
            print("✅ KEYBOARD ACTION TRIGGERED (Ctrl+R)")
            status = self.query_one("#status", Static)
            status.update("Status: ✅ Ctrl+R pressed!")
            self.notify("✅ Keyboard binding works!", severity="success")
        
        def on_mount(self) -> None:
            self.title = "Minimal TUI Test"
            print("✅ App mounted")
            self.notify("App started - try clicking the button or pressing Ctrl+R", severity="information")
    
    def main():
        print("=" * 60)
        print("Minimal TUI Test")
        print("=" * 60)
        print("This will test if:")
        print("1. Button clicks work")
        print("2. Keyboard bindings work (Ctrl+R)")
        print("3. Notifications appear")
        print("\nPress Ctrl+R or click the button to test")
        print("=" * 60)
        
        app = MinimalTestApp()
        app.run()
    
    if __name__ == "__main__":
        main()

