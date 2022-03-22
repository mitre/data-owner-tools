import argparse
from datetime import datetime, date
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

    # DB-related arguments
    parser.add_argument(
        '--schema',
        default='codi',
        help="Database schema to read from. Default is 'codi'"
    )
    parser.add_argument(
        '--table',
        default='identifier',
        help="Database table or view to read from. Default is 'identifier'"
    )
    parser.add_argument(
        '--idcolumn',
        default='patid',
        help="Column name for patient unique ID. Default is 'patid'"
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


def get_column(row, key, source):
    desired_key = DATA_DICTIONARY[key][source]

    if desired_key in row:
        return row[desired_key]
    else:
        for actual_key in row.keys():
            if actual_key.lower() == desired_key:
                return row[actual_key]


def load_db(args):
    connection_string = args.db
    schema = args.schema
    table = args.table
    # This looks like SQL injection, but since it requires the user
    # to pass in their own credentials, there's no risk of privilege escalation
    # or uninintended data being returned.
    db_data = pd.read_sql_query(f"select * from {schema}.{table}", connection_string)
    return db_data  


def load_csv(filepath):
    # force all columns to be strings, even if they look numeric
    csv_data = pd.read_csv(filepath, dtype=str)
    return csv_data


def analyze(data, source):
    stats = {}
    raw_values = {}

    stats['number_of_rows'] = len(data.index)

    patid_col = get_column(data, 'patid', source)
    patid_stats = top_N(patid_col)
    stats['total_unique_patids'] = len(patid_stats)

    patid_dups = {k:v for (k,v) in patid_stats.items() if v > 1}
    stats['patids_with_duplicates'] = len(patid_dups)
    if len(patid_dups) > 0 and len(patid_dups) < (len(patid_stats) * .2):
        # only report individual IDs if there are less than 20% dups
        raw_values['duplicate_patids'] = patid_dups

    dob_col = get_column(data, 'dob', source)
    notnull_dobs = dob_col.dropna()
    stats['dob'] = {
        'min': str(notnull_dobs.min()),  # str-ify because we get Timestamp from DB
        'max': str(notnull_dobs.max()),  # which is not serializable
        'missing': int(dob_col.isna().sum())
    }

    expected_min_dob = '1997-01-01'  # roughly, 19 years old at the start of CODI observation period (2016)
    # expected_max_dob is trickier because we don't know when the data was populated
    # TODO: add another command line arg?

    if source == 'csv':
        if '-' in notnull_dobs[0]:
            out_of_range = notnull_dobs[notnull_dobs < expected_min_dob]
            stats['dob']['count_earlier_dob_than_expected'] = len(out_of_range)
        else:
            # the date format will either be YYYY-MM-DD or YYMMDD
            # we'll assume it's consistent across a single file

            # if YYMMDD, any '90s dates or earlier in there
            # will mean the min/max aren't correct.
            # YYYY-MM-DD preserves normal sorting,
            # so don't spend time parsing it

            parsed_dobs = notnull_dobs.map(yymmdd_to_date)

            stats['dob']['min_parsed'] = str(parsed_dobs.min())  # str-ify the Timestamps again
            stats['dob']['max_parsed'] = str(parsed_dobs.max())

            expected_min_dob = pd.to_datetime(expected_min_dob, format='%Y-%m-%d')

            out_of_range = parsed_dobs[parsed_dobs < expected_min_dob]
            stats['dob']['count_earlier_dob_than_expected'] = len(out_of_range)

    else:
        # different DBs may return different data types for the DOB column
        if type(notnull_dobs[0]) is date:
            expected_min_dob = date.fromisoformat(expected_min_dob)
        # else
        #   assume it's a string in ISO format, no change should be needed

        out_of_range = notnull_dobs[notnull_dobs < expected_min_dob]
        stats['dob']['count_earlier_dob_than_expected'] = len(out_of_range)

    sex_col = get_column(data, 'sex', source)
    stats['sex'] = top_N(sex_col)

    zip_col = get_column(data, 'zip', source)
    data['zip_format'] = zip_col.map(to_format)
    stats['zip_format'] = top_N(data['zip_format'])

    stats['top_10_zip_codes'] = top_N(zip_col, 10)

    phone_col = get_column(data, 'phone', source)
    data['phone_format'] = phone_col.map(to_format)

    stats['phone_format'] = top_N(data['phone_format'])

    # Note: the following top 10s are limited to anything that occurs 3+ times,
    # in order to limit the potential spill of PII.
    # For this analysis, any names that appear 2 or fewer times are not especially useful.
    given_name_col = get_column(data, 'given_name', source)
    raw_values['top_10_given_names'] = top_N(given_name_col, 10, 3)

    family_name_col = get_column(data, 'family_name', source)
    raw_values['top_10_family_names'] = top_N(family_name_col, 10, 3)

    address_col = get_column(data, 'address', source)
    raw_values['top_10_addresses'] = top_N(address_col, 10, 3)

    raw_values['top_10_phone_numbers'] = top_N(phone_col, 10, 3)

    stats['field_summaries'] = {}
    for col in [given_name_col, family_name_col, address_col, zip_col, phone_col]:
        stats['field_summaries'][col.name] = summary(col)

    # TODO: possible quick win: look at the year/month/day breakdown in dates

    return (stats, raw_values)

def yymmdd_to_date(yymmdd):
    if yymmdd[0] in ['0', '1', '2']:
        # if the 3rd digit in year is 0, 1, or 2
        # we assume it's in the 2000s
        # note this is incorrect for dates <= 1929
        # but we expect that there won't be a lot of those here
        # (native date parsing for 2 digit years uses a cutoff for 19/20 at 68)
        century = '20'
    else:
        century = '19'

    return datetime.strptime(century + yymmdd, '%Y%m%d')

def to_format(numeric_string):
    # turn, ex, 123-4567 into ###-####
    if not numeric_string or pd.isnull(numeric_string):
        return ''

    no_digits = re.sub('[0-9]', '#', numeric_string)
    no_letters = re.sub('[A-Za-z]', 'X', no_digits)  # just in case
    return no_letters


def top_N(series, N=0, lower_limit=1):
    # return a dict of the top N most prevalent entries in the column
    # and the count of each

    top_n = series.value_counts()

    if N > 0:
        top_n = top_n[:N]

    if lower_limit > 1:
        # filter anything below a certain count
        # for example, don't return names that only appear once
        top_n = top_n[top_n >= lower_limit]

    top_n = top_n.to_dict()

    return top_n


def summary(series):
    # 1. count the number of missing (null) entries
    missing = series.isna().sum()

    # 2. basic descriptive statistics on the length of the values
    length = series.str.len().describe().to_dict()

    # 3. count the characters across all values
    list_chars = series[series.notna()].map(list)
    # list_chars is a list of lists e.g: [[J,o,h,n],[J,a,n,e],...]
    flat_list = [item for sublist in list_chars.tolist() for item in sublist]
    # flat_list is now a single list [J,o,h,n,J,a,n,e,....]
    total_chars = pd.Series(flat_list).value_counts().to_dict()

    return {
        'missing': int(missing),
        'length': length,
        'characters': total_chars
    }


if __name__ == "__main__":
    args = parse_args()

    if args.csv:
        csv_data = load_csv(args.csv)
        results = analyze(csv_data, 'csv')
        source = 'csv'

    if args.db:
        DATA_DICTIONARY['patid']['db'] = args.idcolumn
        db_data = load_db(args)
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
