#!/usr/bin/env python3
"""
Bygger og analyserer paradigme-grafen over Norsk Ordbank (sqlite/ordbank.db):
  - Noder: lemmaer (paradigmer), representert ved `lemma_id`
  - Kanter: a --(n, delte_ordformer)-- b hvis lemma `a` og lemma `b` deler `n >= 1` bøyningsformer (`oppslag`).

Brukes til å:
  1. Finne sammenhengende komponenter og fler-hopps-kjeder rundt et lemma (f.eks. «fisker»-komponenten).
  2. Kartlegge hvor store og brede (diameter/antall hopp) komponentene er i hele det norske ordforrådet.
  3. Vurdere identifiserbarhet: Hvor mange entydige ankerformer (grad=0-ordformer) finnes i hver komponent
     sammenlignet med antall delte ordformer (kanter)?
"""

from collections import Counter, defaultdict, deque
from typing import Any
from sqlite.queries import get_conn


def build_paradigm_graph(
    pos_filter: tuple[str, ...] = ("subst", "verb", "adj"),
    exclude_imperative: bool = False,
) -> dict[str, Any]:
    """
    Bygger paradigme-grafen fra `lemma_former` i `sqlite/ordbank.db`.
    Hvis `exclude_imperative=True`, utelates verb-imperativ (`boy_nummer = 11` i `verb, normal`)
    for å se hvor mange kunstige koblinger (som subst. 'mann' <-> imp. 'mann!' av 'manne') som forsvinner.
    """
    conn = get_conn()
    pos_placeholders = ",".join("?" for _ in pos_filter)
    imp_clause = "AND NOT (boy_gruppe = 'verb, normal' AND boy_nummer = 11)" if exclude_imperative else ""

    rows = conn.execute(
        f"""
        SELECT DISTINCT lemma_id, grunnform, pos, oppslag
        FROM lemma_former
        WHERE pos IN ({pos_placeholders})
        {imp_clause}
        """,
        pos_filter,
    ).fetchall()
    conn.close()

    lemma_meta: dict[int, str] = {}
    forms_by_lemma: dict[int, set[str]] = defaultdict(set)
    lemmas_by_form: dict[str, set[int]] = defaultdict(set)

    for r in rows:
        lid = r["lemma_id"]
        gf = r["grunnform"]
        pos = r["pos"]
        opp = r["oppslag"]
        lemma_meta[lid] = f"{gf} ({pos}, id={lid})"
        forms_by_lemma[lid].add(opp)
        lemmas_by_form[opp].add(lid)

    adj: dict[int, dict[int, set[str]]] = defaultdict(dict)
    for opp, lids in lemmas_by_form.items():
        if len(lids) > 1:
            lids_list = sorted(lids)
            for i in range(len(lids_list)):
                for j in range(i + 1, len(lids_list)):
                    u, v = lids_list[i], lids_list[j]
                    if v not in adj[u]:
                        adj[u][v] = set()
                        adj[v][u] = set()
                    adj[u][v].add(opp)
                    adj[v][u].add(opp)

    return {
        "lemma_meta": lemma_meta,
        "forms_by_lemma": forms_by_lemma,
        "lemmas_by_form": lemmas_by_form,
        "adj": adj,
    }


def inspect_component(graph: dict[str, Any], start_lemma_id: int) -> dict[str, Any]:
    """Henter hele den sammenhengende komponenten (med BFS-hopp-avstand) fra `start_lemma_id`."""
    adj = graph["adj"]
    lemma_meta = graph["lemma_meta"]
    forms_by_lemma = graph["forms_by_lemma"]
    lemmas_by_form = graph["lemmas_by_form"]

    visited = {start_lemma_id}
    q = deque([(start_lemma_id, 0)])
    nodes = []

    while q:
        u, dist = q.popleft()
        unamb = sorted(f for f in forms_by_lemma[u] if len(lemmas_by_form[f]) == 1)
        shared = sorted(f for f in forms_by_lemma[u] if len(lemmas_by_form[f]) > 1)
        nodes.append(
            {
                "lemma_id": u,
                "label": lemma_meta[u],
                "hop_dist": dist,
                "unambiguous_forms": unamb,
                "shared_forms": shared,
            }
        )
        for v in sorted(adj[u].keys()):
            if v not in visited:
                visited.add(v)
                q.append((v, dist + 1))

    edges = []
    node_ids = [n["lemma_id"] for n in nodes]
    for i, u in enumerate(node_ids):
        for v in node_ids[i + 1 :]:
            if v in adj[u]:
                shared_uv = sorted(adj[u][v])
                edges.append(
                    {
                        "u": lemma_meta[u],
                        "v": lemma_meta[v],
                        "n": len(shared_uv),
                        "shared_forms": shared_uv,
                    }
                )

    return {"nodes": nodes, "edges": edges, "max_hop": max(n["hop_dist"] for n in nodes)}


