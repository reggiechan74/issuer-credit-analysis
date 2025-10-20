"""
FFO and AFFO calculations using REALPAC methodology

Functions for calculating Funds From Operations (FFO) and Adjusted FFO (AFFO)
following REALPAC White Paper (January 2022) guidelines.
"""


def calculate_ffo_from_components(financial_data):
    """
    Calculate FFO from IFRS net income using REALPAC methodology (adjustments A-U)

    Per REALPAC White Paper (Jan 2022), FFO starts from IFRS profit/loss and adds back
    non-cash and non-recurring items unique to real estate operations.

    NOTE: Adjustment U (Jan 2022 enhancement) includes NCI for consolidated entities
    with puttable units classified as financial liabilities under IAS 32.

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

    Per REALPAC White Paper (Jan 2022), AFFO is a recurring economic earnings measure
    (NOT cash flow) that adjusts FFO for sustaining capital requirements.

    NOTE: Adjustment Z (Jan 2022 enhancement) includes NCI for consolidated entities
    with puttable units classified as financial liabilities under IAS 32.

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

    Per REALPAC guidelines (Jan 2022), variance > 5% should be flagged and investigated.

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
