#!/usr/bin/env python3
import sys
import argparse
import pandas as pd
import yaml
from datetime import datetime, timedelta
from data_loader import laad_data, get_trainingskolommen, transformeer_naar_lang

def get_wedstrijdkolommen(file_path="historie.tsv"):
    df = pd.read_csv(file_path, sep='\t')
    type_rij = df[df['Voornaam'] == 'TYPE']
    if type_rij.empty:
        raise ValueError("Rij met Voornaam 'TYPE' niet gevonden.")
    return [col for col in type_rij.columns if type_rij[col].values[0] == 'W']

def get_eerstvolgende_wedstrijd(w_kolommen):
    vandaag = pd.to_datetime(datetime.now().strftime("%Y-%m-%d"))
    wedstrijden = []
    for col in w_kolommen:
        dt = pd.to_datetime(col, errors='coerce')
        if pd.notna(dt) and dt >= vandaag:
            wedstrijden.append((dt, col))
            
    if not wedstrijden:
        alle_wedstrijden = [(pd.to_datetime(col, errors='coerce'), col) for col in w_kolommen if pd.notna(pd.to_datetime(col, errors='coerce'))]
        if not alle_wedstrijden:
            return None
        alle_wedstrijden.sort(key=lambda x: x[0], reverse=True)
        return alle_wedstrijden[0][1]
        
    wedstrijden.sort(key=lambda x: x[0])
    return wedstrijden[0][1]

def bepaal_voetbalfit_label(aanwezig_laatste_n, norm_n, verbose=False):
    if norm_n == 0:
        return "⚠️ N.v.t." if verbose else "⚠️"
    
    pct_voetbalfit = (aanwezig_laatste_n / norm_n) * 100

    if pct_voetbalfit >= 80.0:
        return "🟢 Fit" if verbose else "🟢"
    elif pct_voetbalfit >= 60.0:
        return "🟡 Matig" if verbose else "🟡"
    elif pct_voetbalfit >= 35.0:
        return "🟠 Twijfel" if verbose else "🟠"
    else:
        return "🔴 Niet fit" if verbose else "🔴"

def bereken_voetbalfit_df(df, t_kolommen, laatste_n=8, verbose=False):
    df_long = transformeer_naar_lang(df, t_kolommen, inclusief_vandaag=True)
    df_long['Status_Clean'] = df_long['Status'].fillna('').astype(str).str.strip().str.upper()

    resultaten = []

    for (groep_val, voornaam), groep_df in df_long.groupby(['Groep', 'Voornaam'], dropna=False):
        actief_df = groep_df[groep_df['Status_Clean'] != 'N'].copy()
        
        mogelijke_trainingen = actief_df['Datum'].nunique()
        aanwezig_df = actief_df[actief_df['Status_Clean'] == 'X']
        aantal_aanwezig = len(aanwezig_df)
        
        pct_totaal = (aantal_aanwezig / mogelijke_trainingen * 100) if mogelijke_trainingen > 0 else 0

        actief_gesorteerd = actief_df.sort_values(by='Datum_date', ascending=True)
        laatste_n_df = actief_gesorteerd.tail(laatste_n)
        
        # Aantal keer echt aanwezig geweest in de laatste N team-trainingen
        aanwezig_laatste_n = len(laatste_n_df[laatste_n_df['Status_Clean'] == 'X'])

        # Voetbalfitheid bepalen ten opzichte van de vaste norm (laatste_n)
        status_label = bepaal_voetbalfit_label(aanwezig_laatste_n, norm_n=laatste_n, verbose=verbose)

        if "🟢" in status_label:
            sort_order = 1
        elif "🟡" in status_label:
            sort_order = 2
        elif "🟠" in status_label:
            sort_order = 3
        elif "🔴" in status_label:
            sort_order = 4
        else:
            sort_order = 5

        kolom_laatste_naam = f'Laatste {laatste_n}'

        resultaten.append({
            'Groep': groep_val,
            'Voornaam': voornaam,
            'Status': status_label,
            'Opkomst %': round(pct_totaal, 1),
            kolom_laatste_naam: f"{aanwezig_laatste_n}/{laatste_n}",
            'Aanwezig': f"{aantal_aanwezig}/{mogelijke_trainingen}",
            'Totaal_Aanwezig': aantal_aanwezig,
            'Voetbalfit_Order': sort_order,
            'Aantal_Totaal_Mogelijk': mogelijke_trainingen
        })

    return pd.DataFrame(resultaten)

