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

    # 1. Haal de eigenschappen op van een personeelslid (pas id aan indien nodig)
    db.connect()
    personeelslid_query = "SELECT * FROM personeelslid WHERE id = 1"
    personeelslid = db.execute_query(personeelslid_query)
    db.close()

    # 2. Haal alle onderhoudstaken op
    db.connect()
    ondehoudstaken_query = "SELECT * FROM onderhoudstaak"
    onderhoudstaken = db.execute_query(ondehoudstaken_query)
    db.close()

    # Voorbeeld: print resultaten overzichtelijk
    pprint.pp(personeelslid)
    print(personeelslid[0]['naam'])
    #pprint.pp(onderhoudstaken)

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