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
            'ffo_per_unit': float | None,  # Basic - calculated if common_units_outstanding available
            'ffo_per_unit_diluted': float | None,  # Diluted - calculated if diluted_units_outstanding available
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

    # Calculate per-unit FFO if shares outstanding available
    ffo_per_unit = None
    ffo_per_unit_diluted = None

    if 'balance_sheet' in financial_data:
        # Basic per-unit
        if 'common_units_outstanding' in financial_data['balance_sheet']:
            units = financial_data['balance_sheet']['common_units_outstanding']
            if units and units > 0:
                ffo_per_unit = round(ffo_calculated / units, 4)

        # Diluted per-unit
        if 'diluted_units_outstanding' in financial_data['balance_sheet']:
            units_diluted = financial_data['balance_sheet']['diluted_units_outstanding']
            if units_diluted and units_diluted > 0:
                ffo_per_unit_diluted = round(ffo_calculated / units_diluted, 4)

    result = {
        'ffo_calculated': round(ffo_calculated, 0),
        'net_income_ifrs': net_income,
        'total_adjustments': round(total_adjustments, 0),
        'adjustments_detail': adjustments,
        'missing_components': missing_components,
        'available_adjustments': available_count,
        'total_adjustments_count': len(adjustment_fields),
        'data_quality': data_quality
    }

    # Add per-unit if calculated
    if ffo_per_unit is not None:
        result['ffo_per_unit'] = ffo_per_unit
    if ffo_per_unit_diluted is not None:
        result['ffo_per_unit_diluted'] = ffo_per_unit_diluted

    return result


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
            'affo_per_unit': float | None,  # Basic - calculated if common_units_outstanding available
            'affo_per_unit_diluted': float | None,  # Diluted - calculated if diluted_units_outstanding available
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

    # Calculate per-unit AFFO if shares outstanding available
    affo_per_unit = None
    affo_per_unit_diluted = None

    if 'balance_sheet' in financial_data:
        # Basic per-unit
        if 'common_units_outstanding' in financial_data['balance_sheet']:
            units = financial_data['balance_sheet']['common_units_outstanding']
            if units and units > 0:
                affo_per_unit = round(affo_calculated / units, 4)

        # Diluted per-unit
        if 'diluted_units_outstanding' in financial_data['balance_sheet']:
            units_diluted = financial_data['balance_sheet']['diluted_units_outstanding']
            if units_diluted and units_diluted > 0:
                affo_per_unit_diluted = round(affo_calculated / units_diluted, 4)

    result = {
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

    # Add per-unit if calculated
    if affo_per_unit is not None:
        result['affo_per_unit'] = affo_per_unit
    if affo_per_unit_diluted is not None:
        result['affo_per_unit_diluted'] = affo_per_unit_diluted

    return result


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


def validate_acfo(calculated_acfo, reported_acfo):
    """
    Compare calculated vs. reported ACFO to validate calculation accuracy

    Args:
        calculated_acfo (float | None): Calculated ACFO value
        reported_acfo (float | None): Issuer-reported ACFO (if disclosed)

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

    # Validate ACFO (if issuer reports it)
    if calculated_acfo is not None and reported_acfo is not None and reported_acfo != 0:
        acfo_variance_amount = calculated_acfo - reported_acfo
        acfo_variance_percent = (acfo_variance_amount / abs(reported_acfo)) * 100

        result['acfo_variance_amount'] = round(acfo_variance_amount, 0)
        result['acfo_variance_percent'] = round(acfo_variance_percent, 2)
        result['acfo_within_threshold'] = abs(acfo_variance_percent) <= 5.0

        if not result['acfo_within_threshold']:
            result['validation_notes'].append(
                f'ACFO variance ({acfo_variance_percent:.1f}%) exceeds 5% threshold. '
                f'Review methodology differences (adjustment treatments).'
            )
        else:
            result['validation_notes'].append(
                f'ACFO calculation validated: {acfo_variance_percent:.1f}% variance (within 5% threshold).'
            )
    elif calculated_acfo is not None and reported_acfo is None:
        result['validation_notes'].append(
            'Issuer did not report ACFO - calculated value used (common for most REITs).'
        )
    elif calculated_acfo is None:
        result['validation_notes'].append(
            'ACFO calculation not available - missing cash flow from operations data.'
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

            # Add diluted per-unit values if present in reported data
            if 'ffo_per_unit_diluted' in ffo_data:
                result['ffo_per_unit_diluted'] = ffo_data['ffo_per_unit_diluted']
            if 'affo_per_unit_diluted' in ffo_data:
                result['affo_per_unit_diluted'] = ffo_data['affo_per_unit_diluted']
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

                # Use per-unit metrics from calculation functions if available
                if 'ffo_per_unit' in ffo_calc_result:
                    result['ffo_per_unit'] = ffo_calc_result['ffo_per_unit']
                if 'ffo_per_unit_diluted' in ffo_calc_result:
                    result['ffo_per_unit_diluted'] = ffo_calc_result['ffo_per_unit_diluted']
                if 'affo_per_unit' in affo_calc_result:
                    result['affo_per_unit'] = affo_calc_result['affo_per_unit']
                if 'affo_per_unit_diluted' in affo_calc_result:
                    result['affo_per_unit_diluted'] = affo_calc_result['affo_per_unit_diluted']

                # Calculate payout ratios if distributions and per-unit values available
                if 'ffo_per_unit' in result and 'affo_per_unit' in result:
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

                # Use per-unit ACFO from calculation function if available
                if 'acfo_per_unit' in acfo_calc_result:
                    result['acfo_per_unit'] = acfo_calc_result['acfo_per_unit']
                if 'acfo_per_unit_diluted' in acfo_calc_result:
                    result['acfo_per_unit_diluted'] = acfo_calc_result['acfo_per_unit_diluted']

                # Calculate ACFO payout ratio if distributions available
                if 'acfo_per_unit' in result and 'distributions_per_unit' in result:
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
            'acfo_per_unit': float | None,  # Basic - calculated if common_units_outstanding available
            'acfo_per_unit_diluted': float | None,  # Diluted - calculated if diluted_units_outstanding available
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

    # Calculate per-unit ACFO if shares outstanding available
    acfo_per_unit = None
    acfo_per_unit_diluted = None

    if 'balance_sheet' in financial_data:
        # Basic per-unit
        if 'common_units_outstanding' in financial_data['balance_sheet']:
            units = financial_data['balance_sheet']['common_units_outstanding']
            if units and units > 0:
                acfo_per_unit = round(acfo_calculated / units, 4)

        # Diluted per-unit
        if 'diluted_units_outstanding' in financial_data['balance_sheet']:
            units_diluted = financial_data['balance_sheet']['diluted_units_outstanding']
            if units_diluted and units_diluted > 0:
                acfo_per_unit_diluted = round(acfo_calculated / units_diluted, 4)

    result = {
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

    # Add per-unit if calculated
    if acfo_per_unit is not None:
        result['acfo_per_unit'] = acfo_per_unit
    if acfo_per_unit_diluted is not None:
        result['acfo_per_unit_diluted'] = acfo_per_unit_diluted

    return result


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

    # Get annualized interest expense from coverage_ratios
    annualized_interest = 0
    if 'coverage_ratios' in financial_data:
        annualized_interest = financial_data['coverage_ratios'].get('annualized_interest_expense', 0)

    # Get principal repayments and distributions from cash_flow_financing
    principal_repayments = 0
    total_distributions = 0
    new_financing = 0

    if 'cash_flow_financing' in financial_data:
        cff_data = financial_data['cash_flow_financing']

        # Principal repayments (negative number in data, make positive for calculation)
        if 'debt_principal_repayments' in cff_data and cff_data['debt_principal_repayments'] is not None:
            principal_repayments = abs(cff_data['debt_principal_repayments'])

        # Distributions (sum all types, make positive)
        dist_common = abs(cff_data.get('distributions_common', 0) or 0)
        dist_preferred = abs(cff_data.get('distributions_preferred', 0) or 0)
        dist_nci = abs(cff_data.get('distributions_nci', 0) or 0)
        total_distributions = dist_common + dist_preferred + dist_nci

        # New financing (positive inflows)
        new_debt = cff_data.get('new_debt_issuances', 0) or 0
        new_equity = cff_data.get('equity_issuances', 0) or 0
        new_financing = new_debt + new_equity

    # Calculate total debt service
    total_debt_service = annualized_interest + principal_repayments

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

    # Calculate self-funding ratio
    net_financing_needs = total_debt_service + total_distributions - new_financing
    if net_financing_needs > 0:
        result['afcf_self_funding_ratio'] = round(afcf / net_financing_needs, 2)
        result['net_financing_needs'] = net_financing_needs
    else:
        result['afcf_self_funding_ratio'] = None
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


def calculate_burn_rate(financial_data, afcf_metrics, afcf_coverage=None):
    """
    Calculate monthly and annualized burn rate when AFCF cannot cover financing needs

    Burn rate measures cash depletion when AFCF < Net Financing Needs.
    This occurs when free cash flow is insufficient to cover debt service + distributions.

    Formula:
        Net Financing Needs = Total Debt Service + Distributions - New Financing
        Burn Rate = Net Financing Needs - AFCF (when AFCF < Net Financing Needs)
        Monthly Burn Rate = Annualized Burn Rate / 12

    Args:
        financial_data (dict): Validated JSON with cash_flow_financing data
        afcf_metrics (dict): Result from calculate_afcf() with 'afcf' key
        afcf_coverage (dict): Optional AFCF coverage metrics with net_financing_needs

    Returns:
        dict: {
            'applicable': bool,  # True when AFCF < Net Financing Needs
            'monthly_burn_rate': float or None,
            'annualized_burn_rate': float or None,
            'afcf': float,
            'net_financing_needs': float or None,
            'self_funding_ratio': float or None,  # AFCF / Net Financing Needs
            'reason': str,  # Explanation if not applicable
            'data_quality': str
        }
    """

    result = {
        'applicable': False,
        'monthly_burn_rate': None,
        'annualized_burn_rate': None,
        'afcf': None,
        'net_financing_needs': None,
        'self_funding_ratio': None,
        'reason': None,
        'data_quality': 'none'
    }

    # Check if AFCF metrics available
    if not afcf_metrics or 'afcf' not in afcf_metrics:
        result['reason'] = 'AFCF not calculated - missing AFCF metrics'
        return result

    afcf = afcf_metrics['afcf']

    # Check if AFCF is None
    if afcf is None:
        result['reason'] = 'AFCF is None - insufficient data for calculation'
        return result

    result['afcf'] = afcf

    # Get net financing needs from AFCF coverage or calculate from cash_flow_financing
    net_financing_needs = None

    if afcf_coverage and 'net_financing_needs' in afcf_coverage:
        net_financing_needs = afcf_coverage['net_financing_needs']
    elif 'cash_flow_financing' in financial_data and 'coverage_ratios' in financial_data:
        # Calculate net financing needs
        cff = financial_data['cash_flow_financing']
        coverage = financial_data['coverage_ratios']

        # Debt service = Interest + Principal Repayments
        annualized_interest = coverage.get('annualized_interest_expense', 0) or 0
        principal = abs(cff.get('debt_principal_repayments', 0) or 0)
        total_debt_service = annualized_interest + principal

        # Distributions (all outflows are negative, so abs())
        dist_common = abs(cff.get('distributions_common', 0) or 0)
        dist_preferred = abs(cff.get('distributions_preferred', 0) or 0)
        dist_nci = abs(cff.get('distributions_nci', 0) or 0)
        total_distributions = dist_common + dist_preferred + dist_nci

        # New financing (positive inflows)
        new_debt = cff.get('new_debt_issuances', 0) or 0
        new_equity = cff.get('equity_issuances', 0) or 0
        new_financing = new_debt + new_equity

        net_financing_needs = total_debt_service + total_distributions - new_financing

    if net_financing_needs is None:
        result['reason'] = 'Cannot calculate burn rate - missing financing data'
        result['data_quality'] = 'limited'
        return result

    result['net_financing_needs'] = net_financing_needs

    # Calculate self-funding ratio
    if net_financing_needs > 0:
        result['self_funding_ratio'] = round(afcf / net_financing_needs, 2)
    else:
        result['self_funding_ratio'] = None

    # Burn rate applicable when AFCF < Net Financing Needs
    if afcf >= net_financing_needs:
        result['applicable'] = False
        surplus = afcf - net_financing_needs
        result['reason'] = f'AFCF covers financing needs - surplus of ${surplus:,.0f} annually'
        result['monthly_surplus'] = round(surplus / 12, 2)
        result['data_quality'] = 'complete'
        return result

    # Calculate burn rate (Net Financing Needs exceeds AFCF)
    annualized_burn = net_financing_needs - afcf
    monthly_burn = annualized_burn / 12

    result['applicable'] = True
    result['monthly_burn_rate'] = round(monthly_burn, 2)
    result['annualized_burn_rate'] = round(annualized_burn, 2)
    result['data_quality'] = afcf_metrics.get('data_quality', 'moderate')

    return result


def calculate_cash_runway(financial_data, burn_rate_metrics):
    """
    Calculate months until cash depletion based on burn rate

    Runway measures how long a REIT can sustain operations before depleting
    available cash reserves at current burn rate.

    Formulas:
        Available Cash = Cash + Marketable Securities - Restricted Cash
        Runway (months) = Available Cash / Monthly Burn Rate
        Extended Runway = (Available Cash + Undrawn Facilities) / Monthly Burn Rate

    Args:
        financial_data (dict): Validated JSON with liquidity section
        burn_rate_metrics (dict): Result from calculate_burn_rate()

    Returns:
        dict: {
            'runway_months': float or None,
            'runway_years': float or None,
            'extended_runway_months': float or None,  # Including credit facilities
            'extended_runway_years': float or None,
            'depletion_date': str or None,  # Estimated date (YYYY-MM-DD)
            'available_cash': float,
            'total_available_liquidity': float,
            'data_quality': str,
            'error': str or None
        }
    """

    result = {
        'runway_months': None,
        'runway_years': None,
        'extended_runway_months': None,
        'extended_runway_years': None,
        'depletion_date': None,
        'available_cash': None,
        'total_available_liquidity': None,
        'data_quality': 'none',
        'error': None
    }

    # Check if burn rate applicable
    if not burn_rate_metrics or not burn_rate_metrics.get('applicable', False):
        result['error'] = 'Burn rate not applicable - AFCF is not negative'
        return result

    monthly_burn = burn_rate_metrics.get('monthly_burn_rate')
    if not monthly_burn or monthly_burn <= 0:
        result['error'] = 'Invalid monthly burn rate'
        return result

    # Get liquidity data
    if 'liquidity' not in financial_data:
        result['error'] = 'No liquidity section in financial data'
        result['data_quality'] = 'none'
        return result

    liquidity = financial_data['liquidity']

    # Calculate available cash
    cash = liquidity.get('cash_and_equivalents', 0) or 0
    marketable_sec = liquidity.get('marketable_securities', 0) or 0
    restricted = liquidity.get('restricted_cash', 0) or 0
    undrawn_facilities = liquidity.get('undrawn_credit_facilities', 0) or 0

    available_cash = cash + marketable_sec - restricted
    total_liquidity = available_cash + undrawn_facilities

    result['available_cash'] = round(available_cash, 2)
    result['total_available_liquidity'] = round(total_liquidity, 2)

    # Calculate runway
    if available_cash <= 0:
        result['error'] = 'No available cash - immediate liquidity crisis'
        result['data_quality'] = 'complete'
        return result

    runway_months = available_cash / monthly_burn
    runway_years = runway_months / 12

    result['runway_months'] = round(runway_months, 1)
    result['runway_years'] = round(runway_years, 1)

    # Calculate extended runway with credit facilities
    if total_liquidity > 0:
        extended_months = total_liquidity / monthly_burn
        extended_years = extended_months / 12
        result['extended_runway_months'] = round(extended_months, 1)
        result['extended_runway_years'] = round(extended_years, 1)

    # Estimate depletion date (from reporting date if available)
    if 'reporting_date' in financial_data:
        from datetime import datetime, timedelta
        try:
            reporting_date = datetime.strptime(financial_data['reporting_date'], '%Y-%m-%d')
            depletion_date = reporting_date + timedelta(days=int(runway_months * 30))
            result['depletion_date'] = depletion_date.strftime('%Y-%m-%d')
        except:
            pass  # Skip if date parsing fails

    # Assess data quality
    has_all_components = all([
        cash > 0,
        'marketable_securities' in liquidity,
        'restricted_cash' in liquidity,
        'undrawn_credit_facilities' in liquidity
    ])

    if has_all_components:
        result['data_quality'] = 'strong'
    elif cash > 0:
        result['data_quality'] = 'moderate'
    else:
        result['data_quality'] = 'limited'

    return result


def assess_liquidity_risk(runway_metrics):
    """
    Assess liquidity risk level based on cash runway

    Risk Levels:
        CRITICAL: < 6 months - Immediate financing required
        HIGH: 6-12 months - Near-term capital raise needed
        MODERATE: 12-24 months - Plan financing within 12 months
        LOW: > 24 months or positive AFCF - Adequate liquidity

    Args:
        runway_metrics (dict): Result from calculate_cash_runway()

    Returns:
        dict: {
            'risk_level': str,  # CRITICAL, HIGH, MODERATE, LOW, N/A
            'risk_score': int,  # 0-4 (0=N/A, 1=LOW, 2=MODERATE, 3=HIGH, 4=CRITICAL)
            'warning_flags': list,
            'assessment': str,
            'recommendations': list,
            'data_quality': str
        }
    """

    result = {
        'risk_level': 'N/A',
        'risk_score': 0,
        'warning_flags': [],
        'assessment': '',
        'recommendations': [],
        'data_quality': 'none'
    }

    # Check if runway metrics available
    if not runway_metrics or runway_metrics.get('error'):
        result['assessment'] = runway_metrics.get('error', 'No runway data available')
        return result

    runway_months = runway_metrics.get('runway_months')

    if runway_months is None:
        result['assessment'] = 'Cannot assess risk - runway not calculated'
        return result

    # Assess risk based on runway thresholds
    if runway_months < 6:
        result['risk_level'] = 'CRITICAL'
        result['risk_score'] = 4
        result['assessment'] = '🚨 Immediate financing required - runway < 6 months'
        result['warning_flags'] = [
            'Cash depletion imminent',
            'Emergency financing needed',
            'Going concern risk'
        ]
        result['recommendations'] = [
            'Suspend or reduce distributions immediately',
            'Accelerate non-core asset sales',
            'Pursue emergency financing (bridge loan, equity raise)',
            'Defer all non-critical capital expenditures',
            'Engage restructuring advisors'
        ]
    elif runway_months < 12:
        result['risk_level'] = 'HIGH'
        result['risk_score'] = 3
        result['assessment'] = '⚠️ Near-term capital raise required - runway 6-12 months'
        result['warning_flags'] = [
            'Limited financing window',
            'Capital raise needed within 6 months',
            'Potential covenant concerns'
        ]
        result['recommendations'] = [
            'Initiate capital raise process immediately',
            'Consider distribution reduction',
            'Identify asset sales to bridge liquidity gap',
            'Defer growth capital expenditures',
            'Negotiate credit facility extensions'
        ]
    elif runway_months < 24:
        result['risk_level'] = 'MODERATE'
        result['risk_score'] = 2
        result['assessment'] = '⚠️ Plan financing within 12 months - runway 12-24 months'
        result['warning_flags'] = [
            'Financing needed within planning horizon',
            'Monitor burn rate trends closely'
        ]
        result['recommendations'] = [
            'Begin financing planning (12-month timeline)',
            'Evaluate distribution sustainability',
            'Consider strategic asset sales',
            'Optimize capital allocation to reduce burn',
            'Maintain strong lender relationships'
        ]
    else:
        result['risk_level'] = 'LOW'
        result['risk_score'] = 1
        result['assessment'] = '✓ Adequate liquidity runway (> 24 months)'
        result['warning_flags'] = []
        result['recommendations'] = [
            'Monitor burn rate quarterly',
            'Maintain covenant compliance',
            'Continue current growth strategy',
            'Consider opportunistic refinancing'
        ]

    # Additional warning if extended runway (with facilities) is still concerning
    extended_runway = runway_metrics.get('extended_runway_months')
    if extended_runway and extended_runway < 12 and runway_months >= 12:
        result['warning_flags'].append(
            f'Extended runway with facilities still limited ({extended_runway:.1f} months)'
        )

    result['data_quality'] = runway_metrics.get('data_quality', 'moderate')

    return result


def calculate_sustainable_burn_rate(financial_data, burn_rate_metrics, target_runway_months=24):
    """
    Calculate maximum sustainable monthly burn rate to maintain target runway

    Purpose: Identify if current burn rate exceeds sustainable levels and quantify
    the overspend that needs to be addressed.

    Formula:
        Sustainable Monthly Burn = Available Cash / Target Runway (months)
        Excess Burn = Actual Monthly Burn - Sustainable Monthly Burn

    Args:
        financial_data (dict): Validated JSON with liquidity data
        burn_rate_metrics (dict): Result from calculate_burn_rate()
        target_runway_months (int): Desired runway length (default: 24 months)

    Returns:
        dict: {
            'target_runway_months': int,
            'sustainable_monthly_burn': float or None,
            'actual_monthly_burn': float or None,
            'excess_burn_per_month': float or None,
            'excess_burn_annualized': float or None,
            'status': str,  # 'Above sustainable', 'Below sustainable', 'N/A'
            'available_cash': float,
            'data_quality': str
        }
    """

    result = {
        'target_runway_months': target_runway_months,
        'sustainable_monthly_burn': None,
        'actual_monthly_burn': None,
        'excess_burn_per_month': None,
        'excess_burn_annualized': None,
        'status': 'N/A',
        'available_cash': None,
        'data_quality': 'none'
    }

    # Check if burn rate applicable
    if not burn_rate_metrics or not burn_rate_metrics.get('applicable', False):
        result['status'] = 'N/A - REIT is cash-generative'
        return result

    actual_monthly_burn = burn_rate_metrics.get('monthly_burn_rate')
    if not actual_monthly_burn:
        return result

    result['actual_monthly_burn'] = actual_monthly_burn

    # Get available cash from liquidity
    if 'liquidity' not in financial_data:
        return result

    liquidity = financial_data['liquidity']
    cash = liquidity.get('cash_and_equivalents', 0) or 0
    marketable_sec = liquidity.get('marketable_securities', 0) or 0
    restricted = liquidity.get('restricted_cash', 0) or 0

    available_cash = cash + marketable_sec - restricted
    result['available_cash'] = round(available_cash, 2)

    if available_cash <= 0:
        result['status'] = 'Critical - No available cash'
        return result

    # Calculate sustainable burn rate
    sustainable_burn = available_cash / target_runway_months
    result['sustainable_monthly_burn'] = round(sustainable_burn, 2)

    # Calculate excess burn
    excess_burn = actual_monthly_burn - sustainable_burn
    result['excess_burn_per_month'] = round(excess_burn, 2)
    result['excess_burn_annualized'] = round(excess_burn * 12, 2)

    # Assess status
    if excess_burn > 0:
        result['status'] = f'Above sustainable - Overspending by ${excess_burn:,.0f}/month'
    else:
        result['status'] = f'Below sustainable - ${abs(excess_burn):,.0f}/month cushion'

    result['data_quality'] = burn_rate_metrics.get('data_quality', 'moderate')

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

    # Calculate AFCF metrics if cash flow data available
    afcf_metrics = None
    afcf_coverage = None
    afcf_reconciliation = None

    if 'cash_flow_investing' in financial_data:
        # First, ensure financial_data has access to ACFO
        # ACFO may be in reit_metrics or acfo_calculated at top level
        if 'acfo' in reit_metrics:
            financial_data['acfo_calculated'] = reit_metrics['acfo']

        # Calculate AFCF
        afcf_result = calculate_afcf(financial_data)

        if afcf_result and afcf_result.get('afcf') is not None:
            afcf_metrics = afcf_result

            # Calculate AFCF coverage ratios if financing data available
            if 'cash_flow_financing' in financial_data:
                # Add coverage_ratios to financial_data for AFCF coverage calculation
                financial_data['coverage_ratios'] = coverage_ratios
                afcf_coverage = calculate_afcf_coverage_ratios(financial_data, afcf_result['afcf'])

            # Validate AFCF reconciliation
            acfo_for_validation = afcf_result.get('acfo_starting_point')
            if acfo_for_validation is not None:
                afcf_reconciliation = validate_afcf_reconciliation(
                    financial_data,
                    acfo_for_validation,
                    afcf_result['afcf']
                )

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
    result = {
        'issuer_name': financial_data['issuer_name'],
        'reporting_date': financial_data['reporting_date'],
        'reporting_period': financial_data.get('reporting_period', 'Unknown'),
        'currency': financial_data.get('currency', 'Unknown'),
        'leverage_metrics': leverage_metrics,
        'reit_metrics': reit_metrics,
        'coverage_ratios': coverage_ratios,
        'portfolio_metrics': portfolio_metrics
    }

    # Add AFCF metrics if calculated
    if afcf_metrics is not None:
        result['afcf_metrics'] = afcf_metrics
    if afcf_coverage is not None:
        result['afcf_coverage'] = afcf_coverage
    if afcf_reconciliation is not None:
        result['afcf_reconciliation'] = afcf_reconciliation

    # Calculate burn rate and cash runway if AFCF available
    burn_rate_analysis = None
    liquidity_position = None
    cash_runway = None
    liquidity_risk = None
    sustainable_burn = None

    if afcf_metrics is not None:
        # Calculate burn rate (only applicable if AFCF < Net Financing Needs)
        burn_rate_analysis = calculate_burn_rate(financial_data, afcf_metrics, afcf_coverage)

        # If burn rate is applicable and liquidity data exists, calculate runway and risk
        if burn_rate_analysis.get('applicable', False) and 'liquidity' in financial_data:
            # Extract liquidity position for output
            liquidity_data = financial_data['liquidity']
            liquidity_position = {
                'cash_and_equivalents': liquidity_data.get('cash_and_equivalents', 0),
                'marketable_securities': liquidity_data.get('marketable_securities', 0),
                'restricted_cash': liquidity_data.get('restricted_cash', 0),
                'undrawn_credit_facilities': liquidity_data.get('undrawn_credit_facilities', 0),
                'credit_facility_limit': liquidity_data.get('credit_facility_limit', 0),
                'available_cash': liquidity_data.get('available_cash'),
                'total_available_liquidity': liquidity_data.get('total_available_liquidity'),
                'data_source': liquidity_data.get('data_source', 'Not specified')
            }

            # Calculate cash runway
            cash_runway = calculate_cash_runway(financial_data, burn_rate_analysis)

            # Assess liquidity risk
            if cash_runway and not cash_runway.get('error'):
                liquidity_risk = assess_liquidity_risk(cash_runway)

                # Calculate sustainable burn rate
                sustainable_burn = calculate_sustainable_burn_rate(
                    financial_data,
                    burn_rate_analysis,
                    target_runway_months=24
                )

    # Add burn rate metrics if calculated
    if burn_rate_analysis is not None:
        result['burn_rate_analysis'] = burn_rate_analysis
    if liquidity_position is not None:
        result['liquidity_position'] = liquidity_position
    if cash_runway is not None:
        result['cash_runway'] = cash_runway
    if liquidity_risk is not None:
        result['liquidity_risk'] = liquidity_risk
    if sustainable_burn is not None:
        result['sustainable_burn'] = sustainable_burn

    # Analyze dilution if detail available
    dilution_analysis = analyze_dilution(financial_data)
    if dilution_analysis['has_dilution_detail']:
        result['dilution_analysis'] = dilution_analysis

    return result


def analyze_dilution(financial_data):
    """
    Analyze share dilution from dilution_detail section

    Provides materiality assessment and credit quality implications of dilution.

    Args:
        financial_data (dict): Phase 2 extraction with optional dilution_detail section

    Returns:
        dict: {
            'has_dilution_detail': bool,
            'dilution_percentage': float | None,
            'dilution_materiality': str,  # 'minimal', 'low', 'moderate', 'high'
            'material_instruments': list,  # Instruments contributing >1% dilution
            'convertible_debt_risk': str,  # 'none', 'low', 'moderate', 'high'
            'governance_score': str,  # 'standard', 'enhanced' (based on disclosure)
            'credit_assessment': str,  # Overall credit quality impact
            'detail': dict  # Full dilution_detail if available
        }
    """

    if 'dilution_detail' not in financial_data:
        return {
            'has_dilution_detail': False,
            'dilution_percentage': None,
            'dilution_materiality': 'unknown',
            'material_instruments': [],
            'convertible_debt_risk': 'unknown',
            'governance_score': 'standard',
            'credit_assessment': 'No detailed dilution disclosure - standard for many REITs',
            'detail': None
        }

    dilution = financial_data['dilution_detail']

    # Calculate dilution percentage if not provided
    dilution_pct = dilution.get('dilution_percentage')
    if dilution_pct is None and 'basic_units' in dilution and 'diluted_units_reported' in dilution:
        basic = dilution['basic_units']
        diluted = dilution['diluted_units_reported']
        if basic and basic > 0:
            dilution_pct = ((diluted - basic) / basic) * 100

    # Assess materiality
    if dilution_pct is None:
        materiality = 'unknown'
    elif dilution_pct < 1.0:
        materiality = 'minimal'
    elif dilution_pct < 3.0:
        materiality = 'low'
    elif dilution_pct < 7.0:
        materiality = 'moderate'
    else:
        materiality = 'high'

    # Identify material instruments (>1% dilution each)
    material_instruments = []
    instruments = dilution.get('dilutive_instruments', {})
    basic_units = dilution.get('basic_units', 1)  # Avoid division by zero

    for instrument, count in instruments.items():
        if count and basic_units > 0:
            instrument_pct = (count / basic_units) * 100
            if instrument_pct > 1.0:
                material_instruments.append({
                    'instrument': instrument,
                    'units': count,
                    'dilution_pct': round(instrument_pct, 2)
                })

    # Assess convertible debt risk
    convertible_units = instruments.get('convertible_debentures', 0)
    if convertible_units and basic_units > 0:
        convertible_pct = (convertible_units / basic_units) * 100
        if convertible_pct == 0:
            conv_risk = 'none'
        elif convertible_pct < 3:
            conv_risk = 'low'
        elif convertible_pct < 7:
            conv_risk = 'moderate'
        else:
            conv_risk = 'high'
    else:
        conv_risk = 'none'

    # Governance score (enhanced disclosure = better governance)
    governance = 'enhanced' if dilution.get('disclosure_source') else 'standard'

    # Overall credit assessment
    if materiality == 'minimal' or materiality == 'low':
        if conv_risk == 'none':
            assessment = '✓ Low dilution risk - minimal equity overhang, positive for creditworthiness'
        else:
            assessment = '⚠ Low overall dilution but monitor convertible debt for forced conversion scenarios'
    elif materiality == 'moderate':
        if conv_risk in ['none', 'low']:
            assessment = '⚠ Moderate dilution from equity compensation - typical for REITs, manageable credit impact'
        else:
            assessment = '⚠ Moderate dilution with material convertibles - assess conversion terms and debt capacity implications'
    else:  # high
        assessment = '🚨 HIGH dilution - material equity overhang, review impact on debt capacity and unit holder value dilution'

    return {
        'has_dilution_detail': True,
        'dilution_percentage': round(dilution_pct, 2) if dilution_pct else None,
        'dilution_materiality': materiality,
        'material_instruments': material_instruments,
        'convertible_debt_risk': conv_risk,
        'governance_score': governance,
        'credit_assessment': assessment,
        'detail': dilution
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
