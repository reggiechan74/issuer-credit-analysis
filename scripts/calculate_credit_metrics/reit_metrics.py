"""
REIT-specific metrics orchestrator

Coordinates calculation of FFO, AFFO, and ACFO using either reported values
or calculated values from components (REALPAC methodology).
"""

from .validation import validate_required_fields
from .ffo_affo import (
    calculate_ffo_from_components,
    calculate_affo_from_ffo,
    validate_ffo_affo
)
from .acfo import calculate_acfo_from_components, validate_acfo


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
