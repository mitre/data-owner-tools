#!/usr/bin/env python3

import argparse
import csv
import os
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

import pandas as pd

from derive_subkey import derive_subkey
from households.matching import addr_parse, get_houshold_matches

HEADERS = ["HOUSEHOLD_POSITION", "PAT_CLK_POSITIONS"]
HOUSEHOLD_PII_HEADERS = [
    "family_name",
    "phone_number",
    "household_street_address",
    "household_zip",
]
HOUSEHOLD_POS_PID_HEADERS = ["household_position", "pid"]


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Tool for extracting households from pii.csv"
    )
    parser.add_argument("sourcefile", help="Source PII CSV file")
    parser.add_argument("secretfile", help="Location of de-identification secret file")
    parser.add_argument(
        "--schemafile", default="example-schema/household-schema/fn-phone-addr-zip.json",
        help="Location of linkage schema. Default: example-schema/household-schema/fn-phone-addr-zip.json"
    )
    parser.add_argument(
        "--mappingfile", default="output/households/households.csv",
        help="Specify a mapping file output. Default is output/households/household.csv"
    )
    parser.add_argument(
        '-o', '--output', dest='outputfile', default="output/garbled_households.zip",
         help="Specify an output file. Default is output/garbled_households.zip"
    )
    parser.add_argument(
        "-t", "--testrun", action="store_true",
        help="Optional generate files used for testing against an answer key"
    )
    args = parser.parse_args()
    if not Path(args.sourcefile).exists():
        parser.error("Unable to find source file: " + args.secretfile)
    if not Path(args.schemafile).exists():
        parser.error("Unable to find schema file: " + args.secretfile)
    if not Path(args.secretfile).exists():
        parser.error("Unable to find secret file: " + args.secretfile)
    return args


def validate_secret_file(secret_file):
    secret = None
    with open(secret_file, "r") as secret_text:
        secret = secret_text.read()
        if len(secret) < 256:
            sys.exit("Secret length not long enough to ensure proper de-identification")
    return secret


def parse_source_file(source_file):
    all_strings = {
        'record_id': 'str',
        'given_name': 'str',
        'family_name': 'str',
        'DOB': 'str',
        'sex': 'str',
        'phone_number': 'str',
        'household_street_address': 'str',
        'household_zip': 'str',
        'parent_given_name': 'str',
        'parent_family_name': 'str',
        'parent_email': 'str'
    }
    # force all columns to be strings, even if they look numeric
    df = pd.read_csv(source_file, dtype=all_strings)

    # break out the address into number, street, suffix, etc,
    # so we can prefilter matches based on those
    addr_cols = df.apply(lambda row: addr_parse(row.household_street_address),
                         axis='columns', result_type='expand')
    df = pd.concat([df, addr_cols], axis='columns')

    return df


def write_households_pii(output_rows):
    with open(
        "temp-data/households_pii.csv", "w", newline="", encoding="utf-8"
    ) as house_csv:
        writer = csv.writer(house_csv)
        writer.writerow(HOUSEHOLD_PII_HEADERS)
        for output_row in output_rows:
            writer.writerow(output_row)


# Simple breadth-first-search to turn a graph-like structure of pairs
# into a list representing the ids in the household
def bfs_traverse_matches(pos_to_pairs, position):
    queue = [position]
    visited = [position]

    while queue:
        curr = queue.pop(0)
        pairs = pos_to_pairs[curr]

        for p in pairs:
            if p[0] not in visited:
                visited.append(p[0])
                queue.append(p[0])
            if p[1] not in visited:
                visited.append(p[1])
                queue.append(p[1])

    visited.sort()
    return visited


def write_mapping_file(pos_pid_rows, hid_pat_id_rows, args):
    source_file = Path(args.sourcefile)
    pii_lines = parse_source_file(source_file)
    output_rows = []
    with open(
        args.mappingfile, "w", newline="", encoding="utf-8"
    ) as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(HEADERS)
        already_added = set()

        # pos_to_pairs is a dict of:
        # (patient position) --> [matching pairs that include that patient]
        # so it can be traversed sort of like a graph from any given patient
        # note the key is patient position within the pii_lines dataframe
        pos_to_pairs = get_houshold_matches(pii_lines)

        hclk_position = 0
        # Match households
        for position, line in pii_lines.iterrows():
            if position in already_added:
                continue
            already_added.add(position)

            if position in pos_to_pairs:
                pat_clks = bfs_traverse_matches(pos_to_pairs, position)
                pat_ids = list(map(lambda p: pii_lines.at[p, 'record_id'], pat_clks))
                already_added.update(pat_clks)
            else:
                pat_clks = [position]
                pat_ids = [line[0]]

            string_pat_clks = [str(int) for int in pat_clks]
            pat_string = ",".join(string_pat_clks)
            writer.writerow([hclk_position, pat_string])
            pos_pid_rows.append([hclk_position, line[0]])
            for patid in pat_ids:
                hid_pat_id_rows.append([hclk_position, patid])
            output_row = [line[2], line[5], line[6], line[7]]
            hclk_position += 1
            output_rows.append(output_row)
    return output_rows


def write_scoring_file(hid_pat_id_rows):
    # Format is used for scoring
    with open(
        "temp-data/hh_pos_patids.csv", "w", newline="", encoding="utf-8"
    ) as hpos_pat_csv:
        writer = csv.writer(hpos_pat_csv)
        writer.writerow(HOUSEHOLD_POS_PID_HEADERS)
        for output_row in hid_pat_id_rows:
            writer.writerow(output_row)


def write_hid_hh_pos_map(pos_pid_rows):
    # Format is used for generating a hid to hh_pos for full answer key
    with open(
        "temp-data/household_pos_pid.csv", "w", newline="", encoding="utf-8"
    ) as house_pos_csv:
        writer = csv.writer(house_pos_csv)
        writer.writerow(HOUSEHOLD_POS_PID_HEADERS)
        for output_row in pos_pid_rows:
            writer.writerow(output_row)


def hash_households(args):
    schema_file = Path(args.schemafile)
    secret_file = Path(args.secretfile)
    secret = validate_secret_file(secret_file)
    households_secret = derive_subkey(secret, 'households')
    with open(schema_file, "r") as schema:
        file_contents = schema.read()
        if "doubleHash" in file_contents:
            sys.exit(
                "The following schema uses doubleHash, which is insecure: "
                + str(schema_file)
            )
    output_file = Path("output/households/fn-phone-addr-zip.json")
    subprocess.run(
        [
            "anonlink",
            "hash",
            "temp-data/households_pii.csv",
            households_secret,
            str(schema_file),
            str(output_file),
        ]
    )


def garble_households(args):
    pos_pid_rows = []
    hid_pat_id_rows = []
    os.makedirs('output/households', exist_ok=True)
    os.makedirs('temp-data', exist_ok=True)
    output_rows = write_mapping_file(pos_pid_rows, hid_pat_id_rows, args)
    write_households_pii(output_rows)
    if args.testrun:
        write_scoring_file(hid_pat_id_rows)
        write_hid_hh_pos_map(pos_pid_rows)
    hash_households(args)


def create_clk_zip(args):
    with ZipFile(args.outputfile, "w") as garbled_zip:
        garbled_zip.write("output/households/fn-phone-addr-zip.json")
        garbled_zip.write(args.mappingfile)
    print("Zip file created at: " + args.outputfile)


def main():
    args = parse_arguments()
    garble_households(args)
    create_clk_zip(args)


if __name__ == "__main__":
    main()
