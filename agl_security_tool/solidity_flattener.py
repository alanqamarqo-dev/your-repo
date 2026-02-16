"""
AGL Security — Solidity Import Flattener + Inheritance Resolver
================================================================
يحل مشكلة العقود متعددة الملفات:
  1. Import Resolution: يتبع كل import ويجمع الكود
  2. Flattening: يدمج كل الملفات في ملف واحد موحد
  3. Inheritance Chain: يبني شجرة التوارث الكاملة
  4. Context Injection: يزود المحلل بسياق الوالد (state vars + functions)

No external dependencies — works with pure Python.

Usage:
    flattener = SolidityFlattener("d:/project")
    flat_source = flattener.flatten("contracts/Token.sol")
    chain = flattener.get_inheritance_chain("Token")
    context = flattener.get_full_context("Token")
"""

import os
import re
from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from collections import defaultdict


# ═══════════════════════════════════════════════════════
#  نماذج البيانات
# ═══════════════════════════════════════════════════════


@dataclass
class ContractDef:
    """تعريف عقد واحد مع كل تفاصيله."""

    name: str
    file_path: str  # المسار الكامل
    kind: str = "contract"  # contract / interface / library / abstract
    parents: List[str] = field(default_factory=list)  # is X, Y, Z
    state_vars: List[Dict] = field(
        default_factory=list
    )  # [{name, type, visibility, line}]
    functions: List[Dict] = field(
        default_factory=list
    )  # [{name, visibility, modifiers, params, returns, body_start, body_end, line}]
    modifiers: List[Dict] = field(default_factory=list)  # [{name, params, line}]
    events: List[Dict] = field(default_factory=list)  # [{name, params, line}]
    structs: List[str] = field(default_factory=list)
    enums: List[str] = field(default_factory=list)
    usings: List[str] = field(default_factory=list)  # using SafeMath for uint256
    source_start: int = 0  # السطر الأول
    source_end: int = 0  # السطر الأخير
    raw_source: str = ""  # الكود الخام


@dataclass
class FlattenResult:
    """نتيجة عملية الدمج."""

    source: str  # الكود المدمج
    files_included: List[str] = field(default_factory=list)
    contracts_found: List[str] = field(default_factory=list)
    unresolved_imports: List[str] = field(default_factory=list)
    total_lines: int = 0
    pragma: str = ""


@dataclass
class InheritanceContext:
    """السياق الكامل لعقد مع كل التوارث."""

    contract_name: str
    full_chain: List[str] = field(
        default_factory=list
    )  # [contract, parent1, grandparent, ...]
    all_state_vars: List[Dict] = field(default_factory=list)  # من كل السلسلة
    all_functions: List[Dict] = field(default_factory=list)  # من كل السلسلة
    all_modifiers: List[Dict] = field(default_factory=list)
    all_events: List[Dict] = field(default_factory=list)
    overridden_functions: Dict[str, str] = field(
        default_factory=dict
    )  # func_name -> contract that overrides
    virtual_functions: List[str] = field(default_factory=list)
    has_external_calls: bool = False
    has_delegatecall: bool = False
    has_selfdestruct: bool = False
    total_state_slots: int = 0


# ═══════════════════════════════════════════════════════
#  Regex patterns
# ═══════════════════════════════════════════════════════

_RE_IMPORT = re.compile(
    r"import\s+"
    r"(?:"
    r"(?:\{[^}]*\}\s+from\s+)?"
    r"|"
    r"(?:\*\s+as\s+\w+\s+from\s+)?"
    r"|"
    r"(?:\w+\s+from\s+)?"
    r")?"
    r'["\']([^"\']+)["\']'
    r"\s*;"
)

_RE_PRAGMA = re.compile(r"^(\s*pragma\s+[^;]+;)", re.MULTILINE)
_RE_LICENSE = re.compile(r"^(\s*//\s*SPDX-License-Identifier:\s*.+)$", re.MULTILINE)

_RE_CONTRACT = re.compile(
    r"(abstract\s+)?(?:contract|interface|library)\s+(\w+)"
    r"(?:\s+is\s+([^{]+))?"
    r"\s*\{"
)

