#!/usr/bin/env python3
"""Run a small Demo Knowledge Network (DKN) using in-process bus + blackboard.

This script boots core engines via the registry (best-effort), wraps some
engines with EngineAdapter, and runs the MetaOrchestrator loop for a number
of cycles then emits the final result.
"""
from __future__ import annotations
import sys
import os
import time

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from Integration_Layer.inproc_bus import PriorityBus
from Integration_Layer.knowledge_graph import KnowledgeGraph
from Integration_Layer.meta_orchestrator import MetaOrchestrator
from Integration_Layer.engine_adapter import EngineAdapter
from Integration_Layer.dkn_types import Signal
from Integration_Layer.integration_registry import registry
import Core_Engines as CE


def boot():
    CE.bootstrap_register_all_engines(registry, allow_optional=True)
    g = KnowledgeGraph()
    bus = PriorityBus()

    # wrap some engines if present in registry; registry.get returns default None
    adapters = [
        EngineAdapter('Prompt_Composer_V2', registry.get('Prompt_Composer_V2'), subscriptions=['task:new'], capabilities=['compose']),
        EngineAdapter('Reasoning_Layer', registry.get('Reasoning_Layer'), subscriptions=['claim','subtask:reasoning','task:new'], capabilities=['answer']),
        EngineAdapter('Mathematical_Brain', registry.get('Mathematical_Brain'), subscriptions=['subtask:math','task:new'], capabilities=['compute']),
        EngineAdapter('Analogy_Mapping_Engine', registry.get('Analogy_Mapping_Engine'), subscriptions=['xfer','task:new'], capabilities=['map']),
        EngineAdapter('Hybrid_Reasoner', registry.get('Hybrid_Reasoner'), subscriptions=['claim','plan','metric'], capabilities=['merge']),
        EngineAdapter('Self_Critique_and_Revise', registry.get('Self_Critique_and_Revise'), subscriptions=['claim','io:pre-final'], capabilities=['review']),
    ]

    orch = MetaOrchestrator(g, bus, adapters)
    return g, bus, orch


def main():
    g, bus, orch = boot()

    # seed the task
    bus.publish(Signal(topic='task:new', score=0.9, source='IO', payload={'prompt': 'صمِّم ريًا لحديقة 10x20 م بميزانية 1000$ وعلّمنا كيف نربط الفكرة مع تنظيم تقاطع مرور.'}))

    # run a small event loop
    cycles = 200
    for i in range(cycles):
        orch.route_once()

    orch.consensus_and_emit() # type: ignore

    # collect final io:final
    out = None
    for _ in range(10):
        out = bus.pop(timeout=0.2)
        if out and getattr(out, 'topic', None) == 'io:final':
            print('FINAL:', out.payload)
            return 0
    print('No final output produced; DKN ran but did not emit io:final')
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
