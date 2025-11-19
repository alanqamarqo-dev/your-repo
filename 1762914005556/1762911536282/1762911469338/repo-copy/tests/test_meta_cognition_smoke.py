from AGL import create_agl_instance


def test_meta_cognition_smoke(tmp_path, monkeypatch):
    cfg = tmp_path / 'config.yaml'
    cfg.write_text(
        "features:\n"
        "  enable_meta_cognition: true\n",
        encoding='utf-8'
    )
    monkeypatch.chdir(tmp_path)

    agl = create_agl_instance(config=None)
    reg = agl.integration_registry

    assert reg.has('meta_cognition'), 'meta_cognition should be registered'
    meta = reg.resolve('meta_cognition')
    assert hasattr(meta, 'evaluate')
    out = meta.evaluate({'plan': 'do something'})
    assert isinstance(out, dict)
    assert 'score' in out and 'notes' in out
