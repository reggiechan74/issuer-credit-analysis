# OpenBB Platform Integration for Real-Time Market Data

## Overview

This document provides comprehensive guidance on integrating OpenBB Platform to access real-time market data for issuer due diligence analysis. OpenBB enhances the credit analysis workflow by providing live data on:

- **REIT equity prices and fundamentals**
- **Corporate bond yields and spreads**
- **Treasury yields and benchmark rates**
- **Economic indicators (GDP, CPI, unemployment)**
- **Peer company financials**
- **Market comparables and trading multiples**

**OpenBB Platform:** Open-source financial data platform integrating ~100 data providers
**Documentation:** https://docs.openbb.co/platform
**GitHub:** https://github.com/OpenBB-finance/OpenBB

---

## I. Installation and Setup

### 1.1 Install OpenBB Platform

```bash
# Install via pip
pip install openbb

# Install with all extensions (recommended for full functionality)
pip install openbb[all]

# Verify installation
python -c "from openbb import obb; print(obb.__version__)"
```

### 1.2 API Keys and Authentication

While OpenBB provides free data from several providers, some premium data sources require API keys.

**Setting up API keys:**

```python
# Option 1: Set via Python
from openbb import obb

obb.account.login(
    email="your_email@example.com",
    password="your_password"
)

# Option 2: Set environment variables
import os
os.environ['OPENBB_FMP_API_KEY'] = 'your_fmp_key'
os.environ['OPENBB_FRED_API_KEY'] = 'your_fred_key'
```

**Free data providers (no API key required):**
- Yahoo Finance
- Federal Reserve Economic Data (FRED) - requires free API key
- ECB (European Central Bank)
- Many others

**Premium providers (API key required):**
- Financial Modeling Prep (FMP)
- Alpha Vantage
- Intrinio
- Benzinga
- Others

### 1.3 Basic Configuration

```python
from openbb import obb

# Check available providers
providers = obb.coverage.providers
print(providers)

# Check available commands
commands = obb.coverage.commands
print(commands)

# Set preferences
obb.user.preferences.output_type = 'dataframe'  # Return pandas DataFrames by default
```

---

## II. Accessing REIT Market Data

### 2.1 REIT Stock Prices and Historical Data

```python
from openbb import obb
import pandas as pd

def get_reit_price_history(
    ticker: str,
    start_date: str = None,
    end_date: str = None,
    provider: str = 'yfinance'
) -> pd.DataFrame:
    """
    Get historical price data for a REIT.

    Parameters:
    -----------
    ticker : str
        REIT ticker symbol (e.g., 'VNQ', 'PLD', 'O')
    start_date : str
        Start date (YYYY-MM-DD format)
    end_date : str
        End date (YYYY-MM-DD format)
    provider : str
        Data provider ('yfinance', 'fmp', 'polygon', etc.)

    Returns:
    --------
    pd.DataFrame : Historical price data with OHLCV
    """
    data = obb.equity.price.historical(
        symbol=ticker,
        start_date=start_date,
        end_date=end_date,
        provider=provider
    )

    return data.to_dataframe()


# Example usage
reit_prices = get_reit_price_history(
    ticker='PLD',  # Prologis (industrial REIT)
    start_date='2024-01-01',
    end_date='2025-10-17'
)

print(reit_prices.tail())
print(f"Current price: ${reit_prices['close'].iloc[-1]:.2f}")
```

### 2.2 REIT Financial Statements

