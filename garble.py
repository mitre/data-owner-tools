#!/usr/bin/env python3

import argparse
import glob
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zipfile import ZipFile

from definitions import TIMESTAMP_FMT, TIMESTAMP_LEN
from derive_subkey import derive_subkey


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Tool for garbling PII in for PPRL purposes in the CODI project"
    )
    parser.add_argument(
        "sourcefile", default=None, nargs="?", help="Source pii-TIMESTAMP.csv file"
    )
    parser.add_argument("schemadir", help="Directory of linkage schema")
    parser.add_argument("secretfile", help="Location of de-identification secret file")
    parser.add_argument(
        "-z",
        "--outputzip",
        dest="outputzip",
        default="garbled.zip",
        help="Specify an name for the .zip file. Default is garbled.zip",
    )
    parser.add_argument(
        "-o",
        "--outputdir",
        dest="outputdir",
        default="output",
        help="Specify an output directory. Default is output/",
    )
    args = parser.parse_args()
    if not Path(args.schemadir).exists():
        parser.error("Unable to find directory: " + args.schemadir)
    if not Path(args.secretfile).exists():
        parser.error("Unable to find secret file: " + args.secretfile)
    return args


def validate_secret_file(secret_file):
    secret = None
    with open(secret_file, "r") as secret_text:
        secret = secret_text.read()
        try:
            int(secret, 16)
        except ValueError:
            sys.exit("Secret must be in hexadecimal format")
        if len(secret) < 32:
            sys.exit("Secret smaller than minimum security level")
    return secret


def validate_clks(clk_files, metadata_file):
    with open(metadata_file, "r") as meta_fp:
        metadata = json.load(meta_fp)
    n_lines_expected = metadata["number_of_records"]
    for clk_file in clk_files:
        with open(clk_file, "r") as clk_fp:
            data = json.load(clk_fp)
        n_lines_actual = len(data["clks"])
        assert (
            n_lines_expected == n_lines_actual
        ), f"Expected {n_lines_expected} in {clk_file.name}, found {n_lines_actual}"


def garble_pii(args):
    secret_file = Path(args.secretfile)

    if args.sourcefile:
        source_file = Path(args.sourcefile)
    else:
        filenames = list(
            filter(
                lambda x: "pii" in x and len(x) == 8 + TIMESTAMP_LEN,
                os.listdir("temp-data"),
            )
        )
        timestamps = [
            datetime.strptime(filename[4:-4], TIMESTAMP_FMT) for filename in filenames
        ]
        newest_name = filenames[timestamps.index(max(timestamps))]
        source_file = Path("temp-data") / newest_name
        print(f"PII Source: {str(source_file)}")

    os.makedirs("output", exist_ok=True)

    source_file_name = os.path.basename(source_file)
    source_dir_name = os.path.dirname(source_file)

    source_timestamp = os.path.splitext(source_file_name.replace("pii-", ""))[0]
    metadata_file_name = source_file_name.replace("pii", "metadata").replace(
        ".csv", ".json"
    )
    metadata_file = Path(source_dir_name) / metadata_file_name
    with open(metadata_file, "r") as fp:
        metadata = json.load(fp)
    meta_timestamp = metadata["creation_date"].replace("-", "").replace(":", "")[:-7]
    assert (
        source_timestamp == meta_timestamp
    ), "Metadata creation date does not match pii file timestamp"

    garble_time = datetime.now()

    metadata["garble_time"] = garble_time.isoformat()

    timestamp = datetime.strftime(garble_time, TIMESTAMP_FMT)

    with open("output/metadata.json", "w+") as fp:
        json.dump(metadata, fp, indent=2)

    secret = validate_secret_file(secret_file)
    individuals_secret = derive_subkey(secret, "individuals")

    clk_files = []
    schema = glob.glob(args.schemadir + "/*.json")
    for s in schema:
        with open(s, "r") as schema_file:
            file_contents = schema_file.read()
            if "doubleHash" in file_contents:
                sys.exit(
                    "The following schema uses doubleHash, which is insecure: " + str(s)
                )
        output_file = Path(args.outputdir) / os.path.basename(s)

        outfile = str(output_file).replace(".json", f"{timestamp}.json")

        subprocess.run(
            [
                "anonlink",
                "hash",
                source_file,
                individuals_secret,
                str(s),
                outfile,
            ],
            check=True,
        )
        clk_files.append(Path(outfile))
    validate_clks(clk_files, metadata_file)
    return clk_files + [Path("output/metadata.json")]


def create_output_zip(clk_files, args):
    print(args.outputdir, args.outputzip)
    with ZipFile(os.path.join(args.outputdir, args.outputzip), "w") as garbled_zip:
        for output_file in clk_files:
            garbled_zip.write(output_file)
            if "metadata" in output_file.name:
                os.remove(output_file)
    print("Zip file created at: " + str(Path(args.outputdir) / args.outputzip))


def main():
    args = parse_arguments()
    output_files = garble_pii(args)
    create_output_zip(output_files, args)


if __name__ == "__main__":
    main()
