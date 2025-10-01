# Imports
from pathlib import Path
import json
import pprint
from database_wrapper import Database
import secrets

def main() -> None:
    # Database setup
    # Pas deze parameters aan voor je eigen database
    # (host, gebruiker, wachtwoord, database)
    db = Database(host=secrets.host,
                  gebruiker=secrets.gebruiker,
                  wachtwoord=secrets.wachtwoord,
                  database=secrets.database)

    BEVOEGDHEID_HIERARCHY = ['Senior', 'Medior', 'Junior', 'Stagiair']

    # 1. Haal personeelsgegevens op
    def get_personeelslid(db, personeels_id: int):
        try:
            db.connect()
            personeelslid_query = (f"SELECT naam, werktijd, beroepstype, bevoegdheid, "
                                   f"specialist_in_attracties, pauze_opsplitsen, "
                                   f"leeftijd, verlaagde_fysieke_belasting "
                                   f"FROM personeelslid WHERE id = {personeels_id}")
            return db.execute_query(personeelslid_query)
        finally:
            db.close()

    def transform_personeelslid(personeelslid_raw):
        if not personeelslid_raw:
            return None
        personeelslid_processing = personeelslid_raw[0]
        personeelslid_transformed = {
            "naam": personeelslid_processing['naam'],
            "werktijd": personeelslid_processing['werktijd'],
            "beroepstype": personeelslid_processing['beroepstype'],
            "bevoegdheid": personeelslid_processing['bevoegdheid'],
            "specialist_in_attracties": personeelslid_processing['specialist_in_attracties'].split(',') if
            personeelslid_processing['specialist_in_attracties'] else None,
            "pauze_opsplitsen": bool(personeelslid_processing['pauze_opsplitsen']),
            "max_fysieke_belasting": max_fysieke_belasting_berekenen(personeelslid_processing['leeftijd'],
                                                                     personeelslid_processing[
                                                                         'verlaagde_fysieke_belasting']),
        }
        return personeelslid_transformed

    def max_fysieke_belasting_berekenen(personeel_leeftijd: int, arbo):
        if arbo != 0:
            return arbo
        else:
            if personeel_leeftijd < 25:
                return 25
            elif 25 <= personeel_leeftijd <= 51:
                return 40
            elif personeel_leeftijd >= 51:
                return 20
            else:
                return 0

    # --- Bouw de dagtakenlijst dictionary ---
    dagtakenlijst = {
        "personeelsgegevens": {
            "naam": personeelslid[0]['naam'] # Vul aan met andere eigenschappen indien nodig
        },
        "weergegevens": {
            # Vul aan met weergegevens
        },
        "dagtaken": [], # Hier komt een lijst met alle dagtaken
        "totale_duur": 0 # Pas aan naar daadwerkelijke totale duur
    }

    # --- Schrijf de dictionary weg naar een JSON-bestand ---
    with open('dagtakenlijst_personeelslid_x.json', 'w') as json_bestand_uitvoer:
        json.dump(dagtakenlijst, json_bestand_uitvoer, indent=4)

if __name__ == "__main__":
    main()