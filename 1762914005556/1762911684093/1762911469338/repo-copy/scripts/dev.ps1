# Dev helper script for AGL workspace
# Usage examples:
#   powershell -ExecutionPolicy Bypass -File .\scripts\dev.ps1
#   .\scripts\dev.ps1 -Data "data\hooke_sample.csv"

# run all tests
D:\AGL\.venv\Scripts\python.exe -m unittest discover -v tests

# coverage
D:\AGL\.venv\Scripts\python.exe -m coverage run -m unittest discover -s tests
D:\AGL\.venv\Scripts\python.exe -m coverage report -m

# quick train example
param([string]$Data = "data\hooke_sample.csv")
D:\AGL\.venv\Scripts\python.exe .\AGL.py --task "train-laws" --data $Data
