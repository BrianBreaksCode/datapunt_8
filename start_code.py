# Imports
from pathlib import Path
import json
import pprint
from database_wrapper import Database
import secrets


#TODO: Implementeer functie
#TODO: Taalconsistentie Nederlands + Engels -> English

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

    # 2. Haal alle onderhoudstaken op
    # FR6. Alleen onderhoudstaken toevoegen als:
    # - beroepstype overeenkomt
    # - personeelslid bevoegd is (of hogere bevoegdheid heeft)
    # - fysieke belasting taak <= max van personeelslid

    # FR7. Hogere bevoegdheden mogen ook lagere taken doen; hoogste bevoegdheid krijgt voorrang.

    # FR8. Taken met hoge prioriteit (en specialistisch) eerst, daarna lage prioriteit.

    def get_onderhoudstaken(db, personeelslid: dict):
        try:
            beroepstype = personeelslid['beroepstype']
            # Determine the list of allowed bevoegdheden for this personeelslid
            bevoegdheid = BEVOEGDHEID_HIERARCHY[BEVOEGDHEID_HIERARCHY.index(personeelslid['bevoegdheid']):]
            # Build the SQL IN clause for bevoegdheid
            bevoegdheid_in_clause = "('" + "', '".join(bevoegdheid) + "')"
            specialisatie_in_clause = "('" + "', '".join(personeelslid['specialist_in_attracties']) + "')" \
                if personeelslid['specialist_in_attracties'] else "('')"
            # If specialist_in_attracties is None, use an empty list
            specialist = personeelslid['specialist_in_attracties'] if personeelslid[
                                                                          'specialist_in_attracties'] is not None else []
            db.connect()
            onderhoudstaken_query = (
                f"SELECT * FROM onderhoudstaak"
                f" WHERE beroepstype = '{beroepstype}'"
                f" AND bevoegdheid in {bevoegdheid_in_clause}"
                f" AND fysieke_belasting <= {personeelslid['max_fysieke_belasting']}"
                f" ORDER BY case prioriteit when 'hoog' then 1 when 'laag' then 2 end, "
                f" attractie in {specialisatie_in_clause}"
            )
            return db.execute_query(onderhoudstaken_query)
        finally:
            db.close()

    def select_taak_combinatie_op_werktijd(onderhoudstaken, werktijd):
        takenlijst = []
        totale_duur = 0
        for taak in onderhoudstaken:
            if totale_duur + taak['duur'] < werktijd:
                takenlijst.append(taak)
                totale_duur += taak['duur']
        print(f"{totale_duur}/{werktijd} minuten gevuld")
        return takenlijst

    # 3. Haal weergegevens op (optioneel)
    #TODO: Implementeer functie

    # 4. Bouw de dagtakenlijst dictionary
    #TODO: Implementeer functie
    def bouw_dagtakenlijst(personeelslid_processed, onderhoudstaken):
        pass

    # example dagtakenlijst bouwen
    dagtakenlijst = {
        "personeelsgegevens": {
            "naam": "Voorbeeld"
        },
        "weergegevens": {
            # Vul aan met weergegevens
        },
        "dagtaken": [],  # Hier komt een lijst met alle dagtaken
        "totale_duur": 0  # Pas aan naar daadwerkelijke totale duur
    }

    # 5. Schrijf de dagtakenlijst naar een JSON-bestand
    #TODO: Implementeer functie
    with open('dagtakenlijst_personeelslid_x.json', 'w') as json_bestand_uitvoer:
        json.dump(dagtakenlijst, json_bestand_uitvoer, indent=4)

    # Print testing
    personeels_id = 1  # Pas dit aan naar het gewenste personeelslid ID
    personeelslid_raw = get_personeelslid(db, personeels_id)
    personeelslid_processed = transform_personeelslid(personeelslid_raw)
    # pprint.pp(personeelslid_processed)

    onderhoudstaken_suitable = get_onderhoudstaken(db, personeelslid_processed)
    # pprint.pp(onderhoudstaken_suitable)

    onderhoudstaken_processed = select_taak_combinatie_op_werktijd(onderhoudstaken_suitable,
                                                                   personeelslid_processed['werktijd'])
    # pprint.pp(onderhoudstaken_processed)
if __name__ == "__main__":
    main()
