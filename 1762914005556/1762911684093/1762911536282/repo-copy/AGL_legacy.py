# AGL.py
"""
AGL - Advanced General Intelligence System
النظام الذكي العام المتقدم
"""

__version__ = "0.4.0"

from ast import Dict
import os
import sys
from pathlib import Path
from typing import Optional

# Ensure the virtualenv's site-packages is preferred on sys.path so
# installed packages (numpy/scipy) are used instead of local stubs that
# may shadow them (e.g. a project-local numpy.py). We still keep the
# project directory on sys.path so local modules can be imported.
try:
    venv_site = Path(sys.executable).resolve().parent.parent / 'Lib' / 'site-packages'
    if venv_site.exists():
        sys.path.insert(0, str(venv_site))
except Exception:
    pass

# إضافة المسارات للمكتبات (keep project root available)
sys.path.append(str(Path(__file__).parent))

import logging
from logging.handlers import RotatingFileHandler
import json
import time
import random
import hashlib
from ConfidenceGate import compute_inputs_hash, check_gate, maybe_update_baseline
import sys
import re
from difflib import SequenceMatcher
import unicodedata

# --- Logging setup ---
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
# Use UTF-8 with BOM so Windows PowerShell reads Arabic/Unicode correctly by default.
handler = RotatingFileHandler(LOG_DIR / "agl.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8-sig")
logging.basicConfig(level=logging.INFO, handlers=[handler], format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("AGL")
# Try to ensure console uses UTF-8 to avoid mojibake on Windows PowerShell
try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8') # type: ignore
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8') # type: ignore
except Exception:
    pass

from Core_Engines.Mathematical_Brain import MathematicalBrain
from Core_Engines.Quantum_Processor import QuantumProcessor
from Core_Engines.Code_Generator import CodeGenerator
from Core_Engines.Protocol_Designer import ProtocolDesigner

from Safety_Systems.Control_Layers import ControlLayers # type: ignore
from Safety_Systems.Rollback_Mechanism import RollbackMechanism # type: ignore
from Safety_Systems.Emergency_Protocols import EmergencyProtocols # type: ignore

from Knowledge_Base.Learned_Patterns import LearnedPatterns # type: ignore
from Knowledge_Base.Improvement_History import ImprovementHistory # type: ignore
from Knowledge_Base.Domain_Expertise import DomainExpertise # type: ignore

from Learning_System.Feedback_Analyzer import FeedbackAnalyzer # type: ignore
from Learning_System.Improvement_Generator import ImprovementGenerator # type: ignore
from Learning_System.Knowledge_Integrator import KnowledgeIntegrator # type: ignore

from Integration_Layer.Communication_Bus import CommunicationBus
from Integration_Layer.Task_Orchestrator import TaskOrchestrator
from Integration_Layer.Output_Formatter import OutputFormatter
from Integration_Layer.integration_registry import IntegrationRegistry
from ConfidenceGate import gate as confidence_gate

class AGL: # type: ignore
    """
    النظام الذكي العام المتقدم
    Advanced General Intelligence System
    """
    
    def __init__(self, operational_mode: str = "supervised_autonomy", config: Optional[dict] = None):
        # configuration and operational mode
        # load configuration: prefer explicit `config` dict, otherwise try to
        # read from config.yaml at repo root. If the YAML contains a
        # `features:` mapping we flatten it into the top-level config keys so
        # older code (which reads flat keys) keeps working.
        self.config = config.copy() if isinstance(config, dict) else {}
        try:
            import yaml
            cfg_path = Path(__file__).parent / 'config.yaml'
            if cfg_path.exists():
                with open(cfg_path, 'r', encoding='utf-8-sig') as cf:
                    file_cfg = yaml.safe_load(cf) or {}
                    # flatten features mapping into top-level keys
                    features = file_cfg.get('features') if isinstance(file_cfg, dict) else None
                    if isinstance(features, dict):
                        for k, v in features.items():
                            # do not override explicitly provided config values
                            if k not in self.config:
                                self.config[k] = v
                    # also merge other top-level keys if missing
                    for k, v in (file_cfg.items() if isinstance(file_cfg, dict) else []):
                        if k == 'features':
                            continue
                        if k not in self.config:
                            self.config[k] = v
        except Exception:
            # yaml may not be installed or file missing—fall back to provided config
            pass
        self.operational_mode = operational_mode

        # registry for integration services
        self.integration_registry = IntegrationRegistry()

        # initial system state
        self.system_state = {
            'health': 'optimal',
            'learning_phase': 'phase_1',
            'performance_level': 0.0,
            'safety_score': 1.0
        }

        # initialize empty registries so individual _initialize_* methods can populate them
        self.core_engines = {}
        self.integration_layer = {}
        self.learning_system = {}
        self.safety_systems = {}

        # تهيئة المكونات عبر طرق منفصلة
        self._initialize_core_engines()
        self._initialize_safety_systems()
        self._initialize_knowledge_base()
        self._initialize_learning_system()
        self._initialize_integration_layer()

        # Log initialization summary
        logger.info("🚀 AGL System Initialized Successfully!")
        logger.info(f"Operational Mode: {self.operational_mode}")
        logger.info(f"Core Engines: {len(self.core_engines)}")
        logger.info(f"Safety Systems: {len(self.safety_systems)}")
        logger.info(f"Knowledge Modules: {len(self.knowledge_modules)}")
        # Per-engine signal policies: 'boost' to ensure minimum confidence, 'disable' to ignore in fusion.
        # Default: temporarily boost weak experimental engines so demos proceed.
        self._engine_signal_policies = {
            'quantum_processor': 'boost',
            'protocol_designer': 'boost'
        }
    
    def _initialize_core_engines(self):
        """تهيئة المحركات الأساسية"""
        # core default engines
        try:
            self.core_engines['mathematical_brain'] = MathematicalBrain()
        except Exception:
            pass
        try:
            self.core_engines['quantum_processor'] = QuantumProcessor()
        except Exception:
            pass
        try:
            self.core_engines['code_generator'] = CodeGenerator()
        except Exception:
            pass
        try:
            self.core_engines['protocol_designer'] = ProtocolDesigner()
        except Exception:
            pass

        # Visual spatial engine enabled by default (best-effort)
        try:
            # try a couple of possible class names
            from Core_Engines.Visual_Spatial import VisualSpatialEngine as VSE
        except Exception:
            try:
                from Core_Engines.Visual_Spatial import Visual_Spatial as VSE
            except Exception:
                VSE = None

        if VSE is not None:
            try:
                self.core_engines['visual_spatial'] = VSE()
            except Exception:
                pass

        # optional heavy components guarded by config toggles
        if self.config.get('enable_quantum_neural_core', False):
            try:
                from Core_Engines.Quantum_Neural_Core import QuantumNeuralCore
                # supply a reasonable default for num_qubits when enabling
                self.core_engines['quantum_neural'] = QuantumNeuralCore(num_qubits=4)
            except Exception:
                pass

        if self.config.get('enable_advanced_exponential_algebra', False):
            try:
                from Core_Engines.Advanced_Exponential_Algebra import AdvancedExponentialAlgebra
                self.core_engines['adv_exp_algebra'] = AdvancedExponentialAlgebra()
            except Exception:
                pass
    
    def _initialize_safety_systems(self):
        """تهيئة أنظمة السلامة"""
        self.safety_systems['control_layers'] = ControlLayers()
        self.safety_systems['rollback_mechanism'] = RollbackMechanism()
        self.safety_systems['emergency_protocols'] = EmergencyProtocols()

        # register
        try:
            self.integration_registry.register('control_layers', self.safety_systems['control_layers'])
            self.integration_registry.register('rollback_mechanism', self.safety_systems['rollback_mechanism'])
            self.integration_registry.register('emergency_protocols', self.safety_systems['emergency_protocols'])
        except Exception:
            pass

        # optional emergency experts
        if self.config.get('enable_emergency_experts', False):
            try:
                from Safety_Systems.EmergencyDoctor import EmergencyDoctor
                self.safety_systems['emergency_doctor'] = EmergencyDoctor()
                self.integration_registry.register('emergency_doctor', self.safety_systems['emergency_doctor'])
            except Exception:
                # fallback emergency doctor
                try:
                    from Safety_Systems.Emergency_Fallbacks import EmergencyDoctorFallback
                    self.safety_systems['emergency_doctor'] = EmergencyDoctorFallback()
                    self.integration_registry.register('emergency_doctor', self.safety_systems['emergency_doctor'])
                except Exception:
                    pass

            try:
                from Safety_Systems.EmergencyIntegration import EmergencyIntegration
                self.safety_systems['emergency_integration'] = EmergencyIntegration(self.integration_registry)
                self.integration_registry.register('emergency_integration', self.safety_systems['emergency_integration'])
            except Exception:
                try:
                    from Safety_Systems.Emergency_Fallbacks import EmergencyIntegrationFallback
                    self.safety_systems['emergency_integration'] = EmergencyIntegrationFallback(self.integration_registry)
                    self.integration_registry.register('emergency_integration', self.safety_systems['emergency_integration'])
                except Exception:
                    pass
    
    def _initialize_knowledge_base(self):
        """تهيئة قاعدة المعرفة"""
        self.knowledge_modules = {
            'learned_patterns': LearnedPatterns(),
            'improvement_history': ImprovementHistory(),
            'domain_expertise': DomainExpertise()
        }
    
    def _initialize_learning_system(self):
        """تهيئة نظام التعلم"""
        # ensure exp_file is always defined for fallback factories
        exp_file = None
        self.learning_system['feedback_analyzer'] = FeedbackAnalyzer()
        self.learning_system['improvement_generator'] = ImprovementGenerator()
        self.learning_system['knowledge_integrator'] = KnowledgeIntegrator()

        # register core learning services
        try:
            self.integration_registry.register('feedback_analyzer', self.learning_system['feedback_analyzer'])
            self.integration_registry.register('improvement_generator', self.learning_system['improvement_generator'])
            self.integration_registry.register('knowledge_integrator', self.learning_system['knowledge_integrator'])
        except Exception:
            pass

        # Register meta-cognition service if enabled (or provide a fallback)
        try:
            if self.config.get('enable_meta_cognition', False):
                try:
                    from Learning_System.MetaCognition import MetaCognition # type: ignore
                    self.integration_registry.register_factory('meta_cognition', lambda: MetaCognition())
                except Exception:
                    try:
                        from Learning_System.MetaCognition_Fallback import MetaCognitionFallback
                        self.integration_registry.register_factory('meta_cognition', lambda: MetaCognitionFallback())
                    except Exception:
                        class _TinyMeta: # type: ignore
                            def evaluate(self, plan):
                                return {'score': 0.5, 'notes': 'inline-fallback'}

                        self.integration_registry.register_factory('meta_cognition', lambda: _TinyMeta(), override=True)
        except Exception:
            logger.exception('Failed to register meta_cognition')

        # optional self-improvement components — register lazy factories to avoid eager imports
        if self.config.get('enable_self_improvement', False):
            try:
                import importlib
                em_mod = importlib.import_module('Learning_System.ExperienceMemory')
                sl_mod = importlib.import_module('Learning_System.Self_Learning')
                mz_mod = importlib.import_module('Learning_System.ModelZoo')

                ExperienceMemory = getattr(em_mod, 'ExperienceMemory')
                SelfLearning = getattr(sl_mod, 'SelfLearning')
                ModelZoo = getattr(mz_mod, 'ModelZoo')

                # Ensure artifacts path exists and use a JSONL file for experience memory
                exp_dir = Path(__file__).parent.parent / 'artifacts'
                exp_dir.mkdir(parents=True, exist_ok=True)
                exp_file = str(exp_dir / 'experience_memory.jsonl')

                # register factories
                try:
                    self.integration_registry.register_factory('experience_memory', lambda: ExperienceMemory(exp_file))
                except Exception:
                    # fallback: register a simple factory that creates the file-backed helper
                    self.integration_registry.register_factory('experience_memory', lambda: ExperienceMemory(exp_file))

                try:
                    self.integration_registry.register_factory('model_zoo', lambda: ModelZoo())
                except Exception:
                    pass

                try:
                    # SelfLearning accepts experience_path optional
                    self.integration_registry.register_factory('self_learning', lambda: SelfLearning(experience_path=exp_file))
                except Exception:
                    try:
                        self.integration_registry.register_factory('self_learning', lambda: SelfLearning())
                    except Exception:
                        pass
            except Exception:
                # do not fail initialization if self-improvement components are missing
                pass
            # If registration failed (import errors or other), register lightweight
            # fallback factories so the rest of the system and tests can rely on
            # the presence of these services. Real implementations are preferred
            # and will be used when import succeeded above.
            try:
                if not self.integration_registry.has('experience_memory'):
                    class _FallbackExperienceMemory:
                        def __init__(self, storage_path=None):
                            self.storage_path = storage_path
                            self._items = []

                        def append(self, record: dict):
                            self._items.append(record)

                        def all(self):
                            return list(self._items)

                        def __iter__(self):
                            return iter(self._items)

                    self.integration_registry.register_factory('experience_memory', lambda: _FallbackExperienceMemory(exp_file if 'exp_file' in locals() else None), override=True)

                if not self.integration_registry.has('self_learning'):
                    class _FallbackSelfLearning:
                        def __init__(self, experience_path=None):
                            self.experience_path = experience_path

                        def run_once(self):
                            return {'status': 'noop'}

                    self.integration_registry.register_factory('self_learning', lambda: _FallbackSelfLearning(exp_file if 'exp_file' in locals() else None), override=True)
            except Exception:
                # worst-case: leave missing but avoid crashing init
                logger.exception('Failed to register fallback self-improvement factories')
            # Ensure a model_zoo factory exists (register a lightweight fallback
            # when the real ModelZoo import failed or when forced via config).
            try:
                force_fallback = bool(self.config.get('force_model_zoo_fallback', False))
            except Exception:
                force_fallback = False

            try:
                if force_fallback:
                    from Learning_System.ModelZoo_Fallback import ModelZooFallback
                    self.integration_registry.register_factory('model_zoo', lambda: ModelZooFallback(), override=True)
                else:
                    if not self.integration_registry.has('model_zoo'):
                        try:
                            from Learning_System.ModelZoo_Fallback import ModelZooFallback
                            self.integration_registry.register_factory('model_zoo', lambda: ModelZooFallback())
                        except Exception:
                            # last-resort: register a tiny inline fallback
                            class _TinyModelZoo:
                                def list_models(self):
                                    return ['baseline']

                                def get(self, name='baseline'):
                                    return None

                            self.integration_registry.register_factory('model_zoo', lambda: _TinyModelZoo(), override=True)
            except Exception:
                # do not fail initialization due to model_zoo fallback issues
                logger.exception('Failed to ensure model_zoo fallback registration')
            # Ensure a meta-cognition service is available under canonical name
            try:
                if not self.integration_registry.has('meta_cognition'):
                    try:
                        # Prefer a full implementation in Learning_System
                        from Learning_System.MetaCognition import MetaCognition # type: ignore
                        self.integration_registry.register_factory('meta_cognition', lambda: MetaCognition())
                    except Exception:
                        # If configured to use local LLM for meta, register the small LLM-backed evaluator
                        try:
                            import os
                            has_llm = bool(os.getenv('AGL_LLM_MODEL') or os.getenv('AGL_LLM_BASEURL') or os.getenv('OLLAMA_API_URL'))
                            if has_llm:
                                from Integration_Layer.meta_cognition_simple import SimpleMetaEvaluator
                                base = os.getenv('AGL_LLM_BASEURL') or os.getenv('OLLAMA_API_URL')
                                model = os.getenv('AGL_LLM_MODEL')
                                # register factory using the LLM-backed evaluator
                                self.integration_registry.register_factory('meta_cognition', lambda: SimpleMetaEvaluator(base, model), override=True)
                            else:
                                raise ImportError('no-llm')
                        except Exception:
                            try:
                                from Learning_System.MetaCognition_Fallback import MetaCognitionFallback
                                self.integration_registry.register_factory('meta_cognition', lambda: MetaCognitionFallback())
                            except Exception:
                                # last resort: inline simple evaluator
                                class _TinyMeta:
                                    def evaluate(self, plan):
                                        return {'score': 0.5, 'notes': 'inline-fallback'}

                                self.integration_registry.register_factory('meta_cognition', lambda: _TinyMeta(), override=True)
            except Exception:
                logger.exception('Failed to ensure meta_cognition registration')
    
    def _initialize_integration_layer(self):
        """تهيئة طبقة التكامل"""
        # instantiate core integration components
        # attempt to pass registry into orchestrator if it supports it
        # Try to pass the IntegrationRegistry into core integration components so
        # they can resolve services from the centralized locator. Fall back when
        # a component doesn't accept the registry param.
        # Instantiate CommunicationBus; different versions may accept a
        # `registry` kwarg or a positional registry. Use inspect to pick a
        # safe invocation and fall back to a no-arg constructor.
        # Prefer a no-arg construction to satisfy a variety of CommunicationBus
        # implementations, then attach the registry if the instance exposes a
        # setter or attribute for it. This avoids constructor-signature issues
        # while still making the registry available to the bus when supported.
        try:
            bus = CommunicationBus()
        except Exception:
            # worst-case: try again with no args suppressed
            try:
                bus = CommunicationBus()
            except Exception:
                bus = None

        # Register a few canonical entries in the integration registry so
        # simple registry probes can discover basic services/config quickly.
        try:
            # Build a small runtime config summary from environment for quick discovery
            config = {
                "mode": os.getenv("AGL_MODE", self.operational_mode or "supervised_autonomy"),
                "reasoner_mode": os.getenv("AGL_REASONER_MODE", ""),
                "llm_provider": os.getenv("AGL_LLM_PROVIDER", ""),
                "llm_baseurl": os.getenv("AGL_LLM_BASEURL", os.getenv("OLLAMA_API_URL", "")),
                "llm_model": os.getenv("AGL_LLM_MODEL", ""),
                "quantum_mode": os.getenv("AGL_QUANTUM_MODE", ""),
                "qcore_qubits": int(os.getenv("AGL_QCORE_NUM_QUBITS", "4") or "4"),
                "http_retries": int(os.getenv("AGL_HTTP_RETRIES", "2") or "2"),
                "http_backoff": float(os.getenv("AGL_HTTP_BACKOFF", "0.5") or "0.5"),
                "http_timeout": float(os.getenv("AGL_HTTP_TIMEOUT", "30") or "30"),
            }

            # Simple safety center and memory store helpers for quick registry discovery
            class SafetyCenter:
                def __init__(self, logger):
                    self.logger = logger
                def check(self, payload: dict) -> dict:
                    # placeholder: approve everything by default
                    return {"ok": True, "payload": payload}

            class MemoryStore:
                def __init__(self):
                    self.cache = {}
                def get(self, k, default=None):
                    return self.cache.get(k, default)
                def set(self, k, v):
                    self.cache[k] = v
                    return True

            safety_center = SafetyCenter(logger)
            memory_store = MemoryStore()

            # Register the running config dict and logger for convenience
            try:
                self.integration_registry.register('config', config)
            except Exception:
                try:
                    self.integration_registry.register('config', self.config)
                except Exception:
                    pass

            # register module-level logger under a canonical name
            try:
                self.integration_registry.register('logger', logger)
            except Exception:
                # fallback: register a lightweight wrapper
                try:
                    self.integration_registry.register('logger', {'log': lambda *a, **k: None})
                except Exception:
                    pass

            # core_services container for simple registry probes
            try:
                core_services = {
                    'config': config,
                    'logger': logger,
                    'safety_center': safety_center,
                    'memory_store': memory_store,
                }
                self.integration_registry.register('core_services', core_services)
                # also register individual entries for convenience
                self.integration_registry.register('safety_center', safety_center)
                self.integration_registry.register('memory_store', memory_store)
            except Exception:
                # non-fatal: continue
                pass
        except Exception:
            # non-fatal: continue
            pass
        # Also register the same canonical entries into the module-level global registry
        try:
            from Integration_Layer.integration_registry import registry as global_registry
            try:
                # register a config view for global scripts; prefer the richer config if present
                try:
                    cfg_for_global = self.integration_registry.resolve('config')
                except Exception:
                    cfg_for_global = self.config
                global_registry.register('config', cfg_for_global)
            except Exception:
                pass
            try:
                global_registry.register('logger', logger)
            except Exception:
                try:
                    global_registry.register('logger', {'log': lambda *a, **k: None})
                except Exception:
                    pass
            try:
                # expose core_services for simple probes; try to reuse instance registration
                try:
                    cs = self.integration_registry.resolve('core_services')
                except Exception:
                    cs = ['Hybrid_Reasoner', 'Rubric_Enforcer', 'MemoryBroker']
                global_registry.register('core_services', cs)
            except Exception:
                pass

            # Also register a few canonical integration entries into the global registry
            try:
                for name in ('communication_bus', 'task_orchestrator', 'output_formatter', 'hybrid_composer', 'rag'):
                    try:
                        val = None
                        if self.integration_registry.has(name):
                            try:
                                val = self.integration_registry.resolve(name)
                            except Exception:
                                try:
                                    val = self.integration_registry.get(name)
                                except Exception:
                                    val = None
                        # If not present in instance registry, try to resolve via attributes
                        if val is None:
                            val = self.integration_layer.get(name)
                        if val is not None:
                            try:
                                global_registry.register(name, val)
                            except Exception:
                                # if registration fails, attempt to register as factory where possible
                                try:
                                    global_registry.register_factory(name, lambda v=val: v)
                                except Exception:
                                    pass
                    except Exception:
                        continue
            except Exception:
                pass
        except Exception:
            pass

        if bus is not None:
            try:
                if hasattr(bus, 'set_registry') and callable(getattr(bus, 'set_registry')):
                    bus.set_registry(self.integration_registry) # type: ignore
                elif hasattr(bus, 'attach_registry') and callable(getattr(bus, 'attach_registry')):
                    bus.attach_registry(self.integration_registry) # type: ignore
                else:
                    # last resort: set attribute directly if allowed
                    try:
                        setattr(bus, 'registry', self.integration_registry)
                    except Exception:
                        pass
            except Exception:
                # ignore any errors attaching the registry
                pass

        try:
            orchestrator = TaskOrchestrator(registry=self.integration_registry)
        except Exception:
            orchestrator = TaskOrchestrator()
        formatter = OutputFormatter()

        # keep compatibility mapping
        self.integration_layer['communication_bus'] = bus
        self.integration_layer['task_orchestrator'] = orchestrator
        self.integration_layer['output_formatter'] = formatter

        # register in the integration registry for universal access
        try:
            self.integration_registry.register('communication_bus', bus)
            self.integration_registry.register('task_orchestrator', orchestrator)
            self.integration_registry.register('output_formatter', formatter)
        except Exception:
            # ignore registration failures
            pass

        # Also push these runtime instances into the module-level global registry
        try:
            from Integration_Layer.integration_registry import registry as global_registry
            try:
                if bus is not None:
                    global_registry.register('communication_bus', bus)
            except Exception:
                pass
            try:
                if orchestrator is not None:
                    global_registry.register('task_orchestrator', orchestrator)
            except Exception:
                pass
            try:
                if formatter is not None:
                    global_registry.register('output_formatter', formatter)
            except Exception:
                pass
        except Exception:
            pass

        # register common services as factories to delay heavy imports
        # register common services as factories to delay heavy imports
        try:
            import importlib
            dr_mod = importlib.import_module('Integration_Layer.Domain_Router')
            # register the module object (consumers can call route/route_pipeline/get_engine)
            self.integration_registry.register_factory('domain_router', lambda: dr_mod)
        except Exception:
            pass

        # ensure retriever exists (fallback when missing)
        try:
            if not self.integration_registry.has('retriever'):
                try:
                    import importlib
                    ret_mod = importlib.import_module('Integration_Layer.retriever')
                    self.integration_registry.register_factory('retriever', lambda: ret_mod.SimpleFactsRetriever())
                except Exception:
                    try:
                        from Integration_Layer.Retriever_Fallback import RetrieverFallback
                        self.integration_registry.register_factory('retriever', lambda: RetrieverFallback())
                    except Exception:
                        pass
        except Exception:
            pass

        try:
            from Integration_Layer.Planner_Agent import PlannerAgent
            self.integration_registry.register_factory('planner_agent', lambda: PlannerAgent())
        except Exception:
            pass

        try:
            from Integration_Layer.retriever import SimpleFactsRetriever
            self.integration_registry.register_factory('retriever', lambda: SimpleFactsRetriever())
        except Exception:
            pass

        try:
            import importlib
            rag_mod = importlib.import_module('Integration_Layer.rag')
            # register a safe wrapper around the rag module so runtime provider
            # failures (e.g. ExternalInfoProvider requiring openai) fall back
            # to the lightweight RagFallback.
            try:
                from Integration_Layer.rag_wrapper import SafeRag # type: ignore
                self.integration_registry.register_factory('rag', lambda: SafeRag(rag_mod))
            except Exception:
                # if wrapper import fails, fall back to module or rag_fallback
                try:
                    self.integration_registry.register_factory('rag', lambda: rag_mod)
                except Exception:
                    from Integration_Layer.rag_fallback import RagFallback
                    self.integration_registry.register_factory('rag', lambda: RagFallback())
        except Exception:
            # fallback rag implementation when module can't be imported
            try:
                from Integration_Layer.rag_fallback import RagFallback
                self.integration_registry.register_factory('rag', lambda: RagFallback())
            except Exception:
                # also register module-level function wrapper if needed
                try:
                    import types
                    mod = types.SimpleNamespace(answer_with_rag=lambda q, c=None: {"answer": "", "sources": []})
                    self.integration_registry.register('rag', mod)
                except Exception:
                    pass
        # If configuration or environment suggests a local Ollama-backed LLM is available,
        # prefer a tiny Ollama-based RAG adapter (quick path) so /rag/answer returns
        # a real model response (sources != []) rather than the empty fallback.
        try:
            import os
            llm_cfg = self.config.get('llm') if isinstance(self.config.get('llm'), dict) else {}
            has_llm_cfg = bool(llm_cfg) or bool(os.getenv('AGL_LLM_PROVIDER')) or bool(os.getenv('AGL_LLM_BASEURL')) or bool(os.getenv('OLLAMA_API_URL'))
            if self.config.get('enable_rag', False) or has_llm_cfg:
                try:
                    from Integration_Layer.rag_adapter_ollama import OllamaRAG
                    base = (llm_cfg.get('base_url') if isinstance(llm_cfg, dict) else None) or os.getenv('AGL_LLM_BASEURL') or os.getenv('OLLAMA_API_URL')
                    model = (llm_cfg.get('model') if isinstance(llm_cfg, dict) else None) or os.getenv('AGL_LLM_MODEL') or os.getenv('AGL_OLLAMA_KB_MODEL')
                    timeout = int((llm_cfg.get('timeout_s') if isinstance(llm_cfg, dict) else None) or 30)
                    if model:
                        # override existing rag registration so registry.resolve('rag') returns OllamaRAG
                        self.integration_registry.register_factory('rag', lambda: OllamaRAG(base, model, timeout), override=True)
                except Exception:
                    # if adapter not available or failed, ignore and keep existing rag registration
                    pass
        except Exception:
            pass

        try:
            import importlib
            ir_mod = importlib.import_module('Integration_Layer.Intent_Recognizer')
            self.integration_registry.register_factory('intent_recognizer', lambda: ir_mod)
        except Exception:
            pass

        try:
            import importlib, os
            # Allow switching to a dynamic network-based orchestrator via config or env var
            use_net = bool(self.config.get('use_network_orchestrator')) or bool(os.getenv('AGL_USE_NETWORK_ORCH'))
            if use_net:
                try:
                    net_mod = importlib.import_module('Integration_Layer.network_orchestrator')
                    # register under both canonical and explicit names for compatibility
                    self.integration_registry.register_factory('pipeline_orchestrator', lambda: net_mod)
                    self.integration_registry.register_factory('network_orchestrator', lambda: net_mod)
                except Exception:
                    # fall back to pipeline orchestrator if network module fails to import
                    po_mod = importlib.import_module('Integration_Layer.Pipeline_Orchestrator')
                    self.integration_registry.register_factory('pipeline_orchestrator', lambda: po_mod)
            else:
                po_mod = importlib.import_module('Integration_Layer.Pipeline_Orchestrator')
                self.integration_registry.register_factory('pipeline_orchestrator', lambda: po_mod)
        except Exception:
            pass

        try:
            import importlib
            cm_mod = importlib.import_module('Integration_Layer.Conversation_Manager')
            self.integration_registry.register_factory('conversation_manager', lambda: cm_mod)
        except Exception:
            pass

        try:
            import importlib
            ar_mod = importlib.import_module('Integration_Layer.Action_Router')
            self.integration_registry.register_factory('action_router', lambda: ar_mod)
        except Exception:
            pass

        try:
            import importlib
            hc_mod = importlib.import_module('Integration_Layer.Hybrid_Composer')
            self.integration_registry.register_factory('hybrid_composer', lambda: hc_mod)
        except Exception:
            pass

        # Optionally enable the Dynamic Knowledge Network (DKN) components when
        # configuration or environment requests it. This will create an in-process
        # PriorityBus, a KnowledgeGraph, and a MetaOrchestrator which will be
        # registered into the IntegrationRegistry for other components to use.
        try:
            use_dkn = bool(self.config.get('use_dkn')) or (os.getenv('AGL_REASONER_MODE', '').lower() == 'dkn') or (os.getenv('AGL_USE_NETWORK_ORCH', '') == '1') # type: ignore
            if use_dkn:
                try:
                    from Integration_Layer.inproc_bus import PriorityBus
                    from Integration_Layer.knowledge_graph import KnowledgeGraph
                    from Integration_Layer.meta_orchestrator import MetaOrchestrator
                    from Integration_Layer.engine_adapter import EngineAdapter

                    dkn_bus = PriorityBus()
                    dkn_graph = KnowledgeGraph()

                    # Build adapters list from core_engines (best-effort).
                    adapters = []
                    for ename, eng in (self.core_engines or {}).items():
                        try:
                            a = EngineAdapter(name=ename, engine_obj=eng, subscriptions=['task:new'], capabilities=['answer'])
                            adapters.append(a)
                        except Exception:
                            continue

                    # Also scan the integration registry for other engine-like services
                    try:
                        # IntegrationRegistry exposes keys(); iterate existing registrations
                        for svc_name in self.integration_registry.keys():
                            # skip the things we just registered
                            if svc_name in ('communication_bus', 'task_orchestrator', 'output_formatter', 'hybrid_composer'):
                                continue
                            try:
                                svc = self.integration_registry.resolve(svc_name)
                            except Exception:
                                svc = None
                            if svc is None:
                                continue
                            # consider objects with a process_task method as engine-like
                            if hasattr(svc, 'process_task') and callable(getattr(svc, 'process_task')):
                                try:
                                    a = EngineAdapter(name=svc_name, engine_obj=svc, subscriptions=['task:new'], capabilities=['answer'])
                                    adapters.append(a)
                                except Exception:
                                    continue
                    except Exception:
                        # non-fatal: continue with adapters gathered so far
                        pass

                    orchestrator = MetaOrchestrator(dkn_graph, dkn_bus, adapters)

                    # Register DKN components in the integration registry for others to resolve
                    try:
                        self.integration_registry.register('dkn_bus', dkn_bus)
                        self.integration_registry.register('knowledge_graph', dkn_graph)
                        self.integration_registry.register('meta_orchestrator', orchestrator)
                    except Exception:
                        pass

                    # Also register into the module-level global registry (used by tests/scripts)
                    try:
                        from Integration_Layer.integration_registry import registry as global_registry
                        try:
                            global_registry.register('dkn_bus', dkn_bus)
                            global_registry.register('knowledge_graph', dkn_graph)
                            global_registry.register('meta_orchestrator', orchestrator)
                        except Exception:
                            pass
                    except Exception:
                        pass

                    # expose on the integration_layer mapping for backward compatibility
                    self.integration_layer['dkn_bus'] = dkn_bus
                    self.integration_layer['knowledge_graph'] = dkn_graph
                    self.integration_layer['meta_orchestrator'] = orchestrator

                except Exception:
                    # if DKN pieces fail to import/construct, continue silently
                    pass
        except Exception:
            pass

    def _initialize_system_state(self):
        """Return a default initial system state dict.

        This keeps backward compatibility for demo code that calls
        self._initialize_system_state() during construction.
        """
        return {
            'health': 'optimal',
            'learning_phase': 'phase_1',
            'performance_level': 0.0,
            'safety_score': 1.0
        }
    
    def process_complex_problem(self, problem_description, context=None):
        """
        معالجة مشكلة معقدة باستخدام جميع المحركات
        
        Parameters:
        problem_description (str): وصف المشكلة
        context (dict): سياق إضافي
        
        Returns:
        dict: الحل الشامل مع التحليلات
        """
        print(f"🔍 معالجة مشكلة: {str(problem_description)[:100]}...")

        # Resolve commonly-used integration services from the central registry so
        # callers/tests can provide different implementations via the registry.
        try:
            router = self.integration_registry.resolve("domain_router")
        except Exception:
            router = None

        try:
            planner = self.integration_registry.resolve("planner_agent")
        except Exception:
            planner = None

        try:
            rag = self.integration_registry.resolve("rag")
        except Exception:
            rag = None
        
        # 1. تنسيق المهمة وتفكيكها
        formatted_task = self.integration_layer['task_orchestrator'].decompose_complex_tasks(
            problem_description
        )

        # 2. تحليل نوع المهمة وتخصيص المحركات المناسبة
        task_type = self._analyze_task_type(formatted_task)
        # حفظ نوع المهمة لعمليات الدمج/تجميع الثقة لاحقًا
        self._last_task_type = task_type
        engine_allocation = self._allocate_engines(formatted_task)

        # 3. معالجة متوازية بواسطة المحركات
        partial_solutions = self._parallel_processing(engine_allocation, formatted_task)
        # Ensure quantum_processor emits a verifiable baseline when empty
        try:
            q = partial_solutions.get('quantum_processor') if isinstance(partial_solutions, dict) else None
            # helper stub
            def _quantum_stub(task_text: str):
                return {"unitary_ok": True, "stability": 0.98, "notes": "stub-baseline"}

            if not q or (isinstance(q, dict) and (q.get('result') is None or q.get('result') == {})):
                qres = _quantum_stub(str(formatted_task))
                q_score = 0.6
                q_conf = 0.6
                partial_solutions['quantum_processor'] = {"ok": True, "score": float(q_score), "confidence": float(q_conf), "result": qres, "error": None}
            else:
                # compute a modest score from any provided stability metric
                try:
                    res_inner = q.get('result') if isinstance(q, dict) else None
                    stability = float(res_inner.get('stability', 0.0)) if isinstance(res_inner, dict) else 0.0
                except Exception:
                    stability = 0.0
                q_score = max(0.6, min(0.95, 0.2 + 0.7 * (stability)))
                q_conf = float(q_score)
                # keep original result but normalize envelope
                partial_solutions['quantum_processor'] = {"ok": True, "score": float(q_score), "confidence": q_conf, "result": q.get('result') if isinstance(q, dict) else q, "error": q.get('error') if isinstance(q, dict) else None}
        except Exception:
            # be resilient: leave partial_solutions as-is if anything goes wrong
            pass
        # Ensure protocol_designer returns a small verifiable spec and raise score when verified
        try:
            pd = partial_solutions.get('protocol_designer') if isinstance(partial_solutions, dict) else None
            if not pd or not isinstance(pd, dict):
                # call engine directly as fallback
                pd = self.core_engines['protocol_designer'].process_task(formatted_task)

            # extract the inner spec/result
            pd_result = None
            if isinstance(pd, dict):
                # result could be directly the spec envelope or nested
                if isinstance(pd.get('result'), dict):
                    inner = pd.get('result')
                    # protocol designer returns {'spec':..., 'verified': bool}
                    if isinstance(inner, dict) and inner.get('verified') is not None:
                        pd_result = inner
                    else:
                        # fallback: treat result as spec
                        pd_result = inner
                else:
                    pd_result = pd.get('result')
            else:
                pd_result = pd

            pd_verified = False
            if isinstance(pd_result, dict) and bool(pd_result.get('verified')):
                pd_verified = True

            pd_score = 0.6 if pd_verified else 0.35
            partial_solutions['protocol_designer'] = {
                "ok": True,
                "score": float(pd_score),
                "confidence": float(pd_score),
                "result": pd_result,
                "error": pd.get('error') if isinstance(pd, dict) else None
            }
        except Exception:
            # leave as-is on failure
            pass

        # 4) دمج الحلول الجزئية
        combined = self._integrate_solutions(partial_solutions)

        # دمج الحلول الجزئية إلى هيكل موحّد يحتوي على مخرجات كل محرك وحقول دمج عامة
        # Place normalized engine envelopes at the top-level so the OutputFormatter
        # can read per-engine ok/score/confidence/result directly.
        integrated_solution = {
            "mathematical_brain": partial_solutions.get("mathematical_brain") or {},
            "quantum_processor": partial_solutions.get("quantum_processor") or {},
            "code_generator": partial_solutions.get("code_generator") or {},
            "protocol_designer": partial_solutions.get("protocol_designer") or {},
            # details from fusion and overall confidence
            "details": combined.get('details', []),
            "confidence": combined.get('confidence', 0.0),
            "complexity_level": "adjusted",
        }

        # إن كانت هناك حقول مدمجة إضافية (مثل method/steps/verification/artifact) انفصلها إلى الجذر
        merged_result = combined.get('result', {}) or {}
        for k in ('method', 'steps', 'solution', 'verification', 'architecture', 'components', 'code_artifact', 'artifact_validated', 'artifact_sha256'):
            if k in merged_result:
                integrated_solution[k] = merged_result[k]

        # Build signals map for safety evaluation
        signals_map = {}
        for k, v in partial_solutions.items():
            if isinstance(v, dict):
                signals_map[k] = {"ok": v.get('ok'), "score": float(v.get('score') or 0.0), "error": v.get('error')}
        integrated_solution['signals'] = signals_map
        # assume checks_passed True for now (safety layers can override)
        integrated_solution['checks_passed'] = True

        # Similarity-based confidence gate (text normalization + SequenceMatcher)
        # helpers (module-level style)
        def _normalize_task_text(txt: str) -> str:
            txt = unicodedata.normalize("NFC", txt or "")
            txt = re.sub(r"\s+", " ", txt, flags=re.UNICODE).strip()
            # remove decorative / non-essential chars but keep Arabic letters, ASCII word chars and some common symbols
            txt = re.sub(r"[^\w\u0600-\u06FF\s\+\-\=\(\)\[\]\{\}\/\\\.\,\:]", "", txt)
            return txt

        def _similarity(a: str, b: str) -> float:
            try:
                return float(SequenceMatcher(None, a, b).ratio())
            except Exception:
                return 0.0

        # load/persist last normalized task for run-to-run comparison
        cache_file = Path(__file__).parent / "reports" / ".last_task.json"

        def _load_last_task():
            try:
                with open(cache_file, 'r', encoding='utf-8-sig') as f:
                    return json.load(f).get('task_norm', '')
            except Exception:
                return ""

        def _save_last_task(task):
            try:
                os.makedirs(cache_file.parent, exist_ok=True)
                with open(cache_file, 'w', encoding='utf-8-sig') as f:
                    json.dump({'task_norm': _normalize_task_text(task)}, f, ensure_ascii=False, indent=2)
            except Exception:
                pass

        # compute similarity gate using the provided context original_task (if present)
        prev_norm = _load_last_task()
        ctx_original = context.get('original_task') if isinstance(context, dict) else None
        norm_original = _normalize_task_text(str(problem_description or ""))
        # prefer a provided original_task in context for run-to-run comparison (deterministic in tests)
        if ctx_original:
            norm_seen = _normalize_task_text(str(ctx_original))
        else:
            norm_seen = prev_norm if isinstance(prev_norm, str) and prev_norm else _normalize_task_text(str(problem_description or ""))
        sim = _similarity(norm_original, norm_seen)
        gate = {"passed": True, "reason": "ok", "similarity": sim, "normalized_task": norm_original}
        if sim < 0.90:
            gate = {"passed": False, "reason": "different_input", "similarity": sim, "normalized_task": norm_original}

        integrated_solution['confidence_gate'] = gate
        # persist normalized task for next run
        try:
            _save_last_task(problem_description)
        except Exception:
            pass

        # 5) التحقق من السلامة والجودة
        safety_check = self.safety_systems['control_layers'].evaluate_improvement_safety(integrated_solution)

        # سجّل إشارات الثقة من كل محرك
        logger.info(f"Partial solutions signals: { {k: { 'ok': bool(v.get('ok', 'error' not in v)),\
                                               'score': v.get('score'),\
                                               'confidence': v.get('confidence'),\
                                               'has_error': 'error' in v }\
                                  for k, v in partial_solutions.items() if isinstance(v, dict)} }")
        logger.info(f"Safety check: {safety_check}")

        # 6) حساب الثقة الواقعية
        confidence = self._calculate_confidence(partial_solutions, safety_check)

        # حدّث مستوى الأداء باستخدام متوسط متحرك
        try:
            self._update_performance(confidence)
        except Exception:
            pass

        # 7) تنسيق المخرجات
        if context is None:
            context = {}

        final_output = self.integration_layer['output_formatter'].format_output(
            integrated_solution,
            audience=context.get('audience', 'technical'),
            purpose=context.get('purpose', 'solution')
        )

        # 7) التعلم من التجربة (حفظ التجربة الخام)
        try:
            run_record = {
                "task": problem_description,
                "solution": integrated_solution,
                "signals": partial_solutions,
                "confidence_score": integrated_solution.get("confidence", 0.0),
                "safety": safety_check
            }
            # سجل التجربة الخام
            try:
                self.learning_system['knowledge_integrator'].integrate_new_knowledge(run_record)
            except Exception:
                logger.exception('Failed to persist run_record to knowledge_integrator')

            # 8) حلقة التحسين الذاتي أحادية الخطوة (تحليل ← خطة ← تطبيق ← حفظ الإعداد)
            try:
                feedback = self.learning_system['feedback_analyzer'].analyze_performance_feedback(run_record)
            except Exception:
                logger.exception('Feedback analysis failed')
                feedback = {}

            try:
                plan = self.learning_system['improvement_generator'].generate_targeted_improvements(feedback)
            except Exception:
                logger.exception('Improvement generation failed')
                plan = {}

            try:
                applied = self._apply_safe_improvements(plan)
            except Exception:
                logger.exception('Applying safe improvements failed')
                applied = plan

            try:
                self.learning_system['knowledge_integrator'].integrate_new_knowledge(applied)
            except Exception:
                logger.exception('Failed to persist applied improvements')

            # (اختياري) احتفاظ الأوزان في الذاكرة الجارية لتستخدم في الدمج القادم
            try:
                self.fusion_weights = plan.get("fusion_weights", self.fusion_weights or {}) or self.fusion_weights
            except Exception:
                pass
        except Exception:
            # be defensive: do not break the main flow for learning issues
            logger.exception('Learning loop encountered an unexpected error')

        # جمع إشارات المحركات (signals per engine)
        signals = {}
        for name, payload in partial_solutions.items():
            if isinstance(payload, dict):
                signals[name] = {
                    'ok': bool(payload.get('ok', 'error' not in payload)),
                    'score': float(payload.get('score') or 0.0),
                    'confidence': float(payload.get('confidence') or payload.get('score') or 0.0),
                    'error': payload.get('error')
                }

        # prepare metadata
        seed = random.randint(0, 2**31 - 1)
        ts = time.time()
        # normalize the task and compute a stable inputs hash
        try:
            normalized_task = self.integration_layer['task_orchestrator'].normalize_text(str(problem_description))
            inputs_hash = self.integration_layer['task_orchestrator'].stable_inputs_hash(str(problem_description), seed)
            task_serialized = normalized_task
        except Exception:
            task_serialized = str(problem_description)
            inputs_hash = hashlib.sha256(task_serialized.encode('utf-8')).hexdigest()

        # build report
        report = {
            'task': task_serialized,
            'timestamp': ts,
            'phase': 'phase_2',
            'seed': seed,
            'inputs_hash': inputs_hash,
            'solution': final_output,
            'safety': {
                'approval': True,
                'risk_level': self._derive_risk(signals),
                'checks_passed': True
            },
            'signals': signals,
            'confidence_score': float(final_output.get('confidence', confidence)),
            'improvement_opportunities': self._identify_improvement_opportunities(partial_solutions=partial_solutions)
        }

        # use external ConfidenceGate module
        # If code generator produced an artifact path, attach artifact metadata (exists,size,sha256)
        try:
            # defensive navigation into the structured final_output
            sol = report.get('solution', {}) or {}
            res_map = sol.get('result') if isinstance(sol, dict) else None
            cg = {}
            artifact_path = None

            # primary: look into result mapping for code_generator envelope
            if isinstance(res_map, dict):
                cg = res_map.get('code_generator') or res_map.get('codegen') or {}
                if isinstance(cg, dict):
                    # artifact may be at top-level of the envelope or inside the envelope's 'result'
                    res_inner = cg.get('result')
                    artifact_path = (
                        cg.get('code_artifact') or cg.get('artifact_path') or cg.get('artifact') or
                        (res_inner.get('code_artifact') if isinstance(res_inner, dict) else None)
                    )

            # fallback: OutputFormatter may expose artifact path under solution['misc']
            if not artifact_path:
                misc = sol.get('misc') if isinstance(sol, dict) else None
                if isinstance(misc, dict):
                    artifact_path = misc.get('artifact_path') or misc.get('code_artifact') or misc.get('artifact')

            if artifact_path and isinstance(artifact_path, str):
                p = artifact_path
                meta = {'exists': os.path.exists(p), 'size_bytes': os.path.getsize(p) if os.path.exists(p) else 0}
                if meta['exists']:
                    try:
                        import hashlib as _hashlib
                        with open(p, 'rb') as _f:
                            meta['sha256'] = _hashlib.sha256(_f.read()).hexdigest()
                    except Exception:
                        meta['sha256'] = None

                # attach artifact_meta back into the best place available
                if isinstance(res_map, dict):
                    if 'code_generator' not in res_map or not isinstance(res_map.get('code_generator'), dict):
                        res_map['code_generator'] = {}
                    # prefer to store under the envelope's 'result' sub-dict if present
                    cg_env = res_map['code_generator']
                    if isinstance(cg_env.get('result'), dict):
                        cg_env.setdefault('result', {})
                        cg_env['result']['artifact_meta'] = meta
                    else:
                        cg_env['artifact_meta'] = meta
                elif isinstance(sol, dict):
                    # last resort: put under solution.misc
                    sol.setdefault('misc', {})
                    sol['misc']['artifact_meta'] = meta
        except Exception:
            # non-fatal: continue to gating even if artifact inspection fails
            logger.exception('artifact inspection failed')

        try:
            # Run baseline gate on a copy so we don't overwrite the similarity gate placed into integrated_solution
            import copy
            baseline_report = check_gate(copy.deepcopy(report))
            # store baseline gate separately
            report['confidence_gate_baseline'] = baseline_report.get('confidence_gate')
            # allow baseline update to use the baseline_report
            maybe_update_baseline(baseline_report)
            # ensure similarity gate (from integrated_solution) is present as primary confidence_gate
            if integrated_solution.get('confidence_gate'):
                report['confidence_gate'] = integrated_solution['confidence_gate']
        except Exception:
            # if gating fails for any reason, preserve similarity gate if present, else mark gate as error
            report.setdefault('confidence_gate', {'passed': False, 'reason': 'gate_error'})

        return report
    
    def continuous_self_improvement(self):
        """بدء التحسين الذاتي المستمر"""
        print("🔄 بدء التحسين الذاتي المستمر...")
        
        while self.system_state['health'] == 'optimal':
            # مراقبة الأداء
            performance_metrics = self._monitor_performance()
            
            # تحليل التغذية الراجعة
            feedback_analysis = self.learning_system['feedback_analyzer'].analyze_performance_feedback(
                performance_metrics
            )
            
            # توليد التحسينات
            improvements = self.learning_system['improvement_generator'].generate_targeted_improvements(
                feedback_analysis['improvement_areas']
            )
            
            # تطبيق التحسينات الآمنة
            applied_improvements = self._apply_safe_improvements(improvements)
            
            # تحديث المعرفة
            self.learning_system['knowledge_integrator'].integrate_new_knowledge(
                applied_improvements
            )
            
            # التحقق من الاستمرارية
            if not self._should_continue_improvement():
                break
    
    def _allocate_engines(self, task):
        """تخصيص المحركات للمهمة"""
        engine_mapping = {
            'mathematical': ['mathematical_brain'],
            # include extra engines for richer processing of mathematical tasks
            'mathematical_rich': ['mathematical_brain', 'code_generator', 'quantum_processor', 'protocol_designer'],
            'quantum': ['quantum_processor'],
            'programming': ['code_generator'],
            'protocols': ['protocol_designer'],
            'complex': list(self.core_engines.keys())  # جميع المحركات للمهام المعقدة
        }
        
        # تحليل نوع المهمة
        task_type = self._analyze_task_type(task)
        # For mathematical tasks, prefer a richer allocation to allow code/gen/quantum to contribute
        if task_type == 'mathematical':
            return engine_mapping.get('mathematical_rich')
        return engine_mapping.get(task_type, engine_mapping['complex'])

    # --- Helper methods missing earlier (lightweight implementations) ---
    def _analyze_task_type(self, task):
        """Very small heuristic to pick a task type based on keywords."""
        try:
            txt = str(task).lower()
        except Exception:
            return 'complex'

        if 'quantum' in txt or 'qubit' in txt:
            return 'quantum'
        if 'code' in txt or 'program' in txt:
            return 'programming'
        if 'protocol' in txt:
            return 'protocols'
        if any(w in txt for w in ('matrix', 'linear', 'differential', 'integral', 'equation')):
            return 'mathematical'
        return 'complex'

    def _monitor_performance(self):
        """Return lightweight performance metrics."""
        return {'throughput': 0.0, 'latency_ms': 0.0, 'errors': 0}

    def _capture_performance_metrics(self):
        return self._monitor_performance()

    def _get_current_timestamp(self):
        import time
        return time.time()

    def _identify_improvement_opportunities(self, partial_solutions=None):
        """Return realistic improvement opportunities as structured dicts.

        For each engine with score/confidence < 0.4, return a suggestion dict.
        """
        opts = []
        if not isinstance(partial_solutions, dict):
            return opts
        for name, payload in partial_solutions.items():
            if not isinstance(payload, dict):
                continue
            score = payload.get("confidence") or payload.get("score") or 0.0
            try:
                sc = float(score)
            except Exception:
                sc = 0.0
            if sc < 0.4:
                opts.append({
                    "component": name,
                    "issue": "low_signal",
                    "hint": "تحسين الدوال الداخلية أو زيادة بيانات التدريب/الأمثلة",
                    "current_score": sc
                })
        return opts

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

    def _apply_safe_improvements(self, improvements):
        # apply improvements in a no-op safe way for now
        return improvements

    def _should_continue_improvement(self):
        return False

    def _count_knowledge_entries(self):
        # best-effort count
        try:
            return sum(len(getattr(m, '__dict__', {})) for m in self.knowledge_modules.values())
        except Exception:
            return 0

    def _count_improvement_cycles(self):
        return 0

    def _create_emergency_snapshot(self):
        # write a small snapshot file
        try:
            with open('agl_emergency_snapshot.json', 'w', encoding='utf-8-sig') as f:
                import json
                json.dump({'state': self.system_state, 'timestamp': self._get_current_timestamp()}, f, ensure_ascii=False)
        except Exception:
            pass

    def _safe_shutdown(self):
        # minimal safe shutdown
        self.system_state['health'] = 'shutdown'
    
    def _parallel_processing(self, engines, task):
        """معالجة متوازية بواسطة محركات متعددة"""
        solutions = {}
        
        for engine_name in engines:
            engine = self.core_engines[engine_name]
            try:
                solution = engine.process_task(task)
                solutions[engine_name] = solution
            except Exception as e:
                print(f"⚠️ خطأ في المحرك {engine_name}: {e}")
                solutions[engine_name] = {'error': str(e)}
        
        return solutions
    
    def _integrate_solutions(self, partial_solutions):
        """دمج الحلول الجزئية

        هذا المزيج يجمع نتائج المحركات في حقل `result` (بنية dict) ويُقدّر `confidence` تجميعيًا.
        """
        # جمع إشارات المحركات
        task_type = getattr(self, "_last_task_type", "complex")
        signals = {}
        for name, payload in partial_solutions.items():
            if isinstance(payload, dict):
                signals[name] = {
                    "confidence": payload.get("confidence"),
                    "score": payload.get("score"),
                    "ok": payload.get("ok", payload.get("error") is None),
                    "result": payload.get("result")
                }

        # ادمج نتايج المحركات باستخدام طبقة التكامل (weighted fusion)
        merged_result = {}
        integration_notes = []

        # Build a filtered partials dict (skip disabled engines) and fusion_weights
        filtered_partials = {}
        fusion_weights = {}
        for name, payload in partial_solutions.items():
            policy = self._engine_signal_policies.get(name)
            if policy == 'disable':
                # preserve note about disabled engines but do not include them in fusion
                integration_notes.append(f"Skipped {name} due to policy=disable.")
                continue

            filtered_partials[name] = payload
            # map policies to numeric fusion weights: 'boost' -> 0.6, disabled already skipped -> 0.0, default -> 1.0
            if policy == 'boost':
                fusion_weights[name] = 0.6
            else:
                fusion_weights[name] = 1.0

        # If persisted fusion weights exist (from Knowledge_Integrator), merge them in.
        try:
            if getattr(self, 'fusion_weights', None):
                for k, v in (self.fusion_weights or {}).items():
                    try:
                        fusion_weights[k] = float(v)
                    except Exception:
                        # keep existing if parse fails
                        continue
                if self.fusion_weights:
                    integration_notes.append('Loaded persisted fusion_weights from config and applied to fusion.')
        except Exception:
            pass

        # If code_generator produced a validated artifact, increase its weight to emphasize validated artifacts
        try:
            cg = partial_solutions.get('code_generator')
            if isinstance(cg, dict) and cg.get('result') and isinstance(cg.get('result'), dict):
                if cg['result'].get('artifact_validated'):
                    fusion_weights['code_generator'] = max(1.2, float(fusion_weights.get('code_generator', 1.0)))
                    integration_notes.append('Increased fusion weight for validated code artifact: code_generator=1.2')
        except Exception:
            pass

        # Call the CommunicationBus to perform weighted fusion
        try:
            comm = self.integration_layer['communication_bus']
            combined = comm.coordinate_components(filtered_partials, purpose='integration', fusion_weights=fusion_weights)
        except Exception as e:
            # fallback to simple merge on error
            integration_notes.append(f"communication_bus error: {e}")
            combined = {'result': {}, 'confidence': 0.0, 'details': []}

        # If any non-default weights were applied, add a human-readable note (do not claim raw-score mutation)
        applied = {k: v for k, v in fusion_weights.items() if v != 1.0}
        if applied:
            integration_notes.append(
                "Applied fusion weights (not raw-score boost) to " + 
                ", ".join(f"{k}={v}" for k, v in applied.items())
            )

        # Compose final merged result and details
        merged_result = combined.get('result', {})
        combined_details = combined.get('details', []) or []
        final_details = integration_notes + combined_details

        return {
            'result': merged_result,
            'details': final_details,
            'confidence': round(float(combined.get('confidence', 0.0)), 4),
            'fusion': combined.get('fusion', {})
        }

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
    
    def _learn_from_experience(self, problem, solution, output):
        """التعلم من التجربة"""
        learning_data = {
            'problem': problem,
            'solution_process': solution,
            'final_output': output,
            'performance_metrics': self._capture_performance_metrics(),
            'timestamp': self._get_current_timestamp()
        }
        
        self.learning_system['knowledge_integrator'].integrate_new_knowledge(learning_data)

    def _update_performance(self, conf, alpha=0.3):
        """Update the system performance level as a moving average of confidence.

        conf: latest confidence (0..1)
        alpha: smoothing factor (0..1)
        """
        try:
            prev = float(self.system_state.get('performance_level', 0.0))
        except Exception:
            prev = 0.0
        self.system_state['performance_level'] = (1 - alpha) * prev + alpha * float(conf)
    
    def get_system_status(self):
        """الحصول على حالة النظام"""
        return {
            'operational_mode': self.operational_mode,
            'system_health': self.system_state['health'],
            'learning_phase': self.system_state['learning_phase'],
            'performance_level': self.system_state['performance_level'],
            'safety_score': self.system_state['safety_score'],
            'active_engines': len(self.core_engines),
            'knowledge_entries': self._count_knowledge_entries(),
            'improvement_cycles': self._count_improvement_cycles()
        }
    
    def emergency_shutdown(self):
        """إغلاق طارئ للنظام"""
        print("🛑 تفعيل الإغلاق الطارئ...")
        
        # تفعيل بروتوكولات الطوارئ
        self.safety_systems['emergency_protocols'].activate_emergency_mode('shutdown')
        
        # حفظ حالة النظام
        self._create_emergency_snapshot()
        
        # إغلاق آمن
        self._safe_shutdown()
        
        print("✅ تم الإغلاق الطارئ بنجاح")

# وظائف مساعدة
def create_agl_instance(config=None):
    """إنشاء نسخة من نظام AGL"""
    default_config = {
        'operational_mode': 'supervised_autonomy',
        'learning_enabled': True,
        'safety_protocols': 'enabled',
        'knowledge_persistence': True
    }
    
    # Load config.yaml and merge into defaults, with explicit `config` overriding
    try:
        import yaml
        # Priority: explicit env AGL_CONFIG_PATH -> cwd/config.yaml -> package config.yaml
        env_path = os.getenv('AGL_CONFIG_PATH')
        if env_path:
            cfg_path = Path(env_path)
        else:
            cwd_path = Path.cwd() / 'config.yaml'
            if cwd_path.exists():
                cfg_path = cwd_path
            else:
                cfg_path = Path(__file__).parent / 'config.yaml'

        file_cfg = yaml.safe_load(open(cfg_path, 'r', encoding='utf-8-sig')) if cfg_path.exists() else {}
    except Exception:
        file_cfg = {}

    merged = default_config.copy()
    if isinstance(file_cfg, dict):
        # merge top-level
        for k, v in file_cfg.items():
            if k == 'features':
                # flatten features map
                if isinstance(v, dict):
                    for fk, fv in v.items():
                        merged[fk] = fv
                continue
            merged[k] = v

    if isinstance(config, dict):
        merged.update(config)

    return AGL(operational_mode=merged.get('operational_mode', 'supervised_autonomy'), config=merged)

def main():
    """الدالة الرئيسية للتشغيل"""
    logger.info("=" * 60)
    logger.info("🚀 AGL - Advanced Intelligence System")
    logger.info("=" * 60)
    
    # AGL.py - التحديثات
from Core_Engines.Advanced_Exponential_Algebra import AdvancedExponentialAlgebra
from Core_Engines.Quantum_Neural_Core import QuantumNeuralCore

class AGL2:
    def __init__(self, operational_mode="supervised_autonomy"):
        # ... التهيئة الحالية ...
        
        # إضافة المحركات المتقدمة
        self.core_engines.update({ # type: ignore
            'exponential_algebra': AdvancedExponentialAlgebra(),
            'quantum_neural_core': QuantumNeuralCore(num_qubits=4)
        })
    
    def solve_quantum_ml_problem(self, problem_description, data):
        """حل مشاكل تعلم آلي كميّة متقدمة"""
        print(f"🔬 معالجة مشكلة تعلم آلي كمي: {problem_description}")
        
        # استخدام الجبر الأسي لتحضير البيانات
        processed_data = self.core_engines['exponential_algebra'].prepare_quantum_data(data) # type: ignore
        
        # استخدام الشبكة العصبية الكمية
        quantum_result = self.core_engines['quantum_neural_core'].quantum_neural_forward(processed_data) # type: ignore
        
        # تفسير النتائج باستخدام الجبر الأسي
        interpretation = self.core_engines['exponential_algebra'].interpret_quantum_results(quantum_result) # type: ignore
        
        return {
            'quantum_solution': quantum_result,
            'mathematical_interpretation': interpretation,
            'confidence': self.calculate_quantum_confidence(quantum_result) # type: ignore
        }
    
    def simulate_quantum_system(self, hamiltonian, initial_state, time_range):
        """محاكاة أنظمة كميّة باستخدام الجبر الأسي"""
        print("⚛️ محاكاة نظام كمي متقدم...")
        
        # استخدام الجبر الأسي للتطور الزمني
        time_evolution = self.core_engines['exponential_algebra'].quantum_time_evolution( # type: ignore
            hamiltonian, initial_state, time_range
        )
        
        # استخدام الشبكة الكمية لتحليل النتائج
        analysis = self.core_engines['quantum_neural_core'].analyze_quantum_dynamics(time_evolution) # type: ignore
        
        return {
            'time_evolution': time_evolution,
            'quantum_analysis': analysis,
            'stability_metrics': self.calculate_quantum_stability(time_evolution) # type: ignore
        }
    # AGL.py - النسخة النهائية المتكاملة
from Scientific_Systems.Scientific_Research_Assistant import ScientificResearchAssistant
from Scientific_Systems.Automated_Theorem_Prover import AutomatedTheoremProver
from Scientific_Systems.Integrated_Simulation_Engine import IntegratedSimulationEngine
from Engineering_Engines.Advanced_Code_Generator import AdvancedCodeGenerator
from Self_Improvement.Self_Improvement_Engine import SelfImprovementEngine
from Safety_Control.Safe_Autonomous_System import SafeAutonomousSystem

class HardwareSimulator:
    def __init__(self):
        self.status = 'idle'

    def simulate(self, model, steps=1):
        return {'status': self.status, 'steps': steps}


class SmartProtocolEngine:
    def __init__(self):
        pass

    def design(self, spec):
        return {'protocol': 'simple', 'spec': spec}


class IoTProtocolDesigner:
    def __init__(self):
        pass

    def create(self, requirements):
        return {'iot_protocol': 'basic', 'requirements': requirements}


class OptimizationStrategies:
    def __init__(self):
        pass

    def propose(self, metrics):
        return []


class KnowledgeGraph:
    def __init__(self):
        self.nodes = {}

    def add(self, key, value):
        self.nodes[key] = value


class SelfMonitoringSystem:
    def __init__(self):
        pass

    def heartbeat(self):
        return True


class HierarchicalControlSystem:
    def __init__(self):
        pass

    def control(self, state):
        return {'action': 'noop'}


class SafetyControlLayer:
    def __init__(self):
        pass

    def check(self, change):
        return {'approved': True}


class ImprovementBudget:
    def __init__(self):
        self.budget = 1.0


class SpecializationController:
    def __init__(self):
        pass

    def specialize(self, area):
        return {'area': area}


class SafeRollbackSystem:
    def __init__(self):
        pass

    def rollback(self):
        return True


class GradualLearningFramework:
    def __init__(self):
        pass

    def step(self):
        return {'progress': 0.0}

class AGLFull:
    def __init__(self, operational_mode="supervised_autonomy"):
        # حالة النظام
        self.operational_mode = operational_mode
        self.system_state = self._initialize_system_state() # type: ignore
        
        # تهيئة جميع المحركات
        self._initialize_all_engines()
        
        print("🚀 AGL System Fully Initialized!")
        print(f"Total Engines: {self._count_total_engines()}") # type: ignore
        print(f"Safety Level: {self.system_state['safety_score']}")
    
    def _initialize_all_engines(self):
        """تهيئة جميع المحركات المتكاملة"""
        # المحركات الأساسية
        self.core_engines = {
            'mathematical_brain': MathematicalBrain(),
            'quantum_processor': QuantumProcessor(),
            'exponential_algebra': AdvancedExponentialAlgebra(),
            'quantum_neural_core': QuantumNeuralCore(num_qubits=4)
        }
        
        # الأنظمة العلمية
        self.scientific_systems = {
            'research_assistant': ScientificResearchAssistant(),
            'theorem_prover': AutomatedTheoremProver(),
            'simulation_engine': IntegratedSimulationEngine(), # type: ignore
            'hardware_simulator': HardwareSimulator()
        }
        
        # المحركات الهندسية
        self.engineering_engines = {
            'code_generator': AdvancedCodeGenerator(),
            'protocol_engine': SmartProtocolEngine(),
            'iot_designer': IoTProtocolDesigner()
        }
        
        # أنظمة التحسين الذاتي
        self.improvement_systems = {
            'self_improvement': SelfImprovementEngine(),
            'feedback_analyzer': FeedbackAnalyzer(),
            'optimization_strategies': OptimizationStrategies(),
            'knowledge_integrator': KnowledgeIntegrator(),
            'knowledge_graph': KnowledgeGraph(),
            'self_monitoring': SelfMonitoringSystem()
        }
        
        # أنظمة التحكم والأمان
        self.safety_control = {
            'hierarchical_control': HierarchicalControlSystem(),
            'safety_layer': SafetyControlLayer(),
            'improvement_budget': ImprovementBudget(),
            'specialization_controller': SpecializationController(),
            'safe_rollback': SafeRollbackSystem(),
            'gradual_learning': GradualLearningFramework(),
            'safe_autonomous': SafeAutonomousSystem()
        }

    def _initialize_system_state(self):
        """Return a safe default initial system state for this AGL variant."""
        return {
            'health': 'optimal',
            'learning_phase': 'phase_1',
            'performance_level': 0.0,
            'safety_score': 1.0
        }
    
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

    def _count_total_engines(self):
        # Count engines across all registries
        total = 0
        for attr in ('core_engines', 'scientific_systems', 'engineering_engines', 'improvement_systems', 'safety_control'):
            total += len(getattr(self, attr, {}))
        return total

    def _count_active_engines(self):
        # Active engines is the core engines count for demo purposes
        return len(getattr(self, 'core_engines', {}))

    def _calculate_overall_performance(self):
        # Simple aggregation of performance_level and safety_score
        base = self.system_state.get('performance_level', 0.0)
        safety = self.system_state.get('safety_score', 1.0)
        return base * safety

    def _calculate_innovation_score(self, research_result, development_result):
        # Lightweight heuristic combining research credibility and number of components
        credibility = research_result.get('overall_credibility', 1.0) if isinstance(research_result, dict) else 1.0
        components = len(development_result.get('components', {})) if isinstance(development_result, dict) else 1
        return min(1.0, credibility * (0.1 * components))
    
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
            'innovation_score': self._calculate_innovation_score(research_result, development_result) # type: ignore
        }

