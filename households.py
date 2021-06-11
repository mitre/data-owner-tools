import os
import sys
import subprocess
import csv
import uuid
from pathlib import Path
import argparse
import textdistance
import usaddress
from zipfile import ZipFile

parser = argparse.ArgumentParser(description='Tool for extracting households from pii.csv')
parser.add_argument('--source', nargs=1, required=True, help='Source PII CSV file')
parser.add_argument('--schema', nargs=1, required=True, help='Location of linkage schema')
parser.add_argument('--secretfile', nargs=1, required=True, help='Location of de-identification secret file')
args = parser.parse_args()

# Could make this pull from pii.csv folder and iterate over files (see patid translate script)
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
pii_lines = []
output_rows = []
MATCH_THRESHOLD = 0.7

if not os.path.exists('output'):
  os.mkdir('output')
if not os.path.exists('output/households'):
  os.mkdir('output/households')

with open(source_file) as source:
  source_reader = csv.reader(source)
  next(source_reader)
  pii_lines = list(source_reader)

def addr_parse(addr):
  addr_tuples = usaddress.parse(addr)
  address_dict = {'number': '', 'street': '', 'suffix': '', 'prefix': '', 'value': '', }
  for pair in addr_tuples:
    if pair[1] == 'AddressNumber':
      address_dict['number'] = pair[0]
    elif pair[1] == 'StreetName':
      address_dict['street'] = pair[0]
    elif pair[1] == 'StreetNamePostType':
      address_dict['suffix'] = pair[0]
    elif pair[1] == 'OccupancyType':
      address_dict['prefix'] = pair[0]
    elif pair[1] == 'OccupancyIdentifier':
      address_dict['value'] = pair[0]
  return address_dict

# Python version of FRIL matchStreetName functionality
def address_distance(a1, a2):
  score = 0
  secondary_score = 0
  # Need to parse because usaddress returns list of tuples without set indices
  addr1 = addr_parse(a1)
  addr2 = addr_parse(a2)
  # Alternative way to parse usaddress.parse(a1) return (less efficient I think)
  # addr_number_1 = next((v[0] for v in addr1 if v[1] == 'AddressNumber'), None)

  # Change weights based on existance of second level address
  if not addr1['prefix'] and not addr2['prefix'] and not addr1['value'] and not addr2['value']:
    weight_number = 0.5
    weight_street_name = 0.5
    weight_secondary = 0
  else:
    weight_number = 0.3
    weight_street_name = 0.5
    weight_secondary = 0.2

  if addr1['number'] and addr2['number']:
    score += weight_number * textdistance.hamming.normalized_similarity(addr1['number'], addr2['number'])

  max_score_str = 0
  if addr1['street'] and addr2['street']:
    # Try perfect match
    if addr1['suffix'] and addr2['suffix']:
      max_score_str = textdistance.jaro_winkler(addr1['street'],addr2['street']) * 0.8
      if max_score_str:
        max_score_str += textdistance.jaro_winkler(addr1['suffix'],addr2['suffix']) * 0.2
    # Try removing either suffix
    if addr1['suffix']:
      max_score_str = max(max_score_str, textdistance.jaro_winkler(addr1['street']+' '+addr1['suffix'],addr2['street']))
    if addr2['suffix']:
      max_score_str = max(max_score_str, textdistance.jaro_winkler(addr2['street']+' '+addr2['suffix'],addr1['street']))
    # Try ignoring suffixes but adjust value by 0.7
    adjustment = 1.0 if not addr1['suffix'] and not addr2['suffix'] else 0.7
    max_score_str = max(max_score_str, textdistance.jaro_winkler(addr1['street'],addr2['street']) * adjustment)
  else:
    # No street name in one address or both, test each with prefix of other
    if addr1['street'] and addr2['suffix']:
      max_score_str = max(max_score_str, textdistance.jaro_winkler(addr1['street']+' '+addr1['suffix'],addr2['suffix']) * 0.7)
      max_score_str = max(max_score_str, textdistance.jaro_winkler(addr1['street'], addr2['suffix']) * 0.7)
    if addr2['street'] and addr1['suffix']:
      max_score_str = max(max_score_str, textdistance.jaro_winkler(addr2['street']+' '+addr2['suffix'],addr1['suffix']) * 0.7)
      max_score_str = max(max_score_str, textdistance.jaro_winkler(addr2['street'], addr1['suffix']) * 0.7)
    if not addr1['street'] and not addr2['street'] and addr1['suffix'] and addr1['street']:
      max_score_str = max(max_score_str, textdistance.jaro_winkler(addr1['suffix'], addr2['suffix']) * 0.1)

  if max_score_str:
    score += max_score_str * weight_street_name

  # Second level score if something to compare, else leave secondary_score = 0
  if (addr1['prefix'] and addr2['prefix']) or (addr1['value'] and addr2['value']):
    max_score_sec = 0
    if addr1['value'] and addr2['value']:
      if addr1['prefix'] and addr2['prefix']:
        max_score_sec = textdistance.jaro_winkler(addr1['value'], addr2['value']) * 0.8
        max_score_sec += textdistance.jaro_winkler(addr1['prefix'], addr2['prefix']) * 0.2
      if addr1['prefix']:
        max_score_sec = max(max_score_sec, textdistance.jaro_winkler(addr1['prefix']+' '+addr1['value'], addr2['value']))
      if addr2['prefix']:
        max_score_sec = max(max_score_sec, textdistance.jaro_winkler(addr2['prefix']+' '+addr2['value'], addr1['value']))
      adjustment_sec = 1 if not addr1['prefix'] and not addr2['prefix'] else 0.7
      max_score_sec = max(max_score_sec, textdistance.jaro_winkler(addr1['value'], addr2['value']) * adjustment_sec)
    else:
      if addr1['value']:
        max_score_sec = max(max_score_sec, textdistance.jaro_winkler(addr1['prefix']+addr1['value'],addr2['prefix']) * 0.6)
        max_score_sec = max(max_score_sec, textdistance.jaro_winkler(addr1['value'],addr2['prefix']) * 0.6)
      if addr2['value']:
        max_score_sec = max(max_score_sec, textdistance.jaro_winkler(addr2['prefix']+addr2['value'],addr1['prefix']) * 0.6)
        max_score_sec = max(max_score_sec, textdistance.jaro_winkler(addr2['value'],addr1['prefix']) * 0.6)
    max_score_sec = max(max_score_sec, textdistance.jaro_winkler(addr1['prefix']+addr1['value'], addr2['prefix']+addr2['value']) * 0.8)
    if max_score_sec:
      secondary_score = max_score_sec

  # See if simple string compare of all things combined with a 0.6 adjustment is better
  score = max(score, textdistance.jaro_winkler(a1, a2) * (weight_number + weight_street_name) * 0.6) + (secondary_score * weight_secondary)
  return score

