# OpenBB Platform - Quick Start Guide for Canadian REIT Analysis

**Purpose:** Quick reference for using OpenBB Platform to retrieve Canadian REIT data

---

## Installation

```bash
# Install OpenBB Platform and TMX extension
pip install openbb openbb-tmx
```

**First run:** OpenBB will automatically install required extensions (~30 seconds)

---

## Basic Usage

### Get Dividend History

```python
from openbb import obb

# Retrieve dividend history for RioCan REIT
result = obb.equity.fundamental.dividends(
    symbol='REI-UN.TO',
    provider='tmx'
)

# Convert to pandas DataFrame
df = result.to_df()
print(df.head())
```

**Output:**
```
  ex_dividend_date  amount currency record_date payment_date
0       2009-02-25   0.115      CAD  2009-02-27   2009-03-06
1       2009-03-27   0.115      CAD  2009-03-31   2009-04-07
```

### Get Current Price

```python
from openbb import obb
from datetime import datetime, timedelta

# Get last 7 days of price data
result = obb.equity.price.historical(
    symbol='REI-UN.TO',
    start_date=(datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
    provider='tmx'
)

df = result.to_df()
current_price = df['close'].iloc[-1]

print(f"Current price: ${current_price:.2f}")
```

### Calculate Dividend Yield

```python
from openbb import obb
import pandas as pd
from datetime import datetime, timedelta

ticker = 'REI-UN.TO'

# Get TTM dividends
div_result = obb.equity.fundamental.dividends(symbol=ticker, provider='tmx')
div_df = div_result.to_df()
div_df['ex_dividend_date'] = pd.to_datetime(div_df['ex_dividend_date'])

cutoff = datetime.now() - timedelta(days=365)
ttm_divs = div_df[div_df['ex_dividend_date'] >= cutoff]
annual_dividend = ttm_divs['amount'].sum()

# Get current price
price_result = obb.equity.price.historical(symbol=ticker, provider='tmx')
price_df = price_result.to_df()
current_price = price_df['close'].iloc[-1]

# Calculate yield
dividend_yield = (annual_dividend / current_price) * 100

print(f"TTM Dividend: ${annual_dividend:.3f}")
print(f"Current Price: ${current_price:.2f}")
print(f"Dividend Yield: {dividend_yield:.2f}%")
```

**Output:**
```
TTM Dividend: $1.239
Current Price: $18.97
Dividend Yield: 6.53%
```

---

## Canadian REIT Tickers

| REIT Name | TSX Ticker | Yahoo/OpenBB Ticker | Status |
|-----------|------------|---------------------|--------|
| RioCan REIT | REI.UN | **REI-UN.TO** | ✓ Tested |
| Dream Industrial REIT | DIR.UN | **DIR-UN.TO** | ✓ Tested |
| Artis REIT | AX.UN | **AX-UN.TO** | ✓ Tested |
| H&R REIT | HR.UN | **HR-UN.TO** | Expected to work |
| SmartCentres REIT | SRU.UN | **SRU-UN.TO** | Expected to work |
| Allied Properties REIT | AP.UN | **AP-UN.TO** | Expected to work |

**Format:** Use `SYMBOL-UN.TO` for best compatibility with both TMX and YFinance providers

---

## Providers Comparison

### TMX Provider (Recommended for Canadian REITs)

**Pros:**
- ✅ Native Canadian data source
- ✅ Rich metadata (6 fields)
- ✅ Free, no API key required
- ✅ Includes payment_date, declaration_date, record_date

**Cons:**
- ⚠️ History only from 2009+ for most REITs

**Use when:** You need detailed dividend information with all key dates

### YFinance Provider

**Pros:**
- ✅ Free, no API key required
- ✅ Longer history (1996+ for some REITs)
- ✅ Works with OpenBB standardized API

**Cons:**
- ⚠️ Limited metadata (only ex-date and amount)
- ⚠️ Some ticker format sensitivity

**Use when:** You need extended historical data (pre-2009)

---

## Common Tasks

### Export to CSV

```python
from openbb import obb

result = obb.equity.fundamental.dividends(symbol='REI-UN.TO', provider='tmx')
df = result.to_df()

df.to_csv('riocan_dividends.csv', index=False)
print(f"Exported {len(df)} records")
```

