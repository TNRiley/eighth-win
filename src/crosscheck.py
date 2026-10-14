"""Compare the two sources rikishi by rikishi: same basho, same banzuke slot, same 15 days?

Matching is on (basho, rank slot), never on name, because romanisations differ between sites.
Prints agreement counts and the kinds of disagreement, which go into the methods panel.
"""
import re, sys
from collections import Counter
from load import load_api, load_sumodb

CODE = {"win": "W", "loss": "L", "fusen win": "w", "fusen loss": "l", "absent": "-", "": "?"}
PFX = {"Yokozuna": "Y", "Ozeki": "O", "Sekiwake": "S", "Komusubi": "K", "Maegashira": "M", "Juryo": "J"}


def slot(rank):
    m = re.match(r"(\w+) (\d+) (East|West)", rank)
    if not m:
        return None
    return f"{PFX.get(m.group(1), '?')}{m.group(2)}{m.group(3)[0].lower()}"


def main(verbose=False):
    entries, _, _ = load_api()
    db = load_sumodb()
    api, by_name = {}, {}
    for (b, rid), e in entries.items():
        rec = (e["name"], "".join(CODE[r] for r in e["record"]))
        by_name[(b, e["name"].lower())] = rec
        s = slot(e["rank"])
        if s:
            api[(b, s)] = rec
    stats = Counter()
    kinds = Counter()
    examples = []
    for b, rows in db.items():
        for div, rk, name, s in rows:
            key = (b, re.sub(r"(HD|TD)$", "", rk))
            hit = api.get(key)
            if hit is None or hit[0].lower() != name.lower():
                # the two sites sometimes slot the same man differently; fall back to the name
                alt = by_name.get((b, name.lower()))
                if alt is not None:
                    if hit is not None:
                        kinds["slot differs, matched by name"] += 1
                    hit = alt
            if hit is None:
                stats["sumodb only"] += 1
                continue
            aname, a = hit
            if a == s:
                stats["identical"] += 1
                continue
            # same up to fusen/absence notation?
            norm = lambda x: x.replace("w", "W").replace("l", "L")
            if "?" in a:
                stats["api has blank days"] += 1
                if all(c == "?" or c == d or norm(c) == norm(d) for c, d in zip(a, s)):
                    kinds["blank days only"] += 1
                continue
            if norm(a) == norm(s):
                stats["differ only in default notation"] += 1
                continue
            same_wins = sum(c in "Ww" for c in a) == sum(c in "Ww" for c in s)
            stats["different" + (" (same win total)" if same_wins else " (different win total)")] += 1
            if len(examples) < 25:
                examples.append((b, rk, name, aname, a, s))
    total = sum(stats.values())
    print("rows compared", total)
    for k, v in stats.most_common():
        print(f"  {k:40s} {v:6d}  {v/total*100:.2f}%")
    print(kinds)
    for x in examples[: 25 if verbose else 8]:
        print("  ", x)
    return {**stats, **kinds}


if __name__ == "__main__":
    main("-v" in sys.argv)
    jsa_check()


ALT = {"白丸": "W", "黒丸": "L", "不戦勝": "w", "不戦敗": "l"}


def jsa_check():
    """Latest basho only: the JSA's own chart against sumo-api, bout by bout (day, opponent, result)."""
    import glob, json, os
    from load import RAW
    entries, _, _ = load_api()
    latest = max(b for b, _ in entries)
    api = {e["name"].lower(): e for (b, _), e in entries.items() if b == latest}
    seen, same, diff, alts = set(), 0, [], Counter()
    for f in sorted(glob.glob(os.path.join(RAW, "jsa", "hoshitori_*.json"))):
        d = json.load(open(f, encoding="utf-8"))
        names = {}
        for side in ("E", "W"):
            for r in d["BanzukeTable"][side]:
                names[str(r["rikishi_id"])] = r["shikona_eng"]
        for side in ("E", "W"):
            for rid, days in d["TorikumiData"][side].items():
                if rid in seen:
                    continue
                seen.add(rid)
                e = api.get(names.get(rid, "").lower())
                for day in range(1, 16):
                    x = days.get(str(day)) if isinstance(days, dict) else None
                    alt = x.get("alt", "") if x else ""
                    alts[alt] += 1
                    if alt not in ALT:
                        continue
                    if e is None:
                        diff.append((names.get(rid), day, "not in sumo-api"))
                        continue
                    res = CODE[e["record"][day - 1]]
                    opp = entries.get((latest, e["opp"][day - 1]))
                    # an opponent from Makushita has no sumo-api entry here, so only the result is compared
                    opp_ok = opp is None or x.get("opponent_name_eng", "").lower() == opp["name"].lower()
                    if res == ALT[alt] and opp_ok:
                        same += 1
                    else:
                        diff.append((names.get(rid), day, alt, res, x.get("opponent_name_eng")))
    print("JSA vs sumo-api,", latest, ": bouts identical", same, "different", len(diff), diff[:5], dict(alts))
    return {"basho": latest, "identical": same, "different": len(diff)}
