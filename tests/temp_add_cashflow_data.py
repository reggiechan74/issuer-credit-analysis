#!/usr/bin/env python3
"""
Temporary script to add actual cash flow data to Artis REIT and DIR Phase 2 files
Then test AFCF calculations
"""

import json
import sys
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent / 'scripts'))
from calculate_credit_metrics import calculate_all_metrics

def add_artis_cash_flow_data():
    """Add actual cash flow data from Artis REIT Q2 2025 financial statements"""

    file_path = Path('/workspaces/issuer-credit-analysis/Issuer_Reports/Artis_REIT/temp/phase2_extracted_data.json')

    with open(file_path) as f:
        data = json.load(f)

    # Add cash_flow_investing (Six months ended June 30, 2025)
    # From Consolidated Statements of Cash Flows
    data['cash_flow_investing'] = {
        'development_capex': 0,  # No development additions shown separately
        'property_acquisitions': 0,  # No acquisitions in this period
        'property_dispositions': 47389,  # Proceeds from dispositions
        'jv_capital_contributions': -408,  # Contributions to equity accounted
        'jv_return_of_capital': 3511,  # Distributions from equity accounted
        'business_combinations': 0,
        'other_investing_outflows': -8631,  # Purchases of equity securities
        'other_investing_inflows': 30377,  # Proceeds from equity securities
        'total_cfi': 44196  # Total from statement
    }

    # Add cash_flow_financing (Six months ended June 30, 2025)
    data['cash_flow_financing'] = {
        'debt_principal_repayments': -27921,  # Repayment of mortgages
        'new_debt_issuances': 18799,  # Advance of mortgages (net of -200k debenture repayment handled separately)
        'distributions_common': -29770,  # Distributions on common units
        'distributions_preferred': -6374,  # Distributions on preferred units
        'distributions_nci': 0,  # Not separately shown
        'equity_issuances': 0,  # None this period
        'unit_buybacks': -28860,  # Common (-26,738) + Preferred (-2,122) unit buybacks
        'deferred_financing_costs_paid': 0,  # Not separately shown
        'other_financing_outflows': -200000,  # Repayment of senior unsecured debentures
        'other_financing_inflows': 186290,  # Net revolving credit (249,775 - 63,485)
        'total_cff': -88238  # Total from statement
    }

    # Save updated file
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"✅ Updated Artis REIT with cash flow data")
    return data

def add_dir_cash_flow_data():
    """Add actual cash flow data from DIR Q2 2025 financial statements"""

    file_path = Path('/workspaces/issuer-credit-analysis/Issuer_Reports/DIR-Q2-Report-FINAL/temp/phase2_extracted_data.json')

    with open(file_path) as f:
        data = json.load(f)

    # Add cash_flow_investing (Six months ended June 30, 2025)
    # From Condensed Consolidated Statements of Cash Flows
    data['cash_flow_investing'] = {
        'development_capex': -38092,  # Building improvements and development costs
        'property_acquisitions': -26832,  # Acquisitions and deposits
        'property_dispositions': 11387,  # Dispositions (net of mortgages/costs)
        'jv_capital_contributions': -37018,  # Contributions to equity accounted
        'jv_return_of_capital': 17089,  # Distributions from equity accounted
        'business_combinations': 0,
        'other_investing_outflows': 0,
        'other_investing_inflows': 0,
        'total_cfi': -73466  # Total from statement
    }

    # Add cash_flow_financing (Six months ended June 30, 2025)
    data['cash_flow_financing'] = {
        'debt_principal_repayments': -84898,  # Lump sum (-83,558) + Principal (-1,340)
        'new_debt_issuances': 96376,  # Borrowings
        'distributions_common': -71921,  # Distributions on REIT Units
        'distributions_preferred': 0,  # Not separately shown
        'distributions_nci': -3640,  # Interest on subsidiary redeemable units
        'equity_issuances': 0,
        'unit_buybacks': -20036,  # NCIB repurchases
        'deferred_financing_costs_paid': -898,  # Financing costs additions
        'other_financing_outflows': 0,
        'other_financing_inflows': 0,
        'total_cff': -121919  # Total from statement (includes other adjustments)
    }

    # Save updated file
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"✅ Updated DIR with cash flow data")
    return data

