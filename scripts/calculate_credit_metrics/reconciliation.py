"""
Reconciliation and formatting functions

Functions for generating FFO/AFFO/ACFO reconciliations and formatted tables.
"""

from .ffo_affo import calculate_ffo_from_components, calculate_affo_from_ffo
from .acfo import generate_acfo_reconciliation as generate_acfo_reconciliation_internal


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
    lines.append("*Source: Calculated per REALPAC White Paper on FFO & AFFO for IFRS (January 2022)*")

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




__all__ = [
    'generate_ffo_affo_reconciliation',
    'format_reconciliation_table',
    'format_acfo_reconciliation_table'
]
