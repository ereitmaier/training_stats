#!/usr/bin/env python3
import sys
import os
import argparse
import pandas as pd
from datetime import datetime
from data_loader import laad_data

def parse_args():
    parser = argparse.ArgumentParser(
        description="Toont overzicht van personen gefilterd op status voor een specifieke datum."
    )
    parser.add_argument(
        "file_path", 
        nargs="?", 
        default="historie.tsv", 
        help="Pad naar het TSV-bestand (standaard: historie.tsv)"
    )
    parser.add_argument(
        "-d", "--datum", 
        type=str, 
        default=None, 
        help="Specifieke datum in YYYY-MM-DD formaat (standaard: vandaag)"
    )
    parser.add_argument(
        "-s", "--status", 
        type=str, 
        default="leeg", 
        help="Filter op status (bijv. 'B', 'X', of 'leeg' [standaard])"
    )
    parser.add_argument(
        "-g", "--groep", 
        type=str, 
        default=None, 
        help="Extra filter voor een specifieke Groep (bijv. 1, 2 of '-' / 'geen')"
    )
    return parser.parse_args()

def format_groep_label(g_waarde):
    """Zet groepswaarden netjes om: NaN -> '-', '1.0' -> '1', 'B' -> 'B'."""
    if pd.isna(g_waarde):
        return "-"
    g_str = str(g_waarde).strip()
    try:
        val = float(g_str)
        return str(int(val)) if val.is_integer() else g_str
    except ValueError:
        return g_str

def main():
    args = parse_args()
    
    # 1. Bepaal de datum (opgegeven datum OF vandaag)
    doel_datum = args.datum if args.datum else datetime.now().strftime("%Y-%m-%d")

    # 2. Laad de data via de centrale data_loader en ontdubbel op Voornaam
    df = laad_data(args.file_path, verwijder_s_nul=True)
    df = df.drop_duplicates(subset=['Voornaam']).copy()

    # 3. Controleer of de kolom aanwezig is
    if doel_datum not in df.columns:
        print(f"Fout: Kolom voor datum '{doel_datum}' niet gevonden in '{args.file_path}'.")
        sys.exit(1)

    # 4. Filteren op de opgegeven status
    status_gekozen = args.status.strip()
    
    if status_gekozen.lower() in ['leeg', 'na', 'none', '']:
        df_gefilterd = df[
            df[doel_datum].isna() | (df[doel_datum].astype(str).str.strip() == '')
        ].copy()
        label_status = "Oningevuld / Leeg"
    else:
        df_gefilterd = df[
            df[doel_datum].astype(str).str.strip().str.upper() == status_gekozen.upper()
        ].copy()
        label_status = f"Status '{status_gekozen.upper()}'"

    # 5. Extra filter op Groep indien meegegeven via -g / --groep
    if args.groep is not None:
        groep_input = args.groep.strip().lower()
        if groep_input in ['-', 'geen', 'nan', 'na']:
            df_gefilterd = df_gefilterd[df_gefilterd['Groep'].isna()].copy()
            label_status += " | Groep: Geen (-)"
        else:
            # Match zowel op exact string-niveau als numeriek (bijv. match 1 met 1.0 of '1')
            df_gefilterd = df_gefilterd[
                df_gefilterd['Groep'].apply(format_groep_label).str.lower() == groep_input
            ].copy()
            label_status += f" | Groep: {args.groep.strip()}"

    # 6. Header afdrukken
    print(f"\n=== Overzicht voor {doel_datum} ({label_status}) ===")
    print(f"Bestand: {args.file_path}")

    if df_gefilterd.empty:
        print(f"\nGeen personen gevonden die voldoen aan de criteria.")
        return

    # 7. Sorteer en verwerk nummering per Groep
    df_gefilterd = df_gefilterd.sort_values(by=['Groep', 'Voornaam'], key=lambda x: x.astype(str).str.lower())
    df_gefilterd['Nr'] = range(1, len(df_gefilterd) + 1)
    df_gefilterd['PG'] = df_gefilterd.groupby('Groep', dropna=False).cumcount() + 1

    # Format Voornaam strak links uitgelijnd
    max_len = max(df_gefilterd['Voornaam'].astype(str).str.len().max(), len("Voornaam"))
    df_gefilterd['Voornaam_Formatted'] = df_gefilterd['Voornaam'].astype(str).str.ljust(max_len)

    # 8. Afdrukken in Visuele Blokken per Groep
    for g_waarde, groep in df_gefilterd.groupby('Groep', dropna=False):
        g_label = format_groep_label(g_waarde)
        print(f"\n--- Subgroep: {g_label} ---")
        
        weergave = groep[['Nr', 'PG', 'Voornaam_Formatted']].rename(
            columns={'Voornaam_Formatted': 'Voornaam', 'PG': 'PGroep'}
        )
        print(weergave.to_string(index=False, justify='left'))

if __name__ == "__main__":
    main()
