import re

# match ascii or arabic-indic numerals (٠١٢٣٤٥٦٧٨٩)
NUM = r"[-+]?\d+(?:\.\d+)?"
AR_NUM = r"[\u0660-\u0669\u06F0-\u06F9\d]+(?:[\.,]\d+)?"


def _arabic_indic_to_ascii(s: str) -> str:
    # translate Arabic-Indic digits to ASCII digits
    trans = {}
    # ٠..٩
    for i, c in enumerate("\u0660\u0661\u0662\u0663\u0664\u0665\u0666\u0667\u0668\u0669"):
        trans[ord(c)] = ord(str(i))
    # ۰..۹ (extended Persian/Urdu)
    for i, c in enumerate("\u06F0\u06F1\u06F2\u06F3\u06F4\u06F5\u06F6\u06F7\u06F8\u06F9"):
        trans[ord(c)] = ord(str(i))
    return s.translate(trans)


def parse_entities(text: str) -> dict:
    tx = (text or "").replace("،", ",")
    tx = _arabic_indic_to_ascii(tx)
    kv = {}

    # common patterns like V=12 or جهد=12
    # latin-style assignments
    mV = re.search(r"v\s*=\s*(" + NUM + r")", tx, re.I)
    mI = re.search(r"i\s*=\s*(" + NUM + r")", tx, re.I)
    mR = re.search(r"r\s*=\s*(" + NUM + r")", tx, re.I)
    mT = re.search(r"t\s*=\s*(" + NUM + r")", tx, re.I)
    if mV:
        kv["V"] = float(mV.group(1))
    if mI:
        kv["I"] = float(mI.group(1))
    if mR:
        kv["R"] = float(mR.group(1))
    if mT:
        kv["t"] = float(mT.group(1))

    # Arabic named assignments: الجهد, التيار, المقاومة
    mV2 = re.search(r"(\d+(?:\.\d+)?)\s*(?:فولت|فولط|الجهد)", tx)
    if mV2 and "V" not in kv:
        kv["V"] = float(mV2.group(1))
    mR2 = re.search(r"(\d+(?:\.\d+)?)\s*(?:أوم|اوم|المقاومة)", tx)
    if mR2 and "R" not in kv:
        kv["R"] = float(mR2.group(1))
    mI2 = re.search(r"(\d+(?:\.\d+)?)\s*(?:أمبير|امبير|التيار)", tx)
    if mI2 and "I" not in kv:
        kv["I"] = float(mI2.group(1))

    # fallback: patterns like 'التيار = 5' or 'المقاومة= 10'
    mArI = re.search(r"(التيار)\s*=\s*(" + NUM + r")", tx)
    if mArI and "I" not in kv:
        kv["I"] = float(mArI.group(2))
    mArV = re.search(r"(الجهد)\s*=\s*(" + NUM + r")", tx)
    if mArV and "V" not in kv:
        kv["V"] = float(mArV.group(2))
    mArR = re.search(r"(المقاومة)\s*=\s*(" + NUM + r")", tx)
    if mArR and "R" not in kv:
        kv["R"] = float(mArR.group(2))

    return kv
