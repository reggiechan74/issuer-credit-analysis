#!/usr/bin/env python3
"""
Credit Metrics Calculation Library for Real Estate Issuers

SAFETY DESIGN:
- NO hardcoded financial data anywhere in this module
- All functions require explicit input (no defaults)
- Fail loudly with KeyError/ValueError if data missing or invalid
- Include issuer identification in all outputs

EXAMPLE USAGE (documentation only - not executable):

    # After Phase 2 extraction produces: sample_extracted_data.json
    $ python scripts/calculate_credit_metrics.py sample_extracted_data.json

    Calculating metrics for: Sample Real Estate Investment Trust
    Reporting date: 2025-06-30
    ✓ Metrics calculated and saved to calculated_metrics.json
"""

import json
import sys
from pathlib import Path


def validate_required_fields(data, required_fields):
    """
    Ensure all required fields exist - fail loudly if missing

    Args:
        data: Dictionary to validate
        required_fields: List of dot-notation field paths (e.g., 'balance_sheet.total_assets')

    Raises:
        KeyError: If any required field is missing
    """
    for field in required_fields:
        keys = field.split('.')
        current = data
        for key in keys:
            if key not in current:
                raise KeyError(
                    f"Missing required field: {field}. "
                    f"Ensure Phase 2 extraction included this field."
                )
            current = current[key]


def calculate_leverage_metrics(financial_data):
    """
    Calculate leverage metrics from standardized financial data.

    SAFETY: This function has NO defaults and NO hardcoded data.
    It will fail loudly if required data is missing.

    Args:
        financial_data (dict): Validated JSON from Phase 2 extraction
                               REQUIRED - no defaults

    Returns:
        dict: Calculated leverage metrics

    Raises:
        KeyError: If required fields are missing
        ValueError: If data validation fails
    """

    # Validate all required fields exist (fail loudly)
    required_fields = [
        'balance_sheet.total_assets',
        'balance_sheet.mortgages_noncurrent',
        'balance_sheet.mortgages_current',
        'balance_sheet.credit_facilities',
        'balance_sheet.cash'
    ]
    validate_required_fields(financial_data, required_fields)

    # Extract from provided data only
    bs = financial_data['balance_sheet']

    # Validate individual debt components (must be non-negative)
    debt_components = {
        'mortgages_noncurrent': bs['mortgages_noncurrent'],
        'mortgages_current': bs['mortgages_current'],
        'credit_facilities': bs['credit_facilities']
    }

    for component_name, value in debt_components.items():
        if value < 0:
            raise ValueError(
                f"Invalid {component_name}: {value}. "
                f"Debt components cannot be negative. Check Phase 2 extraction."
            )

    total_debt = (
        bs['mortgages_noncurrent'] +
        bs['mortgages_current'] +
        bs['credit_facilities']
    )

    # Add senior unsecured debentures if present
    if 'senior_unsecured_debentures' in bs:
        if bs['senior_unsecured_debentures'] < 0:
            raise ValueError(
                f"Invalid senior_unsecured_debentures: {bs['senior_unsecured_debentures']}. "
                f"Debt cannot be negative."
            )
        total_debt += bs['senior_unsecured_debentures']

    net_debt = total_debt - bs['cash']

    # Get total assets
    total_assets = bs['total_assets']

    # Safety checks: reasonable values
    if total_assets <= 0:
        raise ValueError(
            f"Invalid total_assets: {total_assets}. "
            f"Assets must be positive. Check Phase 2 extraction."
        )

    # Calculate metrics
    debt_to_assets_percent = (total_debt / total_assets) * 100
    net_debt_ratio = (net_debt / total_assets) * 100

    return {
        'total_debt': total_debt,
        'net_debt': net_debt,
        'gross_assets': total_assets,
        'debt_to_assets_percent': round(debt_to_assets_percent, 2),
        'net_debt_ratio': round(net_debt_ratio, 2)
    }


def calculate_ffo_from_components(financial_data):
    """
    Calculate FFO from IFRS net income using REALPAC methodology (adjustments A-U)

    Per REALPAC White Paper (Feb 2019), FFO starts from IFRS profit/loss and adds back
    non-cash and non-recurring items unique to real estate operations.

    Args:
        financial_data (dict): Validated JSON from Phase 2 with ffo_affo_components section

    Returns:
        dict: {
            'ffo_calculated': float,
            'net_income_ifrs': float,
            'total_adjustments': float,
            'adjustments_detail': dict,  # A-U breakdown
            'missing_components': list,  # flags for incomplete data
            'data_quality': str  # 'strong', 'moderate', 'limited'
        }
    """

    # Check if components section exists
    if 'ffo_affo_components' not in financial_data:
        return {
            'ffo_calculated': None,
            'error': 'No ffo_affo_components section in financial data',
            'data_quality': 'none'
        }

    components = financial_data['ffo_affo_components']

    # Require net_income_ifrs as starting point
    if 'net_income_ifrs' not in components or components['net_income_ifrs'] is None:
        return {
            'ffo_calculated': None,
            'error': 'Missing net_income_ifrs - cannot calculate FFO',
            'data_quality': 'insufficient'
        }

    net_income = components['net_income_ifrs']

    # Define all FFO adjustments (A-U) per REALPAC
    adjustment_fields = {
        'unrealized_fv_changes': 'A',
        'depreciation_real_estate': 'B',
        'amortization_tenant_allowances': 'C',
        'amortization_intangibles': 'D',
        'gains_losses_property_sales': 'E',
        'tax_on_disposals': 'F',
        'deferred_taxes': 'G',
        'impairment_losses_reversals': 'H',
        'revaluation_gains_losses': 'I',
        'transaction_costs_business_comb': 'J',
        'foreign_exchange_gains_losses': 'K',
        'sale_foreign_operations': 'L',
        'fv_changes_hedges': 'M',
        'goodwill_impairment': 'N',
        'puttable_instruments_effects': 'O',
        'discontinued_operations': 'P',
        'equity_accounted_adjustments': 'Q',
        'incremental_leasing_costs': 'R',
        'property_taxes_ifric21': 'S',
        'rou_asset_revenue_expense': 'T',
        'non_controlling_interests_ffo': 'U'
    }

    # Collect adjustments and track missing ones
    adjustments = {}
    missing_components = []
    total_adjustments = 0.0

    for field, letter in adjustment_fields.items():
        if field in components and components[field] is not None:
            value = components[field]
            adjustments[f'adjustment_{letter}_{field}'] = value
            # For adjustment U (NCI), subtract instead of add
            if letter == 'U':
                total_adjustments -= value
            else:
                total_adjustments += value
        else:
            missing_components.append(f'adjustment_{letter}')
            adjustments[f'adjustment_{letter}_{field}'] = 0.0

    # Calculate FFO
    ffo_calculated = net_income + total_adjustments

    # Assess data quality
    available_count = len(adjustment_fields) - len(missing_components)
    if available_count >= 15:  # 15+ of 21 adjustments
        data_quality = 'strong'
    elif available_count >= 8:  # 8-14 of 21 adjustments
        data_quality = 'moderate'
    else:
        data_quality = 'limited'

    return {
        'ffo_calculated': round(ffo_calculated, 0),
        'net_income_ifrs': net_income,
        'total_adjustments': round(total_adjustments, 0),
        'adjustments_detail': adjustments,
        'missing_components': missing_components,
        'available_adjustments': available_count,
        'total_adjustments_count': len(adjustment_fields),
        'data_quality': data_quality
    }


