import os
import sys
import getpass
from zipfile import ZipFile
import argparse

parser = argparse.ArgumentParser(description='Tool for garbling PII in for PPRL purposes in the CODI project')
parser.add_argument('--source', nargs=1, required=True, help='Source PII CSV file')
parser.add_argument('--schema', nargs=1, required=True, help='Directory of linkage schema')
args = parser.parse_args()
command = "clkutil hash {source_file} {secret_one} {secret_two} {schema_path} {output_file}"

schema_dir = args.schema[0]

if not schema_dir.endswith('/'):
  schema_dir = schema_dir + '/'

if not os.path.exists(schema_dir):
  sys.exit('Unable to find directory: ' + schema_dir)

schema = filter(lambda f: f.endswith('.json'), os.listdir(schema_dir))

source_file = args.source[0]
secret_one = getpass.getpass('First salt value: ')
secret_two = getpass.getpass('Second salt value: ')
clk_files = []

if not os.path.exists('output'):
  os.mkdir('output')

for s in schema:
  schema_path = schema_dir + s
  output_file = 'output/' + s
  to_execute = command.format(source_file=source_file, secret_one=secret_one,
    secret_two=secret_two, schema_path=schema_path, output_file=output_file)
  os.system(to_execute)
  clk_files.append(output_file)

with ZipFile('garbled.zip', 'w') as garbled_zip:
  for clk_file in clk_files:
    garbled_zip.write(clk_file)
