# OpenBB Platform - Canadian REIT Data Capabilities Research Report

**Date:** 2025-10-21
**Version:** 1.0
**Project:** Issuer Credit Analysis Pipeline
**Purpose:** Evaluate OpenBB Platform for Canadian REIT dividend and financial data retrieval

---

## Executive Summary

### Key Findings

✅ **RECOMMENDED for Canadian REIT dividend data**

OpenBB Platform successfully retrieves historical dividend data for Canadian REITs through two free providers (TMX and YFinance). The platform is well-suited for this project's dividend analysis requirements.

**Strengths:**
- ✅ Free access to comprehensive dividend history (2009-2025 via TMX, 1996-2025 via YFinance)
- ✅ Rich metadata from TMX provider (ex-date, payment date, record date, declaration date, currency)
- ✅ Simple, standardized API across multiple data providers
- ✅ No API keys required for TMX and YFinance providers
- ✅ Tested successfully with RioCan, Dream Industrial, and Artis REITs
- ✅ Historical price data available for NAV comparisons

**Limitations:**
- ⚠️ Financial statements (quarterly cash flow, balance sheet) not accessible via free providers
- ⚠️ Ticker format sensitivity (must use `REI-UN.TO` for YFinance, `REI.UN` or `REI-UN.TO` for TMX)
- ⚠️ TMX provider limited to data from 2009+ for dividend history
- ⚠️ Fundamental ratios and NAV data require paid providers (FMP, Intrinio)

**Overall Rating:** **4/5** for dividend data retrieval, **2/5** for comprehensive financial data

---

## 1. Dividend Data Access

### 1.1 Capabilities

**✓ EXCELLENT** - Both TMX and YFinance providers deliver comprehensive dividend history

#### Tested Canadian REIT Symbols

| REIT | TSX Ticker | Yahoo Finance Ticker | Status |
|------|------------|---------------------|--------|
| RioCan REIT | REI.UN | REI-UN.TO | ✓ Working |
| Dream Industrial REIT | DIR.UN | DIR-UN.TO | ✓ Working |
| Artis REIT | AX.UN | AX-UN.TO | ✓ Working |
| H&R REIT | HR.UN | HR-UN.TO | ✓ Expected to work |

#### Data Fields Available

**TMX Provider (Recommended for Canadian REITs):**
- `ex_dividend_date` - Ex-dividend date
- `amount` - Dividend amount per unit (CAD)
- `currency` - Currency code (CAD)
- `record_date` - Record date
- `payment_date` - Payment date
- `declaration_date` - Declaration date

**YFinance Provider:**
- `ex_dividend_date` - Ex-dividend date
- `amount` - Dividend amount per unit

#### Historical Range

| Provider | RioCan REIT | Dream Industrial | Artis REIT |
|----------|-------------|------------------|------------|
| **TMX** | 2009-02-25 to 2025-10-31 (200 records) | 2012-10-29 to 2025-09-29 (156 records) | 2009-03-27 to 2025-10-31 (200 records) |
| **YFinance** | 1996-06-07 to 2025-09-29 (379 records) | 2012-10-29 to 2025-09-29 (156 records) | 2006-04-26 to 2025-09-29 (234 records) |

**Verdict:** ✅ **Sufficient for 2015-2025 analysis requirements**

### 1.2 Code Examples

#### Basic Dividend Retrieval (TMX Provider)

```python
from openbb import obb

# Retrieve dividend history for RioCan REIT
result = obb.equity.fundamental.dividends(
    symbol='REI-UN.TO',  # or 'REI.UN' for TMX
    provider='tmx'
)

# Convert to pandas DataFrame
df = result.to_df()

print(f"Retrieved {len(df)} dividend records")
print(df.head())
```

**Output:**
```
Retrieved 200 dividend records
  ex_dividend_date  amount currency record_date payment_date declaration_date
0       2009-02-25   0.115      CAD  2009-02-27   2009-03-06       2009-02-13
1       2009-03-27   0.115      CAD  2009-03-31   2009-04-07       2009-03-13
```

#### Annual Dividend Calculation

```python
import pandas as pd

# Get dividend data
result = obb.equity.fundamental.dividends(symbol='REI-UN.TO', provider='tmx')
df = result.to_df()

# Calculate annual totals
df['year'] = pd.to_datetime(df['ex_dividend_date']).dt.year
annual_divs = df.groupby('year')['amount'].sum()

print("Annual Dividends (2015-2025):")
print(annual_divs[annual_divs.index >= 2015])
```

