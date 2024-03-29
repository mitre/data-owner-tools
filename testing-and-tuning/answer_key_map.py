#!/usr/bin/env python3

# Creates an answer key for all data owners specified
# to be consumed by the scoring and evaluation tools for tuning

import csv
from pathlib import Path

systems = ["site_a", "site_b", "site_c", "site_d", "site_e", "site_f"]

# output is clk_pos | h_id
header = ["HOUSEHOLD_POSITION", "HOUSEHOLD_ID"]
household_dict = {}
full_answer_key_path = Path("../temp-data/full_answer_key.csv")

for s in systems:
    hid_line_map = []
    pos_pid_map = []
    output_lines = []
    hid_dict = {}
    key_path = Path("../temp-data") / "{}_key.csv".format(s)
    pos_pid_path = Path("../temp-data") / "{}_household_pos_pid.csv".format(s)
    hid_out_path = Path("../temp-data") / "{}_hid_mapping.csv".format(s)

    with open(key_path) as key_csv:
        key_reader = csv.reader(key_csv)
        # Skips header
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
        # Skips header
        next(pos_pid_reader)
        pos_pid_map = list(pos_pid_reader)

    for line in pos_pid_map:
        hid = hid_dict[line[1]]
        output_lines.append({"HOUSEHOLD_POSITION": line[0], "HOUSEHOLD_ID": hid})

    with open(hid_out_path, "w", newline="", encoding="utf-8") as hid_out:
        writer = csv.DictWriter(hid_out, fieldnames=header)
        writer.writeheader()
        for row in output_lines:
            writer.writerow(row)

with open(full_answer_key_path, "w", newline="", encoding="utf-8") as full_key:
    writer = csv.DictWriter(full_key, fieldnames=systems)
    writer.writeheader()
    for key in household_dict:
        new_row = {}
        for system in household_dict[key]:
            new_row[system] = key
        writer.writerow(new_row)
