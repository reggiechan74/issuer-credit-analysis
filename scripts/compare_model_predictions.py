#!/usr/bin/env python3
"""
Compare predictions between v2.1 and v2.2 models on 3 test REITs.
"""

import json
import pickle
import pandas as pd
from pathlib import Path

# Load both models
model_v21_path = Path("models/distribution_cut_logistic_regression.pkl")
model_v22_path = Path("models/distribution_cut_logistic_regression_v2.2.pkl")

with open(model_v21_path, 'rb') as f:
    model_v21 = pickle.load(f)

with open(model_v22_path, 'rb') as f:
    model_v22 = pickle.load(f)

print("="*70)
print("MODEL COMPARISON: v2.1 (Total AFCF) vs v2.2 (Sustainable AFCF)")
print("="*70)
print()

# Test REITs
reits = [
    ("Artis REIT", "Issuer_Reports/Artis_REIT/temp/phase4_enriched_data.json"),
    ("RioCan REIT", "Issuer_Reports/RioCan_REIT/temp/phase4_enriched_data.json"),
    ("Dream Industrial REIT", "Issuer_Reports/Dream_Industrial_REIT/temp/phase4_enriched_data.json")
]

results = []

for name, path in reits:
    print(f"Testing: {name}")
    print("-"*70)

    # Load enriched data
    with open(path) as f:
        data = json.load(f)

    # Get v2.1 prediction (already in the file)
    v21_prediction = data.get('distribution_cut_prediction', {})
    v21_prob = v21_prediction.get('cut_probability_pct', 0)
    v21_risk = v21_prediction.get('risk_level', 'Unknown')

    # Extract metrics from phase3_metrics section
    phase3 = data.get('phase3_metrics', {})
    leverage = phase3.get('leverage_metrics', {})
    reit = phase3.get('reit_metrics', {})
    coverage = phase3.get('coverage_ratios', {})
    burn_rate = phase3.get('burn_rate_analysis', {})
    liquidity = phase3.get('liquidity_position', {})
    portfolio = phase3.get('portfolio', {})
    dilution = phase3.get('dilution_analysis', {})

    # Build fundamentals dict for v2.2 - MUST match exact column order from training dataset
    fundamentals = {
        'total_debt': leverage.get('total_debt', 0),
        'debt_to_assets_percent': leverage.get('debt_to_assets_percent', 0),
        'net_debt_ratio': leverage.get('net_debt_ratio', 0),
        'ffo_reported': reit.get('ffo', 0),
        'affo_reported': reit.get('affo', 0),
        'ffo_per_unit': reit.get('ffo_per_unit', 0),
        'affo_per_unit': reit.get('affo_per_unit', 0),
        'distributions_per_unit': reit.get('distributions_per_unit', 0),
        'ffo_payout_ratio': reit.get('ffo_payout_ratio', 0),
        'affo_payout_ratio': reit.get('affo_payout_ratio', 0),
        'ffo_calculated': reit.get('ffo_calculated', 0),
        'affo_calculated': reit.get('affo_calculated', 0),
        'acfo_calculated': reit.get('acfo_calculated', 0),
        'ffo_per_unit_calc': reit.get('ffo_per_unit', 0),
        'affo_per_unit_calc': reit.get('affo_per_unit', 0),
        'acfo_per_unit_calc': reit.get('acfo_per_unit', 0),
        'noi_interest_coverage': coverage.get('noi_interest_coverage', 0),
        'annualized_interest_expense': coverage.get('annualized_interest_expense', 0),
        'total_properties': portfolio.get('total_properties', 0),
        'occupancy_rate': portfolio.get('occupancy_rate', 0),
        'same_property_noi_growth': portfolio.get('same_property_noi_growth', 0),
        'available_cash': liquidity.get('available_cash', 0),
        'total_available_liquidity': liquidity.get('total_available_liquidity', 0),
        'monthly_burn_rate': burn_rate.get('monthly_burn_rate', 0),
        'self_funding_ratio': burn_rate.get('self_funding_ratio', 0),
        'dilution_percentage': dilution.get('dilution_percentage', 0),
        'dilution_materiality': dilution.get('dilution_materiality', 'minimal'),
        'sector': phase3.get('sector', 'Other')
    }

    # Convert to DataFrame
    df = pd.DataFrame([fundamentals])

    # Run v2.2 prediction
    try:
        selector_v22 = model_v22['selector']
        scaler_v22 = model_v22['scaler']
        clf_v22 = model_v22['model']  # Use 'model' key not 'classifier'
        label_encoders = model_v22['label_encoders']

        # Encode categorical features
        for col, encoder in label_encoders.items():
            if col in df.columns:
                # Handle unknown categories by mapping to first class
                try:
                    df[col] = encoder.transform(df[col])
                except ValueError:
                    # Unknown category - map to first class
                    df[col] = encoder.transform([encoder.classes_[0]])

        # Fill any missing values with 0
        df_filled = df.fillna(0)

        # Transform using selector
        X_selected = selector_v22.transform(df_filled)
        X_scaled = scaler_v22.transform(X_selected)

        # Get prediction
        v22_prob = clf_v22.predict_proba(X_scaled)[0, 1] * 100

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

    except Exception as e:
        print(f"  ⚠️  v2.2 Prediction Error: {e}")
        v22_prob = None
        v22_risk = "Error"

    # Compare
    print(f"  v2.1 (Total AFCF):       {v21_prob:.1f}% ({v21_risk})")
    if v22_prob is not None:
        print(f"  v2.2 (Sustainable AFCF): {v22_prob:.1f}% ({v22_risk})")
        diff = v22_prob - v21_prob
        print(f"  Difference:              {diff:+.1f}%")
    print()

    # Get self-funding ratio for context
    sfr = fundamentals.get('self_funding_ratio', 0)
    print(f"  Self-Funding Ratio: {sfr:.2f}x")
    print()

    results.append({
        'name': name,
        'v21_prob': v21_prob,
        'v21_risk': v21_risk,
        'v22_prob': v22_prob,
        'v22_risk': v22_risk,
        'diff': v22_prob - v21_prob if v22_prob is not None else None,
        'self_funding_ratio': sfr
    })

print("="*70)
print("SUMMARY")
print("="*70)
print()

for r in results:
    print(f"{r['name']}:")
    if r['v22_prob'] is not None:
        print(f"  v2.1: {r['v21_prob']:.1f}% → v2.2: {r['v22_prob']:.1f}% (Δ {r['diff']:+.1f}%)")
    else:
        print(f"  v2.1: {r['v21_prob']:.1f}% → v2.2: Error")
    print(f"  Self-Funding: {r['self_funding_ratio']:.2f}x")
    print()

print("✓ Comparison complete")
