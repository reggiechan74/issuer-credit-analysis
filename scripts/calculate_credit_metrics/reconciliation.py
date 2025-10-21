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
                'amount': amount  # Already signed correctly (negative for deductions, per extraction guide)
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


def generate_issuer_reported_ffo_affo_reconciliation(phase2_data):
    """
    Generate issuer-reported FFO/AFFO reconciliation table (if disclosed)

    Args:
        phase2_data (dict): Phase 2 extraction data (full JSON)

    Returns:
        dict or None: Issuer-reported reconciliation structure, or None if not disclosed
    """

    ffo_affo = phase2_data.get('ffo_affo', {})
    ffo_affo_components = phase2_data.get('ffo_affo_components', {})

    # Check if issuer disclosed detailed components (any non-zero adjustment)
    has_components = False
    component_fields = [
        'unrealized_fv_changes', 'depreciation_real_estate', 'amortization_tenant_allowances',
        'amortization_intangibles', 'gains_losses_property_sales', 'tax_on_disposals',
        'deferred_taxes', 'impairment_losses_reversals', 'revaluation_gains_losses',
        'transaction_costs_business_comb', 'foreign_exchange_gains_losses',
        'sale_foreign_operations', 'fv_changes_hedges', 'goodwill_impairment',
        'puttable_instruments_effects', 'discontinued_operations',
        'equity_accounted_adjustments', 'incremental_leasing_costs',
        'property_taxes_ifric21', 'rou_asset_revenue_expense',
        'non_controlling_interests_ffo', 'capex_sustaining', 'leasing_costs',
        'tenant_improvements', 'straight_line_rent', 'non_controlling_interests_affo'
    ]

    for field in component_fields:
        if ffo_affo_components.get(field, 0) != 0:
            has_components = True
            break

    # Case 1: Issuer provides detailed reconciliation (rare)
    if has_components and ffo_affo.get('ffo') and ffo_affo.get('affo'):
        ffo_adjustments = _build_issuer_adjustments(ffo_affo_components, 'ffo')
        net_income = ffo_affo_components.get('net_income_ifrs', 0)
        ffo_reported = ffo_affo.get('ffo', 0)
        affo_reported = ffo_affo.get('affo', 0)

        # Calculate FFO validation metrics
        total_ffo_adjustments = sum(adj['amount'] for adj in ffo_adjustments)
        expected_ffo = net_income + total_ffo_adjustments
        ffo_missing_amount = ffo_reported - expected_ffo
        ffo_variance_percent = abs(ffo_missing_amount / ffo_reported * 100) if ffo_reported != 0 else 0
        ffo_reconciliation_complete = ffo_variance_percent < 2.0

        # Check calculation method
        calc_method = ffo_affo_components.get('calculation_method', 'unknown')
        uses_reserves = calc_method in ['reserve', 'hybrid'] or 'reserve' in ffo_affo_components.get('reserve_methodology', '').lower()

        # Check if issuer disclosed specific AFFO adjustments (reserve methodology)
        issuer_affo_adjustments = ffo_affo_components.get('affo_adjustments_issuer_reported', [])

        if issuer_affo_adjustments:
            # Use issuer's disclosed AFFO components (reserve methodology)
            affo_adjustments = []
            for adj in issuer_affo_adjustments:
                affo_adjustments.append({
                    'description': adj.get('description', 'Unknown adjustment'),
                    'amount': adj.get('amount', 0),
                    'source_page': adj.get('source_page', ''),
                    'note': adj.get('note', ''),
                    'is_issuer_reported': True
                })
            total_affo_adjustments = ffo_affo_components.get('affo_total_adjustments_issuer', sum(adj['amount'] for adj in affo_adjustments))
            expected_affo = ffo_reported + total_affo_adjustments
            affo_missing_amount = affo_reported - expected_affo
            affo_variance_percent = abs(affo_missing_amount / affo_reported * 100) if affo_reported != 0 else 0
            affo_reconciliation_complete = affo_variance_percent < 2.0
        else:
            # Calculate AFFO validation metrics from REALPAC standard fields
            affo_adjustments = _build_issuer_adjustments(ffo_affo_components, 'affo')
            total_affo_adjustments = sum(adj['amount'] for adj in affo_adjustments)
            expected_affo = ffo_reported + total_affo_adjustments
            affo_missing_amount = affo_reported - expected_affo
            affo_variance_percent = abs(affo_missing_amount / affo_reported * 100) if affo_reported != 0 else 0
            affo_reconciliation_complete = affo_variance_percent < 2.0

            # If AFFO doesn't reconcile (likely due to undisclosed reserves), show implied total instead
            if not affo_reconciliation_complete and uses_reserves:
                implied_affo_adjustment = affo_reported - ffo_reported
                affo_adjustments = [{
                    'description': f'AFFO adjustments ({calc_method} methodology - components not disclosed in detail)',
                    'amount': implied_affo_adjustment,
                    'is_implied': True
                }]

        return {
            'reconciliation_type': 'detailed',
            'starting_point': {
                'description': 'IFRS Net Income (as reported by issuer)',
                'amount': net_income
            },
            'ffo_adjustments': ffo_adjustments,
            'ffo_total': {
                'description': 'Funds From Operations (FFO) - Issuer Reported',
                'amount': ffo_reported
            },
            'affo_adjustments': affo_adjustments,
            'affo_total': {
                'description': 'Adjusted Funds From Operations (AFFO) - Issuer Reported',
                'amount': affo_reported
            },
            'validation': {
                'total_ffo_adjustments_extracted': total_ffo_adjustments,
                'expected_ffo': expected_ffo,
                'ffo_reported': ffo_reported,
                'ffo_missing_amount': ffo_missing_amount,
                'ffo_variance_percent': ffo_variance_percent,
                'ffo_reconciliation_complete': ffo_reconciliation_complete,
                'total_affo_adjustments_extracted': total_affo_adjustments,
                'expected_affo': expected_affo,
                'affo_reported': affo_reported,
                'affo_missing_amount': affo_missing_amount,
                'affo_variance_percent': affo_variance_percent,
                'affo_reconciliation_complete': affo_reconciliation_complete,
                'uses_reserve_methodology': uses_reserves
            },
            'metadata': {
                'disclosure_quality': 'detailed',
                'source': 'MD&A FFO/AFFO reconciliation table',
                'num_realpac_adjustments': sum(1 for adj in ffo_adjustments if not adj.get('is_other', False)),
                'num_other_adjustments': sum(1 for adj in ffo_adjustments if adj.get('is_other', False))
            }
        }

    # Case 2: Issuer provides only top-level FFO/AFFO (common - Artis example)
    elif ffo_affo.get('ffo') and ffo_affo.get('affo'):
        return {
            'reconciliation_type': 'summary_only',
            'ffo_reported': ffo_affo.get('ffo', 0),
            'ffo_per_unit': ffo_affo.get('ffo_per_unit', 0),
            'affo_reported': ffo_affo.get('affo', 0),
            'affo_per_unit': ffo_affo.get('affo_per_unit', 0),
            'metadata': {
                'disclosure_quality': 'summary_only',
                'source': 'MD&A - top-level FFO/AFFO disclosure',
                'note': 'Issuer does not disclose detailed FFO/AFFO reconciliation components. Only top-level values provided.'
            }
        }

    # Case 3: No FFO/AFFO disclosure (very rare for public REITs)
    else:
        return None


