"""Second-pass probes on measure A: is the expectation biased by record context?

1. Day-15 placebo: rikishi on 6-8 and 8-6 (no eighth win at stake) against the same kind of
   opponents, judged by the same Elo.
2. A second, independent expectation: banzuke rank difference, fitted per era on non-test bouts.
3. Rematch measure C against an early-day placebo (days 1-5 winners).
"""
import math
from collections import defaultdict
import analyse as A

entries, bouts, _ = A.load_api()
pre = A.pre_records(entries)
bad = {k for k, e in entries.items() if "" in e["record"]}
skip, info = set(), {}
for i, bt in enumerate(bouts):
    ka, kb = (bt["basho"], bt["a"]), (bt["basho"], bt["b"])
    if ka in pre and kb in pre and ka not in bad and kb not in bad:
        wa, la = pre[ka][bt["day"] - 1]; wb, lb = pre[kb][bt["day"] - 1]
        ma, mb = A.on_margin(wa, bt["day"]), A.on_margin(wb, bt["day"])
        info[i] = (wa, la, wb, lb, ma, mb)
        if bt["day"] >= 11 and ma != mb:
            skip.add(i)
exp = A.elo(bouts, skip, K=10)

# 2. rank model: logistic on rankValue difference, fitted per era on non-test bouts, days 1-15
def rv(k):
    return entries[k]["rankValue"]
fit = {}
for era, *_ in A.ERAS:
    xs, ys = [], []
    for i, bt in enumerate(bouts):
        if i in skip or bt["fusen"] or i not in info or A.era_of(bt["basho"]) != era:
            continue
        xs.append((rv((bt["basho"], bt["b"])) - rv((bt["basho"], bt["a"]))) / 100.0); ys.append(bt["a_won"])
    b0 = b1 = 0.0
    for _ in range(30):  # Newton
        g0 = g1 = h00 = h01 = h11 = 0.0
        for x, y in zip(xs, ys):
            p = 1 / (1 + math.exp(-(b0 + b1 * x)))
            g0 += y - p; g1 += (y - p) * x
            w = p * (1 - p); h00 += w; h01 += w * x; h11 += w * x * x
        det = h00 * h11 - h01 * h01
        b0 += (h11 * g0 - h01 * g1) / det; b1 += (h00 * g1 - h01 * g0) / det
    fit[era] = (b0, b1)
    print(f"rank model {era}: b1={b1:.3f} per 100 rank units, n={len(xs)}")

def prank(i):
    bt = bouts[i]; b0, b1 = fit[A.era_of(bt["basho"])]
    x = (rv((bt["basho"], bt["b"])) - rv((bt["basho"], bt["a"]))) / 100.0
    return 1 / (1 + math.exp(-(0 * b0 + b1 * x)))  # no side intercept: a/b order is arbitrary

print("\nDay 15, by the record of the focal rikishi, against opponents who are not on 7-7")
res = defaultdict(lambda: [0, 0, 0.0, 0.0])
for i, bt in enumerate(bouts):
    if bt["day"] != 15 or bt["fusen"] or i not in info:
        continue
    wa, la, wb, lb, ma, mb = info[i]
    for side in (0, 1):
        w, l, wo, lo = (wa, la, wb, lb) if side == 0 else (wb, lb, wa, la)
        if (wo, lo) == (7, 7) or w + l != 14:
            continue
        if (w, l) not in ((7, 7), (6, 8), (8, 6)):
            continue
        won = bt["a_won"] if side == 0 else not bt["a_won"]
        pe = exp[i] if side == 0 else 1 - exp[i]
        pr = prank(i) if side == 0 else 1 - prank(i)
        r = res[(A.era_of(bt["basho"]), f"{w}-{l}")]
        r[0] += 1; r[1] += won; r[2] += pe; r[3] += pr
for era, *_ in A.ERAS:
    for rec in ("7-7", "6-8", "8-6"):
        n, w, e, rr = res[(era, rec)]
        if n:
            se = math.sqrt(0.25 / n)
            print(f"  {era:18s} {rec} n={n:5d} won {w/n:.3f}  vs Elo {(w-e)/n:+.3f}  vs rank {(w-rr)/n:+.3f}  (se {se:.3f})")

print("\nDay 15 7-7 vs non-margin, by division of the 7-7 rikishi")
dv = defaultdict(lambda: [0, 0, 0.0])
for i, bt in enumerate(bouts):
    if bt["day"] != 15 or bt["fusen"] or i not in info:
        continue
    wa, la, wb, lb, ma, mb = info[i]
    if ma == mb:
        continue
    side = 0 if ma else 1
    k = (bt["basho"], bt["a"] if side == 0 else bt["b"])
    won = bt["a_won"] if side == 0 else not bt["a_won"]
    pe = exp[i] if side == 0 else 1 - exp[i]
    r = dv[(A.era_of(bt["basho"]), entries[k]["div"])]
    r[0] += 1; r[1] += won; r[2] += pe
for k in sorted(dv):
    n, w, e = dv[k]
    print(f"  {k} n={n} won {w/n:.3f} excess {(w-e)/n:+.3f}")

print("\nRematch: next meeting, from the side of whoever won the first bout")
nxt, last = {}, {}
for i in range(len(bouts) - 1, -1, -1):
    k = (bouts[i]["a"], bouts[i]["b"])
    if k in last:
        nxt[i] = last[k]
    last[k] = i
rm = defaultdict(lambda: [0, 0, 0.0])
for i, bt in enumerate(bouts):
    if bt["fusen"] or i not in nxt or i not in info or bouts[nxt[i]]["fusen"]:
        continue
    wa, la, wb, lb, ma, mb = info[i]
    if bt["day"] <= 5:
        kind = "early-day winner (placebo)"
    elif bt["day"] >= 13 and ma != mb:
        kind = "margin rikishi won" if (bt["a_won"] == ma) else "margin rikishi lost"
    elif bt["day"] >= 13:
        kind = "late, nobody on margin"
    else:
        continue
    j = nxt[i]
    if kind == "margin rikishi lost":  # look from the margin rikishi's side
        focal_a = ma
    else:
        focal_a = bt["a_won"] if kind != "margin rikishi won" else ma
    r = rm[(A.era_of(bt["basho"]), kind)]
    r[0] += 1; r[1] += bouts[j]["a_won"] == focal_a; r[2] += exp[j] if focal_a else 1 - exp[j]
for k in sorted(rm):
    n, w, e = rm[k]
    print(f"  {k[0]:18s} {k[1]:28s} n={n:6d} next won {w/n:.3f} excess {(w-e)/n:+.3f} (se {math.sqrt(.25/n):.3f})")