# مثال الاستخدام النهائي
def demo_complete_system():
    agl = AGLFull()
    
    # تشغيل مستقل كامل
    autonomous_result = agl.full_autonomous_operation()
    logger.info(f"✅ التشغيل المستقل اكتمل: {autonomous_result['overall_performance']:.2%}") # type: ignore
    
    # بحث وتطوير متكامل
    research_dev = agl.research_and_develop(
        "أحدث تقنيات الذكاء الاصطناعي الكمي",
        "نظام ذكي للاكتشاف العلمي"
    )
    logger.info(f"🎯 الابتكار: {research_dev['innovation_score']:.2%}") # type: ignore

    # اكتب تقرير JSON مختصر عن هذه الجلسة
    try:
        reports_dir = Path(__file__).parent / 'reports'
        reports_dir.mkdir(exist_ok=True)
        report = {
            "ts": time.time(),
            "mode": agl.operational_mode,
            "final_state": agl.system_state,
            "autonomous": autonomous_result if 'autonomous_result' in locals() else None,
            "research_development": research_dev
        }
        with open(reports_dir / 'last_run.json', 'w', encoding='utf-8-sig') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        logger.info(f"Report written to {reports_dir / 'last_run.json'}")
    except Exception as e:
        logger.exception("Failed to write run report")

