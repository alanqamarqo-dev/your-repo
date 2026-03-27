#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
# 🛡️ AGL Full Pipeline Audit — WSL Runner
# سكريبت تشغيل الفحص الأمني الكامل عبر WSL
#
# Usage:
#   bash scripts/run_audit_wsl.sh                     # Scan default contracts
#   bash scripts/run_audit_wsl.sh /path/to/contract.sol  # Scan specific file
#   bash scripts/run_audit_wsl.sh /path/to/contracts/    # Scan entire directory
#
# WSL Setup (one-time):
#   # Create venv on ext4 (NOT /mnt/d NTFS!)
#   python3 -m venv ~/agl_venv
#   source ~/agl_venv/bin/activate
#   pip install z3-solver numpy scipy sympy requests
#   # Optional: pip install slither-analyzer mythril
# ═══════════════════════════════════════════════════════════════
set -euo pipefail

# ── Colors ──
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}🛡️  AGL Security — Full Pipeline Audit (WSL)${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"

# ── Detect project root ──
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo -e "${BLUE}📂 Project root:${NC} $PROJECT_ROOT"

# ── Auto-detect or activate virtual environment ──
if [ -n "${VIRTUAL_ENV:-}" ]; then
    echo -e "${GREEN}✅ Virtual env active:${NC} $VIRTUAL_ENV"
elif [ -f "$HOME/agl_venv/bin/activate" ]; then
    echo -e "${YELLOW}🔄 Activating ~/agl_venv...${NC}"
    source "$HOME/agl_venv/bin/activate"
elif [ -f "$PROJECT_ROOT/.venv/bin/activate" ]; then
    echo -e "${YELLOW}🔄 Activating .venv...${NC}"
    source "$PROJECT_ROOT/.venv/bin/activate"
else
    echo -e "${YELLOW}⚠️  No virtual env found — using system Python${NC}"
fi

# ── Ensure PYTHONPATH includes project root ──
export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH:-}"

# ── Check Python and z3 ──
echo -e "\n${BLUE}🔍 Environment check:${NC}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
echo "   Python: $($PYTHON_BIN --version 2>&1)"

$PYTHON_BIN -c "import z3; print(f'   Z3:     v{z3.get_version_string()}')" 2>/dev/null || \
    echo -e "   ${YELLOW}Z3:     NOT installed (pip install z3-solver)${NC}"

$PYTHON_BIN -c "import numpy; print(f'   NumPy:  v{numpy.__version__}')" 2>/dev/null || \
    echo -e "   ${YELLOW}NumPy:  NOT installed (pip install numpy)${NC}"

# ── Check for solc (needed for Slither/Mythril) ──
if command -v solc &>/dev/null; then
    SOLC_VER=$(solc --version 2>/dev/null | grep -oP 'Version: \K[0-9.]+' || echo "unknown")
    echo "   solc:   v$SOLC_VER"
elif [ -f "$HOME/.solc-select/artifacts/solc-0.8.28/solc-0.8.28" ]; then
    echo "   solc:   via solc-select"
    export PATH="$HOME/.solc-select/artifacts/solc-0.8.28:$PATH"
else
    echo -e "   ${YELLOW}solc:   NOT found (Slither/Mythril disabled)${NC}"
fi

# ── Check optional tools ──
command -v slither &>/dev/null && echo "   Slither: $(slither --version 2>&1 | head -1)" || \
    echo -e "   ${YELLOW}Slither: NOT installed (optional)${NC}"

# ── Determine target ──
TARGET="${1:-}"
EXTRA_ARGS=""

if [ -n "$TARGET" ]; then
    # User specified a target
    if [ -f "$TARGET" ]; then
        echo -e "\n${GREEN}🎯 Target: single file — $TARGET${NC}"
        EXTRA_ARGS="--target $TARGET"
    elif [ -d "$TARGET" ]; then
        echo -e "\n${GREEN}🎯 Target: directory — $TARGET${NC}"
        EXTRA_ARGS="--target $TARGET"
    else
        echo -e "${RED}❌ Target not found: $TARGET${NC}"
        exit 1
    fi
else
    echo -e "\n${GREEN}🎯 Target: all project contracts (default)${NC}"
fi

# ── Run the audit ──
echo -e "\n${CYAN}🚀 Starting full pipeline audit...${NC}\n"

cd "$PROJECT_ROOT"
$PYTHON_BIN scripts/run_full_audit.py $EXTRA_ARGS

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo -e "\n${GREEN}════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}✅ Audit complete! Reports saved to:${NC}"
    echo -e "   📝 reports/FULL_AUDIT_REPORT.md"
    echo -e "   📊 reports/full_pipeline_audit.json"
    echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
else
    echo -e "\n${RED}❌ Audit failed with exit code $EXIT_CODE${NC}"
    exit $EXIT_CODE
fi
