#!/usr/bin/env python3
"""
Figurer til MONS-presentasjonen (tekst/figurer/*.png).

    python3 -m sqlite.figurer

Krever matplotlib (Matplotlib License, BSD-lignende) og numpy. Bruker bokkorpuset
1950–2020 via sqlite/ngram.py (cache i sqlite/ngram_cache.db) og
resultater/verbtyper.tsv (skrives av `python3 -m sqlite.verbtyper`).

1. verb_ternaer.png      – hvert verb i Sett A (N = 580) som et punkt i inf/pres/pret-trekanten
2. verb_stabilitet.png   – andel per form per år for fire stabile verb
3. fisker_over_tid.png   – ordformen «fisker» fordelt på tre leksemer per år, to sett forholdstall
4. paradigmegraf_fisker.png – komponenten rundt «fisker» i paradigmegrafen (sqlite/paradigm_graph.py)
5. dor_tro_over_tid.png  – «dør» og «tro» fordelt på leksemer per år, med usikkerhetsbånd (sqlite/tidsserie.py)
6. dor_tro_metoder.png   – verbandelen av «dør» og «tro» per år: bigrammer (hovedmetode) mot paradigmet
"""

import contextlib
import csv
import io
import math
from pathlib import Path

import logging

import matplotlib

matplotlib.use("Agg")
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)  # Calibri finnes ikke overalt
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from sqlite.ngram import fetch_ngram_dhlab  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "tekst" / "figurer"
TSV = ROOT / "resultater" / "verbtyper.tsv"
PERIOD = (1950, 2020)
YEARS = list(range(PERIOD[0], PERIOD[1] + 1))

# Farge følger formen i hele decket (validert med dataviz-skillens validate_palette.js).
INK = "#22223B"
MUTED = "#4A4E69"
GRID = "#D9DCE3"
FORM_COLOR = {"inf": "#B5482F", "pres": "#3D5A98", "pret": "#2A9D8F"}
FORM_LABEL = {"inf": "infinitiv", "pres": "presens", "pret": "preteritum"}

plt.rcParams.update({
    "font.family": ["Calibri", "Helvetica Neue", "Arial", "DejaVu Sans"],
    "font.size": 13,
    "text.color": INK,
    "axes.labelcolor": MUTED,
    "axes.edgecolor": GRID,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "savefig.dpi": 200,
    "savefig.bbox": "tight",
    "savefig.facecolor": "white",
})


def load_verbs() -> list[dict]:
    with TSV.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    for r in rows:
        tot = sum(int(r[f"book_{s}"]) for s in FORM_COLOR)
        r["share"] = {s: int(r[f"book_{s}"]) / tot for s in FORM_COLOR}
        r["top"] = max(FORM_COLOR, key=lambda s: r["share"][s])
    return rows


# ---------- 1. Ternærplott ----------

H = math.sqrt(3) / 2


def tern_xy(inf: float, pres: float, pret: float) -> tuple[float, float]:
    # inf øverst, pres nede til venstre, pret nede til høyre
    return pret + inf / 2, inf * H