```python
def get_reit_financials(
    ticker: str,
    statement_type: str = 'income',
    period: str = 'annual',
    limit: int = 5,
    provider: str = 'fmp'
) -> pd.DataFrame:
    """
    Get financial statements for a REIT.

    Parameters:
    -----------
    ticker : str
        REIT ticker symbol
    statement_type : str
        'income', 'balance', or 'cash'
    period : str
        'annual' or 'quarter'
    limit : int
        Number of periods to retrieve
    provider : str
        Data provider

    Returns:
    --------
    pd.DataFrame : Financial statement data
    """
    if statement_type == 'income':
        data = obb.equity.fundamental.income(
            symbol=ticker,
            period=period,
            limit=limit,
            provider=provider
        )
    elif statement_type == 'balance':
        data = obb.equity.fundamental.balance(
            symbol=ticker,
            period=period,
            limit=limit,
            provider=provider
        )
    elif statement_type == 'cash':
        data = obb.equity.fundamental.cash(
            symbol=ticker,
            period=period,
            limit=limit,
            provider=provider
        )
    else:
        raise ValueError("statement_type must be 'income', 'balance', or 'cash'")

    return data.to_dataframe()


# Example: Get Prologis income statements
income_stmt = get_reit_financials('PLD', statement_type='income', period='annual', limit=5)
print(income_stmt[['period_ending', 'revenue', 'net_income', 'ebitda']])

# Get balance sheet
balance_sheet = get_reit_financials('PLD', statement_type='balance', period='annual')
print(balance_sheet[['period_ending', 'total_assets', 'total_debt', 'total_equity']])
```

### 2.3 REIT Fundamentals and Metrics

```python
def get_reit_metrics(
    ticker: str,
    provider: str = 'fmp'
) -> pd.DataFrame:
    """
    Get key financial metrics and ratios for a REIT.

    Returns metrics like P/E, P/B, dividend yield, ROE, debt ratios, etc.
    """
    data = obb.equity.fundamental.metrics(
        symbol=ticker,
        provider=provider
    )

    return data.to_dataframe()


# Example: Get REIT metrics
metrics = get_reit_metrics('PLD')

# Extract relevant metrics
relevant_metrics = metrics[[
    'market_cap',
    'price_to_book',
    'price_to_sales',
    'dividend_yield',
    'return_on_equity',
    'debt_to_equity',
    'current_ratio'
]].iloc[0]

print(relevant_metrics)
```

### 2.4 REIT Valuation Multiples

```python
def get_reit_valuation_multiples(
    ticker: str,
    provider: str = 'fmp'
) -> dict:
    """
    Calculate key REIT valuation multiples.
    """
    # Get current quote
    quote = obb.equity.price.quote(symbol=ticker, provider=provider).to_dataframe()

    # Get financial metrics
    metrics = obb.equity.fundamental.metrics(symbol=ticker, provider=provider).to_dataframe()

    # Get latest financials
    income = get_reit_financials(ticker, 'income', 'annual', limit=1)
    balance = get_reit_financials(ticker, 'balance', 'annual', limit=1)

    # Calculate multiples
    market_cap = quote['market_cap'].iloc[0] if 'market_cap' in quote else None
    price = quote['price'].iloc[0]

    # Price/FFO would require FFO calculation from income statement
    # (This is a simplified example - actual FFO calc more complex)

    valuation = {
        'ticker': ticker,
        'current_price': price,
        'market_cap': market_cap,
        'price_to_book': metrics['price_to_book'].iloc[0] if 'price_to_book' in metrics else None,
        'dividend_yield': metrics['dividend_yield'].iloc[0] if 'dividend_yield' in metrics else None,
        'total_assets': balance['total_assets'].iloc[0] if 'total_assets' in balance.columns else None,
        'total_debt': balance['total_debt'].iloc[0] if 'total_debt' in balance.columns else None
    }

    return valuation
```

---

## III. Accessing Bond and Credit Market Data

### 3.1 Corporate Bond Yields and Spreads