def _build_issuer_adjustments(components, metric_type):
    """
    Helper: Build adjustment list from Phase 2 components (REALPAC A-Z + Other)

    Args:
        components (dict): ffo_affo_components from Phase 2
        metric_type (str): 'ffo' or 'affo'

    Returns:
        list: Adjustment entries with description and amount
    """
    adjustments = []

    if metric_type == 'ffo':
        # FFO adjustments (A-U)
        adj_map = {
            'unrealized_fv_changes': 'A. Unrealized fair value changes (investment properties)',
            'depreciation_real_estate': 'B. Depreciation of depreciable real estate assets',
            'amortization_tenant_allowances': 'C. Amortization of tenant allowances (fit-out)',
            'amortization_intangibles': 'D. Amortization of tenant/customer relationship intangibles',
            'gains_losses_property_sales': 'E. Gains/losses from sales of investment properties',
            'tax_on_disposals': 'F. Tax on gains or losses on disposals',
            'deferred_taxes': 'G. Deferred taxes',
            'impairment_losses_reversals': 'H. Impairment losses or reversals',
            'revaluation_gains_losses': 'I. Revaluation gains/losses (owner-occupied)',
            'transaction_costs_business_comb': 'J. Transaction costs (business combinations)',
            'foreign_exchange_gains_losses': 'K. Foreign exchange gains/losses',
            'sale_foreign_operations': 'L. Gain/loss on sale of foreign operations',
            'fv_changes_hedges': 'M. Fair value changes (economically effective hedges)',
            'goodwill_impairment': 'N. Goodwill impairment or negative goodwill',
            'puttable_instruments_effects': 'O. Effects of puttable instruments',
            'discontinued_operations': 'P. Results of discontinued operations',
            'equity_accounted_adjustments': 'Q. Adjustments for equity accounted entities',
            'incremental_leasing_costs': 'R. Incremental leasing costs',
            'property_taxes_ifric21': 'S. Property taxes (IFRIC 21)',
            'rou_asset_revenue_expense': 'T. ROU asset revenue/expenses',
            'non_controlling_interests_ffo': 'U. Non-controlling interests (FFO adjustments)'
        }
    else:  # affo
        # AFFO adjustments (V-Z)
        adj_map = {
            'capex_sustaining': 'V. Sustaining/maintenance capital expenditures',
            'leasing_costs': 'W. Leasing costs (internal + external)',
            'tenant_improvements': 'X. Tenant improvements (sustaining)',
            'straight_line_rent': 'Y. Straight-line rent adjustment',
            'non_controlling_interests_affo': 'Z. Non-controlling interests (AFFO adjustments)'
        }

    # Add REALPAC standard adjustments
    for field, description in adj_map.items():
        amount = components.get(field, 0)
        if amount != 0:  # Only include non-zero adjustments
            adjustments.append({
                'description': description,
                'amount': amount
            })

    # Add Other adjustments (issuer-specific, non-REALPAC)
    # Note: Only include Other adjustments for FFO (they apply to FFO calculation, not separate AFFO step)
    if metric_type == 'ffo':
        other_adjustments = components.get('other_adjustments', [])
        if other_adjustments:
            for other_adj in other_adjustments:
                description = other_adj.get('description', 'Unknown adjustment')
                amount = other_adj.get('amount', 0)
                source_page = other_adj.get('source_page', '')

                # Format description with source page if available
                full_description = f"{description}"
                if source_page:
                    full_description += f" [{source_page}]"

                adjustments.append({
                    'description': full_description,
                    'amount': amount,
                    'is_other': True  # Flag to identify Other adjustments in formatting
                })

    return adjustments


