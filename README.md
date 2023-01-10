# Data Owner Tools

[![.github/workflows/style.yml](https://github.com/mitre/data-owner-tools/actions/workflows/style.yml/badge.svg)](https://github.com/mitre/data-owner-tools/actions/workflows/style.yml)

Tools for Clinical and Community Data Initiative (CODI) Data Owners to extract personally identifiable information (PII) from the CODI Data Model and garble PII to send to the linkage agent for matching. These tools facilitate hashing and Bloom filter creation part of a Privacy-Preserving Record Linkage (PPRL) process.

This software package is specifically for use by CODI "Data Owners" and "Data Partners" to garble their data, which is then sent to a Linkage Agent, a third-party organization that links the hashes (see "PPRL Overivew/CODI Roles" in the wiki for more information). To view the software package used by the CODI Linkage Agent, see [Linkage Agent Tools](https://github.com/mitre/linkage-agent-tools).

For more information about PPRL and CODI, visit the wiki: https://github.com/mitre/data-owner-tools/wiki/PPRL-Overview

![pprl_example](https://user-images.githubusercontent.com/13512036/208981398-a3e206b3-5366-494e-99bd-63d4bc8ea27f.png)


## Quick Start
This section provides a very brief overview of the sequence of steps required of a Data Owner within CODI. For more detailed instructions, see our [wiki](https://github.com/mitre/data-owner-tools/wiki).

#### Installation
Details at: https://github.com/mitre/data-owner-tools/wiki/Installation

```sh
git clone https://github.com/mitre/data-owner-tools.git
cd data-owner-tools/
pip install -r requirements.txt
```

#### Extracting Data from a CODI Record Linkage Data Model
Details at: https://github.com/mitre/data-owner-tools/wiki/Data-Extraction,-Validation,-and-Cleaning
```sh
python extract.py -s v2 postgresql://codi:codi@localhost/codi
```

#### Garbling PII
Details at: https://github.com/mitre/data-owner-tools/wiki/Garbling-PII
```sh
python garble.py temp-data/pii.csv ./example-schema/ deidentification_secret.txt
```

#### Mapping LINKIDs to PATIDs
Details at: https://github.com/mitre/data-owner-tools/wiki/Mapping-LINK-IDs-to-PATIDs
```sh
python linkid_to_patid.py --sourcefile pii-20220304.csv --linkszip sitename.zip --hhsourcefile households_pii-20220304.csv --hhlinkszip sitename_households.zip
```


## Notice

Copyright 2020-2023 The MITRE Corporation.

Approved for Public Release; Distribution Unlimited. Case Number 19-2008

#### Licence

[Apache License 2.0](https://github.com/mitre/data-owner-tools/blob/master/LICENSE)
