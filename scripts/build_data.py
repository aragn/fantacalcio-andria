"""Unisce voti, quotazioni e rose e scrive docs/data.json con le sole statistiche derivate.

Uso: python scripts/build_data.py
Input in data/raw/ (non versionati): voti_2026-27.csv, quotazioni_2026-27.csv, rose_2026-27.txt
Formato rose, una squadra per riga: Squadra>>id|ruoli|nome|prezzo;id|ruoli|nome|prezzo;...
"""
import csv
import json
import pathlib
import re
import statistics as st
from collections import defaultdict

RAW = pathlib.Path("data/raw")
SEASON = "2026-27"
VOTO = "stat"  # voto statistico Alvin, da regolamento 2026/27
# I ruoli Mantra contengono ';', quindi un giocatore si riconosce dal pattern completo.
PLAYER = re.compile(r"(\d+)\|([^|]+)\|([^|]+)\|(\d+)(?:;|$)")


def load_votes():
    games, days = defaultdict(list), set()
    with open(RAW / f"voti_{SEASON}.csv", encoding="utf8") as fh:
        for row in csv.DictReader(fh):
            days.add(int(row["giornata"]))
            if not row[f"v_{VOTO}"]:
                continue  # senza voto
            fv = float(row[f"fv_{VOTO}"])
            if row["ruolo"] == "p" and row["gol_subiti"] == "0":
                fv += 1  # Clean Sheet: il fantavoto del sito non lo include
            games[row["id"]].append((float(row[f"v_{VOTO}"]), fv))
    return games, max(days)


def load_quotes():
    with open(RAW / f"quotazioni_{SEASON}.csv", encoding="utf8") as fh:
        return {r["id"]: r for r in csv.DictReader(fh)}


def load_rosters():
    roster = {}
    with open(RAW / f"rose_{SEASON}.txt", encoding="utf8") as fh:
        for line in fh:
            team, players = line.strip().split(">>")
            for pid, roles, name, price in PLAYER.findall(players):
                roster[pid] = {"team": team, "ruoli": roles, "nome": name, "crediti": int(price)}
    return roster


def assign_keeper_trios(roster, quotes, games):
    """Il terzetto si compra in blocco: il prezzo sta su una riga sola, spesso quella del terzo portiere.

    Si somma il costo dei portieri dello stesso club nella stessa rosa e lo si assegna a chi gioca.
    """
    groups = defaultdict(list)
    for pid, p in roster.items():
        if p["ruoli"] == "Por" and pid in quotes:
            groups[(p["team"], quotes[pid]["squadra"])].append(pid)
    for pids in groups.values():
        if len(pids) < 2:
            continue
        total = sum(roster[p]["crediti"] for p in pids)
        starter = max(pids, key=lambda p: len(games.get(p, [])))
        for p in pids:
            roster[p]["crediti"] = total if p == starter else 0
            roster[p]["terzetto"] = True


def main():
    games, days = load_votes()
    quotes, roster = load_quotes(), load_rosters()
    spent = defaultdict(int)
    for p in roster.values():
        spent[p["team"]] += p["crediti"]
    print("rose:", len(roster), "spesa per squadra:", dict(spent))
    print("senza quotazione:", [p["nome"] for i, p in roster.items() if i not in quotes])
    assign_keeper_trios(roster, quotes, games)

    players = []
    for pid, played in games.items():
        if pid not in quotes or len(played) < 2:
            continue
        q, own = quotes[pid], roster.get(pid, {})
        v, fv = [g[0] for g in played], [g[1] for g in played]
        players.append({
            "id": int(pid),
            "nome": q["nome"],
            "squadra": q["squadra"].title(),
            "r": q["r"],
            "rm": q["rm"],
            "qi": int(q["qi"]),
            "crediti": own.get("crediti"),
            "team": own.get("team"),
            "terzetto": own.get("terzetto", False),
            "pv": len(played),
            "punti": round(sum(fv), 1),
            "fm": round(st.mean(fv), 2),
            "mv": round(st.mean(v), 2),
            "sd_fv": round(st.stdev(fv), 3),
            "sd_v": round(st.stdev(v), 3),
        })
    players.sort(key=lambda p: -p["punti"])
    # Totali sull'intera rosa, compresi i giocatori senza voti: i loro crediti sono comunque spesi.
    totals = defaultdict(lambda: {"crediti": 0, "punti": 0.0})
    for pid, own in roster.items():
        totals[own["team"]]["crediti"] += own["crediti"]
        totals[own["team"]]["punti"] += sum(g[1] for g in games.get(pid, []))
    squadre = [{"team": t, "crediti": v["crediti"], "punti": round(v["punti"], 1)} for t, v in totals.items()]
    data = {"stagione": SEASON, "giornate": days, "squadre": squadre, "players": players}
    pathlib.Path("docs").mkdir(exist_ok=True)
    with open("docs/data.json", "w", encoding="utf8") as fh:
        json.dump(data, fh, ensure_ascii=False, separators=(",", ":"))
    paid = [p for p in players if p["crediti"] is not None]
    print("giornate", days, "giocatori", len(players), "in rosa con voti", len(paid))


if __name__ == "__main__":
    main()
