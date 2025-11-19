import pytest

from Core_Engines.Protocol_Designer import ProtocolDesigner


def test_verify_handshake_sequence_types_and_results():
    pd = ProtocolDesigner()

    # invalid type
    res = pd.verify_handshake_sequence("not-a-list") # type: ignore
    assert res['accepted'] is False and res['reason'] == 'invalid_sequence_type'

    # exact match
    good = ["client_hello", "server_hello", "key_exchange", "finished"]
    res = pd.verify_handshake_sequence(good)
    assert res['accepted'] is True and res['reason'] == 'ok'

    # mismatch early
    bad = ["client_hello", "bad_token"]
    res = pd.verify_handshake_sequence(bad)
    assert res['accepted'] is False and res['reason'].startswith('mismatch_at_')

    # too long
    long = good + ["extra"]
    res = pd.verify_handshake_sequence(long)
    assert res['accepted'] is False and res['reason'] == 'too_long'

    # incomplete
    incomplete = ["client_hello", "server_hello"]
    res = pd.verify_handshake_sequence(incomplete)
    assert res['accepted'] is False and res['reason'] == 'incomplete'
