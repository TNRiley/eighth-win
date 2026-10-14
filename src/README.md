# The Eighth Win: pipeline

Run from this directory with plain `python` (the scripts import each other).

```
python fetch_banzuke.py          # sumo-api.com, 826 files into raw/banzuke/ (resumable, ~30 min)
python fetch_sumodb.py           # SumoDB day-15 pages into raw/sumodb/ (resumable)
python fetch_sumodb.py --reverse #   ...a second worker from the newest end, optional
python fetch_jsa.py              # JSA chart for the current tournament into raw/jsa/
python build_payload.py          # shape both sources, run the cross-checks, write payload.json
python inject.py                 # splice into template.html, write ../index.html, wrap + breadcrumb
```

| file | what |
|---|---|
| `load.py` | loaders for both sources |
| `crosscheck.py` | SumoDB against sumo-api by rank slot (name fallback), and the JSA spot check |
| `build_payload.py` | gzipped base64 typed-array columns plus the instrument counts |
| `template.html` | the page; every statistic is computed here from the payload |
| `analyse.py`, `probe.py` | exploratory analysis in Python that the page reproduces (eras, placebos, rank model, rematch by day) |

`raw/` and `payload.json` are not committed. See `../REBUILD.md` for the expected values.
