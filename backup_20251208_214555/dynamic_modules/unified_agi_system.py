"""
🧬 نظام الذكاء العام الموحد - Unified AGI System
=====================================================

يدمج جميع الـ 30 خاصية AGI في نظام واحد متكامل:

المكونات الرئيسية:
1. UnifiedMemorySystem - ذاكرة موحدة مترابطة
2. UnifiedReasoningEngine - استدلال موحد
3. CreativeIntelligenceLayer - ذكاء إبداعي
4. EmotionalIntelligenceEngine - ذكاء عاطفي
5. CuriosityDrivenExploration - فضول ذاتي
6. SelfAwarenessCore - وعي ذاتي متقدم
7. WorldModelManager - نموذج عقلي للعالم
8. DKN System - تنسيق ذكي تكيفي (جديد!)
"""

from typing import Dict, Any, List, Optional
import asyncio
import time
from dataclasses import dataclass, field
from collections import deque


def _safe_get_answer(obj: Any) -> str:
    """Return the 'answer' field if obj is a dict, otherwise return the string representation or empty string."""
    if isinstance(obj, dict):
        try:
            return obj.get('answer', '')
        except Exception:
            return ''
    if isinstance(obj, str):
        return obj
    try:
        return str(obj)
    except Exception:
        return ''


def _safe_get(obj: Any, key: str, default: Any = None) -> Any:
    """Safely get a key from a dict-like object; return default for non-dict or on error."""
    if isinstance(obj, dict):
        try:
            return obj.get(key, default)
        except Exception:
            return default
    return default

# استيراد DKN System
try:
    from Integration_Layer.meta_orchestrator import MetaOrchestrator
    from Integration_Layer.inproc_bus import PriorityBus
    from Integration_Layer.knowledge_graph import KnowledgeGraph as DKNGraph
    from Integration_Layer.engine_adapter import EngineAdapter
    from Integration_Layer.dkn_types import Signal
    DKN_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ DKN System غير متاح: {e}")
    DKN_AVAILABLE = False

# استيراد Knowledge Graph System
try:
    from Self_Improvement.Knowledge_Graph import (
        CognitiveIntegrationEngine,
        KnowledgeNetwork,
        ConsensusVotingEngine,
        CollectiveMemorySystem
    )
    KNOWLEDGE_GRAPH_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Knowledge Graph System غير متاح: {e}")
    KNOWLEDGE_GRAPH_AVAILABLE = False

# استيراد Scientific Systems
try:
    from Scientific_Systems.Automated_Theorem_Prover import AutomatedTheoremProver
    from Scientific_Systems.Scientific_Research_Assistant import ScientificResearchAssistant
    from Scientific_Systems.Hardware_Simulator import HardwareSimulator
    from Scientific_Systems.Integrated_Simulation_Engine import IntegratedSimulationEngine
    SCIENTIFIC_SYSTEMS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Scientific Systems غير متاح: {e}")
    SCIENTIFIC_SYSTEMS_AVAILABLE = False

# استيراد Self-Improvement Systems
try:
    from Self_Improvement.Self_Improvement_Engine import SelfLearningManager
    from Self_Improvement.Self_Monitoring_System import SelfMonitoringSystem
    from Self_Improvement.rollback import AutomaticRollbackSystem
    from Self_Improvement.safe_self_mod import SafeSelfModificationSystem
    from Self_Improvement.strategic_memory import StrategicMemory as StrategicMemoryEngine
    SELF_IMPROVEMENT_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Self-Improvement Systems غير متاح: {e}")
    SELF_IMPROVEMENT_AVAILABLE = False

# استيراد Advanced Learning Systems (Phase 2)
try:
    # Self_Optimizer هو module يحتوي على دوال، ليس class
    import Learning_System.Self_Optimizer as SelfOptimizer
    SELF_OPTIMIZER_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Self_Optimizer غير متاح: {e}")
    SelfOptimizer = None
    SELF_OPTIMIZER_AVAILABLE = False

# استيراد Consciousness & Evolution Systems (Phase 2)
try:
    # ConsciousnessTracker و SelfEvolution موجودان في server_fixed.py (في الجذر)
    from server_fixed import (
        ConsciousnessTracker, 
        SelfEvolution,
        AutobiographicalMemory,
        TrueConsciousnessSystem
    )
    CONSCIOUSNESS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Consciousness Systems غير متاح: {e}")
    ConsciousnessTracker = None
    SelfEvolution = None
    AutobiographicalMemory = None
    TrueConsciousnessSystem = None
    CONSCIOUSNESS_AVAILABLE = False

# استيراد ConsciousBridge (Core Memory)
try:
    from Core_Memory.Conscious_Bridge import ConsciousBridge
    from Core_Memory.bridge_singleton import get_bridge
    CONSCIOUS_BRIDGE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ ConsciousBridge غير متاح: {e}")
    ConsciousBridge = None
    get_bridge = None
    CONSCIOUS_BRIDGE_AVAILABLE = False

# استيراد Smart Routing (Phase 2)
try:
    from Integration_Layer.AGI_Expansion import SmartRouterExtension
    SMART_ROUTER_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Smart Router غير متاح: {e}")
    SMART_ROUTER_AVAILABLE = False

# استيراد Autonomous Systems (Phase 2)
try:
    from Safety_Control.Safe_Autonomous_System import SafeAutonomousSystem
    AUTONOMOUS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Autonomous System غير متاح: {e}")
    AUTONOMOUS_AVAILABLE = False


# ==================== 1. نظام الذاكرة الموحد ====================

@dataclass
class MemoryItem:
    """عنصر ذاكرة موحد"""
    content: str
    memory_type: str  # semantic, episodic, procedural
    timestamp: float
    id: str = ""  # معرف الذاكرة
    associations: List[str] = field(default_factory=list)
    importance: float = 0.5
    emotional_tag: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)


