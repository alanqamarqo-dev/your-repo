from typing import Dict


def score_arabic_answer(text: str) -> Dict[str, bool]:
    score = {
        "has_paragraphs": False,
        "has_bullets": False,
        "has_ordering": False,
        "has_medical_disclaimer": False,
    }

    if "\n\n" in text:
        score["has_paragraphs"] = True

    if any(b in text for b in ("•", "▪", "–", "- ")):
        score["has_bullets"] = True

    if any(k in text for k in ("أولًا", "ثانيًا", "ثالثًا", "١-", "2-", "3-")):
        score["has_ordering"] = True

    if "لا تغني هذه المعلومات عن استشارة طبيب مختص" in text:
        score["has_medical_disclaimer"] = True

    return score


def improve_arabic_answer(text: str) -> str:
    if not text:
        return text

    # توحيد الفقرات
    lines = [ln.strip() for ln in text.splitlines()]
    non_empty = [ln for ln in lines if ln]
    text = "\n\n".join(non_empty)

    # إضافة تنبيه طبي فقط إذا بدا النص متعلقًا بمحتوى طبي
    try:
        lower = text.lower()
        medical_keywords = (
            "الإنفلونزا",
            "حمى",
            "أعراض",
            "علاج",
            "دواء",
            "مضاد",
            "استشارة",
            "طبيب",
            "مرض",
            "التهاب",
            "عدوى",
            "ضغط الدم",
            "سكري",
            "فشل الكلوي",
            "مضاعفات",
        )
        looks_medical = any(k.lower() in lower for k in medical_keywords)
    except Exception:
        looks_medical = False

    if looks_medical and "لا تغني هذه المعلومات عن استشارة طبيب مختص" not in text:
        text += "\n\n🔺 تنبيه: لا تغني هذه المعلومات عن استشارة طبيب مختص."

    return text
