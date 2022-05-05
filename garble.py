#!/usr/bin/env python3

import argparse
import glob
import os
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

from derive_subkey import derive_subkey


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Tool for garbling PII in for PPRL purposes in the CODI project"
    )
    parser.add_argument("sourcefile", help="Source PII CSV file")
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


def garble_pii(args):
    schema_dir = Path(args.schemadir)
    secret_file = Path(args.secretfile)
    source_file = args.sourcefile
    os.makedirs("output", exist_ok=True)
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
        output_file = Path(args.outputdir, s.split("/")[-1])
        subprocess.run(
            [
                "anonlink",
                "hash",
                source_file,
                individuals_secret,
                str(s),
                str(output_file),
            ],
            check=True,
        )
        clk_files.append(output_file)
    return clk_files


def create_clk_zip(clk_files, args):
    with ZipFile(os.path.join(args.outputdir, args.outputzip), "w") as garbled_zip:
        for clk_file in clk_files:
            garbled_zip.write(clk_file)
    print("Zip file created at: " + args.outputdir + "/" + args.outputzip)


def main():
    args = parse_arguments()
    clk_files = garble_pii(args)
    create_clk_zip(clk_files, args)


if __name__ == "__main__":
    main()
