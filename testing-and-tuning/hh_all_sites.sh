#!/bin/bash

# Script to run through all sites, group by households, and score the results.

# Note this script expects to be run from the root data-owner-tools folder, i.e.,
# ./testing-and-tuning/hh_all_sites.sh

# Required files in temp_data:
# - pii_site_*.csv -- obtained by extract.py
# - site_*_key.csv -- obtained by build_key.py

SITES="a b c d e f"
for s in $SITES
do
  echo running site_$s
  python3 households.py -t temp-data/pii_site_${s}.csv deidentification_secret.txt
  mv temp-data/household_pos_pid.csv temp-data/site_${s}_household_pos_pid.csv
  mv temp-data/hh_pos_patids.csv temp-data/site_${s}_hh_pos_patids.csv
done

cd testing-and-tuning

python3 answer_key_map.py

python3 hh_score.py