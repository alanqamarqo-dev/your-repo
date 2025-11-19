"""Output sanitizer utilities.

Rules implemented (per user request):
- remove control tokens like <|im_start|>, <|im_end|>
- remove forbidden literal tokens (repo_name, file_sep)
- remove non-Arabic fragments except when inside LaTeX ($...$, \[...] ) or known units
- if a long non-Arabic run (>5 chars) appears mid-answer, cut to the main Arabic block
- normalize numbering to Arabic-Indic (١., ٢.) or Latin (1., 2.) per env AGL_NUMBERING
"""
from __future__ import annotations
import os
import re
from typing import Tuple

# Patterns
CTRL_TOKENS = [r"<\|im_start\|>", r"<\|im_end\|>", r"repo_name", r"file_sep"]
CTRL_RE = re.compile('|'.join(CTRL_TOKENS), flags=re.I)

ARABIC_LETTER = re.compile(r"[\u0600-\u06FF]")
LATIN_RUN = re.compile(r"[A-Za-z]{3,}")
CHINESE_RUN = re.compile(r"[\u4e00-\u9fff]+")

LATEX_INLINE = re.compile(r"\$(?:[^$]|\\\$)+\$")
LATEX_BLOCK = re.compile(r"\\\[(?:[^\]]|\\\])+\\\]")

# allowed latin tokens when inside math/units
ALLOWED_UNIT_NAMES = set(["kg", "g", "m", "cm", "mm", "km", "Hz", "kHz", "MHz", "s", "ms", "°C", "K"])

def _strip_control_tokens(s: str) -> str:
    return CTRL_RE.sub('', s)

def _find_arabic_blocks(s: str) -> Tuple[int,int]:
    # return start,end of the largest Arabic block
    blocks = []
    cur = None
    for i, ch in enumerate(s):
        if ARABIC_LETTER.match(ch):
            if cur is None:
                cur = [i, i]
            else:
                cur[1] = i
        else:
            if cur is not None:
                blocks.append(tuple(cur))
                cur = None
    if cur is not None:
        blocks.append(tuple(cur))
    if not blocks:
        return (0,0)
    # return largest block
    blocks.sort(key=lambda b: b[1]-b[0], reverse=True)
    return blocks[0]

def _normalize_numbering(s: str, numbering: str = 'arabic') -> str:
    # convert common numbering forms to desired format
    # detect lines starting with 1. or - or • and unify
    lines = s.splitlines()
    # if there's only one non-empty line and it doesn't already look like a list,
    # don't force enumeration (preserve single-sentence answers requested as such)
    nonempty = [ln for ln in lines if ln.strip()]
    if len(nonempty) <= 1:
        first = nonempty[0] if nonempty else ''
        if not re.match(r'^\s*(?:\d+\.|\(|\-|•|–)\s*', first):
            return s

    out = []
    for line in lines:
        stripped = line.lstrip()
        m = re.match(r'^(?:\d+\.|\(|\-|•|–)\s*(.*)$', stripped)
        if m:
            content = m.group(1)
            out.append(content)
        else:
            out.append(line)
    # now re-enumerate with chosen digits
    enumerated = []
    for i, line in enumerate(out, start=1):
        if numbering == 'arabic':
            sdig = ''.join(['٠١٢٣٤٥٦٧٨٩'[int(d)] for d in str(i)])
            enumerated.append(f"{sdig}. {line.strip()}")
        else:
            enumerated.append(f"{i}. {line.strip()}")
    return '\n'.join(enumerated)

def sanitize_text(text: str, numbering: str | None = None) -> str:
    """Sanitize text according to rules.

    numbering: 'arabic' or 'latin' or None (leave as-is). Default from env AGL_NUMBERING.
    """
    if text is None:
        return ''
    numbering = numbering or os.environ.get('AGL_NUMBERING', 'arabic')
    # remove control tokens
    t = _strip_control_tokens(text)

    # remove explicit control sequences like <|im*|>
    t = re.sub(r"<\|[^>]+\|>", '', t)

    # preserve LaTeX blocks by temporarily replacing them
    latex_parts = {}
    def _store_latex(m):
        key = f"@@LATEX{len(latex_parts)}@@"
        latex_parts[key] = m.group(0)
        return key
    t = LATEX_INLINE.sub(_store_latex, t)
    t = LATEX_BLOCK.sub(_store_latex, t)

    # remove Chinese runs and latin runs except allowed units inside $...$ or known unit words
    t = CHINESE_RUN.sub('', t)

    def _latin_filter(match):
        token = match.group(0)
        if token in ALLOWED_UNIT_NAMES:
            return token
        return ''
    t = LATIN_RUN.sub(_latin_filter, t)

    # If there is a long non-Arabic run in middle, cut to largest Arabic block
    non_ar_runs = [m.group(0) for m in re.finditer(r"[^\u0600-\u06FF\s]{5,}", t)]
    if non_ar_runs:
        start, end = _find_arabic_blocks(t)
        if end > start:
            t = t[start:end+1]

    # restore latex parts
    for k, v in latex_parts.items():
        t = t.replace(k, v)

    # normalize whitespace
    t = re.sub(r"[ \t]+", ' ', t)
    t = re.sub(r"\n{3,}", '\n\n', t)
    t = t.strip()

    # numbering normalization
    if numbering in ('arabic', 'latin'):
        t = _normalize_numbering(t, numbering=numbering)

    return t

def contains_forbidden_run(s: str, max_non_ar_len: int = 5) -> bool:
    m = re.search(r"[^\u0600-\u06FF\s]{%d,}" % (max_non_ar_len,), s)
    return bool(m)
