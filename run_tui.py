#!/usr/bin/env python3
"""
Launch the AI Coding Team TUI
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    try:
        from tui.main import main
        main()
    except ImportError as e:
        print(f"❌ Error: {e}")
        print("\nPlease install required dependencies:")
        print("  pip install textual")
        print("\nOr install all requirements:")
        print("  pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting TUI: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