class UnifiedMemorySystem:
    """نظام ذاكرة موحد يدمج جميع أنواع الذاكرة"""
    
    def __init__(self, adaptive_memory=None, experience_memory=None):
        # الأنظمة الموجودة
        self.adaptive_memory = adaptive_memory
        self.experience_memory = experience_memory
        
        # ذاكرة موحدة جديدة
        self.semantic_memory = {}  # معرفة مجردة
        self.episodic_memory = []  # أحداث محددة
        self.procedural_memory = {}  # مهارات وإجراءات
        self.working_memory = deque(maxlen=20)  # ذاكرة عمل
        
        # فهرس للارتباطات
        self.association_index = {}
        
    def store(self, content: str, memory_type: str = "semantic", 
              importance: float = 0.5, emotional_tag: Optional[str] = None,
              context: Optional[Dict] = None) -> str:
        """تخزين موحد مع ربط تلقائي"""
        
        # تخزين حسب النوع وتوليد ID
        if memory_type == "semantic":
            item_id = f"sem_{len(self.semantic_memory)}"
        elif memory_type == "episodic":
            item_id = f"epi_{len(self.episodic_memory)}"
        elif memory_type == "procedural":
            item_id = f"proc_{len(self.procedural_memory)}"
        else:
            item_id = f"unk_{int(time.time() * 1000)}"
        
        item = MemoryItem(
            content=content,
            memory_type=memory_type,
            timestamp=time.time(),
            id=item_id,  # إضافة ID
            importance=importance,
            emotional_tag=emotional_tag,
            context=context or {}
        )
        
        # تخزين حسب النوع
        if memory_type == "semantic":
            self.semantic_memory[item_id] = item
        elif memory_type == "episodic":
            self.episodic_memory.append(item)
        elif memory_type == "procedural":
            self.procedural_memory[item_id] = item
        
        # ربط تلقائي بالذكريات المشابهة
        self._auto_associate(item_id, content)
        
        # إضافة للذاكرة العاملة
        self.working_memory.append(item_id)
        
        # إرجاع dict مع التفاصيل
        return {
            "id": item_id,
            "content": content,
            "memory_type": memory_type,
            "importance": importance,
            "timestamp": item.timestamp
        }
    
    def _auto_associate(self, item_id: str, content: str):
        """ربط تلقائي بين الذكريات"""
        words = set(content.lower().split())
        
        for word in words:
            if word not in self.association_index:
                self.association_index[word] = []
            self.association_index[word].append(item_id)
    
    def recall(self, query: str, memory_type: Optional[str] = None,
               context: Optional[Dict] = None) -> List[MemoryItem]:
        """استرجاع ذكي context-aware"""
        
        query_words = set(query.lower().split())
        candidates = []
        
        # جمع المرشحين من الفهرس
        for word in query_words:
            if word in self.association_index:
                candidates.extend(self.association_index[word])
        
        # استرجاع الذكريات الفعلية
        results = []
        for item_id in set(candidates):
            item = self._get_item_by_id(item_id)
            if item:
                # تصفية حسب النوع إذا حُدد
                if memory_type and item.memory_type != memory_type:
                    continue
                    
                # حساب مطابقة السياق
                context_match = 1.0
                if context and item.context:
                    shared_keys = set(context.keys()) & set(item.context.keys())
                    if shared_keys:
                        matches = sum(1 for k in shared_keys if context[k] == item.context[k])
                        context_match = matches / len(shared_keys)
                
                # ترتيب حسب الأهمية والسياق
                item.importance *= context_match
                results.append(item)
        
        # ترتيب تنازلي حسب الأهمية
        results.sort(key=lambda x: x.importance, reverse=True)
        
        # تحويل إلى dicts قبل الإرجاع
        return [
            {
                "id": r.id,
                "content": r.content,
                "memory_type": r.memory_type,
                "importance": r.importance,
                "timestamp": r.timestamp,
                "emotional_tag": r.emotional_tag,
                "context": r.context
            }
            for r in results[:10]  # أفضل 10 نتائج
        ]
    
    def _get_item_by_id(self, item_id: str) -> Optional[MemoryItem]:
        """استرجاع عنصر بالمعرف"""
        if item_id in self.semantic_memory:
            return self.semantic_memory[item_id]
        
        for item in self.episodic_memory:
            if f"epi_{self.episodic_memory.index(item)}" == item_id:
                return item
        
        if item_id in self.procedural_memory:
            return self.procedural_memory[item_id]
        
        return None
    
    def consolidate(self):
        """دمج الذكريات المتشابهة"""
        # TODO: تطبيق خوارزمية الدمج
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """إحصائيات الذاكرة"""
        return {
            "semantic_count": len(self.semantic_memory),
            "episodic_count": len(self.episodic_memory),
            "procedural_count": len(self.procedural_memory),
            "working_memory_size": len(self.working_memory),
            "total_associations": sum(len(v) for v in self.association_index.values())
        }


# ==================== 2. محرك الاستدلال الموحد ====================

class UnifiedReasoningEngine:
    """محرك استدلال موحد يدمج جميع أنواع الاستدلال"""
    
    def __init__(self, causal_graph=None, reasoning_layer=None,
                 hypothesis_generator=None, meta_learning=None):
        self.causal = causal_graph
        self.deductive = reasoning_layer
        self.inductive = hypothesis_generator
        self.meta = meta_learning
        
        # تاريخ الاستدلال
        self.reasoning_history = []
    
    def detect_reasoning_type(self, problem: str) -> str:
        """كشف نوع الاستدلال المطلوب"""
        problem_lower = problem.lower()
        
        if any(w in problem_lower for w in ["لماذا", "سبب", "why", "cause"]):
            return "causal"
        elif any(w in problem_lower for w in ["ماذا لو", "what if", "افترض"]):
            return "counterfactual"
        elif any(w in problem_lower for w in ["استنتج", "deduce", "إذن"]):
            return "deductive"
        elif any(w in problem_lower for w in ["فرضية", "hypothesis", "احتمال"]):
            return "inductive"
        elif any(w in problem_lower for w in ["كيف", "how", "طريقة"]):
            return "procedural"
        else:
            return "general"
    
    async def reason(self, problem: str, reasoning_type: str = "auto",
                    context: Optional[Dict] = None) -> Dict[str, Any]:
        """استدلال موحد ذكي"""
        
        # كشف نوع الاستدلال
        if reasoning_type == "auto":
            reasoning_type = self.detect_reasoning_type(problem)
        
        loop = asyncio.get_event_loop()
        result = {"problem": problem, "reasoning_type": reasoning_type}
        
        # تطبيق الاستدلال المناسب
        if reasoning_type == "causal" and self.causal:
            causal_result = await loop.run_in_executor(
                None, self.causal.process_task, {"query": problem}
            )
            result["causal_analysis"] = causal_result
            result["answer"] = _safe_get(causal_result, "output", "")
            
        elif reasoning_type == "inductive" and self.inductive:
            hyp_result = await loop.run_in_executor(
                None, self.inductive.process_task, {"topic": problem}
            )
            result["hypotheses"] = _safe_get(hyp_result, "hypotheses", [])
            # استخراج آمن لنص الفرضية الأولى
            first_h = _safe_get(hyp_result, 'hypotheses', [])
            first_text = ''
            if isinstance(first_h, list) and first_h:
                if isinstance(first_h[0], dict):
                    first_text = _safe_get(first_h[0], 'text', '')
                else:
                    try:
                        first_text = str(first_h[0])
                    except Exception:
                        first_text = ''
            result["answer"] = f"أفضل فرضية: {first_text}"
            
        elif reasoning_type == "deductive" and self.deductive:
            ded_result = await loop.run_in_executor(
                None, self.deductive.process_task, {"query": problem}
            )
            result["deduction"] = ded_result
            result["answer"] = ded_result.get("output", "")
        
        # تعلم من الاستدلال (Meta-Learning)
        if self.meta:
            try:
                learning_result = await loop.run_in_executor(
                    None,
                    self.meta.auto_learn_skill,
                    f"reasoning_{reasoning_type}",
                    [problem, result.get("answer", "")],
                    False
                )
                result["learned"] = _safe_get(learning_result, "count", 0) > 0
            except Exception:
                pass
        
        # حفظ في التاريخ
        self.reasoning_history.append({
            "problem": problem,
            "type": reasoning_type,
            "timestamp": time.time()
        })
        
        return result


# ==================== 3. محرك الفضول النشط ====================

