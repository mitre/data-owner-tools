import argparse
import json
from pathlib import Path
from zipfile import ZipFile


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Tool for verifying metadata sent to and received from"
        "linkage agent against one another."
    )
    parser.add_argument(
        "source_archive", help="path to ZIP archive containing garbled PII"
    )
    parser.add_argument(
        "linkage_archive",
        help="path ZIP archive containing PPRL results from linkage agent",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        dest="verbose",
        action="store_true",
        help="Verbose mode prints output to console",
    )
    args = parser.parse_args()
    if not Path(args.source_archive).exists():
        parser.error("Unable to find source archive: " + args.source_archive)
    if not Path(args.linkage_archive).exists():
        parser.error("Unable to find linkage archive: " + args.linkage_archive)
    return args


def get_metadata(archive_path_str):
    with ZipFile(archive_path_str) as archive:
        metadata_namelist = list(filter(lambda x: "metadata" in x, archive.namelist()))
        if len(metadata_namelist) == 0:
            print(f"WARNING: could not find metadata file in {archive_path_str}")
            return
        if len(metadata_namelist) > 1:
            print(f"WARNING: found more than one metadata file in {archive_path_str}")
            print(f"\tUsing {metadata_namelist[0]}")
        with archive.open(metadata_namelist[0]) as meta_file:
            metadata = json.load(meta_file)

    return metadata


def verify_metadata(
    source_json, linkage_json, source_name="source_json", linkage_name="linkage_json"
):
    metadata_issues = []
    source_keys = set(source_json.keys())
    linkage_keys = set(linkage_json.keys())
    for key in source_keys.union(linkage_keys):
        if key not in source_keys:
            metadata_issues.append(
                f"Found key {key} in {linkage_name}, "
                f"but not in {source_name}"
            )
        elif key not in linkage_keys:
            metadata_issues.append(
                f"Found key {key} in {source_name},"
                f" but not in {linkage_name}"
            )
        elif source_json[key] != linkage_json[key]:
            metadata_issues.append(
                f"Disagreement in value for key {key}"
                f"\n\t {source_name} has value {source_json[key]}"
                f"\n\t {linkage_name} has value {linkage_json[key]}"
            )
    return metadata_issues


def main():
    args = parse_arguments()
    source_json = get_metadata(args.source_archive)
    linkage_json = get_metadata(args.linkage_archive)["input_system_metadata"]
    metadata_issues = verify_metadata(source_json, linkage_json)
    if len(metadata_issues) > 0:
        print(f"Validation Failed: \nFound {len(metadata_issues)} issues")
        if args.verbose:
            for issue in metadata_issues:
                print("\t" + issue)
    else:
        print(f"Validation Successful: Found {len(metadata_issues)} issues")


if __name__ == "__main__":
    main()
