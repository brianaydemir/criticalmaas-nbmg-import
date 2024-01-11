# criticalmaas-nbmg-import

Scripts for importing maps from NBMG

## Quickstart

1. Install [Poetry](https://python-poetry.org/).

2. Tell Poetry which Python 3.11+ installation to use for this project's environment.

       poetry env use /usr/bin/python3.11

3. Install dependencies.

       poetry install --sync

4. Scrape NBMG's website for maps to download.

       poetry run python3 -m macrostrat.nbmg_import.scrape > urls.txt

5. Run the download script, saving the output into a log file.

       xargs -a urls.txt -d "\n" poetry run python3 -m macrostrat.nbmg_import.download 2>&1 | tee -a download.log

   Check for errors.

       grep -i error download.log

   The maps downloaded from NBMG should be in `./tmp/download`.

6. Run the registration script, saving the output into a log file.

       poetry run python3 -m macrostrat.nbmg_import.register ./tmp/download/* 2>&1 | tee -a register.log

   Check for errors.

       grep -i error register.log

7. Run the integration script, saving the output into a log file.

       poetry run python3 -m macrostrat.nbmg_import.integrate 2>&1 | tee -a integrate.log

   Check for errors.

       grep -i error integrate.log
