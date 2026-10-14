# Rebuilding The Eighth Win

Enough for someone with a shell, Python 3 and Node (optional, for checking) to rebuild this
page from nothing.

## 1. What it is

A single self-contained `index.html` that reruns Duggan and Levitt's sumo match-fixing test
("Winning Isn't Everything", AER 2002) on every Makuuchi and Juryo bout from March 1958 to
September 2026. Then it asks the question the paper could not: did the 2011 match-fixing
scandal, which cancelled a tournament and expelled 23 wrestlers, change the final day?

**The finding:** no. From March 2000 to January 2011, a wrestler on seven wins going into day 15
beat an opponent not on seven wins 62.0% of the time, against 49.9% expected (+12.2 points).
From May 2011 to November 2018 the figures are 61.0% against 49.1% (+11.9). The change is
−0.4 points, 95% interval −7.3 to +6.6. The model-free second measure agrees: the 8-7 share
minus the 7-8 share is +5.2 before and +4.7 after (change −0.5, interval −3.2 to +2.3).

Every statistic is computed in the page from the shipped columns, Elo ratings included.

## 2. Data sources

| source | what | how |
|---|---|---|
| sumo-api.com | `GET https://www.sumo-api.com/api/basho/<YYYYMM>/banzuke/<Makuuchi\|Juryo>` | 826 requests (413 basho × 2 divisions), months 01/03/05/07/09/11, 1958-01 to 2026-09. About 0.5 to 1 MB each. `src/fetch_banzuke.py`, about 30 minutes at a 0.4 s gap. |
| SumoDB | `https://sumodb.sumogames.de/Results.aspx?b=<YYYYMM>&d=15` | 413 pages of 125 to 290 kB, saved gzipped. `src/fetch_sumodb.py`; run a second copy with `--reverse` to halve the time. Old pages are slow (about 10 s each). |
| Japan Sumo Association | `POST https://www.sumo.or.jp/ResultData/hoshitoriAjax/<1\|2>/<1\|2>/` | Current tournament only. `src/fetch_jsa.py`. |

Quirks that will bite:

- **sumo-api returns an empty body for cancelled tournaments** (`{"bashoId":""}`): 1958-01 (not
  covered), 2011-03 (cancelled after the scandal), 2020-05 (cancelled for COVID). SumoDB does
  have 1958-01.
- **sumo-api has blank days** (`"result": ""`). Whole days are missing for everyone in 1965-03
  (day 7), 1965-05 (day 6) and 1978-11 (day 5), and a few individuals elsewhere: 267
  wrestler-tournaments in all. Their morning records are unknown, so they are excluded, not
  guessed. SumoDB has these days, and agrees with sumo-api everywhere else.
- **84 sumo-api entries have no `record` at all** (totals only), and four records are shorter
  than 15 days. Both are dropped.
- **Juryo wrestlers fight visiting Makushita wrestlers** who are not in either banzuke file. 4,982
  such bouts count in the Juryo man's record but cannot be rated, so they are not shipped as
  bouts.
- **Fusen (default) results** are `fusen win` / `fusen loss`. They count toward the record, as on
  the banzuke, but are excluded from every win-rate measure and from Elo learning.
- **SumoDB's Yusho Arasoi block** lists every top-two-division wrestler as a 15-character string
  of ○ ● □ ■ and – (win, loss, default win, default loss, absent), followed by a rank code like
  `M13e` or `Y2wHD` (HD = haridashi). Matching the two sites by rank slot fails 15 times, where
  they slot the same man differently; fall back to the ring name.
- **The JSA endpoint answers 403** unless the request carries a cookie the results page sets in
  inline script, `document.cookie = "<name>=<value>; path=/ResultData ..."`. The name and value
  change between loads ("game=cat" on the hoshitori page, "mischeief=OK" on the torikumi page).
  Read the page, regex the cookie out, replay it.
- **The two main sources probably share an upstream.** sumo-api.com's about page names SumoDB as
  the resource it improves on. Treat their agreement as a parse check, not two witnesses.

## 3. Processing, and why

