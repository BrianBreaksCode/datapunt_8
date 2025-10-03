# Imports
from pathlib import Path
import json
import pprint
from database_wrapper import Database
import secrets


#TODO: Taalconsistentie Nederlands + Engels -> English
#TODO: Docstrings toevoegen
#TODO: Consider solving several 'shadows names from outer scope' warnings

# Database setup
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

def max_fysieke_belasting_berekenen(personeel_leeftijd: int, verlaagde_fysieke_belasting):
    """Calculates the maximum physical workload based on age and any reduced physical workload.

    Args:
        personeel_leeftijd (int): The age of the staff member.
        verlaagde_fysieke_belasting: The reduced physical workload value. If not 0, this value takes precedence.

    Returns:
        int: The maximum physical workload allowed.
    """
    if verlaagde_fysieke_belasting != 0:
        return verlaagde_fysieke_belasting
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
    """Retrieve all maintenance tasks suitable for a given staff member based on their role, authority, and physical capacity.

    Args:
        db (Database): The database connection object.
        personeelslid (dict): Dictionary containing staff member details, including 'beroepstype', 'bevoegdheid',
            'specialist_in_attracties', and 'max_fysieke_belasting'.

    Returns:
        list: List of maintenance task dictionaries that match the staff member's qualifications and constraints.

    Notes:
        - Only tasks matching the staff member's role (beroepstype) are considered. (FR6)
        - Staff can perform tasks at their authority level or below (bevoegdheid hierarchy). (FR6, FR7)
        - Tasks are filtered by the staff member's maximum allowed physical workload. (FR6)
        - Tasks are ordered by priority (high before low)
            and whether the staff member is a specialist for the attraction. (FR8)
    """
    try:
        beroepstype = personeelslid['beroepstype']
        # Determine the list of allowed bevoegdheden for this personeelslid
        bevoegdheid = BEVOEGDHEID_HIERARCHY[BEVOEGDHEID_HIERARCHY.index(personeelslid['bevoegdheid']):]
        # Build the SQL IN clause for bevoegdheid
        # SQL expects values inside the in clause to be a specific way,
        # and this is the best implementation I could piece together
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
            f" attractie in {specialisatie_in_clause} DESC"
        )
        return db.execute_query(onderhoudstaken_query)
    finally:
        db.close()

def select_taak_combinatie_op_werktijd(onderhoudstaken, werktijd):
    """Select a combination of tasks that fit within the given working time.

    This function iterates through a list of maintenance tasks (`onderhoudstaken`)
    and selects tasks until the total duration of the selected tasks
    (`totale_duur`) fits within the available working time (`werktijd`).

    Args:
        onderhoudstaken (list): A list of dictionaries, where each dictionary
            represents a maintenance task and contains at least the key 'duur'
            (duration of the task in minutes).
        werktijd (int): The total available working time in minutes.

    Returns:
        list: A list of selected tasks (dictionaries) that fit within the
        available working time.
    """
    takenlijst = []
    totale_duur = 0
    for taak in onderhoudstaken:
        if totale_duur + taak['duur'] < werktijd:
            takenlijst.append(taak)
            totale_duur += taak['duur']
    return takenlijst

def get_totale_duur(takenlijst):
    return sum(taak['duur'] for taak in takenlijst)

# 3. Haal weergegevens op (optioneel)
#TODO: Implementeer functie

# 4. Bouw de dagtakenlijst dictionary
def bouw_dagtakenlijst(personeelslid, takenlijst):
    return {
        "personeelsgegevens": personeelslid,
        "weergegevens": {
            #TODO: Vul aan met weergegevens
            #   implementeer methode om weergegevens op te halen
            "temperatuur": "20°C",
            "neerslag": "0mm",
            "wind": "5km/h"
        },
        "dagtaken": takenlijst,
        "totale_duur": get_totale_duur(takenlijst)
    }

# 5. Schrijf de dagtakenlijst naar een JSON-bestand
def write_dagtakenlijst_to_json(takenlijst, filename):
    with open(filename, 'w') as json_bestand_uitvoer:
        json.dump(takenlijst, json_bestand_uitvoer, indent=4)

personeelslid_raw = get_personeelslid(db, personeels_id=2)
personeelslid = transform_personeelslid(personeelslid_raw)
onderhoudstaken = get_onderhoudstaken(db, personeelslid)
takenlijst = select_taak_combinatie_op_werktijd(onderhoudstaken, personeelslid['werktijd'])
dagtakenlijst = bouw_dagtakenlijst(personeelslid, takenlijst)
write_dagtakenlijst_to_json(dagtakenlijst, 'dagtakenlijst_personeelslid_x.json')

print(type(db))