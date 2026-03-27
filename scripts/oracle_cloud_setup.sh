#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════
# 🛡️ AGL Security Tool — Oracle Cloud Setup (24GB RAM)
# أداة AGL للتدقيق الأمني — إعداد سحابة أوراكل (24 جيجا رام)
#
# هذا السكربت يُهيئ خادم Oracle Cloud Always Free (ARM/x86)
# بالكامل مع جميع الأدوات والاعتمادات
#
# Usage:
#   1. SSH to your Oracle Cloud instance
#   2. Upload this file or curl it:
#      curl -O https://raw.githubusercontent.com/alanqamarqo-dev/your-repo/agl_security/scripts/oracle_cloud_setup.sh
#   3. chmod +x oracle_cloud_setup.sh && ./oracle_cloud_setup.sh
#
# After setup:
#   python3 scripts/colab_full_audit.py --target <repo_url> --mode deep --skip-install
#
# ═══════════════════════════════════════════════════════════════════════

set -e

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║   🛡️  AGL Security Tool — Oracle Cloud Setup               ║"
echo "║   إعداد سحابة أوراكل — 24 جيجا رام                          ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# ─── System info ──────────────────────────────────────────────────
echo "📊 System Info:"
echo "  CPU: $(nproc) cores"
echo "  RAM: $(free -h | awk '/Mem:/ {print $2}')"
echo "  Disk: $(df -h / | awk 'NR==2 {print $4}') free"
echo "  Arch: $(uname -m)"
echo "  OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
echo ""

# ─── [1/6] System packages ───────────────────────────────────────
echo "📦 [1/6] Installing system packages / تثبيت حزم النظام..."
sudo apt-get update -qq
sudo apt-get install -y -qq \
    python3 python3-pip python3-venv \
    git curl wget \
    build-essential \
    software-properties-common \
    npm nodejs 2>/dev/null || true
echo "  ✅ System packages installed"
echo ""

# ─── [2/6] Python environment ────────────────────────────────────
echo "🐍 [2/6] Setting up Python environment / تهيئة بيئة بايثون..."

WORK_DIR="$HOME/agl-audit"
mkdir -p "$WORK_DIR"
cd "$WORK_DIR"

# Create venv
python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip -q
echo "  ✅ Python $(python3 --version | cut -d' ' -f2) + venv ready"
echo ""

# ─── [3/6] Clone the tool ────────────────────────────────────────
echo "📂 [3/6] Cloning AGL Security Tool / استنساخ أداة AGL..."

# ═══════════════════════════════════════════
# 👇 غيّر هذا إلى رابط مستودعك
TOOL_REPO="https://github.com/alanqamarqo-dev/your-repo.git"
BRANCH="agl_security"
# ═══════════════════════════════════════════

if [ -d "tool" ]; then
    echo "  ♻️ Already exists, pulling latest..."
    cd tool && git pull origin $BRANCH && cd ..
else
    git clone --branch $BRANCH --depth 1 $TOOL_REPO tool
fi

cd tool
echo "  ✅ Tool cloned at $(pwd)"
echo ""

# ─── [4/6] Python dependencies ───────────────────────────────────
echo "📥 [4/6] Installing Python dependencies / تثبيت اعتمادات بايثون..."

# Core deps
pip install -q z3-solver requests pytest

# External security tools
pip install -q slither-analyzer
pip install -q semgrep
pip install -q solc-select

# Mythril — heavy but powerful (24GB RAM can handle it!)
echo "  📥 Installing Mythril (EVM symbolic execution)..."
pip install -q mythril || echo "  ⚠️ Mythril install failed (optional)"

echo "  ✅ Python dependencies installed"
echo ""

# ─── [5/6] Solidity compiler ─────────────────────────────────────
echo "⚙️ [5/6] Installing Solidity compiler / تثبيت مُصرّف Solidity..."

# Install multiple versions for compatibility
for ver in 0.8.19 0.8.20 0.8.21 0.8.24 0.7.6 0.6.12; do
    solc-select install $ver 2>/dev/null || true
done
solc-select use 0.8.19

echo "  ✅ Solidity compilers installed"
echo ""

# ─── [6/6] Verify everything ─────────────────────────────────────
echo "🔧 [6/6] Verifying tools / التحقق من الأدوات..."

echo -n "  Python: "; python3 --version
echo -n "  solc:   "; solc --version 2>/dev/null | head -1 || echo "⚠️ not found"
echo -n "  slither: "; slither --version 2>/dev/null || echo "⚠️ not found"
echo -n "  semgrep: "; semgrep --version 2>/dev/null || echo "⚠️ not found"
echo -n "  myth:    "; myth version 2>/dev/null || echo "⚠️ not found (optional)"
echo -n "  z3:     "; python3 -c "import z3; print(z3.get_version_string())" 2>/dev/null || echo "⚠️ not found"

# Verify tool import
python3 -c "
import sys
sys.path.insert(0, '.')
from agl_security_tool import AGLSecurityAudit, __version__
from agl_security_tool.detectors import DetectorRunner
audit = AGLSecurityAudit()
dr = DetectorRunner()
print(f'  🛡️ AGL Security Tool v{__version__} — {len(dr.detectors)} detectors')
"

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║   ✅  SETUP COMPLETE / اكتمل الإعداد                        ║"
echo "║                                                              ║"
echo "║   24GB RAM = ALL 12 layers at full power!                    ║"
echo "║   24 جيجا رام = كل الـ 12 طبقة بالقوة الكاملة!               ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║                                                              ║"
echo "║   USAGE / الاستخدام:                                         ║"
echo "║                                                              ║"
echo "║   # Activate environment                                     ║"
echo "║   source ~/agl-audit/venv/bin/activate                       ║"
echo "║   cd ~/agl-audit/tool                                        ║"
echo "║                                                              ║"
echo "║   # Scan a project (deep mode — all 12 layers)               ║"
echo "║   python3 scripts/oracle_audit.py <target> [--mode deep]     ║"
echo "║                                                              ║"
echo "║   # Examples:                                                 ║"
echo "║   python3 scripts/oracle_audit.py \\                          ║"
echo "║     https://github.com/owner/defi-protocol                   ║"
echo "║                                                              ║"
echo "║   python3 scripts/oracle_audit.py \\                          ║"
echo "║     tinchoabbate/damn-vulnerable-defi                        ║"
echo "║                                                              ║"
echo "║   # Results → ~/agl-audit/tool/audit_reports/                ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
