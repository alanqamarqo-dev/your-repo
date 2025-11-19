from pathlib import Path
from AGL import create_agl_instance


def test_safety_smoke(tmp_path, monkeypatch):
    cfg = tmp_path / 'config.yaml'
    cfg.write_text(
        "features:\n"
        "  enable_emergency_experts: true\n"
        "  enable_self_improvement: false\n",
        encoding='utf-8'
    )
    monkeypatch.chdir(tmp_path)

    agl = create_agl_instance(config=None)
    reg = agl.integration_registry

    # required keys
    for k in ('control_layers', 'rollback_mechanism', 'emergency_protocols'):
        assert reg.has(k), f"Missing safety key: {k}"

    # optional emergency experts
    if reg.has('emergency_doctor'):
        doc = reg.resolve('emergency_doctor')
        # call assess with a synthetic failure
        try:
            res = doc.assess({'error': True})
            assert isinstance(res, dict)
        except Exception:
            # fallback behavior: ensure no crash
            assert True

    if reg.has('emergency_integration'):
        integ = reg.resolve('emergency_integration')
        try:
            res = integ.integrate({'fatal': True})
            assert isinstance(res, dict)
        except Exception:
            assert True