```python
def get_corporate_bond_spreads(
    rating: str = 'aaa',
    provider: str = 'fred'
) -> pd.DataFrame:
    """
    Get corporate bond yield spreads by rating.

    Parameters:
    -----------
    rating : str
        Bond rating category ('aaa', 'bbb', etc.)
    provider : str
        Data provider

    Returns:
    --------
    pd.DataFrame : Spread data
    """
    # Corporate bond spreads via FRED
    # AAA: BAMLC0A1CAAAEY
    # BBB: BAMLC0A4CBBBEY

    symbol_map = {
        'aaa': 'BAMLC0A1CAAAEY',
        'aa': 'BAMLC0A2CAAEY',
        'a': 'BAMLC0A3CAEY',
        'bbb': 'BAMLC0A4CBBBEY',
        'bb': 'BAMLH0A1HYBBEY',
        'b': 'BAMLH0A2HYBEY'
    }

    if rating.lower() not in symbol_map:
        raise ValueError(f"Rating must be one of: {list(symbol_map.keys())}")

    symbol = symbol_map[rating.lower()]

    data = obb.economy.fred_series(
        symbol=symbol,
        provider='fred'
    )

    return data.to_dataframe()


# Example: Get BBB corporate bond spreads
bbb_spreads = get_corporate_bond_spreads('bbb')
print(f"Current BBB spread: {bbb_spreads['value'].iloc[-1]:.2f} bps")
```

### 3.2 Treasury Yields (Benchmark Rates)

```python
def get_treasury_yields(
    maturity: str = None,
    provider: str = 'fred'
) -> pd.DataFrame:
    """
    Get US Treasury yields.

    Parameters:
    -----------
    maturity : str
        Specific maturity ('3m', '2y', '5y', '10y', '30y') or None for full curve
    provider : str
        Data provider

    Returns:
    --------
    pd.DataFrame : Treasury yield data
    """
    if maturity is None:
        # Get full yield curve
        data = obb.fixedincome.government.treasury_rates(
            provider=provider
        )
    else:
        # Get specific maturity from FRED
        symbol_map = {
            '3m': 'DGS3MO',
            '6m': 'DGS6MO',
            '1y': 'DGS1',
            '2y': 'DGS2',
            '5y': 'DGS5',
            '7y': 'DGS7',
            '10y': 'DGS10',
            '20y': 'DGS20',
            '30y': 'DGS30'
        }

        if maturity.lower() not in symbol_map:
            raise ValueError(f"Maturity must be one of: {list(symbol_map.keys())}")

        symbol = symbol_map[maturity.lower()]

        data = obb.economy.fred_series(
            symbol=symbol,
            provider='fred'
        )

    return data.to_dataframe()


# Example: Get 10-year Treasury yield
ten_year = get_treasury_yields('10y')
current_10y = ten_year['value'].iloc[-1]
print(f"Current 10Y Treasury: {current_10y:.2f}%")

# Get full yield curve
yield_curve = get_treasury_yields()
print(yield_curve.tail())
```

### 3.3 Calculate Credit Spreads

```python
def calculate_issuer_credit_spread(
    issuer_yield: float,
    maturity_years: float,
    issuer_rating: str
) -> dict:
    """
    Calculate credit spread for an issuer relative to benchmarks.

    Parameters:
    -----------
    issuer_yield : float
        Issuer's bond yield (%)
    maturity_years : float
        Bond maturity in years
    issuer_rating : str
        Credit rating (e.g., 'A3', 'Baa2')

    Returns:
    --------
    dict : Spread analysis
    """
    # Get comparable Treasury yield
    maturity_map = {
        (0, 0.5): '3m',
        (0.5, 1.5): '1y',
        (1.5, 3): '2y',
        (3, 7): '5y',
        (7, 12): '10y',
        (12, 100): '30y'
    }

    treasury_maturity = None
    for (low, high), mat in maturity_map.items():
        if low <= maturity_years < high:
            treasury_maturity = mat
            break

    # Get Treasury yield
    treasury_data = get_treasury_yields(treasury_maturity)
    treasury_yield = treasury_data['value'].iloc[-1]

    # Get comparable corporate spread
    rating_map = {
        'Aaa': 'aaa', 'Aa1': 'aa', 'Aa2': 'aa', 'Aa3': 'aa',
        'A1': 'a', 'A2': 'a', 'A3': 'a',
        'Baa1': 'bbb', 'Baa2': 'bbb', 'Baa3': 'bbb',
        'Ba1': 'bb', 'Ba2': 'bb', 'Ba3': 'bb',
        'B1': 'b', 'B2': 'b', 'B3': 'b'
    }

    corporate_category = rating_map.get(issuer_rating, 'bbb')
    corporate_spread_data = get_corporate_bond_spreads(corporate_category)
    market_spread = corporate_spread_data['value'].iloc[-1]

    # Calculate spreads
    spread_to_treasury = (issuer_yield - treasury_yield) * 100  # bps
    spread_to_market = spread_to_treasury - market_spread  # bps

    return {
        'issuer_yield': issuer_yield,
        'treasury_yield': treasury_yield,
        'treasury_maturity': treasury_maturity,
        'spread_to_treasury': spread_to_treasury,
        'market_spread': market_spread,
        'spread_to_market': spread_to_market,
        'interpretation': 'Tight' if spread_to_market < -10 else 'Wide' if spread_to_market > 10 else 'In-line'
    }


# Example usage
spread_analysis = calculate_issuer_credit_spread(
    issuer_yield=4.25,
    maturity_years=7,
    issuer_rating='A3'
)

print(spread_analysis)
```

