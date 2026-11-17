import sys
import unittest
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import verify_citations as vc  # noqa: E402

# Real record shape (PMID 30840181, VanderWeele 2019), trimmed to the fields the checker reads.
ESUMMARY = {"result": {"uids": ["30840181"], "30840181": {
    "uid": "30840181", "title": "Principles of confounder selection.", "pubdate": "2019 Mar",
    "source": "Eur J Epidemiol", "fulljournalname": "European journal of epidemiology",
    "authors": [{"name": "VanderWeele TJ"}],
    "articleids": [{"idtype": "pubmed", "value": "30840181"}, {"idtype": "doi", "value": "10.1007/s10654-019-00494-6"}]}}}
CROSSREF = {"message": {"DOI": "10.1007/s10654-019-00494-6", "title": ["Principles of confounder selection"],
                        "container-title": ["European Journal of Epidemiology"], "issued": {"date-parts": [[2019, 3, 6]]},
                        "author": [{"family": "VanderWeele", "given": "Tyler J."}]}}


def fake_fetch(url):
    if "esummary" in url:
        if "id=30840181" in url:
            return ESUMMARY
        return {"result": {"uids": ["99999999"], "99999999": {"uid": "99999999", "error": "cannot get document summary"}}}
    if "esearch" in url:
        return {"esearchresult": {"idlist": ["30840181"]}}
    if "crossref" in url:
        if "10.1007/s10654-019-00494-6" in url:
            return CROSSREF
        raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)
    raise AssertionError(url)


def offline_fetch(url):
    raise urllib.error.URLError("Tunnel connection failed: 403")


TITLE = "Principles of confounder selection"


class VerifierTests(unittest.TestCase):
    def setUp(self):
        self.v = vc.Verifier(fetch=fake_fetch, pause=0)

    def paper(self, **kw):
        base = {"id": "p", "title": TITLE, "source_type": "retrieved"}
        base.update(kw)
        return base

    def test_pmid_verified(self):
        r = self.v.check(self.paper(pmid="30840181"))
        self.assertEqual(r["status"], "verified")
        self.assertEqual(r["record"]["year"], 2019)

    def test_pmid_wrong_title_is_mismatch(self):
        r = self.v.check(self.paper(pmid="30840181", title="Exercise and blood pressure in older adults"))
        self.assertEqual(r["status"], "mismatch")

    def test_pmid_doi_conflict_is_mismatch(self):
        r = self.v.check(self.paper(pmid="30840181", doi="10.1000/other"))
        self.assertEqual(r["status"], "mismatch")

    def test_fabricated_pmid_not_found(self):
        self.assertEqual(self.v.check(self.paper(pmid="99999999"))["status"], "not_found")

    def test_doi_verified_via_crossref(self):
        r = self.v.check(self.paper(doi="10.1007/s10654-019-00494-6"))
        self.assertEqual((r["status"], r["via"]), ("verified", "crossref"))

    def test_fabricated_doi_not_found(self):
        self.assertEqual(self.v.check(self.paper(doi="10.9999/fake.123"))["status"], "not_found")

    def test_no_identifier_suggests_but_does_not_verify(self):
        r = self.v.check(self.paper())
        self.assertEqual(r["status"], "unverified")
        self.assertTrue(any("30840181" in n for n in r["notes"]))

    def test_uploaded_without_identifier_not_applicable(self):
        self.assertEqual(self.v.check(self.paper(source_type="uploaded"))["status"], "not_applicable")

    def test_network_failure_is_error_and_leaves_ledger_alone(self):
        v = vc.Verifier(fetch=offline_fetch, pause=0)
        ledger = {"papers": [self.paper(pmid="30840181", verification_status="unverified")]}
        res = [v.check(p) for p in ledger["papers"]]
        self.assertEqual(res[0]["status"], "error")
        vc.apply_results(ledger, res)
        self.assertEqual(ledger["papers"][0]["verification_status"], "unverified")

    def test_apply_results_fills_metadata(self):
        ledger = {"papers": [self.paper(pmid="30840181", verification_status="unverified")]}
        vc.apply_results(ledger, [self.v.check(ledger["papers"][0])], today="2026-11-16")
        p = ledger["papers"][0]
        self.assertEqual((p["verification_status"], p["verified_via"], p["doi"]), ("verified", "pubmed", "10.1007/s10654-019-00494-6"))

    def test_title_normalization(self):
        self.assertGreater(vc.title_similarity("Principles of <i>confounder</i> selection.", "principles of confounder selection"), 0.99)


if __name__ == "__main__":
    unittest.main()