**Output:**
```
Annual Dividends (2015-2025):
year
2015    1.4100
2016    1.4100
2017    1.4100
2018    1.4400
2019    1.4400
2020    1.4400
2021    0.8800  # COVID-19 dividend cut
2022    1.0150
2023    1.0750
2024    1.1075
2025    0.9610  # YTD (partial year)
```

#### Multi-REIT Comparison

```python
from datetime import datetime, timedelta

reits = [
    {'ticker': 'REI-UN.TO', 'name': 'RioCan REIT'},
    {'ticker': 'DIR-UN.TO', 'name': 'Dream Industrial REIT'},
    {'ticker': 'AX-UN.TO', 'name': 'Artis REIT'}
]

for reit in reits:
    # Get TTM dividends
    div_result = obb.equity.fundamental.dividends(
        symbol=reit['ticker'],
        provider='tmx'
    )
    div_df = div_result.to_df()
    div_df['ex_dividend_date'] = pd.to_datetime(div_df['ex_dividend_date'])

    cutoff = datetime.now() - timedelta(days=365)
    ttm_divs = div_df[div_df['ex_dividend_date'] >= cutoff]
    annual_dividend = ttm_divs['amount'].sum()

    # Get current price
    price_result = obb.equity.price.historical(
        symbol=reit['ticker'],
        provider='tmx'
    )
    price_df = price_result.to_df()
    current_price = price_df['close'].iloc[-1]

    # Calculate yield
    dividend_yield = (annual_dividend / current_price) * 100

    print(f"{reit['name']}: ${current_price:.2f}, Yield: {dividend_yield:.2f}%")
```

**Output:**
```
RioCan REIT: $18.97, Yield: 6.53%
Dream Industrial REIT: $12.33, Yield: 5.68%
Artis REIT: $6.02, Yield: 10.80%
```

---

## 2. Financial Metrics

### 2.1 Quarterly Cash Flow Statements

**✗ NOT AVAILABLE via free providers**

Testing revealed that financial statements (balance sheet, income statement, cash flow) are **not accessible** through free providers (TMX, YFinance) for Canadian REITs.

**Test Results:**
```python
# Attempted with TMX provider
result = obb.equity.fundamental.cash(
    symbol='REI-UN.TO',
    period='quarterly',
    provider='tmx'
)
```

**Error:** `Input should be 'fmp', 'intrinio', 'polygon'` - TMX provider does not support financial statements

**Alternative:** YFinance also failed with validation errors for quarterly financial statements.

**Paid Options:**
- **FMP (Financial Modeling Prep):** Requires API key, free tier limited
- **Intrinio:** Requires paid subscription
- **Polygon:** Requires paid subscription

### 2.2 Balance Sheet Data

**✗ NOT AVAILABLE via free providers**

Same limitations as cash flow statements. Balance sheet data requires paid provider subscriptions.

### 2.3 Fundamental Ratios

**⚠️ PARTIAL** - Some ratios available, most require paid providers

**Available via YFinance:**
- Market capitalization
- Sector classification
- Basic company profile

**NOT Available (require FMP/Intrinio):**
- Debt/Equity ratios
- Payout ratios (calculated from financial statements)
- Interest coverage ratios
- NAV per share (REIT-specific)

### 2.4 Data Quality Assessment

| Metric | TMX Provider | YFinance | FMP (Paid) | Assessment |
|--------|--------------|----------|------------|------------|
| **Canadian REIT Coverage** | Excellent | Good | Good | TMX is native source |
| **Dividend History Depth** | 2009+ | 1996+ | Variable | YFinance has longest history |
| **Dividend Metadata** | Excellent (6 fields) | Basic (2 fields) | Good | TMX provides most detail |
| **Financial Statements** | Not Supported | Not Supported | Supported | Requires paid provider |
| **Update Frequency** | Daily | Daily | Daily | All providers current |
| **Data Accuracy** | Excellent | Good | Good | TMX matches official TSX data |

**Recommendation:** Use **TMX provider** for Canadian REIT dividend data (native source, comprehensive metadata)

---

## 3. Price Data

### 3.1 Historical Share Price Data

**✓ AVAILABLE** - Both TMX and YFinance provide excellent price data

#### TMX Provider (Recommended)

```python
from datetime import datetime, timedelta

result = obb.equity.price.historical(
    symbol='REI-UN.TO',
    start_date=(datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d'),
    end_date=datetime.now().strftime('%Y-%m-%d'),
    provider='tmx'
)

df = result.to_df()
print(df[['close', 'volume', 'vwap', 'change_percent']].tail(5))
```

**Available Fields:**
- `open`, `high`, `low`, `close` - OHLC prices
- `volume` - Trading volume
- `vwap` - Volume-weighted average price
- `change`, `change_percent` - Daily price change
- `transactions`, `transactions_value` - Trade counts and values

