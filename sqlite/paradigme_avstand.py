#!/usr/bin/env python3
"""
Avstander i paradigmegrafen: hvor langt er det fra ett paradigme (lemma) til et annet?

    python3 -m sqlite.paradigme_avstand                    # statistikk for hele grafen + figur
    python3 -m sqlite.paradigme_avstand liten rose         # korteste vei mellom to grunnformer
    python3 -m sqlite.paradigme_avstand --uten-imperativ   # samme uten verbimperativ

Grafen er den samme som i `sqlite/paradigm_graph.py`: noder er lemmaer (substantiv, verb og adjektiv i
`lemma_former`), og to lemmaer er koblet når de deler minst én ordform. Kanten har vekten n = antall
delte former.

To avstandsmål:
  - hopp: antall kanter på korteste vei (hvor mange ganger må man «bytte paradigme via en delt form»);
  - vektet: kantlengde 1/n, så paradigmer som deler mange former, ligger nærmere hverandre
    (*fiske* subst. og *fiske* verb deler fire former og har lengde 0,25; ett delt imperativ gir 1).
Lemmaer i ulike komponenter har uendelig avstand; statistikken gjelder par i samme komponent.
"""

import heapq
from collections import Counter, deque
from pathlib import Path

import numpy as np

from sqlite.paradigm_graph import build_paradigm_graph

ROOT = Path(__file__).resolve().parent.parent
OUT_TSV = ROOT / "resultater" / "paradigme_avstand.tsv"


def label(graph: dict, lid: int) -> str:
    """«grunnform (pos)» uten lemma_id."""
    return graph["lemma_meta"][lid].split(", id=")[0] + ")"


def lemmas_for(graph: dict, grunnform: str) -> list[int]:
    return sorted(l for l, m in graph["lemma_meta"].items() if m.split(" (")[0] == grunnform)


def components(graph: dict) -> list[list[int]]:
    """Sammenhengende komponenter, største først."""
    adj, seen, out = graph["adj"], set(), []
    for s in graph["lemma_meta"]:
        if s in seen:
            continue
        seen.add(s)
        q, comp = deque([s]), []
        while q:
            u = q.popleft()
            comp.append(u)
            for v in adj.get(u, {}):
                if v not in seen:
                    seen.add(v)
                    q.append(v)
        out.append(comp)
    return sorted(out, key=len, reverse=True)


def bfs(graph: dict, src: int) -> dict[int, int]:
    adj, dist, q = graph["adj"], {src: 0}, deque([src])
    while q:
        u = q.popleft()
        for v in adj.get(u, {}):
            if v not in dist:
                dist[v] = dist[u] + 1
                q.append(v)
    return dist


def dijkstra(graph: dict, src: int) -> tuple[dict[int, float], dict[int, int]]:
    """Vektet avstand med kantlengde 1/n; returnerer avstand og forgjenger."""
    adj, dist, prev, heap = graph["adj"], {src: 0.0}, {}, [(0.0, src)]
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:
            continue
        for v, shared in adj.get(u, {}).items():
            nd = d + 1.0 / len(shared)
            if nd < dist.get(v, float("inf")):
                dist[v], prev[v] = nd, u
                heapq.heappush(heap, (nd, v))
    return dist, prev


def shortest_path(graph: dict, a: str, b: str) -> dict | None:
    """Korteste vei mellom to grunnformer (alle homografe lemmaer prøves). None hvis ingen vei."""
    best = None
    for la in lemmas_for(graph, a):
        hops = bfs(graph, la)
        dist, prev = dijkstra(graph, la)
        for lb in lemmas_for(graph, b):
            if lb not in dist or la == lb:
                continue
            if best is None or dist[lb] < best["weighted"]:
                path = [lb]
                while path[-1] != la:
                    path.append(prev[path[-1]])
                path.reverse()
                steps = [{"from": label(graph, u), "to": label(graph, v), "shared": sorted(graph["adj"][u][v])}
                         for u, v in zip(path, path[1:])]
                best = {"a": label(graph, la), "b": label(graph, lb), "hops": hops[lb],
                        "weighted": dist[lb], "path_hops": len(steps), "steps": steps}
    return best


def distance_stats(graph: dict) -> dict:
    """Avstander mellom alle par i samme komponent (bare komponenter med mer enn ett lemma)."""
    comps = [c for c in components(graph) if len(c) > 1]
    hop_hist, diam_hist, wdist = Counter(), Counter(), []
    per_comp = []
    for c in comps:
        diam, wmax, pair_h = 0, 0.0, []
        for u in c:
            h = bfs(graph, u)
            w, _ = dijkstra(graph, u)
            for v in c:
                if u < v:
                    hop_hist[h[v]] += 1
                    pair_h.append(h[v])
                    wdist.append(w[v])
                    wmax = max(wmax, w[v])
            diam = max(diam, max(h.values()))
        diam_hist[diam] += 1
        per_comp.append({"size": len(c), "diameter": diam, "mean_hops": float(np.mean(pair_h)), "w_diameter": wmax,
                         "lemmas": c})
    return {"n_comps": len(comps), "hop_hist": hop_hist, "diam_hist": diam_hist,
            "weighted": np.array(wdist), "per_comp": per_comp}


