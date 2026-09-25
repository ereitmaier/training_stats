#!/usr/bin/env python3

import argparse
import os
import sys
import yaml


def verwerk_spelers_lijst(details):
    """Helper om een lijst van spelers op te halen uit een lijst of dictionary structuur."""
    if isinstance(details, dict):
        return details.get("Spelers", [])
    elif isinstance(details, list):
        return details
    return []


def formatteer_selecties(selecties):
    """Genereert WhatsApp-bericht voor wedstrijdselecties."""
    whatsapp_output = "⚽ *Indeling Selecties* ⚽\n\n"

    for groep, details in selecties.items():
        if groep.lower() == "overige":
            whatsapp_output += "------------------------------\n"
            if isinstance(details, dict):
                totaal_overige = sum(
                    len(verwerk_spelers_lijst(v)) for v in details.values()
                )
                whatsapp_output += f"📌 *{groep.upper()}* ({totaal_overige}):\n\n"
                for code, subdetails in details.items():
                    spelers = verwerk_spelers_lijst(subdetails)
                    whatsapp_output += f"❓ *{code}* ({len(spelers)}):\n"
                    whatsapp_output += ", ".join(spelers) + "\n\n"
            elif isinstance(details, list):
                whatsapp_output += f"📌 *{groep.upper()}* ({len(details)}):\n"
                whatsapp_output += ", ".join(details) + "\n\n"
        else:
            spelers = verwerk_spelers_lijst(details)
            whatsapp_output += f"🟢 *{groep}* ({len(spelers)}):\n"
            whatsapp_output += ", ".join(spelers) + "\n\n"

    return whatsapp_output.strip()


def formatteer_trainingsgroepen(trainingsgroepen):
    """Genereert WhatsApp-bericht voor trainingsgroepen."""
    whatsapp_output = "⚽ *Indeling Trainingsgroepen* ⚽\n\n"

    for groep, details in trainingsgroepen.items():
        if groep.lower() == "overige":
            whatsapp_output += "------------------------------\n"
            whatsapp_output += f"📌 *{groep.upper()}*\n\n"
            if isinstance(details, dict):
                for subcategorie, subdetails in details.items():
                    spelers = verwerk_spelers_lijst(subdetails)
                    whatsapp_output += f"❓ *{subcategorie}* ({len(spelers)}):\n"
                    whatsapp_output += ", ".join(spelers) + "\n\n"
        else:
            spelers = verwerk_spelers_lijst(details)
            whatsapp_output += f"🟢 *{groep}* ({len(spelers)}):\n"
            whatsapp_output += ", ".join(spelers) + "\n\n"

    return whatsapp_output.strip()


def main():
    parser = argparse.ArgumentParser(
        description="Zet een YAML-bestand (wedstrijd of training) om naar een WhatsApp-bericht."
    )
    parser.add_argument(
        "yaml_file",
        type=str,
        nargs="?",
        default="-",
        help="Pad naar het YAML-bestand of '-' voor stdin (standaard: stdin)",
    )

    args = parser.parse_args()

    # 1. Lees data in vanuit stdin of vanuit een bestand
    if args.yaml_file == "-" or not sys.stdin.isatty() and args.yaml_file == "-":
        try:
            data = yaml.safe_load(sys.stdin)
        except Exception as e:
            print(f"❌ Fout bij het lezen van de input via stdin: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        if not os.path.exists(args.yaml_file):
            print(f"❌ Fout: Het bestand '{args.yaml_file}' is niet gevonden.", file=sys.stderr)
            sys.exit(1)

        try:
            with open(args.yaml_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except Exception as e:
            print(f"❌ Fout bij het lezen van het YAML-bestand: {e}", file=sys.stderr)
            sys.exit(1)

    if not data or not isinstance(data, dict):
        print("❌ Fout: Ongeldige of lege YAML-data.", file=sys.stderr)
        sys.exit(1)

    # 2. Bepaal type op basis van YAML inhoud
    if "Selecties" in data:
        whatsapp_output = formatteer_selecties(data["Selecties"])
    elif "Trainingsgroep" in data:
        whatsapp_output = formatteer_trainingsgroepen(data["Trainingsgroep"])
    else:
        print("❌ Fout: Geen sleutel 'Selecties' of 'Trainingsgroep' gevonden in YAML-data.", file=sys.stderr)
        sys.exit(1)

    # 3. Print het resultaat
    print("--- WhatsApp Bericht ---")
    print(whatsapp_output)


if __name__ == "__main__":
    main()