# === AGL auto-injected knobs (idempotent) ===
try:
    import os
    def _to_int(name, default):
        try:
            return int(os.environ.get(name, str(default)))
        except Exception:
            return default
except Exception:
    def _to_int(name, default): return default
_AGL_PREVIEW_120 = _to_int('AGL_PREVIEW_120', 120)
_AGL_PREVIEW_500 = _to_int('AGL_PREVIEW_500', 500)

try:
    import os
    def _to_int(name, default):
        try:
            return int(os.environ.get(name, str(default)))
        except Exception:
            return default
except Exception:
    def _to_int(name, default): return default
import sys, time, json, os
sys.path.insert(0, 'D:/AGL/repo-copy')
from Core_Engines import bootstrap_register_all_engines
from tests.helpers.engine_ask import ask_engine
class AGLIntegrator:
    def __init__(self):
        self.registry = {}
        self.performance_stats = {}
        self.self_model = None
        self.curiosity_engine = None
        self.perception_loop = None
        self.initialize_system()
    def initialize_system(self):
        try:
            bootstrap_register_all_engines(self.registry)
            print('✅ تم اكتشاف {} محرك'.format(len(self.registry)))
            self._initialize_consciousness_layer()
        except Exception as e:
            print('❌ خطأ في تهيئة النظام:', e)
    def _initialize_consciousness_layer(self):
        try:
            from Core_Consciousness.Self_Model import SelfModel
            self.self_model = SelfModel.identity_singleton()
            print('✅ تم تحميل نموذج الذات (SelfModel)')
        except Exception as e:
            print('⚠️ لم يتم تحميل SelfModel:', e)
            self.self_model = None
        try:
            from Core_Engines.Self_Reflective import create_curiosity_engine
            self.curiosity_engine = create_curiosity_engine()
            print('✅ تم تحميل محرك الفضول (CuriosityEngine)')
        except Exception as e:
            print('⚠️ لم يتم تحميل CuriosityEngine:', e)
            self.curiosity_engine = None
        try:
            from Core_Consciousness.Perception_Loop import PerceptionLoop
            self.perception_loop = PerceptionLoop(self.self_model)
            print('✅ تم تحميل حلقة الإدراك (PerceptionLoop)')
        except Exception as e:
            print('⚠️ لم يتم تحميل PerceptionLoop:', e)
            self.perception_loop = None
    def _analyze_with_perception(self, question):
        if not self.perception_loop:
            return {'depth': 'basic', 'key_concepts': []}
        try:
            if hasattr(self.perception_loop, 'analyze_query'):
                res = self.perception_loop.analyze_query(question)
            else:
                res = self.perception_loop.run_once(trace_debug=False) or {}
                try:
                    types = res.get('recent_event_types', [])
                    res.setdefault('key_concepts', [])
                    try:
                        pc_limit = int(os.getenv('AGL_PERCEPTION_KEYCONCEPTS_LIMIT', '8'))
                    except Exception:
                        pc_limit = 8
                    res['key_concepts'] = list(dict.fromkeys(types))[:pc_limit]
                    res.setdefault('depth', 'sample')
                except Exception:
                    pass
            if self.self_model:
                try:
                    self.self_model.add_biography_event(kind='perception_analysis', note='تحليل سؤال: {}'.format(question[:_AGL_PREVIEW_120]), source='AGLIntegrator', context=res)
                except Exception:
                    pass
            return res or {'depth': 'basic', 'key_concepts': []}
        except Exception as e:
            print('⚠️ خطأ في التحليل الإدراكي:', e)
            return {'depth': 'basic', 'key_concepts': [], 'error': str(e)}
    def _activate_curiosity(self, question, perception_data):
        if not self.curiosity_engine:
            return []
        try:
            try:
                cur_max = int(os.getenv('AGL_CURIO_MAX_QUESTIONS', '3'))
            except Exception:
                cur_max = 3
            curiosity_qs = self.curiosity_engine.generate_curiosity_questions(main_question=question, context=perception_data, max_questions=cur_max)
            quality = 0.0
            try:
                quality = self.curiosity_engine.evaluate_curiosity_quality(curiosity_qs)
            except Exception:
                quality = 0.5
            if quality > 0.6 and curiosity_qs:
                print('🎯 محرك الفضول ولّد {} سؤال استكشافي (score={})'.format(len(curiosity_qs), quality))
                if self.self_model:
                    try:
                        self.self_model.add_biography_event(kind='curiosity_triggered', note='فضول مستثار بجودة {:.2f}'.format(quality), source='CuriosityEngine', context={'questions': curiosity_qs})
                    except Exception:
                        pass
                return curiosity_qs
            return []
        except Exception as e:
            print('⚠️ خطأ في تفعيل الفضول:', e)
            return []
    def _execute_parallel_engines(self, question, categories, timeout_per_engine=20):
        responses = {}
        engines_to_call = []
        if isinstance(categories, dict):
            for lst in categories.values():
                engines_to_call.extend(lst)
        elif isinstance(categories, list):
            engines_to_call = categories
        else:
            engines_to_call = ['Hybrid_Reasoner', 'Mathematical_Brain', 'Analogy_Mapping_Engine']
        seen = set()
        engines = []
        for e in engines_to_call:
            if e and e not in seen:
                seen.add(e)
                engines.append(e)
        for engine in engines:
            try:
                start = time.time()
                r = ask_engine(engine, question)
                took = time.time() - start
                if not isinstance(r, dict):
                    r = {'ok': True, 'text': str(r)}
                responses[engine] = {'ok': r.get('ok', True), 'text': r.get('text', r.get('reply_text', str(r))), 'raw': r, 'time': took}
                print('✅ {}: ok={} time={:.2f}s'.format(engine, responses[engine]['ok'], took))
            except Exception as e:
                responses[engine] = {'ok': False, 'text': '', 'error': str(e), 'time': 0.0}
                print('❌ {}: error - {}'.format(engine, e))
        return responses
    def _evaluate_curiosity_quality(self, questions):
        return bool(questions)
    def _process_curiosity_questions(self, curiosity_questions):
        out = {}
        try:
            cur_proc = int(os.getenv('AGL_CURIO_PROCESS_LIMIT', '2'))
        except Exception:
            cur_proc = 2
        for i, q in enumerate(curiosity_questions[:cur_proc]):
            try:
                resp = self._execute_parallel_engines(q, {'reasoning': ['Hybrid_Reasoner', 'Reasoning_Layer']}, timeout_per_engine=15)
                out['curiosity_{}'.format(i + 1)] = {'question': q, 'responses': resp, 'timestamp': time.time()}
                print('🔍 معالجة سؤال الفضول {}: {}...'.format(i + 1, q[:60]))
            except Exception as e:
                print('⚠️ فشل معالجة سؤال الفضول:', e)
        return out
    def _update_self_awareness(self, question, result, perception_data):
        if not self.self_model:
            return
        try:
            confidence = result.get('confidence_score', 0.5)
            if confidence > 0.7:
                try:
                    self.self_model.set_core_value('curiosity', 0.05, mode='delta')
                    self.self_model.set_core_value('confidence', 0.03, mode='delta')
                except Exception:
                    pass
            try:
                self.self_model.add_biography_event(kind='integrated_processing', note='معالجة متكاملة بثقة {:.2f}'.format(confidence), source='AGLIntegrator', context={'question': question, 'perception': perception_data})
                self.self_model.persist_profile()
            except Exception as e:
                print('⚠️ خطأ عند تحديث السيرة/الحفظ:', e)
            print('✅ تم تحديث الوعي الذاتي (إن وُجد)')
        except Exception as e:
            print('⚠️ خطأ في تحديث الوعي الذاتي:', e)
    def _integrate_responses(self, all_responses):
        final = {'final_answer': '', 'supporting_evidence': [], 'confidence_score': 0.0, 'sources_used': []}
        sum_conf = 0.0
        cnt = 0
        for engine, r in all_responses.items():
            if engine == 'curiosity':
                continue
            txt = r.get('text') if isinstance(r, dict) else str(r)
            if txt:
                final['supporting_evidence'].append({'engine': engine, 'text': txt[:800]})
                final['final_answer'] += '\n---\nContribution from {}:\n'.format(engine) + txt + '\n'
                final['sources_used'].append(engine)
                score = 0.6 if r.get('ok') else 0.3
                sum_conf += score
                cnt += 1
        final['confidence_score'] = sum_conf / cnt if cnt else 0.5
        if 'curiosity' in all_responses:
            final['curiosity_explorations'] = {'total_explorations': len(all_responses['curiosity']), 'details': all_responses['curiosity']}
            for k, exploration in all_responses['curiosity'].items():
                if exploration.get('responses'):
                    for eng, rr in exploration['responses'].items():
                        text = rr.get('text') if isinstance(rr, dict) else str(rr)
                        if text:
                            final['final_answer'] += '\nCuriosity {} - {}: {}\n'.format(k, eng, text[:_AGL_PREVIEW_500])
        return final
    def integrate_query(self, question, timeout_per_engine=30):
        perception = self._analyze_with_perception(question)
        curiosity_qs = self._activate_curiosity(question, perception)
        categories = {'reasoning': ['Hybrid_Reasoner', 'Reasoning_Layer'], 'creative': ['Analogy_Mapping_Engine', 'Creative_Innovation'], 'mathematical': ['Mathematical_Brain']}
        all_responses = self._execute_parallel_engines(question, categories, timeout_per_engine)
        if curiosity_qs and self._evaluate_curiosity_quality(curiosity_qs):
            all_responses['curiosity'] = self._process_curiosity_questions(curiosity_qs)
        integrated = self._integrate_responses(all_responses)
        self._update_self_awareness(question, integrated, perception)
        return integrated