def fig_ternary(verbs: list[dict]) -> Path:
    fig, ax = plt.subplots(figsize=(7.4, 6.4))
    ax.set_aspect("equal")
    ax.axis("off")
    corners = {"inf": (0.5, H), "pres": (0, 0), "pret": (1, 0)}
    ax.add_patch(plt.Polygon(list(corners.values()), closed=True, fill=False, ec=GRID, lw=1.5, zorder=1))
    # Grenser mellom topp-regionene: fra midtpunktet til midten av hver side
    c = tern_xy(1 / 3, 1 / 3, 1 / 3)
    for a, b in (("inf", "pres"), ("pres", "pret"), ("inf", "pret")):
        m = ((corners[a][0] + corners[b][0]) / 2, (corners[a][1] + corners[b][1]) / 2)
        ax.plot([c[0], m[0]], [c[1], m[1]], color=GRID, lw=1.2, ls=(0, (4, 3)), zorder=1)
    for s in FORM_COLOR:
        pts = [tern_xy(v["share"]["inf"], v["share"]["pres"], v["share"]["pret"]) for v in verbs if v["top"] == s]
        n = len(pts)
        ax.scatter(*zip(*pts), s=22, color=FORM_COLOR[s], alpha=0.75, edgecolors="white", linewidths=0.6, zorder=3,
                   label=f"{FORM_LABEL[s]} på topp ({100 * n / len(verbs):.0f} %)".replace(".", ","))
    # Hjørnetekster
    ax.text(0.5, H + 0.04, "infinitiv", ha="center", va="bottom", fontsize=15, fontweight="bold")
    ax.text(-0.02, -0.04, "presens", ha="right", va="top", fontsize=15, fontweight="bold")
    ax.text(1.02, -0.04, "preteritum", ha="left", va="top", fontsize=15, fontweight="bold")
    # Utvalgte verb
    labels = {"ta": (0.05, 0.03), "vurdere": (-0.08, 0.03), "undersøke": (0.07, -0.02), "trenge": (-0.07, 0.07),
              "forsvinne": (0.06, 0.03), "rope": (0.06, -0.01), "bestå": (-0.08, -0.04)}
    for v in verbs:
        if v["grunnform"] in labels:
            x, y = tern_xy(v["share"]["inf"], v["share"]["pres"], v["share"]["pret"])
            dx, dy = labels[v["grunnform"]]
            ax.annotate(v["grunnform"], (x, y), (x + dx, y + dy), fontsize=12, style="italic", color=INK,
                        ha="left" if dx > 0 else "right", va="center",
                        arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8), zorder=4)
            ax.scatter([x], [y], s=34, facecolor="none", edgecolor=INK, linewidths=1.0, zorder=4)
    ax.legend(loc="upper left", bbox_to_anchor=(-0.02, 1.0), frameon=False, fontsize=12, handletextpad=0.3,
              markerscale=1.4)
    ax.set_xlim(-0.12, 1.12)
    ax.set_ylim(-0.1, H + 0.1)
    out = OUT_DIR / "verb_ternaer.png"
    fig.savefig(out)
    plt.close(fig)
    return out


# ---------- 2. Tidsserier for stabile verb ----------

STABLE = ["vurdere", "undersøke", "forsvinne", "trenge"]


def fig_stability(verbs: list[dict]) -> Path:
    by_gf = {v["grunnform"]: v for v in verbs}
    forms = {gf: {s: by_gf[gf][s].split(",") for s in FORM_COLOR} for gf in STABLE}
    words = sorted({w for gf in STABLE for s in FORM_COLOR for w in forms[gf][s]})
    series = fetch_ngram_dhlab(words, period=PERIOD, batch_size=80)
    fig, axes = plt.subplots(2, 2, figsize=(7.3, 4.9), sharex=True, sharey=True)
    for ax, gf in zip(axes.flat, STABLE):
        yearly = {s: np.array([sum(series[w].get(y, 0) for w in forms[gf][s]) for y in YEARS], float) for s in FORM_COLOR}
        tot = sum(yearly.values())
        ends = {}
        for s in FORM_COLOR:
            share = 100 * yearly[s] / tot
            ax.plot(YEARS, share, color=FORM_COLOR[s], lw=2, solid_capstyle="round")
            ends[s] = share[-1]
        # Direkte etiketter i høyre kant, skjøvet fra hverandre (minst 9 prosentpoeng)
        order = sorted(ends, key=ends.get)
        ys = [ends[s] for s in order]
        for i in range(1, len(ys)):
            ys[i] = max(ys[i], ys[i - 1] + 9)
        for s, y in zip(order, ys):
            ax.text(PERIOD[1] + 1.5, y, forms[gf][s][0], color=INK, fontsize=11, style="italic", va="center")
        ax.set_title(gf, loc="left", fontsize=14, fontweight="bold", style="italic", color=INK)
        ax.set_ylim(0, 100)
        ax.set_yticks([0, 50, 100])
        ax.set_xticks([1950, 1985, 2020])
        ax.grid(axis="y", color=GRID, lw=0.8)
        ax.tick_params(length=0)
    for ax in axes[:, 0]:
        ax.set_ylabel("% av formene")
    handles = [plt.Line2D([], [], color=FORM_COLOR[s], lw=2.5) for s in FORM_COLOR]
    fig.legend(handles, [FORM_LABEL[s] for s in FORM_COLOR], loc="lower center", ncol=3, frameon=False,
               bbox_to_anchor=(0.5, -0.06), fontsize=12)
    fig.tight_layout(w_pad=3.0)
    out = OUT_DIR / "verb_stabilitet.png"
    fig.savefig(out)
    plt.close(fig)
    return out