def report(graph: dict, st: dict, title: str) -> None:
    pairs = sum(st["hop_hist"].values())
    print(f"\n{title}: {st['n_comps']} komponenter med mer enn ett lemma, {pairs:,} par i samme komponent")
    print("  Avstand i hopp mellom par i samme komponent:")
    cum = 0
    for k in sorted(st["hop_hist"]):
        cum += st["hop_hist"][k]
        print(f"    {k:2d} hopp: {st['hop_hist'][k]:7,d} par ({100 * st['hop_hist'][k] / pairs:5.1f} %, kumulativt {100 * cum / pairs:5.1f} %)")
    print("  Diameter (lengste korteste vei) per komponent:")
    for k in sorted(st["diam_hist"]):
        print(f"    {k:2d}: {st['diam_hist'][k]:5d} komponenter")
    w = st["weighted"]
    print(f"  Vektet avstand (1/n per kant): median {np.median(w):.2f}, 90-pers. {np.percentile(w, 90):.2f}, maks {w.max():.2f}")
    print("  Største komponenter:")
    for c in st["per_comp"][:5]:
        names = sorted({label(graph, l).split(" (")[0] for l in c["lemmas"]})
        print(f"    {c['size']:3d} lemmaer, diameter {c['diameter']} hopp (vektet {c['w_diameter']:.1f}), "
              f"snitt {c['mean_hops']:.1f}: {', '.join(names[:10])} …")


def write_tsv(graph: dict, st: dict) -> None:
    OUT_TSV.parent.mkdir(exist_ok=True)
    with OUT_TSV.open("w", encoding="utf-8") as f:
        f.write("komponent\tstorrelse\tdiameter_hopp\tsnitt_hopp\tdiameter_vektet\tlemmaer\n")
        for i, c in enumerate(st["per_comp"], 1):
            names = ";".join(sorted(label(graph, l) for l in c["lemmas"]))
            f.write(f"{i}\t{c['size']}\t{c['diameter']}\t{c['mean_hops']:.3f}\t{c['w_diameter']:.3f}\t{names}\n")


SUP = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")


def lemma_labels(graph: dict, lids: list[int]) -> dict[int, str]:
    """Bare grunnformen; homografe lemmaer nummereres som i en ordbok (leie¹, leie², …), ordnet etter ordklasse og lemma_id."""
    by_gf: dict[str, list[int]] = {}
    for l in lids:
        by_gf.setdefault(label(graph, l).split(" (")[0], []).append(l)
    out = {}
    for gf, ls in by_gf.items():
        ls = sorted(ls, key=lambda l: (label(graph, l).split(" (")[1], l))
        for i, l in enumerate(ls, 1):
            out[l] = gf if len(ls) == 1 else gf + str(i).translate(SUP)
    return out


def _spring_layout(nodes: list[int], edges: list[tuple[int, int, int]], seed: int = 7, iters: int = 1500) -> dict:
    """Enkel Fruchterman–Reingold i numpy (unngår ny avhengighet)."""
    rng = np.random.default_rng(seed)
    idx = {n: i for i, n in enumerate(nodes)}
    pos = rng.uniform(-1, 1, (len(nodes), 2))
    k = 2.2 / np.sqrt(len(nodes))  # større k = mer luft mellom nodene
    E = np.array([(idx[u], idx[v]) for u, v, _ in edges])
    t = 0.2
    for _ in range(iters):
        d = pos[:, None, :] - pos[None, :, :]
        dist = np.linalg.norm(d, axis=2) + 1e-9
        disp = (d / dist[..., None] * (k * k / dist)[..., None]).sum(axis=1)
        dv = pos[E[:, 0]] - pos[E[:, 1]]
        dl = np.linalg.norm(dv, axis=1)[:, None] + 1e-9
        f = dv / dl * (dl * dl / k)
        np.add.at(disp, E[:, 0], -f)
        np.add.at(disp, E[:, 1], f)
        ln = np.linalg.norm(disp, axis=1)[:, None] + 1e-9
        pos += disp / ln * np.minimum(ln, t)
        t *= 0.997
    # Kollisjoner: tette homografklynger (leie¹–⁵) trekkes sammen av mange kanter; skyv dem fra hverandre
    span = pos.max(axis=0) - pos.min(axis=0)
    dmin = 0.075 * float(span.max())
    for _ in range(400):
        d = pos[:, None, :] - pos[None, :, :]
        dist = np.linalg.norm(d * np.array([1.0, 1.6]), axis=2) + np.eye(len(nodes)) * 1e9  # etiketter er brede, ikke høye
        over = np.clip(dmin - dist, 0, None)
        if over.max() < 1e-4:
            break
        pos += 0.5 * (d / (dist[..., None]) * over[..., None]).sum(axis=1)
    return {n: pos[idx[n]] for n in nodes}


