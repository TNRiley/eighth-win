"""Download every top-two-division banzuke (with day-by-day records) from sumo-api.com.

One request per basho per division; each response carries every rikishi's 15 daily results
with opponent ids. Files land in src/raw/banzuke/<bashoId>_<Division>.json and are skipped
if already present, so the script can be re-run to resume.
"""
import json, os, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "raw", "banzuke")
os.makedirs(OUT, exist_ok=True)
API = "https://www.sumo-api.com/api/basho/{}/banzuke/{}"

def basho_ids(first=1958, last=(2026, 9)):
    for y in range(first, last[0] + 1):
        for m in (1, 3, 5, 7, 9, 11):
            if (y, m) > last:
                return
            yield f"{y}{m:02d}"

def main():
    for b in basho_ids():
        for div in ("Makuuchi", "Juryo"):
            path = os.path.join(OUT, f"{b}_{div}.json")
            if os.path.exists(path):
                continue
            for attempt in range(4):
                try:
                    with urllib.request.urlopen(API.format(b, div), timeout=60) as r:
                        body = r.read()
                    break
                except Exception as e:  # retry transient failures
                    print("retry", b, div, e, file=sys.stderr)
                    time.sleep(5 * (attempt + 1))
            else:
                raise SystemExit(f"failed {b} {div}")
            d = json.loads(body)
            if not d.get("bashoId"):
                print("empty", b, div)  # cancelled basho (2011-03, 2020-05) come back empty
            with open(path, "wb") as f:
                f.write(body)
            time.sleep(0.4)
        print(b, flush=True)

if __name__ == "__main__":
    main()
