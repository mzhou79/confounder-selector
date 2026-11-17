#!/usr/bin/env python3
"""DAG utilities for a Confounder Selector ledger (no dependencies).

Reads ledger["dag"] = {"exposure", "outcome", "edges": [[from, to], ...], "latent": [...]}
and:
  * prints DAGitty code you can paste into https://www.dagitty.net/dags.html
    or use with the R package `dagitty`
  * enumerates minimal sufficient adjustment sets (back-door criterion,
    excluding descendants of the exposure and latent nodes)
  * checks whether the ledger's proposed set (recommendation == "adjust")
    satisfies the back-door criterion under this DAG

The result is only as good as the DAG. Edges are assumptions; record the
papers that justify each one in dag.edge_sources.

Usage: dag_tools.py LEDGER.json [--dagitty-only] [--max-size N]
"""
import argparse
import itertools
import json
import re
import sys
from pathlib import Path


class DAG:
    def __init__(self, edges, latent=()):
        self.parents, self.children = {}, {}
        for a, b in edges:
            for n in (a, b):
                self.parents.setdefault(n, set())
                self.children.setdefault(n, set())
            self.parents[b].add(a)
            self.children[a].add(b)
        self.latent = set(latent)
        self.nodes = set(self.parents)
        cycle = self._find_cycle()
        if cycle:
            raise ValueError(f"graph has a cycle: {' -> '.join(cycle)}")

    def _find_cycle(self):
        state = {}
        def visit(n, stack):
            state[n] = 1
            stack.append(n)
            for c in self.children[n]:
                if state.get(c) == 1:
                    return stack[stack.index(c):] + [c]
                if not state.get(c):
                    r = visit(c, stack)
                    if r:
                        return r
            stack.pop()
            state[n] = 2
            return None
        for n in sorted(self.nodes):
            if not state.get(n):
                r = visit(n, [])
                if r:
                    return r
        return None

    def _closure(self, start, nbrs):
        seen, todo = set(), list(start)
        while todo:
            n = todo.pop()
            for m in nbrs[n]:
                if m not in seen:
                    seen.add(m)
                    todo.append(m)
        return seen

    def descendants(self, n):
        return self._closure([n], self.children)

    def ancestors(self, ns):
        return self._closure(list(ns), self.parents) | set(ns)

    def d_separated(self, x, y, z, drop_out_of=None):
        """x _||_ y | z, optionally in the graph with edges out of `drop_out_of` removed."""
        parents = {n: set(p) for n, p in self.parents.items()}
        if drop_out_of is not None:
            for c in self.children[drop_out_of]:
                parents[c].discard(drop_out_of)
        # ancestral set of {x, y} U z
        anc, todo = {x, y, *z}, [x, y, *z]
        while todo:
            n = todo.pop()
            for p in parents[n]:
                if p not in anc:
                    anc.add(p)
                    todo.append(p)
        # moralize
        und = {n: set() for n in anc}
        for n in anc:
            ps = [p for p in parents[n] if p in anc]
            for p in ps:
                und[n].add(p); und[p].add(n)
            for a, b in itertools.combinations(ps, 2):
                und[a].add(b); und[b].add(a)
        # remove z, test connectivity
        blocked = set(z)
        seen, todo = {x}, [x]
        while todo:
            n = todo.pop()
            if n == y:
                return False
            for m in und[n]:
                if m not in seen and m not in blocked:
                    seen.add(m)
                    todo.append(m)
        return True

    def satisfies_backdoor(self, x, y, z):
        z = set(z)
        if z & self.descendants(x):
            return False
        return self.d_separated(x, y, z, drop_out_of=x)

    def minimal_adjustment_sets(self, x, y, max_size=None):
        pool = sorted(self.nodes - {x, y} - self.latent - self.descendants(x))
        max_size = len(pool) if max_size is None else min(max_size, len(pool))
        found = []
        for k in range(max_size + 1):
            for combo in itertools.combinations(pool, k):
                s = set(combo)
                if any(f <= s for f in found):
                    continue
                if self.satisfies_backdoor(x, y, s):
                    found.append(s)
        return [sorted(s) for s in found]


def _ident(name):
    s = re.sub(r"[^A-Za-z0-9_]", "_", name)
    return s if re.match(r"[A-Za-z_]", s) else "v_" + s


def to_dagitty(dag_spec):
    x, y = dag_spec["exposure"], dag_spec["outcome"]
    latent = set(dag_spec.get("latent", []))
    nodes = sorted({n for e in dag_spec["edges"] for n in e} | {x, y})
    lines = ["dag {"]
    for n in nodes:
        tag = " [exposure]" if n == x else " [outcome]" if n == y else " [latent]" if n in latent else ""
        lines.append(f"  {_ident(n)}{tag}")
    for a, b in dag_spec["edges"]:
        lines.append(f"  {_ident(a)} -> {_ident(b)}")
    lines.append("}")
    return "\n".join(lines)


def analyze(ledger, max_size=None):
    spec = ledger.get("dag")
    if not spec:
        raise ValueError("ledger has no 'dag' section")
    x, y = spec["exposure"], spec["outcome"]
    g = DAG(spec["edges"], spec.get("latent", []))
    for n in (x, y):
        if n not in g.nodes:
            raise ValueError(f"'{n}' does not appear in any edge")
    proposed = sorted(c["variable"] for c in ledger.get("candidates", []) if c.get("recommendation") == "adjust")
    not_in_dag = [v for v in proposed if v not in g.nodes]
    in_dag = [v for v in proposed if v in g.nodes]
    desc = g.descendants(x)
    return {
        "dagitty": to_dagitty(spec),
        "minimal_sets": g.minimal_adjustment_sets(x, y, max_size),
        "proposed": proposed,
        "proposed_not_in_dag": not_in_dag,
        "proposed_descendants_of_exposure": sorted(set(in_dag) & desc),
        "proposed_sufficient": g.satisfies_backdoor(x, y, in_dag),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ledger")
    ap.add_argument("--dagitty-only", action="store_true")
    ap.add_argument("--max-size", type=int, default=None, help="largest adjustment set to enumerate")
    args = ap.parse_args(argv)
    try:
        ledger = json.loads(Path(args.ledger).read_text(encoding="utf-8"))
        res = analyze(ledger, args.max_size)
    except (OSError, ValueError, KeyError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    print(res["dagitty"])
    if args.dagitty_only:
        return 0
    print("\nMinimal sufficient adjustment sets (back-door criterion):")
    if res["minimal_sets"]:
        for s in res["minimal_sets"]:
            print("  {" + ", ".join(s) + "}")
    else:
        print("  none among observed, non-descendant nodes (unmeasured confounding cannot be blocked under this DAG)")
    print(f"\nProposed set: {{{', '.join(res['proposed'])}}}")
    if res["proposed_not_in_dag"]:
        print(f"  not in DAG: {', '.join(res['proposed_not_in_dag'])}")
    if res["proposed_descendants_of_exposure"]:
        print(f"  WARNING descendants of exposure: {', '.join(res['proposed_descendants_of_exposure'])}")
    print(f"  sufficient under this DAG: {'yes' if res['proposed_sufficient'] else 'NO'}")
    return 0 if res["proposed_sufficient"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
