"""Helper utilities for the DKN: dynamic prompt builder and small helpers."""
from typing import List, Dict


def build_dynamic_prompt(context_claims: List[Dict], user_prompt: str, max_context_items: int = 5) -> str:
    """Build a lightweight dynamic prompt using top context_claims and the user prompt.

    context_claims: list of claim dicts (each should have 'content' and optional 'source')
    """
    lines = []
    if context_claims:
        lines.append('Context:')
        for c in context_claims[:max_context_items]:
            src = c.get('source') or c.get('source', '')
            cont = c.get('content') or c
            # try to extract text
            txt = ''
            if isinstance(cont, dict):
                for key in ('text', 'answer', 'summary'):
                    if key in cont and isinstance(cont[key], str):
                        txt = cont[key]
                        break
                if not txt:
                    txt = str(cont)
            else:
                txt = str(cont)
            lines.append(f"- from {src}: {txt}")
    lines.append('\nUser Prompt:')
    lines.append(user_prompt)
    lines.append('\nInstructions: Answer concisely in Arabic; include sections if relevant.')
    return "\n".join(lines)
