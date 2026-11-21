#!/usr/bin/env python3
"""
Leksemandeler for en flertydig ordform over tid, med usikkerhetsbånd (bokkorpuset 1950–2020).

    python3 -m sqlite.tidsserie dør tro

Brukstilfellet: en bruker ser bøyningsparadigmet til et ord i en ordbok og vil se kurven for ordet,
ikke for overflateformen. «dør» er både substantivet *dør* og presens av *dø*; kurven for «dør» i
n-grammene må deles.

Metode (se `rapport_dekomponering_tid.md`):
1. `decomposer.estimate_wordform_shares(form, corpus="book")` anslår for hele perioden hvor mange
   forekomster hvert kandidatleksem står for (x̂ᵢ), ut fra resten av paradigmet (komplementet Rᵢ).
   Delte former i komplementet fordeles etter det OBT-taggede korpuset (`obt_anchor_split`).
2. Antakelsen om stabile profiler: forholdet ρᵢ = x̂ᵢ / Rᵢ er det samme hvert år. Da er
   xᵢ(t) = ρᵢ · Rᵢ(t), og andelen er xᵢ(t) / Σⱼ xⱼ(t).
3. Usikkerhet: profilen til et enkelt leksem avviker fra den typiske. Hver kandidat får en felles
   faktor exp(σ·z) for hele perioden (z ~ N(0, 1)); σ er kalibrert på de kunstige homografene i
   `resultater/dekomponering_validering.tsv`. Båndet er 10- og 90-persentilen over 2 000 trekninger.
   Variasjon mellom år i båndet kommer bare fra ankrene; antakelsen om stabil profil er ikke testet
   år for år.
"""

import csv
import math
import statistics as st
from pathlib import Path

import numpy as np

import sqlite.decomposer as dec
from sqlite.ngram import fetch_ngram_dhlab
from sqlite.queries import get_conn

ROOT = Path(__file__).resolve().parent.parent
VALIDATION_TSV = ROOT / "resultater" / "dekomponering_validering.tsv"
PERIOD = (1950, 2020)
SEED = 20261121
N_DRAWS = 2000
MIN_SHARE = 0.01  # kandidater under 1 % av formen tas ikke med i figuren


def calibrate_sigma() -> dict[str, float]:
    """σ per kandidat (log-skala) fra feilen i logit-andel for kunstige homografer, per metode."""
    errs: dict[str, list[float]] = {}
    with VALIDATION_TSV.open(encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            t, e = float(r["fasit_subst"]), float(r["anslag_subst"])
            if 0.01 < t < 0.99 and 0.001 < e < 0.999:
                errs.setdefault(r["metode"], []).append(math.log(e / (1 - e)) - math.log(t / (1 - t)))
    out = {}
    for m, xs in errs.items():
        mad = st.median(abs(x - st.median(xs)) for x in xs)
        # Feilen i logit-andel er differansen av to kandidaters feil, derfor / √2
        out[m] = 1.4826 * mad / math.sqrt(2)
    return out


def _smooth(v: np.ndarray, k: int) -> np.ndarray:
    if k <= 1:
        return v
    return np.convolve(np.pad(v, k // 2, mode="edge"), np.ones(k) / k, mode="valid")


def decompose_over_time(form: str, period: tuple[int, int] = PERIOD, smooth: int = 5,
                        use_obt: bool = True, n_draws: int = N_DRAWS) -> dict:
    prev = dec.ANCHOR_SPLIT
    dec.set_anchor_split(dec.obt_anchor_split() if use_obt else None)
    try:
        est = dec.estimate_wordform_shares(form, conn=get_conn(), corpus="book")
    finally:
        dec.set_anchor_split(prev)
    cands = [c for c in est["candidates"] if c["uncapped_est"] > 0]
    years = list(range(period[0], period[1] + 1))
    words = [form] + sorted({w for c in cands for w in c["anchor_weights"]})
    ser = fetch_ngram_dhlab(words, period=period, batch_size=80)
    yearly = {w: np.array([ser.get(w, {}).get(y, 0.0) for y in years], float) for w in words}
    obs = yearly[form]

    sigma = calibrate_sigma()
    raw, info = [], []
    for c in cands:
        r_t = sum(wt * yearly[w] for w, wt in c["anchor_weights"].items())
        r_tot = float(r_t.sum())
        if r_tot > 0:
            x_t = c["uncapped_est"] / r_tot * r_t  # stabil profil: x̂ / R er likt hvert år
        else:  # ingen ankre: samme andel av formen hvert år
            x_t = c["uncapped_est"] / max(obs.sum(), 1.0) * obs
        raw.append(_smooth(x_t, smooth))
        info.append({"label": f"{c['grunnform']} ({c['pos']})", "pos": c["pos"], "grunnform": c["grunnform"],
                     "method": c["method_used"], "sigma": sigma.get(c["method_used"], sigma.get("regler", 1.0))})
    raw = np.array(raw)  # kandidat × år
    total = raw.sum(axis=0)
    share = raw / np.where(total > 0, total, 1)

    rng = np.random.default_rng(SEED)
    sig = np.array([i["sigma"] for i in info])[:, None]
    draws = np.empty((n_draws, *raw.shape))
    for d in range(n_draws):
        mult = np.exp(sig * rng.standard_normal((len(info), 1)))
        x = raw * mult
        draws[d] = x / np.where(x.sum(axis=0) > 0, x.sum(axis=0), 1)
    lo, hi = np.percentile(draws, [10, 90], axis=0)
    # Endring fra første til siste år: usikkerheten i profilen er felles for alle år og faller
    # derfor nesten ut, så endringen er mye sikrere enn nivået
    change = draws[:, :, -1] - draws[:, :, 0]
    ch_lo, ch_hi = np.percentile(change, [10, 90], axis=0)
    return {
        "change": share[:, -1] - share[:, 0], "change_lo": ch_lo, "change_hi": ch_hi,
        "form": form, "years": years, "candidates": info,
        "share": share, "lo": lo, "hi": hi,
        "sum_obs": total / np.where(_smooth(obs, smooth) > 0, _smooth(obs, smooth), 1),
        "obs": _smooth(obs, smooth), "calibration_total": est["calibration"], "sigma": sigma,
    }


def summary(res: dict) -> str:
    y = res["years"]
    idx = [0, len(y) // 2, len(y) - 1]
    lines = [f"«{res['form']}»: sum anslag / observert for hele perioden {res['calibration_total']:.2f}"]
    for i, c in enumerate(res["candidates"]):
        if res["share"][i].max() < MIN_SHARE:
            continue
        parts = [f"{y[j]} {100 * res['share'][i][j]:4.1f} % ({100 * res['lo'][i][j]:.0f}–{100 * res['hi'][i][j]:.0f})" for j in idx]
        lines.append(f"  {c['label']:16s} [{c['method']}, σ={c['sigma']:.2f}]  " + "   ".join(parts)
                     + f"   endring {100 * res['change'][i]:+.1f} pp ({100 * res['change_lo'][i]:+.0f} til {100 * res['change_hi'][i]:+.0f})")
    return "\n".join(lines)


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Leksemandeler for flertydige former over tid.")
    ap.add_argument("ord", nargs="*", default=["dør", "tro"])
    ap.add_argument("--uten-obt", action="store_true", help="ikke bruk OBT til å fordele delte ankerformer")
    a = ap.parse_args()
    for w in a.ord:
        print(summary(decompose_over_time(w, use_obt=not a.uten_obt)))
