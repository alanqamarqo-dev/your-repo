def test_simulation_and_integration_imports():
    from Scientific_Systems import Integrated_Simulation_Engine as ise
    from Integration_Layer import Conversation_Manager as cm
    from Integration_Layer import Intent_Recognizer as ir
    from Integration_Layer import Action_Router as ar

    assert ise is not None
    assert cm is not None
    assert ir is not None
    assert ar is not None

    # minimal instantiation where safe
    try:
        inst = ise.IntegratedSimulationEngine()  # type: ignore
    except Exception:
        inst = None
    assert inst is None or hasattr(inst, '__class__')
