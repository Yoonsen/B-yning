#!/usr/bin/env python3
"""
Hva står foran infinitivene? Profil over infinitivstyrere og utviklingen 1950–2020 (logg del 61).

    python3 -m sqlite.infinitiv_styrere

Utforskende. For de N_VERBS hyppigste entydige verbene (Sett A) henter vi bigrammet «styrer + infinitiv»
fra NB N-gram for hvert ord i STYRERE, og infinitiv-, presens- og preteritumsformene som unigram.

Måltall:
  - profil: andel av de styrte infinitivene som står etter hvert styringsord (hele perioden og per tiår);
  - dekning: andel av alle infinitivforekomster som står rett etter et av styringsordene;
  - infinitivandel: inf / (inf + pres + pret) per tiår, for å se om infinitiven går ned samtidig.
Bare naboposisjon telles: «vil ikke gå» og «skal vi gå» mangler, så dekningen er et nedre anslag.
"""

from collections import defaultdict
from pathlib import Path

import numpy as np

from sqlite.ngram import fetch_nb_ngram
from sqlite.queries import get_conn

PERIOD = (1950, 2020)
N_VERBS = 60
STYRERE = {
    "å": "å",
    "modal, presens": ["kan", "vil", "skal", "må", "bør", "får", "tør"],
    "modal, preteritum": ["kunne", "ville", "skulle", "måtte", "burde", "fikk", "torde"],
    "la/lot": ["la", "lot"],
}
ALL = ["å"] + STYRERE["modal, presens"] + STYRERE["modal, preteritum"] + STYRERE["la/lot"]
OUT_TSV = Path(__file__).resolve().parent.parent / "resultater" / "infinitiv_styrere.tsv"


def gold_verbs() -> list[dict]:
    from sqlite.verbtyper import load_verbs, select_sets

    verbs = select_sets(load_verbs(get_conn()))[0]["580"]
    verbs = sorted(verbs, key=lambda d: -sum(d["nb_slot"].values()))
    out = []
    for d in verbs:
        f = {s: list(d["forms"][s]) for s in (1, 2, 4)}
        if len(f[1]) == 1:
            out.append({"grunnform": d["grunnform"], "inf": f[1][0], "pres": f[2], "pret": f[4]})
        if len(out) == N_VERBS:
            break
    return out


def run() -> dict:
    verbs = gold_verbs()
    terms = ALL + [v["inf"] for v in verbs] + [w for v in verbs for w in v["pres"] + v["pret"]]
    terms += [f"{g} {v['inf']}" for v in verbs for g in ALL]
    ser = fetch_nb_ngram(terms, period=PERIOD)
    years = list(range(PERIOD[0], PERIOD[1] + 1))
    arr = lambda t: np.array([ser[t][y] for y in years])  # noqa: E731
    inf = sum(arr(v["inf"]) for v in verbs)
    pres = sum(arr(w) for v in verbs for w in v["pres"])
    pret = sum(arr(w) for v in verbs for w in v["pret"])
    gov = {g: sum(arr(f"{g} {v['inf']}") for v in verbs) for g in ALL}
    per_verb = {v["grunnform"]: {g: float(arr(f"{g} {v['inf']}").sum()) for g in ALL} | {"inf": float(arr(v["inf"]).sum())}
                for v in verbs}
    return {"years": years, "inf": inf, "pres": pres, "pret": pret, "gov": gov, "per_verb": per_verb,
            "unigram": {g: arr(g) for g in ALL}, "verbs": verbs}


