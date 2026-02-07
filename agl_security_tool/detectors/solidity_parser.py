"""
AGL Solidity Semantic Parser — المحلل الدلالي
Extracts structured function-level semantics from Solidity source code.

Not a full AST parser — focused on extracting what matters for security analysis:
- State variables and their types
- Function boundaries, visibility, modifiers
- ORDERED operations within each function (reads, writes, calls, requires)
- Cross-function relationships (what calls what, shared state)

Key principle: extract the ORDER of state_write vs external_call.
This is what catches reentrancy, unchecked calls, and CEI violations.
"""

import re
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass, field

from . import (
    ParsedContract, ParsedFunction, StateVar, ModifierInfo,
    Operation, OpType
)


class SoliditySemanticParser:
    """
    محلل دلالي لـ Solidity — يستخرج البنية والعمليات المرتبة.

    Usage:
        parser = SoliditySemanticParser()
        contracts = parser.parse(source_code)
        # contracts[0].functions["withdraw"].operations -> [REQUIRE, EXTERNAL_CALL, STATE_WRITE]
    """

    # ═══════════════════════════════════════════════════
    #  Compiled Regex Patterns (performance)
    # ═══════════════════════════════════════════════════

    # العقود
    _RE_CONTRACT = re.compile(
        r'(?:abstract\s+)?(?:contract|interface|library)\s+(\w+)'
        r'(?:\s+is\s+([\w\s,]+?))?'
        r'\s*\{',
        re.MULTILINE
    )
    _RE_CONTRACT_TYPE = re.compile(r'(abstract\s+contract|contract|interface|library)\s+\w+')

    # متغيرات الحالة
    _RE_STATE_VAR = re.compile(
        r'^\s*(mapping\s*\([^)]+\)|address(?:\s+payable)?|u?int\d*|bytes\d*|string|bool'
        r'|I\w+|IERC\w+|\w+(?:\[\])?)'      # النوع
        r'(?:\s+(public|private|internal|external))?'
        r'(?:\s+(constant|immutable))?'
        r'\s+(\w+)',                            # الاسم
        re.MULTILINE
    )

    # الدوال
    _RE_FUNCTION = re.compile(
        r'function\s+(\w+)\s*\(([^)]*)\)'
        r'((?:\s+(?:public|external|internal|private|view|pure|payable'
        r'|virtual|override|returns\s*\([^)]*\)|\w+(?:\([^)]*\))?))*)'
        r'\s*(?:\{|;)',
        re.MULTILINE | re.DOTALL
    )

    # Constructor, fallback, receive — أنماط خاصة
    _RE_CONSTRUCTOR = re.compile(r'constructor\s*\(([^)]*)\)([^{]*)\{', re.MULTILINE)
    _RE_FALLBACK = re.compile(r'fallback\s*\(\s*\)([^{]*)\{', re.MULTILINE)
    _RE_RECEIVE = re.compile(r'receive\s*\(\s*\)([^{]*)\{', re.MULTILINE)

    # Modifiers
    _RE_MODIFIER = re.compile(r'modifier\s+(\w+)\s*(?:\(([^)]*)\))?\s*\{', re.MULTILINE)

    # Pragma
    _RE_PRAGMA = re.compile(r'pragma\s+solidity\s+([^;]+);')
    _RE_LICENSE = re.compile(r'//\s*SPDX-License-Identifier:\s*(.+)')

    # Using for
    _RE_USING = re.compile(r'using\s+(\w+)\s+for\s+([^;]+);')

    # Events
    _RE_EVENT = re.compile(r'event\s+(\w+)\s*\([^)]*\)')

    # ═══ عمليات داخل الدوال ═══

    # External calls
    _RE_EXT_CALL_VALUE = re.compile(
        r'(\w[\w.\[\]]*)\s*\.\s*call\s*\{[^}]*value\s*:',
    )
    _RE_EXT_CALL_PLAIN = re.compile(
        r'(\w[\w.\[\]]*)\s*\.\s*(call|send)\s*[\({]',
    )
    _RE_TRANSFER = re.compile(
        r'(\w[\w.\[\]]*)\s*\.\s*transfer\s*\(',
    )
    _RE_DELEGATECALL = re.compile(
        r'(\w[\w.\[\]]*)\s*\.\s*delegatecall\s*[\({]',
    )
    _RE_STATICCALL = re.compile(
        r'(\w[\w.\[\]]*)\s*\.\s*staticcall\s*[\({]',
    )

    # ERC20 calls
    _RE_ERC20_TRANSFER = re.compile(
        r'(\w[\w.\[\]]*)\s*\.\s*(transfer|transferFrom|safeTransfer|safeTransferFrom'
        r'|approve|safeApprove)\s*\(',
    )

    # Internal calls
    _RE_INTERNAL_CALL = re.compile(
        r'(?<!\.)(?<!\w)(\w+)\s*\(',
    )

    # State writes — assignment to state variable
    # Catches: var = ..., var += ..., var -= ..., mapping[k] = ..., s.field = ...
    _RE_ASSIGNMENT = re.compile(
        r'([\w.\[\]]+)\s*(?:=|\+=|-=|\*=|/=|%=|&=|\|=|\^=)',
    )

    # Require / assert / revert
    _RE_REQUIRE = re.compile(r'require\s*\((.+?)(?:,\s*["\'].*?["\'])?\s*\)', re.DOTALL)
    _RE_ASSERT = re.compile(r'assert\s*\((.+?)\)', re.DOTALL)
    _RE_REVERT = re.compile(r'revert\s+\w*\s*\(', re.DOTALL)
    _RE_IF_REVERT = re.compile(r'if\s*\((.+?)\)\s*revert', re.DOTALL)

    # Emit
    _RE_EMIT = re.compile(r'emit\s+(\w+)\s*\(')

    # Selfdestruct
    _RE_SELFDESTRUCT = re.compile(r'selfdestruct\s*\(')

    # Loops
    _RE_FOR = re.compile(r'for\s*\(')
    _RE_WHILE = re.compile(r'while\s*\(')

    # Assembly
    _RE_ASSEMBLY = re.compile(r'assembly\s*\{')

    # abi.encodePacked
    _RE_ENCODE_PACKED = re.compile(r'abi\.encodePacked\s*\(')

    # Array push
    _RE_ARRAY_PUSH = re.compile(r'(\w[\w.\[\]]*)\s*\.push\s*\(')

    # Mapping access pattern
    _RE_MAPPING_ACCESS = re.compile(r'(\w+)\s*\[')

    # Reentrancy guard patterns
    _REENTRANCY_MODS = {'nonReentrant', 'nonreentrant', 'noReentrant', 'lock', 'mutex'}

    # Access control patterns
    _ACCESS_MODS = {'onlyOwner', 'onlyAdmin', 'onlyRole', 'onlyGovernance',
                    'onlyMinter', 'onlyOperator', 'onlyAuthorized',
                    'whenNotPaused', 'whenPaused', 'onlyProxy', 'onlyInitializing'}
    _ACCESS_CHECKS = {'msg.sender ==', 'msg.sender!=', '_checkOwner()', '_checkRole(',
                      'hasRole(', 'isOwner(', 'isAdmin(', 'require(msg.sender'}

    def parse(self, source: str, file_path: str = "") -> List[ParsedContract]:
        """
        تحليل كود Solidity واستخراج كل العقود بمعلومات دلالية كاملة.

        Args:
            source: كود Solidity الخام
            file_path: مسار الملف (اختياري، للتقارير)

        Returns:
            قائمة العقود المحللة
        """
        # تنظيف التعليقات مع الحفاظ على أرقام الأسطر
        cleaned = self._strip_comments(source)
        lines = source.splitlines()

        # استخراج معلومات عامة
        pragma = ""
        license_id = ""
        m = self._RE_PRAGMA.search(source)
        if m:
            pragma = m.group(1).strip()
        m = self._RE_LICENSE.search(source)
        if m:
            license_id = m.group(1).strip()

        # استخراج العقود
        contracts = []
        for match in self._RE_CONTRACT.finditer(cleaned):
            name = match.group(1)
            inherits_raw = match.group(2) or ""
            inherits = [i.strip() for i in inherits_raw.split(',') if i.strip()]
            contract_start = source[:match.start()].count('\n') + 1

            # تحديد نوع العقد
            type_match = self._RE_CONTRACT_TYPE.search(match.group(0))
            ctype = "contract"
            if type_match:
                t = type_match.group(1)
                if "interface" in t:
                    ctype = "interface"
                elif "library" in t:
                    ctype = "library"
                elif "abstract" in t:
                    ctype = "abstract"

            # استخراج جسم العقد
            body_start = match.end()
            body_end = self._find_matching_brace(cleaned, body_start - 1)
            contract_body = cleaned[body_start:body_end] if body_end > 0 else cleaned[body_start:]
            contract_body_raw = source[body_start:body_end] if body_end > 0 else source[body_start:]
            contract_end_line = source[:body_end].count('\n') + 1 if body_end > 0 else len(lines)

            contract = ParsedContract(
                name=name,
                contract_type=ctype,
                inherits=inherits,
                pragma=pragma,
                license=license_id,
                line_start=contract_start,
                line_end=contract_end_line,
                source_file=file_path,
            )

            # استخراج إصدار Solidity
            contract.solidity_version = self._extract_version(pragma)
            contract.uses_safe_math = "SafeMath" in source
            contract.is_upgradeable = any(
                p in " ".join(inherits).lower()
                for p in ["upgradeable", "initializable", "uupsupgradeable", "proxy"]
            )

            # using X for Y
            for um in self._RE_USING.finditer(contract_body):
                contract.using_for.append({"library": um.group(1), "type": um.group(2).strip()})

            # Events
            contract.events = self._RE_EVENT.findall(contract_body)

            # State variables
            contract.state_vars = self._extract_state_vars(contract_body, contract_start)

            # Modifiers
            contract.modifiers = self._extract_modifiers(contract_body, contract_start)

            # Functions
            contract.functions = self._extract_functions(
                contract_body, contract_body_raw, contract_start, contract.state_vars,
                contract_modifiers=contract.modifiers
            )

            contracts.append(contract)

        return contracts

    # ═══════════════════════════════════════════════════
    #  استخراج متغيرات الحالة
    # ═══════════════════════════════════════════════════

    def _extract_state_vars(self, body: str, offset: int) -> Dict[str, StateVar]:
        """استخراج متغيرات الحالة من جسم العقد."""
        state_vars = {}

        # نستخرج سطراً بسطر قبل أول دالة/modifier/event
        first_func = None
        for m in re.finditer(r'(?:function|modifier|constructor|event|receive|fallback)\s', body):
            first_func = m.start()
            break

        var_section = body[:first_func] if first_func else body

        for match in self._RE_STATE_VAR.finditer(var_section):
            var_type = match.group(1).strip()
            visibility = match.group(2) or "internal"
            qualifier = match.group(3) or ""
            var_name = match.group(4)

            # تخطي أسماء الدوال والأحداث
            if var_name in ('function', 'event', 'modifier', 'constructor', 'returns'):
                continue

            line = var_section[:match.start()].count('\n') + offset

            state_vars[var_name] = StateVar(
                name=var_name,
                var_type=var_type,
                visibility=visibility,
                is_constant="constant" in qualifier,
                is_immutable="immutable" in qualifier,
                is_mapping=var_type.startswith("mapping"),
                is_array="[]" in var_type,
                line=line,
            )

        return state_vars

    # ═══════════════════════════════════════════════════
    #  استخراج Modifiers
    # ═══════════════════════════════════════════════════

    def _extract_modifiers(self, body: str, offset: int) -> Dict[str, ModifierInfo]:
        """استخراج modifiers مع تحليل الحماية."""
        modifiers = {}

        for match in self._RE_MODIFIER.finditer(body):
            name = match.group(1)
            params = match.group(2) or ""
            mod_start = match.end()
            mod_end = self._find_matching_brace(body, mod_start - 1)
            mod_body = body[mod_start:mod_end] if mod_end > 0 else ""
            line = body[:match.start()].count('\n') + offset

            modifiers[name] = ModifierInfo(
                name=name,
                params=[p.strip() for p in params.split(',') if p.strip()],
                body=mod_body,
                checks_owner=bool(re.search(r'msg\.sender\s*[!=]=|_checkOwner|isOwner', mod_body)),
                checks_role=bool(re.search(r'hasRole|_checkRole|onlyRole', mod_body)),
                is_reentrancy_guard=bool(re.search(
                    r'_status\s*!=|_locked|_notEntered|_reentrancyGuardEntered|require\(!locked',
                    mod_body
                )) or name.lower() in ('nonreentrant', 'noreentrant', 'lock'),
                is_paused_check=bool(re.search(r'!paused|_requireNotPaused|whenNotPaused', mod_body)),
                line=line,
            )

        return modifiers

    # ═══════════════════════════════════════════════════
    #  استخراج الدوال
    # ═══════════════════════════════════════════════════

    def _extract_functions(self, body: str, raw_body: str,
                           offset: int, state_vars: Dict[str, StateVar],
                           contract_modifiers: Dict = None
                           ) -> Dict[str, ParsedFunction]:
        """استخراج الدوال مع تحليل دلالي كامل."""
        functions = {}
        state_var_names = set(state_vars.keys())

        # ═══ الدوال العادية ═══
        for match in self._RE_FUNCTION.finditer(body):
            func_name = match.group(1)
            params_raw = match.group(2)
            qualifiers = match.group(3) or ""

            # استخراج جسم الدالة
            if match.group(0).rstrip().endswith(';'):
                # دالة بدون جسم (interface)
                continue

            func_start = match.end()
            func_end = self._find_matching_brace(body, func_start - 1)
            func_body = body[func_start:func_end] if func_end > 0 else ""
            raw_func_body = raw_body[func_start:func_end] if func_end > 0 else ""

            line_start = body[:match.start()].count('\n') + offset
            line_end = body[:func_end].count('\n') + offset if func_end > 0 else line_start

            func = self._build_parsed_function(
                func_name, params_raw, qualifiers, func_body, raw_func_body,
                line_start, line_end, state_var_names
            )
            functions[func_name] = func

        # ═══ Constructor ═══
        for match in self._RE_CONSTRUCTOR.finditer(body):
            func_start = match.end()
            func_end = self._find_matching_brace(body, func_start - 1)
            func_body = body[func_start:func_end] if func_end > 0 else ""
            line_start = body[:match.start()].count('\n') + offset

            func = ParsedFunction(
                name="constructor",
                visibility="public",
                line_start=line_start,
                line_end=body[:func_end].count('\n') + offset if func_end > 0 else line_start,
                raw_body=func_body,
                is_constructor=True,
            )
            self._analyze_function_body(func, func_body, state_var_names)
            functions["constructor"] = func

        # ═══ Receive ═══
        for match in self._RE_RECEIVE.finditer(body):
            func_start = match.end()
            func_end = self._find_matching_brace(body, func_start - 1)
            func_body = body[func_start:func_end] if func_end > 0 else ""
            line_start = body[:match.start()].count('\n') + offset

            func = ParsedFunction(
                name="receive",
                visibility="external",
                mutability="payable",
                line_start=line_start,
                raw_body=func_body,
                is_receive=True,
            )
            self._analyze_function_body(func, func_body, state_var_names)
            functions["receive"] = func

        # ═══ Fallback ═══
        for match in self._RE_FALLBACK.finditer(body):
            func_start = match.end()
            func_end = self._find_matching_brace(body, func_start - 1)
            func_body = body[func_start:func_end] if func_end > 0 else ""
            line_start = body[:match.start()].count('\n') + offset

            func = ParsedFunction(
                name="fallback",
                visibility="external",
                line_start=line_start,
                raw_body=func_body,
                is_fallback=True,
            )
            self._analyze_function_body(func, func_body, state_var_names)
            functions["fallback"] = func

        # ═══ تحسين has_access_control بناءً على modifiers العقد ═══
        # إذا الدالة تستخدم modifier مخصص يحتوي على فحص msg_sender
        if contract_modifiers:
            for func in functions.values():
                if func.has_access_control:
                    continue
                for mod_name in func.modifiers:
                    if mod_name in contract_modifiers:
                        mod_info = contract_modifiers[mod_name]
                        if mod_info.checks_owner or mod_info.checks_role:
                            func.has_access_control = True
                            break

        return functions

    def _build_parsed_function(self, name: str, params_raw: str, qualifiers: str,
                                func_body: str, raw_func_body: str,
                                line_start: int, line_end: int,
                                state_var_names: Set[str]) -> ParsedFunction:
        """بناء ParsedFunction من المعلومات المستخرجة."""
        # تحليل الرؤية والتعديل
        visibility = "internal"
        mutability = ""
        modifiers = []

        quals = qualifiers.strip().split()
        reserved = {'public', 'external', 'internal', 'private',
                     'view', 'pure', 'payable', 'virtual', 'override', 'returns'}
        i = 0
        while i < len(quals):
            q = quals[i]
            if q in ('public', 'external', 'internal', 'private'):
                visibility = q
            elif q in ('view', 'pure', 'payable'):
                mutability = q
            elif q in ('virtual', 'override'):
                pass
            elif q == 'returns':
                # skip returns(...) block
                break
            elif q not in reserved and not q.startswith('('):
                modifiers.append(q)
            i += 1

        # تحليل المعاملات
        parameters = self._parse_params(params_raw)

        func = ParsedFunction(
            name=name,
            visibility=visibility,
            mutability=mutability,
            modifiers=modifiers,
            parameters=parameters,
            line_start=line_start,
            line_end=line_end,
            raw_body=raw_func_body,
            is_initializer=name in ('initialize', 'initializer', '__init__'),
        )

        # تحليل الجسم
        self._analyze_function_body(func, func_body, state_var_names)

        return func

    def _parse_params(self, raw: str) -> List[Dict]:
        """تحليل معاملات الدالة."""
        params = []
        if not raw.strip():
            return params
        for part in raw.split(','):
            part = part.strip()
            tokens = part.split()
            if len(tokens) >= 2:
                p_type = tokens[0]
                p_name = tokens[-1]
                params.append({"name": p_name, "type": p_type})
            elif len(tokens) == 1:
                params.append({"name": "", "type": tokens[0]})
        return params

    # ═══════════════════════════════════════════════════
    #  تحليل جسم الدالة — Function Body Analysis
    #  هُنا يحدث السحر — تحليل العمليات بالترتيب
    # ═══════════════════════════════════════════════════

    def _analyze_function_body(self, func: ParsedFunction, body: str,
                                state_var_names: Set[str]):
        """
        تحليل جسم الدالة واستخراج العمليات المرتبة.
        هذه هي الدالة الأهم — تحول الكود الخام إلى قائمة عمليات مرتبة.
        """
        if not body.strip():
            return

        operations = []
        in_loop_depth = 0

        # تقسيم الجسم إلى أسطر/عبارات
        statements = self._split_statements(body)

        for stmt_line, stmt_text in statements:
            stripped = stmt_text.strip()
            if not stripped:
                continue

            in_loop = in_loop_depth > 0

            # ═══ Loops ═══
            if self._RE_FOR.match(stripped) or self._RE_WHILE.match(stripped):
                in_loop_depth += 1
                operations.append(Operation(OpType.LOOP_START, stmt_line, raw_text=stripped))
                continue

            # Track brace depth for loop end
            if in_loop_depth > 0 and stripped == '}':
                in_loop_depth -= 1
                if in_loop_depth == 0:
                    operations.append(Operation(OpType.LOOP_END, stmt_line))
                continue

            # ═══ Assembly ═══
            if self._RE_ASSEMBLY.match(stripped):
                operations.append(Operation(OpType.ASSEMBLY, stmt_line, raw_text=stripped))
                continue

            # ═══ Selfdestruct ═══
            if self._RE_SELFDESTRUCT.search(stripped):
                operations.append(Operation(OpType.SELFDESTRUCT, stmt_line, raw_text=stripped))
                func.has_selfdestruct = True
                continue

            # ═══ Require / Assert / Revert ═══
            req_match = self._RE_REQUIRE.search(stripped)
            if req_match:
                condition = req_match.group(1).strip()
                operations.append(Operation(
                    OpType.REQUIRE, stmt_line, target=condition,
                    raw_text=stripped, in_loop=in_loop
                ))
                func.require_checks.append(condition)
                continue

            if self._RE_ASSERT.search(stripped):
                operations.append(Operation(OpType.ASSERT, stmt_line, raw_text=stripped, in_loop=in_loop))
                continue

            if_rev = self._RE_IF_REVERT.search(stripped)
            if if_rev:
                operations.append(Operation(
                    OpType.REQUIRE, stmt_line, target=if_rev.group(1).strip(),
                    raw_text=stripped, in_loop=in_loop
                ))
                continue

            if self._RE_REVERT.search(stripped):
                operations.append(Operation(OpType.REVERT, stmt_line, raw_text=stripped))
                continue

            # ═══ Emit ═══
            emit_match = self._RE_EMIT.search(stripped)
            if emit_match:
                operations.append(Operation(
                    OpType.EMIT, stmt_line, target=emit_match.group(1),
                    raw_text=stripped, in_loop=in_loop
                ))
                continue

            # ═══ Return ═══
            if stripped.startswith('return'):
                operations.append(Operation(OpType.RETURN, stmt_line, raw_text=stripped))
                continue

            # ═══ External calls (ORDER MATTERS — check before assignments) ═══

            # .call{value:...} — sends ETH
            ext_val = self._RE_EXT_CALL_VALUE.search(stripped)
            if ext_val:
                op = Operation(
                    OpType.EXTERNAL_CALL_ETH, stmt_line,
                    target=ext_val.group(1), sends_eth=True,
                    raw_text=stripped, in_loop=in_loop
                )
                operations.append(op)
                func.external_calls.append(op)
                func.sends_eth = True
                # Also check if return value is checked
                if '(bool' not in stripped and 'success' not in stripped.split('=')[0] if '=' in stripped else True:
                    pass  # will be caught by unchecked call detector
                # Check assignment (return value capture)
                self._check_state_assignment(stripped, stmt_line, state_var_names, operations, in_loop)
                continue

            # .transfer(...)
            ext_transfer = self._RE_TRANSFER.search(stripped)
            if ext_transfer:
                op = Operation(
                    OpType.EXTERNAL_CALL_ETH, stmt_line,
                    target=ext_transfer.group(1), sends_eth=True,
                    raw_text=stripped, in_loop=in_loop
                )
                operations.append(op)
                func.external_calls.append(op)
                func.sends_eth = True
                continue

            # .delegatecall
            deleg = self._RE_DELEGATECALL.search(stripped)
            if deleg:
                op = Operation(
                    OpType.DELEGATECALL, stmt_line,
                    target=deleg.group(1),
                    raw_text=stripped, in_loop=in_loop
                )
                operations.append(op)
                func.external_calls.append(op)
                func.has_delegatecall = True
                continue

            # .call / .send (without value)
            ext_plain = self._RE_EXT_CALL_PLAIN.search(stripped)
            if ext_plain and not ext_val:
                op = Operation(
                    OpType.EXTERNAL_CALL, stmt_line,
                    target=ext_plain.group(1),
                    details=ext_plain.group(2),
                    raw_text=stripped, in_loop=in_loop
                )
                operations.append(op)
                func.external_calls.append(op)
                self._check_state_assignment(stripped, stmt_line, state_var_names, operations, in_loop)
                continue

            # .staticcall
            if self._RE_STATICCALL.search(stripped):
                operations.append(Operation(
                    OpType.STATICCALL, stmt_line, raw_text=stripped, in_loop=in_loop
                ))
                continue

            # ERC20 transfers — these are external calls too
            erc = self._RE_ERC20_TRANSFER.search(stripped)
            if erc:
                op = Operation(
                    OpType.EXTERNAL_CALL, stmt_line,
                    target=erc.group(1), details=erc.group(2),
                    raw_text=stripped, in_loop=in_loop
                )
                operations.append(op)
                func.external_calls.append(op)
                self._check_state_assignment(stripped, stmt_line, state_var_names, operations, in_loop)
                continue

            # ═══ Array push (state modification) ═══
            push_match = self._RE_ARRAY_PUSH.search(stripped)
            if push_match:
                var = push_match.group(1).split('[')[0].split('.')[0]
                if var in state_var_names:
                    operations.append(Operation(
                        OpType.STATE_WRITE, stmt_line,
                        target=var, details="push",
                        raw_text=stripped, in_loop=in_loop
                    ))
                    if var not in func.state_writes:
                        func.state_writes.append(var)
                    func.modifies_state = True
                continue

            # ═══ abi.encodePacked ═══
            if self._RE_ENCODE_PACKED.search(stripped):
                operations.append(Operation(
                    OpType.ENCODE_PACKED, stmt_line, raw_text=stripped, in_loop=in_loop
                ))

            # ═══ State writes and reads — assignment operations ═══
            assign_match = self._RE_ASSIGNMENT.search(stripped)
            if assign_match:
                full_var = assign_match.group(1).strip()
                # Extract base variable name
                base_var = full_var.split('[')[0].split('.')[0]

                if base_var in state_var_names:
                    operations.append(Operation(
                        OpType.STATE_WRITE, stmt_line,
                        target=base_var, details=full_var,
                        raw_text=stripped, in_loop=in_loop
                    ))
                    if base_var not in func.state_writes:
                        func.state_writes.append(base_var)
                    func.modifies_state = True

                    # Also check the RHS for state reads
                    rhs = stripped.split('=', 1)[1] if '=' in stripped else ""
                    self._extract_state_reads(rhs, state_var_names, func, operations, stmt_line, in_loop)
                    continue

            # ═══ State reads (non-assignment) ═══
            self._extract_state_reads(stripped, state_var_names, func, operations, stmt_line, in_loop)

            # ═══ Internal calls ═══
            for ic_match in self._RE_INTERNAL_CALL.finditer(stripped):
                callee = ic_match.group(1)
                # Filter out keywords and known types
                if callee not in ('if', 'for', 'while', 'require', 'assert', 'revert',
                                  'emit', 'return', 'uint256', 'uint', 'int', 'bool',
                                  'address', 'bytes', 'string', 'mapping', 'keccak256',
                                  'abi', 'block', 'msg', 'tx', 'type', 'new',
                                  'delete', 'push', 'pop', 'send', 'transfer', 'call'):
                    if callee not in func.internal_calls:
                        func.internal_calls.append(callee)
                    operations.append(Operation(
                        OpType.INTERNAL_CALL, stmt_line,
                        target=callee, raw_text=stripped, in_loop=in_loop
                    ))

        # ═══ حفظ العمليات ═══
        func.operations = operations

        # ═══ حساب الخصائص ═══
        func.has_loops = any(op.op_type == OpType.LOOP_START for op in operations)

        # reentrancy guard
        func.has_reentrancy_guard = any(
            m.lower() in self._REENTRANCY_MODS or m.lower().replace('_', '') in self._REENTRANCY_MODS
            for m in func.modifiers
        )

        # access control
        func.has_access_control = any(
            m in self._ACCESS_MODS or any(m.lower().startswith(a.lower()) for a in self._ACCESS_MODS)
            for m in func.modifiers
        ) or any(
            any(check in req for check in self._ACCESS_CHECKS)
            for req in func.require_checks
        )

    def _check_state_assignment(self, stmt: str, line: int,
                                 state_var_names: Set[str],
                                 operations: List[Operation], in_loop: bool):
        """فحص ما إذا كان السطر يتضمن تعيين لمتغير حالة (بجانب العملية الرئيسية)."""
        # e.g. (bool success, ) = target.call{...}(...)
        # The LHS might assign to a state var
        if '=' in stmt:
            lhs = stmt.split('=')[0]
            for var in state_var_names:
                if var in lhs and '(' not in lhs.split(var)[0][-5:]:
                    operations.append(Operation(
                        OpType.STATE_WRITE, line,
                        target=var, raw_text=stmt, in_loop=in_loop
                    ))

    def _extract_state_reads(self, text: str, state_var_names: Set[str],
                              func: ParsedFunction, operations: List[Operation],
                              line: int, in_loop: bool):
        """استخراج قراءات متغيرات الحالة من نص."""
        for var in state_var_names:
            # تأكد أنه كلمة كاملة (ليس جزء من كلمة أخرى)
            pattern = r'\b' + re.escape(var) + r'\b'
            if re.search(pattern, text):
                if var not in func.state_reads:
                    func.state_reads.append(var)
                operations.append(Operation(
                    OpType.STATE_READ, line,
                    target=var, raw_text=text, in_loop=in_loop
                ))

    # ═══════════════════════════════════════════════════
    #  أدوات مساعدة — Utilities
    # ═══════════════════════════════════════════════════

    def _strip_comments(self, source: str) -> str:
        """حذف التعليقات مع الحفاظ على أرقام الأسطر."""
        result = []
        i = 0
        in_string = False
        string_char = ''

        while i < len(source):
            c = source[i]

            # تتبع الأنماط النصية
            if in_string:
                result.append(c)
                if c == '\\' and i + 1 < len(source):
                    result.append(source[i + 1])
                    i += 2
                    continue
                if c == string_char:
                    in_string = False
                i += 1
                continue

            if c in ('"', "'"):
                in_string = True
                string_char = c
                result.append(c)
                i += 1
                continue

            # تعليق سطر واحد
            if c == '/' and i + 1 < len(source) and source[i + 1] == '/':
                while i < len(source) and source[i] != '\n':
                    result.append(' ')
                    i += 1
                continue

            # تعليق متعدد الأسطر
            if c == '/' and i + 1 < len(source) and source[i + 1] == '*':
                i += 2
                while i + 1 < len(source) and not (source[i] == '*' and source[i + 1] == '/'):
                    result.append('\n' if source[i] == '\n' else ' ')
                    i += 1
                result.append(' ')  # *
                result.append(' ')  # /
                i += 2
                continue

            result.append(c)
            i += 1

        return ''.join(result)

    def _find_matching_brace(self, source: str, start: int) -> int:
        """إيجاد القوس المطابق {}. start يشير إلى الـ { الأولى."""
        if start >= len(source) or source[start] != '{':
            # ابحث عن الـ { التالية
            idx = source.find('{', start)
            if idx == -1:
                return -1
            start = idx

        depth = 0
        i = start
        in_string = False
        string_char = ''

        while i < len(source):
            c = source[i]

            if in_string:
                if c == '\\':
                    i += 2
                    continue
                if c == string_char:
                    in_string = False
                i += 1
                continue

            if c in ('"', "'"):
                in_string = True
                string_char = c
            elif c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    return i

            i += 1

        return -1

    def _split_statements(self, body: str) -> List[Tuple[int, str]]:
        """
        تقسيم جسم الدالة إلى عبارات مع أرقام الأسطر.
        يجمع الأسطر المتعددة التي تنتمي لعبارة واحدة.
        """
        statements = []
        lines = body.splitlines()
        current_stmt = ""
        current_line = 0
        brace_depth = 0
        paren_depth = 0

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped:
                continue

            if not current_stmt:
                current_line = i
                current_stmt = stripped
            else:
                current_stmt += " " + stripped

            # Track depth
            for c in stripped:
                if c == '(':
                    paren_depth += 1
                elif c == ')':
                    paren_depth -= 1
                elif c == '{':
                    brace_depth += 1
                elif c == '}':
                    brace_depth -= 1

            # العبارة مكتملة إذا: ينتهي بـ ; أو { أو } وليس داخل أقواس
            if paren_depth <= 0 and (
                stripped.endswith(';') or stripped.endswith('{') or stripped == '}'
            ):
                statements.append((current_line, current_stmt))
                current_stmt = ""
                paren_depth = 0

        # آخر عبارة غير مكتملة
        if current_stmt:
            statements.append((current_line, current_stmt))

        return statements

    def _extract_version(self, pragma: str) -> str:
        """استخراج رقم الإصدار من pragma."""
        m = re.search(r'(\d+\.\d+\.\d+)', pragma)
        if m:
            return m.group(1)
        m = re.search(r'(\d+\.\d+)', pragma)
        if m:
            return m.group(1)
        return ""
