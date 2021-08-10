import os
import sys
import subprocess
from zipfile import ZipFile
from pathlib import Path
import argparse

parser = argparse.ArgumentParser(description='Tool for garbling PII for PPRL purposes in the CODI project')
parser.add_argument('--schema', nargs=1, required=True, help='Path to blocking schema')
args = parser.parse_args()

if not os.path.exists('blocking-output'):
  os.mkdir('blocking-output')

schema_file = Path(args.schema[0])

if not schema_file.exists():
  sys.exit('Unable to find schema file' + str(schema_file))

if not os.path.exists('output'):
  sys.exit('Unable to find directory with clk files, make sure you have run extract.py and garble.py first')

blocked_files = []
clk_files = filter(lambda f: f.endswith('.json'), os.listdir('output'))
for clk in clk_files:
  clk_path = Path('output', clk)
  output_file = Path('blocking-output', clk)
  print("Blocking file: {}".format(str(clk_path)))
  subprocess.run(["anonlink", "block", str(clk_path), str(schema_file), str(output_file)])
  blocked_files.append(output_file)

with ZipFile('garbled_blocked.zip', 'w') as garbled_zip:
  for blocked_file in blocked_files:
    garbled_zip.write(blocked_file)