---

## IV. Accessing Economic Data

### 4.1 GDP and Economic Growth

```python
def get_gdp_data(
    country: str = 'united_states',
    provider: str = 'fred'
) -> pd.DataFrame:
    """
    Get GDP data for economic context.

    Parameters:
    -----------
    country : str
        Country name
    provider : str
        Data provider

    Returns:
    --------
    pd.DataFrame : GDP data
    """
    # US Real GDP: GDPC1 (quarterly, seasonally adjusted annual rate)
    data = obb.economy.fred_series(
        symbol='GDPC1',
        provider='fred'
    )

    df = data.to_dataframe()

    # Calculate YoY growth
    df['gdp_growth_yoy'] = df['value'].pct_change(periods=4) * 100

    return df


# Example
gdp = get_gdp_data()
print(f"Latest GDP: ${gdp['value'].iloc[-1]:.1f}B")
print(f"YoY Growth: {gdp['gdp_growth_yoy'].iloc[-1]:.2f}%")
```

### 4.2 Inflation (CPI)

```python
def get_inflation_data(
    provider: str = 'fred'
) -> pd.DataFrame:
    """
    Get Consumer Price Index (CPI) data.
    """
    # CPI-U: All items (CPIAUCSL)
    data = obb.economy.fred_series(
        symbol='CPIAUCSL',
        provider='fred'
    )

    df = data.to_dataframe()

    # Calculate YoY inflation rate
    df['inflation_yoy'] = df['value'].pct_change(periods=12) * 100

    return df


# Example
cpi = get_inflation_data()
print(f"Latest CPI: {cpi['value'].iloc[-1]:.2f}")
print(f"YoY Inflation: {cpi['inflation_yoy'].iloc[-1]:.2f}%")
```

### 4.3 Unemployment Rate

```python
def get_unemployment_rate(
    provider: str = 'fred'
) -> pd.DataFrame:
    """
    Get unemployment rate data.
    """
    # Unemployment Rate (UNRATE)
    data = obb.economy.fred_series(
        symbol='UNRATE',
        provider='fred'
    )

    return data.to_dataframe()


# Example
unemployment = get_unemployment_rate()
print(f"Current unemployment: {unemployment['value'].iloc[-1]:.1f}%")
```

### 4.4 Federal Funds Rate

```python
def get_fed_funds_rate(
    provider: str = 'fred'
) -> pd.DataFrame:
    """
    Get Federal Funds effective rate.
    """
    # Effective Federal Funds Rate (FEDFUNDS)
    data = obb.economy.fred_series(
        symbol='FEDFUNDS',
        provider='fred'
    )

    return data.to_dataframe()


# Example
fed_funds = get_fed_funds_rate()
print(f"Current Fed Funds Rate: {fed_funds['value'].iloc[-1]:.2f}%")
```

---

## V. Peer Analysis with Live Data

### 5.1 Build Peer Comparison Table with Live Data

