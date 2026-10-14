# 🤼 The Eighth Win

**Sumo's 2011 match-fixing purge left no mark on the final day: a wrestler who needed his eighth win beat an opponent who did not 62% of the time in the decade before it and 61% in the eight years after, against about 49% expected.**

→ **[Open it](https://tnriley.github.io/eighth-win/)**

Every top-division bout since 1958 (197,779 of them), rated in the browser, and the famous Freakonomics finding rerun from scratch: it reproduces Duggan and Levitt's published figures almost to the decimal, then follows the final-day 7-7 advantage for 26 more years. Two measures from two sites, one about bouts and one about final records, track each other at r = 0.97; both fell sharply in 2000, when a former wrestler went public, and neither moved when 23 wrestlers were expelled in 2011. What did change things was the schedule: since 2019 most 7-7 wrestlers are drawn against each other. The rematch payback the paper read as proof of trading turns out to show up after ordinary late bouts too, so it is documented as the half that did not work.

## Running it

One self-contained HTML file. No build step, no server, no network access at runtime — open `index.html` in a browser, or serve the directory with any static host.

```bash
python3 -m http.server 8000   # then visit http://localhost:8000
```

## Rebuilding it from scratch

[REBUILD.md](REBUILD.md) is written for an LLM with a shell and nothing else: the data sources and their quirks, the processing decisions, the page's structure and interactions, and a table of expected values to check the result against.

## Source

The full build pipeline is in [`src/`](src/), with a README describing how to regenerate the page from scratch.

## Data

- **[sumo-api.com, banzuke endpoint: every Makuuchi and Juryo wrestler's day-by-day results and opponents, March 1958 to September 2026 (826 requests, read 2026-10-14)](https://www.sumo-api.com/)** — No licence stated; match results used as factual records
- **[SumoDB, final-day results page of each tournament: every top-two-division wrestler's fifteen-day win/loss string (413 pages, read 2026-10-14)](https://sumodb.sumogames.de/)** — No licence stated; match results used as factual records
- **[Japan Sumo Association, hoshitori chart for the September 2026 tournament, read from the endpoint behind its results page as a spot check](https://www.sumo.or.jp/ResultData/hoshitori/1/1/)** — Copyright Nihon Sumo Kyokai; used only to verify, nothing redistributed
- **[Duggan and Levitt (2002), Winning Isn't Everything: Corruption in Sumo Wrestling, American Economic Review 92(5): the published figures the page reproduces](https://doi.org/10.1257/000282802762024665)** — Cited, not redistributed

Every figure on the page is computed from the data shipped with it. Check the page's own methods panel for how each number is derived and where it should not be pushed.

## Built with

Python, vanilla JS, SVG, gzipped base64 typed-array payload, DecompressionStream, in-page Elo and logistic fits.

## Licence

Code is MIT (see [LICENSE](LICENSE)). Data keeps the licence of its source, listed above.

---

Part of [Quick Projects](https://github.com/TNRiley/quick-projects) — one self-contained thing, built in one session. First published 2026-10-14.
