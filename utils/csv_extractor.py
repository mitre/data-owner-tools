def read_duplicate_file(duplicate_path):
  duplicate_lines = None
  with open(duplicate_path[0]) as duplicates:
    duplicate_rows = csv.DictReader(duplicates)
    duplicate_lines = list(duplicate_rows)
  return duplicate_lines

def read_deduplicated_file(dedupe_path):
  deduplicated_lines = None
  with open(dedupe_path[0]) as deduped:
    participant_rows = csv.DictReader(deduped)
    deduplicated_lines = list(participant_rows)
  return deduplicated_lines