_RE_STATE_VAR = re.compile(
    r"^\s+"
    r"(mapping\s*\([^)]+\)|[\w\[\]]+(?:\s*\[\s*\])?)"  # type
    r"\s+"
    r"(public|private|internal|external|immutable|constant|override)*"
    r"\s*"
    r"((?:public|private|internal|external|immutable|constant|override)\s+)*"
    r"(\w+)"  # name
    r"\s*(?:[=;])",
    re.MULTILINE,
)

_RE_FUNCTION = re.compile(
    r"function\s+(\w+)\s*\(([^)]*)\)"  # name + params
    r"([^{;]*)"  # modifiers block
    r"(?:\{|;)",  # body start or interface
    re.DOTALL,
)

_RE_MODIFIER_DEF = re.compile(r"modifier\s+(\w+)\s*\(([^)]*)\)", re.DOTALL)

_RE_EVENT_DEF = re.compile(r"event\s+(\w+)\s*\(([^)]*)\)\s*;")

_RE_USING = re.compile(r"using\s+(\w+)\s+for\s+([^;]+);")

_RE_STRUCT = re.compile(r"struct\s+(\w+)\s*\{")
_RE_ENUM = re.compile(r"enum\s+(\w+)\s*\{")


# ═══════════════════════════════════════════════════════
#  محلل العقود — Contract Parser
# ═══════════════════════════════════════════════════════


