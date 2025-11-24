import unittest
from datetime import datetime, timedelta, timezone
from Learning_System.TemporalMemory import TemporalMemory

class TestTemporalMemory(unittest.TestCase):
    """نختبر الإضافة مع الطابع الزمني والاستعلام بنطاق زمني."""

    def test_append_and_range_query(self):
        tm = TemporalMemory()
        t0 = datetime(2025, 1, 1, tzinfo=timezone.utc)
        t1 = t0 + timedelta(seconds=10)
        t2 = t0 + timedelta(seconds=20)

        tm.append({"event": "a"}, ts=t0)
        tm.append({"event": "b"}, ts=t1)
        tm.append({"event": "c"}, ts=t2)

        got = tm.range_query(t0 + timedelta(seconds=5), t2 - timedelta(seconds=5))
        self.assertEqual([g["event"] for g in got], ["b"])

    def test_latest(self):
        tm = TemporalMemory()
        base = datetime(2025, 1, 1, tzinfo=timezone.utc)
        for i in range(5):
            tm.append({"i": i}, ts=base + timedelta(seconds=i))
        latest_two = tm.latest(2)
        self.assertEqual([x["i"] for x in latest_two], [4, 3])

if __name__ == "__main__":
    unittest.main()
