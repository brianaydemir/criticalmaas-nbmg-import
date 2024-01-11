"""
Download objects specified by URLs.
"""

import asyncio
import logging
import pathlib
import sys
from typing import Optional

import aiohttp
import anyio

CONCURRENCY = 1  # how many objects to download concurrently
DOWNLOAD_DIR = pathlib.Path("tmp/download")  # where to put downloaded objects


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


async def main() -> None:
    """
    Downloads the objects specified by the URLs given on the command line.
    """
    urls = sys.argv[1:]
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
