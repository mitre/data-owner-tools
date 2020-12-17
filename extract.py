import csv
import argparse
import unicodedata
from  dataownertools import clean, report
from collections import Counter
from random import shuffle
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.sql import select

def case_insensitive_lookup(row, desired_key):
  if row.has_key(desired_key):
    return row[desired_key]
  else:
    for actual_key in row.keys():
      if actual_key.lower() == desired_key:
        return row[actual_key]

header = ['record_id', 'given_name', 'family_name', 'DOB', 'sex', 'phone_number',
  'household_street_address', 'household_zip', 'parent_given_name' , 'parent_family_name',
  'parent_email']

report = report.Report(header)

export_count = 0

parser = argparse.ArgumentParser(description='Tool for extracting, validating and cleaning data for CODI PPRL')
parser.add_argument('--db', nargs=1, required=True, help='Database connection string')
args = parser.parse_args()

connection_string = args.db[0]

output_rows = []

engine = create_engine(connection_string)
with engine.connect() as connection:
  meta = MetaData()
  identity = Table('identifier', meta, autoload=True, autoload_with=engine, schema='codi')

  query = select([identity])
  results = connection.execute(query)
  for row in results:
    output_row = [case_insensitive_lookup(row, 'patid')]
    given_name = case_insensitive_lookup(row, 'given_name')
    report.validate('given_name', given_name)
    output_row.append(clean.name(given_name))
    family_name = case_insensitive_lookup(row, 'family_name')
    report.validate('family_name', family_name)
    output_row.append(clean.name(family_name))
    birth_date = case_insensitive_lookup(row, 'birth_date')
    output_row.append(birth_date.isoformat())
    sex = case_insensitive_lookup(row, 'sex')
    report.validate('sex', sex)
    output_row.append(sex.strip())
    phone_number = case_insensitive_lookup(row, 'household_phone')
    report.validate('phone_number', phone_number)
    output_row.append(clean.phone(phone_number))
    household_street_address = case_insensitive_lookup(row, 'household_street_address')
    report.validate('household_street_address', household_street_address)
    output_row.append(clean.address(household_street_address))
    household_zip = case_insensitive_lookup(row, 'household_zip')
    report.validate('household_zip', household_zip)
    output_row.append(clean.zip(household_zip))
    parent_given_name = case_insensitive_lookup(row, 'parent_given_name')
    report.validate('parent_given_name', parent_given_name)
    output_row.append(clean.name(parent_given_name))
    parent_family_name = case_insensitive_lookup(row, 'parent_family_name')
    report.validate('parent_family_name', parent_family_name)
    output_row.append(clean.name(parent_family_name))
    parent_email = case_insensitive_lookup(row, 'household_email')
    report.validate('parent_email', parent_email)
    output_row.append(clean.email(parent_email))
    output_rows.append(output_row)
    export_count += 1

shuffle(output_rows)

with open('pii.csv', 'w', newline='', encoding='utf-8') as csvfile:
  writer = csv.writer(csvfile)
  writer.writerow(header)
  for output_row in output_rows:
    writer.writerow(output_row)

print('Total records exported: {}'.format(export_count))
print('')

report.print()
