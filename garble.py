import os
import sys
import subprocess
import getpass
from zipfile import ZipFile
from pathlib import Path
import argparse

parser = argparse.ArgumentParser(description='Tool for garbling PII in for PPRL purposes in the CODI project')
parser.add_argument('--source', nargs=1, required=True, help='Source PII CSV file')
parser.add_argument('--schema', nargs=1, required=True, help='Directory of linkage schema')
args = parser.parse_args()

schema_dir = Path(args.schema[0])

if not schema_dir.exists():
  sys.exit('Unable to find directory: ' + schema_dir)

schema = filter(lambda f: f.endswith('.json'), os.listdir(schema_dir))

source_file = args.source[0]
secret_one = getpass.getpass('Salt value: ')
clk_files = []

if not os.path.exists('output'):
  os.mkdir('output')

for s in schema:
  schema_path = schema_dir.joinpath(s)
  with open(schema_path, 'r') as schema_file:
    file_contents = schema_file.read()
    if 'doubleHash' in file_contents:
      sys.exit('The following schema uses doubleHash, which is insecure: ' + str(schema_path))
  output_file = Path('output', s)
  subprocess.run(["clkutil", "hash", source_file, secret_one, schema_path, output_file])
  clk_files.append(output_file)

with ZipFile('garbled.zip', 'w') as garbled_zip:
  for clk_file in clk_files:
    garbled_zip.write(clk_file)
