import csv
import argparse
import unicodedata
import ndjson
from collections import Counter
from random import shuffle

header = ['record_id', 'given_name', 'family_name', 'DOB', 'sex', 'phone_number',
  'household_street_address', 'household_zip', 'parent_given_name' , 'parent_family_name',
  'parent_email']

report = {}
for h in header:
  report[h] = Counter()

export_count = 0

parser = argparse.ArgumentParser(description='Tool for extracting, validating and cleaning data for CODI PPRL')
parser.add_argument('--bulkfile', nargs=1, required=True, help='Path to bulk FHIR patient resources')
args = parser.parse_args()

bulkfile_path = args.bulkfile[0]

output_rows = []


with open(bulkfile_path) as f:
  reader = ndjson.reader(f)

  for patient in reader:
    patient_row = []
    patient_row.append(patient['id'])
    patient_row.append(patient['name'][0]['given'][0])
    patient_row.append(patient['name'][0]['family'])
    patient_row.append(patient['birthDate'])
    patient_row.append(patient['gender'])
    patient_row.append(patient['address'][0]['line'][0])
    patient_row.append(patient['address'][0].get('postalCode'))
    patient_row.append("")
    patient_row.append("")
    patient_row.append("")
    output_rows.append(patient_row)
    export_count += 1

shuffle(output_rows)

with open('pii.csv', 'w', newline='', encoding='utf-8') as csvfile:
  writer = csv.writer(csvfile)
  writer.writerow(header)
  for output_row in output_rows:
    writer.writerow(output_row)

print('Total records exported: {}'.format(export_count))
print('')
