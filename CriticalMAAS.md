# CriticalMAAS 6-month Hackathon


## Overview of the process

The import process can be divided into two phases:

1. "Scraping" some data source for potential maps of interest. This is
   a task that cannot be generalized across multiple data sources.

2. Using the data obtained in the previous step to populate data into
   Macrostrat's database and object store. This task can be generalized to
   work across multiple data sources.

The scripts in this repository generally take as input and produce as output
text files containing JSON-serialized
[`MacrostratObject`](macrostrat/criticalmaas/types.py)s, one object per line.


## Step 0: Initial set up and configuration

1. Install [Poetry](https://python-poetry.org/).

2. Tell Poetry which Python 3.11+ installation to use for this project's environment.

       poetry env use /usr/bin/python3.11

3. Install dependencies.

       poetry install --sync

4. Copy [`macrostrat.toml.template`](macrostrat.toml.template) to
   `macrostrat.toml`, copy the `example` section, and set each key to an
   appropriate value.


## Step 1: Scraping a data source

Run the following:

    poetry run python3 -m macrostrat.criticalmaas.scrapers.${SCRAPER_MODULE} > 10-scraped-maps.txt

Replace `${SCRAPER_MODULE}` with one of the modules in
[macrostrat/criticalmaas/scrapers](macrostrat/criticalmaas/scrapers).

Each line in `10-scraped-mapes.txt` should be the JSON representation of
a `MacrostratObject` describing a map to ingest.


## Step 2: Download the maps

Run the following:

    poetry run python3 -m macrostrat.criticalmaas.run --verbose download \
        --input 10-scraped-maps.txt \
        --output 20-downloaded-maps.txt \
        --error 99-errors.txt

This step and the ones below all follow the same basic structure:

* The input file is a list of `MacrostratObject`s produced by the previous
  step.

* The output file is a list of `MacrostratObject`s that were successfully
  processed by the step.

* The errors file is a list of `MacrostratObject`s that encountered errors
  during processing.


## Step 3: Register the maps

Run the following:

    poetry run python3 -m macrostrat.criticalmaas.run --verbose register \
        --input 20-downloaded-maps.txt \
        --output 30-registered-maps.txt \
        --error 99-errors.txt


## Step 4: Integrate the maps

Run the following after replacing `${SOURCE_ID_PREFIX}` with an appropriate
value:

    poetry run python3 -m macrostrat.criticalmaas.run --verbose integrate \
        --input 30-registered-maps.txt \
        --output 40-integrated-maps.txt \
        --error 99-errors.txt \
        ${SOURCE_ID_PREFIX}
