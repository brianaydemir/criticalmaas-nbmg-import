"""
Download USGS geologic maps from the Nevada Bureau of Mines and Geology.
"""

import asyncio
import logging
import pathlib
import sys
from typing import Optional

import aiohttp
import anyio
import bs4
import requests

CONCURRENCY = 1  # how many files to download concurrently
DOWNLOAD_DIR = pathlib.Path("tmp/download")  # where to put downloaded files


async def download_object(url: str) -> Optional[pathlib.Path]:
    """
    Downloads the given object, and returns the file it was written into.
    """
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    filename = DOWNLOAD_DIR / url.split("/")[-1]

    logging.info("Downloading %s into %s", url, filename)

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            try:
                response.raise_for_status()
            except aiohttp.ClientResponseError:
                logging.error("Not downloading %s due to an HTTP error", url)
                return None
            async with await anyio.open_file(filename, "wb") as fp:
                async for data in response.content.iter_chunked(8 * 1024 * 1024):  # 8 MB
                    await fp.write(data)

    return filename


def is_valid_url(url: str) -> bool:
    """
    Returns whether the given URL is one that we are interested in downloading.
    """
    return url.startswith("https://data.nbmg.unr.edu/Public/") and url.endswith(".zip")


async def main() -> None:
    url_to_scrape = "https://nbmg.unr.edu/USGS.html"
    response = requests.get(url_to_scrape)
    soup = bs4.BeautifulSoup(response.text, "html.parser")
    links = soup.find_all("a")
    urls = [link["href"] for link in links if is_valid_url(link["href"])]

    while True:
        current, urls = urls[:CONCURRENCY], urls[CONCURRENCY:]
        if not current:
            break
        await asyncio.gather(*[download_object(url) for url in current])


def entrypoint() -> None:
    try:
        logging.basicConfig(
            format="[%(asctime)s] %(levelname)s %(module)s:%(lineno)d %(message)s",
            level=logging.DEBUG,
        )
        asyncio.run(main())
    except Exception:  # pylint: disable=broad-except
        logging.exception("Uncaught exception")
        sys.exit(1)


if __name__ == "__main__":
    entrypoint()
