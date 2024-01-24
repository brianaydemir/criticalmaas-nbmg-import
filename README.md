# criticalmaas-nbmg-import

Scripts for importing maps from NBMG


## Overview of the process

The import process can be divided into two phases:

1. Scraping NBMG's website. This is inherently a task that cannot be
   generalized to work across multiple map repositories.

2. Using the data obtained in the previous step to populate data into
   Macrostrat's database and object store. This task can be generalized to
   work across multiple map repositories.

The scripts in this repository generally take as input and produce as output
text files containing JSON-serialized
[`MacrostratObject`](macrostrat/nbmg_import/types.py)s, one object per line.


## Step 0: Initial set up and configuration

1. Install [Poetry](https://python-poetry.org/).

2. Tell Poetry which Python 3.11+ installation to use for this project's environment.

       poetry env use /usr/bin/python3.11

3. Install dependencies.

       poetry install --sync

4. Copy [`.env.template`](.env.template) to `.env`, and set all the keys.


## Step 1: Scraping NBMG's website

Run the following:

    poetry run python3 -m macrostrat.nbmg_import.scrape > 10-scraped-maps.txt

Each line in `00-scraped-objects.txt` should be the JSON representation of
a `MacrostratObject` describing a map to ingest.


## Step 2: Download the maps

Run the following:

    poetry run python3 -m macrostrat.nbmg_import.run download \
        --verbose \
        --input 10-scraped-maps.txt \
        --output 20-downloaded-maps.txt \
        --errors 99-errors.txt

This step and the ones below all follow the same basic structure:

* The input file is a list of `MacrostratObject`s produced by the previous
  step.

* The output file is a list of `MacrostratObject`s that were successfully
  processed by the step.

* The errors file is a list of `MacrostratObject`s that encountered errors
  during processing.


## Step 3: Register the maps

Run the following:

    poetry run python3 -m macrostrat.nbmg_import.run register \
        --verbose \
        --input 20-downloaded-maps.txt \
        --output 30-registered-maps.txt \
        --errors 99-errors.txt


## Step 4: Integrate the maps

Run the following:

    poetry run python3 -m macrostrat.nbmg_import.run integrate \
        --verbose \
        --input 30-registered-maps.txt \
        --output 40-integrated-maps.txt \
        --errors 99-errors.txt
