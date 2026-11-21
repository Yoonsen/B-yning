#!/usr/bin/env python3
"""
Dekomponering med bigramkontekster (logg del 57).

    python3 -m sqlite.bigram_kontekst tro dør

Idé: noen kontekster forekommer nesten bare med én ordklasse. «en tro» er substantiv, «å tro» er verb.
Vi lærer hvor stor andel av formene til entydige ord som står i slike kontekster (kontekstraten r),
og deler bigramtallene for den flertydige formen på raten:

    x̂ᵢ = B_i / rᵢ        B_i = Σ_c f(c O) over kontekstene c for kandidat i
                         rᵢ  = typisk andel av en form i cellen som står etter c (median over entydige ord)

Samme logikk som paradigmeanslaget (komplement × odds), men med syntaktisk kontekst i stedet for de
andre bøyningsformene. I tillegg gir bigrammene en sikker nedre grense: xᵢ ≥ B_i.

Usikkerhet: rᵢ varierer mellom ord (f.eks. sjelden «en» foran abstrakte substantiv). Spredningen i
log rᵢ blant de entydige ordene gir båndet (10.–90. persentil over trekninger).

Kilde: NB N-gram (api.nb.no/dhlab/nb_ngram), bøker, bokmål, 1950–2020; både uni- og bigrammer derfra.
"""

import math
import statistics as st

import numpy as np

from sqlite.ngram import fetch_nb_ngram
from sqlite.queries import get_conn

PERIOD = (1950, 2020)
N_GOLD = 120  # antall entydige ord per celle som kontekstraten læres på
SEED = 20261121
N_DRAWS = 2000

# Kontekster (ordet foran) som peker på én celle. «den» er utelatt fordi «den tro tjener» er adjektiv.
CUES = {
    ("subst", 1): ["en", "ei", "et", "min", "sin", "din", "vår"],  # ent ub etter ubestemt artikkel/possessiv
    ("verb", 1): ["å", "kan", "vil", "skal", "må"],  # infinitiv
    ("verb", 2): ["jeg", "han", "hun", "vi", "de", "som", "det", "den"],  # presens; det/den lagt til i del 59 (*det dreier seg*)
}
CELL_LABEL = {("subst", 1): "ent ub", ("verb", 1): "inf", ("verb", 2): "pres"}
# Substantiv: kontekstene tilpasses kjønnet (logg del 58). Kjønnsnøytrale eiendomsord gjelder alle.
NOUN_CUES_BY_GENDER = {
    "mask": ["en", "min", "sin", "din", "vår"],
    "fem": ["ei", "en", "mi", "min", "si", "sin", "di", "din", "vår"],  # hunkjønn kan bøyes som hankjønn
    "nøyt": ["et", "mitt", "sitt", "ditt", "vårt"],
}
NOUN_CUES_NEUTRAL = ["hans", "hennes", "deres"]


def noun_gender(grunnform: str, conn=None) -> set[str]:
    conn = conn or get_conn()
    s = " ".join(r[0] for r in conn.execute(
        "SELECT DISTINCT ordklasser FROM lemma_former WHERE grunnform = ? AND pos = 'subst'", (grunnform,)))
    return {g for g in NOUN_CUES_BY_GENDER if g in s} or {"mask"}


def cues_for(cell: tuple[str, int], grunnform: str | None = None) -> list[str]:
    if cell == ("subst", 1) and grunnform is not None:
        return sorted({c for g in noun_gender(grunnform) for c in NOUN_CUES_BY_GENDER[g]} | set(NOUN_CUES_NEUTRAL))
    return CUES.get(cell, [])  # celler uten kontekster (f.eks. subst. fl ub) bidrar ikke med bigrammer


def _total(series: dict[int, float]) -> float:
    return float(sum(series.values()))


def gold_forms(conn=None) -> dict[tuple[str, int], list[str]]:
    """Én entydig form per ord og celle for de N_GOLD hyppigste gullstandardordene."""
    from sqlite.substantivtyper import load_noun_forms, select_gold
    from sqlite.verbtyper import load_verbs, select_sets

    conn = conn or get_conn()
    nouns, _ = select_gold(load_noun_forms(conn))
    verbs = select_sets(load_verbs(conn))[0]["580"]
    out = {("subst", 1): [(next(iter(d["forms"][1])), d["grunnform"]) for d in nouns[:N_GOLD] if len(d["forms"][1]) == 1]}
    verbs = sorted(verbs, key=lambda d: -sum(d["nb_slot"].values()))[:N_GOLD]
    for cell in (1, 2):
        out[("verb", cell)] = [(next(iter(d["forms"][cell])), d["grunnform"]) for d in verbs if len(d["forms"][cell]) == 1]
    return out


