#!/usr/bin/env python3
"""
Diagrammene i MONS-decket som PNG (Keynote viser ikke pptxgenjs-diagrammer; logg.md del 78–79).

    python3 -m sqlite.deck_figurer

Tallene er de samme som stod i addChart-kallene i tekst/deck/build_master.js; kilden til hvert tall
står i talernotatene til lysbildet. Hver figur lagres i nøyaktig den størrelsen (tommer) den har på
lysbildet, så build_master.js / build_deck.js kan legge den inn med samme x, y, w og h.
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from sqlite.figurer import GRID, INK, MUTED, OUT_DIR

ACC1, ACC2, LIGHT = "#B5482F", "#4F7C7A", "#C9CCD3"
INF, PRES, PRET = "#B5482F", "#3D5A98", "#2A9D8F"

# id: (bredde, høyde, spesifikasjon)
CHARTS = {
    "subst_topp": dict(size=(5.4, 4.6), dir="col", title="Formen på 1. plass, Sett A (N = 5 799)",
                       labels=["ent ub", "ent be", "fl ub", "fl be"],
                       series=[("Andel", [67.1, 16.5, 14.5, 1.9], ACC2)], vmax=80, fmt="{:.1f} %"),
    "bok_verb": dict(size=(5.6, 4.2), dir="col", title="Verb: bøker med bare én form (N = 1 145)",
                     labels=["Global #1", "Global #2", "Global #3"],
                     series=[("Verb", [57.2, 26.1, 16.7], ACC1)], vmax=70, fmt="{:.1f} %", tag="Verb"),
    "bok_subst": dict(size=(5.8, 4.2), dir="col", title="Substantiv: bøker med bare én form (N = 813)",
                      labels=["Global #1", "Global #2", "Global #3", "Global #4"],
                      series=[("Substantiv", [56.0, 32.5, 9.7, 1.8], ACC2)], vmax=70, fmt="{:.1f} %", tag="Substantiv"),
    "dor_profil": dict(size=(7.2, 4.6), dir="col", title="Profilen til verbet dø, bokkorpuset 1950–2020",
                       labels=["inf: dø", "pres: dør", "pret: døde"],
                       series=[("Råtall", [15.1, 20.6, 64.3], LIGHT), ("Etter dekomponering", [17.4, 8.7, 74.0], ACC1)],
                       vmax=85, fmt="{:.1f} %"),
    "dode_profil": dict(size=(7.6, 4.9), dir="col", title="Profilen til dø i bokkorpuset (%)",
                        labels=["Uten korreksjon", "28 % adjektiv (OBT)", "46 % adjektiv\n(høyeste overslag)"],
                        series=[("inf", [17.4, 21.9, 26.3], INF), ("pres", [8.7, 10.9, 13.1], PRES),
                                ("pret", [74.0, 67.2, 60.5], PRET)], vmax=90, fmt="{:.1f} %"),
    "bigram_validering": dict(size=(7.4, 4.8), dir="col", title="Avvik i verbandel fra OBT, 150 substantiv/verb-homografer (pp)",
                              labels=["Paradigme", "Bigram", "Kombinert"],
                              series=[("Median", [9.7, 5.0, 5.4], ACC1), ("80-persentil", [37.4, 14.5, 15.4], LIGHT)],
                              vmax=45, fmt="{:.1f}"),
    "validering": dict(size=(7.4, 4.7), dir="bar",
                       title="Median feil i substantivandel (pp), 3 000 kunstige homografer per type",
                       labels=["fl ub + pres (fisker)", "ent be + pret (landet)", "ent ub + inf (fiske)", "ent ub + pres (dør)"],
                       series=[("Faste regler", [13.3, 14.6, 14.4, 16.8], LIGHT), ("Log-regresjon", [11.0, 11.5, 10.5, 10.1], ACC1)],
                       vmax=20, fmt="{:.1f}"),
    "obt_avvik": dict(size=(7.4, 4.8), dir="bar", title="Median avvik fra OBT, paradigmemetoden (pp), 4 170 flertydige former",
                      labels=["Alle kandidater modellert", "… og godt grunnlag", "Alle innholdsord", "Minst én kandidat umodellert"],
                      series=[("Median avvik", [10.4, 9.6, 16.5, 50.0], [ACC2, ACC2, ACC2, ACC1])], vmax=60, fmt="{:.1f}"),
    "stabilitet_obt": dict(size=(7.6, 4.9), kind="line", title="Andel av lemmaets kjerneformer per tiår, bøker (%), OBT-fordeling per tiår",
                           labels=["1950", "1960", "1970", "1980", "1990", "2000", "2010", "2020"],
                           series=[("krone: ubestemt flertall", [81, 82, 85, 88, 89, 89, 90, 89], ACC2),
                                   ("dør: bestemt entall", [71, 69, 68, 65, 68, 72, 76, 75], ACC1),
                                   ("gå: preteritum", [41, 38, 34, 33, 33, 34, 38, 39], PRES),
                                   ("sette: preteritum", [32, 24, 20, 16, 22, 19, 29, 34], PRET)], vmax=100),
}


def _bars(ax, spec):
    labels, series = spec["labels"], spec["series"]
    n, k = len(labels), len(series)
    width = 0.72 / k if k > 1 else 0.6
    pos = np.arange(n)
    horiz = spec["dir"] == "bar"
    for j, (name, vals, color) in enumerate(series):
        off = (j - (k - 1) / 2) * width
        if horiz:
            bars = ax.barh(pos + off, vals, height=width * 0.92, color=color, label=name)
        else:
            bars = ax.bar(pos + off, vals, width=width * 0.92, color=color, label=name)
        for b, v in zip(bars, vals):
            txt = spec["fmt"].format(v).replace(".", ",")
            if horiz:
                ax.text(v + spec["vmax"] * 0.015, b.get_y() + b.get_height() / 2, txt, va="center", fontsize=11, color=INK)
            else:
                ax.text(b.get_x() + b.get_width() / 2, v + spec["vmax"] * 0.015, txt, ha="center", va="bottom", fontsize=11, color=INK)
    if horiz:
        ax.set_yticks(pos, labels, fontsize=12)
        ax.invert_yaxis()
        ax.set_xlim(0, spec["vmax"])
        ax.set_xticks([])
        ax.spines["bottom"].set_visible(False)
        ax.spines["left"].set_color(GRID)
        ax.tick_params(axis="y", length=0, colors=MUTED)
    else:
        ax.set_xticks(pos, labels, fontsize=12)
        ax.set_ylim(0, spec["vmax"])
        ax.set_yticks([])
        ax.spines["left"].set_visible(False)
        ax.spines["bottom"].set_color(GRID)
        ax.tick_params(axis="x", length=0, colors=MUTED)


def _lines(ax, spec):
    x = np.arange(len(spec["labels"]))
    for name, vals, color in spec["series"]:
        ax.plot(x, vals, color=color, lw=2.5, marker="o", ms=5, label=name)
    ax.set_xticks(x, spec["labels"], fontsize=11)
    ax.set_ylim(0, spec["vmax"])
    ax.set_yticks(range(0, spec["vmax"] + 1, 20), [f"{v} %" for v in range(0, spec["vmax"] + 1, 20)], fontsize=11)
    ax.yaxis.grid(True, color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    ax.spines["left"].set_visible(False)
    ax.tick_params(length=0, colors=MUTED)


def render(cid: str):
    spec = CHARTS[cid]
    w, h = spec["size"]
    fig, ax = plt.subplots(figsize=(w, h))
    (_lines if spec.get("kind") == "line" else _bars)(ax, spec)
    # Ingen tittel i figuren (lysbildet har overskrift); tittelen brukes som alt-tekst i decket
    if spec.get("tag"):  # kort etikett når to diagrammer står side om side
        ax.text(0.98, 0.97, spec["tag"], transform=ax.transAxes, ha="right", va="top", fontsize=15, fontweight="bold",
                color=spec["series"][0][2])
    legend = len(spec["series"]) > 1
    if legend:
        ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12 if spec.get("kind") != "line" and spec["dir"] == "col" else -0.08),
                  ncol=2 if len(spec["series"]) > 3 else len(spec["series"]), frameon=False, fontsize=11)
    fig.tight_layout()
    out = OUT_DIR / f"deck_{cid}.png"
    fig.savefig(out, dpi=200, bbox_inches=None)  # fast størrelse = feltet på lysbildet
    plt.close(fig)
    return out


# Semantiske klasser (Norsk ordvev) × profil i det OBT-taggede bokkorpuset (logg.md del 82–84).
# Entall i blågrønt, flertall i rust; ubestemt mørk, bestemt lys.
SEM_CLASSES = ["kroppsdel", "sted/bygning", "gjenstand", "person", "substans", "hendelse", "tid", "egenskap"]
SEM_CELLS = [("ent ub", "#4F7C7A"), ("ent be", "#A9C4C1"), ("fl ub", "#B5482F"), ("fl be", "#E3AE9E")]


def render_semantic(size=(7.6, 4.9)):
    import csv
    from collections import defaultdict

    from sqlite.figurer import ROOT

    groups = defaultdict(list)
    with (ROOT / "resultater" / "ordvev_klasser_obt.tsv").open(encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            groups[r["klasse"]].append([float(r[k]) for k in ("ent_ub", "ent_be", "fl_ub", "fl_be")])
    data = {c: np.mean(groups[c], axis=0) * 100 for c in SEM_CLASSES}
    order = sorted(SEM_CLASSES, key=lambda c: -(data[c][1] + data[c][3]))  # mest bestemt øverst
    fig, ax = plt.subplots(figsize=size)
    y = np.arange(len(order))
    left = np.zeros(len(order))
    for j, (name, color) in enumerate(SEM_CELLS):
        vals = np.array([data[c][j] for c in order])
        ax.barh(y, vals, left=left, height=0.72, color=color, edgecolor="white", linewidth=1.5, label=name)
        for yi, (l, v) in enumerate(zip(left, vals)):
            if v >= 7:
                ax.text(l + v / 2, yi, f"{v:.0f}", ha="center", va="center", fontsize=11,
                        color="white" if j in (0, 2) else INK)
        left += vals
    ax.set_yticks(y, [f"{c}  ({len(groups[c])})" for c in order], fontsize=12)
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xticks([])
    for sp in ("top", "right", "bottom", "left"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(axis="y", length=0, colors=INK)
    ax.legend(loc="lower center", bbox_to_anchor=(0.45, 1.0), ncol=4, frameon=False, fontsize=11, handlelength=1.2)
    fig.tight_layout()
    out = OUT_DIR / "deck_semantiske_klasser.png"
    fig.savefig(out, dpi=200, bbox_inches=None)
    plt.close(fig)
    return out, {c: (len(groups[c]), data[c].round(1).tolist()) for c in order}


# «lærer» mellom to paradigmer (logg.md del 86). Tall fra
# decomposer.estimate_wordform_shares("lærer", corpus="book") med OBT-fordeling av delte ankre,
# bokkorpuset 1950–2020; taggeren er obt_typer i korpus/obt_frekvenser.db (lære verb 311, lærer subst 253
# inkl. «Lærer», lære subst 44 av 608).
LAERER = {
    "anchors": [  # (kandidat, farge, [(ankerform, forekomster)], anslag x̂)
        ("å lære (verb)", ACC1, [("lærte", 392_030), ("lært", 608_873)], 252_717),
        ("en lærer (subst.)", ACC2, [("læreren", 501_966), ("lærere", 706_402), ("lærerne", 393_113)], 229_908),
        ("lære (subst., «doktrine»)", LIGHT, [("lærene", 15_418)], 51_496),
    ],
    "tagger": [51.2, 41.6, 7.2],
}


def render_laerer(size=(12.1, 3.7)):
    import matplotlib.gridspec as gs

    fig = plt.figure(figsize=size)
    g = gs.GridSpec(1, 2, width_ratios=[1.25, 1], wspace=0.35)
    # 1) Ankrene: summen av de entydige formene i hvert paradigme
    ax = fig.add_subplot(g[0])
    cands = LAERER["anchors"]
    for i, (name, color, forms, x_hat) in enumerate(cands):
        left = 0
        for j, (f, n) in enumerate(forms):
            v = n / 1e6
            ax.barh(i, v, left=left, height=0.62, color=color, alpha=1 - 0.28 * j, edgecolor="white", linewidth=2)
            if v > 0.25:
                ax.text(left + v / 2, i, f, ha="center", va="center", fontsize=11, style="italic",
                        color="white" if color != LIGHT else INK)
            left += v
        rho = x_hat / (left * 1e6)
        ax.text(left + 0.04, i, f"{left:.2f}".replace(".", ",") + f" mill.  × ρ {rho:.2f}".replace("0.", "0,").replace("3.", "3,")
                + f"  = {round(x_hat, -3) / 1e3:.0f} 000", va="center", fontsize=11, color=INK)
    ax.set_yticks(range(len(cands)), [c[0] for c in cands], fontsize=12)
    ax.invert_yaxis()
    ax.set_xlim(0, 2.75)
    ax.set_xticks([])
    ax.tick_params(axis="y", length=0, colors=INK)
    for sp in ("top", "right", "bottom", "left"):
        ax.spines[sp].set_visible(False)
    ax.set_title("1  Ankrene i hvert paradigme (bøker, forekomster) × typisk forhold ρ", loc="left", fontsize=13, color=INK, pad=10)
    # 2) Anslaget: x̂ = ρ · R, normert til andeler, mot taggeren
    ax2 = fig.add_subplot(g[1])
    est = np.array([c[3] for c in cands], float)
    rows = [("Paradigmet", 100 * est / est.sum()), ("Taggeren (OBT)", np.array(LAERER["tagger"]))]
    for i, (lab, vals) in enumerate(rows):
        left = 0
        for (name, color, _, _), v in zip(cands, vals):
            if v <= 0:
                continue
            ax2.barh(i, v, left=left, height=0.55, color=color, edgecolor="white", linewidth=2)
            if v >= 12:
                ax2.text(left + v / 2, i, f"{v:.0f} %", ha="center", va="center", fontsize=12,
                         color="white" if color != LIGHT else INK, fontweight="bold")
            left += v
    ax2.set_yticks([0, 1], [r[0] for r in rows], fontsize=12)
    ax2.invert_yaxis()
    ax2.set_xlim(0, 100)
    ax2.set_ylim(1.6, -0.6)
    ax2.set_xticks([])
    ax2.tick_params(axis="y", length=0, colors=INK)
    for sp in ("top", "right", "bottom", "left"):
        ax2.spines[sp].set_visible(False)
    ax2.set_title("2  Anslaget for «lærer»", loc="left", fontsize=13, color=INK, pad=10)
    fig.subplots_adjust(left=0.17, right=0.98, top=0.86, bottom=0.06)
    out = OUT_DIR / "deck_laerer.png"
    fig.savefig(out, dpi=200, bbox_inches=None)
    plt.close(fig)
    return out


if __name__ == "__main__":
    print(render_laerer())
    for cid in CHARTS:
        print(render(cid))
    print(render_semantic())
