"""Shape both sources into src/payload.json: gzipped, base64 typed-array columns.

The page recomputes every statistic from these columns (including the Elo ratings), so the
only things precomputed here are the cross-source comparison and the instrument counts, which
need both raw sources side by side.

    python src/build_payload.py && python src/inject.py
"""
import base64, gzip, json, os, re, sys
from array import array
from load import load_api, load_sumodb
import crosscheck

HERE = os.path.dirname(os.path.abspath(__file__))
CODE = {"win": 0, "loss": 1, "fusen win": 2, "fusen loss": 3, "absent": 4, "": 5}


def col(typecode, values):
    a = array(typecode, values)
    if sys.byteorder != "little":
        a.byteswap()
    return base64.b64encode(gzip.compress(a.tobytes(), 9, mtime=0)).decode("ascii")


def main():
    entries, bouts, problems = load_api()
    db = load_sumodb()
    basho = sorted(set(b for b, _ in entries) | set(db))
    bidx = {b: i for i, b in enumerate(basho)}

    keys = sorted(entries, key=lambda k: (k[0], entries[k]["div"] != "Makuuchi", entries[k]["rankValue"], k[1]))
    eidx = {k: i for i, k in enumerate(keys)}
    rids = sorted(set(k[1] for k in keys))
    ridx = {r: i for i, r in enumerate(rids)}
    assert len(keys) < 65535 and len(rids) < 65535

    e_basho, e_rik, e_div, e_rank, e_days = [], [], [], [], []
    names = {}
    for k in keys:
        e = entries[k]
        e_basho.append(bidx[k[0]]); e_rik.append(ridx[k[1]])
        e_div.append(0 if e["div"] == "Makuuchi" else 1)
        e_rank.append(e["rankValue"] or 0)
        e_days.extend(CODE[r] for r in e["record"])
        names[ridx[k[1]]] = e["name"]

    b_a, b_b, b_day, b_flag = [], [], [], []
    dropped = 0
    for bt in bouts:
        ka, kb = (bt["basho"], bt["a"]), (bt["basho"], bt["b"])
        if ka not in eidx or kb not in eidx:
            dropped += 1
            continue
        b_a.append(eidx[ka]); b_b.append(eidx[kb]); b_day.append(bt["day"])
        b_flag.append((1 if bt["a_won"] else 0) | (2 if bt["fusen"] else 0))

    s_basho, s_div, s_w, s_l, s_abs = [], [], [], [], []
    for b, rows in db.items():
        for div, rk, name, s in rows:
            s_basho.append(bidx[b]); s_div.append(0 if div == "Makuuchi" else 1)
            s_w.append(sum(c in "Ww" for c in s)); s_l.append(sum(c in "Ll" for c in s)); s_abs.append(s.count("-"))

    xc = crosscheck.main()
    jsa = crosscheck.jsa_check()
    payload = {
        "basho": basho,
        "names": [names.get(i, "") for i in range(len(rids))],
        "entries": len(keys), "bouts": len(b_a), "sumodbRows": len(s_basho),
        "cols": {
            "eBasho": col("H", e_basho), "eRik": col("H", e_rik), "eDiv": col("B", e_div),
            "eRank": col("H", e_rank), "eDays": col("B", e_days),
            "bA": col("H", b_a), "bB": col("H", b_b), "bDay": col("B", b_day), "bFlag": col("B", b_flag),
            "sBasho": col("H", s_basho), "sDiv": col("B", s_div), "sW": col("B", s_w),
            "sL": col("B", s_l), "sAbs": col("B", s_abs),
        },
        "instrument": {
            "totalsOnly": len(problems.get("no record (totals only)", [])),
            "short": len(problems.get("record not 15 days", [])),
            "sidesDisagree": len(problems.get("two sides disagree", [])),
            "droppedBouts": dropped,
            "blankEntries": sum(1 for k in keys if 5 in [CODE[r] for r in entries[k]["record"]]),
            "cross": dict(xc),
            "jsa": jsa,
        },
    }
    out = os.path.join(HERE, "payload.json")
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(payload, f, separators=(",", ":"), ensure_ascii=False)
    print("payload %.0f kB, %d basho, %d entries, %d bouts, %d sumodb rows, dropped %d"
          % (os.path.getsize(out) / 1e3, len(basho), len(keys), len(b_a), len(s_basho), dropped))


if __name__ == "__main__":
    main()
