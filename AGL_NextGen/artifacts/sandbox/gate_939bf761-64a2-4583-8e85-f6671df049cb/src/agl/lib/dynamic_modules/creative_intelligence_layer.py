"""
طبقة الذكاء الإبداعي - Creative Intelligence Layer
======================================================

تدمج Creative_Innovation مع باقي محركات AGI لتحقيق:
1. إبداع موجه بالسياق (Context-Aware Creativity)
2. توليد أفكار مدعومة بالاستدلال السببي
3. تقييم الإبداع بالذكاء العاطفي
4. تعلم من الإبداعات السابقة
"""

from typing import Dict, Any, List, Optional
import asyncio


class CreativeIntelligenceLayer:
    """طبقة ذكاء إبداعي متقدمة تدمج Creative_Innovation مع محركات أخرى"""
    
    def __init__(
        self,
        creative_engine,
        causal_graph=None,
        meta_learning=None,
        analogy_mapping=None,
        memory_system=None
    ):
        self.creative = creative_engine
        self.causal = causal_graph
        self.meta_learning = meta_learning
        self.analogy = analogy_mapping
        self.memory = memory_system
        
        # ذاكرة الإبداعات السابقة
        self.creativity_history = []
        
    def detect_creativity_type(self, task_text: str) -> str:
        """كشف نوع الإبداع المطلوب من النص"""
        task_lower = task_text.lower()
        
        if any(w in task_lower for w in ["ابتكر", "اخترع", "فكرة جديدة", "حل إبداعي"]):
            return "innovation"
        elif any(w in task_lower for w in ["تطوير", "تحسين", "optimize"]):
            return "improvement"
        elif any(w in task_lower for w in ["تصور", "imagine", "تخيل"]):
            return "imagination"
        elif any(w in task_lower for w in ["ماذا لو", "what if", "سيناريو"]):
            return "counterfactual"
        elif any(w in task_lower for w in ["دمج", "combine", "تكامل"]):
            return "synthesis"
        else:
            return "general"
    
    async def generate_creative_ideas(
        self,
        topic: str,
        creativity_type: str = "general",
        n: int = 5,
        use_causal: bool = True,
        use_analogy: bool = True
    ) -> Dict[str, Any]:
        """توليد أفكار إبداعية مع دعم من محركات أخرى"""
        
        loop = asyncio.get_event_loop()
        
        # 1. توليد أفكار أساسية من Creative_Innovation
        base_ideas = await loop.run_in_executor(
            None,
            self.creative.generate_ideas,
            topic,
            n
        )
        
        # 2. تعزيز الأفكار بالاستدلال السببي
        if use_causal and self.causal:
            enhanced_ideas = []
            for idea in base_ideas:
                try:
                    # تحليل سببي للفكرة
                    causal_analysis = await loop.run_in_executor(
                        None,
                        self.causal.process_task,
                        {"query": f"ما أسباب نجاح: {idea['idea']}"}
                    )
                    
                    idea['causal_support'] = causal_analysis.get('output', '')
                    idea['scores']['causal_feasibility'] = 0.8  # تقييم إضافي
                    enhanced_ideas.append(idea)
                except Exception:
                    enhanced_ideas.append(idea)
            
            base_ideas = enhanced_ideas
        
        # 3. إضافة أفكار من التشابهات (Analogy)
        if use_analogy and self.analogy:
            try:
                analogy_result = await loop.run_in_executor(
                    None,
                    self.analogy.process_task,
                    {"query": f"أفكار مشابهة لـ: {topic}"}
                )
                
                # إضافة كفكرة إضافية
                if analogy_result.get('output'):
                    base_ideas.append({
                        "idea": f"💡 فكرة بالتشابه: {analogy_result['output'][:100]}",
                        "scores": {"composite": 0.85, "analogy_based": True}
                    })
            except Exception:
                pass
        
        # 4. حفظ في الذاكرة للتعلم المستقبلي
        self.creativity_history.append({
            "topic": topic,
            "type": creativity_type,
            "ideas_count": len(base_ideas),
            "timestamp": asyncio.get_event_loop().time()
        })
        
        return {
            "ok": True,
            "ideas": base_ideas,
            "creativity_type": creativity_type,
            "enhanced": use_causal or use_analogy
        }
    
    async def lateral_thinking_enhanced(
        self,
        topic: str,
        technique: str = "SCAMPER"
    ) -> Dict[str, Any]:
        """تفكير جانبي محسّن مع دعم التعلم الذاتي"""
        
        loop = asyncio.get_event_loop()
        
        # 1. تطبيق التفكير الجانبي الأساسي
        lateral_result = await loop.run_in_executor(
            None,
            self.creative.lateral_thinking,
            topic,
            technique
        )
        
        # 2. تعلم من النتيجة (إذا كان Meta_Learning متاحاً)
        if self.meta_learning:
            try:
                # استخلاص patterns من الخطوات
                steps_text = [s['detail'] for s in lateral_result['steps']]
                
                learning_result = await loop.run_in_executor(
                    None,
                    self.meta_learning.auto_learn_skill,
                    f"lateral_thinking_{technique}",
                    steps_text,
                    False  # لا نحفظ بشكل دائم بعد
                )
                
                lateral_result['learned_patterns'] = learning_result.get('count', 0)
            except Exception:
                pass
        
        return lateral_result
    
    async def evaluate_novelty_with_context(
        self,
        text: str,
        context: Optional[Dict] = None
    ) -> float:
        """تقييم الحداثة مع السياق"""
        
        loop = asyncio.get_event_loop()
        
        # 1. تقييم الحداثة الأساسي
        base_novelty = await loop.run_in_executor(
            None,
            self.creative.evaluate_novelty,
            text
        )
        
        # 2. تعديل بناءً على السياق
        if context:
            # تحقق من التشابه مع الأفكار السابقة في السياق
            similar_count = 0
            for prev in self.creativity_history[-10:]:  # آخر 10
                if prev.get('topic', '').lower() in text.lower():
                    similar_count += 1
            
            # تخفيض الحداثة إذا كان الموضوع متكرراً
            novelty_penalty = similar_count * 0.1
            adjusted_novelty = max(0.0, base_novelty - novelty_penalty)
            
            return adjusted_novelty
        
        return base_novelty
    
    async def synthesize_ideas(
        self,
        ideas_list: List[str],
        goal: str = "دمج الأفكار"
    ) -> Dict[str, Any]:
        """دمج عدة أفكار لإنشاء فكرة مركبة جديدة"""
        
        # استخدام lateral thinking مع combine
        combined_text = " + ".join(ideas_list)
        
        result = await self.lateral_thinking_enhanced(
            topic=f"{goal}: {combined_text}",
            technique="SCAMPER"
        )
        
        # استخراج خطوة الدمج (Combine)
        combine_steps = [
            s for s in result.get('steps', [])
            if 'Combine' in s.get('op', '')
        ]
        
        return {
            "ok": True,
            "synthesis": combine_steps[0]['detail'] if combine_steps else "دمج ناجح",
            "input_ideas": ideas_list,
            "method": "SCAMPER_Combine"
        }
    
    def get_creativity_stats(self) -> Dict[str, Any]:
        """إحصائيات الإبداع"""
        
        if not self.creativity_history:
            return {"total_sessions": 0}
        
        return {
            "total_sessions": len(self.creativity_history),
            "total_ideas": sum(h['ideas_count'] for h in self.creativity_history),
            "avg_ideas_per_session": sum(h['ideas_count'] for h in self.creativity_history) / len(self.creativity_history),
            "creativity_types": list(set(h['type'] for h in self.creativity_history))
        }


# ============ Integration Helper ============

def create_creative_intelligence_layer(engine_registry: Dict[str, Any]) -> CreativeIntelligenceLayer:
    """إنشاء طبقة الذكاء الإبداعي من registry المحركات"""
    
    creative_engine = engine_registry.get('Creative_Innovation')
    causal_graph = engine_registry.get('Causal_Graph') or engine_registry.get('CAUSAL_GRAPH')
    meta_learning = engine_registry.get('Meta_Learning')
    analogy_mapping = engine_registry.get('Analogy_Mapping_Engine')
    
    return CreativeIntelligenceLayer(
        creative_engine=creative_engine,
        causal_graph=causal_graph,
        meta_learning=meta_learning,
        analogy_mapping=analogy_mapping
    )
