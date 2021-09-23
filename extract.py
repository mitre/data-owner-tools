#!/usr/bin/env python3

import argparse
from collections import Counter
import csv
import os
from random import shuffle
import unicodedata

from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.sql import select

HEADER = [
    "record_id",
    "given_name",
    "family_name",
    "DOB",
    "sex",
    "phone_number",
    "household_street_address",
    "household_zip",
    "parent_given_name",
    "parent_family_name",
    "parent_email",
]


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Tool for extracting, validating and cleaning data for CODI PPRL"
    )
    parser.add_argument('database', help="Database connection string")
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true', help="Verbose mode prints output to console")
    parser.add_argument(
        '-o', '--output', dest='output_file', default="temp-data/pii.csv",
         help="Specify an output file. Default is temp-data/pii.csv"
    )
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
    ascii_pii_string = unicodedata.normalize("NFKD", pii_string).encode("ascii", "ignore")
    return ascii_pii_string.strip().upper().decode("ascii")


def clean_phone(phone):
    if phone is None:
        return None
    return "".join(filter(lambda x: x.isdigit(), phone.strip()))


def clean_zip(household_zip):
    if household_zip is None:
        return None
    return household_zip.strip()


def case_insensitive_lookup(row, desired_key):
    if desired_key in row:
        return row[desired_key]
    else:
        for actual_key in row.keys():
            if actual_key.lower() == desired_key:
                return row[actual_key]


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
    report = get_report()
    engine = create_engine(connection_string)
    with engine.connect() as connection:
        meta = MetaData()
        identity = Table(
            "identifier", meta, autoload=True, autoload_with=engine, schema="codi"
        )

        query = select([identity])
        results = connection.execute(query)
        for row in results:
            output_row = [case_insensitive_lookup(row, "patid")]
            given_name = case_insensitive_lookup(row, "given_name")
            validate(report, "given_name", given_name)
            output_row.append(clean_string(given_name))
            family_name = case_insensitive_lookup(row, "family_name")
            validate(report, "family_name", family_name)
            output_row.append(clean_string(family_name))
            birth_date = case_insensitive_lookup(row, "birth_date")
            output_row.append(birth_date.isoformat())
            sex = case_insensitive_lookup(row, "sex")
            validate(report, "sex", sex)
            output_row.append(sex.strip())
            phone_number = case_insensitive_lookup(row, "household_phone")
            validate(report, "phone_number", phone_number)
            output_row.append(clean_phone(phone_number))
            household_street_address = case_insensitive_lookup(
                row, "household_street_address"
            )
            validate(report, "household_street_address", household_street_address)
            output_row.append(clean_string(household_street_address))
            household_zip = case_insensitive_lookup(row, "household_zip")
            validate(report, "household_zip", household_zip)
            output_row.append(clean_zip(household_zip))
            parent_given_name = case_insensitive_lookup(row, "parent_given_name")
            validate(report, "parent_given_name", parent_given_name)
            output_row.append(clean_string(parent_given_name))
            parent_family_name = case_insensitive_lookup(row, "parent_family_name")
            validate(report, "parent_family_name", parent_family_name)
            output_row.append(clean_string(parent_family_name))
            parent_email = case_insensitive_lookup(row, "household_email")
            validate(report, "parent_email", parent_email)
            output_row.append(clean_string(parent_email))
            output_rows.append(output_row)

    shuffle(output_rows)
    if args.verbose:
        print_report(report)
    return output_rows


def write_data(output_rows, args):
    os.makedirs('temp-data', exist_ok=True)
    with open(args.output_file, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(HEADER)
        for output_row in output_rows:
            writer.writerow(output_row)


def main():
    args = parse_arguments()
    output_rows = extract_database(args)
    write_data(output_rows, args)
    if args.verbose:
        print("Total records exported: {}".format(len(output_rows)))
        print("")


if __name__ == "__main__":
    main()
