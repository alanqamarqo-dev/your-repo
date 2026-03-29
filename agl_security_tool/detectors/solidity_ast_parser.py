"""
AGL Solidity AST Parser — المحلل النحوي بالنزول التكراري
Recursive-descent parser that builds a proper AST from a token stream.

Replaces the regex-based SoliditySemanticParser with a real parser that:
  - Handles arbitrary nesting depth (no regex depth limits)
  - Correctly scopes local vs state variables
  - Tracks multi-line expressions as single statements
  - Builds a real AST, then converts to our existing data models

Zero external dependencies.

Architecture:
    Source → SolidityLexer → [Token] → SolidityASTParser → [ASTNode]
    [ASTNode] → ASTSemanticAnalyzer → [ParsedContract]  (same models as before)
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Tuple, Any

from .solidity_lexer import SolidityLexer, Token, TT, _VISIBILITY, _MUTABILITY, _DATA_LOC
from . import (
    ParsedContract, ParsedFunction, StateVar, ModifierInfo,
    Operation, OpType,
)


# ═══════════════════════════════════════════════════════════
#  AST Node Types
# ═══════════════════════════════════════════════════════════

@dataclass
class ASTNode:
    """Base AST node."""
    line: int = 0
    end_line: int = 0


@dataclass
class PragmaNode(ASTNode):
    value: str = ""


@dataclass
class ImportNode(ASTNode):
    path: str = ""


@dataclass
class UsingNode(ASTNode):
    library: str = ""
    target_type: str = ""


@dataclass
class EventNode(ASTNode):
    name: str = ""
    params: List[Dict] = field(default_factory=list)


@dataclass
class ErrorNode(ASTNode):
    name: str = ""


@dataclass
class StructNode(ASTNode):
    name: str = ""
    members: List[Dict] = field(default_factory=list)


@dataclass
class EnumNode(ASTNode):
    name: str = ""
    values: List[str] = field(default_factory=list)


@dataclass
class StateVarNode(ASTNode):
    name: str = ""
    var_type: str = ""
    visibility: str = "internal"
    is_constant: bool = False
    is_immutable: bool = False
    is_mapping: bool = False
    is_array: bool = False
    initializer: str = ""


@dataclass
class ParamNode(ASTNode):
    name: str = ""
    param_type: str = ""
    data_location: str = ""
    indexed: bool = False


@dataclass
class FunctionNode(ASTNode):
    name: str = ""
    params: List[ParamNode] = field(default_factory=list)
    returns: List[ParamNode] = field(default_factory=list)
    visibility: str = "internal"
    mutability: str = ""
    modifiers: List[str] = field(default_factory=list)
    is_virtual: bool = False
    is_override: bool = False
    is_constructor: bool = False
    is_fallback: bool = False
    is_receive: bool = False
    body_tokens: List[Token] = field(default_factory=list)
    raw_body: str = ""


@dataclass
class ModifierNode(ASTNode):
    name: str = ""
    params: List[ParamNode] = field(default_factory=list)
    body_tokens: List[Token] = field(default_factory=list)
    raw_body: str = ""


@dataclass
class ContractNode(ASTNode):
    name: str = ""
    contract_type: str = "contract"  # contract, interface, library, abstract
    inherits: List[str] = field(default_factory=list)
    state_vars: List[StateVarNode] = field(default_factory=list)
    functions: List[FunctionNode] = field(default_factory=list)
    modifiers: List[ModifierNode] = field(default_factory=list)
    events: List[EventNode] = field(default_factory=list)
    errors: List[ErrorNode] = field(default_factory=list)
    structs: List[StructNode] = field(default_factory=list)
    enums: List[EnumNode] = field(default_factory=list)
    using_for: List[UsingNode] = field(default_factory=list)


@dataclass
class SourceUnit(ASTNode):
    """Root AST node — one per file."""
    pragma: str = ""
    license: str = ""
    imports: List[ImportNode] = field(default_factory=list)
    contracts: List[ContractNode] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════
#  Recursive Descent Parser
# ═══════════════════════════════════════════════════════════

class SolidityASTParser:
    """
    Recursive-descent parser for Solidity.
    Converts token stream → AST (SourceUnit).

    Does NOT do type checking or full expression parsing.
    Focus: extract contract structure, function signatures, and
    raw function bodies (as token slices) for semantic analysis.
    """

    def __init__(self, tokens: List[Token], source: str = ""):
        self._tokens = tokens
        self._source = source
        self._pos = 0

    def parse(self) -> SourceUnit:
        """Parse the entire source unit."""
        unit = SourceUnit()
        while not self._at_end():
            saved = self._pos
            if self._check(TT.KW_PRAGMA):
                unit.pragma = self._parse_pragma()
            elif self._check(TT.KW_IMPORT):
                unit.imports.append(self._parse_import())
            elif self._check(TT.KW_ABSTRACT, TT.KW_CONTRACT, TT.KW_INTERFACE, TT.KW_LIBRARY):
                unit.contracts.append(self._parse_contract())
            else:
                self._advance()  # skip unknown top-level tokens
            if self._pos == saved:
                self._advance()  # guard: ensure progress
        return unit

    # ── Contract-level ──

    def _parse_pragma(self) -> str:
        self._expect(TT.KW_PRAGMA)
        parts = []
        while not self._at_end() and not self._check(TT.SEMICOLON):
            parts.append(self._current().value)
            self._advance()
        self._eat(TT.SEMICOLON)
        return " ".join(parts)

    def _parse_import(self) -> ImportNode:
        line = self._current().line
        self._expect(TT.KW_IMPORT)
        path = ""
        while not self._at_end() and not self._check(TT.SEMICOLON):
            if self._check(TT.STRING):
                path = self._current().value
            self._advance()
        self._eat(TT.SEMICOLON)
        return ImportNode(line=line, path=path)

    def _parse_contract(self) -> ContractNode:
        line = self._current().line
        # abstract?
        is_abstract = False
        if self._check(TT.KW_ABSTRACT):
            is_abstract = True
            self._advance()

        # contract/interface/library
        ctype = "contract"
        if self._check(TT.KW_INTERFACE):
            ctype = "interface"
        elif self._check(TT.KW_LIBRARY):
            ctype = "library"
        elif is_abstract:
            ctype = "abstract"
        self._advance()

        # Name
        name = self._expect_ident()

        # Inheritance
        inherits = []
        if self._check(TT.KW_IS):
            self._advance()
            while not self._at_end() and not self._check(TT.LBRACE):
                if self._check(TT.IDENT):
                    inherits.append(self._current().value)
                    self._advance()
                    # Skip constructor arguments in inheritance: Base(arg1, arg2)
                    if self._check(TT.LPAREN):
                        self._skip_balanced(TT.LPAREN, TT.RPAREN)
                elif self._check(TT.COMMA):
                    self._advance()
                else:
                    self._advance()

        contract = ContractNode(
            name=name, contract_type=ctype, inherits=inherits, line=line,
        )

        # Body
        self._expect(TT.LBRACE)
        self._parse_contract_body(contract)
        contract.end_line = self._current().line if not self._at_end() else line
        self._eat(TT.RBRACE)

        return contract

    def _parse_contract_body(self, contract: ContractNode):
        """Parse the inside of a contract { ... }."""
        while not self._at_end() and not self._check(TT.RBRACE):
            saved_pos = self._pos
            tok = self._current()

            if tok.tt == TT.KW_FUNCTION:
                contract.functions.append(self._parse_function())
            elif tok.tt == TT.KW_CONSTRUCTOR:
                contract.functions.append(self._parse_constructor())
            elif tok.tt == TT.KW_RECEIVE:
                contract.functions.append(self._parse_receive())
            elif tok.tt == TT.KW_FALLBACK:
                contract.functions.append(self._parse_fallback())
            elif tok.tt == TT.KW_MODIFIER:
                contract.modifiers.append(self._parse_modifier())
            elif tok.tt == TT.KW_EVENT:
                contract.events.append(self._parse_event())
            elif tok.tt == TT.KW_ERROR:
                contract.errors.append(self._parse_error())
            elif tok.tt == TT.KW_STRUCT:
                contract.structs.append(self._parse_struct())
            elif tok.tt == TT.KW_ENUM:
                contract.enums.append(self._parse_enum())
            elif tok.tt == TT.KW_USING:
                contract.using_for.append(self._parse_using())
            else:
                # Try state variable
                sv = self._try_parse_state_var()
                if sv:
                    contract.state_vars.append(sv)
                else:
                    self._advance()  # skip unrecognized
            # Guard: ensure progress — prevent infinite loops
            if self._pos == saved_pos:
                self._advance()

    # ── Functions ──

    def _parse_function(self) -> FunctionNode:
        line = self._current().line
        self._expect(TT.KW_FUNCTION)

        # Name (can be missing for unnamed fallback in older Solidity)
        name = ""
        if self._check(TT.IDENT):
            name = self._current().value
            self._advance()

        # Parameters
        params = self._parse_params()

        # Qualifiers
        vis, mut, mods, is_virtual, is_override = self._parse_function_qualifiers()

        # Returns
        returns = []
        if self._check(TT.KW_RETURNS):
            self._advance()
            returns = self._parse_params()

        # More qualifiers can appear after returns
        vis2, mut2, mods2, virt2, over2 = self._parse_function_qualifiers()
        vis = vis or vis2
        mut = mut or mut2
        mods.extend(mods2)
        is_virtual = is_virtual or virt2
        is_override = is_override or over2

        # Body or semicolon
        body_tokens = []
        raw_body = ""
        end_line = line
        if self._check(TT.LBRACE):
            body_tokens, raw_body = self._capture_brace_block()
            end_line = self._tokens[self._pos - 1].line if self._pos > 0 else line
        elif self._check(TT.SEMICOLON):
            self._advance()

        return FunctionNode(
            name=name, params=params, returns=returns,
            visibility=vis or "internal", mutability=mut,
            modifiers=mods, is_virtual=is_virtual, is_override=is_override,
            body_tokens=body_tokens, raw_body=raw_body,
            line=line, end_line=end_line,
        )

    def _parse_constructor(self) -> FunctionNode:
        line = self._current().line
        self._expect(TT.KW_CONSTRUCTOR)
        params = self._parse_params()
        vis, mut, mods, _, _ = self._parse_function_qualifiers()
        body_tokens, raw_body = [], ""
        if self._check(TT.LBRACE):
            body_tokens, raw_body = self._capture_brace_block()
        return FunctionNode(
            name="constructor", params=params,
            visibility=vis or "public", mutability=mut, modifiers=mods,
            is_constructor=True, body_tokens=body_tokens, raw_body=raw_body,
            line=line,
        )

    def _parse_receive(self) -> FunctionNode:
        line = self._current().line
        self._expect(TT.KW_RECEIVE)
        self._expect(TT.LPAREN)
        self._expect(TT.RPAREN)
        _, _, mods, _, _ = self._parse_function_qualifiers()
        body_tokens, raw_body = [], ""
        if self._check(TT.LBRACE):
            body_tokens, raw_body = self._capture_brace_block()
        return FunctionNode(
            name="receive", visibility="external", mutability="payable",
            modifiers=mods, is_receive=True,
            body_tokens=body_tokens, raw_body=raw_body, line=line,
        )

    def _parse_fallback(self) -> FunctionNode:
        line = self._current().line
        self._expect(TT.KW_FALLBACK)
        params = []
        if self._check(TT.LPAREN):
            params = self._parse_params()
        vis, mut, mods, _, _ = self._parse_function_qualifiers()
        returns = []
        if self._check(TT.KW_RETURNS):
            self._advance()
            returns = self._parse_params()
        body_tokens, raw_body = [], ""
        if self._check(TT.LBRACE):
            body_tokens, raw_body = self._capture_brace_block()
        return FunctionNode(
            name="fallback", params=params, returns=returns,
            visibility=vis or "external", mutability=mut, modifiers=mods,
            is_fallback=True, body_tokens=body_tokens, raw_body=raw_body,
            line=line,
        )

    def _parse_modifier(self) -> ModifierNode:
        line = self._current().line
        self._expect(TT.KW_MODIFIER)
        name = self._expect_ident()
        params = []
        if self._check(TT.LPAREN):
            params = self._parse_params()
        # Skip virtual/override
        while self._check(TT.KW_VIRTUAL, TT.KW_OVERRIDE):
            self._advance()
        body_tokens, raw_body = [], ""
        if self._check(TT.LBRACE):
            body_tokens, raw_body = self._capture_brace_block()
        return ModifierNode(
            name=name, params=params,
            body_tokens=body_tokens, raw_body=raw_body, line=line,
        )

    # ── Declarations ──

    def _parse_event(self) -> EventNode:
        line = self._current().line
        self._expect(TT.KW_EVENT)
        name = self._expect_ident()
        params = []
        if self._check(TT.LPAREN):
            params = self._parse_params()
        self._eat(TT.SEMICOLON)
        return EventNode(name=name, line=line, params=[
            {"name": p.name, "type": p.param_type, "indexed": p.indexed} for p in params
        ])

    def _parse_error(self) -> ErrorNode:
        line = self._current().line
        self._expect(TT.KW_ERROR)
        name = self._expect_ident()
        if self._check(TT.LPAREN):
            self._skip_balanced(TT.LPAREN, TT.RPAREN)
        self._eat(TT.SEMICOLON)
        return ErrorNode(name=name, line=line)

    def _parse_struct(self) -> StructNode:
        line = self._current().line
        self._expect(TT.KW_STRUCT)
        name = self._expect_ident()
        members = []
        self._expect(TT.LBRACE)
        while not self._at_end() and not self._check(TT.RBRACE):
            saved = self._pos
            mtype = self._read_type_name()
            mname = self._expect_ident() if self._check(TT.IDENT) else ""
            members.append({"name": mname, "type": mtype})
            self._eat(TT.SEMICOLON)
            if self._pos == saved:
                self._advance()  # guard: ensure progress
        self._eat(TT.RBRACE)
        return StructNode(name=name, members=members, line=line)

    def _parse_enum(self) -> EnumNode:
        line = self._current().line
        self._expect(TT.KW_ENUM)
        name = self._expect_ident()
        values = []
        self._expect(TT.LBRACE)
        while not self._at_end() and not self._check(TT.RBRACE):
            saved = self._pos
            if self._check(TT.IDENT):
                values.append(self._current().value)
                self._advance()
            if self._check(TT.COMMA):
                self._advance()
            if self._pos == saved:
                self._advance()  # guard: ensure progress
        self._eat(TT.RBRACE)
        return EnumNode(name=name, values=values, line=line)

    def _parse_using(self) -> UsingNode:
        line = self._current().line
        self._expect(TT.KW_USING)
        library = self._expect_ident()
        self._expect(TT.KW_FOR)
        # Type can be complex: "uint256", "*", etc.
        target = ""
        while not self._at_end() and not self._check(TT.SEMICOLON):
            target += self._current().value
            self._advance()
        self._eat(TT.SEMICOLON)
        return UsingNode(library=library, target_type=target.strip(), line=line)

    def _try_parse_state_var(self) -> Optional[StateVarNode]:
        """
        Try to parse a state variable declaration.
        Returns None if the current position doesn't look like a state var.
        """
        saved = self._pos
        line = self._current().line

        # Read type
        var_type = self._try_read_type_name()
        if not var_type:
            self._pos = saved
            return None

        is_mapping = var_type.startswith("mapping")
        is_array = "[]" in var_type

        # Visibility / constant / immutable
        visibility = "internal"
        is_constant = False
        is_immutable = False

        while self._check(TT.KW_PUBLIC, TT.KW_PRIVATE, TT.KW_INTERNAL,
                          TT.KW_EXTERNAL, TT.KW_CONSTANT, TT.KW_IMMUTABLE,
                          TT.KW_OVERRIDE):
            tok = self._current()
            if tok.tt in _VISIBILITY:
                visibility = tok.value
            elif tok.tt == TT.KW_CONSTANT:
                is_constant = True
            elif tok.tt == TT.KW_IMMUTABLE:
                is_immutable = True
            self._advance()

        # Name
        if not self._check(TT.IDENT):
            self._pos = saved
            return None
        name = self._current().value
        self._advance()

        # Must end with ; or = (with initializer then ;)
        initializer = ""
        if self._check(TT.ASSIGN):
            self._advance()
            # Read until ;
            parts = []
            depth = 0
            while not self._at_end():
                if self._check(TT.SEMICOLON) and depth == 0:
                    break
                if self._current().tt in (TT.LPAREN, TT.LBRACKET, TT.LBRACE):
                    depth += 1
                elif self._current().tt in (TT.RPAREN, TT.RBRACKET, TT.RBRACE):
                    depth -= 1
                parts.append(self._current().value)
                self._advance()
            initializer = " ".join(parts)
        
        if not self._check(TT.SEMICOLON):
            # Not a valid state var declaration
            self._pos = saved
            return None
        self._advance()  # eat ;

        return StateVarNode(
            name=name, var_type=var_type, visibility=visibility,
            is_constant=is_constant, is_immutable=is_immutable,
            is_mapping=is_mapping, is_array=is_array,
            initializer=initializer, line=line,
        )

    # ── Parameters ──

    def _parse_params(self) -> List[ParamNode]:
        """Parse a parameter list: (type name, type name, ...)"""
        params = []
        self._expect(TT.LPAREN)
        while not self._at_end() and not self._check(TT.RPAREN):
            saved = self._pos
            p = self._parse_one_param()
            if p:
                params.append(p)
            if self._check(TT.COMMA):
                self._advance()
            elif self._pos == saved:
                # No progress — skip unrecognized token to avoid infinite loop
                self._advance()
        self._eat(TT.RPAREN)
        return params

    def _parse_one_param(self) -> Optional[ParamNode]:
        line = self._current().line
        ptype = self._try_read_type_name()
        if not ptype:
            return None

        data_loc = ""
        indexed = False

        # data location or indexed
        while True:
            if self._check(TT.KW_MEMORY):
                data_loc = "memory"
                self._advance()
            elif self._check(TT.KW_STORAGE):
                data_loc = "storage"
                self._advance()
            elif self._check(TT.KW_CALLDATA):
                data_loc = "calldata"
                self._advance()
            elif self._check(TT.KW_INDEXED):
                indexed = True
                self._advance()
            else:
                break

        # Name (optional)
        name = ""
        if self._check(TT.IDENT):
            name = self._current().value
            self._advance()

        return ParamNode(name=name, param_type=ptype, data_location=data_loc,
                         indexed=indexed, line=line)

    # ── Function qualifiers ──

    def _parse_function_qualifiers(self) -> Tuple[str, str, List[str], bool, bool]:
        """Parse visibility, mutability, modifiers, virtual, override."""
        vis = ""
        mut = ""
        mods = []
        is_virtual = False
        is_override = False

        while not self._at_end():
            tok = self._current()
            if tok.tt in _VISIBILITY:
                vis = tok.value
                self._advance()
            elif tok.tt in _MUTABILITY:
                mut = tok.value
                self._advance()
            elif tok.tt == TT.KW_VIRTUAL:
                is_virtual = True
                self._advance()
            elif tok.tt == TT.KW_OVERRIDE:
                is_override = True
                self._advance()
                # override(Base1, Base2)
                if self._check(TT.LPAREN):
                    self._skip_balanced(TT.LPAREN, TT.RPAREN)
            elif tok.tt == TT.IDENT:
                # Custom modifier: nonReentrant, onlyOwner, etc.
                # Tricky: could be start of return type or next declaration.
                # Heuristic: if followed by ( or another qualifier, it's a modifier
                if self._peek_is_modifier_context():
                    mods.append(tok.value)
                    self._advance()
                    if self._check(TT.LPAREN):
                        self._skip_balanced(TT.LPAREN, TT.RPAREN)
                else:
                    break
            else:
                break

        return vis, mut, mods, is_virtual, is_override

    def _peek_is_modifier_context(self) -> bool:
        """Heuristic: are we still in function qualifiers area?"""
        # Look ahead: if the next non-consumed tokens before { or ; include
        # 'returns', another keyword, or '{', the current IDENT is a modifier.
        saved = self._pos
        self._advance()  # skip current IDENT
        # Skip potential modifier args
        if self._check(TT.LPAREN):
            self._skip_balanced(TT.LPAREN, TT.RPAREN)

        result = False
        tok = self._current() if not self._at_end() else None
        if tok:
            if tok.tt in (TT.KW_RETURNS, TT.LBRACE, TT.SEMICOLON,
                          TT.KW_VIRTUAL, TT.KW_OVERRIDE,
                          *_VISIBILITY, *_MUTABILITY):
                result = True
            elif tok.tt == TT.IDENT:
                # Could be another modifier — check recursively or just accept
                result = True

        self._pos = saved
        return result

    # ── Type reading ──

    def _read_type_name(self) -> str:
        """Read a type name (may include mapping, arrays, function types)."""
        t = self._try_read_type_name()
        return t or ""

    def _try_read_type_name(self) -> Optional[str]:
        """Try to read a type name. Returns None if current token isn't a type."""
        if self._at_end():
            return None

        tok = self._current()

        # mapping(KeyType => ValueType)
        if tok.tt == TT.KW_MAPPING:
            return self._read_mapping_type()

        # function type: function(...) ... returns (...)
        if tok.tt == TT.KW_FUNCTION:
            return self._read_function_type()

        # Elementary types or user-defined types
        if tok.tt == TT.IDENT or tok.tt in (
            TT.KW_PAYABLE,  # address payable
        ):
            parts = [tok.value]
            self._advance()

            # Dot-separated: SomeLib.SomeType
            while self._check(TT.DOT) and self._pos + 1 < len(self._tokens):
                parts.append(".")
                self._advance()
                if self._check(TT.IDENT):
                    parts.append(self._current().value)
                    self._advance()

            # Array brackets
            while self._check(TT.LBRACKET):
                parts.append("[")
                self._advance()
                # Array size can be a number (uint256[3]) or identifier/constant (uint256[NUM_COINS])
                if self._check(TT.NUMBER):
                    parts.append(self._current().value)
                    self._advance()
                elif self._check(TT.IDENT):
                    parts.append(self._current().value)
                    self._advance()
                if self._check(TT.RBRACKET):
                    parts.append("]")
                    self._advance()

            # 'address payable' special case
            if parts == ["address"] and self._check(TT.KW_PAYABLE):
                parts.append("payable")
                self._advance()

            return "".join(parts)

        return None

    def _read_mapping_type(self) -> str:
        """Read mapping(K => V) — supports Solidity 0.8 named parameters."""
        result = "mapping("
        self._expect(TT.KW_MAPPING)
        self._expect(TT.LPAREN)
        # Key type
        key = self._read_type_name()
        result += key
        # Skip optional parameter name (Solidity 0.8+: mapping(uint256 id => ...))
        if self._check(TT.IDENT) and not self._check(TT.KW_MAPPING):
            self._advance()  # skip the name
        self._expect(TT.ARROW)
        result += " => "
        # Value type (can be another mapping)
        val = self._read_type_name()
        result += val
        # Skip optional value parameter name
        if self._check(TT.IDENT):
            self._advance()
        result += ")"
        self._expect(TT.RPAREN)
        return result

    def _read_function_type(self) -> str:
        """Read function type: function(...) external returns (...)."""
        self._advance()  # skip 'function'
        parts = ["function"]
        if self._check(TT.LPAREN):
            self._skip_balanced(TT.LPAREN, TT.RPAREN)
            parts.append("(...)")
        while self._check(TT.KW_EXTERNAL, TT.KW_INTERNAL, TT.KW_VIEW, TT.KW_PURE, TT.KW_PAYABLE):
            parts.append(self._current().value)
            self._advance()
        if self._check(TT.KW_RETURNS):
            self._advance()
            if self._check(TT.LPAREN):
                self._skip_balanced(TT.LPAREN, TT.RPAREN)
        return " ".join(parts)

    # ── Block capture ──

    def _capture_brace_block(self) -> Tuple[List[Token], str]:
        """
        Capture all tokens inside a { } block (including the braces themselves).
        Also reconstructs the raw source text of the body.
        Returns (body_tokens_without_outer_braces, raw_body_text).
        """
        self._expect(TT.LBRACE)
        depth = 1
        body_tokens = []
        start_pos = self._pos

        while not self._at_end() and depth > 0:
            tok = self._current()
            if tok.tt == TT.LBRACE:
                depth += 1
            elif tok.tt == TT.RBRACE:
                depth -= 1
                if depth == 0:
                    break
            body_tokens.append(tok)
            self._advance()

        # Reconstruct raw body from source using line numbers
        raw_body = ""
        if body_tokens and self._source:
            src_lines = self._source.splitlines()
            start_line = body_tokens[0].line - 1
            end_line = body_tokens[-1].line if body_tokens else start_line
            if start_line < len(src_lines):
                raw_body = "\n".join(src_lines[start_line:end_line])

        self._eat(TT.RBRACE)
        return body_tokens, raw_body

    # ── Utility ──

    def _current(self) -> Token:
        if self._pos < len(self._tokens):
            return self._tokens[self._pos]
        return Token(TT.EOF, "", 0, 0)

    def _at_end(self) -> bool:
        return self._pos >= len(self._tokens) or self._tokens[self._pos].tt == TT.EOF

    def _check(self, *types: TT) -> bool:
        if self._at_end():
            return False
        return self._tokens[self._pos].tt in types

    def _advance(self) -> Token:
        tok = self._current()
        if not self._at_end():
            self._pos += 1
        return tok

    def _expect(self, tt: TT) -> Token:
        if self._check(tt):
            return self._advance()
        # Error recovery: skip ahead until we find the expected token
        return self._advance()

    def _eat(self, tt: TT):
        if self._check(tt):
            self._advance()

    def _expect_ident(self) -> str:
        if self._check(TT.IDENT):
            return self._advance().value
        # Some keywords can be used as identifiers in certain contexts
        tok = self._current()
        if tok.tt.name.startswith("KW_"):
            self._advance()
            return tok.value
        return ""

    def _skip_balanced(self, open_tt: TT, close_tt: TT):
        """Skip a balanced pair of tokens (e.g., parentheses)."""
        if not self._check(open_tt):
            return
        self._advance()
        depth = 1
        while not self._at_end() and depth > 0:
            if self._check(open_tt):
                depth += 1
            elif self._check(close_tt):
                depth -= 1
            self._advance()


