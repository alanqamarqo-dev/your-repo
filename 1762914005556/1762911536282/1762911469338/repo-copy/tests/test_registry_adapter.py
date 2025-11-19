import importlib, os

import Integration_Layer.integration_registry as ir


def test_process_task_adapter_present():
    # force scaffold mode if your bootstrap uses it
    os.environ["AGL_TEST_SCAFFOLD_FORCE"] = "1"
    # re-import AGL to trigger bootstrap if needed
    if "AGL" in importlib.sys.modules:
        del importlib.sys.modules["AGL"]
    import AGL  # this should run the bootstrap/registration

    # ensure engines are registered by name
    names = ir.registry.list_names()
    for key in ("Creative_Innovation", "Protocol_Designer"):
        eng = ir.registry.get(key)
        assert eng is not None, f"{key} not registered"
        assert hasattr(eng, "process_task") and callable(eng.process_task), f"{key} lacks process_task adapter"
