"""Core_Engines public surface and bootstrap helpers.

This module exposes a mapping of known engine modules and a small bootstrap
helper that registers available engines into a provided registry. It is
designed to be robust: optional/heavy engines are skipped safely if their
dependencies are not installed.
"""

from importlib import import_module
from typing import Dict, Any, Tuple
import logging

from .orchestrator import Orchestrator

# اسم الوحدة → (مسار الوحدة, اسم الفئة داخل الوحدة أو None)
ENGINE_SPECS = {
	"Mathematical_Brain":        ("Core_Engines.Mathematical_Brain",       "MathematicalBrain"),
	"Quantum_Processor":         ("Core_Engines.Quantum_Processor",        "QuantumProcessor"),
	"Code_Generator":            ("Core_Engines.Code_Generator",           "CodeGenerator"),
	"Protocol_Designer":         ("Core_Engines.Protocol_Designer",        "ProtocolDesigner"),
	"Visual_Spatial":            ("Core_Engines.Visual_Spatial",           "VisualSpatial"),

	# محركات عليا / اختيارية
	"Strategic_Thinking":        ("Core_Engines.Strategic_Thinking",       "StrategicThinking"),
	"Social_Interaction":        ("Core_Engines.Social_Interaction",       "SocialInteraction"),
	"Creative_Innovation":       ("Core_Engines.Creative_Innovation",      "CreativeInnovation"),
	"NLP_Advanced":              ("Core_Engines.NLP_Advanced",             "NLPAdvanced"),
	"Causal_Graph":              ("Core_Engines.Causal_Graph",             "CausalGraph"),
	"Reasoning_Layer":           ("Core_Engines.Reasoning_Layer",          "ReasoningLayer"),
    "CAUSAL_GRAPH":             ("Core_Engines.Causal_Graph",             "CausalGraphEngine"),
    "HYPOTHESIS_GENERATOR":     ("Core_Engines.Hypothesis_Generator",     "HypothesisGeneratorEngine"),
	"Reasoning_Planner":         ("Core_Engines.Reasoning_Planner",        "ReasoningPlanner"),
    "Meta_Learning":             ("Core_Engines.Meta_Learning",    "MetaLearningEngine"),
    "Self_Reflective":          ("Core_Engines.Self_Reflective",   "SelfReflectiveEngine"),
    # Curiosity detector built into Self_Reflective module (lightweight)
    "Curiosity_Engine":        ("Core_Engines.Self_Reflective",   "create_curiosity_engine"),
    "AdvancedMetaReasoner":     ("Core_Engines.AdvancedMetaReasoner",    "AdvancedMetaReasonerEngine"),
	"Meta_Ensembler":            ("Core_Engines.Meta_Ensembler",           "MetaEnsembler"),
	"AdvancedMetaReasoner":      ("Core_Engines.AdvancedMetaReasoner",     "AdvancedMetaReasoner"),

	# معرفة/تحقق
	"General_Knowledge":         ("Core_Engines.General_Knowledge",        "GeneralKnowledge"),
	"GK_graph":                  ("Core_Engines.GK_graph",                  "GKGraph"),
    "GK_reasoner":               ("Core_Engines.GK_reasoner_engine",     "GKReasoner"),
	"GK_retriever":              ("Core_Engines.GK_retriever",              "GKRetriever"),
	"GK_verifier":               ("Core_Engines.GK_verifier",               "GKVerifier"),
	"Units_Validator":           ("Core_Engines.Units_Validator",           "UnitsValidator"),
	"Consistency_Checker":       ("Core_Engines.Consistency_Checker",       "ConsistencyChecker"),
	"Law_Matcher":               ("Core_Engines.Law_Matcher",               "LawMatcher"),
	"Law_Parser":                ("Core_Engines.Law_Parser",                "LawParser"),

	# عددي/أدوات
	"Robust_Regression":         ("Core_Engines.Robust_Regression",         "RobustRegression"),
	"tensor_utils":              ("Core_Engines.tensor_utils",              None),

	# واجهات LLM (تُسجَّل إن توفرت تبعياتها)
	"Hosted_LLM":                ("Core_Engines.Hosted_LLM",                "HostedLLM"),
	"Ollama_KnowledgeEngine":    ("Core_Engines.Ollama_KnowledgeEngine",    "OllamaKnowledgeEngine"),
	"OpenAI_KnowledgeEngine":    ("Core_Engines.OpenAI_KnowledgeEngine",    "OpenAIKnowledgeEngine"),

    # New cognitive / ensemble engines
    "Hybrid_Reasoner":          ("Core_Engines.hybrid_reasoner2",          "HybridReasoner"),
    "Analogy_Mapping_Engine":   ("Core_Engines.analogy_mapping",          "AnalogyMappingEngine"),
    "Moral_Reasoner":           ("Core_Engines.moral_reasoner",          "MoralReasoner"),
    "Prompt_Composer_V2":       ("Core_Engines.prompt_composer_v2",      "PromptComposerV2"),
    "Self_Critique_and_Revise": ("Core_Engines.self_critique",           "SelfCritiqueAndRevise"),
    "Counterfactual_Explorer":  ("Core_Engines.counterfactual_explorer", "CounterfactualExplorer"),
    "Math_Prover_Lite":         ("Core_Engines.math_prover_lite",        "MathProverLite"),
    "Plan-and-Execute_MicroPlanner": ("Core_Engines.plan_microplanner",   "PlanAndExecuteMicroPlanner"),
    "Humor_Irony_Stylist":      ("Core_Engines.humor_stylist",           "HumorIronyStylist"),
    "Rubric_Enforcer":          ("Core_Engines.rubric_enforcer_engine",  "RubricEnforcer"),
    "Quantum_Simulator_Wrapper": ("Core_Engines.quantum_simulator_wrapper", "QuantumSimulatorWrapper"),

    # Core conscious service (lightweight C-Layer package)
    "Core_Consciousness":      ("Core_Consciousness", None),
    # C-Layer state logger factory (optional)
    "C_Layer_StateLogger":    ("Core.C_Layer", "create_engine"),

	# اختيارية ثقيلة
	"Quantum_Neural_Core":       ("Core_Engines.Quantum_Neural_Core",       "QuantumNeuralCore"),
	"Advanced_Exponential_Algebra": ("Core_Engines.Advanced_Exponential_Algebra", "AdvancedExponentialAlgebra"),
}