def cue_rates() -> dict[tuple[str, int], dict]:
    """Kontekstrate per celle: median og spredning (sd av log r) over entydige ord."""
    out = {}
    for cell, forms in gold_forms().items():
        cue = {w: cues_for(cell, gf) for w, gf in forms}
        terms = [w for w, _ in forms] + [f"{c} {w}" for w, _ in forms for c in cue[w]]
        ser = fetch_nb_ngram(terms, period=PERIOD)
        rates = []
        for w, _ in forms:
            uni = _total(ser[w])
            big = sum(_total(ser[f"{c} {w}"]) for c in cue[w])
            if uni > 0 and big > 0:
                rates.append(big / uni)
        logs = [math.log(r) for r in rates]
        mad = st.median(abs(x - st.median(logs)) for x in logs)
        out[cell] = {"median": st.median(rates), "sd_log": 1.4826 * mad, "n": len(rates),
                     "q": st.quantiles(rates, n=10)}
    return out


def decompose(form: str, cells: list[tuple[str, str, tuple[str, int]]], rates: dict | None = None,
              n_draws: int = N_DRAWS) -> dict:
    """cells: [(etikett, grunnform, (ordklasse, celle)), ...] for kandidatene som kan gi `form`."""
    rates = rates or cue_rates()
    terms = [form] + [f"{c} {form}" for _, gf, cell in cells for c in cues_for(cell, gf)]
    ser = fetch_nb_ngram(terms, period=PERIOD)
    years = list(range(PERIOD[0], PERIOD[1] + 1))
    obs = np.array([ser[form][y] for y in years])
    b = np.array([[sum(ser[f"{c} {form}"][y] for c in cues_for(cell, gf)) for y in years] for _, gf, cell in cells])
    med = np.array([rates[cell]["median"] for _, _, cell in cells])[:, None]
    sd = np.array([rates[cell]["sd_log"] for _, _, cell in cells])[:, None]
    est = b / med
    rng = np.random.default_rng(SEED)
    tot_b, tot_obs = b.sum(axis=1), obs.sum()
    draws_tot, draws_t = [], []
    for _ in range(n_draws):
        r = med * np.exp(sd * rng.standard_normal((len(cells), 1)))
        x = b / r
        draws_t.append(x / np.where(x.sum(axis=0) > 0, x.sum(axis=0), 1))
        xt = tot_b / r[:, 0]
        draws_tot.append(xt / xt.sum())
    draws_tot, draws_t = np.array(draws_tot), np.array(draws_t)
    share_tot = (tot_b / med[:, 0]) / (tot_b / med[:, 0]).sum()
    return {
        "form": form, "years": years, "labels": [c[0] for c in cells], "obs_total": tot_obs,
        "bigram_total": tot_b, "lower_bound": tot_b / tot_obs,
        "share": share_tot, "lo": np.percentile(draws_tot, 10, axis=0), "hi": np.percentile(draws_tot, 90, axis=0),
        "calibration": float((tot_b / med[:, 0]).sum() / tot_obs),
        "share_t": est / np.where(est.sum(axis=0) > 0, est.sum(axis=0), 1),
        "lo_t": np.percentile(draws_t, 10, axis=0), "hi_t": np.percentile(draws_t, 90, axis=0),
    }


