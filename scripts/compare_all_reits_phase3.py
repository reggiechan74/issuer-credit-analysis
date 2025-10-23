#!/usr/bin/env python3
"""
Compare v2.1 vs v2.2 predictions for ALL REITs with Phase 3 data.
Works directly from Phase 3 calculated metrics (no Phase 4 enriched data needed).
"""

import json
import pickle
import pandas as pd
from pathlib import Path

# Load models
print("Loading models...")
model_v21 = pickle.load(open("models/distribution_cut_logistic_regression.pkl", 'rb'))
model_v22 = pickle.load(open("models/distribution_cut_logistic_regression_v2.2.pkl", 'rb'))

print("="*100)
print("COMPREHENSIVE MODEL COMPARISON: ALL REITs WITH PHASE 3 DATA")
print("="*100)
print()

# Find all REITs with Phase 3 data
reits = []
for p in Path('Issuer_Reports').iterdir():
    if p.is_dir() and p.name != 'phase1b':
        phase3 = p / 'temp' / 'phase3_calculated_metrics.json'
        if phase3.exists():
            reits.append({
                'name': p.name.replace('_', ' '),
                'folder': p.name,
                'phase3_path': phase3
            })

reits = sorted(reits, key=lambda x: x['name'])

print(f"Found {len(reits)} REITs with Phase 3 calculated metrics")
print()

# Process each REIT
results = []

for reit in reits:
    print(f"Processing: {reit['name']}")

    # Load Phase 3 data
    with open(reit['phase3_path']) as f:
        phase3 = json.load(f)

    # Extract metrics
    leverage = phase3.get('leverage_metrics', {})
    reit_metrics = phase3.get('reit_metrics', {})
    coverage = phase3.get('coverage_ratios', {})
    burn = phase3.get('burn_rate_analysis', {})
    liquidity = phase3.get('liquidity_position', {})
    portfolio = phase3.get('portfolio', {})
    dilution = phase3.get('dilution_analysis', {})
    afcf = phase3.get('afcf_metrics', {})

    # Build fundamentals dict (exact column order from training dataset)
    fundamentals = {
        'total_debt': leverage.get('total_debt', 0),
        'debt_to_assets_percent': leverage.get('debt_to_assets_percent', 0),
        'net_debt_ratio': leverage.get('net_debt_ratio', 0),
        'ffo_reported': reit_metrics.get('ffo', 0),
        'affo_reported': reit_metrics.get('affo', 0),
        'ffo_per_unit': reit_metrics.get('ffo_per_unit', 0),
        'affo_per_unit': reit_metrics.get('affo_per_unit', 0),
        'distributions_per_unit': reit_metrics.get('distributions_per_unit', 0),
        'ffo_payout_ratio': reit_metrics.get('ffo_payout_ratio', 0),
        'affo_payout_ratio': reit_metrics.get('affo_payout_ratio', 0),
        'ffo_calculated': reit_metrics.get('ffo_calculated', 0),
        'affo_calculated': reit_metrics.get('affo_calculated', 0),
        'acfo_calculated': reit_metrics.get('acfo_calculated', 0),
        'ffo_per_unit_calc': reit_metrics.get('ffo_per_unit', 0),
        'affo_per_unit_calc': reit_metrics.get('affo_per_unit', 0),
        'acfo_per_unit_calc': reit_metrics.get('acfo_per_unit', 0),
        'noi_interest_coverage': coverage.get('noi_interest_coverage', 0),
        'annualized_interest_expense': coverage.get('annualized_interest_expense', 0),
        'total_properties': portfolio.get('total_properties', 0),
        'occupancy_rate': portfolio.get('occupancy_rate', 0),
        'same_property_noi_growth': portfolio.get('same_property_noi_growth', 0),
        'available_cash': liquidity.get('available_cash', 0),
        'total_available_liquidity': liquidity.get('total_available_liquidity', 0),
        'monthly_burn_rate': burn.get('monthly_burn_rate', 0),
        'self_funding_ratio': burn.get('self_funding_ratio', 0),
        'dilution_percentage': dilution.get('dilution_percentage', 0),
        'dilution_materiality': dilution.get('dilution_materiality', 'minimal'),
        'sector': phase3.get('sector', 'Other')
    }

    # Get v2.2 prediction
    df = pd.DataFrame([fundamentals])

    # Encode categorical features
    for col, encoder in model_v22['label_encoders'].items():
        if col in df.columns:
            try:
                df[col] = encoder.transform(df[col])
            except ValueError:
                df[col] = encoder.transform([encoder.classes_[0]])

    df_filled = df.fillna(0)
    X_selected = model_v22['selector'].transform(df_filled)
    X_scaled = model_v22['scaler'].transform(X_selected)
    v22_prob = model_v22['model'].predict_proba(X_scaled)[0, 1] * 100

    # Classify risk
    if v22_prob < 5:
        v22_risk = "Very Low"
    elif v22_prob < 15:
        v22_risk = "Low"
    elif v22_prob < 30:
        v22_risk = "Moderate"
    elif v22_prob < 50:
        v22_risk = "High"
    else:
        v22_risk = "Very High"

    # Get AFCF details
    afcf_sustainable = afcf.get('afcf_sustainable', 0) / 1000
    afcf_total = afcf.get('afcf_total', 0) / 1000
    afcf_diff = afcf_total - afcf_sustainable

    results.append({
        'REIT': reit['name'],
        'period': phase3.get('reporting_period', 'Unknown'),
        'v22_prob': v22_prob,
        'v22_risk': v22_risk,
        'afcf_sustainable': afcf_sustainable,
        'afcf_total': afcf_total,
        'afcf_difference': afcf_diff,
        'self_funding_ratio': burn.get('self_funding_ratio', 0),
        'debt_to_assets': leverage.get('debt_to_assets_percent', 0),
        'affo_payout': reit_metrics.get('affo_payout_ratio', 0),
        'noi_coverage': coverage.get('noi_interest_coverage', 0)
    })

