# training_stats

Een verzameling (Python) scripts om data te analyseren en te presenteren.

## Voorbeelddata

Alle aangeleverde data moet in een tsv file worden opgeslagen. tsv file staat voor Tab Separated Values.
De kolommen zijn gescheiden door een tab teken.

### Historie tabel

Deze tabel bevat alle data tot nu toe.

```csv
ID	Voornaam	Groep	2026-08-11	2026-08-13	2026-08-16	2026-08-18	2026-08-20	2026-08-23	2026-08-25	2026-08-27	2026-08-30	2026-09-01
	TYPE			T	T	T	T	T	W	T	T	T	T	
1.0	Janny	1.0	X	W	\	W	X	W	W	W	X	A	X
2.0	Sandra	1.0	X	X	X	X	X	S1	X	X	X	X	X
3.0	Fien	1.0	X	A	V	V	V	V	V	V	V	V	V
4.0	Henny	1.0	X	W	X	X	X		X	G	X	X	X
5.0	Anna	1.0	X	A	X	X	X	S1	X	X	X	X	X
```

## fitheids_analyse.py

Het script `fitheids_analyse.py` analyseert de opkomst en fitheid van spelers op basis van een trainings- en wedstrijdhistorie (`historie.tsv`). Het bepaalt de fitheidsstatus van spelers, berekent opkomstpercentages en kan de resultaten in verschillende sjablonen (zoals tabellen of WhatsApp-berichten) tonen.

[Handleiding fitheids_analyze.py](Handleiding-fitheids_analyse.md)
