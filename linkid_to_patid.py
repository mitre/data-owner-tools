#!/usr/bin/env python3

import argparse
import csv
import os
from pathlib import Path

HEADERS = ["LINK_ID", "PATID"]
HH_HEADERS = ["HOUSEHOLD_ID", "PATID"]


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Tool for translating LINK_IDs back into PATIDs"
    )
    parser.add_argument("--sourcefile", help="Source PII CSV file")
    parser.add_argument("--linksfile", help="LINK_ID CSV file from linkage agent")
    parser.add_argument(
        "--hhsourcefile",
        help="Household PII csv, either inferred by households.py or provided by data owner",
    )
    parser.add_argument(
        "--hhlinksfile",
        help="HOUSEHOLD_ID CSV file from linkage agent",
    )
    parser.add_argument(
        "-o",
        "--outputdir",
        dest="outputdir",
        default="output",
        help="Specify an output directory for links. Default is './output'",
    )
    args = parser.parse_args()
    return args


def parse_source_file(source_file):
    pii_lines = []
    with open(Path(source_file)) as source:
        source_reader = csv.reader(source)
        pii_lines = list(source_reader)
    return pii_lines


def write_patid_links(args):
    links_file = Path(args.linksfile)
    pii_lines = parse_source_file(args.sourcefile)
    with open(
        os.path.join(args.outputdir, "linkid_to_patid.csv"),
        "w",
        newline="",
        encoding="utf-8",
    ) as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(HEADERS)
        with open(links_file) as links:
            links_reader = csv.reader(links)
            # Skipping header
            next(links_reader)
            for row in links_reader:
                link_id = row[0]
                # The +1 accounts for the header row in spreadsheet index
                patid = pii_lines[int(row[1]) + 1][0]
                writer.writerow([link_id, patid])


def write_hh_links(args):
    hh_links_file = Path(args.hhlinksfile)
    hh_pii_lines = parse_source_file(args.hhsourcefile)
    with open(
        os.path.join(args.outputdir, "householdid_to_patid.csv"),
        "w",
        newline="",
        encoding="utf-8",
    ) as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(HH_HEADERS)
        with open(hh_links_file) as links:
            links_reader = csv.reader(links)
            # Skipping header
            next(links_reader)

            for row in links_reader:
                household_id = row[0]
                household_position = row[1]
                # The +1 accounts for the header row in spreadsheet index
                # HH_PII headers:
                # family_name,phone_number,household_street_address,household_zip,record_ids
                record_ids = hh_pii_lines[int(household_position) + 1][4]
                record_ids_list = record_ids.split(",")

                for record_id in record_ids_list:
                    writer.writerow([household_id, record_id])


def translate_linkids(args):
    if args.linksfile and args.sourcefile:
        write_patid_links(args)

    if args.hhlinksfile and args.hhsourcefile:
        write_hh_links(args)


def main():
    args = parse_arguments()
    translate_linkids(args)


if __name__ == "__main__":
    main()
