import unicodedata

import pandas as pd
from sqlalchemy import MetaData, Table, create_engine
from sqlalchemy.sql import select

V1 = "v1"
V2 = "v2"
CSV = "csv"

# This provides a mapping of our field names
# to the field names used across versions of the DM and the CSV
DATA_DICTIONARY = {
    V1: {
        "record_id": "patid",
        "given_name": "given_name",
        "family_name": "family_name",
        "DOB": "birth_date",
        "sex": "sex",
        "phone": "household_phone",
        "address": "household_street_address",
        "zip": "household_zip",
    },
    V2: {
        "record_id": "patid",
        "given_name": "pat_firstname",
        "family_name": "pat_lastname",
        "DOB": "birth_date",
        "sex": "sex",
        "phone": "primary_phone",
        "address": "address_street",
        "zip": "address_zip5",
    },
    CSV: {
        "record_id": "record_id",
        "given_name": "given_name",
        "family_name": "family_name",
        "DOB": "DOB",
        "sex": "sex",
        "phone": "phone_number",
        "address": "household_street_address",
        "zip": "household_zip",
    },
}


def add_parser_db_args(parser):
    parser.add_argument(
        "-s",
        "--schema",
        dest="schema",
        default=V2,
        choices=[V1, V2],
        help="Version of the CODI Data Model schema to use. "
        f'Valid options are "{V1}" or "{V2}"',
    )

    parser.add_argument(
        "--v1.schema",
        dest="v1_schema",
        default="codi",
        help="Database schema to read from in a v1 database. " "Default is 'codi'",
    )
    parser.add_argument(
        "--v1.table",
        dest="v1_table",
        default="identifier",
        help="Database table or view to read from in a v1 database. "
        "Default is 'identifier'",
    )
    parser.add_argument(
        "--v1.idcolumn",
        dest="v1_idcolumn",
        default="patid",
        help="Column name for patient unique ID in a v1 database. "
        "Default is 'patid'",
    )
    parser.add_argument(
        "--schema_name",
        dest="v2_schema",
        default="cdm",
        help="Name of the database schema containing the CODI DEMOGRAPHIC"
        " and PRIVATE_DEMOGRAPHIC tables",
    )


def clean_string(pii_string):
    if pii_string is None:
        return None
    ascii_pii_string = unicodedata.normalize("NFKD", pii_string).encode(
        "ascii", "ignore"
    )
    return ascii_pii_string.strip().upper().decode("ascii")


def map_key(row, key):
    if key in row:
        return key
    else:
        lower_key = key.lower()
        for row_key in row.keys():
            if row_key.lower() == lower_key:
                return row_key


def case_insensitive_lookup(row, key, version):
    mapped_key = map_key(row, DATA_DICTIONARY[version][key])
    return row[mapped_key] if (mapped_key) else None


def translation_lookup(row, key, translation_map):
    desired_keys = translation_map.get(key, key)
    data = []
    defaults = translation_map.get("default_values", {})
    translation_rules = translation_map.get("value_mapping_rules", {})
    if type(desired_keys) == list:
        for desired_key in desired_keys:
            if (mapped_key := map_key(row, desired_key)) and (
                row_data := row[mapped_key].strip()
            ) != "":
                clean_str = clean_string(row_data)
            else:
                clean_str = clean_string(defaults.get(desired_key, ""))
            data.append(
                translation_rules.get(desired_key, {}).get(clean_str, clean_str)
            )
    elif (mapped_key := map_key(row, desired_keys)) and row[mapped_key].strip() != "":
        data.append(
            clean_string(
                translation_rules.get(mapped_key, {}).get(
                    row[mapped_key], row[mapped_key]
                )
            )
        )
    else:
        data.append(clean_string(defaults.get(key, "")))

    return " ".join(data)


def get_query(engine, version, args):
    if version == V1:
        DATA_DICTIONARY[V1]["record_id"] = args.v1_idcolumn

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
            schema=args.v2_schema,
        )

        prv_address = Table(
            "private_address_history",
            MetaData(),
            autoload=True,
            autoload_with=engine,
            schema=args.v2_schema,
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
