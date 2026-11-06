"""Scarica i voti per giornata da fantacalcio.it e li salva in data/raw/ (non versionato).

Uso: python scripts/fetch_votes.py 2026-27 1 10
"""
import csv
import html as htmllib
import pathlib
import re
import sys
import time
import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130 Safari/537.36"
URL = "https://www.fantacalcio.it/voti-fantacalcio-serie-a/{season}/{day}"
SOURCES = ("fc", "stat", "ita")  # ordine delle colonne nella pagina
SV = "55"  # valore usato dal sito per "senza voto"

ROW = re.compile(r"<tr>(.*?)</tr>", re.S)
LINK = re.compile(r'href="https://www\.fantacalcio\.it/serie-a/squadre/([^/]+)/([^/]+)/(\d+)(?:/[\d-]+)?"')
ROLE = re.compile(r'class="role" data-value="([a-z]+)"')
NAME = re.compile(r'player-name player-link".*?<span>(.*?)</span>', re.S)
GRADE = re.compile(r'class="player-grade[^"]*" data-value="([^"]*)"')
FANTA = re.compile(r'class="player-fanta-grade[^"]*" data-value="([^"]*)"')
BONUS = re.compile(r'class="player-bonus[^"]*" data-value="([^"]*)" title="([^"]*)"')


def num(value):
    return None if value == SV else float(value.replace(",", "."))


def parse(html, day):
    for row in ROW.findall(html):
        link, role = LINK.search(row), ROLE.search(row)
        grades, fanta = GRADE.findall(row), FANTA.findall(row)
        if not (link and role) or role.group(1) == "all" or len(grades) != 3:
            continue
        bonus = {title: value for value, title in BONUS.findall(row)}
        rec = {
            "giornata": day,
            "id": link.group(3),
            "nome": htmllib.unescape(NAME.search(row).group(1).strip()),
            "squadra": link.group(1),
            "ruolo": role.group(1),
            "gol_subiti": bonus.get("Gol subiti", "0"),
        }
        for src, g, f in zip(SOURCES, grades, fanta):
            rec[f"v_{src}"], rec[f"fv_{src}"] = num(g), num(f)
        yield rec


def main(season, first, last):
    out = pathlib.Path("data/raw")
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for day in range(first, last + 1):
        req = urllib.request.Request(URL.format(season=season, day=day), headers={"User-Agent": UA})
        html = urllib.request.urlopen(req, timeout=60).read().decode("utf8")
        got = list(parse(html, day))
        print(season, day, len(got), flush=True)
        rows += got
        time.sleep(2)
    with open(out / f"voti_{season}.csv", "w", newline="", encoding="utf8") as fh:
        writer = csv.DictWriter(fh, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