def format_issuer_reported_ffo_affo_reconciliation(recon):
    """
    Format issuer-reported FFO/AFFO reconciliation as markdown

    Args:
        recon (dict or None): Output from generate_issuer_reported_ffo_affo_reconciliation()

    Returns:
        str: Markdown-formatted table or "Not disclosed" message
    """

    if not recon:
        return """## Issuer-Reported FFO/AFFO Reconciliation

**Not disclosed** - Issuer does not report FFO/AFFO. All metrics calculated using REALPAC methodology (see Section 2.3.2).

*Note: This is rare for public REITs. Verify MD&A for non-standard FFO disclosures.*"""

    if recon['reconciliation_type'] == 'summary_only':
        # Case: Top-level values only (Artis example)
        return f"""## Issuer-Reported FFO/AFFO Summary

**Disclosure Type:** Summary values only (detailed reconciliation not disclosed)

| Metric | Amount (000s) | Per Unit |
|--------|---------------|----------|
| **FFO (Issuer-Reported)** | {recon['ffo_reported']:,.0f} | ${recon['ffo_per_unit']:.4f} |
| **AFFO (Issuer-Reported)** | {recon['affo_reported']:,.0f} | ${recon['affo_per_unit']:.4f} |

**Note:** {recon['metadata']['note']}

**Source:** {recon['metadata']['source']}

*For detailed reconciliation showing Net Income → FFO → AFFO adjustments, see Section 2.3.2 (REALPAC-Calculated Reconciliation).*"""

    else:  # detailed reconciliation
        lines = []
        lines.append("## Issuer-Reported FFO/AFFO Reconciliation (Detailed)")
        lines.append("")
        lines.append("**Disclosure Type:** Full reconciliation disclosed by issuer")
        lines.append("")
        lines.append("| Line Item | Amount (000s) |")
        lines.append("|-----------|---------------|")

        # Starting point
        lines.append(f"| **{recon['starting_point']['description']}** | **{recon['starting_point']['amount']:,.0f}** |")

        # FFO adjustments - separate REALPAC and Other
        if recon['ffo_adjustments']:
            # REALPAC adjustments
            realpac_adjustments = [adj for adj in recon['ffo_adjustments'] if not adj.get('is_other', False)]
            other_adjustments = [adj for adj in recon['ffo_adjustments'] if adj.get('is_other', False)]

            if realpac_adjustments:
                lines.append("| **FFO Adjustments (REALPAC A-U):** | |")
                for adj in realpac_adjustments:
                    sign = "+" if adj['amount'] >= 0 else ""
                    lines.append(f"| {adj['description']} | {sign}{adj['amount']:,.0f} |")

            if other_adjustments:
                lines.append("| **Other Adjustments (Issuer-Specific):** | |")
                for adj in other_adjustments:
                    sign = "+" if adj['amount'] >= 0 else ""
                    lines.append(f"| {adj['description']} | {sign}{adj['amount']:,.0f} |")

        # FFO total
        lines.append(f"| **{recon['ffo_total']['description']}** | **{recon['ffo_total']['amount']:,.0f}** |")

        # AFFO adjustments
        if recon['affo_adjustments']:
            lines.append("| **AFFO Adjustments (as reported):** | |")
            for adj in recon['affo_adjustments']:
                sign = "+" if adj['amount'] >= 0 else ""
                lines.append(f"| {adj['description']} | {sign}{adj['amount']:,.0f} |")

        # AFFO total
        lines.append(f"| **{recon['affo_total']['description']}** | **{recon['affo_total']['amount']:,.0f}** |")

        # Add validation status if available
        if recon.get('validation'):
            lines.append("| | |")
            val = recon['validation']

            # FFO reconciliation status
            if val.get('ffo_reconciliation_complete'):
                lines.append("| **✓ FFO Reconciliation** | **Complete** |")
            else:
                ffo_missing = val.get('ffo_missing_amount', 0)
                lines.append(f"| **FFO Reconciliation Gap** | {ffo_missing:,.0f} ({val.get('ffo_variance_percent', 0):.1f}%) |")

            # AFFO reconciliation status
            if val.get('affo_reconciliation_complete'):
                lines.append("| **✓ AFFO Reconciliation** | **Complete** |")
            elif val.get('uses_reserve_methodology'):
                lines.append("| **⚠️ AFFO Methodology** | **Reserve-based (components not disclosed)** |")
                actual_vs_reserve = val.get('affo_missing_amount', 0)
                lines.append(f"| Actual cash vs. Reserve | {actual_vs_reserve:,.0f} difference |")
            else:
                affo_missing = val.get('affo_missing_amount', 0)
                lines.append(f"| **AFFO Reconciliation Gap** | {affo_missing:,.0f} ({val.get('affo_variance_percent', 0):.1f}%) |")

        lines.append("")
        lines.append(f"**Source:** {recon['metadata']['source']}")

        # Add note about reserve methodology if applicable
        if recon.get('validation', {}).get('uses_reserve_methodology'):
            lines.append("")
            lines.append("**Methodology Note:** Issuer uses reserve methodology for AFFO adjustments (not actual cash amounts). AFFO adjustments shown above represent the implied total needed to reconcile reported FFO to reported AFFO. See Section 2.3.2 for REALPAC calculation using actual cash amounts.")

        lines.append("")
        lines.append("*Note: This reconciliation reflects the issuer's disclosed methodology, which may differ from standardized REALPAC methodology. See Section 2.3.2 for REALPAC-calculated reconciliation for cross-issuer comparability.*")

        return "\n".join(lines)


