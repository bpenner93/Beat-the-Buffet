# Beat the Buffett

A stock-picking game inspired by [20-0.com](https://www.20-0.com) (the NFL "perfect season"
roster builder), reimagined for everyday investors.

**The pitch:** each round drops you into a real year and shows you the companies you could have
bought then. Pick one, hold it ten years — and find out whether it **beat Warren Buffett** over
that decade. Each year is a **win or a loss**. Beat him most years to win; beat him *every* year
for a perfect game. Some companies on the board went on to make fortunes; most quietly trailed the
market, and a few went to zero.

## Play it

Open `index.html` in any browser (double-click it). No install, no server needed. Scores save in
your browser.

## How it works

| File | What it is |
|------|-----------|
| `index.html` | The whole game — difficulty selector, year-by-year draft, the 10-year fast-forward, the win–loss scoring, and leaderboard. Self-contained. |
| `data.js` | **159 companies:** ~67 winners, ~80 market laggards, and 12 busts. Real split/dividend-adjusted monthly closes (1990–2026) for everything that still trades; benchmarks are the S&P 500 Total Return index and Berkshire Hathaway. Auto-generated. |
| `build_data.py` | Fetches the data from Yahoo Finance (no API key) and regenerates `data.js`. |

Each **round** is a real year. The game picks a year, shows you ~8 companies that were public then
(a `(company, year)` card each), and you keep one to "hold" for ten years. It knows each company's
full price history, so it computes that bet's ten-year return — and the benchmark's — on the fly.
Future returns are never shown while you pick.

## The hard part: you're scored on a win–loss *record*

The first versions were too easy to beat the market — and measuring it showed exactly why:

- **One lucky moonshot carried everything.** When you score a *basket total*, a single Nvidia or
  Monster (a $2k slice becoming $40k+) drags four dud picks past the benchmark. A random basket
  beat Buffett's total **~63%** of the time.
- **Fix: each year is its own head-to-head.** Your pick either beat the benchmark over its decade
  or it didn't — a win or a loss. A moonshot only wins *its own* year; it can't rescue the others.

That single change makes a *random* player lose more than they win:

| Mode | A random player's winning-record rate | Perfect 5-0 |
|------|----------------------------------------|-------------|
| 🟢 Easy   | 44% | ~2% |
| 🟠 Hard   | **38%** | ~2% |
| 🔴 Brutal | **20%** (shut out 0-5 in ~14% of games) | <1% |

Note: you can *make money* and still lose every year — beating the market is a different thing
from getting richer, which is exactly the lesson.

### Difficulty

You get a generous slate to choose from (the hardness is in the record, not in limiting choice):

| Mode | Companies/year | Re-deals | Each year you must beat… |
|------|----------------|----------|--------------------------|
| 🟢 Easy   | 8 | 2 | Buffett |
| 🔵 Normal | 8 | 1 | Buffett |
| 🟠 Hard   | 8 | 1 | the tougher of Buffett and the S&P 500 |
| 🔴 Brutal | 8 | 0 | the tougher of Buffett & the S&P, **by 25%** |

## Scoring

- **Your record** (e.g. *3–2 vs Buffett*) is the headline. Winning record = you beat the Oracle.
  Going undefeated = a **Perfect Game** (the true 20-0 "perfect season").
- **Grade S–F** by win rate; badges for the perfect game, 10-/50-baggers, and stepping on a
  landmine.
- **Money** is shown too — what your $10k became — as a secondary "where it landed."
- **Leaderboard:** local (`localStorage`), ranked by record (weighted by difficulty), then money.
  No accounts, no server.
- Fun fact the game surfaces: Berkshire *trailed* the S&P over 2010s windows — so on Hard+ the bar
  is the tougher of the two.

### Regenerate or extend the data

```
python build_data.py
```

Edit `UNIVERSE` (winners), `LAGGARDS` (also-rans), or `BUSTS` (wipeouts) in `build_data.py`; change
`HORIZON` for a different hold length or `BASE_YEAR`/`P1` to reach further back. Re-run to rebuild
`data.js`.

## Ideas for next

- "Pick 2 of 6" rounds, or a sector-themed variant
- Selectable hold length (3 / 5 / 10 years)
- Shareable result cards, and an online global leaderboard

This is a historical game, not investment advice. Past performance ≠ future results.
