#!/usr/bin/env python3

import argparse
import requests
from bs4 import BeautifulSoup, ResultSet
import os
from urllib.error import URLError
from urllib.request import urlopen
from urllib.parse import urlparse
from datetime import datetime
from http.client import IncompleteRead

URL = "https://www.3gpp.org/ftp/Specs"

def scrape_file(url: str, modified_date: datetime, dest: str):
    path = urlparse(url).path.lstrip("/")
    local_path = os.path.normpath(os.path.join(dest, path))
    if not os.path.exists(local_path) or datetime.fromtimestamp(os.path.getmtime(local_path)) < modified_date:
        # Store file
        try:
            response = urlopen(url)
            print("Writing %s" % (local_path))
            try:
                with open(local_path, 'wb') as out_file:
                    out_file.write(response.read())
            except IncompleteRead:
                print("File download error! Deleting %s" % (local_path))
                os.unlink(local_path)
        except URLError:
            print("File download error! %s" % (local_path))

def scrape_directory(url: str, dest: str):
    print("Scraping %s" % (url))
    path = urlparse(url).path.lstrip("/")
    local_path = os.path.normpath(os.path.join(dest, path))
    page = requests.get(url)
    if page.status_code == 404:
        return
    os.makedirs(local_path, exist_ok=True)
    soup: BeautifulSoup = BeautifulSoup(page.content, "html.parser")
    # Find the a hrefs, and scrape / download depending on link type
    results: ResultSet = soup.find_all(name='tr')
    results.pop(0)
    for row in results:
        child_url = list(list(row.children)[3].children)[1]["href"]
        if list(list(row.children)[1].children)[1]["src"] == "/ftp/geticon.axd?file=":
            scrape_directory(child_url, dest)
        else:
            modified_date = datetime.strptime(list(list(row.children)[5].children)[0].strip(), "%Y/%m/%d %H:%M")
            scrape_file(child_url, modified_date, dest)


def main() -> int:
    parser = argparse.ArgumentParser(description="3gpp Specs scraper.", prog="scrape-3gpp-specs")
    parser.add_argument(
        "--output",
        action="store",
        type=str,
        required=True,
        help="Directory to scrape specs to.",
    )
    
    args = parser.parse_args()

    scrape_directory(URL, args.output)

if __name__ == "__main__":
    exit(main())