def figure(graph: dict, st: dict, center: str = "liten") -> Path:
    """Venstre: største komponent, farget etter hopp fra `center`. Høyre: fordeling av hopp mellom par."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from sqlite.figurer import GRID, INK, MUTED, OUT_DIR

    comp = st["per_comp"][0]["lemmas"]
    cset = set(comp)
    edges = [(u, v, len(s)) for u in comp for v, s in graph["adj"][u].items() if v in cset and u < v]
    pos = _spring_layout(comp, edges)
    src = next(l for l in lemmas_for(graph, center) if l in cset)
    hops = bfs(graph, src)
    far = max(comp, key=lambda l: hops[l])
    # diameterstien fra center til den fjerneste noden
    path, cur = [far], far
    while cur != src:
        cur = next(v for v in graph["adj"][cur] if hops.get(v) == hops[cur] - 1)
        path.append(cur)
    on_path = set(zip(path, path[1:])) | set(zip(path[1:], path))

    names = lemma_labels(graph, comp)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(13.5, 6.4), gridspec_kw={"width_ratios": [1.9, 1]})
    cmap = plt.get_cmap("viridis_r")
    maxh = max(hops[l] for l in comp)
    for u, v, n in edges:
        (x1, y1), (x2, y2) = pos[u], pos[v]
        hl = (u, v) in on_path
        a1.plot([x1, x2], [y1, y2], color=INK if hl else MUTED, lw=(2.2 if hl else 0.8) + 0.9 * (n - 1),
                alpha=0.9 if hl else 0.35, zorder=2 if hl else 1, solid_capstyle="round")
    for l in comp:
        x, y = pos[l]
        a1.scatter([x], [y], s=150, color=cmap(hops[l] / maxh), edgecolor="white", lw=1.5, zorder=3)
        a1.text(x, y + 0.045, names[l], fontsize=9.5, ha="center", va="bottom", color=INK,
                fontweight="bold" if l in (src, far) else "normal", zorder=4)
    a1.set_title(f"Største komponent: {len(comp)} lemmaer, farget etter hopp fra «{center}»",
                 fontsize=13, loc="left", color=INK)
    a1.axis("off")
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(0, maxh))
    cb = fig.colorbar(sm, ax=a1, fraction=0.03, pad=0.01)
    cb.set_label("hopp", color=MUTED)

    hh = st["hop_hist"]
    ks = sorted(hh)
    tot = sum(hh.values())
    a2.bar(ks, [100 * hh[k] / tot for k in ks], color=MUTED, width=0.7)
    for k in ks:
        if hh[k] / tot > 0.005:
            a2.text(k, 100 * hh[k] / tot + 1, f"{100 * hh[k] / tot:.0f} %", ha="center", fontsize=9, color=INK)
    a2.set_title("Hopp mellom par i samme komponent (hele grafen)", fontsize=13, loc="left", color=INK)
    a2.set_xticks(ks)
    a2.set_xlabel("antall hopp", color=MUTED)
    a2.yaxis.grid(True, color=GRID, lw=0.8)
    a2.set_axisbelow(True)
    a2.set_ylim(0, 100)
    fig.text(0.01, 0.01, "Noder: lemmaer; homografer nummerert (leie¹, leie², …). Kanter: delte ordformer, bredde = antall. "
             f"Mørk sti: korteste vei fra {center} til {label(graph, far).split(' (')[0]} ({hops[far]} hopp).",
             fontsize=9.5, color=MUTED)
    out = OUT_DIR / "paradigme_avstand.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out


def print_path(res: dict | None, a: str, b: str) -> None:
    if res is None:
        print(f"Ingen vei mellom «{a}» og «{b}»: de ligger i ulike komponenter.")
        return
    print(f"{res['a']} → {res['b']}: {res['hops']} hopp (vektet {res['weighted']:.2f}; vektet sti har {res['path_hops']} hopp)")
    for s in res["steps"]:
        print(f"  {s['from']:22s} → {s['to']:22s} via {', '.join(s['shared'])}")


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Avstander i paradigmegrafen.")
    ap.add_argument("ord", nargs="*", help="to grunnformer: vis korteste vei mellom dem")
    ap.add_argument("--uten-imperativ", action="store_true", help="utelat verbimperativ (som skaper mange tilfeldige koblinger)")
    a = ap.parse_args()
    g = build_paradigm_graph(exclude_imperative=a.uten_imperativ)
    if len(a.ord) == 2:
        print_path(shortest_path(g, *a.ord), *a.ord)
    else:
        st = distance_stats(g)
        report(g, st, "Uten imperativ" if a.uten_imperativ else "Hele grafen")
        if not a.uten_imperativ:
            write_tsv(g, st)
            print(f"\nSkrev {OUT_TSV}\nSkrev {figure(g, st)}")
