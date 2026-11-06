"""Scarica le quotazioni della stagione in corso da fantacalcio.it in data/raw/.

Uso: python scripts/fetch_quotes.py 2026-27
"""
import csv
import html as htmllib
import pathlib
import re
import sys
import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130 Safari/537.36"
URL = "https://www.fantacalcio.it/quotazioni-fantacalcio"

ROW = re.compile(r'<tr class="player-row".*?</tr>', re.S)
LINK = re.compile(r'squadre/([^/]+)/[^/]+/(\d+)"[^>]*>\s*<span>(.*?)</span>', re.S)
CLASSIC = re.compile(r'data-filter-role-classic="([a-z]+)"')
MANTRA = re.compile(r'class="role role-mantra" data-value="([a-z]+)"')
CELL = r'data-col-key="{}">\s*(-?\d+)'


def main(season):
    req = urllib.request.Request(URL, headers={"User-Agent": UA})
    html = urllib.request.urlopen(req, timeout=60).read().decode("utf8")
    rows = []
    for row in ROW.findall(html):
        team, pid, name = LINK.search(row).groups()
        rows.append({
            "id": pid,
            "nome": htmllib.unescape(name.strip()),
            "squadra": team,
            "r": CLASSIC.search(row).group(1).upper(),
            "rm": ";".join(m.capitalize() for m in MANTRA.findall(row)),
            "qi": re.search(CELL.format("m_qi"), row).group(1),
            "qa": re.search(CELL.format("m_qa"), row).group(1),
        })
    out = pathlib.Path("data/raw")
    out.mkdir(parents=True, exist_ok=True)
    with open(out / f"quotazioni_{season}.csv", "w", newline="", encoding="utf8") as fh:
        writer = csv.DictWriter(fh, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(len(rows), rows[0])


if __name__ == "__main__":
    main(sys.argv[1])