- **On the margin** (paper's definition): wins so far < 8 and wins + bouts remaining including
  today ≥ 8. Day 15 means exactly seven wins. Absences count as losses.
- **Measure A**: day-15 bouts with exactly one wrestler on the margin, no default, neither entry
  with a blank day. Actual minus expected wins for the margin side.
- **Expected** = sequential Elo over all shipped bouts in (basho, day) order, everyone starting
  at 1500, **K = 10** (chosen by log-loss on ordinary bouts before any control existed: K 6, 10,
  16, 24 gave 0.6658, 0.6640, 0.6647, 0.6681). **Bouts under test (days 11 to 15, exactly one on
  the margin) are predicted but never learned from**; otherwise a thrown bout inflates the
  rating that judges the rematch.
- **Measure B** (SumoDB only, no model): among wrestlers with no absences and 15 decided bouts,
  share finishing 8-7 minus share finishing 7-8.
- **Periods**: 1958-01 to 1988-11; 1989-01 to 2000-01 (the paper); 2000-03 to 2011-01; 2011-05 to
  2018-11; 2019-01 to 2026-09. The headline compares the third and fourth. It stops at 2018-11
  because from 2019 the final-day schedule pairs about 61% of 7-7 wrestlers with each other (33%
  in 2008 to 2018). That halves measure A's sample and mechanically pulls measure B towards zero.
- **Payload**: 14 columns, each a little-endian typed array, gzipped (mtime 0), base64. Decoded
  in the page with `DecompressionStream("gzip")`. 783 kB page.

## 4. The page

Banzuke-sheet identity: washi ground, sumi ink, Shippori Mincho B1 headings, IBM Plex Sans and
Mono. **Vermilion means only "needs the eighth win"**; indigo is the model's expectation; greys
are everything else. Light and dark themes.

Sections: hero (a 7-7 hoshi row with a dashed day-15 mark, the computed finding, four number
tiles); a two-panel history (A over B, 1, 3 or 5-year bins, with event lines at 2000, 2011 and
2019 and the paper's years shaded); before and after the purge (two cards, each with a computed
verdict); four controls with live verdicts; a K slider that reruns everything; the schedule
chart; the payback test with period chips; the instrument table; methods.

**Performance trap:** reading `getComputedStyle` inside drawing loops while appending SVG nodes
forces a full restyle per call, and froze the renderer for tens of seconds. Colours are cached
once per draw (`PAL`). The whole computation then takes about 170 ms.

## 5. Expected values (K = 10)

| check | value |
|---|---|
| bouts shipped / basho with data | 197,779 / 410 |
| SumoDB rows matched / identical | 27,642 / 27,378 (263 differ only at sumo-api blank days, 0 truly different) |
| JSA 2026-09 spot check | 1,000 of 1,000 bouts identical |
| Paper, day 15 raw excess (published .244) | .253, n = 534 |
| Paper, days 14 / 13 / 12 / 11 (published .150 / .096 / .038 / .000) | .148 / .097 / .048 / −.041 |
| Paper, share on 8 / 7 / 9 / 6 wins (published 26.0 / 12.2 / 16.2 / 13.9%) | 25.3 / 12.0 / 15.9 / 13.7%, n = 4,131 |
| Paper, margin wrestler's next meeting (published −.073) | −.073, n = 1,829 |
| 7-7 day-15 excess by period | +21.1, +25.6, +12.2, +11.9, +8.0 points |
| Same, rank model instead of Elo | +20.6, +25.4, +12.0, +11.0, +5.5 |
| 6-8 / 8-6 placebo, largest absolute | 2.7 points (8-6, 1958–1988) |
| Calibration, favourite in late non-margin bouts | −0.9, **−3.6**, −0.3, −0.6, −1.2 points |
| Headline windows | 62.0% vs 49.9% (n 466); 61.0% vs 49.1% (n 328) |
| Measure B, headline windows | 19.6 − 14.4 = +5.2; 19.3 − 14.5 = +4.7 |
| 2019–2026 | 56% of 178 vs 48% expected (+8.0, interval +0.8 to +15.2); B +1.4 |
| A against B across 23 three-year bins | r = 0.97 |
| Sharpest fall | 1997–99 +20.8 (n 155) → 2000–02 +8.0 (n 123), measure A |

## 6. Controls, and what they showed

1. **Reproduce the paper first.** All ten published figures within two combined standard errors.
   *Wrong answer recorded:* the first version used a flat ±.040 tolerance, and day 11 (−.041 vs
   .000) missed it by .001, which withdrew the headline. The flat number had no basis; the paper
   publishes standard errors, so the tolerance was changed to use them, and the page says so.
2. **6-8 and 8-6 on day 15** (nothing at stake, same model): never more than 4 points. Pass.
3. **Rank-only expectation**, fitted per period: within 4 points of Elo everywhere. Pass.
4. **Calibration on late non-margin bouts**: within 3 points except 1989–2000 (−3.6). The gate is
   applied per period. The headline periods pass, and 1989–2000 is flagged on the page.
   For K 4 to 8 everything passes. From K 18 up, control 4 fails in the headline periods and the
   page withdraws its own headline, although the comparison moves by under a point.

## 7. The failed half

**The payback test does not isolate the bubble.** The paper's argument against "they just try
harder" was that the 7-7 winner loses the rematch more often. That reproduces exactly (−.073).
But in 1958–1988, winners of ordinary late bouts with nobody on the margin also underperform in
the rematch (−6.0 points against Elo), while winners of day 1–5 bouts do not (+1.2). It is not an
Elo overshoot either: in the Python exploration (1963 to about 1995), moving K from 6 to 24
only moved the late reversal from −4.9 to −6.6. So in the old
record the rematch cannot tell a repaid favour on the margin from whatever else the end of a
tournament does. After 2011 nobody's rematch reverses (+1.9 for the 7-7 winners, +1.4 for
ordinary late bouts), so the remaining excess carries no trading signature. It could be effort.
The data cannot say.

## 8. What the page must say about itself

It accuses no one; an excess is a pattern across hundreds of bouts. The post-2011 excess is not
shown to be corruption. The purge may have changed who, how or when, just not how often the 7-7
man won on day 15. Lower divisions are out of scope (seven bouts, and schedules already pair
equal records). Post-2019 samples are small.
