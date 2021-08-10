import os
import sys
import subprocess
from zipfile import ZipFile
from pathlib import Path
import argparse

parser = argparse.ArgumentParser(description='Tool for garbling PII in for PPRL purposes in the CODI project')
parser.add_argument('--source', nargs=1, required=True, help='Source PII CSV file')
parser.add_argument('--schema', nargs=1, required=True, help='Directory of linkage schema')
parser.add_argument('--secretfile', nargs=1, required=True, help='Location of de-identification secret file')
args = parser.parse_args()

schema_dir = Path(args.schema[0])
source_file = args.source[0]
secret = None
secret_file = Path(args.secretfile[0])

if not schema_dir.exists():
  sys.exit('Unable to find directory: ' + str(schema_dir))
if not secret_file.exists():
  sys.exit('Unable to find secret file' + str(secret_file))
if not os.path.exists('output'):
  os.mkdir('output')

with open(secret_file, 'r') as secret_text:
  secret = secret_text.read()
  if len(secret) < 256:
    sys.exit('Secret length not long enough to ensure proper de-identification')

clk_files = []
schema = filter(lambda f: f.endswith('.json'), os.listdir(schema_dir))

for s in schema:
  schema_path = schema_dir.joinpath(s)
  with open(schema_path, 'r') as schema_file:
    file_contents = schema_file.read()
    if 'doubleHash' in file_contents:
      sys.exit('The following schema uses doubleHash, which is insecure: ' + str(schema_path))
  output_file = Path('output', s)
  subprocess.run(["anonlink", "hash", source_file, secret, str(schema_path), str(output_file)])
  clk_files.append(output_file)

with ZipFile('output/garbled.zip', 'w') as garbled_zip:
  for clk_file in clk_files:
    garbled_zip.write(clk_file)