def generate_issuer_reported_acfo_reconciliation(phase2_data):
    """
    Generate issuer-reported ACFO reconciliation table (if disclosed)

    Note: > 95% of issuers do NOT report ACFO. This will almost always return None.

    Args:
        phase2_data (dict): Phase 2 extraction data (full JSON)

    Returns:
        dict or None: Issuer-reported ACFO reconciliation, or None if not disclosed
    """

    ffo_affo = phase2_data.get('ffo_affo', {})
    acfo_components = phase2_data.get('acfo_components', {})

    # Check if issuer reported ACFO (very rare)
    issuer_acfo = ffo_affo.get('acfo')

    if issuer_acfo is None:
        # Common case - issuer does not report ACFO
        return None

    # Issuer reports ACFO - check if detailed components disclosed
    has_components = False
    component_fields = [
        'change_in_working_capital', 'interest_financing', 'jv_distributions',
        'capex_sustaining_acfo', 'leasing_costs_external', 'tenant_improvements_acfo',
        'realized_investment_gains_losses', 'taxes_non_operating',
        'transaction_costs_acquisitions', 'transaction_costs_disposals',
        'deferred_financing_fees', 'debt_termination_costs'
    ]

    for field in component_fields:
        if acfo_components.get(field, 0) != 0:
            has_components = True
            break

    cfo = acfo_components.get('cash_flow_from_operations', 0)

    if has_components and cfo > 0:
        # Detailed ACFO reconciliation disclosed (extremely rare)
        return {
            'reconciliation_type': 'detailed',
            'starting_point': {
                'description': 'Cash Flow from Operations (IFRS) - Issuer Reported',
                'amount': cfo
            },
            'acfo_adjustments': _build_issuer_acfo_adjustments(acfo_components),
            'acfo_total': {
                'description': 'Adjusted Cash Flow from Operations (ACFO) - Issuer Reported',
                'amount': issuer_acfo
            },
            'metadata': {
                'disclosure_quality': 'detailed',
                'source': 'MD&A ACFO reconciliation table',
                'note': 'Rare disclosure - most issuers do not report ACFO'
            }
        }
    else:
        # Summary only - issuer reports ACFO value but not detailed reconciliation
        return {
            'reconciliation_type': 'summary_only',
            'acfo_reported': issuer_acfo,
            'acfo_per_unit': ffo_affo.get('acfo_per_unit', 0),
            'cfo_reported': cfo if cfo > 0 else None,
            'metadata': {
                'disclosure_quality': 'summary_only',
                'source': 'MD&A - top-level ACFO disclosure',
                'note': 'Issuer reports ACFO value but does not disclose detailed reconciliation components.'
            }
        }


