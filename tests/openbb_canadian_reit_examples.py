#!/usr/bin/env python3
"""
OpenBB Platform - Canadian REIT Data Access Examples
Recommended patterns for retrieving dividend and financial data
"""

from openbb import obb
import pandas as pd
from datetime import datetime, timedelta

def example_1_dividend_history():
    """
    Example 1: Retrieve complete dividend history for a Canadian REIT
    Best for: Historical analysis, dividend growth calculations
    """
    print("\n" + "="*80)
    print("EXAMPLE 1: COMPLETE DIVIDEND HISTORY")
    print("="*80)

    ticker = 'REI-UN.TO'  # RioCan REIT (Yahoo Finance format)

    # Recommended: Use TMX for Canadian REITs (better metadata)
    result = obb.equity.fundamental.dividends(
        symbol=ticker,
        provider='tmx'
    )

    df = result.to_df()

    print(f"\nRetrieved {len(df)} dividend records for {ticker}")
    print(f"Date range: {df['ex_dividend_date'].min()} to {df['ex_dividend_date'].max()}")
    print(f"\nAvailable fields: {', '.join(df.columns)}")
    print(f"\nSample data:")
    print(df.head(10).to_string())

    # Calculate annual dividends
    df['year'] = pd.to_datetime(df['ex_dividend_date']).dt.year
    annual_divs = df.groupby('year')['amount'].sum()

    print(f"\n\nAnnual Dividends (2015-2025):")
    print(annual_divs[annual_divs.index >= 2015].to_string())

    return df

def example_2_recent_dividends():
    """
    Example 2: Get recent dividend payments (last 2 years)
    Best for: Current yield analysis, recent trends
    """
    print("\n" + "="*80)
    print("EXAMPLE 2: RECENT DIVIDEND PAYMENTS (Last 24 months)")
    print("="*80)

    tickers = ['REI-UN.TO', 'DIR-UN.TO', 'AX-UN.TO']
    reit_names = ['RioCan REIT', 'Dream Industrial REIT', 'Artis REIT']

    cutoff_date = datetime.now() - timedelta(days=730)  # 2 years

    for ticker, name in zip(tickers, reit_names):
        try:
            result = obb.equity.fundamental.dividends(
                symbol=ticker,
                provider='tmx'
            )

            df = result.to_df()
            df['ex_dividend_date'] = pd.to_datetime(df['ex_dividend_date'])

            # Filter last 24 months
            recent = df[df['ex_dividend_date'] >= cutoff_date]

            print(f"\n{name} ({ticker}):")
            print(f"  Payments (last 24 months): {len(recent)}")

            if len(recent) > 0:
                total_divs = recent['amount'].sum()
                avg_monthly = total_divs / 24
                print(f"  Total dividends: ${total_divs:.3f}")
                print(f"  Average monthly: ${avg_monthly:.3f}")

                # Show last 3 payments
                print(f"\n  Last 3 payments:")
                print(recent[['ex_dividend_date', 'amount', 'payment_date']].tail(3).to_string())

        except Exception as e:
            print(f"\n{name}: Error - {e}")

def example_3_price_data():
    """
    Example 3: Get historical price data for Canadian REITs
    Best for: NAV comparison, total return calculations
    """
    print("\n" + "="*80)
    print("EXAMPLE 3: HISTORICAL PRICE DATA (Last 90 days)")
    print("="*80)

    ticker = 'REI-UN.TO'
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')

    # Use TMX for Canadian data (includes VWAP, transactions)
    result = obb.equity.price.historical(
        symbol=ticker,
        start_date=start_date,
        end_date=end_date,
        provider='tmx'
    )

    df = result.to_df()

    print(f"\nTicker: {ticker}")
    print(f"Retrieved {len(df)} trading days")
    print(f"\nPrice Statistics:")
    print(df['close'].describe())

    print(f"\n\nRecent Trading Data (Last 10 days):")
    print(df[['close', 'volume', 'vwap', 'change_percent']].tail(10).to_string())

    # Calculate metrics
    current_price = df['close'].iloc[-1]
    avg_volume = df['volume'].mean()

    print(f"\n\nKey Metrics:")
    print(f"  Current Price: ${current_price:.2f}")
    print(f"  30-day Avg Volume: {avg_volume:,.0f}")
    print(f"  Price Range (90d): ${df['close'].min():.2f} - ${df['close'].max():.2f}")

    return df

