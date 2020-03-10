import csv
import argparse
from collections import Counter
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
  return name.strip().upper()

def clean_phone(phone):
  if phone is None:
    return None
  return ''.join(filter(lambda x: x.isdigit(), phone.strip()))

def clean_address(address):
  if address is None:
    return None
  return address.strip().upper()

def clean_zip(zip):
  if zip is None:
    return None
  return zip.strip()

def clean_email(email):
  if email is None:
    return None
  return email.strip().upper()

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

engine = create_engine(connection_string)
with engine.connect() as connection:
  with open('pii.csv', 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(header)

    meta = MetaData()
    identity = Table('identifier', meta, autoload=True, autoload_with=engine)

    query = select([identity])
    results = connection.execute(query)
    for row in results:
      output_row = [row['patid']]
      given_name = row['given_name']
      validate(report, 'given_name', given_name)
      output_row.append(clean_name(given_name))
      family_name = row['family_name']
      validate(report, 'family_name', family_name)
      output_row.append(clean_name(family_name))
      output_row.append(row['birth_date'].isoformat())
      sex = row['sex']
      validate(report, 'sex', sex)
      output_row.append(sex.strip())
      phone_number = row['household_phone']
      validate(report, 'phone_number', phone_number)
      output_row.append(clean_phone(phone_number))
      household_street_address = row['household_street_address']
      validate(report, 'household_street_address', household_street_address)
      output_row.append(clean_address(household_street_address))
      household_zip = row['household_zip']
      validate(report, 'household_zip', household_zip)
      output_row.append(clean_zip(household_zip))
      parent_given_name = row['parent_given_name']
      validate(report, 'parent_given_name', parent_given_name)
      output_row.append(clean_name(parent_given_name))
      parent_family_name = row['parent_family_name']
      validate(report, 'parent_family_name', parent_family_name)
      output_row.append(clean_name(parent_family_name))
      parent_email = row['household_email']
      validate(report, 'parent_email', parent_email)
      output_row.append(clean_email(parent_email))
      writer.writerow(output_row)
      export_count += 1

print('Total records exported: {}'.format(export_count))
print('')

for field, counter in report.items():
  print(field)
  print('--------------------')
  for issue, count in counter.items():
    print("{}: {}".format(issue, count))
  print('')

