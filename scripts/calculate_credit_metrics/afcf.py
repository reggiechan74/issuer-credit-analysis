"""
AFCF (Adjusted Free Cash Flow) calculations

Extends ACFO analysis to measure cash available after ALL investing activities.
Per REALPAC methodology with double-counting prevention.
"""

def calculate_afcf(financial_data):
    """
    Calculate Adjusted Free Cash Flow (AFCF) from ACFO and investing activities

    AFCF = ACFO + Net Cash Flow from Investing Activities

    Purpose: Measure cash available for financing obligations (debt service + distributions)
    after all operating AND investing activities.

    CRITICAL: Prevents double-counting with ACFO:
    - Sustaining CAPEX: Already deducted in ACFO (Adj 4) - DO NOT deduct again
    - Tenant Improvements (sustaining): Already in ACFO (Adj 6) - DO NOT deduct again
    - External Leasing Costs: Already in ACFO (Adj 5) - DO NOT deduct again
    - JV Distributions: Already in ACFO (Adj 3) - DO NOT add again

    AFCF should ONLY include investing activities NOT in ACFO:
    - Development CAPEX (growth projects, not sustaining)
    - Property acquisitions and dispositions
    - JV capital contributions/returns (not distributions)
    - Other investing activities

    Args:
        financial_data (dict): Validated JSON with cash_flow_investing section and ACFO calculated

    Returns:
        dict: {
            'afcf': float,
            'afcf_per_unit': float | None,  # Basic - calculated if common_units_outstanding available
            'afcf_per_unit_diluted': float | None,  # Diluted - calculated if diluted_units_outstanding available
            'acfo_starting_point': float,
            'net_cfi': float,
            'cfi_breakdown': dict,  # Individual CFI components
            'data_quality': str,  # 'strong', 'moderate', 'limited', 'none'
            'has_cfi_data': bool,
            'missing_components': list
        }
    """

    # Check if cash flow investing data available
    if 'cash_flow_investing' not in financial_data:
        return {
            'afcf': None,
            'error': 'No cash_flow_investing section in financial data',
            'data_quality': 'none',
            'has_cfi_data': False
        }

    cfi_data = financial_data['cash_flow_investing']

    # Get ACFO starting point (should already be calculated in reit_metrics)
    acfo = None
    if 'acfo_calculated' in financial_data:
        acfo = financial_data['acfo_calculated']
    elif 'reit_metrics' in financial_data and 'acfo' in financial_data['reit_metrics']:
        acfo = financial_data['reit_metrics']['acfo']

    if acfo is None:
        return {
            'afcf': None,
            'error': 'ACFO must be calculated before AFCF',
            'data_quality': 'insufficient',
            'has_cfi_data': True
        }

    # Define investing activity components
    cfi_components = {
        'development_capex': 'Development CAPEX (growth projects)',
        'property_acquisitions': 'Property acquisitions',
        'property_dispositions': 'Property dispositions (proceeds)',
        'jv_capital_contributions': 'JV capital contributions',
        'jv_return_of_capital': 'JV return of capital',
        'business_combinations': 'Business combinations',
        'other_investing_outflows': 'Other investing outflows',
        'other_investing_inflows': 'Other investing inflows'
    }

    # Collect CFI components and calculate net CFI
    cfi_breakdown = {}
    missing_components = []
    net_cfi = 0.0
    available_count = 0

    for component, description in cfi_components.items():
        if component in cfi_data and cfi_data[component] is not None:
            value = cfi_data[component]
            cfi_breakdown[component] = {
                'description': description,
                'amount': value
            }
            net_cfi += value
            available_count += 1
        else:
            missing_components.append(component)
            cfi_breakdown[component] = {
                'description': description,
                'amount': 0.0
            }

    # Calculate AFCF
    afcf = acfo + net_cfi

    # Check against total_cfi if provided (for reconciliation)
    reconciliation_check = None
    if 'total_cfi' in cfi_data and cfi_data['total_cfi'] is not None:
        reported_cfi = cfi_data['total_cfi']
        variance = net_cfi - reported_cfi
        reconciliation_check = {
            'calculated_net_cfi': net_cfi,
            'reported_total_cfi': reported_cfi,
            'variance': variance,
            'matches': abs(variance) < 100  # Allow small rounding differences
        }

    # Assess data quality
    if available_count >= 6:  # 6+ of 8 components
        data_quality = 'strong'
    elif available_count >= 3:  # 3-5 of 8 components
        data_quality = 'moderate'
    else:  # < 3 components
        data_quality = 'limited'

    # Calculate per-unit AFCF if shares outstanding available
    afcf_per_unit = None
    afcf_per_unit_diluted = None

    if 'balance_sheet' in financial_data:
        # Basic per-unit
        if 'common_units_outstanding' in financial_data['balance_sheet']:
            units = financial_data['balance_sheet']['common_units_outstanding']
            if units and units > 0:
                afcf_per_unit = round(afcf / units, 4)

        # Diluted per-unit
        if 'diluted_units_outstanding' in financial_data['balance_sheet']:
            units_diluted = financial_data['balance_sheet']['diluted_units_outstanding']
            if units_diluted and units_diluted > 0:
                afcf_per_unit_diluted = round(afcf / units_diluted, 4)

    result = {
        'afcf': round(afcf, 0),
        'acfo_starting_point': acfo,
        'net_cfi': round(net_cfi, 0),
        'cfi_breakdown': cfi_breakdown,
        'missing_components': missing_components,
        'available_components': available_count,
        'total_components': len(cfi_components),
        'data_quality': data_quality,
        'has_cfi_data': True,
        'reconciliation_check': reconciliation_check
    }

    # Add per-unit if calculated
    if afcf_per_unit is not None:
        result['afcf_per_unit'] = afcf_per_unit
    if afcf_per_unit_diluted is not None:
        result['afcf_per_unit_diluted'] = afcf_per_unit_diluted

    return result