### Calculate Annual Dividends

```python
from openbb import obb
import pandas as pd

result = obb.equity.fundamental.dividends(symbol='REI-UN.TO', provider='tmx')
df = result.to_df()

df['year'] = pd.to_datetime(df['ex_dividend_date']).dt.year
annual_divs = df.groupby('year')['amount'].sum()

print(annual_divs[annual_divs.index >= 2015])
```

**Output:**
```
year
2015    1.4100
2016    1.4100
2017    1.4100
2018    1.4400
2019    1.4400
2020    1.4400
2021    0.8800  # COVID dividend cut
2022    1.0150
2023    1.0750
2024    1.1075
```

### Compare Multiple REITs

```python
from openbb import obb
from datetime import datetime, timedelta

reits = [
    ('REI-UN.TO', 'RioCan'),
    ('DIR-UN.TO', 'Dream Industrial'),
    ('AX-UN.TO', 'Artis')
]

for ticker, name in reits:
    # Get TTM dividends
    div_result = obb.equity.fundamental.dividends(symbol=ticker, provider='tmx')
    div_df = div_result.to_df()
    div_df['ex_dividend_date'] = pd.to_datetime(div_df['ex_dividend_date'])

    cutoff = datetime.now() - timedelta(days=365)
    ttm_divs = div_df[div_df['ex_dividend_date'] >= cutoff]
    annual_dividend = ttm_divs['amount'].sum()

    # Get price
    price_result = obb.equity.price.historical(symbol=ticker, provider='tmx')
    price_df = price_result.to_df()
    current_price = price_df['close'].iloc[-1]

    # Calculate yield
    dividend_yield = (annual_dividend / current_price) * 100

    print(f"{name:20} ${current_price:6.2f}  Yield: {dividend_yield:5.2f}%")
```

**Output:**
```
RioCan               $ 18.97  Yield:  6.53%
Dream Industrial     $ 12.33  Yield:  5.68%
Artis                $  6.02  Yield: 10.80%
```

---

## Limitations

**What OpenBB CAN do (free tier):**
- ✅ Historical dividend data (2009-2025 via TMX)
- ✅ Current and historical prices
- ✅ Trading volume data
- ✅ Basic company information

**What OpenBB CANNOT do (free tier):**
- ❌ Quarterly financial statements (balance sheet, cash flow, income)
- ❌ REIT-specific metrics (FFO, AFFO, ACFO, NAV)
- ❌ Fundamental ratios (debt/equity, payout ratios)
- ❌ Real-time intraday data (historical intraday from Apr 2022+ only)

**Workaround:** Continue using Phase 1-2 PDF extraction for financial statements and REIT metrics

---

## Error Troubleshooting

### "possibly delisted; no price data found"

**Cause:** Wrong ticker format for YFinance provider

**Solution:** Use `REI-UN.TO` format (with hyphen and .TO), not `REI.UN`

### "Missing credential 'fmp_api_key'"

**Cause:** Trying to use a paid provider (FMP, Intrinio) without API key

**Solution:** Use free providers: `provider='tmx'` or `provider='yfinance'`

### "No dividend data found"

**Cause:**
1. Ticker format incorrect for the provider
2. REIT may not have dividend history in database

**Solution:**
- For TMX: Use `REI.UN` or `REI-UN.TO`
- For YFinance: Use `REI-UN.TO` (must have hyphen)

---

## Next Steps

1. **Read full research report:** `/workspaces/issuer-credit-analysis/docs/OPENBB_CANADIAN_REIT_RESEARCH_REPORT.md`
2. **Review code examples:** `/workspaces/issuer-credit-analysis/tests/openbb_canadian_reit_examples.py`
3. **Test with your REIT:** Run tests in `/workspaces/issuer-credit-analysis/tests/`
4. **Integrate into pipeline:** See recommended Phase 2.5 implementation in research report

---

**Version:** 1.0
**Last Updated:** 2025-10-21
**For Questions:** See full research report in `docs/OPENBB_CANADIAN_REIT_RESEARCH_REPORT.md`
