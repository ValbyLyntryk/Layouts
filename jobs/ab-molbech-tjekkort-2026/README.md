# AB Molbech — tjekkort 2026 (udkast)

Printklare A4-tjekkort, så vicevært og leverandører kan kvittere for udførte opgaver, og bestyrelsen kan se **senest udført**.

Kilde: `Molbech_Driftsplan 2026 (TE, Bentsen, Køge Bugt).xlsx` plus mailen fra bestyrelsen 20. august 2026.

## Output

`AB-Molbech-tjekkort-2026-udkast.pdf`

Byg:

```bash
python3 jobs/ab-molbech-tjekkort-2026/build_tjekkort.py
```

Kræver PyMuPDF (`pip install pymupdf`) og Inter-fonte (ligger i miljøet).

## Indhold

1. Forside
2. Vejledning
3. Oversigt — senest udført (bestyrelsens overblik)
4. Dagligt tjekkort (ugevis)
5. Ugentligt tjekkort, ejendom + beboer/status
6. Måned · kvartal · halvår · år
7. Bygningsvedligehold
8. Kloak og rottespærre (8 udløb)
9. Faner til ringbind

Udkast til gennemsyn hos kunden inden tryk.
