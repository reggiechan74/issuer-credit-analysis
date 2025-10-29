# OpenBB Platform Research - Executive Summary

**Date:** 2025-10-21  
**Research Question:** Can OpenBB API retrieve Canadian REIT dividend and financial data?  
**Verdict:** ✅ **YES for dividends, NO for financial statements (free tier)**

---

## Key Findings (TL;DR)

### What Works ✅

1. **Dividend History** - Excellent coverage via TMX and YFinance providers
   - RioCan REIT: 200 records (2009-2025) via TMX, 379 records (1996-2025) via YFinance
   - Dream Industrial: 156 records (2012-2025)
   - Artis REIT: 200 records (2009-2025) via TMX, 234 records (2006-2025) via YFinance
   - **Sufficient for 2015-2025 analysis requirements**

2. **Price Data** - Complete historical and current prices
   - Daily OHLC data available
   - Trading volume included
   - VWAP data from TMX provider
   - Current market prices for yield calculations

3. **No API Key Required** - Free tier sufficient for dividend analysis
   - TMX provider: Free, unlimited requests
   - YFinance provider: Free, unlimited requests
   - No rate limits on free tier

### What Doesn't Work ❌

1. **Financial Statements** - Quarterly cash flow, balance sheet, income statements
   - Requires paid providers (FMP, Intrinio, Polygon)
   - TMX and YFinance do not support financial statements
   - **Continue using Phase 1-2 PDF extraction for this**

2. **REIT-Specific Metrics** - FFO, AFFO, ACFO, NAV per share
   - Not available from any provider
   - **Continue calculating in Phase 3 from extracted financial data**

3. **Fundamental Ratios** - Debt/equity, payout ratios, interest coverage
   - Requires financial statements (see above)
   - **Continue using Phase 3 calculations**

---

## Recommendation: Hybrid Approach

**Use OpenBB for:** Dividend validation and peer comparison (Phase 2.5 - NEW)  
**Keep PDF extraction for:** Financial statements and REIT metrics (Phases 1-3)

```
Current Pipeline:
  Phase 1: PDF → Markdown
  Phase 2: Markdown → JSON
  Phase 3: Calculate Metrics
  Phase 4: Credit Analysis
  Phase 5: Generate Report

Enhanced Pipeline (RECOMMENDED):
  Phase 1: PDF → Markdown
  Phase 2: Markdown → JSON
  Phase 2.5 (NEW): Market Data Enrichment ← OpenBB goes here
    • Retrieve dividend history from TMX
    • Get current market price
    • Calculate market dividend yield
    • Compare with 3-4 peer REITs
    • Validate distributions vs market data
  Phase 3: Calculate Metrics (use Phase 2 + Phase 2.5 data)
  Phase 4: Credit Analysis (enhanced with peer comparisons)
  Phase 5: Generate Report (include dividend charts, peer tables)
```

---

## Test Results

### Dividend Data Access ✅

| REIT | Ticker | TMX Records | YFinance Records | Status |
|------|--------|-------------|------------------|--------|
| RioCan REIT | REI-UN.TO | 200 (2009-2025) | 379 (1996-2025) | ✓ Working |
| Dream Industrial | DIR-UN.TO | 156 (2012-2025) | 156 (2012-2025) | ✓ Working |
| Artis REIT | AX-UN.TO | 200 (2009-2025) | 234 (2006-2025) | ✓ Working |

**Data Fields Available (TMX):**
- ex_dividend_date, amount, currency, record_date, payment_date, declaration_date

**Data Fields Available (YFinance):**
- ex_dividend_date, amount

### Price Data Access ✅

**TMX Provider Fields:**
- open, high, low, close, volume, vwap, change, change_percent, transactions

**YFinance Provider Fields:**
- open, high, low, close, volume, dividend

**Test Result:** Retrieved 62 days of price data for RioCan REIT successfully

### Financial Statements ❌

**Test Result:** Not available via free providers (TMX, YFinance)
- Requires paid providers: FMP ($14.99/mo), Intrinio ($50+/mo), Polygon ($29+/mo)
- **Recommendation:** Continue using PDF extraction (working well)

---

## Code Examples

### Example 1: Get Dividend History

```python
from openbb import obb

result = obb.equity.fundamental.dividends(
    symbol='REI-UN.TO',
    provider='tmx'
)

df = result.to_df()
print(f"Retrieved {len(df)} dividend records")
# Output: Retrieved 200 dividend records
```

### Example 2: Calculate Dividend Yield

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
current_price = price_result.to_df()['close'].iloc[-1]

# Calculate yield
dividend_yield = (annual_dividend / current_price) * 100

print(f"RioCan REIT: ${current_price:.2f}, Yield: {dividend_yield:.2f}%")
# Output: RioCan REIT: $18.97, Yield: 6.53%
```

### Example 3: Multi-REIT Comparison

```python
reits = [
    ('REI-UN.TO', 'RioCan REIT'),
    ('DIR-UN.TO', 'Dream Industrial REIT'),
    ('AX-UN.TO', 'Artis REIT')
]