def exporteer_trainingen_naar_yaml(df_voetbalfit, laatste_n, max_training, output_pad=None):
    """
    Exporteert het trainings-overzicht naar YAML-formaat (Optie 1).
    - fitindex = recente vorm (% aanwezigheid in de laatste N trainingen)
    - aantal = totaal aantal bezochte trainingen over de gehele periode
    """
    kolom_laatste = f'Laatste {laatste_n}'
    
    yaml_data = {
        'Laatste-n': laatste_n,
        'Max-training': int(max_training),
        'Groep': {}
    }
    
    df_gesorteerd = df_voetbalfit.sort_values(
        by=['Groep', 'Voetbalfit_Order', 'Opkomst %'], 
        ascending=[True, True, False]
    )
    
    for g_waarde, groep_df in df_gesorteerd.groupby('Groep', dropna=False):
        g_sleutel = int(g_waarde) if pd.notna(g_waarde) else 'Overig'
        
        spelers_lijst = []
        for _, row in groep_df.iterrows():
            aanwezig_laatste_n = int(str(row[kolom_laatste]).split('/')[0])
            
            # Bereken de fitindex als percentage van de recente vorm (laatste_n)
            fitindex_recente_vorm = round((aanwezig_laatste_n / laatste_n) * 100, 1) if laatste_n > 0 else 0.0
            
            # Totaal aantal bezochte trainingen
            totaal_bezocht = int(row['Totaal_Aanwezig'])
            
            spelers_lijst.append({
                'naam': str(row['Voornaam']),
                'fitindex': fitindex_recente_vorm,
                'aantal': totaal_bezocht
            })
            
        yaml_data['Groep'][g_sleutel] = spelers_lijst

    yaml_output = yaml.dump(yaml_data, default_flow_style=False, sort_keys=False, allow_unicode=True)

    if output_pad:
        with open(output_pad, 'w', encoding='utf-8') as f:
            f.write(yaml_output)

    return yaml_output

def print_handmatige_tabel(df_weergave, verbose=False, is_whatsapp=False):
    if is_whatsapp:
        print("```")

    cols = list(df_weergave.columns)
    max_naam_len = max(df_weergave[cols[0]].astype(str).str.len().max(), len(cols[0]))

    if verbose:
        header_str = f" {cols[0]:<{max_naam_len}}  {cols[1]:<10}  {cols[2]:>10}  {cols[3]:>10}  {cols[4]:>10}"
    else:
        header_str = f" {cols[0]:<{max_naam_len}}  {cols[1]:<6}  {cols[2]:>10}  {cols[3]:>10}  {cols[4]:>10}"
    
    print(header_str)

    for _, row in df_weergave.iterrows():
        naam = str(row[cols[0]])
        status = str(row[cols[1]])
        opkomst = f"{row[cols[2]]:.1f}"
        laatste_n_val = str(row[cols[3]])
        aanwezig = str(row[cols[4]])

        if verbose:
            row_str = f" {naam:<{max_naam_len}}  {status:<10}  {opkomst:>10}  {laatste_n_val:>10}  {aanwezig:>10}"
        else:
            row_str = f" {naam:<{max_naam_len}}     {status}  {opkomst:>10}  {laatste_n_val:>10}  {aanwezig:>10}"

        print(row_str)

    if is_whatsapp:
        print("```")

def print_lijst_weergave(df_weergave, kolom_laatste_naam):
    statussen = [
        (1, "Fit", "🟢"), 
        (2, "Matig", "🟡"), 
        (3, "Twijfel", "🟠"), 
        (4, "Niet fit", "🔴"), 
        (5, "Overig", "⚠️")
    ]
    for order_val, status_naam, emoji in statussen:
        sub_df = df_weergave[df_weergave['Voetbalfit_Order'] == order_val]
        if not sub_df.empty:
            print(f"{emoji} *{status_naam}*")
            for _, row in sub_df.iterrows():
                print(f"• *{row['Voornaam']}* — {row[kolom_laatste_naam]} ({row['Opkomst %']}% - {row['Aanwezig']})")
            print()

