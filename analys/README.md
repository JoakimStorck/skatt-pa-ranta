# Skattemodell — reproducerbar analys

Räknar fram artikelns svenska nyckeltal direkt ur SCB:s datafiler:
övervinst-residualen, markförmögenheten och den intäktsneutrala
kompositionstabellen med marginalskattekil.

## Datafiler

Lägg följande fem SCB PxWeb-CSV-filer (latin-1) i raw/; de versionshanterade extrakten ligger i data/, återskapas med python extract.py. Filnamnen kan ändras i `config.py`.

| Logiskt namn        | Fil            | SCB-innehåll                                   |
|---------------------|----------------|------------------------------------------------|
| `sektorrakenskaper` | `TAB3574_sv.csv` | Sektorräkenskaper, nettodriftsöverskott B2n (S11) |
| `kapitalstock`      | `TAB5625_sv.csv` | Nettostock fast realkapital, NR0103            |
| `smahus`            | `TAB403_sv.csv`  | Fastighetstaxering, småhus                      |
| `hyreshus_industri` | `TAB402_sv.csv`  | Fastighetstaxering, hyreshus/industri m.fl.    |
| `lantbruk`          | `TAB4955_sv.csv` | Fastighetstaxering, lantbruk (delvärden)       |
| `bnp`               | `TAB_bnp_sv.csv` | NR0103...T01, BNP från användningssidan (marknadspris) |

BNP läses ur den sista tabellen (NR0103, BNP till marknadspris, löpande
priser). Saknas filen används fallback-konstanten i `config.py`. Döp din
nedladdning till `TAB_bnp_sv.csv` eller ändra namnet i `config.py`.

## Körning

```bash
pip install pandas
python run_analysis.py                 # filerna i aktuell katalog
python run_analysis.py --data-dir DATA # filerna i katalogen DATA
python run_analysis.py --no-write      # skriv inte resultatfiler
```

Skriptet skriver en rapport till skärmen, resultatfiler till `./resultat/`
och avslutar med en verifiering mot de aggregat vi känner till (B2n S11,
kapitalstock, lantbrukets markvärde, bebyggt taxeringsvärde).

## Struktur

| Fil              | Ansvar                                                            |
|------------------|-------------------------------------------------------------------|
| `extract.py`     | skapar data/ ur raw/                                              |
| `config.py`      | Filnamn, inmatade konstanter (skattestruktur, satser), antaganden |
| `scb_io.py`      | Robust inläsning/filtrering av PxWeb-CSV (ingen affärslogik)      |
| `gdp.py`         | BNP till marknadspris ur NR0103 (gör BNP till ett hämtat tal)     |
| `overprofit.py`  | Övervinst-residual: B2n − r·K, per avkastningskrav                |
| `land.py`        | Markförmögenhet: (lantbruk + markandel·bebyggt)/0,75, markränta   |
| `composition.py` | Kompositionstabell (arbete som restpost) och marginalskattekil    |
| `run_analysis.py`| Kör allt, skriver rapport och resultatfiler, verifierar           |

Ändra bara antaganden i `config.py` (t.ex. `MARKANDEL`, `R_MARK`,
`R_OVERVINST`, `BNP_MNKR`). Analysmodulerna rör du inte.

## Vad som är hämtat och vad som är antaget

**Hämtat ur filerna:** BNP till marknadspris, nettodriftsöverskott,
kapitalstock, lantbrukets mark- och naturvärde (exakt), samt totalt
taxeringsvärde för bebyggd fastighet.

**Inmatat (ej ur filerna):** dagens skattestruktur i procent av BNP
(ESV/Ekonomifakta), de lagstadgade satserna i marginalkilen, och den
fångbara övervinst/koncessionsposten (1,0 %).

**Antaget:** markandelen av bebyggd fastighet (35/45/55 %) och
avkastningskraven. Markandelen är den enda kvarvarande antagandeparametern
på markbasen sedan markförmögenheten hämtats ur fastighetstaxeringen.

## Förbehåll (byggs in i tolkningen)

- **Specialenheter är skattebefriade** och saknar taxeringsvärde — offentlig
  mark och infrastruktur ligger utanför. Basen är alltså ägbar, taxerad mark.
- **Olika basår** per fastighetstyp (lantbruk 2023, småhus 2024,
  hyreshus/industri 2025); skriptet tar senaste år per fil.
- **Taxeringsvärde = 75 % av marknadsvärde**; mark/byggnad-fördelningen är
  schabloniserad av Skatteverket.
