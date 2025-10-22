#!/usr/bin/env python3
"""
Enhanced Macro Monitor - Bank of Canada + US Fed (FRED)

Combines Canadian rates (Bank of Canada Valet API) with US rates (FRED)
to provide comprehensive North American interest rate context.

Usage:
    python scripts/openbb_macro_monitor_enhanced.py --output data/macro_enhanced.json
"""

import requests
import pandas as pd
import json
from datetime import datetime, timedelta
from pathlib import Path
from openbb import obb

class EnhancedMacroMonitor:
    """Monitor both Canadian and US interest rates."""
    
    def __init__(self):
        self.boc_url = "https://www.bankofcanada.ca/valet/observations"
    
    def get_boc_rate(self, months=120):
        """Get Bank of Canada overnight rate."""
        start = (datetime.now() - timedelta(days=months*30)).strftime('%Y-%m-%d')
        url = f"{self.boc_url}/V122530/json?start_date={start}"
        data = requests.get(url, timeout=30).json()
        
        records = []
        for obs in data.get('observations', []):
            if obs.get('d') and obs.get('V122530', {}).get('v'):
                records.append({
                    'date': pd.to_datetime(obs['d']),
                    'rate': float(obs['V122530']['v'])
                })
        return pd.DataFrame(records).sort_values('date')
    
    def get_us_fed_rate(self, months=120):
        """Get US Federal Funds Rate from FRED."""
        start_date = (datetime.now() - timedelta(days=months*30)).strftime('%Y-%m-%d')
        
        try:
            result = obb.economy.fred_series(
                symbol='FEDFUNDS',
                start_date=start_date,
                provider='fred'
            )
            
            df = result.to_df()
            if df.empty:
                return pd.DataFrame()
            
            # Reset index to get date column
            df = df.reset_index()
            df = df.rename(columns={'FEDFUNDS': 'rate'})
            df['date'] = pd.to_datetime(df['date'])
            
            return df.sort_values('date')
            
        except Exception as e:
            print(f"WARNING: Could not retrieve US Fed data: {e}")
            return pd.DataFrame()
    
    def analyze_rate_cycle(self, df, label="Rate"):
        """Analyze rate cycle for any country."""
        if df.empty:
            return {}
        
        current_rate = df['rate'].iloc[-1]
        current_date = df['date'].iloc[-1]
        
        # 12-month comparison
        date_12m_ago = current_date - timedelta(days=365)
        past_df = df[df['date'] <= date_12m_ago]
        past_rate = past_df['rate'].iloc[-1] if not past_df.empty else df['rate'].iloc[0]
        
        change = current_rate - past_rate
        change_bps = change * 100
        
        # Classify cycle
        if abs(change) < 0.25:
            cycle = "STABLE"
        elif change >= 2.0:
            cycle = "AGGRESSIVE TIGHTENING"
        elif change >= 1.0:
            cycle = "TIGHTENING"
        elif change >= 0.25:
            cycle = "MILD TIGHTENING"
        elif change <= -2.0:
            cycle = "AGGRESSIVE EASING"
        elif change <= -1.0:
            cycle = "EASING"
        else:
            cycle = "MILD EASING"
        
        return {
            'current_rate': round(current_rate, 2),
            'past_rate_12m': round(past_rate, 2),
            'change_12m_pct': round(change, 2),
            'change_12m_bps': round(change_bps, 0),
            'cycle': cycle,
            'max_rate': round(df['rate'].max(), 2),
            'min_rate': round(df['rate'].min(), 2),
            'observations': len(df)
        }
    
    def generate_assessment(self, lookback=120):
        """Generate comprehensive Canada + US rate assessment."""
        print("Analyzing North American interest rate environment...")
        
        # Get Canadian rates
        ca_df = self.get_boc_rate(lookback)
        print(f"✓ Bank of Canada: {len(ca_df)} observations")
        ca_analysis = self.analyze_rate_cycle(ca_df, "Canada")
        
        # Get US rates
        us_df = self.get_us_fed_rate(lookback)
        if not us_df.empty:
            print(f"✓ US Federal Reserve: {len(us_df)} observations")
            us_analysis = self.analyze_rate_cycle(us_df, "United States")
        else:
            us_analysis = None
        
        # Calculate spread
        spread = None
        if us_analysis:
            spread = ca_analysis['current_rate'] - us_analysis['current_rate']
        
        # Credit environment scoring
        ca_rate = ca_analysis['current_rate']
        rate_stress = min(40, int(ca_rate / 5.0 * 40))
        
        cycle_stress = 0
        if 'TIGHTENING' in ca_analysis['cycle']:
            cycle_stress = 30
        elif ca_analysis['cycle'] == 'STABLE':
            cycle_stress = 5
        
        stress_score = rate_stress + cycle_stress
        
        if stress_score >= 70:
            environment = "VERY TIGHT"
        elif stress_score >= 50:
            environment = "TIGHT"
        elif stress_score >= 30:
            environment = "MODERATE"
        else:
            environment = "ACCOMMODATIVE"
        
        assessment = {
            'assessment_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'canada': {
                'data_source': 'Bank of Canada Valet API',
                'policy_rate': ca_analysis,
                'credit_stress_score': stress_score,
                'credit_environment': environment
            },
            'united_states': {
                'data_source': 'FRED (Federal Reserve Economic Data)',
                'policy_rate': us_analysis
            } if us_analysis else None,
            'rate_differential': {
                'ca_minus_us_bps': round(spread * 100, 0) if spread is not None else None,
                'note': 'Negative = Canada below US (typical), Positive = Canada above US (unusual)'
            } if spread is not None else None
        }
        
        return assessment

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Enhanced macro monitor (Canada + US rates)")
    parser.add_argument('--output', type=Path, default=Path('data/macro_enhanced.json'))
    parser.add_argument('--lookback', type=int, default=120)
    args = parser.parse_args()
    
    monitor = EnhancedMacroMonitor()
    assessment = monitor.generate_assessment(args.lookback)
    
    # Export
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(assessment, f, indent=2, default=str)
    
    # Display
    print(f"\n{'='*60}")
    print("NORTH AMERICAN INTEREST RATE ENVIRONMENT")
    print(f"{'='*60}")
    
    ca = assessment['canada']
    print(f"\n🍁 BANK OF CANADA:")
    print(f"  Current Rate:         {ca['policy_rate']['current_rate']:.2f}%")
    print(f"  12-Month Change:      {ca['policy_rate']['change_12m_bps']:.0f} bps")
    print(f"  Cycle:                {ca['policy_rate']['cycle']}")
    print(f"  Credit Environment:   {ca['credit_environment']} ({ca['credit_stress_score']}/100)")
    
    if assessment.get('united_states'):
        us = assessment['united_states']
        print(f"\n🦅 US FEDERAL RESERVE:")
        print(f"  Current Rate:         {us['policy_rate']['current_rate']:.2f}%")
        print(f"  12-Month Change:      {us['policy_rate']['change_12m_bps']:.0f} bps")
        print(f"  Cycle:                {us['policy_rate']['cycle']}")
    
    if assessment.get('rate_differential'):
        diff = assessment['rate_differential']
        spread_bps = diff['ca_minus_us_bps']
        print(f"\n📊 RATE DIFFERENTIAL:")
        print(f"  Canada vs US:         {spread_bps:+.0f} bps")
        if spread_bps < 0:
            print(f"  Status:               Canada BELOW US (typical)")
        else:
            print(f"  Status:               Canada ABOVE US (unusual)")
    
    print(f"\n✓ Exported to {args.output}")
    print(f"{'='*60}")
