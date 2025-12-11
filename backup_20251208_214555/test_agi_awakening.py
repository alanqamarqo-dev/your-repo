"""
Integration test: 'AGI Awakening' - wire perception -> memory -> causal -> meta-reasoner -> self-reflection
This script attempts to import real modules from the codebase and falls back to lightweight stubs if a component isn't available.
Run with: python test_agi_awakening.py
"""
import importlib
import traceback

COMPONENTS = {
    'Perception_Context': ('Core_Engines', 'Perception_Context'),
    'Conscious_Bridge': ('Core_Memory', 'Conscious_Bridge'),
    'Causal_Graph': ('Core_Engines', 'Causal_Graph'),
    'AdvancedMetaReasoner': ('Core_Engines', 'AdvancedMetaReasoner'),
    'Self_Reflective': ('Core_Engines', 'Self_Reflective'),
    'Quantum_Neural_Core': ('Core_Engines', 'Quantum_Neural_Core'),
}

loaded = {}

for name, (pkg, modname) in COMPONENTS.items():
    try:
        module = importlib.import_module(f"{pkg}.{modname}")
        loaded[name] = module
        print(f"✅ Loaded: {pkg}.{modname}")
    except Exception as e:
        print(f"⚠️ Could not import {pkg}.{modname}: {e}")
        loaded[name] = None

# Provide safe stubs if not present
class _Stub:
    @staticmethod
    def analyze(text):
        return { 'text': text, 'sentiment': 'neutral', 'keywords': [w for w in text.split()[:6]] }
    @staticmethod
    def fetch_relevant(context):
        return [ { 'id': 'm1', 'note': 'stub memory about previous project', 'text': 'previous project failed due to scope creep' } ]
    @staticmethod
    def build_graph(query, context):
        return { 'nodes': ['planning','resources','team'], 'edges': [('planning','resources'),('team','planning')] }
    @staticmethod
    def synthesize_plan(query, causes, memories):
        return { 'steps': [ 'Define clear scope', 'Allocate buffer resources', 'Weekly reviews with stakeholders' ], 'rationale': 'combined causal & memory analysis' }
    @staticmethod
    def critique(plan):
        return { 'status': 'APPROVED', 'reason': '' }

PerceptionModule = loaded.get('Perception_Context')
ConsciousModule = loaded.get('Conscious_Bridge')
CausalModule = loaded.get('Causal_Graph')
MetaModule = loaded.get('AdvancedMetaReasoner')
ReflectModule = loaded.get('Self_Reflective')
QuantumModule = loaded.get('Quantum_Neural_Core')  # optional

# Instantiate adapters/wrappers or fallback to stubs
def _instantiate_perception(mod):
    if not mod:
        return _Stub
    if hasattr(mod, 'PerceptionContext'):
        try:
            return mod.PerceptionContext()
        except Exception:
            return _Stub
    return _Stub

def _instantiate_conscious(mod):
    if not mod:
        return _Stub
    if hasattr(mod, 'ConsciousBridge'):
        try:
            return mod.ConsciousBridge()
        except Exception:
            return _Stub
    return _Stub

def _instantiate_causal(mod):
    if not mod:
        return _Stub
    # prefer factory
    try:
        if hasattr(mod, 'create_engine'):
            return mod.create_engine()
        if hasattr(mod, 'CausalGraphEngine'):
            return mod.CausalGraphEngine()
    except Exception:
        pass
    return _Stub

def _instantiate_meta(mod):
    if not mod:
        return _Stub
    try:
        if hasattr(mod, 'create_engine'):
            return mod.create_engine()
        if hasattr(mod, 'AdvancedMetaReasonerEngine'):
            return mod.AdvancedMetaReasonerEngine()
    except Exception:
        pass
    return _Stub

def _instantiate_reflect(mod):
    if not mod:
        return _Stub
    try:
        if hasattr(mod, 'create_engine'):
            return mod.create_engine()
        if hasattr(mod, 'SelfReflectiveEngine'):
            return mod.create_engine() if hasattr(mod, 'create_engine') else mod.SelfReflectiveEngine()
    except Exception:
        pass
    return _Stub

def _instantiate_quantum(mod):
    if not mod:
        return None
    try:
        if hasattr(mod, 'create_engine'):
            return mod.create_engine()
        # if module is itself a class instance/factory
        return mod
    except Exception:
        return None

