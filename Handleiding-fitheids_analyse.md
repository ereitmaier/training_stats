# Handleiding: fitheids_analyse.py

## 💬 Beschrijving

Het script `fitheids_analyse.py` analyseert de opkomst en fitheid van spelers op basis van een trainings- en wedstrijdhistorie (`historie.tsv`). Het bepaalt de fitheidsstatus van spelers, berekent opkomstpercentages en kan de resultaten in verschillende sjablonen (zoals tabellen of WhatsApp-berichten) tonen.

---

## 🛠️ Werking van het Fitheidslabel

De fitheidsstatus wordt bepaald op basis van de **laatste $N$ teamtrainingen** (standaard $N = 8$):

- 🟢 **Fit**: Speler is bij $\ge 75\%$ van de laatste $N$ trainingen aanwezig geweest (bijv. $\ge 6/8$).
- 🟡 **Matig**: Speler is bij $50\%$ tot $74\%$ van de laatste $N$ trainingen aanwezig geweest (bijv. $4/8$ of $5/8$).
- 🔴 **Niet fit**: Speler is bij $< 50\%$ van de laatste $N$ trainingen aanwezig geweest (bijv. $< 4/8$).

> **Opmerking:** Als een speler nieuw is en bijv. 2 van de 2 mogelijke trainingen aanwezig is geweest, is de totale opkomst $100\%$, maar de fitheidsstatus **🔴 Niet fit** ($2/8 = 25\%$), omdat er fysiek nog onvoldoende trainingsvolume is opgebouwd.

---

## 🚀 Gebruik & Opties

Run het script via de terminal:

```bash
python3 fitheids_analyse.py [BESTAND] [OPTIES]
```

### Command-line Opties

| Vlag | Lange optie | Omschrijving | Standaardwaarde |
| :--- | :--- | :--- | :--- |
| `file_path` | Positional | Pad naar het TSV-databestand. | `historie.tsv` |
| `-t` | `--training` | Toon het algemene trainingsoverzicht. | `True` (indien geen `-m`) |
| `-m` | `--match` | Toon wedstrijdoverzicht voor selecties (S1 / S2). | `False` |
| `-d` | `--datum` | Specifieke wedstrijddatum in `YYYY-MM-DD` formaat. | Eerstvolgende wedstrijd |
| `-g` | `--groep` | Filter de resultaten op een specifieke Groep (bijv. 1 of 2). | Alle groepen |
| `-L` | `--laatste-n` | Instellen van het aantal meest recente trainingen ($N$). | `8` |
| `-v` | `--verbose` | Toon de tekstuele status (Fit, Matig, Niet fit) achter het icoon. | Alleen icoon |
| `-w` | `--whatsapp` | Wrapt de tabel in monospace-codeblokken (```) voor WhatsApp. | `False` |
| `-l` | `--lijst` | Genereert een geformatteerde opsommingslijst per categorie. | `False` |

---

## 📋 Voorbeelden

### 1. Standaard overzicht van de trainingen (laatste 8 trainingen)

```bash
python3 fitheids_analyse.py
```

### 2. Analyseer de laatste 6 trainingen met uitgebreide status-tekst

```bash
python3 fitheids_analyse.py -L 6 -v
```

### 3. Wedstrijdoverzicht voor de eerstvolgende wedstrijd

```bash
python3 fitheids_analyse.py -m
```

### 4. WhatsApp-vriendelijke lijstweergave genereren over de laatste 10 trainingen

```bash
python3 fitheids_analyse.py -l -L 10
```

*Voorbeeld output:*

```text
=== FITHEIDSOVERZICHT TRAININGEN ===
Bestand: historie.tsv
Laatste: 10
Algemeen totaal: 13
--- Groep: 1 ---
🟢 *Fit*
• *Sandra* — 8/10 (100.0% - 13/13)
• *Linda* — 8/10 (92.3% - 12/13)

🟡 *Matig*
• *Jessica* — 7/10 (69.2% - 9/13)
```

### 5. Tabel kopiëren voor WhatsApp als monospace blok voor Groep 1

```bash
python3 fitheids_analyse.py -g 1 -w
```
