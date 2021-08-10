#!/bin/bash
#
# Set argv[1] to the path of the blocking schema
# and argv[2] to inbox path
# and argv[3] to deidentification_secret file
#
# Script assumes temp-data folder contains
# pii extracted into 'pii_*.csv'

# If data is not extracted from database make sure to run following for each data owner:
# python extract.py --db postgresql://apellitieri:codi@localhost/ch
# mv pii.csv pii_ch.csv

parent_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )

cd "$parent_path/.."

DATA_OWNER_NAMES=('site_a' 'site_b' 'site_c' 'site_d' 'site_e' 'site_f')

SCHEMA_FILE=$1
INBOX_PATH=$2
SECRET_FILE=$3

echo 'Cleaning inbox...'
rm -r $INBOX_PATH/*

for site in ${DATA_OWNER_NAMES[@]}; do
  echo "Running garble.py for ${site}"
  python garble.py --source temp-data/pii_${site}.csv --schema example-schema/ --secretfile $SECRET_FILE
  mv output/garbled.zip $INBOX_PATH/${site}.zip
  python block.py --schema $SCHEMA_FILE
  mv output/garbled_blocked.zip $INBOX_PATH/${site}_block.zip
done

echo 'Garbled and blocked zip files created:'
ls $INBOX_PATH
