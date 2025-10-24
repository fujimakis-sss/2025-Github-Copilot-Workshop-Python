# AGENTS.md

## Python Command Usage

**CRITICAL:** This environment uses Windows Python Launcher.

- **Before venv activation:** Use `py` command
- **After venv activation:** Use `python` command (NOT `py`)

```powershell
# Setup
py -m venv .venv
py -m pip install -r requirements.txt

# Activate venv
.\.venv\Scripts\Activate.ps1

# After activation - use python (py ignores venv)
python app.py
python -m pytest
```

**Why:** `py` launcher always references system Python and ignores virtual environments.
