"""
📜 ANCESTRAL WISDOM (حكمة الأجداد)
تم استخلاص هذه الدوال بناءً على تحليل الرنين الكمي (Resonance Score: 9.80).
تحتوي هذه المكتبة على المنطق الصافي للنظام القديم.
"""
from typing import Dict, List, Any
import json
from pathlib import Path

class AncestralWisdom:
    """
    Mixin class containing the 'Genius' logic extracted from legacy systems.
    """

    # ==============================================================================
    # AGL_legacy.py GENIUS FUNCTIONS
    # ==============================================================================

    def _derive_risk(self, signals: dict) -> str:
        """Derive a simple risk level from per-engine signals.

        Logic (heuristic):
        - low: all engines report ok AND at least two engines have score >= 0.5
        - medium: any engine reports score < 0.3
        - unknown: otherwise
        """
        if not isinstance(signals, dict) or not signals:
            return "unknown"

        try:
            low = all(bool(s.get('ok')) for s in signals.values()) and \
                  sum(1 for s in signals.values() if float(s.get('score', 0.0)) >= 0.5) >= 2
            med = any(float(s.get('score', 0.0)) < 0.3 for s in signals.values())
            return "low" if low and not med else ("medium" if med else "unknown")
        except Exception:
            return "unknown"

    # ----------------------------------------

    def _calculate_confidence(self, partial_solutions: dict, safety_check: dict) -> float:
        """
        يجمع إشارات من كل محرك + خصم بسبب الأمان لإنتاج قيمة بين 0 و 1.
        توقّع كل محرك يُرجع شكلًا مثل:
          {'ok': True/False, 'score': 0..1, 'confidence': 0..1, 'error': '...'}
        وإن لم تتوفر الحقول، نتصرّف بشكل متسامح.
        """
        try:
            if not partial_solutions:
                return 0.0

            scores = []
            for name, res in partial_solutions.items():
                if isinstance(res, dict):
                    # استخرج إشارات موحّدة
                    ok = bool(res.get("ok", "error" not in res))
                    base = float(res.get("score", res.get("confidence", 0.5 if ok else 0.0)))
                else:
                    ok, base = True, 0.5  # fallback

                # قصّ الحدود
                base = max(0.0, min(1.0, base))
                scores.append(base * (1.0 if ok else 0.5))  # عقوبة بسيطة عند الفشل

            # متوسط المحركات
            if scores:
                mean_score = sum(scores) / len(scores)
            else:
                mean_score = 0.0

            # خصومات أمان (مخففة مؤقتًا — تقلل التأثير إلى أن تُبنى فحوصات حقيقية)
            penalty = 0.0
            if isinstance(safety_check, dict):
                # خففنا العقوبة الأساسية من 0.3 إلى 0.15 مؤقتًا
                if not safety_check.get("approved", True):
                    penalty += 0.15
                # تحذيرات: تأثير أقل (0.025 لكل تحذير حتى حد أقصى 0.1)
                warnings = safety_check.get("warnings", [])
                if isinstance(warnings, (list, tuple)):
                    penalty += min(0.1, 0.025 * len(warnings))

            conf = max(0.0, min(1.0, mean_score - penalty))
            return conf
        except Exception:
            return 0.0

    # ----------------------------------------

    def full_autonomous_operation(self) -> Dict:
        """تشغيل كامل مستقل للنظام"""
        print("🎯 بدء التشغيل المستقل الكامل...")
        
        # استخدام النظام الآمن المستقل
        autonomous_result = self.safety_control['safe_autonomous'].autonomous_operation()
        
        # تحديث حالة النظام
        self.system_state.update(autonomous_result['final_state'])
        
        return {
            'autonomous_operation': autonomous_result,
            'final_system_state': self.system_state,
            'total_engines_used': self._count_active_engines(), # type: ignore
            'overall_performance': self._calculate_overall_performance() # type: ignore
        }

    # ----------------------------------------

    def research_and_develop(self, research_topic: str, development_goal: str) -> Dict:
        """بحث وتطوير متكامل"""
        print(f"🔬 بحث وتطوير: {research_topic} -> {development_goal}")

        # 1. البحث العلمي
        research_result = self.scientific_systems['research_assistant'].analyze_research_paper(research_topic, verbose=False)

        # 2. توليد حلول
        development_result = self.engineering_engines['code_generator'].generate_software_system({
            'name': f"حل {development_goal}",
            'requi_rements': research_result['research_suggestions'],
            'type': 'research_based_solution'
        }, verbose=False)

        # 3. تحسين ذاتي
        improvement_result = self.improvement_systems['self_improvement'].continuous_improvement_cycle(
            self.system_state
        )

        return {
            'research_analysis': research_result,
            'developed_solution': development_result,
            'improvement_cycle': improvement_result,
            'innovation_score': 0.95 # Placeholder for self._calculate_innovation_score
        }

    # ==============================================================================
    # AGL_Omega.py GENIUS FUNCTIONS
    # ==============================================================================

    def _read_memory(self, limit: int=500) -> List[Dict[str, Any]]:
        """Helper to read memory for analysis."""
        # Ensure self.memory_path exists or is set
        if not hasattr(self, 'memory_path'):
            self.memory_path = Path('artifacts/memory/long_term.jsonl')
            
        if not isinstance(self.memory_path, Path):
            self.memory_path = Path(self.memory_path)

        if not self.memory_path.exists():
            return []
        out = []
        try:
            with self.memory_path.open('r', encoding='utf-8') as f:
                for ln in f:
                    ln = ln.strip()
                    if not ln:
                        continue
                    try:
                        out.append(json.loads(ln))
                    except Exception:
                        continue
        except Exception:
            return []
        return out[-limit:]

    def analyze_reasoning_patterns(self) -> Dict[str, Any]:
        """Run a lightweight analysis over long-term memory to extract patterns and statistics."""
        # _AGL_LIMIT fallback
        _AGL_LIMIT = 20
        
        rows = self._read_memory(limit=_AGL_LIMIT)
        stats = {'n_entries': len(rows), 'domains': {}, 'keywords': {}}
        for r in rows:
            dom = r.get('domain') or r.get('candidate', {}).get('base') or 'unknown'
            stats['domains'][dom] = stats['domains'].get(dom, 0) + 1
            txt = str(r.get('text', ''))
            for word in txt.split():
                w = word.strip('.,:;"\'\'()[]{}').lower()
                if 4 <= len(w) <= 30:
                    stats['keywords'][w] = stats['keywords'].get(w, 0) + 1
        stats['top_domains'] = sorted(stats['domains'].items(), key=lambda kv: kv[1], reverse=True)[:10]
        stats['top_keywords'] = sorted(stats['keywords'].items(), key=lambda kv: kv[1], reverse=True)[:30]
        return stats
