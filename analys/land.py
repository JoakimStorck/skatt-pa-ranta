"""Markförmögenheten ur fastighetstaxeringen.

Taxeringsvärdet motsvarar 75 procent av marknadsvärdet, så markvärde
dividerat med 0,75 ger markförmögenheten i marknadsvärde.

Lantbrukets mark- och naturvärde tas exakt ur delvärdestabellen
(skog, jordbruk, tomtmark). För bebyggda enheter (småhus,
hyreshus/industri) redovisar SCB bara totalt taxeringsvärde, så
markandelen av den bebyggda delen är den enda kvarvarande
antagandeparametern.

    markförmögenhet = (lantbruk_mark + markandel * bebyggt_taxv) / 0,75
    årlig markränta  = r * markförmögenhet
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from scb_io import load_pxweb, col_like, year_column, year_of, latest_year, contains

# Delvärden i lantbrukstabellen som utgör mark-/naturvärde.
LANTBRUK_LAND = ("skogsmark", "skogsimpediment", "jordbruksvärde", "tomtmarksvärde")

TAXV_TO_MARKET = 0.75  # taxeringsvärde = 75 % av marknadsvärde


@dataclass
class LandResult:
    lantbruk_year: int
    smahus_year: int
    hyres_year: int
    lantbruk_mark_mnkr: float
    smahus_mnkr: float
    hyres_mnkr: float
    bebyggt_mnkr: float
    bnp_mnkr: float
    r: float
    table: pd.DataFrame   # per markandel: markförmögenhet, x_bnp, markränta%


def compute(lantbruk_path, smahus_path, hyres_path, bnp_mnkr, r, markandelar) -> LandResult:
    lant, ly = _riket_latest_sum(load_pxweb(lantbruk_path), LANTBRUK_LAND)
    sma, sy = _riket_latest_sum(load_pxweb(smahus_path), ("totalt taxeringsvärde",))
    hyr, hy = _riket_latest_sum(load_pxweb(hyres_path), ("totalt taxerings",))
    bebyggt = sma + hyr

    rows = []
    for name, andel in markandelar.items():
        taxv = lant + bebyggt * andel
        formogenhet = taxv / TAXV_TO_MARKET
        markranta_pct = 100.0 * r * formogenhet / bnp_mnkr
        rows.append({
            "markandel": name,
            "andel": andel,
            "markformogenhet_mnkr": formogenhet,
            "x_bnp": formogenhet / bnp_mnkr,
            "markranta_andel_bnp_pct": markranta_pct,
        })
    return LandResult(ly, sy, hy, lant, sma, hyr, bebyggt, bnp_mnkr, r, pd.DataFrame(rows))


def _riket_latest_sum(df: pd.DataFrame, content_needles) -> tuple[float, int]:
    """Summera 'value' för riket, senaste år, över de rader vars
    tabellinnehåll matchar content_needles (t.ex. markkomponenter eller
    totalt taxeringsvärde). Summerar över alla ägarkategorier och
    typkoder men bara region = Riket, så inga läns- eller totalrader
    dubbelräknas."""
    region = col_like(df, "region")
    innehall = col_like(df, "tabellinnehåll")
    yc = year_column(df)
    y = latest_year(df, yc)

    sel = (contains(df[region], "riket")
           & (df[yc].map(year_of) == y)
           & contains(df[innehall], *content_needles))
    if not sel.any():
        raise ValueError(f"Inga rader matchar {content_needles} för riket {y}.")
    return df.loc[sel, "value"].sum(), y
