import json
from os.path import exists

MAP_COLS = [
    "given_name",
    "family_name",
    "DOB",
    "sex",
    "phone",
    "address",
    "zip",
]


def validate_csv_conf(filepath):
    with open(filepath, 'r') as f:
        conf = json.load(f)
    issues = []

    if "filepath" not in conf:
        issues.append("No csv file specified")
    elif not exists(conf['filepath']):
        issues.append("Specified csv does not exist")
    if "date_format" not in conf:
        issues.append("No date ingest format specified")
    if "translation_map" not in conf:
        issues.append("No column mapping specified")
    else:
        mapping = conf['translation_map']
        defaults = mapping.get('default_values', {})
        for col in MAP_COLS:
            if col not in mapping and col not in defaults:
                issues.append(f"no target column or default value specified for field: {col}")

    return issues
