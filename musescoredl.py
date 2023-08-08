#!/usr/bin/python3
import sys
import os
import re
import requests
import tempfile
from PIL import Image
from bs4 import BeautifulSoup
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF
from pypdf import PdfMerger

if len(sys.argv) < 2:
    print("Missing score URL")
    print(f"Usage: {sys.argv[0]} <url>")
    sys.exit(0)


def get_score_title(url: str) -> str:
    response = requests.get(url=url)
    parser = BeautifulSoup(response.text, "html.parser")
    return parser.find("meta", attrs={"property": "og:title"})["content"].strip(" .")


def get_score_id(url: str) -> str:
    return url.rsplit("/", maxsplit=1)[-1]


# https://musescore.com/static/public/build/musescore_es6/202308/2946.b939fe57e9c71db1cf2d0dbf4aceab6d.js
HEADERS = {"Authorization": "8c022bdef45341074ce876ae57a48f64b86cdcf5"}
BASE_URL = "https://musescore.com/api/jmuse"
SCORE_TITLE = get_score_title(sys.argv[1])
SCORE_ID = get_score_id(sys.argv[1])
DIRNAME = "scores"
OUTFILE = f"{DIRNAME}/{SCORE_TITLE}.pdf"

if not os.path.isdir(DIRNAME):
    os.makedirs(DIRNAME)

merger = PdfMerger()
index = 0
while True:
    params = {
        "id": SCORE_ID,
        "index": index,
        "type": "img",
        "v2": 1,
    }
    response = requests.get(url=BASE_URL, params=params, headers=HEADERS)
    if response.status_code != 200:
        print(f"Received a {response.status_code} response code")
        break
    response = requests.get(url=response.json()["info"]["url"])
    if response.status_code != 200:
        break

    _, img_file = tempfile.mkstemp()
    _, pdf_file = tempfile.mkstemp()
    with open(img_file, "wb") as f:
        f.write(response.content)
    if response.headers["Content-Type"] in ("image/svg", "image/svg+xml"):
        drawing = svg2rlg(img_file)
        renderPDF.drawToFile(drawing, pdf_file)
    elif response.headers["Content-Type"] == "image/png":
        Image.open(img_file).save(pdf_file, "PDF", resolution=100.0)
    else:
        print(f"Received the following MIME type: {response.headers['Content-Type']}")
        exit(1)

    merger.append(pdf_file)
    try:
        os.remove(img_file)
        os.remove(pdf_file)
    except PermissionError:
        pass

    index += 1

merger.write(OUTFILE)
print(f"Saved PDF to {OUTFILE}")
