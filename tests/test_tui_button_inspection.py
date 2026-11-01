#!/usr/bin/env python3
"""
Test to inspect if buttons exist and have correct IDs in the actual TUI
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_button_definition():
    """Check if the button is defined correctly in the compose method"""
    print("=" * 60)
    print("Testing Button Definition")
    print("=" * 60)
    
    # Read the TUI file
    tui_file = project_root / "tui" / "main.py"
    with open(tui_file) as f:
        content = f.read()
    
    # Check for button definition
    if 'id="run-btn"' in content:
        print("✅ Found button with id='run-btn'")
    else:
        print("❌ Button with id='run-btn' NOT FOUND")
    
    # Check for button in compose
    if 'Button' in content and 'run-btn' in content:
        print("✅ Button appears in code")
        # Try to find the exact line
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if 'run-btn' in line:
                print(f"   Line {i}: {line.strip()}")
    else:
        print("❌ Button definition not found")
    
    # Check for button handler
    if 'on_button_pressed' in content:
        print("✅ Found on_button_pressed handler")
    else:
        print("❌ on_button_pressed handler NOT FOUND")
    
    # Check for action method
    if 'def action_run_task' in content:
        print("✅ Found action_run_task method")
    else:
        print("❌ action_run_task method NOT FOUND")
    
    # Check for binding
    if 'Binding("ctrl+r", "run_task"' in content or "Binding('ctrl+r', 'run_task'" in content:
        print("✅ Found Ctrl+R binding")
    else:
        print("❌ Ctrl+R binding NOT FOUND")

def test_imports():
    """Test if all required imports work"""
    print("\n" + "=" * 60)
    print("Testing Imports")
    print("=" * 60)
    
    try:
        from textual.app import App
        print("✅ textual.app imported")
    except Exception as e:
        print(f"❌ Failed to import textual.app: {e}")
    
    try:
        from textual.widgets import Button
        print("✅ textual.widgets.Button imported")
    except Exception as e:
        print(f"❌ Failed to import Button: {e}")
    
    try:
        from tui.main import TaskInputScreen
        print("✅ TaskInputScreen imported")
    except Exception as e:
        print(f"❌ Failed to import TaskInputScreen: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_button_definition()
    test_imports()

