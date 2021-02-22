import subprocess
import csv
import sys

subprocess.run(["python", "../linkidtopatid.py", "--source", "fake_pii.csv", "--links", "fake_linkids.csv"])

true_mappings = {'a1': '19442804', 'a2': '19440950', 'a3': '19440740'}

with open("linkidtopatid.csv") as source:
  source_reader = csv.reader(source)
  next(source_reader)
  for row in source_reader:
    link_id = row[0]
    patid = row[1]
    if true_mappings[link_id] != patid:
      sys.exit('Mismatch on ' + link_id)
