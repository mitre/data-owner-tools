import csv
import argparse
from pathlib import Path

parser = argparse.ArgumentParser(description='Tool for translating LINK_IDs back into PATIDs')
parser.add_argument('--source', nargs=1, required=True, help='Source PII CSV file')
parser.add_argument('--links', nargs=1, required=True, help='LINK_ID CSV file')
args = parser.parse_args()

source_file = Path(args.source[0])

headers = ['LINK_ID', 'PATID']
pii_lines = []

with open(source_file) as source:
  source_reader = csv.reader(source)
  next(source)
  pii_lines = list(source_reader)

links_file = Path(args.links[0])

with open('linkidtopatid.csv', 'w', newline='', encoding='utf-8') as csvfile:
  writer = csv.writer(csvfile)
  writer.writerow(headers)
  with open(links_file) as links:
    links_reader = csv.reader(links)
    next(links_reader)
    for row in links_reader:
      link_id = row[0]
      patid = pii_lines[int(row[1])][0]
      writer.writerow([link_id, patid])