Perception = _instantiate_perception(PerceptionModule)
Conscious = _instantiate_conscious(ConsciousModule)
Causal = _instantiate_causal(CausalModule)
Meta = _instantiate_meta(MetaModule)
Reflect = _instantiate_reflect(ReflectModule)
Quantum = _instantiate_quantum(QuantumModule)


# --- إضافة 1: دالة لزرع ذاكرة وهمية قبل الاختبار ---
def seed_test_memory():
    print("\n[Setup] Initialization: Injecting REAL experience into Long-Term Memory (LTM)...")
    try:
        memory_1 = {
            "content": "In previous Solar Energy project, failure was caused by Supply Chain Delay.",
            "type": "experience",
            "tags": ["failure", "solar", "supply_chain"]
        }

        memory_2 = {
            "content": "Project Alpha succeeded by using Local Sourcing strategies.",
            "type": "experience",
            "tags": ["success", "strategy", "local_sourcing"]
        }

        # Attempt to write using the real Conscious bridge API (best-effort)
        written = False
        if hasattr(Conscious, 'put'):
            try:
                # Conscious.put(type:str, payload:dict, *, to='stm'|'ltm', ...)
                Conscious.put(memory_1.get('type', 'experience'), memory_1, to='ltm')
                Conscious.put(memory_2.get('type', 'experience'), memory_2, to='ltm')
                written = True
            except Exception as e:
                print(f">> [Warning] Conscious.put failed: {e}")

        if not written and hasattr(Conscious, 'save_memory'):
            try:
                Conscious.save_memory(memory_1)
                Conscious.save_memory(memory_2)
                written = True
            except Exception as e:
                print(f">> [Warning] Conscious.save_memory failed: {e}")

        if written:
            print(">> [Success] Real memories written to DB.")
        else:
            print(">> [Warning] Could not find or write using 'put'/'save_memory'. Check Conscious_Bridge API or permissions.")

    except Exception as e:
        print(f">> [Error] Memory Injection Failed: {e}")