```python
def build_live_peer_comparison(
    issuer_ticker: str,
    peer_tickers: list,
    provider: str = 'fmp'
) -> pd.DataFrame:
    """
    Create comprehensive peer comparison using live market data.

    Parameters:
    -----------
    issuer_ticker : str
        Ticker of issuer being analyzed
    peer_tickers : list
        List of peer tickers
    provider : str
        Data provider

    Returns:
    --------
    pd.DataFrame : Peer comparison table
    """
    all_tickers = [issuer_ticker] + peer_tickers
    comparison_data = []

    for ticker in all_tickers:
        try:
            # Get quote
            quote = obb.equity.price.quote(symbol=ticker, provider=provider).to_dataframe()

            # Get metrics
            metrics = obb.equity.fundamental.metrics(symbol=ticker, provider=provider).to_dataframe()

            # Get latest financials
            income = get_reit_financials(ticker, 'income', 'annual', limit=1)
            balance = get_reit_financials(ticker, 'balance', 'annual', limit=1)

            # Extract key data
            row = {
                'Ticker': ticker,
                'Company': quote['name'].iloc[0] if 'name' in quote else ticker,
                'Price': quote['price'].iloc[0] if 'price' in quote else None,
                'Market Cap ($M)': quote['market_cap'].iloc[0] / 1e6 if 'market_cap' in quote else None,
                'Dividend Yield (%)': metrics['dividend_yield'].iloc[0] * 100 if 'dividend_yield' in metrics else None,
                'P/B': metrics['price_to_book'].iloc[0] if 'price_to_book' in metrics else None,
                'Total Assets ($M)': balance['total_assets'].iloc[0] / 1e6 if 'total_assets' in balance.columns else None,
                'Total Debt ($M)': balance['total_debt'].iloc[0] / 1e6 if 'total_debt' in balance.columns else None,
                'Revenue ($M)': income['revenue'].iloc[0] / 1e6 if 'revenue' in income.columns else None,
                'Net Income ($M)': income['net_income'].iloc[0] / 1e6 if 'net_income' in income.columns else None,
                'Is Issuer': ticker == issuer_ticker
            }

            # Calculate derived metrics
            if row['Total Debt ($M)'] and row['Total Assets ($M)']:
                row['Debt / Assets (%)'] = (row['Total Debt ($M)'] / row['Total Assets ($M)']) * 100

            comparison_data.append(row)

        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
            continue

    df = pd.DataFrame(comparison_data)

    # Highlight issuer row
    return df


# Example usage
peer_comp = build_live_peer_comparison(
    issuer_ticker='PLD',
    peer_tickers=['DRE', 'FR', 'REXR', 'EGP']  # Industrial REIT peers
)

print(peer_comp)
```

### 5.2 Trading Multiples Analysis

```python
def analyze_trading_multiples(
    issuer_ticker: str,
    peer_tickers: list
) -> dict:
    """
    Analyze issuer's trading multiples relative to peers.
    """
    peer_comp = build_live_peer_comparison(issuer_ticker, peer_tickers)

    # Calculate peer averages (excluding issuer)
    peer_data = peer_comp[peer_comp['Is Issuer'] == False]

    metrics = ['P/B', 'Dividend Yield (%)', 'Debt / Assets (%)']

    analysis = {}

    for metric in metrics:
        if metric in peer_data.columns:
            peer_avg = peer_data[metric].mean()
            peer_median = peer_data[metric].median()

            issuer_value = peer_comp[peer_comp['Is Issuer'] == True][metric].iloc[0]

            analysis[metric] = {
                'issuer': issuer_value,
                'peer_average': peer_avg,
                'peer_median': peer_median,
                'vs_average': issuer_value - peer_avg,
                'percentile': (peer_data[metric] < issuer_value).sum() / len(peer_data) * 100
            }

    return analysis


# Example
multiples_analysis = analyze_trading_multiples('PLD', ['DRE', 'FR', 'REXR', 'EGP'])

for metric, data in multiples_analysis.items():
    print(f"\n{metric}:")
    print(f"  Issuer: {data['issuer']:.2f}")
    print(f"  Peer Avg: {data['peer_average']:.2f}")
    print(f"  Percentile: {data['percentile']:.0f}th")
```

