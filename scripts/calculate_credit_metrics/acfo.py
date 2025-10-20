"""
ACFO (Adjusted Cash Flow from Operations) calculations

REALPAC methodology for calculating sustainable economic cash flow.
Per REALPAC ACFO White Paper (January 2023).
"""


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
        'acfo': round(acfo_calculated, 0),  # Alias for convenience
        'cash_flow_from_operations': cfo,
        'total_adjustments': round(total_adjustments, 0),
        'adjustments_detail': adjustments,
        'missing_components': missing_components,
        'available_adjustments': available_count,
        'total_adjustments_count': len(adjustment_fields),
        'calculation_method': calculation_method,
        'jv_treatment_method': jv_treatment_method,
        'data_quality': data_quality,
        'consistency_checks': consistency_checks
    }

    # Add per-unit if calculated
    if acfo_per_unit is not None:
        result['acfo_per_unit'] = acfo_per_unit
    if acfo_per_unit_diluted is not None:
        result['acfo_per_unit_diluted'] = acfo_per_unit_diluted

    # Add reserve methodology if provided
    if reserve_methodology:
        result['reserve_methodology'] = reserve_methodology

    return result


def validate_acfo(calculated_acfo, reported_acfo):
    """
    Validate calculated ACFO against issuer-reported ACFO

    Args:
        calculated_acfo (float): Our calculated ACFO value
        reported_acfo (float): Issuer-reported ACFO value

    Returns:
        dict: {
            'acfo_variance_amount': float,
            'acfo_variance_percent': float,
            'acfo_within_threshold': bool,  # < 5% variance
            'validation_notes': list
        }
    """
    if calculated_acfo is None or reported_acfo is None:
        return {
            'acfo_variance_amount': None,
            'acfo_variance_percent': None,
            'acfo_within_threshold': None,
            'validation_notes': ['Cannot validate - missing calculated or reported ACFO']
        }

    variance_amount = calculated_acfo - reported_acfo
    variance_percent = (variance_amount / reported_acfo) * 100 if reported_acfo != 0 else 0

    within_threshold = abs(variance_percent) < 5.0

    validation_notes = []
    if not within_threshold:
        validation_notes.append(
            f"ACFO variance ({variance_percent:.1f}%) exceeds 5% threshold. "
            f"Review ACFO methodology differences."
        )

    return {
        'acfo_variance_amount': round(variance_amount, 0),
        'acfo_variance_percent': round(variance_percent, 2),
        'acfo_within_threshold': within_threshold,
        'validation_notes': validation_notes
    }


def generate_acfo_reconciliation(financial_data):
    """
    Generate ACFO reconciliation from CFO to ACFO with all adjustment details

    Args:
        financial_data (dict): Complete financial data with acfo_components

    Returns:
        dict: Detailed reconciliation structure suitable for reporting with keys:
            - starting_point: dict with description and amount
            - acfo_adjustments: list of adjustments
            - acfo_total: dict with description and amount
            - metadata: dict with data_quality, calculation_method, etc.
    """
    if 'acfo_components' not in financial_data:
        return None

    components = financial_data['acfo_components']
    cfo = components.get('cash_flow_from_operations')

    if cfo is None:
        return None

    # Calculate ACFO using the main calculation function
    acfo_result = calculate_acfo_from_components(financial_data)
    if acfo_result['acfo_calculated'] is None:
        return None

    # Build reconciliation structure matching the format expected by format_acfo_reconciliation_table
    reconciliation = {
        'starting_point': {
            'description': 'Cash Flow from Operations (IFRS)',
            'amount': cfo
        },
        'acfo_adjustments': [],
        'acfo_total': {
            'description': 'Adjusted Cash Flow from Operations (ACFO)',
            'amount': acfo_result['acfo_calculated']
        },
        'metadata': {
            'data_quality': acfo_result['data_quality'],
            'calculation_method': acfo_result['calculation_method'],
            'jv_treatment_method': acfo_result['jv_treatment_method'],
            'missing_components': acfo_result['missing_components'],
            'consistency_checks': acfo_result.get('consistency_checks', {}),
            'reserve_methodology': components.get('reserve_methodology_acfo', 'Not specified')
        }
    }

    # Add each adjustment with description (17 REALPAC adjustments)
    # Note: adjustments_detail keys are formatted as 'adjustment_<num>_<field_name>'
    adjustment_descriptions = {
        'adjustment_1_change_in_working_capital': '1. Eliminate working capital changes',
        'adjustment_2_interest_financing': '2. Interest paid in financing activities',
        'adjustment_3a_jv_distributions': '3a. JV distributions received',
        'adjustment_3b_jv_acfo': '3b. REIT share of JV ACFO',
        'adjustment_3c_jv_notional_interest': '3c. JV notional interest',
        'adjustment_4_capex_sustaining_acfo': '4. Sustaining CAPEX',
        'adjustment_5_leasing_costs_external': '5. External leasing costs',
        'adjustment_6_tenant_improvements_acfo': '6. Sustaining tenant improvements',
        'adjustment_7_realized_investment_gains_losses': '7. Realized investment gains/losses',
        'adjustment_8_taxes_non_operating': '8. Taxes on non-operating items',
        'adjustment_9_transaction_costs_acquisitions': '9. Acquisition transaction costs',
        'adjustment_10_transaction_costs_disposals': '10. Disposal transaction costs',
        'adjustment_11_deferred_financing_fees': '11. Deferred financing costs',
        'adjustment_12_debt_termination_costs': '12. Debt termination costs',
        'adjustment_13a_off_market_debt_favorable': '13a. Off-market debt (favorable)',
        'adjustment_13b_off_market_debt_unfavorable': '13b. Off-market debt (unfavorable)',
        'adjustment_14a_interest_income_timing': '14a. Interest income timing',
        'adjustment_14b_interest_expense_timing': '14b. Interest expense timing',
        'adjustment_15_puttable_instruments_distributions': '15. Puttable instruments distributions',
        'adjustment_16a_rou_sublease_principal_received': '16a. ROU sublease principal received',
        'adjustment_16b_rou_sublease_interest_received': '16b. ROU sublease interest received',
        'adjustment_16c_rou_lease_principal_paid': '16c. ROU lease principal paid',
        'adjustment_16d_rou_depreciation_amortization': '16d. ROU depreciation/amortization',
        'adjustment_17a_non_controlling_interests_acfo': '17a. Non-controlling interests',
        'adjustment_17b_nci_puttable_units': '17b. NCI puttable units'
    }

    # Use the adjustments_detail from the calculated result
    for field, description in adjustment_descriptions.items():
        if field in acfo_result['adjustments_detail']:
            amount = acfo_result['adjustments_detail'][field]
            if amount != 0:  # Only include non-zero adjustments
                reconciliation['acfo_adjustments'].append({
                    'description': description,
                    'amount': amount
                })

    return reconciliation


__all__ = [
    'calculate_acfo_from_components',
    'validate_acfo',
    'generate_acfo_reconciliation'
]
