import datetime

TIMESTAMP_FMT = "%Y%m%dT%H%M%S"
TIMESTAMP_LEN = len(datetime.datetime.now().strftime(TIMESTAMP_FMT))