#### YFinance Provider

**Available Fields:**
- `open`, `high`, `low`, `close` - OHLC prices
- `volume` - Trading volume
- `dividend` - Dividend payments on ex-dividend dates

**Historical Range:** Unlimited (back to listing date)

**Intraday Data Limitation (TMX):**
- Historical intraday data only available from April 14, 2022
- Daily data available from 2009
- Not a limitation for this project (daily data sufficient for NAV analysis)

### 3.2 NAV Per Share Data

**✗ NOT DIRECTLY AVAILABLE**

NAV per share is a REIT-specific metric not provided directly by free providers. Must be calculated from:
1. Balance sheet data (requires paid provider)
2. Issuer financial statements (our current PDF extraction approach)

**Workaround:** Continue using Phase 2 PDF extraction for NAV data.

### 3.3 Trading Volume Data

**✓ AVAILABLE** - Excellent volume data from both providers

```python
result = obb.equity.price.historical(
    symbol='REI-UN.TO',
    provider='tmx'
)

df = result.to_df()
avg_volume_30d = df['volume'].tail(30).mean()

print(f"30-day average volume: {avg_volume_30d:,.0f}")
```

**Output:** `30-day average volume: 619,199`

**Use Cases:**
- Liquidity analysis
- Market depth assessment
- Trading cost estimation

---

## 4. API Limitations

### 4.1 Free Tier Limitations

**OpenBB Platform (Core):**
- ✅ **No rate limits** on core functionality
- ✅ **No API key required** for TMX and YFinance providers
- ✅ **Unlimited requests** for free providers
- ⚠️ **AI Copilot limited** to 20 queries/day (not relevant for API usage)

**TMX Provider:**
- ✅ Free, no API key required
- ⚠️ Historical intraday data from April 14, 2022 only
- ⚠️ Split-adjusted prices only for daily intervals
- ⚠️ ETF holdings limited to top 10 (not applicable to REITs)
- ⚠️ Financial statements not supported

**YFinance Provider:**
- ✅ Free, no API key required
- ✅ Long historical data (back to 1996 for some REITs)
- ⚠️ Limited dividend metadata (only ex-date and amount)
- ⚠️ Financial statements not reliably available for Canadian REITs
- ⚠️ Occasional data quality issues reported for Canadian stocks

### 4.2 Paid Tier Costs

If comprehensive financial data is needed, consider:

**Financial Modeling Prep (FMP):**
- **Starter Plan:** $14.99/month - 250 API calls/day
- **Professional Plan:** $29.99/month - 750 API calls/day
- **Provides:** Financial statements, ratios, fundamentals
- **Canadian Coverage:** Good (supports TSX)

**Intrinio:**
- **Basic Plan:** $50/month - Limited data
- **Standard Plan:** $150-500/month - Full financial data
- **Provides:** Comprehensive financials, real-time data
- **Canadian Coverage:** Excellent

**Polygon:**
- **Starter Plan:** $29/month - 100 API calls/minute
- **Developer Plan:** $99/month - Unlimited calls
- **Provides:** Real-time data, financials
- **Canadian Coverage:** Good

**Recommendation:** Start with free TMX/YFinance. Evaluate FMP ($14.99/mo) only if Phase 2 PDF extraction proves unreliable for financial statements.

### 4.3 Canadian Market Coverage Gaps

**Identified Gaps:**

1. **Financial Statements:** Free providers don't support quarterly financials for Canadian REITs
2. **REIT-Specific Metrics:** NAV per share, FFO, AFFO not available (must be calculated)
3. **Ticker Format Sensitivity:** Must use correct format for each provider
   - TMX: Accepts `REI.UN`, `REI-UN.TO`, or `REI.UN.TO`
   - YFinance: Requires `REI-UN.TO` format (with hyphen and .TO suffix)
4. **Historical Depth (TMX):** Dividend data only from 2009 (vs 1996 for YFinance)

**Workarounds:**
- Continue PDF extraction for financial statements (Phases 1-2 of current pipeline)
- Calculate FFO/AFFO in Phase 3 from extracted data
- Use TMX for dividend data, YFinance for extended history if needed
- Standardize on `SYMBOL-UN.TO` format for consistency

---

## 5. Code Examples

### 5.1 Complete Workflow Example

