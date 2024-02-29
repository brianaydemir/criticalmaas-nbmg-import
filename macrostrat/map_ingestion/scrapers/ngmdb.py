"""
Look for USGS geologic maps from the National Geologic Map Database.
"""

import csv
import hashlib
import os.path
import re
import sys
import urllib.parse
from typing import Optional

import bs4
import requests

from macrostrat.map_ingestion import config
from macrostrat.map_ingestion.types import MacrostratObject


def new_obj(
    website: str,
    origin: str,
    name: str,
    ref_title: Optional[str] = None,
    ref_authors: Optional[str] = None,
    ref_year: Optional[str] = None,
) -> MacrostratObject:
    description = {
        "website": website,
        "url": origin,
    }

    # Construct a short but unique "basename" for the object.
    filename = origin.split("/")[-1]
    (root, ext) = os.path.splitext(filename)
    digest = hashlib.sha256(origin.encode("utf-8")).hexdigest()
    basename = f"{root}-{digest[:8]}{ext}"

    return MacrostratObject(
        origin=origin,
        description=description,
        #
        scheme="s3",
        host=config.S3_HOST,
        bucket=config.S3_BUCKET,
        key=f"{config.S3_PREFIX}/{basename}",
        #
        local_file=config.DOWNLOAD_DIR / basename,
        #
        name=name or filename,
        ref_title=ref_title,
        ref_authors=ref_authors,
        ref_year=ref_year,
    )


def main() -> None:
    """
    Read in a CSV file from the USGS, and print any resulting objects.
    """

    input_file = sys.argv[1]
    with open(input_file, mode="r", encoding="utf-8", newline="") as fp:
        reader = csv.reader(fp)
        rows = list(reader)
        header = rows.pop(0)

    url_col = header.index("url")
    gis_data_col = header.index("gis_data")
    title_col = header.index("title")
    authors_col = header.index("authors")
    year_col = header.index("year")

    for row in rows:
        if row[gis_data_col] == "yes":
            url_to_scrape = row[url_col]
            resp = requests.get(url_to_scrape, timeout=config.TIMEOUT)
            soup = bs4.BeautifulSoup(resp.text, "html.parser")

            title = None
            url = None

            for span in soup.find_all("span"):
                if span.text.startswith("Title:"):
                    if match := re.match(r"(\s*)Title:(.*)", span.text):
                        title = match.group(2).strip()

            for link in soup.find_all("a"):
                if link.text.startswith("Shapefile version"):
                    parsed_url = urllib.parse.urlparse(link["href"])
                    if parsed_url.scheme:
                        url = link["href"]
                    else:
                        parsed_url = urllib.parse.urlparse(url_to_scrape)
                        parsed_url = parsed_url._replace(path=link["href"])
                        url = parsed_url.geturl()

            if title and url:
                print(
                    new_obj(
                        url_to_scrape,
                        url,
                        title,
                        ref_title=row[title_col],
                        ref_authors=row[authors_col],
                        ref_year=row[year_col],
                    )
                )


if __name__ == "__main__":
    main()
