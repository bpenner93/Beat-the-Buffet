#!/usr/bin/env python3
"""Fetch real adjusted monthly prices (1990->present) for a broad stock universe from
Yahoo Finance and emit data.js for the 'time-travel draft' Market Game.

Each game card is a (company, start-year) bet held for a fixed horizon (10 years), so we
need full per-ticker monthly histories; the game computes any 10-year window on the fly."""
import json, os, time, urllib.request, urllib.error, urllib.parse
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_JS = os.path.join(HERE, "data.js")
OUT_RAW = os.path.join(HERE, "raw_history.json")

BASE_YEAR = 1990
HORIZON = 10  # years held per pick
P1 = int(datetime(BASE_YEAR, 1, 1, tzinfo=timezone.utc).timestamp())
P2 = int(datetime(2026, 7, 1, tzinfo=timezone.utc).timestamp())

# (ticker, name, sector, era-neutral descriptor). Descriptors avoid spoiling any single era.
UNIVERSE = [
    ("AAPL","Apple","Tech","Personal computers, then iPods, iPhones and Macs."),
    ("MSFT","Microsoft","Tech","Windows, Office, and enterprise software."),
    ("NVDA","Nvidia","Tech","Graphics chips for gaming, later AI."),
    ("AMD","AMD","Tech","Underdog maker of CPUs and graphics chips."),
    ("INTC","Intel","Tech","The dominant PC processor maker."),
    ("CSCO","Cisco","Tech","Networking gear that runs the internet."),
    ("ORCL","Oracle","Tech","Corporate databases and enterprise software."),
    ("IBM","IBM","Tech","Mainframes, services, and constant reinvention."),
    ("QCOM","Qualcomm","Tech","Wireless chips and patents in every phone."),
    ("TXN","Texas Instruments","Tech","Analog chips inside almost everything."),
    ("ADBE","Adobe","Tech","Creative software — Photoshop and PDF."),
    ("CRM","Salesforce","Tech","Cloud software for sales teams."),
    ("AVGO","Broadcom","Tech","Acquisitive semiconductor giant."),
    ("INTU","Intuit","Tech","TurboTax and QuickBooks."),
    ("HPQ","HP","Tech","PCs, printers, and servers."),
    ("AMZN","Amazon","Consumer","From online bookstore to everything-store and cloud."),
    ("NFLX","Netflix","Media","DVD-by-mail, then streaming."),
    ("GOOGL","Alphabet (Google)","Tech","Search and online advertising."),
    ("META","Meta (Facebook)","Tech","Social networking and digital ads."),
    ("BKNG","Booking (Priceline)","Consumer","Online travel booking."),
    ("DIS","Disney","Media","Movies, theme parks, and television."),
    ("WMT","Walmart","Retail","The biggest retailer on earth."),
    ("COST","Costco","Retail","Membership warehouse clubs."),
    ("HD","Home Depot","Retail","Home-improvement superstores."),
    ("LOW","Lowe's","Retail","The other home-improvement chain."),
    ("TGT","Target","Retail","Cheap-chic big-box retail."),
    ("NKE","Nike","Consumer","Athletic shoes and apparel."),
    ("SBUX","Starbucks","Consumer","Global coffee chain."),
    ("MCD","McDonald's","Consumer","The golden arches."),
    ("KO","Coca-Cola","Consumer","The world's soft-drink giant."),
    ("PEP","PepsiCo","Consumer","Sodas and snacks (Frito-Lay)."),
    ("PG","Procter & Gamble","Consumer","Household brands — Tide, Pampers, Gillette."),
    ("MO","Altria","Consumer","Marlboro cigarettes and fat dividends."),
    ("MNST","Monster Beverage","Consumer","Energy drinks (formerly Hansen Natural)."),
    ("DPZ","Domino's Pizza","Consumer","Pizza delivery chain."),
    ("CMG","Chipotle","Consumer","Fast-casual burritos."),
    ("GME","GameStop","Retail","Mall video-game retailer."),
    ("M","Macy's","Retail","Department stores."),
    ("JNJ","Johnson & Johnson","Health","Consumer health and pharmaceuticals."),
    ("UNH","UnitedHealth","Health","Health-insurance giant."),
    ("PFE","Pfizer","Health","Big pharma — drugs and vaccines."),
    ("MRK","Merck","Health","Pharmaceutical maker."),
    ("ABT","Abbott","Health","Medical devices and diagnostics."),
    ("AMGN","Amgen","Health","Biotech drugmaker."),
    ("GILD","Gilead Sciences","Health","Antiviral biotech."),
    ("V","Visa","Finance","Card payment network."),
    ("MA","Mastercard","Finance","Card payment network."),
    ("JPM","JPMorgan Chase","Finance","The largest US bank."),
    ("GS","Goldman Sachs","Finance","Wall Street investment bank."),
    ("AXP","American Express","Finance","Charge cards and travel services."),
    ("WFC","Wells Fargo","Finance","Big consumer bank."),
    ("C","Citigroup","Finance","Sprawling global bank."),
    ("BAC","Bank of America","Finance","Big consumer bank."),
    ("BRK-B","Berkshire Hathaway","Finance","Warren Buffett's conglomerate."),
    ("GE","General Electric","Industrial","Iconic industrial conglomerate."),
    ("BA","Boeing","Industrial","Commercial jet maker."),
    ("CAT","Caterpillar","Industrial","Construction and mining equipment."),
    ("UPS","UPS","Industrial","Package delivery."),
    ("FDX","FedEx","Industrial","Overnight shipping."),
    ("XOM","Exxon Mobil","Energy","Oil and gas supermajor."),
    ("CVX","Chevron","Energy","Oil and gas supermajor."),
    ("TSLA","Tesla","Auto","Electric vehicles."),
    ("F","Ford","Auto","Detroit automaker."),
    ("T","AT&T","Telecom","Phone and wireless carrier."),
    ("VZ","Verizon","Telecom","Wireless carrier."),
    ("BB","BlackBerry","Tech","Smartphone pioneer with the keyboard."),
]