def calculate_affo_from_ffo(financial_data, ffo):
    """
    Calculate AFFO from FFO using REALPAC methodology (adjustments V-Z)

    Per REALPAC White Paper (Feb 2019), AFFO is a recurring economic earnings measure
    (NOT cash flow) that adjusts FFO for sustaining capital requirements.

    Args:
        financial_data (dict): Validated JSON from Phase 2 with ffo_affo_components section
        ffo (float): FFO value (calculated or reported)

    Returns:
        dict: {
            'affo_calculated': float,
            'ffo_starting_point': float,
            'total_adjustments': float,
            'adjustments_detail': dict,  # V-Z breakdown
            'missing_components': list,
            'calculation_method': str,  # 'actual', 'reserve', 'hybrid'
            'data_quality': str
        }
    """

    # Check if components section exists
    if 'ffo_affo_components' not in financial_data:
        return {
            'affo_calculated': None,
            'error': 'No ffo_affo_components section in financial data',
            'data_quality': 'none'
        }

    components = financial_data['ffo_affo_components']

    # Define AFFO adjustments (V-Z) per REALPAC - all are subtractions from FFO
    adjustment_fields = {
        'capex_sustaining': 'V',
        'leasing_costs': 'W',
        'tenant_improvements': 'X',
        'straight_line_rent': 'Y',
        'non_controlling_interests_affo': 'Z'
    }

    # Collect adjustments and track missing ones
    adjustments = {}
    missing_components = []
    total_adjustments = 0.0

    for field, letter in adjustment_fields.items():
        if field in components and components[field] is not None:
            value = components[field]
            adjustments[f'adjustment_{letter}_{field}'] = value
            total_adjustments += value  # All are subtractions, so add to get total deduction
        else:
            missing_components.append(f'adjustment_{letter}')
            adjustments[f'adjustment_{letter}_{field}'] = 0.0

    # Calculate AFFO (subtract adjustments from FFO)
    affo_calculated = ffo - total_adjustments

    # Get calculation method if provided
    calculation_method = components.get('calculation_method', 'unknown')

    # Assess data quality
    available_count = len(adjustment_fields) - len(missing_components)
    if available_count >= 4:  # 4-5 of 5 adjustments
        data_quality = 'strong'
    elif available_count >= 2:  # 2-3 of 5 adjustments
        data_quality = 'moderate'
    else:
        data_quality = 'limited'

    return {
        'affo_calculated': round(affo_calculated, 0),
        'ffo_starting_point': ffo,
        'total_adjustments': round(total_adjustments, 0),
        'adjustments_detail': adjustments,
        'missing_components': missing_components,
        'available_adjustments': available_count,
        'total_adjustments_count': len(adjustment_fields),
        'calculation_method': calculation_method,
        'reserve_methodology': components.get('reserve_methodology'),
        'data_quality': data_quality
    }


def validate_ffo_affo(calculated_ffo, calculated_affo, reported_ffo, reported_affo):
    """
    Compare calculated vs. reported FFO/AFFO to validate calculation accuracy

    Per REALPAC guidelines, variance > 5% should be flagged and investigated.

    Args:
        calculated_ffo (float): Calculated FFO value
        calculated_affo (float): Calculated AFFO value
        reported_ffo (float | None): Issuer-reported FFO
        reported_affo (float | None): Issuer-reported AFFO

    Returns:
        dict: {
            'ffo_variance_amount': float | None,
            'ffo_variance_percent': float | None,
            'ffo_within_threshold': bool | None,
            'affo_variance_amount': float | None,
            'affo_variance_percent': float | None,
            'affo_within_threshold': bool | None,
            'validation_notes': str
        }
    """

    result = {
        'ffo_variance_amount': None,
        'ffo_variance_percent': None,
        'ffo_within_threshold': None,
        'affo_variance_amount': None,
        'affo_variance_percent': None,
        'affo_within_threshold': None,
        'validation_notes': []
    }

    # Validate FFO
    if calculated_ffo is not None and reported_ffo is not None and reported_ffo != 0:
        ffo_variance_amount = calculated_ffo - reported_ffo
        ffo_variance_percent = (ffo_variance_amount / abs(reported_ffo)) * 100

        result['ffo_variance_amount'] = round(ffo_variance_amount, 0)
        result['ffo_variance_percent'] = round(ffo_variance_percent, 2)
        result['ffo_within_threshold'] = abs(ffo_variance_percent) <= 5.0

        if not result['ffo_within_threshold']:
            result['validation_notes'].append(
                f'FFO variance ({ffo_variance_percent:.1f}%) exceeds 5% threshold. '
                f'Review methodology differences.'
            )
        else:
            result['validation_notes'].append(
                f'FFO calculation validated: {ffo_variance_percent:.1f}% variance (within 5% threshold).'
            )
    elif calculated_ffo is not None and reported_ffo is None:
        result['validation_notes'].append(
            'Issuer did not report FFO - calculated value used.'
        )

    # Validate AFFO
    if calculated_affo is not None and reported_affo is not None and reported_affo != 0:
        affo_variance_amount = calculated_affo - reported_affo
        affo_variance_percent = (affo_variance_amount / abs(reported_affo)) * 100

        result['affo_variance_amount'] = round(affo_variance_amount, 0)
        result['affo_variance_percent'] = round(affo_variance_percent, 2)
        result['affo_within_threshold'] = abs(affo_variance_percent) <= 5.0

        if not result['affo_within_threshold']:
            result['validation_notes'].append(
                f'AFFO variance ({affo_variance_percent:.1f}%) exceeds 5% threshold. '
                f'Likely differences in CAPEX/leasing cost treatment.'
            )
        else:
            result['validation_notes'].append(
                f'AFFO calculation validated: {affo_variance_percent:.1f}% variance (within 5% threshold).'
            )
    elif calculated_affo is not None and reported_affo is None:
        result['validation_notes'].append(
            'Issuer did not report AFFO - calculated value used.'
        )

    result['validation_summary'] = ' '.join(result['validation_notes'])

    return result


