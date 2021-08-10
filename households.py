import os
import sys
import subprocess
from pathlib import Path
import argparse
from zipfile import ZipFile
import csv

from households.matching import match_households

parser = argparse.ArgumentParser(description='Tool for extracting households from pii.csv')
parser.add_argument('--source', nargs=1, required=True, help='Source PII CSV file')
parser.add_argument('--schema', nargs=1, required=True, help='Location of linkage schema')
parser.add_argument('--secretfile', nargs=1, required=True, help='Location of de-identification secret file')
args = parser.parse_args()

source_file = Path(args.source[0])
schema_file = Path(args.schema[0])
secret = None
secret_file = Path(args.secretfile[0])

if not source_file.exists():
  sys.exit('Unable to find source_file' + str(source_file))
if not schema_file.exists():
  sys.exit('Unable to find schema_file' + str(schema_file))
if not secret_file.exists():
  sys.exit('Unable to find secret file' + str(secret_file))

with open(secret_file, 'r') as secret_text:
  secret = secret_text.read()
  if len(secret) < 256:
    sys.exit('Secret length not long enough to ensure proper de-identification')

headers = ['HOUSEHOLD_POSITION','PAT_CLK_POSITIONS']
household_pii_headers = ['family_name','phone_number','household_street_address', 'household_zip']
household_pos_pid_headers = ['household_position','pid']
pos_pid_rows = []
hid_pat_id_rows = []
pii_lines = []
output_rows = []

if not os.path.exists('output'):
  os.mkdir('output')
if not os.path.exists('output/households'):
  os.mkdir('output/households')

with open(source_file) as source:
  source_reader = csv.reader(source)
  next(source_reader)
  pii_lines = list(source_reader)

with open('output/households/households.csv', 'w', newline='', encoding='utf-8') as csvfile:
  writer = csv.writer(csvfile)
  writer.writerow(headers)
  already_added = []
  hclk_position = 0
  # Match households
  for position, line in enumerate(pii_lines):
    if position in already_added:
      continue
    already_added.append(position)
    pat_clks = [position]
    pat_ids = [line[0]]
    match_households(already_added, pat_clks, pat_ids, line, pii_lines)
    print(pat_clks)
    string_pat_clks = [str(int) for int in pat_clks]
    pat_string = ','.join(string_pat_clks)
    writer.writerow([hclk_position, pat_string])
    pos_pid_rows.append([hclk_position,line[0]])
    for patid in pat_ids:
      hid_pat_id_rows.append([hclk_position, patid])
    output_row = [line[2],line[5],line[6],line[7]]
    hclk_position += 1
    output_rows.append(output_row)

with open('temp-data/households_pii.csv', 'w', newline='', encoding='utf-8') as house_csv:
  writer = csv.writer(house_csv)
  writer.writerow(household_pii_headers)
  for output_row in output_rows:
    writer.writerow(output_row)

# Format is used for scoring
with open('temp-data/hh_pos_patids.csv', 'w', newline='', encoding='utf-8') as hpos_pat_csv:
  writer = csv.writer(hpos_pat_csv)
  writer.writerow(household_pos_pid_headers)
  for output_row in hid_pat_id_rows:
    writer.writerow(output_row)

# Format is used for generating a hid to hh_pos for full answer key
with open('temp-data/household_pos_pid.csv', 'w', newline='', encoding='utf-8') as house_pos_csv:
  writer = csv.writer(house_pos_csv)
  writer.writerow(household_pos_pid_headers)
  for output_row in pos_pid_rows:
    writer.writerow(output_row)

with open(schema_file, 'r') as schema:
  file_contents = schema.read()
  if 'doubleHash' in file_contents:
    sys.exit('The following schema uses doubleHash, which is insecure: ' + str(schema_file))
output_file = Path('output/households/fn-phone-addr-zip.json')
subprocess.run(["anonlink", "hash", "temp-data/households_pii.csv", secret, str(schema_file), str(output_file)])

with ZipFile('output/garbled_households.zip', 'w') as garbled_zip:
  garbled_zip.write(output_file)
  garbled_zip.write('output/households/households.csv')
