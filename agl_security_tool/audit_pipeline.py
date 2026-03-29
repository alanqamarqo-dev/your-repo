#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════════╗
║  AGL FULL-POWER DYNAMIC AUDIT API                                                ║
║  واجهة تدقيق أمني ديناميكية كاملة القوة — لأي مشروع عقود ذكية                 ║
╠══════════════════════════════════════════════════════════════════════════════════╣
║                                                                                  ║
║  الوصف العام:                                                                    ║
║    هذا الملف هو نقطة الدخول الرئيسية لمنظومة التدقيق الأمني AGL.                ║
║    يُنسِّق تشغيل 8 طبقات تحليلية متتالية على أي مشروع عقود ذكية               ║
║    (Solidity) سواء كان محلياً أو على GitHub.                                     ║
║                                                                                  ║
║  البنية المعمارية (خط الأنابيب — Pipeline):                                      ║
║                                                                                  ║
║    ┌─────────────────────────────────────────────────────────────────-─┐           ║
║    │ المرحلة 0: تحليل الهدف واستنساخه إن كان رابط Git               │           ║
║    │ المرحلة 1: تحميل جميع المحركات ديناميكياً                      │           ║
║    │ المرحلة 2: اكتشاف بنية المشروع (Foundry/Hardhat/Truffle/Bare)  │           ║
║    │ المرحلة 2.5: التحليل الدلالي المشترك (تحليل مرة واحدة للجميع) │           ║
║    │ المرحلة 3: الفحص العميق Layer 0-5 (Z3 + أنماط + كواشف)        │           ║
║    │ المرحلة 4: Z3 على المكتبات فقط (العقود الرئيسية مُغطاة)       │           ║
║    │ المرحلة 5: استخراج الحالة المالية + محاكاة الهجمات             │           ║
║    │ المرحلة 6: 22 كاشف دلالي على المكتبات                         │           ║
║    │ المرحلة 7: تحليل الاستغلال بإثبات Z3                          │           ║
║    │ المرحلة 8: خوارزميات هيكل الرياضية (نفق + موجة + هولوغرام)    │           ║
║    │ المرحلة 8.5: إزالة التكرارات عبر الطبقات                      │           ║
║    │ المرحلة 8.7: توليد PoC ديناميكي + تشغيل Foundry               │           ║
║    │ المرحلة 9: توليد التقرير النهائي                               │           ║
║    └─────────────────────────────────────────────────────────────────-─┘           ║
║                                                                                  ║
║  الطبقات التحليلية:                                                              ║
║    Layer 0   : Solidity Flattener — تسطيح ملفات Solidity                         ║
║    Layer 0.5 : Z3 Symbolic Engine — تنفيذ رمزي رياضي (BitVec 256-bit)            ║
║    Layer 1-4 : State Extraction — استخراج الحالة + فضاء الأفعال + محاكاة هجوم   ║
║    Layer 5   : 22 Semantic Detectors — كواشف دلالية متخصصة                       ║
║    Layer 6   : Exploit Reasoning — إثبات قابلية الاستغلال بـ Z3 SAT             ║
║    Layer 7   : Heikal Math — خوارزميات النفق الكمومي والموجة والهولوغرام        ║
║                                                                                  ║
║  أنواع الأهداف المدعومة:                                                         ║
║    • مسار محلي لمشروع (Foundry / Hardhat / Truffle / Brownie / Ape / Bare)       ║
║    • رابط GitHub مباشر (يُستنسَخ تلقائياً مع الوحدات الفرعية)                   ║
║    • ملف .sol واحد (يُستخدم المجلد الأب كجذر المشروع)                           ║
║                                                                                  ║
║  أمثلة الاستخدام:                                                                ║
║    python agl_audit_api.py <path_or_github_url>                                  ║
║    python agl_audit_api.py https://github.com/Uniswap/v3-core                   ║
║    python agl_audit_api.py ./my-defi-project                                     ║
║    python agl_audit_api.py contract.sol                                           ║
║    python agl_audit_api.py <target> --mode deep --format markdown -o report.md   ║
║    python agl_audit_api.py <target> --skip-heikal   # بدون Heikal Math          ║
║    python agl_audit_api.py <target> --include-deps   # فحص المكتبات أيضاً       ║
║                                                                                  ║
║  أوضاع التشغيل:                                                                  ║
║    full  — جميع الطبقات (0-7) + خوارزميات هيكل (الأكمل والأبطأ)                ║
║    deep  — الطبقات 0-6 بدون هيكل (أسرع، كافٍ لمعظم الحالات)                    ║
║    quick — أنماط فقط بدون Z3 أو استخراج حالة (الأسرع)                           ║
║                                                                                  ║
║  المخرجات:                                                                        ║
║    • تقرير JSON كامل (افتراضي) يحوي كل النتائج المُوحَّدة                       ║
║    • تقرير Markdown مُنسَّق للقراءة البشرية                                     ║
║    • ملخص خطورة مُوحَّد بعد إزالة التكرارات عبر الطبقات                        ║
╚══════════════════════════════════════════════════════════════════════════════════╝
"""

import logging
import sys
import os
import re
import json
import time
import shutil
import argparse
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

# === إعداد المسارات ===
# الجذر = المستوى الأعلى للمشروع (أب مجلد الحزمة)
ROOT = Path(__file__).resolve().parent.parent


# ═══════════════════════════════════════════════════════════
#  AuditContext — سياق مشترك بين كل الطبقات
#  كل طبقة تقرأ من وتكتب إلى هذا الكائن بدل dicts منفصلة
# ═══════════════════════════════════════════════════════════


class AuditContext:
    """
    كائن سياق مشترك يربط كل طبقات التدقيق.

    بدلاً من أن تعمل كل طبقة بمعزل وتُمرر النتائج في dicts متفرقة،
    AuditContext يجمع:
      - النتائج المحللة مسبقاً (shared_parse)
      - النتائج التراكمية من كل طبقة
      - الدوال الآمنة المعروفة (safe_funcs)
      - Z3 proofs المُثبتة
      - أي بيانات تحتاجها طبقة لاحقة من طبقة سابقة

    يتكامل مع النمط الحالي (dicts) بشكل تدريجي —
    الطبقات التي لم تُحدَّث بعد تستمر بالعمل كالسابق.
    """

    def __init__(self):
        # Shared parse data (from run_shared_parsing)
        self.shared_parse: Dict[str, Dict] = {}

        # Per-contract findings from each layer
        self.deep_scan_results: Dict[str, Dict] = {}
        self.z3_findings: List[Dict] = []
        self.detector_findings: List[Dict] = []
        self.exploit_results: Dict[str, Dict] = {}
        self.heikal_results: Dict[str, Dict] = {}
        self.state_results: Dict[str, Dict] = {}

        # Cross-layer intelligence
        self.safe_functions: Dict[str, set] = {}  # contract -> {safe_func_names}
        self.z3_proven: Dict[str, List[Dict]] = {}  # contract -> [proven findings]
        self.remappings: List[str] = []  # Solidity import remappings

        # Unified findings (after dedup)
        self.unified_findings: List[Dict] = []

    def get_z3_proven_for(self, contract_name: str) -> List[Dict]:
        """Get Z3-proven findings for a specific contract."""
        return self.z3_proven.get(contract_name, [])

    def mark_safe_function(self, contract_name: str, func_name: str):
        """Mark a function as verified-safe (suppress FPs in later stages)."""
        self.safe_functions.setdefault(contract_name, set()).add(func_name)

    def is_safe_function(self, contract_name: str, func_name: str) -> bool:
        """Check if a function has been marked as safe."""
        return func_name in self.safe_functions.get(contract_name, set())

    def add_z3_proof(self, contract_name: str, finding: Dict):
        """Register a Z3-proven finding for cross-layer use."""
        self.z3_proven.setdefault(contract_name, []).append(finding)

    # ── Integration helpers ──────────────────────────────

    def populate_from_shared_parse(self, shared_parse: Dict):
        """استيراد الدوال الآمنة والبيانات المشتركة من التحليل الدلالي."""
        self.shared_parse = shared_parse
        # _safe_funcs is a flat set of lowercase function names
        self._global_safe_funcs: set = shared_parse.get("_safe_funcs", set())
        self.remappings = shared_parse.get("_remappings", [])

    def is_globally_safe(self, func_name: str) -> bool:
        """Check if a function is safe (internal/private/view/pure) globally."""
        return func_name.lower() in getattr(self, "_global_safe_funcs", set())

    def store_layer_result(self, layer: str, results):
        """تخزين نتائج طبقة تلقائياً في الحقل المناسب."""
        if layer == "deep_scan":
            self.deep_scan_results = results
        elif layer == "z3_symbolic":
            self.z3_findings = results if isinstance(results, list) else []
        elif layer == "detectors":
            self.detector_findings = results if isinstance(results, list) else []
        elif layer == "exploit_reasoning":
            self.exploit_results = results
        elif layer == "heikal_math":
            self.heikal_results = results
        elif layer == "state_extraction":
            self.state_results = results


# ═══════════════════════════════════════════════════════════
#  أدوات مساعدة — UTILITIES
#  دوال بسيطة تُستخدم في أنحاء الملف (طباعة، فحص روابط، استنساخ)
# ═══════════════════════════════════════════════════════════


def banner(text: str, char="═"):
    """طباعة عنوان مُحاط بإطار لتسهيل قراءة الخرج في الطرفية."""
    width = 80
    print(f"\n{char * width}")
    print(f"  {text}")
    print(f"{char * width}")


def is_github_url(target: str) -> bool:
    """التحقق مما إذا كان الهدف رابط GitHub صالح."""
    return bool(re.match(r"https?://github\.com/[\w\-\.]+/[\w\-\.]+", target))


def is_git_url(target: str) -> bool:
    """التحقق مما إذا كان الهدف أي نوع من روابط Git (GitHub, git@, git://, .git)."""
    return (
        is_github_url(target)
        or target.endswith(".git")
        or target.startswith("git@")
        or target.startswith("git://")
    )


def clone_repo(
    url: str, dest: Optional[str] = None, branch: Optional[str] = None, depth: int = 1
) -> str:
    """
    استنساخ مستودع Git وإرجاع المسار المحلي.

    تُستخدم عندما يُعطى المستخدم رابط GitHub بدلاً من مسار محلي.
    يتم الاستنساخ في مجلد مؤقت (temp) يُحذف تلقائياً بعد انتهاء التدقيق.

    المعاملات:
        url: رابط المستودع (GitHub أو أي Git URL)
        dest: مسار الوجهة (اختياري — يُنشأ مجلد مؤقت إذا لم يُحدَّد)
        branch: الفرع أو العلامة المطلوب استنساخها (اختياري)
        depth: عمق الاستنساخ (1 = آخر commit فقط — أسرع وأخف)

    يُرجع:
        المسار المحلي للمستودع المُستنسَخ

    الأخطاء:
        RuntimeError: إذا فشل git clone أو لم يكن git مثبتاً
    """
    # Clean up URL
    url = url.rstrip("/")
    if not url.endswith(".git") and is_github_url(url):
        url = url + ".git"

    # Extract repo name for directory naming
    repo_name = url.split("/")[-1].replace(".git", "")

    if dest is None:
        dest = os.path.join(tempfile.mkdtemp(prefix="agl_audit_"), repo_name)
    else:
        dest = os.path.join(dest, repo_name)

    print(f"  📥 Cloning: {url}")
    print(f"     To: {dest}")

    cmd = ["git", "clone"]
    if depth > 0:
        cmd += ["--depth", str(depth)]
    if branch:
        cmd += ["--branch", branch]
    cmd += ["--recurse-submodules", "--shallow-submodules"]
    cmd += [url, dest]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 min timeout
        )
        if result.returncode != 0:
            # Try without submodules
            cmd_basic = ["git", "clone"]
            if depth > 0:
                cmd_basic += ["--depth", str(depth)]
            if branch:
                cmd_basic += ["--branch", branch]
            cmd_basic += [url, dest]

            result = subprocess.run(
                cmd_basic,
                capture_output=True,
                text=True,
                timeout=300,
            )
            if result.returncode != 0:
                raise RuntimeError(f"git clone failed: {result.stderr[:500]}")

        print(f"  ✅ Clone complete")
        return dest

    except FileNotFoundError:
        raise RuntimeError("git is not installed or not in PATH")
    except subprocess.TimeoutExpired:
        raise RuntimeError("git clone timed out (>5 min)")


def install_dependencies(project_path: str) -> None:
    """
    تثبيت اعتماديات المشروع تلقائياً عند الحاجة.

    يكتشف نوع المشروع ويُشغِّل الأمر المناسب:
      - Foundry → forge install (إذا وُجد foundry.toml)
      - Node.js → yarn install أو npm install (إذا وُجد package.json)

    الأخطاء تُبتلع بصمت (لا تُوقف التدقيق) لأن كثيراً من المشاريع
    تعمل بدون تثبيت الاعتماديات.
    """
    root = Path(project_path)

    # Foundry: forge install
    if (root / "foundry.toml").exists():
        print("  📦 Installing Foundry dependencies...")
        try:
            forge_path = shutil.which("forge")
            if forge_path:
                subprocess.run(
                    [forge_path, "install"],
                    cwd=str(root),
                    capture_output=True,
                    timeout=120,
                )
        except Exception:
            pass

    # Node: npm install / yarn
    if (root / "package.json").exists():
        print("  📦 Installing Node dependencies...")
        try:
            if (root / "yarn.lock").exists() and shutil.which("yarn"):
                subprocess.run(
                    ["yarn", "install"],
                    cwd=str(root),
                    capture_output=True,
                    timeout=180,
                )
            elif shutil.which("npm"):
                subprocess.run(
                    ["npm", "install"],
                    cwd=str(root),
                    capture_output=True,
                    timeout=180,
                )
        except Exception:
            pass


def resolve_target(
    target: str, branch: Optional[str] = None, no_deps: bool = False
) -> Tuple[str, bool]:
    """
    تحويل الهدف (أياً كان نوعه) إلى مسار مجلد محلي.

    يتعامل مع ثلاث حالات:
      1. رابط Git → يُستنسَخ في مجلد مؤقت + تُثبَّت الاعتماديات
      2. ملف .sol واحد → يُستخدم المجلد الأب كجذر المشروع
      3. مجلد محلي → يُستخدم مباشرة

    يُرجع:
        (المسار_المحلي, هل_مؤقت) — is_temp=True يعني أنه مُستنسَخ ويجب حذفه لاحقاً

    الأخطاء:
        FileNotFoundError: إذا لم يُوجد الهدف كملف أو مجلد
    """
    # Case 1: Git URL
    if is_git_url(target):
        local_path = clone_repo(target, branch=branch)
        if not no_deps:
            install_dependencies(local_path)
        return local_path, True

    # Case 2: Local path
    target_path = Path(target).resolve()

    if target_path.is_file() and target_path.suffix == ".sol":
        # Single .sol file — use its parent
        return str(target_path.parent), False

    if target_path.is_dir():
        return str(target_path), False

    raise FileNotFoundError(f"Target not found: {target}")


# ═══════════════════════════════════════════════════════════
#  مُحمِّل المحركات — ENGINE LOADER
#  يُحاول تحميل كل محرك من الطبقات 0-7 ديناميكياً.
#  إذا فشل محرك يُتجاوَز برسالة تحذير (لا يوقف التدقيق).
# ═══════════════════════════════════════════════════════════