def calculate_reit_metrics(financial_data):
    """
    Calculate REIT-specific metrics (FFO, AFFO, ACFO, payout ratios)

    Enhanced to support both:
    1. Issuer-reported FFO/AFFO/ACFO (original behavior)
    2. Calculated FFO/AFFO/ACFO from components (new REALPAC methodology)

    Args:
        financial_data (dict): Validated JSON from Phase 2 extraction

    Returns:
        dict: REIT metrics (including calculated FFO/AFFO/ACFO if components available)

    Raises:
        KeyError: If required fields are missing
    """

    # Check if issuer reported FFO/AFFO and if components available
    has_reported_ffo_affo = 'ffo_affo' in financial_data
    has_ffo_affo_components = 'ffo_affo_components' in financial_data
    has_acfo_components = 'acfo_components' in financial_data

    result = {}

    # Try to get issuer-reported values
    if has_reported_ffo_affo:
        required_fields = [
            'ffo_affo.ffo',
            'ffo_affo.affo',
            'ffo_affo.ffo_per_unit',
            'ffo_affo.affo_per_unit',
            'ffo_affo.distributions_per_unit'
        ]

        try:
            validate_required_fields(financial_data, required_fields)
            ffo_data = financial_data['ffo_affo']

            # Calculate payout ratios
            ffo_payout = (ffo_data['distributions_per_unit'] / ffo_data['ffo_per_unit']) * 100
            # Handle AFFO=0 case (some REITs don't report AFFO)
            affo_payout = (ffo_data['distributions_per_unit'] / ffo_data['affo_per_unit']) * 100 if ffo_data['affo_per_unit'] > 0 else 0.0

            result = {
                'ffo': ffo_data['ffo'],
                'affo': ffo_data['affo'],
                'ffo_per_unit': ffo_data['ffo_per_unit'],
                'affo_per_unit': ffo_data['affo_per_unit'],
                'distributions_per_unit': ffo_data['distributions_per_unit'],
                'ffo_payout_ratio': round(ffo_payout, 1),
                'affo_payout_ratio': round(affo_payout, 1),
                'source': 'issuer_reported'
            }
        except KeyError:
            # Some fields missing, will try to calculate
            has_reported_ffo_affo = False

    # Calculate FFO/AFFO from components if available
    if has_ffo_affo_components:
        ffo_calc_result = calculate_ffo_from_components(financial_data)

        if ffo_calc_result.get('ffo_calculated') is not None:
            # We have calculated FFO, now calculate AFFO
            affo_calc_result = calculate_affo_from_ffo(
                financial_data,
                ffo_calc_result['ffo_calculated']
            )

            # Validate against reported values if available
            validation = validate_ffo_affo(
                ffo_calc_result['ffo_calculated'],
                affo_calc_result['affo_calculated'],
                result.get('ffo'),
                result.get('affo')
            )

            # Add calculated values to result
            result['ffo_calculated'] = ffo_calc_result['ffo_calculated']
            result['affo_calculated'] = affo_calc_result['affo_calculated']
            result['ffo_calculation_detail'] = ffo_calc_result
            result['affo_calculation_detail'] = affo_calc_result
            result['validation'] = validation

            # If no reported values, use calculated values
            if not has_reported_ffo_affo or 'ffo' not in result:
                result['ffo'] = ffo_calc_result['ffo_calculated']
                result['affo'] = affo_calc_result['affo_calculated']
                result['source'] = 'calculated_from_components'

                # Calculate per-unit metrics if shares outstanding available
                if 'balance_sheet' in financial_data and 'common_units_outstanding' in financial_data['balance_sheet']:
                    units = financial_data['balance_sheet']['common_units_outstanding']
                    if units > 0:
                        result['ffo_per_unit'] = round(result['ffo'] / units, 4)
                        result['affo_per_unit'] = round(result['affo'] / units, 4)

                        # Calculate payout ratios if distributions available
                        if 'ffo_affo' in financial_data and 'distributions_per_unit' in financial_data['ffo_affo']:
                            dist = financial_data['ffo_affo']['distributions_per_unit']
                            result['distributions_per_unit'] = dist
                            result['ffo_payout_ratio'] = round((dist / result['ffo_per_unit']) * 100, 1)
                            result['affo_payout_ratio'] = round((dist / result['affo_per_unit']) * 100, 1)

    # Calculate ACFO from components if available
    if has_acfo_components:
        acfo_calc_result = calculate_acfo_from_components(financial_data)

        if acfo_calc_result.get('acfo_calculated') is not None:
            # Get reported ACFO if available (rare, but some issuers report it)
            reported_acfo = None
            if 'ffo_affo' in financial_data and 'acfo' in financial_data['ffo_affo']:
                reported_acfo = financial_data['ffo_affo']['acfo']

            # Validate against reported ACFO if available
            acfo_validation = validate_acfo(
                acfo_calc_result['acfo_calculated'],
                reported_acfo
            )

            # Add ACFO to result
            result['acfo_calculated'] = acfo_calc_result['acfo_calculated']
            result['acfo_calculation_detail'] = acfo_calc_result
            result['acfo_validation'] = acfo_validation

            # If no reported ACFO, use calculated value
            if reported_acfo is None:
                result['acfo'] = acfo_calc_result['acfo_calculated']

                # Calculate per-unit ACFO if shares outstanding available
                if 'balance_sheet' in financial_data and 'common_units_outstanding' in financial_data['balance_sheet']:
                    units = financial_data['balance_sheet']['common_units_outstanding']
                    if units > 0:
                        result['acfo_per_unit'] = round(result['acfo'] / units, 4)

                        # Calculate ACFO payout ratio if distributions available
                        if 'distributions_per_unit' in result:
                            result['acfo_payout_ratio'] = round((result['distributions_per_unit'] / result['acfo_per_unit']) * 100, 1)
            else:
                result['acfo'] = reported_acfo

    # If we still don't have any FFO/AFFO data, raise error
    if 'ffo' not in result or 'affo' not in result:
        raise KeyError(
            "Missing FFO/AFFO data. Need either: "
            "(1) issuer-reported ffo_affo section, or "
            "(2) ffo_affo_components section to calculate"
        )

    return result


