#!/usr/bin/env python3
import sys
import argparse
import pandas as pd
from data_loader import laad_data, get_trainingskolommen, transformeer_naar_lang

def parse_args():
    parser = argparse.ArgumentParser(
        description="Genereert een gedetailleerd statusoverzicht per speler."
    )
    parser.add_argument(
        "file_path", 
        nargs="?", 
        default="historie.tsv", 
        help="Pad naar het TSV-bestand (standaard: historie.tsv)"
    )
    parser.add_argument(
        "-g", "--groeperen",
        action="store_true",
        help="Groepeer en toon de resultaten per 'Groep'"
    )
    parser.add_argument(
        "-p", "--persoon",
        type=str,
        default=None,
        help="Filter op (een deel van) de voornaam van een specifieke speler"
    )
    parser.add_argument(
        "-v", "--verklaring",
        action="store_true",
        help="Toon onderaan de legenda/verklaring van de statuscodes"
    )
    return parser.parse_args()

def toon_verklaring():
    """Drukt de legenda af van alle statuscodes."""
    verklaringen = [
        ("X", "Aanwezig"),
        ("A", "Afwezig (algemeen)"),
        ("V", "Vakantie"),
        ("Z", "Ziek"),
        ("ZW", "Zwanger"),
        ("W", "Werk / School"),
        ("O", "Onbekend"),
        ("G", "Geblesseerd"),
        ("N", "Nog niet lid"),
        ("LEEG", "Oningevuld")
    ]
    
    print("\n--- Legenda / Verklaring van de codes ---")
    df_legenda = pd.DataFrame(verklaringen, columns=["Code", "Betekenis"])
    print(df_legenda.to_string(index=False))

def main():
    args = parse_args()

    # 1. Data ophalen EN direct op Voornaam ontdubbelen
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

    # 3. Filter op specifieke speler indien opgegeven
    if args.persoon is not None:
        naam_query = args.persoon.strip().lower()
        df_long = df_long[df_long['Voornaam'].astype(str).str.lower().str.contains(naam_query)].copy()
        if df_long.empty:
            print(f"Geen speler gevonden die voldoet aan zoekterm '{args.persoon}'.")
            sys.exit(0)

    # 4. Status & Groep opschonen
    df_long['Status_Clean'] = (
        df_long['Status']
        .fillna('')
        .astype(str)
        .str.strip()
        .str.upper()
        .replace({'': 'LEEG'})
    )
    
    df_long['Groep_Label'] = df_long['Groep'].apply(
        lambda x: '-' if pd.isna(x) or str(x).strip() in ['', 'nan', 'None'] else str(int(x)) if isinstance(x, (int, float)) and x == x else str(x)
    )

    # 5. Pivot-tabel maken
    overzicht = pd.crosstab(
        index=[df_long['Voornaam'], df_long['Groep_Label']],
        columns=df_long['Status_Clean'],
        dropna=True
    ).reset_index()

    # Totaal aantal gehouden trainingen
    totaal_gehouden = df_long['Datum'].nunique()

    # Mogelijk aantal trainingen berekenen (Exclusief 'N')
    if 'N' in overzicht.columns:
        overzicht['Mogelijk'] = totaal_gehouden - overzicht['N']
    else:
        overzicht['Mogelijk'] = totaal_gehouden

    # Opkomstpercentage berekenen op basis van 'X' t.o.v. 'Mogelijk'
    if 'X' in overzicht.columns:
        overzicht['Opkomst %'] = (overzicht['X'] / overzicht['Mogelijk'] * 100).fillna(0).round(1)
    else:
        overzicht['X'] = 0
        overzicht['Opkomst %'] = 0.0

    # Kolommen netjes ordenen
    vaste_start = ['Voornaam', 'Groep_Label']
    vaste_eind = ['Mogelijk', 'Opkomst %']
    status_kolommen = [c for c in overzicht.columns if c not in vaste_start + vaste_eind]
    
    if 'X' in status_kolommen:
        status_kolommen.remove('X')
        status_kolommen = ['X'] + status_kolommen

    kolom_volgorde = vaste_start + status_kolommen + vaste_eind
    overzicht = overzicht[kolom_volgorde].rename(columns={'Groep_Label': 'Groep'})

    print(f"\n========================================================")
    print(f"=== OVERZICHT TRAININGSSAANWEZIGHEID PER PERSOON ===")
    print(f"=== Totaal gehouden trainingen: {totaal_gehouden:<21} ===")
    print(f"========================================================\n")

    # 6. Weergave: Groeperen bij -g optie, anders op alfabetische volgorde op Naam
    if args.groeperen:
        overzicht = overzicht.sort_values(by=['Groep', 'Voornaam'], key=lambda col: col.astype(str).str.lower())
        for groep_val, sub_df in overzicht.groupby('Groep', dropna=False):
            print(f"--- Groep: {groep_val} ({len(sub_df)} spelers) ---")
            weergave = sub_df.drop(columns=['Groep'])
            print(weergave.to_string(index=False))
            print()
    else:
        overzicht = overzicht.sort_values(by='Voornaam', key=lambda col: col.str.lower(), ascending=True)
        print(overzicht.to_string(index=False))
        print()

    # 7. Optionele verklaring weergeven als -v is meegegeven
    if args.verklaring:
        toon_verklaring()

if __name__ == "__main__":
    main()
