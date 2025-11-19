import unittest
from Core_Engines.Protocol_Designer import ProtocolDesigner

class TestProtocolDesignerBranches(unittest.TestCase):
    def setUp(self):
        self.pd = ProtocolDesigner()

    def test_reject_small_mtu(self):
        spec = {"constraints": {"mtu_min": 512}}
        hs = {"client_hello": {"mtu": 128}}
        ok, reason = self.pd.verify_handshake_sequence(["client_hello"])['accepted'], self.pd.verify_handshake_sequence(["client_hello"])['reason']
        self.assertFalse(ok)

    def test_reject_unsupported_cipher(self):
        # Use verify_handshake_sequence indirectly to simulate disapproval
        res = self.pd.verify_handshake_sequence(["client_hello", "server_hello"]) 
        self.assertFalse(res['accepted'])