def calculate_acfo_from_components(financial_data):
    """
    Calculate ACFO from IFRS Cash Flow from Operations using REALPAC methodology (17 adjustments)

    Per REALPAC ACFO White Paper (January 2023), ACFO is a sustainable economic cash flow measure
    that starts from IFRS CFO and applies adjustments for recurring vs non-recurring items.

    CRITICAL: CAPEX, leasing costs, and tenant improvements MUST match AFFO values.

    Args:
        financial_data (dict): Validated JSON from Phase 2 with acfo_components section

    Returns:
        dict: {
            'acfo_calculated': float,
            'cash_flow_from_operations': float,
            'total_adjustments': float,
            'adjustments_detail': dict,  # All 17 adjustments breakdown
            'missing_components': list,
            'calculation_method': str,  # 'actual', 'reserve', 'hybrid'
            'jv_treatment_method': str,  # 'distributions' or 'acfo'
            'consistency_checks': dict,  # Validation against AFFO
            'data_quality': str  # 'strong', 'moderate', 'limited'
        }
    """

    # Check if components section exists
    if 'acfo_components' not in financial_data:
        return {
            'acfo_calculated': None,
            'error': 'No acfo_components section in financial data',
            'data_quality': 'none'
        }

    components = financial_data['acfo_components']

    # Require cash_flow_from_operations as starting point
    if 'cash_flow_from_operations' not in components or components['cash_flow_from_operations'] is None:
        return {
            'acfo_calculated': None,
            'error': 'Missing cash_flow_from_operations - cannot calculate ACFO',
            'data_quality': 'insufficient'
        }

    cfo = components['cash_flow_from_operations']

    # Define all ACFO adjustments (17 adjustments per REALPAC Jan 2023)
    # Adjustments 1-17 with clear categorization
    adjustment_fields = {
        # Working capital & financing
        'change_in_working_capital': '1',
        'interest_financing': '2',
        # Joint ventures (3 fields, mutually exclusive)
        'jv_distributions': '3a',
        'jv_acfo': '3b',
        'jv_notional_interest': '3c',
        # Capital expenditures & leasing (MUST match AFFO)
        'capex_sustaining_acfo': '4',
        'capex_development_acfo': '4_dev',  # Disclosure only
        'leasing_costs_external': '5',
        'tenant_improvements_acfo': '6',
        # Investment & tax items
        'realized_investment_gains_losses': '7',
        'taxes_non_operating': '8',
        # Transaction costs
        'transaction_costs_acquisitions': '9',
        'transaction_costs_disposals': '10',
        # Financing items
        'deferred_financing_fees': '11',
        'debt_termination_costs': '12',
        'off_market_debt_favorable': '13a',
        'off_market_debt_unfavorable': '13b',
        # Interest timing
        'interest_income_timing': '14a',
        'interest_expense_timing': '14b',
        # Puttable instruments (IAS 32)
        'puttable_instruments_distributions': '15',
        # ROU assets (IFRS 16) - 4 components
        'rou_sublease_principal_received': '16a',
        'rou_sublease_interest_received': '16b',
        'rou_lease_principal_paid': '16c',
        'rou_depreciation_amortization': '16d',
        # Non-controlling interests
        'non_controlling_interests_acfo': '17a',
        'nci_puttable_units': '17b'
    }

    # Collect adjustments and track missing ones
    adjustments = {}
    missing_components = []
    total_adjustments = 0.0

    for field, adj_num in adjustment_fields.items():
        if field in components and components[field] is not None:
            value = components[field]
            adjustments[f'adjustment_{adj_num}_{field}'] = value
            total_adjustments += value
        else:
            missing_components.append(f'adjustment_{adj_num}')
            adjustments[f'adjustment_{adj_num}_{field}'] = 0.0

    # Calculate ACFO
    acfo_calculated = cfo + total_adjustments

    # Get calculation methods if provided
    calculation_method = components.get('calculation_method_acfo', 'unknown')
    jv_treatment_method = components.get('jv_treatment_method', 'unknown')
    reserve_methodology = components.get('reserve_methodology_acfo')

    # Check consistency with AFFO (critical requirement)
    consistency_checks = {}
    if 'ffo_affo_components' in financial_data:
        affo_components = financial_data['ffo_affo_components']

        # CAPEX must match
        if 'capex_sustaining' in affo_components and 'capex_sustaining_acfo' in components:
            affo_capex = affo_components['capex_sustaining']
            acfo_capex = components['capex_sustaining_acfo']
            if affo_capex is not None and acfo_capex is not None:
                consistency_checks['capex_match'] = (affo_capex == acfo_capex)
                consistency_checks['capex_variance'] = acfo_capex - affo_capex

        # Tenant improvements must match
        if 'tenant_improvements' in affo_components and 'tenant_improvements_acfo' in components:
            affo_ti = affo_components['tenant_improvements']
            acfo_ti = components['tenant_improvements_acfo']
            if affo_ti is not None and acfo_ti is not None:
                consistency_checks['tenant_improvements_match'] = (affo_ti == acfo_ti)
                consistency_checks['tenant_improvements_variance'] = acfo_ti - affo_ti

    # Assess data quality
    # ACFO has 17 core adjustments (excluding development CAPEX disclosure)
    core_adjustments = 17
    available_count = len([f for f in adjustment_fields.keys() if f in components and components[f] is not None])

    if available_count >= 12:  # 12+ of 17 adjustments
        data_quality = 'strong'
    elif available_count >= 6:  # 6-11 of 17 adjustments
        data_quality = 'moderate'
    else:
        data_quality = 'limited'

    return {
        'acfo_calculated': round(acfo_calculated, 0),
        'cash_flow_from_operations': cfo,
        'total_adjustments': round(total_adjustments, 0),
        'adjustments_detail': adjustments,
        'missing_components': missing_components,
        'available_adjustments': available_count,
        'total_adjustments_count': core_adjustments,
        'calculation_method': calculation_method,
        'jv_treatment_method': jv_treatment_method,
        'reserve_methodology': reserve_methodology,
        'consistency_checks': consistency_checks,
        'data_quality': data_quality
    }


