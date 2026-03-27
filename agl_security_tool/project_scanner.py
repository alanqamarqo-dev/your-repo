"""
AGL Security — ماسح المشاريع الكاملة
Project Scanner for Foundry / Hardhat / Truffle / Bare Solidity Projects

يفحص مشروع كامل من العقود الذكية مع تحليل:
  - اكتشاف نوع المشروع تلقائياً (Foundry/Hardhat/Truffle)
  - حل مسارات الاستيراد (import resolution) مع remappings
  - بناء شجرة التبعيات (dependency graph)
  - فحص متسلسل لكل عقد مع سياق التوارث
  - تقرير شامل على مستوى المشروع

Usage:
    from agl_security_tool import ProjectScanner
    scanner = ProjectScanner("path/to/project")
    report = scanner.full_scan()
"""

import os
import re
import sys
import json
import time
import glob
from typing import Dict, Any, List, Optional, Set, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from collections import defaultdict


# ═══════════════════════════════════════════════════════════════
#  نماذج البيانات — Data Models
# ═══════════════════════════════════════════════════════════════


@dataclass
class SolidityFile:
    """نموذج بيانات لملف Solidity واحد."""

    path: str  # المسار الكامل
    relative_path: str  # المسار النسبي من جذر المشروع
    size: int = 0  # حجم الملف
    pragma: str = ""  # إصدار المترجم
    license: str = ""  # نوع الرخصة
    imports: List[str] = field(default_factory=list)  # الاستيرادات الخام
    resolved_imports: List[str] = field(default_factory=list)  # الاستيرادات بعد الحل
    contracts: List[str] = field(default_factory=list)  # أسماء العقود المعرّفة
    interfaces: List[str] = field(default_factory=list)  # أسماء الواجهات
    libraries: List[str] = field(default_factory=list)  # أسماء المكتبات
    inherits: List[str] = field(default_factory=list)  # العقود المورّثة
    functions_count: int = 0  # عدد الدوال
    external_calls: int = 0  # عدد النداءات الخارجية
    state_vars: int = 0  # عدد المتغيرات الحالة
    loc: int = 0  # عدد الأسطر البرمجية (بدون تعليقات وفراغات)


@dataclass
class ProjectInfo:
    """معلومات المشروع المكتشفة."""

    project_type: str = "unknown"  # foundry / hardhat / truffle / bare
    root_dir: str = ""  # المجلد الجذري
    contracts_dir: str = ""  # مجلد العقود الرئيسي
    test_dir: str = ""  # مجلد الاختبارات
    lib_dirs: List[str] = field(default_factory=list)  # مجلدات المكتبات
    remappings: Dict[str, str] = field(default_factory=dict)  # إعادة تعيين المسارات
    compiler_version: str = ""  # إصدار المترجم
    node_modules: str = ""  # مسار node_modules
    total_sol_files: int = 0  # إجمالي ملفات .sol
    total_contracts: int = 0  # إجمالي العقود


# ═══════════════════════════════════════════════════════════════
#  الماسح الرئيسي — ProjectScanner
# ═══════════════════════════════════════════════════════════════