def decade(v: np.ndarray, years: list[int]) -> dict[int, float]:
    out = defaultdict(float)
    for y, x in zip(years, v):
        out[min(y // 10 * 10, 2010)] += x
    return dict(out)


def report(res: dict) -> None:
    years, gov, inf = res["years"], res["gov"], res["inf"]
    total_gov = sum(gov[g].sum() for g in ALL)
    print(f"{len(res['verbs'])} verb; {inf.sum():,.0f} infinitivforekomster, {total_gov:,.0f} rett etter et styringsord "
          f"({100 * total_gov / inf.sum():.0f} %)\n")
    print("Profil (andel av de styrte infinitivene, hele perioden) og endring 1950-tallet → 2010-tallet:")
    dec_tot = {d: sum(decade(gov[g], years)[d] for g in ALL) for d in decade(inf, years)}
    rows = []
    for g in sorted(ALL, key=lambda g: -gov[g].sum()):
        dg = decade(gov[g], years)
        s50, s10 = dg[1950] / dec_tot[1950], dg[2010] / dec_tot[2010]
        per_inf50, per_inf10 = dg[1950] / decade(inf, years)[1950], dg[2010] / decade(inf, years)[2010]
        rows.append((g, gov[g].sum() / total_gov, s50, s10, per_inf50, per_inf10))
        print(f"  {g:7s} {100 * gov[g].sum() / total_gov:5.1f} %   {100 * s50:5.1f} → {100 * s10:5.1f} %   "
              f"(per 100 infinitiver: {100 * per_inf50:4.1f} → {100 * per_inf10:4.1f})")
    di, dp, dr = decade(inf, years), decade(res["pres"], years), decade(res["pret"], years)
    print("\nInfinitivandel inf / (inf + pres + pret) og dekning per tiår:")
    for d in sorted(di):
        print(f"  {d}-tallet: infinitiv {100 * di[d] / (di[d] + dp[d] + dr[d]):4.1f} %, "
              f"styrt rett etter styringsord {100 * dec_tot[d] / di[d]:4.1f} %")
    OUT_TSV.parent.mkdir(exist_ok=True)
    with OUT_TSV.open("w", encoding="utf-8") as f:
        f.write("styrer\tandel_hele\tandel_1950\tandel_2010\tper_inf_1950\tper_inf_2010\n")
        for r in rows:
            f.write("\t".join([r[0]] + [f"{x:.4f}" for x in r[1:]]) + "\n")


def figure(res: dict) -> Path:
    """Venstre: styrte infinitiver per 100 infinitiver per tiår, etter gruppe. Høyre: infinitivandel per tiår."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from sqlite.figurer import FORM_COLOR, GRID, INK, MUTED, OUT_DIR

    years = res["years"]
    di = decade(res["inf"], years)
    decs = sorted(di)
    groups = {"å": ["å"], "modal i presens": STYRERE["modal, presens"], "modal i preteritum": STYRERE["modal, preteritum"]}
    colors = {"å": FORM_COLOR["inf"], "modal i presens": FORM_COLOR["pres"], "modal i preteritum": FORM_COLOR["pret"]}
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.4, 4.4), gridspec_kw={"width_ratios": [1.5, 1]})
    for name, gs in groups.items():
        v = [100 * sum(decade(res["gov"][g], years)[d] for g in gs) / di[d] for d in decs]
        a1.plot(decs, v, color=colors[name], lw=2.4, marker="o", ms=5)
        a1.text(decs[-1] + 2, v[-1], name, color=colors[name], fontsize=12, fontweight="bold", va="center")
    a1.set_title("Infinitiver rett etter styringsord, per 100 infinitiver", fontsize=13, loc="left", color=INK)
    a1.set_xlim(decs[0] - 2, decs[-1] + 25)
    a1.set_ylim(0, 45)
    dp, dr = decade(res["pres"], years), decade(res["pret"], years)
    share = [100 * di[d] / (di[d] + dp[d] + dr[d]) for d in decs]
    a2.plot(decs, share, color=INK, lw=2.4, marker="o", ms=5)
    a2.set_title("Infinitivandel av inf + pres + pret", fontsize=13, loc="left", color=INK)
    a2.set_ylim(30, 40)
    for ax in (a1, a2):
        ax.set_xticks(decs)
        ax.set_xticklabels([f"{d}-" for d in decs], fontsize=10)
        ax.yaxis.grid(True, color=GRID, lw=0.8)
        ax.set_axisbelow(True)
    fig.text(0.01, -0.03, f"De {len(res['verbs'])} hyppigste entydige verbene, NB N-gram (bøker), tiår. Modal i presens: kan, vil, skal, "
             "må, bør, får, tør. I preteritum: kunne, ville, skulle, måtte, burde, fikk, torde. Bare naboposisjon.",
             fontsize=9.5, color=MUTED)
    out = OUT_DIR / "infinitiv_styrere.png"
    fig.savefig(out)
    plt.close(fig)
    return out


if __name__ == "__main__":
    res = run()
    report(res)
    print(f"Skrev {figure(res)}")
