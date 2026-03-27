"""Analogy Mapping Engine
Simple stub that maps irrigation concepts to traffic concepts.
"""
from typing import Dict, Any
try:
    from agl.lib.core_memory.bridge_singleton import get_bridge
except ImportError:
    def get_bridge(): return None

class AnalogyMappingEngine:
    name = "Analogy_Mapping_Engine"

    def process_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        src = payload.get("source_domain", "")
        tgt = payload.get("target_domain", "")
        draft = payload.get("draft", "")
        prompt_text = (payload.get("text") or draft or "")

        # Triggers that force an education-targeted mapping (expanded to cover
        # common Arabic spellings and English keywords)
        EDU_TRIGGERS = (
            "تعليم", "تعليمي", "التعليم", "التعلّم", "تعلم",
            "education", "learning", "curriculum", "course", "students",
            "مسار تعلم", "مسارات تعلم"
        )

        def _map_to_education() -> Dict[str, Any]:
            edu_pairs = [
                ("تدفّق الماء", "تدفّق المحتوى/المواد"),
                ("صمام/بوابة", "بوابة مناهج/متطلّبات مسبقة (Prereqs)"),
                ("ضغط", "أولوية/جدولة/حمولة الطالب"),
                ("فقدان احتكاك", "احتكاك معرفي/إرهاق/تشتيت"),
                ("خزان", "مخزن محتوى/بنك أسئلة"),
                ("مضخة", "محفّز/تنبيه/مدرّس آلي"),
                ("مقياس تدفّق", "مقياس تقدّم/Throughput تعلّمي"),
                ("تسرّب", "نسيان/فجوات تعلّم"),
            ]
            constraints = [
                "قيود زمنية للطلاب والمعلمين",
                "تفاوت الخلفيات (ضغط غير متجانس)",
                "تكلفة إنتاج/صيانة المحتوى",
                "خطر الاحتكاك المعرفي من مسارات معقّدة",
                "محدودية دقة القياس بالبيانات الضوضائية",
            ]
            steps = [
                "تعريف المخطط الشبكي للمحتوى (وحدات/حزم/مسارات)",
                "تعريف بوابات/Prereqs كصمّامات تتحكم بالمرور",
                "قياس Throughput وLatency وBacklog لكل مسار",
                "تفعيل مسارات تكيفية لتفادي نقاط الاختناق",
                "حلقة تغذية راجعة أسبوعية لضبط الأوزان/الأولويات",
                "لوحات مراقبة بمؤشرات مع عتبات تنبيه وإجراءات تلقائية",
            ]
            metrics = [
                "Throughput (وحدات/أسبوع/طالب) — الهدف ≥ 1.5",
                "Latency (زمن إنجاز وحدة) — الهدف ≤ 5 أيام",
                "Backlog (وحدات معلّقة) — الهدف ≤ 2",
                "Error Rate (إخفاق في الاختبارات القصيرة) — الهدف ≤ 10%",
                "Retention (احتفاظ بعد 14 يومًا) — الهدف ≥ 80%",
            ]
            txt = [
                "روابط التشابه (تعليم):",
                *[f"- {a} ↔ {b}" for a, b in edu_pairs],
                "",
                "قيود/مقايضات:",
                *[f"- {c}" for c in constraints],
                "",
                "خطوات تنفيذ:",
                *[f"{i+1}) {s}" for i, s in enumerate(steps)],
                "",
                "مقاييس أداء:",
                *[f"- {m}" for m in metrics],
            ]
            out = {
                "ok": True,
                "engine": self.name,
                "text": "\n".join(txt),
                "map": edu_pairs,
                "constraints": constraints,
                "steps": steps,
                "metrics": metrics,
                "domain": "education",
                "source_used": bool(draft),
            }
            # Best-effort: persist the analogy map into the ConsciousBridge
            try:
                br = get_bridge()
                trace = payload.get('trace_id') if isinstance(payload, dict) else None
                aid = br.put('analogy_map', {'map': edu_pairs, 'text': out.get('text'), 'domain': 'education'}, trace_id=trace)
                # link to the most recent rationale for the same trace, if any
                if trace:
                    # use strict intersection query
                    try:
                        rats = br.query_by_trace_and_type(trace, 'rationale', scope = 'stm')
                    except Exception:
                        rats = [e for e in br.query(trace_id=trace, scope='stm') if e.get('type') == 'rationale']
                    if rats:
                        # link last rationale -> this analogy
                        last = rats[-1]
                        br.link(last['id'], aid, 'supports_analogy')
            except Exception:
                pass
            return out

        # If prompt contains any education trigger, return the education mapping
        try:
            if any(t in (prompt_text or "").lower() for t in EDU_TRIGGERS):
                return _map_to_education()
        except Exception:
            # Defensive: if normalization fails, fall back to default behavior below
            pass

        # Default mapping (existing behavior)
        mapping = [
            ("تدفق الماء", "تدفق المركبات"),
            ("صمام/بوابة", "إشارة مرور/دوّار"),
            ("ضغط", "كثافة/ازدحام"),
            ("أنبوب/قناة", "حارة/مسار"),
        ]
        lines = [f"- {a} ↔ {b}" for a, b in mapping]
        text = "روابط التشابه:\n" + "\n".join(lines) + "\n\n" + "تطبيق المبدأ: قانون حفظ التدفق، خرائط شبكية."
        out2 = {"ok": True, "engine": self.name, "text": text, "map": mapping, "source_used": bool(draft)}
        try:
            br = get_bridge()
            trace = payload.get('trace_id') if isinstance(payload, dict) else None
            aid = br.put('analogy_map', {'map': mapping, 'text': text, 'domain': 'default'}, trace_id=trace)
            if trace:
                try:
                    rats = br.query_by_trace_and_type(trace, 'rationale', scope = 'stm')
                except Exception:
                    rats = [e for e in br.query(trace_id=trace, scope='stm') if e.get('type') == 'rationale']
                if rats:
                    br.link(rats[-1]['id'], aid, 'supports_analogy')
        except Exception:
            pass
        return out2


def factory():
    return AnalogyMappingEngine()