def load_engines(project_root: str, *, core_config: Optional[Dict] = None) -> Dict[str, Any]:
    """
    تحميل جميع محركات التدقيق الأمني المتوفرة.

    يُحمِّل كل محرك داخل try/except مستقل حتى يعمل التدقيق
    حتى لو كانت بعض المحركات غير مثبتة.

    المحركات المُحمَّلة ومفاتيحها:
      - 'core'          : AGLSecurityAudit — الأنبوب الرئيسي (الطبقات 0-5)
      - 'z3'            : Z3SymbolicEngine — تنفيذ رمزي BitVec(256)
      - 'state'         : StateExtractionEngine — استخراج الحالة المالية
      - 'exploit'       : ExploitReasoningEngine — إثبات قابلية الاستغلال
      - 'flattener'     : SolidityFlattener — تسطيح الملفات
      - 'detectors'     : DetectorRunner — 22 كاشف دلالي
      - 'parser'        : SoliditySemanticParser — مُحلل العقود
      - 'tunneling'     : HeikalTunnelingScorer — نموذج النفق الكمومي
      - 'wave'          : WaveDomainEvaluator — تحليل الموجة
      - 'holographic'   : HolographicVulnerabilityMemory — أنماط هولوغرافية
      - 'resonance'     : ResonanceProfitOptimizer — تحسين العائد بالرنين

    المعاملات:
        project_root: المسار الجذري للمشروع (يُستخدم في StateExtractionEngine و Flattener)
        core_config:  إعدادات اختيارية تُمرر إلى AGLSecurityAudit (skip_llm, skip_deep_analyzer...)

    يُرجع:
        قاموس {اسم_المحرك: كائن_المحرك} — يحوي فقط المحركات التي نجح تحميلها
    """
    engines = {}

    # --- Core AGLSecurityAudit (wraps Layer 0-5) ---
    try:
        from agl_security_tool.core import AGLSecurityAudit

        engines["core"] = AGLSecurityAudit(config=core_config or {})
        print("  ✅ Layer 0-5: AGLSecurityAudit (Core Pipeline)")
    except Exception as e:
        print(f"  ⚠️  AGLSecurityAudit: {e}")

    # --- Z3 Symbolic Engine ---
    try:
        from agl_security_tool.z3_symbolic_engine import Z3SymbolicEngine

        engines["z3"] = Z3SymbolicEngine()
        print("  ✅ Layer 0.5: Z3 Symbolic Execution Engine")
    except Exception as e:
        print(f"  ⚠️  Z3SymbolicEngine: {e}")

    # --- State Extraction Engine (Layer 1-4) ---
    try:
        from agl_security_tool.state_extraction import StateExtractionEngine # type: ignore

        engines["state"] = StateExtractionEngine(
            {
                "project_root": project_root,
                "action_space": True,
                "attack_simulation": True,
                "search_engine": True,
            }
        )
        print("  ✅ Layer 1-4: State Extraction + Action Space + Attack Sim + Search")
    except Exception as e:
        print(f"  ⚠️  StateExtractionEngine: {e}")

    # --- Exploit Reasoning Layer ---
    try:
        from agl_security_tool.exploit_reasoning import ExploitReasoningEngine

        engines["exploit"] = ExploitReasoningEngine()
        print("  ✅ Layer 6: Exploit Reasoning (Z3 Path Extraction)")
    except Exception as e:
        print(f"  ⚠️  ExploitReasoningEngine: {e}")

    # --- Solidity Flattener ---
    try:
        from agl_security_tool.solidity_flattener import SolidityFlattener

        engines["flattener"] = SolidityFlattener(project_root)
        print("  ✅ Layer 0: Solidity Flattener")
    except Exception as e:
        print(f"  ⚠️  SolidityFlattener: {e}")

    # --- 22 Semantic Detectors (Layer 5) ---
    try:
        from agl_security_tool.detectors import DetectorRunner
        from agl_security_tool.detectors.solidity_ast_parser import SolidityASTParserFull

        engines["detectors"] = DetectorRunner()
        engines["parser"] = SolidityASTParserFull()
        print("  ✅ Layer 5: 22 Semantic Detectors (AST Parser)")
    except Exception as e:
        # Fallback to regex parser
        try:
            from agl_security_tool.detectors.solidity_parser import SoliditySemanticParser
            engines["parser"] = SoliditySemanticParser()
            print(f"  ⚠️  AST parser failed ({e}), using regex parser fallback")
        except Exception as e2:
            print(f"  ⚠️  DetectorRunner: {e2}")

    # --- Heikal Math Algorithms (Layer 7) ---
    try:
        from agl_security_tool.heikal_math import (
            HeikalTunnelingScorer,
            WaveDomainEvaluator,
            HolographicVulnerabilityMemory,
            ResonanceProfitOptimizer,
        )

        engines["tunneling"] = HeikalTunnelingScorer()
        engines["wave"] = WaveDomainEvaluator()
        engines["holographic"] = HolographicVulnerabilityMemory()
        engines["resonance"] = ResonanceProfitOptimizer()
        print("  ✅ Layer 7: Heikal Math (4 algorithms)")
    except Exception as e:
        print(f"  ⚠️  Heikal Math: {e}")

    return engines


# ═══════════════════════════════════════════════════════════
#  اكتشاف بنية المشروع — DYNAMIC PROJECT DISCOVERY
#  يكتشف نوع المشروع ويُصنِّف العقود إلى: رئيسية / مكتبات / واجهات
# ═══════════════════════════════════════════════════════════


def discover_project(project_path: str, config: Dict = None) -> Dict[str, Any]:
    """
    اكتشاف بنية المشروع وتصنيف العقود ديناميكياً.

    يقوم بـ:
      1. استخدام ProjectScanner (إن وُجد) لاكتشاف ذكي
      2. الرجوع للاكتشاف البسيط إذا فشل الماسح
      3. مسح جميع ملفات .sol في المشروع (مع استثناءات ذكية)
      4. تصنيف كل عقد كـ: رئيسي (main) / مكتبة (lib) / واجهة (interface)
      5. تحديد نوع المشروع: Foundry / Hardhat / Truffle / Bare

    مجلدات تُستثنى تلقائياً: node_modules, .git, cache, out, build,
    artifacts, typechain, coverage, crytic-export

    الإعدادات (عبر config):
      - exclude_tests: استثناء ملفات الاختبار (افتراضي: True)
      - scan_dependencies: فحص المكتبات الخارجية (افتراضي: False)

    يُرجع:
        {
            'project_type':    نوع المشروع (foundry/hardhat/truffle/bare),
            'contracts_dir':   مسار مجلد العقود,
            'contracts':       {اسم: مسار, ...} لجميع العقود,
            'main_contracts':  [اسم, ...] العقود الرئيسية,
            'libraries':       [اسم, ...] المكتبات,
            'interfaces':      [اسم, ...] الواجهات,
            'info':            معلومات المشروع من ProjectScanner
        }
    """
    config = config or {}

    try:
        from agl_security_tool.project_scanner import ProjectScanner

        scanner = ProjectScanner(project_path, config=config)
        scanner.discover()
        info = scanner.project_info
    except Exception as e:
        print(f"  ⚠️  ProjectScanner failed: {e}, using fallback discovery")
        info = None

    root = Path(project_path)
    contracts = {}
    main_contracts = []
    libraries = []
    interfaces = []

    # Determine contracts directory
    contracts_dir = None
    if info and info.contracts_dir:
        contracts_dir = info.contracts_dir
    else:
        # Fallback heuristic
        for candidate in ["src", "contracts", "."]:
            p = root / candidate
            if p.exists() and list(p.glob("**/*.sol")):
                contracts_dir = str(p)
                break
        if not contracts_dir:
            contracts_dir = str(root)

    contracts_path = Path(contracts_dir)

    # === Collect all .sol files ===
    exclude_dirs = {
        "node_modules",
        ".git",
        "cache",
        "out",
        "build",
        "artifacts",
        "typechain",
        "typechain-types",
        "coverage",
        "crytic-export",
    }
    exclude_tests = config.get("exclude_tests", True)
    scan_deps = config.get("scan_dependencies", False)

    def should_skip(dirpath: str) -> bool:
        parts = Path(os.path.relpath(dirpath, project_path)).parts
        if set(parts) & exclude_dirs:
            return True
        if not scan_deps and ("lib" in parts or "node_modules" in parts):
            return True
        if exclude_tests and any(
            p in parts
            for p in {"test", "tests", "test-foundry", "certora", "mocks", "mock"}
        ):
            return True
        return False

    def is_test_file(name: str) -> bool:
        lower = name.lower()
        return (
            lower.endswith(".t.sol")
            or lower.startswith("test")
            or lower.startswith("mock")
            or "harness" in lower
            or "helper" in lower
        )

    # Walk entire project
    for dirpath, dirnames, filenames in os.walk(project_path):
        if should_skip(dirpath):
            dirnames.clear()
            continue

        for fname in filenames:
            if not fname.endswith(".sol"):
                continue
            if exclude_tests and is_test_file(fname):
                continue

            fullpath = Path(dirpath) / fname
            rel = os.path.relpath(str(fullpath), project_path)
            parts = Path(rel).parts

            # Classify
            stem = fullpath.stem
            is_lib = any(p in ("libraries", "lib", "utils", "math") for p in parts)
            is_iface = any(
                p in ("interfaces", "interface") for p in parts
            ) or fname.startswith("I")

            if is_iface:
                key = f"iface/{stem}"
                interfaces.append(key)
            elif is_lib:
                key = f"lib/{stem}"
                libraries.append(key)
            else:
                key = stem
                main_contracts.append(key)

            contracts[key] = fullpath

    # Also scan the contracts_dir specifically if it's different from project root
    if str(contracts_path) != project_path:
        for sol_file in contracts_path.glob("*.sol"):
            stem = sol_file.stem
            if stem not in contracts and not (
                exclude_tests and is_test_file(sol_file.name)
            ):
                contracts[stem] = sol_file
                main_contracts.append(stem)

    project_type = "unknown"
    if info and info.project_type:
        project_type = info.project_type
    elif (root / "foundry.toml").exists():
        project_type = "foundry"
    elif (root / "hardhat.config.js").exists() or (root / "hardhat.config.ts").exists():
        project_type = "hardhat"
    elif (root / "truffle-config.js").exists():
        project_type = "truffle"
    else:
        project_type = "bare"

    return {
        "project_type": project_type,
        "contracts_dir": contracts_dir,
        "contracts": contracts,
        "main_contracts": list(set(main_contracts)),
        "libraries": list(set(libraries)),
        "interfaces": list(set(interfaces)),
        "info": info,
    }


# ═══════════════════════════════════════════════════════════
#  التحليل الدلالي المشترك — SHARED SEMANTIC PARSING
#  تحليل جميع العقود مرة واحدة ومشاركة النتائج مع كل طبقة.
#  يمنع تكرار التحليل ويُتيح الذكاء عبر الطبقات.
# ═══════════════════════════════════════════════════════════


def run_shared_parsing(engines: Dict, project: Dict) -> Dict[str, Any]:
    """
    تحليل دلالي مسبق لجميع العقود — يُحلَّل مرة واحدة ويُشارَك الناتج مع كل طبقة.

    الفوائد:
      - يمنع تكرار عملية التحليل (كانت كل طبقة تُحلِّل مستقلة)
      - يبني قائمة الدوال الآمنة (internal/private/view/pure)
        لتجاهلها في تحليلات الاستغلال (Layer 6 و Heikal)
      - يوفر function_blocks (اسم → جسم) لـ Z3 / Exploit / Heikal
      - يُنشئ فهرس _all_contracts لأي طبقة تحتاج ParsedContract مباشرة

    يُرجع:
        {
            اسم_العقد: {
                'parsed': [كائنات ParsedContract],
                'source': الكود المصدري,
                'path':   مسار الملف,
                'function_blocks': {اسم_الدالة: الكود_الكامل},
            },
            '_safe_funcs': مجموعة أسماء الدوال الآمنة (بحروف صغيرة),
            '_all_contracts': {اسم_العقد: [ParsedContract, ...]},
            '_state_vars': {اسم_العقد: {متغير: StateVar}},
        }
    """
    banner("SHARED PARSING — التحليل الدلالي المشترك")

    parser = engines.get("parser")
    if not parser:
        print(
            "  ⚠️  Solidity parser not available — layers will parse independently"
        )
        return {}

    contracts = project["contracts"]
    # Parse everything except interfaces (they have no logic to analyze)
    targets = {k: v for k, v in contracts.items() if not k.startswith("iface/")}

    shared = {}
    total_funcs = 0
    all_contracts_index = {}  # contract_name → ParsedContract
    all_state_vars = {}  # contract_name → merged state_vars
    inherited_count = 0

    for name, path in sorted(targets.items()):
        if not path.exists():
            continue
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                source = f.read()
            parsed = parser.parse(source, str(path))
            if parsed:
                nf = sum(len(c.functions) for c in parsed)
                total_funcs += nf

                # Build function_blocks: function_name → raw body (for Z3/Exploit/Heikal)
                function_blocks = {}
                for contract in parsed:
                    for fn_name, fn in contract.functions.items():
                        if fn.raw_body:
                            # Include function signature + body for downstream analysis
                            sig = f"function {fn.name}(...) {fn.visibility} {fn.mutability}"
                            function_blocks[fn_name] = fn.raw_body

                    # Index by contract name for cross-file lookup
                    all_contracts_index[contract.name] = contract
                    all_state_vars[contract.name] = contract.state_vars
                    if len(contract.state_vars) > len(contract.functions):
                        inherited_count += 1

                shared[name] = {
                    "parsed": parsed,
                    "source": source,
                    "path": path,
                    "function_blocks": function_blocks,
                }
        except Exception as e:
            print(f"  ⚠️  {path.name}: {str(e)[:120]}")

    print(f"  ✅ Pre-parsed {len(shared)} files — {total_funcs} functions extracted")

    # Build a fast lookup: which functions are safe (internal/private/view/pure)
    safe_funcs = set()
    for entry in shared.values():
        for contract in entry["parsed"]:
            for fn_name, fn in contract.functions.items():
                if fn.visibility in ("internal", "private") or fn.mutability in (
                    "view",
                    "pure",
                ):
                    safe_funcs.add(fn_name.lower())

    shared["_safe_funcs"] = safe_funcs
    shared["_all_contracts"] = all_contracts_index
    shared["_state_vars"] = all_state_vars

    print(f"  📊 Safe functions (skip for external attacks): {len(safe_funcs)}")
    print(f"  📊 Indexed contracts: {len(all_contracts_index)} — State vars tracked: {sum(len(v) for v in all_state_vars.values())}")

    return shared


# ═══════════════════════════════════════════════════════════
#  إزالة التكرارات عبر الطبقات — CROSS-LAYER DEDUPLICATION
#  توحيد النتائج من جميع الطبقات في قائمة واحدة بدون تكرار.
# ═══════════════════════════════════════════════════════════