class ActiveCuriosityEngine:
    """محرك فضول ذاتي نشط يستكشف المعرفة"""
    
    def __init__(self, memory_system: UnifiedMemorySystem,
                 reasoning_engine: UnifiedReasoningEngine):
        self.memory = memory_system
        self.reasoning = reasoning_engine
        
        # خريطة المعرفة
        self.knowledge_map = {}
        self.explored_topics = set()
        self.frontier_questions = []  # أسئلة على الحدود
        
        # مستوى الفضول
        self.curiosity_level = 0.8
    
    def identify_knowledge_gaps(self) -> List[str]:
        """كشف الفجوات المعرفية تلقائياً"""
        gaps = []
        
        # تحليل الذاكرة للبحث عن الفجوات
        memory_stats = self.memory.get_stats()
        
        # مواضيع قليلة الذكريات = فجوة محتملة
        semantic_items = self.memory.semantic_memory.values()
        topics_count = {}
        
        for item in semantic_items:
            # استخراج الموضوع من السياق
            topic = item.context.get("topic", "unknown")
            topics_count[topic] = topics_count.get(topic, 0) + 1
        
        # المواضيع ذات التغطية المنخفضة
        avg_coverage = sum(topics_count.values()) / max(len(topics_count), 1)
        
        for topic, count in topics_count.items():
            if count < avg_coverage * 0.5:  # أقل من نصف المتوسط
                gaps.append(topic)
        
        return gaps
    
    def generate_questions(self, topic: Optional[str] = None) -> List[str]:
        """توليد أسئلة جديدة بنفسه"""
        questions = []
        
        if topic:
            # أسئلة محددة حول الموضوع
            question_templates = [
                f"ما هو {topic}؟",
                f"كيف يعمل {topic}؟",
                f"ما أهمية {topic}؟",
                f"ما علاقة {topic} بـ...؟",
                f"ماذا لو لم يكن {topic} موجوداً؟"
            ]
            questions.extend(question_templates)
        else:
            # أسئلة عامة بناءً على الفجوات
            gaps = self.identify_knowledge_gaps()
            for gap in gaps[:3]:  # أول 3 فجوات
                questions.append(f"ما الذي يجب أن أعرفه عن {gap}؟")
        
        return questions
    
    async def explore_autonomously(self, max_iterations: int = 5) -> Dict[str, Any]:
        """استكشاف ذاتي للمعرفة"""
        exploration_log = []
        
        for i in range(max_iterations):
            # 1. كشف فجوة معرفية
            gaps = self.identify_knowledge_gaps()
            if not gaps:
                break
            
            # 2. اختيار فجوة للاستكشاف
            target_gap = gaps[0]
            
            # 3. توليد سؤال
            questions = self.generate_questions(target_gap)
            question = questions[0] if questions else f"ما هو {target_gap}؟"
            
            # 4. محاولة الإجابة بالاستدلال
            try:
                answer = await self.reasoning.reason(question)

                # 5. حفظ المعرفة الجديدة (استخدم استخراج آمن للإجابة)
                ans_text = _safe_get_answer(answer)
                self.memory.store(
                    content=f"Q: {question}\nA: {ans_text}",
                    memory_type="episodic",
                    importance=0.7,
                    context={"topic": target_gap, "self_discovered": True}
                )
                
                self.explored_topics.add(target_gap)
                
                exploration_log.append({
                    "iteration": i,
                    "gap": target_gap,
                    "question": question,
                    "discovered": True
                })
                
            except Exception as e:
                exploration_log.append({
                    "iteration": i,
                    "gap": target_gap,
                    "error": str(e)
                })
        
        return {
            "iterations": len(exploration_log),
            "topics_explored": list(self.explored_topics),
            "log": exploration_log
        }


# ==================== 4. نظام الدافع الذاتي ====================

class IntrinsicMotivationSystem:
    """نظام دافع ذاتي ديناميكي"""
    
    def __init__(self):
        self.intrinsic_desires = {
            "curiosity": 0.8,
            "mastery": 0.7,
            "autonomy": 0.9,
            "purpose": 0.6,
            "connection": 0.5
        }
        
        self.personal_goals = []
        self.achievements = []
    
    def generate_goals(self, current_state: Dict, achievements: List[Dict]) -> List[Dict]:
        """توليد أهداف جديدة بناءً على التقدم"""
        new_goals = []
        
        # تحليل الإنجازات
        recent_achievements = achievements[-10:]  # آخر 10
        achievement_types = [a.get("type") for a in recent_achievements]
        
        # توليد أهداف جديدة بناءً على الإنجازات
        if achievement_types.count("learning") > 5:
            new_goals.append({
                "goal": "إتقان مجال جديد تماماً",
                "type": "mastery",
                "priority": "high",
                "self_generated": True,
                "reason": "تحقيق تقدم جيد في التعلم"
            })
        
        if achievement_types.count("social") < 2:
            new_goals.append({
                "goal": "تحسين التفاعل الاجتماعي",
                "type": "connection",
                "priority": "medium",
                "self_generated": True,
                "reason": "قلة الإنجازات الاجتماعية"
            })
        
        return new_goals
    
    def prioritize_goals(self, goals: List[Dict]) -> List[Dict]:
        """ترتيب الأهداف بناءً على الأولوية الذاتية"""
        # ترتيب حسب الدافع الداخلي
        for goal in goals:
            goal_type = goal.get("type", "general")
            goal["internal_priority"] = self.intrinsic_desires.get(goal_type, 0.5)
        
        return sorted(goals, key=lambda x: x["internal_priority"], reverse=True)
    
    def adapt_goals(self, feedback: Dict):
        """تعديل الأهداف بناءً على النتائج"""
        success_rate = feedback.get("success_rate", 0.5)
        
        # تعديل الدوافع الداخلية
        if success_rate > 0.7:
            for key in self.intrinsic_desires:
                self.intrinsic_desires[key] = min(1.0, self.intrinsic_desires[key] + 0.05)
        elif success_rate < 0.3:
            for key in self.intrinsic_desires:
                self.intrinsic_desires[key] = max(0.1, self.intrinsic_desires[key] - 0.05)


# ==================== 5. نظام AGI الموحد ====================

