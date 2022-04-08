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
]

V1 = 'v1'
V2 = 'v2'

# This provides a mapping of our field names
# to the field names used across versions of the DM
DATA_DICTIONARY = {
    "record_id": {V1: 'patid', V2: 'patid'},
    "given_name": {V1: 'given_name', V2: 'pat_firstname'},
    "family_name": {V1: 'family_name', V2: 'pat_lastname'},
    "DOB": {V1: 'birth_date', V2: 'birth_date'},
    "sex": {V1: 'sex', V2: 'sex'},
    "phone_number": {V1: 'household_phone', V2: 'primary_phone'},
    "household_street_address": {V1: 'household_street_address', V2: 'address_street'},
    "household_zip": {V1: 'household_zip', V2: 'address_zip5'},
}


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Tool for extracting, validating and cleaning data for CODI PPRL"
    )
    parser.add_argument('database', help="Database connection string")
    parser.add_argument(
        '-v', '--verbose', dest='verbose', action='store_true',
        help="Verbose mode prints output to console"
    )
    parser.add_argument(
        '-s', '--schema', dest='schema', default=V2, choices=[V1, V2],
        help=f"Version of the CODI Data Model schema to use. \
               Valid options are \"{V1}\" or \"{V2}\"")
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


def case_insensitive_lookup(row, key, version):
    desired_key = DATA_DICTIONARY[key][version]

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
    version = args.schema
    report = get_report()
    engine = create_engine(connection_string)
    with engine.connect() as connection:
        query = get_query(engine, version)
        results = connection.execute(query)
        for row in results:
            output_row = handle_row(row, report, version)
            output_rows.append(output_row)

    shuffle(output_rows)
    if args.verbose:
        print_report(report)
    return output_rows


def get_query(engine, version):
    if version == V1:
        identity = Table(
            "identifier", MetaData(),
            autoload=True, autoload_with=engine, schema="codi"
        )

        query = select([identity])
        return query
    else:
        # note there is also the `demographic` table, but
        # all relevant identifiers there are also in the two tables below.
        # so we join just the 2 private_ tables to get all the necessary items
        prv_demo = Table(
            "private_demographic", MetaData(),
            autoload=True, autoload_with=engine, schema="cdm"
        )

        prv_address = Table(
            "private_address_history", MetaData(),
            autoload=True, autoload_with=engine, schema="cdm"
        )

        # the expectation is there will only be one record per individual 
        # in private_address_history, so we simply join the tables
        # with no further filtering
        query = select([prv_demo, prv_address])\
            .filter(prv_demo.columns.patid == prv_address.columns.patid)

        return query


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
    output_row.append(dob.isoformat())

    sex = case_insensitive_lookup(row, "sex", version)
    validate(report, "sex", sex)
    output_row.append(sex.strip())

    phone_number = case_insensitive_lookup(row, "phone_number", version)
    validate(report, "phone_number", phone_number)
    output_row.append(clean_phone(phone_number))

    household_street_address = case_insensitive_lookup(
        row, "household_street_address", version
    )
    validate(report, "household_street_address", household_street_address)
    output_row.append(clean_string(household_street_address))

    household_zip = case_insensitive_lookup(row, "household_zip", version)
    validate(report, "household_zip", household_zip)
    output_row.append(clean_zip(household_zip))

    return output_row


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