for ticker, name in reits:
    # ... (same code as Example 2)
    print(f"{name}: ${current_price:.2f}, Yield: {dividend_yield:.2f}%")

# Output:
# RioCan REIT: $18.97, Yield: 6.53%
# Dream Industrial REIT: $12.33, Yield: 5.68%
# Artis REIT: $6.02, Yield: 10.80%
```

---

## Deliverables

1. **Comprehensive Research Report** (13,500 words)
   - Location: `/workspaces/issuer-credit-analysis/docs/OPENBB_CANADIAN_REIT_RESEARCH_REPORT.md`
   - Covers: Capabilities, limitations, code examples, recommendations, implementation guide

2. **Quick Start Guide**
   - Location: `/workspaces/issuer-credit-analysis/docs/OPENBB_QUICK_START.md`
   - Quick reference for common tasks and troubleshooting

3. **Test Code** (3 files)
   - `tests/test_openbb_canadian_reits.py` - Comprehensive capability tests
   - `tests/test_openbb_ticker_formats.py` - Ticker format validation
   - `tests/openbb_canadian_reit_examples.py` - 6 practical examples

4. **Sample Data Export**
   - `tests/riocan_dividends.csv` - 200 dividend records exported to CSV

---

## Implementation Checklist

Ready to integrate OpenBB into the pipeline:

- [ ] Install OpenBB Platform: `pip install openbb openbb-tmx`
- [ ] Review research report: `docs/OPENBB_CANADIAN_REIT_RESEARCH_REPORT.md`
- [ ] Test with your REITs: `python tests/openbb_canadian_reit_examples.py`
- [ ] Create ticker mapping: `config/ticker_mapping.yaml` (see report Section 6.3)
- [ ] Implement Phase 2.5: `scripts/enrich_market_data.py` (see report Section 6.3)
- [ ] Update `/analyzeREissuer` command to include Phase 2.5
- [ ] Add validation: Compare OpenBB dividends vs PDF distributions
- [ ] Enhance Phase 4 with peer comparisons
- [ ] Update Phase 5 template with market data sections
- [ ] Update documentation: CLAUDE.md, README.md

---

## Cost Analysis

**Current Approach (PDF Extraction):**
- Cost: $0/month
- Coverage: Complete financial statements, FFO/AFFO/ACFO, NAV
- Limitation: No historical dividend data beyond PDFs (1-2 years)

**OpenBB Free Tier:**
- Cost: $0/month
- Coverage: Dividend history (10+ years), current prices
- Limitation: No financial statements, no REIT-specific metrics

**Hybrid Approach (RECOMMENDED):**
- Cost: $0/month
- Coverage: Best of both worlds
- Benefits:
  - ✅ PDF extraction for financial statements (Phases 1-2)
  - ✅ OpenBB for dividend validation and peer comparison (Phase 2.5)
  - ✅ Enhanced credit analysis with market context
  - ✅ No additional cost

**If Financial Statements API Needed (Optional):**
- FMP Starter: $14.99/month (250 calls/day)
- FMP Professional: $29.99/month (750 calls/day)
- **Evaluation:** Only needed if PDF extraction reliability < 90%
- **Current status:** PDF extraction working well, no immediate need

---

## Alternative Data Sources

If OpenBB proves insufficient in the future:

1. **EOD Historical Data (EODHD)** - $19.99/month
   - 30+ years dividend history
   - Includes financial statements
   - Excellent Canadian coverage

2. **Norgate Data** - $30-50/month
   - Survivorship bias-free
   - Deep Canadian equities coverage
   - Daily updates

3. **Direct yfinance library** - Free
   - Already integrated via OpenBB
   - No need for separate integration

---

## Rating

**Overall: 4/5** for Canadian REIT dividend data retrieval

**Strengths:**
- ✅ Free tier sufficient for dividend analysis
- ✅ Comprehensive historical data (2009-2025)
- ✅ Rich metadata from TMX provider
- ✅ Simple API, well-documented
- ✅ Active development

**Weaknesses:**
- ⚠️ No financial statements (free tier)
- ⚠️ No REIT-specific metrics
- ⚠️ Ticker format sensitivity

**Recommendation:**
Use OpenBB as **complementary data source** for dividend validation and peer comparison. Continue PDF extraction for financial statements and REIT metrics.

---

## Questions?

- **Full research report:** `docs/OPENBB_CANADIAN_REIT_RESEARCH_REPORT.md`
- **Quick start guide:** `docs/OPENBB_QUICK_START.md`
- **Test code:** `tests/openbb_canadian_reit_examples.py`
- **Contact:** See project documentation in `/workspaces/issuer-credit-analysis/`

---

**Research completed:** 2025-10-21  
**OpenBB version tested:** 4.4.0  
**Extensions tested:** TMX 1.4.0, YFinance 1.5.0
