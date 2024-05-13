# macrostrat-map-ingestion

Scripts for ingesting maps into Macrostrat


## CriticalMAAS 6-month Hackathon

The map ingestion code written for TA4 tasks at the 6-month hackathon has
been re-packaged into the following commands of the Macrostrat CLI:

* `macrostrat maps ingest-file`
* `macrostrat maps ingest-from-csv`

See [UW-Macrostrat/macrostrat/map-integration](https://github.com/UW-Macrostrat/macrostrat/tree/main/map-integration)
for the implementation of these commands.


## Basic Setup and Configuration

1. Install [Poetry](https://python-poetry.org/).

2. Tell Poetry which Python 3.11+ installation to use for this project's environment.

       poetry env use /usr/bin/python3.11

3. Install dependencies.

       poetry install --sync

4. Copy [`macrostrat.toml.template`](macrostrat.toml.template) to
   `macrostrat.toml`, copy the `example` section, and set each key to an
   appropriate value.


## CLI-based Bulk Ingest of Maps

The import process can be divided into two phases:

1. Scraping some data source for potential maps of interest. This is a task
   that cannot be generalized across multiple data sources.

2. Using the data obtained in the previous step to populate data into
   Macrostrat's database and object store. This task can be generalized to
   work across multiple data sources.

The scripts in the [`macrostrat.map_ingestion`](macrostrat/map_ingestion)
package address the first of these two steps. Each script outputs a CSV file
that can be fed into `macrostrat maps ingest-from-csv`, which addresses the
second of these two steps.


## Examples

Each example below describes how to "scrape" a data source and produce a CSV
file for the `macrostrat maps ingest-file` command.


### CriticalMAAS 9 Month Hackathon

    poetry run python3 macrostrat/map_ingestion/criticalmaas_09.py data/criticalmaas_09_all.csv

The resulting output is in [data/criticalmaas_09.csv](data/criticalmaas_09.csv).

The input CSV file was provided by the CriticalMAAS program.


### National Geologic Map Database (NGMDB)

    poetry run python3 macrostrat/map_ingestion/ngmdb.py data/ngmdb_usgs_records_all.csv

The resulting output is in [data/ngmdb.csv](data/ngmdb.csv).

The input CSV file was provided by the USGS and flags NGMDB products of
interest to the CriticalMAAS program.


### Alaska Division of Geological & Geophysical Surveys

    poetry run python3 macrostrat/map_ingestion/alaska.py

The resulting output is in [data/alaska_all.csv](data/alaska_all.csv).

NOTE: Several rows describing maps that are problematic for Macrostrat's
ingestion pipeline were deleted, yielding [data/alaska.csv](data/alaska.csv).


### Nevada Bureau of Mines and Geology

    poetry run python3 macrostrat/map_ingestion/nevada.py

The resulting output is in [data/nevada.csv](data/nevada.csv).
