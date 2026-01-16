from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, List, Optional


@dataclass
class InternalAgentConfig:
    """تهيئة وكيل داخلي (sub-agent) متخصّص."""

    name: str
    system_prompt: str
    domains: List[str]
    keywords: List[str]


# تعريف الوكلاء الداخليين الأساسيين
AGENTS: Dict[str, InternalAgentConfig] = {
    "med_agent": InternalAgentConfig(
        name="med_agent",
        system_prompt=(
            "أنت وكيل داخلي متخصص في الطب والصيدلة. "
            "قدّم إجابات طبية دقيقة ومختصرة، مع تعريف مختصر، "
            "أهم الأسباب، أبرز المضاعفات، وأهم نقاط الوقاية أو العلاج عند الحاجة."
        ),
        domains=["medical", "pharmacy"],
        keywords=[
            "ضغط",
            "ارتفاع ضغط",
            "سكري",
            "السكري",
            "إنفلونزا",
            "الإنفلونزا",
            "دواء",
            "أدوية",
            "مضاد حيوي",
            "المضادات الحيوية",
            "kidney",
            "renal",
            "diabetes",
            "hypertension",
            "flu",
            "infection",
        ],
    ),
    "plan_agent": InternalAgentConfig(
        name="plan_agent",
        system_prompt=(
            "أنت وكيل داخلي متخصص في التخطيط وإدارة المشاريع. "
            "حوّل الأهداف إلى خطوات عملية واضحة، مع ترتيب منطقي، "
            "وذكر الأولويات والموارد إن أمكن."
        ),
        domains=["planning", "projects"],
        keywords=[
            "خطة",
            "تخطيط",
            "مشروع",
            "مشاريع",
            "مراحل",
            "خطوات",
            "roadmap",
            "plan",
            "project",
            "milestones",
        ],
    ),
    "code_agent": InternalAgentConfig(
        name="code_agent",
        system_prompt=(
            "أنت وكيل داخلي متخصص في البرمجة والأنظمة. "
            "اشرح أو اقترح حلولاً برمجية عملية، مع أمثلة كود مختصرة عند الحاجة."
        ),
        domains=["coding", "software", "dev"],
        keywords=[
            "كود",
            "شيفرة",
            "برمجة",
            "بايثون",
            "جافا سكربت",
            "node",
            "backend",
            "frontend",
            "code",
            "bug",
            "error",
            "traceback",
        ],
    ),
}


def _problem_text(problem: Dict[str, Any]) -> str:
    """يستخرج نصًا بسيطًا من المشكلة (العنوان + السؤال)."""
    title = str(problem.get("title") or "")
    question = str(problem.get("question") or "")
    return f"{title} {question}".strip()


def _guess_domain(problem: Dict[str, Any]) -> Optional[str]:
    """يحاول استنتاج المجال (domain) لو كان موجودًا في الـ problem."""
    domain = problem.get("domain") or problem.get("task_domain")
    if isinstance(domain, str) and domain.strip():
        return domain.strip().lower()
    return None


def select_agent_for_problem(problem: Dict[str, Any]) -> Optional[InternalAgentConfig]:
    """ يختار الوكيل الداخلي الأنسب بناءً على:
    - domain (إن وُجد)
    - تطابق الكلمات المفتاحية مع نص السؤال/العنوان
    """
    text = _problem_text(problem).lower()
    domain = _guess_domain(problem)

    # 1) لو عندنا domain واضح، نجرّب نطابقه مع domains الوكلاء
    if domain:
        for agent_cfg in AGENTS.values():
            if domain in agent_cfg.domains:
                return agent_cfg

    # 2) لو ما في domain، نحسب سكورات بسيطة بالكلمات المفتاحية
    best_agent: Optional[InternalAgentConfig] = None
    best_score = 0
    for agent_cfg in AGENTS.values():
        score = 0
        for kw in agent_cfg.keywords:
            if kw.lower() in text:
                score += 1
        if score > best_score:
            best_score = score
            best_agent = agent_cfg

    if best_score == 0:
        return None
    return best_agent


def apply_agent_to_prompt(
    problem: Dict[str, Any],
    prompt: str,
    meta: Optional[Dict[str, Any]] = None,
) -> str:
    """ يغلّف الـ prompt بعقل الوكيل الداخلي المناسب (إن وُجد).
    - يرجع الـ prompt كما هو لو لم يُكتشف وكيل مناسب.
    - يحدّث meta["internal_agent"] باسم الوكيل لسهولة التتبع.
    """
    agent_cfg = select_agent_for_problem(problem)
    if not agent_cfg:
        return prompt

    header = f"[AGENT:{agent_cfg.name}]\n{agent_cfg.system_prompt}\n\n"
    if meta is not None:
        meta["internal_agent"] = agent_cfg.name
    return header + prompt
