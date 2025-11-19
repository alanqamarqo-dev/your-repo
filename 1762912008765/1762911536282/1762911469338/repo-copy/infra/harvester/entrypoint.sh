#!/bin/sh
set -euo pipefail

# Entry point: run harvester loop under a simple supervisor.
export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8

echo "Starting harvester supervisor (checks every 60s)"
while true; do
  # run harvester once (it will exit) and rely on supervisor for restarts
  python workers/knowledge_harvester.py || true
  sleep 60
done
