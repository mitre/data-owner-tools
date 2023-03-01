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
        "address": ["address_street", "address_detail"],
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
        f'Valid options are "{V1}" or "{V2}". Default is "{V2}',
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
        help="Name of the database schema containing the PRIVATE_DEMOGRAPHIC"
        " and PRIVATE_ADDRESS_HISTORY tables in a v2 database. "
        "Default is 'cdm'",
    )
    parser.add_argument(
        "--address_selection",
        dest="v2_address_selection",
        choices=["full", "preferred", "single"],
        default="full",
        help="Determines the approach for selecting a single address per PATID"
        " from PRIVATE_ADDRESS_HISTORY. Options: Use \"single\" if "
        "the data is already guaranteed to only contain one address per PATID."
        " Use \"preferred\" if the database is guaranteed to only contain one "
        "address with address_preferred='Y' per PATID. "
        "Use \"full\" if the database may contain multiple preferred addresses"
        " for different dates/types/use. This option will select "
        "the most recent preferred address by start date."
        "Default if not specified is 'full'",
    )
    parser.add_argument(
        "--debug_query",
        action="store_true",
        help="Aids in debugging by printing out the actual DB query being run",
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


def empty_str_from_none(string):
    if string is None:
        return ""
    else:
        return string


def case_insensitive_lookup(row, key, version):
    data_key = DATA_DICTIONARY[version][key]
    if isinstance(data_key, list):
        first_key = map_key(row, data_key[0])
        data = empty_str_from_none(row[first_key])
        for subkey in data_key[1:]:
            mapped_subkey = map_key(row, subkey)
            if mapped_subkey:
                subdata = empty_str_from_none(row[mapped_subkey])
                data = data + " " + subdata

        return data

    else:
        mapped_key = map_key(row, data_key)
        return row[mapped_key] if mapped_key else None


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

        if args.debug_query:
            print(query)

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

        if args.v2_address_selection == "single":
            # The user said their data is guaranteed to only have a single
            # address per PATID. This simplifies the query to just
            # join the tables together with no additional filters
            query = select([prv_demo, prv_address]).filter(
                prv_demo.columns.patid == prv_address.columns.patid
            )
        elif args.v2_address_selection == "preferred":
            # The user said their data may have multiple addresses,
            # but is guaranteed that only one per PATID will be preferred.
            # This simplifies the query to just select ADDRESS_PREFERRED=Y
            query = select([prv_demo, prv_address]).filter(
                prv_demo.columns.patid == prv_address.columns.patid,
                prv_address.columns.address_preferred == 'Y',
            )
        else:
            # The user indicated the data may have multiple preferreds,
            # (or at least did not select one of the above options)
            # so we select the most recent by date.
            # The PCOR schema includes "type" (physical/postal/both/unknown)
            # and "use" (home/word/temp/old/unknown) fields, and the hierarchy
            # of the possible combination of those options is not well-defined.
            # (eg, should we pick physical/work over a both-type/unknown-use?)
            # For simplicity and performance we will just pick
            # the first preferred address we find, sorting by date.
            # Going forward, a better solution is likely to include all of
            # an individuals' addresses in PPRL, rather than more complex ways
            # of picking a single one.

            addr_period_order = prv_address.columns.address_period_start.desc()

            # Different SQL engines have different semantics for sorting DESC:
            # Postgres and Oracle put nulls first, so we want NULLS LAST
            # MSSQL puts nulls last, but doesn't support NULLS LAST
            # so we use this hack to get NULLS LAST for all main dialects.
            # For safety, in case other engines also don't support NULLS LAST,
            #  only apply it to the ones that we know it works on
            #  (vs not applying it to the ones we know it doesn't)

            # TODO: test on MySQL - deferring since none of our partners use it now

            # known engine dialect names are "mssql", "postgresql", and "oracle"
            if engine.dialect.name in ["postgresql", "oracle"]:
                addr_period_order = addr_period_order.nulls_last()

            subquery = (
                select(prv_address.columns.addressid)
                .filter(
                    prv_address.columns.patid == prv_demo.columns.patid,
                    prv_address.columns.address_preferred == 'Y'
                )
                .order_by(prv_address.columns.address_preferred.desc())
                .order_by(addr_period_order)
                .limit(1)
                .correlate(prv_demo)
                .scalar_subquery()
            )

            query = select([prv_demo, prv_address]).filter(
                prv_demo.columns.patid == prv_address.columns.patid,
                prv_address.columns.addressid == subquery,
            )

        if args.debug_query:
            print(query)

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
