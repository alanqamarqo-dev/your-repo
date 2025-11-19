import pytest
from Core_Engines.Protocol_Designer import ProtocolDesigner


def test_process_task_spec():
    pd = ProtocolDesigner()
    out = pd.process_task("design secure protocol")
    assert out["ok"] is True
    assert out["result"]["verified"] is True


def test_verify_handshake_sequence_ok():
    pd = ProtocolDesigner()
    seq = ["client_hello", "server_hello", "key_exchange", "finished"]
    res = pd.verify_handshake_sequence(seq)
    assert res["accepted"] is True


def test_verify_handshake_sequence_mismatch():
    pd = ProtocolDesigner()
    seq = ["client_hello", "bad_step"]
    res = pd.verify_handshake_sequence(seq)
    assert res["accepted"] is False
import unittest
from Core_Engines.Protocol_Designer import ProtocolDesigner

class TestProtocolDesigner(unittest.TestCase):
    def test_handshake_rejection(self):
        pd = ProtocolDesigner()
        # invalid sequence (wrong second message)
        seq = ["client_hello", "bad_server_hello", "key_exchange", "finished"]
        out = pd.verify_handshake_sequence(seq)
        self.assertFalse(out.get('accepted', False))
        self.assertTrue(out.get('reason', '').startswith('mismatch'))

    def test_handshake_accept(self):
        pd = ProtocolDesigner()
        seq = ["client_hello", "server_hello", "key_exchange", "finished"]
        out = pd.verify_handshake_sequence(seq)
        self.assertTrue(out.get('accepted', False))
        self.assertEqual(out.get('reason'), 'ok')

if __name__ == '__main__':
    unittest.main()