logger = logging.getLogger("AGL.Core_Engines")
if not logger.handlers:
    # إعداد خفيف إذا لم يتم تهيئة اللوجر عالميًا
    handler = logging.StreamHandler()
    fmt = logging.Formatter("[%(levelname)s] %(name)s: %(message)s")
    handler.setFormatter(fmt)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)  # غيّرها إلى DEBUG أثناء التطوير


def _is_already_registered_error(e: Exception) -> bool:
    """Heuristic to detect when a registry rejected registration due to duplication.

    We don't want to spam logs with repetitive "already registered" messages when
    bootstrap is invoked multiple times in the same process.
    """
    try:
        txt = str(e).lower()
    except Exception:
        return False
    # common phrases returned by different registry implementations
    return any(k in txt for k in ("already registered", "already exists", "service .* already", "duplicate", "already added"))


def _try_registry_register(registry: Any, name: str, engine_obj: Any) -> bool:
    """يساند أشكال registry المختلفة: كائن بواجهات متعددة أو dict مباشرة."""
    # 1) dict-like
    if isinstance(registry, dict):
        registry[name] = engine_obj
        return True
    # 2) try common register signatures in a forgiving order
    # a) register(name=..., engine=...)
    try:
        registry.register(name=name, engine=engine_obj)
        logger.debug("registry.register(name=..., engine=...) succeeded")
        return True
    except TypeError:
        # signature didn't accept these keyword names; try other forms
        pass
    except Exception as e:
        # suppress noisy duplicate-registration messages
        if _is_already_registered_error(e):
            logger.debug("registry.register(name=..., engine=...) already registered (suppressed)")
            return False
        logger.debug(f"registry.register(name=..., engine=...) فشل: {e}")

    # b) register(key, service) positional (e.g., register(key, service))
    try:
        registry.register(name, engine_obj)
        logger.debug("registry.register(name, engine) positional succeeded")
        return True
    except TypeError:
        pass
    except Exception as e:
        if _is_already_registered_error(e):
            logger.debug("registry.register(name, engine) positional already registered (suppressed)")
            return False
        logger.debug(f"registry.register(name, engine) positional فشل: {e}")

    # c) register(key=..., service=...)
    try:
        registry.register(key=name, service=engine_obj)
        logger.debug("registry.register(key=..., service=...) succeeded")
        return True
    except TypeError:
        pass
    except Exception as e:
        if _is_already_registered_error(e):
            logger.debug("registry.register(key=..., service=...) already registered (suppressed)")
            return False
        logger.debug(f"registry.register(key=..., service=...) فشل: {e}")

    # d) register(engine_obj) simple form
    try:
        registry.register(engine_obj)
        logger.debug("registry.register(engine_obj) succeeded")
        return True
    except Exception as e:
        if _is_already_registered_error(e):
            logger.debug("registry.register(engine_obj) already registered (suppressed)")
            return False
        logger.debug(f"registry.register(engine_obj) فشل: {e}")

    # e) try add_engine/add variants
    try:
        if hasattr(registry, 'add_engine'):
            registry.add_engine(name, engine_obj)
            logger.debug("registry.add_engine(name, engine) succeeded")
            return True
    except Exception as e:
        if _is_already_registered_error(e):
            logger.debug("registry.add_engine already registered (suppressed)")
            return False
        logger.debug(f"registry.add_engine فشل: {e}")

    try:
        if hasattr(registry, 'add'):
            registry.add(name, engine_obj)
            logger.debug("registry.add(name, engine) succeeded")
            return True
    except Exception as e:
        if _is_already_registered_error(e):
            logger.debug("registry.add already registered (suppressed)")
            return False
        logger.debug(f"registry.add فشل: {e}")

    return False


