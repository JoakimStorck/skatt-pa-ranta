"""Kompositionstabell och marginalskattekil.

Kompositionstabellen är intäktsneutral: totalt skatteuttag hålls
konstant (summan av dagens poster). Konsumtion och kapital/bolag ligger
kvar; markbasen växer enligt läsningen och övervinst/koncession sätts
till en fast liten post. Arbetsskatten är restposten.

Marginalskattekilen räknas ur lagstadgade satser. Reformkolumnerna
sänker arbetsskattens komponenter (arbetsgivaravgift, kommunal och
statlig marginalskatt) i proportion till den andel av arbetsskatten som
frigörs; momsen hålls oförändrad.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class CompositionResult:
    table: pd.DataFrame          # baser (rader) × Nu/läsningar (kolumner)
    arbete: dict                 # läsning -> arbetsskatt, % av BNP
    freed: dict                  # läsning -> frigjord andel av BNP (pp)
    wedge_now: float             # utbudskil i utgångsläget (inkl. moms)
    wedge_reform: dict           # läsning -> utbudskil efter reform
    wedge_now_subst: float       # substitutionsmarginal i utgångsläget (exkl. moms)
    wedge_reform_subst: dict     # läsning -> substitutionsmarginal efter reform


def _wedge(t_k: float, t_s: float, t_c: float, a: float) -> float:
    """Marginell skattekil: (kommunal + statlig + moms på återstoden +
    arbetsgivaravgift) / (1 + arbetsgivaravgift)."""
    return (t_k + t_s + (1 - t_k - t_s) * t_c + a) / (1 + a)


def compute(tax: dict, overvinst_koncession: float,
            mark_by_reading: dict, wedge_rates: dict) -> CompositionResult:
    kons = tax["konsumtion"]
    kap = tax["kapital_bolag"]
    arbete_nu = tax["arbete"]
    mark_nu = tax["mark_idag"]
    total = arbete_nu + kons + kap + mark_nu     # intäktsneutralt tak

    columns = {
        "Nu": {
            "Arbete": arbete_nu,
            "Konsumtion": kons,
            "Kapital och bolag": kap,
            "Mark/läge/natur": mark_nu,
            "Övervinst+koncession": 0.0,
        }
    }
    arbete, freed = {}, {}
    for reading, mark in mark_by_reading.items():
        a = total - kons - kap - mark - overvinst_koncession
        arbete[reading] = a
        freed[reading] = arbete_nu - a
        columns[reading.capitalize()] = {
            "Arbete": a,
            "Konsumtion": kons,
            "Kapital och bolag": kap,
            "Mark/läge/natur": mark,
            "Övervinst+koncession": overvinst_koncession,
        }

    table = pd.DataFrame(columns)
    table.loc["Summa"] = table.sum()

    tk, ts, tc, ar = (wedge_rates["kommunalskatt"], wedge_rates["statlig"],
                      wedge_rates["moms_effekt"], wedge_rates["arbetsgivaravgift"])
    # Utbudskil (arbete vs konsumtion/fritid): momsen ingår.
    wedge_now = _wedge(tk, ts, tc, ar)
    # Substitutionsmarginal (arbete vs automation): momsen utgår på
    # slutprodukten oavsett produktionssätt och ingår därför inte.
    wedge_now_subst = _wedge(tk, ts, 0.0, ar)
    wedge_reform, wedge_reform_subst = {}, {}
    for reading, a in arbete.items():
        share = freed[reading] / arbete_nu     # andel av arbetsskatten som frigörs
        f = 1 - share
        wedge_reform[reading] = _wedge(tk * f, ts * f, tc, ar * f)
        wedge_reform_subst[reading] = _wedge(tk * f, ts * f, 0.0, ar * f)

    return CompositionResult(table, arbete, freed, wedge_now, wedge_reform,
                             wedge_now_subst, wedge_reform_subst)
