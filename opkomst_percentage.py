#!/usr/bin/env python3
import sys
import argparse
import pandas as pd
from data_loader import laad_data, get_trainingskolommen, transformeer_naar_lang

def parse_args():
    parser = argparse.ArgumentParser(
        description="Berekent het opkomstpercentage voor trainingen (type 'T') met correctie voor 'N'."
    )
    parser.add_argument(
        "file_path", 
        nargs="?", 
        default="historie.tsv", 
        help="Pad naar het TSV-bestand (standaard: historie.tsv)"
    )
    parser.add_argument(
        "-a", "--aanwezig-code",
        type=str,
        default="X",
        help="Code die geldt als aanwezig (standaard: X)"
    )
    parser.add_argument(
        "-g", "--groep",
        type=str,
        default=None,
        help="Filter op een specifieke Groep (bijv. 1, 2 of '-' voor geen groep)"
    )
    return parser.parse_args()

def main():
    args = parse_args()

    # 1. Data ophalen en ontdubbelen op Voornaam
    df = laad_data(args.file_path, verwijder_s_nul=True)
    df = df.drop_duplicates(subset=['Voornaam']).copy()

    try:
        t_kolommen = get_trainingskolommen(args.file_path)
    except Exception as e:
        print(f"Fout bij ophalen van trainingskolommen: {e}")
        sys.exit(1)

    if not t_kolommen:
        print("Geen trainingskolommen (TYPE 'T') gevonden.")
        sys.exit(0)

    # 2. Omzetten naar lang formaat tot en met vandaag
    df_long = transformeer_naar_lang(df, t_kolommen, inclusief_vandaag=True)

    if df_long.empty:
        print("Geen trainingsgegevens tot en met vandaag gevonden.")
        sys.exit(0)

    # 3. Filter op specifieke Groep
    if args.groep is not None:
        groep_input = args.groep.strip().lower()
        if groep_input in ['-', 'geen', 'nan', 'na']:
            df_long = df_long[df_long['Groep'].isna()].copy()
        else:
            try:
                g_val = float(groep_input)
                df_long = df_long[df_long['Groep'] == g_val].copy()
            except ValueError:
                print(f"Fout: Ongeldige groep '{args.groep}' opgegeven.")
                sys.exit(1)

    # 4. Status opschonen en 'N' negeren
    df_long['Status_Clean'] = df_long['Status'].fillna('').astype(str).str.strip().str.upper()
    
    # Filter 'N' eruit voor alle berekeningen van de betreffende speler
    df_actief = df_long[df_long['Status_Clean'] != 'N'].copy()
    
    code_aanwezig = args.aanwezig_code.strip().upper()
    df_actief['Is_Aanwezig'] = df_actief['Status_Clean'] == code_aanwezig

    # 5. Aggregeren per persoon
    overzicht = df_actief.groupby(['Groep', 'Voornaam'], dropna=False).agg(
        Aantal_Aanwezig=('Is_Aanwezig', 'sum'),
        Mogelijke_Trainingen=('Datum', 'nunique')
    ).reset_index()

    # Opkomst % berekenen op basis van 'Mogelijke_Trainingen' (excl. N)
    overzicht['Opkomst_%'] = (overzicht['Aantal_Aanwezig'] / overzicht['Mogelijke_Trainingen'] * 100).fillna(0).round(1)
    overzicht = overzicht.sort_values(by=['Groep', 'Opkomst_%'], ascending=[True, False])

    # 6. Resultaten weergeven
    totaal_gehouden = df_long['Datum'].nunique()
    print(f"\n=== Opkomstoverzicht Trainingen (Totaal gehouden: {totaal_gehouden}) ===")
    print(f"Bestand: {args.file_path}")
    print(f"Aanwezigheidscode: '{code_aanwezig}' (Status 'N' gecompenseerd)\n")

    for g_waarde, groep in overzicht.groupby('Groep', dropna=False):
        g_label = "-" if pd.isna(g_waarde) else str(int(g_waarde))
        print(f"--- Subgroep Groep: {g_label} ---")
        
        weergave = groep[['Voornaam', 'Aantal_Aanwezig', 'Mogelijke_Trainingen', 'Opkomst_%']].copy()
        weergave.columns = ['Voornaam', 'Aanwezig', 'Mogelijk', 'Opkomst %']
        print(weergave.to_string(index=False))
        print()

    gemiddelde_totaal = overzicht['Opkomst_%'].mean()
    print(f"Gemiddelde opkomst selectie: {gemiddelde_totaal:.1f}%")

if __name__ == "__main__":
    main()
