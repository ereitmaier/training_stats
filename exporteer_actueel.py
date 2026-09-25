#!/usr/bin/env python3
import sys
import argparse
import pandas as pd
import yaml

# Custom Dumper om inspringing van lijsten (dash) goed te regelen voor yamllint
class YamlLintDumper(yaml.SafeDumper):
    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow=False, indentless=False)

# Mapping van de statuscodes naar de volledige omschrijvingen
STATUS_MAP = {
    "A": "Afwezig (algemeen)",
    "V": "Vakantie",
    "Z": "Ziek",
    "ZW": "Zwanger",
    "W": "Werk / School",
    "O": "Onbekend",
    "G": "Geblesseerd",
    "T": "Twijfel",
    "LEEG": "Onbekend"
}

def parse_args():
    parser = argparse.ArgumentParser(
        description="Exporteert trainingsgroepen of wedstrijdselecties naar YAML op basis van een verplichte datum."
    )
    parser.add_argument(
        "file_path", 
        nargs="?", 
        default="actueel.tsv", 
        help="Pad naar het TSV-bestand (standaard: actueel.tsv)"
    )
    parser.add_argument(
        "-d", "--datum", 
        type=str, 
        required=True, 
        help="Verplichte datum (YYYY-MM-DD). Bijv. 2026-09-24 of 2026-09-27."
    )
    parser.add_argument(
        "-o", "--output", 
        type=str, 
        default=None, 
        help="Uitvoer YAML-bestand. Indien niet opgegeven wordt de YAML naar de standaard output geschreven."
    )
    return parser.parse_args()

def is_groep_1_of_2(g_waarde):
    """Controleert of een groepswaarde gelijk is aan 1 of 2."""
    if pd.isna(g_waarde):
        return False
    g_str = str(g_waarde).strip()
    try:
        val = float(g_str)
        return int(val) in [1, 2] if val.is_integer() else False
    except ValueError:
        return g_str in ['1', '2']

def get_groep_nummer(g_waarde):
    """Bepaalt of het exact Groep 1 of Groep 2 is."""
    if pd.isna(g_waarde):
        return None
    g_str = str(g_waarde).strip()
    try:
        val = float(g_str)
        return int(val) if val.is_integer() and int(val) in [1, 2] else None
    except ValueError:
        return int(g_str) if g_str in ['1', '2'] else None

