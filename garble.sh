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

echo 'Running garble.py for A'
python garble.py --source pii_site_a.csv --schema example-schema/ --secretfile ../deidentification_secret.txt
mv garbled.zip $INBOX_PATH/site_a.zip
echo 'Running garble.py for B'
python garble.py --source pii_site_b.csv --schema example-schema/ --secretfile ../deidentification_secret.txt
mv garbled.zip $INBOX_PATH/site_b.zip
echo 'Running garble.py for C'
python garble.py --source pii_site_c.csv --schema example-schema/ --secretfile ../deidentification_secret.txt
mv garbled.zip $INBOX_PATH/site_c.zip
echo 'Running garble.py for D'
python garble.py --source pii_site_d.csv --schema example-schema/ --secretfile ../deidentification_secret.txt
mv garbled.zip $INBOX_PATH/site_d.zip
echo 'Running garble.py for E'
python garble.py --source pii_site_e.csv --schema example-schema/ --secretfile ../deidentification_secret.txt
mv garbled.zip $INBOX_PATH/site_e.zip
echo 'Running garble.py for F'
python garble.py --source pii_site_f.csv --schema example-schema/ --secretfile ../deidentification_secret.txt
mv garbled.zip $INBOX_PATH/site_f.zip
echo 'Garbled and blocked zip files created:'
ls $INBOX_PATH
