# OpenBB Quick Start Guide for Issuer Due Diligence

## 5-Minute Setup

### Step 1: Install OpenBB
```bash
pip install openbb[all]
```

### Step 2: Test Installation
```python
from openbb import obb

# Test with a simple query
data = obb.equity.price.quote(symbol="PLD", provider="yfinance")
print(data.to_dataframe())
```

### Step 3: Set Up Free API Keys (Optional but Recommended)

**FRED (Federal Reserve Economic Data):**
1. Go to https://fred.stlouisfed.org/docs/api/api_key.html
2. Register for free API key
3. Set in Python:
```python
import os
os.environ['OPENBB_FRED_API_KEY'] = 'your_key_here'
```

**Financial Modeling Prep (FMP) - Free Tier:**
1. Go to https://site.financialmodelingprep.com/developer/docs
2. Sign up for free tier
3. Set in Python:
```python
os.environ['OPENBB_FMP_API_KEY'] = 'your_key_here'
```

---

## Most Useful Functions for Credit Analysis

### 1. Get REIT Financial Statements (5-Year History)
```python
from openbb import obb

# Income statement
income = obb.equity.fundamental.income(
    symbol="PLD",
    period="annual",
    limit=5,
    provider="fmp"
).to_dataframe()

# Balance sheet
balance = obb.equity.fundamental.balance(
    symbol="PLD",
    period="annual",
    limit=5,
    provider="fmp"
).to_dataframe()

print(income[['period_ending', 'revenue', 'net_income', 'ebitda']])
print(balance[['period_ending', 'total_assets', 'total_debt', 'total_equity']])
```

### 2. Get Current Treasury Yields
```python
# 10-Year Treasury
ten_year = obb.economy.fred_series(
    symbol="DGS10",
    provider="fred"
).to_dataframe()

current_10y = ten_year['value'].iloc[-1]
print(f"10Y Treasury: {current_10y:.2f}%")
```

### 3. Get Credit Spreads
```python
# BBB Corporate Spreads
bbb_spread = obb.economy.fred_series(
    symbol="BAMLC0A4CBBBEY",
    provider="fred"
).to_dataframe()

current_spread = bbb_spread['value'].iloc[-1]
print(f"BBB Spread: {current_spread:.0f} bps")
```

### 4. Build Peer Comparison
```python
def quick_peer_comp(tickers):
    """Quick peer comparison table."""
    results = []

    for ticker in tickers:
        # Get quote
        quote = obb.equity.price.quote(symbol=ticker, provider="yfinance").to_dataframe()

        # Get key metrics
        metrics = obb.equity.fundamental.metrics(symbol=ticker, provider="fmp").to_dataframe()

        results.append({
            'Ticker': ticker,
            'Price': quote['price'].iloc[0],
            'Market Cap ($B)': quote['market_cap'].iloc[0] / 1e9,
            'Dividend Yield': metrics['dividend_yield'].iloc[0] * 100,
            'P/B': metrics['price_to_book'].iloc[0]
        })

    return pd.DataFrame(results)

# Example
peers = quick_peer_comp(['PLD', 'DRE', 'FR', 'REXR'])
print(peers)
```

### 5. Get Economic Indicators
```python
# GDP Growth
gdp = obb.economy.fred_series(symbol="GDPC1", provider="fred").to_dataframe()
gdp['yoy_growth'] = gdp['value'].pct_change(periods=4) * 100
print(f"GDP YoY Growth: {gdp['yoy_growth'].iloc[-1]:.2f}%")

# Inflation (CPI)
cpi = obb.economy.fred_series(symbol="CPIAUCSL", provider="fred").to_dataframe()
cpi['yoy_inflation'] = cpi['value'].pct_change(periods=12) * 100
print(f"Inflation YoY: {cpi['yoy_inflation'].iloc[-1]:.2f}%")

# Unemployment
unemployment = obb.economy.fred_series(symbol="UNRATE", provider="fred").to_dataframe()
print(f"Unemployment: {unemployment['value'].iloc[-1]:.1f}%")
```

---

## Common FRED Symbols Reference

### Interest Rates
| Symbol | Description |
|--------|-------------|
| DGS3MO | 3-Month Treasury |
| DGS2 | 2-Year Treasury |
| DGS5 | 5-Year Treasury |
| DGS10 | 10-Year Treasury |
| DGS30 | 30-Year Treasury |
| FEDFUNDS | Federal Funds Rate |

### Corporate Bond Spreads
| Symbol | Description |
|--------|-------------|
| BAMLC0A1CAAAEY | AAA Corporate Spread |
| BAMLC0A2CAAEY | AA Corporate Spread |
| BAMLC0A3CAEY | A Corporate Spread |
| BAMLC0A4CBBBEY | BBB Corporate Spread |
| BAMLH0A1HYBBEY | BB High Yield Spread |
| BAMLH0A2HYBEY | B High Yield Spread |

