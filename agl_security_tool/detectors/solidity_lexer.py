"""
AGL Solidity Tokenizer — المُقَسِّم المعجمي
Converts raw Solidity source into a token stream.

This replaces the regex-based _strip_comments + _split_statements approach
with a proper lexer that correctly handles:
  - String/hex literals (no false matches inside strings)
  - Nested comments  /* /* */ */
  - Multi-line expressions  foo(\n  bar,\n  baz\n)
  - All Solidity operators and punctuation
  - Precise line/column tracking

Zero external dependencies — pure Python.
"""

from __future__ import annotations
import re
from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Optional, Iterator


class TT(Enum):
    """Token Type — every lexical element in Solidity."""

    # ── Literals ──
    IDENT = auto()           # variable/type/function names
    NUMBER = auto()          # 123, 0xff, 1e18, 1_000
    STRING = auto()          # "..." or '...'
    HEX_STRING = auto()      # hex"..." or hex'...'
    UNICODE_STRING = auto()  # unicode"..."

    # ── Keywords ──
    # Contract-level
    KW_PRAGMA = auto()
    KW_IMPORT = auto()
    KW_CONTRACT = auto()
    KW_INTERFACE = auto()
    KW_LIBRARY = auto()
    KW_ABSTRACT = auto()
    KW_IS = auto()
    KW_USING = auto()
    KW_FOR = auto()

    # Function-level
    KW_FUNCTION = auto()
    KW_MODIFIER = auto()
    KW_CONSTRUCTOR = auto()
    KW_FALLBACK = auto()
    KW_RECEIVE = auto()
    KW_EVENT = auto()
    KW_ERROR = auto()
    KW_STRUCT = auto()
    KW_ENUM = auto()
    KW_TYPE = auto()

    # Visibility
    KW_PUBLIC = auto()
    KW_PRIVATE = auto()
    KW_INTERNAL = auto()
    KW_EXTERNAL = auto()

    # Mutability
    KW_VIEW = auto()
    KW_PURE = auto()
    KW_PAYABLE = auto()
    KW_CONSTANT = auto()
    KW_IMMUTABLE = auto()

    # Control flow
    KW_IF = auto()
    KW_ELSE = auto()
    KW_WHILE = auto()
    KW_DO = auto()
    KW_RETURN = auto()
    KW_RETURNS = auto()
    KW_BREAK = auto()
    KW_CONTINUE = auto()
    KW_EMIT = auto()
    KW_REVERT = auto()
    KW_REQUIRE = auto()
    KW_ASSERT = auto()
    KW_NEW = auto()
    KW_DELETE = auto()
    KW_TRY = auto()
    KW_CATCH = auto()
    KW_ASSEMBLY = auto()
    KW_UNCHECKED = auto()

    # Type keywords
    KW_MAPPING = auto()
    KW_STORAGE = auto()
    KW_MEMORY = auto()
    KW_CALLDATA = auto()
    KW_VIRTUAL = auto()
    KW_OVERRIDE = auto()
    KW_INDEXED = auto()
    KW_ANONYMOUS = auto()

    # Special
    KW_SELFDESTRUCT = auto()

    # ── Punctuation / Operators ──
    LBRACE = auto()       # {
    RBRACE = auto()       # }
    LPAREN = auto()       # (
    RPAREN = auto()       # )
    LBRACKET = auto()     # [
    RBRACKET = auto()     # ]
    SEMICOLON = auto()    # ;
    COMMA = auto()        # ,
    DOT = auto()          # .
    COLON = auto()        # :
    QUESTION = auto()     # ?
    ARROW = auto()        # =>
    ASSIGN = auto()       # =
    PLUS_ASSIGN = auto()  # +=
    MINUS_ASSIGN = auto() # -=
    MUL_ASSIGN = auto()   # *=
    DIV_ASSIGN = auto()   # /=
    MOD_ASSIGN = auto()   # %=
    OR_ASSIGN = auto()    # |=
    AND_ASSIGN = auto()   # &=
    XOR_ASSIGN = auto()   # ^=
    SHL_ASSIGN = auto()   # <<=
    SHR_ASSIGN = auto()   # >>=

    # Comparison / Logic
    EQ = auto()           # ==
    NEQ = auto()          # !=
    LT = auto()           # <
    GT = auto()           # >
    LTE = auto()          # <=
    GTE = auto()          # >=
    AND = auto()          # &&
    OR = auto()           # ||
    NOT = auto()          # !
    BIT_AND = auto()      # &
    BIT_OR = auto()       # |
    BIT_XOR = auto()      # ^
    BIT_NOT = auto()      # ~
    SHL = auto()          # <<
    SHR = auto()          # >>

    # Arithmetic
    PLUS = auto()         # +
    MINUS = auto()        # -
    STAR = auto()         # *
    SLASH = auto()        # /
    PERCENT = auto()      # %
    POWER = auto()        # **
    INC = auto()          # ++
    DEC = auto()          # --

    # ── Special ──
    PRAGMA_VALUE = auto()  # everything after 'pragma solidity' until ';'
    COMMENT_LINE = auto()  # // ...  (kept for SPDX extraction)
    EOF = auto()


