import csv
import argparse
import unicodedata
import ndjson
from  dataownertools import clean, report
from collections import Counter
from random import shuffle

header = ['record_id', 'given_name', 'family_name', 'DOB', 'sex', 'phone_number',
  'household_street_address', 'household_zip', 'parent_given_name' , 'parent_family_name',
  'parent_email']

report = report.Report(header)

export_count = 0

parser = argparse.ArgumentParser(description='Tool for extracting, validating and cleaning data for CODI PPRL')
parser.add_argument('--bulkfile', nargs=1, required=True, help='Path to bulk FHIR patient resources')
args = parser.parse_args()

bulkfile_path = args.bulkfile[0]

output_rows = []

with open(bulkfile_path) as f:
  reader = ndjson.reader(f)

  # TODO: null safe search when digging through the Patient resource
  for patient in reader:
    patient_row = []
    record_id = patient['id']
    patient_row.append(record_id)
    given_name = patient['name'][0]['given'][0]
    report.validate('given_name', given_name)
    patient_row.append(clean.name(given_name))
    family_name = patient['name'][0]['family']
    report.validate('family_name', family_name)
    patient_row.append(clean.name(family_name))
    patient_row.append(patient['birthDate'])
    sex = patient['gender']
    report.validate('sex', sex)
    patient_row.append(sex[0].upper())
    phone_number = patient['telecom'][0]['value']
    report.validate('phone_number', phone_number)
    patient_row.append(clean.phone(phone_number))
    household_street_address = patient['address'][0]['line'][0]
    report.validate('household_street_address', household_street_address)
    patient_row.append(clean.address(household_street_address))
    household_zip = patient['address'][0].get('postalCode')
    report.validate('household_zip', household_zip)
    patient_row.append(clean.zip(household_zip))
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
