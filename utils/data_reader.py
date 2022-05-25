import pandas as pd

from sqlalchemy import MetaData, Table, create_engine
from sqlalchemy.sql import select

V1 = "v1"
V2 = "v2"
CSV = "csv"

# This provides a mapping of our field names
# to the field names used across versions of the DM and the CSV
DATA_DICTIONARY = {
    "record_id": {V1: "patid", V2: "patid", CSV: 'record_id'},
    "given_name": {V1: "given_name", V2: "pat_firstname", CSV: 'given_name'},
    "family_name": {V1: "family_name", V2: "pat_lastname", CSV: 'family_name'},
    "DOB": {V1: "birth_date", V2: "birth_date", CSV: 'DOB'},
    "sex": {V1: "sex", V2: "sex", CSV: 'sex'},
    "phone": {V1: "household_phone", V2: "primary_phone", CSV: 'phone_number'},
    "address": {V1: "household_street_address", V2: "address_street", CSV: 'household_street_address'},
    "zip": {V1: "household_zip", V2: "address_zip5", CSV: 'household_zip'},
}


def add_parser_db_args(parser):
    parser.add_argument(
        "-s",
        "--schema",
        dest="schema",
        default=V2,
        choices=[V1, V2],
        help=f"Version of the CODI Data Model schema to use. "
               "Valid options are \"{V1}\" or \"{V2}\"",
    )

    parser.add_argument(
        '--v1.schema',
        dest='v1_schema',
        default='codi',
        help="Database schema to read from in a v1 database. "
             "Default is 'codi'"
    )
    parser.add_argument(
        '--v1.table',
        dest='v1_table',
        default='identifier',
        help="Database table or view to read from in a v1 database. "
             "Default is 'identifier'"
    )
    parser.add_argument(
        '--v1.idcolumn',
        dest='v1_idcolumn',
        default='patid',
        help="Column name for patient unique ID in a v1 database. "
             "Default is 'patid'"
    )


def case_insensitive_lookup(row, key, version):
    desired_key = DATA_DICTIONARY[key][version]

    if desired_key in row:
        return row[desired_key]
    else:
        for actual_key in row.keys():
            if actual_key.lower() == desired_key:
                return row[actual_key]


def get_query(engine, version, args):
    if version == V1:
        DATA_DICTIONARY["record_id"][V1] = args.v1_idcolumn

        identifier = Table(
            args.v1_table,  # default: "identifier"
            MetaData(),
            autoload=True,
            autoload_with=engine,
            schema=args.v1_schema,  # default: "codi"
        )

        query = select([identifier])
        return query
    else:
        # note there is also the `demographic` table, but
        # all relevant identifiers there are also in the two tables below.
        # so we join just the 2 private_ tables
        # to get all the necessary items
        prv_demo = Table(
            "private_demographic",
            MetaData(),
            autoload=True,
            autoload_with=engine,
            schema="cdm",
        )

        prv_address = Table(
            "private_address_history",
            MetaData(),
            autoload=True,
            autoload_with=engine,
            schema="cdm",
        )

        # the expectation is there will only be one record per individual
        # in private_address_history, so we simply join the tables
        # with no further filtering
        query = select([prv_demo, prv_address]).filter(
            prv_demo.columns.patid == prv_address.columns.patid
        )

        return query


def load_db(args):
    connection_string = args.db
    version = args.schema
    engine = create_engine(connection_string)
    query = get_query(engine, version, args)
    db_data = pd.read_sql(query, connection_string)
    return db_data


def load_csv(filepath):
    # force all columns to be strings, even if they look numeric
    csv_data = pd.read_csv(filepath, dtype=str)
    return csv_data