def main():
    parser = argparse.ArgumentParser(description="Analyseer voetbalfitheid voor trainingen of wedstrijden met 4-staps verloop (🟢 🟡 🟠 🔴).")
    parser.add_argument("file_path", nargs="?", default="historie.tsv", help="Pad naar TSV-bestand")
    parser.add_argument("-t", "--training", action="store_true", help="Toon algemeen trainingsoverzicht")
    parser.add_argument("-m", "--match", action="store_true", help="Toon wedstrijdoverzicht voor S1 en S2")
    parser.add_argument("-d", "--datum", type=str, default=None, help="Specifieke wedstrijddatum (YYYY-MM-DD)")
    parser.add_argument("-g", "--groep", type=str, default=None, help="Filter op specifieke Groep (bijv. 1 of 2)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Toon de tekst beschrijving achter de status-icoontjes")
    parser.add_argument("-w", "--whatsapp", action="store_true", help="Formatteer output als WhatsApp monospace blok (triple backticks)")
    parser.add_argument("-l", "--lijst", action="store_true", help="Toon overzicht als WhatsApp-vriendelijke opsommingslijst")
    parser.add_argument("-L", "--laatste-n", type=int, default=8, help="Aantal meest recente trainingen als voetbalfitheidsnorm (standaard: 8)")
    parser.add_argument("-y", "--yaml", type=str, nargs='?', const='trainingen.yaml', default=None, help="Exporteer trainingsoverzicht naar YAML-bestand (standaard: trainingen.yaml)")
    args = parser.parse_args()

    toon_training = args.training
    toon_wedstrijd = args.match
    if not toon_training and not toon_wedstrijd:
        toon_training = True

    df = laad_data(args.file_path, verwijder_s_nul=True)
    df = df.drop_duplicates(subset=['Voornaam']).copy()

    t_kolommen = get_trainingskolommen(args.file_path)
    df_voetbalfit = bereken_voetbalfit_df(df, t_kolommen, laatste_n=args.laatste_n, verbose=args.verbose)

    if args.groep is not None:
        try:
            g_val = float(args.groep.strip())
            df_voetbalfit = df_voetbalfit[df_voetbalfit['Groep'] == g_val].copy()
            df = df[df['Groep'] == g_val].copy()
        except ValueError:
            print(f"Ongeldige groep: {args.groep}")
            sys.exit(1)

    max_totaal_mogelijk = df_voetbalfit['Aantal_Totaal_Mogelijk'].max() if not df_voetbalfit.empty else 0
    kolom_laatste_naam = f'Laatste {args.laatste_n}'

    if toon_training:
        df_t = df_voetbalfit.sort_values(
            by=['Groep', 'Voetbalfit_Order', 'Opkomst %'], 
            ascending=[True, True, False]
        )

        print(f"=== VOETBALFITHEIDSOVERZICHT TRAININGEN ===")
        print(f"Bestand: {args.file_path}")
        print(f"Laatste: {args.laatste_n}")
        print(f"Algemeen totaal: {max_totaal_mogelijk}")
        print()

        for g_waarde, groep in df_t.groupby('Groep', dropna=False):
            g_label = "-" if pd.isna(g_waarde) else str(int(g_waarde))
            print(f"--- Groep: {g_label} ---")
            
            if args.lijst:
                print_lijst_weergave(groep, kolom_laatste_naam)
            else:
                weergave = groep[['Voornaam', 'Status', 'Opkomst %', kolom_laatste_naam, 'Aanwezig']]
                print_handmatige_tabel(weergave, verbose=args.verbose, is_whatsapp=args.whatsapp)
                print()

        if args.yaml is not None:
            exporteer_trainingen_naar_yaml(
                df_voetbalfit=df_voetbalfit,
                laatste_n=args.laatste_n,
                max_training=max_totaal_mogelijk,
                output_pad=args.yaml
            )
            print(f"[YAML Exporter] Gegevens succesvol geëxporteerd naar: {args.yaml}\n")

    if toon_wedstrijd:
        w_kolommen = get_wedstrijdkolommen(args.file_path)
        if not w_kolommen:
            print("Geen wedstrijdkolommen (TYPE 'W') gevonden.")
            sys.exit(0)

        if args.datum:
            wedstrijd_datum = args.datum.strip()
            if wedstrijd_datum not in df.columns:
                print(f"Fout: Wedstrijddatum '{wedstrijd_datum}' niet gevonden.")
                sys.exit(1)
        else:
            wedstrijd_datum = get_eerstvolgende_wedstrijd(w_kolommen)
            if not wedstrijd_datum:
                print("Geen geldige wedstrijddatum gevonden.")
                sys.exit(1)

        df_m = df_voetbalfit.copy()
        w_statussen = []

        for voornaam in df_m['Voornaam']:
            speler_rij = df[df['Voornaam'] == voornaam]
            val = speler_rij[wedstrijd_datum].values[0] if not speler_rij.empty and wedstrijd_datum in speler_rij.columns else ''
            val_clean = str(val).strip().upper() if pd.notna(val) else ''
            w_statussen.append(val_clean)

        df_m['Wedstrijd_Code'] = w_statussen
        df_m = df_m[df_m['Wedstrijd_Code'].isin(['S1', 'S2'])].copy()

        df_m = df_m.sort_values(
            by=['Wedstrijd_Code', 'Voetbalfit_Order', 'Opkomst %'], 
            ascending=[True, True, False]
        )

        print(f"\n========================================================")
        print(f"=== VOETBALFITHEIDSOVERZICHT WEDSTRIJD ({wedstrijd_datum}) ===")
        print(f"========================================================\n")

        if df_m.empty:
            print(f"Geen spelers gevonden met 'S1' or 'S2' voor {wedstrijd_datum}.\n")
        else:
            for code in ['S1', 'S2']:
                groep = df_m[df_m['Wedstrijd_Code'] == code]
                if not groep.empty:
                    print(f"--- Wedstrijd Selectie: {code} ({len(groep)} spelers) ---")
                    if args.lijst:
                        print_lijst_weergave(groep, kolom_laatste_naam)
                    else:
                        weergave = groep[['Voornaam', 'Status', 'Opkomst %', kolom_laatste_naam, 'Aanwezig']].copy()
                        weergave.columns = ['Voornaam', 'Status', 'Opkomst %', kolom_laatste_naam, 'Training X/Tot']
                        print_handmatige_tabel(weergave, verbose=args.verbose, is_whatsapp=args.whatsapp)
                        print()

if __name__ == "__main__":
    main()