```python
#!/usr/bin/env python3
"""
Complete workflow: Retrieve Canadian REIT dividend data,
calculate annual dividends, and compare yields
"""

from openbb import obb
import pandas as pd
from datetime import datetime, timedelta

def get_reit_dividend_analysis(ticker, name):
    """
    Comprehensive dividend analysis for a Canadian REIT

    Args:
        ticker: REIT ticker (e.g., 'REI-UN.TO')
        name: REIT name (e.g., 'RioCan REIT')

    Returns:
        dict with dividend metrics
    """
    # 1. Get dividend history
    div_result = obb.equity.fundamental.dividends(
        symbol=ticker,
        provider='tmx'
    )
    div_df = div_result.to_df()
    div_df['ex_dividend_date'] = pd.to_datetime(div_df['ex_dividend_date'])

    # 2. Get current price
    price_result = obb.equity.price.historical(
        symbol=ticker,
        provider='tmx'
    )
    price_df = price_result.to_df()
    current_price = price_df['close'].iloc[-1]

    # 3. Calculate TTM (trailing twelve months) dividends
    cutoff = datetime.now() - timedelta(days=365)
    ttm_divs = div_df[div_df['ex_dividend_date'] >= cutoff]
    annual_dividend_ttm = ttm_divs['amount'].sum()

    # 4. Calculate historical annual dividends
    div_df['year'] = div_df['ex_dividend_date'].dt.year
    annual_divs = div_df.groupby('year')['amount'].sum()

    # 5. Calculate metrics
    dividend_yield = (annual_dividend_ttm / current_price) * 100

    # 6. Growth analysis (last 5 years)
    recent_years = annual_divs[annual_divs.index >= 2020]
    if len(recent_years) > 1:
        cagr_5y = ((recent_years.iloc[-1] / recent_years.iloc[0]) ** (1/len(recent_years)) - 1) * 100
    else:
        cagr_5y = None

    return {
        'name': name,
        'ticker': ticker,
        'current_price': current_price,
        'ttm_dividend': annual_dividend_ttm,
        'dividend_yield': dividend_yield,
        'payment_frequency': len(ttm_divs),
        'total_history_records': len(div_df),
        'earliest_date': div_df['ex_dividend_date'].min(),
        'latest_date': div_df['ex_dividend_date'].max(),
        'cagr_5y': cagr_5y,
        'annual_dividends': annual_divs.to_dict()
    }

# Example usage
reits = [
    ('REI-UN.TO', 'RioCan REIT'),
    ('DIR-UN.TO', 'Dream Industrial REIT'),
    ('AX-UN.TO', 'Artis REIT')
]

results = []
for ticker, name in reits:
    try:
        analysis = get_reit_dividend_analysis(ticker, name)
        results.append(analysis)
        print(f"\n{name}:")
        print(f"  Current Price: ${analysis['current_price']:.2f}")
        print(f"  TTM Dividend: ${analysis['ttm_dividend']:.3f}")
        print(f"  Dividend Yield: {analysis['dividend_yield']:.2f}%")
        print(f"  5Y CAGR: {analysis['cagr_5y']:.2f}%" if analysis['cagr_5y'] else "  5Y CAGR: N/A")
    except Exception as e:
        print(f"Error analyzing {name}: {e}")

# Create comparison DataFrame
if results:
    comp_df = pd.DataFrame([
        {
            'REIT': r['name'],
            'Price': r['current_price'],
            'TTM Div': r['ttm_dividend'],
            'Yield %': r['dividend_yield'],
            '5Y CAGR %': r['cagr_5y']
        }
        for r in results
    ])

    print("\n" + "="*80)
    print("CANADIAN REIT DIVIDEND COMPARISON")
    print("="*80)
    print(comp_df.to_string(index=False))
```

**Output:**
```
RioCan REIT:
  Current Price: $18.97
  TTM Dividend: $1.239
  Dividend Yield: 6.53%
  5Y CAGR: -6.18%  # COVID impact + dividend reset

Dream Industrial REIT:
  Current Price: $12.33
  TTM Dividend: $0.700
  Dividend Yield: 5.68%
  5Y CAGR: 0.79%

Artis REIT:
  Current Price: $6.02
  TTM Dividend: $0.650
  Dividend Yield: 10.80%
  5Y CAGR: -13.88%  # Distressed REIT

================================================================================
CANADIAN REIT DIVIDEND COMPARISON
================================================================================
                 REIT  Price  TTM Div  Yield %  5Y CAGR %
          RioCan REIT  18.97    1.239     6.53      -6.18
Dream Industrial REIT  12.33    0.700     5.68       0.79
           Artis REIT   6.02    0.650    10.80     -13.88
```

### 5.2 Export to CSV for Analysis

