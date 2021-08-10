import csv
from itertools import combinations
from pathlib import Path

true_positives = 0
false_positives = 0

hid_csv_path = Path("../temp-data/hh_pos_patids.csv")
key_csv_path = Path("../temp-data/site_f_key.csv")
map_csv_path = Path("../temp-data/site_f_hid_mapping.csv")

answer_key_dict = {}
mapping_dict = {}
hpos_pid_dict = {}
result_dict = {}
household_answer_count = 0

with open(key_csv_path) as key_csv:
    key_reader = csv.reader(key_csv)
    next(key_reader)
    for row in key_reader:
        household_answer_count += 1
        answer_key_dict[row[2]] = row[0]

with open(hid_csv_path) as hid_csv:
    hid_reader = csv.reader(hid_csv)
    next(hid_reader)
    for row in hid_reader:
        hpos_pid_dict[row[0]] = row[1]

with open(map_csv_path) as map_csv:
    map_reader = csv.reader(map_csv)
    next(map_reader)
    for row in map_reader:
        mapping_dict[row[0]] = row[1]

for hpos, pid in hpos_pid_dict.items():
    if hpos in mapping_dict:
        hid = mapping_dict[hpos]
        if hid in answer_key_dict:
            if answer_key_dict[hid] == pid:
                true_positives += 1
            else:
                false_positives += 1

precision = true_positives / (true_positives + false_positives)
recall = true_positives / household_answer_count
fscore = 2 * ((precision * recall) / (precision + recall))
print(
    "Data owner household linkage scoring:\nPrecision: {} Recall: {} F-Score: {}".format(
        precision, recall, fscore
    )
)