def bootstrap_register_all_engines(
    registry: Any,
    allow_optional: bool = True,
    config: Dict[str, Any] | None = None,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    يحاول استيراد وتهيئة وتسجيل كل المحركات المعرفة في ENGINE_SPECS.
    - registry: قد يكون dict أو كائن Registry.
    - config: إن وُجد، يُمرَّر إلى create_engine(config) إن كانت متاحة.
    - allow_optional: إن False، أي فشل استيراد/تهيئة يرفع استثناء.
    - verbose: إن True، يزيد مستوى التفصيل في الـ logging.
    يعيد dict بالمحركات المسجلة فعلًا؛ كما يكتب تحذيرات للأسماء المتخطّاة.
    """
    if verbose:
        logger.setLevel(logging.DEBUG)

    registered: Dict[str, Any] = {}
    skipped: Dict[str, str] = {}  # name -> reason

    for name, spec in ENGINE_SPECS.items():
        # Quick guard: if OpenAI engine is listed but no API key and no mock is set,
        # skip it to avoid noisy runtime errors when tests/CI don't provide a key.
        try:
            import os
            if name == "OpenAI_KnowledgeEngine":
                # If the environment explicitly selects Ollama (HTTP or provider), prefer Ollama
                # over OpenAI so tests use the local model instead of requiring an OpenAI key.
                provider = os.getenv("AGL_LLM_PROVIDER") or ""
                baseurl = os.getenv("AGL_LLM_BASEURL") or ""
                if provider.lower().startswith("ollama") or baseurl:
                    skipped[name] = "preferred provider is Ollama (AGL_LLM_PROVIDER/AGL_LLM_BASEURL)"
                    logger.info(f"تخطي {name}: استخدام Ollama عبر AGL_LLM_PROVIDER/AGL_LLM_BASEURL")
                    continue
                # allow an explicit opt-out via env var
                if os.getenv("AGL_SKIP_OPENAI") in ("1", "true", "True"):
                    skipped[name] = "skipped by AGL_SKIP_OPENAI"
                    logger.warning(f"تخطي {name}: تعطيل عبر AGL_SKIP_OPENAI")
                    continue
                if not os.getenv("OPENAI_API_KEY") and not os.getenv("AGL_OPENAI_KB_MOCK"):
                    skipped[name] = "no OPENAI_API_KEY and not mocked"
                    logger.warning(f"تخطي {name}: لا يوجد OPENAI_API_KEY ولا يتم استخدام mock.")
                    continue
        except Exception:
            # non-fatal guard; continue normally if env cannot be read
            pass
        modpath, clsname = spec
        try:
            mod = import_module(modpath)
            # تفضيل create_engine
            eng = None
            if hasattr(mod, "create_engine") and callable(getattr(mod, "create_engine")):
                try:
                    if config is not None:
                        eng = mod.create_engine(config)
                    else:
                        eng = mod.create_engine()
                except TypeError:
                    # بعض المصانع قد لا تقبل config
                    eng = mod.create_engine()
            elif clsname:
                cls = getattr(mod, clsname, None)
                if cls is None:
                    raise AttributeError(f"لم أجد الصنف '{clsname}' داخل {modpath}")
                # محاولة تمرير config إلى الباني إن كان يقبل
                try:
                    eng = cls(config=config)  # قد يفشل إن لم يقبل وسيتم fallback
                except TypeError:
                    eng = cls()
            else:
                # لا مصنع ولا صنف: غالبًا وحدة أدوات مثل tensor_utils
                skipped[name] = "no factory/class (utility module?)"
                logger.debug(f"تخطي {name}: وحدة أدوات بلا كائن محرك.")
                continue

            # فحص واجهة المحرك (duck-typing خفيف)
            # If the engine exposes `process` but not `process_task`, adapt it
            # so older registry callers (which expect process_task) can still
            # invoke the engine. This prevents skipping valid lightweight
            # engines that implement a different method name.
            if not hasattr(eng, "process_task"):
                # Accept engines that implement `process(prompt, **kw)` and
                # expose a compatible `process_task` wrapper.
                if hasattr(eng, "process") and callable(getattr(eng, "process")):
                    try:
                        def _make_pt(eng_ref):
                            def _ptask(self_or_payload, *a, **kw):
                                # support both call signatures: payload dict or text
                                try:
                                    if isinstance(self_or_payload, dict):
                                        text = self_or_payload.get('text') or self_or_payload.get('prompt') or ''
                                    else:
                                        text = str(self_or_payload)
                                except Exception:
                                    text = ''
                                try:
                                    return eng_ref.process(text, **kw)
                                except TypeError:
                                    # some process implementations accept only (prompt)
                                    return eng_ref.process(text)
                            return _ptask
                        # bind adapter as an instance method if possible
                        eng.process_task = _make_pt(eng)
                        logger.debug(f"Adapter bound: {name} (process -> process_task)")
                    except Exception as e:
                        skipped[name] = f"failed to adapt process->process_task: {e}"
                        logger.warning(f"تخطي {name}: فشل تكييف process -> process_task: {e}")
                        continue
                else:
                    # Attach a safe default process_task adapter using the shared template
                    try:
                        from .process_task_template import attach_default_process_task
                        attach_default_process_task(eng, name)
                        logger.debug(f"Attached default process_task to {name}")
                    except Exception:
                        skipped[name] = "missing process_task"
                        logger.warning(f"تخطي {name}: لا يوفّر process_task.")
                        continue
            if not hasattr(eng, "name"):
                # إن لم يوفّر name، نعطيه اسمًا افتراضيًا
                try:
                    setattr(eng, "name", name)
                except Exception:
                    skipped[name] = "missing name and cannot set"
                    logger.warning(f"تخطي {name}: لا يوفّر name ولا يمكن تعيينه.")
                    continue
            # Optionally wrap process_task with engine monitor if available.
            try:
                from infra.engine_monitor import monitor_engine  # type: ignore
                fn = getattr(eng.__class__, "process_task", None)
                if callable(fn):
                    wrapped = monitor_engine(fn)
                    # bind wrapped to the instance so it behaves like a method
                    eng.process_task = wrapped.__get__(eng, eng.__class__) # type: ignore
            except Exception:
                # ignore failures to wrap monitoring; monitoring is optional
                pass

            if _try_registry_register(registry, name, eng):
                registered[name] = eng
                logger.debug(f"تم تسجيل المحرك: {name}")
            else:
                skipped[name] = "registry rejected"
                logger.warning(f"فشل تسجيل {name}: registry رفض الكائن.")

        except Exception as e:
            # أثناء التطوير مفيد جدًا أن نرى سبب التجاوز بسرعة
            try:
                logging.getLogger(__name__).warning("Skip engine %s due to: %r", name, e)
            except Exception:
                pass
            msg = f"فشل تهيئة/استيراد {name} من {modpath}: {e}"
            if allow_optional:
                skipped[name] = str(e)
                logger.warning(msg)
                continue
            else:
                logger.error(msg)
                raise

    # تقرير ختامي موجز
    if skipped:
        logger.info(f"محركات مسجَّلة: {list(registered.keys())}")
        logger.info(f"محركات متخطّاة ({len(skipped)}): "
                    + ", ".join([f"{k} ({v})" for k, v in skipped.items()]))

    # Optional: write a machine-readable report (useful in CI)
    try:
        import json, os
        os.makedirs("artifacts", exist_ok=True)
        with open("artifacts/bootstrap_report.json", "w", encoding="utf-8") as f:
            json.dump(
                {
                    "registered": list(registered.keys()),
                    "skipped": {k: str(v) for k, v in skipped.items()},
                },
                f,
                ensure_ascii=False,
                indent=2,
            )
    except Exception as _e:
        logger.debug("Could not write bootstrap_report.json: %r", _e)

    return registered


__all__ = [
    "bootstrap_register_all_engines",
    "ENGINE_SPECS",
    "Orchestrator",
]


# Ensure a small set of high-level engine names are present in ENGINE_SPECS so
# tests that validate presence can construct them directly. Some CI runs or
# downstream modifications may replace ENGINE_SPECS earlier; this final pass
# guarantees these keys exist with reasonable defaults.
_ENSURE_SPECS = {
    "NLP_Advanced": ("Core_Engines.NLP_Advanced", "NLPAdvanced"),
    "General_Knowledge": ("Core_Engines.General_Knowledge", "GeneralKnowledge"),
    "Creative_Innovation": ("Core_Engines.Creative_Innovation", "CreativeInnovation"),
    "Strategic_Thinking": ("Core_Engines.Strategic_Thinking", "StrategicThinking"),
    "Visual_Spatial": ("Core_Engines.Visual_Spatial", "VisualSpatial"),
    "Social_Interaction": ("Core_Engines.Social_Interaction", "SocialInteraction"),
    "Meta_Learning": ("Core_Engines.Meta_Learning", "MetaLearningEngine"),
    "AdvancedMetaReasoner": ("Core_Engines.AdvancedMetaReasoner", "AdvancedMetaReasoner"),
}

for k, v in _ENSURE_SPECS.items():
    if k not in ENGINE_SPECS:
        ENGINE_SPECS[k] = v


# Export a module-level alias `__init__` so that callers doing
# `from Core_Engines import __init__ as CE` receive the module object with
# attributes like ENGINE_SPECS. Some tests import that name directly.
try:
    import sys
    sys.modules[__name__].__init__ = sys.modules[__name__] # type: ignore
except Exception:
    # non-fatal if the environment prevents this assignment
    pass
