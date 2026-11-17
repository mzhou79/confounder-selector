import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from dag_tools import DAG, analyze, to_dagitty  # noqa: E402


class DagTests(unittest.TestCase):
    def test_simple_confounder(self):
        g = DAG([["C", "X"], ["C", "Y"], ["X", "Y"]])
        self.assertEqual(g.minimal_adjustment_sets("X", "Y"), [["C"]])

    def test_mediator_excluded(self):
        g = DAG([["X", "M"], ["M", "Y"], ["X", "Y"]])
        self.assertEqual(g.minimal_adjustment_sets("X", "Y"), [[]])
        self.assertFalse(g.satisfies_backdoor("X", "Y", {"M"}))

    def test_m_bias(self):
        # X <- U1 -> C <- U2 -> Y : adjusting for collider C opens the path
        g = DAG([["U1", "X"], ["U1", "C"], ["U2", "C"], ["U2", "Y"], ["X", "Y"]], latent=["U1", "U2"])
        self.assertTrue(g.satisfies_backdoor("X", "Y", set()))
        self.assertFalse(g.satisfies_backdoor("X", "Y", {"C"}))
        self.assertEqual(g.minimal_adjustment_sets("X", "Y"), [[]])

    def test_two_alternative_sets(self):
        # X <- A <- L -> Y : either {A} or {L} suffices
        g = DAG([["L", "A"], ["A", "X"], ["L", "Y"], ["X", "Y"]])
        self.assertEqual(g.minimal_adjustment_sets("X", "Y"), [["A"], ["L"]])

    def test_unblockable_latent(self):
        g = DAG([["U", "X"], ["U", "Y"], ["X", "Y"]], latent=["U"])
        self.assertEqual(g.minimal_adjustment_sets("X", "Y"), [])

    def test_cycle_rejected(self):
        with self.assertRaises(ValueError):
            DAG([["A", "B"], ["B", "A"]])

    def test_fixture_analysis(self):
        ledger = json.loads((ROOT / "tests" / "fixtures" / "synthetic_ledger.json").read_text())
        res = analyze(ledger)
        self.assertEqual(res["minimal_sets"], [["age"]])
        self.assertTrue(res["proposed_sufficient"])
        self.assertIn("exercise [exposure]", res["dagitty"])

    def test_dagitty_identifiers(self):
        code = to_dagitty({"exposure": "exercise 30min", "outcome": "SBP", "edges": [["age (yrs)", "exercise 30min"]]})
        self.assertIn("age__yrs_ -> exercise_30min", code)


if __name__ == "__main__":
    unittest.main()