def deduplicate_cross_layer(
    all_results: Dict,
    shared_parse: Dict,
    audit_ctx: "AuditContext" = None,
) -> Dict:
    """
    توحيد وتنقية النتائج عبر جميع الطبقات في مستوى الـ API.

    يقوم بـ:
      1. جمع كل النتائج من deep_scan و Z3 المستقل والكواشف المستقلة
      2. حذف النتائج المُكررة (نفس العنوان + نفس السطر ±5)
      3. كبت النتائج على دوال آمنة (internal/private/view/pure)
      4. حساب ملخص الخطورة المُوحَّد

    هذا يضمن أن كل ثغرة تظهر مرة واحدة فقط في التقرير النهائي،
    حتى لو اكتشفتها عدة طبقات مستقلة.

    يُرجع:
        all_results مُحدَّث بإضافة:
          - 'unified_findings': قائمة النتائج المُوحَّدة بدون تكرار
          - 'dedup_stats':      إحصائيات التنقية (كم حُذف من كل طبقة)
          - 'severity_unified': ملخص الخطورة النهائي
    """
    banner("CROSS-LAYER DEDUPLICATION — تنقية التكرارات")

    safe_funcs = set(shared_parse.get("_safe_funcs", set()))
    # Merge per-contract safe functions from AuditContext (if layers marked extras)
    if audit_ctx:
        for funcs in audit_ctx.safe_functions.values():
            safe_funcs |= {f.lower() for f in funcs}

    # Collect ALL findings from every layer into one flat list
    unified = []
    sources_seen = {}  # (title_norm, line) -> list of sources

    def normalize_title(t: str) -> str:
        import re

        t = re.sub(r"[^a-z0-9 ]", "", t.lower())
        return " ".join(t.split()[:8])

    def extract_func_from_finding(f: Dict) -> str:
        """Try to extract function name from a finding."""
        fn = f.get("function", "")
        if fn:
            return fn.lower()
        title = f.get("title", "") + " " + f.get("description", "")
        import re

        # Match func=name or name() or (CFG: name) patterns
        m = re.search(r"func[=:]\s*(\w+)", title, re.IGNORECASE)
        if m:
            return m.group(1).lower()
        m = re.search(r"\b(\w+)\s*\(", title)
        if m:
            return m.group(1).lower()
        # Match "in functionName" pattern (common in finding titles)
        m = re.search(r"\bin\s+(\w+)\b", title)
        return m.group(1).lower() if m else ""

    # --- Gather findings from deep_scan (already deduped internally) ---
    deep_findings = []
    for name, result in all_results.get("deep_scan", {}).items():
        if isinstance(result, dict) and not result.get("error"):
            for f in result.get("all_findings_unified", result.get("findings", [])):
                f = dict(f)  # copy
                f["_layer"] = "deep_scan"
                f["_contract"] = name
                deep_findings.append(f)

    # --- Gather standalone Z3 findings ---
    z3_standalone = []
    for f in all_results.get("z3_symbolic", []):
        f = dict(f)
        f["_layer"] = "z3_standalone"
        z3_standalone.append(f)

    # --- Gather standalone detector findings ---
    det_standalone = []
    for f in all_results.get("detectors", []):
        f = dict(f)
        f["_layer"] = "detectors_standalone"
        det_standalone.append(f)

    # --- Gather exploit reasoning findings (were previously ignored) ---
    exploit_standalone = []
    for name, result in all_results.get("exploit_reasoning", {}).items():
        if isinstance(result, dict) and not result.get("error"):
            for proof in result.get("exploit_proofs", []):
                if proof.get("exploitable"):
                    # Use the proof's actual confidence — don't hardcode
                    proof_conf = proof.get("confidence", 0.5)
                    # Severity from confidence: aligned with RC3 fix
                    # (exploitable threshold raised to 0.85 + >=3 attack_steps)
                    if proof_conf >= 0.85:
                        proof_sev = "CRITICAL"
                    elif proof_conf >= 0.70:
                        proof_sev = "HIGH"
                    else:
                        proof_sev = "MEDIUM"
                    exploit_standalone.append(
                        {
                            "title": f"Proven exploit: {proof.get('vulnerability_type', 'unknown')} in {proof.get('function', '?')}()",
                            "severity": proof_sev,
                            "category": proof.get(
                                "vulnerability_type", "exploit_proven"
                            ),
                            "description": proof.get(
                                "attack_steps", proof.get("description", "")
                            ),
                            "line": proof.get("line", 0),
                            "function": proof.get("function", ""),
                            "confidence": proof_conf,
                            "source": "exploit_reasoning",
                            "is_proven": True,
                            "exploitable": True,
                            "z3_proven": proof.get("z3_result") == "SAT",
                            "_layer": "exploit_reasoning",
                            "_contract": name,
                            "exploit_proof": proof,
                        }
                    )

    # --- Gather Heikal Math findings (were previously ignored) ---
    heikal_standalone = []
    heikal_data = all_results.get("heikal_math", {})
    for key, item in heikal_data.get("functions", {}).items():
        sev = item.get("severity", "INFO")
        if sev in ("CRITICAL", "HIGH", "MEDIUM"):
            tunnel_conf = item.get("tunneling", {}).get("confidence", 0)
            wave_score = item.get("wave", {}).get("heuristic_score", 0)
            contract_name = item.get("_contract", "")
            # Extract function name from "Contract::function" key
            func_name = key.split("::")[-1] if "::" in key else key
            heikal_standalone.append(
                {
                    "title": f"Heikal Math: High-risk function {func_name}() — tunnel={tunnel_conf:.4f}",
                    "severity": sev.upper(),
                    "category": "heikal_tunneling",
                    "description": item.get("description", ""),
                    "line": 0,
                    "function": func_name,
                    "confidence": max(tunnel_conf, wave_score),
                    "source": "heikal_math",
                    "heikal_enriched": True,
                    "_layer": "heikal_math",
                    "_contract": contract_name,
                }
            )
    for aname, adata in heikal_data.get("attacks", {}).items():
        sev = adata.get("severity", "LOW")
        if sev in ("CRITICAL", "HIGH", "MEDIUM"):
            tunnel_conf = adata.get("tunneling", {}).get("confidence", 0)
            heikal_standalone.append(
                {
                    "title": f"Heikal Attack Scenario: {aname}",
                    "severity": sev.upper(),
                    "category": "heikal_attack_scenario",
                    "description": adata.get("description", ""),
                    "line": 0,
                    "confidence": tunnel_conf,
                    "source": "heikal_math",
                    "heikal_enriched": True,
                    "_layer": "heikal_math",
                }
            )

    # --- Gather state extraction findings (project-level) ---
    state_standalone = []
    state_data = all_results.get("state_extraction", {})
    if isinstance(state_data, dict) and not state_data.get("error"):
        raw_state = state_data.get("raw", state_data)
        # Fund flow findings from project-level state extraction
        for issue in state_data.get("validation_issues", []):
            if isinstance(issue, dict):
                # Map validator severity (error/warning/info) to standard security severity
                _val_sev_map = {"error": "HIGH", "warning": "MEDIUM", "info": "LOW"}
                raw_sev = issue.get("severity", "MEDIUM")
                mapped_sev = _val_sev_map.get(raw_sev.lower(), raw_sev.upper())
                state_standalone.append(
                    {
                        "title": issue.get("description", str(issue))[:200],
                        "severity": mapped_sev,
                        "original_severity": mapped_sev,
                        "category": "state_consistency",
                        "description": issue.get("description", ""),
                        "line": issue.get("line", 0),
                        "confidence": issue.get("confidence", 0.5),
                        "source": "state_extraction_project",
                        "_layer": "state_extraction",
                    }
                )

    # Build signature set from deep_scan to detect duplicates
    # Function-based keys preferred (aligned with core.py RC4 fix)
    deep_func_sigs = set()  # (func_name, category_norm) for function-based matching
    deep_title_sigs = set() # (title_norm) for fallback title-only matching
    for f in deep_findings:
        title_n = normalize_title(f.get("title", ""))
        deep_title_sigs.add(title_n)
        # Function-based dedup key (primary — aligned with core.py)
        fn = extract_func_from_finding(f)
        cat_n = normalize_title(f.get("category", ""))
        if fn:
            deep_func_sigs.add((fn, cat_n))

    def _is_dup(f):
        """Check if a finding duplicates one already in deep_scan."""
        # Function-based match first (preferred — aligned with core.py RC4 fix)
        fn = extract_func_from_finding(f)
        cat_n = normalize_title(f.get("category", ""))
        if fn and (fn, cat_n) in deep_func_sigs:
            return True
        # Fallback: exact title match (no line tolerance)
        title_n = normalize_title(f.get("title", ""))
        if title_n in deep_title_sigs:
            return True
        return False

    # Filter standalone Z3: remove if already in deep_scan
    z3_kept = []
    z3_duped = 0
    for f in z3_standalone:
        if _is_dup(f):
            z3_duped += 1
        else:
            z3_kept.append(f)

    # Filter standalone detectors: remove if already in deep_scan
    det_kept = []
    det_duped = 0
    for f in det_standalone:
        if _is_dup(f):
            det_duped += 1
        else:
            det_kept.append(f)

    # Filter exploit reasoning: remove if already in deep_scan
    exploit_kept = []
    exploit_duped = 0
    for f in exploit_standalone:
        if _is_dup(f):
            exploit_duped += 1
        else:
            exploit_kept.append(f)

    # Filter heikal: remove if already in deep_scan (by function match)
    heikal_kept = []
    heikal_duped = 0
    for f in heikal_standalone:
        if _is_dup(f):
            heikal_duped += 1
        else:
            heikal_kept.append(f)

    # Merge all unique findings
    unified = (
        deep_findings
        + z3_kept
        + det_kept
        + exploit_kept
        + heikal_kept
        + state_standalone
    )

    # --- Enrich deep_scan findings with exploit/heikal flags ---
    # Build lookup: (function_lower, contract) → exploit proof data
    exploit_func_set = set()
    for ef in exploit_standalone:
        fn = ef.get("function", "").lower()
        cn = ef.get("_contract", "")
        if fn:
            exploit_func_set.add((fn, cn))

    # Build lookup: function_lower → heikal data
    heikal_func_set = set()
    for hf in heikal_standalone:
        fn = hf.get("function", "").lower()
        if fn:
            heikal_func_set.add(fn)

    for f in unified:
        fn = extract_func_from_finding(f)
        cn = f.get("_contract", "")
        # Propagate exploitable flag from exploit reasoning proofs
        if fn and (fn, cn) in exploit_func_set and "exploitable" not in f:
            f["exploitable"] = True
        # Propagate heikal_enriched flag from heikal analysis
        if fn and fn in heikal_func_set and "heikal_enriched" not in f:
            f["heikal_enriched"] = True

    # --- Suppress findings on safe functions ---
    # Only suppress LOW/INFO findings on internal/private/view/pure functions.
    # CRITICAL/HIGH/MEDIUM findings on safe functions are kept — real vulnerabilities
    # can exist in internal helpers (e.g., reentrancy in _withdraw called by public fn).
    suppressed = 0
    final = []
    for f in unified:
        fn = extract_func_from_finding(f)
        sev = str(f.get("severity", "MEDIUM")).upper()
        if fn and fn in safe_funcs and sev in ("LOW", "INFO"):
            suppressed += 1
            continue
        # Normalize internal fields → public fields for downstream consumers
        if "_layer" in f and "layer" not in f:
            f["layer"] = f["_layer"]
        if "_contract" in f and "contract" not in f:
            f["contract"] = f["_contract"]
        final.append(f)

    # --- Severity summary ---
    severity_total = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
    for f in final:
        sev = str(f.get("severity", "MEDIUM")).upper()
        if sev in severity_total:
            severity_total[sev] += 1

    stats = {
        "deep_scan_findings": len(deep_findings),
        "z3_standalone_raw": len(z3_standalone),
        "z3_standalone_kept": len(z3_kept),
        "z3_duplicates_removed": z3_duped,
        "detectors_standalone_raw": len(det_standalone),
        "detectors_standalone_kept": len(det_kept),
        "detectors_duplicates_removed": det_duped,
        "exploit_reasoning_findings": len(exploit_kept),
        "exploit_reasoning_duplicates_removed": exploit_duped,
        "heikal_findings": len(heikal_kept),
        "heikal_duplicates_removed": heikal_duped,
        "state_extraction_findings": len(state_standalone),
        "safe_function_suppressed": suppressed,
        "total_unified": len(final),
    }

    all_results["unified_findings"] = final
    all_results["dedup_stats"] = stats
    all_results["severity_unified"] = severity_total

    print(f"  Deep scan findings:            {len(deep_findings)}")
    print(
        f"  Z3 standalone: {len(z3_standalone)} raw → {len(z3_kept)} kept ({z3_duped} duplicates removed)"
    )
    print(
        f"  Detectors standalone: {len(det_standalone)} raw → {len(det_kept)} kept ({det_duped} duplicates removed)"
    )
    print(
        f"  Exploit reasoning: {len(exploit_standalone)} raw → {len(exploit_kept)} kept ({exploit_duped} duplicates removed)"
    )
    print(
        f"  Heikal math: {len(heikal_standalone)} raw → {len(heikal_kept)} kept ({heikal_duped} duplicates removed)"
    )
    print(f"  State extraction (project):    {len(state_standalone)}")
    print(f"  Safe-function suppressed:      {suppressed}")
    print(f"  ─────────────────────────────────")
    print(f"  TOTAL UNIFIED FINDINGS:        {len(final)}")
    for s in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        if severity_total.get(s, 0):
            print(f"    {s}: {severity_total[s]}")

    return all_results


# ═══════════════════════════════════════════════════════════
#  الطبقات 0-5: الفحص العميق — CORE DEEP SCAN
#  يُشغِّل AGLSecurityAudit.deep_scan() على العقود الرئيسية.
#  يشمل: تسطيح → Z3 → أنماط → منسق → كواشف → إزالة تكرار داخلي
# ═══════════════════════════════════════════════════════════


def run_core_deep_scan(engines: Dict, project: Dict, shared_parse: Dict = None) -> Dict:
    """
    تشغيل الفحص العميق على العقود الرئيسية (بحد 20 عقد).

    يُشغِّل AGLSecurityAudit.deep_scan() الذي يمرر العقد عبر:
      - Layer 0: Solidity Flattener (تسطيح الاستيرادات)
      - Layer 0.5: Z3 Symbolic Execution (إثبات رياضي)
      - أنماط الثغرات المعروفة (pattern matching)
      - المُنسِّق الأمني (security orchestrator)
      - 22 كاشف دلالي
      - إزالة التكرار الداخلي

    يمرر البيانات المُحلَّلة مسبقاً (shared_parse) لـ core لتجنب التحليل المكرر.

    يُرجع:
        {اسم_العقد: نتيجة_الفحص, ...} — كل نتيجة تحوي findings و severity_summary
    """
    banner("LAYER 0-5: DEEP SCAN (Flattener + Z3 + Patterns + Detectors)")

    core = engines.get("core")
    if not core:
        print("  ❌ AGLSecurityAudit not available — skipping")
        return {}

    shared_parse = shared_parse or {}
    contracts = project["contracts"]
    # Deep scan main contracts (not interfaces)
    targets = project["main_contracts"]
    if not targets:
        targets = [k for k in contracts if not k.startswith("iface/")]

    results = {}
    for name in targets[:20]:  # Limit to 20 for performance
        path = contracts.get(name)
        if not path or not path.exists():
            continue

        print(f"\n  🔍 Deep scanning: {path.name} ...")
        t0 = time.time()
        try:
            # Pass pre-parsed contracts to avoid duplicate SoliditySemanticParser call
            entry = shared_parse.get(name, {})
            pre_parsed = entry.get("parsed", None)
            # Use thread-based timeout to prevent infinite hangs (e.g. Mythril on complex contracts)
            from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
            _mythril_t = 90  # default; core also reads from its config
            _outer_timeout = _mythril_t + 180  # orchestrator wait + remaining layers overhead
            with ThreadPoolExecutor(max_workers=1) as _executor:
                _future = _executor.submit(core.deep_scan, str(path), pre_parsed=pre_parsed)
                result = _future.result(timeout=_outer_timeout)
            elapsed = time.time() - t0
            result["_scan_time"] = round(elapsed, 2)
            results[name] = result

            findings = result.get("all_findings_unified", result.get("findings", []))
            sev = result.get("severity_summary", {})
            sym = len(result.get("symbolic_findings", []))
            det = len(result.get("detector_findings", []))
            layers = result.get("layers_used", [])

            print(f"     ✅ {name}: {len(findings)} findings in {elapsed:.1f}s")
            print(
                f"        Severity: C={sev.get('CRITICAL',0)} H={sev.get('HIGH',0)} "
                f"M={sev.get('MEDIUM',0)} L={sev.get('LOW',0)}"
            )
            print(f"        Z3 symbolic: {sym} | Detectors: {det} | Layers: {layers}")
        except FuturesTimeout:
            elapsed = time.time() - t0
            # Try to salvage partial results from core's incremental progress
            partial = getattr(core, "_last_partial_result", None)
            if partial and isinstance(partial, dict) and partial.get("layers_used"):
                partial["_scan_time"] = round(elapsed, 2)
                partial["_timeout_warning"] = f"Partial result: timeout after {elapsed:.0f}s"
                results[name] = partial
                findings = partial.get("all_findings_unified", partial.get("findings", []))
                layers = partial.get("layers_used", [])
                print(f"     ⚠️  {name}: TIMEOUT after {elapsed:.0f}s — salvaged {len(findings)} findings from layers: {layers}")
            else:
                print(f"     ⏰ {name}: TIMEOUT after {elapsed:.0f}s — no partial results available")
                results[name] = {"error": f"timeout after {elapsed:.0f}s", "_scan_time": round(elapsed, 2)}
        except Exception as e:
            print(f"     ❌ {name}: {str(e)[:200]}")
            results[name] = {"error": str(e)[:300]}

    return results


