#!/usr/bin/env python3

import argparse
import glob
import os
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Tool for garbling PII for PPRL purposes in the CODI project"
    )
    parser.add_argument(
        "--schemafile", default="example-schema/blocking-schema/lambda.json",
        help="Path to blocking schema. Default: example-schema/blocking-schema/lambda.json"
    )
    parser.add_argument(
        '--clkpath', default="output",
         help="Specify a folder containing clks. Default is 'output' folder"
    )
    args = parser.parse_args()
    if not Path(args.schemafile).exists():
        parser.error("Unable to find schema file: " + args.schemafile)
    return args


def block_individuals(args):
    os.makedirs('temp-data', exist_ok=True)
    os.makedirs('output', exist_ok=True)
    schema_file = Path(args.schemafile)
    clk_files = glob.glob(os.path.join(args.clkpath, "*.json"))
    blocked_files = []
    for clk in clk_files:
        clk_path = Path(clk)
        temp_file = Path("temp-data", clk.split('/')[-1])
        subprocess.run(
            ["anonlink", "block", str(clk_path), str(schema_file), str(temp_file)],
            check=True
        )
        blocked_files.append(temp_file)
    return blocked_files


def zip_blocked_files(blocked_files):
    with ZipFile("output/garbled_blocked.zip", "w") as garbled_zip:
        for blocked_file in blocked_files:
            garbled_zip.write(blocked_file)


def main():
    args = parse_arguments()
    blocked_files = block_individuals(args)
    zip_blocked_files(blocked_files)


if __name__ == "__main__":
    main()
