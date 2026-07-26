#!/usr/bin/env python3
"""Kör hela skattemodellens analys ur SCB-filerna.

    python run_analysis.py [--data-dir KATALOG]

Läser de fem SCB-filerna (se config.py), räknar
  1) övervinst-residualen,
  2) markförmögenheten,
  3) kompositionstabellen och marginalskattekilen,
skriver en rapport till skärmen och resultatfiler till ./resultat/,
och verifierar de hämtade aggregaten mot de värden vi känner till.
"""
from __future__ import annotations

import argparse
import os
import sys

import pandas as pd

import config as C
import overprofit
import land
import composition
import gdp

pd.set_option("display.width", 100)
pd.set_option("display.max_columns", 20)


def _rule(title=""):
    print("\n" + "=" * 72)
    if title:
        print(title)
        print("=" * 72)


def _have(name: str) -> bool:
    p = C.path(name)
    if not os.path.exists(p):
        print(f"  [VARNING] saknar fil för {name}: {p}")
        return False
    return True


def run() -> dict:
    results: dict = {}

    _rule("Skattemodell -- reproducerbar analys ur SCB-data")
    print(f"Datakatalog : {os.path.abspath(C.DATA_DIR)}")

    # BNP: hämtas ur NR0103-tabellen om den finns, annars konstanten.
    bnp = C.BNP_MNKR
    if os.path.exists(C.path("bnp")):
        try:
            bnp = gdp.compute(C.path("bnp"), C.YEAR_KAPITAL)
            print(f"BNP (hämtad ur NR0103): {bnp/1000:,.0f} mdkr")
        except Exception as e:
            print(f"  [VARNING] kunde inte läsa BNP-tabellen ({e}); använder konstant.")
            print(f"BNP (inmatad konstant): {bnp/1000:,.0f} mdkr")
    else:
        print(f"BNP (inmatad konstant): {bnp/1000:,.0f} mdkr")

    # 1) Övervinst-residual --------------------------------------------------
    if _have("sektorrakenskaper") and _have("kapitalstock"):
        op = overprofit.compute(C.path("sektorrakenskaper"), C.path("kapitalstock"),
                                 bnp, C.R_OVERVINST, C.YEAR_OVERVINST)
        results["overprofit"] = op
        _rule("1) Övervinst-residual -- icke-finansiella bolag (S11)")
        print(f"Nettodriftsöverskott B2n {op.year}: "
              f"{op.nos_mnkr/1000:,.1f} mdkr ({100*op.nos_mnkr/bnp:.1f} % av BNP)")
        print(f"Nettokapitalstock: näringsliv {op.k_naringsliv_mnkr/1000:,.0f} "
              f"- småhus {op.k_smahus_mnkr/1000:,.0f} = K {op.k_mnkr/1000:,.0f} mdkr "
              f"({op.k_mnkr/bnp:.2f}x BNP)")
        show = op.table.copy()
        show["ranta_mdkr"] = show["ranta_mnkr"] / 1000
        print(show[["r", "ranta_mdkr", "ranta_andel_bnp_pct"]]
              .round({"ranta_mdkr": 0, "ranta_andel_bnp_pct": 1}).to_string(index=False))

    # 2) Markförmögenhet -----------------------------------------------------
    if all(_have(n) for n in ("lantbruk", "smahus", "hyreshus_industri")):
        lr = land.compute(C.path("lantbruk"), C.path("smahus"), C.path("hyreshus_industri"),
                          bnp, C.R_MARK, C.MARKANDEL)
        results["land"] = lr
        _rule("2) Markförmögenhet -- fastighetstaxering")
        print(f"Lantbruk mark+natur (taxv, {lr.lantbruk_year}): {lr.lantbruk_mark_mnkr/1000:,.0f} mdkr")
        print(f"Bebyggt totalt taxv: småhus {lr.smahus_mnkr/1000:,.0f} ({lr.smahus_year}) "
              f"+ hyres/industri {lr.hyres_mnkr/1000:,.0f} ({lr.hyres_year}) "
              f"= {lr.bebyggt_mnkr/1000:,.0f} mdkr")
        t = lr.table.copy()
        t["markformogenhet_mdkr"] = t["markformogenhet_mnkr"] / 1000
        print(t[["markandel", "andel", "markformogenhet_mdkr", "x_bnp", "markranta_andel_bnp_pct"]]
              .round({"markformogenhet_mdkr": 0, "x_bnp": 2, "markranta_andel_bnp_pct": 1})
              .to_string(index=False))

        # 3) Komposition + kil -----------------------------------------------
        mark_by = {r: _val(lr.table, r) for r in ("forsiktig", "generos")}
        comp = composition.compute(C.TAX, C.OVERVINST_KONCESSION, mark_by, C.WEDGE)
        results["composition"] = comp
        _rule("3) Kompositionstabell (intäktsneutralt, steg ett) -- % av BNP")
        print(comp.table.round(1).to_string())
        _rule("   Marginalskattekil")
        print("Utbudskil arbete (inkl. moms):")
        print(f"  Nu: {100*comp.wedge_now:.0f} %")
        for reading, w in comp.wedge_reform.items():
            print(f"  {reading.capitalize()}: ~{100*w:.0f} %  "
                  f"(arbete {comp.arbete[reading]:.1f} % av BNP, "
                  f"frigjort {comp.freed[reading]:.1f} pp)")
        print("Substitutionsmarginal arbete/automation (exkl. moms):")
        print(f"  Nu: {100*comp.wedge_now_subst:.0f} %")
        for reading, w in comp.wedge_reform_subst.items():
            print(f"  {reading.capitalize()}: ~{100*w:.0f} %")
        # Kil mot automationskapitalets normalavkastning (~10-15 %).
        a_lo, a_hi = 10.0, 15.0
        def _kil(w):
            return (100*w - a_hi, 100*w - a_lo)
        klo, khi = _kil(comp.wedge_now_subst)
        print(f"Kil människa<->automation: nu ~{(klo+khi)/2:.0f} pp "
              f"({klo:.0f}-{khi:.0f})")
        for reading, w in comp.wedge_reform_subst.items():
            lo, hi = _kil(w)
            print(f"  {reading.capitalize()}: ~{lo:.0f}-{hi:.0f} pp")

    return results