---

## VI. Market Context for Credit Reports

### 6.1 Generate Market Context Section

```python
def generate_market_context(
    issuer_rating: str,
    report_date: str = None
) -> dict:
    """
    Generate market context data for inclusion in credit report.

    Parameters:
    -----------
    issuer_rating : str
        Issuer's credit rating
    report_date : str
        Report date (defaults to today)

    Returns:
    --------
    dict : Market context data
    """
    from datetime import datetime

    if report_date is None:
        report_date = datetime.today().strftime('%Y-%m-%d')

    # Get key market indicators
    ten_year_treasury = get_treasury_yields('10y')['value'].iloc[-1]
    fed_funds = get_fed_funds_rate()['value'].iloc[-1]

    # Get credit spreads
    rating_category = 'bbb' if 'Baa' in issuer_rating else 'a' if 'A' in issuer_rating else 'bb'
    credit_spreads = get_corporate_bond_spreads(rating_category)['value'].iloc[-1]

    # Get economic indicators
    gdp = get_gdp_data()
    gdp_growth = gdp['gdp_growth_yoy'].iloc[-1]

    inflation = get_inflation_data()
    inflation_rate = inflation['inflation_yoy'].iloc[-1]

    unemployment = get_unemployment_rate()['value'].iloc[-1]

    context = {
        'report_date': report_date,
        'market_indicators': {
            '10Y_Treasury_Yield': round(ten_year_treasury, 2),
            'Fed_Funds_Rate': round(fed_funds, 2),
            f'{rating_category.upper()}_Spread': round(credit_spreads, 0),
            'GDP_Growth_YoY': round(gdp_growth, 2),
            'Inflation_YoY': round(inflation_rate, 2),
            'Unemployment_Rate': round(unemployment, 1)
        },
        'credit_market_assessment': 'Tight' if credit_spreads < 100 else 'Wide' if credit_spreads > 150 else 'Normal',
        'economic_outlook': 'Expansionary' if gdp_growth > 2.5 else 'Slowdown' if gdp_growth < 1.5 else 'Moderate'
    }

    return context


# Example
market_context = generate_market_context('A3')
print("Market Context:")
for key, value in market_context['market_indicators'].items():
    print(f"  {key}: {value}")

print(f"\nCredit Market: {market_context['credit_market_assessment']}")
print(f"Economic Outlook: {market_context['economic_outlook']}")
```

### 6.2 Embed Market Data in Report

```python
def create_market_context_section_text(context: dict) -> str:
    """
    Generate formatted text for market context section of report.
    """
    indicators = context['market_indicators']

    text = f"""
## Market Environment (as of {context['report_date']})

The credit analysis is conducted in the following market environment:

**Interest Rate Environment:**
- 10-Year US Treasury Yield: {indicators['10Y_Treasury_Yield']:.2f}%
- Federal Funds Rate: {indicators['Fed_Funds_Rate']:.2f}%

**Credit Markets:**
- Investment Grade Spreads: {indicators.get('BBB_Spread', indicators.get('A_Spread', 'N/A'))} bps
- Market Assessment: {context['credit_market_assessment']}

**Economic Backdrop:**
- GDP Growth (YoY): {indicators['GDP_Growth_YoY']:.1f}%
- Inflation Rate (YoY): {indicators['Inflation_YoY']:.1f}%
- Unemployment Rate: {indicators['Unemployment_Rate']:.1f}%
- Economic Outlook: {context['economic_outlook']}

This market context informs our assessment of the issuer's refinancing risk, cost of capital assumptions, and outlook for operating performance.
"""

    return text
```

---

## VII. Real-Time Data Workflow Integration

### 7.1 Enhanced Due Diligence Workflow with OpenBB

