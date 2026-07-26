# Hjälpfiler (.aux, .log, .fls, .fdb_latexmk) hamnar i build/,
# medan den färdiga PDF:en läggs i projektroten.
$aux_dir = 'build';
$out_dir = '.';

# Kör pdflatex (LuaLaTeX används inte i detta projekt).
$pdf_mode = 1;

# 'latexmk -c' städar build/ utan att röra PDF:en.