def summarize_global_graph(graph: dict[str, Any], label: str = "Hele grafen"):
    adj = graph["adj"]
    lemma_meta = graph["lemma_meta"]
    forms_by_lemma = graph["forms_by_lemma"]
    lemmas_by_form = graph["lemmas_by_form"]

    all_lids = sorted(lemma_meta.keys())
    visited = set()
    comp_sizes = []
    max_hops_sample = []
    edge_n_counts = Counter()

    for u in all_lids:
        for v, sh in adj[u].items():
            if u < v:
                edge_n_counts[len(sh)] += 1

    for lid in all_lids:
        if lid in visited:
            continue
        visited.add(lid)
        q = deque([(lid, 0)])
        comp = []
        max_d = 0
        while q:
            u, d = q.popleft()
            comp.append(u)
            max_d = max(max_d, d)
            for v in adj[u]:
                if v not in visited:
                    visited.add(v)
                    q.append((v, d + 1))
        comp_sizes.append((len(comp), max_d, comp))

    size_buckets = Counter()
    for sz, _, _ in comp_sizes:
        if sz == 1:
            size_buckets["1 (helt isolert / 100 % entydig)"] += 1
        elif sz == 2:
            size_buckets["2 (par)"] += 1
        elif sz == 3:
            size_buckets["3 (triangel/kjede)"] += 1
        elif sz == 4:
            size_buckets["4 (f.eks. fisker-gruppen)"] += 1
        elif 5 <= sz <= 10:
            size_buckets["5–10"] += 1
        else:
            size_buckets["> 10"] += 1

    print(f"==========================================================================")
    print(f"GLOBAL PARADIGME-GRAF: {label} (Totalt {len(all_lids):,d} lemmaer)")
    print(f"==========================================================================")
    print("Fordeling av komponentstørrelser (antall lemmaer og andel av ordforrådet):")
    for k in [
        "1 (helt isolert / 100 % entydig)",
        "2 (par)",
        "3 (triangel/kjede)",
        "4 (f.eks. fisker-gruppen)",
        "5–10",
        "> 10",
    ]:
        n_comps = size_buckets[k]
        n_lemmas = sum(
            sz for sz, _, _ in comp_sizes
            if (sz == 1 and k.startswith("1"))
            or (sz == 2 and k.startswith("2"))
            or (sz == 3 and k.startswith("3"))
            or (sz == 4 and k.startswith("4"))
            or (5 <= sz <= 10 and k == "5–10")
            or (sz > 10 and k == "> 10")
        )
        print(f"  Komponentstørrelse {k:34s}: {n_comps:6,d} komponenter ({n_lemmas:7,d} lemmaer = {n_lemmas/len(all_lids)*100:5.1f}%)")

    print("\nFordeling av kantvekter n (antall delte ordformer mellom to nabo-paradigmer a -- n -- b):")
    for n_val, cnt in sorted(edge_n_counts.items()):
        print(f"  n = {n_val:2d} delte ordformer: {cnt:7,d} kanter")

    largest = sorted(comp_sizes, key=lambda x: -x[0])[:5]
    print("\nDe 5 største sammenhengende komponentene:")
    for sz, max_d, comp in largest:
        sample_names = [lemma_meta[x] for x in comp[:6]]
        print(f"  Størrelse = {sz:3d} lemmaer (BFS-dybde fra startnode = {max_d}): {', '.join(sample_names)} ...")


if __name__ == "__main__":
    g_all = build_paradigm_graph(exclude_imperative=False)
    comp_fisker = inspect_component(g_all, 17348)
    print("=== KOMPONENTEN RUNDT «FISKER» (lemma_id=17348) ===")
    for n in comp_fisker["nodes"]:
        print(
            f"  [hopp={n['hop_dist']}] {n['label']:30s} | "
            f"Entydige ({len(n['unambiguous_forms'])}): {n['unambiguous_forms']} | "
            f"Delte ({len(n['shared_forms'])}): {n['shared_forms']}"
        )
    print("\nKanter (a -- n -- b) i «fisker»-komponenten:")
    for e in comp_fisker["edges"]:
        print(f"  {e['u']:28s} <-- n={e['n']} {e['shared_forms']} --> {e['v']}")
    print()

    summarize_global_graph(g_all, label="Subst + Verb + Adj (inkl. imperativ)")
    print()
    g_no_imp = build_paradigm_graph(exclude_imperative=True)
    summarize_global_graph(g_no_imp, label="Subst + Verb + Adj (UTEN verb-imperativ)")
