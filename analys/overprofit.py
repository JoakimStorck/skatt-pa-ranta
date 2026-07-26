"""Övervinst-residualen för icke-finansiella bolag (S11).

Metod (Barkai på svenska nationalräkenskaper):

    ren ränta = nettodriftsöverskott (B2n) - r * nettokapitalstock

Nettodriftsöverskottet hämtas ur sektorräkenskaperna (S11, summa över
årets fyra kvartal). Kapitalstocken hämtas ur NR0103: näringslivets
nettostock minus småhusstocken (L68A), som ligger i hushållssektorn och
därför inte hör ihop med S11:s överskott.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from scb_io import load_pxweb, col_like, year_column, year_of, contains


@dataclass
class OverprofitResult:
    year: int
    nos_mnkr: float             # nettodriftsöverskott (B2n), S11
    k_naringsliv_mnkr: float    # nettokapitalstock, näringslivet
    k_smahus_mnkr: float        # småhus (L68A), dras bort
    k_mnkr: float               # K = näringsliv - småhus
    bnp_mnkr: float
    table: pd.DataFrame         # residual per avkastningskrav r


def compute(sektor_path: str, kapital_path: str, bnp_mnkr: float,
            r_values, year: int) -> OverprofitResult:
    nos = _net_operating_surplus_s11(sektor_path, year)
    k_naring, k_smahus = _capital_stock(kapital_path, year)
    K = k_naring - k_smahus

    rows = []
    for r in r_values:
        normal = r * K
        rent = nos - normal
        rows.append({
            "r": r,
            "normal_avkastning_mnkr": normal,
            "ranta_mnkr": rent,
            "ranta_andel_bnp_pct": 100.0 * rent / bnp_mnkr,
        })
    table = pd.DataFrame(rows)
    return OverprofitResult(year, nos, k_naring, k_smahus, K, bnp_mnkr, table)


def _net_operating_surplus_s11(path: str, year: int) -> float:
    df = load_pxweb(path)
    yc = year_column(df)
    sektor = col_like(df, "sektor")
    post = col_like(df, "transaktionspost")

    p = df[post].str.lower()
    # B2n = nettodriftsöverskott. Undvik brutto (B2g) och B3n (blandinkomst).
    is_b2n = (p.str.startswith("b2n")
              | (p.str.contains("driftsöverskott", na=False) & p.str.contains("netto", na=False)))
    is_b2n &= ~(p.str.contains("brutto", na=False)
                | p.str.contains("b3n", na=False)
                | p.str.contains("blandinkomst", na=False)
                | p.str.contains("sammansatt", na=False))

    is_s11 = contains(df[sektor], "s11") | contains(df[sektor], "icke-finansiella")
    is_year = df[yc].map(year_of) == year

    cand = df[is_b2n & is_s11 & is_year]
    if cand.empty:
        raise ValueError("Hittade ingen B2n-rad för S11 -- kontrollera etiketter/år.")

    # Filen innehåller ofta både S11-totalen och delsektorerna (S11001,
    # S11002, S11003), som tillsammans summerar till totalen. Välj enbart
    # totalen -- den kortaste sektoretiketten -- för att inte dubbelräkna.
    sektor_label = min(cand[sektor].unique(), key=len)
    posts = cand.loc[cand[sektor] == sektor_label, post].unique()
    post_label = min(posts, key=len)

    sub = cand[(cand[sektor] == sektor_label) & (cand[post] == post_label)]
    print(f"  [info] B2n-serie: sektor='{sektor_label}', post='{post_label}', "
          f"{len(sub)} kvartal summerade")
    return sub["value"].sum()


def _capital_stock(path: str, year: int):
    df = load_pxweb(path)
    yc = year_column(df)
    ng = col_like(df, "näringsgren")
    slag = col_like(df, "tillgångsslag")
    innehall = col_like(df, "tabellinnehåll")

    base = ((df[yc].map(year_of) == year)
            & contains(df[innehall], "löpande")
            & contains(df[slag], "samtliga fasta"))

    k_naring = df.loc[base & contains(df[ng], "näringslivet totalt"), "value"].sum()
    k_smahus = df.loc[base & contains(df[ng], "l68a"), "value"].sum()
    if k_naring == 0:
        raise ValueError("Hittade inte 'näringslivet totalt' i kapitalstocken.")
    return k_naring, k_smahus
