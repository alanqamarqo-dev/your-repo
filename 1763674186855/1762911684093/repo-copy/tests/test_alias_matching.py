import unittest
from Knowledge_Base.Domain_Expertise import apply_aliases_to_tokens


class TestAliases(unittest.TestCase):
    def test_voltage_u_equals_v(self):
        self.assertEqual(apply_aliases_to_tokens(["U","=","I","*","R"]),
                         ["V","=","I","*","R"])

    def test_no_change_if_not_in_aliases(self):
        self.assertEqual(apply_aliases_to_tokens(["F","=","m","*","a"]),
                         ["force","=","m","*","acc"])


if __name__ == "__main__":
    unittest.main()