def test_afcf_calculation(issuer_name, data):
    """Test AFCF calculation and display results"""

    print(f"\n{'='*70}")
    print(f"TESTING AFCF CALCULATION: {issuer_name}")
    print(f"{'='*70}\n")

    # Run Phase 3 calculations
    try:
        results = calculate_all_metrics(data)

        # Display results
        print(f"📊 {issuer_name} - {results['reporting_period']}")
        print(f"Currency: {results['currency']}\n")

        # REIT Metrics
        if 'reit_metrics' in results:
            rm = results['reit_metrics']
            print("REIT METRICS:")
            print(f"  FFO:  ${rm.get('ffo', 'N/A'):,}K")
            print(f"  AFFO: ${rm.get('affo', 'N/A'):,}K")
            if 'acfo' in rm:
                print(f"  ACFO: ${rm['acfo']:,}K")

        # AFCF Metrics
        if 'afcf_metrics' in results:
            afcf = results['afcf_metrics']
            print(f"\n✨ AFCF METRICS:")
            print(f"  ACFO (starting point): ${afcf['acfo_starting_point']:,}K")
            print(f"  Net CFI:               ${afcf['net_cfi']:,}K")
            print(f"  AFCF:                  ${afcf['afcf']:,}K")
            print(f"  Data Quality:          {afcf['data_quality']}")

            # CFI Breakdown
            print(f"\n  CFI Breakdown:")
            for component, details in afcf['cfi_breakdown'].items():
                if details['amount'] != 0:
                    print(f"    {details['description']:40} ${details['amount']:>10,}K")

        # AFCF Coverage Ratios
        if 'afcf_coverage' in results:
            cov = results['afcf_coverage']
            print(f"\n💹 AFCF COVERAGE RATIOS:")
            if cov['afcf_debt_service_coverage']:
                print(f"  Debt Service Coverage: {cov['afcf_debt_service_coverage']:.2f}x")
                print(f"    (AFCF ${afcf['afcf']:,}K / Debt Service ${cov['total_debt_service']:,}K)")
                if cov['afcf_debt_service_coverage'] < 1.0:
                    print(f"    ⚠️  Coverage < 1.0x - Needs external financing for debt service")

            if cov['afcf_distribution_coverage']:
                print(f"  Distribution Coverage: {cov['afcf_distribution_coverage']:.2f}x")
                print(f"  Payout Ratio:          {cov['afcf_payout_ratio']:.1f}%")

            if cov['afcf_self_funding_ratio']:
                print(f"  Self-Funding Ratio:    {cov['afcf_self_funding_ratio']:.2f}x")
                print(f"    (Net Financing Needs: ${cov['net_financing_needs']:,}K)")

        # AFCF Reconciliation
        if 'afcf_reconciliation' in results:
            recon = results['afcf_reconciliation']
            print(f"\n✓ RECONCILIATION:")
            for note in recon['validation_notes']:
                print(f"  {note}")

        print(f"\n{'='*70}\n")
        return results

    except Exception as e:
        print(f"❌ Error calculating AFCF: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    # Add cash flow data from actual financial statements
    artis_data = add_artis_cash_flow_data()
    dir_data = add_dir_cash_flow_data()

    # Test AFCF calculations
    artis_results = test_afcf_calculation("Artis REIT", artis_data)
    dir_results = test_afcf_calculation("Dream Industrial REIT", dir_data)

    print("\n" + "="*70)
    print("AFCF TESTING COMPLETE")
    print("="*70)

    if artis_results and dir_results:
        print("\n✅ Both issuers tested successfully!")
        print("\nKey Findings:")

        if 'afcf_metrics' in artis_results:
            artis_afcf = artis_results['afcf_metrics']['afcf']
            artis_net_cfi = artis_results['afcf_metrics']['net_cfi']
            print(f"\nArtis REIT:")
            print(f"  AFCF = ${artis_afcf:,}K")
            print(f"  Net CFI = ${artis_net_cfi:,}K ({'positive - net seller' if artis_net_cfi > 0 else 'negative - net investor'})")

        if 'afcf_metrics' in dir_results:
            dir_afcf = dir_results['afcf_metrics']['afcf']
            dir_net_cfi = dir_results['afcf_metrics']['net_cfi']
            print(f"\nDIR:")
            print(f"  AFCF = ${dir_afcf:,}K")
            print(f"  Net CFI = ${dir_net_cfi:,}K ({'positive - net seller' if dir_net_cfi > 0 else 'negative - net investor'})")
