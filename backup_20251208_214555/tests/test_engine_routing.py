import os
from Self_Improvement.Knowledge_Graph import (
    ENGINE_CAPABILITIES,
    route_engines,
    HealthMonitor,
)


def test_route_engines_language_prefers_language_caps():
    # empty HealthMonitor snapshot
    hm = HealthMonitor(path=None)

    all_engines = list(ENGINE_CAPABILITIES.keys())
    routed = route_engines(
        all_available=all_engines,
        domains_needed=("language", "analysis"),
        health=hm,
        top_k=5,
    )

    lang_like = {"analysis", "reason", "summarize", "translate", "hosted_storyqa"}
    assert any(name in routed for name in lang_like), f"routed={routed}"


def test_route_engines_math_prefers_math_caps():
    hm = HealthMonitor(path=None)

    all_engines = list(ENGINE_CAPABILITIES.keys())
    routed = route_engines(
        all_available=all_engines,
        domains_needed=("math", "analysis"),
        health=hm,
        top_k=5,
    )

    math_like = {"math", "proof"}
    assert any(name in routed for name in math_like), f"routed={routed}"
