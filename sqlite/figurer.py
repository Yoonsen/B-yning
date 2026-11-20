#!/usr/bin/env python3
"""
Figurer til MONS-presentasjonen (tekst/figurer/*.png).

    python3 -m sqlite.figurer

Krever matplotlib (Matplotlib License, BSD-lignende) og numpy. Bruker bokkorpuset
1950–2020 via sqlite/ngram.py (cache i sqlite/ngram_cache.db) og
resultater/verbtyper.tsv (skrives av `python3 -m sqlite.verbtyper`).

1. verb_ternaer.png      – hvert verb i Sett A (N = 580) som et punkt i inf/pres/pret-trekanten
2. verb_stabilitet.png   – andel per form per år for fire stabile verb
3. fisker_over_tid.png   – ordformen «fisker» fordelt på tre leksemer per år
"""

import contextlib
import csv
import io
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
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
    shares, ratio, _ = fisker_yearly()
    fig, ax = plt.subplots(figsize=(7.3, 4.6))
    bottom = np.zeros(len(YEARS))
    for lx, col in LEXEME_COLOR.items():
        ax.fill_between(YEARS, bottom, bottom + shares[lx], color=col, lw=0, alpha=0.9)
        ax.plot(YEARS, bottom + shares[lx], color="white", lw=2)
        mid = bottom + shares[lx] / 2
        i = YEARS.index(1985)
        ax.text(1985, mid[i], f"{lx}", ha="center", va="center", color="white", fontsize=14, fontweight="bold")
        bottom = bottom + shares[lx]
    ax.set_xlim(PERIOD)
    ax.set_ylim(0, 100)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_yticklabels(["0", "25", "50", "75", "100 %"])
    ax.set_xticks([1950, 1960, 1970, 1980, 1990, 2000, 2010, 2020])
    ax.tick_params(length=0)
    for sp in ax.spines.values():
        sp.set_visible(False)
    out = OUT_DIR / "fisker_over_tid.png"
    fig.savefig(out)
    plt.close(fig)
    for lx in LEXEME_COLOR:
        v = shares[lx]
        print(f"  {lx:18s} 1950 {v[0]:5.1f} %  1985 {v[35]:5.1f} %  2020 {v[-1]:5.1f} %  (min {v.min():.1f}, maks {v.max():.1f})")
    print(f"  Sum ukappede estimater / observert «fisker»: median {np.median(ratio):.2f} (spenn {ratio.min():.2f}–{ratio.max():.2f})")
    return out


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    verbs = load_verbs()
    print(f"Skrev {fig_ternary(verbs)}")
    print(f"Skrev {fig_stability(verbs)}")
    print(f"Skrev {fig_fisker()}")


if __name__ == "__main__":
    main()
