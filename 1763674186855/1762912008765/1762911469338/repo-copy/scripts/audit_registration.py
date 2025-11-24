"""Audit the repository to produce a module reference report.

This script inspects `AGL.py` for bootstrap registrations (core engines,
integration factories/instances, learning and safety registrations) and
compares them to the files present under the main packages. The output is
written to `reports/module_reference_report.json`.

Run: python -m scripts.audit_registration
"""
import ast
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports' / 'module_reference_report.json'
OUT.parent.mkdir(exist_ok=True)


def read_agl_registrations(agl_path: Path):
    text = agl_path.read_text(encoding='utf-8')
    regs = {
        'core_engines': [],
        'integration': [],
        'integration_factories': [],
        'learning': [],
        'learning_factories': [],
        'safety': []
    }

    # core engines: look for self.core_engines['name'] =
    for m in re.finditer(r"self\.core_engines\['([a-z0-9_]+)'\]", text, re.I):
        regs['core_engines'].append(m.group(1))

    # integration registry.register('key'
    for m in re.finditer(r"integration_registry\.register\('\s*([a-z0-9_]+)\s*'", text, re.I):
        regs['integration'].append(m.group(1))

    for m in re.finditer(r"integration_registry\.register_factory\('\s*([a-z0-9_]+)\s*'", text, re.I):
        regs['integration_factories'].append(m.group(1))

    # learning registers
    for m in re.finditer(r"integration_registry\.register\('\s*([a-z0-9_]+)\s*'", text, re.I):
        if m.group(1) in ('feedback_analyzer', 'improvement_generator', 'knowledge_integrator'):
            regs['learning'].append(m.group(1))

    for m in re.finditer(r"register_factory\('\s*([a-z0-9_]+)\s*'", text, re.I):
        if m.group(1) in ('experience_memory', 'model_zoo', 'self_learning'):
            regs['learning_factories'].append(m.group(1))

    # safety
    for m in re.finditer(r"integration_registry\.register\('\s*([a-z0-9_]+)\s*'", text, re.I):
        if m.group(1) in ('control_layers', 'rollback_mechanism', 'emergency_protocols', 'emergency_doctor', 'emergency_integration'):
            regs['safety'].append(m.group(1))

    # normalize unique
    for k in regs:
        regs[k] = sorted(set(regs[k]))

    return regs


def read_package_all(package_dir: Path):
    initf = package_dir / '__init__.py'
    if not initf.exists():
        return []
    txt = initf.read_text(encoding='utf-8')
    m = re.search(r"__all__\s*=\s*(\[.*?\])", txt, re.S)
    if not m:
        return []
    try:
        return ast.literal_eval(m.group(1))
    except Exception:
        return []


def list_package_files(package_dir: Path):
    return sorted([p.name for p in package_dir.iterdir() if p.suffix == '.py' and p.name != '__init__.py'])