if __name__ == '__main__':
    print('🧠 بدء تشغيل المجموع المتكامل (بدون ملفات جديدة)')
    intg = AGLIntegrator()
    q = 'طبق مفهوم الإنتروبيا من الفيزياء على: 1) علم النفس البشري (الاضطرابات العقلية) 2) تطور اللغات البشرية 3) تصميم المدن الذكية\nأجب مع شرح علمي ومعادلات ومقاييس قابلة للقياس'
    res = intg.integrate_query(q, timeout_per_engine=25)
    try:
        from Core_Memory.bridge_singleton import get_bridge
        br = get_bridge()
        try:
            br.put('agl_integrated_response', res, to='ltm')
            print('💾 تم حفظ النتيجة المدمجة إلى جسر الوعي (LTM)')
        except Exception as e:
            print('⚠️ فشل حفظ إلى الجسر:', e)
    except Exception:
        print('⚠️ جسر الذاكرة غير متاح؛ تخطّي حفظ إلى LTM')
    try:
        import os
        os.makedirs('artifacts/integrated_responses', exist_ok=True)
        fn = f'artifacts/integrated_responses/integration_{int(time.time())}.json'
        with open(fn, 'w', encoding='utf-8') as fh:
            json.dump(res, fh, ensure_ascii=False, indent=2)
        print('💾 تم حفظ النتيجة المدمجة إلى', fn)
    except Exception as e:
        print('⚠️ فشل كتابة الملف في artifacts:', e)
    print('\n=== Integrated Result (JSON) ===')
    print(json.dumps(res, ensure_ascii=False, indent=2))