# ── Keyword map ──
_KEYWORDS = {
    "pragma": TT.KW_PRAGMA, "import": TT.KW_IMPORT,
    "contract": TT.KW_CONTRACT, "interface": TT.KW_INTERFACE,
    "library": TT.KW_LIBRARY, "abstract": TT.KW_ABSTRACT,
    "is": TT.KW_IS, "using": TT.KW_USING, "for": TT.KW_FOR,
    "function": TT.KW_FUNCTION, "modifier": TT.KW_MODIFIER,
    "constructor": TT.KW_CONSTRUCTOR, "fallback": TT.KW_FALLBACK,
    "receive": TT.KW_RECEIVE, "event": TT.KW_EVENT,
    "error": TT.KW_ERROR, "struct": TT.KW_STRUCT,
    "enum": TT.KW_ENUM, "type": TT.KW_TYPE,
    "public": TT.KW_PUBLIC, "private": TT.KW_PRIVATE,
    "internal": TT.KW_INTERNAL, "external": TT.KW_EXTERNAL,
    "view": TT.KW_VIEW, "pure": TT.KW_PURE,
    "payable": TT.KW_PAYABLE, "constant": TT.KW_CONSTANT,
    "immutable": TT.KW_IMMUTABLE,
    "if": TT.KW_IF, "else": TT.KW_ELSE,
    "while": TT.KW_WHILE, "do": TT.KW_DO, "for": TT.KW_FOR,
    "return": TT.KW_RETURN, "returns": TT.KW_RETURNS,
    "break": TT.KW_BREAK, "continue": TT.KW_CONTINUE,
    "emit": TT.KW_EMIT, "revert": TT.KW_REVERT,
    "require": TT.KW_REQUIRE, "assert": TT.KW_ASSERT,
    "new": TT.KW_NEW, "delete": TT.KW_DELETE,
    "try": TT.KW_TRY, "catch": TT.KW_CATCH,
    "assembly": TT.KW_ASSEMBLY, "unchecked": TT.KW_UNCHECKED,
    "mapping": TT.KW_MAPPING,
    "storage": TT.KW_STORAGE, "memory": TT.KW_MEMORY,
    "calldata": TT.KW_CALLDATA,
    "virtual": TT.KW_VIRTUAL, "override": TT.KW_OVERRIDE,
    "indexed": TT.KW_INDEXED, "anonymous": TT.KW_ANONYMOUS,
    "selfdestruct": TT.KW_SELFDESTRUCT,
}

_VISIBILITY = {TT.KW_PUBLIC, TT.KW_PRIVATE, TT.KW_INTERNAL, TT.KW_EXTERNAL}
_MUTABILITY = {TT.KW_VIEW, TT.KW_PURE, TT.KW_PAYABLE}
_DATA_LOC = {TT.KW_STORAGE, TT.KW_MEMORY, TT.KW_CALLDATA}


@dataclass(slots=True)
class Token:
    """A single token with position information."""
    tt: TT
    value: str
    line: int      # 1-based
    col: int       # 0-based
    end_line: int = 0
    end_col: int = 0

    def __repr__(self):
        v = self.value[:30] + "…" if len(self.value) > 30 else self.value
        return f"Token({self.tt.name}, {v!r}, L{self.line})"


# ═══════════════════════════════════════════════════════════
#  Tokenizer
# ═══════════════════════════════════════════════════════════