def _build_issuer_acfo_adjustments(components):
    """
    Helper: Build ACFO adjustment list from Phase 2 components

    Args:
        components (dict): acfo_components from Phase 2

    Returns:
        list: Adjustment entries with description and amount
    """
    adjustments = []

    adj_map = {
        'change_in_working_capital': '1. Eliminate working capital changes',
        'interest_financing': '2. Interest expense (financing activities)',
        'jv_distributions': '3a. JV distributions received',
        'jv_acfo': '3b. JV ACFO (calculated)',
        'capex_sustaining_acfo': '4. Sustaining/maintenance capital expenditures',
        'leasing_costs_external': '5. External leasing costs',
        'tenant_improvements_acfo': '6. Sustaining tenant improvements',
        'realized_investment_gains_losses': '7. Realized investment gains/losses',
        'taxes_non_operating': '8. Taxes related to non-operating activities',
        'transaction_costs_acquisitions': '9. Transaction costs (acquisitions)',
        'transaction_costs_disposals': '10. Transaction costs (disposals)',
        'deferred_financing_fees': '11. Deferred financing fees',
        'debt_termination_costs': '12. Debt termination costs',
        'interest_income_timing': '14a. Interest income timing adjustments',
        'interest_expense_timing': '14b. Interest expense timing adjustments',
        'rou_sublease_principal_received': '16a. ROU sublease principal received',
        'rou_lease_principal_paid': '16c. ROU lease principal paid',
        'non_controlling_interests_acfo': '17a. Non-controlling interests (ACFO)'
    }

    for field, description in adj_map.items():
        amount = components.get(field, 0)
        if amount != 0:  # Only include non-zero adjustments
            adjustments.append({
                'description': description,
                'amount': amount
            })

    return adjustments


