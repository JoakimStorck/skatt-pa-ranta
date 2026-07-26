"""Robust inläsning av SCB:s PxWeb-CSV-filer.

Alla filer i projektet har samma grundform: några dimensionskolumner
följt av EN värdekolumn vars rubrik är tabellens långa beskrivning.
Filerna är latin-1-kodade och kommaseparerade. Värden använder punkt som
decimaltecken, ".." för saknat värde och kan innehålla blanksteg eller
hårda blanksteg (\\xa0) som tusentalsavgränsare.

Modulen exponerar små, generella hjälpfunktioner som analysmodulerna
bygger vidare på -- ingen affärslogik här.
"""
from __future__ import annotations

import re
import pandas as pd

_YEAR_RE = re.compile(r"(\d{4})")


def load_pxweb(path: str) -> pd.DataFrame:
    """Läs en PxWeb-CSV. Sista kolumnen döps om till 'value' (numerisk),
    övriga kolumner städas från hårda blanksteg och trimmas."""
    df = pd.read_csv(path, encoding="latin-1", dtype=str, quotechar='"')
    df.columns = [c.strip() for c in df.columns]
    value_col = df.columns[-1]
    for c in df.columns[:-1]:
        df[c] = (df[c].astype(str)
                 .str.replace("\xa0", " ", regex=False)
                 .str.strip())
    df = df.rename(columns={value_col: "value"})
    df["value"] = _to_number(df["value"])
    return df


def _to_number(s: pd.Series) -> pd.Series:
    return pd.to_numeric(
        s.astype(str)
         .str.replace("\xa0", "", regex=False)
         .str.replace(" ", "", regex=False)
         .str.replace(",", ".", regex=False),
        errors="coerce",
    )


def col_like(df: pd.DataFrame, *keywords: str) -> str:
    """Första kolumn vars namn innehåller alla nyckelord (case-insensitivt)."""
    for c in df.columns:
        lc = c.lower()
        if all(k.lower() in lc for k in keywords):
            return c
    raise KeyError(f"Ingen kolumn matchar {keywords}: {list(df.columns)}")


def year_column(df: pd.DataFrame) -> str:
    """Hitta års-/tidskolumnen ('år', 'år, oregelb', 'kvartal', ...)."""
    for c in df.columns:
        lc = c.lower()
        if lc.startswith("år") or lc in ("kvartal", "tid", "year"):
            return c
    raise KeyError("Ingen års-/tidskolumn hittades: " + ", ".join(df.columns))


def year_of(value) -> int | None:
    """Plocka ut de fyra första årssiffrorna ur t.ex. '2024' eller '2024K1'."""
    m = _YEAR_RE.search(str(value))
    return int(m.group(1)) if m else None


def latest_year(df: pd.DataFrame, col: str | None = None) -> int:
    col = col or year_column(df)
    yrs = df[col].map(year_of).dropna()
    if yrs.empty:
        raise ValueError(f"Inga giltiga år i kolumnen {col!r}")
    return int(yrs.max())


def contains(series: pd.Series, *needles: str) -> pd.Series:
    """Boolean-mask: True där texten innehåller NÅGOT av delsträngarna
    (case-insensitivt, ingen regex)."""
    low = series.astype(str).str.lower()
    mask = pd.Series(False, index=series.index)
    for n in needles:
        mask = mask | low.str.contains(n.lower(), regex=False, na=False)
    return mask
