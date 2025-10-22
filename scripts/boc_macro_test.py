#!/usr/bin/env python3
"""Test Bank of Canada Valet API for macro data"""

import requests
import pandas as pd
from datetime import datetime, timedelta

# Test policy rate retrieval
start_date = (datetime.now() - timedelta(days=3650)).strftime('%Y-%m-%d')
url = f"https://www.bankofcanada.ca/valet/observations/V122530/json?start_date={start_date}"

response = requests.get(url, timeout=30)
data = response.json()

observations = data.get('observations', [])
print(f"✓ Retrieved {len(observations)} policy rate observations")

# Convert to DataFrame
records = []
for obs in observations:
    date_str = obs.get('d')
    rate_data = obs.get('V122530', {})
    rate_value = rate_data.get('v')
    
    if date_str and rate_value:
        records.append({
            'date': pd.to_datetime(date_str),
            'rate': float(rate_value)
        })

df = pd.DataFrame(records)
current_rate = df['rate'].iloc[-1]
rate_12m_ago = df['rate'].iloc[-12]
rate_change = current_rate - rate_12m_ago

print(f"Current rate: {current_rate:.2f}%")
print(f"12-month change: {rate_change*100:.0f} bps")
print(f"Peak rate: {df['rate'].max():.2f}%")
print(f"✓ Bank of Canada Valet API works perfectly!")
