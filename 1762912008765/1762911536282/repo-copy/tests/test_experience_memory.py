import os
import tempfile
import json
import unittest

from Learning_System.ExperienceMemory import ExperienceMemory

class TestExperienceMemory(unittest.TestCase):
    def test_append_and_persist(self):
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "experiences.jsonl")
            mem = ExperienceMemory(storage_path=path)

            item1 = {"t": 1, "task": "A", "result": "ok"}
            item2 = {"t": 2, "task": "B", "result": "fail"}
            mem.append(item1)
            mem.append(item2)

            # live buffer
            self.assertEqual(len(mem.buffer), 2)
            self.assertEqual(mem.buffer[0]["t"], 1)

            # file content
            self.assertTrue(os.path.exists(path))
            with open(path, "r", encoding="utf-8") as f:
                lines = [json.loads(l) for l in f.read().splitlines() if l.strip()]
            self.assertEqual(len(lines), 2)
            self.assertEqual(lines[1]["task"], "B")

            # reload
            mem2 = ExperienceMemory(storage_path=path)
            mem2.load()
            self.assertEqual(len(mem2.buffer), 2)
            self.assertEqual(mem2.buffer[0]["result"], "ok")
