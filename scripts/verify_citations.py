#!/usr/bin/env python3
"""Check every paper in an evidence ledger against PubMed and Crossref.

For each paper:
  * PMID given  -> NCBI E-utilities esummary; compare title (and DOI if both given)
  * DOI given   -> Crossref /works/{doi}; compare title
  * neither     -> PubMed title search; report candidate PMIDs (never auto-filled)

A paper is `verified` only when a record exists AND its title matches the
ledger title (similarity >= --threshold, default 0.90). A record that exists
but does not match is `mismatch`; a lookup that returns nothing is `not_found`.
validate_evidence.py rejects candidates that cite mismatch/not_found papers.

Usage:
  verify_citations.py LEDGER.json                # report only
  verify_citations.py LEDGER.json --write OUT.json   # write updated ledger

Network: needs HTTPS access to eutils.ncbi.nlm.nih.gov and api.crossref.org.
Set NCBI_API_KEY and CONTACT_EMAIL env vars to be a polite API client.
Exit codes: 0 all verified/skipped, 1 any mismatch/not_found/error, 2 bad input.
"""
import argparse
import datetime as dt
import difflib
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
CROSSREF = "https://api.crossref.org/works/"
TOOL = "confounder-selector"


def http_get_json(url, timeout=20):
    headers = {"User-Agent": f"{TOOL}/2.0 (mailto:{os.environ.get('CONTACT_EMAIL', 'unknown')})"}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def normalize_title(s):
    s = unicodedata.normalize("NFKD", s or "")
    s = re.sub(r"<[^>]+>", " ", s)          # strip HTML/MathML tags Crossref sometimes includes
    s = re.sub(r"[^a-z0-9 ]+", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def title_similarity(a, b):
    return difflib.SequenceMatcher(None, normalize_title(a), normalize_title(b)).ratio()


class Verifier:
    def __init__(self, fetch=http_get_json, threshold=0.90, pause=None):
        self.fetch = fetch
        self.threshold = threshold
        key = os.environ.get("NCBI_API_KEY")
        self.ncbi_params = {"tool": TOOL}
        if os.environ.get("CONTACT_EMAIL"):
            self.ncbi_params["email"] = os.environ["CONTACT_EMAIL"]
        if key:
            self.ncbi_params["api_key"] = key
        # NCBI: 3 req/s without a key, 10 with one
        self.pause = pause if pause is not None else (0.11 if key else 0.34)

    def _eutils(self, endpoint, **params):
        q = urllib.parse.urlencode({**params, **self.ncbi_params, "retmode": "json"})
        time.sleep(self.pause)
        return self.fetch(f"{EUTILS}/{endpoint}.fcgi?{q}")

    def pubmed_summary(self, pmid):
        res = self._eutils("esummary", db="pubmed", id=pmid).get("result", {})
        rec = res.get(str(pmid))
        if not rec or "error" in rec or not rec.get("title"):
            return None
        doi = next((a.get("value") for a in rec.get("articleids", []) if a.get("idtype") == "doi"), None)
        year = re.match(r"(\d{4})", rec.get("pubdate", "") or "")
        authors = rec.get("authors") or []
        return {
            "title": rec.get("title", "").rstrip("."),
            "journal": rec.get("fulljournalname") or rec.get("source"),
            "year": int(year.group(1)) if year else None,
            "first_author": authors[0].get("name") if authors else None,
            "doi": doi,
        }

    def crossref(self, doi):
        try:
            msg = self.fetch(CROSSREF + urllib.parse.quote(doi, safe="/")).get("message", {})
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            raise
        titles = msg.get("title") or []
        if not titles:
            return None
        parts = (msg.get("issued") or {}).get("date-parts") or [[None]]
        authors = msg.get("author") or []
        return {
            "title": titles[0],
            "journal": (msg.get("container-title") or [None])[0],
            "year": parts[0][0] if parts and parts[0] else None,
            "first_author": authors[0].get("family") if authors else None,
            "doi": msg.get("DOI"),
        }

    def pubmed_title_search(self, title, retmax=3):
        term = f'"{title}"[Title]'
        ids = self._eutils("esearch", db="pubmed", term=term, retmax=retmax).get("esearchresult", {}).get("idlist", [])
        return ids

    def check(self, paper):
        """Return a result dict; never mutates `paper`."""
        out = {"id": paper["id"], "status": None, "via": None, "notes": [], "record": None}
        title = paper.get("title", "")
        try:
            if paper.get("pmid"):
                rec = self.pubmed_summary(paper["pmid"])
                out["via"] = "pubmed"
                if rec is None:
                    out["status"] = "not_found"
                    out["notes"].append(f"PMID {paper['pmid']} not found in PubMed")
                    return out
                out["record"] = rec
                sim = title_similarity(title, rec["title"])
                if sim < self.threshold:
                    out["status"] = "mismatch"
                    out["notes"].append(f"title mismatch (similarity {sim:.2f}); PubMed title: {rec['title']!r}")
                    return out
                if paper.get("doi") and rec.get("doi") and paper["doi"].lower() != rec["doi"].lower():
                    out["status"] = "mismatch"
                    out["notes"].append(f"DOI in ledger ({paper['doi']}) differs from PubMed DOI ({rec['doi']})")
                    return out
                out["status"] = "verified"
                return out
            if paper.get("doi"):
                rec = self.crossref(paper["doi"])
                out["via"] = "crossref"
                if rec is None:
                    out["status"] = "not_found"
                    out["notes"].append(f"DOI {paper['doi']} not found in Crossref")
                    return out
                out["record"] = rec
                sim = title_similarity(title, rec["title"])
                if sim < self.threshold:
                    out["status"] = "mismatch"
                    out["notes"].append(f"title mismatch (similarity {sim:.2f}); Crossref title: {rec['title']!r}")
                    return out
                out["status"] = "verified"
                return out
            # no identifier
            if paper.get("source_type") == "uploaded":
                out["status"] = "not_applicable"
                out["notes"].append("uploaded paper without identifier; cited by upload location")
            else:
                out["status"] = "unverified"
                out["notes"].append("no PMID/DOI; cannot verify")
            if title:
                ids = self.pubmed_title_search(title)
                if ids:
                    out["notes"].append(f"possible PubMed matches by title: {', '.join(ids)} (confirm before adding)")
            return out
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as e:
            out["status"] = "error"
            out["notes"].append(f"lookup failed: {e}")
            return out


def apply_results(ledger, results, today=None):
    today = today or dt.date.today().isoformat()
    by_id = {r["id"]: r for r in results}
    for p in ledger.get("papers", []):
        r = by_id.get(p["id"])
        if not r or r["status"] == "error":
            continue  # leave as-is; network failure is not evidence of anything
        p["verification_status"] = r["status"]
        if r["status"] == "verified":
            p["verified_via"] = r["via"]
            p["verified_on"] = today
            rec = r["record"] or {}
            for k in ("journal", "year", "first_author", "doi"):
                if rec.get(k) and not p.get(k):
                    p[k] = rec[k]
    return ledger


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ledger")
    ap.add_argument("--write", metavar="OUT", help="write updated ledger to OUT (may equal input)")
    ap.add_argument("--threshold", type=float, default=0.90)
    args = ap.parse_args(argv)
    try:
        ledger = json.loads(Path(args.ledger).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        print(f"Could not read JSON: {e}", file=sys.stderr)
        return 2
    v = Verifier(threshold=args.threshold)
    results = [v.check(p) for p in ledger.get("papers", [])]
    bad = 0
    for r in results:
        flag = {"verified": "OK  ", "not_applicable": "SKIP", "unverified": "WARN"}.get(r["status"], "FAIL")
        if flag == "FAIL":
            bad += 1
        print(f"[{flag}] {r['id']}: {r['status']}" + (f" via {r['via']}" if r["via"] else ""))
        for n in r["notes"]:
            print(f"       - {n}")
    if all(r["status"] == "error" for r in results) and results:
        print("\nAll lookups failed: this environment probably has no network access to PubMed/Crossref."
              "\nVerify each paper manually at https://pubmed.ncbi.nlm.nih.gov/<PMID>/ or https://doi.org/<DOI>.",
              file=sys.stderr)
    if args.write:
        Path(args.write).write_text(json.dumps(apply_results(ledger, results), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"\nUpdated ledger written to {args.write}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