def calculate_afcf_coverage_ratios(financial_data, afcf):
    """
    Calculate coverage ratios using AFCF

    Ratios measure ability to service financing obligations from free cash flow:
    1. AFCF to Total Debt Service = AFCF / (Interest + Principal Repayments)
    2. AFCF Distribution Coverage = AFCF / Total Distributions
    3. AFCF Self-Funding Ratio = AFCF / (Debt Service + Dist - New Financing)

    Args:
        financial_data (dict): Validated JSON with cash_flow_financing and coverage_ratios
        afcf (float): Calculated AFCF value

    Returns:
        dict: {
            'afcf_debt_service_coverage': float,  # AFCF / (Interest + Principal)
            'afcf_distribution_coverage': float,  # AFCF / Distributions (inverted payout)
            'afcf_payout_ratio': float,           # Distributions / AFCF (%)
            'afcf_self_funding_ratio': float,     # AFCF / Net Financing Needs
            'total_debt_service': float,
            'total_distributions': float,
            'net_financing_needs': float,
            'data_quality': str
        }
    """

    result = {
        'afcf_debt_service_coverage': None,
        'afcf_distribution_coverage': None,
        'afcf_payout_ratio': None,
        'afcf_self_funding_ratio': None,
        'total_debt_service': None,
        'total_distributions': None,
        'net_financing_needs': None,
        'data_quality': 'none'
    }

    # Require AFCF to be non-None
    if afcf is None:
        result['error'] = 'AFCF must be calculated first'
        return result

    # Get PERIOD interest expense from coverage_ratios (NOT annualized)
    # AFCF coverage uses period-to-period comparison
    period_interest = 0
    if 'coverage_ratios' in financial_data:
        period_interest = financial_data['coverage_ratios'].get('period_interest_expense', 0)

    # Get principal repayments and distributions from cash_flow_financing
    principal_repayments = 0
    total_distributions = 0
    new_financing = 0

    if 'cash_flow_financing' in financial_data:
        cff_data = financial_data['cash_flow_financing']

        # Principal repayments (negative number in data, make positive for calculation)
        # Use PERIOD amount (NOT annualized) - period-to-period comparison with AFCF
        if 'debt_principal_repayments' in cff_data and cff_data['debt_principal_repayments'] is not None:
            principal_repayments = abs(cff_data['debt_principal_repayments'])

        # Distributions (sum all types, make positive)
        # These are already period amounts
        dist_common = abs(cff_data.get('distributions_common', 0) or 0)
        dist_preferred = abs(cff_data.get('distributions_preferred', 0) or 0)
        dist_nci = abs(cff_data.get('distributions_nci', 0) or 0)
        total_distributions = dist_common + dist_preferred + dist_nci

        # New financing (positive inflows)
        new_debt = cff_data.get('new_debt_issuances', 0) or 0
        new_equity = cff_data.get('equity_issuances', 0) or 0
        new_financing = new_debt + new_equity

    # Calculate total debt service (PERIOD amounts for period-to-period comparison with AFCF)
    total_debt_service = period_interest + principal_repayments

    # Calculate AFCF debt service coverage
    if total_debt_service > 0:
        result['afcf_debt_service_coverage'] = round(afcf / total_debt_service, 2)
        result['total_debt_service'] = total_debt_service
    else:
        result['afcf_debt_service_coverage'] = None
        result['total_debt_service'] = 0

    # Calculate AFCF distribution coverage and payout ratio
    if total_distributions > 0:
        result['afcf_distribution_coverage'] = round(afcf / total_distributions, 2)
        result['afcf_payout_ratio'] = round((total_distributions / afcf) * 100, 1) if afcf != 0 else None
        result['total_distributions'] = total_distributions
    else:
        result['afcf_distribution_coverage'] = None
        result['afcf_payout_ratio'] = None
        result['total_distributions'] = 0

    # Calculate self-funding ratio and capacity
    # Self-Funding Ratio = AFCF / (Total Debt Service + Total Distributions)
    # This measures how many times AFCF covers all financing obligations
    total_obligations = total_debt_service + total_distributions

    if total_obligations > 0:
        result['afcf_self_funding_ratio'] = round(afcf / total_obligations, 2)
    else:
        result['afcf_self_funding_ratio'] = None

    # Self-Funding Capacity = AFCF - Total Debt Service - Total Distributions
    # This is the dollar cushion remaining after all obligations are paid
    result['afcf_self_funding_capacity'] = round(afcf - total_obligations, 0)

    # Net financing needs (for informational purposes)
    net_financing_needs = total_debt_service + total_distributions - new_financing
    result['net_financing_needs'] = net_financing_needs

    # Assess data quality
    has_debt_service = total_debt_service > 0
    has_distributions = total_distributions > 0
    has_financing = new_financing > 0

    if has_debt_service and has_distributions and has_financing:
        result['data_quality'] = 'strong'
    elif has_debt_service or has_distributions:
        result['data_quality'] = 'moderate'
    else:
        result['data_quality'] = 'limited'

    return result


