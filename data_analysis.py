import argparse
from datetime import datetime
import json
import re
import time

import pandas as pd


def parse_args():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--csv",
        help='Location of pii.csv file to analyze',
    )
    group.add_argument(
        "--db",
        help='Connection string for DB to analyze',
    )
    args = parser.parse_args()
    return args

# This provides a mapping of friendly names
# to the field names used in the DB and CSV
DATA_DICTIONARY = {
    "patid": {'db': 'patid', 'csv': 'record_id'},
    "given_name": {'db': 'given_name', 'csv': 'given_name'},
    "family_name": {'db': 'family_name', 'csv': 'family_name'},
    "dob": {'db': 'birth_date', 'csv': 'DOB'},
    "sex": {'db': 'sex', 'csv': 'sex'},
    "phone": {'db': 'household_phone', 'csv': 'phone_number'},
    "address": {'db': 'household_street_address', 'csv': 'household_street_address'},
    "zip": {'db': 'household_zip', 'csv': 'household_zip'},
}


def load_db(connection_string):
    db_data = pd.read_sql_table('identifier', connection_string, schema='codi')
    return db_data  


def load_csv(filepath):
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
    csv_data = pd.read_csv(filepath, dtype=all_strings)
    return csv_data


def analyze(data, source):
    stats = {}
    raw_values = {}

    stats['number_of_rows'] = len(data.index)

    patid_col = DATA_DICTIONARY['patid'][source]
    patid_stats = top_N(data, patid_col)
    stats['total_unique_patids'] = len(patid_stats)

    patid_dups = {k:v for (k,v) in patid_stats.items() if v > 1}
    stats['patids_with_duplicates'] = len(patid_dups)
    if len(patid_dups) > 0 and len(patid_dups) < (len(patid_stats) * .2):
        # only report individual IDs if there are less than 20% dups
        raw_values['duplicate_patids'] = patid_dups

    dob_col = DATA_DICTIONARY['dob'][source]
    dob_values = data[dob_col]
    stats['dob'] = {
        'min': str(dob_values.min()),  # str-ify because we get Timestamp from DB
        'max': str(dob_values.max())   # which is not serializable
    }

    if source == 'csv':
        # we should have truncated the dates to YYMMDD,
        # which means if there are any '90s dates in there,
        # the min/max aren't correct
        parsed_dobs = dob_values.map(lambda d: datetime.strptime(d, '%y%m%d'))
        stats['parsed_dob'] = {
            'min': str(parsed_dobs.min()),  # str-ify the Timestamps again
            'max': str(parsed_dobs.max())
        }


    sex_col = DATA_DICTIONARY['sex'][source]
    stats['sex'] = top_N(data, sex_col)

    zip_col = DATA_DICTIONARY['zip'][source]
    data['zip_format'] = data[zip_col].map(to_format)
    stats['zip_format'] = top_N(data, 'zip_format')

    stats['top_10_zip_codes'] = top_N(data, zip_col, 10)

    phone_col = DATA_DICTIONARY['phone'][source]
    data['phone_format'] = data[phone_col].map(to_format)
    stats['phone_format'] = top_N(data, 'phone_format')

    given_name_col = DATA_DICTIONARY['given_name'][source]
    raw_values['top_10_given_names'] = top_N(data, given_name_col, 10, 3)

    family_name_col = DATA_DICTIONARY['family_name'][source]
    raw_values['top_10_family_names'] = top_N(data, family_name_col, 10, 3)

    address_col = DATA_DICTIONARY['address'][source]
    raw_values['top_10_addresses'] = top_N(data, address_col, 10, 3)

    raw_values['top_10_phone_numbers'] = top_N(data, phone_col, 10, 3)

    stats['field_summaries'] = {}
    for col in [given_name_col, family_name_col, address_col, zip_col]:
        stats['field_summaries'][col] = summary(data, col)

    # possible quick win: look at the year/month/day breakdown in dates

    return (stats, raw_values)


def to_format(numeric_string):
    # turn, ex, 123-4567 into ###-####
    if not numeric_string or pd.isnull(numeric_string):
        return ''

    no_digits = re.sub('[0-9]', '#', numeric_string)
    no_letters = re.sub('[A-Za-z]', 'X', no_digits)  # just in case
    return no_letters


def top_N(df, column, N=0, lower_limit=1):
    # return a dict of the top 10 most prevalent entries in the column
    # and the count of each

    top_n = df[column].value_counts()

    if N > 0:
        top_n = top_n[:N]

    if lower_limit > 1:
        # filter anything below a certain count
        # for example, don't return names that only appear once
        top_n = top_n[top_n >= lower_limit]

    top_n = top_n.to_dict()

    return top_n


def summary(df, column):
    length = df[column].str.len().describe().to_dict()

    list_chars = df[column].map(lambda v: to_char_list(v))
    # list_chars is a list of lists e.g: [[J,o,h,n],[J,a,n,e],...]
    flat_list = [item for sublist in list_chars.tolist() for item in sublist]
    # flat_list is now a single list [J,o,h,n,J,a,n,e,....]
    total_chars = pd.Series(flat_list).value_counts().to_dict()
    return {
        'length': length,
        'characters': total_chars
    }


def to_char_list(string):
    if not string or pd.isnull(string):
        return []
    return list(string)


if __name__ == "__main__":
    args = parse_args()

    if args.csv:
        csv_data = load_csv(args.csv)
        results = analyze(csv_data, 'csv')
        source = 'csv'

    if args.db:
        db_data = load_db(args.db)
        results = analyze(db_data, 'db')
        source = 'db'

    timestamp = int(time.time())
    results_file = f"results_{source}_{timestamp}.json.txt"
    with open(results_file, 'w') as outfile:
        json.dump(results[0], outfile, indent=2)
        print(f"Wrote aggregate results to {results_file}")

    results_file = f"private_results_{source}_{timestamp}.json.txt"
    with open(results_file, 'w') as outfile:
        json.dump(results[1], outfile, indent=2)
        print(f"Wrote PRIVATE results to {results_file}")
