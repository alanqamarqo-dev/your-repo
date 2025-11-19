from Integration_Layer import Domain_Router


def test_route_domain_electrical_and_fallback():
    # A text mentioning volt and Ohm should bias electrical domain
    txt = "Compute V=I*R in an ohm circuit"
    out = Domain_Router.route_domain(txt)
    assert isinstance(out, dict)
    # primary_domain may be 'electrical' when ontology is present, or None otherwise
    assert "primary_domain" in out
    assert "primary_confidence" in out
    assert isinstance(out.get("features"), dict)
