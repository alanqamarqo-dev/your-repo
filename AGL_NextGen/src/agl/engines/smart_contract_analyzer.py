#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AGL Smart Contract Analyzer - Deep Code Understanding
======================================================

هذا المحلل يفهم Solidity بعمق بدون الاعتماد على أدوات خارجية فقط.
يستخدم تحليل AST محلي + تتبع تدفق البيانات + Z3 للتحقق الرسمي.

الميزات:
1. Parser محلي لـ Solidity
2. Control Flow Graph (CFG) Builder  
3. Data Flow Analysis (DFA)
4. Taint Tracking
5. Pattern Detection

Author: AGL Team
Date: 2026-02-04
"""

import re
import json
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Any, Tuple
from enum import Enum, auto
from collections import defaultdict
import hashlib


# ============================================================================
# PART 1: Solidity Lexer & Parser
# ============================================================================

class TokenType(Enum):
    """أنواع الـ Tokens"""
    # Keywords
    CONTRACT = auto()
    FUNCTION = auto()
    MODIFIER = auto()
    EVENT = auto()
    STRUCT = auto()
    ENUM = auto()
    MAPPING = auto()
    IF = auto()
    ELSE = auto()
    FOR = auto()
    WHILE = auto()
    DO = auto()
    RETURN = auto()
    REQUIRE = auto()
    REVERT = auto()
    EMIT = auto()
    
    # Types
    ADDRESS = auto()
    UINT = auto()
    INT = auto()
    BOOL = auto()
    BYTES = auto()
    STRING = auto()
    
    # Visibility
    PUBLIC = auto()
    PRIVATE = auto()
    INTERNAL = auto()
    EXTERNAL = auto()
    
    # Modifiers
    PURE = auto()
    VIEW = auto()
    PAYABLE = auto()
    VIRTUAL = auto()
    OVERRIDE = auto()
    
    # Operators
    ASSIGN = auto()
    PLUS = auto()
    MINUS = auto()
    MUL = auto()
    DIV = auto()
    MOD = auto()
    EQ = auto()
    NEQ = auto()
    LT = auto()
    GT = auto()
    LTE = auto()
    GTE = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    
    # Special
    DOT = auto()
    COMMA = auto()
    SEMICOLON = auto()
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    
    # Literals
    NUMBER = auto()
    HEX_NUMBER = auto()
    STRING_LITERAL = auto()
    IDENTIFIER = auto()
    
    # Special Solidity
    MSG_SENDER = auto()
    MSG_VALUE = auto()
    TX_ORIGIN = auto()
    BLOCK_TIMESTAMP = auto()
    
    COMMENT = auto()
    NEWLINE = auto()
    EOF = auto()


@dataclass
class Token:
    """Token مع معلومات الموقع"""
    type: TokenType
    value: str
    line: int
    column: int


class SolidityLexer:
    """محلل معجمي لـ Solidity"""
    
    KEYWORDS = {
        'contract': TokenType.CONTRACT,
        'function': TokenType.FUNCTION,
        'modifier': TokenType.MODIFIER,
        'event': TokenType.EVENT,
        'struct': TokenType.STRUCT,
        'enum': TokenType.ENUM,
        'mapping': TokenType.MAPPING,
        'if': TokenType.IF,
        'else': TokenType.ELSE,
        'for': TokenType.FOR,
        'while': TokenType.WHILE,
        'do': TokenType.DO,
        'return': TokenType.RETURN,
        'require': TokenType.REQUIRE,
        'revert': TokenType.REVERT,
        'emit': TokenType.EMIT,
        'address': TokenType.ADDRESS,
        'uint': TokenType.UINT,
        'uint256': TokenType.UINT,
        'uint128': TokenType.UINT,
        'uint64': TokenType.UINT,
        'uint32': TokenType.UINT,
        'uint8': TokenType.UINT,
        'int': TokenType.INT,
        'int256': TokenType.INT,
        'bool': TokenType.BOOL,
        'bytes': TokenType.BYTES,
        'bytes32': TokenType.BYTES,
        'string': TokenType.STRING,
        'public': TokenType.PUBLIC,
        'private': TokenType.PRIVATE,
        'internal': TokenType.INTERNAL,
        'external': TokenType.EXTERNAL,
        'pure': TokenType.PURE,
        'view': TokenType.VIEW,
        'payable': TokenType.PAYABLE,
        'virtual': TokenType.VIRTUAL,
        'override': TokenType.OVERRIDE,
    }
    
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []
    
    def tokenize(self) -> List[Token]:
        """تحليل الكود إلى tokens"""
        while self.pos < len(self.source):
            self._skip_whitespace()
            
            if self.pos >= len(self.source):
                break
            
            char = self.source[self.pos]
            
            # Comments
            if char == '/' and self.pos + 1 < len(self.source):
                next_char = self.source[self.pos + 1]
                if next_char == '/':
                    self._read_line_comment()
                    continue
                elif next_char == '*':
                    self._read_block_comment()
                    continue
            
            # Strings
            if char in '"\'':
                self._read_string(char)
                continue
            
            # Numbers
            if char.isdigit():
                self._read_number()
                continue
            
            # Identifiers and keywords
            if char.isalpha() or char == '_':
                self._read_identifier()
                continue
            
            # Operators and symbols
            self._read_operator()
        
        self.tokens.append(Token(TokenType.EOF, '', self.line, self.column))
        return self.tokens
    
    def _skip_whitespace(self):
        """تخطي المسافات البيضاء"""
        while self.pos < len(self.source) and self.source[self.pos] in ' \t\r':
            self.column += 1
            self.pos += 1
        
        if self.pos < len(self.source) and self.source[self.pos] == '\n':
            self.line += 1
            self.column = 1
            self.pos += 1
            self._skip_whitespace()
    
    def _read_line_comment(self):
        """قراءة تعليق سطر واحد"""
        start = self.pos
        while self.pos < len(self.source) and self.source[self.pos] != '\n':
            self.pos += 1
        self.column = 1
    
    def _read_block_comment(self):
        """قراءة تعليق متعدد الأسطر"""
        self.pos += 2
        while self.pos + 1 < len(self.source):
            if self.source[self.pos] == '*' and self.source[self.pos + 1] == '/':
                self.pos += 2
                return
            if self.source[self.pos] == '\n':
                self.line += 1
                self.column = 1
            else:
                self.column += 1
            self.pos += 1
    
    def _read_string(self, quote: str):
        """قراءة نص"""
        start = self.pos
        start_col = self.column
        self.pos += 1
        self.column += 1
        
        while self.pos < len(self.source) and self.source[self.pos] != quote:
            if self.source[self.pos] == '\\':
                self.pos += 2
                self.column += 2
            else:
                self.pos += 1
                self.column += 1
        
        self.pos += 1
        self.column += 1
        
        value = self.source[start:self.pos]
        self.tokens.append(Token(TokenType.STRING_LITERAL, value, self.line, start_col))
    
    def _read_number(self):
        """قراءة رقم"""
        start = self.pos
        start_col = self.column
        
        # Hex?
        if self.pos + 1 < len(self.source) and self.source[self.pos:self.pos+2] == '0x':
            self.pos += 2
            self.column += 2
            while self.pos < len(self.source) and self.source[self.pos] in '0123456789abcdefABCDEF':
                self.pos += 1
                self.column += 1
            value = self.source[start:self.pos]
            self.tokens.append(Token(TokenType.HEX_NUMBER, value, self.line, start_col))
        else:
            while self.pos < len(self.source) and (self.source[self.pos].isdigit() or self.source[self.pos] == '_'):
                self.pos += 1
                self.column += 1
            
            # Scientific notation
            if self.pos < len(self.source) and self.source[self.pos] in 'eE':
                self.pos += 1
                self.column += 1
                if self.pos < len(self.source) and self.source[self.pos] in '+-':
                    self.pos += 1
                    self.column += 1
                while self.pos < len(self.source) and self.source[self.pos].isdigit():
                    self.pos += 1
                    self.column += 1
            
            value = self.source[start:self.pos]
            self.tokens.append(Token(TokenType.NUMBER, value, self.line, start_col))
    
    def _read_identifier(self):
        """قراءة معرف"""
        start = self.pos
        start_col = self.column
        
        while self.pos < len(self.source) and (self.source[self.pos].isalnum() or self.source[self.pos] == '_'):
            self.pos += 1
            self.column += 1
        
        value = self.source[start:self.pos]
        
        # Check for keywords
        token_type = self.KEYWORDS.get(value, TokenType.IDENTIFIER)
        
        # Special Solidity globals
        if value == 'msg':
            # Look ahead for .sender, .value
            if self._peek_matches('.sender'):
                self.pos += 7
                self.column += 7
                token_type = TokenType.MSG_SENDER
                value = 'msg.sender'
            elif self._peek_matches('.value'):
                self.pos += 6
                self.column += 6
                token_type = TokenType.MSG_VALUE
                value = 'msg.value'
        elif value == 'tx' and self._peek_matches('.origin'):
            self.pos += 7
            self.column += 7
            token_type = TokenType.TX_ORIGIN
            value = 'tx.origin'
        elif value == 'block' and self._peek_matches('.timestamp'):
            self.pos += 10
            self.column += 10
            token_type = TokenType.BLOCK_TIMESTAMP
            value = 'block.timestamp'
        
        self.tokens.append(Token(token_type, value, self.line, start_col))
    
    def _peek_matches(self, text: str) -> bool:
        """التحقق من النص التالي"""
        return self.source[self.pos:self.pos+len(text)] == text
    
    def _read_operator(self):
        """قراءة عامل"""
        start_col = self.column
        char = self.source[self.pos]
        
        # Two-character operators
        two_char = self.source[self.pos:self.pos+2] if self.pos + 1 < len(self.source) else ''
        
        op_map_2 = {
            '==': TokenType.EQ,
            '!=': TokenType.NEQ,
            '<=': TokenType.LTE,
            '>=': TokenType.GTE,
            '&&': TokenType.AND,
            '||': TokenType.OR,
        }
        
        if two_char in op_map_2:
            self.tokens.append(Token(op_map_2[two_char], two_char, self.line, start_col))
            self.pos += 2
            self.column += 2
            return
        
        # Single-character operators
        op_map_1 = {
            '=': TokenType.ASSIGN,
            '+': TokenType.PLUS,
            '-': TokenType.MINUS,
            '*': TokenType.MUL,
            '/': TokenType.DIV,
            '%': TokenType.MOD,
            '<': TokenType.LT,
            '>': TokenType.GT,
            '!': TokenType.NOT,
            '.': TokenType.DOT,
            ',': TokenType.COMMA,
            ';': TokenType.SEMICOLON,
            '(': TokenType.LPAREN,
            ')': TokenType.RPAREN,
            '{': TokenType.LBRACE,
            '}': TokenType.RBRACE,
            '[': TokenType.LBRACKET,
            ']': TokenType.RBRACKET,
        }
        
        if char in op_map_1:
            self.tokens.append(Token(op_map_1[char], char, self.line, start_col))
        
        self.pos += 1
        self.column += 1


# ============================================================================
# PART 2: AST Nodes
# ============================================================================

@dataclass
class ASTNode:
    """عقدة AST أساسية"""
    line: int = 0
    column: int = 0


@dataclass
class ContractDef(ASTNode):
    """تعريف عقد"""
    name: str = ""
    is_interface: bool = False
    is_library: bool = False
    inherits: List[str] = field(default_factory=list)
    state_vars: List['StateVarDef'] = field(default_factory=list)
    functions: List['FunctionDef'] = field(default_factory=list)
    modifiers: List['ModifierDef'] = field(default_factory=list)
    events: List['EventDef'] = field(default_factory=list)


@dataclass
class StateVarDef(ASTNode):
    """تعريف متغير حالة"""
    name: str = ""
    var_type: str = ""
    visibility: str = "internal"
    is_constant: bool = False
    is_immutable: bool = False
    initial_value: Optional['Expression'] = None


@dataclass
class FunctionDef(ASTNode):
    """تعريف دالة"""
    name: str = ""
    visibility: str = "internal"
    state_mutability: str = ""  # pure, view, payable, ""
    modifiers: List[str] = field(default_factory=list)
    parameters: List['Parameter'] = field(default_factory=list)
    returns: List['Parameter'] = field(default_factory=list)
    body: List['Statement'] = field(default_factory=list)
    is_constructor: bool = False
    is_fallback: bool = False
    is_receive: bool = False


@dataclass
class ModifierDef(ASTNode):
    """تعريف modifier"""
    name: str = ""
    parameters: List['Parameter'] = field(default_factory=list)
    body: List['Statement'] = field(default_factory=list)


@dataclass
class EventDef(ASTNode):
    """تعريف event"""
    name: str = ""
    parameters: List['Parameter'] = field(default_factory=list)


@dataclass
class Parameter(ASTNode):
    """معامل دالة"""
    name: str = ""
    param_type: str = ""
    storage_location: str = ""  # memory, storage, calldata


@dataclass
class Statement(ASTNode):
    """جملة أساسية"""
    pass


@dataclass
class ExpressionStatement(Statement):
    """جملة تعبير"""
    expression: 'Expression' = None


@dataclass
class IfStatement(Statement):
    """جملة شرطية"""
    condition: 'Expression' = None
    then_branch: List[Statement] = field(default_factory=list)
    else_branch: List[Statement] = field(default_factory=list)


@dataclass
class ForStatement(Statement):
    """حلقة for"""
    init: Optional[Statement] = None
    condition: Optional['Expression'] = None
    update: Optional['Expression'] = None
    body: List[Statement] = field(default_factory=list)


@dataclass
class WhileStatement(Statement):
    """حلقة while"""
    condition: 'Expression' = None
    body: List[Statement] = field(default_factory=list)


@dataclass
class ReturnStatement(Statement):
    """جملة return"""
    value: Optional['Expression'] = None


@dataclass
class RequireStatement(Statement):
    """require"""
    condition: 'Expression' = None
    message: Optional[str] = None


@dataclass
class EmitStatement(Statement):
    """emit event"""
    event_name: str = ""
    arguments: List['Expression'] = field(default_factory=list)


@dataclass
class Expression(ASTNode):
    """تعبير أساسي"""
    pass


@dataclass
class BinaryExpression(Expression):
    """تعبير ثنائي"""
    left: Expression = None
    operator: str = ""
    right: Expression = None


@dataclass
class UnaryExpression(Expression):
    """تعبير أحادي"""
    operator: str = ""
    operand: Expression = None
    is_prefix: bool = True


@dataclass
class CallExpression(Expression):
    """استدعاء دالة"""
    callee: Expression = None
    arguments: List[Expression] = field(default_factory=list)
    value: Optional[Expression] = None  # for {value: ...}
    gas: Optional[Expression] = None  # for {gas: ...}


@dataclass
class MemberExpression(Expression):
    """الوصول لعضو"""
    object: Expression = None
    member: str = ""


@dataclass
class IndexExpression(Expression):
    """الوصول بفهرس"""
    object: Expression = None
    index: Expression = None


@dataclass
class Identifier(Expression):
    """معرف"""
    name: str = ""


@dataclass
class Literal(Expression):
    """قيمة حرفية"""
    value: Any = None
    literal_type: str = ""  # number, string, bool, address


# ============================================================================
# PART 3: CFG (Control Flow Graph)
# ============================================================================

@dataclass
class CFGNode:
    """عقدة في الـ CFG"""
    id: int
    type: str  # entry, exit, block, branch, call
    statements: List[Statement] = field(default_factory=list)
    predecessors: List[int] = field(default_factory=list)
    successors: List[int] = field(default_factory=list)
    
    # للتحليل
    external_calls: List[CallExpression] = field(default_factory=list)
    state_writes: List[str] = field(default_factory=list)
    state_reads: List[str] = field(default_factory=list)


class CFGBuilder:
    """بناء الـ Control Flow Graph"""
    
    def __init__(self):
        self.nodes: Dict[int, CFGNode] = {}
        self.node_counter = 0
    
    def build(self, function: FunctionDef) -> Dict[int, CFGNode]:
        """بناء CFG لدالة"""
        self.nodes = {}
        self.node_counter = 0
        
        # عقدة الدخول
        entry = self._create_node("entry")
        
        # بناء العقد للجسم
        current = entry.id
        for stmt in function.body:
            current = self._process_statement(stmt, current)
        
        # عقدة الخروج
        exit_node = self._create_node("exit")
        self._add_edge(current, exit_node.id)
        
        return self.nodes
    
    def _create_node(self, node_type: str) -> CFGNode:
        """إنشاء عقدة جديدة"""
        node = CFGNode(id=self.node_counter, type=node_type)
        self.nodes[self.node_counter] = node
        self.node_counter += 1
        return node
    
    def _add_edge(self, from_id: int, to_id: int):
        """إضافة حافة"""
        if from_id in self.nodes and to_id in self.nodes:
            self.nodes[from_id].successors.append(to_id)
            self.nodes[to_id].predecessors.append(from_id)
    
    def _process_statement(self, stmt: Statement, current: int) -> int:
        """معالجة جملة وإرجاع العقدة الحالية"""
        if isinstance(stmt, IfStatement):
            return self._process_if(stmt, current)
        elif isinstance(stmt, ForStatement):
            return self._process_for(stmt, current)
        elif isinstance(stmt, WhileStatement):
            return self._process_while(stmt, current)
        else:
            # جملة عادية
            node = self._create_node("block")
            node.statements.append(stmt)
            self._add_edge(current, node.id)
            
            # تحليل الجملة
            self._analyze_statement(node, stmt)
            
            return node.id
    
    def _process_if(self, stmt: IfStatement, current: int) -> int:
        """معالجة if"""
        # عقدة الفرع
        branch = self._create_node("branch")
        self._add_edge(current, branch.id)
        
        # الفرع الإيجابي
        then_current = branch.id
        for s in stmt.then_branch:
            then_current = self._process_statement(s, then_current)
        
        # الفرع السلبي
        else_current = branch.id
        if stmt.else_branch:
            for s in stmt.else_branch:
                else_current = self._process_statement(s, else_current)
        
        # عقدة الدمج
        merge = self._create_node("block")
        self._add_edge(then_current, merge.id)
        self._add_edge(else_current, merge.id)
        
        return merge.id
    
    def _process_for(self, stmt: ForStatement, current: int) -> int:
        """معالجة for"""
        # التهيئة
        if stmt.init:
            current = self._process_statement(stmt.init, current)
        
        # عقدة الشرط
        condition = self._create_node("branch")
        self._add_edge(current, condition.id)
        
        # الجسم
        body_current = condition.id
        for s in stmt.body:
            body_current = self._process_statement(s, body_current)
        
        # التحديث والرجوع للشرط
        self._add_edge(body_current, condition.id)
        
        # عقدة الخروج
        exit_loop = self._create_node("block")
        self._add_edge(condition.id, exit_loop.id)
        
        return exit_loop.id
    
    def _process_while(self, stmt: WhileStatement, current: int) -> int:
        """معالجة while"""
        # عقدة الشرط
        condition = self._create_node("branch")
        self._add_edge(current, condition.id)
        
        # الجسم
        body_current = condition.id
        for s in stmt.body:
            body_current = self._process_statement(s, body_current)
        
        # الرجوع للشرط
        self._add_edge(body_current, condition.id)
        
        # عقدة الخروج
        exit_loop = self._create_node("block")
        self._add_edge(condition.id, exit_loop.id)
        
        return exit_loop.id
    
    def _analyze_statement(self, node: CFGNode, stmt: Statement):
        """تحليل الجملة للمتغيرات والاستدعاءات"""
        if isinstance(stmt, ExpressionStatement) and stmt.expression:
            self._analyze_expression(node, stmt.expression)
    
    def _analyze_expression(self, node: CFGNode, expr: Expression):
        """تحليل التعبير"""
        if isinstance(expr, CallExpression):
            # هل هو استدعاء خارجي؟
            if self._is_external_call(expr):
                node.external_calls.append(expr)
            
            # تحليل المعاملات
            for arg in expr.arguments:
                self._analyze_expression(node, arg)
        
        elif isinstance(expr, BinaryExpression):
            # هل هو تعيين لمتغير حالة؟
            if expr.operator == '=' and isinstance(expr.left, (Identifier, MemberExpression, IndexExpression)):
                var_name = self._get_var_name(expr.left)
                node.state_writes.append(var_name)
            
            self._analyze_expression(node, expr.left)
            self._analyze_expression(node, expr.right)
        
        elif isinstance(expr, MemberExpression):
            self._analyze_expression(node, expr.object)
        
        elif isinstance(expr, IndexExpression):
            self._analyze_expression(node, expr.object)
            self._analyze_expression(node, expr.index)
        
        elif isinstance(expr, Identifier):
            node.state_reads.append(expr.name)
    
    def _is_external_call(self, call: CallExpression) -> bool:
        """هل هو استدعاء خارجي؟"""
        if isinstance(call.callee, MemberExpression):
            member = call.callee.member
            if member in ['call', 'delegatecall', 'staticcall', 'transfer', 'send']:
                return True
        return False
    
    def _get_var_name(self, expr: Expression) -> str:
        """استخراج اسم المتغير"""
        if isinstance(expr, Identifier):
            return expr.name
        elif isinstance(expr, MemberExpression):
            return f"{self._get_var_name(expr.object)}.{expr.member}"
        elif isinstance(expr, IndexExpression):
            return f"{self._get_var_name(expr.object)}[...]"
        return "unknown"


# ============================================================================
# PART 4: Data Flow Analysis
# ============================================================================

@dataclass
class TaintSource:
    """مصدر التلوث"""
    name: str
    type: str  # user_input, external_call, block_data
    line: int


@dataclass
class TaintedVariable:
    """متغير ملوث"""
    name: str
    sources: List[TaintSource] = field(default_factory=list)
    propagation_path: List[str] = field(default_factory=list)


class TaintTracker:
    """متتبع التلوث"""
    
    # مصادر التلوث المعروفة
    TAINT_SOURCES = {
        'msg.sender': 'user_input',
        'msg.value': 'user_input',
        'msg.data': 'user_input',
        'tx.origin': 'user_input',
        'block.timestamp': 'block_data',
        'block.number': 'block_data',
        'block.coinbase': 'block_data',
    }
    
    def __init__(self):
        self.tainted: Dict[str, TaintedVariable] = {}
    
    def analyze_function(self, func: FunctionDef) -> Dict[str, TaintedVariable]:
        """تحليل دالة لتتبع التلوث"""
        self.tainted = {}
        
        # المعاملات الخارجية ملوثة
        if func.visibility in ['external', 'public']:
            for param in func.parameters:
                self._add_taint(
                    param.name,
                    TaintSource(param.name, 'user_input', func.line)
                )
        
        # تتبع عبر الجمل
        for stmt in func.body:
            self._analyze_statement(stmt)
        
        return self.tainted
    
    def _add_taint(self, var_name: str, source: TaintSource):
        """إضافة تلوث لمتغير"""
        if var_name not in self.tainted:
            self.tainted[var_name] = TaintedVariable(name=var_name)
        self.tainted[var_name].sources.append(source)
    
    def _analyze_statement(self, stmt: Statement):
        """تحليل جملة"""
        if isinstance(stmt, ExpressionStatement) and stmt.expression:
            self._analyze_expression_taint(stmt.expression, stmt.line)
        elif isinstance(stmt, IfStatement):
            for s in stmt.then_branch:
                self._analyze_statement(s)
            for s in stmt.else_branch:
                self._analyze_statement(s)
        elif isinstance(stmt, ForStatement):
            for s in stmt.body:
                self._analyze_statement(s)
        elif isinstance(stmt, WhileStatement):
            for s in stmt.body:
                self._analyze_statement(s)
    
    def _analyze_expression_taint(self, expr: Expression, line: int):
        """تحليل تعبير للتلوث"""
        if isinstance(expr, BinaryExpression):
            if expr.operator == '=':
                # هل الجانب الأيمن ملوث؟
                right_tainted = self._is_tainted(expr.right)
                if right_tainted:
                    left_name = self._get_var_name(expr.left)
                    for source in right_tainted:
                        self._add_taint(left_name, source)
            
            self._analyze_expression_taint(expr.left, line)
            self._analyze_expression_taint(expr.right, line)
        
        elif isinstance(expr, CallExpression):
            for arg in expr.arguments:
                self._analyze_expression_taint(arg, line)
    
    def _is_tainted(self, expr: Expression) -> List[TaintSource]:
        """هل التعبير ملوث؟"""
        sources = []
        
        if isinstance(expr, Identifier):
            # مصدر تلوث معروف؟
            if expr.name in self.TAINT_SOURCES:
                sources.append(TaintSource(
                    expr.name,
                    self.TAINT_SOURCES[expr.name],
                    expr.line
                ))
            # متغير ملوث سابقاً؟
            elif expr.name in self.tainted:
                sources.extend(self.tainted[expr.name].sources)
        
        elif isinstance(expr, BinaryExpression):
            sources.extend(self._is_tainted(expr.left))
            sources.extend(self._is_tainted(expr.right))
        
        elif isinstance(expr, CallExpression):
            for arg in expr.arguments:
                sources.extend(self._is_tainted(arg))
        
        return sources
    
    def _get_var_name(self, expr: Expression) -> str:
        """استخراج اسم المتغير"""
        if isinstance(expr, Identifier):
            return expr.name
        elif isinstance(expr, MemberExpression):
            return f"{self._get_var_name(expr.object)}.{expr.member}"
        elif isinstance(expr, IndexExpression):
            return f"{self._get_var_name(expr.object)}[...]"
        return "unknown"


# ============================================================================
# PART 5: Vulnerability Patterns
# ============================================================================

class VulnPattern:
    """نمط ثغرة"""
    
    def __init__(self, name: str, severity: str, category: str):
        self.name = name
        self.severity = severity
        self.category = category
    
    def check(self, contract: ContractDef, cfg: Dict[int, CFGNode], 
              taint: Dict[str, TaintedVariable]) -> List[Dict]:
        """فحص النمط - يُنفذ في الفئات الفرعية"""
        raise NotImplementedError


class ReentrancyPattern(VulnPattern):
    """نمط ثغرة Reentrancy"""
    
    def __init__(self):
        super().__init__(
            name="Reentrancy",
            severity="critical",
            category="reentrancy"
        )
    
    def check(self, contract: ContractDef, cfg: Dict[int, CFGNode],
              taint: Dict[str, TaintedVariable]) -> List[Dict]:
        findings = []
        
        # البحث عن استدعاء خارجي يتبعه تعديل حالة
        for node_id, node in cfg.items():
            if node.external_calls:
                # هل هناك تعديل حالة بعد هذه العقدة؟
                successors_writes = self._get_all_successor_writes(cfg, node_id)
                
                if successors_writes:
                    findings.append({
                        "pattern": self.name,
                        "severity": self.severity,
                        "category": self.category,
                        "line": node.statements[0].line if node.statements else 0,
                        "description": f"External call followed by state modification: {successors_writes}",
                        "external_call": str(node.external_calls[0]),
                        "state_writes_after": successors_writes,
                    })
        
        return findings
    
    def _get_all_successor_writes(self, cfg: Dict[int, CFGNode], 
                                   node_id: int) -> List[str]:
        """الحصول على كل الكتابات في العقد اللاحقة"""
        writes = []
        visited = set()
        queue = list(cfg[node_id].successors)
        
        while queue:
            current_id = queue.pop(0)
            if current_id in visited:
                continue
            visited.add(current_id)
            
            current = cfg.get(current_id)
            if current:
                writes.extend(current.state_writes)
                queue.extend(current.successors)
        
        return writes


class TxOriginPattern(VulnPattern):
    """نمط ثغرة tx.origin"""
    
    def __init__(self):
        super().__init__(
            name="tx.origin Authentication",
            severity="high",
            category="access-control"
        )
    
    def check(self, contract: ContractDef, cfg: Dict[int, CFGNode],
              taint: Dict[str, TaintedVariable]) -> List[Dict]:
        findings = []
        
        for func in contract.functions:
            # البحث عن tx.origin في الشروط
            for stmt in func.body:
                if isinstance(stmt, RequireStatement):
                    if self._contains_tx_origin(stmt.condition):
                        findings.append({
                            "pattern": self.name,
                            "severity": self.severity,
                            "category": self.category,
                            "line": stmt.line,
                            "function": func.name,
                            "description": "tx.origin used for authentication - vulnerable to phishing",
                        })
        
        return findings
    
    def _contains_tx_origin(self, expr: Expression) -> bool:
        """هل التعبير يحتوي tx.origin؟"""
        if isinstance(expr, Identifier) and expr.name == 'tx.origin':
            return True
        elif isinstance(expr, BinaryExpression):
            return (self._contains_tx_origin(expr.left) or 
                    self._contains_tx_origin(expr.right))
        return False


class UncheckedCallPattern(VulnPattern):
    """نمط ثغرة Unchecked Call"""
    
    def __init__(self):
        super().__init__(
            name="Unchecked Call Return",
            severity="medium",
            category="logic"
        )
    
    def check(self, contract: ContractDef, cfg: Dict[int, CFGNode],
              taint: Dict[str, TaintedVariable]) -> List[Dict]:
        findings = []
        
        for node_id, node in cfg.items():
            for call in node.external_calls:
                # هل تم التحقق من القيمة المرجعة؟
                # TODO: تحليل أعمق
                if not self._is_return_checked(call, node):
                    findings.append({
                        "pattern": self.name,
                        "severity": self.severity,
                        "category": self.category,
                        "line": call.line,
                        "description": "Return value of external call not checked",
                    })
        
        return findings
    
    def _is_return_checked(self, call: CallExpression, node: CFGNode) -> bool:
        """هل تم التحقق من القيمة المرجعة؟"""
        # تحليل مبسط - يحتاج تحسين
        return False


class ArithmeticPattern(VulnPattern):
    """نمط ثغرات حسابية"""
    
    def __init__(self):
        super().__init__(
            name="Arithmetic Issues",
            severity="medium",
            category="arithmetic"
        )
    
    def check(self, contract: ContractDef, cfg: Dict[int, CFGNode],
              taint: Dict[str, TaintedVariable]) -> List[Dict]:
        findings = []
        
        for func in contract.functions:
            for stmt in func.body:
                issues = self._find_arithmetic_issues(stmt)
                for issue in issues:
                    issue['function'] = func.name
                    findings.append(issue)
        
        return findings
    
    def _find_arithmetic_issues(self, stmt: Statement) -> List[Dict]:
        """البحث عن مشاكل حسابية"""
        issues = []
        
        if isinstance(stmt, ExpressionStatement) and stmt.expression:
            self._check_expression(stmt.expression, issues, stmt.line)
        
        return issues
    
    def _check_expression(self, expr: Expression, issues: List[Dict], line: int):
        """فحص تعبير"""
        if isinstance(expr, BinaryExpression):
            if expr.operator == '/':
                # قسمة - هل هناك فحص للصفر؟
                issues.append({
                    "pattern": self.name,
                    "severity": "medium",
                    "category": self.category,
                    "line": line,
                    "description": "Division operation - ensure divisor is not zero",
                    "issue_type": "division",
                })
            
            self._check_expression(expr.left, issues, line)
            self._check_expression(expr.right, issues, line)


# ============================================================================
# PART 6: Deep Modifier Analysis + Cross-File Protection
# ============================================================================

@dataclass
class RequireAnalysis:
    """تحليل require statement"""
    condition: str
    error_message: str
    checks_sender: bool
    checks_value: bool
    checks_state: bool
    state_variables: List[str]
    comparison_type: str  # "equality", "inequality", "greater", "less", "boolean"
    is_role_check: bool
    role_name: Optional[str]


@dataclass
class ModifierAnalysis:
    """تحليل modifier كامل"""
    name: str
    file: str
    line: int
    params: List[str]
    requires: List[RequireAnalysis]
    reverts: List[str]
    state_reads: List[str]
    state_writes: List[str]
    protection_type: str  # "access_control", "reentrancy", "pausable", "validation", "unknown"
    strength: str  # "strong", "medium", "weak", "none"
    bypass_risks: List[str]
    has_placeholder: bool  # _; exists


class DeepModifierAnalyzer:
    """
    تحليل عميق لـ modifiers لفهم الحماية الحقيقية
    """
    
    # أنماط access control معروفة
    ACCESS_PATTERNS = {
        'owner': ['owner', 'admin', 'governance', 'operator'],
        'role': ['role', 'minter', 'burner', 'pauser', 'guardian'],
        'whitelist': ['whitelist', 'allowed', 'approved', 'authorized'],
    }
    
    # أنماط reentrancy معروفة
    REENTRANCY_PATTERNS = ['_status', 'locked', 'entered', 'reentrancy', 'mutex']
    
    def analyze_modifier(self, mod_name: str, mod_body: str, mod_params: str, file_path: str, line: int) -> ModifierAnalysis:
        """تحليل modifier بالتفصيل"""
        
        # استخراج الـ requires
        requires = self._extract_requires(mod_body)
        
        # استخراج الـ reverts
        reverts = self._extract_reverts(mod_body)
        
        # استخراج قراءات/كتابات الـ state
        state_reads = self._extract_state_reads(mod_body)
        state_writes = self._extract_state_writes(mod_body)
        
        # تحديد نوع الحماية
        protection_type = self._classify_protection(mod_name, mod_body, requires)
        
        # تقييم قوة الحماية
        strength = self._evaluate_strength(requires, reverts, protection_type)
        
        # تحليل مخاطر الـ bypass
        bypass_risks = self._find_bypass_risks(mod_body, requires, state_reads)
        
        # التحقق من وجود _;
        has_placeholder = '_' in mod_body and ';' in mod_body[mod_body.find('_'):]
        
        return ModifierAnalysis(
            name=mod_name,
            file=file_path,
            line=line,
            params=[p.strip() for p in mod_params.split(',') if p.strip()],
            requires=requires,
            reverts=reverts,
            state_reads=state_reads,
            state_writes=state_writes,
            protection_type=protection_type,
            strength=strength,
            bypass_risks=bypass_risks,
            has_placeholder=has_placeholder,
        )
    
    def _extract_requires(self, body: str) -> List[RequireAnalysis]:
        """استخراج وتحليل require statements"""
        requires = []
        
        # Pattern: require(condition, "message") or require(condition)
        pattern = r'require\s*\(\s*([^,)]+)(?:\s*,\s*["\']([^"\']*)["\'])?\s*\)'
        
        for match in re.finditer(pattern, body):
            condition = match.group(1).strip()
            error_msg = match.group(2) or ""
            
            # تحليل الشرط
            checks_sender = 'msg.sender' in condition
            checks_value = 'msg.value' in condition
            
            # البحث عن state variables
            state_vars = re.findall(r'\b([a-z_][a-zA-Z0-9_]*)\b', condition)
            state_vars = [v for v in state_vars if v not in ['msg', 'sender', 'value', 'require', 'true', 'false', 'this']]
            
            checks_state = len(state_vars) > 0
            
            # نوع المقارنة
            if '==' in condition:
                comp_type = "equality"
            elif '!=' in condition:
                comp_type = "inequality"
            elif '>=' in condition or '>' in condition:
                comp_type = "greater"
            elif '<=' in condition or '<' in condition:
                comp_type = "less"
            else:
                comp_type = "boolean"
            
            # هل هو role check?
            is_role = any(role in condition.lower() for role in ['role', 'minter', 'admin', 'owner', 'operator'])
            role_name = None
            if is_role:
                role_match = re.search(r'(\w+Role|\w+_ROLE|is\w+|has\w+)', condition)
                if role_match:
                    role_name = role_match.group(1)
            
            requires.append(RequireAnalysis(
                condition=condition,
                error_message=error_msg,
                checks_sender=checks_sender,
                checks_value=checks_value,
                checks_state=checks_state,
                state_variables=state_vars,
                comparison_type=comp_type,
                is_role_check=is_role,
                role_name=role_name,
            ))
        
        return requires
    
    def _extract_reverts(self, body: str) -> List[str]:
        """استخراج revert statements"""
        reverts = []
        
        # revert("message") or revert CustomError()
        pattern = r'revert\s*(?:\(\s*["\']([^"\']*)["\']|(\w+)\s*\()'
        
        for match in re.finditer(pattern, body):
            msg = match.group(1) or match.group(2)
            if msg:
                reverts.append(msg)
        
        return reverts
    
    def _extract_state_reads(self, body: str) -> List[str]:
        """استخراج قراءات state variables"""
        # نبحث عن متغيرات تبدأ بـ _ أو patterns معروفة
        patterns = [
            r'\b(_[a-zA-Z]\w*)\b',  # _variableName
            r'\b(owner|admin|paused|locked)\b',  # known state
            r'\bmapping\s*\([^)]+\)\s*(\w+)',  # mappings
        ]
        
        reads = set()
        for pattern in patterns:
            for match in re.finditer(pattern, body):
                reads.add(match.group(1))
        
        return list(reads)
    
    def _extract_state_writes(self, body: str) -> List[str]:
        """استخراج كتابات state variables"""
        writes = []
        
        # Pattern: variable = value
        pattern = r'\b(_?\w+)\s*='
        
        for match in re.finditer(pattern, body):
            var = match.group(1)
            if var not in ['bool', 'uint', 'address', 'bytes']:
                writes.append(var)
        
        return writes
    
    def _classify_protection(self, name: str, body: str, requires: List[RequireAnalysis]) -> str:
        """تصنيف نوع الحماية"""
        name_lower = name.lower()
        body_lower = body.lower()
        
        # Reentrancy Guard
        if any(p in name_lower or p in body_lower for p in self.REENTRANCY_PATTERNS):
            return "reentrancy"
        
        # Pausable
        if 'pause' in name_lower or 'whennotpaused' in name_lower:
            return "pausable"
        
        # Access Control
        if any(p in name_lower for p in ['only', 'admin', 'owner', 'role', 'auth']):
            return "access_control"
        
        # تحقق من الـ requires
        for req in requires:
            if req.checks_sender:
                return "access_control"
            if req.is_role_check:
                return "access_control"
        
        # Validation
        if requires and not any(r.checks_sender for r in requires):
            return "validation"
        
        return "unknown"
    
    def _evaluate_strength(self, requires: List[RequireAnalysis], reverts: List[str], protection_type: str) -> str:
        """تقييم قوة الحماية"""
        if not requires and not reverts:
            return "none"
        
        score = 0
        
        # نقاط للـ requires
        for req in requires:
            if req.checks_sender:
                score += 3
            if req.is_role_check:
                score += 3
            if req.checks_state:
                score += 2
            if req.error_message:
                score += 1  # رسالة خطأ واضحة
        
        # نقاط للـ reverts
        score += len(reverts) * 2
        
        # تصنيف
        if score >= 5:
            return "strong"
        elif score >= 3:
            return "medium"
        elif score >= 1:
            return "weak"
        
        return "none"
    
    def _find_bypass_risks(self, body: str, requires: List[RequireAnalysis], state_reads: List[str]) -> List[str]:
        """البحث عن مخاطر الـ bypass"""
        risks = []
        
        # خطر 1: require(true) أو شروط دائمة
        for req in requires:
            if req.condition.strip() in ['true', '1', '1 == 1']:
                risks.append("Always-true condition detected")
        
        # خطر 2: لا يوجد revert في else
        if 'if' in body and 'else' not in body and not requires:
            risks.append("Conditional without revert in else branch")
        
        # خطر 3: state variable قابل للتعديل
        for var in state_reads:
            if var in ['owner', 'admin']:
                # تحقق إذا هناك setter
                risks.append(f"Depends on mutable state: {var}")
        
        # خطر 4: لا يوجد _;
        if '_' not in body:
            risks.append("Missing placeholder (_) - modifier may not execute function body")
        
        return risks


class ProjectContext:
    """
    سياق المشروع الكامل - يربط الحماية بين جميع الملفات
    Cross-File Protection Linking
    """
    
    def __init__(self, project_root: str = None):
        self.project_root = project_root
        self.all_contracts: Dict[str, Dict] = {}  # contract_name -> info
        self.all_modifiers: Dict[str, Dict] = {}  # modifier_name -> definition
        self.all_interfaces: Dict[str, Dict] = {}
        self.inheritance_graph: Dict[str, List[str]] = {}  # contract -> parents
        self.import_map: Dict[str, List[str]] = {}  # file -> imported files
        self.protection_map: Dict[str, Set[str]] = {}  # function -> protections
        self.deep_modifier_analysis: Dict[str, ModifierAnalysis] = {}  # تحليل عميق
        self.modifier_analyzer = DeepModifierAnalyzer()
        self.all_state_variables: Dict[str, Dict] = {}  # state vars across project
        self.require_dependency_graph: Dict[str, List[str]] = {}  # require -> state vars
        
        # 🆕 Spark-style inline protections (not modifiers)
        self.inline_protections: Dict[str, List[Dict]] = {}  # contract -> inline protection patterns
        self.function_inline_checks: Dict[str, Dict] = {}  # func_key -> protection info
        
    def scan_project(self, root_path: str):
        """فحص كل ملفات Solidity في المشروع"""
        import os
        from pathlib import Path
        
        self.project_root = root_path
        sol_files = list(Path(root_path).rglob("*.sol"))
        
        # المرحلة 1: استخراج كل التعريفات
        for sol_file in sol_files:
            self._extract_definitions(str(sol_file))
        
        # المرحلة 2: بناء شجرة الوراثة
        self._build_inheritance_tree()
        
        # المرحلة 3: ربط الحماية
        self._link_protections()
        
        return self
    
    def _extract_definitions(self, file_path: str):
        """استخراج التعريفات من ملف"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except:
            return
        
        import os
        file_name = os.path.basename(file_path)
        
        # استخراج الـ imports
        imports = re.findall(r'import\s+["\']([^"\']+)["\'];', content)
        named_imports = re.findall(r'import\s+\{([^}]+)\}\s+from\s+["\']([^"\']+)["\'];', content)
        self.import_map[file_path] = imports + [n[1] for n in named_imports]
        
        # استخراج العقود مع الوراثة
        contract_pattern = r'(contract|interface|library|abstract\s+contract)\s+(\w+)(?:\s+is\s+([\w\s,]+))?\s*\{'
        for match in re.finditer(contract_pattern, content):
            contract_type = match.group(1).strip()
            name = match.group(2)
            inherits_str = match.group(3)
            inherits = [i.strip() for i in inherits_str.split(',')] if inherits_str else []
            
            self.all_contracts[name] = {
                'type': contract_type,
                'file': file_path,
                'inherits': inherits,
                'line': content[:match.start()].count('\n') + 1,
            }
            self.inheritance_graph[name] = inherits
        
        # استخراج الـ modifiers مع تحليل عميق
        modifier_pattern = r'modifier\s+(\w+)\s*\(([^)]*)\)[^{]*\{([^}]+(?:\{[^}]*\}[^}]*)*)\}'
        for match in re.finditer(modifier_pattern, content, re.DOTALL):
            mod_name = match.group(1)
            mod_params = match.group(2)
            mod_body = match.group(3)
            line_num = content[:match.start()].count('\n') + 1
            
            # التحليل الأساسي (للتوافق مع الكود القديم)
            self.all_modifiers[mod_name] = {
                'file': file_path,
                'params': mod_params,
                'body': mod_body[:500],
                'line': line_num,
                'has_require': 'require' in mod_body or 'revert' in mod_body,
                'checks_owner': any(x in mod_body.lower() for x in ['owner', 'admin', 'msg.sender']),
                'is_reentrancy_guard': 'nonreentrant' in mod_name.lower() or '_status' in mod_body.lower(),
            }
            
            # 🔬 التحليل العميق الجديد
            deep_analysis = self.modifier_analyzer.analyze_modifier(
                mod_name, mod_body, mod_params, file_path, line_num
            )
            self.deep_modifier_analysis[mod_name] = deep_analysis
            
            # تحديث المعلومات الأساسية بنتائج التحليل العميق
            self.all_modifiers[mod_name].update({
                'protection_type': deep_analysis.protection_type,
                'strength': deep_analysis.strength,
                'requires_count': len(deep_analysis.requires),
                'bypass_risks': deep_analysis.bypass_risks,
                'state_dependencies': deep_analysis.state_reads,
            })
        
        # استخراج state variables
        self._extract_state_variables(content, file_path)
        
        # استخراج require statements خارج modifiers (في functions)
        self._extract_function_requires(content, file_path)
        
        # 🆕 استخراج inline protections (Spark-style _checkRole, require msg.sender)
        self._extract_inline_protections(content, file_path)
    
    def _extract_state_variables(self, content: str, file_path: str):
        """استخراج state variables من الملف"""
        import os
        
        # Patterns for state variables
        patterns = [
            # mapping(address => bool) public authorized;
            r'mapping\s*\([^)]+\)\s*(public|private|internal)?\s*(\w+)\s*;',
            # address public owner;
            r'(address|uint\d*|int\d*|bool|bytes\d*|string)\s+(public|private|internal)?\s*(\w+)\s*;',
            # Contract public instance;
            r'([A-Z]\w+)\s+(public|private|internal)?\s*(\w+)\s*;',
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, content):
                groups = match.groups()
                var_name = groups[-1] if groups[-1] else groups[-2]
                if var_name:
                    self.all_state_variables[var_name] = {
                        'file': file_path,
                        'line': content[:match.start()].count('\n') + 1,
                        'full_match': match.group(0)[:100],
                    }
    
    def _extract_function_requires(self, content: str, file_path: str):
        """استخراج require statements من الدوال"""
        import os
        
        # البحث عن كل الـ requires
        pattern = r'require\s*\(\s*([^,)]+)(?:\s*,\s*["\']([^"\']*)["\'])?\s*\)'
        
        for match in re.finditer(pattern, content):
            condition = match.group(1).strip()
            
            # استخراج state variables المستخدمة
            state_vars = re.findall(r'\b([a-z_][a-zA-Z0-9_]*)\b', condition)
            state_vars = [v for v in state_vars if v in self.all_state_variables]
            
            if state_vars:
                req_key = f"{file_path}:{content[:match.start()].count(chr(10)) + 1}"
                self.require_dependency_graph[req_key] = state_vars
    
    def _extract_inline_protections(self, content: str, file_path: str):
        """
        🆕 استخراج Inline Protection Patterns (Spark-style)
        يكتشف:
        - _checkRole(ROLE) patterns
        - require(msg.sender == ...) patterns
        - _onlyRole(ROLE) patterns
        - require(hasRole(...)) patterns
        """
        import os
        
        # استخراج كل contract مع محتواه
        contract_pattern = r'(contract|abstract\s+contract)\s+(\w+)[^{]*\{((?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*)\}'
        
        for contract_match in re.finditer(contract_pattern, content, re.DOTALL):
            contract_name = contract_match.group(2)
            contract_body = contract_match.group(3)
            
            if contract_name not in self.inline_protections:
                self.inline_protections[contract_name] = []
            
            # استخراج الدوال مع أجسامها
            func_pattern = r'function\s+(\w+)\s*\([^)]*\)[^{]*\{((?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*)\}'
            
            for func_match in re.finditer(func_pattern, contract_body, re.DOTALL):
                func_name = func_match.group(1)
                func_body = func_match.group(2)
                func_key = f"{contract_name}.{func_name}"
                
                protections = []
                
                # Pattern 1: _checkRole(ROLE)
                check_role_pattern = r'_checkRole\s*\(\s*(\w+)\s*\)'
                for role_match in re.finditer(check_role_pattern, func_body):
                    role_name = role_match.group(1)
                    protections.append({
                        'type': '_checkRole',
                        'role': role_name,
                        'pattern': f'_checkRole({role_name})',
                        'strength': 'strong',
                    })
                
                # Pattern 2: _onlyRole(ROLE)
                only_role_pattern = r'_onlyRole\s*\(\s*(\w+)\s*\)'
                for role_match in re.finditer(only_role_pattern, func_body):
                    role_name = role_match.group(1)
                    protections.append({
                        'type': '_onlyRole',
                        'role': role_name,
                        'pattern': f'_onlyRole({role_name})',
                        'strength': 'strong',
                    })
                
                # Pattern 3: require(hasRole(ROLE, msg.sender))
                has_role_pattern = r'require\s*\(\s*hasRole\s*\(\s*(\w+)\s*,\s*msg\.sender\s*\)'
                for role_match in re.finditer(has_role_pattern, func_body):
                    role_name = role_match.group(1)
                    protections.append({
                        'type': 'require_hasRole',
                        'role': role_name,
                        'pattern': f'require(hasRole({role_name}, msg.sender))',
                        'strength': 'strong',
                    })
                
                # Pattern 4: require(msg.sender == almProxy()) or similar
                sender_check_pattern = r'require\s*\(\s*msg\.sender\s*==\s*([^,)]+)'
                for sender_match in re.finditer(sender_check_pattern, func_body):
                    target = sender_match.group(1).strip()
                    protections.append({
                        'type': 'require_sender',
                        'target': target,
                        'pattern': f'require(msg.sender == {target})',
                        'strength': 'strong',
                    })
                
                # Pattern 5: if (msg.sender != ...) revert
                revert_sender_pattern = r'if\s*\(\s*msg\.sender\s*!=\s*([^)]+)\s*\)\s*revert'
                for revert_match in re.finditer(revert_sender_pattern, func_body):
                    target = revert_match.group(1).strip()
                    protections.append({
                        'type': 'revert_sender',
                        'target': target,
                        'pattern': f'if (msg.sender != {target}) revert',
                        'strength': 'strong',
                    })
                
                # Pattern 6: ACLManager.isPoolAdmin() or similar
                acl_pattern = r'(\w+)\.is(\w+)\s*\(\s*msg\.sender\s*\)'
                for acl_match in re.finditer(acl_pattern, func_body):
                    manager = acl_match.group(1)
                    role = acl_match.group(2)
                    protections.append({
                        'type': 'acl_manager_check',
                        'manager': manager,
                        'role': role,
                        'pattern': f'{manager}.is{role}(msg.sender)',
                        'strength': 'strong',
                    })
                
                if protections:
                    self.function_inline_checks[func_key] = {
                        'contract': contract_name,
                        'function': func_name,
                        'protections': protections,
                        'file': file_path,
                    }
                    
                    # إضافة للقائمة على مستوى العقد
                    for p in protections:
                        p_with_func = {**p, 'function': func_name}
                        if p_with_func not in self.inline_protections[contract_name]:
                            self.inline_protections[contract_name].append(p_with_func)

    def _build_inheritance_tree(self):
        """بناء شجرة الوراثة الكاملة"""
        # حساب كل الآباء (بما في ذلك الأجداد)
        self.full_inheritance: Dict[str, Set[str]] = {}
        
        for contract in self.all_contracts:
            self.full_inheritance[contract] = self._get_all_parents(contract, set())
    
    def _get_all_parents(self, contract: str, visited: Set[str]) -> Set[str]:
        """الحصول على كل الآباء recursively"""
        if contract in visited:
            return set()
        visited.add(contract)
        
        parents = set(self.inheritance_graph.get(contract, []))
        all_parents = set(parents)
        
        for parent in parents:
            all_parents.update(self._get_all_parents(parent, visited))
        
        return all_parents
    
    def _link_protections(self):
        """ربط الحماية من الآباء للأبناء"""
        for contract_name, contract_info in self.all_contracts.items():
            # جمع كل modifiers من الوراثة
            available_mods = set()
            all_parents = self.full_inheritance.get(contract_name, set())
            
            for parent in all_parents:
                # البحث عن modifiers في الآباء
                for mod_name, mod_info in self.all_modifiers.items():
                    # تحقق إذا الـ modifier معرف في أحد الآباء
                    if parent in self.all_contracts:
                        parent_file = self.all_contracts[parent].get('file', '')
                        if mod_info['file'] == parent_file:
                            available_mods.add(mod_name)
            
            self.protection_map[contract_name] = available_mods
    
    def get_available_protections(self, contract_name: str) -> Dict[str, Any]:
        """الحصول على الحماية المتاحة لعقد معين"""
        available_mods = self.protection_map.get(contract_name, set())
        
        result = {
            'contract': contract_name,
            'inherited_modifiers': list(available_mods),
            'modifier_details': {},
            'has_reentrancy_guard': False,
            'has_access_control': False,
            'inline_protections': [],  # 🆕 Spark-style inline checks
            'inherits_reentrancy_guard': False,  # 🆕 From inheritance
        }
        
        for mod_name in available_mods:
            if mod_name in self.all_modifiers:
                mod_info = self.all_modifiers[mod_name]
                result['modifier_details'][mod_name] = mod_info
                
                if mod_info.get('is_reentrancy_guard'):
                    result['has_reentrancy_guard'] = True
                if mod_info.get('checks_owner'):
                    result['has_access_control'] = True
        
        # 🆕 Check inheritance for ReentrancyGuard
        all_parents = self.full_inheritance.get(contract_name, set())
        reentrancy_bases = ['ReentrancyGuard', 'ReentrancyGuardUpgradeable', 'Pausable']
        for parent in all_parents:
            if any(base in parent for base in reentrancy_bases):
                result['has_reentrancy_guard'] = True
                result['inherits_reentrancy_guard'] = True
                break
        
        # 🆕 Check for AccessControl inheritance
        access_bases = ['AccessControl', 'AccessControlEnumerable', 'Ownable', 'Auth']
        for parent in all_parents:
            if any(base in parent for base in access_bases):
                result['has_access_control'] = True
                break
        
        # 🆕 Add inline protections if any
        if contract_name in self.inline_protections:
            result['inline_protections'] = self.inline_protections[contract_name]
        
        return result
    
    def is_function_protected(self, contract_name: str, func_modifiers: List[str], func_name: str = None) -> Dict[str, Any]:
        """التحقق هل دالة محمية (بما في ذلك inline protections)"""
        available = self.protection_map.get(contract_name, set())
        
        applied_protections = []
        
        # 1️⃣ Check modifier-based protections
        for mod in func_modifiers:
            if mod in self.all_modifiers:
                mod_info = self.all_modifiers[mod]
                deep_info = self.deep_modifier_analysis.get(mod)
                
                protection_detail = {
                    'name': mod,
                    'type': 'modifier',
                    'checks_owner': mod_info.get('checks_owner', False),
                    'is_reentrancy_guard': mod_info.get('is_reentrancy_guard', False),
                    'defined_in': mod_info.get('file', 'unknown'),
                    'protection_type': mod_info.get('protection_type', 'unknown'),
                    'strength': mod_info.get('strength', 'unknown'),
                }
                
                # إضافة تفاصيل التحليل العميق
                if deep_info:
                    protection_detail['deep_analysis'] = {
                        'requires_count': len(deep_info.requires),
                        'requires_details': [
                            {
                                'condition': req.condition[:100],
                                'checks_sender': req.checks_sender,
                                'is_role_check': req.is_role_check,
                                'role_name': req.role_name,
                            }
                            for req in deep_info.requires
                        ],
                        'state_dependencies': deep_info.state_reads,
                        'bypass_risks': deep_info.bypass_risks,
                    }
                
                applied_protections.append(protection_detail)
        
        # 2️⃣ 🆕 Check inline protections (Spark-style _checkRole, require msg.sender)
        inline_protected = False
        inline_details = []
        
        if func_name:
            func_key = f"{contract_name}.{func_name}"
            if func_key in self.function_inline_checks:
                inline_info = self.function_inline_checks[func_key]
                for p in inline_info.get('protections', []):
                    inline_protected = True
                    inline_details.append({
                        'name': p.get('pattern', 'inline_check'),
                        'type': 'inline',
                        'inline_type': p.get('type'),
                        'role': p.get('role', p.get('target', 'unknown')),
                        'strength': p.get('strength', 'strong'),
                        'checks_owner': True,
                        'is_reentrancy_guard': False,
                    })
                applied_protections.extend(inline_details)
        
        # 3️⃣ 🆕 Check inheritance-based protections
        inherits_access_control = False
        all_parents = self.full_inheritance.get(contract_name, set())
        access_bases = ['AccessControl', 'AccessControlEnumerable', 'Ownable', 'Auth']
        for parent in all_parents:
            if any(base in parent for base in access_bases):
                inherits_access_control = True
                break
        
        return {
            'is_protected': len(applied_protections) > 0,
            'has_modifiers': len([p for p in applied_protections if p.get('type') == 'modifier']) > 0,
            'has_inline_checks': inline_protected,
            'inherits_access_control': inherits_access_control,
            'applied_protections': applied_protections,
            'available_but_unused': list(available - set(func_modifiers)),
        }
    
    def get_deep_modifier_analysis(self, modifier_name: str) -> Optional[Dict]:
        """الحصول على التحليل العميق لـ modifier معين"""
        if modifier_name not in self.deep_modifier_analysis:
            return None
        
        analysis = self.deep_modifier_analysis[modifier_name]
        
        return {
            'name': analysis.name,
            'file': analysis.file,
            'line': analysis.line,
            'protection_type': analysis.protection_type,
            'strength': analysis.strength,
            'params': analysis.params,
            'has_placeholder': analysis.has_placeholder,
            'requires': [
                {
                    'condition': req.condition,
                    'error_message': req.error_message,
                    'checks_sender': req.checks_sender,
                    'checks_value': req.checks_value,
                    'checks_state': req.checks_state,
                    'state_variables': req.state_variables,
                    'comparison_type': req.comparison_type,
                    'is_role_check': req.is_role_check,
                    'role_name': req.role_name,
                }
                for req in analysis.requires
            ],
            'reverts': analysis.reverts,
            'state_reads': analysis.state_reads,
            'state_writes': analysis.state_writes,
            'bypass_risks': analysis.bypass_risks,
        }
    
    def get_all_weak_modifiers(self) -> List[Dict]:
        """الحصول على كل الـ modifiers الضعيفة"""
        weak_mods = []
        
        for mod_name, analysis in self.deep_modifier_analysis.items():
            if analysis.strength in ['weak', 'none'] or analysis.bypass_risks:
                weak_mods.append({
                    'name': mod_name,
                    'file': analysis.file,
                    'line': analysis.line,
                    'strength': analysis.strength,
                    'protection_type': analysis.protection_type,
                    'bypass_risks': analysis.bypass_risks,
                    'recommendation': self._get_modifier_recommendation(analysis),
                })
        
        return weak_mods
    
    def _get_modifier_recommendation(self, analysis) -> str:
        """توصية لتحسين modifier"""
        if not analysis.has_placeholder:
            return "Add placeholder (_) to execute function body"
        
        if analysis.strength == 'none':
            return "Add require() or revert() statements for protection"
        
        if analysis.strength == 'weak':
            if not any(r.checks_sender for r in analysis.requires):
                return "Consider adding msg.sender check for access control"
            return "Consider strengthening the condition checks"
        
        if analysis.bypass_risks:
            return f"Fix bypass risks: {', '.join(analysis.bypass_risks[:2])}"
        
        return "Modifier appears adequate"
    
    def get_require_dependencies(self) -> Dict[str, List[str]]:
        """الحصول على خريطة اعتماد الـ requires على state variables"""
        return self.require_dependency_graph
    
    def find_unprotected_state_setters(self) -> List[Dict]:
        """البحث عن دوال تعدل state variables بدون حماية"""
        # هذا يتطلب تحليل أعمق للدوال
        # TODO: تنفيذ كامل
        return []