def validate_acfo(calculated_acfo, reported_acfo):
    """
    Compare calculated vs. reported ACFO to validate calculation accuracy

    Per REALPAC guidelines, variance > 5% should be flagged and investigated.

    Args:
        calculated_acfo (float): Calculated ACFO value
        reported_acfo (float | None): Issuer-reported ACFO

    Returns:
        dict: {
            'acfo_variance_amount': float | None,
            'acfo_variance_percent': float | None,
            'acfo_within_threshold': bool | None,
            'validation_notes': str
        }
    """

    result = {
        'acfo_variance_amount': None,
        'acfo_variance_percent': None,
        'acfo_within_threshold': None,
        'validation_notes': []
    }

    # Validate ACFO
    if calculated_acfo is not None and reported_acfo is not None and reported_acfo != 0:
        acfo_variance_amount = calculated_acfo - reported_acfo
        acfo_variance_percent = (acfo_variance_amount / abs(reported_acfo)) * 100

        result['acfo_variance_amount'] = round(acfo_variance_amount, 0)
        result['acfo_variance_percent'] = round(acfo_variance_percent, 2)
        result['acfo_within_threshold'] = abs(acfo_variance_percent) <= 5.0

        if not result['acfo_within_threshold']:
            result['validation_notes'].append(
                f'ACFO variance ({acfo_variance_percent:.1f}%) exceeds 5% threshold. '
                f'Review methodology differences (joint venture treatment, CAPEX/leasing cost methods).'
            )
        else:
            result['validation_notes'].append(
                f'ACFO calculation validated: {acfo_variance_percent:.1f}% variance (within 5% threshold).'
            )
    elif calculated_acfo is not None and reported_acfo is None:
        result['validation_notes'].append(
            'Issuer did not report ACFO - calculated value used.'
        )

    result['validation_summary'] = ' '.join(result['validation_notes'])

    return result


def generate_acfo_reconciliation(financial_data):
    """
    Generate IFRS CFO → ACFO reconciliation table per REALPAC format

    This creates a detailed reconciliation showing all adjustments from
    IFRS Cash Flow from Operations to ACFO, suitable for disclosure in reports.

    Args:
        financial_data (dict): Validated JSON from Phase 2

    Returns:
        dict: Complete reconciliation table with line items, or None if insufficient data
    """

    if 'acfo_components' not in financial_data:
        return None

    components = financial_data['acfo_components']

    if 'cash_flow_from_operations' not in components or components['cash_flow_from_operations'] is None:
        return None

    # Calculate ACFO
    acfo_result = calculate_acfo_from_components(financial_data)
    if acfo_result.get('acfo_calculated') is None:
        return None

    # Build reconciliation table
    reconciliation = {
        'starting_point': {
            'description': 'IFRS Cash Flow from Operations',
            'amount': components['cash_flow_from_operations']
        },
        'acfo_adjustments': [],
        'acfo_total': {
            'description': 'Adjusted Cash Flow from Operations (ACFO)',
            'amount': acfo_result['acfo_calculated']
        },
        'metadata': {
            'data_quality': acfo_result['data_quality'],
            'calculation_method': acfo_result.get('calculation_method', 'unknown'),
            'jv_treatment_method': acfo_result.get('jv_treatment_method', 'unknown'),
            'reserve_methodology': acfo_result.get('reserve_methodology'),
            'missing_components': acfo_result['missing_components'],
            'consistency_checks': acfo_result.get('consistency_checks', {})
        }
    }

    # Add ACFO adjustments (17 adjustments per REALPAC Jan 2023)
    acfo_adjustment_names = {
        'adjustment_1_change_in_working_capital': '1. Change in working capital (non-sustainable fluctuations)',
        'adjustment_2_interest_financing': '2. Interest expense included in financing activities',
        'adjustment_3a_jv_distributions': '3. Distributions from joint ventures',
        'adjustment_3b_jv_acfo': '3. ACFO from joint ventures (alternative)',
        'adjustment_3c_jv_notional_interest': '3. Notional interest on JV development',
        'adjustment_4_capex_sustaining_acfo': '4. Sustaining capital expenditures',
        'adjustment_4_dev_capex_development_acfo': '4. Development CAPEX (disclosure only, excluded from ACFO)',
        'adjustment_5_leasing_costs_external': '5. External leasing costs',
        'adjustment_6_tenant_improvements_acfo': '6. Sustaining tenant improvements',
        'adjustment_7_realized_investment_gains_losses': '7. Realized gains/losses on marketable securities',
        'adjustment_8_taxes_non_operating': '8. Taxes related to non-operating activities',
        'adjustment_9_transaction_costs_acquisitions': '9. Transaction costs for acquiring properties',
        'adjustment_10_transaction_costs_disposals': '10. Transaction costs for disposing properties',
        'adjustment_11_deferred_financing_fees': '11. Deferred financing fees (amortization)',
        'adjustment_12_debt_termination_costs': '12. Costs to terminate debt',
        'adjustment_13a_off_market_debt_favorable': '13. Favorable off-market debt adjustments',
        'adjustment_13b_off_market_debt_unfavorable': '13. Unfavorable off-market debt adjustments',
        'adjustment_14a_interest_income_timing': '14. Interest income timing adjustments',
        'adjustment_14b_interest_expense_timing': '14. Interest expense timing adjustments',
        'adjustment_15_puttable_instruments_distributions': '15. Distributions on puttable instruments (IAS 32)',
        'adjustment_16a_rou_sublease_principal_received': '16. Principal from finance lease subleases (IFRS 16)',
        'adjustment_16b_rou_sublease_interest_received': '16. Interest from finance lease subleases (IFRS 16)',
        'adjustment_16c_rou_lease_principal_paid': '16. Principal payments on ground leases (IFRS 16)',
        'adjustment_16d_rou_depreciation_amortization': '16. Depreciation/amortization on ROU assets (IFRS 16)',
        'adjustment_17a_non_controlling_interests_acfo': '17. Non-controlling interests (ACFO adjustments)',
        'adjustment_17b_nci_puttable_units': '17. NCI for puttable units as liabilities (IAS 32)'
    }

    for adj_key, amount in acfo_result['adjustments_detail'].items():
        if amount != 0.0:  # Only include non-zero adjustments
            reconciliation['acfo_adjustments'].append({
                'description': acfo_adjustment_names.get(adj_key, adj_key),
                'amount': amount
            })

    return reconciliation


