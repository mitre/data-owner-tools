#!/usr/bin/env python3

import argparse
import csv
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from random import shuffle
from zipfile import ZipFile

import pandas as pd

from definitions import TIMESTAMP_FMT
from derive_subkey import derive_subkey
from households.matching import addr_parse, get_houshold_matches

HEADERS = ["HOUSEHOLD_POSITION", "PII_POSITIONS"]
HOUSEHOLD_PII_HEADERS = [
    "family_name",
    "phone_number",
    "household_street_address",
    "household_zip",
    "record_ids",
]
HOUSEHOLD_POS_PID_HEADERS = ["household_position", "pid"]


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Tool for garbling household PII for PPRL purposes"
        " in the CODI project"
    )
    parser.add_argument(
        "sourcefile", default=None, nargs="?", help="Source pii-TIMESTAMP.csv file"
    )
    parser.add_argument("secretfile", help="Location of de-identification secret file")
    parser.add_argument(
        "-d",
        "--householddef",  # would have used -h but that's help
        help="Location of household definitions file;"
        " don't infer households from source PII",
    )
    parser.add_argument(
        "--schemafile",
        default="example-schema/household-schema/fn-phone-addr-zip.json",
        help="Location of linkage schema."
        " Default: example-schema/household-schema/fn-phone-addr-zip.json",
    )
    parser.add_argument(
        "--mappingfile",
        default="output/households/households.csv",
        help="Specify a mapping file output for inferred households."
        " Default is output/households/household.csv",
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="outputfile",
        default="output/garbled_households.zip",
        help="Specify an output file. Default is output/garbled_households.zip",
    )
    parser.add_argument(
        "-t",
        "--testrun",
        action="store_true",
        help="Optional generate files used for testing against an answer key",
    )
    args = parser.parse_args()
    if args.sourcefile and not Path(args.sourcefile).exists():
        parser.error("Unable to find source file: " + args.secretfile)
    if not Path(args.schemafile).exists():
        parser.error("Unable to find schema file: " + args.secretfile)
    if not Path(args.secretfile).exists():
        parser.error("Unable to find secret file: " + args.secretfile)
    return args


def validate_secret_file(secret_file):
    secret = None
    with open(secret_file, "r") as secret_text:
        secret = secret_text.read().strip()
        try:
            int(secret, 16)
        except ValueError:
            sys.exit("Secret must be in hexadecimal format")
        if len(secret) < 32:
            sys.exit("Secret smaller than minimum security level")
    return secret


def parse_source_file(source_file):
    all_strings = {
        "record_id": "str",
        "given_name": "str",
        "family_name": "str",
        "DOB": "str",
        "sex": "str",
        "phone_number": "str",
        "household_street_address": "str",
        "household_zip": "str",
        "parent_given_name": "str",
        "parent_family_name": "str",
        "parent_email": "str",
    }
    # force all columns to be strings, even if they look numeric
    df = pd.read_csv(source_file, dtype=all_strings)

    # break out the address into number, street, suffix, etc,
    # so we can prefilter matches based on those
    addr_cols = df.apply(
        lambda row: addr_parse(row.household_street_address),
        axis="columns",
        result_type="expand",
    )
    df = pd.concat([df, addr_cols], axis="columns")

    return df


