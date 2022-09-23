#!/usr/bin/env python3

import argparse
import csv
import json
import os
import unicodedata
import uuid
from collections import Counter
from datetime import datetime
from random import shuffle
from time import strftime, strptime

from sqlalchemy import create_engine

from utils.data_reader import (
    add_parser_db_args,
    case_insensitive_lookup,
    get_query,
    translation_lookup,
)
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
    parser.add_argument(
        "source",
        help="Specify an extraction source."
        "Valid source is database connection string or path to csv file",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        dest="verbose",
        action="store_true",
        help="Verbose mode prints output to console",
    )
    parser.add_argument(
        "--csv_config",
        dest="csv_conf",
        default=False,
        help="Specify path to csv translation config file",
    )

    add_parser_db_args(parser)

    args = parser.parse_args()

    return args


def validate(report, field, value, value_mapping=None):
    if value is None:
        report[field]["NULL Value"] += 1
        return
    if not value.isascii():
        report[field]["Contains Non-ASCII Characters"] += 1
    if not value.isprintable():
        report[field]["Contains Non-printable Characters"] += 1
    if value.isspace():
        report[field]["Empty String"] += 1
    if type(value_mapping) == dict:
        if field in value_mapping and value not in value_mapping[field]:
            report[field]["No Mapping Available"] += 1


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


def clean_dob_fromstr(dob_str, date_format):
    norm_str = unicodedata.normalize("NFKD", dob_str).encode("ascii", "ignore")
    return strftime("%Y-%m-%d", strptime(norm_str.decode("ascii"), date_format))


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
    connection_string = args.source
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


def extract_csv(args, conf):
    output_rows = []
    report = get_report()
    person_id = conf.get("initial_id", 0)
    with open(args.source, "r") as datasource:
        rows = csv.DictReader(datasource)
        for row in rows:
            handled_row = translate_row(row, report, conf)
            if not handled_row[0]:
                handled_row[0] = person_id
                person_id += 1
            output_rows.append(handled_row)

    shuffle(output_rows)
    if args.verbose:
        print_report(report)
    return output_rows


def translate_row(row, report, conf):
    output_row = []
    value_maps = conf["value_mapping_rules"]
    column_maps = conf["translation_map"]

    record_id = translation_lookup(row, "record_id", column_maps)
    output_row.append(record_id)

    given_name = translation_lookup(row, "given_name", column_maps)
    validate(report, "given_name", given_name, value_maps)
    clean_given_name = clean_string(given_name)
    output_row.append(
        value_maps.get("given_name", {}).get(clean_given_name, clean_given_name)
    )

    family_name = translation_lookup(row, "family_name", column_maps)
    validate(report, "family_name", family_name, value_maps)
    clean_family_name = clean_string(family_name)
    output_row.append(
        value_maps.get("family_name", {}).get(clean_family_name, clean_family_name)
    )

    dob = translation_lookup(row, "DOB", column_maps)
    dob = clean_dob_fromstr(dob, conf["date_format"])
    validate(report, "DOB", dob, value_maps)
    output_row.append(value_maps.get("DOB", {}).get(dob, dob))

    sex = translation_lookup(row, "sex", column_maps)
    validate(report, "sex", sex, value_maps)
    output_row.append(value_maps.get("sex", {}).get(sex, sex))

    # is phone or phone_number the canonical field name?
    phone_number = translation_lookup(row, "phone", column_maps)
    validate(report, "phone_number", phone_number, value_maps)
    clean_phone_number = clean_phone(phone_number)
    output_row.append(
        value_maps.get("phone", {}).get(clean_phone_number, clean_phone_number)
    )

    household_street_address = translation_lookup(row, "address", column_maps)
    validate(report, "household_street_address", household_street_address, value_maps)
    clean_household_street_address = clean_string(household_street_address)
    output_row.append(
        value_maps.get("address", {}).get(
            clean_household_street_address, clean_household_street_address
        )
    )

    household_zip = translation_lookup(row, "zip", column_maps)
    validate(report, "household_zip", household_zip, value_maps)
    cleaned_zip = clean_zip(household_zip)
    output_row.append(value_maps.get("zip", {}).get(cleaned_zip, cleaned_zip))

    return output_row


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


def write_metadata(n_rows, creation_time):
    metadata = {
        "number_of_records": n_rows,
        "creation_date": creation_time.isoformat(),
        "uuid1": str(uuid.uuid1()),
    }
    timestamp = datetime.strftime(creation_time, "%Y%m%dT%H%M%S")
    metaname = Path("temp-data") / f"metadata-{timestamp}.json"
    with open(metaname, "w", newline="", encoding="utf-8") as metafile:
        json.dump(metadata, metafile, indent=2)


def write_data(output_rows, args):
    creation_time = datetime.now()
    timestamp = datetime.strftime(creation_time, "%Y%m%dT%H%M%S")
    os.makedirs("temp-data", exist_ok=True)
    csvname = f"temp-data/pii-{timestamp}.csv"
    with open(csvname, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(HEADER)
        for output_row in output_rows:
            writer.writerow(output_row)
    write_metadata(len(output_rows), creation_time)

    return timestamp


def main():
    args = parse_arguments()
    if args.csv_conf:

        issues = validate_csv_conf(args.csv_conf)
        if len(issues) == 0 and args.verbose:
            print("\nNo issues found in csv extraction config")
        elif args.verbose:
            print(f"Found {len(issues)} issues in csv extraction config:")
            for issue in issues:
                print("\t-", issue)
            print()
        with open(args.csv_conf, "r") as f:
            conf = json.load(f)
        output_rows = extract_csv(args, conf)
    else:
        output_rows = extract_database(args)
    write_data(output_rows, args)
    if args.verbose:
        print("Total records exported: {}".format(len(output_rows)))
        print("")


if __name__ == "__main__":
    main()