def example_4_multi_reit_comparison():
    """
    Example 4: Compare dividend yields across multiple Canadian REITs
    Best for: Peer comparison, sector analysis
    """
    print("\n" + "="*80)
    print("EXAMPLE 4: MULTI-REIT DIVIDEND COMPARISON")
    print("="*80)

    reits = [
        {'ticker': 'REI-UN.TO', 'name': 'RioCan REIT'},
        {'ticker': 'DIR-UN.TO', 'name': 'Dream Industrial REIT'},
        {'ticker': 'AX-UN.TO', 'name': 'Artis REIT'}
    ]

    comparison_data = []

    for reit in reits:
        try:
            # Get dividends
            div_result = obb.equity.fundamental.dividends(
                symbol=reit['ticker'],
                provider='tmx'
            )
            div_df = div_result.to_df()
            div_df['ex_dividend_date'] = pd.to_datetime(div_df['ex_dividend_date'])

            # Get price
            price_result = obb.equity.price.historical(
                symbol=reit['ticker'],
                start_date=(datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
                provider='tmx'
            )
            price_df = price_result.to_df()
            current_price = price_df['close'].iloc[-1]

            # Calculate TTM dividends (last 12 months)
            cutoff = datetime.now() - timedelta(days=365)
            ttm_divs = div_df[div_df['ex_dividend_date'] >= cutoff]
            annual_dividend = ttm_divs['amount'].sum()
            dividend_yield = (annual_dividend / current_price) * 100

            comparison_data.append({
                'REIT': reit['name'],
                'Ticker': reit['ticker'],
                'Price': current_price,
                'Annual Div (TTM)': annual_dividend,
                'Yield %': dividend_yield,
                'Payments (12mo)': len(ttm_divs)
            })

        except Exception as e:
            print(f"Error processing {reit['name']}: {e}")

    # Display comparison
    if comparison_data:
        comp_df = pd.DataFrame(comparison_data)
        print("\n" + comp_df.to_string(index=False))

        print(f"\n\nSummary:")
        print(f"  Average Yield: {comp_df['Yield %'].mean():.2f}%")
        print(f"  Highest Yield: {comp_df.loc[comp_df['Yield %'].idxmax(), 'REIT']} ({comp_df['Yield %'].max():.2f}%)")

    return comparison_data

def example_5_data_export():
    """
    Example 5: Export dividend data to CSV for analysis
    Best for: Integration with external tools, Excel analysis
    """
    print("\n" + "="*80)
    print("EXAMPLE 5: EXPORT DIVIDEND DATA TO CSV")
    print("="*80)

    ticker = 'REI-UN.TO'
    output_file = '/workspaces/issuer-credit-analysis/tests/riocan_dividends.csv'

    # Get data
    result = obb.equity.fundamental.dividends(
        symbol=ticker,
        provider='tmx'
    )

    df = result.to_df()

    # Add calculated fields
    df['year'] = pd.to_datetime(df['ex_dividend_date']).dt.year
    df['month'] = pd.to_datetime(df['ex_dividend_date']).dt.month

    # Export
    df.to_csv(output_file, index=False)

    print(f"\nExported {len(df)} records to: {output_file}")
    print(f"\nColumns exported:")
    for col in df.columns:
        print(f"  - {col}")

    return output_file

def example_6_dividend_growth_analysis():
    """
    Example 6: Calculate dividend growth rates
    Best for: Credit analysis, sustainability assessment
    """
    print("\n" + "="*80)
    print("EXAMPLE 6: DIVIDEND GROWTH ANALYSIS")
    print("="*80)

    ticker = 'REI-UN.TO'

    # Get dividend history
    result = obb.equity.fundamental.dividends(
        symbol=ticker,
        provider='tmx'
    )

    df = result.to_df()
    df['ex_dividend_date'] = pd.to_datetime(df['ex_dividend_date'])
    df['year'] = df['ex_dividend_date'].dt.year

    # Calculate annual totals
    annual_divs = df.groupby('year')['amount'].sum().reset_index()
    annual_divs.columns = ['year', 'total_dividend']

    # Calculate year-over-year growth
    annual_divs['yoy_growth'] = annual_divs['total_dividend'].pct_change() * 100

    print(f"\nAnnual Dividend History (2015-2025):")
    recent = annual_divs[annual_divs['year'] >= 2015]
    print(recent.to_string(index=False))

    # Summary statistics
    avg_growth = recent['yoy_growth'].mean()
    print(f"\n\nGrowth Statistics (2015-2025):")
    print(f"  Average YoY Growth: {avg_growth:.2f}%")
    print(f"  Best Year: {recent.loc[recent['yoy_growth'].idxmax(), 'year']:.0f} ({recent['yoy_growth'].max():.2f}%)")
    print(f"  Worst Year: {recent.loc[recent['yoy_growth'].idxmin(), 'year']:.0f} ({recent['yoy_growth'].min():.2f}%)")

    # Identify cuts/increases
    cuts = recent[recent['yoy_growth'] < 0]
    if len(cuts) > 0:
        print(f"\n  Years with dividend cuts: {len(cuts)}")
        print(cuts[['year', 'total_dividend', 'yoy_growth']].to_string(index=False))

    return annual_divs

def main():
    """Run all examples"""
    print("\n" + "="*80)
    print("OPENBB PLATFORM - CANADIAN REIT DATA ACCESS EXAMPLES")
    print("="*80)
    print("\nThese examples demonstrate recommended patterns for accessing")
    print("Canadian REIT data using the OpenBB Platform")

    # Run examples
    example_1_dividend_history()
    example_2_recent_dividends()
    example_3_price_data()
    example_4_multi_reit_comparison()
    example_5_data_export()
    example_6_dividend_growth_analysis()

    print("\n" + "="*80)
    print("ALL EXAMPLES COMPLETE")
    print("="*80)
    print("\nKey Takeaways:")
    print("  - Use 'REI-UN.TO' format for Yahoo Finance provider")
    print("  - Use 'REI.UN' or 'REI-UN.TO' for TMX provider")
    print("  - TMX provider offers more metadata (payment dates, currency, etc.)")
    print("  - YFinance has longer history (back to 1996 vs 2009)")
    print("  - Both providers are free (no API key required)")
    print("  - TMX is recommended for Canadian REITs (native data source)")

if __name__ == "__main__":
    main()
