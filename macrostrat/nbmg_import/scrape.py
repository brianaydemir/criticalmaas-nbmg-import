"""
Look for USGS geologic maps from the Nevada Bureau of Mines and Geology.
"""

import bs4
import requests


def is_valid_url(url: str) -> bool:
    """
    Returns whether the given URL is one that we are interested in downloading.
    """
    return url.startswith("https://data.nbmg.unr.edu/Public/") and url.endswith(".zip")


def main() -> None:
    """
    Scrape NBMG's website for URLs of interest, and print them out.
    """
    url_to_scrape = "https://nbmg.unr.edu/USGS.html"
    resp = requests.get(url_to_scrape, timeout=5)
    soup = bs4.BeautifulSoup(resp.text, "html.parser")
    links = soup.find_all("a")

    for url in sorted(link["href"] for link in links if is_valid_url(link["href"])):
        print(url)


if __name__ == "__main__":
    main()
