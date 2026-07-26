"""BNP till marknadspris ur nationalräkenskaperna (NR0103).

Läser försörjningsbalansen från användningssidan (t.ex. tabell
NR0103...T01, \"BNP från användningssidan\") och plockar ut BNP till
marknadspris i löpande priser för målåret. Därmed blir BNP ett hämtat
tal i stället för en inmatad konstant, och hela procent-av-BNP-kedjan
vilar på SCB-data.
"""
from __future__ import annotations

import pandas as pd

from scb_io import load_pxweb, year_column, year_of, contains

# Etiketter som identifierar BNP-raden i försörjningsbalansen.
BNP_LABELS = ("bruttonationalprodukt", "bnp till marknadspris", "bnp/marknadspris")


def compute(path: str, year: int) -> float:
    df = load_pxweb(path)
    yc = year_column(df)
    innehall = next((c for c in df.columns if "innehåll" in c.lower()), None)

    mask = df[yc].map(year_of).eq(year)
    if innehall is not None:
        mask &= contains(df[innehall], "löpande")

    dim_cols = [c for c in df.columns if c not in ("value", yc, innehall)]
    bnp_mask = pd.Series(False, index=df.index)
    for c in dim_cols:
        bnp_mask |= contains(df[c], *BNP_LABELS)

    sel = df[mask & bnp_mask]
    if sel.empty:
        raise ValueError("Hittade ingen BNP-rad (löpande priser) för året "
                         f"{year} -- kontrollera tabell/etiketter.")
    # Om flera rader matchar (t.ex. flera innehållsvarianter) är BNP till
    # marknadspris det största beloppet.
    return float(sel["value"].max())
