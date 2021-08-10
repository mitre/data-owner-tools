# Data Owner Tools

Tools for Childhood Obesity Data Initiative (CODI) data owners to extract personally identifiable information (PII) from the CODI Data Model and garble PII to send to the data coordinating center (DCC) for matching. These tools facilitate hashing / Bloom filter creation part of a Privacy-Preserving Record Linkage (PPRL) process.

## Installation

### Dependency Overview

These tools were created and tested on Python 3.7.4. The tools rely on two libraries: [SQLAlchemy](https://www.sqlalchemy.org/) and [clkhash](https://github.com/data61/clkhash).

SQLAlchemy is a library that allows the tools to connect to a database in a vendor independent fashion. This allows the tools to connect to a database that conforms to the CODI Identity Data Model implented in PostgreSQL or Microsoft SQLServer (and a number of others).

clkhash is a part of the [anonlink](https://github.com/data61/anonlink) suite of tools. It is repsonsible for garbling the PII so that it can be de-identified prior to transmission to the DCC. Note: you may have to specify the latest anonlink docker image when pulling, to ensure you are on the right version as registry may have old version (tested on v1.14)

### Installing with an existing Python install

1. Download the tools as a zip file using the "Clone or download" button on GitHub.
1. Unzip the file.
1. From the unzipped directory run:

    `pip install -r requirements.txt`

N.B. If the install fails during install of psycopg2 due to a clang error, you may need to run the following to resolve:
    `env LDFLAGS='-L/usr/local/lib -L/usr/local/opt/openssl/lib -L/usr/local/opt/readline/lib' pip install psycopg2==2.8.4`

### Installing with Anaconda

1. Install Anaconda by following the [install instructions](https://docs.anaconda.com/anaconda/install/).
    1. Depending on user account permissions, Anaconda may not install the latest version or may not be available to all users. If that is the case, try running `conda update -n base -c defaults conda`
1. Download the tools as a zip file using the "Clone or download" button on GitHub.
1. Unzip the file.
1. Open an Anaconda Powershell Prompt
1. Go to the unzipped directory
1. Run the following commands:
    1. `conda create --name codi`
    1. `conda activate codi`
    1. `conda install pip`
    1. `pip install -r requirements.txt`

## Overall Process

![Data Flow Diagram](img/data-flow.png)

## Extract PII

The CODI PPRL process depends on information pulled from a database structured to match the CODI Data Model. `extract.py` connects to a database and extracts information, cleaning and validating it to prepare it for the PPRL process. The script will output a `temp-data/pii.csv` file that contains the PII ready for garbling.

`extract.py` requires a database connection string to connect. Consult the [SQLAlchemy documentation](https://docs.sqlalchemy.org/en/13/core/engines.html#database-urls) to determine the exact string for the database in use.

When finished, the script will print a report to the terminal, documening various issues it found when extracting the data. An example execution of the script is included below:

```
$ python extract.py --db postgresql://codi:codi@localhost/codi
Total records exported: 5476

record_id
--------------------

given_name
--------------------
Contains Non-ASCII Characters: 226
Contains Non-printable Characters: 3

family_name
--------------------
Contains Non-ASCII Characters: 2

DOB
--------------------

sex
--------------------

phone_number
--------------------

household_street_address
--------------------
Contains Non-ASCII Characters: 1
Contains Non-printable Characters: 1

household_zip
--------------------
NULL Value: 9

parent_given_name
--------------------
Contains Non-ASCII Characters: 386
Contains Non-printable Characters: 4

parent_family_name
--------------------
NULL Value: 19
Contains Non-ASCII Characters: 4

parent_email
--------------------
NULL Value: 238
Contains Non-ASCII Characters: 12
```

## Garbling PII

clkhash will garble personally identifiable information (PII) in a way that it can be used for linkage later on. The CODI PPRL process garbles information a number of different ways. The `garble.py` script will manage executing clkhash multiple times and package the information for transmission to the DCC.

`garble.py` requires 3 different inputs:
1. The location of a directory of clkhash linkage schema files
1. The location of a secret file to use in the garbling process (you have to generate this file yourself creating a secret with 128 bit length)
1. The location of a CSV file containing the PII to garble

`garble.py` requires that the location of the PII and schema files are provided via command line flags. The salt value are collected while the application is running, to avoid them being captured in command line execution history.

The [clkhash schema files](https://clkhash.readthedocs.io/en/latest/schema.html) specify the fields that will be used in the hashing process as well as assigning weights to those fields. The `example-schema` directory contains a set of example schema that can be used to test the tools.

`garble.py` will provide usage information with the `-h` flag:

```
$ python garble.py -h
usage: garble.py [-h] --source SOURCE --schema SCHEMA --secretfile SECRET_FILE

Tool for garbling PII in for PPRL purposes in the CODI project

required arguments:
  --source SOURCE  Source PII CSV file
  --schema SCHEMA  Directory of linkage schema
  --secretfile SECRET_FILE  Location of de-identification secret file

optional arguments:
  -h, --help       show this help message and exit
```

`garble.py` will package up the garbled PII files into a [zip file](https://en.wikipedia.org/wiki/Zip_(file_format)) called `garbled.zip` and place it in the `output/` folder.

Example execution of `garble.py` is shown below:

```
$ python garble.py --source /Users/andrewg/projecs/anonlink-multiparty/data/siblings/system-a.csv --schema /Users/andrewg/Desktop/schema
Salt value:
generating CLKs:  21%|▏| 52.0/252 [00:00<00:00, 321clk/s, mean=1.16e+3, std=21.2generating CLKs: 100%|█| 252/252 [00:00<00:00, 420clk/s, mean=1.17e+3, std=36.1]
CLK data written to output/name-sex-dob-phone.json
generating CLKs:  21%|▏| 52.0/252 [00:00<00:00, 417clk/s, mean=1.17e+3, std=22.4generating CLKs: 100%|███| 252/252 [00:00<00:00, 535clk/s, mean=1.17e+3, std=32]
CLK data written to output/name-sex-dob-zip.json
generating CLKs:  21%|▏| 52.0/252 [00:00<00:00, 340clk/s, mean=1.53e+3, std=73.1generating CLKs: 100%|█| 252/252 [00:00<00:00, 424clk/s, mean=1.54e+3, std=68.2]
CLK data written to output/name-sex-dob-parents.json
generating CLKs:  21%|▏| 52.0/252 [00:00<00:00, 423clk/s, mean=1.17e+3, std=23.7generating CLKs: 100%|███| 252/252 [00:00<00:00, 532clk/s, mean=1.17e+3, std=34]
CLK data written to output/name-sex-dob-addr.json
```
### [Optional] Household Extract and Garble

You may now run `households.py` with the same arguments as the `garble.py` script, with the only difference being specifying a specific schema file instead of a schema directory (use `-h` flag for more information).

The households script will do the following:
  1. Attempt to group individuals into households and store those records in a csv file in temp-date
  2. Create a mapping file to be sent to the linkage agent, along with a zip file of household specific garbled information.

This information must be provided to the linkage agent if you would like to get a household linkages table as well.

## Mapping LINK_IDs to PATIDs

When anonlink matches across data owners / partners, it identifies records by their position in the file. It essentially uses the line number in the extracted PII file as the identifier for the record. When results are returned from the DCC, it will assign a LINK_ID to a line number in the PII CSV file.

To map the LINK_IDs back to PATIDs, use the `linkid_to_patid.py` script. The script takes two arguments:

1. The path to the PII CSV file
1. The path to the LINK_ID CSV file provided by the DCC
1. [Optional] The path to the `temp-data/*_hid_mapping.csv` file created by the `testing-and-tuning/answer_key_map.py` script (this should only be used if running with household linkage and testing against an answer key / ground truth)
1. [Optional] The path to the HOUSEHOLD_LINK_ID CSV file provided by the DCC if you provided household information

The script will create a file called `linkid_to_patid.csv` with the mapping of LINK_IDs to PATIDs in the `output/` folder. If you are testing and running household linkage this will also create a `linkid_to_hid.csv` file in the `output/` folder.

## Notice

Copyright 2020 The MITRE Corporation.

Approved for Public Release; Distribution Unlimited. Case Number 19-2008
