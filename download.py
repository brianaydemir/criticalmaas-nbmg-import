from bs4 import BeautifulSoup
import requests
import aiohttp
import asyncio
import anyio

async def download_file(url):

    filename = "./data/" + url.split("/")[-1]
    url = url.replace("https://", "http://")

    async with aiohttp.ClientSession() as session:
        async with session.get(url, ssl=False) as response:
            async with await anyio.open_file(filename, 'wb') as f:
                async for data in response.content.iter_chunked(1024):
                    await f.write(data)

    return filename


async def main():
    url = "https://nbmg.unr.edu/USGS.html"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    links = soup.find_all("a")
    zip_files = [link['href'] for link in links if link['href'].endswith(".zip")]

    while True:
        current, zip_files = zip_files[:5], zip_files[5:]

        if len(current) == 0:
            break

        tasks = await asyncio.gather(*[download_file(zip_file) for zip_file in current])


if __name__ == "__main__":
    asyncio.run(main())
