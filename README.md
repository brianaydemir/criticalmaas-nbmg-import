## Quickstart

1. Install [Poetry](https://python-poetry.org/).

2. Tell Poetry which Python 3.11+ installation to use for this project's environment.

       poetry env use /usr/bin/python3.11

3. Install dependencies.

       poetry install --sync

4. Run the download script, saving the output into a log file.

       poetry run python3 -m macrostrat.nbmg_import.download 2>&1 | tee -a download.log

   Check for errors.

       grep -i error download.log
