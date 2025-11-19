import re

def ar_norm(s: str) -> str:
    s = s or ""
    s = re.sub(r"[إأآا]", "ا", s)
    s = re.sub(r"ى", "ي", s)
    s = re.sub(r"ة", "ه", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def any_synonym(s: str, syns) -> bool:
    s = ar_norm(s)
    return any(ar_norm(x) in s for x in syns)
