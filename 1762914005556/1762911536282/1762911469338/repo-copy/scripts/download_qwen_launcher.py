"""Launcher that runs the fixed downloader while avoiding local-package shadowing.

It removes the project root from sys.path so local modules like `torch.py`
won't shadow the real installed packages in the venv. Use this when the
repo contains top-level modules named like popular packages.
"""

import runpy
import os
import sys

this_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(this_dir, '..'))
# remove project root and empty path entries from sys.path
sys.path = [p for p in sys.path if p and os.path.abspath(p) != project_root]

script_path = os.path.join(this_dir, 'download_qwen_fixed.py')
if not os.path.exists(script_path):
    raise SystemExit(f'Expected script not found: {script_path}')

# Execute the downloader as __main__ so it behaves like a script
runpy.run_path(script_path, run_name='__main__')