```python
def run_comprehensive_analysis_with_live_data(
    issuer_ticker: str,
    issuer_rating: str,
    peer_tickers: list,
    output_dir: str = './output'
) -> dict:
    """
    Complete analysis workflow integrating live market data.

    Parameters:
    -----------
    issuer_ticker : str
        Issuer ticker symbol
    issuer_rating : str
        Credit rating
    peer_tickers : list
        Peer ticker symbols
    output_dir : str
        Output directory for results

    Returns:
    --------
    dict : Complete analysis package
    """
    import os
    os.makedirs(output_dir, exist_ok=True)

    print("Fetching live market data...")

    # 1. Get issuer financial data
    print(f"  - Fetching {issuer_ticker} financials...")
    issuer_income = get_reit_financials(issuer_ticker, 'income', 'annual', limit=5)
    issuer_balance = get_reit_financials(issuer_ticker, 'balance', 'annual', limit=5)
    issuer_metrics = get_reit_metrics(issuer_ticker)

    # 2. Get peer comparison
    print("  - Building peer comparison...")
    peer_comparison = build_live_peer_comparison(issuer_ticker, peer_tickers)
    peer_comparison.to_csv(f'{output_dir}/peer_comparison.csv', index=False)

    # 3. Get market context
    print("  - Gathering market context...")
    market_context = generate_market_context(issuer_rating)

    # 4. Get current pricing and yields
    print("  - Fetching bond market data...")
    treasury_curve = get_treasury_yields()
    credit_spreads = {}
    for rating in ['aaa', 'bbb', 'bb']:
        credit_spreads[rating] = get_corporate_bond_spreads(rating)['value'].iloc[-1]

    # 5. Calculate valuation metrics
    print("  - Calculating valuation metrics...")
    valuation = get_reit_valuation_multiples(issuer_ticker)

    # 6. Trading multiples analysis
    print("  - Analyzing trading multiples...")
    multiples = analyze_trading_multiples(issuer_ticker, peer_tickers)

    # Package results
    results = {
        'issuer_ticker': issuer_ticker,
        'issuer_financials': {
            'income_statement': issuer_income,
            'balance_sheet': issuer_balance,
            'metrics': issuer_metrics
        },
        'valuation': valuation,
        'peer_comparison': peer_comparison,
        'multiples_analysis': multiples,
        'market_context': market_context,
        'treasury_curve': treasury_curve,
        'credit_spreads': credit_spreads
    }

    # Save summary
    with open(f'{output_dir}/market_data_summary.txt', 'w') as f:
        f.write(f"Live Market Data Summary - {issuer_ticker}\n")
        f.write("=" * 60 + "\n\n")
        f.write(create_market_context_section_text(market_context))
        f.write("\n\n")
        f.write(f"Valuation Metrics:\n")
        for key, val in valuation.items():
            f.write(f"  {key}: {val}\n")

    print(f"\nAnalysis complete. Results saved to {output_dir}/")

    return results


# Example usage
analysis_results = run_comprehensive_analysis_with_live_data(
    issuer_ticker='PLD',
    issuer_rating='A3',
    peer_tickers=['DRE', 'FR', 'REXR', 'EGP'],
    output_dir='./output/pld_analysis'
)
```

---

## VIII. Best Practices and Error Handling

### 8.1 Robust Data Fetching with Retries

```python
import time
from functools import wraps

def retry_on_failure(max_retries=3, delay=2):
    """
    Decorator to retry OpenBB API calls on failure.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        print(f"Failed after {max_retries} attempts: {e}")
                        raise
                    print(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                    time.sleep(delay)
        return wrapper
    return decorator


@retry_on_failure(max_retries=3)
def robust_get_financials(ticker, statement_type='income'):
    """
    Get financials with automatic retry on failure.
    """
    return get_reit_financials(ticker, statement_type)
```

### 8.2 Data Validation

```python
def validate_financial_data(df: pd.DataFrame, required_columns: list) -> bool:
    """
    Validate that financial data contains required columns.
    """
    missing = [col for col in required_columns if col not in df.columns]

    if missing:
        print(f"Warning: Missing columns: {missing}")
        return False

    return True


# Example usage
income_data = get_reit_financials('PLD', 'income')
is_valid = validate_financial_data(
    income_data,
    required_columns=['revenue', 'net_income', 'ebitda', 'total_assets']
)
```

