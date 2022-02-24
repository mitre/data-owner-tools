import csv
import argparse
import unicodedata
from collections import Counter
from random import shuffle
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.sql import select

def validate(report, field, value):
  if value is None:
    report[field]['NULL Value'] += 1
    return
  if not value.isascii():
    report[field]['Contains Non-ASCII Characters'] += 1
  if not value.isprintable():
    report[field]['Contains Non-printable Characters'] += 1
  if value.isspace():
    report[field]['Empty String'] += 1

def clean_name(name):
  if name is None:
    return None
  ascii_name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore')
  return ascii_name.strip().upper().decode('ascii')

def clean_phone(phone):
  if phone is None:
    return None
  return ''.join(filter(lambda x: x.isdigit(), phone.strip()))

def clean_address(address):
  if address is None:
    return None
  ascii_address = unicodedata.normalize('NFKD', address).encode('ascii', 'ignore')
  return ascii_address.strip().upper().decode('ascii')

def clean_zip(zip):
  if zip is None:
    return None
  return zip.strip()

def clean_email(email):
  if email is None:
    return None
  ascii_email = unicodedata.normalize('NFKD', email).encode('ascii', 'ignore')
  return ascii_email.strip().upper().decode('ascii')

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

report = {}
for h in header:
  report[h] = Counter()

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
    validate(report, 'given_name', given_name)
    output_row.append(clean_name(given_name))
    family_name = case_insensitive_lookup(row, 'family_name')
    validate(report, 'family_name', family_name)
    output_row.append(clean_name(family_name))
    birth_date = case_insensitive_lookup(row, 'birth_date')
    output_row.append(birth_date.strftime('%y%m%d'))
    sex = case_insensitive_lookup(row, 'sex')
    validate(report, 'sex', sex)
    output_row.append(sex.strip())
    phone_number = case_insensitive_lookup(row, 'household_phone')
    validate(report, 'phone_number', phone_number)
    output_row.append(clean_phone(phone_number))
    household_street_address = case_insensitive_lookup(row, 'household_street_address')
    validate(report, 'household_street_address', household_street_address)
    output_row.append(clean_address(household_street_address))
    household_zip = case_insensitive_lookup(row, 'household_zip')
    validate(report, 'household_zip', household_zip)
    output_row.append(clean_zip(household_zip))
    parent_given_name = case_insensitive_lookup(row, 'parent_given_name')
    validate(report, 'parent_given_name', parent_given_name)
    output_row.append(clean_name(parent_given_name))
    parent_family_name = case_insensitive_lookup(row, 'parent_family_name')
    validate(report, 'parent_family_name', parent_family_name)
    output_row.append(clean_name(parent_family_name))
    parent_email = case_insensitive_lookup(row, 'household_email')
    validate(report, 'parent_email', parent_email)
    output_row.append(clean_email(parent_email))
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

for field, counter in report.items():
  print(field)
  print('--------------------')
  for issue, count in counter.items():
    print("{}: {}".format(issue, count))
  print('')

