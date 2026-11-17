#!/usr/bin/env python3
"""Validate a Confounder Selector evidence ledger.

Two layers:
  1. Structure: the ledger must conform to references/evidence-schema.json
     (uses the `jsonschema` package when installed, otherwise a built-in
     subset validator that reads the same schema file -- no duplicated rules).
  2. Provenance: cross-field rules that make "every confounder comes from a
     real paper" checkable (see references/literature-protocol.md).

This script does NOT contact PubMed/Crossref. Run scripts/verify_citations.py
first so that `verification_status` reflects a real lookup.

Usage: validate_evidence.py LEDGER.json [--strict]
Exit codes: 0 pass, 1 errors (or warnings with --strict), 2 bad input.
"""
import argparse
import json
import re
import sys
from pathlib import Path

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "references" / "evidence-schema.json"

TRUSTED_STATUSES = {"verified"}
FAILED_STATUSES = {"mismatch", "not_found"}
NEEDS_SOURCE_RECS = {"adjust", "sensitivity_only"}
NEEDS_SOURCE_ROLES = {"candidate confounder", "proxy for unmeasured confounder"}
CAUSAL_SUPPORT = {"causes_exposure", "causes_outcome", "associated_with_exposure", "associated_with_outcome"}
MAX_QUOTE_WORDS = 40


# ---------------------------------------------------------------- structure
_TYPES = {
    "object": dict, "array": list, "string": str, "boolean": bool,
    "integer": int, "number": (int, float),
}


def _mini_validate(inst, schema, path="$"):
    """Subset of JSON Schema sufficient for evidence-schema.json."""
    errs = []
    t = schema.get("type")
    if t:
        py = _TYPES[t]
        ok = isinstance(inst, py) and not (t in ("integer", "number") and isinstance(inst, bool))
        if not ok:
            return [f"{path}: expected {t}"]
    if "enum" in schema and inst not in schema["enum"]:
        errs.append(f"{path}: {inst!r} not one of {schema['enum']}")
    if isinstance(inst, str):
        if len(inst.strip()) < schema.get("minLength", 0):
            errs.append(f"{path}: too short")
        if "pattern" in schema and not re.search(schema["pattern"], inst):
            errs.append(f"{path}: {inst!r} does not match {schema['pattern']}")
    if isinstance(inst, (int, float)) and not isinstance(inst, bool):
        if "minimum" in schema and inst < schema["minimum"]:
            errs.append(f"{path}: below minimum {schema['minimum']}")
        if "maximum" in schema and inst > schema["maximum"]:
            errs.append(f"{path}: above maximum {schema['maximum']}")
    if isinstance(inst, list):
        if len(inst) < schema.get("minItems", 0):
            errs.append(f"{path}: needs at least {schema['minItems']} item(s)")
        if "maxItems" in schema and len(inst) > schema["maxItems"]:
            errs.append(f"{path}: at most {schema['maxItems']} item(s)")
        if "items" in schema:
            for i, item in enumerate(inst):
                errs += _mini_validate(item, schema["items"], f"{path}[{i}]")
    if isinstance(inst, dict):
        for k in schema.get("required", []):
            if k not in inst:
                errs.append(f"{path}: missing required '{k}'")
        props = schema.get("properties", {})
        for k, v in inst.items():
            if k in props:
                errs += _mini_validate(v, props[k], f"{path}.{k}")
            elif isinstance(schema.get("additionalProperties"), dict):
                errs += _mini_validate(v, schema["additionalProperties"], f"{path}.{k}")
    return errs


def structural_errors(data, schema):
    try:
        import jsonschema  # type: ignore
    except ImportError:
        return _mini_validate(data, schema)
    validator = jsonschema.Draft202012Validator(schema)
    out = []
    for e in sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path)):
        loc = "$" + "".join(f"[{p}]" if isinstance(p, int) else f".{p}" for p in e.absolute_path)
        out.append(f"{loc}: {e.message}")
    return out


