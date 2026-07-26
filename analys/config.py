"""Konfiguration för skattemodellens dataanalys.

Här samlas allt som styr körningen: var datafilerna ligger, vilka
inmatade konstanter som används (sådant som INTE kommer ur SCB-filerna,
t.ex. skattestrukturen från ESV/Ekonomifakta), samt modellens
antaganden (avkastningskrav, markandel). Ändra bara här -- aldrig i
analysmodulerna.
"""

# --------------------------------------------------------------------------
# Datafiler (SCB PxWeb-CSV). Byt namn/sökväg vid behov.
# --------------------------------------------------------------------------
import os
_HERE = os.path.dirname(os.path.abspath(__file__))   # katalogen där config.py ligger (analys/)

# Sökvägarna ankras till paketkatalogen, inte till var python startas ifrån,
# så att t.ex. `python analys/run_analysis.py` från repo-roten hittar rätt.
DATA_DIR = os.path.join(_HERE, "data")   # slimmade extrakt som pipelinen läser (versionshanteras)
RAW_DIR  = os.path.join(_HERE, "raw")    # fullständiga SCB-nedladdningar som extract.py läser (gitignoreras)

FILES = {
    "sektorrakenskaper": "TAB3574_sv.csv",   # nettodriftsöverskott (B2n), sektor S11
    "kapitalstock":      "TAB5625_sv.csv",   # nettostock fast realkapital (NR0103)
    "smahus":            "TAB403_sv.csv",    # fastighetstaxering, småhus
    "hyreshus_industri": "TAB402_sv.csv",    # fastighetstaxering, hyreshus/industri
    "lantbruk":          "TAB4955_sv.csv",   # fastighetstaxering, lantbruk (delvärden)
    "bnp":               "TAB3610_sv.csv",   # NR0103 T01: BNP från användningssidan
}

# --------------------------------------------------------------------------
# Inmatade konstanter -- EJ ur filerna.
# Källor: ESV/Ekonomifakta 2024, OECD, SCB (skattekil).
# --------------------------------------------------------------------------
# BNP läses i första hand ur BNP-tabellen (NR0103, BNP till marknadspris,
# löpande priser). Konstanten nedan används bara som fallback om filen saknas.
BNP_MNKR = 6_443_000            # BNP 2024, löpande priser, mnkr (SCB NR0103; fallback)

# Dagens skattestruktur, procent av BNP
TAX = {
    "arbete":        23.6,
    "konsumtion":    10.6,
    "kapital_bolag": 6.2,
    "mark_idag":     0.3,
}

# Fångbar övervinst + kvarvarande koncessionsränta (modellval), procent av BNP.
# Lika i båda läsningarna -- det är markvärdet som skiljer dem.
OVERVINST_KONCESSION = 1.0

# Marginalskattekil: lagstadgade satser (SCB/Ekonomifakta 2024; Lundberg 2024).
WEDGE = {
    "kommunalskatt":     0.3237,
    "statlig":           0.20,
    "moms_effekt":       0.20,
    "arbetsgivaravgift": 0.3142,
}

# --------------------------------------------------------------------------
# Modellens antaganden.
# --------------------------------------------------------------------------
R_OVERVINST = (0.04, 0.05, 0.06)   # avkastningskrav för residualräntan
R_MARK = 0.04                      # avkastningskrav för kapitalisering av markränta

# Uttagsandel: hur stor del av den beräknade markräntan som faktiskt tas ut i
# reformens steg ett (alternativ C). Skatten läggs på markens avkastningsvärde,
# inte på löpande marknadspris, så uttaget blir en andel av räntan och basen
# urholkas inte av sin egen kapitalisering. 1.0 = fullt uttag (steg tvås
# potential); 0.5 = hälften, vilket är den siffersatta versionen.
UTTAGSANDEL = 0.5

# Markandel av bebyggd fastighet -- den enda kvarvarande antagandeparametern
# på markbasen sedan markförmögenheten hämtats ur fastighetstaxeringen.
MARKANDEL = {"forsiktig": 0.35, "central": 0.45, "generos": 0.55}

# Målår. Sektorräkenskaperna summeras över fyra kvartal detta år;
# kapitalstocken avläses detta år. Fastighetstaxeringen tar senaste
# tillgängliga år per fil automatiskt (olika basår per fastighetstyp).
YEAR_OVERVINST = 2024
YEAR_KAPITAL = 2024


def path(name: str) -> str:
    import os
    return os.path.join(DATA_DIR, FILES[name])


def raw_path(name: str) -> str:
    import os
    return os.path.join(RAW_DIR, FILES[name])