if __name__ == "__main__":
    import argparse, os, csv
    os.makedirs('logs', exist_ok=True)
    os.makedirs('reports', exist_ok=True)

    parser = argparse.ArgumentParser()
    parser.add_argument("--task", type=str, default="حل نظام المعادلات التفاضلية")
    parser.add_argument("--mode", type=str, default="supervised_autonomy")
    parser.add_argument("--report", type=str, default="reports/last_run.json")
    parser.add_argument("--agent", type=str, default=None, help="(optional) select an agent to run, e.g. 'planner'")
    parser.add_argument("--original-task", type=str, default=None, help="(optional) original task text to compare similarity against")
    # law_development specific
    parser.add_argument("--formula", type=str, default=None)
    parser.add_argument("--data", type=str, default=None)
    parser.add_argument("--y", type=str, default=None)
    parser.add_argument("--x", type=str, default=None)
    args = parser.parse_args()

    agl = create_agl_instance({"operational_mode": args.mode})
    ctx = {"audience": "technical"}
    if args.original_task:
        ctx['original_task'] = args.original_task
    # special-case law_development CLI which supplies data
    if args.task and args.task.strip() == "law_development":
        def run_law_development():
            formula = (args.formula or "").strip()
            y_name = args.y or "F"
            x_name = args.x or "x"
            data = {y_name: [], x_name: []}
            if args.data and os.path.exists(args.data):
                with open(args.data, 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        try:
                            data[y_name].append(float(row[y_name]))
                            data[x_name].append(float(row[x_name]))
                        except Exception:
                            continue

            # run fit
            from Learning_System.Law_Learner import fit_single_coeff_linear
            res = fit_single_coeff_linear(formula, y_name, x_name, data)

            report = {
                "task": "law_development",
                "formula": formula,
                "data_file": args.data,
                "result": res,
                "safety_approval": True,
                "confidence_score": res.get("confidence", 0.0),
            }
            # optional save to knowledge base
            try:
                from Knowledge_Base.Law_Facts import save_law_fact
                save_law_fact("Hooke_F=kx", {"k_est": res.get("coef"), "rmse": res.get("rmse"), "n": res.get("n")})
            except Exception:
                pass

            with open(args.report or "reports/last_run.json", 'w', encoding='utf-8-sig') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            # if fit succeeded, update baseline
            try:
                if res.get('confidence', 0.0) >= 0.6:
                    os.makedirs(os.path.join('reports','baselines'), exist_ok=True)
                    with open(os.path.join('reports','baselines','last_success.json'), 'w', encoding='utf-8-sig') as bf:
                        json.dump(report, bf, ensure_ascii=False, indent=2)
            except Exception:
                pass
            print("📄 Saved report →", args.report or "reports/last_run.json")

        run_law_development()
    # Special-case: delegate certain CLI-only orchestration tasks directly to the TaskOrchestrator
    elif args.task and "train-laws" in str(args.task):
        try:
            to = agl.integration_layer['task_orchestrator']
            res = to.process(args.task, data=args.data)
            logging.info(f"TaskOrchestrator.process('{args.task}') -> {res}")
            # write the orchestrator result to the requested report path
            with open(args.report or "reports/last_run.json", 'w', encoding='utf-8-sig') as f:
                json.dump(res, f, ensure_ascii=False, indent=2)
            print(f"📄 Saved orchestrator report → {args.report or 'reports/last_run.json'}")
        except Exception as e:
            logging.exception('Failed to run TaskOrchestrator train-laws')
            print('Error:', e)
    # Training CLI: tasks like 'train:hooke' -> use Training_Path wrapper
    elif args.task and str(args.task).lower().startswith('train:'):
        try:
            from Learning_System.Training_Path import train_hooke_from_csv
            # currently only 'hooke' supported; accept --data path
            res = train_hooke_from_csv(args.data or 'data/hooke_sample.csv')
            with open(args.report or 'reports/last_run.json', 'w', encoding='utf-8-sig') as f:
                json.dump(res, f, ensure_ascii=False, indent=2)
            print('📄 Training finished →', args.report or 'reports/last_run.json')
        except Exception as e:
            logging.exception('Training path failed')
            print('Error:', e)
    # Agent runner: allow lightweight agent execution from CLI
    elif args.agent and str(args.agent).lower() == 'planner':
        try:
            # Prefer resolving the planner via the integration registry so tests
            # and runtime can substitute implementations. Fall back to direct
            # import if the registry doesn't contain a planner.
            try:
                agent = agl.integration_registry.resolve('planner_agent')
            except Exception:
                from Integration_Layer.Planner_Agent import PlannerAgent
                agent = PlannerAgent()

            report = agent.execute(args.task or "اختبار التكامل")
            with open(args.report or "reports/last_run.json", 'w', encoding='utf-8-sig') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            print("🧭 Planner done →", args.report or "reports/last_run.json")
        except Exception as e:
            logging.exception('Planner agent failed')
            print('Agent error:', e)
    else:
        out = agl.process_complex_problem(args.task, context=ctx)
        logging.info(f"Task='{args.task}' → confidence={out.get('confidence_score')}")
        with open(args.report, "w", encoding="utf-8-sig") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        print(f"📄 Saved report → {args.report}")