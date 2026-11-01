# TUI Installation Fix

## Problem

The apt-installed `python3-textual` package (version 0.1.13) is too old and incompatible with our TUI code, which requires textual 0.70.0+ (API has changed significantly).

## Solution

Install the modern version of textual via pip:

```bash
pip3 install --user --upgrade --break-system-packages textual
```

This installs textual 6.6.0 (or latest) to your user site-packages, which takes precedence over the system-installed version.

## Why This Works

- Python's import system checks user site-packages (`~/.local/lib/python3.12/site-packages`) before system packages
- The modern version (6.6.0) includes all the widgets and components we need
- The `--user` flag installs to your home directory, avoiding system-wide changes

## Verification

After installation, verify it works:

```bash
python3 -c "
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Button
print('✅ Modern textual imports work!')
"
```

## Alternative: Virtual Environment

If you prefer to use a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
pip install textual
python3 run_tui.py
```

## Status

✅ **Fixed**: Textual 6.6.0 is now installed and working!

The TUI should now run correctly:
```bash
python3 run_tui.py
```