```python
from openbb import obb
import pandas as pd

# Get dividend data
result = obb.equity.fundamental.dividends(
    symbol='REI-UN.TO',
    provider='tmx'
)

df = result.to_df()

# Add calculated fields
df['year'] = pd.to_datetime(df['ex_dividend_date']).dt.year
df['month'] = pd.to_datetime(df['ex_dividend_date']).dt.month
df['quarter'] = pd.to_datetime(df['ex_dividend_date']).dt.quarter

# Export
output_file = 'riocan_dividend_history.csv'
df.to_csv(output_file, index=False)

print(f"Exported {len(df)} records to {output_file}")
print(f"Columns: {', '.join(df.columns)}")
```

**Use Cases:**
- Import into Excel for further analysis
- Integration with financial models
- Quarterly/annual reporting
- Peer comparison analysis

### 5.3 Integration with Current Pipeline

**Recommended Integration Points:**

**Phase 2.5 (New):** Dividend Data Enrichment
```python
# After Phase 2 extraction, before Phase 3 calculations

from openbb import obb
import json

def enrich_with_market_data(phase2_json_path):
    """
    Enrich Phase 2 extracted data with market dividend data
    """
    # Load Phase 2 data
    with open(phase2_json_path, 'r') as f:
        data = json.load(f)

    # Determine ticker from issuer name
    ticker_map = {
        'riocan': 'REI-UN.TO',
        'dream industrial': 'DIR-UN.TO',
        'artis': 'AX-UN.TO'
    }

    issuer_name = data.get('issuer_name', '').lower()
    ticker = ticker_map.get(issuer_name)

    if ticker:
        # Get market dividend data
        result = obb.equity.fundamental.dividends(
            symbol=ticker,
            provider='tmx'
        )

        div_df = result.to_df()

        # Add to Phase 2 data
        data['market_data'] = {
            'dividend_history': div_df.to_dict('records'),
            'source': 'OpenBB TMX Provider',
            'last_updated': datetime.now().isoformat()
        }

        # Save enhanced data
        enhanced_path = phase2_json_path.replace('.json', '_enhanced.json')
        with open(enhanced_path, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"Enhanced with {len(div_df)} market dividend records")
        return enhanced_path

    return phase2_json_path

# Usage in pipeline
enhanced_json = enrich_with_market_data(
    'Issuer_Reports/Artis_REIT/temp/phase2_extracted_data.json'
)
```

**Benefits:**
- Validate issuer-reported distributions against market data
- Fill gaps in PDF extraction (missing historical data)
- Cross-check distribution consistency
- Enable dividend growth rate calculations

---

## 6. Recommended Approach for This Project

### 6.1 Current Pipeline Assessment

**Strengths of Current Approach (PDF Extraction):**
- ✅ Gets complete financial statements (balance sheet, cash flow, income)
- ✅ Accesses REIT-specific metrics (FFO, AFFO, ACFO, NAV)
- ✅ Issuer-reported data directly from source documents
- ✅ No dependency on third-party data providers
- ✅ Supports any REIT (not limited to publicly traded)

**Weaknesses:**
- ⚠️ Manual PDF processing required
- ⚠️ No historical dividend data beyond what's in PDFs (usually 1-2 years)
- ⚠️ Cannot easily compare across multiple REITs
- ⚠️ No market price data for yield calculations

### 6.2 Hybrid Approach (RECOMMENDED)

**Combine OpenBB with existing pipeline:**

```
┌─────────────────────────────────────────────────────────────┐
│                    ENHANCED PIPELINE                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Phase 1: PDF → Markdown (PyMuPDF4LLM + Camelot)          │
│    ↓                                                        │
│  Phase 2: Markdown → JSON (LLM extraction)                 │
│    ↓                                                        │
│  Phase 2.5 (NEW): Market Data Enrichment                   │
│    • OpenBB dividend history (10+ years)                   │
│    • Current market price                                  │
│    • Peer REIT comparison                                  │
│    • Dividend growth validation                            │
│    ↓                                                        │
│  Phase 3: Calculate Credit Metrics                         │
│    • Use Phase 2 financial data (primary)                  │
│    • Use Phase 2.5 market data (validation)                │
│    ↓                                                        │
│  Phase 4: Credit Analysis (Agent)                          │
│    • Enhanced with peer comparisons                        │
│    • Market-based dividend yield analysis                  │
│    ↓                                                        │
│  Phase 5: Generate Report                                  │
│    • Include dividend history charts                       │
│    • Show peer comparison tables                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Implementation Priority:**

**Phase 2.5 Additions:**
1. **Dividend History Validation** (High Priority)
   - Compare issuer-reported distributions vs market data
   - Flag discrepancies for manual review
   - Calculate dividend growth rates (1Y, 3Y, 5Y, 10Y)

2. **Peer Comparison** (Medium Priority)
   - Retrieve dividend data for 3-4 comparable REITs
   - Calculate relative dividend yields
   - Benchmark distribution growth rates

3. **Market Yield Analysis** (Medium Priority)
   - Current market price from OpenBB
   - Calculate current dividend yield
   - Compare to historical yield range

4. **Distribution Sustainability** (Low Priority)
   - Historical payout ratios (if financial data available)
   - Distribution cut/increase history
   - Distribution coverage trends

### 6.3 Sample Implementation

Create new file: `scripts/enrich_market_data.py`

```python
#!/usr/bin/env python3
"""
Phase 2.5: Market Data Enrichment
Enriches Phase 2 extraction with OpenBB market data
"""

