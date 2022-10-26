# Data Owner Tools

[![.github/workflows/style.yml](https://github.com/mitre/data-owner-tools/actions/workflows/style.yml/badge.svg)](https://github.com/mitre/data-owner-tools/actions/workflows/style.yml)

Tools for Clinical and Community Data Initiative (CODI) data owners to extract personally identifiable information (PII) from the CODI Data Model and garble PII to send to the linkage agent for matching. These tools facilitate hashing / Bloom filter creation part of a Privacy-Preserving Record Linkage (PPRL) process.

## Contents:
1. [Installation](#installation)
1. [Overall Process](#overall-process)
1. [Extract PII](#extract-pii)
1. [Garbling](#garbling-pii)
1. [Mapping LINKIDs to PATIDs](#mapping-linkids-to-patids)
1. [Additional Information for Developer Testing and Tuning](#developer-testing)
1. [Notice](#notice)


## Installation

### Dependency Overview

These tools were created and tested on Python 3.9.12. The tools rely on two libraries: [SQLAlchemy](https://www.sqlalchemy.org/) and [anonlink](https://github.com/data61/anonlink).

SQLAlchemy is a library that allows the tools to connect to a database in a vendor independent fashion. This allows the tools to connect to a database that conforms to the CODI Identity Data Model implented in PostgreSQL or Microsoft SQLServer (and a number of others).

anonlink is repsonsible for garbling the PII so that it can be de-identified prior to transmission to the linkage agent. Note: you may have to specify the latest anonlink docker image when pulling, to ensure you are on the right version as registry may have old version (tested on v1.14)

### Installing with an existing Python install


#### Cloning the Repository

Clone the project locally as a Git repository
```shell
git clone https://github.com/mitre/data-owner-tools.git
```

Or download as a zip file:

1. [Click this link to download the project as a zip](https://github.com/mitre/data-owner-tools/archive/refs/heads/master.zip) or use the "Clone or download" button on GitHub.
1. Unzip the file.

#### Set up a virtual environment _(Optional, but recommended)_

It can be helpful to set up a virtual environment to isolate project dependencies from system dependencies.
There are a few libraries that can do this, but this documentation will stick with `venv` since that is included
in the Python Standard Library.

```shell
# Navigate to the project folder
cd data-owner-tools/
# Create a virtual environment in a `venv/` folder
python -m venv venv/
# Activate the virtual environment
source venv/bin/activate
```

#### Installing dependencies

```shell
pip install --upgrade pip
pip install -r requirements.txt
```

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

The CODI PPRL process depends on information pulled from a database or translated from a `.csv` file structured to match the CODI Data Model. `extract.py` either connects to a database and extracts information, or reads from a provided `.csv` file, cleaning and validating it to prepare it for the PPRL process. The script will output a `temp-data/pii-TIMESTAMP.csv` file that contains the PII ready for garbling.

To extract from a database, `extract.py` requires a database connection string to connect. Consult the [SQLAlchemy documentation](https://docs.sqlalchemy.org/en/13/core/engines.html#database-urls) to determine the exact string for the database in use.

By default, `extract.py` expects a schema named `cdm` containing the CODI Data Model DEMOGRAPHIC and PRIVATE_DEMOGRAPHIC tables. The `--schema_name` option can be used to provide the name of schema containing these tables in the source system if other than `cdm`.

To translate from a `.csv` file, `extract.py` requires a `.json` configuration file, the path to which must be specified with the `--csv_config` flag. The requirements of this configuration file are described [below](#csv-translation-configuration-file)

When finished, if you specify the `--verbose` flag, the script will print a report to the terminal, documenting various issues it found when extracting the data. An example execution of the script is included below:

```
$ python extract.py postgresql://codi:codi@localhost/codi -v
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
```

### `.csv` Translation Configuration File

The configuration file used to extract and translate data for PPRL from a `.csv` file must be a `.json` file, the path to which is specified with the `--csv_config` flag.

```shell
python extract.py my_data.csv --csv_config my_config.json
```

The `.json` file must contain the following fields:

* A "date_format" field which specifies the string date representation of dates within the `.csv` for DOB extraction. The string must conform to the 1989 C Date format standard. See [Python's datetime documentation](https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior) for the most relevant information.
* A "translation_map" field that contains an object mapping standardized column names used in the PPRL process to the column names within the `.csv` file. The following columns require a mapping or a default value:
	* "given_name" 
	* "family_name"
	* "DOB"
	* "sex"
	* "phone"
	* "address"
	* "zip"
Default values are provided as an object within the "tranlsation_map" under the field "default_values". It both provides a single default value to assign to an entire column if not present within the `.csv` or if a given record has no value for that field

The configuration file may also optionally contain the following fields:

* A "value_mapping_rules" field which contains an dictionary which maps values found within a given column to values expected for the PPRL process (e.g. mapping "Male" and "Female" within the "sex" column to "M" and "F", respectively)
* An "initial_id" field which gives an integer to be used as the ID number for each of the records if a suitable column is not present in the `.csv` file or if a value is not present for that field in a given record. IDs are generated sequentially counting up from the provided "initial_id" if used.

See [`testing-and-tuning/sample_conf.json`](https://github.com/mitre/data-owner-tools/blob/csv-translation/testing-and-tuning/sample_conf.json) for an example of the configuration file.

### Data Quality and Characterization

A data characterization script is provided to assist in identifying data anomalies or quality issues. This script can be run against the `pii-TIMESTAMP.csv` generated by `extract.py` or directly against the database used by `extract.py`.
It is recommended that `data_analyis.py` at least be run against the generated `pii-TIMESTAMP.csv` file to help ensure that extraction succeeded successfully.

```shell
python data_analysis.py --csv temp-data/pii-TIMESTAMP.csv

python data_analysis.py --db postgresql://username:password@host:port/database
```

`data_analysis.py` produces two json text files containing summary statistics including: total number of records, number of individuals of each gender, zip code and phone number formats, most common zip codes, and address length at various percentiles among others.
Any aberrant results should be investigated rectified within the data set before proceeding.

## Garbling PII

anonlink will garble personally identifiable information (PII) in a way that it can be used for linkage later on. The CODI PPRL process garbles information a number of different ways. The `garble.py` script will manage executing anonlink multiple times and package the information for transmission to the linkage agent.

`garble.py` accepts the following positional inputs:
1. (optional) The location of a CSV file containing the PII to garble. If not provided, the script will look for the newest `pii-TIMESTAMP.csv` file in the `temp-data` directory.
1. (required) The location of a directory of anonlink linkage schema files
1. (required)  The location of a secret file to use in the garbling process - this should be a text file containing a single hexadecimal string of at least 128 bits (32 characters); the `testing-and-tuning/generate_secret.py` script will create this for you if require it, e.g.:
```
python testing-and-tuning/generate_secret.py
```
This should create a new file called deidentification_secret.txt in your root directory.

The [anonlink schema files](https://anonlink-client.readthedocs.io/en/latest/schema.html) specify the fields that will be used in the hashing process as well as assigning weights to those fields. The `example-schema` directory contains a set of example schema that can be used to test the tools.

`garble.py`, and all other scripts in the repository, will provide usage information with the `-h` flag:

```
$ python garble.py -h
usage: garble.py [-h] [-z OUTPUTZIP] [-o OUTPUTDIR] [sourcefile] schemadir secretfile

Tool for garbling PII in for PPRL purposes in the CODI project

positional arguments:
  sourcefile            Source pii-TIMESTAMP.csv file
  schemadir             Directory of linkage schema
  secretfile            Location of de-identification secret file

optional arguments:
  -h, --help            show this help message and exit
  -z OUTPUTZIP, --outputzip OUTPUTZIP
                        Specify an name for the .zip file. Default is garbled.zip
  -o OUTPUTDIR, --outputdir OUTPUTDIR
                        Specify an output directory. Default is output/
```

`garble.py` will package up the garbled PII files into a [zip file](https://en.wikipedia.org/wiki/Zip_(file_format)) called `garbled.zip` and place it in the `output/` folder by default, you can change this with an `--output` flag if desired.

Two example executions of `garble.py` is shown below–first with the PII CSV specified via positional argument:

```
$ python garble.py temp-data/pii-TIMESTAMP.csv example-schema ../deidentification_secret.txt
CLK data written to output/name-sex-dob-phone.json
CLK data written to output/name-sex-dob-zip.json
CLK data written to output/name-sex-dob-parents.json
CLK data written to output/name-sex-dob-addr.json
Zip file created at: output/garbled.zip
```
And second without the PII CSV specified as a positional argument:
```
$ python garble.py example-schema ../deidentification_secret.txt
PII Source: temp-data/pii-TIMESTAMP.csv
CLK data written to output/name-sex-dob-phone.json
CLK data written to output/name-sex-dob-zip.json
CLK data written to output/name-sex-dob-parents.json
CLK data written to output/name-sex-dob-addr.json
Zip file created at: output/garbled.zip
```
### [Optional] Household Extract and Garble

You may now run `households.py` with the same arguments as the `garble.py` script, with the only difference being specifying a specific schema file instead of a schema directory - if no schema is specified it will default to the `example-schema/household-schema/fn-phone-addr-zip.json`. To specify a schemafile, it must be preceeded by the flag `--schemafile` (use `-h` flag for more information). NOTE: If you want to generate the testing and tuning files for development on a synthetic dataset, you need to specify the `-t` or `--testrun` flags

The households script will do the following:
  1. Attempt to group individuals into households and store those records in a csv file in temp-data
  1. Create a mapping file to be sent to the linkage agent, along with a zip file of household specific garbled information.

This information must be provided to the linkage agent if you would like to get a household linkages table as well.

Example run with PII CSV specified:
```
$ python households.py temp-data/pii-TIMESTAMP.csv ../deidentification_secret.txt
CLK data written to output/households/fn-phone-addr-zip.json
Zip file created at: output/garbled_households.zip
```
and without PII CSV specified:
```
$ python households.py ../deidentification_secret.txt
PII Source: temp-data/pii-TIMESTAMP.csv
CLK data written to output/households/fn-phone-addr-zip.json
Zip file created at: output/garbled_households.zip
```

### [Optional] Blocking Individuals

Currently there is optional functionality for evaluation purposes to use blocking techniques to try and make the matching more efficient. After running `garble.py` you can run `block.py` to generate an additional blocking .zip file to send to the linkage agent.

Example run - note this is using the default settings, i.e. looking for the CLKs from the `garble.py` run in `output/` and using the `example-schema/blocking-schema/lambda.json` LSH blocking configuration (Read more about [blocking schmea here](https://anonlink-client.readthedocs.io/en/latest/blocking-schema.html), and more about anonlink's [LSH-based blocking approach here](https://www.computer.org/csdl/journal/tk/2015/04/06880802/13rRUxASubY)):
```
$ python block.py
Statistics for the generated blocks:
	Number of Blocks:   79
	Minimum Block Size: 1
	Maximum Block Size: 285
	Average Block Size: 31.10126582278481
	Median Block Size:  9
	Standard Deviation of Block Size:  59.10477331947379
Statistics for the generated blocks:
	Number of Blocks:   82
	Minimum Block Size: 1
	Maximum Block Size: 232
	Average Block Size: 29.963414634146343
	Median Block Size:  9
	Standard Deviation of Block Size:  45.5122952108199
Statistics for the generated blocks:
	Number of Blocks:   75
	Minimum Block Size: 1
	Maximum Block Size: 339
	Average Block Size: 32.76
	Median Block Size:  10
	Standard Deviation of Block Size:  61.43725430238738
Statistics for the generated blocks:
	Number of Blocks:   80
	Minimum Block Size: 1
	Maximum Block Size: 307
	Average Block Size: 30.7125
	Median Block Size:  9
	Standard Deviation of Block Size:  58.4333860157515
```

## Mapping LINKIDs to PATIDs

When anonlink matches across data owners / partners, it identifies records by their position in the file. It essentially uses the line number in the extracted PII file as the identifier for the record. When results are returned from the linkage agent, it will assign a LINK_ID to a line number in the pii-timestamp.csv file.

To map the LINK_IDs back to PATIDs, use the `linkid_to_patid.py` script. The script takes four arguments:

1. The path to the pii-timestamp.csv file. 
2. The path to the LINK_ID CSV file provided by the linkage agent
3. The path to the household pii CSV file, either provided by the data owner directly or inferred by the `households.py` script (which by default is named `household_pii-timestamp.csv`)
4. The path to the HOUSEHOLDID CSV file provided by the linkage agent if you provided household information

If both the pii-timestamp.csv and LINK_ID CSV file are provided as arguments, the script will create a file called `linkid_to_patid.csv` with the mapping of LINK_IDs to PATIDs in the `output/` folder by default. If both the household pii-timestamp.csv and LINK_ID CSV file are provided as arguments this will also create a `householdid_to_patid.csv` file in the `output/` folder.

### [Optional] Independently Validate Result Metadata

The metadata created by the garbling process is used to validate the metadata returned by the linkage agent within the `linkid_to_patid.py` script. Additionally, the metadata returned by the linkage agents can be validated outside of the `linkid_to_patid.py` script using the `validate_metadata.py` script in the `utils` directory. The syntax from the root directory is 
```
python utils\validate_metadata.py <path-to-garbled.zip> <path-to-result.zip>
```
So, assuming that the output of `garble.py` is a file, `garble.zip` located in the `output` directory, and that the results from the linkage agent are received as a zip archive named `results.zip` located in the `inbox` directory, the syntax would be
```
python utils\validate_metadata.py output\garble.py inbox\results.zip
```
By default, the script will only return the number of issues found during the validation process. Use the `-v` flag in order to print detailled information about each of the issues encountered during validation.

## Cleanup

In between runs it is advisable to run `rm temp-data/*` to clean up temporary data files used for individuals runs.



## Developer Testing

The documentation above outlines the approach for a single data owner to run these tools. For a developer who is testing on a synthetic data set, they might want to run all of the above steps quickly and repeatedly for a list of artificial data owners.

In the [linkage agent tools](https://github.com/mitre/linkage-agent-tools) there is a Jupyter notebook under development that will run all of these steps through the notebook by invoking scripts in the `testing-and-tuning/` folder.

If you would like to test household linkage you can currently run the `garble.sh` script (configuring the sites for which you have extracted pii). If you would like to test blocking you may run the `blocking_garble.sh` script. Note: for these scripts it is assumed that the pii files created by the `extract.py` have been renamed to their respective `pii_{site}.csv`.

## Formatting and Linting

This repository uses `black`, `flake8`, and `isort` to maintain consistent formatting and style. These tools can be run with the following command:

```shell
black .
isort .
flake8
```

## Notice

Copyright 2020-2022 The MITRE Corporation.

Approved for Public Release; Distribution Unlimited. Case Number 19-2008