def generate_ffo_affo_reconciliation(financial_data):
    """
    Generate IFRS P&L → FFO → AFFO reconciliation table per REALPAC format

    This creates a detailed reconciliation showing all adjustments from
    IFRS net income through FFO to AFFO, suitable for disclosure in reports.

    Args:
        financial_data (dict): Validated JSON from Phase 2

    Returns:
        dict: Complete reconciliation table with line items, or None if insufficient data
    """

    if 'ffo_affo_components' not in financial_data:
        return None

    components = financial_data['ffo_affo_components']

    if 'net_income_ifrs' not in components or components['net_income_ifrs'] is None:
        return None

    # Calculate FFO and AFFO
    ffo_result = calculate_ffo_from_components(financial_data)
    if ffo_result.get('ffo_calculated') is None:
        return None

    affo_result = calculate_affo_from_ffo(financial_data, ffo_result['ffo_calculated'])

    # Build reconciliation table
    reconciliation = {
        'starting_point': {
            'description': 'IFRS Net Income (Profit or Loss)',
            'amount': components['net_income_ifrs']
        },
        'ffo_adjustments': [],
        'ffo_total': {
            'description': 'Funds From Operations (FFO)',
            'amount': ffo_result['ffo_calculated']
        },
        'affo_adjustments': [],
        'affo_total': {
            'description': 'Adjusted Funds From Operations (AFFO)',
            'amount': affo_result['affo_calculated']
        },
        'metadata': {
            'ffo_data_quality': ffo_result['data_quality'],
            'affo_data_quality': affo_result['data_quality'],
            'methodology': components.get('calculation_method', 'unknown'),
            'missing_ffo_components': ffo_result['missing_components'],
            'missing_affo_components': affo_result['missing_components']
        }
    }

    # Add FFO adjustments (A-U)
    ffo_adjustment_names = {
        'adjustment_A_unrealized_fv_changes': 'A. Unrealized fair value changes (investment properties)',
        'adjustment_B_depreciation_real_estate': 'B. Depreciation of depreciable real estate',
        'adjustment_C_amortization_tenant_allowances': 'C. Amortization of tenant allowances (fit-out)',
        'adjustment_D_amortization_intangibles': 'D. Amortization of tenant/customer intangibles',
        'adjustment_E_gains_losses_property_sales': 'E. Gains/losses from property sales',
        'adjustment_F_tax_on_disposals': 'F. Tax on property disposals',
        'adjustment_G_deferred_taxes': 'G. Deferred taxes',
        'adjustment_H_impairment_losses_reversals': 'H. Impairment losses/reversals',
        'adjustment_I_revaluation_gains_losses': 'I. Revaluation gains/losses (owner-occupied)',
        'adjustment_J_transaction_costs_business_comb': 'J. Transaction costs (business combinations)',
        'adjustment_K_foreign_exchange_gains_losses': 'K. Foreign exchange gains/losses',
        'adjustment_L_sale_foreign_operations': 'L. Gain/loss on sale of foreign operations',
        'adjustment_M_fv_changes_hedges': 'M. Fair value changes (economically effective hedges)',
        'adjustment_N_goodwill_impairment': 'N. Goodwill impairment/negative goodwill',
        'adjustment_O_puttable_instruments_effects': 'O. Effects of puttable instruments',
        'adjustment_P_discontinued_operations': 'P. Results of discontinued operations',
        'adjustment_Q_equity_accounted_adjustments': 'Q. Equity accounted entities adjustments',
        'adjustment_R_incremental_leasing_costs': 'R. Incremental leasing costs',
        'adjustment_S_property_taxes_ifric21': 'S. Property taxes (IFRIC 21)',
        'adjustment_T_rou_asset_revenue_expense': 'T. ROU asset revenue/expenses (IFRS 16)',
        'adjustment_U_non_controlling_interests_ffo': 'U. Non-controlling interests'
    }

    for adj_key, amount in ffo_result['adjustments_detail'].items():
        if amount != 0.0:  # Only include non-zero adjustments
            reconciliation['ffo_adjustments'].append({
                'description': ffo_adjustment_names.get(adj_key, adj_key),
                'amount': amount
            })

    # Add AFFO adjustments (V-Z)
    affo_adjustment_names = {
        'adjustment_V_capex_sustaining': 'V. Capital expenditures (sustaining/maintenance)',
        'adjustment_W_leasing_costs': 'W. Leasing costs',
        'adjustment_X_tenant_improvements': 'X. Tenant improvements',
        'adjustment_Y_straight_line_rent': 'Y. Straight-line rent adjustment',
        'adjustment_Z_non_controlling_interests_affo': 'Z. Non-controlling interests'
    }

    for adj_key, amount in affo_result['adjustments_detail'].items():
        if amount != 0.0:  # Only include non-zero adjustments
            reconciliation['affo_adjustments'].append({
                'description': affo_adjustment_names.get(adj_key, adj_key),
                'amount': -amount  # Negative because these are deductions from FFO
            })

    return reconciliation


