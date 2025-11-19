import unittest, os, json
from Integration_Layer.Task_Orchestrator import TaskOrchestrator


class TestTrainingPath(unittest.TestCase):
    def test_train_laws_hooke(self):
        orch = TaskOrchestrator()
        # Use the explicit process route (keeps compatibility with older API names)
        res = orch.process("train-laws", data="data/hooke_sample.csv")
        self.assertTrue(res.get("ok"), msg=f"unexpected result: {res}") # type: ignore
        self.assertIn("params", res) # type: ignore
        self.assertIn("mse", res) # type: ignore
        self.assertLess(res["mse"], 1e-9) # type: ignore
        artifact = res.get("artifact") # type: ignore
        self.assertTrue(artifact and os.path.exists(artifact))
        with open(artifact, "r", encoding="utf-8") as f: # type: ignore
            saved = json.load(f)
        self.assertIn("params", saved)


if __name__ == "__main__":
    unittest.main()
