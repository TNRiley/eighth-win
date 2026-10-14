"""Shared loaders for both sources.

Source A: sumo-api.com banzuke files (one per basho per division), giving every bout with the
opponent's id. Source B: SumoDB day-15 pages, giving each rikishi's 15-day win/loss string.
"""
import glob, gzip, html, json, os, re
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")

WIN, LOSS, FWIN, FLOSS, ABSENT, BLANK = "win", "loss", "fusen win", "fusen loss", "absent", ""


def load_api():
    """Return (entries, bouts, problems).

    entries[(basho, rid)] = dict(name, rank, rankValue, div, record=[15 results], opp=[15 ids])
    bouts: list of dict(basho, day, a, b, a_won, fusen, div_a, div_b), one per bout, deduplicated.
    """
    entries = {}
    problems = defaultdict(list)
    for f in sorted(glob.glob(os.path.join(RAW, "banzuke", "*.json"))):
        basho, div = os.path.basename(f)[:-5].split("_")
        d = json.load(open(f, encoding="utf-8"))
        for side in ("east", "west"):
            for r in d.get(side) or []:
                rid = r["rikishiID"]
                rec = r.get("record")
                if rec is None:
                    problems["no record (totals only)"].append((basho, r.get("shikonaEn")))
                    continue
                if len(rec) != 15:
                    problems["record not 15 days"].append((basho, r.get("shikonaEn"), len(rec)))
                    continue
                entries[(basho, rid)] = dict(
                    name=r.get("shikonaEn", ""), rank=r.get("rank", ""), rankValue=r.get("rankValue", 0),
                    div=div, record=[x["result"] for x in rec], opp=[x["opponentID"] for x in rec],
                    kim=[x.get("kimarite", "") for x in rec],
                    totals=(r.get("wins"), r.get("losses"), r.get("absences")))
    bouts = {}
    for (basho, rid), e in entries.items():
        for day in range(15):
            res, opp = e["record"][day], e["opp"][day]
            if res not in (WIN, LOSS, FWIN, FLOSS):
                continue
            if not opp:
                problems["result without opponent"].append((basho, e["name"], day + 1))
                continue
            key = (basho, day + 1, min(rid, opp), max(rid, opp))
            a_won = res in (WIN, FWIN)
            fusen = res in (FWIN, FLOSS)
            other = entries.get((basho, opp))
            if other is not None:
                ores = other["record"][day]
                if other["opp"][day] != rid or (ores in (WIN, FWIN)) == a_won:
                    problems["two sides disagree"].append((basho, day + 1, e["name"], other["name"], res, ores))
            if key in bouts:
                continue
            a, b = key[2], key[3]
            won = a_won if rid == a else (not a_won)
            bouts[key] = dict(basho=basho, day=day + 1, a=a, b=b, a_won=won, fusen=fusen)
    out = sorted(bouts.values(), key=lambda x: (x["basho"], x["day"], x["a"], x["b"]))
    return entries, out, problems


SYM = {"○": "W", "●": "L", "□": "w", "■": "l", "–": "-", "‒": "-"}


def load_sumodb():
    """Return {basho: [(division, rank_code, name, string15)]} from the Yusho Arasoi blocks."""
    out = {}
    for f in sorted(glob.glob(os.path.join(RAW, "sumodb", "*.html.gz"))):
        basho = os.path.basename(f)[:6]
        s = gzip.open(f).read().decode("utf-8", "replace")
        t = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s)))
        rows = []
        for div in ("Makuuchi", "Juryo"):
            i = t.find(div + " Yusho Arasoi:")
            if i < 0:
                continue
            j = t.find("Yusho Arasoi:", i + 20)
            block = t[i:j if j > 0 else len(t)]
            for m in re.finditer(r"([○●□■–‒]{15}) ([YOSKMJ]\d+[ew](?:HD|TD)?) ([A-Za-z'\-]+)", block):
                code = "".join(SYM[c] for c in m.group(1))
                rows.append((div, m.group(2), m.group(3), code))
        out[basho] = rows
    return out