# ═══════════════════════════════════════════════════════════
#  الطبقة 0.5: محرك Z3 الرمزي — Z3 SYMBOLIC ENGINE
#  يعمل على المكتبات فقط (العقود الرئيسية مُغطاة في deep_scan)
# ═══════════════════════════════════════════════════════════


def run_z3_symbolic(
    engines: Dict, project: Dict, shared_parse: Dict = None
) -> List[Dict]:
    """
    تشغيل Z3 Symbolic Execution على المكتبات فقط.

    العقود الرئيسية مُغطاة بالفعل في deep_scan (Layer 0.5 يعمل
    داخل AGLSecurityAudit). لذلك هذه الدالة تفحص المكتبات
    التي لا يشملها deep_scan.

    يُعيد استخدام الكود المُحلَّل مسبقاً من shared_parse
    لتجنب إعادة القراءة من القرص.

    Z3 Symbolic Engine يُنتج إثباتات رياضية حقيقية
    باستخدام BitVec(256) مع counterexamples.

    يُرجع:
        قائمة من النتائج — كل نتيجة تحوي is_proven و counterexample
    """
    banner("LAYER 0.5: Z3 SYMBOLIC EXECUTION — LIBRARIES (Mathematical Proofs)")

    z3_engine = engines.get("z3")
    if not z3_engine:
        print("  ❌ Z3 Symbolic Engine not available — skipping")
        return []

    shared_parse = shared_parse or {}
    contracts = project["contracts"]

    # Only scan libraries — main contracts are already Z3-scanned inside deep_scan
    targets = project["libraries"]
    if not targets:
        print("  ℹ️  No library files to scan — main contracts covered by deep_scan")
        return []

    all_z3_findings = []
    for name in targets[:30]:  # Limit
        path = contracts.get(name)
        if not path or not path.exists():
            continue

        print(f"  🧮 Z3 analyzing library: {path.name} ...")
        try:
            # Reuse pre-parsed source if available
            entry = shared_parse.get(name, {})
            source = entry.get("source", "")
            if not source:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    source = f.read()

            findings = z3_engine.analyze(source, str(path))
            for f_item in findings:
                f_dict = (
                    f_item.__dict__
                    if hasattr(f_item, "__dict__")
                    else {"text": str(f_item)}
                )
                f_dict["_source_file"] = path.name
                all_z3_findings.append(f_dict)

            proven = sum(1 for f in findings if getattr(f, "is_proven", False))
            print(f"     ✅ {path.name}: {len(findings)} findings ({proven} proven)")
        except Exception as e:
            print(f"     ⚠️  {path.name}: {str(e)[:150]}")

    print(f"\n  📊 Total Z3 library findings: {len(all_z3_findings)}")
    return all_z3_findings


# ═══════════════════════════════════════════════════════════
#  الطبقات 1-4: استخراج الحالة — STATE EXTRACTION
#  تحليل الحالة المالية + فضاء الأفعال + محاكاة الهجوم + البحث
# ═══════════════════════════════════════════════════════════


def run_state_extraction(engines: Dict, project: Dict, shared_parse: Dict = None) -> Dict:
    """
    تشغيل محرك استخراج الحالة على المشروع.

    يقوم بـ:
      - بناء مُخطط التدفقات المالية (fund flow graph)
      - تحديد الكيانات والعلاقات بين العقود
      - حساب فضاء الأفعال (action space) — كل الخطوات الممكنة
      - محاكاة سيناريوهات الهجوم (مع حساب الربح)
      - البحث عن مسارات الاستغلال (search engine)

    ملاحظة: shared_parse مقبول للتوافق لكنه غير مُستخدَم حالياً
    لأن StateExtractionEngine.extract_project() يقبل مسار مجلد فقط.

    يُرجع:
        قاموس يحوي نتائج الاستخراج أو {'error': رسالة} إذا فشل
    """
    banner("LAYER 1-4: STATE EXTRACTION + ATTACK SIMULATION + SEARCH")

    state_engine = engines.get("state")
    if not state_engine:
        print("  ❌ State Extraction Engine not available — skipping")
        return {}

    contracts_dir = project["contracts_dir"]
    print(f"  📊 Extracting financial state from: {contracts_dir}")
    t0 = time.time()
    try:
        result = state_engine.extract_project(contracts_dir)
        elapsed = time.time() - t0

        result_dict = (
            result.to_dict() if hasattr(result, "to_dict") else {"raw": str(result)}
        )

        print(f"  ✅ Extraction complete in {elapsed:.1f}s")
        print(f"     Contracts parsed: {result.contracts_parsed}")
        print(f"     Entities found:   {result.entities_found}")
        print(f"     Relationships:    {result.relationships_found}")
        print(f"     Fund flows:       {result.fund_flows_found}")
        print(f"     Validation issues:{result.validation_issues}")

        graph = result.graph
        if graph and hasattr(graph, "action_space") and graph.action_space:
            as_data = graph.action_space
            total_actions = getattr(as_data, "total_actions", "?")
            sequences = getattr(as_data, "attack_sequences", [])
            print(
                f"     Action Space:     {total_actions} actions, {len(sequences)} attack sequences"
            )

        if graph and hasattr(graph, "attack_simulation") and graph.attack_simulation:
            sim = graph.attack_simulation
            print(
                f"     Attack Simulation: {sim.total_sequences_tested} tested, "
                f"{sim.profitable_attacks} profitable"
            )
            if sim.best_attack:
                ba = sim.best_attack
                print(
                    f"     🎯 Best Attack: {ba.attack_type} — profit ${ba.net_profit_usd:.2f}"
                )

        if graph and hasattr(graph, "search_results") and graph.search_results:
            sr = graph.search_results
            candidates = getattr(sr, "candidates", [])
            print(f"     Search Results:   {len(candidates)} candidates found")

        return result_dict
    except Exception as e:
        print(f"  ❌ State extraction failed: {str(e)[:300]}")
        return {"error": str(e)[:300]}


# ═══════════════════════════════════════════════════════════
#  الطبقة 5: 22 كاشف دلالي — SEMANTIC DETECTORS
#  يعمل على المكتبات فقط (العقود الرئيسية مُغطاة في deep_scan)
# ═══════════════════════════════════════════════════════════


def run_detectors(
    engines: Dict, project: Dict, shared_parse: Dict = None,
    audit_ctx: "AuditContext" = None,
) -> List[Dict]:
    """
    تشغيل 22 كاشف دلالي على عقود المكتبات فقط.

    العقود الرئيسية مُغطاة بالفعل في deep_scan.
    يُعيد استخدام البيانات المُحلَّلة مسبقاً من shared_parse
    لتجنب إعادة التحليل.

    الكواشف تشمل: reentrancy, access_control, arithmetic,
    oracle, flash_loan, delegatecall, selfdestruct, إلخ.

    يُرجع:
        قائمة نتائج — كل نتيجة تحوي severity و category
    """
    banner("LAYER 5: 22 SEMANTIC DETECTORS — LIBRARIES")

    runner = engines.get("detectors")
    parser = engines.get("parser")
    if not runner:
        print("  ❌ Detectors not available — skipping")
        return []

    shared_parse = shared_parse or {}
    contracts = project["contracts"]

    # Only scan libraries — main contracts already covered by deep_scan
    target_keys = project["libraries"]
    if not target_keys:
        print("  ℹ️  No library files to scan — main contracts covered by deep_scan")
        return []

    all_findings = []
    for name in sorted(target_keys):
        path = contracts.get(name)
        if not path or not path.exists():
            continue
        try:
            # Reuse pre-parsed data
            entry = shared_parse.get(name, {})
            parsed = entry.get("parsed", None)
            if not parsed and parser:
                source = entry.get("source", "")
                if not source:
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        source = f.read()
                parsed = parser.parse(source, str(path))

            if not parsed:
                continue

            print(f"  📝 {path.name}: {len(parsed)} contracts parsed")
            findings = runner.run(parsed)
            # Determine safe functions for early suppression
            _safe = getattr(audit_ctx, "_global_safe_funcs", set()) if audit_ctx else set()
            for finding in findings:
                f_dict = (
                    finding.__dict__
                    if hasattr(finding, "__dict__")
                    else {"text": str(finding)}
                )
                # Early suppression: skip findings on safe functions
                fn = f_dict.get("function", "").lower()
                if fn and _safe and fn in _safe:
                    continue
                f_dict["_source_file"] = path.name
                f_dict["_contract_key"] = name
                all_findings.append(f_dict)

            if findings:
                print(f"  🔍 {path.name}: {len(findings)} findings")
        except Exception as e:
            print(f"  ⚠️  {path.name}: {str(e)[:120]}")

    # Summary by severity
    sev_count = {}
    for f in all_findings:
        s = str(f.get("severity", "unknown"))
        if hasattr(f.get("severity"), "value"):
            s = f["severity"].value
        sev_count[s] = sev_count.get(s, 0) + 1

    print(f"\n  📊 Total detector library findings: {len(all_findings)}")
    for s, c in sorted(sev_count.items()):
        print(f"     {s.upper()}: {c}")

    return all_findings


# ═══════════════════════════════════════════════════════════
#  الطبقة 6: تحليل الاستغلال — EXPLOIT REASONING
#  يُثبت قابلية الاستغلال باستخدام Z3 SAT solver
# ═══════════════════════════════════════════════════════════


def run_exploit_reasoning(
    engines: Dict, project: Dict, deep_scan_results: Dict = None,
    shared_parse: Dict = None, audit_ctx: "AuditContext" = None,
) -> Dict:
    """
    تشغيل تحليل الاستغلال (Exploit Reasoning).

    العقود الرئيسية التي مرت عبر deep_scan لديها بالفعل نتائج
    exploit reasoning (Layer 5 في core.py). لذلك هذه الدالة:
      1. تستخرج exploit_proofs الموجودة من deep_scan
      2. تُشغِّل exploit reasoning فقط على المكتبات التي لم يفحصها deep_scan

    هذا يمنع التحليل المُكرَّر ويتجنب مشكلة أن deep_scan's
    all_findings_unified قد أُعيد تقييمها بواسطة RiskCore.

    يُرجع:
        {اسم_العقد: نتيجة_التحليل} — يحوي exploitable_count و exploit_proofs
    """
    banner("LAYER 6: EXPLOIT REASONING (Z3 Proof of Exploitability)")

    exploit = engines.get("exploit")
    deep_scan_results = deep_scan_results or {}

    all_exploits = {}

    # === Phase 1: Extract exploit_proofs already computed by deep_scan ===
    # core.py runs exploit reasoning PRE-RiskCore on raw findings (correct order).
    # We reuse those results instead of re-running on post-RiskCore findings.
    deep_scanned_contracts = set()
    extracted_count = 0
    for name, ds in deep_scan_results.items():
        if not isinstance(ds, dict) or ds.get("error"):
            continue
        er = ds.get("exploit_reasoning")
        if er and isinstance(er, dict):
            all_exploits[name] = er
            deep_scanned_contracts.add(name)
            proofs = er.get("exploit_proofs", [])
            exploitable = sum(1 for p in proofs if p.get("exploitable"))
            extracted_count += len(proofs)
            if proofs:
                print(f"  ♻️  {name}: {exploitable} exploit proofs extracted from deep_scan")

    if extracted_count:
        print(f"  📋 Extracted {extracted_count} exploit proofs from deep_scan (no re-computation)")
    else:
        print(f"  ℹ️  No exploit proofs found in deep_scan results")

    # === Phase 2: Run exploit reasoning on contracts NOT in deep_scan ===
    # Libraries and other contracts that deep_scan didn't cover
    if not exploit:
        print("  ❌ Exploit Reasoning Engine not available — skipping standalone analysis")
        return all_exploits

    contracts = project["contracts"]
    # Analyze contracts not already covered by deep_scan
    all_targets = list(project["main_contracts"][:10]) + list(project.get("libraries", [])[:10])
    uncovered = [t for t in all_targets if t not in deep_scanned_contracts]

    if not uncovered:
        print(f"  ✅ All target contracts already analyzed by deep_scan — no additional work needed")
        return all_exploits

    print(f"\n  🔍 Running exploit reasoning on {len(uncovered)} uncovered contracts...")

    for name in uncovered:
        path = contracts.get(name)
        if not path or not path.exists():
            continue

        print(f"  🎯 Exploitation analysis: {path.name} ...")
        try:
            # Reuse pre-parsed source if available
            sp = shared_parse or {}
            entry = sp.get(name, {})
            source = entry.get("source", "")
            if not source:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    source = f.read()

            ds = deep_scan_results.get(name, {})
            findings_for_exploit = ds.get(
                "all_findings_unified", ds.get("findings", [])
            )

            # Feed Z3 proven symbolic findings into exploit reasoning
            # Prefer centralized z3_proven from AuditContext if available
            if audit_ctx:
                z3_proven = audit_ctx.get_z3_proven_for(name)
            else:
                symbolic = ds.get("symbolic_findings", [])
                z3_proven = [
                    sf
                    for sf in symbolic
                    if sf.get("is_proven") or sf.get("z3_result") == "SAT"
                ]
            if z3_proven:
                existing_sigs = {
                    (f.get("title", ""), f.get("line", 0)) for f in findings_for_exploit
                }
                for sf in z3_proven:
                    sig = (sf.get("title", ""), sf.get("line", 0))
                    if sig not in existing_sigs:
                        if "original_severity" not in sf:
                            sf["original_severity"] = sf.get("severity", "high")
                        findings_for_exploit.append(sf)
                        existing_sigs.add(sig)
                print(
                    f"     📐 +{len(z3_proven)} Z3-proven findings fed to exploit reasoning"
                )

            result = exploit.analyze(
                findings=findings_for_exploit,
                source_code=source,
                file_path=str(path),
            )
            if hasattr(result, "__dict__"):
                result = result.__dict__

            all_exploits[name] = result

            if isinstance(result, dict):
                exploitable = result.get("exploitable_count", 0)
                total = result.get("total_analyzed", 0)
                proofs = result.get("exploit_proofs", [])
                print(
                    f"     ✅ {name}: {exploitable} exploitable out of {total} analyzed, "
                    f"{len(proofs)} proofs"
                )
            else:
                print(f"     ✅ {name}: analysis complete")
        except Exception as e:
            print(f"     ⚠️  {name}: {str(e)[:200]}")
            all_exploits[name] = {"error": str(e)[:200]}

    return all_exploits


# ═══════════════════════════════════════════════════════════
#  الطبقة 7: خوارزميات هيكل الرياضية — HEIKAL MATH
#  تحليل ديناميكي للكود المصدري باستخدام 4 خوارزميات:
#  النفق الكمومي | الموجات | الأنماط الهولوغرافية | الرنين
# ═══════════════════════════════════════════════════════════


# --- أدوات تحليل الكود المصدري ---