# Create DataFrame
df_results = pd.DataFrame(results)

# Display results
print()
print("="*100)
print("MODEL v2.2 PREDICTIONS (SUSTAINABLE AFCF)")
print("="*100)
print()

for idx, row in df_results.iterrows():
    print(f"\n{idx+1}. {row['REIT']}")
    print(f"   Period: {row['period']}")
    print("-"*100)
    print(f"   Cut Probability: {row['v22_prob']:6.1f}% ({row['v22_risk']:10})")
    print(f"   AFCF Sustainable: ${row['afcf_sustainable']:>10,.0f}k")
    print(f"   AFCF Total:       ${row['afcf_total']:>10,.0f}k (Diff: ${row['afcf_difference']:>+8,.0f}k)")
    print(f"   Self-Funding:     {row['self_funding_ratio']:>10.2f}x")
    print(f"   Debt/Assets:      {row['debt_to_assets']:>10.1f}%")
    print(f"   AFFO Payout:      {row['affo_payout']:>10.1f}%")
    print(f"   NOI Coverage:     {row['noi_coverage']:>10.2f}x")

print()
print("="*100)
print("SUMMARY STATISTICS")
print("="*100)
print()
print(f"Total REITs Analyzed:        {len(df_results)}")
print(f"Average Cut Probability:     {df_results['v22_prob'].mean():>6.1f}%")
print(f"Median Cut Probability:      {df_results['v22_prob'].median():>6.1f}%")
print(f"Maximum Cut Probability:     {df_results['v22_prob'].max():>6.1f}% ({df_results.loc[df_results['v22_prob'].idxmax(), 'REIT']})")
print(f"Minimum Cut Probability:     {df_results['v22_prob'].min():>6.1f}% ({df_results.loc[df_results['v22_prob'].idxmin(), 'REIT']})")
print()

# Risk level distribution
print("="*100)
print("RISK LEVEL DISTRIBUTION")
print("="*100)
print()
risk_counts = df_results['v22_risk'].value_counts()
for risk_level in ["Very High", "High", "Moderate", "Low", "Very Low"]:
    count = risk_counts.get(risk_level, 0)
    pct = count / len(df_results) * 100
    print(f"  {risk_level:15} {count:2} REITs ({pct:4.1f}%)")

print()
print("="*100)
print("SORTED BY CUT PROBABILITY (HIGHEST RISK FIRST)")
print("="*100)
print()

df_sorted = df_results.sort_values('v22_prob', ascending=False)
for idx, row in df_sorted.iterrows():
    print(f"{row['v22_prob']:5.1f}% ({row['v22_risk']:10}) - {row['REIT']}")

print()
print("✓ Comparison complete - {len(df_results)} REITs analyzed with model v2.2")
