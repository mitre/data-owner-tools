#!/bin/bash
#
# Set argv[1] to the path of the blocking schema
# and argv[2] to inbox path
#
# Script assumes folder contains synthetic denver
# pii extracted into 'pii_*.csv'

# python extract.py --db postgresql://apellitieri:codi@localhost/ch
# mv pii.csv pii_ch.csv
# python extract.py --db postgresql://apellitieri:codi@localhost/dh
# mv pii.csv pii_dh.csv
# python extract.py --db postgresql://apellitieri:codi@localhost/gotr
# mv pii.csv pii_gotr.csv
# python extract.py --db postgresql://apellitieri:codi@localhost/hfc
# mv pii.csv pii_hfc.csv
# python extract.py --db postgresql://apellitieri:codi@localhost/kp
# mv pii.csv pii_kp.csv

parent_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )

cd "$parent_path"

SCHEMA_FILE=$1
INBOX_PATH=$2

echo 'Cleaning inbox...'
rm -r $INBOX_PATH/*

echo 'Running garble.py and block.py for CH'
python garble.py --source pii_ch.csv --schema example-schema/ --secretfile ../deidentification_secret.txt
mv garbled.zip $INBOX_PATH/ch.zip
python block.py --schema $SCHEMA_FILE
mv garbled-blocked.zip $INBOX_PATH/ch-block.zip
echo 'Running garble.py and block.py for DH'
python garble.py --source pii_dh.csv --schema example-schema/ --secretfile ../deidentification_secret.txt
mv garbled.zip $INBOX_PATH/dh.zip
python block.py --schema $SCHEMA_FILE
mv garbled-blocked.zip $INBOX_PATH/dh-block.zip
echo 'Running garble.py and block.py for GotR'
python garble.py --source pii_gotr.csv --schema example-schema/ --secretfile ../deidentification_secret.txt
mv garbled.zip $INBOX_PATH/gotr.zip
python block.py --schema $SCHEMA_FILE
mv garbled-blocked.zip $INBOX_PATH/gotr-block.zip
echo 'Running garble.py and block.py for HFC'
python garble.py --source pii_hfc.csv --schema example-schema/ --secretfile ../deidentification_secret.txt
mv garbled.zip $INBOX_PATH/hfc.zip
python block.py --schema $SCHEMA_FILE
mv garbled-blocked.zip $INBOX_PATH/hfc-block.zip
echo 'Running garble.py and block.py for KP'
python garble.py --source pii_kp.csv --schema example-schema/ --secretfile ../deidentification_secret.txt
mv garbled.zip $INBOX_PATH/kp.zip
python block.py --schema $SCHEMA_FILE
mv garbled-blocked.zip $INBOX_PATH/kp-block.zip
echo 'Garbled and blocked zip files created:'
ls $INBOX_PATH
