import csv
import json
from pathlib import Path

# This script creates the site-specific answer key CSVs out of the
# overall answer_key JSON.
# It iterates over the json and breaks out people based on which site they belong to.
# The columns of the CSV are just the 4 fields from the objects in the JSON.
# Note that nothing actually uses the file_name so it could be stripped
# for file size if necessary.

answer_key = Path("../temp-data/answer_key.json")

sites = ["a", "b", "c", "d", "e", "f"]
site_ids = {}
for site in sites:
    site_ids[site] = set()
    pii_file = Path(f"../temp-data/pii_site_{site}.csv")
    with open(pii_file) as pii_csv:
        pii_reader = csv.reader(pii_csv)
        # Skips header
        next(pii_reader)
        for row in pii_reader:
            site_ids[site].add(row[0])

HEADER = ["record_id", "seed_record_id", "household_id", "file_name"]
new_answer_key = []
with open(answer_key) as f:
    d = json.load(f)

    # {
    #   "14444032-081e-92ac-47dd-eafdbce66365": [
    #     {
    #       "record_id": "19029",
    #       "seed_record_id": "19028",
    #       "household_id": "3879064",
    #       "file_name": "Andrew_Nikla_Denbraber.json"
    #     },
    #     {
    #       "record_id": "19030",
    #       "seed_record_id": "19028",
    #       "household_id": "3879064",
    #       "file_name": "Dr_Andrew_Denbraber.json"
    #     },
    #     {
    #       "record_id": "19029",
    #       "seed_record_id": "19028",
    #       "household_id": "3879064",
    #       "file_name": "Andrew_Nikla_Denbraber.json"
    #     }
    #   ],

    for household in d.values():
        for record in household:
            record_id = record["record_id"]
            seed_record_id = record["seed_record_id"]
            household_id = record["household_id"]
            file_name = record["file_name"]
            key_line = [record_id, seed_record_id, household_id, file_name]
            new_answer_key.append(key_line)

for site in sites:
    csv_out_path = Path(f"../temp-data/site_{site}_key.csv")
    with open(csv_out_path, "w", newline="", encoding="utf-8") as answer_key_csv:
        writer = csv.writer(answer_key_csv)
        writer.writerow(HEADER)
        for output_row in new_answer_key:
            if output_row[0] in site_ids[site]:
                writer.writerow(output_row)
