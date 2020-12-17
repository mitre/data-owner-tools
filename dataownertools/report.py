from collections import Counter

class Report:
  def __init__(self, fields):
    self.field_counters = {}
    for f in fields:
      self.field_counters[f] = Counter()

  def validate(self, field_name, value):
    if value is None:
      self.field_counters[field_name]['NULL Value'] += 1
      return
    if not value.isascii():
      self.field_counters[field_name]['Contains Non-ASCII Characters'] += 1
    if not value.isprintable():
      self.field_counters[field_name]['Contains Non-printable Characters'] += 1
    if value.isspace():
      self.field_counters[field_name]['Empty String'] += 1

  def print(self):
    for field, counter in self.field_counters.items():
      print(field)
      print('--------------------')
      for issue, count in counter.items():
        print("{}: {}".format(issue, count))
        print('')