# ---------------------------------------------------------------- provenance
def provenance_checks(data):
    errors, warnings = [], []
    papers = {}
    for i, p in enumerate(data.get("papers", [])):
        pid = p.get("id")
        if pid in papers:
            errors.append(f"papers[{i}]: duplicate paper id '{pid}'")
        papers[pid] = p
        if p.get("source_type") == "retrieved":
            if p.get("verification_status") == "not_applicable":
                errors.append(f"paper '{pid}': retrieved papers cannot be 'not_applicable'; verify them")
            if p.get("verification_status") == "verified" and not (p.get("pmid") or p.get("doi")):
                errors.append(f"paper '{pid}': marked verified but has no PMID or DOI")
            if p.get("verification_status") == "unverified":
                warnings.append(f"paper '{pid}': retrieved but unverified; run verify_citations.py or check the PubMed/DOI page")
    if any(p.get("source_type") == "retrieved" for p in papers.values()) and not data.get("search_log"):
        errors.append("retrieved papers present but search_log is empty; log every query that found them")

    estimand = data.get("question", {}).get("estimand")
    cited = set()
    seen_vars = set()
    for i, c in enumerate(data.get("candidates", [])):
        var = c.get("variable", f"candidates[{i}]")
        key = var.strip().lower()
        if key in seen_vars:
            errors.append(f"candidate '{var}': listed more than once; merge the evidence")
        seen_vars.add(key)
        ev = c.get("evidence", [])
        trusted, support_types = [], set()
        for j, e in enumerate(ev):
            pid = e.get("paper_id")
            cited.add(pid)
            p = papers.get(pid)
            if p is None:
                errors.append(f"candidate '{var}' evidence[{j}]: unknown paper '{pid}'")
                continue
            status = p.get("verification_status")
            if status in FAILED_STATUSES:
                errors.append(f"candidate '{var}' cites paper '{pid}' which failed verification ({status}); remove or correct it")
            if p.get("source_type") == "uploaded" or status in TRUSTED_STATUSES:
                trusted.append(pid)
                support_types.add(e.get("support_type"))
            q = e.get("quote")
            if q and len(q.split()) > MAX_QUOTE_WORDS:
                warnings.append(f"candidate '{var}' evidence[{j}]: quote exceeds {MAX_QUOTE_WORDS} words; paraphrase in 'finding'")

        needs_source = c.get("recommendation") in NEEDS_SOURCE_RECS or c.get("role") in NEEDS_SOURCE_ROLES
        if needs_source and not trusted:
            if c.get("researcher_proposed"):
                warnings.append(f"candidate '{var}': researcher-proposed with no literature support; label it as such in the report")
            else:
                errors.append(f"candidate '{var}': recommended/classified as a confounder but has no evidence from an uploaded or verified paper")
        if c.get("role") == "candidate confounder" and trusted and not (support_types & CAUSAL_SUPPORT):
            warnings.append(f"candidate '{var}': only evidence is prior adjustment practice; look for evidence linking it to the exposure and the outcome")
        if estimand == "total_effect" and c.get("recommendation") == "adjust" and c.get("measurement_timing") == "post_exposure":
            errors.append(f"candidate '{var}': measured post-exposure but recommended for adjustment of a total effect")

    for pid, p in papers.items():
        if p.get("required") and pid not in cited and not (p.get("required_note") or "").strip():
            errors.append(f"required paper '{pid}' is not cited by any candidate; cite it or add required_note explaining why")

    dag = data.get("dag")
    if dag:
        nodes = {n for edge in dag.get("edges", []) for n in edge}
        for c in data.get("candidates", []):
            if c.get("recommendation") == "adjust" and c.get("variable") not in nodes:
                warnings.append(f"candidate '{c.get('variable')}' is recommended for adjustment but is not a node in the DAG")
        for k, ids in (dag.get("edge_sources") or {}).items():
            for pid in ids:
                if pid not in papers:
                    errors.append(f"dag.edge_sources['{k}']: unknown paper '{pid}'")
    return errors, warnings


def validate(data, schema=None):
    """Return (errors, warnings)."""
    if schema is None:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return ["Root must be an object"], []
    s_errs = structural_errors(data, schema)
    if s_errs:
        return s_errs, []  # provenance checks assume valid structure
    return provenance_checks(data)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ledger")
    ap.add_argument("--strict", action="store_true", help="treat warnings as errors")
    args = ap.parse_args(argv)
    try:
        data = json.loads(Path(args.ledger).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        print(f"Could not read JSON: {e}", file=sys.stderr)
        return 2
    errors, warnings = validate(data)
    for e in errors:
        print("ERROR:", e, file=sys.stderr)
    for w in warnings:
        print("WARNING:", w, file=sys.stderr)
    if errors or (args.strict and warnings):
        return 1
    print(f"PASS: structure and provenance checks passed ({len(warnings)} warning(s)).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