# Market LAGGARDS — real companies that looked perfectly reasonable but trailed the index for
# long stretches. These fix survivorship bias: with the pool dominated by also-rans (as reality
# is), beating the S&P/Buffett takes genuine skill instead of being the default.
LAGGARDS = [
    # Energy (boom-and-bust; mostly lagged, brutal 2010s)
    ("SLB","Schlumberger","Energy","The biggest oilfield-services company."),
    ("HAL","Halliburton","Energy","Oilfield services and equipment."),
    ("OXY","Occidental Petroleum","Energy","Oil and gas exploration and production."),
    ("COP","ConocoPhillips","Energy","Oil and gas major."),
    ("EOG","EOG Resources","Energy","Shale oil and gas producer."),
    ("DVN","Devon Energy","Energy","Oil and gas producer."),
    ("APA","Apache","Energy","Oil and gas exploration company."),
    ("MRO","Marathon Oil","Energy","Oil and gas producer."),
    ("WMB","Williams Companies","Energy","Natural-gas pipelines."),
    ("KMI","Kinder Morgan","Energy","Energy pipelines and terminals."),
    # Utilities (steady, income-y, market-lagging)
    ("SO","Southern Company","Industrial","Southeastern electric utility."),
    ("DUK","Duke Energy","Industrial","Large electric utility."),
    ("D","Dominion Energy","Industrial","Electric and gas utility."),
    ("EXC","Exelon","Industrial","Electric utility and power generator."),
    ("AEP","American Electric Power","Industrial","Electric utility across the Midwest."),
    ("PCG","PG&E","Industrial","California electric and gas utility."),
    ("ED","Consolidated Edison","Industrial","New York's electric and gas utility."),
    ("XEL","Xcel Energy","Industrial","Midwestern electric utility."),
    ("PEG","Public Service Enterprise","Industrial","New Jersey utility holding company."),
    ("FE","FirstEnergy","Industrial","Ohio-based electric utility."),
    # Telecom (chronic underperformers)
    ("LUMN","Lumen (CenturyLink)","Telecom","Landline and fiber telecom carrier."),
    ("NOK","Nokia","Telecom","Telecom equipment; once the phone king."),
    ("ERIC","Ericsson","Telecom","Telecom-network equipment maker."),
    # Regional banks (lagged; some failed)
    ("KEY","KeyCorp","Finance","Cleveland-based regional bank."),
    ("RF","Regions Financial","Finance","Southeastern regional bank."),
    ("HBAN","Huntington Bancshares","Finance","Midwestern regional bank."),
    ("FITB","Fifth Third Bancorp","Finance","Midwestern regional bank."),
    ("CMA","Comerica","Finance","Texas and Midwest business bank."),
    ("ZION","Zions Bancorporation","Finance","Western regional bank."),
    ("MTB","M&T Bank","Finance","Northeastern regional bank."),
    ("USB","U.S. Bancorp","Finance","Large 'super-regional' bank."),
    ("PNC","PNC Financial","Finance","Large regional bank."),
    ("BK","BNY Mellon","Finance","Custody and trust bank."),
    # REITs (income, lower total return; some hammered)
    ("O","Realty Income","Finance","Monthly-dividend net-lease REIT."),
    ("SPG","Simon Property","Finance","The biggest shopping-mall landlord."),
    ("KIM","Kimco Realty","Finance","Shopping-center REIT."),
    ("BXP","Boston Properties","Finance","Premier office-building REIT."),
    ("HST","Host Hotels","Finance","Hotel-owning REIT."),
    ("VTR","Ventas","Finance","Healthcare and senior-housing REIT."),
    # Consumer staples (defensive laggards)
    ("K","Kellanova (Kellogg)","Consumer","Cereal and snack maker."),
    ("GIS","General Mills","Consumer","Cereal and packaged foods."),
    ("CAG","Conagra Brands","Consumer","Packaged-foods company."),
    ("CPB","Campbell Soup","Consumer","Soup and snacks."),
    ("KHC","Kraft Heinz","Consumer","Packaged-foods giant."),
    ("TAP","Molson Coors","Consumer","Big beer brewer."),
    ("KMB","Kimberly-Clark","Consumer","Kleenex, Huggies, paper goods."),
    ("CL","Colgate-Palmolive","Consumer","Toothpaste and household products."),
    ("HRL","Hormel Foods","Consumer","Spam and packaged meats."),
    # Retail strugglers
    ("KSS","Kohl's","Retail","Mid-tier department store."),
    ("JWN","Nordstrom","Retail","Upscale department store."),
    ("GPS","Gap","Retail","Mall apparel chain."),
    ("ANF","Abercrombie & Fitch","Retail","Teen apparel retailer."),
    ("HBI","Hanesbrands","Consumer","Underwear and basic apparel."),
    ("VFC","VF Corporation","Consumer","Apparel holding co (Vans, North Face)."),
    ("WBA","Walgreens","Retail","Drugstore chain."),
    ("CVS","CVS Health","Retail","Drugstore chain and pharmacy-benefits."),
    # Pharma / health also-rans
    ("BMY","Bristol Myers Squibb","Health","Big pharmaceutical maker."),
    ("BIIB","Biogen","Health","Neuroscience-focused biotech."),
    ("TEVA","Teva Pharmaceutical","Health","The largest generic-drug maker."),
    ("CAH","Cardinal Health","Health","Drug-distribution middleman."),
    ("BAX","Baxter International","Health","Hospital products and IV systems."),
    ("BHC","Bausch Health (Valeant)","Health","Acquisitive specialty-pharma company."),
    # Industrials / materials
    ("MMM","3M","Industrial","Post-its, tape, and industrial products."),
    ("EMR","Emerson Electric","Industrial","Industrial automation and tools."),
    ("DOW","Dow","Industrial","Commodity chemicals."),
    ("IP","International Paper","Industrial","Paper and packaging."),
    ("MOS","Mosaic","Industrial","Fertilizer (potash and phosphate)."),
    ("FCX","Freeport-McMoRan","Industrial","Copper and gold miner."),
    ("AA","Alcoa","Industrial","Aluminum producer."),
    ("X","U.S. Steel","Industrial","Integrated steelmaker."),
    ("CLF","Cleveland-Cliffs","Industrial","Iron ore and steel."),
    ("NEM","Newmont","Industrial","The largest gold miner."),
    # Autos / airlines / cruise (capital-hungry, cyclical)
    ("GM","General Motors","Auto","Detroit automaker (post-2010 IPO)."),
    ("AAL","American Airlines","Industrial","The largest US airline."),
    ("UAL","United Airlines","Industrial","Major US airline."),
    ("DAL","Delta Air Lines","Industrial","Major US airline."),
    ("LUV","Southwest Airlines","Industrial","Low-cost US airline."),
    ("CCL","Carnival","Consumer","The biggest cruise-line operator."),
    ("RCL","Royal Caribbean","Consumer","Cruise-line operator."),
    # Tech has-beens
    ("HPE","Hewlett Packard Enterprise","Tech","Enterprise servers and services."),
    ("WDC","Western Digital","Tech","Hard drives and flash storage."),
    ("STX","Seagate","Tech","Hard-disk-drive maker."),
    ("NTAP","NetApp","Tech","Enterprise data storage."),
    ("JNPR","Juniper Networks","Tech","Networking gear (Cisco's rival)."),
    ("GLW","Corning","Tech","Specialty glass for screens and fiber."),
    # Insurance / finance
    ("AIG","AIG","Finance","Global insurance giant."),
    ("MET","MetLife","Finance","Life insurer."),
    ("PRU","Prudential Financial","Finance","Life insurance and retirement."),
    ("ALL","Allstate","Finance","Auto and home insurer."),
    ("HIG","The Hartford","Finance","Property-casualty insurer."),
    ("LNC","Lincoln National","Finance","Life insurance and annuities."),
    ("COF","Capital One","Finance","Credit cards and consumer banking."),
    ("DFS","Discover Financial","Finance","Credit cards and consumer loans."),
]