def _val(table: pd.DataFrame, reading: str) -> float:
    return float(table.loc[table["markandel"] == reading, "markranta_andel_bnp_pct"].iloc[0])


# --------------------------------------------------------------------------
# Utdata + verifiering
# --------------------------------------------------------------------------
def write_outputs(results: dict, outdir: str = "resultat") -> None:
    os.makedirs(outdir, exist_ok=True)
    if "overprofit" in results:
        results["overprofit"].table.to_csv(f"{outdir}/overvinst_residual.csv", index=False)
    if "land" in results:
        results["land"].table.to_csv(f"{outdir}/markformogenhet.csv", index=False)
    if "composition" in results:
        results["composition"].table.round(2).to_csv(f"{outdir}/kompositionstabell.csv")
    print(f"\nResultatfiler skrivna till ./{outdir}/")


# Kända aggregat (mnkr) från våra tidigare uttag, för självkontroll.
EXPECTED = {
    "nos": 659_389,
    "K": 12_750_797,
    "lantbruk": 1_385_592,
    "bebyggt": 13_194_328,
}


def verify(results: dict) -> None:
    _rule("Verifiering mot kända värden (mnkr)")
    ok = True
    if "overprofit" in results:
        op = results["overprofit"]
        ok &= _cmp("B2n S11", op.nos_mnkr, EXPECTED["nos"])
        ok &= _cmp("K (näringsliv - småhus)", op.k_mnkr, EXPECTED["K"])
    if "land" in results:
        lr = results["land"]
        ok &= _cmp("Lantbruk mark+natur", lr.lantbruk_mark_mnkr, EXPECTED["lantbruk"])
        ok &= _cmp("Bebyggt taxv", lr.bebyggt_mnkr, EXPECTED["bebyggt"])
    print("Alla kontroller OK." if ok else "OBS: minst en kontroll avvek -- se ovan.")


def _cmp(name: str, got: float, exp: float) -> bool:
    ok = abs(got - exp) <= max(1.0, 0.005 * exp)   # 0,5 % tolerans
    print(f"  {'OK     ' if ok else 'AVVIKER'} {name:26s}: {got:>14,.0f}  (väntat {exp:>14,.0f})")
    return ok


def main() -> int:
    ap = argparse.ArgumentParser(description="Skattemodellens dataanalys.")
    ap.add_argument("--data-dir", default=None, help="Katalog med SCB-CSV-filerna.")
    ap.add_argument("--no-write", action="store_true", help="Skriv inte resultatfiler.")
    args = ap.parse_args()
    if args.data_dir:
        C.DATA_DIR = args.data_dir

    try:
        results = run()
    except FileNotFoundError as e:
        print(f"\nFEL: hittar inte en datafil: {e}", file=sys.stderr)
        return 1

    if not results:
        print("\nInga analyser kördes -- inga datafiler hittades.", file=sys.stderr)
        return 1

    if not args.no_write:
        write_outputs(results)
    verify(results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
