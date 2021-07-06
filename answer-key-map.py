import csv
from pathlib import Path

systems = ["site_a", "site_b", "site_c", "site_d", "site_e", "site_f"]

# output is clk_pos | h_id
header = ['HOUSEHOLD_POSITION','HOUSEHOLD_ID']
household_dict = {}
full_answer_key_path = Path('/Users/apellitieri/Desktop/CDC/CODI/data-owner-tools/full_answer_key.csv')

for s in systems:
  hid_line_map = []
  pos_pid_map = []
  output_lines = []
  hid_dict = {}
  key_path = Path('/Users/apellitieri/Desktop/CDC/CODI/data-owner-tools') / "{}-key.csv".format(s)
  pos_pid_path = Path('/Users/apellitieri/Desktop/CDC/CODI/data-owner-tools') / "{}_household_pos_pid.csv".format(s)
  hid_out_path = Path('/Users/apellitieri/Desktop/CDC/CODI/data-owner-tools') / "{}-hid-mapping.csv".format(s)

  with open(key_path) as key_csv:
    key_reader = csv.reader(key_csv)
    next(key_reader)
    hid_line_map = list(key_reader)
    for line in hid_line_map:
      hid_dict[line[0]] = line[2]
      if line[2] in household_dict:
        household_dict[line[2]].append(s)
      else:
        household_dict[line[2]] = [s]

  with open(pos_pid_path) as pos_pid_csv:
    pos_pid_reader = csv.reader(pos_pid_csv)
    next(pos_pid_reader)
    pos_pid_map = list(pos_pid_reader)

  for line in pos_pid_map:
    hid = hid_dict[line[1]]
    output_lines.append({'HOUSEHOLD_POSITION': line[0], 'HOUSEHOLD_ID': hid})

  with open(hid_out_path, 'w', newline='', encoding='utf-8') as hid_out:
    writer = csv.DictWriter(hid_out, fieldnames=header)
    writer.writeheader()
    for row in output_lines:
      writer.writerow(row)

with open(full_answer_key_path, 'w', newline='', encoding='utf-8') as full_key:
  writer = csv.DictWriter(full_key, fieldnames=systems)
  writer.writeheader()
  for key in household_dict:
    new_row = {}
    for system in household_dict[key]:
      new_row[system] = key
    writer.writerow(new_row)