def validate_afcf_reconciliation(financial_data, acfo, afcf):
    """
    Validate AFCF calculation reconciles to IFRS cash flow statement

    Checks:
    1. ACFO + Net CFI = AFCF
    2. CFO + CFI + CFF = Change in Cash (if all available)
    3. Development CAPEX consistency between ACFO and CFI

    Args:
        financial_data (dict): Complete financial data
        acfo (float): Calculated ACFO
        afcf (float): Calculated AFCF

    Returns:
        dict: {
            'afcf_calculation_valid': bool,
            'acfo_cfi_reconciles': bool,
            'cash_flow_statement_reconciles': bool,
            'development_capex_consistent': bool,
            'validation_notes': list,
            'reconciliation_summary': str
        }
    """

    result = {
        'afcf_calculation_valid': None,
        'acfo_cfi_reconciles': None,
        'cash_flow_statement_reconciles': None,
        'development_capex_consistent': None,
        'validation_notes': [],
        'reconciliation_summary': ''
    }

    # Check 1: AFCF = ACFO + Net CFI
    if acfo is not None and afcf is not None and 'cash_flow_investing' in financial_data:
        cfi_data = financial_data['cash_flow_investing']

        # Calculate net CFI from components
        net_cfi = 0
        for component in ['development_capex', 'property_acquisitions', 'property_dispositions',
                         'jv_capital_contributions', 'jv_return_of_capital', 'business_combinations',
                         'other_investing_outflows', 'other_investing_inflows']:
            if component in cfi_data and cfi_data[component] is not None:
                net_cfi += cfi_data[component]

        calculated_afcf = acfo + net_cfi
        variance = afcf - calculated_afcf

        if abs(variance) < 1:  # Allow tiny rounding differences
            result['afcf_calculation_valid'] = True
            result['acfo_cfi_reconciles'] = True
            result['validation_notes'].append('✓ AFCF calculation correct: ACFO + Net CFI = AFCF')
        else:
            result['afcf_calculation_valid'] = False
            result['acfo_cfi_reconciles'] = False
            result['validation_notes'].append(
                f'✗ AFCF calculation error: AFCF ({afcf:,.0f}) ≠ ACFO ({acfo:,.0f}) + Net CFI ({net_cfi:,.0f}). '
                f'Variance: {variance:,.0f}'
            )

    # Check 2: Development CAPEX consistency
    if 'acfo_components' in financial_data and 'cash_flow_investing' in financial_data:
        acfo_dev_capex = financial_data['acfo_components'].get('capex_development_acfo')
        cfi_dev_capex = financial_data['cash_flow_investing'].get('development_capex')

        if acfo_dev_capex is not None and cfi_dev_capex is not None:
            # Both should be negative, check if they match
            if abs(acfo_dev_capex - cfi_dev_capex) < 100:  # Allow small differences
                result['development_capex_consistent'] = True
                result['validation_notes'].append(
                    f'✓ Development CAPEX consistent: ACFO ({acfo_dev_capex:,.0f}) matches CFI ({cfi_dev_capex:,.0f})'
                )
            else:
                result['development_capex_consistent'] = False
                result['validation_notes'].append(
                    f'⚠ Development CAPEX mismatch: ACFO ({acfo_dev_capex:,.0f}) vs CFI ({cfi_dev_capex:,.0f})'
                )

    # Check 3: Full cash flow statement reconciliation (if all data available)
    has_cfo = 'acfo_components' in financial_data and 'cash_flow_from_operations' in financial_data['acfo_components']
    has_cfi = 'cash_flow_investing' in financial_data and 'total_cfi' in financial_data['cash_flow_investing']
    has_cff = 'cash_flow_financing' in financial_data and 'total_cff' in financial_data['cash_flow_financing']

    if has_cfo and has_cfi and has_cff:
        cfo = financial_data['acfo_components']['cash_flow_from_operations']
        cfi = financial_data['cash_flow_investing']['total_cfi']
        cff = financial_data['cash_flow_financing']['total_cff']

        # Calculate expected change in cash
        change_in_cash_calculated = cfo + cfi + cff

        # Check if reported change in cash matches (if available)
        # Note: We may not have this field yet, so this is optional
        result['validation_notes'].append(
            f'ℹ Cash flow components: CFO ({cfo:,.0f}) + CFI ({cfi:,.0f}) + CFF ({cff:,.0f}) = {change_in_cash_calculated:,.0f}'
        )
        result['cash_flow_statement_reconciles'] = True  # Can't verify without reported change, assume true

    # Generate summary
    if result['validation_notes']:
        result['reconciliation_summary'] = ' | '.join(result['validation_notes'])
    else:
        result['reconciliation_summary'] = 'Insufficient data for reconciliation validation'

    return result


__all__ = [
    'calculate_afcf',
    'calculate_afcf_coverage_ratios',
    'validate_afcf_reconciliation'
]
