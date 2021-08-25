#!/bin/bash
#
# and argv[1] to inbox path
#
# Script assumes folder contains synthetic denver
# pii extracted into 'pii_*.csv'

# python extract.py --db postgresql://apellitieri:codi@localhost/site_a
# mv pii.csv pii_site_a.csv
# python extract.py --db postgresql://apellitieri:codi@localhost/site_b
# mv pii.csv pii_site_b.csv
# python extract.py --db postgresql://apellitieri:codi@localhost/site_c
# mv pii.csv pii_site_c.csv
# python extract.py --db postgresql://apellitieri:codi@localhost/site_d
# mv pii.csv pii_site_d.csv
# python extract.py --db postgresql://apellitieri:codi@localhost/site_e
# mv pii.csv pii_site_e.csv
# python extract.py --db postgresql://apellitieri:codi@localhost/site_f
# mv pii.csv pii_site_f.csv

parent_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )

cd "$parent_path"
INBOX_PATH=$1

echo 'Cleaning inbox...'
rm -r $INBOX_PATH/*

echo 'Running garble.py for CH'
python garble.py --source pii_ch.csv --schema example-schema/ --secretfile ../deidentification_secret.txt
mv garbled.zip $INBOX_PATH/ch.zip
echo 'Running garble.py for DH'
python garble.py --source pii_dh.csv --schema example-schema/ --secretfile ../deidentification_secret.txt
mv garbled.zip $INBOX_PATH/dh.zip
echo 'Running garble.py for GotR'
python garble.py --source pii_gotr.csv --schema example-schema/ --secretfile ../deidentification_secret.txt
mv garbled.zip $INBOX_PATH/gotr.zip
echo 'Running garble.py for HFC'
python garble.py --source pii_hfc.csv --schema example-schema/ --secretfile ../deidentification_secret.txt
mv garbled.zip $INBOX_PATH/hfc.zip
echo 'Running garble.py for KP'
python garble.py --source pii_kp.csv --schema example-schema/ --secretfile ../deidentification_secret.txt
mv garbled.zip $INBOX_PATH/kp.zip
echo 'Garbled and blocked zip files created:'
ls $INBOX_PATH
