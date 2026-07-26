#!/usr/bin/env python3
"""Extrahera de rader pipelinen behöver ur de fullständiga SCB-filerna.

De fullständiga PxWeb-nedladdningarna (analys/raw/, gitignorerade, ~165 MB)
destilleras här till slimmade delmängder (analys/data/, versionshanterade),
så att repot går att klona och köra utan att först hämta rådata.

Principen är *trogen delmängd*: varje extrakt är ett rent radurval ur
originalfilen, skrivet i samma PxWeb-format (latin-1, samma kolumner och
samma cellsträngar). Urvalet sker enbart på de grova dimensioner pipelinen
ändå kräver (år, region), aldrig på den finare semantiska selektionen
(B2n mot B2g, S11-totalen mot delsektorerna, näringsgren, delvärden) -- den
ligger kvar i analysmodulerna. Därför kan ett extrakt inte tyst ändra ett
tal: läsaren gör exakt samma val på delmängden som på originalet.

BNP-tabellen är redan liten och kopieras oförändrad.

Kör:  python extract.py            # raw/ -> data/
      python extract.py --raw-dir NER --out-dir DATA
"""
from __future__ import annotations

import argparse
import os
import shutil

import pandas as pd

import config
from scb_io import (load_pxweb, col_like, year_column, year_of, latest_year,
                    contains)


# --- Grova, trogna masker: en supermängd av vad respektive läsare väljer. ---

def _sektor_mask(df: pd.DataFrame):
    """Sektorräkenskaper: målåret och sektor S11 (total + delsektorer).
    overprofit.py gör sedan B2n-urvalet och väljer S11-totalen."""
    yc = year_column(df)
    sektor = col_like(df, "sektor")
    return ((df[yc].map(year_of) == config.YEAR_OVERVINST)
            & (contains(df[sektor], "s11") | contains(df[sektor], "icke-finansiella")))


def _kapital_mask(df: pd.DataFrame):
    """Kapitalstock: målåret, löpande priser, samtliga fasta tillgångar.
    overprofit.py väljer sedan näringslivet totalt och L68A."""
    yc = year_column(df)
    innehall = col_like(df, "tabellinnehåll")
    slag = col_like(df, "tillgångsslag")
    return ((df[yc].map(year_of) == config.YEAR_KAPITAL)
            & contains(df[innehall], "löpande")
            & contains(df[slag], "samtliga fasta"))


def _riket_latest_mask(df: pd.DataFrame):
    """Fastighetstaxering: riket, senaste år (samma latest_year som land.py).
    land.py väljer sedan mark-/naturvärde respektive totalt taxeringsvärde."""
    region = col_like(df, "region")
    yc = year_column(df)
    y = latest_year(df, yc)
    return contains(df[region], "riket") & (df[yc].map(year_of) == y)


MASKS = {
    "sektorrakenskaper": _sektor_mask,
    "kapitalstock":      _kapital_mask,
    "smahus":            _riket_latest_mask,
    "hyreshus_industri": _riket_latest_mask,
    "lantbruk":          _riket_latest_mask,
}
COPY_VERBATIM = ("bnp",)   # redan liten; kopieras oförändrad


def _mb(path: str) -> str:
    return f"{os.path.getsize(path) / 1e6:.1f} MB"


def extract_one(name: str, raw_dir: str, out_dir: str) -> None:
    src = os.path.join(raw_dir, config.FILES[name])
    dst = os.path.join(out_dir, config.FILES[name])
    if not os.path.exists(src):
        raise SystemExit(f"FEL: hittar inte {src}. Lägg de fullständiga "
                         f"SCB-filerna i {raw_dir}/ (se analys/README.md).")

    if name in COPY_VERBATIM:
        shutil.copyfile(src, dst)
        print(f"  {name:20s} kopierad oförändrad        ({_mb(src)})")
        return

    # raw: originalsträngarna oförändrade (för trogen utskrift).
    raw = pd.read_csv(src, encoding="latin-1", dtype=str, quotechar='"')
    # parsed: samma fil genom pipelinens egen inläsning, för att bygga masken
    # med exakt de kolumn-/etikettmatchningar läsarna använder. Samma radordning
    # och index som raw, eftersom load_pxweb aldrig släpper eller flyttar rader.
    parsed = load_pxweb(src)
    mask = MASKS[name](parsed)

    n = int(mask.sum())
    if n == 0:
        raise SystemExit(f"FEL: extraktmasken för {name} matchade 0 rader -- "
                         f"etiketter eller år kan ha ändrats i {src}.")

    raw.loc[mask.values].to_csv(dst, encoding="latin-1", index=False)
    print(f"  {name:20s} {len(raw):>8d} -> {n:>6d} rader   "
          f"({_mb(src)} -> {_mb(dst)})")


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Slimma SCB-filerna till trogna delmängder för versionshantering.")
    ap.add_argument("--raw-dir", default=config.RAW_DIR,
                    help="katalog med fullständiga SCB-filer (standard: %(default)s)")
    ap.add_argument("--out-dir", default=config.DATA_DIR,
                    help="katalog för de slimmade extrakten (standard: %(default)s)")
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    print(f"Extraherar ur {args.raw_dir}/ till {args.out_dir}/:")
    for name in config.FILES:
        extract_one(name, args.raw_dir, args.out_dir)
    print("Klart. Kör sedan run_analysis.py mot data/ och kontrollera att "
          "verifieringen mot kända aggregat går igenom.")


if __name__ == "__main__":
    main()