class ProjectScanner:
    """
    ماسح مشاريع العقود الذكية الكاملة.
    يدعم Foundry / Hardhat / Truffle / Bare Projects.

    Usage:
        scanner = ProjectScanner("/path/to/project")
        report = scanner.full_scan()
        print(report["summary"])

        # أو فحص سريع
        report = scanner.quick_scan()

        # فحص عميق مع Z3
        report = scanner.deep_scan()
    """

    # أنماط regex ثابتة
    _RE_PRAGMA = re.compile(r"pragma\s+solidity\s+([^;]+);")
    _RE_LICENSE = re.compile(r"//\s*SPDX-License-Identifier:\s*(.+)")
    _RE_IMPORT = re.compile(
        r"import\s+"
        r"(?:"
        r"(?:{\s*[\w\s,]+\s*}\s+from\s+)?"  # {Symbol, Symbol2} from
        r"|"
        r"(?:[\w]+\s+from\s+)?"  # Alias from
        r")?"
        r'["\']([^"\']+)["\']'  # المسار بين علامات التنصيص
        r"\s*;"
    )
    _RE_CONTRACT = re.compile(
        r"(?:abstract\s+)?contract\s+(\w+)" r"(?:\s+is\s+([\w\s,]+))?"
    )
    _RE_INTERFACE = re.compile(r"interface\s+(\w+)")
    _RE_LIBRARY = re.compile(r"library\s+(\w+)")
    _RE_FUNCTION = re.compile(r"function\s+\w+\s*\(")
    _RE_EXTERNAL_CALL = re.compile(
        r"\.\w+\s*\(|\.call\s*[({]|\.delegatecall\s*[({]|\.staticcall\s*[({]"
    )
    _RE_STATE_VAR = re.compile(
        r"^\s*(?:mapping|address|uint\d*|int\d*|bytes\d*|string|bool|struct)\s+",
        re.MULTILINE,
    )
    _RE_COMMENT_SINGLE = re.compile(r"//.*$", re.MULTILINE)
    _RE_COMMENT_MULTI = re.compile(r"/\*.*?\*/", re.DOTALL)

    # مسارات استثناء (لا يتم فحصها)
    EXCLUDE_PATTERNS = {
        "node_modules",
        ".git",
        "cache",
        "out",
        "build",
        "artifacts",
        "typechain",
        "typechain-types",
        "coverage",
        ".deps",
        "crytic-export",
    }

    def __init__(self, project_path: str, config: Optional[Dict[str, Any]] = None):
        """
        تهيئة ماسح المشروع.

        Args:
            project_path: مسار المجلد الجذري للمشروع
            config: إعدادات اختيارية:
                - exclude_tests: bool — استبعاد ملفات الاختبار (default: True)
                - exclude_mocks: bool — استبعاد ملفات المحاكاة (default: True)
                - exclude_interfaces: bool — استبعاد الواجهات فقط (default: False)
                - max_file_size_kb: int — حد أقصى لحجم الملف بالكيلوبايت (default: 500)
                - severity_filter: list — تصفية حسب الخطورة ["critical","high","medium","low"]
                - custom_remappings: dict — تعيينات مسارات إضافية
                - parallel: bool — فحص متوازي (default: False)
                - scan_dependencies: bool — فحص المكتبات المثبتة أيضاً (default: False)
        """
        self.project_path = str(Path(project_path).resolve())
        self.config = config or {}
        self.project_info = ProjectInfo(root_dir=self.project_path)
        self.files: Dict[str, SolidityFile] = {}  # relative_path -> SolidityFile
        self.dependency_graph: Dict[str, Set[str]] = {}  # contract -> {parents}
        self.reverse_deps: Dict[str, Set[str]] = {}  # contract -> {children}
        self._audit = None  # مرجع لمحرك الفحص
        self._scan_results: Dict[str, Dict] = {}  # file -> scan result

    # ═══════════════════════════════════════════════════
    #  الواجهة العامة — Public API
    # ═══════════════════════════════════════════════════

    def discover(self) -> ProjectInfo:
        """
        اكتشاف نوع المشروع وبنيته. يجب استدعاؤها قبل الفحص.

        Returns:
            ProjectInfo مع كل المعلومات المكتشفة
        """
        self._detect_project_type()
        self._load_remappings()
        self._discover_files()
        self._parse_all_files()
        self._build_dependency_graph()
        return self.project_info

    def full_scan(self, output_format: str = "dict") -> Dict[str, Any]:
        """
        فحص كامل للمشروع — كل الطبقات (Pattern + Suite + Z3).

        Args:
            output_format: "dict" أو "json" أو "markdown" أو "text"

        Returns:
            تقرير شامل بكل النتائج مرتبة حسب الخطورة
        """
        return self._run_scan(mode="scan", output_format=output_format)

    def quick_scan(self, output_format: str = "dict") -> Dict[str, Any]:
        """
        فحص سريع — أنماط regex فقط. مناسب لمئات الملفات.

        Args:
            output_format: "dict" أو "json" أو "markdown" أو "text"
        """
        return self._run_scan(mode="quick", output_format=output_format)

    def deep_scan(self, output_format: str = "dict") -> Dict[str, Any]:
        """
        فحص عميق — كل شيء بما في ذلك Z3 و EVM والذكاء الاصطناعي.

        Args:
            output_format: "dict" أو "json" أو "markdown" أو "text"
        """
        return self._run_scan(mode="deep", output_format=output_format)

    def get_dependency_graph(self) -> Dict[str, Any]:
        """
        إرجاع شجرة التبعيات كـ dict قابل للتسلسل.

        Returns:
            {"nodes": [...], "edges": [...], "roots": [...], "leaves": [...]}
        """
        if not self.files:
            self.discover()

        nodes = []
        edges = []
        all_contracts = set()
        has_parent = set()

        for rel_path, sf in self.files.items():
            for c in sf.contracts:
                all_contracts.add(c)
                nodes.append(
                    {
                        "name": c,
                        "file": rel_path,
                        "type": "contract",
                        "functions": sf.functions_count,
                        "external_calls": sf.external_calls,
                    }
                )
                for parent in sf.inherits:
                    edges.append({"from": c, "to": parent, "type": "inherits"})
                    has_parent.add(c)

            for i in sf.interfaces:
                all_contracts.add(i)
                nodes.append({"name": i, "file": rel_path, "type": "interface"})

            for lib in sf.libraries:
                all_contracts.add(lib)
                nodes.append({"name": lib, "file": rel_path, "type": "library"})

        for rel_path, sf in self.files.items():
            for imp in sf.resolved_imports:
                imp_rel = self._to_relative(imp)
                if imp_rel in self.files:
                    for c in sf.contracts:
                        for ic in self.files[imp_rel].contracts:
                            edges.append({"from": c, "to": ic, "type": "imports"})

        roots = all_contracts - has_parent
        leaf_parents = set()
        for e in edges:
            leaf_parents.add(e["to"])
        leaves = all_contracts - leaf_parents

        return {
            "nodes": nodes,
            "edges": edges,
            "roots": sorted(roots),
            "leaves": sorted(leaves),
            "total_contracts": len(all_contracts),
        }

    def get_project_stats(self) -> Dict[str, Any]:
        """
        إحصائيات المشروع العامة بدون فحص أمني.

        Returns:
            dict مع الإحصائيات: عدد الملفات، العقود، أسطر الكود، إلخ.
        """
        if not self.files:
            self.discover()

        total_loc = sum(sf.loc for sf in self.files.values())
        total_functions = sum(sf.functions_count for sf in self.files.values())
        total_ext_calls = sum(sf.external_calls for sf in self.files.values())
        total_state = sum(sf.state_vars for sf in self.files.values())
        total_contracts = sum(len(sf.contracts) for sf in self.files.values())
        total_interfaces = sum(len(sf.interfaces) for sf in self.files.values())
        total_libraries = sum(len(sf.libraries) for sf in self.files.values())

        # حساب إصدارات المترجم المستخدمة
        pragmas = defaultdict(int)
        for sf in self.files.values():
            if sf.pragma:
                pragmas[sf.pragma] += 1

        licenses = defaultdict(int)
        for sf in self.files.values():
            if sf.license:
                licenses[sf.license] += 1

        # أكبر الملفات (أعلى خطورة عادةً)
        largest = sorted(self.files.values(), key=lambda x: x.loc, reverse=True)[:10]

        # الملفات الأكثر استدعاءات خارجية (أعلى سطح هجوم)
        most_calls = sorted(
            self.files.values(), key=lambda x: x.external_calls, reverse=True
        )[:10]

        return {
            "project_type": self.project_info.project_type,
            "root_dir": self.project_info.root_dir,
            "contracts_dir": self.project_info.contracts_dir,
            "total_sol_files": len(self.files),
            "total_contracts": total_contracts,
            "total_interfaces": total_interfaces,
            "total_libraries": total_libraries,
            "total_loc": total_loc,
            "total_functions": total_functions,
            "total_external_calls": total_ext_calls,
            "total_state_variables": total_state,
            "compiler_versions": dict(pragmas),
            "licenses": dict(licenses),
            "largest_files": [
                {"file": f.relative_path, "loc": f.loc, "contracts": f.contracts}
                for f in largest
            ],
            "highest_attack_surface": [
                {
                    "file": f.relative_path,
                    "external_calls": f.external_calls,
                    "contracts": f.contracts,
                }
                for f in most_calls
                if f.external_calls > 0
            ],
            "remappings": self.project_info.remappings,
            "lib_dirs": self.project_info.lib_dirs,
        }

    # ═══════════════════════════════════════════════════
    #  اكتشاف المشروع — Project Detection
    # ═══════════════════════════════════════════════════

    def _detect_project_type(self):
        """اكتشاف نوع المشروع من الملفات الموجودة."""
        root = Path(self.project_path)

        # ── Foundry ──
        if (root / "foundry.toml").exists():
            self.project_info.project_type = "foundry"
            self.project_info.contracts_dir = str(root / "src")
            self.project_info.test_dir = str(root / "test")
            self.project_info.lib_dirs = [str(root / "lib")]
            if (root / "node_modules").exists():
                self.project_info.node_modules = str(root / "node_modules")
            self._parse_foundry_toml(root / "foundry.toml")
            return

        # ── Hardhat ──
        if (root / "hardhat.config.js").exists() or (
            root / "hardhat.config.ts"
        ).exists():
            self.project_info.project_type = "hardhat"
            self.project_info.contracts_dir = str(root / "contracts")
            self.project_info.test_dir = str(root / "test")
            if (root / "node_modules").exists():
                self.project_info.node_modules = str(root / "node_modules")
                self.project_info.lib_dirs = [str(root / "node_modules")]
            return

        # ── Truffle ──
        if (root / "truffle-config.js").exists() or (root / "truffle.js").exists():
            self.project_info.project_type = "truffle"
            self.project_info.contracts_dir = str(root / "contracts")
            self.project_info.test_dir = str(root / "test")
            if (root / "node_modules").exists():
                self.project_info.node_modules = str(root / "node_modules")
                self.project_info.lib_dirs = [str(root / "node_modules")]
            return

        # ── Brownie ──
        if (root / "brownie-config.yaml").exists():
            self.project_info.project_type = "brownie"
            self.project_info.contracts_dir = str(root / "contracts")
            self.project_info.test_dir = str(root / "tests")
            return

        # ── Ape ──
        if (root / "ape-config.yaml").exists():
            self.project_info.project_type = "ape"
            self.project_info.contracts_dir = str(root / "contracts")
            self.project_info.test_dir = str(root / "tests")
            return

        # ── Bare (مجرد ملفات .sol) ──
        self.project_info.project_type = "bare"
        # ابحث عن مجلد contracts إذا وجد
        if (root / "contracts").exists():
            self.project_info.contracts_dir = str(root / "contracts")
        elif (root / "src").exists():
            self.project_info.contracts_dir = str(root / "src")
        else:
            self.project_info.contracts_dir = self.project_path

    def _parse_foundry_toml(self, toml_path: Path):
        """تحليل foundry.toml لاستخراج الإعدادات."""
        try:
            content = toml_path.read_text(encoding="utf-8")

            # استخراج src
            m = re.search(r'src\s*=\s*["\']([^"\']+)["\']', content)
            if m:
                self.project_info.contracts_dir = str(
                    Path(self.project_path) / m.group(1)
                )

            # استخراج test
            m = re.search(r'test\s*=\s*["\']([^"\']+)["\']', content)
            if m:
                self.project_info.test_dir = str(Path(self.project_path) / m.group(1))

            # استخراج libs
            libs_match = re.search(r"libs\s*=\s*\[([^\]]+)\]", content)
            if libs_match:
                libs_raw = libs_match.group(1)
                libs = re.findall(r'["\']([^"\']+)["\']', libs_raw)
                self.project_info.lib_dirs = [
                    str(Path(self.project_path) / lib) for lib in libs
                ]

            # استخراج solc_version
            m = re.search(r'solc_version\s*=\s*["\']([^"\']+)["\']', content)
            if m:
                self.project_info.compiler_version = m.group(1)

            # استخراج remappings من foundry.toml
            remap_match = re.search(r"remappings\s*=\s*\[([^\]]+)\]", content)
            if remap_match:
                raw = remap_match.group(1)
                pairs = re.findall(r'["\']([^"\']+)["\']', raw)
                for pair in pairs:
                    if "=" in pair:
                        key, val = pair.split("=", 1)
                        self.project_info.remappings[key.strip()] = val.strip()
        except Exception:
            pass

    def _load_remappings(self):
        """تحميل remappings.txt أو من إعدادات المستخدم."""
        root = Path(self.project_path)

        # remappings.txt (يستخدمه Foundry)
        remap_file = root / "remappings.txt"
        if remap_file.exists():
            try:
                for line in remap_file.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line and "=" in line and not line.startswith("#"):
                        key, val = line.split("=", 1)
                        self.project_info.remappings[key.strip()] = val.strip()
            except Exception:
                pass

        # إعادة تعيينات مخصصة من الإعدادات
        custom = self.config.get("custom_remappings", {})
        self.project_info.remappings.update(custom)

        # إضافة remappings تلقائية لمكتبات Foundry
        for lib_dir in self.project_info.lib_dirs:
            if os.path.isdir(lib_dir):
                for entry in os.listdir(lib_dir):
                    full = os.path.join(lib_dir, entry)
                    if os.path.isdir(full):
                        # forge-std/ -> lib/forge-std/src/
                        src_path = os.path.join(full, "src")
                        if os.path.isdir(src_path):
                            key = f"{entry}/"
                            if key not in self.project_info.remappings:
                                self.project_info.remappings[key] = f"{src_path}/"
                        # مباشرة بدون src/
                        contracts_path = os.path.join(full, "contracts")
                        if os.path.isdir(contracts_path):
                            key = f"@{entry}/"
                            if key not in self.project_info.remappings:
                                self.project_info.remappings[key] = f"{contracts_path}/"

        # إضافة remappings لمكتبات node_modules الشائعة
        if self.project_info.node_modules and os.path.isdir(
            self.project_info.node_modules
        ):
            nm = self.project_info.node_modules
            common_libs = [
                ("@openzeppelin/", os.path.join(nm, "@openzeppelin")),
                ("@chainlink/", os.path.join(nm, "@chainlink")),
                ("@uniswap/", os.path.join(nm, "@uniswap")),
                ("solmate/", os.path.join(nm, "solmate", "src")),
            ]
            for key, val in common_libs:
                if os.path.isdir(val) and key not in self.project_info.remappings:
                    self.project_info.remappings[key] = val + "/"

    # ═══════════════════════════════════════════════════
    #  اكتشاف الملفات — File Discovery
    # ═══════════════════════════════════════════════════

    def _discover_files(self):
        """اكتشاف كل ملفات .sol في المشروع."""
        root = Path(self.project_path)
        exclude_tests = self.config.get("exclude_tests", True)
        exclude_mocks = self.config.get("exclude_mocks", True)
        scan_deps = self.config.get("scan_dependencies", False)
        max_size = self.config.get("max_file_size_kb", 500) * 1024

        for dirpath, dirnames, filenames in os.walk(self.project_path):
            # تصفية المجلدات المستبعدة
            rel_dir = os.path.relpath(dirpath, self.project_path)
            parts = set(Path(rel_dir).parts)

            # استبعاد مجلدات البناء/الكاش
            if parts & self.EXCLUDE_PATTERNS:
                dirnames.clear()
                continue

            # استبعاد المكتبات المثبتة (إلا إذا طلب المستخدم فحصها)
            if not scan_deps:
                if "node_modules" in parts or "lib" in parts:
                    dirnames.clear()
                    continue

            # استبعاد مجلدات الاختبار
            if exclude_tests:
                is_test_dir = any(p in parts for p in {"test", "tests", "test-foundry"})
                if is_test_dir:
                    continue

            for filename in filenames:
                if not filename.endswith(".sol"):
                    continue

                filepath = os.path.join(dirpath, filename)
                rel_path = os.path.relpath(filepath, self.project_path)

                # استبعاد ملفات الاختبار
                if exclude_tests and self._is_test_file(filename, rel_path):
                    continue

                # استبعاد ملفات المحاكاة
                if exclude_mocks and self._is_mock_file(filename, rel_path):
                    continue

                # التحقق من الحجم
                try:
                    size = os.path.getsize(filepath)
                    if size > max_size:
                        continue
                    if size == 0:
                        continue
                except OSError:
                    continue

                self.files[rel_path] = SolidityFile(
                    path=filepath,
                    relative_path=rel_path,
                    size=size,
                )

        self.project_info.total_sol_files = len(self.files)

    def _is_test_file(self, filename: str, rel_path: str) -> bool:
        """تحديد ما إذا كان الملف ملف اختبار."""
        name_lower = filename.lower()
        if name_lower.endswith(".t.sol"):
            return True
        if name_lower.startswith("test") or name_lower.startswith("mock"):
            return True
        if "test" in rel_path.lower().split(os.sep):
            return True
        return False

    def _is_mock_file(self, filename: str, rel_path: str) -> bool:
        """تحديد ما إذا كان الملف ملف محاكاة."""
        name_lower = filename.lower()
        if "mock" in name_lower or "stub" in name_lower or "fake" in name_lower:
            return True
        if "mock" in rel_path.lower().split(os.sep):
            return True
        return False

    # ═══════════════════════════════════════════════════
    #  تحليل الملفات — File Parsing
    # ═══════════════════════════════════════════════════

    def _parse_all_files(self):
        """تحليل كل الملفات المكتشفة واستخراج المعلومات."""
        total_contracts = 0

        for rel_path, sf in self.files.items():
            try:
                content = self._read_file(sf.path)
                if not content:
                    continue

                # استخراج pragma
                m = self._RE_PRAGMA.search(content)
                if m:
                    sf.pragma = m.group(1).strip()

                # استخراج license
                m = self._RE_LICENSE.search(content)
                if m:
                    sf.license = m.group(1).strip()

                # استخراج imports
                sf.imports = self._RE_IMPORT.findall(content)
                sf.resolved_imports = [
                    self._resolve_import(imp, sf.path) for imp in sf.imports
                ]

                # استخراج contracts + inheritance
                for match in self._RE_CONTRACT.finditer(content):
                    name = match.group(1)
                    sf.contracts.append(name)
                    if match.group(2):
                        parents = [p.strip() for p in match.group(2).split(",")]
                        sf.inherits.extend(parents)

                # استخراج interfaces
                sf.interfaces = self._RE_INTERFACE.findall(content)

                # استخراج libraries
                sf.libraries = self._RE_LIBRARY.findall(content)

                # إحصائيات
                # حذف التعليقات لحساب LOC
                stripped = self._RE_COMMENT_MULTI.sub("", content)
                stripped = self._RE_COMMENT_SINGLE.sub("", stripped)
                sf.loc = sum(1 for line in stripped.splitlines() if line.strip())

                sf.functions_count = len(self._RE_FUNCTION.findall(content))
                sf.external_calls = len(self._RE_EXTERNAL_CALL.findall(content))
                sf.state_vars = len(self._RE_STATE_VAR.findall(content))

                total_contracts += len(sf.contracts)

            except Exception:
                # تسجيل عدد الملفات الفاشلة بدل التجاهل الصامت
                self._parse_failures = getattr(self, "_parse_failures", 0) + 1

        self.project_info.total_contracts = total_contracts

    def _read_file(self, path: str) -> Optional[str]:
        """قراءة ملف بأمان."""
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception:
            return None

    def _resolve_import(self, import_path: str, source_file: str) -> str:
        """
        حل مسار الاستيراد — يحويل المسار النسبي أو المُعاد تعيينه إلى مسار حقيقي.

        يدعم:
          - مسارات نسبية: "./Token.sol", "../utils/Math.sol"
          - remappings: "@openzeppelin/contracts/token/ERC20/ERC20.sol"
          - node_modules: "solmate/src/tokens/ERC20.sol"
          - lib/: "forge-std/src/Test.sol"
        """
        # 1. المسارات النسبية
        if import_path.startswith("."):
            source_dir = os.path.dirname(source_file)
            resolved = os.path.normpath(os.path.join(source_dir, import_path))
            if os.path.isfile(resolved):
                return resolved
            return resolved

        # 2. Remappings
        for prefix, replacement in sorted(
            self.project_info.remappings.items(),
            key=lambda x: len(x[0]),
            reverse=True,  # أطول prefix أولاً
        ):
            if import_path.startswith(prefix):
                rest = import_path[len(prefix) :]
                resolved = os.path.normpath(
                    os.path.join(self.project_path, replacement, rest)
                )
                if os.path.isfile(resolved):
                    return resolved
                # حاول بدون المجلد الجذري (قد يكون مسار مطلق)
                resolved2 = os.path.normpath(os.path.join(replacement, rest))
                if os.path.isfile(resolved2):
                    return resolved2

        # 3. node_modules
        if self.project_info.node_modules:
            candidate = os.path.join(self.project_info.node_modules, import_path)
            if os.path.isfile(candidate):
                return candidate

        # 4. lib dirs
        for lib_dir in self.project_info.lib_dirs:
            candidate = os.path.join(lib_dir, import_path)
            if os.path.isfile(candidate):
                return candidate
            # محاولة مع src/
            parts = import_path.split("/", 1)
            if len(parts) == 2:
                candidate2 = os.path.join(lib_dir, parts[0], "src", parts[1])
                if os.path.isfile(candidate2):
                    return candidate2

        # 5. مباشرة من جذر المشروع
        candidate = os.path.join(self.project_path, import_path)
        if os.path.isfile(candidate):
            return candidate

        # لم يتم الحل — نعيد المسار الأصلي
        return import_path

    # ═══════════════════════════════════════════════════
    #  شجرة التبعيات — Dependency Graph
    # ═══════════════════════════════════════════════════

    def _build_dependency_graph(self):
        """بناء شجرة التبعيات من العقود والتوارث."""
        # جمع كل أسماء العقود/الواجهات/المكتبات
        name_to_file: Dict[str, str] = {}  # contract_name -> relative_path
        for rel_path, sf in self.files.items():
            for c in sf.contracts + sf.interfaces + sf.libraries:
                name_to_file[c] = rel_path

        # بناء الشجرة
        for rel_path, sf in self.files.items():
            for c in sf.contracts:
                self.dependency_graph[c] = set(sf.inherits)
                for parent in sf.inherits:
                    if parent not in self.reverse_deps:
                        self.reverse_deps[parent] = set()
                    self.reverse_deps[parent].add(c)

    # ═══════════════════════════════════════════════════
    #  تنفيذ الفحص — Scan Execution
    # ═══════════════════════════════════════════════════

    def _run_scan(
        self, mode: str = "scan", output_format: str = "dict"
    ) -> Dict[str, Any]:
        """تنفيذ الفحص الفعلي على كل الملفات المكتشفة."""
        # اكتشاف المشروع إذا لم يتم
        if not self.files:
            self.discover()

        # تحميل محرك الفحص
        if self._audit is None:
            try:
                from agl_security_tool.core import AGLSecurityAudit

                self._audit = AGLSecurityAudit(self.config)
            except ImportError:
                return {"error": "محرك الفحص غير متوفر", "status": "ERROR"}

        t0 = time.time()
        all_findings = []
        file_results = {}
        severity_total = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        files_with_findings = 0
        skipped = 0

        # ترتيب الملفات: الأكبر أولاً (عادةً الأهم)
        sorted_files = sorted(self.files.values(), key=lambda x: x.loc, reverse=True)

        total = len(sorted_files)
        for idx, sf in enumerate(sorted_files, 1):
            try:
                if mode == "quick":
                    result = self._audit.quick_scan(sf.path)
                elif mode == "deep":
                    result = self._audit.deep_scan(sf.path)
                else:
                    result = self._audit.scan(sf.path)

                findings_count = 0
                # جمع النتائج
                for f in result.get("findings", []):
                    f["file"] = sf.relative_path
                    f["contracts_in_file"] = sf.contracts
                    all_findings.append(f)
                    findings_count += 1
                    sev = f.get("severity", "low").upper()
                    if sev in severity_total:
                        severity_total[sev] += 1

                for f in result.get("suite_findings", []):
                    f["file"] = sf.relative_path
                    f["contracts_in_file"] = sf.contracts
                    all_findings.append(f)
                    findings_count += 1
                    sev = f.get("severity", "low").upper()
                    if sev in severity_total:
                        severity_total[sev] += 1

                if findings_count > 0:
                    files_with_findings += 1

                file_results[sf.relative_path] = {
                    "findings_count": findings_count,
                    "severity": result.get("severity_summary", {}),
                    "contracts": sf.contracts,
                    "loc": sf.loc,
                    "time": result.get("time_seconds", 0),
                }
                self._scan_results[sf.relative_path] = result

            except Exception as e:
                file_results[sf.relative_path] = {
                    "error": str(e),
                    "contracts": sf.contracts,
                }
                skipped += 1

        elapsed = round(time.time() - t0, 2)

        # ترتيب النتائج حسب الخطورة
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        all_findings.sort(
            key=lambda f: severity_order.get(f.get("severity", "low").upper(), 4)
        )

        # تحليل الأنماط المتكررة عبر العقود
        cross_contract_patterns = self._analyze_cross_contract(all_findings)

        report = {
            "status": "COMPLETE",
            "scan_mode": mode,
            "project_type": self.project_info.project_type,
            "project_root": self.project_info.root_dir,
            "time_seconds": elapsed,
            "files_scanned": total,
            "files_with_findings": files_with_findings,
            "files_skipped": skipped,
            "total_findings": len(all_findings),
            "severity_summary": severity_total,
            "findings": all_findings,
            "file_results": file_results,
            "cross_contract_patterns": cross_contract_patterns,
            "project_stats": {
                "total_contracts": self.project_info.total_contracts,
                "total_loc": sum(sf.loc for sf in self.files.values()),
                "total_functions": sum(
                    sf.functions_count for sf in self.files.values()
                ),
                "total_external_calls": sum(
                    sf.external_calls for sf in self.files.values()
                ),
            },
        }

        # تنسيق الإخراج
        if output_format == "json":
            return {
                "report_json": json.dumps(
                    report, indent=2, ensure_ascii=False, default=str
                )
            }
        elif output_format == "markdown":
            return {"report_markdown": self._format_project_markdown(report), **report}
        elif output_format == "text":
            return {"report_text": self._format_project_text(report), **report}

        return report

    def _analyze_cross_contract(self, findings: List[Dict]) -> List[Dict]:
        """
        تحليل الأنماط المتكررة عبر عدة عقود.
        يكشف المشاكل النظامية (systemic issues) في المشروع.
        """
        patterns = defaultdict(list)

        for f in findings:
            # تجميع حسب نوع الثغرة
            title = f.get("title", f.get("text", ""))
            vuln_type = self._categorize_finding(title)
            patterns[vuln_type].append(
                {
                    "file": f.get("file", "?"),
                    "line": f.get("line", "?"),
                    "severity": f.get("severity", "?"),
                }
            )

        cross_patterns = []
        for vuln_type, occurrences in patterns.items():
            if len(occurrences) > 1:
                files_affected = list(set(o["file"] for o in occurrences))
                cross_patterns.append(
                    {
                        "vulnerability_type": vuln_type,
                        "occurrences": len(occurrences),
                        "files_affected": files_affected,
                        "systemic": len(files_affected) > 1,
                        "recommendation": self._get_systemic_recommendation(
                            vuln_type, len(files_affected)
                        ),
                    }
                )

        # ترتيب حسب عدد التكرارات
        cross_patterns.sort(key=lambda x: x["occurrences"], reverse=True)
        return cross_patterns

    def _categorize_finding(self, title: str) -> str:
        """تصنيف ثغرة حسب نوعها."""
        title_lower = title.lower()
        categories = {
            "Reentrancy": ["reentrancy", "reentrant", "re-entrancy"],
            "Access Control": [
                "access",
                "onlyowner",
                "unauthorized",
                "permission",
                "tx.origin",
            ],
            "Integer Overflow": ["overflow", "underflow", "integer"],
            "Unchecked Call": ["unchecked", "low-level call", "return value"],
            "Timestamp Dependence": ["timestamp", "block.timestamp", "block.number"],
            "Delegatecall": ["delegatecall", "proxy"],
            "Flash Loan": ["flash", "flashloan"],
            "Price Manipulation": ["oracle", "price", "manipulation", "twap"],
            "Front-Running": ["frontrun", "front-run", "sandwich", "mev"],
            "Denial of Service": ["dos", "denial", "gas limit", "loop"],
            "Centralization Risk": ["centralization", "admin", "owner", "single point"],
            "Missing Events": ["event", "emit", "log"],
        }
        for category, keywords in categories.items():
            if any(kw in title_lower for kw in keywords):
                return category
        return "Other"

    def _get_systemic_recommendation(self, vuln_type: str, file_count: int) -> str:
        """توصية للمشاكل النظامية."""
        recs = {
            "Reentrancy": f"تم اكتشاف Reentrancy في {file_count} ملف. يُنصح بتطبيق نمط Checks-Effects-Interactions في كل المشروع أو استخدام OpenZeppelin ReentrancyGuard.",
            "Access Control": f"مشاكل صلاحيات في {file_count} ملف. يُنصح بتطبيق نظام أدوار موحد (AccessControl) من OpenZeppelin.",
            "Unchecked Call": f"نداءات غير مفحوصة في {file_count} ملف. استخدم Address.sendValue() أو تحقق من القيمة المرجعة دائماً.",
            "Timestamp Dependence": f"اعتماد على الوقت في {file_count} ملف. يُنصح باستخدام Chainlink Keepers أو بدائل آمنة.",
            "Integer Overflow": f"مخاطر تجاوز رقمي في {file_count} ملف. تأكد من استخدام Solidity 0.8+ مع الفحص التلقائي.",
        }
        return recs.get(
            vuln_type, f"تم اكتشاف {vuln_type} في {file_count} ملف. يُنصح بمراجعة شاملة."
        )

    # ═══════════════════════════════════════════════════
    #  تنسيق التقارير — Report Formatting
    # ═══════════════════════════════════════════════════

    def _format_project_text(self, report: Dict) -> str:
        """تنسيق تقرير المشروع كنص عادي."""
        lines = []
        lines.append("╔" + "═" * 62 + "╗")
        lines.append("║   🛡️  AGL Smart Contract Project Security Report              ║")
        lines.append("╚" + "═" * 62 + "╝")
        lines.append("")
        lines.append(f"  📁 Project:    {report.get('project_root', 'N/A')}")
        lines.append(f"  🔧 Type:       {report.get('project_type', 'N/A')}")
        lines.append(f"  ⚡ Mode:       {report.get('scan_mode', 'N/A')}")
        lines.append(f"  ⏱️  Time:       {report.get('time_seconds', 0)}s")
        lines.append(
            f"  📄 Files:      {report.get('files_scanned', 0)} scanned, "
            f"{report.get('files_with_findings', 0)} with findings"
        )
        lines.append("")

        # إحصائيات المشروع
        stats = report.get("project_stats", {})
        lines.append("  📊 Project Stats:")
        lines.append(f"     Contracts:       {stats.get('total_contracts', 0)}")
        lines.append(f"     Lines of Code:   {stats.get('total_loc', 0):,}")
        lines.append(f"     Functions:       {stats.get('total_functions', 0)}")
        lines.append(f"     External Calls:  {stats.get('total_external_calls', 0)}")
        lines.append("")

        # ملخص الخطورة
        summary = report.get("severity_summary", {})
        lines.append("  🎯 Severity Summary:")
        lines.append(f"     🔴 CRITICAL: {summary.get('CRITICAL', 0)}")
        lines.append(f"     🟠 HIGH:     {summary.get('HIGH', 0)}")
        lines.append(f"     🟡 MEDIUM:   {summary.get('MEDIUM', 0)}")
        lines.append(f"     🔵 LOW:      {summary.get('LOW', 0)}")
        lines.append(f"     📋 TOTAL:    {report.get('total_findings', 0)}")
        lines.append("")

        # النتائج حسب الملف
        findings = report.get("findings", [])
        if findings:
            lines.append("─" * 64)
            lines.append("  📋 Findings by File:")
            lines.append("─" * 64)

            # تجميع حسب الملف
            by_file = defaultdict(list)
            for f in findings:
                by_file[f.get("file", "?")].append(f)

            for fname, file_findings in by_file.items():
                lines.append(f"\n  📄 {fname} ({len(file_findings)} findings):")
                for f in file_findings:
                    sev = f.get("severity", "?").upper()
                    title = f.get("title", f.get("text", "Unknown"))
                    line_num = f.get("line", "?")
                    lines.append(f"     [{sev}] L{line_num}: {title}")

        # الأنماط عبر العقود
        cross = report.get("cross_contract_patterns", [])
        if cross:
            lines.append("")
            lines.append("─" * 64)
            lines.append("  ⚠️  Cross-Contract Patterns (Systemic Issues):")
            lines.append("─" * 64)
            for p in cross:
                systemic_tag = " [SYSTEMIC]" if p.get("systemic") else ""
                lines.append(f"\n  🔄 {p['vulnerability_type']}{systemic_tag}")
                lines.append(
                    f"     Occurrences: {p['occurrences']} across {len(p['files_affected'])} files"
                )
                lines.append(f"     Files: {', '.join(p['files_affected'][:5])}")
                if p.get("recommendation"):
                    lines.append(f"     💡 {p['recommendation']}")

        lines.append("")
        lines.append("═" * 64)
        return "\n".join(lines)

    def _format_project_markdown(self, report: Dict) -> str:
        """تنسيق تقرير المشروع كـ Markdown."""
        lines = []
        lines.append("# 🛡️ AGL Smart Contract Project Security Report\n")

        # معلومات المشروع
        lines.append("## Project Info\n")
        lines.append(f"| Property | Value |")
        lines.append(f"|----------|-------|")
        lines.append(f"| Project Root | `{report.get('project_root', 'N/A')}` |")
        lines.append(f"| Project Type | {report.get('project_type', 'N/A')} |")
        lines.append(f"| Scan Mode | {report.get('scan_mode', 'N/A')} |")
        lines.append(f"| Scan Time | {report.get('time_seconds', 0)}s |")
        lines.append(f"| Files Scanned | {report.get('files_scanned', 0)} |")
        lines.append(
            f"| Files with Findings | {report.get('files_with_findings', 0)} |"
        )
        lines.append("")

        # إحصائيات
        stats = report.get("project_stats", {})
        lines.append("## Project Statistics\n")
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Total Contracts | {stats.get('total_contracts', 0)} |")
        lines.append(f"| Lines of Code | {stats.get('total_loc', 0):,} |")
        lines.append(f"| Functions | {stats.get('total_functions', 0)} |")
        lines.append(f"| External Calls | {stats.get('total_external_calls', 0)} |")
        lines.append("")

        # ملخص الخطورة
        summary = report.get("severity_summary", {})
        lines.append("## Severity Summary\n")
        lines.append(f"| Severity | Count |")
        lines.append(f"|----------|-------|")
        lines.append(f"| 🔴 CRITICAL | **{summary.get('CRITICAL', 0)}** |")
        lines.append(f"| 🟠 HIGH | **{summary.get('HIGH', 0)}** |")
        lines.append(f"| 🟡 MEDIUM | **{summary.get('MEDIUM', 0)}** |")
        lines.append(f"| 🔵 LOW | **{summary.get('LOW', 0)}** |")
        lines.append(f"| **TOTAL** | **{report.get('total_findings', 0)}** |")
        lines.append("")

        # النتائج
        findings = report.get("findings", [])
        if findings:
            lines.append("## Detailed Findings\n")

            by_file = defaultdict(list)
            for f in findings:
                by_file[f.get("file", "?")].append(f)

            for fname, file_findings in by_file.items():
                lines.append(f"### 📄 `{fname}` ({len(file_findings)} findings)\n")
                lines.append(f"| # | Severity | Line | Finding |")
                lines.append(f"|---|----------|------|---------|")
                for i, f in enumerate(file_findings, 1):
                    sev = f.get("severity", "?").upper()
                    title = f.get("title", f.get("text", "Unknown"))
                    line_num = f.get("line", "?")
                    icon = {
                        "CRITICAL": "🔴",
                        "HIGH": "🟠",
                        "MEDIUM": "🟡",
                        "LOW": "🔵",
                    }.get(sev, "⚪")
                    lines.append(f"| {i} | {icon} {sev} | {line_num} | {title} |")
                lines.append("")

        # الأنماط عبر العقود
        cross = report.get("cross_contract_patterns", [])
        if cross:
            lines.append("## ⚠️ Cross-Contract Patterns\n")
            lines.append(
                "These patterns appear across multiple files, indicating systemic issues:\n"
            )
            for p in cross:
                systemic = " **[SYSTEMIC]**" if p.get("systemic") else ""
                lines.append(f"### {p['vulnerability_type']}{systemic}\n")
                lines.append(f"- **Occurrences:** {p['occurrences']}")
                lines.append(f"- **Files affected:** {len(p['files_affected'])}")
                for f in p["files_affected"][:10]:
                    lines.append(f"  - `{f}`")
                if p.get("recommendation"):
                    lines.append(f"\n> 💡 **Recommendation:** {p['recommendation']}\n")

        # ملخص الملفات
        file_results = report.get("file_results", {})
        if file_results:
            lines.append("## File-by-File Summary\n")
            lines.append(f"| File | Findings | LOC | Contracts |")
            lines.append(f"|------|----------|-----|-----------|")
            for fname, fr in sorted(
                file_results.items(),
                key=lambda x: x[1].get("findings_count", 0),
                reverse=True,
            ):
                count = fr.get("findings_count", 0)
                loc = fr.get("loc", 0)
                contracts = ", ".join(fr.get("contracts", []))
                icon = (
                    "🔴"
                    if count > 5
                    else "🟠" if count > 2 else "🟡" if count > 0 else "✅"
                )
                lines.append(f"| {icon} `{fname}` | {count} | {loc} | {contracts} |")

        lines.append("\n---\n*Generated by AGL Security Tool v1.0.0*")
        return "\n".join(lines)

    # ═══════════════════════════════════════════════════
    #  أدوات مساعدة — Utilities
    # ═══════════════════════════════════════════════════

    def _to_relative(self, abs_path: str) -> str:
        """تحويل مسار مطلق إلى نسبي."""
        try:
            return os.path.relpath(abs_path, self.project_path)
        except ValueError:
            return abs_path