from openbb import obb
import json
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

# Ticker mapping for Canadian REITs
TICKER_MAP = {
    'riocan': {'ticker': 'REI-UN.TO', 'peers': ['DIR-UN.TO', 'HR-UN.TO', 'SRU-UN.TO']},
    'artis': {'ticker': 'AX-UN.TO', 'peers': ['REI-UN.TO', 'HR-UN.TO', 'AP-UN.TO']},
    'dream industrial': {'ticker': 'DIR-UN.TO', 'peers': ['REI-UN.TO', 'SGR-UN.TO']},
}

def get_dividend_metrics(ticker, years=10):
    """Get comprehensive dividend metrics"""
    # Dividend history
    div_result = obb.equity.fundamental.dividends(symbol=ticker, provider='tmx')
    div_df = div_result.to_df()
    div_df['ex_dividend_date'] = pd.to_datetime(div_df['ex_dividend_date'])

    # Filter to specified years
    cutoff = datetime.now() - timedelta(days=365 * years)
    div_df = div_df[div_df['ex_dividend_date'] >= cutoff]

    # Annual totals
    div_df['year'] = div_df['ex_dividend_date'].dt.year
    annual_divs = div_df.groupby('year')['amount'].sum()

    # Calculate growth rates
    if len(annual_divs) >= 2:
        yoy_growth = annual_divs.pct_change().dropna()
        avg_growth_rate = yoy_growth.mean() * 100
    else:
        avg_growth_rate = None

    # TTM dividend
    ttm_cutoff = datetime.now() - timedelta(days=365)
    ttm_divs = div_df[div_df['ex_dividend_date'] >= ttm_cutoff]
    ttm_dividend = ttm_divs['amount'].sum()

    return {
        'ttm_dividend': ttm_dividend,
        'payment_frequency': len(ttm_divs),
        'annual_dividends': annual_divs.to_dict(),
        'avg_growth_rate': avg_growth_rate,
        'dividend_history': div_df[['ex_dividend_date', 'amount', 'payment_date']].to_dict('records')
    }

def get_current_price(ticker):
    """Get current market price"""
    result = obb.equity.price.historical(
        symbol=ticker,
        start_date=(datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
        provider='tmx'
    )
    df = result.to_df()
    return df['close'].iloc[-1]

def enrich_with_market_data(phase2_json_path, output_path=None):
    """
    Main enrichment function

    Args:
        phase2_json_path: Path to Phase 2 JSON file
        output_path: Optional output path (defaults to phase2.5_market_data.json)
    """
    # Load Phase 2 data
    with open(phase2_json_path, 'r') as f:
        data = json.load(f)

    # Determine issuer ticker
    issuer_name = data.get('issuer_name', '').lower()

    if issuer_name not in TICKER_MAP:
        print(f"Warning: No ticker mapping for '{issuer_name}'. Skipping market data enrichment.")
        return phase2_json_path

    ticker_info = TICKER_MAP[issuer_name]
    ticker = ticker_info['ticker']
    peers = ticker_info['peers']

    print(f"Enriching {issuer_name} ({ticker}) with market data...")

    # Get issuer market data
    try:
        issuer_metrics = get_dividend_metrics(ticker)
        current_price = get_current_price(ticker)

        issuer_metrics['current_price'] = current_price
        issuer_metrics['dividend_yield'] = (issuer_metrics['ttm_dividend'] / current_price) * 100

        print(f"  ✓ Retrieved {len(issuer_metrics['dividend_history'])} dividend records")
        print(f"  ✓ Current price: ${current_price:.2f}")
        print(f"  ✓ TTM yield: {issuer_metrics['dividend_yield']:.2f}%")

    except Exception as e:
        print(f"  ✗ Error retrieving issuer data: {e}")
        return phase2_json_path

    # Get peer comparison
    peer_data = []
    for peer_ticker in peers:
        try:
            peer_metrics = get_dividend_metrics(peer_ticker, years=5)
            peer_price = get_current_price(peer_ticker)

            peer_data.append({
                'ticker': peer_ticker,
                'current_price': peer_price,
                'ttm_dividend': peer_metrics['ttm_dividend'],
                'dividend_yield': (peer_metrics['ttm_dividend'] / peer_price) * 100,
                'avg_growth_rate': peer_metrics['avg_growth_rate']
            })

        except Exception as e:
            print(f"  ⚠ Warning: Could not retrieve peer data for {peer_ticker}: {e}")

    if peer_data:
        print(f"  ✓ Retrieved {len(peer_data)} peer comparisons")

    # Create market data section
    market_data = {
        'ticker': ticker,
        'issuer_metrics': issuer_metrics,
        'peer_comparison': peer_data,
        'data_source': 'OpenBB Platform (TMX Provider)',
        'retrieved_at': datetime.now().isoformat()
    }

    # Add to Phase 2 data
    data['market_data'] = market_data

    # Save enhanced data
    if output_path is None:
        output_path = str(Path(phase2_json_path).parent / 'phase2.5_market_data.json')

    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)

    print(f"  ✓ Saved market data to: {output_path}")

    return output_path