def decompose_residual(form: str, cells: list[tuple[str, str, tuple[str, int]]], rates: dict | None = None,
                       n_draws: int = N_DRAWS) -> dict:
    """
    Verbet anslås fra bigrammene (stabil kontekstrate), substantivet (og alt annet) er resten:
        x̂_V = B_V / r_V,   x̂_rest = f(O) − x̂_V   (kappet til [B_V, f(O) − B_rest])
    Brukes når substantivkonteksten er for ustabil (sd log r > 1). Antar én verbkandidat.
    """
    rates = rates or cue_rates()
    vi = [i for i, (_, _, cell) in enumerate(cells) if cell[0] == "verb"]
    assert len(vi) == 1, "decompose_residual antar én verbkandidat"
    vi = vi[0]
    terms = [form] + [f"{c} {form}" for _, gf, cell in cells for c in cues_for(cell, gf)]
    ser = fetch_nb_ngram(terms, period=PERIOD)
    years = list(range(PERIOD[0], PERIOD[1] + 1))
    obs = np.array([ser[form][y] for y in years])
    b = np.array([[sum(ser[f"{c} {form}"][y] for c in cues_for(cell, gf)) for y in years] for _, gf, cell in cells])
    r = rates[cells[vi][2]]
    b_rest = np.delete(b, vi, axis=0).sum(axis=0)

    def verb_share(rate, bv, bo, br):
        xv = np.clip(bv / rate, bv, np.maximum(bo - br, bv))
        return xv / np.where(bo > 0, bo, 1)

    rng = np.random.default_rng(SEED)
    mult = np.exp(r["sd_log"] * rng.standard_normal(n_draws))
    tot = [verb_share(r["median"] * m, b[vi].sum(), obs.sum(), b_rest.sum()) for m in mult]
    per_year = np.array([verb_share(r["median"] * m, b[vi], obs, b_rest) for m in mult])
    return {
        "form": form, "years": years, "verb_label": cells[vi][0], "obs_total": obs.sum(),
        "verb_share": float(verb_share(r["median"], b[vi].sum(), obs.sum(), b_rest.sum())),
        "lo": float(np.percentile(tot, 10)), "hi": float(np.percentile(tot, 90)),
        "lower_bound": float(b[vi].sum() / obs.sum()), "upper_bound": float(1 - b_rest.sum() / obs.sum()),
        "verb_share_t": verb_share(r["median"], b[vi], obs, b_rest),
        "lo_t": np.percentile(per_year, 10, axis=0), "hi_t": np.percentile(per_year, 90, axis=0),
        "change": None,
    }


EXAMPLES = {
    "tro": [("en tro (subst)", "tro", ("subst", 1)), ("å tro (verb)", "tro", ("verb", 1))],
    "dør": [("en dør (subst)", "dør", ("subst", 1)), ("å dø (verb, pres)", "dø", ("verb", 2))],
}


if __name__ == "__main__":
    import sys

    rates = cue_rates()
    print("Kontekstrater (andel av formen som står etter kontekstordene), entydige ord i NB N-gram 1950–2020:")
    for cell, r in rates.items():
        cue_txt = "artikkel/eiendomsord etter kjønn + hans/hennes/deres" if cell == ("subst", 1) else ", ".join(CUES[cell])
        print(f"  {CELL_LABEL[cell]:7s} {cue_txt:38s} median {100 * r['median']:5.1f} %  "
              f"(10.–90. pers. {100 * r['q'][0]:.1f}–{100 * r['q'][-1]:.1f} %, sd log {r['sd_log']:.2f}, N={r['n']})")
    for w in sys.argv[1:] or ["tro", "dør"]:
        res = decompose(w, EXAMPLES[w], rates)
        print(f"\n«{w}»: {res['obs_total']:,.0f} forekomster; sum anslag / observert {res['calibration']:.2f}")
        for i, lab in enumerate(res["labels"]):
            y = res["years"]
            j0, j1 = 0, len(y) - 1
            print(f"  {lab:20s} bigram {res['bigram_total'][i]:>10,.0f} (nedre grense {100 * res['lower_bound'][i]:4.1f} %)  "
                  f"andel {100 * res['share'][i]:5.1f} % ({100 * res['lo'][i]:.0f}–{100 * res['hi'][i]:.0f})  "
                  f"1950 {100 * res['share_t'][i][j0]:4.1f} %  2020 {100 * res['share_t'][i][j1]:4.1f} %")
        rr = decompose_residual(w, EXAMPLES[w], rates)
        y = rr["years"]
        print(f"  Restmetode: {rr['verb_label']} {100 * rr['verb_share']:.1f} % ({100 * rr['lo']:.0f}–{100 * rr['hi']:.0f}); "
              f"sikre grenser fra bigrammene {100 * rr['lower_bound']:.0f}–{100 * rr['upper_bound']:.0f} %; "
              f"1950 {100 * rr['verb_share_t'][0]:.0f} % ({100 * rr['lo_t'][0]:.0f}–{100 * rr['hi_t'][0]:.0f})  "
              f"2020 {100 * rr['verb_share_t'][-1]:.0f} % ({100 * rr['lo_t'][-1]:.0f}–{100 * rr['hi_t'][-1]:.0f})")