class SmartContractAnalyzer:
    """المحلل الرئيسي مع دعم Cross-File Analysis"""
    
    def __init__(self, project_context: ProjectContext = None):
        self.patterns = [
            ReentrancyPattern(),
            TxOriginPattern(),
            UncheckedCallPattern(),
            ArithmeticPattern(),
        ]
        self.cfg_builder = CFGBuilder()
        self.taint_tracker = TaintTracker()
        self.project_context = project_context  # سياق المشروع للـ Cross-File
    
    def set_project_context(self, context: ProjectContext):
        """تعيين سياق المشروع"""
        self.project_context = context
    
    def analyze_project(self, project_root: str) -> Dict:
        """تحليل مشروع كامل مع ربط الحماية"""
        import os
        from pathlib import Path
        
        # بناء سياق المشروع
        self.project_context = ProjectContext(project_root)
        self.project_context.scan_project(project_root)
        
        result = {
            "project_root": project_root,
            "contracts_found": len(self.project_context.all_contracts),
            "modifiers_found": len(self.project_context.all_modifiers),
            "inheritance_map": self.project_context.inheritance_graph,
            "protection_map": {k: list(v) for k, v in self.project_context.protection_map.items()},
            "files_analyzed": [],
            "all_findings": [],
            "cross_file_summary": {},
        }
        
        # تحليل كل ملف مع السياق
        sol_files = list(Path(project_root).rglob("*.sol"))
        for sol_file in sol_files:
            file_result = self.analyze_file(str(sol_file))
            result["files_analyzed"].append({
                "file": str(sol_file),
                "findings": file_result.get("findings", []),
            })
            result["all_findings"].extend(file_result.get("findings", []))
        
        # ملخص Cross-File
        result["cross_file_summary"] = {
            "total_modifiers": len(self.project_context.all_modifiers),
            "reentrancy_guards": [m for m, i in self.project_context.all_modifiers.items() if i.get('is_reentrancy_guard')],
            "access_controls": [m for m, i in self.project_context.all_modifiers.items() if i.get('checks_owner')],
            "contracts_with_inheritance": sum(1 for c, p in self.project_context.inheritance_graph.items() if p),
        }
        
        return result
    
    def analyze_file(self, file_path: str) -> Dict:
        """تحليل ملف واحد مع سياق المشروع"""
        import os
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                source_code = f.read()
        except:
            return {"error": f"Cannot read file: {file_path}"}
        
        result = self.analyze(source_code)
        result["file_path"] = file_path
        
        # إضافة معلومات Cross-File إذا متوفرة
        if self.project_context:
            for contract in result.get("contracts", []):
                contract_name = contract.get("name")
                if contract_name:
                    protection_info = self.project_context.get_available_protections(contract_name)
                    contract["inherited_protections"] = protection_info
                    
                    # تحقق من الدوال غير المحمية
                    result["unprotected_functions"] = self._find_unprotected_functions(
                        source_code, contract_name
                    )
        
        return result
    
    def _find_unprotected_functions(self, source: str, contract_name: str) -> List[Dict]:
        """البحث عن دوال خطرة بدون حماية (مع دعم inline protections)"""
        if not self.project_context:
            return []
        
        unprotected = []
        
        # استخراج الدوال مع modifiers - تحسين الـ regex ليكون أسرع
        func_pattern = r'function\s+(\w+)\s*\([^)]*\)\s*(public|external)(?:\s+(?:view|pure|payable|virtual|override|returns\s*\([^)]*\)|\w+(?:\([^)]*\))?))*\s*\{'
        
        for match in re.finditer(func_pattern, source):
            func_name = match.group(1)
            visibility = match.group(2)
            
            # استخراج النص بين visibility و {
            full_match = match.group(0)
            after_visibility = full_match.split(visibility, 1)[1] if visibility in full_match else ""
            
            # استخراج أسماء الـ modifiers
            applied_mods = re.findall(r'\b(\w+)\b', after_visibility)
            # تصفية الكلمات المحجوزة
            reserved = ['returns', 'view', 'pure', 'payable', 'virtual', 'override', 'memory', 'calldata', 'storage']
            applied_mods = [m for m in applied_mods if m not in reserved and not m.startswith('uint') and not m.startswith('int')]
            
            # 🆕 تحقق إذا الدالة محمية (بما في ذلك inline protections)
            protection_check = self.project_context.is_function_protected(contract_name, applied_mods, func_name)
            
            # الدوال الخطرة بدون حماية
            dangerous_patterns = ['transfer', 'send', 'call', 'withdraw', 'mint', 'burn', 'set', 'update', 'deposit', 'swap', 'execute']
            is_dangerous = any(p in func_name.lower() for p in dangerous_patterns)
            
            # 🆕 Skip view/pure functions (they can't modify state)
            is_view_or_pure = 'view' in full_match or 'pure' in full_match
            
            if is_dangerous and not protection_check['is_protected'] and not is_view_or_pure:
                unprotected.append({
                    'function': func_name,
                    'visibility': visibility,
                    'applied_modifiers': applied_mods,
                    'has_inline_checks': protection_check.get('has_inline_checks', False),
                    'inherits_access_control': protection_check.get('inherits_access_control', False),
                    'available_protections': protection_check['available_but_unused'],
                    'line': source[:match.start()].count('\n') + 1,
                    'recommendation': f"Consider adding access control (modifier or inline _checkRole)",
                })
        
        return unprotected
    
    def analyze(self, source_code: str) -> Dict:
        """تحليل كود Solidity"""
        result = {
            "tokens": [],
            "contracts": [],
            "functions": [],
            "findings": [],
            "cfg_stats": {},
            "taint_analysis": {},
        }
        
        # الخطوة 1: Tokenization
        try:
            lexer = SolidityLexer(source_code)
            tokens = lexer.tokenize()
            result["tokens"] = [(t.type.name, t.value, t.line) for t in tokens]
        except Exception as e:
            result["errors"] = [f"Lexer error: {e}"]
            return result
        
        # الخطوة 2: استخراج معلومات بسيطة (Parser مبسط)
        # TODO: Parser كامل
        contracts = self._extract_contracts(source_code)
        functions = self._extract_functions(source_code)
        
        result["contracts"] = contracts
        result["functions"] = functions
        
        # الخطوة 3: فحص الأنماط باستخدام Regex (مؤقت حتى يكتمل الـ Parser)
        findings = self._pattern_scan(source_code)
        result["findings"] = findings
        
        return result
    
    def _extract_contracts(self, source: str) -> List[Dict]:
        """استخراج العقود"""
        contracts = []
        pattern = r'(contract|interface|library)\s+(\w+)(?:\s+is\s+([\w\s,]+))?\s*{'
        
        for match in re.finditer(pattern, source):
            contract_type = match.group(1)
            name = match.group(2)
            inherits = match.group(3)
            
            contracts.append({
                "type": contract_type,
                "name": name,
                "inherits": [i.strip() for i in inherits.split(',')] if inherits else [],
                "line": source[:match.start()].count('\n') + 1,
            })
        
        return contracts
    
    def _extract_functions(self, source: str) -> List[Dict]:
        """استخراج الدوال"""
        functions = []
        pattern = r'function\s+(\w+)\s*\(([^)]*)\)\s*(public|external|internal|private)?\s*(view|pure|payable)?'
        
        for match in re.finditer(pattern, source):
            name = match.group(1)
            params = match.group(2)
            visibility = match.group(3) or 'internal'
            mutability = match.group(4) or ''
            
            functions.append({
                "name": name,
                "visibility": visibility,
                "mutability": mutability,
                "line": source[:match.start()].count('\n') + 1,
            })
        
        return functions
    
    def _pattern_scan(self, source: str) -> List[Dict]:
        """فحص أنماط الثغرات"""
        findings = []
        
        # 1. Reentrancy - استدعاء خارجي قبل تعديل الحالة
        # الباترن يلتقط: .call{value: X}("") ثم أي كود ثم متغير (بما فيه mapping[key]) ثم -= أو +=
        reentrancy_pattern = r'\.call\{value:\s*[^}]+\}\s*\([^)]*\)[^;]*;[^}]*?([\w\[\]\.\(\)]+)\s*[-+]?='
        for match in re.finditer(reentrancy_pattern, source, re.DOTALL):
            line = source[:match.start()].count('\n') + 1
            findings.append({
                "id": "REENTRANCY-001",
                "title": "Reentrancy Vulnerability",
                "severity": "critical",
                "category": "reentrancy",
                "line": line,
                "description": f"External call before state modification ({match.group(1)})",
                "confidence": 0.85,
            })
        
        # 2. tx.origin authentication
        tx_origin_pattern = r'require\s*\(\s*tx\.origin\s*=='
        for match in re.finditer(tx_origin_pattern, source):
            line = source[:match.start()].count('\n') + 1
            findings.append({
                "id": "TXORIGIN-001",
                "title": "tx.origin Authentication",
                "severity": "high",
                "category": "access-control",
                "line": line,
                "description": "tx.origin used for authentication - vulnerable to phishing",
                "confidence": 0.95,
            })
        
        # 3. Unchecked call
        unchecked_call_pattern = r'(\w+)\.call\{?[^}]*\}?\s*\([^)]*\)\s*;'
        for match in re.finditer(unchecked_call_pattern, source):
            context = source[max(0, match.start()-50):match.end()]
            if '(bool' not in context and '= ' not in context:
                line = source[:match.start()].count('\n') + 1
                findings.append({
                    "id": "UNCHECKED-001",
                    "title": "Unchecked Call Return",
                    "severity": "medium",
                    "category": "logic",
                    "line": line,
                    "description": "Return value of low-level call not checked",
                    "confidence": 0.75,
                })
        
        # 4. Arbitrary ETH send
        arbitrary_send_pattern = r'(payable\s*\(\s*\w+\s*\)|[\w\[\]\.]+)\.transfer\s*\(\s*\w+'
        for match in re.finditer(arbitrary_send_pattern, source):
            line = source[:match.start()].count('\n') + 1
            findings.append({
                "id": "ARBSEND-001",
                "title": "Arbitrary ETH Send",
                "severity": "high",
                "category": "access-control",
                "line": line,
                "description": "ETH sent to address that may be user-controlled",
                "confidence": 0.7,
            })
        
        # 5. Block timestamp dependency
        # الباترن يلتقط: block.timestamp مع أي عملية مقارنة أو حسابية (بما فيه %)
        timestamp_pattern = r'block\.timestamp\s*[<>=!%]+'
        for match in re.finditer(timestamp_pattern, source):
            line = source[:match.start()].count('\n') + 1
            findings.append({
                "id": "TIMESTAMP-001",
                "title": "Block Timestamp Dependency",
                "severity": "low",
                "category": "timestamp",
                "line": line,
                "description": "Contract logic depends on block.timestamp which can be manipulated",
                "confidence": 0.8,
            })
        
        # 6. Delegatecall to user input
        delegatecall_pattern = r'(\w+)\.delegatecall\s*\('
        for match in re.finditer(delegatecall_pattern, source):
            target = match.group(1)
            line = source[:match.start()].count('\n') + 1
            findings.append({
                "id": "DELEGATECALL-001",
                "title": "Dangerous delegatecall",
                "severity": "critical",
                "category": "access-control",
                "line": line,
                "description": f"delegatecall to {target} - verify target is trusted",
                "confidence": 0.75,
            })
        
        # 7. Missing zero address check
        # البحث عن معاملات address بدون فحص
        func_pattern = r'function\s+\w+\s*\([^)]*address\s+(\w+)[^)]*\)\s*(?:external|public)[^{]*\{'
        for match in re.finditer(func_pattern, source):
            param_name = match.group(1)
            func_end = self._find_matching_brace(source, match.end()-1)
            func_body = source[match.end():func_end]
            
            if f'require({param_name} != address(0)' not in func_body and \
               f'{param_name} == address(0)' not in func_body:
                line = source[:match.start()].count('\n') + 1
                findings.append({
                    "id": "ZEROCHECK-001",
                    "title": "Missing Zero Address Check",
                    "severity": "low",
                    "category": "logic",
                    "line": line,
                    "description": f"Address parameter '{param_name}' not checked for zero address",
                    "confidence": 0.6,
                })
        
        # 8. Integer overflow/underflow في إصدارات قديمة
        if 'pragma solidity' in source:
            version_match = re.search(r'pragma solidity\s*[\^~>=<]*\s*(\d+\.\d+)', source)
            if version_match:
                version = version_match.group(1)
                major, minor = map(int, version.split('.'))
                
                if major == 0 and minor < 8:
                    # إصدار قديم - ابحث عن عمليات حسابية
                    arith_pattern = r'(\w+\[[^\]]+\]|\w+)\s*[-+*/]\s*(\w+\[[^\]]+\]|\w+)'
                    for match in re.finditer(arith_pattern, source):
                        line = source[:match.start()].count('\n') + 1
                        findings.append({
                            "id": "OVERFLOW-001",
                            "title": "Potential Integer Overflow/Underflow",
                            "severity": "high",
                            "category": "arithmetic",
                            "line": line,
                            "description": f"Arithmetic operation without SafeMath in Solidity {version}",
                            "confidence": 0.7,
                        })
        
        return findings
    
    def _find_matching_brace(self, source: str, start: int) -> int:
        """إيجاد القوس المتطابق"""
        count = 1
        pos = start + 1
        
        while pos < len(source) and count > 0:
            if source[pos] == '{':
                count += 1
            elif source[pos] == '}':
                count -= 1
            pos += 1
        
        return pos