_RE_FUNCTION = re.compile(
    r"function\s+(\w+)\s*\(([^)]*)\)[^{]*\{",
    re.DOTALL,
)
_RE_REQUIRE = re.compile(r"require\s*\(")
_RE_MODIFIER_DEF = re.compile(r"modifier\s+(\w+)")
_RE_MODIFIER_USE = re.compile(r"\)\s+([\w\s]+)\s*(?:returns|{)")
_RE_EMIT = re.compile(r"emit\s+\w+")
_RE_EXTERNAL_CALL = re.compile(r"\.\w+\s*\(|\.call\s*[({]|\.transfer\s*\(|\.send\s*\(")
_RE_STATE_WRITE = re.compile(r"\b\w+\s*(?:\[\w+\])?\s*=[^=]")
_RE_STATE_READ = re.compile(
    r"\b(?:mapping|uint|int|address|bool|bytes)\w*\s+\w+\s*=\s*\w+"
)
_RE_DELEGATECALL = re.compile(r"\.delegatecall\s*\(")
_RE_SELFDESTRUCT = re.compile(r"selfdestruct\s*\(")
_RE_SEND_ETH = re.compile(r"\.call\s*\{.*value.*\}|\.transfer\s*\(|\.send\s*\(")
_RE_ACCESS_CHECK = re.compile(
    r"require\s*\(\s*msg\.sender\s*==|onlyOwner|onlyRole|onlyAdmin|_checkOwner"
)


def extract_function_blocks(source: str) -> Dict[str, str]:
    """
    استخراج كتل الدوال من كود Solidity.

    يستخدم regex لتحديد كل دالة، ثم يتبع الأقواس المعقوفة
    لالتقاط الجسم الكامل بما فيه الدوال المتداخلة.

    يُرجع:
        {اسم_الدالة: كود_الدالة_الكامل} — من توقيع الدالة حتى القوس الأخير
    """
    functions = {}
    for match in _RE_FUNCTION.finditer(source):
        fname = match.group(1)
        start = match.end() - 1  # opening brace
        depth = 0
        end = start
        for i in range(start, len(source)):
            if source[i] == "{":
                depth += 1
            elif source[i] == "}":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        functions[fname] = source[match.start() : end]
    return functions


def analyze_function_security(
    fname: str, func_body: str, full_source: str
) -> Dict[str, Any]:
    """
    بناء نموذج أمني هيكل ديناميكي من الكود المصدري الفعلي.

    يحلل الدالة لاستخراج:
      - الحواجز الأمنية (require, modifiers, access control)
      - خصائص الموجة (تحريك أموال، انتهاك CEI، oracle)
      - خصائص هولوغرافية (تعقيد، نسب الحماية، سطح الهجوم)
      - طاقة الهجوم المُقدَّرة (أعلى = أخطر)
      - طول سلسلة الاستدعاءات الخارجية

    يُرجع:
        {
            "barriers": [SecurityBarrier, ...],
            "wave_features": {خصائص الموجة},
            "holo_features": {خصائص هولوغرافية},
            "energy": float,           # 0.0-1.0 طاقة الهجوم
            "chain_length": int,        # عدد الاستدعاءات
            "description": str,         # وصف مختصر
        }
    """
    from agl_security_tool.heikal_math.tunneling_scorer import SecurityBarrier

    barriers = []
    wave_features = {}
    holo_features = {}

    # --- Count security features ---
    require_count = len(_RE_REQUIRE.findall(func_body))
    external_calls = len(_RE_EXTERNAL_CALL.findall(func_body))
    emit_count = len(_RE_EMIT.findall(func_body))
    delegatecall = bool(_RE_DELEGATECALL.search(func_body))
    selfdestruct = bool(_RE_SELFDESTRUCT.search(func_body))
    sends_eth = bool(_RE_SEND_ETH.search(func_body))
    has_access_control = bool(_RE_ACCESS_CHECK.search(func_body))
    state_writes = len(_RE_STATE_WRITE.findall(func_body))
    param_count = (
        func_body.split("(")[1].split(")")[0].count(",") + 1 if "(" in func_body else 0
    )

    # Check for modifiers
    modifier_names = set(_RE_MODIFIER_DEF.findall(full_source))
    used_modifiers = _RE_MODIFIER_USE.findall(func_body[:200]) if func_body else []
    has_modifier = False
    for um in used_modifiers:
        tokens = um.strip().split()
        for t in tokens:
            if t in modifier_names or t in {
                "nonReentrant",
                "lock",
                "onlyOwner",
                "whenNotPaused",
            }:
                has_modifier = True
                break

    # Check for reentrancy guard patterns
    reentrancy_guarded = (
        "nonReentrant" in func_body
        or "unlocked" in func_body
        or "_status" in func_body
        or "ReentrancyGuard" in full_source
    )

    # Check for CEI pattern violation (external call before state write)
    # Simple heuristic: if there's .call() or .transfer() NOT at the end
    moves_funds = bool(
        _RE_SEND_ETH.search(func_body)
        or ".transfer(" in func_body
        or "IERC20" in func_body
        or "safeTransfer" in func_body
    )

    # CEI violation: external call followed by state write
    ext_pos = [m.start() for m in _RE_EXTERNAL_CALL.finditer(func_body)]
    write_pos = [m.start() for m in _RE_STATE_WRITE.finditer(func_body)]
    cei_violation = False
    if ext_pos and write_pos:
        for ep in ext_pos:
            for wp in write_pos:
                if wp > ep:
                    cei_violation = True
                    break

    reads_oracle = any(
        w in func_body
        for w in [
            "oracle",
            "Oracle",
            "observe",
            "TWAP",
            "twap",
            "getPrice",
            "latestAnswer",
            "latestRoundData",
        ]
    )

    has_state_conflict = state_writes > 3 and external_calls > 0

    # --- Build SecurityBarriers ---
    if reentrancy_guarded:
        barriers.append(
            SecurityBarrier(
                barrier_type="modifier",
                height=0.95,
                thickness=2.0,
                source=f"reentrancy guard in {fname}",
            )
        )

    if has_access_control:
        barriers.append(
            SecurityBarrier(
                barrier_type="access_control",
                height=0.85,
                thickness=1.0,
                source=f"access control in {fname}",
            )
        )

    for i in range(min(require_count, 5)):
        barriers.append(
            SecurityBarrier(
                barrier_type="require",
                height=max(0.90 - i * 0.05, 0.60),
                thickness=1.0 + (0.5 if i == 0 else 0),
                source=f"require #{i+1} in {fname}",
            )
        )

    if has_modifier and not reentrancy_guarded:
        barriers.append(
            SecurityBarrier(
                barrier_type="modifier",
                height=0.80,
                thickness=1.0,
                source=f"modifier on {fname}",
            )
        )

    if emit_count > 0:
        barriers.append(
            SecurityBarrier(
                barrier_type="guard",
                height=0.50,
                thickness=0.5,
                source=f"{emit_count} events in {fname}",
            )
        )

    # If no barriers at all, add a default weak one
    if not barriers:
        barriers.append(
            SecurityBarrier(
                barrier_type="guard",
                height=0.40,
                thickness=0.5,
                bypassable=True,
                source=f"no explicit guards in {fname}",
            )
        )

    # --- Wave features ---
    wave_features = {
        "moves_funds": moves_funds,
        "cei_violation": cei_violation,
        "sends_eth": sends_eth,
        "no_access_control": not has_access_control,
        "not_guarded": not reentrancy_guarded and not has_modifier,
        "reads_oracle": reads_oracle,
        "has_state_conflict": has_state_conflict,
        "modifies_balances": moves_funds or state_writes > 2,
    }

    # --- Holographic features ---
    body_len = len(func_body)
    complexity = min(1.0, body_len / 3000)

    holo_features = {
        "has_cei_violation": cei_violation,
        "sends_eth": sends_eth,
        "reentrancy_guarded": reentrancy_guarded,
        "requires_access": has_access_control,
        "moves_funds": moves_funds,
        "reads_oracle": reads_oracle,
        "has_delegatecall": delegatecall,
        "has_state_conflict": has_state_conflict,
        "external_call_count": external_calls,
        "state_write_count": state_writes,
        "state_read_count": max(state_writes, 1),
        "precondition_count": require_count,
        "parameter_count": param_count,
        "fund_flow_ratio": 0.9 if moves_funds else 0.1,
        "complexity_ratio": complexity,
        "attack_surface_ratio": min(
            1.0, external_calls * 0.3 + (0.2 if not has_access_control else 0)
        ),
        "protection_ratio": min(
            1.0, require_count * 0.15 + (0.3 if reentrancy_guarded else 0)
        ),
    }

    # --- Energy estimate ---
    # Higher energy = more dangerous
    energy = 0.3
    if moves_funds:
        energy += 0.2
    if external_calls > 0:
        energy += 0.1 * min(external_calls, 3)
    if not has_access_control:
        energy += 0.1
    if cei_violation:
        energy += 0.15
    if reads_oracle:
        energy += 0.1
    if sends_eth:
        energy += 0.1
    energy = min(1.0, energy)

    # Chain length estimate
    chain_length = max(1, external_calls + (1 if moves_funds else 0))

    # Description
    features_list = []
    if reentrancy_guarded:
        features_list.append("reentrancy_guard")
    if has_access_control:
        features_list.append("access_control")
    if moves_funds:
        features_list.append("moves_funds")
    if reads_oracle:
        features_list.append("oracle")
    desc = f"{fname}() — {require_count} requires, {external_calls} ext calls"
    if features_list:
        desc += f" [{', '.join(features_list)}]"

    return {
        "barriers": barriers,
        "wave_features": wave_features,
        "holo_features": holo_features,
        "energy": energy,
        "chain_length": chain_length,
        "description": desc,
    }


def build_attack_scenarios(
    functions_analysis: Dict[str, Dict], source_map: Dict[str, str]
) -> Dict[str, Dict]:
    """
    بناء سيناريوهات هجوم ديناميكية بناءً على الدوال المُكتشفة.

    يحلل التفاعلات بين الدوال ويُنشئ حتى 7 سيناريوهات:
      1. Reentrancy Attack — إعادة الدخول عبر callbacks
      2. Flash Loan Attack — قرض فوري → تلاعب → ربح
      3. Oracle Manipulation — تلاعب بمُعطيات الأسعار
      4. Sandwich / Front-Running — اعتراض المعاملات
      5. Governance Takeover — اختراق الصلاحيات الإدارية
      6. JIT Liquidity Sniping — سيولة ضيقة النطاق
      7. Unguarded Fund Flow — دوال غير محمية تتعامل مع أموال

    كل سيناريو يحوي: barriers, wave_features, holo_features, energy
    جاهز للتشغيل عبر خوارزميات هيكل الأربع.
    """
    from agl_security_tool.heikal_math.tunneling_scorer import SecurityBarrier

    scenarios = {}

    # Collect function features
    has_flash = any("flash" in fn.lower() for fn in functions_analysis)
    has_swap = any("swap" in fn.lower() for fn in functions_analysis)
    has_mint = any("mint" in fn.lower() for fn in functions_analysis)
    has_burn = any(
        "burn" in fn.lower() or "redeem" in fn.lower() for fn in functions_analysis
    )
    has_oracle = any(
        fa.get("wave_features", {}).get("reads_oracle", False)
        for fa in functions_analysis.values()
    )
    has_governance = any(
        fa.get("wave_features", {}).get("no_access_control", True) is False
        for fa in functions_analysis.values()
    )
    has_reentrancy_guard = any(
        fa.get("holo_features", {}).get("reentrancy_guarded", False)
        for fa in functions_analysis.values()
    )
    fund_movers = [
        fn
        for fn, fa in functions_analysis.items()
        if fa.get("wave_features", {}).get("moves_funds", False)
    ]
    unguarded = [
        fn
        for fn, fa in functions_analysis.items()
        if fa.get("wave_features", {}).get("not_guarded", False)
    ]

    # --- Scenario 1: Reentrancy Attack ---
    if fund_movers:
        barriers = []
        if has_reentrancy_guard:
            barriers.append(
                SecurityBarrier(
                    barrier_type="modifier",
                    height=0.99,
                    thickness=3.0,
                    source="reentrancy guard detected",
                )
            )
            barriers.append(
                SecurityBarrier(
                    barrier_type="invariant",
                    height=0.95,
                    thickness=2.0,
                    source="shared lock mechanism",
                )
            )
        else:
            barriers.append(
                SecurityBarrier(
                    barrier_type="guard",
                    height=0.50,
                    thickness=0.5,
                    bypassable=True,
                    source="no reentrancy guard",
                )
            )

        scenarios["Reentrancy_Attack"] = {
            "description": f"Re-enter via callback into {', '.join(fund_movers[:3])}",
            "barriers": barriers,
            "wave_features": {
                "moves_funds": True,
                "cei_violation": True,
                "sends_eth": True,
                "no_access_control": True,
                "not_guarded": not has_reentrancy_guard,
                "reads_oracle": False,
                "has_state_conflict": True,
                "modifies_balances": True,
            },
            "holo_features": {
                "has_cei_violation": True,
                "sends_eth": True,
                "reentrancy_guarded": has_reentrancy_guard,
                "moves_funds": True,
                "has_state_conflict": True,
                "external_call_count": 3,
                "reentrancy_calls": 1,
                "protection_ratio": 0.95 if has_reentrancy_guard else 0.1,
                "complexity_ratio": 0.7,
            },
            "energy": 0.95 if not has_reentrancy_guard else 0.60,
            "chain_length": 3,
        }

    # --- Scenario 2: Flash Loan Attack ---
    if has_flash or has_swap:
        scenarios["Flash_Loan_Attack"] = {
            "description": "Flash loan → manipulate state → extract profit",
            "barriers": [
                SecurityBarrier(
                    barrier_type="guard",
                    height=0.80,
                    thickness=1.5,
                    source="flash fee enforcement",
                ),
                SecurityBarrier(
                    barrier_type="invariant",
                    height=0.75,
                    thickness=1.0,
                    source="balance check after callback",
                ),
                SecurityBarrier(
                    barrier_type="guard",
                    height=0.65,
                    thickness=0.5,
                    bypassable=True,
                    source="single-block impact limit",
                ),
            ],
            "wave_features": {
                "moves_funds": True,
                "cei_violation": False,
                "sends_eth": False,
                "no_access_control": True,
                "not_guarded": False,
                "reads_oracle": has_oracle,
                "has_state_conflict": True,
                "modifies_balances": True,
            },
            "holo_features": {
                "has_cei_violation": False,
                "moves_funds": True,
                "reads_oracle": has_oracle,
                "has_state_conflict": True,
                "external_call_count": 4,
                "fund_flow_ratio": 0.95,
                "attack_surface_ratio": 0.8,
                "complexity_ratio": 0.8,
            },
            "energy": 0.90,
            "chain_length": 4,
        }

    # --- Scenario 3: Oracle Manipulation ---
    if has_oracle:
        scenarios["Oracle_Manipulation"] = {
            "description": "Manipulate price oracle to exploit dependent functions",
            "barriers": [
                SecurityBarrier(
                    barrier_type="guard",
                    height=0.85,
                    thickness=1.5,
                    source="TWAP / time-weighted average",
                ),
                SecurityBarrier(
                    barrier_type="guard",
                    height=0.75,
                    thickness=1.0,
                    source="multi-block averaging",
                ),
                SecurityBarrier(
                    barrier_type="invariant",
                    height=0.60,
                    thickness=0.5,
                    bypassable=True,
                    source="oracle update lag",
                ),
            ],
            "wave_features": {
                "moves_funds": True,
                "cei_violation": False,
                "sends_eth": False,
                "no_access_control": True,
                "not_guarded": False,
                "reads_oracle": True,
                "has_state_conflict": True,
                "modifies_balances": True,
            },
            "holo_features": {
                "reads_oracle": True,
                "moves_funds": True,
                "has_state_conflict": True,
                "oracle_dependency_ratio": 1.0,
                "external_call_count": 3,
                "attack_surface_ratio": 0.7,
                "complexity_ratio": 0.75,
            },
            "energy": 0.85,
            "chain_length": 5,
        }

    # --- Scenario 4: Sandwich / Front-Running ---
    if has_swap or has_mint:
        scenarios["Sandwich_Frontrun"] = {
            "description": "Front-run → victim tx → back-run for profit extraction",
            "barriers": [
                SecurityBarrier(
                    barrier_type="guard",
                    height=0.70,
                    thickness=1.0,
                    source="slippage protection",
                ),
                SecurityBarrier(
                    barrier_type="guard",
                    height=0.60,
                    thickness=0.5,
                    bypassable=True,
                    source="mempool is public",
                ),
                SecurityBarrier(
                    barrier_type="invariant",
                    height=0.55,
                    thickness=0.5,
                    bypassable=True,
                    source="fee overhead",
                ),
            ],
            "wave_features": {
                "moves_funds": True,
                "cei_violation": False,
                "sends_eth": False,
                "no_access_control": True,
                "not_guarded": True,
                "reads_oracle": has_oracle,
                "has_state_conflict": True,
                "modifies_balances": True,
            },
            "holo_features": {
                "moves_funds": True,
                "reads_oracle": has_oracle,
                "has_state_conflict": True,
                "external_call_count": 3,
                "fund_flow_ratio": 0.85,
                "attack_surface_ratio": 0.7,
            },
            "energy": 0.90,
            "chain_length": 3,
        }

    # --- Scenario 5: Governance Takeover ---
    if has_governance:
        scenarios["Governance_Takeover"] = {
            "description": "Compromise admin/owner → extract value or change rules",
            "barriers": [
                SecurityBarrier(
                    barrier_type="access_control",
                    height=0.80,
                    thickness=1.0,
                    source="owner/admin check",
                ),
                SecurityBarrier(
                    barrier_type="guard",
                    height=0.70,
                    thickness=0.5,
                    bypassable=True,
                    source="no timelock detected",
                ),
            ],
            "wave_features": {
                "moves_funds": False,
                "cei_violation": False,
                "sends_eth": False,
                "no_access_control": False,
                "not_guarded": True,
                "reads_oracle": False,
                "has_state_conflict": False,
                "modifies_balances": False,
            },
            "holo_features": {
                "requires_access": True,
                "external_call_count": 0,
                "state_write_count": 1,
                "complexity_ratio": 0.2,
            },
            "energy": 0.60,
            "chain_length": 2,
        }

    # --- Scenario 6: JIT Liquidity (if has mint+burn+swap) ---
    if has_mint and has_burn and has_swap:
        scenarios["JIT_Liquidity_Sniping"] = {
            "description": "Front-run swap: mint narrow range → wait → burn+collect in same block",
            "barriers": [
                SecurityBarrier(
                    barrier_type="guard",
                    height=0.60,
                    thickness=0.5,
                    bypassable=True,
                    source="mempool is public",
                ),
                SecurityBarrier(
                    barrier_type="guard",
                    height=0.50,
                    thickness=0.5,
                    bypassable=True,
                    source="concentrated liquidity narrow range",
                ),
                SecurityBarrier(
                    barrier_type="guard",
                    height=0.40,
                    thickness=0.5,
                    bypassable=True,
                    source="instant withdraw allowed",
                ),
            ],
            "wave_features": {
                "moves_funds": True,
                "cei_violation": True,
                "sends_eth": False,
                "no_access_control": True,
                "not_guarded": True,
                "reads_oracle": True,
                "has_state_conflict": True,
                "modifies_balances": True,
            },
            "holo_features": {
                "has_cei_violation": True,
                "moves_funds": True,
                "reads_oracle": True,
                "has_state_conflict": True,
                "external_call_count": 4,
                "fund_flow_ratio": 0.95,
                "attack_surface_ratio": 0.9,
                "complexity_ratio": 0.8,
            },
            "energy": 0.95,
            "chain_length": 4,
        }

    # --- Scenario 7: Unguarded functions as entry ---
    if unguarded:
        for fn in unguarded[:3]:
            fa = functions_analysis[fn]
            if fa.get("wave_features", {}).get("moves_funds", False):
                scenarios[f"Unguarded_Fund_Flow_{fn}"] = {
                    "description": f"Exploit unguarded {fn}() which moves funds without proper checks",
                    "barriers": [
                        SecurityBarrier(
                            barrier_type="guard",
                            height=0.40,
                            thickness=0.5,
                            bypassable=True,
                            source=f"no guard on {fn}",
                        ),
                    ],
                    "wave_features": fa["wave_features"],
                    "holo_features": fa["holo_features"],
                    "energy": min(1.0, fa["energy"] + 0.15),
                    "chain_length": fa["chain_length"],
                }

    return scenarios


