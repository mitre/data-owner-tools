#!/bin/bash
#
# Set argv[1] to inbox path
# and argv[2] to SECRET_FILE
#
# Script assumes temp-data folder contains
# pii extracted into 'pii_*.csv' format

# If you haven't extracted the data for each data owner, repeat the following for each:
# python extract.py --db postgresql://apellitieri:codi@localhost/site_a
# mv pii.csv pii_site_a.csv

parent_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )

cd "$parent_path/.."
INBOX_PATH=$1
SECRET_FILE=$2

DATA_OWNER_NAMES=('site_a' 'site_b' 'site_c' 'site_d' 'site_e' 'site_f')

echo 'Cleaning inbox...'
rm -r $INBOX_PATH/*

for site in ${DATA_OWNER_NAMES[@]}; do
  echo "Running garble.py for ${site}"
  python garble.py temp-data/pii_${site}.csv example-schema/ $SECRET_FILE
  mv output/garbled.zip $INBOX_PATH/${site}.zip
  python households.py temp-data/pii_${site}.csv $SECRET_FILE -t
  mv temp-data/household_pos_pid.csv temp-data/${site}_household_pos_pid.csv
  mv output/garbled_households.zip $INBOX_PATH/${site}_households.zip
done

echo 'Garbled zip files created:'
ls $INBOX_PATH