def match_households(already_added, pat_clks, line):
  for position, line_compare in enumerate(pii_lines):
    if position in already_added:
      continue
    weighted_fn = textdistance.jaro_winkler(line[2], line_compare[2]) * 0.2
    weighted_phone = textdistance.jaro_winkler(line[5], line_compare[5]) * 0.2
    weighted_addr = address_distance(line[6], line_compare[6]) * 0.3
    weighted_zip = textdistance.hamming.normalized_similarity(line[7], line_compare[7]) * 0.3
    total_distance = weighted_fn + weighted_zip + weighted_addr + weighted_phone
    if total_distance > MATCH_THRESHOLD:
      pat_clks.append(position)
      already_added.append(position)

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
    match_households(already_added, pat_clks, line)
    print(pat_clks)
    string_pat_clks = [str(int) for int in pat_clks]
    pat_string = ','.join(string_pat_clks)
    writer.writerow([hclk_position, pat_string])
    output_row = [line[2],line[5],line[6],line[7]]
    hclk_position += 1
    output_rows.append(output_row)

with open('households_pii.csv', 'w', newline='', encoding='utf-8') as house_csv:
  writer = csv.writer(house_csv)
  writer.writerow(household_pii_headers)
  for output_row in output_rows:
    writer.writerow(output_row)

with open(schema_file, 'r') as schema:
  file_contents = schema.read()
  if 'doubleHash' in file_contents:
    sys.exit('The following schema uses doubleHash, which is insecure: ' + str(schema_file))
output_file = Path('output/households/fn-phone-addr-zip.json')
subprocess.run(["anonlink", "hash", "households_pii.csv", secret, str(schema_file), str(output_file)])

with ZipFile('garbled_households.zip', 'w') as garbled_zip:
  garbled_zip.write(output_file)
  garbled_zip.write('output/households/households.csv')