def run_heikal_math(engines: Dict, project: Dict, shared_parse: Dict = None,
                    deep_scan_results: Dict = None, exploit_results: Dict = None) -> Dict:
    """
    تشغيل خوارزميات هيكل الرياضية الأربع ديناميكياً على أي مشروع.

    المراحل:
      1. استخراج الدوال من جميع العقود (extract_function_blocks)
      2. بناء سيناريوهات الهجوم (build_attack_scenarios)
      3. تشغيل 4 خوارزميات على كل دالة (أخطر 50 فقط):
         - Tunneling Scorer: احتمال اختراق الحواجز (WKB + Heikal)
         - Wave Evaluator: تقييم خطورة بنمط تداخل الموجات
         - Holographic Patterns: مطابقة أنماط هجمات معروفة
         - Resonance Optimizer: تحسين مبلغ الهجوم لأقصى ربح
      4. تشغيل الخوارزميات على سيناريوهات الهجوم

    يستخدم shared_parse لتخطي الدوال الآمنة (view, pure, getters) تلقائياً.
    يستخدم deep_scan_results و exploit_results لتعزيز تقييم الدوال التي
    لديها أدلة رسمية (Z3 proven) أو استغلال مُثبت.

    يُرجع:
        {
            "functions": {اسم::دالة: نتائج_4_خوارزميات},
            "attacks": {اسم_السيناريو: نتائج_التحليل},
            "summary": {severity_distribution, totals}
        }
    """
    banner("LAYER 7: HEIKAL MATH ALGORITHMS (Dynamic Analysis)")

    tunneling = engines.get("tunneling")
    wave = engines.get("wave")
    holographic = engines.get("holographic")
    resonance = engines.get("resonance")

    if not all([tunneling, wave, holographic, resonance]):
        print("  ❌ Heikal Math not fully available — skipping")
        return {}

    shared_parse = shared_parse or {}
    deep_scan_results = deep_scan_results or {}
    exploit_results = exploit_results or {}
    safe_funcs = shared_parse.get("_safe_funcs", set())

    # === Build cross-layer evidence map ===
    # Collect Z3-proven functions and exploit-proven functions from prior layers
    z3_proven_funcs = set()   # functions with Z3 SAT proofs
    exploit_proven_funcs = set()  # functions with exploit proofs
    for cname, ds in deep_scan_results.items():
        if not isinstance(ds, dict):
            continue
        for sf in ds.get("symbolic_findings", []):
            if sf.get("is_proven") or sf.get("z3_result") == "SAT":
                fn = sf.get("function", "").lower()
                if fn:
                    z3_proven_funcs.add(fn)
    for cname, er in exploit_results.items():
        if not isinstance(er, dict):
            continue
        for proof in er.get("exploit_proofs", []):
            if proof.get("exploitable"):
                fn = proof.get("function", "").lower()
                if fn:
                    exploit_proven_funcs.add(fn)

    if z3_proven_funcs or exploit_proven_funcs:
        print(f"  🔗 Cross-layer: {len(z3_proven_funcs)} Z3-proven, {len(exploit_proven_funcs)} exploit-proven functions")

    contracts = project["contracts"]
    # Analyze main contracts + libraries (not interfaces)
    targets = {k: v for k, v in contracts.items() if not k.startswith("iface/")}

    print(f"\n  📐 Dynamic source code analysis on {len(targets)} files...\n")

    # === Phase 1: Extract functions from all contracts ===
    source_map = {}  # filename -> source
    all_functions = {}  # fname -> analysis
    skipped_safe = 0

    for name, path in targets.items():
        if not path.exists():
            continue
        try:
            # Reuse pre-loaded source from shared parsing
            entry = shared_parse.get(name, {})
            source = entry.get("source", "")
            if not source:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    source = f.read()
            source_map[name] = source

            # Reuse function blocks from shared parsing when available
            pre_blocks = entry.get("function_blocks", {})
            func_blocks = pre_blocks if pre_blocks else extract_function_blocks(source)
            for fname, fbody in func_blocks.items():
                # Skip constructors, internal helpers, view-only getters
                if fname in ("constructor",) or fname.startswith("_"):
                    continue

                # Use shared parse data to skip safe functions
                if fname.lower() in safe_funcs:
                    skipped_safe += 1
                    continue

                # Prefer larger/more complex functions
                analysis = analyze_function_security(fname, fbody, source)
                analysis["_contract"] = name
                analysis["_file"] = str(path)

                # Cross-layer evidence boost: if Z3 or exploit reasoning proved
                # this function is vulnerable, increase its energy score
                fn_lower = fname.lower()
                if fn_lower in z3_proven_funcs:
                    analysis["energy"] = min(1.0, analysis["energy"] + 0.2)
                    analysis["_z3_proven"] = True
                if fn_lower in exploit_proven_funcs:
                    analysis["energy"] = min(1.0, analysis["energy"] + 0.25)
                    analysis["_exploit_proven"] = True

                # Use contract::function as key to avoid collisions
                key = f"{name}::{fname}"
                all_functions[key] = analysis
        except Exception as e:
            print(f"  ⚠️  {name}: {str(e)[:120]}")

    print(
        f"  Found {len(all_functions)} analyzable functions (skipped {skipped_safe} safe)\n"
    )

    if not all_functions:
        return {"error": "No functions found to analyze"}

    # === Phase 2: Build attack scenarios ===
    attack_scenarios = build_attack_scenarios(all_functions, source_map)
    print(f"  Generated {len(attack_scenarios)} attack scenarios\n")

    # === Phase 3: Run 4 Heikal algorithms on each function ===
    results = {"functions": {}, "attacks": {}, "summary": {}}

    print("  --- Function-Level Analysis ---\n")

    # Sort by energy (danger) — analyze most dangerous first
    sorted_funcs = sorted(
        all_functions.items(),
        key=lambda x: x[1]["energy"],
        reverse=True,
    )

    for key, model in sorted_funcs[:50]:  # Top 50 functions
        func_results = {
            "description": model["description"],
            "_contract": model.get("_contract", ""),
        }

        # 1. Tunneling Scorer
        try:
            tunnel_result = tunneling.compute(
                barriers=model["barriers"],
                attack_energy=model["energy"],
                chain_length=model["chain_length"],
            )
            func_results["tunneling"] = {
                "confidence": round(tunnel_result.confidence, 4),
                "p_wkb": round(tunnel_result.p_wkb, 6),
                "p_heikal": round(tunnel_result.p_heikal, 6),
                "p_total": round(tunnel_result.p_total, 6),
                "barriers_penetrable": tunnel_result.barriers_penetrable,
                "resonance_detected": tunnel_result.resonance_detected,
            }
        except Exception as e:
            func_results["tunneling"] = {"error": str(e)[:150]}

        # 2. Wave Evaluator
        try:
            wave_result = wave.evaluate(features=model["wave_features"])
            func_results["wave"] = {
                "heuristic_score": round(wave_result.heuristic_score, 4),
                "danger_intensity": round(wave_result.danger_intensity, 4),
                "interference_bonus": round(wave_result.interference_bonus, 4),
                "protection_cancellation": round(
                    wave_result.protection_cancellation, 4
                ),
                "features_active": wave_result.features_active,
                "constructive_pairs": len(wave_result.constructive_pairs),
                "destructive_pairs": len(wave_result.destructive_pairs),
            }
        except Exception as e:
            func_results["wave"] = {"error": str(e)[:150]}

        # 3. Holographic Patterns
        try:
            holo_matches = holographic.match(contract_features=model["holo_features"])
            func_results["holographic"] = {
                "matches": len(holo_matches),
                "patterns": [
                    {
                        "name": (
                            m.pattern_name if hasattr(m, "pattern_name") else str(m)
                        ),
                        "similarity": (
                            round(m.similarity, 4) if hasattr(m, "similarity") else None
                        ),
                        "severity": m.severity if hasattr(m, "severity") else None,
                    }
                    for m in holo_matches[:5]
                ],
            }
        except Exception as e:
            func_results["holographic"] = {"error": str(e)[:150]}

        # 4. Resonance Optimizer
        try:
            WEI_PER_ETH = 10**18
            current_value = int(model["energy"] * WEI_PER_ETH)
            fee_rate = 0.003
            res_result = resonance.optimize_amount(
                current_value=current_value,
                evaluate_fn=lambda x: float(x) * fee_rate - 50.0,
                min_value=10**15,
                max_value=10 * WEI_PER_ETH,
            )
            func_results["resonance"] = {
                "best_theta": res_result.best_theta,
                "best_profit": round(res_result.best_profit, 2),
                "original_profit": round(res_result.original_profit, 2),
                "improvement_pct": round(res_result.improvement_pct, 2),
                "peaks_found": res_result.peaks_found,
            }
        except Exception as e:
            func_results["resonance"] = {"error": str(e)[:150]}

        # Determine severity (recalibrated for RC2/RC6 fixes)
        tunnel_conf = func_results.get("tunneling", {}).get("confidence", 0)
        wave_score = func_results.get("wave", {}).get("heuristic_score", 0)
        combined = max(tunnel_conf, wave_score)

        if combined > 0.85:
            severity = "HIGH"
        elif combined > 0.65:
            severity = "MEDIUM"
        elif combined > 0.45:
            severity = "LOW"
        else:
            severity = "INFO"

        func_results["severity"] = severity
        results["functions"][key] = func_results

        icon = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢", "INFO": "ℹ️ "}.get(
            severity, "?"
        )
        display_name = key if len(key) <= 42 else f"...{key[-39:]}"
        print(
            f"  {icon} {display_name:42s} | tunnel={tunnel_conf:.4f} wave={wave_score:.4f} -> {severity}"
        )

    # === Phase 4: Run algorithms on attack scenarios ===
    print("\n  --- Attack Scenario Analysis ---\n")

    for attack_name, model in attack_scenarios.items():
        attack_results = {"description": model["description"]}

        try:
            tunnel_result = tunneling.compute(
                barriers=model["barriers"],
                attack_energy=model["energy"],
                chain_length=model["chain_length"],
            )
            attack_results["tunneling"] = {
                "confidence": round(tunnel_result.confidence, 4),
                "p_wkb": round(tunnel_result.p_wkb, 6),
                "p_heikal": round(tunnel_result.p_heikal, 6),
                "p_total": round(tunnel_result.p_total, 6),
                "barriers_penetrable": tunnel_result.barriers_penetrable,
                "resonance_detected": tunnel_result.resonance_detected,
            }
        except Exception as e:
            attack_results["tunneling"] = {"error": str(e)[:150]}

        try:
            wave_result = wave.evaluate(features=model["wave_features"])
            attack_results["wave"] = {
                "heuristic_score": round(wave_result.heuristic_score, 4),
                "danger_intensity": round(wave_result.danger_intensity, 4),
                "features_active": wave_result.features_active,
            }
        except Exception as e:
            attack_results["wave"] = {"error": str(e)[:150]}

        try:
            holo_matches = holographic.match(contract_features=model["holo_features"])
            attack_results["holographic"] = {
                "matches": len(holo_matches),
                "top_pattern": (
                    holo_matches[0].pattern_name
                    if holo_matches and hasattr(holo_matches[0], "pattern_name")
                    else None
                ),
                "top_similarity": (
                    round(holo_matches[0].similarity, 4)
                    if holo_matches and hasattr(holo_matches[0], "similarity")
                    else None
                ),
            }
        except Exception as e:
            attack_results["holographic"] = {"error": str(e)[:150]}

        tunnel_conf = attack_results.get("tunneling", {}).get("confidence", 0)
        wave_score = attack_results.get("wave", {}).get("heuristic_score", 0)
        combined = max(tunnel_conf, wave_score)

        if combined > 0.80:
            severity = "CRITICAL"
        elif combined > 0.70:
            severity = "HIGH"
        elif combined > 0.50:
            severity = "MEDIUM"
        else:
            severity = "LOW"

        attack_results["severity"] = severity
        results["attacks"][attack_name] = attack_results

        icon = {"CRITICAL": "💥", "HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(
            severity, "?"
        )
        print(
            f"  {icon} {attack_name:42s} | tunnel={tunnel_conf:.4f} wave={wave_score:.4f} -> {severity}"
        )

    # Summary
    sev_dist = {}
    for item in list(results["functions"].values()) + list(results["attacks"].values()):
        s = item.get("severity", "UNKNOWN")
        sev_dist[s] = sev_dist.get(s, 0) + 1

    results["summary"] = {
        "total_functions_analyzed": len(results["functions"]),
        "total_attacks_analyzed": len(results["attacks"]),
        "severity_distribution": sev_dist,
    }

    return results


