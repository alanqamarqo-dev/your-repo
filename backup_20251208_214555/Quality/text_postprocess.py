import re
from typing import Optional

META_PATTERNS = [
    re.compile(r'^\s*\{.*"created_at".*\}.*$', re.UNICODE),
    re.compile(r'^\s*\{.*"model".*qwen2\.5[:]?.*\}.*$', re.UNICODE),
    re.compile(r'^\s*<\|im_start\|>.*$', re.UNICODE),
    re.compile(r'^\s*<\|im_end\|>.*$', re.UNICODE),
]


def _looks_like_pure_metadata(line: str) -> bool:
    line_stripped = line.strip()
    if not line_stripped:
        return False
    # JSON-like line that contains known metadata keys
    if line_stripped.startswith("{") and ("created_at" in line_stripped or "done" in line_stripped or '"model"' in line_stripped):
        return True
    for pat in META_PATTERNS:
        if pat.match(line_stripped):
            return True
    # common JSON fragment markers
    if '"created_at"' in line_stripped or '"done"' in line_stripped or '"model"' in line_stripped:
        return True
    # a line that starts with { but isn't valid text likely a fragment
    if line_stripped.startswith('{') and len(line_stripped) < 200 and ':' in line_stripped:
        return True
    return False


def clean_llm_text(raw: str) -> str:
    """
    ينظف مخرجات النموذج من:
    - أسطر JSON الميتا القادمة من streaming
    - تكرار الـ system prompt أو السؤال الأصلي
    - المسافات الفارغة المتطرفة
    """
    if not raw:
        return raw

    lines = raw.splitlines()
    cleaned: list[str] = []

    for ln in lines:
        # skip pure metadata or JSON fragments
        if _looks_like_pure_metadata(ln):
            continue
        # skip short fragments that are mostly punctuation/JSON-like
        s = ln.strip()
        if s.startswith('{') or s.endswith('}') or (s.count('"') >= 2 and ':' in s and len(s) < 200):
            # consider it a fragment unless it contains substantial Arabic letters
            letters = re.findall(r'[\u0600-\u06FF]', s)
            if len(letters) < 3:
                continue
        cleaned.append(ln)

    text = "\n".join(cleaned).strip()

    # إزالة تكرار البريمب إن حصل
    # مثال: يبدأ بـ "«أنت تعمل كـ "نظام AGL" ..."
    try:
        text = re.sub(
            r'^«?أنت\s+تعمل\s+كـ[\s\S]*?سؤال\s+الباحث:\s*',
            '',
            text,
            flags=re.DOTALL,
        ).strip()
    except Exception:
        # fallback to original text if regex fails
        pass

    # remove obvious repeated header fragments often echoed by streaming
    text = re.sub(r'أنت\s+تعمل\s+كـ\s*"?نظام\s+AGL"?.*?سؤال\s+الباحث:\s*', '', text, flags=re.DOTALL)
    # remove stray JSON-like tokens remaining inline
    # remove inline JSON objects that carry metadata (created_at, done, model, etc.)
    text = re.sub(r'\{[^}]*?(?:"created_at"|"done"|"model")[^}]*?\}', '', text, flags=re.S)
    text = re.sub(r'إجابة\s+موجزة:\s*\{[^}]*\}', '', text)

    # deduplicate the medical disclaimer if repeated
    text = re.sub(r'(🔺\s+تنبيه: لا تغني هذه المعلومات عن استشارة طبيب مختص\.){2,}', r'\1', text)

    # collapse excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text
