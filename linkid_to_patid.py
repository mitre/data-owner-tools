#!/usr/bin/env python3

import argparse
import csv
import json
import os
from io import TextIOWrapper
from pathlib import Path
from zipfile import ZipFile

from utils.validate_metadata import get_metadata, verify_metadata

HEADERS = ["LINK_ID", "PATID"]
HH_HEADERS = ["HOUSEHOLD_ID", "PATID"]


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Tool for translating LINK_IDs back into PATIDs"
    )
    parser.add_argument("--sourcefile", help="Source pii-TIMESTAMP.csv file")
    parser.add_argument("--linkszip", help="LINK_ID CSV file from linkage agent")
    parser.add_argument(
        "--hhsourcefile",
        help="Household PII csv, either inferred by households.py"
        " or provided by data owner",
    )
    parser.add_argument(
        "--hhlinkszip",
        help="HOUSEHOLD_ID zip file from linkage agent",
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
    links_archive = Path(args.linkszip)
    pii_lines = parse_source_file(args.sourcefile)
    with open(
        os.path.join(args.outputdir, "linkid_to_patid.csv"),
        "w",
        newline="",
        encoding="utf-8",
    ) as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(HEADERS)
        with ZipFile(links_archive) as link_zip:
            links_list = list(filter(lambda x: ".csv" in x, link_zip.namelist()))
            if len(links_list) > 1:
                print(
                    f"WARNING: found more than one .csv "
                    f"file in link archive {links_archive.name}"
                )
                print(f"\tUsing {links_list[0]}")
            with link_zip.open(links_list[0]) as links:
                links_reader = csv.reader(
                    TextIOWrapper(links, encoding="UTF-8", newline="")
                )
                # Skipping header
                next(links_reader)
                for row in links_reader:
                    link_id = row[0]
                    # The +1 accounts for the header row in spreadsheet index
                    patid = pii_lines[int(row[1]) + 1][0]
                    writer.writerow([link_id, patid])


def write_hh_links(args):
    hh_links_file = Path(args.hhlinkszip)
    hh_pii_lines = parse_source_file(args.hhsourcefile)
    with open(
        os.path.join(args.outputdir, "householdid_to_patid.csv"),
        "w",
        newline="",
        encoding="utf-8",
    ) as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(HH_HEADERS)
        with ZipFile(hh_links_file) as hh_archive:
            hh_links_list = list(filter(lambda x: ".csv" in x, hh_archive.namelist()))
            if len(hh_links_list) > 1:
                print(
                    f"WARNING: found more than one .csv "
                    f"file in link archive {hh_links_file.name}"
                )
                print(f"\tUsing {hh_links_list[0]}")
            with hh_archive.open(hh_links_list[0]) as links:
                links_reader = csv.reader(
                    TextIOWrapper(links, encoding="UTF-8", newline="")
                )
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
    if args.linkszip and args.sourcefile:
        source_metadata_filename = Path(args.sourcefile).parent / Path(
            args.sourcefile
        ).name.replace("pii", "metadata").replace(".csv", ".json")
        with open(source_metadata_filename) as source_metadata_file:
            source_metadata = json.load(source_metadata_file)
        link_metadata = get_metadata(args.linkszip)["input_system_metadata"]
        metadata_issues = verify_metadata(
            source_metadata,
            link_metadata,
            source_name=source_metadata_filename,
            linkage_name=args.linkszip,
        )
        if len(metadata_issues) == 0:
            write_patid_links(args)
        else:
            print(
                f"ERROR: Inconsistencies found in "
                f"source metadata file {args.sourcefile}"
                f" and linkage archive metadata in {args.linkszip}:"
            )
            for issue in metadata_issues:
                print("\t" + issue)

    if args.hhlinkszip and args.hhsourcefile:
        source_metadata_filename = Path(args.hhsourcefile).parent / Path(
            args.hhsourcefile
        ).name.replace("pii", "metadata").replace(".csv", ".json")
        with open(source_metadata_filename) as source_metadata_file:
            source_metadata = json.load(source_metadata_file)
        link_metadata = get_metadata(args.hhlinkszip)["input_system_metadata"]
        metadata_issues = verify_metadata(
            source_metadata,
            link_metadata,
            source_name=source_metadata_filename,
            linkage_name=args.hhlinkszip
        )
        if len(metadata_issues) == 0:
            write_hh_links(args)
        else:
            print(
                f"ERROR: Inconsistencies found in source "
                f"metadata file {args.sourcefile}"
                f" and linkage archive metadata in {args.linkszip}:"
            )
            for issue in metadata_issues:
                print("\t" + issue)


def main():
    args = parse_arguments()
    translate_linkids(args)


if __name__ == "__main__":
    main()
