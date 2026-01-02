# Scripts

This directory contains utility scripts for maintenance, bootstrapping, and analysis.

## Key Scripts

- **verify_integration.py**: Checks if all components are connected correctly.
- **inspect_learning.py**: Analyzes the learning logs and memory artifacts.
- **stats_cruncher.py**: Generates statistics about system performance.
- **talk_to_agl.py**: A CLI interface to chat directly with the agent.
- **check_security.py**: Scans for security vulnerabilities.

## Usage

Run these scripts from the root directory:

```powershell
python scripts/verify_integration.py
```

## How to Run (General)

**Important:** Always run these scripts from the **project root directory** (`D:\AGL`) to ensure all imports work correctly.

### Examples:

```bash
# Correct way (from D:\AGL)
python scripts/run_strict_test.py
python scripts/activate_mother_system.py

# Incorrect way (do not do this)
cd scripts
python run_strict_test.py  # This will likely fail with ImportError
```
