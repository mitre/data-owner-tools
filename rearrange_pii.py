import argparse
import csv
from datetime import date
import json

parser = argparse.ArgumentParser(description='Tool for rearraging PII CSV based on two sets of hashes')
parser.add_argument('--newpii', required=True, help='Current PII CSV file')
parser.add_argument('--oldhashes', required=True, help='Hashes constructed from the PII file to recreate')
parser.add_argument('--newhashes', required=True, help='Hashes constructed from the current PII file')

args = parser.parse_args()

header = ['record_id', 'given_name', 'family_name', 'DOB', 'sex', 'phone_number',
  'household_street_address', 'household_zip', 'parent_given_name' , 'parent_family_name',
  'parent_email']

# step 1, determine the alignment of old hashes to new hashes
with open(args.oldhashes) as oldhashesfile:
    old_hash_json = json.load(oldhashesfile)
    old_hashes = old_hash_json["clks"]

with open(args.newhashes) as newhashesfile:
    new_hash_json = json.load(newhashesfile)
    new_hashes = new_hash_json["clks"]

if len(old_hashes) != len(new_hashes):
    print(f"Hash lengths do not align! Exiting.")
    exit(1)

# a couple possible approaches here:
#  1. load new hashes into a dictionary: {hash: line_number} 
#     then iterate over each hash in old hashes to find the line number
#  2. turn each hash into a tuple (hash, line num) then sort both by hash hashes
#
# for simplicity of validation I go with #2 here
old_hashes_with_line_num = list(enumerate(old_hashes))
new_hashes_with_line_num = list(enumerate(new_hashes))

sorted_old = sorted(old_hashes_with_line_num, key=lambda t: t[1])
sorted_new = sorted(new_hashes_with_line_num, key=lambda t: t[1])

line_num_map = {}

for i in range(len(old_hashes)):
    if sorted_old[i][1] != sorted_new[i][1]:
        print("Hash mismatch!")
        exit(1)

    line_num_map[sorted_old[i][0]] = sorted_new[i][0]

# import pdb; pdb.set_trace()

# step 2, read pii.csv to a list
with open(args.newpii) as source:
    source_reader = csv.reader(source)
    next(source)  # skip header
    newpii_lines = list(source_reader)

output_rows = []

# step 3, reorder new pii to the old order
for i in range(len(newpii_lines)):
    target_line_num = line_num_map[i]
    target_line = newpii_lines[target_line_num]
    output_rows.append(target_line)

# step 4, write new pii file
today = date.today().strftime("%Y-%m-%d")
rearrangedpiifile = f"pii-{today}.csv"
with open(rearrangedpiifile, 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(header)
    for output_row in output_rows:
        writer.writerow(output_row)
    print(f"Wrote {rearrangedpiifile}")