### 8.3 Caching for Performance

```python
import pickle
from datetime import datetime, timedelta

class DataCache:
    """
    Simple cache for OpenBB data to reduce API calls.
    """
    def __init__(self, cache_file='openbb_cache.pkl', expiry_hours=24):
        self.cache_file = cache_file
        self.expiry = timedelta(hours=expiry_hours)
        self.cache = self._load_cache()

    def _load_cache(self):
        try:
            with open(self.cache_file, 'rb') as f:
                return pickle.load(f)
        except:
            return {}

    def _save_cache(self):
        with open(self.cache_file, 'wb') as f:
            pickle.dump(self.cache, f)

    def get(self, key):
        if key in self.cache:
            data, timestamp = self.cache[key]
            if datetime.now() - timestamp < self.expiry:
                return data
        return None

    def set(self, key, data):
        self.cache[key] = (data, datetime.now())
        self._save_cache()


# Usage
cache = DataCache()

def get_cached_financials(ticker, statement_type='income'):
    cache_key = f"{ticker}_{statement_type}"

    # Check cache
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        print(f"Using cached data for {ticker}")
        return cached_data

    # Fetch fresh data
    data = get_reit_financials(ticker, statement_type)

    # Cache it
    cache.set(cache_key, data)

    return data
```

---

## IX. Limitations and Considerations

### 9.1 Data Provider Limitations

**Free vs. Premium Data:**
- Free providers (Yahoo Finance, FRED) have rate limits
- Premium providers offer more comprehensive data but require paid API keys
- Some data may be delayed (15-20 minutes for free sources)

**Data Quality:**
- Always validate data against multiple sources when possible
- Be aware of restatements and data revisions
- Check for missing or null values

**API Rate Limits:**
- Respect provider rate limits to avoid being blocked
- Implement caching to reduce redundant calls
- Use retry logic with exponential backoff

### 9.2 Real-Time vs. Historical Context

**Important Caveats:**
- "Real-time" pricing may be delayed 15-20 minutes for free tiers
- Financial statements are historical (quarterly/annual filings)
- Economic indicators often have 1-2 month reporting lags
- Market sentiment can change rapidly

**Best Practices:**
- Timestamp all data pulls
- Note data vintage in reports ("as of [date]")
- Update key metrics regularly for active monitoring
- Use multiple data points to confirm trends

---

## X. Summary

### Key Capabilities Added with OpenBB Integration

✅ **Live REIT pricing and valuation multiples**
✅ **Automated peer comparison with current market data**
✅ **Real-time Treasury yields and credit spreads**
✅ **Current economic indicators (GDP, inflation, unemployment)**
✅ **Bond market context for refinancing risk assessment**
✅ **Trading multiples analysis relative to market**

### Integration Checklist

- [ ] Install OpenBB Platform (`pip install openbb[all]`)
- [ ] Configure API keys for desired providers
- [ ] Test basic data fetching (equity, fixed income, economy)
- [ ] Build peer comparison workflow
- [ ] Integrate market context into report template
- [ ] Set up data caching for performance
- [ ] Implement error handling and retries
- [ ] Document data sources and timestamps in reports

### Next Steps

1. **Enhance Calculation Library**: Add live data functions to `python_calculation_library.md`
2. **Update Workflow**: Integrate OpenBB calls into `report_generation_workflow.md`
3. **Visualization**: Create charts comparing issuer to real-time peer data
4. **Automation**: Schedule regular data pulls for ongoing monitoring
5. **Alerts**: Set up threshold alerts for material market changes

**With OpenBB integration, the Issuer Due Diligence Expert can now provide:**
- More timely and relevant credit analysis
- Better market contextualization
- Dynamic peer benchmarking
- Real-time refinancing cost estimates
- Current economic environment assessment