def format_issuer_reported_acfo_reconciliation(recon):
    """
    Format issuer-reported ACFO reconciliation as markdown

    Args:
        recon (dict or None): Output from generate_issuer_reported_acfo_reconciliation()

    Returns:
        str: Markdown-formatted table or "Not disclosed" message
    """

    if not recon:
        return """## Issuer-Reported ACFO Reconciliation

**Not disclosed** - Issuer does not report ACFO.

*Note: Most issuers (> 95%) do not report ACFO per REALPAC ACFO White Paper (January 2023). This is expected. All ACFO metrics calculated using REALPAC methodology (see Section 2.4.2).*"""

    if recon['reconciliation_type'] == 'summary_only':
        # Issuer reports ACFO value but not detailed reconciliation
        cfo_line = ""
        if recon.get('cfo_reported'):
            cfo_line = f"| **IFRS Cash Flow from Operations** | {recon['cfo_reported']:,.0f} | N/A |\n"

        return f"""## Issuer-Reported ACFO Summary

**Disclosure Type:** Summary value only (detailed reconciliation not disclosed)

| Metric | Amount (000s) | Per Unit |
|--------|---------------|----------|
{cfo_line}| **ACFO (Issuer-Reported)** | {recon['acfo_reported']:,.0f} | ${recon['acfo_per_unit']:.4f} |

**Note:** {recon['metadata']['note']}

**Source:** {recon['metadata']['source']}

*For detailed reconciliation showing CFO → ACFO adjustments, see Section 2.4.2 (REALPAC-Calculated Reconciliation).*"""

    else:  # detailed reconciliation (extremely rare)
        lines = []
        lines.append("## Issuer-Reported ACFO Reconciliation (Detailed)")
        lines.append("")
        lines.append("**Disclosure Type:** Full reconciliation disclosed by issuer (rare)")
        lines.append("")
        lines.append("| Line Item | Amount (000s) |")
        lines.append("|-----------|---------------|")

        # Starting point
        lines.append(f"| **{recon['starting_point']['description']}** | **{recon['starting_point']['amount']:,.0f}** |")

        # ACFO adjustments
        if recon['acfo_adjustments']:
            lines.append("| **ACFO Adjustments (as reported):** | |")
            for adj in recon['acfo_adjustments']:
                sign = "+" if adj['amount'] >= 0 else ""
                lines.append(f"| {adj['description']} | {sign}{adj['amount']:,.0f} |")

        # ACFO total
        lines.append(f"| **{recon['acfo_total']['description']}** | **{recon['acfo_total']['amount']:,.0f}** |")

        lines.append("")
        lines.append(f"**Source:** {recon['metadata']['source']}")
        lines.append(f"**Note:** {recon['metadata']['note']}")
        lines.append("")
        lines.append("*This reconciliation reflects the issuer's disclosed methodology. See Section 2.4.2 for REALPAC-calculated reconciliation for cross-issuer comparability.*")

        return "\n".join(lines)




__all__ = [
    'generate_ffo_affo_reconciliation',
    'format_reconciliation_table',
    'format_acfo_reconciliation_table',
    'generate_issuer_reported_ffo_affo_reconciliation',
    'format_issuer_reported_ffo_affo_reconciliation',
    'generate_issuer_reported_acfo_reconciliation',
    'format_issuer_reported_acfo_reconciliation'
]
