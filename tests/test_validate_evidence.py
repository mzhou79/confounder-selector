import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import validate_evidence as ve  # noqa: E402

FIXTURE = json.loads((ROOT / "tests" / "fixtures" / "synthetic_ledger.json").read_text())


def errs(data):
    return ve.validate(data)[0]


def warns(data):
    return ve.validate(data)[1]


class StructureTests(unittest.TestCase):
    def setUp(self):
        self.d = copy.deepcopy(FIXTURE)

    def test_fixture_passes(self):
        self.assertEqual(errs(self.d), [])

    def test_missing_required_field(self):
        del self.d["candidates"][0]["evidence"][0]["location"]
        self.assertTrue(any("location" in e for e in errs(self.d)))

    def test_invalid_role(self):
        self.d["candidates"][0]["role"] = "proven confounder"
        self.assertTrue(errs(self.d))

    def test_invalid_doi(self):
        self.d["papers"][1]["doi"] = "made-up"
        self.assertTrue(any("doi" in e.lower() for e in errs(self.d)))

    def test_mini_validator_agrees_with_jsonschema(self):
        schema = json.loads(ve.SCHEMA_PATH.read_text())
        self.assertEqual(ve._mini_validate(self.d, schema), [])
        self.d["candidates"][0]["recommendation"] = "maybe"
        self.assertTrue(ve._mini_validate(self.d, schema))


class ProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.d = copy.deepcopy(FIXTURE)

    def test_confounder_without_papers_fails(self):
        # the exact case the v1 validator let through
        self.d["candidates"][0]["evidence"] = []
        self.assertTrue(any("no evidence from an uploaded or verified paper" in e for e in errs(self.d)))

    def test_confounder_with_only_unverified_paper_fails(self):
        self.d["papers"][1]["verification_status"] = "unverified"
        self.d["candidates"][0]["evidence"] = [self.d["candidates"][0]["evidence"][1]]
        self.assertTrue(any("no evidence from an uploaded or verified" in e for e in errs(self.d)))

    def test_mismatch_paper_cannot_be_cited(self):
        self.d["papers"][1]["verification_status"] = "mismatch"
        self.assertTrue(any("failed verification" in e for e in errs(self.d)))

    def test_researcher_proposed_is_warning_not_error(self):
        self.d["candidates"].append({"variable": "income", "measurement_timing": "pre_exposure", "role": "candidate confounder",
                                     "recommendation": "adjust", "rationale": "PI request", "researcher_proposed": True, "evidence": []})
        self.d["dag"]["edges"] += [["income", "exercise"], ["income", "sbp"]]
        self.assertEqual(errs(self.d), [])
        self.assertTrue(any("researcher-proposed" in w for w in warns(self.d)))

    def test_required_paper_must_be_cited(self):
        self.d["candidates"][0]["evidence"] = [self.d["candidates"][0]["evidence"][1]]
        self.d["dag"]["edge_sources"] = {}
        self.assertTrue(any("required paper 'U1'" in e for e in errs(self.d)))
        self.d["papers"][0]["required_note"] = "Reports crude estimates only"
        self.assertEqual(errs(self.d), [])

    def test_post_exposure_adjustment_for_total_effect_fails(self):
        self.d["candidates"][1]["recommendation"] = "adjust"
        self.assertTrue(any("post-exposure" in e for e in errs(self.d)))

    def test_verified_retrieved_needs_identifier(self):
        del self.d["papers"][1]["pmid"]
        self.assertTrue(any("no PMID or DOI" in e for e in errs(self.d)))

    def test_retrieved_needs_search_log(self):
        self.d["search_log"] = []
        self.assertTrue(any("search_log is empty" in e for e in errs(self.d)))

    def test_adjustment_practice_only_warns(self):
        self.d["candidates"][0]["evidence"] = [self.d["candidates"][0]["evidence"][0]]
        self.assertTrue(any("prior adjustment practice" in w for w in warns(self.d)))

    def test_duplicate_variable(self):
        self.d["candidates"].append(copy.deepcopy(self.d["candidates"][0]))
        self.assertTrue(any("more than once" in e for e in errs(self.d)))

    def test_long_quote_warns(self):
        self.d["candidates"][0]["evidence"][0]["quote"] = "word " * 60
        self.assertTrue(any("quote exceeds" in w for w in warns(self.d)))

    def test_strict_cli(self):
        import tempfile
        self.d["candidates"][0]["evidence"][0]["quote"] = "word " * 60
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(self.d, f)
        self.assertEqual(ve.main([f.name]), 0)
        self.assertEqual(ve.main([f.name, "--strict"]), 1)


if __name__ == "__main__":
    unittest.main()