# ---------- 3. «fisker» over tid ----------

LEXEME_COLOR = {"en fisker": "#3D5A98", "fisk (flertall)": "#2A9D8F", "å fiske (presens)": "#B5482F"}


def fisker_yearly(smooth: int = 5) -> tuple[dict[str, np.ndarray], np.ndarray, np.ndarray]:
    from sqlite.decompose_fisker import analyze_fisker_decomposition

    # Koeffisientene er anslått på totalene i nb_totals; vi antar at de er stabile over tid.
    with contextlib.redirect_stdout(io.StringIO()):
        k = analyze_fisker_decomposition()
    words = ["fisker", "fiskeren", "fiskere", "fiskerne", "fiskene", "fiskes"]
    series = fetch_ngram_dhlab(words, period=PERIOD)
    a = {w: np.array([series[w].get(y, 0) for y in YEARS], float) for w in words}
    if smooth > 1:  # glidende snitt over `smooth` år for å dempe støy i små ankertall
        kern = np.ones(smooth) / smooth
        a = {w: np.convolve(np.pad(v, smooth // 2, mode="edge"), kern, mode="valid") for w, v in a.items()}
    raw = {
        "en fisker": np.dot(k["fisker_noun_weights"], [a["fiskeren"], a["fiskere"], a["fiskerne"]]),
        "fisk (flertall)": k["fisk_fl_ub_per_fiskene"] * a["fiskene"],
        "å fiske (presens)": k["fiske_pres_per_fiskes"] * a["fiskes"],
    }
    raw_sum = sum(raw.values())
    shares = {lx: 100 * v / raw_sum for lx, v in raw.items()}
    return shares, raw_sum / a["fisker"], a["fisker"]


def fig_fisker() -> Path:
    """To varianter: forholdstall lært på nb_totals (stiplet) og i bokkorpuset (heltrukket)."""
    from sqlite.decompose_fisker import book_decomposition

    nb_shares, nb_ratio, _ = fisker_yearly()
    book = book_decomposition(PERIOD)
    fig, ax = plt.subplots(figsize=(7.3, 4.6))
    for lx, col in LEXEME_COLOR.items():
        ax.plot(YEARS, book["shares"][lx], color=col, lw=2.5, solid_capstyle="round")
        ax.plot(YEARS, nb_shares[lx], color=col, lw=1.8, ls=(0, (4, 2.5)), alpha=0.9)
    # Direkte etiketter ved enden av den heltrukne linjen, skjøvet fra hverandre
    ends = sorted(LEXEME_COLOR, key=lambda lx: book["shares"][lx][-1])
    ys = [book["shares"][lx][-1] for lx in ends]
    for i in range(1, len(ys)):
        ys[i] = max(ys[i], ys[i - 1] + 7)
    for lx, y in zip(ends, ys):
        ax.text(PERIOD[1] + 1.5, y, lx, color=INK, fontsize=12, va="center")
    ax.set_xlim(PERIOD)
    ax.set_ylim(0, 80)
    ax.set_yticks([0, 20, 40, 60, 80])
    ax.set_yticklabels(["0", "20", "40", "60", "80 %"])
    ax.set_xticks([1950, 1970, 1990, 2010])
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.tick_params(length=0)
    handles = [plt.Line2D([], [], color=MUTED, lw=2.5), plt.Line2D([], [], color=MUTED, lw=1.8, ls=(0, (4, 2.5)))]
    ax.legend(handles, ["forholdstall lært i bokkorpuset", "forholdstall lært i hele NB-korpuset"], loc="upper center",
              bbox_to_anchor=(0.5, -0.08), ncol=2, frameon=False, fontsize=11)
    out = OUT_DIR / "fisker_over_tid.png"
    fig.savefig(out)
    plt.close(fig)
    for name, sh, ratio in (("bok", book["shares"], book["sum_obs"]), ("nb_totals", nb_shares, nb_ratio)):
        print(f"  Forholdstall lært i {name}:")
        for lx in LEXEME_COLOR:
            v = sh[lx]
            print(f"    {lx:18s} 1950 {v[0]:5.1f} %  1985 {v[35]:5.1f} %  2020 {v[-1]:5.1f} %")
        print(f"    Sum ukappede anslag / observert «fisker»: median {np.median(ratio):.2f} (spenn {ratio.min():.2f}–{ratio.max():.2f})")
    return out


POS_LABEL = {"subst": "substantiv", "verb": "verb", "adj": "adjektiv"}
FISKER_LEMMA_ID = 17348


def fig_paradigm_graph(start_lemma_id: int = FISKER_LEMMA_ID) -> Path:
    """Komponenten rundt et lemma: noder = lemmaer med entydige former, kanter = delte former (bredde ~ n)."""
    from matplotlib.patches import FancyBboxPatch

    from sqlite.paradigm_graph import build_paradigm_graph, inspect_component

    comp = inspect_component(build_paradigm_graph(), start_lemma_id)
    nodes = comp["nodes"]
    if len(nodes) != 4:
        raise ValueError(f"layouten forutsetter fire lemmaer, fikk {len(nodes)}")
    # Startnoden i midten, de tre andre i en trekant rundt (K4 tegnet uten kryssende kanter)
    others = sorted(nodes[1:], key=lambda n: (n["label"].split(" (")[1], n["lemma_id"]))
    pos = {nodes[0]["lemma_id"]: (0.0, 0.0)}
    for n, xy in zip(others, [(0.0, 1.15), (-1.45, -0.95), (1.45, -0.95)]):
        pos[n["lemma_id"]] = xy
    meta = {n["lemma_id"]: n for n in nodes}
    by_label = {n["label"]: n["lemma_id"] for n in nodes}
    W, H = 1.05, 0.62  # nodeboks (dataenheter)

    fig, ax = plt.subplots(figsize=(8.4, 5.6))
    ax.set_xlim(-2.1, 2.1)
    ax.set_ylim(-1.4, 1.55)
    ax.set_aspect("equal")
    ax.axis("off")
    for e in comp["edges"]:
        u, v = by_label[e["u"]], by_label[e["v"]]
        if v == start_lemma_id:
            u, v = v, u
        (x1, y1), (x2, y2) = pos[u], pos[v]
        ax.plot([x1, x2], [y1, y2], color=MUTED, lw=1.2 + 1.8 * (e["n"] - 1), alpha=0.5, zorder=1, solid_capstyle="round")
        # Kanter fra midtnoden: etiketten nær ytternoden; ytterkanter: midt på
        t = 0.58 if u == start_lemma_id else 0.5
        lx, ly = x1 + t * (x2 - x1), y1 + t * (y2 - y1)
        if u != start_lemma_id and abs(y2 - y1) > 0.1:
            # Skrå ytterkanter: etiketten flyttes utover (vekk fra midtnoden), ellers skjules den av midtboksen
            nx, ny = (y2 - y1), -(x2 - x1)
            norm = math.hypot(nx, ny)
            if nx * lx + ny * ly < 0:
                nx, ny = -nx, -ny
            lx, ly = lx + 0.55 * nx / norm, ly + 0.55 * ny / norm
        ax.text(lx, ly, ", ".join(e["shared_forms"]), ha="center", va="center", fontsize=12, style="italic",
                color=INK, zorder=3, bbox={"boxstyle": "round,pad=0.25", "fc": "white", "ec": GRID, "lw": 0.8})
    for lid, (x, y) in pos.items():
        n = meta[lid]
        gf, rest = n["label"].split(" (", 1)
        pos_name = POS_LABEL.get(rest.split(",")[0], rest.split(",")[0])
        anchors = n["unambiguous_forms"]
        # Partisipp/adjektiviske former (-ende, -ede, -ete) er ikke kjerneformer; vis dem bare om de er alt som finnes
        core = [f for f in anchors if not f.endswith(("ende", "ede", "ete"))] or anchors
        is_start = lid == start_lemma_id
        w = W * (1.45 if len(", ".join(core)) > 14 else 1.0)
        ax.add_patch(FancyBboxPatch((x - w / 2, y - H / 2), w, H, boxstyle="round,pad=0.02,rounding_size=0.08",
                                    fc=INK if is_start else "#EEF0F4", ec=INK if is_start else GRID, lw=1, zorder=4))
        main, sub = ("white", "#D9DCE3") if is_start else (INK, MUTED)
        ax.text(x, y + 0.15, gf, ha="center", va="center", fontsize=17, fontweight="bold", color=main, zorder=5)
        ax.text(x, y - 0.04, pos_name, ha="center", va="center", fontsize=11, color=sub, zorder=5)
        if anchors:
            ax.text(x, y - 0.2, ", ".join(core), ha="center", va="center", fontsize=11, color=main, zorder=5)
        else:
            ax.text(x, y - 0.2, "–", ha="center", va="center", fontsize=11, color=sub, zorder=5)
    fig.text(0.5, 0.02, "I boksene: former bare dette lemmaet har (ankre). På linjene: delte former; tykkelse = antall.",
             ha="center", fontsize=10.5, color=MUTED)
    out = OUT_DIR / "paradigmegraf_fisker.png"
    fig.savefig(out)
    plt.close(fig)
    return out

LEX_LABEL = {("dør", "subst"): "en dør", ("dø", "verb"): "å dø", ("tro", "subst"): "en tro",
             ("tro", "verb"): "å tro", ("trå", "verb"): "å trå (pret.)"}
LEX_COLOR = {"subst": FORM_COLOR["pres"], "verb": FORM_COLOR["inf"], "annet": FORM_COLOR["pret"]}


def fig_time_decomposition(forms: tuple[str, ...] = ("dør", "tro")) -> Path:
    """Leksemandel av hver form per år (5-årig glidende snitt), linje = anslag, bånd = 80 %-intervall."""
    from sqlite.tidsserie import MIN_SHARE, decompose_over_time, summary

    fig, axes = plt.subplots(1, len(forms), figsize=(6.2 * len(forms), 4.6), sharey=True)
    for ax, form in zip(np.atleast_1d(axes), forms):
        res = decompose_over_time(form)
        print(summary(res))
        yrs = np.array(res["years"])
        verbs_seen = 0
        ends = []
        for i, c in enumerate(res["candidates"]):
            if res["share"][i].max() < MIN_SHARE:
                continue
            kind = c["pos"] if c["pos"] == "subst" else "verb"
            if kind == "verb":
                verbs_seen += 1
                kind = "verb" if verbs_seen == 1 else "annet"
            col = LEX_COLOR[kind]
            ax.fill_between(yrs, 100 * res["lo"][i], 100 * res["hi"][i], color=col, alpha=0.13, lw=0)
            ax.plot(yrs, 100 * res["share"][i], color=col, lw=2.2)
            ends.append([100 * res["share"][i][-1], LEX_LABEL.get((c["grunnform"], c["pos"]), c["label"]), col])
        ends.sort(key=lambda e: e[0])
        for k in range(1, len(ends)):  # etiketter minst 7 pp fra hverandre
            ends[k][0] = max(ends[k][0], ends[k - 1][0] + 7)
        for y, lab, col in ends:
            ax.text(yrs[-1] + 1.5, y, lab, color=col, fontsize=12, fontweight="bold", va="center")
        ax.set_title(f"«{form}»", fontsize=15, loc="left", color=INK)
        ax.set_xlim(yrs[0], yrs[-1] + 16)
        ax.set_ylim(0, 100)
        ax.set_xticks([1950, 1970, 1990, 2010])
        ax.yaxis.grid(True, color=GRID, lw=0.8)
        ax.set_axisbelow(True)
    np.atleast_1d(axes)[0].set_ylabel("andel av ordformen (%)")
    fig.text(0.01, -0.02, "Linje: anslag. Bånd: 80 % usikkerhet i nivået (profilen til ordet). Endringen over tid er "
             "langt sikrere enn nivået. Bokkorpuset, 5-årig glidende snitt.", fontsize=10, color=MUTED)
    out = OUT_DIR / "dor_tro_over_tid.png"
    fig.savefig(out)
    plt.close(fig)
    return out


def fig_methods_over_time() -> Path:
    """Verbandel per år for «dør» og «tro»: bigrammer (heltrukket, bånd = empirisk 80 %-avvik) og paradigmet (stiplet)."""
    from sqlite.bigram_kontekst import EXAMPLES, cue_rates, decompose_residual
    from sqlite.kombinert import BIGRAM_ERR_PP
    from sqlite.tidsserie import decompose_over_time

    rates = cue_rates()
    obt = {"dør": 0.52, "tro": 0.60 / 0.88}  # OBT-verbandel av substantiv + verb (tro: 60 av 88)
    verb_of = {"dør": "dø", "tro": "tro"}
    fig, axes = plt.subplots(1, 2, figsize=(12.4, 4.6), sharey=True)
    for ax, form in zip(axes, ("dør", "tro")):
        b = decompose_residual(form, EXAMPLES[form], rates)
        par = decompose_over_time(form)
        yrs = np.array(b["years"])
        vb = 100 * _smooth5(b["verb_share_t"])
        half = BIGRAM_ERR_PP["jevne"][1]
        ax.fill_between(yrs, np.clip(vb - half, 0, 100), np.clip(vb + half, 0, 100), color=FORM_COLOR["inf"], alpha=0.12, lw=0)
        ax.plot(yrs, vb, color=FORM_COLOR["inf"], lw=2.4)
        idx = {(c["grunnform"], c["pos"]): i for i, c in enumerate(par["candidates"])}
        iv, i_n = idx[(verb_of[form], "verb")], idx[(form, "subst")]
        vp = 100 * par["share"][iv] / (par["share"][iv] + par["share"][i_n])
        ax.plot(yrs, vp, color=MUTED, lw=1.6, ls="--")
        ax.hlines(100 * obt[form], yrs[0], yrs[-1], color=INK, lw=0.8, ls=":")
        ax.text(yrs[-1] + 1.5, vb[-1], "bigram", color=FORM_COLOR["inf"], fontsize=12, fontweight="bold", va="center")
        gap = vp[-1] - vb[-1]
        y_par = vp[-1] if abs(gap) >= 7 else vb[-1] + (7 if gap >= 0 else -7)
        ax.text(yrs[-1] + 1.5, y_par, "paradigme", color=MUTED, fontsize=11, va="center")
        ax.text(yrs[0] + 1, 100 * obt[form] + 2.5, "tagget korpus (OBT)", color=INK, fontsize=9.5)
        ax.set_title(f"«{form}»: andel å {verb_of[form]}", fontsize=15, loc="left", color=INK)
        ax.set_xlim(yrs[0], yrs[-1] + 15)
        ax.set_ylim(0, 100)
        ax.set_xticks([1950, 1970, 1990, 2010])
        ax.yaxis.grid(True, color=GRID, lw=0.8)
        ax.set_axisbelow(True)
    axes[0].set_ylabel("verbandel av formen (%)")
    fig.text(0.01, -0.02, "Bigram: verbet anslått fra «å/kan/vil … tro» og «jeg/han/som/det … dør», resten er substantiv. "
             "Bånd: ±29 pp, typisk avvik mot OBT for jevnt fordelte former. 5-årig glidende snitt.", fontsize=10, color=MUTED)
    out = OUT_DIR / "dor_tro_metoder.png"
    fig.savefig(out)
    plt.close(fig)
    return out


def _smooth5(v):
    v = np.asarray(v, float)
    return np.convolve(np.pad(v, 2, mode="edge"), np.ones(5) / 5, mode="valid")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    verbs = load_verbs()
    print(f"Skrev {fig_ternary(verbs)}")
    print(f"Skrev {fig_stability(verbs)}")
    print(f"Skrev {fig_fisker()}")
    print(f"Skrev {fig_paradigm_graph()}")
    print(f"Skrev {fig_time_decomposition()}")
    print(f"Skrev {fig_methods_over_time()}")


if __name__ == "__main__":
    main()
