# 🧹 Repo-Copy Organization Plan (خطة تنظيم القلب النابض)

Since `repo-copy` is the "Beating Heart" of the system, we must organize it **internally** without moving it or breaking its structure.

## 1. Proposed Structure
We will create subfolders *inside* `repo-copy` to house the clutter:

*   `repo-copy/logs/`: For all `.log` files.
*   `repo-copy/reports/`: For all `.json` test results and reports.
*   `repo-copy/temp_trash/`: For all `tmp_*` and `.tmp_*` files (to be deleted later after review).
*   `repo-copy/tests/`: For `test_*.py` files (if they are not already in a `tests` folder).
*   `repo-copy/scripts/`: For utility scripts like `fix_*.py`, `inspect_*.py`.

## 2. Action Plan

### Step 1: Move Logs
Move `*.log` -> `repo-copy/logs/`

### Step 2: Move Reports
Move `*.json` (excluding config files) -> `repo-copy/reports/`

### Step 3: Cleanup Temp Files
Move `tmp_*`, `.tmp_*` -> `repo-copy/temp_trash/` (or delete directly if authorized).

### Step 4: Organize Scripts
Move `fix_*.py`, `inspect_*.py`, `run_*.py` -> `repo-copy/scripts/`

## 3. Critical Safety Check
We will NOT move:
*   `Core_Engines/`
*   `Core_Memory/`
*   `Knowledge_Base/`
*   `AGL_UI/`
*   `config/`
*   Any file referenced by `AGL_Awakened.py` directly (though it mostly imports from subfolders).

---
*Waiting for user approval to execute.*
