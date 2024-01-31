"""
Look for USGS geologic maps from the Nevada Bureau of Mines and Geology.
"""

import hashlib

import bs4
import requests

from macrostrat.criticalmaas import config
from macrostrat.criticalmaas.types import MacrostratObject


def new_obj(origin: str) -> MacrostratObject:
    description = {
        "website": "https://nbmg.unr.edu/USGS.html",
        "url": origin,
    }

    # Construct a short but unique "basename" for the object.
    filename = origin.split("/")[-1]
    digest = hashlib.sha256(origin.encode("utf-8")).hexdigest()
    basename = f"{filename}-{digest[:8]}"

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
    links = soup.find_all("a")

    for url in sorted(link["href"] for link in links if is_valid_url(link["href"])):
        print(new_obj(url))


if __name__ == "__main__":
    main()
