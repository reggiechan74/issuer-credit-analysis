#!/usr/bin/env python3
"""
Test different ticker formats for Canadian REITs with OpenBB
Tests which format works best: REI-UN.TO, REI.UN, REI-UN, etc.
"""

from openbb import obb
from datetime import datetime, timedelta

def test_ticker_formats():
    """Test various ticker symbol formats"""
    print("\n" + "="*80)
    print("TESTING CANADIAN REIT TICKER FORMATS")
    print("="*80)

    # RioCan REIT ticker variations
    test_cases = [
        {
            'name': 'RioCan REIT',
            'formats': [
                'REI-UN.TO',   # Yahoo Finance format
                'REI.UN',      # TSX format
                'REI-UN',      # Alternate format
                'REI.UN.TO',   # Alternate format
            ]
        },
        {
            'name': 'Dream Industrial REIT',
            'formats': [
                'DIR-UN.TO',
                'DIR.UN',
                'DIR-UN',
                'DIR.UN.TO',
            ]
        }
    ]

    for test_case in test_cases:
        print(f"\n{test_case['name']}")
        print("-" * 80)

        for ticker in test_case['formats']:
            print(f"\n  Ticker format: {ticker}")

            # Test with TMX provider (free)
            try:
                result = obb.equity.fundamental.dividends(
                    symbol=ticker,
                    provider='tmx'
                )

                if hasattr(result, 'results') and result.results:
                    df = result.to_df()
                    print(f"    ✓ TMX: {len(df)} records")
                else:
                    print(f"    ⚠ TMX: No data")
            except Exception as e:
                print(f"    ✗ TMX: {str(e)[:80]}")

            # Test with yfinance provider (free)
            try:
                result = obb.equity.fundamental.dividends(
                    symbol=ticker,
                    provider='yfinance'
                )

                if hasattr(result, 'results') and result.results:
                    df = result.to_df()
                    print(f"    ✓ YFinance: {len(df)} records")
                else:
                    print(f"    ⚠ YFinance: No data")
            except Exception as e:
                print(f"    ✗ YFinance: {str(e)[:80]}")

def test_dividend_date_range():
    """Test historical dividend data with date filtering"""
    print("\n" + "="*80)
    print("TESTING DIVIDEND DATA WITH DATE RANGES")
    print("="*80)

    ticker = 'REI-UN.TO'
    start_date = '2015-01-01'
    end_date = '2025-12-31'

    print(f"\nTicker: {ticker}")
    print(f"Date range: {start_date} to {end_date}")

    # TMX Provider
    try:
        print("\n  TMX Provider:")
        result = obb.equity.fundamental.dividends(
            symbol=ticker,
            provider='tmx',
            start_date=start_date,
            end_date=end_date
        )

        if hasattr(result, 'results') and result.results:
            df = result.to_df()
            print(f"    ✓ Retrieved {len(df)} records")

            # Analyze data
            if 'ex_dividend_date' in df.columns:
                dates = df['ex_dividend_date']
                print(f"    Date range: {dates.min()} to {dates.max()}")

                # Annual dividend calculation
                df['year'] = df['ex_dividend_date'].dt.year
                annual_divs = df.groupby('year')['amount'].sum()
                print(f"\n    Annual dividends by year:")
                for year, total in annual_divs.items():
                    if 2015 <= year <= 2025:
                        print(f"      {year}: ${total:.3f}")

    except Exception as e:
        print(f"    ✗ Error: {e}")

    # YFinance Provider
    try:
        print("\n  YFinance Provider:")
        result = obb.equity.fundamental.dividends(
            symbol=ticker,
            provider='yfinance'
        )

        if hasattr(result, 'results') and result.results:
            df = result.to_df()

            # Filter by date range
            df_filtered = df[
                (df['ex_dividend_date'] >= start_date) &
                (df['ex_dividend_date'] <= end_date)
            ]

            print(f"    ✓ Retrieved {len(df_filtered)} records in date range")
            print(f"    Total records available: {len(df)}")

            if len(df_filtered) > 0:
                dates = df_filtered['ex_dividend_date']
                print(f"    Date range: {dates.min()} to {dates.max()}")

    except Exception as e:
        print(f"    ✗ Error: {e}")

def test_data_quality_comparison():
    """Compare data quality between TMX and YFinance"""
    print("\n" + "="*80)
    print("DATA QUALITY COMPARISON: TMX vs YFinance")
    print("="*80)

    ticker = 'REI-UN.TO'
    print(f"\nTicker: {ticker}")

    data_tmx = None
    data_yf = None

    # Get TMX data
    try:
        result = obb.equity.fundamental.dividends(
            symbol=ticker,
            provider='tmx'
        )
        if hasattr(result, 'results') and result.results:
            data_tmx = result.to_df()
    except Exception as e:
        print(f"TMX Error: {e}")

    # Get YFinance data
    try:
        result = obb.equity.fundamental.dividends(
            symbol=ticker,
            provider='yfinance'
        )
        if hasattr(result, 'results') and result.results:
            data_yf = result.to_df()
    except Exception as e:
        print(f"YFinance Error: {e}")

    # Compare
    if data_tmx is not None and data_yf is not None:
        print(f"\nRecord Count:")
        print(f"  TMX: {len(data_tmx)} records")
        print(f"  YFinance: {len(data_yf)} records")

        print(f"\nFields Available:")
        print(f"  TMX: {', '.join(data_tmx.columns)}")
        print(f"  YFinance: {', '.join(data_yf.columns)}")

        print(f"\nDate Range:")
        if 'ex_dividend_date' in data_tmx.columns:
            tmx_dates = data_tmx['ex_dividend_date']
            print(f"  TMX: {tmx_dates.min()} to {tmx_dates.max()}")
        if 'ex_dividend_date' in data_yf.columns:
            yf_dates = data_yf['ex_dividend_date']
            print(f"  YFinance: {yf_dates.min()} to {yf_dates.max()}")

        # Compare recent data
        print(f"\nRecent Data (Last 5 records):")
        print(f"\n  TMX:")
        if len(data_tmx) > 0:
            print(data_tmx[['ex_dividend_date', 'amount', 'payment_date']].tail(5).to_string())

        print(f"\n  YFinance:")
        if len(data_yf) > 0:
            print(data_yf[['ex_dividend_date', 'amount']].tail(5).to_string())

def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("OPENBB - CANADIAN REIT TICKER FORMAT & DATA QUALITY TESTS")
    print("="*80)

    test_ticker_formats()
    test_dividend_date_range()
    test_data_quality_comparison()

    print("\n" + "="*80)
    print("ALL TESTS COMPLETE")
    print("="*80)

if __name__ == "__main__":
    main()