# Curated busts — companies that wiped out. They delisted, so Yahoo has no clean history;
# we synthesize a stylized "flat, then collapse to ~total loss" path. The ~-99% outcome is
# the honest part; the interim path is illustrative (it never fabricates gains). Draftable
# years are restricted to those whose 10-year hold contains the collapse, so they're real traps.
BUSTS = [
    ("LEH","Lehman Brothers","Finance","A storied 150-year-old Wall Street investment bank.",1994,2008),
    ("ENE","Enron","Energy","Award-winning, high-flying energy-trading giant.",1990,2001),
    ("WCOM","WorldCom","Telecom","Telecom roll-up; the #2 US long-distance carrier.",1992,2002),
    ("NT","Nortel Networks","Tech","Telecom-equipment titan and dot-com darling.",1990,2009),
    ("WM","Washington Mutual","Finance","The largest savings-and-loan in America.",1991,2008),
    ("BSC","Bear Stearns","Finance","Aggressive, highly profitable Wall Street bank.",1990,2008),
    ("SHLD","Sears","Retail","Once the everything-store of America.",1992,2018),
    ("BBI","Blockbuster","Media","The video-rental superpower on every corner.",1999,2010),
    ("EK","Eastman Kodak","Consumer","The name in film, cameras, and photo paper.",1990,2012),
    ("CC","Circuit City","Retail","The big-box consumer-electronics chain.",1990,2009),
    ("JCP","J.C. Penney","Retail","The mid-market department-store anchor.",1990,2020),
    ("BBBY","Bed Bath & Beyond","Retail","The big-box home-goods chain with the coupons.",1992,2023),
]