def write_households_pii(output_rows, household_time):
    shuffle(output_rows)
    timestamp = household_time.strftime(TIMESTAMP_FMT)
    with open(
        Path("temp-data") / f"households_pii-{timestamp}.csv",
        "w",
        newline="",
        encoding="utf-8",
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


def get_default_pii_csv(dirname="temp-data"):
    filenames = list(filter(lambda x: "pii" in x and len(x) == 23, os.listdir(dirname)))
    timestamps = [
        datetime.strptime(filename[4:-4], TIMESTAMP_FMT) for filename in filenames
    ]
    newest_name = filenames[timestamps.index(max(timestamps))]
    source_file = Path("temp-data") / newest_name
    return source_file


def write_mapping_file(pos_pid_rows, hid_pat_id_rows, args):
    if args.sourcefile:
        source_file = Path(args.sourcefile)
    else:
        source_file = get_default_pii_csv()
        print(f"PII Source: {str(source_file)}")
    pii_lines = parse_source_file(source_file)
    output_rows = []
    mapping_file = Path(args.mappingfile)
    n_households = 0
    with open(mapping_file, "w", newline="", encoding="utf-8") as csvfile:
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
                pat_ids = list(map(lambda p: pii_lines.at[p, "record_id"], pat_clks))
                already_added.update(pat_clks)
            else:
                pat_clks = [position]
                pat_ids = [line[0]]

            string_pat_clks = [str(int) for int in pat_clks]
            pat_string = ",".join(string_pat_clks)
            writer.writerow([hclk_position, pat_string])
            n_households += 1
            pos_pid_rows.append([hclk_position, line[0]])
            for patid in pat_ids:
                hid_pat_id_rows.append([hclk_position, patid])
            # note pat_ids_str will be quoted by the csv writer if needed
            pat_ids_str = ",".join(pat_ids)
            output_row = [line[2], line[5], line[6], line[7], pat_ids_str]
            hclk_position += 1
            output_rows.append(output_row)
    return output_rows, n_households


def write_scoring_file(hid_pat_id_rows):
    # Format is used for scoring
    with open(
        Path("temp-data") / "hh_pos_patids.csv", "w", newline="", encoding="utf-8"
    ) as hpos_pat_csv:
        writer = csv.writer(hpos_pat_csv)
        writer.writerow(HOUSEHOLD_POS_PID_HEADERS)
        for output_row in hid_pat_id_rows:
            writer.writerow(output_row)


def write_hid_hh_pos_map(pos_pid_rows):
    # Format is used for generating a hid to hh_pos for full answer key
    with open(
        Path("temp-data") / "household_pos_pid.csv", "w", newline="", encoding="utf-8"
    ) as house_pos_csv:
        writer = csv.writer(house_pos_csv)
        writer.writerow(HOUSEHOLD_POS_PID_HEADERS)
        for output_row in pos_pid_rows:
            writer.writerow(output_row)


def hash_households(args, household_time):
    timestamp = household_time.strftime(TIMESTAMP_FMT)
    schema_file = Path(args.schemafile)
    secret_file = Path(args.secretfile)
    secret = validate_secret_file(secret_file)
    households_secret = derive_subkey(secret, "households")
    with open(schema_file, "r") as schema:
        file_contents = schema.read()
        if "doubleHash" in file_contents:
            sys.exit(
                "The following schema uses doubleHash, which is insecure: "
                + str(schema_file)
            )
    output_file = Path("output") / "households" / "fn-phone-addr-zip.json"
    household_pii_file = (
        args.householddef or Path("temp-data") / f"households_pii-{timestamp}.csv"
    )
    subprocess.run(
        [
            "anonlink",
            "hash",
            household_pii_file,
            households_secret,
            str(schema_file),
            str(output_file),
        ]
    )


def infer_households(args, household_time):
    pos_pid_rows = []
    hid_pat_id_rows = []
    os.makedirs(Path("output") / "households", exist_ok=True)
    os.makedirs("temp-data", exist_ok=True)
    output_rows, n_households = write_mapping_file(pos_pid_rows, hid_pat_id_rows, args)
    write_households_pii(output_rows, household_time)
    if args.testrun:
        write_scoring_file(hid_pat_id_rows)
        write_hid_hh_pos_map(pos_pid_rows)
    return n_households


def create_output_zip(args, n_households, household_time):

    timestamp = household_time.strftime(TIMESTAMP_FMT)

    if args.sourcefile:
        source_file = Path(args.sourcefile)
    else:
        source_file = get_default_pii_csv()

    source_file_name = os.path.basename(source_file)
    source_dir_name = os.path.dirname(source_file)

    source_timestamp = os.path.splitext(source_file_name.replace("pii-", ""))[0]
    metadata_file_name = source_file_name.replace("pii", "metadata").replace(
        ".csv", ".json"
    )
    metadata_file = Path(source_dir_name) / metadata_file_name
    with open(metadata_file, "r") as fp:
        metadata = json.load(fp)

    new_metadata_filename = f"households_metadata-{timestamp}.json"
    meta_timestamp = metadata["creation_date"].replace("-", "").replace(":", "")[:-7]
    assert (
        source_timestamp == meta_timestamp
    ), "Metadata creation date does not match pii file timestamp"

    metadata["number_of_households"] = n_households

    metadata["household_garble_time"] = household_time.isoformat()

    if not args.householddef:
        metadata["households_inferred"] = True
    else:
        metadata["households_inferred"] = False

    with open(Path("temp-data") / new_metadata_filename, "w+") as metadata_file:
        json.dump(metadata, metadata_file, indent=2)

    with open(Path("output") / new_metadata_filename, "w+") as metadata_file:
        json.dump(metadata, metadata_file, indent=2)

    with ZipFile(Path(args.outputfile), "w") as garbled_zip:
        garbled_zip.write(Path("output") / "households" / "fn-phone-addr-zip.json")
        garbled_zip.write(Path("output") / new_metadata_filename)

    os.remove(Path("output") / new_metadata_filename)

    print("Zip file created at: " + str(Path(args.outputfile)))


def main():
    args = parse_arguments()
    household_time = datetime.now()
    if not args.householddef:
        n_households = infer_households(args, household_time)
    else:
        with open(args.householddef) as household_file:
            households = household_file.read()
        n_households = len(households.split()) - 1

    hash_households(args, household_time)
    create_output_zip(args, n_households, household_time)


if __name__ == "__main__":
    main()
