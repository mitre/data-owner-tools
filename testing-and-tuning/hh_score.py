#!/usr/bin/env python3

import csv
from itertools import combinations
from pathlib import Path


sites = ["a", "b", "c", "d", "e", "f"]

for site in sites:
    hid_csv_path = Path(f"../temp-data/site_{site}_hh_pos_patids.csv")
    key_csv_path = Path(f"../temp-data/site_{site}_key.csv")
    map_csv_path = Path(f"../temp-data/site_{site}_hid_mapping.csv")

    answer_key = set()
    mapping_dict = {}
    hpos_pid_dict = {}
    result_dict = {}
    true_positives = 0
    false_positives = 0

    with open(key_csv_path) as key_csv:
        key_reader = csv.reader(key_csv)
        # Skips header
        next(key_reader)
        for row in key_reader:
            hid = row[2]
            pid = row[0]
            answer_key.add((pid, hid))

    with open(hid_csv_path) as hid_csv:
        hid_reader = csv.reader(hid_csv)
        # Skips header
        next(hid_reader)
        for row in hid_reader:
            hpos_pid_dict[row[0]] = row[1]  # household_pos --> patient_id

    with open(map_csv_path) as map_csv:
        map_reader = csv.reader(map_csv)
        # Skips header
        next(map_reader)
        for row in map_reader:
            mapping_dict[row[0]] = row[1]  # household_pos --> household_id

    for hpos, pid in hpos_pid_dict.items():
        if hpos in mapping_dict:
            hid = mapping_dict[hpos]

            if (pid, hid) in answer_key:
                true_positives += 1
            else:
                false_positives += 1

    precision = true_positives / (true_positives + false_positives)
    recall = true_positives / len(answer_key)
    fscore = 2 * ((precision * recall) / (precision + recall))
    print(
        "Site {} Data owner household linkage scoring:\nPrecision: {} Recall: {} F-Score: {}".format(
            site, precision, recall, fscore
        )
    )