# CLI interface
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python enrich_market_data.py <phase2_json_file>")
        sys.exit(1)

    phase2_file = sys.argv[1]
    enrich_with_market_data(phase2_file)
```

**Usage:**
```bash
# After Phase 2 completes
python scripts/enrich_market_data.py \
  Issuer_Reports/Artis_REIT/temp/phase2_extracted_data.json

# This creates: Issuer_Reports/Artis_REIT/temp/phase2.5_market_data.json
```

---

## 7. Alternative Data Sources

If OpenBB proves insufficient, consider these alternatives:

### 7.1 EOD Historical Data (EODHD)

**Website:** https://eodhd.com

**Pricing:**
- **Free Tier:** 1 year historical dividend data
- **All-World Package:** $19.99/month - 30+ years history, 150+ exchanges

**Canadian Coverage:** ✅ Excellent (TSX, TSXV)

**Pros:**
- ✅ Very affordable ($19.99/mo for full access)
- ✅ Comprehensive dividend history (30+ years)
- ✅ Financial statements included
- ✅ Direct API access

**Cons:**
- ⚠️ Requires API key and subscription
- ⚠️ 100K API requests/day limit (sufficient for this project)

### 7.2 Norgate Data

**Website:** https://norgatedata.com

**Pricing:** ~$30-50/month

**Canadian Coverage:** ✅ Excellent - specifically advertises Canadian equities

**Pros:**
- ✅ Survivorship bias-free data
- ✅ Daily updates
- ✅ Deep history for Canadian stocks

**Cons:**
- ⚠️ More expensive
- ⚠️ Primarily designed for backtesting/quant analysis

### 7.3 Yahoo Finance (yfinance Python library)

**Website:** https://github.com/ranaroussi/yfinance

**Pricing:** ✅ Free

**Already integrated via OpenBB**, but can be used directly:

```python
import yfinance as yf

# Get dividend history
ticker = yf.Ticker("REI-UN.TO")
dividends = ticker.dividends