def synth_bust(first, bust):
    start_idx = (first - BASE_YEAR) * 12
    end_idx = (2026 - BASE_YEAR) * 12 + 6
    bust_local = (bust - BASE_YEAR) * 12 - start_idx
    crash_start = bust_local - 18  # collapse over the final ~18 months
    prices = []
    for i in range(end_idx - start_idx + 1):
        if i < crash_start:
            p = 100.0
        elif i <= bust_local:
            t = (i - crash_start) / max(1, bust_local - crash_start)
            p = 100.0 * (1 - t) + 1.0 * t  # 100 -> ~1 (a near-total loss)
        else:
            p = 1.0
        prices.append(round(p, 3))
    return start_idx, prices

def fetch(ticker):
    q = urllib.parse.quote(ticker, safe="")
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{q}"
           f"?period1={P1}&period2={P2}&interval=1mo")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=25) as r:
                return json.load(r)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
            print(f"  retry {ticker} ({attempt+1}): {e}")
            time.sleep(1.5 * (attempt + 1))
    return None

def idx_of(ts):
    d = datetime.fromtimestamp(ts, tz=timezone.utc)
    return (d.year - BASE_YEAR) * 12 + (d.month - 1)

def to_dense(data):
    """Return (startIdx, [prices...]) dense monthly adjclose, forward-filling interior gaps."""
    res = data["chart"]["result"][0]
    ts = res["timestamp"]
    adj = res["indicators"]["adjclose"][0]["adjclose"]
    by_idx = {}
    for t, a in zip(ts, adj):
        if a is None:
            continue
        i = idx_of(t)
        if i >= 0:
            by_idx[i] = float(a)
    if not by_idx:
        return None, None
    lo, hi = min(by_idx), max(by_idx)
    prices, last = [], None
    for i in range(lo, hi + 1):
        if i in by_idx:
            last = by_idx[i]
        prices.append(round(last, 3))
    return lo, prices

