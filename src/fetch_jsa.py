"""Fetch the Japan Sumo Association's own hoshitori (win/loss chart) for the latest basho.

The page renders its table from a POST to /ResultData/hoshitoriAjax/<division>/<side>/, and that
endpoint answers 403 unless the request carries a cookie the page sets in inline script
(document.cookie = "<name>=<value>; path=/ResultData ..."). The name and value change from load
to load ("game=cat", "mischeief=OK"), so the page is read first and its cookie replayed.
Only the current basho is served, so this is a spot check of the latest tournament.
"""
import json, os, re, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "raw", "jsa")
os.makedirs(OUT, exist_ok=True)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"

for div in (1, 2):  # 1 Makuuchi, 2 Juryo
    page = f"https://www.sumo.or.jp/ResultData/hoshitori/{div}/1/"
    html = urllib.request.urlopen(urllib.request.Request(page, headers={"User-Agent": UA}), timeout=60).read().decode("utf-8")
    m = re.search(r'document\.cookie\s*=\s*"([^=;"]+)=([^;"]*);', html)
    cookie = f"{m.group(1)}={m.group(2)}"
    for ew in (1, 2):
        req = urllib.request.Request(
            f"https://www.sumo.or.jp/ResultData/hoshitoriAjax/{div}/{ew}/",
            data=f"kakuzuke_id={div}&ew_flg={ew}".encode(),
            headers={"User-Agent": UA, "Cookie": cookie, "X-Requested-With": "XMLHttpRequest", "Referer": page,
                     "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"})
        body = urllib.request.urlopen(req, timeout=60).read()
        json.loads(body)
        with open(os.path.join(OUT, f"hoshitori_{div}_{ew}.json"), "wb") as f:
            f.write(body)
        print(div, ew, cookie, len(body))
