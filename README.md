# macrostrat-map-ingestion

Scripts for ingesting maps into Macrostrat


## CriticalMAAS 6-month Hackathon

The map ingestion code written for TA4 tasks at the 6-month hackathon has
been re-packaged into the following commands of the Macrostrat CLI:

* `macrostrat maps ingest-file`
* `macrostrat maps ingest-from-csv`

See [UW-Macrostrat/macrostrat/map-integration](https://github.com/UW-Macrostrat/macrostrat/map-integration)
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
