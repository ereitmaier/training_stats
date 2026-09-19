#!/usr/bin/env python3
import sys
import os
import pandas as pd
from datetime import datetime

def laad_data(file_path="todo.tsv", verwijder_s_nul=True):
    """Leest het TSV-bestand in en verwijdert optioneel de TYPE-rij en Groep==0."""
    if not os.path.exists(file_path):
        print(f"Fout: Bestand '{file_path}' niet gevonden.")
        sys.exit(1)
        
    df = pd.read_csv(file_path, sep='\t')
    
    # Filter spelers (verwijder TYPE-rij en optioneel Groep == 0)
    if verwijder_s_nul:
        df = df[(df['Voornaam'] != 'TYPE') & (df['Groep'].isna() | (df['Groep'] != 0))].copy()
    else:
        df = df[df['Voornaam'] != 'TYPE'].copy()
        
    return df

def get_trainingskolommen(file_path="todo.tsv"):
    """Haalt alle kolomnamen op waar de TYPE-rij gelijk is aan 'T'."""
    df = pd.read_csv(file_path, sep='\t')
    type_rij = df[df['Voornaam'] == 'TYPE']
    if type_rij.empty:
        raise ValueError("Rij met Voornaam 'TYPE' niet gevonden.")
    return [col for col in type_rij.columns if type_rij[col].values[0] == 'T']

def get_vandaag_kolom():
    """Bepaalt de kolomnaam van vandaag in YYYY-MM-DD formaat."""
    return datetime.now().strftime("%Y-%m-%d")

def transformeer_naar_lang(df, t_kolommen, inclusief_vandaag=True):
    """Zet brede datakolommen om naar een lang formaat tot en met vandaag/gisteren."""
    df_long = df.melt(
        id_vars=['Voornaam', 'Groep'], 
        value_vars=t_kolommen, 
        var_name='Datum', 
        value_name='Status'
    )
    
    einddatum = pd.to_datetime(get_vandaag_kolom())
    if not inclusief_vandaag:
        einddatum -= pd.Timedelta(days=1)
        
    df_long['Datum_date'] = pd.to_datetime(df_long['Datum'], errors='coerce')
    return df_long[df_long['Datum_date'].notna() & (df_long['Datum_date'] <= einddatum)].copy()