### Economic Indicators
| Symbol | Description |
|--------|-------------|
| GDPC1 | Real GDP (Quarterly) |
| CPIAUCSL | Consumer Price Index |
| UNRATE | Unemployment Rate |
| HOUST | Housing Starts |
| INDPRO | Industrial Production |

---

## Typical Credit Analysis Workflow with OpenBB

```python
from openbb import obb
import pandas as pd

# 1. Get issuer financials
print("Fetching issuer data...")
ticker = "PLD"

income = obb.equity.fundamental.income(symbol=ticker, period="annual", limit=5, provider="fmp").to_dataframe()
balance = obb.equity.fundamental.balance(symbol=ticker, period="annual", limit=5, provider="fmp").to_dataframe()

# 2. Get peer data
print("Fetching peer data...")
peers = ['DRE', 'FR', 'REXR']
peer_data = []

for peer in [ticker] + peers:
    quote = obb.equity.price.quote(symbol=peer, provider="yfinance").to_dataframe()
    metrics = obb.equity.fundamental.metrics(symbol=peer, provider="fmp").to_dataframe()

    peer_data.append({
        'Ticker': peer,
        'Price': quote['price'].iloc[0],
        'Div Yield': metrics['dividend_yield'].iloc[0] * 100,
        'P/B': metrics['price_to_book'].iloc[0]
    })

peer_comp = pd.DataFrame(peer_data)
print("\nPeer Comparison:")
print(peer_comp)

# 3. Get market context
print("\nFetching market context...")
ten_year = obb.economy.fred_series(symbol="DGS10", provider="fred").to_dataframe()
bbb_spread = obb.economy.fred_series(symbol="BAMLC0A4CBBBEY", provider="fred").to_dataframe()
gdp = obb.economy.fred_series(symbol="GDPC1", provider="fred").to_dataframe()

print(f"10Y Treasury: {ten_year['value'].iloc[-1]:.2f}%")
print(f"BBB Spread: {bbb_spread['value'].iloc[-1]:.0f} bps")

gdp['yoy'] = gdp['value'].pct_change(periods=4) * 100
print(f"GDP Growth: {gdp['yoy'].iloc[-1]:.2f}%")

# 4. Calculate credit metrics from financials
latest_income = income.iloc[0]
latest_balance = balance.iloc[0]

debt_to_assets = (latest_balance['total_debt'] / latest_balance['total_assets']) * 100
print(f"\nDebt / Assets: {debt_to_assets:.1f}%")

# 5. Export for report
peer_comp.to_csv('peer_comparison.csv')
print("\nData export complete!")
```

---

## Troubleshooting

### Issue: "No data returned"
**Solution:** Check if provider supports that ticker/symbol. Try different provider:
```python
# Try different providers
providers = ['fmp', 'yfinance', 'intrinio', 'polygon']
for provider in providers:
    try:
        data = obb.equity.price.quote(symbol="PLD", provider=provider)
        print(f"{provider}: Success!")
        break
    except:
        print(f"{provider}: Failed")
```

### Issue: Rate limit errors
**Solution:** Implement delays between calls:
```python
import time

tickers = ['PLD', 'DRE', 'FR', 'REXR']
for ticker in tickers:
    data = get_data(ticker)
    time.sleep(1)  # 1 second delay between calls
```

### Issue: Missing API key
**Solution:** Check environment variables:
```python
import os
print("FRED Key:", os.getenv('OPENBB_FRED_API_KEY', 'Not set'))
print("FMP Key:", os.getenv('OPENBB_FMP_API_KEY', 'Not set'))
```

---

## Best Practices

1. **Always timestamp your data pulls:**
```python
from datetime import datetime
timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
print(f"Data as of: {timestamp}")
```

2. **Cache data to avoid redundant API calls:**
```python
# Save to CSV for reuse
data.to_csv(f'data_{ticker}_{datetime.now().strftime("%Y%m%d")}.csv')
```

3. **Handle errors gracefully:**
```python
try:
    data = obb.equity.price.quote(symbol=ticker)
except Exception as e:
    print(f"Error fetching {ticker}: {e}")
    data = None
```

4. **Verify data quality:**
```python
# Check for nulls
print(f"Null values: {data.isnull().sum()}")

# Validate ranges
print(f"Data range: {data['date'].min()} to {data['date'].max()}")
```

5. **Use multiple providers for validation:**
```python
# Cross-check critical data points
yf_price = obb.equity.price.quote(symbol="PLD", provider="yfinance").to_dataframe()['price'].iloc[0]
fmp_price = obb.equity.price.quote(symbol="PLD", provider="fmp").to_dataframe()['price'].iloc[0]

if abs(yf_price - fmp_price) > 0.50:
    print("Warning: Price discrepancy between providers!")
```

---

## Next Steps

After completing this quick start:
1. Review full integration guide: `openbb_integration.md`
2. Explore calculation library additions: `python_calculation_library.md`
3. See complete workflow: `report_generation_workflow.md`
4. Check OpenBB documentation: https://docs.openbb.co/platform

**Happy analyzing!**

