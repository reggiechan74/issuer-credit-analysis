#!/usr/bin/env python3
"""
Merge fundamentals, market, and macro data into final training dataset.

Combines:
1. Fundamentals from Phase 3 (33 features)
2. Market data from OpenBB (15 features)
3. Macro data from OpenBB (8 features)

Output: Training dataset with ~56 features for model training.

Usage:
    python scripts/merge_training_dataset.py \
        --fundamentals data/fundamentals_dataset_phase1b.csv \
        --market-dir data/market \
        --macro-dir data/macro \
        --output data/training_dataset_v2_phase1b.csv
"""

import argparse
import csv
import json
from pathlib import Path
from datetime import datetime

def load_market_data(obs_num, market_dir):
    """Load market data for an observation."""
    market_file = Path(market_dir) / f"obs{obs_num:02d}_market.json"
    
    if not market_file.exists():
        print(f"  ⚠️  Market data not found: {market_file}")
        return {}
    
    with open(market_file, 'r') as f:
        data = json.load(f)
    
    # Flatten nested structure
    features = {
        # Price stress
        'mkt_price_stress_decline_pct': data.get('price_stress', {}).get('decline_from_peak_pct', None),
        'mkt_price_stress_level': data.get('price_stress', {}).get('stress_level', None),
        'mkt_price_52w_high': data.get('price_stress', {}).get('high_52w', None),
        'mkt_price_52w_low': data.get('price_stress', {}).get('low_52w', None),
        'mkt_price_current': data.get('price_stress', {}).get('current_price', None),
        
        # Volatility
        'mkt_volatility_30d_pct': data.get('volatility', {}).get('metrics', {}).get('30d', {}).get('volatility_annualized_pct', None),
        'mkt_volatility_90d_pct': data.get('volatility', {}).get('metrics', {}).get('90d', {}).get('volatility_annualized_pct', None),
        'mkt_volatility_252d_pct': data.get('volatility', {}).get('metrics', {}).get('252d', {}).get('volatility_annualized_pct', None),
        'mkt_volatility_classification': data.get('volatility', {}).get('classification', None),
        
        # Momentum
        'mkt_momentum_3m_pct': data.get('momentum', {}).get('metrics', {}).get('3_month', {}).get('total_return_pct', None),
        'mkt_momentum_6m_pct': data.get('momentum', {}).get('metrics', {}).get('6_month', {}).get('total_return_pct', None),
        'mkt_momentum_12m_pct': data.get('momentum', {}).get('metrics', {}).get('12_month', {}).get('total_return_pct', None),
        'mkt_momentum_trend': data.get('momentum', {}).get('trend', None),
        
        # Volume
        'mkt_volume_30d_avg': data.get('volume', {}).get('metrics', {}).get('30d', {}).get('avg_daily_volume', None),
        'mkt_volume_vs_avg': data.get('volume', {}).get('volume_vs_30d_avg', None),
        
        # Risk score
        'mkt_risk_score': data.get('risk_score', {}).get('total_score', None),
        'mkt_risk_level': data.get('risk_score', {}).get('risk_level', None),
    }
    
    return features

def load_macro_data(date, macro_dir):
    """Load macro data for a specific date."""
    # Convert date format: 2022-12-31 -> 2022_12_31
    date_str = date.replace('-', '_')
    macro_file = Path(macro_dir) / f"{date_str}_macro.json"
    
    if not macro_file.exists():
        print(f"  ⚠️  Macro data not found: {macro_file}")
        return {}
    
    with open(macro_file, 'r') as f:
        data = json.load(f)
    
    # Flatten structure
    features = {
        # Canada
        'macro_ca_policy_rate': data.get('canada', {}).get('policy_rate', {}).get('current_rate', None),
        'macro_ca_rate_change_12m_bps': data.get('canada', {}).get('policy_rate', {}).get('change_12m_bps', None),
        'macro_ca_rate_cycle': data.get('canada', {}).get('policy_rate', {}).get('cycle', None),
        'macro_ca_credit_stress_score': data.get('canada', {}).get('credit_stress_score', None),
        'macro_ca_credit_environment': data.get('canada', {}).get('credit_environment', None),
        
        # US
        'macro_us_policy_rate': data.get('united_states', {}).get('policy_rate', {}).get('current_rate', None),
        'macro_us_rate_change_12m_bps': data.get('united_states', {}).get('policy_rate', {}).get('change_12m_bps', None),
        'macro_us_rate_cycle': data.get('united_states', {}).get('policy_rate', {}).get('cycle', None),
        
        # Rate differential
        'macro_rate_diff_ca_us_bps': data.get('rate_differential', {}).get('ca_minus_us_bps', None),
    }
    
    return features

