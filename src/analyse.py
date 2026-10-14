"""Exploratory analysis: prints the numbers the page will recompute from the payload.

Measure A (source A, bout level): on the last days, how often does a rikishi who still needs
his eighth win beat an opponent who does not, against what a rating model expected?
Measure B (source B, tournament level): how many rikishi finish 8-7 against 7-8?
Measure C (source A): what happens the next time the same two meet?
"""
import math, sys
from collections import defaultdict
from load import load_api, load_sumodb, WIN, LOSS, FWIN, FLOSS

ERAS = [("1958-1988", "195801", "198811"), ("1989-2000 (paper)", "198901", "200001"),
        ("2000-2011", "200003", "201101"), ("2011-2026", "201105", "202609")]


def era_of(b):
    for name, lo, hi in ERAS:
        if lo <= b <= hi:
            return name
    return None


def pre_records(entries):
    """(basho, rid) -> list of (wins, losses) before each day 1..15."""
    out = {}
    for k, e in entries.items():
        w = l = 0
        pre = []
        for res in e["record"]:
            pre.append((w, l))
            if res in (WIN, FWIN):
                w += 1
            elif res in (LOSS, FLOSS, "absent"):
                l += 1
        out[k] = pre
    return out


def on_margin(w, day):
    return w < 8 and w + (16 - day) >= 8


def elo(bouts, skip=frozenset(), K=24.0):
    """Sequential Elo over non-fusen bouts; returns expected P(a wins) for every bout.

    Bouts whose index is in `skip` (the ones under test) are predicted but never learned from,
    so a thrown bout cannot inflate the rating that judges the next meeting."""
    R = defaultdict(lambda: 1500.0)
    exp = []
    for i, bt in enumerate(bouts):
        ra, rb = R[bt["a"]], R[bt["b"]]
        p = 1.0 / (1.0 + 10 ** ((rb - ra) / 400.0))
        exp.append(p)
        if not bt["fusen"] and i not in skip:
            s = 1.0 if bt["a_won"] else 0.0
            R[bt["a"]] += K * (s - p)
            R[bt["b"]] -= K * (s - p)
    return exp


