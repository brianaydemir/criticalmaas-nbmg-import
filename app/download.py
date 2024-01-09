"""
Download USGS geologic maps from the Nevada Bureau of Mines and Geology.
"""

import asyncio
import logging
import pathlib
import sys

import aiohttp
import anyio
import bs4
import requests

CONCURRENCY = 5  # how many files to download concurrently
DOWNLOAD_DIR = pathlib.Path("./data")  # where to put downloaded files


async def download_file(url: str) -> pathlib.Path:
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    filename = DOWNLOAD_DIR / url.split("/")[-1]

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            async with await anyio.open_file(filename, "wb") as fp:
                async for data in response.content.iter_chunked(1024):
                    await fp.write(data)

    return filename


async def main() -> None:
    url_to_scrape = "https://nbmg.unr.edu/USGS.html"
    response = requests.get(url_to_scrape)
    soup = bs4.BeautifulSoup(response.text, "html.parser")
    links = soup.find_all("a")
    files = [link["href"] for link in links if link["href"].endswith(".zip")]

    while True:
        current, files = files[:CONCURRENCY], files[CONCURRENCY:]
        if not current:
            break
        await asyncio.gather(*[download_file(file) for file in current])


def entrypoint() -> None:
    try:
        logging.basicConfig(
            format="%(asctime)s ~ %(message)s",
            level=logging.DEBUG,
        )
        asyncio.run(main())
    except Exception:  # pylint: disable=broad-except
        logging.exception("Uncaught exception")
        sys.exit(1)


if __name__ == "__main__":
    entrypoint()
