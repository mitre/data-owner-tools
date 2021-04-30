import csv
import argparse
import os
import sys
from pathlib import Path


def linkids_to_patids(source_file, links_file, output_dir):
    headers = ['LINK_ID', 'PATID']

    with open(source_file) as source:
        source_reader = csv.reader(source)
        pii_lines = list(source_reader)[1::]

    with open(f'{output_dir}/linkidtopatid.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)
        with open(links_file) as links:
            links_reader = csv.reader(links)
            next(links_reader)
            for row in links_reader:
                link_id = row[0]
                pat_id = pii_lines[int(row[1])][0]
                writer.writerow([link_id, pat_id])
    return f"Wrote CSV file to {output_dir}/linkidtopatid.csv"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Tool for translating LINK_IDs back into PATIDs')
    parser.add_argument('--source', nargs=1, required=True, help='Source PII CSV file')
    parser.add_argument('--links', nargs=1, required=True, help='LINK_ID CSV file')
    args = parser.parse_args()

    source_file = Path(args.source[0])
    links_file = Path(args.links[0])

    sys.exit(linkids_to_patids(source_file, links_file, "."))
