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
    parser.add_argument("sourcefile", help="Source PII CSV file")
    parser.add_argument("--linksfile", help="LINK_ID CSV file from linkage agent")

    parser.add_argument(
        "--hhlinks",
        help="HOUSEHOLD_ID CSV file from linkage agent",
    )
    hhgroup = parser.add_mutually_exclusive_group(required=False)
    hhgroup.add_argument(
        "--hhmapping",
        help="Household mapping csv, if inferred by households.py",
    )
    hhgroup.add_argument(
        "--hhdefinition",
        help="Household mapping definition csv, if this source tracks households",
    )

    parser.add_argument(
        '-o', '--outputdir', dest='outputdir', default="output",
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
    with open(os.path.join(args.outputdir, "linkid_to_patid.csv"), "w", newline="", encoding="utf-8") as csvfile:
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
    hh_links_file = Path(args.hhlinks)
    pii_lines = parse_source_file(args.sourcefile)

    with open(os.path.join(args.outputdir, "householdid_to_patid.csv"), "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(HH_HEADERS)
        with open(hh_links_file) as links:
            links_reader = csv.reader(links)
            # Skipping header
            next(links_reader)

            if args.hhmapping:
                write_hh_links_with_mapping(writer, links_reader, pii_lines, args)
            else:
                write_hh_links_with_definition(writer, links_reader, args)


def write_hh_links_with_mapping(writer, links_reader, pii_lines, args):
    # hid_map is HOUSEHOLD_POSITION,PII_POSITIONS
    hid_map = parse_source_file(args.hhmapping)

    for row in links_reader:
        household_id = row[0]
        household_position = row[1]
        # The +1 accounts for the header row in spreadsheet index
        # IMPORTANT ASSUMPTION: this file contains position X at line X+1
        pii_positions = hid_map[int(household_position) + 1][1]

        for position in pii_positions.split(','):
            patid = pii_lines[int(position) + 1][0]
            # The +1 accounts for the header row in spreadsheet index
            writer.writerow([household_id, patid])


def write_hh_links_with_definition(writer, links_reader, args):
    # hid_map is HOUSEHOLD_POSITION,PATIDS
    hid_map = parse_source_file(args.hhdefinition)
    for row in links_reader:
        household_id = row[0]
        household_position = row[1]
        # The +1 accounts for the header row in spreadsheet index
        # IMPORTANT ASSUMPTION: this file contains position X at line X+1
        # TODO: consider parsing this to a dict so the order of the file doesn't matter
        patids = hid_map[int(household_position) + 1]

        for patid in patids:
            writer.writerow([household_id, patid])


def translate_linkids(args):
    if args.linksfile:
        write_patid_links(args)

    if args.hhlinks and (args.hhmapping or args.hhdefinition):
        write_hh_links(args)


def main():
    args = parse_arguments()
    translate_linkids(args)


if __name__ == "__main__":
    main()
