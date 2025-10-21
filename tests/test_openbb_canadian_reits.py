#!/usr/bin/env python3
"""
Test OpenBB Platform capabilities with Canadian REITs
Tests dividend data, financial statements, and price data retrieval
"""

import sys
from datetime import datetime, timedelta

def test_openbb_import():
    """Test OpenBB import and initialization"""
    try:
        from openbb import obb
        print("✓ OpenBB Platform imported successfully")
        return obb
    except ImportError as e:
        print(f"✗ Failed to import OpenBB: {e}")
        return None

def test_dividend_data(obb, symbols):
    """Test dividend data retrieval for Canadian REITs"""
    print("\n" + "="*80)
    print("TESTING DIVIDEND DATA RETRIEVAL")
    print("="*80)

    providers = ['tmx', 'yfinance', 'fmp', 'nasdaq']

    for symbol in symbols:
        print(f"\n📊 Testing {symbol['name']} ({symbol['ticker']})")
        print("-" * 80)

        for provider in providers:
            try:
                print(f"\n  Provider: {provider}")

                # Try retrieving dividend data
                result = obb.equity.fundamental.dividends(
                    symbol=symbol['ticker'],
                    provider=provider
                )

                if hasattr(result, 'results') and result.results:
                    df = result.to_df()
                    print(f"  ✓ Retrieved {len(df)} dividend records")

                    # Show first 3 and last 3 records
                    if len(df) > 0:
                        print(f"\n  Sample data (first 3 records):")
                        print(df.head(3).to_string())

                        # Show data range
                        if 'ex_dividend_date' in df.columns:
                            dates = df['ex_dividend_date'].dropna()
                            if len(dates) > 0:
                                print(f"\n  Date range: {dates.min()} to {dates.max()}")

                        # Show available columns
                        print(f"\n  Available fields: {', '.join(df.columns)}")
                else:
                    print(f"  ⚠ No dividend data returned")

            except Exception as e:
                print(f"  ✗ Error with {provider}: {str(e)[:100]}")

def test_financial_statements(obb, symbols):
    """Test financial statement retrieval"""
    print("\n" + "="*80)
    print("TESTING FINANCIAL STATEMENTS")
    print("="*80)

    providers = ['tmx', 'yfinance', 'fmp']
    statements = [
        ('balance', 'Balance Sheet'),
        ('income', 'Income Statement'),
        ('cash', 'Cash Flow Statement')
    ]

    # Test with first symbol only to save time
    symbol = symbols[0]
    print(f"\n📊 Testing {symbol['name']} ({symbol['ticker']})")

    for provider in providers:
        print(f"\n  Provider: {provider}")
        print("  " + "-" * 76)

        for stmt_func, stmt_name in statements:
            try:
                func = getattr(obb.equity.fundamental, stmt_func)
                result = func(
                    symbol=symbol['ticker'],
                    period='quarterly',
                    limit=4,
                    provider=provider
                )

                if hasattr(result, 'results') and result.results:
                    df = result.to_df()
                    print(f"  ✓ {stmt_name}: {len(df)} periods, {len(df.columns)} fields")
                else:
                    print(f"  ⚠ {stmt_name}: No data")

            except Exception as e:
                print(f"  ✗ {stmt_name}: {str(e)[:80]}")

def test_price_data(obb, symbols):
    """Test historical price data retrieval"""
    print("\n" + "="*80)
    print("TESTING HISTORICAL PRICE DATA")
    print("="*80)

    providers = ['tmx', 'yfinance', 'fmp']

    # Test with first symbol
    symbol = symbols[0]
    print(f"\n📊 Testing {symbol['name']} ({symbol['ticker']})")

    # Get last 30 days
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

    for provider in providers:
        try:
            print(f"\n  Provider: {provider}")

            result = obb.equity.price.historical(
                symbol=symbol['ticker'],
                start_date=start_date,
                end_date=end_date,
                provider=provider
            )

            if hasattr(result, 'results') and result.results:
                df = result.to_df()
                print(f"  ✓ Retrieved {len(df)} price records")
                print(f"  Fields: {', '.join(df.columns)}")

                # Show recent prices
                if len(df) > 0:
                    print(f"\n  Recent prices (last 3 days):")
                    print(df.tail(3)[['close', 'volume']].to_string())
            else:
                print(f"  ⚠ No price data returned")

        except Exception as e:
            print(f"  ✗ Error: {str(e)[:100]}")

def test_company_info(obb, symbols):
    """Test company profile/info retrieval"""
    print("\n" + "="*80)
    print("TESTING COMPANY INFORMATION")
    print("="*80)

    providers = ['tmx', 'yfinance', 'fmp']

    symbol = symbols[0]
    print(f"\n📊 Testing {symbol['name']} ({symbol['ticker']})")

    for provider in providers:
        try:
            print(f"\n  Provider: {provider}")

            result = obb.equity.profile(
                symbol=symbol['ticker'],
                provider=provider
            )

            if hasattr(result, 'results') and result.results:
                data = result.results[0] if isinstance(result.results, list) else result.results
                print(f"  ✓ Company profile retrieved")

                # Show key fields if available
                if hasattr(data, 'name'):
                    print(f"  Name: {data.name}")
                if hasattr(data, 'sector'):
                    print(f"  Sector: {data.sector}")
                if hasattr(data, 'market_cap'):
                    print(f"  Market Cap: {data.market_cap}")
            else:
                print(f"  ⚠ No profile data returned")

        except Exception as e:
            print(f"  ✗ Error: {str(e)[:100]}")

def main():
    """Main test runner"""
    print("\n" + "="*80)
    print("OPENBB PLATFORM - CANADIAN REIT DATA TESTING")
    print("="*80)

    # Initialize OpenBB
    obb = test_openbb_import()
    if not obb:
        print("\n✗ Cannot proceed without OpenBB")
        sys.exit(1)

    # Define Canadian REIT symbols to test
    symbols = [
        {
            'name': 'RioCan REIT',
            'ticker': 'REI-UN.TO',  # Yahoo Finance format
            'tsx_ticker': 'REI.UN'
        },
        {
            'name': 'Dream Industrial REIT',
            'ticker': 'DIR-UN.TO',
            'tsx_ticker': 'DIR.UN'
        },
        {
            'name': 'Artis REIT',
            'ticker': 'AX-UN.TO',
            'tsx_ticker': 'AX.UN'
        }
    ]

    print(f"\nTesting with {len(symbols)} Canadian REITs:")
    for s in symbols:
        print(f"  - {s['name']} ({s['ticker']} / {s['tsx_ticker']})")

    # Run tests
    try:
        test_dividend_data(obb, symbols)
        test_financial_statements(obb, symbols)
        test_price_data(obb, symbols)
        test_company_info(obb, symbols)

        print("\n" + "="*80)
        print("TESTING COMPLETE")
        print("="*80)

    except Exception as e:
        print(f"\n✗ Fatal error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