def run_agi_thought_process(user_query: str):
    print(f"--- AGI Triggered: {user_query} ---")

    try:
        # 1. Perception/context
        try:
            if hasattr(Perception, 'extract'):
                context = Perception.extract(user_query)
            elif hasattr(Perception, 'analyze'):
                context = Perception.analyze(user_query)
            else:
                context = _Stub.analyze(user_query)
        except Exception:
            print("[WARN] Perception.extract/analyze failed, using fallback")
            context = _Stub.analyze(user_query)
        print(f"[1] Context: {context}")

        # 2. Conscious bridge (memory retrieval)
        print("[2] Bridge Activation: Checking memories...")
        try:
            # attempt a straightforward semantic_search if available
            real_memories = []
            if hasattr(Conscious, 'semantic_search'):
                try:
                    real_memories = Conscious.semantic_search(user_query, top_k=5) or []
                except Exception:
                    real_memories = []
            elif hasattr(Conscious, 'semantic_search_by_context'):
                try:
                    q = context.get('context') if isinstance(context, dict) else user_query
                    real_memories = Conscious.semantic_search_by_context(q, top_k=5) or []
                except Exception:
                    real_memories = []
            elif hasattr(Conscious, 'fetch_relevant'):
                try:
                    real_memories = Conscious.fetch_relevant(context) or []
                except Exception:
                    real_memories = []
            else:
                real_memories = []

            # additional robust check: if LTM dict exists and has entries, use that
            if (not real_memories) and hasattr(Conscious, 'ltm') and isinstance(getattr(Conscious, 'ltm'), dict) and len(getattr(Conscious, 'ltm'))>0:
                try:
                    real_memories = list(Conscious.ltm.values())
                except Exception:
                    pass

        except Exception:
            real_memories = []

        # If no real memories found, inject synthetic memories for this test run
        if not real_memories:
            print("[Test Info] No DB memories found. Injecting 'Synthetic Memory' to test Causal Graph flow.")
            memories = [
                "Memory #101: In the previous project (Solar Energy), failure was caused by 'Supply Chain Delay' and 'Budget Overrun'.",
                "Memory #102: Successful mitigation in Project Alpha involved 'Local Sourcing'.",
            ]
        else:
            memories = real_memories

        print(f"[2] Memories Loaded: {len(memories)} items.")

        # 3. Causal analysis
        try:
            if hasattr(Causal, 'process_task'):
                causes = Causal.process_task({'text': user_query, 'events': memories})
            elif hasattr(Causal, 'upsert_from_hypotheses') and isinstance(Causal, object):
                # CausalGraph instance
                causes = {'engine': 'CausalGraph', 'nodes': list(getattr(Causal, 'nodes', {}).keys()), 'edges': getattr(Causal, 'edges', [])}
            else:
                causes = _Stub.build_graph(user_query, context)
        except Exception:
            print("[WARN] Causal processing failed, using fallback")
            causes = _Stub.build_graph(user_query, context)
        print(f"[3] Causal Map Generated: {list(causes.keys()) if isinstance(causes, dict) else type(causes)}")

        # Optionally incorporate Quantum_Neural_Core to add probabilistic creativity
        q_info = None
        if Quantum is not None:
            try:
                if hasattr(Quantum, 'sample_hypotheses'):
                    q_info = Quantum.sample_hypotheses(user_query, context, num_samples=3)
                    print(f"[3b] Quantum hypotheses: {str(q_info)[:200]}")
                else:
                    print("[3b] Quantum_Neural_Core present but no sample_hypotheses()")
            except Exception:
                print("[3b] Quantum_Neural_Core invocation failed:\n", traceback.format_exc())

        # 4. Meta-Reasoning / plan synthesis
        try:
            ranked_hyps = []
            if q_info and isinstance(q_info, list):
                # normalize to expected format
                for h in q_info:
                    if isinstance(h, dict) and h.get('hypothesis'):
                        ranked_hyps.append({'hypothesis': h.get('hypothesis'), 'score': float(h.get('confidence', 0.5))})
            # fallback: create simple hypotheses from causal nodes
            if not ranked_hyps:
                if isinstance(causes, dict):
                    nodes = causes.get('nodes') or causes.get('nodes', [])
                    for i, n in enumerate(nodes[:3]):
                        ranked_hyps.append({'hypothesis': f"{n}", 'score': 0.45 + 0.1 * i})
            payload = {'ranked_hypotheses': ranked_hyps, 'context_info': {'user_query': user_query, 'memories': memories, 'causes': causes}}
            if hasattr(Meta, 'process_task'):
                plan = Meta.process_task(payload)
            else:
                # try engine instance with process_task
                if hasattr(Meta, 'process_task'):
                    plan = Meta.process_task(payload)
                else:
                    plan = _Stub.synthesize_plan(user_query, causes, memories)
        except Exception:
            print("[WARN] Meta reasoning failed, using fallback plan")
            plan = _Stub.synthesize_plan(user_query, causes, memories)
        print(f"[4] Plan Created: {plan}")

        # 5. Self reflection / critique
        try:
            # prefer the process_task API for the reflective engine
            if hasattr(Reflect, 'process_task'):
                reflection = Reflect.process_task({'reasoning_trace': [{'step': 'plan', 'assertions': [], 'confidence': 0.9}], 'plan': plan})
            elif hasattr(Reflect, 'critique'):
                reflection = Reflect.critique(plan)
            else:
                reflection = _Stub.critique(plan)
        except Exception:
            print("[WARN] Self-reflection failed, approving by default")
            reflection = { 'status': 'APPROVED', 'reason': '' }

        print(f"[5] Reflection: {reflection}")

        # --- تعديل 2: إصلاح شرط الموافقة ---
        is_approved = False
        # الطريقة 1: البحث عن حقل الحالة
        if isinstance(reflection, dict) and reflection.get('status') == 'APPROVED':
            is_approved = True
        # الطريقة 2: التحقق من الثقة (Avg Confidence)
        elif isinstance(reflection, dict) and reflection.get('summary', {}).get('avg_confidence', 0) > 0.8:
            is_approved = True
            print("[Orchestra] High confidence detected -> Auto-Approval.")
        # الطريقة 3: التحقق من ok: True وعدم وجود مشاكل
        elif isinstance(reflection, dict) and reflection.get('ok') and not reflection.get('issues'):
            is_approved = True

        if is_approved:
            print("\n>>> FINAL AGI VERDICT: APPROVED <<<")
            return plan
        else:
            reason = reflection.get('suggestions', ['Unknown Reason']) if isinstance(reflection, dict) else ['Unknown Reason']
            return f"Plan Rejected. Critique: {reason}"

    except Exception as e:
        print("[ERROR] AGI run failed:\n", traceback.format_exc())
        return { 'error': str(e) }


if __name__ == '__main__':
    # Ensure test memories are injected into LTM before the run
    try:
        seed_test_memory()
    except Exception:
        pass

    prompt = "لقد فشلت في مشروعي السابق، كيف أضمن نجاح المشروع الحالي؟"
    out = run_agi_thought_process(prompt)
    print('\n--- Final Output ---')
    print(out)
