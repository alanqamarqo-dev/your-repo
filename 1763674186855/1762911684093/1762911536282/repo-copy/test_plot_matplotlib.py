import pytest

# Skip this module in smoke runs on environments where matplotlib may
# be incompatible with the Python version / available GUI backends.
pytest.skip("Skipping plotting in smoke runs (matplotlib backend compatibility)", allow_module_level=True)

