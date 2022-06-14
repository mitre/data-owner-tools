#!/usr/bin/env python3

import argparse
import csv
import json
import os
import unicodedata
from collections import Counter
from random import shuffle
from time import strftime, strptime

from sqlalchemy import create_engine

from utils.data_reader import add_parser_db_args, case_insensitive_lookup, get_query
from utils.validate import validate_csv_conf

HEADER = [
    "record_id",
    "given_name",
    "family_name",
    "DOB",
    "sex",
    "phone_number",
    "household_street_address",
    "household_zip",
]

V1 = "v1"
V2 = "v2"


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Tool for extracting, validating and cleaning data for CODI PPRL"
    )
    parser.add_argument("database", help="Database connection string", nargs="?")
    parser.add_argument(
        "-v",
        "--verbose",
        dest="verbose",
        action="store_true",
        help="Verbose mode prints output to console",
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="output_file",
        default="temp-data/pii.csv",
        help="Specify an output file. Default is temp-data/pii.csv",
    )
    parser.add_argument(
        "--csv",
        dest="csv_conf",
        default=False,
        help="Specify path to csv translation config file"
    )

    add_parser_db_args(parser)

    args = parser.parse_args()

    return args


def validate(report, field, value):
    if value is None:
        report[field]["NULL Value"] += 1
        return
    if not value.isascii():
        report[field]["Contains Non-ASCII Characters"] += 1
    if not value.isprintable():
        report[field]["Contains Non-printable Characters"] += 1
    if value.isspace():
        report[field]["Empty String"] += 1


def clean_string(pii_string):
    if pii_string is None:
        return None
    ascii_pii_string = unicodedata.normalize("NFKD", pii_string).encode(
        "ascii", "ignore"
    )
    return ascii_pii_string.strip().upper().decode("ascii")


def clean_phone(phone):
    if phone is None:
        return None
    return "".join(filter(lambda x: x.isdigit(), phone.strip()))


def clean_zip(household_zip):
    if household_zip is None:
        return None
    return household_zip.strip()


def get_report():
    report = {}
    for h in HEADER:
        report[h] = Counter()
    return report


def print_report(report):
    for field, counter in report.items():
        print(field)
        print("--------------------")
        for issue, count in counter.items():
            print("{}: {}".format(issue, count))
        print("")


def extract_database(args):
    output_rows = []
    connection_string = args.database
    version = args.schema
    report = get_report()
    engine = create_engine(connection_string)
    with engine.connect() as connection:
        query = get_query(engine, version, args)
        results = connection.execute(query)
        for row in results:
            output_row = handle_row(row, report, version)
            output_rows.append(output_row)

    shuffle(output_rows)
    if args.verbose:
        print_report(report)
    return output_rows


def extract_csv(args, mapping=None, csvfile="", init_id=100000, date_format="%y%m%d"):
    if mapping is None:
        mapping = dict()
    mapping['date_format'] = date_format
    output_rows = []
    report = get_report()
    person_id = init_id
    with open(csvfile, 'r') as datasource:
        rows = csv.DictReader(datasource)
        for row in rows:
            handled_row = handle_row(row, report, mapping)
            if not handled_row[0]:
                handled_row[0] = person_id
                person_id += 1
            output_rows.append(handled_row)

    shuffle(output_rows)
    if args.verbose:
        print_report(report)
    return output_rows


def handle_row(row, report, version):
    output_row = []
    record_id = case_insensitive_lookup(row, "record_id", version)
    output_row.append(record_id)

    given_name = case_insensitive_lookup(row, "given_name", version)
    validate(report, "given_name", given_name)
    output_row.append(clean_string(given_name))

    family_name = case_insensitive_lookup(row, "family_name", version)
    validate(report, "family_name", family_name)
    output_row.append(clean_string(family_name))

    dob = case_insensitive_lookup(row, "DOB", version)
    if type(dob) == str:
        dob = strftime('%Y-%m-%d',strptime(dob, version['date_format']))
        validate(report,"DOB",dob)
        output_row.append(dob)
    else:
        output_row.append(dob.isoformat())

    sex = case_insensitive_lookup(row, "sex", version)
    validate(report, "sex", sex)
    output_row.append(sex.strip())

    phone_number = case_insensitive_lookup(row, "phone", version)
    validate(report, "phone_number", phone_number)
    output_row.append(clean_phone(phone_number))

    household_street_address = case_insensitive_lookup(row, "address", version)
    validate(report, "household_street_address", household_street_address)
    output_row.append(clean_string(household_street_address))

    household_zip = case_insensitive_lookup(row, "zip", version)
    validate(report, "household_zip", household_zip)
    output_row.append(clean_zip(household_zip))

    return output_row


def write_data(output_rows, args):
    os.makedirs("temp-data", exist_ok=True)
    with open(args.output_file, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(HEADER)
        for output_row in output_rows:
            writer.writerow(output_row)


def main():
    args = parse_arguments()
    print()
    print("csv-conf:", args.csv_conf)
    if args.csv_conf:

        issues = validate_csv_conf(args.csv_conf)
        if len(issues) == 0 and args.verbose:
            print("\nNo issues found in csv extraction config")
        elif args.verbose:
            print(f"Found {len(issues)} issues in csv extraction config:")
            for issue in issues:
                print("\t-", issue)
            print()
        with open(args.csv_conf, 'r') as f:
            conf = json.load(f)
        ingest_kwargs = {'mapping': conf['translation_map'], 'csvfile': conf['filepath'],
                         'init_id': int(conf['initial_id']), 'date_format': conf['date_format']}
        output_rows = extract_csv(args, **ingest_kwargs)
        if 'output' in conf:
            args.output_file = conf['output']
    else:
        output_rows = extract_database(args)
    write_data(output_rows, args)
    if args.verbose:
        print("Total records exported: {}".format(len(output_rows)))
        print("")


if __name__ == "__main__":
    main()