stocks = []
for ticker, name, sector, desc in UNIVERSE + LAGGARDS:
    print(f"Fetching {ticker} ...")
    data = fetch(ticker)
    try:
        start_idx, prices = to_dense(data)
    except (TypeError, KeyError, IndexError):
        start_idx = None
    if start_idx is None or len(prices) < (HORIZON * 12 + 12):
        print(f"  !! insufficient data for {ticker}, skipping")
        continue
    first_year = BASE_YEAR + (start_idx // 12)
    last_year = BASE_YEAR + ((start_idx + len(prices) - 1) // 12)
    latest_start = last_year - HORIZON
    stocks.append({
        "ticker": ticker, "name": name, "sector": sector, "desc": desc,
        "startIdx": start_idx, "prices": prices,
        "firstYear": first_year, "latestStart": latest_start,
    })
    print(f"  ok  {ticker}: {first_year}-{last_year}  (draftable {first_year}-{latest_start})")

print("\nAdding curated busts (synthetic ~total-loss paths)...")
for ticker, name, sector, desc, first, bust in BUSTS:
    start_idx, prices = synth_bust(first, bust)
    years = list(range(max(first, bust - 10), min(2016, bust - 2) + 1))
    if not years:
        continue
    stocks.append({
        "ticker": ticker, "name": name, "sector": sector, "desc": desc,
        "startIdx": start_idx, "prices": prices,
        "firstYear": years[0], "latestStart": years[-1],
        "bust": True, "synthetic": True, "years": years,
    })
    print(f"  + {ticker} ({name}) bust {bust}, draftable {years[0]}-{years[-1]}")

# Benchmark: S&P 500 Total Return index (^SP500TR), with graceful fallbacks.
bench = None
for sym in ("^SP500TR", "^GSPC", "SPY"):
    print(f"Fetching benchmark {sym} ...")
    d = fetch(sym)
    try:
        si, bp = to_dense(d)
        if si is not None and len(bp) > HORIZON * 12:
            bench = {"symbol": sym, "startIdx": si, "prices": bp}
            print(f"  ok benchmark {sym}: {len(bp)} months from idx {si}")
            break
    except Exception as e:
        print("  failed:", e)

# Buffett benchmark = Berkshire Hathaway (BRK-B), reused from the fetched universe.
brk = next((s for s in stocks if s["ticker"] == "BRK-B"), None)
buffett = {"startIdx": brk["startIdx"], "prices": brk["prices"]} if brk else None

payload = {
    "baseYear": BASE_YEAR,
    "horizonYears": HORIZON,
    "benchmark": bench,
    "buffett": buffett,
    "stocks": stocks,
}

with open(OUT_RAW, "w") as f:
    json.dump(payload, f)
with open(OUT_JS, "w", encoding="utf-8") as f:
    f.write("// Auto-generated by build_data.py — real Yahoo Finance adjusted monthly closes, 1990-2026.\n")
    f.write("window.MARKET_DATA = ")
    json.dump(payload, f, ensure_ascii=False)
    f.write(";\n")

print(f"\n{len(stocks)} stocks. Benchmark: {bench['symbol'] if bench else 'NONE'}.")
print(f"Wrote {OUT_JS}")