def main():
    args = parse_args()

    # 1. Lees het TSV-bestand direct in
    try:
        df = pd.read_csv(args.file_path, sep='\t', dtype=str)
    except Exception as e:
        print(f"Fout bij openen van bestand '{args.file_path}': {e}", file=sys.stderr)
        sys.exit(1)

    # Kolomnamen opschonen (spaties en eventuele onzichtbare karakters verwijderen)
    df.columns = [str(c).strip() for c in df.columns]
    doel_datum = args.datum.strip()

    # Controleer of de opgegeven datum aanwezig is in het bestand
    if doel_datum not in df.columns:
        print(f"Fout: Datum '{doel_datum}' niet gevonden in kolommen.", file=sys.stderr)
        print(f"Beschikbare kolommen: {[c for c in df.columns if not c.startswith('Unnamed')]}", file=sys.stderr)
        sys.exit(1)

    # 2. Zoek de 'TYPE'-rij (controleer elke rij op de aanwezigheid van 'TYPE')
    type_rij_index = None
    for idx, row in df.iterrows():
        row_values = [str(val).strip().upper() for val in row.values if pd.notna(val)]
        if 'TYPE' in row_values:
            type_rij_index = idx
            break

    if type_rij_index is None:
        print(f"Fout: Geen 'TYPE'-rij gevonden in '{args.file_path}'.", file=sys.stderr)
        sys.exit(1)

    type_rij = df.loc[type_rij_index]
    datum_type = str(type_rij[doel_datum]).strip().upper()

    if datum_type not in ['W', 'T']:
        print(f"Fout: Datum '{doel_datum}' heeft een onbekend type '{datum_type}' (verwacht 'W' of 'T').", file=sys.stderr)
        sys.exit(1)

    # 3. Filter de TYPE-rij eruit
    df_spelers = df.drop(index=type_rij_index).copy()
    
    voornaam_col = next((col for col in df_spelers.columns if col.lower() == 'voornaam'), 'Voornaam')
    groep_col = next((col for col in df_spelers.columns if col.lower() == 'groep'), 'Groep')

    # Filter op Groep 1 en 2, en ontdubbel op Voornaam
    df_spelers = df_spelers[df_spelers[groep_col].apply(is_groep_1_of_2)].copy()
    df_spelers = df_spelers.drop_duplicates(subset=[voornaam_col]).copy()

    overige_dict = {}

    # 4. Verwerken op basis van gedetecteerde type
    if datum_type == 'T':
        # --- TRAINING ---
        tg1_lijst = []
        tg2_lijst = []

        for _, row in df_spelers.iterrows():
            naam = str(row[voornaam_col]).strip() if pd.notna(row[voornaam_col]) else ""
            if not naam or naam.lower() == "nan":
                continue

            groep_num = get_groep_nummer(row[groep_col])
            code = str(row[doel_datum]).strip().upper() if pd.notna(row[doel_datum]) else "LEEG"
            if not code or code == "NAN":
                code = "LEEG"

            if code == "B":
                if groep_num == 1:
                    tg1_lijst.append(naam)
                elif groep_num == 2:
                    tg2_lijst.append(naam)
            else:
                status_label = STATUS_MAP.get(code, code)
                if status_label not in overige_dict:
                    overige_dict[status_label] = []
                overige_dict[status_label].append(naam)

        tg1_lijst.sort(key=str.lower)
        tg2_lijst.sort(key=str.lower)

        yaml_data = {
            "Trainingsgroep": {
                "Datum": doel_datum,
                "Trainingsgroep 1": {
                    "Aantal": len(tg1_lijst),
                    "Spelers": tg1_lijst
                },
                "Trainingsgroep 2": {
                    "Aantal": len(tg2_lijst),
                    "Spelers": tg2_lijst
                },
                "Overige": {}
            }
        }

        for cat_label in sorted(overige_dict.keys(), key=str.lower):
            speelsters = overige_dict[cat_label]
            speelsters.sort(key=str.lower)
            yaml_data["Trainingsgroep"]["Overige"][cat_label] = {
                "Aantal": len(speelsters),
                "Spelers": speelsters
            }

    else:
        # --- WEDSTRIJD ('W') ---
        vr1_lijst = []
        vr2_lijst = []

        for _, row in df_spelers.iterrows():
            naam = str(row[voornaam_col]).strip() if pd.notna(row[voornaam_col]) else ""
            if not naam or naam.lower() == "nan":
                continue

            code = str(row[doel_datum]).strip().upper() if pd.notna(row[doel_datum]) else "LEEG"
            if not code or code == "NAN":
                code = "LEEG"

            if code == "S1":
                vr1_lijst.append(naam)
            elif code == "S2":
                vr2_lijst.append(naam)
            else:
                status_label = STATUS_MAP.get(code, f"Overig ({code})" if code != "LEEG" else "Onbekend")
                if status_label not in overige_dict:
                    overige_dict[status_label] = []
                overige_dict[status_label].append(naam)

        vr1_lijst.sort(key=str.lower)
        vr2_lijst.sort(key=str.lower)

        yaml_data = {
            "Selecties": {
                "Datum": doel_datum,
                "Vr1": {
                    "Aantal": len(vr1_lijst),
                    "Spelers": vr1_lijst
                },
                "Vr2": {
                    "Aantal": len(vr2_lijst),
                    "Spelers": vr2_lijst
                },
                "Overige": {}
            }
        }

        for cat_label in sorted(overige_dict.keys(), key=str.lower):
            speelsters = overige_dict[cat_label]
            speelsters.sort(key=str.lower)
            yaml_data["Selecties"]["Overige"][cat_label] = {
                "Aantal": len(speelsters),
                "Spelers": speelsters
            }

    # 5. Output genereren met yamllint ondersteuning
    yaml_str = yaml.dump(
        yaml_data, 
        Dumper=YamlLintDumper,
        allow_unicode=True, 
        sort_keys=False, 
        default_flow_style=False,
        explicit_start=True
    )

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(yaml_str)
        print(f"=== Geëxporteerd voor datum {doel_datum} (Type: {datum_type}) naar '{args.output}' ===", file=sys.stderr)
    else:
        sys.stdout.write(yaml_str)

if __name__ == "__main__":
    main()