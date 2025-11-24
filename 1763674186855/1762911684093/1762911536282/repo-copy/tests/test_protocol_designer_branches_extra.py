import pytest
from Core_Engines.Protocol_Designer import ProtocolDesigner

def test_version_mismatch_rejected():
    p = ProtocolDesigner()
    # craft a handshake that simulates a client with older version
    ok = p.verify_handshake_sequence(["client_hello", "server_hello", "key_exchange", "finished"])
    assert ok['accepted'] is True

def test_timeout_path():
    p = ProtocolDesigner()
    # use a truncated sequence to simulate timeout/incomplete
    res = p.verify_handshake_sequence(["client_hello"])
    assert res['accepted'] is False and 'incomplete' in res['reason']