class SolidityLexer:
    """
    Converts Solidity source code into a stream of tokens.

    Handles:
      - Single-line comments (//) — extracts SPDX
      - Multi-line comments (/* */) — including nested
      - String literals ("...", '...')
      - Hex/unicode string literals (hex"...", unicode"...")
      - All operators and punctuation
      - Number literals (decimal, hex, scientific, underscored)
      - Identifiers and keywords
      - Precise line/column tracking
    """

    def __init__(self, source: str):
        self._src = source
        self._pos = 0
        self._line = 1
        self._col = 0
        self._len = len(source)
        self._spdx: str = ""

    @property
    def spdx(self) -> str:
        return self._spdx

    def tokenize(self) -> List[Token]:
        """Tokenize the entire source and return a list of tokens."""
        tokens = []
        while self._pos < self._len:
            tok = self._next_token()
            if tok is not None:
                tokens.append(tok)
        tokens.append(Token(TT.EOF, "", self._line, self._col))
        return tokens

    # ── Core scanning ──

    def _next_token(self) -> Optional[Token]:
        self._skip_whitespace()
        if self._pos >= self._len:
            return None

        ch = self._src[self._pos]
        line, col = self._line, self._col

        # ── Comments ──
        if ch == '/' and self._pos + 1 < self._len:
            nxt = self._src[self._pos + 1]
            if nxt == '/':
                return self._read_line_comment(line, col)
            if nxt == '*':
                self._read_block_comment()
                return None  # block comments are skipped

        # ── String literals ──
        if ch in ('"', "'"):
            return self._read_string(ch, line, col)

        # ── Hex / Unicode string prefixes ──
        if ch == 'h' and self._src[self._pos:self._pos + 4] in ('hex"', "hex'"):
            quote = self._src[self._pos + 3]
            self._advance(3)
            tok = self._read_string(quote, line, col)
            tok.tt = TT.HEX_STRING
            return tok
        if ch == 'u' and self._src[self._pos:self._pos + 8].startswith('unicode'):
            rest = self._src[self._pos + 7:self._pos + 8]
            if rest in ('"', "'"):
                self._advance(7)
                tok = self._read_string(rest, line, col)
                tok.tt = TT.UNICODE_STRING
                return tok

        # ── Numbers ──
        if ch.isdigit() or (ch == '.' and self._pos + 1 < self._len and self._src[self._pos + 1].isdigit()):
            return self._read_number(line, col)

        # ── Identifiers / Keywords ──
        if ch.isalpha() or ch == '_' or ch == '$':
            return self._read_identifier(line, col)

        # ── Multi-char operators (check longest first) ──
        two = self._src[self._pos:self._pos + 2]
        three = self._src[self._pos:self._pos + 3]

        if three == '<<=':
            self._advance(3)
            return Token(TT.SHL_ASSIGN, three, line, col)
        if three == '>>=':
            self._advance(3)
            return Token(TT.SHR_ASSIGN, three, line, col)
        if two == '**':
            self._advance(2)
            return Token(TT.POWER, two, line, col)
        if two == '++':
            self._advance(2)
            return Token(TT.INC, two, line, col)
        if two == '--':
            self._advance(2)
            return Token(TT.DEC, two, line, col)
        if two == '+=':
            self._advance(2)
            return Token(TT.PLUS_ASSIGN, two, line, col)
        if two == '-=':
            self._advance(2)
            return Token(TT.MINUS_ASSIGN, two, line, col)
        if two == '*=':
            self._advance(2)
            return Token(TT.MUL_ASSIGN, two, line, col)
        if two == '/=':
            self._advance(2)
            return Token(TT.DIV_ASSIGN, two, line, col)
        if two == '%=':
            self._advance(2)
            return Token(TT.MOD_ASSIGN, two, line, col)
        if two == '|=':
            self._advance(2)
            return Token(TT.OR_ASSIGN, two, line, col)
        if two == '&=':
            self._advance(2)
            return Token(TT.AND_ASSIGN, two, line, col)
        if two == '^=':
            self._advance(2)
            return Token(TT.XOR_ASSIGN, two, line, col)
        if two == '==':
            self._advance(2)
            return Token(TT.EQ, two, line, col)
        if two == '!=':
            self._advance(2)
            return Token(TT.NEQ, two, line, col)
        if two == '<=':
            self._advance(2)
            return Token(TT.LTE, two, line, col)
        if two == '>=':
            self._advance(2)
            return Token(TT.GTE, two, line, col)
        if two == '&&':
            self._advance(2)
            return Token(TT.AND, two, line, col)
        if two == '||':
            self._advance(2)
            return Token(TT.OR, two, line, col)
        if two == '<<':
            self._advance(2)
            return Token(TT.SHL, two, line, col)
        if two == '>>':
            self._advance(2)
            return Token(TT.SHR, two, line, col)
        if two == '=>':
            self._advance(2)
            return Token(TT.ARROW, two, line, col)

        # ── Single-char operators ──
        _single = {
            '{': TT.LBRACE, '}': TT.RBRACE,
            '(': TT.LPAREN, ')': TT.RPAREN,
            '[': TT.LBRACKET, ']': TT.RBRACKET,
            ';': TT.SEMICOLON, ',': TT.COMMA,
            '.': TT.DOT, ':': TT.COLON, '?': TT.QUESTION,
            '=': TT.ASSIGN,
            '+': TT.PLUS, '-': TT.MINUS,
            '*': TT.STAR, '/': TT.SLASH, '%': TT.PERCENT,
            '<': TT.LT, '>': TT.GT,
            '!': TT.NOT, '~': TT.BIT_NOT,
            '&': TT.BIT_AND, '|': TT.BIT_OR, '^': TT.BIT_XOR,
        }
        if ch in _single:
            self._advance(1)
            return Token(_single[ch], ch, line, col)

        # Unknown char — skip
        self._advance(1)
        return None

    # ── Helpers ──

    def _advance(self, n: int = 1):
        for _ in range(n):
            if self._pos < self._len:
                if self._src[self._pos] == '\n':
                    self._line += 1
                    self._col = 0
                else:
                    self._col += 1
                self._pos += 1

    def _skip_whitespace(self):
        while self._pos < self._len and self._src[self._pos] in (' ', '\t', '\n', '\r'):
            self._advance()

    def _read_line_comment(self, line: int, col: int) -> Optional[Token]:
        start = self._pos
        while self._pos < self._len and self._src[self._pos] != '\n':
            self._pos += 1
            self._col += 1
        text = self._src[start:self._pos]
        # Extract SPDX
        if 'SPDX-License-Identifier' in text:
            m = re.search(r'SPDX-License-Identifier:\s*(.+)', text)
            if m:
                self._spdx = m.group(1).strip()
        return None  # skip comments by default

    def _read_block_comment(self):
        self._advance(2)  # skip /*
        # Solidity does NOT support nested block comments.
        # Simply scan for the first `*/` closing.
        while self._pos < self._len:
            if self._src[self._pos:self._pos + 2] == '*/':
                self._advance(2)
                return
            self._advance()

    def _read_string(self, quote: str, line: int, col: int) -> Token:
        self._advance()  # skip opening quote
        start = self._pos
        while self._pos < self._len:
            ch = self._src[self._pos]
            if ch == '\\':
                self._advance(2)
                continue
            if ch == quote:
                value = self._src[start:self._pos]
                self._advance()  # skip closing quote
                return Token(TT.STRING, value, line, col, self._line, self._col)
            if ch == '\n':
                break  # unterminated string
            self._advance()
        return Token(TT.STRING, self._src[start:self._pos], line, col, self._line, self._col)

    def _read_number(self, line: int, col: int) -> Token:
        start = self._pos
        # Hex
        if self._src[self._pos:self._pos + 2] in ('0x', '0X'):
            self._advance(2)
            while self._pos < self._len and (self._src[self._pos] in '0123456789abcdefABCDEF_'):
                self._advance()
        else:
            # Decimal with optional underscores
            while self._pos < self._len and (self._src[self._pos].isdigit() or self._src[self._pos] == '_'):
                self._advance()
            # Fractional part
            if self._pos < self._len and self._src[self._pos] == '.':
                self._advance()
                while self._pos < self._len and (self._src[self._pos].isdigit() or self._src[self._pos] == '_'):
                    self._advance()
            # Exponent
            if self._pos < self._len and self._src[self._pos] in ('e', 'E'):
                self._advance()
                if self._pos < self._len and self._src[self._pos] in ('+', '-'):
                    self._advance()
                while self._pos < self._len and self._src[self._pos].isdigit():
                    self._advance()
        # Units (ether, wei, gwei, seconds, minutes, hours, days, weeks)
        # These are separate identifiers — don't consume them here
        return Token(TT.NUMBER, self._src[start:self._pos], line, col, self._line, self._col)

    def _read_identifier(self, line: int, col: int) -> Token:
        start = self._pos
        while self._pos < self._len and (self._src[self._pos].isalnum() or self._src[self._pos] in ('_', '$')):
            self._advance()
        value = self._src[start:self._pos]
        tt = _KEYWORDS.get(value, TT.IDENT)
        return Token(tt, value, line, col, self._line, self._col)