class SolidityContractParser:
    """يستخرج تعريفات العقود والدوال والمتغيرات من ملف Solidity."""

    def parse_file(self, file_path: str) -> List[ContractDef]:
        """تحليل ملف واستخراج كل العقود المعرّفة فيه."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                source = f.read()
        except Exception:
            return []
        return self.parse_source(source, file_path)

    def parse_source(self, source: str, file_path: str = "") -> List[ContractDef]:
        """تحليل كود مصدري واستخراج العقود."""
        contracts = []
        lines = source.split("\n")

        # إيجاد كل تعريفات العقود مع حدودها
        for m in _RE_CONTRACT.finditer(source):
            is_abstract = bool(m.group(1))
            name = m.group(2)
            parents_str = m.group(3)

            # تحديد النوع
            before = source[max(0, m.start() - 20) : m.start()]
            if "interface" in before or "interface" in m.group(0):
                kind = "interface"
            elif "library" in before or "library" in m.group(0):
                kind = "library"
            elif is_abstract:
                kind = "abstract"
            else:
                kind = "contract"

            # كشف النوع من النص الكامل
            full_match = m.group(0)
            if full_match.lstrip().startswith("interface"):
                kind = "interface"
            elif full_match.lstrip().startswith("library"):
                kind = "library"

            # استخراج الآباء
            parents = []
            if parents_str:
                parents = [
                    p.strip().split("(")[0].strip()
                    for p in parents_str.split(",")
                    if p.strip()
                ]

            # حساب أرقام الأسطر
            line_start = source[: m.start()].count("\n") + 1

            # إيجاد نهاية العقد (matching brace)
            body_start = m.end() - 1  # position of opening {
            body_end = self._find_matching_brace(source, body_start)
            line_end = source[:body_end].count("\n") + 1 if body_end > 0 else line_start

            contract_source = source[m.start() : body_end + 1] if body_end > 0 else ""

            cdef = ContractDef(
                name=name,
                file_path=file_path,
                kind=kind,
                parents=parents,
                source_start=line_start,
                source_end=line_end,
                raw_source=contract_source,
            )

            # استخراج التفاصيل من جسم العقد
            if contract_source:
                self._extract_details(cdef, contract_source, line_start)

            contracts.append(cdef)

        return contracts

    def _find_matching_brace(self, source: str, start: int) -> int:
        """إيجاد القوس المقابل — يتعامل مع strings + comments."""
        depth = 0
        i = start
        in_string = False
        string_char = ""
        in_line_comment = False
        in_block_comment = False

        while i < len(source):
            c = source[i]

            if in_line_comment:
                if c == "\n":
                    in_line_comment = False
            elif in_block_comment:
                if c == "*" and i + 1 < len(source) and source[i + 1] == "/":
                    in_block_comment = False
                    i += 1
            elif in_string:
                if c == "\\":
                    i += 1  # skip escaped
                elif c == string_char:
                    in_string = False
            else:
                if c == "/" and i + 1 < len(source):
                    if source[i + 1] == "/":
                        in_line_comment = True
                        i += 1
                    elif source[i + 1] == "*":
                        in_block_comment = True
                        i += 1
                elif c in ('"', "'"):
                    in_string = True
                    string_char = c
                elif c == "{":
                    depth += 1
                elif c == "}":
                    depth -= 1
                    if depth == 0:
                        return i
            i += 1
        return -1

    def _extract_details(self, cdef: ContractDef, source: str, base_line: int):
        """استخراج الدوال والمتغيرات والأحداث من جسم العقد."""

        # Functions
        for m in _RE_FUNCTION.finditer(source):
            name = m.group(1)
            params = m.group(2).strip()
            mods_block = m.group(3).strip()
            line = base_line + source[: m.start()].count("\n")

            visibility = "internal"
            for v in ("public", "external", "internal", "private"):
                if v in mods_block:
                    visibility = v
                    break

            is_view = "view" in mods_block or "pure" in mods_block
            is_payable = "payable" in mods_block
            is_virtual = "virtual" in mods_block
            is_override = "override" in mods_block

            # استخراج returns
            returns_match = re.search(r"returns\s*\(([^)]*)\)", mods_block)
            returns = returns_match.group(1).strip() if returns_match else ""

            cdef.functions.append(
                {
                    "name": name,
                    "params": params,
                    "visibility": visibility,
                    "is_view": is_view,
                    "is_payable": is_payable,
                    "is_virtual": is_virtual,
                    "is_override": is_override,
                    "returns": returns,
                    "line": line,
                    "from_contract": cdef.name,
                }
            )

        # State Variables — فقط في المستوى الأول من القوسين
        # نحتاج لتحليل أكثر دقة — فقط الأسطر خارج الدوال
        outer_lines = self._get_outer_lines(source)
        for line_text in outer_lines:
            m = _RE_STATE_VAR.match(line_text)
            if m:
                var_type = m.group(1).strip()
                var_name = m.group(4) if m.group(4) else ""
                if var_name and not var_name.startswith(
                    ("function", "event", "modifier", "struct", "enum")
                ):
                    visibility = "internal"
                    mods = (m.group(2) or "") + " " + (m.group(3) or "")
                    for v in ("public", "private", "internal", "external"):
                        if v in mods:
                            visibility = v
                            break

                    cdef.state_vars.append(
                        {
                            "name": var_name,
                            "type": var_type,
                            "visibility": visibility,
                            "immutable": "immutable" in mods,
                            "constant": "constant" in mods,
                            "from_contract": cdef.name,
                        }
                    )

        # Modifiers
        for m in _RE_MODIFIER_DEF.finditer(source):
            line = base_line + source[: m.start()].count("\n")
            cdef.modifiers.append(
                {
                    "name": m.group(1),
                    "params": m.group(2).strip(),
                    "line": line,
                    "from_contract": cdef.name,
                }
            )

        # Events
        for m in _RE_EVENT_DEF.finditer(source):
            line = base_line + source[: m.start()].count("\n")
            cdef.events.append(
                {
                    "name": m.group(1),
                    "params": m.group(2).strip(),
                    "line": line,
                    "from_contract": cdef.name,
                }
            )

        # Using
        for m in _RE_USING.finditer(source):
            cdef.usings.append(f"{m.group(1)} for {m.group(2).strip()}")

        # Structs & Enums
        cdef.structs = _RE_STRUCT.findall(source)
        cdef.enums = _RE_ENUM.findall(source)

    def _get_outer_lines(self, source: str) -> List[str]:
        """استخراج الأسطر في المستوى الأول من القوسين (خارج body الدوال)."""
        lines = []
        depth = 0
        found_first_brace = False

        for line in source.split("\n"):
            # حساب الأقواس
            for c in line:
                if c == "{":
                    depth += 1
                    if not found_first_brace:
                        found_first_brace = True
                elif c == "}":
                    depth -= 1

            # المستوى 1 = داخل العقد، خارج الدوال
            if found_first_brace and depth == 1:
                stripped = line.strip()
                if (
                    stripped
                    and not stripped.startswith("//")
                    and not stripped.startswith("/*")
                ):
                    lines.append(line)

        return lines


# ═══════════════════════════════════════════════════════
#  مسطح الملفات — Flattener
# ═══════════════════════════════════════════════════════


class SolidityFlattener:
    """
    يدمج كل الملفات المستوردة في ملف واحد + يبني خريطة التوارث.
    """

    # مسارات استثناء
    EXCLUDE_DIRS = {
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

    def __init__(
        self, project_root: str = "", remappings: Optional[Dict[str, str]] = None
    ):
        self.project_root = str(Path(project_root).resolve()) if project_root else ""
        self.remappings: Dict[str, str] = remappings or {}
        self._parser = SolidityContractParser()

        # Cache
        self._file_cache: Dict[str, str] = {}  # path -> source
        self._contracts_cache: Dict[str, ContractDef] = {}  # name -> ContractDef
        self._file_contracts: Dict[str, List[ContractDef]] = {}  # path -> [ContractDef]

        # اكتشاف remappings تلقائياً
        if self.project_root:
            self._auto_detect_remappings()

    def _auto_detect_remappings(self):
        """اكتشاف remappings من ملفات المشروع."""
        root = Path(self.project_root)

        # foundry.toml
        foundry_toml = root / "foundry.toml"
        if foundry_toml.exists():
            try:
                content = foundry_toml.read_text(encoding="utf-8")
                # بحث بسيط عن remappings
                in_remappings = False
                for line in content.splitlines():
                    line = line.strip()
                    if line.startswith("remappings"):
                        in_remappings = True
                        continue
                    if in_remappings:
                        if line == "]":
                            break
                        # parse "key=value"
                        m = re.match(r'["\']([^"\']+)=([^"\']+)["\']', line)
                        if m:
                            self.remappings[m.group(1)] = m.group(2)
            except Exception:
                pass

        # remappings.txt
        remap_file = root / "remappings.txt"
        if remap_file.exists():
            try:
                for line in remap_file.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line and "=" in line and not line.startswith("#"):
                        k, v = line.split("=", 1)
                        self.remappings[k.strip()] = v.strip()
            except Exception:
                pass

        # hardhat.config.ts — extract paths from node_modules
        node_modules = root / "node_modules"
        if node_modules.is_dir():
            common = [
                ("@openzeppelin/", str(node_modules / "@openzeppelin") + "/"),
                ("@chainlink/", str(node_modules / "@chainlink") + "/"),
                ("@uniswap/", str(node_modules / "@uniswap") + "/"),
                ("@aave/", str(node_modules / "@aave") + "/"),
                ("solmate/", str(node_modules / "solmate" / "src") + "/"),
            ]
            for k, v in common:
                if os.path.isdir(v.rstrip("/")) and k not in self.remappings:
                    self.remappings[k] = v

        # lib/ (Foundry)
        lib_dir = root / "lib"
        if lib_dir.is_dir():
            for entry in os.listdir(str(lib_dir)):
                full = lib_dir / entry
                if full.is_dir():
                    src = full / "src"
                    contracts = full / "contracts"
                    if src.is_dir():
                        self.remappings.setdefault(f"{entry}/", str(src) + "/")
                    elif contracts.is_dir():
                        self.remappings.setdefault(f"@{entry}/", str(contracts) + "/")

    def flatten(self, file_path: str) -> FlattenResult:
        """
        دمج ملف مع كل استيراداته في ملف واحد.
        يُزيل pragma + license المكررة ويحافظ على ترتيب التبعيات.
        """
        file_path = self._resolve_path(file_path)

        visited: Set[str] = set()
        ordered_sources: List[Tuple[str, str]] = []  # (path, cleaned_source)
        unresolved: List[str] = []
        all_contracts: List[str] = []
        best_pragma = ""

        def _walk(fp: str):
            fp_norm = os.path.normpath(fp)
            if fp_norm in visited:
                return
            visited.add(fp_norm)

            source = self._read_file(fp_norm)
            if source is None:
                unresolved.append(fp_norm)
                return

            # استخراج الاستيرادات أولاً — ثم التبعيات قبل العقد الحالي
            imports = _RE_IMPORT.findall(source)
            for imp in imports:
                resolved = self._resolve_import(imp, fp_norm)
                _walk(resolved)

            # استخراج pragma
            nonlocal best_pragma
            pm = _RE_PRAGMA.search(source)
            if pm and not best_pragma:
                best_pragma = pm.group(1).strip()

            # إزالة import + pragma + license من المصدر
            cleaned = _RE_IMPORT.sub("", source)
            cleaned = _RE_PRAGMA.sub("", cleaned)
            cleaned = _RE_LICENSE.sub("", cleaned)
            cleaned = cleaned.strip()

            if cleaned:
                ordered_sources.append((fp_norm, cleaned))

                # تسجيل العقود
                for m in _RE_CONTRACT.finditer(source):
                    all_contracts.append(m.group(2))

        _walk(file_path)

        # بناء المصدر المدمج
        parts = []
        if best_pragma:
            parts.append(f"// SPDX-License-Identifier: MIT")
            parts.append(best_pragma)
            parts.append("")

        for fp, src in ordered_sources:
            parts.append(f"// ━━━ Source: {os.path.basename(fp)} ━━━")
            parts.append(src)
            parts.append("")

        flat_source = "\n".join(parts)

        return FlattenResult(
            source=flat_source,
            files_included=[fp for fp, _ in ordered_sources],
            contracts_found=all_contracts,
            unresolved_imports=unresolved,
            total_lines=flat_source.count("\n") + 1,
            pragma=best_pragma,
        )

    def get_inheritance_chain(self, contract_name: str) -> List[str]:
        """
        بناء سلسلة التوارث الكاملة (C3 linearization مبسطة).
        يعيد [contract, parent1, parent2, grandparent, ...] مرتبة من الأقرب للأبعد.
        """
        self._ensure_contracts_indexed()

        visited = set()
        chain = []

        def _walk(name: str):
            if name in visited:
                return
            visited.add(name)
            chain.append(name)

            cdef = self._contracts_cache.get(name)
            if cdef:
                for parent in cdef.parents:
                    _walk(parent)

        _walk(contract_name)
        return chain

    def get_full_context(self, contract_name: str) -> InheritanceContext:
        """
        بناء السياق الكامل لعقد — يشمل كل الدوال والمتغيرات الموروثة.
        هذا ما يحتاجه المحلل لفهم عقود كبيرة متعددة الملفات.
        """
        self._ensure_contracts_indexed()

        chain = self.get_inheritance_chain(contract_name)

        ctx = InheritanceContext(
            contract_name=contract_name,
            full_chain=chain,
        )

        seen_funcs = {}  # name -> contract_name (أول من يعرّفها = override)
        seen_vars = set()

        for c_name in chain:
            cdef = self._contracts_cache.get(c_name)
            if not cdef:
                continue

            # Functions
            for func in cdef.functions:
                fname = func["name"]
                if fname not in seen_funcs:
                    seen_funcs[fname] = c_name
                    ctx.all_functions.append(func)
                else:
                    # override — سجّل
                    ctx.overridden_functions[fname] = seen_funcs[fname]

                if func.get("is_virtual"):
                    ctx.virtual_functions.append(fname)

            # State Variables
            for var in cdef.state_vars:
                vname = var["name"]
                if vname not in seen_vars:
                    seen_vars.add(vname)
                    ctx.all_state_vars.append(var)

            # Modifiers
            for mod in cdef.modifiers:
                ctx.all_modifiers.append(mod)

            # Events
            for evt in cdef.events:
                ctx.all_events.append(evt)

            # أعلام الأمان
            raw = cdef.raw_source.lower()
            if ".call{" in raw or ".call(" in raw:
                ctx.has_external_calls = True
            if "delegatecall" in raw:
                ctx.has_delegatecall = True
            if "selfdestruct" in raw or "suicide" in raw:
                ctx.has_selfdestruct = True

        # حساب slots
        ctx.total_state_slots = len(
            [
                v
                for v in ctx.all_state_vars
                if not v.get("constant") and not v.get("immutable")
            ]
        )

        return ctx

    def index_project(self, root: Optional[str] = None):
        """
        فهرسة كل العقود في المشروع — يبني الكاش لاستخدام سريع.
        """
        root = root or self.project_root
        if not root:
            return

        for dirpath, dirnames, filenames in os.walk(root):
            # استبعاد مجلدات البناء
            parts = set(Path(os.path.relpath(dirpath, root)).parts)
            if parts & self.EXCLUDE_DIRS:
                dirnames.clear()
                continue

            for fn in filenames:
                if fn.endswith(".sol"):
                    fp = os.path.join(dirpath, fn)
                    try:
                        contracts = self._parser.parse_file(fp)
                        self._file_contracts[fp] = contracts
                        for c in contracts:
                            self._contracts_cache[c.name] = c
                    except Exception:
                        # تسجيل الملفات الفاشلة بدل التجاهل
                        self._parse_errors = getattr(self, "_parse_errors", [])
                        self._parse_errors.append(fp)

    def _ensure_contracts_indexed(self):
        """التأكد من أن الكاش مبني."""
        if not self._contracts_cache and self.project_root:
            self.index_project()

    def _read_file(self, path: str) -> Optional[str]:
        """قراءة ملف مع كاش."""
        if path in self._file_cache:
            return self._file_cache[path]
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            self._file_cache[path] = content

            # أيضاً parse العقود
            if path not in self._file_contracts:
                contracts = self._parser.parse_source(content, path)
                self._file_contracts[path] = contracts
                for c in contracts:
                    self._contracts_cache[c.name] = c

            return content
        except Exception:
            return None

    def _resolve_path(self, file_path: str) -> str:
        """تحويل مسار نسبي إلى مطلق."""
        p = Path(file_path)
        if p.is_absolute():
            return str(p)
        if self.project_root:
            return str(Path(self.project_root) / p)
        return str(p.resolve())

    def _resolve_import(self, import_path: str, source_file: str) -> str:
        """حل مسار الاستيراد."""
        # 1. مسارات نسبية
        if import_path.startswith("."):
            source_dir = os.path.dirname(source_file)
            resolved = os.path.normpath(os.path.join(source_dir, import_path))
            if os.path.isfile(resolved):
                return resolved
            return resolved

        # 2. Remappings (أطول prefix أولاً)
        for prefix, replacement in sorted(
            self.remappings.items(), key=lambda x: len(x[0]), reverse=True
        ):
            if import_path.startswith(prefix):
                rest = import_path[len(prefix) :]
                # حاول المسار المطلق في replacement
                if os.path.isabs(replacement):
                    resolved = os.path.normpath(os.path.join(replacement, rest))
                else:
                    resolved = os.path.normpath(
                        os.path.join(self.project_root, replacement, rest)
                    )
                if os.path.isfile(resolved):
                    return resolved
                # حاول بدون join
                resolved2 = os.path.normpath(os.path.join(replacement, rest))
                if os.path.isfile(resolved2):
                    return resolved2

        # 3. من جذر المشروع
        if self.project_root:
            candidate = os.path.join(self.project_root, import_path)
            if os.path.isfile(candidate):
                return candidate

            # node_modules
            nm = os.path.join(self.project_root, "node_modules", import_path)
            if os.path.isfile(nm):
                return nm

        return import_path

    def get_contract_def(self, name: str) -> Optional[ContractDef]:
        """جلب تعريف عقد بالاسم."""
        self._ensure_contracts_indexed()
        return self._contracts_cache.get(name)

    def get_all_contracts(self) -> Dict[str, ContractDef]:
        """جلب كل العقود المفهرسة."""
        self._ensure_contracts_indexed()
        return dict(self._contracts_cache)