def main():
    entries, bouts, problems = load_api()
    for k, v in problems.items():
        print("instrument:", k, len(v), v[:3])
    pre = pre_records(entries)
    bad = {k for k, e in entries.items() if "" in e["record"]}
    print("instrument: entries with a blank day (excluded)", len(bad))
    skip = set()
    for i, bt in enumerate(bouts):
        ka, kb = (bt["basho"], bt["a"]), (bt["basho"], bt["b"])
        if bt["day"] >= 11 and ka in pre and kb in pre:
            if on_margin(pre[ka][bt["day"] - 1][0], bt["day"]) != on_margin(pre[kb][bt["day"] - 1][0], bt["day"]):
                skip.add(i)
    exp = elo(bouts, skip, K=10)
    print("bouts", len(bouts), "fusen", sum(b["fusen"] for b in bouts))

    # calibration control: non-margin bouts days 11-15, by decile of expectation
    print("\nCalibration (days 11-15, neither on the margin, no fusen):")
    cal = defaultdict(lambda: [0, 0.0, 0])
    tagged = []
    for bt, p in zip(bouts, exp):
        ea, eb = entries.get((bt["basho"], bt["a"])), entries.get((bt["basho"], bt["b"]))
        if ea is None or eb is None or (bt["basho"], bt["a"]) in bad or (bt["basho"], bt["b"]) in bad:
            continue
        wa, la = pre[(bt["basho"], bt["a"])][bt["day"] - 1]
        wb, lb = pre[(bt["basho"], bt["b"])][bt["day"] - 1]
        ma, mb = on_margin(wa, bt["day"]), on_margin(wb, bt["day"])
        tagged.append((bt, p, wa, la, wb, lb, ma, mb))
        if bt["day"] >= 11 and not ma and not mb and not bt["fusen"]:
            c = cal[(era_of(bt["basho"]), min(9, int(p * 10)))]
            c[0] += 1; c[1] += p; c[2] += bt["a_won"]
    for era, *_ in ERAS:
        row = []
        for dec in range(10):
            n, sp, sw = cal[(era, dec)]
            if n:
                row.append(f"{sp/n:.2f}/{sw/n:.2f}({n})")
        print(" ", era, " ".join(row))

    # measure A
    print("\nMeasure A: margin rikishi vs non-margin opponent (no fusen)")
    for day in (15, 14, 13, 12, 11):
        for era, *_ in ERAS:
            n = won = ex = 0
            for bt, p, wa, la, wb, lb, ma, mb in tagged:
                if bt["day"] != day or bt["fusen"] or ma == mb or era_of(bt["basho"]) != era:
                    continue
                if day == 15 and not ((wa == 7 and la == 7) or (wb == 7 and lb == 7)):
                    pass
                won += bt["a_won"] if ma else (not bt["a_won"])
                ex += p if ma else 1 - p
                n += 1
            if n:
                print(f"  day {day} {era:18s} n={n:5d} won {won/n:.3f} expected {ex/n:.3f} excess {(won-ex)/n:+.3f}")

    # fusen on day 15 for margin wrestlers
    fz = defaultdict(lambda: [0, 0])
    for bt, p, wa, la, wb, lb, ma, mb in tagged:
        if bt["day"] == 15 and ma != mb:
            fz[era_of(bt["basho"])][0] += 1
            fz[era_of(bt["basho"])][1] += bt["fusen"]
    print("day-15 margin bouts decided by default:", dict(fz))

    # measure B from SumoDB
    print("\nMeasure B (SumoDB): share finishing 8-7 vs 7-8, full 15 bouts fought or defaulted, no absences")
    db = load_sumodb()
    for era, *_ in ERAS:
        cnt = defaultdict(int)
        tot = 0
        for b, rows in db.items():
            if era_of(b) != era:
                continue
            for div, rk, name, s in rows:
                if "-" in s:
                    continue
                w = sum(c in "Ww" for c in s)
                cnt[w] += 1; tot += 1
        if tot:
            print(f"  {era:18s} n={tot} " + " ".join(f"{k}:{cnt[k]/tot*100:.1f}" for k in range(4, 12)),
                  f" 8/7={cnt[8]/max(1,cnt[7]):.2f} 9/6={cnt[9]/max(1,cnt[6]):.2f} 10/5={cnt[10]/max(1,cnt[5]):.2f}")

    # measure C: next meeting after a day 13-15 margin bout (margin rikishi vs non-margin)
    print("\nMeasure C: next meeting of the same pair, from the margin rikishi's side")
    nxt = {}
    by_pair = defaultdict(list)
    for i, (bt, *_rest) in enumerate(tagged):
        by_pair[(bt["a"], bt["b"])].append(i)
    res = defaultdict(lambda: [0, 0, 0.0])
    for pair, idx in by_pair.items():
        for j in range(len(idx) - 1):
            bt, p, wa, la, wb, lb, ma, mb = tagged[idx[j]]
            if bt["day"] < 13 or ma == mb or bt["fusen"]:
                continue
            margin_is_a = ma
            margin_won = bt["a_won"] == margin_is_a
            nb, np_ = tagged[idx[j + 1]][0], tagged[idx[j + 1]][1]
            if nb["fusen"]:
                continue
            w = nb["a_won"] == margin_is_a
            e = np_ if margin_is_a else 1 - np_
            r = res[(era_of(bt["basho"]), margin_won)]
            r[0] += 1; r[1] += w; r[2] += e
    plc = defaultdict(lambda: [0, 0, 0.0])
    for pair, idx in by_pair.items():
        for j in range(len(idx) - 1):
            bt, p, wa, la, wb, lb, ma, mb = tagged[idx[j]]
            if bt["day"] < 13 or ma or mb or bt["fusen"]:
                continue
            nb, np_ = tagged[idx[j + 1]][0], tagged[idx[j + 1]][1]
            if nb["fusen"]:
                continue
            winner_is_a = bt["a_won"]
            r = plc[era_of(bt["basho"])]
            r[0] += 1; r[1] += nb["a_won"] == winner_is_a; r[2] += np_ if winner_is_a else 1 - np_
    for era, *_ in ERAS:
        n, w, e = plc[era]
        if n:
            print(f"  PLACEBO {era:18s} winner of a non-margin late bout n={n:5d} next won {w/n:.3f} expected {e/n:.3f} excess {(w-e)/n:+.3f}")
    for era, *_ in ERAS:
        for mw in (True, False):
            n, w, e = res[(era, mw)]
            if n:
                print(f"  {era:18s} margin {'won ' if mw else 'lost'} n={n:5d} next won {w/n:.3f} expected {e/n:.3f} excess {(w-e)/n:+.3f}")


if __name__ == "__main__":
    main()
