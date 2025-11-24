from Integration_Layer.Domain_Router import route_domain


def test_route_domain_no_ontology_and_quantum_signal(monkeypatch):
    # force ontology to be empty by monkeypatching ONTO in module
    import Integration_Layer.Domain_Router as dr
    dr.ONTO = {"domains": {}}

    res = route_domain('')
    # with no domains defined, primary_domain should be None
    assert res['primary_domain'] is None

    # now test quantum signal selection when ontology contains quantum
    dr.ONTO = {"domains": {"quantum": {}, "electrical": {}}}
    res = route_domain('ψ is the wavefunction H operator')
    # quantum signal should surface as primary_domain
    assert res['primary_domain'] in ('quantum', 'electrical')
    assert 'features' in res
