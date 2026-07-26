# Skatten på arbete och valet mellan människa och maskin

Policyartikel om en skatteväxling från arbete till mark-, natur- och
koncessionsräntor, med tillämpning på Sverige. Avsedd för *Ekonomisk Debatt*.

## Innehåll

- `skatt-pa-ranta.tex` — artikelns källa.
- `analys/` — reproducerbar Python-pipeline som räknar fram
  artikelns svenska nyckeltal (övervinst-residual, markförmögenhet,
  kompositionstabell och marginalskattekil) direkt ur SCB:s datafiler.
  Se paketets egen `README.md` för datafiler, körning och struktur.

## Bygga PDF:en

Kräver `pdflatex` (två pass för korsreferenser och tabeller):

    pdflatex skatt-pa-ranta.tex
    pdflatex skatt-pa-ranta.tex

Svensk `babel`, `lmodern` och `fontspec` laddas villkorligt, så filen
kompilerar även där paketen saknas. LuaLaTeX används inte.