# ═══════════════════════════════════════════════════════════
#  Semantic Analyzer — AST → ParsedContract models
# ═══════════════════════════════════════════════════════════

# Known reentrancy guard modifiers
_REENTRANCY_MODS = frozenset({
    "nonreentrant", "nonreentrancy", "reentrancyguard",
    "lock", "mutex", "noreentrancy",
})

# Access control modifiers
_ACCESS_MODS = frozenset({
    "onlyowner", "onlyadmin", "onlygovernance", "onlyguardian",
    "onlyrole", "onlyauthorized", "onlycontroller", "onlymanager",
    "onlyoperator", "onlyminter", "onlypauser", "onlygov",
    "auth", "restricted", "requiresauth",
})

# Access control checks in require statements
_ACCESS_CHECKS = frozenset({
    "msg.sender ==", "msg.sender !=", "_msgSender() ==",
    "owner()", "hasRole(", "isOwner", "authorized",
})


class ASTSemanticAnalyzer:
    """
    Converts AST nodes into the existing ParsedContract/ParsedFunction models.
    Also performs semantic analysis (operation ordering, state reads/writes, etc.)
    on function bodies using the token stream (not regex).

    This is the bridge between the new AST parser and the old model interface,
    ensuring full backward compatibility.
    """

    def __init__(self, source: str = "", file_path: str = ""):
        self._source = source
        self._file_path = file_path

    def analyze(self, unit: SourceUnit) -> List[ParsedContract]:
        """Convert SourceUnit AST to list of ParsedContract."""
        contracts = []
        for cnode in unit.contracts:
            contract = self._analyze_contract(cnode, unit.pragma, unit.license)
            contracts.append(contract)

        # Resolve inheritance (same logic as before, but on the clean AST output)
        self._resolve_inheritance(contracts)
        return contracts

    def _analyze_contract(self, cnode: ContractNode, pragma: str, license_id: str) -> ParsedContract:
        contract = ParsedContract(
            name=cnode.name,
            contract_type=cnode.contract_type,
            inherits=cnode.inherits,
            pragma=pragma,
            license=license_id,
            line_start=cnode.line,
            line_end=cnode.end_line,
            source_file=self._file_path,
        )

        # Version
        contract.solidity_version = self._extract_version(pragma)
        contract.uses_safe_math = "SafeMath" in self._source
        contract.is_upgradeable = any(
            p in " ".join(cnode.inherits).lower()
            for p in ["upgradeable", "initializable", "uupsupgradeable", "proxy"]
        )

        # Using for
        for u in cnode.using_for:
            contract.using_for.append({"library": u.library, "type": u.target_type})

        # Events
        contract.events = [e.name for e in cnode.events]

        # State variables
        for sv in cnode.state_vars:
            contract.state_vars[sv.name] = StateVar(
                name=sv.name, var_type=sv.var_type,
                visibility=sv.visibility, is_constant=sv.is_constant,
                is_immutable=sv.is_immutable, is_mapping=sv.is_mapping,
                is_array=sv.is_array, line=sv.line,
            )
        # Also register struct/enum names as pseudo state-vars for detection
        for st in cnode.structs:
            contract.state_vars[st.name] = StateVar(
                name=st.name, var_type="struct", line=st.line,
            )
        for en in cnode.enums:
            contract.state_vars[en.name] = StateVar(
                name=en.name, var_type="enum", line=en.line,
            )

        # Modifiers
        for mnode in cnode.modifiers:
            mod = ModifierInfo(
                name=mnode.name,
                params=[p.name for p in mnode.params],
                body=mnode.raw_body,
                line=mnode.line,
            )
            # Check if modifier enforces access control
            body_lower = mnode.raw_body.lower()
            mod.checks_owner = "msg.sender" in body_lower and ("==" in body_lower or "require" in body_lower)
            mod.checks_role = any(kw in body_lower for kw in ("hasrole", "role", "authorized"))
            mod.is_reentrancy_guard = any(kw in mnode.name.lower().replace('_', '') for kw in _REENTRANCY_MODS)
            mod.is_paused_check = any(kw in body_lower for kw in ("paused", "whennotpaused"))
            contract.modifiers[mnode.name] = mod

        # Functions
        state_var_names = set(contract.state_vars.keys())
        for fnode in cnode.functions:
            func = self._analyze_function(fnode, state_var_names, contract.modifiers)
            # Handle overloading
            key = fnode.name
            if key in contract.functions:
                param_types = ",".join(p.param_type for p in fnode.params)
                key = f"{fnode.name}({param_types})"
            contract.functions[key] = func

        return contract

    def _analyze_function(self, fnode: FunctionNode, state_var_names: Set[str],
                          contract_modifiers: Dict[str, ModifierInfo]) -> ParsedFunction:
        func = ParsedFunction(
            name=fnode.name,
            visibility=fnode.visibility,
            mutability=fnode.mutability,
            modifiers=fnode.modifiers,
            parameters=[{"name": p.name, "type": p.param_type} for p in fnode.params],
            returns=[{"name": p.name, "type": p.param_type} for p in fnode.returns],
            line_start=fnode.line,
            line_end=fnode.end_line,
            raw_body=fnode.raw_body,
            is_constructor=fnode.is_constructor,
            is_fallback=fnode.is_fallback,
            is_receive=fnode.is_receive,
        )

        # Analyze body using tokens (not regex!)
        if fnode.body_tokens:
            self._analyze_body_tokens(func, fnode.body_tokens, state_var_names)

        # Reentrancy guard
        func.has_reentrancy_guard = any(
            m.lower().replace('_', '') in _REENTRANCY_MODS
            for m in func.modifiers
        )

        # Access control from modifiers
        func.has_access_control = any(
            m.lower().replace('_', '') in _ACCESS_MODS or
            any(m.lower().startswith(a) for a in _ACCESS_MODS)
            for m in func.modifiers
        ) or any(
            any(check in req for check in _ACCESS_CHECKS)
            for req in func.require_checks
        )

        # Enhance access control from contract-level modifiers
        if not func.has_access_control and contract_modifiers:
            for mod_name in func.modifiers:
                if mod_name in contract_modifiers:
                    mod_info = contract_modifiers[mod_name]
                    if mod_info.checks_owner or mod_info.checks_role:
                        func.has_access_control = True
                        break

        return func

    # ── Token-based body analysis ──

    def _analyze_body_tokens(self, func: ParsedFunction, tokens: List[Token],
                             state_var_names: Set[str]):
        """
        Analyze function body using the token stream.
        This replaces the regex-based _analyze_function_body.

        Advantages over regex:
          - Correctly handles multi-line expressions
          - No false matches inside strings
          - Proper scope tracking (loops, conditions)
          - Unlimited nesting depth
        """
        operations = []
        local_vars: Set[str] = set()
        loop_depth = 0
        condition_depth = 0

        # Extract parameter names as local variables
        for p in func.parameters:
            if p.get("name"):
                local_vars.add(p["name"])

        i = 0
        while i < len(tokens):
            tok = tokens[i]
            in_loop = loop_depth > 0
            in_condition = condition_depth > 0

            # ── For/While loops ──
            if tok.tt in (TT.KW_FOR, TT.KW_WHILE, TT.KW_DO):
                loop_depth += 1
                operations.append(Operation(OpType.LOOP_START, tok.line))
                func.has_loops = True
                i += 1
                continue

            # ── If/Else ──
            if tok.tt == TT.KW_IF:
                condition_depth += 1
                i += 1
                continue

            # ── Brace tracking for loop/condition end ──
            if tok.tt == TT.RBRACE:
                if loop_depth > 0:
                    loop_depth -= 1
                    operations.append(Operation(OpType.LOOP_END, tok.line))
                elif condition_depth > 0:
                    condition_depth -= 1
                i += 1
                continue

            # ── Assembly ──
            if tok.tt == TT.KW_ASSEMBLY:
                operations.append(Operation(OpType.ASSEMBLY, tok.line))
                # Skip assembly block
                i += 1
                if i < len(tokens) and tokens[i].tt == TT.LBRACE:
                    depth = 1
                    i += 1
                    while i < len(tokens) and depth > 0:
                        if tokens[i].tt == TT.LBRACE:
                            depth += 1
                        elif tokens[i].tt == TT.RBRACE:
                            depth -= 1
                        i += 1
                continue

            # ── Unchecked block ──
            if tok.tt == TT.KW_UNCHECKED:
                i += 1
                continue

            # ── Selfdestruct ──
            if tok.tt == TT.KW_SELFDESTRUCT:
                operations.append(Operation(OpType.SELFDESTRUCT, tok.line))
                func.has_selfdestruct = True
                i += 1
                continue

            # ── Require ──
            if tok.tt == TT.KW_REQUIRE:
                condition = self._extract_call_arg_text(tokens, i)
                operations.append(Operation(
                    OpType.REQUIRE, tok.line, target=condition,
                    in_loop=in_loop, in_condition=in_condition,
                ))
                func.require_checks.append(condition)
                i = self._skip_past_semicolon(tokens, i)
                continue

            # ── Assert ──
            if tok.tt == TT.KW_ASSERT:
                operations.append(Operation(
                    OpType.ASSERT, tok.line, in_loop=in_loop, in_condition=in_condition,
                ))
                i = self._skip_past_semicolon(tokens, i)
                continue

            # ── Revert ──
            if tok.tt == TT.KW_REVERT:
                operations.append(Operation(OpType.REVERT, tok.line))
                i = self._skip_past_semicolon(tokens, i)
                continue

            # ── Emit ──
            if tok.tt == TT.KW_EMIT:
                i += 1
                event_name = ""
                if i < len(tokens) and tokens[i].tt == TT.IDENT:
                    event_name = tokens[i].value
                operations.append(Operation(
                    OpType.EMIT, tok.line, target=event_name,
                    in_loop=in_loop, in_condition=in_condition,
                ))
                i = self._skip_past_semicolon(tokens, i)
                continue

            # ── Return ──
            if tok.tt == TT.KW_RETURN:
                operations.append(Operation(OpType.RETURN, tok.line))
                i = self._skip_past_semicolon(tokens, i)
                continue

            # ── External calls and ERC20 transfers ──
            # Pattern: expr.call{value:...}(...) / expr.transfer(...) / IERC20(x).transferFrom(...)
            # We detect: IDENT DOT (call|send|transfer|delegatecall|staticcall|transferFrom|...)
            if tok.tt in (TT.IDENT, TT.LPAREN, TT.KW_PAYABLE):
                call_info = self._detect_external_call(tokens, i, state_var_names, local_vars)
                if call_info:
                    op_type, target, details, new_i = call_info
                    op = Operation(
                        op_type, tok.line, target=target, details=details,
                        sends_eth=(op_type == OpType.EXTERNAL_CALL_ETH),
                        in_loop=in_loop, in_condition=in_condition,
                    )
                    operations.append(op)
                    func.external_calls.append(op)
                    if op_type == OpType.EXTERNAL_CALL_ETH:
                        func.sends_eth = True
                    if op_type == OpType.DELEGATECALL:
                        func.has_delegatecall = True
                    i = self._skip_past_semicolon(tokens, new_i)
                    continue

            # ── State writes (assignments) ──
            # pattern: stateVar = ... ; or stateVar[x] = ... ; or stateVar.field = ... ;
            # Also: stateVar += / -= / etc.
            if tok.tt == TT.IDENT and tok.value in state_var_names and tok.value not in local_vars:
                assign_i = self._find_assignment(tokens, i)
                if assign_i is not None:
                    var = tok.value
                    operations.append(Operation(
                        OpType.STATE_WRITE, tok.line, target=var,
                        in_loop=in_loop, in_condition=in_condition,
                    ))
                    if var not in func.state_writes:
                        func.state_writes.append(var)
                    func.modifies_state = True
                    # Also scan RHS for state reads
                    self._scan_state_reads(tokens, assign_i + 1, state_var_names,
                                           local_vars, func, operations, tok.line,
                                           in_loop, in_condition)
                    i = self._skip_past_semicolon(tokens, i)
                    continue

            # ── Local variable declarations ──
            local_name = self._detect_local_var_decl(tokens, i)
            if local_name:
                local_vars.add(local_name)

            # ── State reads (any mention of a state var) ──
            if tok.tt == TT.IDENT and tok.value in state_var_names and tok.value not in local_vars:
                var = tok.value
                if var not in func.state_reads:
                    func.state_reads.append(var)
                operations.append(Operation(
                    OpType.STATE_READ, tok.line, target=var,
                    in_loop=in_loop, in_condition=in_condition,
                ))

            # ── Internal calls ──
            if tok.tt == TT.IDENT and (i + 1) < len(tokens) and tokens[i + 1].tt == TT.LPAREN:
                callee = tok.value
                skip_names = {
                    'if', 'for', 'while', 'require', 'assert', 'revert',
                    'emit', 'return', 'uint256', 'uint', 'int', 'bool',
                    'address', 'bytes', 'string', 'mapping', 'keccak256',
                    'abi', 'block', 'msg', 'tx', 'type', 'new',
                    'delete', 'push', 'pop', 'send', 'transfer', 'call',
                }
                if callee not in skip_names and callee not in state_var_names:
                    if callee not in func.internal_calls:
                        func.internal_calls.append(callee)
                    operations.append(Operation(
                        OpType.INTERNAL_CALL, tok.line, target=callee,
                        in_loop=in_loop, in_condition=in_condition,
                    ))

            i += 1

        func.operations = operations
        func.has_loops = any(op.op_type == OpType.LOOP_START for op in operations)

    # ── External call detection (token-based) ──

    _ERC20_METHODS = frozenset({
        "transfer", "transferFrom", "safeTransfer", "safeTransferFrom",
        "approve", "safeApprove",
    })

    _LOW_LEVEL_CALLS = frozenset({"call", "send", "delegatecall", "staticcall"})

    def _detect_external_call(self, tokens: List[Token], pos: int,
                              state_var_names: Set[str],
                              local_vars: Set[str]) -> Optional[Tuple[OpType, str, str, int]]:
        """
        Detect external call patterns starting at pos.
        Returns (OpType, target_name, method_name, new_pos) or None.

        Handles:
          - target.call{value:...}(...)     → EXTERNAL_CALL_ETH
          - target.transfer(amount)         → EXTERNAL_CALL_ETH (.transfer sends ETH)
          - target.send(amount)             → EXTERNAL_CALL
          - target.call(...)                → EXTERNAL_CALL
          - target.delegatecall(...)        → DELEGATECALL
          - target.staticcall(...)          → STATICCALL
          - IERC20(addr).transfer(...)      → EXTERNAL_CALL (ERC20)
          - token.transferFrom(...)         → EXTERNAL_CALL (ERC20)
        """
        # We need: ... DOT method_name
        # Scan forward to find the DOT + method pattern
        # The target can be: ident, ident(args), ident[x], ident(args).field(args)...
        
        # Look for  ... . (call|send|transfer|delegatecall|staticcall|transferFrom|...) (
        scan = pos
        target_parts = []
        last_ident = ""
        
        while scan < len(tokens):
            t = tokens[scan]
            
            if t.tt == TT.IDENT or t.tt == TT.KW_PAYABLE:
                last_ident = t.value
                target_parts.append(t.value)
                scan += 1
                
                # Skip function call args: IDENT(...)
                if scan < len(tokens) and tokens[scan].tt == TT.LPAREN:
                    target_parts.append("(...")
                    scan = self._skip_balanced_from(tokens, scan, TT.LPAREN, TT.RPAREN)
                    
                # Skip array access: IDENT[...]
                while scan < len(tokens) and tokens[scan].tt == TT.LBRACKET:
                    target_parts.append("[...]")
                    scan = self._skip_balanced_from(tokens, scan, TT.LBRACKET, TT.RBRACKET)
                
            elif t.tt == TT.DOT:
                # Check what's after the dot
                if scan + 1 >= len(tokens):
                    break
                    
                next_tok = tokens[scan + 1]
                method = next_tok.value if next_tok.tt == TT.IDENT else ""
                
                # .call{value:...}(...)
                if method == "call" and scan + 2 < len(tokens):
                    if tokens[scan + 2].tt == TT.LBRACE:
                        # Check for value
                        target = "".join(target_parts)
                        return (OpType.EXTERNAL_CALL_ETH, target, "call", scan + 2)
                    elif tokens[scan + 2].tt == TT.LPAREN:
                        target = "".join(target_parts)
                        return (OpType.EXTERNAL_CALL, target, "call", scan + 2)
                
                # .send(...)
                if method == "send" and scan + 2 < len(tokens) and tokens[scan + 2].tt == TT.LPAREN:
                    target = "".join(target_parts)
                    return (OpType.EXTERNAL_CALL, target, "send", scan + 2)
                
                # .transfer(...) — could be ETH transfer (address.transfer) or ERC20
                if method == "transfer" and scan + 2 < len(tokens) and tokens[scan + 2].tt == TT.LPAREN:
                    target = "".join(target_parts)
                    # Heuristic: if target looks like state var address → ETH transfer
                    # If target looks like IERC20(...) or token var → ERC20 transfer
                    is_erc20 = any(p.startswith("IERC20") or p.startswith("IERC") for p in target_parts)
                    if is_erc20:
                        return (OpType.EXTERNAL_CALL, target, "transfer", scan + 2)
                    else:
                        return (OpType.EXTERNAL_CALL_ETH, target, "transfer", scan + 2)
                
                # .delegatecall(...)
                if method == "delegatecall":
                    target = "".join(target_parts)
                    return (OpType.DELEGATECALL, target, "delegatecall", scan + 2)
                
                # .staticcall(...)
                if method == "staticcall":
                    target = "".join(target_parts)
                    return (OpType.STATICCALL, target, "staticcall", scan + 2)
                
                # ERC20 methods: .transferFrom, .safeTransfer, .approve, etc.
                if method in self._ERC20_METHODS and scan + 2 < len(tokens) and tokens[scan + 2].tt == TT.LPAREN:
                    target = "".join(target_parts)
                    return (OpType.EXTERNAL_CALL, target, method, scan + 2)
                
                # Not a recognized call — it's a member access, continue
                target_parts.append(".")
                scan += 1  # skip dot, loop will pick up next ident
                
            else:
                # Not part of a call chain
                break
        
        return None

    # ── Helpers ──

    def _find_assignment(self, tokens: List[Token], pos: int) -> Optional[int]:
        """
        Starting at pos (a state var ident), check if this is an assignment.
        Skips over [x], .field, etc. Returns position of the assignment operator,
        or None if not an assignment.
        """
        i = pos + 1
        # Skip member access / array access
        while i < len(tokens):
            if tokens[i].tt == TT.DOT:
                i += 1
                if i < len(tokens) and tokens[i].tt == TT.IDENT:
                    i += 1
            elif tokens[i].tt == TT.LBRACKET:
                i = self._skip_balanced_from(tokens, i, TT.LBRACKET, TT.RBRACKET)
            else:
                break

        if i < len(tokens) and tokens[i].tt in (
            TT.ASSIGN, TT.PLUS_ASSIGN, TT.MINUS_ASSIGN,
            TT.MUL_ASSIGN, TT.DIV_ASSIGN, TT.MOD_ASSIGN,
            TT.OR_ASSIGN, TT.AND_ASSIGN, TT.XOR_ASSIGN,
            TT.SHL_ASSIGN, TT.SHR_ASSIGN,
        ):
            return i
        return None

    def _detect_local_var_decl(self, tokens: List[Token], pos: int) -> Optional[str]:
        """Detect if current position is a local variable declaration. Return var name or None."""
        # Common patterns:
        # uint256 x = ...;
        # (uint256 x, bool y) = ...;
        # Type memory/storage/calldata name = ...;
        tok = tokens[pos]

        # Simple type ident: uint256/bool/address/bytes32/etc followed by (memory|storage|calldata)? ident
        if tok.tt == TT.IDENT:
            # Skip ahead to check pattern: Type [memory|storage|calldata] Name [=|;]
            i = pos + 1
            # Skip array brackets in type
            while i < len(tokens) and tokens[i].tt == TT.LBRACKET:
                i = self._skip_balanced_from(tokens, i, TT.LBRACKET, TT.RBRACKET)
            # Skip data location
            if i < len(tokens) and tokens[i].tt in (TT.KW_MEMORY, TT.KW_STORAGE, TT.KW_CALLDATA):
                i += 1
            # Next should be identifier (the variable name)
            if i < len(tokens) and tokens[i].tt == TT.IDENT:
                # Followed by = or ; means it's a declaration
                if i + 1 < len(tokens) and tokens[i + 1].tt in (TT.ASSIGN, TT.SEMICOLON):
                    return tokens[i].value
        return None

    def _scan_state_reads(self, tokens: List[Token], start: int,
                          state_var_names: Set[str], local_vars: Set[str],
                          func: ParsedFunction, operations: List[Operation],
                          line: int, in_loop: bool, in_condition: bool):
        """Scan tokens for state variable reads in an expression."""
        i = start
        while i < len(tokens) and tokens[i].tt != TT.SEMICOLON:
            if tokens[i].tt == TT.IDENT:
                var = tokens[i].value
                if var in state_var_names and var not in local_vars:
                    if var not in func.state_reads:
                        func.state_reads.append(var)
                    operations.append(Operation(
                        OpType.STATE_READ, tokens[i].line, target=var,
                        in_loop=in_loop, in_condition=in_condition,
                    ))
            i += 1

    def _extract_call_arg_text(self, tokens: List[Token], pos: int) -> str:
        """Extract the text of the first argument in a call: require(CONDITION, ...)."""
        i = pos + 1  # skip the keyword
        if i < len(tokens) and tokens[i].tt == TT.LPAREN:
            i += 1
            parts = []
            depth = 0
            while i < len(tokens):
                t = tokens[i]
                if t.tt == TT.LPAREN:
                    depth += 1
                    parts.append("(")
                elif t.tt == TT.RPAREN:
                    if depth == 0:
                        break
                    depth -= 1
                    parts.append(")")
                elif t.tt == TT.COMMA and depth == 0:
                    break
                else:
                    parts.append(t.value)
                i += 1
            return " ".join(parts)
        return ""

    def _skip_past_semicolon(self, tokens: List[Token], pos: int) -> int:
        """Advance past the next semicolon."""
        i = pos
        while i < len(tokens) and tokens[i].tt != TT.SEMICOLON:
            i += 1
        return i + 1  # past the semicolon

    def _skip_balanced_from(self, tokens: List[Token], pos: int, open_tt: TT, close_tt: TT) -> int:
        """Skip a balanced pair starting at pos. Returns position after the closing token."""
        if pos >= len(tokens) or tokens[pos].tt != open_tt:
            return pos + 1
        depth = 1
        pos += 1
        while pos < len(tokens) and depth > 0:
            if tokens[pos].tt == open_tt:
                depth += 1
            elif tokens[pos].tt == close_tt:
                depth -= 1
            pos += 1
        return pos

    # ── Inheritance resolution ──

    def _resolve_inheritance(self, contracts: List[ParsedContract]):
        """Merge parent state vars into children and re-analyze function bodies."""
        if not contracts:
            return

        by_name: Dict[str, ParsedContract] = {c.name: c for c in contracts}
        resolved: Set[str] = set()

        def resolve(name: str, visiting: Set[str]):
            if name in resolved or name not in by_name:
                return
            if name in visiting:
                return  # circular
            visiting.add(name)

            contract = by_name[name]
            for parent_name in contract.inherits:
                resolve(parent_name, visiting)

            inherited_vars: Dict[str, StateVar] = {}
            for parent_name in contract.inherits:
                parent = by_name.get(parent_name)
                if parent:
                    for var_name, var in parent.state_vars.items():
                        if var_name not in inherited_vars and var_name not in contract.state_vars:
                            inherited_vars[var_name] = var

            if inherited_vars:
                merged = {}
                merged.update(inherited_vars)
                merged.update(contract.state_vars)
                contract.state_vars = merged

                # NOTE: We don't need to re-analyze function bodies here
                # because the AST analyzer already has the tokens.
                # We just need to update state_reads/state_writes.
                all_var_names = set(merged.keys())
                for func in contract.functions.values():
                    # Add any newly visible inherited vars to reads/writes
                    for var_name in inherited_vars:
                        # Check raw_body for mentions (simple text check as backup)
                        if func.raw_body and re.search(r'\b' + re.escape(var_name) + r'\b', func.raw_body):
                            if var_name not in func.state_reads:
                                func.state_reads.append(var_name)
                            # Check if it's a write
                            write_pattern = re.escape(var_name) + r'\s*[\[\].]*\s*[+\-*/%|&^]?='
                            if re.search(write_pattern, func.raw_body):
                                if var_name not in func.state_writes:
                                    func.state_writes.append(var_name)
                                func.modifies_state = True

            resolved.add(name)
            visiting.discard(name)

        for name in list(by_name.keys()):
            resolve(name, set())

    def _extract_version(self, pragma: str) -> str:
        m = re.search(r'(\d+\.\d+\.\d+)', pragma)
        if m:
            return m.group(1)
        m = re.search(r'(\d+\.\d+)', pragma)
        if m:
            return m.group(1)
        return ""


# ═══════════════════════════════════════════════════════════
#  Public API — Drop-in replacement for SoliditySemanticParser
# ═══════════════════════════════════════════════════════════

class SolidityASTParserFull:
    """
    Drop-in replacement for SoliditySemanticParser.
    Same interface: parser.parse(source, file_path) -> List[ParsedContract]

    Internally uses:
      SolidityLexer → SolidityASTParser → ASTSemanticAnalyzer
    """

    def parse(self, source: str, file_path: str = "") -> List[ParsedContract]:
        # Step 1: Tokenize
        lexer = SolidityLexer(source)
        tokens = lexer.tokenize()

        # Step 2: Parse tokens into AST
        parser = SolidityASTParser(tokens, source)
        ast = parser.parse()

        # Inject SPDX license from lexer
        if lexer.spdx and not ast.license:
            ast.license = lexer.spdx

        # Step 3: Convert AST to ParsedContract models
        analyzer = ASTSemanticAnalyzer(source, file_path)
        contracts = analyzer.analyze(ast)

        return contracts
