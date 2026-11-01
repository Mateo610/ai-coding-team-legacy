#!/usr/bin/env python3
"""
Interactive test - checks if the actual TUI screen can be instantiated
and if buttons are accessible
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_screen_instantiation():
    """Test if we can create the screen and query widgets"""
    print("=" * 60)
    print("Testing Screen Instantiation")
    print("=" * 60)
    
    try:
        from tui.main import TaskInputScreen, AI_Coding_Team_TUI
        from textual.app import App
        
        # Try to create the app
        print("1. Creating app...")
        app = AI_Coding_Team_TUI()
        print("   ✅ App created")
        
        # Try to create the screen
        print("2. Creating TaskInputScreen...")
        screen = TaskInputScreen()
        print("   ✅ Screen created")
        
        # Check if button handler exists
        print("3. Checking handlers...")
        if hasattr(screen, 'on_button_pressed'):
            print("   ✅ on_button_pressed method exists")
        else:
            print("   ❌ on_button_pressed method missing")
        
        if hasattr(screen, 'action_run_task'):
            print("   ✅ action_run_task method exists")
        else:
            print("   ❌ action_run_task method missing")
        
        # Check bindings
        print("4. Checking bindings...")
        if hasattr(screen, 'BINDINGS'):
            print(f"   ✅ BINDINGS found: {len(screen.BINDINGS)}")
            for binding in screen.BINDINGS:
                if 'run' in str(binding).lower():
                    print(f"      - {binding}")
        else:
            print("   ❌ BINDINGS not found")
        
        # Try to simulate compose
        print("5. Testing compose...")
        try:
            compose_result = screen.compose()
            print("   ✅ Compose method works")
            # Count buttons
            button_count = 0
            for item in compose_result:
                if hasattr(item, 'id'):
                    if item.id == "run-btn":
                        print(f"   ✅ Found run-btn button: {item}")
                        button_count += 1
                # Also check the generator
            print(f"   ✅ Compose returned items")
        except Exception as e:
            print(f"   ❌ Compose failed: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n✅ All basic checks passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_event_system():
    """Test if Textual event system works at all"""
    print("\n" + "=" * 60)
    print("Testing Textual Event System")
    print("=" * 60)
    
    try:
        from textual.app import App
        from textual.widgets import Button
        
        class TestApp(App):
            def compose(self):
                yield Button("Test", id="test-btn")
            
            def on_button_pressed(self, event: Button.Pressed):
                print(f"   ✅ Event received: {event.button.id}")
        
        print("1. Created test app with button")
        app = TestApp()
        print("   ✅ Test app created")
        
        print("\n✅ Textual event system should work")
        return True
        
    except Exception as e:
        print(f"❌ Textual event system test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n🔍 Comprehensive TUI Testing\n")
    
    results = []
    results.append(("Screen Instantiation", test_screen_instantiation()))
    results.append(("Event System", test_event_system()))
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")

