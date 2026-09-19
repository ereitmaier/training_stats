#!/usr/bin/env python3
import sys
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from data_loader import laad_data, get_trainingskolommen, transformeer_naar_lang

file_path = sys.argv[1] if len(sys.argv) > 1 else "historie.tsv"

# 1. Modulair laden en ontdubbelen op Voornaam
df = laad_data(file_path, verwijder_s_nul=True)
df = df.drop_duplicates(subset=['Voornaam']).copy()

t_kolommen = get_trainingskolommen(file_path)
df_filtered = transformeer_naar_lang(df, t_kolommen, inclusief_vandaag=True)

# 2. Status opschonen en 'N' negeren
df_filtered['Status_Clean'] = df_filtered['Status'].fillna('').astype(str).str.strip().str.upper()
df_filtered = df_filtered[df_filtered['Status_Clean'] != 'N'].copy()

df_filtered['Aanwezigheid'] = df_filtered['Status_Clean'].apply(
    lambda x: 'Aanwezig (X)' if x == 'X' else 'Afwezig'
)

# 3. Sorteren op aantal aanwezigheid (X) per Voornaam (van meest naar minst)
groen_counts = (
    df_filtered[df_filtered['Status_Clean'] == 'X']
    ['Voornaam']
    .value_counts()
)

# Zorg dat eventuele spelers met 0x aanwezigheid ook meegenomen worden
alle_voornamen = df_filtered['Voornaam'].unique()
voornamen_volgorde = (
    groen_counts.reindex(alle_voornamen, fill_value=0)
    .sort_values(ascending=False)
    .index.tolist()
)

# Maak van Voornaam een Categorical. 
# reversed() zorgt ervoor dat de persoon met de meeste aanwezigheid bovenaan de Y-as komt te staan.
df_filtered['Voornaam'] = pd.Categorical(
    df_filtered['Voornaam'], 
    categories=list(reversed(voornamen_volgorde)), 
    ordered=True
)

# Chronologische volgorde voor de Datums instellen
chronologische_datums = df_filtered.sort_values(by='Datum_date')['Datum'].unique()
df_filtered['Datum'] = pd.Categorical(df_filtered['Datum'], categories=chronologische_datums, ordered=True)

# 4. Plotten
plt.figure(figsize=(12, 8))

sns.scatterplot(
    data=df_filtered, 
    x='Datum', 
    y='Voornaam', 
    hue='Aanwezigheid', 
    palette={"Aanwezig (X)": "#2ca02c", "Afwezig": "#d62728"}, 
    s=120
)

plt.xticks(rotation=45, ha='right')
plt.title("Aanwezigheid op Trainingen (Gesorteerd op aanwezigheid, TYPE = T)")
plt.xlabel("Datum")
plt.ylabel("Voornaam")
plt.tight_layout()
plt.savefig("puntengrafiek_python.png", dpi=300)
plt.show()