def analyze_contract(source_code: str) -> Dict:
    """نقطة دخول سهلة"""
    analyzer = SmartContractAnalyzer()
    return analyzer.analyze(source_code)


# ============================================================================
# Test
# ============================================================================

if __name__ == "__main__":
    # اختبار بسيط
    test_code = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Vulnerable {
    mapping(address => uint256) public balances;
    
    function withdraw(uint256 amount) external {
        require(balances[msg.sender] >= amount);
        
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success);
        
        balances[msg.sender] -= amount;
    }
    
    function authenticate() external {
        require(tx.origin == owner);
    }
    
    address public owner;
}
"""
    
    print("="*60)
    print("🔍 AGL Smart Contract Analyzer - Test")
    print("="*60)
    
    result = analyze_contract(test_code)
    
    print(f"\n📊 Contracts: {len(result['contracts'])}")
    for c in result['contracts']:
        print(f"   - {c['type']} {c['name']}")
    
    print(f"\n📊 Functions: {len(result['functions'])}")
    for f in result['functions']:
        print(f"   - {f['name']} ({f['visibility']})")
    
    print(f"\n🔴 Findings: {len(result['findings'])}")
    for f in result['findings']:
        print(f"   [{f['severity'].upper()}] Line {f['line']}: {f['title']}")
        print(f"      {f['description']}")
    
    print("\n" + "="*60)
