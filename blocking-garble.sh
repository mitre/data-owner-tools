#!/bin/bash
#
# Set argv[1] to the path of the blocking schema
# and argv[2] to inbox path
#
# Script assumes folder contains synthetic denver
# pii extracted into 'pii_*.csv'

parent_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )

cd "$parent_path"

SCHEMA_FILE=$1
INBOX_PATH=$2

echo 'Cleaning inbox...'
rm -r $INBOX_PATH/*

echo 'Running garble.py for A'
python garble.py --source pii_site_a.csv --schema example-schema/ --secretfile ../deidentification_secret.txt
mv garbled.zip $INBOX_PATH/site_a.zip
python block.py --schema $SCHEMA_FILE
mv garbled-blocked.zip $INBOX_PATH/site_a-block.zip
echo 'Running garble.py for B'
python garble.py --source pii_site_b.csv --schema example-schema/ --secretfile ../deidentification_secret.txt
mv garbled.zip $INBOX_PATH/site_b.zip
python block.py --schema $SCHEMA_FILE
mv garbled-blocked.zip $INBOX_PATH/site_b-block.zip
echo 'Running garble.py for C'
python garble.py --source pii_site_c.csv --schema example-schema/ --secretfile ../deidentification_secret.txt
mv garbled.zip $INBOX_PATH/site_c.zip
python block.py --schema $SCHEMA_FILE
mv garbled-blocked.zip $INBOX_PATH/site_c-block.zip
echo 'Running garble.py for D'
python garble.py --source pii_site_d.csv --schema example-schema/ --secretfile ../deidentification_secret.txt
mv garbled.zip $INBOX_PATH/site_d.zip
python block.py --schema $SCHEMA_FILE
mv garbled-blocked.zip $INBOX_PATH/site_d-block.zip
echo 'Running garble.py for E'
python garble.py --source pii_site_e.csv --schema example-schema/ --secretfile ../deidentification_secret.txt
mv garbled.zip $INBOX_PATH/site_e.zip
python block.py --schema $SCHEMA_FILE
mv garbled-blocked.zip $INBOX_PATH/site_e-block.zip
echo 'Running garble.py for F'
python garble.py --source pii_site_f.csv --schema example-schema/ --secretfile ../deidentification_secret.txt
mv garbled.zip $INBOX_PATH/site_f.zip
python block.py --schema $SCHEMA_FILE
mv garbled-blocked.zip $INBOX_PATH/site_f-block.zip
echo 'Garbled and blocked zip files created:'
ls $INBOX_PATH