# ═══════════════════════════════════════════════════════════
#  مُولِّد إثبات المفهوم — PoC GENERATION & FOUNDRY EXECUTION
#  يأخذ نتائج التحليل ويُولّد اختبارات Foundry ديناميكية
#  تستورد العقد الحقيقي (لا MockVulnerable)
# ═══════════════════════════════════════════════════════════


def _link_pocs_to_findings(all_results: Dict) -> int:
    """
    ربط ملفات PoC بالنتائج الموحّدة — Link PoC files back to unified findings.

    Matches poc_generation.poc_files entries to unified_findings
    by (contract, function) and attaches a 'poc' field to each matched finding.

    Returns:
        Number of findings that got a PoC link.
    """
    poc_gen = all_results.get("poc_generation", {})
    poc_files = poc_gen.get("poc_files", [])
    unified = all_results.get("unified_findings", [])

    if not poc_files or not unified:
        return 0

    # Build lookup: (contract_lower, function_lower) → poc_file entry
    poc_lookup: Dict[tuple, Dict] = {}
    for pf in poc_files:
        c = (pf.get("contract", "") or "").lower().strip()
        f = (pf.get("function", "") or "").lower().strip()
        vt = (pf.get("vuln_type", "") or "").lower().strip()
        # Primary key: (contract, function)
        if c and f:
            poc_lookup[(c, f)] = pf
        # Secondary key: (contract, vuln_type) for broader matching
        if c and vt:
            poc_lookup.setdefault(("_vt_", c, vt), pf)

    linked = 0
    for finding in unified:
        fc = (finding.get("contract", "") or "").lower().strip()
        ff = (finding.get("function", finding.get("location", "")) or "").lower().strip()
        fcat = (finding.get("category", finding.get("detector", "")) or "").lower().strip()

        # Try exact (contract, function) match
        matched = poc_lookup.get((fc, ff))

        # Fallback: try (contract, vuln_type) match via category
        if not matched:
            matched = poc_lookup.get(("_vt_", fc, fcat))

        if matched:
            finding["poc"] = {
                "file": matched.get("path", ""),
                "vuln_type": matched.get("vuln_type", ""),
                "confidence": matched.get("confidence", 0),
            }
            linked += 1

    return linked


def run_poc_generation(
    all_results: Dict,
    project: Dict,
    run_forge: bool = False,
) -> Dict:
    """
    توليد اختبارات PoC ديناميكية وتشغيلها على Foundry.

    خطوتين:
      1. توليد ملفات .t.sol بناء على exploit_proofs والنتائج الموحدة
      2. (اختياري) تشغيل forge test على الملفات المُولَّدة

    المُعطيات:
        all_results:  نتائج التدقيق الكاملة (بعد إزالة التكرارات)
        project:      معلومات المشروع (contracts, project_path, ...)
        run_forge:    تشغيل Foundry تلقائياً على PoC المُولَّدة

    يُرجع:
        {
            "poc_generation": {poc_files, count, skipped, errors},
            "foundry_results": {forge_available, results, passed, failed, errors} أو None
        }
    """
    banner("LAYER 8.7: DYNAMIC PoC GENERATION — توليد إثبات المفهوم")

    project_path = project.get("project_path", "")
    if not project_path:
        # Try to infer from contracts
        contracts = project.get("contracts", {})
        if contracts:
            first_path = next(iter(contracts.values()))
            if first_path:
                project_path = str(Path(first_path).parent.parent)

    if not project_path:
        print("  ❌ Cannot determine project path — skipping PoC generation")
        return {
            "poc_generation": {"poc_files": [], "count": 0},
            "foundry_results": None,
        }

    try:
        from agl_security_tool.poc_generator import PoCGenerator, run_foundry_pocs

        generator = PoCGenerator(project_path=project_path)
        poc_result = generator.generate(all_results)

        count = poc_result.get("count", 0)
        skipped = poc_result.get("skipped", 0)
        errors = poc_result.get("errors", [])

        print(f"  📝 Generated {count} PoC files, skipped {skipped}")
        if errors:
            for err in errors[:5]:
                print(f"     ⚠️  {err}")

        for poc in poc_result.get("poc_files", []):
            print(
                f"     ✅ {Path(poc['path']).name} — {poc['contract']}.{poc.get('function','')} [{poc['vuln_type']}]"
            )

        # Run Foundry if requested
        foundry_results = None
        if run_forge and count > 0:
            print(f"\n  ⚡ Running Foundry tests on {count} PoC files...")
            foundry_results = run_foundry_pocs(
                poc_files=poc_result.get("poc_files", []),
                project_path=project_path,
            )

            if foundry_results.get("forge_available"):
                p = foundry_results.get("passed", 0)
                f = foundry_results.get("failed", 0)
                e = foundry_results.get("errors", 0)
                print(f"  🧪 Foundry: {p} PASS / {f} FAIL / {e} ERROR")

                for r in foundry_results.get("results", []):
                    icon = {
                        "PASS": "✅",
                        "FAIL": "❌",
                        "ERROR": "⚠️",
                        "TIMEOUT": "⏰",
                    }.get(r["status"], "?")
                    print(f"     {icon} {r['file']}: {r['status']}")
            else:
                print(f"  ℹ️  Forge not available: {foundry_results.get('message', '')}")

        return {
            "poc_generation": poc_result,
            "foundry_results": foundry_results,
        }

    except Exception as e:
        print(f"  ❌ PoC generation failed: {e}")
        _logger = logging.getLogger("AGL.audit_api")
        _logger.exception("PoC generation error")
        return {
            "poc_generation": {"poc_files": [], "count": 0, "error": str(e)},
            "foundry_results": None,
        }


# ═══════════════════════════════════════════════════════════
#  مُولِّد التقرير النهائي — FINAL REPORT GENERATOR
#  يُجمِّع نتائج جميع الطبقات في تقرير موحّد مع ملخص بصري
# ═══════════════════════════════════════════════════════════


def generate_final_report(
    all_results: Dict,
    project: Dict,
    target_name: str,
    total_time: float,
) -> Dict:
    """
    توليد التقرير النهائي الشامل.

    يُجمِّع نتائج جميع الطبقات (deep_scan, z3, detectors, state,
    exploit_reasoning, heikal_math) في تقرير موحّد.

    يستخدم unified_findings (بعد إزالة التكرار) إدا وُجدت،
    وإلا يحسب الإحصائيات من الطبقات الفردية.

    يطبع صندوق ملخص بصري في الطرفية مع:
      - إحصائيات الخطورة (CRITICAL → INFO)
      - عدد التكرارات المُزالة
      - الطبقات المُنفَّذة
      - أخطر النتائج من Heikal Math

    يُرجع:
        قاموس التقرير الكامل بما فيه total_findings و severity_total
    """
    banner("FINAL COMPREHENSIVE REPORT", "█")

    project_type = project.get("project_type", "unknown")
    contracts_count = len(project.get("contracts", {}))

    report = {
        "audit_name": f"{target_name} — AGL Full-Power Dynamic Audit",
        "timestamp": datetime.now().isoformat(),
        "target": target_name,
        "project_type": project_type,
        "contracts_scanned": contracts_count,
        "audit_time_seconds": round(total_time, 1),
        "engines_used": [],
        "results": all_results,
    }

    # Use unified findings from cross-layer dedup if available
    unified = all_results.get("unified_findings", [])
    dedup_stats = all_results.get("dedup_stats", {})
    severity_total = all_results.get("severity_unified", {})

    if not unified:
        # Fallback: count from individual layers (backward compat)
        total_findings = 0
        severity_total = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}

        for name, result in all_results.get("deep_scan", {}).items():
            if isinstance(result, dict):
                sev = result.get("severity_summary", {})
                for k, v in sev.items():
                    severity_total[k] = severity_total.get(k, 0) + v
                    total_findings += v

        z3_findings = all_results.get("z3_symbolic", [])
        total_findings += len(z3_findings)
        detector_findings = all_results.get("detectors", [])
        total_findings += len(detector_findings)
    else:
        total_findings = len(unified)

    # Heikal findings (counted separately — different kind of output)
    heikal = all_results.get("heikal_math", {})
    heikal_count = 0
    for item in list(heikal.get("functions", {}).values()) + list(
        heikal.get("attacks", {}).values()
    ):
        s = item.get("severity", "INFO")
        heikal_count += 1

    report["total_findings"] = total_findings
    report["severity_total"] = severity_total
    report["dedup_stats"] = dedup_stats
    report["heikal_analyses"] = heikal_count

    # PoC generation stats
    poc_gen = all_results.get("poc_generation", {})
    poc_count = poc_gen.get("count", 0)
    foundry_res = all_results.get("foundry_results")
    foundry_passed = foundry_res.get("passed", 0) if foundry_res else 0
    foundry_failed = foundry_res.get("failed", 0) if foundry_res else 0
    report["poc_generated"] = poc_count
    report["foundry_passed"] = foundry_passed
    report["foundry_failed"] = foundry_failed

    # Dedup summary line
    z3_duped = dedup_stats.get("z3_duplicates_removed", 0)
    det_duped = dedup_stats.get("detectors_duplicates_removed", 0)
    suppressed = dedup_stats.get("safe_function_suppressed", 0)
    total_removed = z3_duped + det_duped + suppressed

    # Z3 / Detector standalone counts for display
    z3_lib_count = len(all_results.get("z3_symbolic", []))
    det_lib_count = len(all_results.get("detectors", []))

    # Layer 1-4 status: check if deep_scan ran them per-file
    _l14_layers = set()
    for _name, _res in all_results.get("deep_scan", {}).items():
        if isinstance(_res, dict):
            for _ly in _res.get("layers_used", []):
                _l14_layers.add(_ly)
    _l14_ran = _l14_layers & {
        "state_extraction",
        "action_space",
        "attack_simulation",
        "search_engine",
    }
    _state_proj = all_results.get("state_extraction", {})
    _state_proj_ok = bool(_state_proj and not _state_proj.get("error"))
    if _l14_ran:
        _l14_parts = sorted(_l14_ran)
        _l14_label = (
            f"State/Action/Attack/Search ({len(_l14_ran)}/4 in deep_scan"
            + (", +project" if _state_proj_ok else "")
            + ")"
        )
    elif _state_proj_ok:
        _l14_label = "State Extraction (project-level only)"
    else:
        _l14_label = "⚠ SKIPPED (engine not available)"

    # Print summary box
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(
        f"""
  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
  ┃  TARGET: {target_name[:67]:67s} ┃
  ┃  TYPE:   {project_type:67s} ┃
  ┃  DATE:   {now_str:67s} ┃
  ┃  FILES:  {contracts_count:<67d} ┃
  ┃  TIME:   {total_time:<67.1f} ┃
  ┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
  ┃                                                                                ┃
  ┃  UNIFIED SEVERITY (after cross-layer dedup):                                   ┃
  ┃    💥 CRITICAL: {severity_total.get('CRITICAL', 0):<59d} ┃
  ┃    🔴 HIGH:     {severity_total.get('HIGH', 0):<59d} ┃
  ┃    🟡 MEDIUM:   {severity_total.get('MEDIUM', 0):<59d} ┃
  ┃    🟢 LOW:      {severity_total.get('LOW', 0):<59d} ┃
  ┃    ℹ️  INFO:     {severity_total.get('INFO', 0):<59d} ┃
  ┃                                                                                ┃
  ┃  DEDUP: {total_removed} removed (Z3 dup={z3_duped}, Det dup={det_duped}, safe={suppressed}){' ' * max(0, 52 - len(str(total_removed)) - len(str(z3_duped)) - len(str(det_duped)) - len(str(suppressed)))}┃
  ┃                                                                                ┃
  ┃  LAYERS EXECUTED:                                                              ┃
  ┃    Layer 0   : Solidity Flattener                                              ┃
  ┃    Layer 0.5 : Z3 Symbolic (deep_scan + {z3_lib_count} lib findings)                       ┃
  ┃    Layer 1-4 : {_l14_label:67s} ┃
  ┃    Layer 5   : 22 Semantic Detectors (deep_scan + {det_lib_count} lib findings)                  ┃
  ┃    Layer 6   : Exploit Reasoning (Z3 Proofs)                                   ┃
  ┃    Layer 7   : Heikal Math ({heikal_count} analyses)                                        ┃
  ┃    Layer 8.7 : PoC Generation ({poc_count} files) + Foundry ({foundry_passed}P/{foundry_failed}F)                    ┃
  ┃                                                                                ┃
  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
"""
    )

    # Print top findings
    print("  === TOP FINDINGS ===\n")

    heikal_attacks = heikal.get("attacks", {})
    for aname, adata in sorted(
        heikal_attacks.items(),
        key=lambda x: x[1].get("tunneling", {}).get("confidence", 0),
        reverse=True,
    ):
        conf = adata.get("tunneling", {}).get("confidence", 0)
        sev = adata.get("severity", "?")
        desc = adata.get("description", "")
        icon = {"CRITICAL": "💥", "HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(
            sev, "?"
        )
        print(f"  {icon} [{sev:8s}] {aname}")
        print(f"      Tunneling: {conf:.4f} | {desc[:80]}")
        print()

    return report


def generate_markdown_report(report: Dict) -> str:
    """
    توليد تقرير بصيغة Markdown.

    يشمل:
      - ملخص الخطورة (جدول)
      - نتائج هيكل: سيناريوهات + دوال (جداول)
      - نتائج الفحص العميق لكل عقد

    يُرجع:
        نص Markdown جاهز للحفظ في ملف .md
    """
    lines = []
    lines.append(f"# 🛡️ AGL Security Audit Report")
    lines.append(f"")
    lines.append(f"**Target:** {report.get('target', 'Unknown')}")
    lines.append(f"**Project Type:** {report.get('project_type', 'Unknown')}")
    lines.append(f"**Date:** {report.get('timestamp', '')}")
    lines.append(f"**Contracts Scanned:** {report.get('contracts_scanned', 0)}")
    lines.append(f"**Audit Duration:** {report.get('audit_time_seconds', 0):.1f}s")
    lines.append(f"")

    sev = report.get("severity_total", {})
    lines.append("## Severity Summary")
    lines.append("")
    lines.append("| Severity | Count |")
    lines.append("|----------|-------|")
    for s in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]:
        lines.append(f"| {s} | {sev.get(s, 0)} |")
    lines.append("")

    # Heikal Math results
    heikal = report.get("results", {}).get("heikal_math", {})
    if heikal:
        lines.append("## Heikal Math Analysis")
        lines.append("")

        attacks = heikal.get("attacks", {})
        if attacks:
            lines.append("### Attack Scenarios")
            lines.append("")
            lines.append("| Scenario | Severity | Tunneling | Wave | Description |")
            lines.append("|----------|----------|-----------|------|-------------|")
            for aname, adata in sorted(
                attacks.items(),
                key=lambda x: x[1].get("tunneling", {}).get("confidence", 0),
                reverse=True,
            ):
                sev = adata.get("severity", "?")
                tunnel = adata.get("tunneling", {}).get("confidence", 0)
                wv = adata.get("wave", {}).get("heuristic_score", 0)
                desc = adata.get("description", "")[:60]
                lines.append(f"| {aname} | {sev} | {tunnel:.4f} | {wv:.4f} | {desc} |")
            lines.append("")

        funcs = heikal.get("functions", {})
        if funcs:
            lines.append("### Function-Level Analysis (Top 20)")
            lines.append("")
            lines.append("| Function | Severity | Tunneling | Wave | Description |")
            lines.append("|----------|----------|-----------|------|-------------|")
            sorted_funcs = sorted(
                funcs.items(),
                key=lambda x: x[1].get("tunneling", {}).get("confidence", 0),
                reverse=True,
            )
            for fname, fdata in sorted_funcs[:20]:
                sev = fdata.get("severity", "?")
                tunnel = fdata.get("tunneling", {}).get("confidence", 0)
                wv = fdata.get("wave", {}).get("heuristic_score", 0)
                desc = fdata.get("description", "")[:60]
                lines.append(f"| {fname} | {sev} | {tunnel:.4f} | {wv:.4f} | {desc} |")
            lines.append("")

    # Deep scan brief
    deep = report.get("results", {}).get("deep_scan", {})
    if deep:
        lines.append("## Deep Scan Results")
        lines.append("")
        for name, result in deep.items():
            if isinstance(result, dict):
                sev = result.get("severity_summary", {})
                findings = result.get(
                    "all_findings_unified", result.get("findings", [])
                )
                t = result.get("_scan_time", 0)
                lines.append(f"### {name}")
                lines.append(f"- Findings: {len(findings)} ({t:.1f}s)")
                lines.append(
                    f"- CRITICAL: {sev.get('CRITICAL', 0)}, HIGH: {sev.get('HIGH', 0)}, MEDIUM: {sev.get('MEDIUM', 0)}, LOW: {sev.get('LOW', 0)}"
                )
                lines.append("")

    lines.append("---")
    lines.append(f"*Generated by AGL Security Auditor — Heikal Math Algorithms*")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════
