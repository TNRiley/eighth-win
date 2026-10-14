"""Download SumoDB's final-day results page for every basho (the independent second source).

The day-15 page carries a 'Yusho Arasoi' block listing every Makuuchi and Juryo rikishi with
his full 15-character win/loss string, which is all measure B needs. One page per basho,
one request every 1.5 s. Saved gzipped to src/raw/sumodb/<bashoId>.html.gz; resumable.
"""
import gzip, os, sys, time, urllib.request
from fetch_banzuke import basho_ids

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "raw", "sumodb")
os.makedirs(OUT, exist_ok=True)
URL = "https://sumodb.sumogames.de/Results.aspx?b={}&d=15"

ids = list(basho_ids())
if '--reverse' in sys.argv:  # a second worker can walk from the other end
    ids.reverse()
for b in ids:
    path = os.path.join(OUT, f"{b}.html.gz")
    if os.path.exists(path):
        continue
    for attempt in range(4):
        try:
            req = urllib.request.Request(URL.format(b), headers={"User-Agent": "eighth-win research script (one page per basho)"})
            with urllib.request.urlopen(req, timeout=90) as r:
                body = r.read()
            break
        except Exception as e:
            print("retry", b, e, file=sys.stderr)
            time.sleep(10 * (attempt + 1))
    else:
        raise SystemExit(f"failed {b}")
    with gzip.open(path, "wb") as f:
        f.write(body)
    print(b, len(body), flush=True)
    time.sleep(1.5)