def format_reconciliation_table(reconciliation):
    """
    Format reconciliation table as markdown for reports

    Args:
        reconciliation (dict): Output from generate_ffo_affo_reconciliation()

    Returns:
        str: Markdown-formatted reconciliation table
    """

    if not reconciliation:
        return "**FFO/AFFO Reconciliation**: Insufficient data to generate reconciliation table.\n"

    lines = []
    lines.append("## FFO/AFFO Reconciliation Table (REALPAC Methodology)")
    lines.append("")
    lines.append("| Line Item | Amount (000s) |")
    lines.append("|-----------|---------------|")

    # Starting point
    lines.append(f"| **{reconciliation['starting_point']['description']}** | **{reconciliation['starting_point']['amount']:,.0f}** |")

    # FFO adjustments
    if reconciliation['ffo_adjustments']:
        lines.append("| **FFO Adjustments (A-U):** | |")
        for adj in reconciliation['ffo_adjustments']:
            sign = "+" if adj['amount'] >= 0 else ""
            lines.append(f"| {adj['description']} | {sign}{adj['amount']:,.0f} |")

    # FFO total
    lines.append(f"| **{reconciliation['ffo_total']['description']}** | **{reconciliation['ffo_total']['amount']:,.0f}** |")

    # AFFO adjustments
    if reconciliation['affo_adjustments']:
        lines.append("| **AFFO Adjustments (V-Z):** | |")
        for adj in reconciliation['affo_adjustments']:
            sign = "+" if adj['amount'] >= 0 else ""
            lines.append(f"| {adj['description']} | {sign}{adj['amount']:,.0f} |")

    # AFFO total
    lines.append(f"| **{reconciliation['affo_total']['description']}** | **{reconciliation['affo_total']['amount']:,.0f}** |")

    # Add metadata notes
    lines.append("")
    lines.append("**Data Quality:**")
    lines.append(f"- FFO: {reconciliation['metadata']['ffo_data_quality'].upper()}")
    lines.append(f"- AFFO: {reconciliation['metadata']['affo_data_quality'].upper()}")

    if reconciliation['metadata']['missing_ffo_components']:
        lines.append(f"- Missing FFO components: {len(reconciliation['metadata']['missing_ffo_components'])}")

    if reconciliation['metadata']['missing_affo_components']:
        lines.append(f"- Missing AFFO components: {len(reconciliation['metadata']['missing_affo_components'])}")

    lines.append("")
    lines.append("*Source: Calculated per REALPAC White Paper on FFO & AFFO for IFRS (February 2019)*")

    return "\n".join(lines)


def format_acfo_reconciliation_table(reconciliation):
    """
    Format ACFO reconciliation table as markdown for reports

    Args:
        reconciliation (dict): Output from generate_acfo_reconciliation()

    Returns:
        str: Markdown-formatted ACFO reconciliation table
    """

    if not reconciliation:
        return "**ACFO Reconciliation**: Insufficient data to generate reconciliation table.\n"

    lines = []
    lines.append("## ACFO Reconciliation Table (REALPAC Methodology)")
    lines.append("")
    lines.append("| Line Item | Amount (000s) |")
    lines.append("|-----------|---------------|")

    # Starting point
    lines.append(f"| **{reconciliation['starting_point']['description']}** | **{reconciliation['starting_point']['amount']:,.0f}** |")

    # ACFO adjustments
    if reconciliation['acfo_adjustments']:
        lines.append("| **ACFO Adjustments (1-17):** | |")
        for adj in reconciliation['acfo_adjustments']:
            sign = "+" if adj['amount'] >= 0 else ""
            lines.append(f"| {adj['description']} | {sign}{adj['amount']:,.0f} |")

    # ACFO total
    lines.append(f"| **{reconciliation['acfo_total']['description']}** | **{reconciliation['acfo_total']['amount']:,.0f}** |")

    # Add metadata notes
    lines.append("")
    lines.append("**Data Quality:**")
    lines.append(f"- ACFO: {reconciliation['metadata']['data_quality'].upper()}")
    lines.append(f"- Calculation Method: {reconciliation['metadata']['calculation_method']}")
    lines.append(f"- JV Treatment: {reconciliation['metadata']['jv_treatment_method']}")

    if reconciliation['metadata']['missing_components']:
        lines.append(f"- Missing components: {len(reconciliation['metadata']['missing_components'])}")

    # Consistency checks
    if reconciliation['metadata'].get('consistency_checks'):
        lines.append("")
        lines.append("**Consistency Checks (vs AFFO):**")
        checks = reconciliation['metadata']['consistency_checks']

        if 'capex_match' in checks:
            status = "✅ Match" if checks['capex_match'] else f"⚠️ Variance: {checks.get('capex_variance', 0):,.0f}"
            lines.append(f"- CAPEX (sustaining): {status}")

        if 'tenant_improvements_match' in checks:
            status = "✅ Match" if checks['tenant_improvements_match'] else f"⚠️ Variance: {checks.get('tenant_improvements_variance', 0):,.0f}"
            lines.append(f"- Tenant Improvements: {status}")

    if reconciliation['metadata'].get('reserve_methodology'):
        lines.append(f"- Reserve Methodology: {reconciliation['metadata']['reserve_methodology']}")

    lines.append("")
    lines.append("*Source: Calculated per REALPAC ACFO White Paper for IFRS (January 2023)*")

    return "\n".join(lines)


def calculate_coverage_ratios(financial_data):
    """
    Calculate interest coverage and EBITDA-based ratios

    Args:
        financial_data (dict): Validated JSON from Phase 2 extraction

    Returns:
        dict: Coverage ratios

    Raises:
        KeyError: If required fields are missing
        ValueError: If calculations produce invalid results
    """

    required_fields = [
        'income_statement.noi',
        'income_statement.interest_expense'
    ]
    validate_required_fields(financial_data, required_fields)

    income = financial_data['income_statement']

    noi = income['noi']
    interest_expense = income['interest_expense']

    if interest_expense <= 0:
        raise ValueError(
            f"Invalid interest_expense: {interest_expense}. "
            f"Interest expense must be positive."
        )

    # NOI / Interest Coverage (period coverage is same as annualized if both same period)
    noi_interest_coverage = noi / interest_expense

    # Detect reporting period to determine correct annualization factor
    reporting_period = financial_data.get('reporting_period', '').lower()

    if 'six months' in reporting_period or '6 months' in reporting_period or 'six-month' in reporting_period:
        # 6-month period: multiply by 2 to annualize
        annualization_factor = 2
        period_label = 'semi_annual'
    elif 'three months' in reporting_period or '3 months' in reporting_period or 'quarterly' in reporting_period or 'quarter' in reporting_period:
        # Quarterly period: multiply by 4 to annualize
        annualization_factor = 4
        period_label = 'quarterly'
    elif 'year' in reporting_period or 'annual' in reporting_period:
        # Already annual
        annualization_factor = 1
        period_label = 'annual'
    else:
        # Default to quarterly with warning if period unclear
        print(f"⚠️  WARNING: Unable to detect reporting period from '{financial_data.get('reporting_period', 'Unknown')}'")
        print(f"   Defaulting to quarterly (×4 multiplier). Verify annualized interest expense manually.")
        annualization_factor = 4
        period_label = 'quarterly_assumed'

    annualized_interest = interest_expense * annualization_factor

    return {
        'noi_interest_coverage': round(noi_interest_coverage, 2),
        'annualized_interest_expense': annualized_interest,
        'period_interest_expense': interest_expense,
        'annualization_factor': annualization_factor,
        'detected_period': period_label
    }


