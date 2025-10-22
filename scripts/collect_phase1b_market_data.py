#!/usr/bin/env python3
"""
Automated market and macro data collection for Phase 1B observations.

Reads ticker mapping config and collects:
1. Market data for each observation (19 API calls)
2. Macro data for unique dates (8 API calls)

Usage:
    python scripts/collect_phase1b_market_data.py
"""

import yaml
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime

def load_ticker_mapping(config_file='data/phase1b_ticker_mapping.yaml'):
    """Load ticker mapping configuration."""
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    return config

def collect_market_data(obs_num, ticker, date, output_dir='data/market'):
    """Collect market data for a single observation."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / f"obs{obs_num:02d}_market.json"
    
    print(f"\n{'='*60}")
    print(f"Obs {obs_num:2d}: {ticker} @ {date}")
    print(f"{'='*60}")
    
    # Run openbb_market_monitor.py
    cmd = [
        'python', 'scripts/openbb_market_monitor.py',
        '--ticker', ticker,
        '--output', str(output_file)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print(f"✓ Market data saved to: {output_file}")
            return True
        else:
            print(f"❌ Error collecting market data:")
            print(result.stderr)
            return False
    except subprocess.TimeoutExpired:
        print(f"❌ Timeout collecting market data")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def collect_macro_data(date, output_dir='data/macro'):
    """Collect macro data for a specific date."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Format date for filename
    date_str = date.replace('-', '_')
    output_file = output_dir / f"{date_str}_macro.json"
    
    print(f"\n{'='*60}")
    print(f"Macro data for: {date}")
    print(f"{'='*60}")
    
    # Run openbb_macro_monitor.py
    cmd = [
        'python', 'scripts/openbb_macro_monitor.py',
        '--output', str(output_file)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print(f"✓ Macro data saved to: {output_file}")
            return True
        else:
            print(f"❌ Error collecting macro data:")
            print(result.stderr)
            return False
    except subprocess.TimeoutExpired:
        print(f"❌ Timeout collecting macro data")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("="*70)
    print("Phase 1B Market & Macro Data Collection")
    print("="*70)
    
    # Load configuration
    print("\n📂 Loading ticker mapping...")
    config = load_ticker_mapping()
    observations = config['observations']
    
    print(f"✓ Loaded {len(observations)} observations")
    
    # Extract unique dates
    unique_dates = sorted(set(obs['date'] for obs in observations.values()))
    print(f"✓ Found {len(unique_dates)} unique dates")
    
    # Collect market data for each observation
    print(f"\n{'='*70}")
    print(f"STEP 1: Collecting Market Data ({len(observations)} observations)")
    print(f"{'='*70}")
    
    market_success = 0
    market_failed = []
    
    for obs_num in sorted(observations.keys()):
        obs = observations[obs_num]
        ticker = obs['ticker']
        date = obs['date']
        
        if ticker == "UNKNOWN":
            print(f"\n⚠️  Obs {obs_num}: Skipping (unknown ticker)")
            market_failed.append(obs_num)
            continue
        
        success = collect_market_data(obs_num, ticker, date)
        if success:
            market_success += 1
        else:
            market_failed.append(obs_num)
    
    # Collect macro data for unique dates
    print(f"\n{'='*70}")
    print(f"STEP 2: Collecting Macro Data ({len(unique_dates)} unique dates)")
    print(f"{'='*70}")
    
    macro_success = 0
    macro_failed = []
    
    for date in unique_dates:
        success = collect_macro_data(date)
        if success:
            macro_success += 1
        else:
            macro_failed.append(date)
    
    # Summary
    print(f"\n{'='*70}")
    print("COLLECTION SUMMARY")
    print(f"{'='*70}")
    print(f"\nMarket Data:")
    print(f"  ✓ Successful: {market_success}/{len(observations)}")
    if market_failed:
        print(f"  ❌ Failed: {market_failed}")
    
    print(f"\nMacro Data:")
    print(f"  ✓ Successful: {macro_success}/{len(unique_dates)}")
    if macro_failed:
        print(f"  ❌ Failed: {macro_failed}")
    
    # Check if we can proceed
    if market_success == len(observations) and macro_success == len(unique_dates):
        print(f"\n🎉 SUCCESS! All data collected.")
        print(f"\nNext step: Run merge script")
        print(f"  python scripts/merge_training_dataset.py")
        return 0
    else:
        print(f"\n⚠️  Some data collection failed. Review errors above.")
        return 1

if __name__ == '__main__':
    exit(main())