def merge_datasets(fundamentals_file, market_dir, macro_dir, output_file):
    """Merge all datasets into final training dataset."""
    
    print("="*70)
    print("Training Dataset Merge")
    print("="*70)
    
    # Read fundamentals
    print(f"\n📂 Loading fundamentals from: {fundamentals_file}")
    with open(fundamentals_file, 'r') as f:
        reader = csv.DictReader(f)
        fundamentals = list(reader)
    print(f"✓ Loaded {len(fundamentals)} observations")
    
    # Merge market and macro data
    print(f"\n🔗 Merging market and macro data...")
    merged_data = []
    
    for row in fundamentals:
        obs_num = int(row['observation'])
        date = row['reporting_date']
        issuer = row['issuer_name']
        
        print(f"\n  Obs {obs_num:2d}: {issuer[:30]:30s} @ {date}")
        
        # Load market data
        market_features = load_market_data(obs_num, market_dir)
        print(f"    ✓ Market features: {len([v for v in market_features.values() if v is not None])}/{len(market_features)}")
        
        # Load macro data
        macro_features = load_macro_data(date, macro_dir)
        print(f"    ✓ Macro features: {len([v for v in macro_features.values() if v is not None])}/{len(macro_features)}")
        
        # Merge all features
        merged_row = {**row, **market_features, **macro_features}
        merged_data.append(merged_row)
    
    # Write merged dataset
    print(f"\n💾 Writing merged dataset to: {output_file}")
    
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if merged_data:
        fieldnames = list(merged_data[0].keys())
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(merged_data)
        
        print(f"✓ Wrote {len(merged_data)} observations")
        print(f"✓ Total features: {len(fieldnames)}")
        
        # Feature breakdown
        fundamental_count = 33  # From Phase 3
        market_count = len([k for k in fieldnames if k.startswith('mkt_')])
        macro_count = len([k for k in fieldnames if k.startswith('macro_')])
        metadata_count = len(fieldnames) - fundamental_count - market_count - macro_count
        
        print(f"\n📊 Feature Breakdown:")
        print(f"  • Metadata: {metadata_count}")
        print(f"  • Fundamentals: {fundamental_count}")
        print(f"  • Market: {market_count}")
        print(f"  • Macro: {macro_count}")
        print(f"  • TOTAL: {len(fieldnames)}")
        
        print(f"\n🎉 SUCCESS! Training dataset ready.")
        print(f"\nNext step: Train model")
        print(f"  python scripts/train_distribution_cut_model.py \\")
        print(f"    --input {output_file} \\")
        print(f"    --output models/distribution_cut_v2_phase1b.pkl")
        
        return 0
    else:
        print("❌ No data to write")
        return 1

def main():
    parser = argparse.ArgumentParser(description='Merge fundamentals, market, and macro datasets')
    parser.add_argument('--fundamentals', default='data/fundamentals_dataset_phase1b.csv',
                       help='Fundamentals CSV file')
    parser.add_argument('--market-dir', default='data/market',
                       help='Directory containing market JSON files')
    parser.add_argument('--macro-dir', default='data/macro',
                       help='Directory containing macro JSON files')
    parser.add_argument('--output', default='data/training_dataset_v2_phase1b.csv',
                       help='Output training dataset CSV')
    
    args = parser.parse_args()
    
    return merge_datasets(args.fundamentals, args.market_dir, args.macro_dir, args.output)

if __name__ == '__main__':
    exit(main())