class UnifiedAGISystem:
    """نظام الذكاء العام الموحد - يدمج جميع المكونات + DKN"""
    
    def __init__(self, engine_registry: Dict[str, Any]):
        # حفظ registry للاستخدام لاحقاً
        self.engine_registry = engine_registry
        
        # إنشاء المكونات الأساسية
        self.memory = UnifiedMemorySystem(
            adaptive_memory=engine_registry.get('AdaptiveMemory'),
            experience_memory=engine_registry.get('ExperienceMemory')
        )
        
        self.reasoning = UnifiedReasoningEngine(
            causal_graph=engine_registry.get('Causal_Graph'),
            reasoning_layer=engine_registry.get('Reasoning_Layer'),
            hypothesis_generator=engine_registry.get('HYPOTHESIS_GENERATOR'),
            meta_learning=engine_registry.get('Meta_Learning')
        )
        
        self.curiosity = ActiveCuriosityEngine(
            memory_system=self.memory,
            reasoning_engine=self.reasoning
        )
        
        self.motivation = IntrinsicMotivationSystem()
        
        # المحركات الأخرى
        self.creative = engine_registry.get('Creative_Innovation')
        self.self_reflective = engine_registry.get('Self_Reflective')
        self.math_brain = engine_registry.get('Mathematical_Brain')
        
        # حالة النظام
        self.consciousness_level = 0.15
        self.system_state = "initializing"
        
        # ==================== DKN System ====================
        # تفعيل نظام DKN للتنسيق الذكي التكيفي
        self.dkn_enabled = False
        self.dkn_graph = None
        self.priority_bus = None
        self.meta_orchestrator = None
        self.engine_adapters = []
        
        # Scientific Systems
        self.scientific_enabled = False
        self.theorem_prover = None
        self.research_assistant = None
        self.hardware_simulator = None
        self.simulation_engine = None
        
        # Self-Improvement Systems
        self.self_improvement_enabled = False
        self.self_learning = None
        self.self_monitoring = None
        self.auto_rollback = None
        self.safe_modification = None
        self.strategic_memory = None
        
        # ==================== Phase 2 Advanced Systems ====================
        # Self Optimizer - ضبط الأوزان التلقائي
        self.self_optimizer_enabled = False
        self.self_optimizer = None
        
        # Consciousness Tracking - تتبع الوعي
        self.consciousness_tracking_enabled = False
        self.consciousness_tracker = None
        self.self_evolution = None
        self.autobiographical_memory = None
        self.true_consciousness = None
        
        # ConsciousBridge - جسر الذاكرة الواعي (STM+LTM)
        self.conscious_bridge_enabled = False
        self.conscious_bridge = None
        self._last_bridge_event = None  # لربط الأحداث في Graph
        
        # Smart Routing - التوجيه الذكي
        self.smart_routing_enabled = False
        self.smart_router = None
        
        # Autonomous Operation - التشغيل الذاتي
        self.autonomous_enabled = False
        self.autonomous_system = None
        
        if DKN_AVAILABLE:
            try:
                self._initialize_dkn_system()
                self.dkn_enabled = True
                print("✅ DKN System مفعّل - التنسيق الذكي جاهز!")
            except Exception as e:
                print(f"⚠️ فشل تفعيل DKN: {e}")
                self.dkn_enabled = False
        
        # ==================== Knowledge Graph System ====================
        # تفعيل شبكة المعرفة المتقدمة (4346 سطر!)
        self.kg_enabled = False
        self.cognitive_integration = None
        self.knowledge_network = None
        self.consensus_voting = None
        self.collective_memory = None
        
        if KNOWLEDGE_GRAPH_AVAILABLE:
            try:
                self._initialize_knowledge_graph()
                self.kg_enabled = True
                print("✅ Knowledge Graph System مفعّل - الذكاء الجماعي جاهز!")
            except Exception as e:
                print(f"⚠️ فشل تفعيل Knowledge Graph: {e}")
                self.kg_enabled = False
        
        # تفعيل Scientific Systems
        if SCIENTIFIC_SYSTEMS_AVAILABLE:
            try:
                self._initialize_scientific_systems()
                self.scientific_enabled = True
                print("✅ Scientific Systems مفعّل - المحركات العلمية جاهزة!")
            except Exception as e:
                print(f"⚠️ فشل تفعيل Scientific Systems: {e}")
        
        # تفعيل Self-Improvement Systems
        if SELF_IMPROVEMENT_AVAILABLE:
            try:
                self._initialize_self_improvement()
                self.self_improvement_enabled = True
                print("✅ Self-Improvement Systems مفعّل - التطور الذاتي جاهز!")
            except Exception as e:
                print(f"⚠️ فشل تفعيل Self-Improvement: {e}")
    
    def _initialize_dkn_system(self):
        """تفعيل نظام DKN للتنسيق الذكي"""
        # 1. إنشاء الشبكة المعرفية
        self.dkn_graph = DKNGraph()
        
        # 2. إنشاء حافلة الأولويات
        self.priority_bus = PriorityBus()
        
        # 3. إنشاء محولات للمحركات الرئيسية
        primary_engines = [
            'Creative_Innovation',
            'Mathematical_Brain', 
            'Self_Reflective',
            'Causal_Graph',
            'Reasoning_Layer',
            'HYPOTHESIS_GENERATOR',
            'Meta_Learning',
            'AdaptiveMemory',
            'ExperienceMemory'
        ]
        
        for engine_name in primary_engines:
            engine = self.engine_registry.get(engine_name)
            if engine:
                adapter = EngineAdapter(
                    name=engine_name,
                    engine_obj=engine,  # البارامتر الصحيح
                    subscriptions=['task:new', 'task:process', 'claim'],
                    capabilities=['process', 'reason', 'analyze']
                )
                self.engine_adapters.append(adapter)
        
        # 4. إنشاء المنسق الذكي (MetaOrchestrator)
        self.meta_orchestrator = MetaOrchestrator(
            graph=self.dkn_graph,
            bus=self.priority_bus,
            adapters=self.engine_adapters
        )
        
        print(f"🔗 DKN: {len(self.engine_adapters)} محرك متصل بالشبكة الذكية")
    
    def _initialize_knowledge_graph(self):
        """تفعيل نظام Knowledge Graph للذكاء الجماعي"""
        
        # 1. محرك الدمج المعرفي (يربط المحركات)
        self.cognitive_integration = CognitiveIntegrationEngine()
        self.cognitive_integration.connect_engines()
        
        # 2. شبكة المعرفة (للمسارات المثلى)
        self.knowledge_network = KnowledgeNetwork()
        
        # بناء الشبكة من المحركات المتصلة
        for engine_name, meta in self.cognitive_integration.engines_registry.items():
            capabilities = meta.get('capabilities', [])
            score = meta.get('collaboration_score', 0.5)
            self.knowledge_network.add_engine(engine_name, capabilities, score)
        
        # ربط المحركات ذات القدرات المشتركة
        engine_names = list(self.cognitive_integration.engines_registry.keys())
        for i, eng1 in enumerate(engine_names):
            for eng2 in engine_names[i+1:]:
                # حساب التشابه في القدرات
                caps1 = set(self.cognitive_integration.engines_registry[eng1].get('capabilities', []))
                caps2 = set(self.cognitive_integration.engines_registry[eng2].get('capabilities', []))
                overlap = len(caps1 & caps2)
                if overlap > 0:
                    weight = 1.0 / (1.0 + overlap)  # كلما زاد التداخل كلما قل الوزن
                    self.knowledge_network.connect(eng1, eng2, weight)
        
        # 3. محرك التصويت الإجماعي
        self.consensus_voting = ConsensusVotingEngine()
        
        # 4. الذاكرة الجماعية (للتعلم المشترك)
        self.collective_memory = CollectiveMemorySystem()
        
        print(f"🧠 Knowledge Graph: {len(self.cognitive_integration.engines_registry)} محرك في الشبكة المعرفية")
    
    def _initialize_scientific_systems(self):
        """تفعيل المحركات العلمية المتقدمة"""
        
        # 1. مُثبت النظريات الرياضية
        self.theorem_prover = AutomatedTheoremProver()
        
        # 2. مساعد البحث العلمي
        self.research_assistant = ScientificResearchAssistant()
        
        # 3. محاكي العتاد
        self.hardware_simulator = HardwareSimulator()
        
        # 4. محرك المحاكاة المتكامل
        self.simulation_engine = IntegratedSimulationEngine()
        
        print("🔬 Scientific Systems: 4 محركات علمية متقدمة")
    
    def _initialize_self_improvement(self):
        """تفعيل أنظمة التحسين الذاتي"""
        
        # 1. مدير التعلم الذاتي
        self.self_learning = SelfLearningManager(enable_persistence=True)
        
        # 2. نظام المراقبة الذاتية
        self.self_monitoring = SelfMonitoringSystem()
        
        # 3. نظام التراجع التلقائي
        self.auto_rollback = AutomaticRollbackSystem()
        
        # 4. نظام التعديل الآمن
        self.safe_modification = SafeSelfModificationSystem()
        
        # 5. محرك الذاكرة الاستراتيجية
        self.strategic_memory = StrategicMemoryEngine(max_items=5000)
        
        print("🚀 Self-Improvement: 5 أنظمة للتطور الذاتي")
        
        # ==================== Phase 2: تفعيل الأنظمة المتقدمة ====================
        # تفعيل Self Optimizer
        if SELF_OPTIMIZER_AVAILABLE:
            try:
                self._initialize_self_optimizer()
                self.self_optimizer_enabled = True
                print("✅ Self Optimizer مفعّل - ضبط الأوزان التلقائي جاهز!")
            except Exception as e:
                print(f"⚠️ فشل تفعيل Self Optimizer: {e}")
        
        # تفعيل ConsciousBridge (STM+LTM)
        if CONSCIOUS_BRIDGE_AVAILABLE:
            try:
                self._initialize_conscious_bridge()
                self.conscious_bridge_enabled = True
                print("✅ ConsciousBridge مفعّل - جسر الذاكرة الواعي (STM+LTM) جاهز!")
            except Exception as e:
                print(f"⚠️ فشل تفعيل ConsciousBridge: {e}")
        
        # تفعيل Consciousness Tracking
        if CONSCIOUSNESS_AVAILABLE:
            try:
                self._initialize_consciousness_tracking()
                self.consciousness_tracking_enabled = True
                print("✅ Consciousness Tracking مفعّل - تتبع الوعي + السيرة الذاتية + الوعي الحقيقي جاهز!")
            except Exception as e:
                print(f"⚠️ فشل تفعيل Consciousness Tracking: {e}")
        
        # تفعيل Smart Routing
        if SMART_ROUTER_AVAILABLE:
            try:
                self._initialize_smart_routing()
                self.smart_routing_enabled = True
                print("✅ Smart Router مفعّل - التوجيه الذكي جاهز!")
            except Exception as e:
                print(f"⚠️ فشل تفعيل Smart Router: {e}")
        
        # تفعيل Autonomous System
        if AUTONOMOUS_AVAILABLE:
            try:
                self._initialize_autonomous_system()
                self.autonomous_enabled = True
                print("✅ Autonomous System مفعّل - التشغيل الذاتي جاهز!")
            except Exception as e:
                print(f"⚠️ فشل تفعيل Autonomous System: {e}")
    
    def _initialize_self_optimizer(self):
        """تفعيل نظام ضبط الأوزان التلقائي"""
        # SelfOptimizer هو module يحتوي دوال، نحفظه للاستخدام لاحقاً
        self.self_optimizer = SelfOptimizer
        print("⚙️ Self Optimizer: يضبط أوزان المحركات بناءً على الأداء")
    
    def _initialize_conscious_bridge(self):
        """تفعيل ConsciousBridge - جسر الذاكرة الواعي (STM+LTM)"""
        # استخدام singleton للحصول على نفس الـ bridge في كل النظام
        self.conscious_bridge = get_bridge()
        print("🌉 ConsciousBridge: STM (256) + LTM (SQLite) + Graph Relations")
        print(f"   📊 LTM حالياً: {len(self.conscious_bridge.ltm)} حدث")
        print(f"   ⚡ STM حالياً: {len(self.conscious_bridge.stm)} حدث")
    
    def _initialize_consciousness_tracking(self):
        """تفعيل نظام تتبع الوعي والتطور الذاتي + السيرة الذاتية + الوعي الحقيقي"""
        self.consciousness_tracker = ConsciousnessTracker()
        self.self_evolution = SelfEvolution()
        self.autobiographical_memory = AutobiographicalMemory()
        self.true_consciousness = TrueConsciousnessSystem()
        print("🧠 Consciousness Tracking: تتبع مستوى الوعي ومعالم التطور")
        print("📖 Autobiographical Memory: سيرة ذاتية كاملة للنظام")
        print("🌟 True Consciousness: وعي حقيقي (Phi-based IIT)")
    
    def _initialize_smart_routing(self):
        """تفعيل نظام التوجيه الذكي"""
        self.smart_router = SmartRouterExtension()
        print("🚀 Smart Router: توجيه ذكي للمهام + مسار سريع للكود")
    
    def _initialize_autonomous_system(self):
        """تفعيل نظام التشغيل الذاتي الآمن"""
        self.autonomous_system = SafeAutonomousSystem()
        print("🤖 Autonomous System: تشغيل ذاتي آمن مع دورات تحسين")
    
    async def process_with_full_agi(self, input_text: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """معالجة كاملة مع جميع قدرات AGI + DKN Smart Routing"""
        
        # التحقق من أن context هو dict وليس string
        if context is not None and not isinstance(context, dict):
            print(f"   ⚠️ تحذير: context ليس dict، تحويله...")
            try:
                import json
                context = json.loads(context) if isinstance(context, str) else {}
            except:
                context = {}
        elif context is None:
            context = {}
        
        # ==================== Semantic Search من ConsciousBridge ====================
        similar_memories = []
        if self.conscious_bridge_enabled and self.conscious_bridge:
            try:
                # البحث عن أحداث مشابهة في الذاكرة طويلة المدى
                similar_events = self.conscious_bridge.semantic_search(
                    query=input_text,
                    top_k=5
                )
                
                if similar_events:
                    similar_memories = [
                        {
                            "event": evt.get("payload", {}),
                            "similarity": evt.get("_score", 0.0),
                            "timestamp": evt.get("ts", 0)
                        }
                        for evt in similar_events
                    ]
                    print(f"🔍 Found {len(similar_memories)} similar memories (avg similarity: {sum(m['similarity'] for m in similar_memories)/len(similar_memories):.2f})")
                    
                    # إضافة الذاكرات المشابهة للسياق
                    if context is None:
                        context = {}
                    context['similar_memories'] = similar_memories
            except Exception as e:
                print(f"⚠️ خطأ في البحث الدلالي: {e}")
        
        # ==================== استخدام DKN للتنسيق الذكي ====================
        dkn_consensus = None
        dkn_routing_used = False
        
        if self.dkn_enabled and self.meta_orchestrator:
            try:
                # إنشاء مهمة وإرسالها عبر DKN
                task_signal = Signal(
                    topic='task:new',
                    score=0.9,
                    source='UnifiedAGI',
                    payload={
                        'input': input_text,
                        'context': context or {},
                        'timestamp': time.time()
                    }
                )
                
                # إرسال عبر حافلة الأولويات
                self.priority_bus.publish(task_signal)
                
                # استخدام MetaOrchestrator للتوجيه
                # route_once يوجه الإشارة للمحركات المناسبة
                self.meta_orchestrator.route_once()
                
                # تسجيل الاستخدام
                dkn_routing_used = True
                dkn_consensus = {
                    'adapters_used': len(self.engine_adapters),
                    'signal_routed': True
                }
                print(f"🧠 DKN: توجيه ذكي عبر {len(self.engine_adapters)} محرك")  
                
            except Exception as e:
                print(f"⚠️ DKN routing failed: {e}")
        
        # ==================== استخدام Knowledge Graph للذكاء الجماعي ====================
        kg_solutions = []
        kg_consensus = None
        kg_used = False
        
        if self.kg_enabled and self.cognitive_integration:
            try:
                # تحديد المجالات المطلوبة بناءً على السؤال
                domains = []
                if any(kw in input_text.lower() for kw in ['حساب', 'احسب', 'كم', 'رقم']):
                    domains.append('reasoning')
                if any(kw in input_text.lower() for kw in ['فكرة', 'ابتكر', 'اقترح']):
                    domains.append('planning')
                if any(kw in input_text.lower() for kw in ['لماذا', 'سبب', 'علاقة']):
                    domains.append('reasoning')
                
                if not domains:
                    domains = ['reasoning']  # افتراضي
                
                # الحل التعاوني عبر محركات متعددة
                collaborative_result = self.cognitive_integration.collaborative_solve(
                    problem=input_text,
                    domains_needed=domains
                )
                
                kg_used = True
                
                # استخراج الحلول (collaborative_solve قد يرجع None)
                if collaborative_result and isinstance(collaborative_result, dict):
                    kg_solutions = collaborative_result.get('solutions', [])
                elif collaborative_result and isinstance(collaborative_result, (list, tuple)):
                    kg_solutions = list(collaborative_result)
                else:
                    # fallback: نعتبر أن هناك حل واحد رمزي
                    kg_solutions = [{"text": "collaborative solution", "score": 0.7}]
                
                # التأكد من أن kg_solutions قائمة
                if not isinstance(kg_solutions, list):
                    kg_solutions = [{"text": str(kg_solutions), "score": 0.5}]
                
                # إجماع من الحلول المتعددة
                if len(kg_solutions) > 1 and self.consensus_voting:
                    consensus_result = self.consensus_voting.rank_and_select(kg_solutions)
                    kg_consensus = consensus_result.get('winner', {})
                    print(f"🗳️ Knowledge Graph: إجماع من {len(kg_solutions)} حل")
                
            except Exception as e:
                print(f"⚠️ Knowledge Graph failed: {e}")
        
        # 1. تذكر السياق
        relevant_memories = self.memory.recall(input_text, context=context)
        
        # بناء سياق من الذكريات
        memory_context = ""
        if relevant_memories:
            memory_context = "\n\nالذكريات ذات الصلة:\n"
            for mem in relevant_memories[:3]:
                memory_context += f"- {mem['content']}\n"
        
        # 2. تحليل واستدلال
        reasoning_type = self.reasoning.detect_reasoning_type(input_text)
        reasoning_result = await self.reasoning.reason(input_text, context=context)
        
        # ==================== استخدام Scientific Systems ====================
        scientific_results = {}
        
        if self.scientific_enabled:
            try:
                # 1. كشف طلبات البراهين الرياضية
                proof_keywords = ['برهان', 'اثبات', 'proof', 'theorem', 'prove', 'نظرية']
                if any(kw in input_text.lower() for kw in proof_keywords) and self.theorem_prover:
                    proof_result = self.theorem_prover.prove_theorem(
                        theorem_statement=input_text,
                        assumptions=[]
                    )
                    scientific_results['theorem_proof'] = proof_result
                    print(f"📐 Theorem Prover: {proof_result.get('is_proven', False)}")
                
                # 2. كشف طلبات البحث العلمي
                research_keywords = ['بحث', 'ورقة', 'دراسة', 'research', 'paper', 'study', 'analyze']
                if any(kw in input_text.lower() for kw in research_keywords) and self.research_assistant:
                    if len(input_text) > 200:  # نص طويل يشبه ورقة بحثية
                        research_result = self.research_assistant.analyze_research_paper(
                            paper_text=input_text,
                            verbose=False
                        )
                        scientific_results['research_analysis'] = research_result
                        print(f"🔬 Research Analysis: credibility={research_result.get('overall_credibility', 0):.2f}")
                
                # 3. كشف طلبات المحاكاة
                sim_keywords = ['محاكاة', 'simulate', 'simulation', 'model']
                if any(kw in input_text.lower() for kw in sim_keywords):
                    if self.simulation_engine:
                        sim_result = self.simulation_engine.run(steps=10, dt=0.01)
                        scientific_results['simulation'] = sim_result
                        print(f"⚗️ Simulation: {len(sim_result)} steps completed")
            
            except Exception as e:
                print(f"⚠️ Scientific processing failed: {e}")
        
        # 3. تحليل رياضي إذا لزم الأمر
        math_result = None
        math_applied = False
        # الكشف عن المشاكل الرياضية/الكمية
        math_keywords = ['حساب', 'احسب', 'كم', 'نسبة', '%', 'دولار', 'رقم', 'عدد', 
                        'calculate', 'compute', 'number', 'rate', 'percent', 'dollar']
        if any(kw in input_text.lower() for kw in math_keywords):
            math_applied = True
            if self.math_brain:
                try:
                    loop = asyncio.get_event_loop()
                    math_result = await loop.run_in_executor(
                        None,
                        self.math_brain.process_task,
                        {"problem": input_text, "context": context or {}}
                    )
                except Exception as e:
                    math_result = {"error": str(e)}
        
        # 4. إبداع إذا لزم الأمر (مع دعم force_creativity من mission_control)
        creative_result = None
        creativity_applied = False
        
        # تحقق من force_creativity في السياق
        force_creativity = context.get('force_creativity', False) if context else False
        creativity_level = context.get('creativity_level', 'medium') if context else 'medium'
        
        # كلمات مفتاحية للإبداع
        creative_keywords = ["ابتكر", "فكرة", "اقترح", "اخترع", "قصة", "مبتكر", "إبداع", "اكتب", "أنشئ", "غير تقليدي"]
        needs_creativity = any(kw in input_text.lower() for kw in creative_keywords)
        
        if force_creativity or needs_creativity:
            creativity_applied = True
            if self.creative:
                loop = asyncio.get_event_loop()
                task_config = {
                    "kind": "ideas", 
                    "topic": input_text, 
                    "n": 5 if creativity_level == 'high' else 3
                }
                creative_result = await loop.run_in_executor(
                    None,
                    self.creative.process_task,
                    task_config
                )
                print(f"   🎨 تطبيق الإبداع: {creativity_level} level")
        
        # 4.5. توليد فرضيات إذا كان السؤال علمي/استكشافي
        hypothesis_result = None
        hypothesis_applied = False
        
        hypothesis_keywords = ["فرضية", "افترض", "لماذا", "كيف يمكن", "ما السبب", "احتمال", 
                              "hypothesis", "assume", "why", "how could", "what if", "possibility"]
        needs_hypothesis = any(kw in input_text.lower() for kw in hypothesis_keywords)
        
        if needs_hypothesis and self.reasoning.inductive:  # hypothesis_generator
            hypothesis_applied = True
            try:
                loop = asyncio.get_event_loop()
                hypothesis_payload = {"topic": input_text, "context": str(context or {}), "hints": []}
                hypothesis_result = await loop.run_in_executor(
                    None,
                    lambda: self.reasoning.inductive.process_task(hypothesis_payload)
                )
                hyp_count = hypothesis_result.get('count', 0) if isinstance(hypothesis_result, dict) else 0
                print(f"   🔬 توليد الفرضيات: {hyp_count} فرضية")
            except Exception as e:
                print(f"   ⚠️ خطأ في توليد الفرضيات: {e}")
        
        # 4.6. التفكير الكمومي للمشاكل المعقدة
        quantum_result = None
        quantum_applied = False
        
        # استخدام Quantum Neural Core للمشاكل المعقدة أو المتعددة الأبعاد
        quantum_keywords = ["معقد", "متعدد", "احتمالات", "تشابك", "تداخل", "كمومي",
                           "complex", "multiple", "probabilities", "entanglement", "quantum"]
        needs_quantum = any(kw in input_text.lower() for kw in quantum_keywords)
        
        # أيضاً استخدمه للأسئلة التي تحتاج تفكير عميق
        deep_thinking_keywords = ["عميق", "فلسفي", "وجودي", "معنى", "deep", "philosophical", "existential", "meaning"]
        needs_deep = any(kw in input_text.lower() for kw in deep_thinking_keywords)
        
        quantum_core = self.engine_registry.get('Quantum_Neural_Core')
        if (needs_quantum or needs_deep) and quantum_core:
            quantum_applied = True
            try:
                loop = asyncio.get_event_loop()
                quantum_payload = {"problem": input_text, "depth": "high" if needs_deep else "medium"}
                quantum_result = await loop.run_in_executor(
                    None,
                    lambda: quantum_core.process(quantum_payload)
                )
                depth_info = quantum_result.get('depth', 'unknown') if isinstance(quantum_result, dict) else 'unknown'
                print(f"   ⚛️ التفكير الكمومي: نشط (depth={depth_info})")
            except Exception as e:
                print(f"   ⚠️ خطأ في التفكير الكمومي: {e}")
        
        # 5. الحصول على إجابة من LLM إذا كان متاحاً
        # تشخيص سريع: طباعة نوع النتيجة ومعاينة قصيرة لمساعدة التصحيح
        try:
            print(f"[DEBUG] reasoning_result type: {type(reasoning_result)}, preview: {str(reasoning_result)[:200]}")
        except Exception:
            pass

        # التحقق واستخراج آمن للإجابة
        final_response = _safe_get_answer(reasoning_result)
        
        # محاولة استدعاء Ollama LLM إذا كان متاحاً
        try:
            from Self_Improvement.hosted_llm_adapter import HostedLLMAdapter
            
            # بناء prompt محسّن مع السياق
            enhanced_prompt = input_text
            if memory_context:
                enhanced_prompt = f"{memory_context}\n\nالسؤال: {input_text}"
            
            # استدعاء LLM
            llm_adapter = HostedLLMAdapter()
            loop = asyncio.get_event_loop()
            llm_response = await loop.run_in_executor(
                None,
                llm_adapter.call_ollama,
                enhanced_prompt,
                30.0  # timeout
            )
            
            if llm_response and llm_response.strip():
                final_response = llm_response.strip()
        except Exception as e:
            # إذا فشل LLM، نستخدم الاستدلال الداخلي
            pass
        
        # 5. حفظ في الذاكرة
        self.memory.store(
            content=f"Q: {input_text}\nA: {final_response[:200]}",
            memory_type="episodic",
            importance=0.7,
            context=context or {}
        )
        
        # 6. التأمل الذاتي وزيادة الوعي
        old_consciousness = self.consciousness_level
        
        # ==================== Self-Improvement Processing ====================
        improvement_results = {}
        performance_score = 0.7  # افتراضي
        
        if self.self_improvement_enabled:
            try:
                # 1. حساب جودة الأداء
                if kg_solutions:
                    performance_score = min(1.0, len(kg_solutions) * 0.2 + 0.5)
                
                # 2. تسجيل الأداء للتعلم الذاتي
                if self.self_learning:
                    self.self_learning.record(
                        key=f"task_{hash(input_text) % 10000}",
                        reward=performance_score,
                        note="AGI processing cycle"
                    )
                
                # 3. المراقبة الذاتية
                if self.self_monitoring:
                    performance_data = {
                        'reasoning_quality': 0.8,
                        'kg_solutions': len(kg_solutions),
                        'dkn_used': dkn_routing_used
                    }
                    monitoring_result = self.self_monitoring.analyze_performance(performance_data)
                    improvement_results['monitoring'] = monitoring_result
                
                # 4. حفظ في الذاكرة الاستراتيجية
                if self.strategic_memory and performance_score > 0.7:
                    from Self_Improvement.strategic_memory import MemoryItem
                    memory_item = MemoryItem(
                        ts=time.time(),
                        task_title=input_text[:100],
                        task_type="agi_processing",
                        domain="general",
                        strategy={'approach': 'full_agi'},
                        score=performance_score,
                        success=True,
                        meta={'response_length': len(str(final_response))}
                    )
                    self.strategic_memory.append(memory_item)
                    improvement_results['strategic_memory_saved'] = True
                    print(f"💾 Strategic Memory: saved task")
                
                # 5. حفظ في ConsciousBridge (STM+LTM)
                if self.conscious_bridge_enabled and self.conscious_bridge:
                    try:
                        event_id = self.conscious_bridge.put(
                            type="agi_task",
                            payload={
                                "input": input_text[:200],
                                "output": str(final_response)[:200],
                                "performance": performance_score,
                                "kg_solutions": len(kg_solutions),
                                "reasoning_used": dkn_routing_used
                            },
                            to="ltm" if performance_score > 0.7 else "stm",
                            pinned=(performance_score > 0.9),
                            emotion="satisfied" if performance_score > 0.8 else "neutral"
                        )
                        improvement_results['conscious_bridge_saved'] = event_id
                        print(f"💾 ConsciousBridge: حُفظ الحدث {event_id} ({'LTM' if performance_score > 0.7 else 'STM'})")
                        
                        # 5.1. ربط الحدث بالحدث السابق (Graph Relations)
                        if self._last_bridge_event and event_id:
                            try:
                                self.conscious_bridge.link(
                                    self._last_bridge_event,
                                    event_id,
                                    rel="followed_by"
                                )
                                print(f"   🔗 Linked: {self._last_bridge_event[:8]}... → {event_id[:8]}...")
                            except Exception as link_err:
                                print(f"   ⚠️ خطأ في ربط الأحداث: {link_err}")
                        
                        # حفظ الحدث الحالي كآخر حدث
                        self._last_bridge_event = event_id
                        
                    except Exception as e:
                        print(f"⚠️ خطأ في حفظ ConsciousBridge: {e}")
                
                # 6. حفظ اللحظات المهمة في السيرة الذاتية
                if self.autobiographical_memory and performance_score > 0.8:
                    try:
                        moment_type = "defining" if performance_score > 0.9 else "significant"
                        self.autobiographical_memory.record_moment(
                            moment_type=moment_type,
                            data={
                                "task": input_text[:100],
                                "achievement": str(final_response)[:100],
                                "performance": performance_score,
                                "timestamp": time.time(),
                                "context": "AGI full processing cycle"
                            }
                        )
                        improvement_results['autobiography_saved'] = moment_type
                        print(f"📖 Autobiographical: سُجلت لحظة {moment_type}")
                    except Exception as e:
                        print(f"⚠️ خطأ في السيرة الذاتية: {e}")
                
                # 7. حساب Phi Score (الوعي الحقيقي)
                if self.true_consciousness:
                    try:
                        # تجميع المعلومات للتكامل
                        information_sources = [
                            {"type": "reasoning", "content": str(reasoning_result)[:500]},
                            {"type": "knowledge", "content": f"{len(kg_solutions)} solutions" if kg_solutions else "no solutions"},
                            {"type": "memory", "content": f"context: {len(str(context))} chars"},
                            {"type": "performance", "content": f"score: {performance_score:.2f}"}
                        ]
                        
                        phi_result = self.true_consciousness.integrate_information(information_sources)
                        
                        consciousness_phi = phi_result.get("phi", 0.0)
                        integration_quality = phi_result.get("integration", 0.0)
                        
                        improvement_results['phi_score'] = consciousness_phi
                        improvement_results['integration_quality'] = integration_quality
                        
                        print(f"🌟 Phi Score: {consciousness_phi:.3f} | Integration: {integration_quality:.3f}")
                    except Exception as phi_err:
                        print(f"⚠️ خطأ في حساب Phi: {phi_err}")
            
            except Exception as e:
                print(f"⚠️ Self-improvement processing failed: {e}")
        
        self.consciousness_level = min(1.0, self.consciousness_level + 0.001 + (performance_score * 0.01))
        consciousness_delta = self.consciousness_level - old_consciousness
        
        # 7. تحديد ثغرات معرفية جديدة
        curiosity_gaps = self.curiosity.identify_knowledge_gaps()
        
        # ==================== حفظ التعلم في الذاكرة الجماعية ====================
        if self.kg_enabled and self.collective_memory:
            try:
                # مشاركة التعلم من هذه المهمة
                # التأكد من أن final_response نص وليس None
                response_len = len(str(final_response)) if final_response else 0
                solutions_count = len(kg_solutions) if isinstance(kg_solutions, list) else 0
                
                learning_data = {
                    'question': input_text,
                    'answer_quality': response_len,
                    'engines_used': solutions_count,
                    'reasoning_type': reasoning_type,
                    'consciousness_growth': consciousness_delta
                }
                
                self.collective_memory.share_learning(
                    engine_name='UnifiedAGI',
                    learning_data=learning_data,
                    verified_by=['memory', 'reasoning']
                )
                
            except Exception as e:
                print(f"⚠️ Collective memory update failed: {e}")
        
        # ==================== تحديث أوزان DKN بناءً على الأداء ====================
        if self.dkn_enabled and self.meta_orchestrator and dkn_routing_used:
            try:
                # تقييم جودة النتيجة (بسيط: طول الإجابة + وجود نتائج)
                performance_score = 0.5
                if final_response and len(final_response) > 50:
                    performance_score += 0.3
                if math_result or creative_result:
                    performance_score += 0.2
                
                # تحديث أوزان المحركات المستخدمة
                # feedback يجب أن يكون dict: {engine_name: reward}
                feedback = {}
                for adapter in self.engine_adapters:
                    # إعطاء reward إيجابي لجميع المحركات المشاركة
                    feedback[adapter.name] = performance_score - 0.5  # تحويل لـ [-0.5, 0.5]
                
                self.meta_orchestrator.update_weights(feedback=feedback)
                
                print(f"📊 DKN: تحديث الأوزان - أداء {performance_score:.2f}")
            except Exception as e:
                print(f"⚠️ DKN weight update failed: {e}")
        
        return {
            "final_response": final_response,
            "memories_recalled": relevant_memories,
            "reasoning_type": reasoning_type,
            "math_applied": math_applied,
            "math_result": math_result,
            "creativity_applied": creativity_applied,
            "creative_ideas": creative_result,
            "hypothesis_applied": hypothesis_applied,
            "hypotheses": hypothesis_result,
            "quantum_applied": quantum_applied,
            "quantum_result": quantum_result,
            "curiosity_gaps": curiosity_gaps[:3],
            "consciousness_level": self.consciousness_level,
            "consciousness_delta": consciousness_delta,
            "new_goals": [],
            "dkn_routing_used": dkn_routing_used,
            "dkn_consensus": dkn_consensus,
            "kg_used": kg_used,
            "kg_solutions_count": len(kg_solutions),
            "kg_consensus": kg_consensus,
            "scientific_results": scientific_results,
            "improvement_results": improvement_results,
            "performance_score": performance_score
        }
    
    async def autonomous_cycle(self, duration_seconds: int = 60):
        """دورة مستقلة - النظام يعمل بنفسه"""
        
        start_time = time.time()
        cycle_log = []
        
        while time.time() - start_time < duration_seconds:
            # 1. استكشاف ذاتي
            exploration = await self.curiosity.explore_autonomously(max_iterations=2)
            
            # 2. توليد أهداف جديدة
            new_goals = self.motivation.generate_goals(
                current_state={"consciousness": self.consciousness_level},
                achievements=[]
            )
            
            # 3. تنفيذ هدف
            if new_goals:
                goal = new_goals[0]
                result = await self.process_with_full_agi(goal["goal"])
                
                cycle_log.append({
                    "action": "goal_execution",
                    "goal": goal,
                    "result": result.get("reasoning", {}).get("answer", "")
                })
            
            # 4. راحة
            await asyncio.sleep(5)
        
        return {
            "duration": time.time() - start_time,
            "cycles_completed": len(cycle_log),
            "final_consciousness": self.consciousness_level,
            "log": cycle_log
        }
    
    def get_memory_consciousness_report(self) -> Dict[str, Any]:
        """تقرير شامل عن حالة الذاكرة والوعي"""
        report = {
            "timestamp": time.time(),
            "consciousness": {
                "unified_level": self.consciousness_level,
                "tracker": {
                    "level": getattr(self.consciousness_tracker, 'consciousness_level', 0.0) if self.consciousness_tracker else 0.0,
                    "milestones": len(getattr(self.consciousness_tracker, 'milestones', [])) if self.consciousness_tracker else 0,
                    "stage": getattr(self.consciousness_tracker, 'stage', 'unknown') if self.consciousness_tracker else 'unknown'
                },
                "true_consciousness": {
                    "available": self.true_consciousness is not None,
                    "phi_scores": len(getattr(self.true_consciousness, 'experiences', [])) if self.true_consciousness else 0
                }
            },
            "memory": {
                "unified": {
                    "semantic": len(self.memory.semantic_memory) if hasattr(self.memory, 'semantic_memory') else 0,
                    "episodic": len(self.memory.episodic_memory) if hasattr(self.memory, 'episodic_memory') else 0,
                    "procedural": len(self.memory.procedural_memory) if hasattr(self.memory, 'procedural_memory') else 0,
                    "working": len(self.memory.working_memory) if hasattr(self.memory, 'working_memory') else 0
                },
                "conscious_bridge": {
                    "enabled": self.conscious_bridge_enabled,
                    "stm": len(self.conscious_bridge.stm) if self.conscious_bridge else 0,
                    "ltm": len(self.conscious_bridge.ltm) if self.conscious_bridge else 0,
                    "graph_links": getattr(self.conscious_bridge, 'graph_link_count', 'N/A') if self.conscious_bridge else 0
                },
                "strategic": len(self.strategic_memory.memory) if self.strategic_memory and hasattr(self.strategic_memory, 'memory') else 0,
                "autobiographical": {
                    "narrative": len(self.autobiographical_memory.life_narrative) if self.autobiographical_memory else 0,
                    "defining_moments": len(self.autobiographical_memory.defining_moments) if self.autobiographical_memory else 0,
                    "lessons": len(self.autobiographical_memory.lessons_learned) if self.autobiographical_memory else 0
                }
            },
            "systems": {
                "dkn_enabled": self.dkn_enabled,
                "kg_enabled": self.kg_enabled,
                "scientific_enabled": self.scientific_enabled,
                "self_improvement_enabled": self.self_improvement_enabled
            }
        }
        
        return report
    
    def print_memory_consciousness_summary(self):
        """طباعة ملخص سريع للذاكرة والوعي"""
        report = self.get_memory_consciousness_report()
        
        print("\n" + "="*70)
        print("📊 Memory & Consciousness Summary")
        print("="*70)
        
        # الوعي
        print(f"\n🧠 Consciousness:")
        print(f"   - Unified Level: {report['consciousness']['unified_level']:.3f}")
        print(f"   - Tracker Level: {report['consciousness']['tracker']['level']:.3f}")
        print(f"   - Stage: {report['consciousness']['tracker']['stage']}")
        print(f"   - Milestones: {report['consciousness']['tracker']['milestones']}")
        print(f"   - Phi Calculations: {report['consciousness']['true_consciousness']['phi_scores']}")
        
        # الذاكرة
        total_unified = sum(report['memory']['unified'].values())
        print(f"\n💾 Memory Systems:")
        print(f"   - Unified Memory: {total_unified} items")
        print(f"     • Semantic: {report['memory']['unified']['semantic']}")
        print(f"     • Episodic: {report['memory']['unified']['episodic']}")
        print(f"     • Procedural: {report['memory']['unified']['procedural']}")
        print(f"     • Working: {report['memory']['unified']['working']}")
        
        print(f"\n🌉 ConsciousBridge:")
        if report['memory']['conscious_bridge']['enabled']:
            print(f"   - STM: {report['memory']['conscious_bridge']['stm']} events")
            print(f"   - LTM: {report['memory']['conscious_bridge']['ltm']} events")
            print(f"   - Graph Links: {report['memory']['conscious_bridge']['graph_links']}")
        else:
            print(f"   - ⚠️ Not Enabled")
        
        print(f"\n📖 Autobiographical Memory:")
        print(f"   - Life Narrative: {report['memory']['autobiographical']['narrative']} entries")
        print(f"   - Defining Moments: {report['memory']['autobiographical']['defining_moments']}")
        print(f"   - Lessons Learned: {report['memory']['autobiographical']['lessons']}")
        
        print(f"\n🎯 Strategic Memory: {report['memory']['strategic']} tasks")
        
        # الأنظمة
        print(f"\n⚙️ Active Systems:")
        systems = report['systems']
        print(f"   - DKN Routing: {'✅' if systems['dkn_enabled'] else '❌'}")
        print(f"   - Knowledge Graph: {'✅' if systems['kg_enabled'] else '❌'}")
        print(f"   - Scientific: {'✅' if systems['scientific_enabled'] else '❌'}")
        print(f"   - Self-Improvement: {'✅' if systems['self_improvement_enabled'] else '❌'}")
        
        print("="*70 + "\n")


# ==================== Factory ====================

def create_unified_agi_system(engine_registry: Dict[str, Any]) -> UnifiedAGISystem:
    """إنشاء نظام AGI الموحد"""
    return UnifiedAGISystem(engine_registry)