def calculate_all_metrics(financial_data):
    """
    Calculate all metrics and return comprehensive results

    Args:
        financial_data (dict): Validated JSON from Phase 2

    Returns:
        dict: Complete metrics with issuer identification
    """

    # Validate issuer identification exists
    if 'issuer_name' not in financial_data:
        raise KeyError("Missing issuer_name in financial_data")
    if 'reporting_date' not in financial_data:
        raise KeyError("Missing reporting_date in financial_data")

    # Calculate all metric categories
    leverage_metrics = calculate_leverage_metrics(financial_data)
    reit_metrics = calculate_reit_metrics(financial_data)
    coverage_ratios = calculate_coverage_ratios(financial_data)

    # Extract portfolio metrics if available
    portfolio_metrics = {}
    if 'portfolio' in financial_data:
        portfolio = financial_data['portfolio']

        # Handle null values by converting to 0
        gla = portfolio.get('total_gla_sf')
        if gla is None:
            gla = 0

        # Support both naming conventions for occupancy_with_commitments
        occ_with_commitments = (
            portfolio.get('occupancy_with_commitments') or
            portfolio.get('occupancy_including_commitments', 0)
        )

        # Support both naming conventions for same property NOI growth
        noi_growth = (
            portfolio.get('same_property_noi_growth_6m') or
            portfolio.get('same_property_noi_growth', 0)
        )

        portfolio_metrics = {
            'total_properties': portfolio.get('property_count', portfolio.get('total_properties', 0)),
            'gla_sf': gla,
            'occupancy_rate': portfolio.get('occupancy_rate', 0),
            'occupancy_including_commitments': occ_with_commitments,
            'same_property_noi_growth': noi_growth
        }

    # Assemble complete output with issuer identification
    return {
        'issuer_name': financial_data['issuer_name'],
        'reporting_date': financial_data['reporting_date'],
        'reporting_period': financial_data.get('reporting_period', 'Unknown'),
        'currency': financial_data.get('currency', 'Unknown'),
        'leverage_metrics': leverage_metrics,
        'reit_metrics': reit_metrics,
        'coverage_ratios': coverage_ratios,
        'portfolio_metrics': portfolio_metrics
    }


def main():
    """Main execution - command-line interface"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Calculate credit metrics from extracted financial data',
        epilog='Example: python calculate_credit_metrics.py --issuer-name "Artis REIT" phase2_extracted_data.json'
    )
    parser.add_argument(
        'input_json',
        help='Path to Phase 2 extracted data JSON (REQUIRED)'
    )
    parser.add_argument(
        '--issuer-name',
        default=None,
        help='Issuer name (for folder organization, optional - can infer from input path)'
    )
    parser.add_argument(
        '--output',
        default=None,
        help='Output path for calculated metrics (default: auto-generated from input path)'
    )

    args = parser.parse_args()

    # MUST provide input file - no defaults
    input_path = Path(args.input_json)

    if not input_path.exists():
        print(f"❌ Error: Input file not found: {input_path}")
        sys.exit(1)

    # Auto-generate output path if not specified (same folder as input)
    if args.output is None:
        args.output = str(input_path.parent / 'phase3_calculated_metrics.json')

    print(f"📊 Loading financial data from: {input_path}")

    try:
        with open(input_path, 'r') as f:
            financial_data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in input file: {e}")
        sys.exit(1)

    # Validate issuer identification
    if 'issuer_name' not in financial_data:
        print("❌ Error: Missing issuer_name in input data")
        print("   Phase 2 extraction must include issuer_name field")
        sys.exit(1)

    print(f"\n🏢 Calculating metrics for: {financial_data['issuer_name']}")
    print(f"📅 Reporting date: {financial_data['reporting_date']}")

    try:
        # Calculate all metrics
        print("\n⚙️  Calculating leverage metrics...")
        print("⚙️  Calculating REIT metrics...")
        print("⚙️  Calculating coverage ratios...")

        result = calculate_all_metrics(financial_data)

        # Save results
        output_path = Path(args.output)
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)

        print(f"\n✅ Success! Metrics calculated and saved to: {output_path}")

        # Print summary
        print("\n📊 SUMMARY")
        print("=" * 60)
        print(f"Issuer: {result['issuer_name']}")
        print(f"Period: {result['reporting_period']}")
        print(f"\nLeverage:")
        print(f"  • Total Debt: {result['leverage_metrics']['total_debt']:,.0f}")
        print(f"  • Debt/Assets: {result['leverage_metrics']['debt_to_assets_percent']:.1f}%")
        print(f"\nREIT Metrics:")
        print(f"  • FFO per Unit: {result['reit_metrics']['ffo_per_unit']:.2f}")
        print(f"  • AFFO Payout: {result['reit_metrics']['affo_payout_ratio']:.1f}%")
        print(f"\nCoverage:")
        print(f"  • NOI/Interest: {result['coverage_ratios']['noi_interest_coverage']:.2f}x")
        print("=" * 60)

        sys.exit(0)

    except KeyError as e:
        print(f"\n❌ Error: Missing required field: {e}")
        print("   Check that Phase 2 extraction completed successfully")
        sys.exit(1)

    except ValueError as e:
        print(f"\n❌ Error: Invalid data: {e}")
        sys.exit(1)

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