#  المُنسِّق الرئيسي — MAIN ORCHESTRATOR
#  يُدير خط التدقيق الكامل بجميع طبقاته بالترتيب
# ═══════════════════════════════════════════════════════════


def run_audit(
    target: str,
    branch: Optional[str] = None,
    mode: str = "full",
    skip_heikal: bool = False,
    skip_llm: bool = False,
    include_deps: bool = False,
    include_tests: bool = False,
    output_format: str = "json",
    output_path: Optional[str] = None,
    no_deps_install: bool = False,
    generate_poc: bool = True,
    run_poc: bool = False,
) -> Dict:
    """
    واجهة التدقيق الرئيسية — تُشغِّل التدقيق الكامل على أي هدف.

    خطوات التنفيذ (11 خطوة):
      0. تحليل الهدف (resolve_target) — رابط / ملف / مجلد
      1. تحميل المحركات (load_engines) — 12 مكون
      2. اكتشاف المشروع (discover_project)
      2.5. تحليل مشترك (run_shared_parsing) — مرة واحدة
      3. فحص عميق (Layer 0-5) — deep_scan
      4. Z3 رمزي (Layer 0.5) — مكتبات فقط
      5. استخراج حالة (Layer 1-4)
      6. كواشف دلالية (Layer 5) — مكتبات فقط
      7. تحليل استغلال (Layer 6)
      7.5. إزالة التكرار عبر الطبقات
      8. هيكل رياضيات (Layer 7) — 4 خوارزميات
      8.7. توليد PoC ديناميكي + تشغيل Foundry (اختياري)
      9. توليد التقرير + حفظ الملف

    المُعطيات:
        target:          مسار محلي أو ملف .sol أو رابط GitHub
        branch:          فرع git اختياري
        mode:            "full" | "quick" | "deep" (بدون Heikal)
        skip_heikal:     تخطي Layer 7
        include_deps:    فحص الاعتماديات أيضاً
        include_tests:   شمل ملفات الاختبار
        output_format:   "json" | "markdown" | "text"
        output_path:     مسار حفظ التقرير
        no_deps_install: تخطي تثبيت الاعتماديات
        generate_poc:    توليد اختبارات PoC ديناميكية (افتراضي: True)
        run_poc:         تشغيل PoC على Foundry تلقائياً (افتراضي: False)

    يُرجع:
        قاموس التقرير الكامل
    """
    print(
        """
╔══════════════════════════════════════════════════════════════════════════════════╗
║  AGL SECURITY — FULL-POWER DYNAMIC AUDIT API                                    ║
║  واجهة تدقيق أمني ديناميكية — أي مشروع — أي رابط GitHub                       ║
╚══════════════════════════════════════════════════════════════════════════════════╝
"""
    )

    t_total = time.time()
    all_results = {}
    audit_ctx = AuditContext()
    is_temp = False

    try:
        # Step 0: Resolve target to local path
        banner("RESOLVING TARGET")
        print(f"  Target: {target}")
        project_path, is_temp = resolve_target(
            target, branch=branch, no_deps=no_deps_install
        )
        print(f"  Resolved: {project_path}")
        target_name = (
            target
            if is_github_url(target) or is_git_url(target)
            else Path(project_path).name
        )

        # Step 1: Load engines
        banner("LOADING ALL ENGINES")
        _core_cfg = {}
        if skip_llm:
            _core_cfg["skip_llm"] = True
            _core_cfg["skip_deep_analyzer"] = True
        _core_cfg["mythril_timeout"] = 90  # Cap Mythril to 90s per contract for benchmark reliability
        engines = load_engines(project_path, core_config=_core_cfg)
        print(f"\n  Loaded {len(engines)} engine components")

        # Step 2: Discover project
        banner("DISCOVERING PROJECT STRUCTURE")
        config = {
            "exclude_tests": not include_tests,
            "exclude_mocks": True,
            "scan_dependencies": include_deps,
        }
        project = discover_project(project_path, config=config)
        project["project_path"] = project_path  # needed by PoC generator
        contracts = project["contracts"]
        print(f"  Project type: {project['project_type']}")
        print(f"  Contracts dir: {project['contracts_dir']}")
        print(f"  Total files: {len(contracts)}")
        print(f"    Main contracts: {len(project['main_contracts'])}")
        print(f"    Libraries:      {len(project['libraries'])}")
        print(f"    Interfaces:     {len(project['interfaces'])}")
        print(f"\n  Files found:")
        for name, path in sorted(contracts.items())[:30]:
            print(f"    {name:45s} → {path.name}")
        if len(contracts) > 30:
            print(f"    ... and {len(contracts) - 30} more")

        if not contracts:
            print("\n  ❌ No Solidity files found!")
            return {"error": "No Solidity files found", "target": target}

        # ═══════════════════════════════════════════════════
        #  Step 2.5: SHARED SEMANTIC PARSING  — مرحلة أولى
        #  Parse all contracts ONCE, share with every layer
        # ═══════════════════════════════════════════════════
        shared_parse = run_shared_parsing(engines, project)
        audit_ctx.populate_from_shared_parse(shared_parse)

        # Step 3: Core deep scan (Layer 0-5)
        # This already includes: Flattener → Z3 → Patterns → Orchestrator → Detectors
        if mode in ("full", "deep"):
            all_results["deep_scan"] = run_core_deep_scan(engines, project, shared_parse=shared_parse)
            # Populate AuditContext with Z3-proven findings for cross-layer use
            audit_ctx.deep_scan_results = all_results["deep_scan"]
            for cname, ds in all_results["deep_scan"].items():
                if not isinstance(ds, dict):
                    continue
                for sf in ds.get("symbolic_findings", []):
                    if sf.get("is_proven") or sf.get("z3_result") == "SAT":
                        audit_ctx.add_z3_proof(cname, sf)
        else:
            all_results["deep_scan"] = {}

        # Step 4: Z3 Symbolic — LIBRARIES ONLY (main contracts already in deep_scan)
        if mode in ("full", "deep"):
            all_results["z3_symbolic"] = run_z3_symbolic(
                engines, project, shared_parse=shared_parse
            )
            audit_ctx.store_layer_result("z3_symbolic", all_results["z3_symbolic"])
        else:
            all_results["z3_symbolic"] = []

        # Step 5: State Extraction (Layer 1-4)
        # Note: L1-4 already run per-file inside deep_scan (core.py).
        # This project-level call adds cross-contract fund-flow analysis.
        if mode in ("full", "deep"):
            all_results["state_extraction"] = run_state_extraction(engines, project, shared_parse=shared_parse)
            audit_ctx.store_layer_result("state_extraction", all_results["state_extraction"])
        else:
            all_results["state_extraction"] = {}

        # Step 6: 22 Semantic Detectors — LIBRARIES ONLY (main contracts in deep_scan)
        all_results["detectors"] = run_detectors(
            engines, project, shared_parse=shared_parse, audit_ctx=audit_ctx
        )
        audit_ctx.store_layer_result("detectors", all_results["detectors"])

        # Step 7: Exploit Reasoning
        if mode in ("full", "deep"):
            all_results["exploit_reasoning"] = run_exploit_reasoning(
                engines, project, deep_scan_results=all_results.get("deep_scan", {}),
                shared_parse=shared_parse, audit_ctx=audit_ctx
            )
            audit_ctx.store_layer_result("exploit_reasoning", all_results["exploit_reasoning"])
        else:
            all_results["exploit_reasoning"] = {}

        # Step 8: Heikal Math (Layer 7) — with shared context + cross-layer data
        if not skip_heikal and mode == "full":
            all_results["heikal_math"] = run_heikal_math(
                engines, project, shared_parse=shared_parse,
                deep_scan_results=all_results.get("deep_scan", {}),
                exploit_results=all_results.get("exploit_reasoning", {}),
            )
            audit_ctx.store_layer_result("heikal_math", all_results["heikal_math"])
        else:
            all_results["heikal_math"] = {}

        # ═══════════════════════════════════════════════════
        #  Step 8.5: CROSS-LAYER DEDUPLICATION
        #  Unify, deduplicate, suppress safe-function findings
        # ═══════════════════════════════════════════════════
        all_results = deduplicate_cross_layer(all_results, shared_parse, audit_ctx=audit_ctx)
        audit_ctx.unified_findings = all_results.get("unified_findings", [])

        # ═══════════════════════════════════════════════════
        #  Step 8.7: DYNAMIC PoC GENERATION + FOUNDRY EXECUTION
        #  توليد اختبارات إثبات المفهوم وتشغيلها على Foundry
        # ═══════════════════════════════════════════════════
        if generate_poc and mode in ("full", "deep"):
            poc_results = run_poc_generation(
                all_results=all_results,
                project=project,
                run_forge=run_poc,
            )
            all_results["poc_generation"] = poc_results.get("poc_generation", {})
            all_results["foundry_results"] = poc_results.get("foundry_results")

            # Link PoC files back to individual unified findings
            linked = _link_pocs_to_findings(all_results)
            if linked:
                print(f"  🔗 Linked {linked} PoC files to unified findings")
        else:
            all_results["poc_generation"] = {}
            all_results["foundry_results"] = None

        # Step 9: Final report
        total_time = time.time() - t_total
        report = generate_final_report(all_results, project, target_name, total_time)

        print(f"\n  ⏱️  Total audit time: {total_time:.1f} seconds")

        # Step 10: Save results
        if output_path:
            save_path = Path(output_path)
        else:
            safe_name = re.sub(r"[^\w\-.]", "_", target_name)[:50]
            save_path = ROOT / f"audit_results_{safe_name}.json"

        try:
            if output_format == "markdown" or str(save_path).endswith(".md"):
                md_report = generate_markdown_report(report)
                with open(save_path, "w", encoding="utf-8") as f:
                    f.write(md_report)
                print(f"  💾 Markdown report saved to: {save_path}")
            else:
                with open(save_path, "w", encoding="utf-8") as f:
                    json.dump(report, f, indent=2, ensure_ascii=False, default=str)
                print(f"  💾 JSON results saved to: {save_path}")
        except Exception as e:
            print(f"  ⚠️  Failed to save: {e}")

        print(f"\n{'█' * 80}")
        print("  ✅ AUDIT COMPLETE / التدقيق اكتمل")
        print(f"{'█' * 80}\n")

        return report

    finally:
        # Cleanup temp directory if we cloned
        if is_temp and project_path and os.path.exists(project_path):
            try:
                print(f"\n  🧹 Cleaning up temp directory: {project_path}")
                shutil.rmtree(project_path, ignore_errors=True)
            except Exception:
                pass


# ═══════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════
#  واجهة سطر الأوامر — CLI INTERFACE
#  نقطة الدخول عبر python agl_audit_api.py <target>
# ═══════════════════════════════════════════════════════════


def main():
    """
    نقطة الدخول الرئيسية لواجهة سطر الأوامر (CLI).

    تدعم:
      - مسار محلي (مجلد أو ملف .sol)
      - رابط GitHub (يُستنسخ تلقائياً)
      - أوضاع: full | deep | quick
      - صيغ الخرج: json | markdown | text
      - خيارات: --skip-heikal, --include-deps, --include-tests

    الاستخدام:
      python agl_audit_api.py ./my-project
      python agl_audit_api.py https://github.com/Uniswap/v3-core
      python agl_audit_api.py ./project --mode full --format markdown -o report.md
    """
    parser = argparse.ArgumentParser(
        prog="agl_audit_api",
        description=(
            "🛡️ AGL Full-Power Dynamic Audit API\n"
            "واجهة تدقيق أمني ديناميكية — لأي مشروع عقود ذكية\n"
            "\n"
            "Supports:\n"
            "  • Local Foundry/Hardhat/Truffle/Brownie/Ape projects\n"
            "  • GitHub repository URLs (auto-cloned)\n"
            "  • Single .sol files\n"
            "  • Bare directories with .sol files\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s ./my-defi-project
  %(prog)s ./contracts/MyToken.sol
  %(prog)s https://github.com/Uniswap/v3-core
  %(prog)s https://github.com/aave/aave-v3-core --branch main
  %(prog)s https://github.com/OpenZeppelin/openzeppelin-contracts --mode quick
  %(prog)s ./project --mode full --format markdown -o report.md
  %(prog)s ./project --include-deps --include-tests
  %(prog)s ./project --skip-heikal  # faster, no Layer 7
        """,
    )

    parser.add_argument(
        "target",
        help="Local path (directory or .sol file) or GitHub URL",
    )
    parser.add_argument(
        "--branch",
        "-b",
        help="Git branch or tag to clone (default: default branch)",
    )
    parser.add_argument(
        "--mode",
        "-m",
        choices=["full", "deep", "quick"],
        default="full",
        help="Audit mode: full (all 8 layers), deep (0-6), quick (patterns only)",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["json", "markdown", "text"],
        default="json",
        help="Output format (default: json)",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output file path (default: auto-named in current dir)",
    )
    parser.add_argument(
        "--skip-heikal",
        action="store_true",
        help="Skip Layer 7 Heikal Math analysis",
    )
    parser.add_argument(
        "--include-deps",
        action="store_true",
        help="Also scan project dependencies (node_modules, lib/)",
    )
    parser.add_argument(
        "--include-tests",
        action="store_true",
        help="Include test files in the scan",
    )
    parser.add_argument(
        "--no-deps-install",
        action="store_true",
        help="Skip dependency installation for cloned repos",
    )
    parser.add_argument(
        "--no-poc",
        action="store_true",
        help="Skip PoC generation (enabled by default in full/deep mode)",
    )
    parser.add_argument(
        "--run-poc",
        action="store_true",
        help="Run generated PoC tests on Foundry (requires forge)",
    )

    args = parser.parse_args()

    run_audit(
        target=args.target,
        branch=args.branch,
        mode=args.mode,
        skip_heikal=args.skip_heikal,
        include_deps=args.include_deps,
        include_tests=args.include_tests,
        output_format=args.format,
        output_path=args.output,
        no_deps_install=args.no_deps_install,
        generate_poc=not args.no_poc,
        run_poc=args.run_poc,
    )


if __name__ == "__main__":
    main()