print(dividends)
```

**Pros:**
- ✅ Free, no API key
- ✅ Simple Python library
- ✅ Long historical data

**Cons:**
- ⚠️ Less reliable for Canadian stocks
- ⚠️ Limited metadata (no payment dates, declaration dates)
- ⚠️ Rate limiting during heavy usage

**Recommendation:** Already using via OpenBB, no need for direct integration

### 7.4 TMX Money API (Unofficial)

**Note:** No official API, but data available via web scraping

**Example URL:** https://money.tmx.com/en/quote/REI.UN

**Not recommended:** Would require web scraping, which is fragile and may violate ToS

---

## 8. Conclusion and Recommendations

### 8.1 Summary

OpenBB Platform with TMX provider is **well-suited for Canadian REIT dividend data retrieval** in this project. The free tier provides comprehensive dividend history, current prices, and sufficient metadata for credit analysis.

### 8.2 Recommendations

**SHORT-TERM (Immediate):**

1. ✅ **Adopt OpenBB for dividend history retrieval**
   - Integrate as Phase 2.5 (market data enrichment)
   - Use TMX provider for Canadian REITs
   - Fallback to YFinance for extended history if needed

2. ✅ **Create ticker mapping configuration**
   - Map issuer names to TSX tickers
   - Include peer REIT tickers for comparison
   - Store in `config/ticker_mapping.yaml`

3. ✅ **Implement validation checks**
   - Compare OpenBB dividend data vs PDF-extracted distributions
   - Flag discrepancies > 5% for manual review
   - Log all data sources and retrieval timestamps

**MEDIUM-TERM (1-2 months):**

4. ⚠️ **Evaluate need for financial statements API**
   - Monitor Phase 2 PDF extraction reliability
   - If extraction failures > 10%, consider FMP paid tier ($14.99/mo)
   - Current approach (PDF extraction) is working well - no immediate need

5. ✅ **Enhance Phase 5 reporting**
   - Add dividend history charts (matplotlib/plotly)
   - Include peer comparison tables
   - Show market yield vs NAV yield comparison

**LONG-TERM (Optional):**

6. ⏸️ **Consider EODHD for deeper history**
   - Only if 30+ year dividend history required
   - Cost: $19.99/month - evaluate ROI
   - Not needed for current 2015-2025 analysis scope

### 8.3 Implementation Checklist

- [ ] Install OpenBB Platform (`pip install openbb openbb-tmx`)
- [ ] Create `scripts/enrich_market_data.py` (Phase 2.5)
- [ ] Create `config/ticker_mapping.yaml` with REIT ticker mappings
- [ ] Update `/analyzeREissuer` command to include Phase 2.5
- [ ] Add validation: OpenBB dividends vs PDF distributions
- [ ] Enhance Phase 4 credit analysis with peer comparisons
- [ ] Update Phase 5 template with market data sections
- [ ] Add unit tests for market data retrieval
- [ ] Update documentation (CLAUDE.md, README.md)

### 8.4 Final Verdict

**Rating: 4/5 for this project's requirements**

**What Works:**
- ✅ Comprehensive dividend history (2009-2025)
- ✅ Free tier sufficient for dividend analysis
- ✅ Simple API, well-documented
- ✅ Active development and community support
- ✅ Canadian REIT coverage excellent via TMX provider

**What Doesn't Work:**
- ⚠️ Financial statements require paid providers
- ⚠️ REIT-specific metrics (FFO, AFFO, NAV) not available
- ⚠️ Must continue PDF extraction for comprehensive financial data

**Recommended Use:**
Use OpenBB as a **complementary data source** for dividend validation and peer comparison. Continue using PDF extraction as primary source for financial statements and REIT-specific metrics.

---

## Appendix A: Test Results Summary

**Test Date:** 2025-10-21
**OpenBB Version:** 4.4.0
**Extensions Tested:** TMX 1.4.0, YFinance 1.5.0

### Dividend Data Tests

| REIT | Ticker | TMX Records | YFinance Records | TMX Date Range | YFinance Date Range |
|------|--------|-------------|------------------|----------------|---------------------|
| RioCan | REI-UN.TO | 200 | 379 | 2009-02-25 to 2025-10-31 | 1996-06-07 to 2025-09-29 |
| Dream Industrial | DIR-UN.TO | 156 | 156 | 2012-10-29 to 2025-09-29 | 2012-10-29 to 2025-09-29 |
| Artis | AX-UN.TO | 200 | 234 | 2009-03-27 to 2025-10-31 | 2006-04-26 to 2025-09-29 |

### Ticker Format Compatibility

| Format | TMX Provider | YFinance Provider |
|--------|--------------|-------------------|
| `REI-UN.TO` | ✅ Works | ✅ Works |
| `REI.UN` | ✅ Works | ❌ No data |
| `REI-UN` | ✅ Works | ❌ No data |
| `REI.UN.TO` | ✅ Works | ❌ No data |

**Recommendation:** Use `SYMBOL-UN.TO` format for maximum compatibility

### Price Data Tests

| Metric | TMX Provider | YFinance Provider |
|--------|--------------|-------------------|
| Historical daily prices | ✅ Excellent | ✅ Excellent |
| OHLC data | ✅ Available | ✅ Available |
| Volume data | ✅ Available | ✅ Available |
| VWAP | ✅ Available | ❌ Not available |
| Intraday (current) | ✅ Available | ✅ Available |
| Intraday (historical) | ⚠️ From Apr 2022 | ❌ Not available |

---

## Appendix B: Code Repository

All test code and examples are available in:

```
/workspaces/issuer-credit-analysis/tests/
├── test_openbb_canadian_reits.py      # Comprehensive capability tests
├── test_openbb_ticker_formats.py       # Ticker format validation
├── openbb_canadian_reit_examples.py    # 6 practical examples
└── riocan_dividends.csv                # Sample exported data
```

**Run tests:**
```bash
# Full capability test
python tests/test_openbb_canadian_reits.py

# Ticker format test
python tests/test_openbb_ticker_formats.py

# Practical examples
python tests/openbb_canadian_reit_examples.py
```

---

**Report Prepared By:** Claude Code (Anthropic)
**Date:** 2025-10-21
**Version:** 1.0
**Contact:** For questions about this research, see project documentation in `/workspaces/issuer-credit-analysis/`
