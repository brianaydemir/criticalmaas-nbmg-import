"""
Look for USGS geologic maps from the Nevada Bureau of Mines and Geology.
"""

import hashlib
import os.path

import bs4
import requests

from macrostrat.criticalmaas import config
from macrostrat.criticalmaas.types import MacrostratObject


def new_obj(origin: str, name: str) -> MacrostratObject:
    description = {
        "website": "https://nbmg.unr.edu/USGS.html",
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
        name=(name or filename) + ", NV",
    )


def is_valid_url(url: str) -> bool:
    """
    Return whether the given URL is one that we are interested in downloading.
    """
    return url.startswith("https://data.nbmg.unr.edu/Public/") and url.endswith(".zip")


def main() -> None:
    """
    Scrape NBMG's website for URLs of interest, and print the resulting objects.
    """
    url_to_scrape = "https://nbmg.unr.edu/USGS.html"
    resp = requests.get(url_to_scrape, timeout=config.TIMEOUT)
    soup = bs4.BeautifulSoup(resp.text, "html.parser")
    links = [x for x in soup.find_all("a") if is_valid_url(x["href"])]

    for link in links:
        print(new_obj(link["href"], link.text))


if __name__ == "__main__":
    main()