def build_report():
    agl = read_agl_registrations(ROOT / 'AGL.py')

    packages = {}
    pkgs = ['Core_Engines', 'Integration_Layer', 'Learning_System', 'Safety_Systems']
    for p in pkgs:
        d = ROOT / p
        files = list_package_files(d) if d.exists() else []
        exported = read_package_all(d)
        packages[p] = {
            'files': files,
            'exports': exported,
        }

    # heuristic covered lists using AGL registrations + __all__ exports
    covered = {
        'Core_Engines': [],
        'Integration_Layer': [],
        'Learning_System': [],
        'Safety_Systems': []
    }

    # mapping keys -> filenames (best-effort)
    core_map = {
        'mathematical_brain': 'Mathematical_Brain.py',
        'quantum_processor': 'Quantum_Processor.py',
        'code_generator': 'Code_Generator.py',
        'protocol_designer': 'Protocol_Designer.py',
        'visual_spatial': 'Visual_Spatial.py',
        'quantum_neural': 'Quantum_Neural_Core.py',
        'adv_exp_algebra': 'Advanced_Exponential_Algebra.py'
    }

    for k in agl['core_engines']:
        if k in core_map:
            covered['Core_Engines'].append(core_map[k])

    int_map = {
        'communication_bus': 'Communication_Bus.py',
        'task_orchestrator': 'Task_Orchestrator.py',
        'output_formatter': 'Output_Formatter.py',
        'domain_router': 'Domain_Router.py',
        'planner_agent': 'Planner_Agent.py',
        'retriever': 'retriever.py',
        'rag': 'rag.py',
        'intent_recognizer': 'Intent_Recognizer.py',
        'pipeline_orchestrator': 'Pipeline_Orchestrator.py',
        'conversation_manager': 'Conversation_Manager.py',
        'action_router': 'Action_Router.py',
        'hybrid_composer': 'Hybrid_Composer.py'
    }
    for k in agl['integration'] + agl['integration_factories']:
        if k in int_map:
            covered['Integration_Layer'].append(int_map[k])

    learn_map = {
        'feedback_analyzer': 'Feedback_Analyzer.py',
        'improvement_generator': 'Improvement_Generator.py',
        'knowledge_integrator': 'Knowledge_Integrator.py',
        'experience_memory': 'ExperienceMemory.py',
        'model_zoo': 'ModelZoo.py',
        'self_learning': 'Self_Learning.py',
        'temporal_memory': 'TemporalMemory.py'
    }
    for k in agl['learning'] + agl['learning_factories']:
        if k in learn_map:
            covered['Learning_System'].append(learn_map[k])

    safety_map = {
        'control_layers': 'Control_Layers.py',
        'rollback_mechanism': 'Rollback_Mechanism.py',
        'emergency_protocols': 'Emergency_Protocols.py',
        'emergency_doctor': 'EmergencyDoctor.py',
        'emergency_integration': 'EmergencyIntegration.py'
    }
    for k in agl['safety']:
        if k in safety_map:
            covered['Safety_Systems'].append(safety_map[k])

    # compute suspect = files - covered - exported
    report = {
        'reference_of_truth': {
            'AGL._initialize_core_engines': True,
            'AGL._initialize_integration_layer': True,
            'AGL._initialize_learning_system': True,
            'AGL._initialize_safety_systems': True,
            'packages___all__': {p: packages[p]['exports'] for p in packages}
        },
        'packages': {}
    }

    for p in packages:
        files = packages[p]['files']
        exp = set(packages[p]['exports'] or [])
        cov = set(tuple(covered.get(p, [])))
        suspect = sorted([f for f in files if f not in cov and f not in exp])
        report['packages'][p] = {
            'covered': sorted(list(cov)),
            'suspect': suspect,
            'notes': []
        }

    # explicit conflict heuristics
    conflicts = []
    # domain_router conflict
    if (ROOT / 'Core_Engines' / 'domain_router.py').exists() and (ROOT / 'Integration_Layer' / 'Domain_Router.py').exists():
        conflicts.append({
            'topic': 'Domain Router',
            'candidates': ['Core_Engines/domain_router.py', 'Integration_Layer/Domain_Router.py'],
            'action': 'Keep Integration_Layer/Domain_Router.py as canonical; make Core_Engines/domain_router.py a shim or remove.'
        })
    # experience_memory conflict
    if (ROOT / 'Core_Engines' / 'experience_memory.py').exists() and (ROOT / 'Learning_System' / 'ExperienceMemory.py').exists():
        conflicts.append({
            'topic': 'Experience Memory',
            'candidates': ['Core_Engines/experience_memory.py', 'Learning_System/ExperienceMemory.py'],
            'action': 'Keep Learning_System/ExperienceMemory.py as canonical; migrate or shim Core_Engines version.'
        })

    report['conflicts_or_duplicates'] = conflicts

    report['next_steps'] = [
        'Add explicit __all__ exports for Core_Engines to define the supported public engines.',
        'Register selected engines in AGL._initialize_* or create IntegrationRegistry/ServiceLocator for managed access.',
        'Resolve duplicate modules by shimming/migrating and update imports to canonical locations.',
        'Run this audit script again after changes; diff the JSON to confirm reductions in "suspect".'
    ]

    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Wrote', OUT)


if __name__ == '__main__':
    build_report()
