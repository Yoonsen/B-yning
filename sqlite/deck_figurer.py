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
                     series=[("Verb", [57.2, 26.1, 16.7], ACC1)], vmax=70, fmt="{:.1f} %"),
    "bok_subst": dict(size=(5.8, 4.2), dir="col", title="Substantiv: bøker med bare én form (N = 813)",
                      labels=["Global #1", "Global #2", "Global #3", "Global #4"],
                      series=[("Substantiv", [56.0, 32.5, 9.7, 1.8], ACC2)], vmax=70, fmt="{:.1f} %"),
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
    ax.set_title(spec["title"], fontsize=12.5, color=INK, loc="left", pad=10, wrap=True)
    legend = len(spec["series"]) > 1
    if legend:
        ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12 if spec.get("kind") != "line" and spec["dir"] == "col" else -0.08),
                  ncol=2 if len(spec["series"]) > 3 else len(spec["series"]), frameon=False, fontsize=11)
    fig.tight_layout()
    out = OUT_DIR / f"deck_{cid}.png"
    fig.savefig(out, dpi=200, bbox_inches=None)  # fast størrelse = feltet på lysbildet
    plt.close(fig)
    return out


if __name__ == "__main__":
    for cid in CHARTS:
        print(render(cid))
