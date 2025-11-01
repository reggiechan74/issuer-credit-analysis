#!/usr/bin/env python3
"""
Phase 5: Report Generation and Assembly

This script:
1. Loads Phase 3 calculated metrics (JSON)
2. Loads Phase 4 credit analysis (markdown)
3. Combines them using templates
4. Generates comprehensive final report

IMPORTANT: Pure Python templating - NO LLM usage (0 tokens)
"""

import json
import sys
import re
from pathlib import Path
from datetime import datetime

# Import reconciliation functions for v1.0.11+ comprehensive tables
sys.path.insert(0, str(Path(__file__).parent))
from calculate_credit_metrics.reconciliation import (
    generate_ffo_affo_reconciliation,
    format_reconciliation_table,
    format_acfo_reconciliation_table,
    generate_issuer_reported_ffo_affo_reconciliation,
    format_issuer_reported_ffo_affo_reconciliation,
    generate_issuer_reported_acfo_reconciliation,
    format_issuer_reported_acfo_reconciliation
)
from calculate_credit_metrics.acfo import generate_acfo_reconciliation


def load_metrics(metrics_path):
    """
    Load Phase 3 calculated metrics (or enriched Phase 4 data)

    Args:
        metrics_path: Path to Phase 3 metrics JSON or Phase 4 enriched JSON

    Returns:
        dict: Metrics data (merged if enriched file)

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file is invalid JSON
    """
    metrics_path = Path(metrics_path)

    if not metrics_path.exists():
        raise FileNotFoundError(
            f"Phase 3 metrics not found: {metrics_path}\n"
            f"Run Phase 3 first to generate calculated metrics."
        )

    print(f"📊 Loading Phase 3 metrics from: {metrics_path}")

    with open(metrics_path, 'r') as f:
        data = json.load(f)

    # Check if this is an enriched file (has phase3_metrics nested)
    if 'phase3_metrics' in data:
        print("✓ Detected enriched data file (Phase 4 enrichment)")
        # Extract Phase 3 metrics and merge with enrichment data at top level
        metrics = data['phase3_metrics'].copy()
        # Add enrichment data at top level for template access
        metrics['market_risk'] = data.get('market_risk')
        metrics['macro_environment'] = data.get('macro_environment')
        metrics['distribution_cut_prediction'] = data.get('distribution_cut_prediction')
        metrics['distribution_history'] = data.get('distribution_history')
        print(f"✓ Loaded enriched metrics for: {metrics.get('issuer_name', 'Unknown')}")
    else:
        # Standard Phase 3 file
        metrics = data
        print(f"✓ Loaded metrics for: {metrics.get('issuer_name', 'Unknown')}")

    return metrics


def load_analysis(analysis_path):
    """
    Load Phase 4 credit analysis

    Args:
        analysis_path: Path to Phase 4 analysis markdown

    Returns:
        dict: Parsed analysis sections

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    analysis_path = Path(analysis_path)

    if not analysis_path.exists():
        raise FileNotFoundError(
            f"Phase 4 analysis not found: {analysis_path}\n"
            f"Run Phase 4 first to generate credit analysis."
        )

    print(f"📄 Loading Phase 4 analysis from: {analysis_path}")

    with open(analysis_path, 'r') as f:
        content = f.read()

    # Parse into sections
    sections = parse_analysis_sections(content)

    print(f"✓ Loaded analysis with {len(sections)} sections")

    return sections


def parse_analysis_sections(content):
    """
    Parse Phase 4 analysis markdown into sections

    Handles both:
    - ## Executive Summary
    - ## 1. Executive Summary
    - ## 1) Executive Summary

    Args:
        content: Markdown content

    Returns:
        dict: Section name → section content
    """
    sections = {}

    # Split by headers (## Section Name)
    parts = re.split(r'^## (.+)$', content, flags=re.MULTILINE)

    # First part is before any headers (typically title and date)
    if parts:
        sections['_header'] = parts[0].strip()

    # Rest are alternating section names and content
    for i in range(1, len(parts), 2):
        if i + 1 < len(parts):
            section_name_raw = parts[i].strip()
            section_content = parts[i + 1].strip()

            # Strip leading numbers and punctuation (e.g., "1. " or "1) " or "12. ")
            # Handles formats like "1. Executive Summary", "12) Key Observations", etc.
            section_name = re.sub(r'^\d+[\.\)]\s*', '', section_name_raw)

            # Store both with and without numbers for flexible lookup
            sections[section_name] = section_content
            if section_name != section_name_raw:
                # Also store with original name for debugging
                sections[section_name_raw] = section_content

    return sections


def load_template(template_name='credit_opinion_template.md'):
    """
    Load report template

    Args:
        template_name: Template filename

    Returns:
        str: Template content

    Raises:
        FileNotFoundError: If template doesn't exist
    """
    template_dir = Path(__file__).parent.parent / 'templates'
    template_path = template_dir / template_name

    if not template_path.exists():
        raise FileNotFoundError(
            f"Template not found: {template_path}\n"
            f"Ensure templates directory exists with {template_name}"
        )

    with open(template_path, 'r') as f:
        return f.read()


def assess_leverage(debt_to_assets):
    """
    Assess leverage level based on Debt/Assets ratio

    Args:
        debt_to_assets: Debt/Assets percentage

    Returns:
        tuple: (level_description, rating_category, threshold_text)
    """
    if debt_to_assets < 25:
        return ("very low", "Aaa/Aa", "< 25%")
    elif debt_to_assets < 35:
        return ("low", "A", "25-35%")
    elif debt_to_assets < 45:
        return ("moderate", "Baa", "35-45%")
    elif debt_to_assets < 55:
        return ("elevated", "Ba", "45-55%")
    else:
        return ("high", "B", "> 55%")


def assess_coverage(coverage_ratio):
    """
    Assess interest coverage level

    Args:
        coverage_ratio: NOI/Interest coverage ratio

    Returns:
        tuple: (level_description, rating_category, threshold_text)
    """
    if coverage_ratio > 6.0:
        return ("strong", "Aaa/Aa", "> 6.0x")
    elif coverage_ratio > 4.0:
        return ("good", "A", "4.0-6.0x")
    elif coverage_ratio > 3.0:
        return ("adequate", "Baa", "3.0-4.0x")
    elif coverage_ratio > 2.0:
        return ("moderate", "Ba", "2.0-3.0x")
    else:
        return ("weak", "B", "< 2.0x")


def assess_payout_ratio(payout_ratio, metric_name="FFO"):
    """
    Assess payout ratio sustainability

    Args:
        payout_ratio: Payout ratio percentage
        metric_name: FFO or AFFO

    Returns:
        str: Assessment text
    """
    if payout_ratio < 70:
        return f"Conservative - {metric_name} payout well below 70%"
    elif payout_ratio < 90:
        return f"Sustainable - {metric_name} payout within typical range (70-90%)"
    elif payout_ratio < 100:
        return f"Elevated - {metric_name} payout approaching 100%"
    elif payout_ratio < 120:
        return f"Unsustainable - {metric_name} payout exceeds cash generation"
    else:
        return f"Highly unsustainable - {metric_name} payout significantly exceeds cash generation"


def assess_occupancy(occupancy_rate):
    """
    Assess portfolio occupancy

    Args:
        occupancy_rate: Occupancy percentage

    Returns:
        str: Assessment text
    """
    if occupancy_rate > 95:
        return "Excellent occupancy"
    elif occupancy_rate > 90:
        return "Strong occupancy"
    elif occupancy_rate > 85:
        return "Good occupancy"
    elif occupancy_rate > 80:
        return "Moderate occupancy"
    else:
        return "Below-average occupancy"


def assess_noi_growth(noi_growth):
    """
    Assess same-property NOI growth

    Args:
        noi_growth: NOI growth percentage

    Returns:
        str: Assessment text
    """
    if noi_growth > 5:
        return "Strong NOI growth"
    elif noi_growth > 2:
        return "Positive NOI growth"
    elif noi_growth > 0:
        return "Modest NOI growth"
    elif noi_growth > -2:
        return "Slight NOI decline"
    else:
        return "Negative NOI growth"


def assess_afcf_coverage(coverage_ratio):
    """
    Assess AFCF debt service coverage level

    Args:
        coverage_ratio: AFCF / Total Debt Service

    Returns:
        str: Assessment text
    """
    if coverage_ratio >= 1.5:
        return "Strong - AFCF significantly exceeds financing needs"
    elif coverage_ratio >= 1.0:
        return "Adequate - AFCF covers financing needs"
    elif coverage_ratio >= 0.75:
        return "Moderate - Partial capital markets reliance"
    elif coverage_ratio >= 0.5:
        return "Weak - Significant capital markets dependence"
    else:
        return "Critical - Heavy reliance on external financing"


def assess_self_funding_ratio(ratio):
    """
    Assess self-funding ratio (AFCF / Net Financing Needs)

    Args:
        ratio: Self-funding ratio

    Returns:
        str: Assessment text
    """
    if ratio >= 1.2:
        return "Excellent - Fully self-funding with cushion"
    elif ratio >= 1.0:
        return "Strong - Self-funding operations"
    elif ratio >= 0.75:
        return "Moderate - Requires periodic capital access"
    elif ratio >= 0.5:
        return "Weak - Regular capital markets reliance"
    else:
        return "Critical - Heavy capital markets dependence"


def assess_liquidity_risk(risk_level):
    """
    Assess liquidity risk level based on cash runway

    Args:
        risk_level: Risk level string (LOW/MODERATE/HIGH/CRITICAL)

    Returns:
        str: Assessment text
    """
    risk_map = {
        'LOW': '✓ Low Risk - Adequate liquidity runway (> 24 months)',
        'MODERATE': '⚠️ Moderate Risk - Plan financing within 12 months',
        'HIGH': '⚠️ High Risk - Near-term capital raise needed (6-12 months)',
        'CRITICAL': '🚨 Critical Risk - Immediate financing required (< 6 months)'
    }
    return risk_map.get(risk_level, 'Unknown risk level')


def assess_burn_rate_sustainability(status):
    """
    Assess burn rate sustainability status

    Args:
        status: Sustainability status string from Phase 3

    Returns:
        str: Assessment text
    """
    if 'below sustainable' in status.lower() or 'cushion' in status.lower():
        return "✓ Burn rate is sustainable - operating below target"
    elif 'at sustainable' in status.lower():
        return "Burn rate at target - monitor closely"
    elif 'exceeds sustainable' in status.lower():
        return "⚠️ Burn rate exceeds sustainable level - corrective action needed"
    else:
        return status


def format_cfi_breakdown_table(cfi_breakdown, currency='CAD'):
    """
    Format cash flow investing breakdown as markdown table

    Args:
        cfi_breakdown: Dictionary of CFI components from Phase 3
        currency: Currency code

    Returns:
        str: Formatted markdown table
    """
    if not cfi_breakdown or not isinstance(cfi_breakdown, dict):
        return "No cash flow investing data available"

    lines = []
    lines.append(f"| Investing Activity | Amount ({currency} 000s) |")
    lines.append("|--------------------|-----------------------------|")

    component_labels = {
        'development_capex': 'Development CAPEX',
        'property_acquisitions': 'Property Acquisitions',
        'property_dispositions': 'Property Dispositions',
        'jv_capital_contributions': 'JV Capital Contributions',
        'jv_return_of_capital': 'JV Return of Capital',
        'business_combinations': 'Business Combinations',
        'other_investing_outflows': 'Other Investing Outflows',
        'other_investing_inflows': 'Other Investing Inflows'
    }

    for component, data in cfi_breakdown.items():
        label = component_labels.get(component, component.replace('_', ' ').title())
        amount = data.get('amount', 0) if isinstance(data, dict) else data
        # Format with parentheses for negatives (accounting convention)
        if amount < 0:
            formatted = f"({abs(amount):,.0f})"
        else:
            formatted = f"{amount:,.0f}"
        lines.append(f"| {label} | {formatted} |")

    lines.append(f"| **Net Cash from Investing** | **See total above** |")

    return "\n".join(lines)


def format_afcf_reconciliation_table(acfo, afcf, net_cfi, currency='CAD'):
    """
    Format ACFO → AFCF reconciliation as markdown table

    Args:
        acfo: ACFO amount
        afcf: AFCF amount
        net_cfi: Net cash from investing
        currency: Currency code

    Returns:
        str: Formatted markdown table
    """
    if not acfo or not afcf:
        return "Insufficient data - AFCF reconciliation not available"

    lines = []
    lines.append(f"| Line Item | Amount ({currency} 000s) |")
    lines.append("|-----------|----------------------------|")
    lines.append(f"| **Adjusted Cash Flow from Operations (ACFO)** | **{acfo:,.0f}** |")

    # Format net CFI with parentheses if negative
    if net_cfi < 0:
        cfi_formatted = f"({abs(net_cfi):,.0f})"
    else:
        cfi_formatted = f"{net_cfi:,.0f}"
    lines.append(f"| Add: Net Cash Flow from Investing Activities | {cfi_formatted} |")
    lines.append(f"| **Adjusted Free Cash Flow (AFCF)** | **{afcf:,.0f}** |")

    return "\n".join(lines)


def generate_affo_validation_summary(affo_metrics, validation_data):
    """
    Generate AFFO validation summary text

    Args:
        affo_metrics: AFFO calculation detail from Phase 3
        validation_data: Validation data from reit_metrics

    Returns:
        str: Validation summary text
    """
    if not affo_metrics and not validation_data:
        return "AFFO validation not available"

    lines = []

    # Variance vs reported
    if validation_data and 'affo_variance_percent' in validation_data and validation_data['affo_variance_percent'] is not None:
        variance = validation_data['affo_variance_percent']
        within_threshold = validation_data.get('affo_within_threshold', False)
        variance_amount = validation_data.get('affo_variance_amount', 0)

        if within_threshold:
            lines.append(f"✓ **AFFO Variance:** Calculated matches reported (variance: {abs(variance):.1f}%)")
        else:
            lines.append(f"⚠️ **AFFO Variance:** Calculated differs from reported by {abs(variance_amount):,.0f} ({variance:.1f}%)")
            lines.append(f"  - This variance exceeds the 5% threshold and requires investigation")
    else:
        lines.append("**AFFO Variance:** Issuer did not report AFFO - using calculated value")

    # Validation notes
    if validation_data and 'validation_notes' in validation_data:
        notes = validation_data['validation_notes']
        affo_notes = [note for note in notes if 'AFFO' in note or 'affo' in note]
        if affo_notes:
            lines.append("\n**Validation Notes:**")
            for note in affo_notes:
                lines.append(f"- {note}")

    # AFFO calculation details
    if affo_metrics:
        available_adjustments = affo_metrics.get('available_adjustments', 0)
        total_adjustments = affo_metrics.get('total_adjustments_count', 0)
        lines.append(f"\n**REALPAC Adjustments:** {total_adjustments} of {available_adjustments} adjustments populated")

        # Missing components
        missing = affo_metrics.get('missing_components', [])
        if missing:
            lines.append(f"**Missing Components:** {', '.join(missing)}")

    # Data quality
    if affo_metrics:
        data_quality = affo_metrics.get('data_quality', 'unknown')
        calculation_method = affo_metrics.get('calculation_method', 'unknown')
        lines.append(f"\n**Data Quality:** {data_quality.capitalize()}")
        lines.append(f"**Calculation Method:** {calculation_method.capitalize()}")

    return "\n".join(lines) if lines else "AFFO validation not available"


def generate_acfo_validation_summary(acfo_metrics):
    """
    Generate ACFO validation summary text

    Args:
        acfo_metrics: ACFO metrics from Phase 3

    Returns:
        str: Validation summary text
    """
    if not acfo_metrics:
        return "ACFO validation not available"


    lines = []

    validation = acfo_metrics.get('acfo_validation', {})

    # Variance vs reported
    if 'acfo_variance_percent' in validation and validation['acfo_variance_percent'] is not None:
        variance = validation['acfo_variance_percent']
        within_threshold = validation.get('acfo_within_threshold', False)
        if within_threshold:
            lines.append(f"✓ **ACFO Variance:** Calculated matches reported (variance: {abs(variance):.1f}%)")
        else:
            lines.append(f"⚠️ **ACFO Variance:** Calculated differs from reported (variance: {abs(variance):.1f}%)")
    else:
        lines.append("**ACFO Variance:** Issuer did not report ACFO - using calculated value")

    # Consistency checks
    consistency = acfo_metrics.get('consistency_checks', {})
    if consistency:
        lines.append("\n**Consistency Checks:**")
        capex_check = consistency.get('capex_sustaining_consistent')
        ti_check = consistency.get('tenant_improvements_consistent')

        if capex_check is True:
            lines.append("- Sustaining CAPEX matches AFFO: ✓")
        elif capex_check is False:
            lines.append("- Sustaining CAPEX differs from AFFO: ⚠️")

        if ti_check is True:
            lines.append("- Tenant improvements match AFFO: ✓")
        elif ti_check is False:
            lines.append("- Tenant improvements differ from AFFO: ⚠️")

    # Data quality
    data_quality = acfo_metrics.get('data_quality', 'unknown')
    lines.append(f"\n**Data Quality:** {data_quality.capitalize()}")

    return "\n".join(lines) if lines else "ACFO validation not available"


def calculate_per_unit(amount, units_outstanding):
    """
    Calculate per-unit metric safely

    Args:
        amount (float): Dollar amount (000s)
        units_outstanding (float): Number of units (000s)

    Returns:
        float: Per-unit value (dollars), or None if invalid

    Examples:
        >>> calculate_per_unit(34500, 100000)
        0.35
        >>> calculate_per_unit(None, 100000)
        None
        >>> calculate_per_unit(34500, 0)
        None
    """
    if amount is None or units_outstanding is None or units_outstanding == 0:
        return None
    return round(amount / units_outstanding, 4)  # 4 decimals for per-unit precision


def calculate_payout_ratio(metric_per_unit, distributions_per_unit):
    """
    Calculate payout ratio as percentage

    Args:
        metric_per_unit (float): FFO/AFFO/ACFO/AFCF per unit
        distributions_per_unit (float): Distributions per unit

    Returns:
        float: Payout ratio (percentage), or None if invalid

    Formula:
        payout_ratio = (distributions_per_unit / metric_per_unit) * 100

    Examples:
        >>> calculate_payout_ratio(0.35, 0.30)
        85.7
        >>> calculate_payout_ratio(0, 0.30)
        None
        >>> calculate_payout_ratio(None, 0.30)
        None
        >>> calculate_payout_ratio(-0.0298, 0.14)
        None  # Negative metric (loss) - payout ratio meaningless
    """
    # Check for invalid inputs: None, zero, or negative (loss)
    # When metric is negative, payout ratio is meaningless (REIT paying from capital, not cash flow)
    if metric_per_unit is None or metric_per_unit == 0 or metric_per_unit < 0:
        return None
    if distributions_per_unit is None:
        return None
    return round((distributions_per_unit / metric_per_unit) * 100, 1)


def calculate_coverage_ratio(metric_per_unit, dist_per_unit):
    """
    Calculate per-unit coverage ratio (inverse of payout ratio)

    Args:
        metric_per_unit (float): FFO/AFFO/ACFO/AFCF per unit
        dist_per_unit (float): Distributions per unit

    Returns:
        float: Coverage ratio (x.xx), or None if invalid

    Formula:
        coverage_ratio = metric_per_unit / dist_per_unit

    Examples:
        >>> calculate_coverage_ratio(0.34, 0.30)
        1.13
        >>> calculate_coverage_ratio(0.17, 0.30)
        0.57
        >>> calculate_coverage_ratio(0, 0.30)
        None
        >>> calculate_coverage_ratio(-0.0298, 0.14)
        None  # Negative metric (loss) - coverage ratio meaningless
    """
    # Check for invalid inputs: None, zero, or negative (loss)
    # When metric is negative, coverage ratio is meaningless (REIT has loss, not covering distributions)
    if metric_per_unit is None or metric_per_unit == 0 or metric_per_unit < 0:
        return None
    if dist_per_unit is None or dist_per_unit == 0:
        return None
    return round(metric_per_unit / dist_per_unit, 2)


def format_reporting_period(report_period):
    """
    Format reporting period for display in table headers

    Args:
        report_period (str): Raw period (e.g., "Q2 2025", "Annual 2024", "H1 2025")

    Returns:
        str: Formatted period for headers (e.g., "YTD Q2-2025", "Annual 2024")

    Examples:
        >>> format_reporting_period("Q2 2025")
        'YTD Q2-2025'
        >>> format_reporting_period("Annual 2024")
        'Annual 2024'
        >>> format_reporting_period("H1 2025")
        'Semi Annual H1-2025'
    """
    if not report_period:
        return ""

    # Quarterly reports: "Q2 2025" → "YTD Q2-2025"
    if "Q" in report_period and "YTD" not in report_period:
        parts = report_period.split()
        if len(parts) >= 2:
            return f"YTD {parts[0]}-{parts[1]}"

    # Half-year reports: "H1 2025" → "Semi Annual H1-2025"
    if "H" in report_period and "Semi" not in report_period:
        parts = report_period.split()
        if len(parts) >= 2:
            return f"Semi Annual {parts[0]}-{parts[1]}"

    # Annual or already formatted - return as is
    return report_period


def format_metric_with_per_unit(total, per_unit, currency="CAD"):
    """
    Format metric with per-unit display: "34,491 ($0.34/unit)"

    Args:
        total (float): Total amount in thousands
        per_unit (float): Per-unit amount in dollars
        currency (str): Currency code (default: CAD)

    Returns:
        str: Formatted string with total and per-unit

    Examples:
        >>> format_metric_with_per_unit(34491, 0.34)
        '34,491 ($0.34/unit)'
        >>> format_metric_with_per_unit(3956, 0.0396)
        '3,956 ($0.0396/unit)'
        >>> format_metric_with_per_unit(34491, None)
        '34,491'
    """
    if total is None:
        return "Not available"

    formatted_total = f"{total:,.0f}"

    if per_unit is None:
        return formatted_total

    # Format per-unit with appropriate decimal places
    if abs(per_unit) >= 1:
        per_unit_str = f"${per_unit:.2f}"
    elif abs(per_unit) >= 0.01:
        per_unit_str = f"${per_unit:.4f}"
    else:
        per_unit_str = f"${per_unit:.6f}"

    return f"{formatted_total} ({per_unit_str}/unit)"


def assess_distribution_coverage(coverage_ratio):
    """
    Assess distribution coverage quality based on ratio

    This is for FFO/AFFO/ACFO/AFCF distribution coverage, NOT NOI/Interest coverage.

    Args:
        coverage_ratio (float): Coverage ratio (x.xx)

    Returns:
        str: Assessment (Strong/Adequate/Tight/Insufficient)

    Thresholds:
        >= 1.3x: Strong coverage
        >= 1.1x: Adequate coverage
        >= 1.0x: Tight coverage
        < 1.0x: Insufficient coverage

    Examples:
        >>> assess_distribution_coverage(1.5)
        'Strong coverage'
        >>> assess_distribution_coverage(0.95)
        'Insufficient coverage'
    """
    if coverage_ratio is None:
        return 'Not available'

    if coverage_ratio >= 1.3:
        return 'Strong coverage'
    elif coverage_ratio >= 1.1:
        return 'Adequate coverage'
    elif coverage_ratio >= 1.0:
        return 'Tight coverage'
    else:
        return 'Insufficient coverage'


def assess_self_funding_capacity(self_funding_ratio):
    """
    Assess self-funding capacity

    Args:
        self_funding_ratio (float): Self-funding ratio (AFCF / Net Financing Needs)

    Returns:
        str: Assessment of self-funding capability

    Thresholds:
        >= 1.0x: Self-funding
        >= 0.75x: Moderate reliance on external financing
        >= 0.5x: High reliance on external financing
        < 0.5x: Critical reliance on external financing

    Examples:
        >>> assess_self_funding_capacity(1.2)
        'Self-funding - no external financing required'
        >>> assess_self_funding_capacity(0.4)
        'Critical reliance on external financing'
    """
    if self_funding_ratio is None:
        return 'Not available'

    if self_funding_ratio >= 1.0:
        return 'Self-funding - no external financing required'
    elif self_funding_ratio >= 0.75:
        return 'Moderate reliance on external financing'
    elif self_funding_ratio >= 0.5:
        return 'High reliance on external financing'
    else:
        return 'Critical reliance on external financing'


def generate_reported_adjustments_list(ffo_affo_components):
    """
    Generate formatted list of top FFO→AFFO adjustments from reported components

    Args:
        ffo_affo_components (dict): Phase 2 extracted FFO/AFFO components

    Returns:
        str: Formatted markdown list of top 3-5 adjustments

    Example Output:
        - Sustaining CAPEX: ($8,752)
        - Leasing costs: ($10,800)
        - Tenant improvements: ($3,300)
    """
    if not ffo_affo_components:
        return 'Issuer does not disclose detailed adjustments'

    # Extract AFFO adjustments (V-Z from REALPAC schema)
    affo_adjustments = {
        'Sustaining CAPEX': ffo_affo_components.get('adjustment_V_capex_sustaining', 0),
        'Leasing costs': ffo_affo_components.get('adjustment_X_leasing_costs', 0),
        'Tenant improvements': ffo_affo_components.get('adjustment_W_tenant_improvements', 0),
        'Straight-line rent': ffo_affo_components.get('adjustment_Y_straight_line_rent', 0),
        'Amortization of financing costs': ffo_affo_components.get('adjustment_Z_amortization', 0),
    }

    # Sort by absolute value
    sorted_adjustments = sorted(
        [(k, v) for k, v in affo_adjustments.items() if v != 0],
        key=lambda x: abs(x[1]),
        reverse=True
    )

    # Format top 3-5
    lines = []
    for name, amount in sorted_adjustments[:5]:
        # Format with parentheses for negative (accounting convention)
        formatted_amount = f"({abs(amount):,.0f})" if amount < 0 else f"{amount:,.0f}"
        lines.append(f"- {name}: {formatted_amount}")

    return '\n'.join(lines) if lines else 'No material adjustments disclosed'


def generate_top_adjustments_list(adjustments_dict, top_n=5, clean_names=True):
    """
    Generate formatted list of top N adjustments by absolute value

    Args:
        adjustments_dict (dict): Dictionary of {adjustment_name: amount}
        top_n (int): Number of top adjustments to return (default 5)
        clean_names (bool): Whether to clean up adjustment names (default True)

    Returns:
        str: Formatted markdown list

    Example Output:
        - Amortization Tenant Allowances: $11,321k
        - Fair Value Changes Hedges: $3,149k
        - Unrealized FV Changes: $862k
    """
    if not adjustments_dict:
        return "No adjustments available"

    # Filter out zero/null values
    non_zero = {k: v for k, v in adjustments_dict.items()
                if v is not None and v != 0}

    if not non_zero:
        return "No material adjustments (all adjustments are zero)"

    # Sort by absolute value descending
    sorted_adjustments = sorted(non_zero.items(),
                               key=lambda x: abs(x[1]),
                               reverse=True)

    # Take top N
    top_adjustments = sorted_adjustments[:top_n]

    # Format as markdown list
    lines = []
    for name, amount in top_adjustments:
        # Clean up adjustment name if requested
        if clean_names:
            # Remove 'adjustment_' prefix and underscores
            clean_name = name.replace('adjustment_', '').replace('_', ' ')
            # Remove leading letter codes (A_, B_, etc.)
            import re
            clean_name = re.sub(r'^[A-Z0-9]+\s+', '', clean_name)
            clean_name = clean_name.title()
        else:
            clean_name = name

        # Format amount with sign
        sign = '+' if amount > 0 else ''
        lines.append(f"- {clean_name}: {sign}${amount:,.0f}k")

    return '\n'.join(lines)


def parse_scenario_analysis(scenario_text):
    """
    Parse scenario analysis section to extract individual scenarios

    Args:
        scenario_text (str): Full scenario analysis section from Phase 4

    Returns:
        dict: Parsed scenarios with keys for each placeholder

    Example structure:
        {
            'BASE_ASSUMPTIONS': '...',
            'BASE_METRICS': '...',
            'BASE_RATING_IMPACT': '...',
            'BASE_LIKELIHOOD': '...',
            ...
            'DOWNGRADE_TRIGGERS': '...'
        }
    """
    if not scenario_text or scenario_text == 'Not available':
        return {
            'BASE_ASSUMPTIONS': 'Not available',
            'BASE_METRICS': 'Not available',
            'BASE_RATING_IMPACT': 'Not available',
            'BASE_LIKELIHOOD': 'Not available',
            'UPSIDE_ASSUMPTIONS': 'Not available',
            'UPSIDE_METRICS': 'Not available',
            'UPSIDE_RATING_IMPACT': 'Not available',
            'UPSIDE_LIKELIHOOD': 'Not available',
            'DOWNSIDE_ASSUMPTIONS': 'Not available',
            'DOWNSIDE_METRICS': 'Not available',
            'DOWNSIDE_RATING_IMPACT': 'Not available',
            'DOWNSIDE_LIKELIHOOD': 'Not available',
            'STRESS_ASSUMPTIONS': 'Not available',
            'STRESS_METRICS': 'Not available',
            'STRESS_RATING_IMPACT': 'Not available',
            'STRESS_LIKELIHOOD': 'Not available',
            'DOWNGRADE_TRIGGERS': 'Not available',
        }

    result = {}

    # Define scenario patterns to search for
    scenarios = [
        ('BASE', r'###\s+Base Case[^\n]*\n(.*?)(?=###|\Z)'),
        ('UPSIDE', r'###\s+Upside[^\n]*\n(.*?)(?=###|\Z)'),
        ('DOWNSIDE', r'###\s+Downside[^\n]*\n(.*?)(?=###|\Z)'),
        ('STRESS', r'###\s+(?:Stress|Severe Stress)[^\n]*\n(.*?)(?=###|\Z)'),
    ]

    for prefix, pattern in scenarios:
        match = re.search(pattern, scenario_text, re.DOTALL | re.IGNORECASE)
        if match:
            full_match = match.group(0)  # Full match including header
            scenario_content = match.group(1)  # Just the content

            # Extract Assumptions
            assumptions_match = re.search(r'\*\*Assumptions:\*\*\s*\n(.*?)(?=\*\*Pro Forma|\*\*Rating|\Z)', scenario_content, re.DOTALL)
            result[f'{prefix}_ASSUMPTIONS'] = assumptions_match.group(1).strip() if assumptions_match else 'Not available'

            # Extract Pro Forma Metrics
            metrics_match = re.search(r'\*\*Pro Forma Metrics[^\n]*:\*\*\s*\n(.*?)(?=\*\*Rating Impact|\*\*Key Monitoring|\*\*Upgrade|\*\*Downgrade|\*\*Mitigation|\*\*Crisis|\*\*Downward|\*\*Recovery|\*\*Probability|\Z)', scenario_content, re.DOTALL)
            result[f'{prefix}_METRICS'] = metrics_match.group(1).strip() if metrics_match else 'Not available'

            # Extract Rating Impact
            rating_match = re.search(r'\*\*Rating Impact:\*\*\s*([^\n]+)', scenario_content)
            result[f'{prefix}_RATING_IMPACT'] = rating_match.group(1).strip() if rating_match else 'Not available'

            # Extract Likelihood/Probability
            likelihood_match = re.search(r'\*\*Probability Assessment:\*\*\s*([^\n]+)', scenario_content)
            if likelihood_match:
                result[f'{prefix}_LIKELIHOOD'] = likelihood_match.group(1).strip()
            else:
                # Try to extract from header (e.g., "### Base Case (50-60% probability)")
                header_match = re.search(r'###[^\(]*\((\d+[-%]\d*%?)\s+probability\)', full_match, re.IGNORECASE)
                result[f'{prefix}_LIKELIHOOD'] = header_match.group(1) if header_match else 'Not available'
        else:
            result[f'{prefix}_ASSUMPTIONS'] = 'Not available'
            result[f'{prefix}_METRICS'] = 'Not available'
            result[f'{prefix}_RATING_IMPACT'] = 'Not available'
            result[f'{prefix}_LIKELIHOOD'] = 'Not available'

    # Extract Downgrade Triggers table (more robust pattern)
    triggers_match = re.search(r'###\s+Downgrade Trigger Summary\s*\n+(.*?)(?:\n###|\n---|\n\n##|\Z)', scenario_text, re.DOTALL | re.IGNORECASE)
    if triggers_match:
        result['DOWNGRADE_TRIGGERS'] = triggers_match.group(1).strip()
    else:
        result['DOWNGRADE_TRIGGERS'] = 'Not available'

    return result


def parse_esg_section(esg_text):
    """
    Parse ESG section to extract Environmental, Social, and Governance components

    Args:
        esg_text (str): Full ESG section from Phase 4

    Returns:
        dict: Parsed ESG components with individual sections
    """
    if not esg_text or esg_text == 'Not available':
        return {
            'ENVIRONMENTAL_ANALYSIS': 'Not available',
            'SOCIAL_ANALYSIS': 'Not available',
            'GOVERNANCE_ANALYSIS': 'Not available',
        }

    result = {}

    # Extract Environmental Factors
    env_match = re.search(r'###\s+Environmental Factors\s*\n(.*?)(?=###|$)', esg_text, re.DOTALL | re.IGNORECASE)
    result['ENVIRONMENTAL_ANALYSIS'] = env_match.group(1).strip() if env_match else 'Not available'

    # Extract Social Factors
    social_match = re.search(r'###\s+Social Factors\s*\n(.*?)(?=###|\*\*ESG Rating|$)', esg_text, re.DOTALL | re.IGNORECASE)
    result['SOCIAL_ANALYSIS'] = social_match.group(1).strip() if social_match else 'Not available'

    # Extract Governance Factors
    gov_match = re.search(r'###\s+Governance Factors\s*\n(.*?)(?=\*\*Credit Impact|\*\*ESG Rating|###|$)', esg_text, re.DOTALL | re.IGNORECASE)
    result['GOVERNANCE_ANALYSIS'] = gov_match.group(1).strip() if gov_match else 'Not available'

    return result


def parse_debt_structure(phase4_content, phase2_data=None, phase3_data=None):
    """
    Parse debt structure information from Phase 4 content

    Extracts credit facility details, covenant analysis, and debt profile
    from the Liquidity and Leverage sections of Phase 4.

    Args:
        phase4_content (str): Full Phase 4 analysis content
        phase2_data (dict): Phase 2 extraction data (optional)
        phase3_data (dict): Phase 3 calculated metrics (optional)

    Returns:
        str: Synthesized debt structure summary or 'Not available'
    """
    if not phase4_content or phase4_content == 'Not available':
        return 'Not available'

    sections = []

    # Extract credit facility information
    # Pattern: "Credit facilities:" followed by capacity/drawn/available
    credit_facility_match = re.search(
        r'\*\*Credit facilities:\*\*\s*([^\n]*(?:\n(?!\*\*)[^\n]*)*)',
        phase4_content,
        re.IGNORECASE
    )

    if credit_facility_match:
        facility_text = credit_facility_match.group(1).strip()
        sections.append(f"**Credit Facilities:**\n{facility_text}")

    # Extract covenant analysis
    # Pattern: "Covenant Risk:" or "Covenant Compliance:" section
    covenant_match = re.search(
        r'\*\*Covenant (?:Risk|Compliance):\*\*\s*\n(.*?)(?=\n\*\*|\n###|\Z)',
        phase4_content,
        re.DOTALL | re.IGNORECASE
    )

    if covenant_match:
        covenant_text = covenant_match.group(1).strip()
        # Clean up and format
        covenant_lines = [line.strip() for line in covenant_text.split('\n') if line.strip()]
        sections.append(f"**Covenant Compliance:**\n" + '\n'.join(covenant_lines))

    # Extract debt profile metrics from Phase 3 if available
    if phase3_data:
        leverage_metrics = phase3_data.get('leverage_metrics', {})
        total_debt = leverage_metrics.get('total_debt', 0)
        debt_to_assets = leverage_metrics.get('debt_to_assets', 0)
        net_debt_to_ebitda = leverage_metrics.get('net_debt_to_ebitda', 0)

        if total_debt or debt_to_assets or net_debt_to_ebitda:
            debt_profile_lines = ["**Debt Profile:**"]
            if total_debt:
                # Convert from thousands to billions (divide by 1,000,000)
                debt_profile_lines.append(f"- Total debt: ${total_debt/1_000_000:,.1f}B")
            if debt_to_assets:
                debt_profile_lines.append(f"- Debt/Assets: {debt_to_assets*100:.1f}%")
            if net_debt_to_ebitda:
                debt_profile_lines.append(f"- Net Debt/EBITDA: {net_debt_to_ebitda:.2f}x")

            sections.append('\n'.join(debt_profile_lines))

    # If we found content, combine it
    if sections:
        return '\n\n'.join(sections)

    # Fallback: Try to find any debt-related summary
    debt_summary_match = re.search(
        r'(?:total debt|debt profile|capital structure).*?(?:\$[\d,]+[BM]|[\d.]+%)',
        phase4_content,
        re.IGNORECASE
    )

    if debt_summary_match:
        return f"**Debt Profile:**\n{debt_summary_match.group(0)}"

    return 'Not available'


def parse_security_collateral(phase4_content, phase2_data=None, phase3_data=None):
    """
    Parse security and collateral information from Phase 4 content

    Extracts unencumbered asset pool, LTV ratios, recovery estimates,
    and security structure assessment from scattered Phase 4 content.

    Args:
        phase4_content (str): Full Phase 4 analysis content
        phase2_data (dict): Phase 2 extraction data (optional)
        phase3_data (dict): Phase 3 calculated metrics (optional)

    Returns:
        str: Synthesized security/collateral analysis or 'Not available'
    """
    if not phase4_content or phase4_content == 'Not available':
        return 'Not available'

    sections = []

    # Extract unencumbered asset information
    # Pattern: Look for dollar amounts and percentages associated with unencumbered assets
    unencumbered_info = []

    # Search for "Unencumbered assets: $X.XB" pattern
    # Match both "$9.0 billion" and "$9.0B" formats
    amount_match = re.search(
        r'[Uu]nencumbered\s+asset(?:s|\s+pool)[^$]*\$(\d+\.?\d*)\s*([BM]|[Bb]illion|[Mm]illion)',
        phase4_content
    )
    if amount_match:
        value = amount_match.group(1)
        unit = amount_match.group(2)
        # Normalize to B/M format
        if unit.lower().startswith('b'):
            unencumbered_info.append(f"${value}B")
        elif unit.lower().startswith('m'):
            unencumbered_info.append(f"${value}M")

    # Search for percentage of gross assets
    pct_match = re.search(
        r'(\d+%)\s+of\s+gross\s+assets',
        phase4_content,
        re.IGNORECASE
    )
    if pct_match:
        unencumbered_info.append(f"{pct_match.group(1)} of gross assets")

    # Search for "provides ... refinancing capacity" mentions
    capacity_match = re.search(
        r'(?:provides|providing)\s+(?:substantial|significant)\s+(?:financial\s+flexibility|refinancing\s+capacity)',
        phase4_content,
        re.IGNORECASE
    )
    if capacity_match:
        unencumbered_info.append("Provides substantial refinancing capacity")

    if unencumbered_info:
        unencumbered_section = ["**Unencumbered Asset Pool:**"]
        for info in unencumbered_info:
            unencumbered_section.append(f"- {info}")
        sections.append('\n'.join(unencumbered_section))

    # Extract LTV and recovery analysis
    # Pattern: "LTV", "recovery", "well-secured"
    recovery_lines = []

    ltv_match = re.search(r'LTV[:\s]+(\d+%)', phase4_content, re.IGNORECASE)
    if ltv_match:
        recovery_lines.append(f"LTV: {ltv_match.group(1)}")

    # Look for recovery percentage estimates (e.g., ">80-90%", "80-90%")
    # Prefer mentions with "substantial recovery" or "provides ... recovery"
    recovery_match = re.search(
        r'(?:substantial|provides)\s+recovery[^.]*?(>?\s*\d+(?:-\d+)?%)',
        phase4_content,
        re.IGNORECASE
    )
    if recovery_match:
        recovery_lines.append(f"Recovery estimate: {recovery_match.group(1).strip()}")
    else:
        # Fallback: Look for "recovery >" pattern (high recovery rates)
        recovery_match = re.search(
            r'recovery\s+(>\s*\d+(?:-\d+)?%)',
            phase4_content,
            re.IGNORECASE
        )
        if recovery_match:
            recovery_lines.append(f"Recovery estimate: {recovery_match.group(1).strip()}")

    # Look for security assessment statements
    security_assessment_patterns = [
        r'(?:senior\s+)?unsecured\s+debt\s+(?:appears?\s+)?well-secured',
        r'debt\s+holders?\s+well-secured',
        r'substantial\s+(?:security|collateral)',
    ]

    for pattern in security_assessment_patterns:
        assessment_match = re.search(pattern, phase4_content, re.IGNORECASE)
        if assessment_match:
            # Get surrounding context (up to 100 chars)
            start = max(0, assessment_match.start() - 50)
            end = min(len(phase4_content), assessment_match.end() + 100)
            context = phase4_content[start:end].strip()
            # Extract the sentence containing the match
            sentence_match = re.search(r'[^.!?]*' + re.escape(assessment_match.group(0)) + r'[^.!?]*[.!?]', context)
            if sentence_match:
                recovery_lines.append(f"- Assessment: {sentence_match.group(0).strip()}")
                break

    if recovery_lines:
        sections.append("**Security Analysis:**\n" + '\n'.join(recovery_lines))

    # Extract asset quality mentions related to security
    asset_quality_match = re.search(
        r'(?:asset quality|portfolio quality)[^.]*(?:provides|support)[^.]*(?:recovery|security|refinancing)[^.]*\.',
        phase4_content,
        re.IGNORECASE
    )

    if asset_quality_match:
        sections.append(f"**Asset Quality:**\n{asset_quality_match.group(0).strip()}")

    # If we found content, combine it
    if sections:
        return '\n\n'.join(sections)

    return 'Not available'


def check_perpetual_securities(phase4_content, phase2_data=None, phase3_data=None):
    """
    Check for perpetual securities in capital structure

    Searches Phase 2, Phase 3, and Phase 4 content for perpetual securities.
    Returns analysis if found, otherwise indicates "Not applicable".

    Args:
        phase4_content (str): Full Phase 4 analysis content
        phase2_data (dict): Phase 2 extraction data (optional)
        phase3_data (dict): Phase 3 calculated metrics (optional)

    Returns:
        str: Perpetual securities analysis or 'Not applicable'
    """
    # Check Phase 4 for perpetual mentions
    if phase4_content and phase4_content != 'Not available':
        perpetual_match = re.search(
            r'###\s+Perpetual\s+Securities[^\n]*\n(.*?)(?=###|\Z)',
            phase4_content,
            re.DOTALL | re.IGNORECASE
        )

        if perpetual_match:
            content = perpetual_match.group(1).strip()
            if content and len(content) > 50:  # Meaningful content
                return content

        # Look for perpetual securities mentions in other sections
        perpetual_mentions = re.finditer(
            r'perpetual\s+(?:securities|preferred|units)[^.]*\.',
            phase4_content,
            re.IGNORECASE
        )

        mentions = [match.group(0).strip() for match in perpetual_mentions]
        if mentions:
            return '\n'.join(mentions)

    # Check Phase 2 debt structure for perpetuals
    if phase2_data:
        debt_structure = phase2_data.get('debt_structure', {})
        perpetual_debt = debt_structure.get('perpetual_securities', 0)

        if perpetual_debt and perpetual_debt > 0:
            return f"Perpetual securities outstanding: ${perpetual_debt/1000:,.1f}M"

        # Check for preferred units/shares
        balance_sheet = phase2_data.get('balance_sheet', {})
        preferred_equity = balance_sheet.get('preferred_equity', 0)

        if preferred_equity and preferred_equity > 0:
            return f"Preferred equity (perpetual): ${preferred_equity/1000:,.1f}M"

    # Check Phase 3 for perpetual adjustments
    if phase3_data:
        leverage_metrics = phase3_data.get('leverage_metrics', {})
        perpetual_adjustments = leverage_metrics.get('perpetual_securities_adjustment', 0)

        if perpetual_adjustments and perpetual_adjustments > 0:
            return f"Perpetual securities adjustment in leverage calculation: ${perpetual_adjustments/1000:,.1f}M"

    # Default: No perpetual securities found
    return 'Not applicable - no perpetual securities in capital structure'


def generate_final_report(metrics, analysis_sections, template, phase2_data=None):
    """
    Generate final report by combining metrics and analysis with template

    Args:
        metrics: Phase 3 metrics dictionary
        analysis_sections: Phase 4 analysis sections
        template: Report template string
        phase2_data: Phase 2 extraction data (optional, for reconciliation tables)

    Returns:
        str: Complete report
    """

    # Extract metrics
    issuer_name = metrics.get('issuer_name', 'Unknown Issuer')
    reporting_date = metrics.get('reporting_date', 'Unknown')
    report_period = metrics.get('reporting_period', 'Unknown')  # Use consistent field name from Phase 2/3
    currency = metrics.get('currency', 'CAD')

    leverage_metrics = metrics.get('leverage_metrics', {})
    reit_metrics = metrics.get('reit_metrics', {})
    coverage_ratios = metrics.get('coverage_ratios', {})
    portfolio_metrics = metrics.get('portfolio_metrics', {})

    # Extract AFCF, burn rate, and liquidity metrics (v1.0.6, v1.0.7)
    afcf_metrics = metrics.get('afcf_metrics', {})
    afcf_coverage = metrics.get('afcf_coverage', {})
    burn_rate_analysis = metrics.get('burn_rate_analysis', {})
    cash_runway = metrics.get('cash_runway', {})
    liquidity_position = metrics.get('liquidity_position', {})
    liquidity_risk = metrics.get('liquidity_risk', {})
    sustainable_burn = metrics.get('sustainable_burn', {})

    # ACFO metrics are stored in reit_metrics, not as top-level acfo_metrics
    acfo_metrics = {
        'acfo': reit_metrics.get('acfo'),
        'acfo_per_unit': reit_metrics.get('acfo_per_unit'),
        'acfo_per_unit_diluted': reit_metrics.get('acfo_per_unit_diluted'),
        'acfo_payout_ratio': reit_metrics.get('acfo_payout_ratio'),
        'data_source': 'calculated' if reit_metrics.get('acfo') else None,
        'acfo_calculation_detail': reit_metrics.get('acfo_calculation_detail', {}),
        'acfo_validation': reit_metrics.get('acfo_validation', {}),
        'data_quality': reit_metrics.get('acfo_calculation_detail', {}).get('data_quality')
    } if reit_metrics.get('acfo') else {}

    # Extract specific values
    total_debt = leverage_metrics.get('total_debt', 0)
    net_debt = leverage_metrics.get('net_debt', 0)
    gross_assets = leverage_metrics.get('gross_assets', 0)
    debt_to_assets = leverage_metrics.get('debt_to_assets_percent', 0)
    net_debt_ratio = leverage_metrics.get('net_debt_ratio', 0)

    # Extract issuer-reported metrics (quarterly from Phase 2/3)
    ffo = reit_metrics.get('ffo', 0)
    affo = reit_metrics.get('affo', 0)
    ffo_per_unit = reit_metrics.get('ffo_per_unit', 0)
    affo_per_unit = reit_metrics.get('affo_per_unit', 0)
    ffo_payout = reit_metrics.get('ffo_payout_ratio', 0)
    affo_payout = reit_metrics.get('affo_payout_ratio', 0)

    # Get YTD distributions per unit (for consistency with YTD ACFO/AFCF totals)
    # Phase 2 has ytd_2025.distributions_per_unit which matches the YTD period
    distributions = reit_metrics.get('distributions_per_unit', 0)  # Default to quarterly
    if phase2_data:
        ytd_distributions = phase2_data.get('ffo_affo', {}).get('ytd_2025', {}).get('distributions_per_unit')
        if ytd_distributions:
            distributions = ytd_distributions  # Use YTD if available

    noi_coverage = coverage_ratios.get('noi_interest_coverage', 0)
    annualized_interest = coverage_ratios.get('annualized_interest_expense', 0)
    quarterly_interest = coverage_ratios.get('quarterly_interest_expense', 0)

    occupancy = portfolio_metrics.get('occupancy_rate', 0) * 100  # Convert decimal to percentage
    occupancy_with_commitments = portfolio_metrics.get('occupancy_including_commitments', 0) * 100  # Convert decimal to percentage
    noi_growth = portfolio_metrics.get('same_property_noi_growth', 0) * 100  # Convert decimal to percentage
    property_count = portfolio_metrics.get('total_properties', 0)
    gla = portfolio_metrics.get('gla_sf', 0) / 1_000_000  # Convert to millions

    # Extract enriched data (Issue #40: market, macro, distribution history, prediction)
    # Check if metrics contains enriched data (market_risk key present and not None)
    # Note: load_metrics() merges enriched data at top level, so check for market_risk directly
    if metrics.get('market_risk') is not None:
        # Enriched data from enrich_phase4_data.py (merged at top level by load_metrics)
        market_risk = metrics.get('market_risk', {})
        macro_environment = metrics.get('macro_environment', {})
        distribution_history = metrics.get('distribution_history', {})
        distribution_prediction = metrics.get('distribution_cut_prediction', {})
        print("✓ Using enriched data for market/macro/prediction sections")
    else:
        # No enriched data - use empty dictionaries (graceful degradation)
        market_risk = {}
        macro_environment = {}
        distribution_history = {}
        distribution_prediction = {}
        print("⚠️  No enriched data found - market/macro/prediction sections will show N/A")

    # Generate assessments
    leverage_level, leverage_rating, leverage_threshold = assess_leverage(debt_to_assets)
    coverage_level, coverage_rating, coverage_threshold = assess_coverage(noi_coverage)
    ffo_assessment = assess_payout_ratio(ffo_payout, "FFO")
    affo_assessment = assess_payout_ratio(affo_payout, "AFFO")
    occupancy_assessment = assess_occupancy(occupancy)
    noi_growth_assessment = assess_noi_growth(noi_growth)

    # Generate reconciliation tables (v1.0.11+ comprehensive extraction)
    # Use Phase 2 extraction data for reconciliations if available
    recon_data_source = phase2_data if phase2_data else metrics

    try:
        # FFO/AFFO Reconciliation Table
        ffo_affo_recon_data = generate_ffo_affo_reconciliation(recon_data_source)
        ffo_affo_table = format_reconciliation_table(ffo_affo_recon_data) if ffo_affo_recon_data else "Insufficient data - FFO/AFFO reconciliation not available. Enable comprehensive Phase 2 extraction for detailed reconciliations."
    except Exception as e:
        ffo_affo_table = f"Error generating FFO/AFFO reconciliation: {str(e)}"

    try:
        # ACFO Reconciliation Table
        acfo_recon_data = generate_acfo_reconciliation(recon_data_source)
        acfo_table = format_acfo_reconciliation_table(acfo_recon_data) if acfo_recon_data else "Insufficient data - ACFO reconciliation not available. Requires cash flow statement data in Phase 2 extraction."
    except Exception as e:
        acfo_table = f"Error generating ACFO reconciliation: {str(e)}"

    # Generate issuer-reported reconciliation tables (v1.0.13+)
    try:
        # FFO/AFFO Reconciliation Table (ISSUER-REPORTED)
        ffo_affo_recon_reported = generate_issuer_reported_ffo_affo_reconciliation(phase2_data) if phase2_data else None
        ffo_affo_table_reported = format_issuer_reported_ffo_affo_reconciliation(ffo_affo_recon_reported)
    except Exception as e:
        ffo_affo_table_reported = f"Error generating issuer-reported FFO/AFFO reconciliation: {str(e)}"

    try:
        # ACFO Reconciliation Table (ISSUER-REPORTED)
        acfo_recon_reported = generate_issuer_reported_acfo_reconciliation(phase2_data) if phase2_data else None
        acfo_table_reported = format_issuer_reported_acfo_reconciliation(acfo_recon_reported)
    except Exception as e:
        acfo_table_reported = f"Error generating issuer-reported ACFO reconciliation: {str(e)}"

    # AFFO Validation Summary
    affo_calculation_detail = reit_metrics.get('affo_calculation_detail', {})
    affo_validation_data = reit_metrics.get('validation', {})
    affo_validation_summary = generate_affo_validation_summary(affo_calculation_detail, affo_validation_data)

    # ACFO Validation Summary
    acfo_validation_summary = generate_acfo_validation_summary(acfo_metrics)

    # AFCF Tables
    cfi_breakdown_table = format_cfi_breakdown_table(afcf_metrics.get('cfi_breakdown'), currency)

    acfo_value = acfo_metrics.get('acfo', 0)
    afcf_value = afcf_metrics.get('afcf', 0)
    net_cfi_value = afcf_metrics.get('net_cfi', 0)
    afcf_recon_table = format_afcf_reconciliation_table(acfo_value, afcf_value, net_cfi_value, currency)

    # Bridge Analysis (Section 2.6) - FFO → AFFO → ACFO
    # Extract calculated values
    ffo_calculated = reit_metrics.get('ffo_calculated', 0) or 0
    affo_calculated = reit_metrics.get('affo_calculated', 0) or 0
    acfo_calculated = reit_metrics.get('acfo_calculated', 0) or 0

    # FFO → AFFO Bridge (Calculated vs Reported)
    # Try calculated values first
    if ffo_calculated and affo_calculated:
        ffo_affo_reduction_calc = ffo_calculated - affo_calculated
        ffo_affo_reduction_pct = (ffo_affo_reduction_calc / ffo_calculated * 100) if ffo_calculated else 0

        # Get top adjustments from AFFO calculation detail
        affo_calc_detail = reit_metrics.get('affo_calculation_detail', {})
        affo_adjustments = affo_calc_detail.get('adjustments_detail', {})
        ffo_affo_top_adjustments = generate_top_adjustments_list(affo_adjustments, top_n=5)

        # If calculated has no material adjustments (reserve methodology), use reported values
        if "No material adjustments" in ffo_affo_top_adjustments or ffo_affo_reduction_calc == 0:
            # Try to use reported values instead
            ffo_reported = reit_metrics.get('ffo', 0) or 0
            affo_reported = reit_metrics.get('affo', 0) or 0

            if ffo_reported and affo_reported and ffo_reported != affo_reported:
                # Use reported values for bridge
                ffo_affo_reduction_calc = ffo_reported - affo_reported
                ffo_affo_reduction_pct = (ffo_affo_reduction_calc / ffo_reported * 100) if ffo_reported else 0

                # Check for reserve methodology note
                reserve_methodology = affo_calc_detail.get('reserve_methodology', '')
                if reserve_methodology:
                    ffo_affo_top_adjustments = f"**Reserve Methodology Used:** {reserve_methodology}\n\n**Note:** Detailed component breakdown not disclosed by issuer. Total adjustment of ${ffo_affo_reduction_calc:,.0f}k represents sustaining capital reserve."
                else:
                    ffo_affo_top_adjustments = f"**Note:** Detailed component breakdown not disclosed by issuer. Total adjustment of ${ffo_affo_reduction_calc:,.0f}k calculated from reported FFO and AFFO values."
    else:
        ffo_affo_reduction_calc = 0
        ffo_affo_reduction_pct = 0
        ffo_affo_top_adjustments = "FFO/AFFO calculation detail not available"

    # AFFO → ACFO Bridge (Calculated)
    if affo_calculated is not None and acfo_calculated:
        affo_acfo_adjustment = acfo_calculated - affo_calculated
        affo_acfo_adjustment_pct = (affo_acfo_adjustment / affo_calculated * 100) if affo_calculated and affo_calculated != 0 else 0

        # Get top adjustments from ACFO calculation detail
        acfo_calc_detail = reit_metrics.get('acfo_calculation_detail', {})
        acfo_adjustments = acfo_calc_detail.get('adjustments_detail', {})
        affo_acfo_top_adjustments = generate_top_adjustments_list(acfo_adjustments, top_n=5)
    else:
        affo_acfo_adjustment = 0
        affo_acfo_adjustment_pct = 0
        affo_acfo_top_adjustments = "ACFO calculation detail not available"

    # Gap Analysis Interpretation
    # Use calculated ACFO, but use reported AFFO if calculated AFFO had no adjustments
    affo_for_comparison = affo_calculated
    affo_comparison_source = "calculated"

    # If we used reported values for FFO→AFFO bridge, use reported AFFO for gap analysis too
    if ffo_affo_reduction_calc != 0 and (affo_calculated == 0 or ffo_calculated == affo_calculated):
        affo_reported = reit_metrics.get('affo', 0) or 0
        if affo_reported:
            affo_for_comparison = affo_reported
            affo_comparison_source = "reported"

    if acfo_calculated and affo_for_comparison:
        gap = acfo_calculated - affo_for_comparison
        gap_pct = (gap / affo_for_comparison * 100) if affo_for_comparison and affo_for_comparison != 0 else 0

        if acfo_calculated > affo_for_comparison:
            gap_interpretation = f"ACFO (${acfo_calculated:,.0f}k calculated) exceeds AFFO (${affo_for_comparison:,.0f}k {affo_comparison_source}) by ${abs(gap):,.0f}k ({abs(gap_pct):.1f}%). This indicates stronger cash generation when accounting for working capital changes and actual capital expenditures."
        elif acfo_calculated < affo_for_comparison:
            gap_interpretation = f"ACFO (${acfo_calculated:,.0f}k calculated) is below AFFO (${affo_for_comparison:,.0f}k {affo_comparison_source}) by ${abs(gap):,.0f}k ({abs(gap_pct):.1f}%). This indicates that ACFO provides a more conservative measure of sustainable cash flow after accounting for working capital changes and actual capital expenditures."
        else:
            gap_interpretation = f"ACFO equals AFFO (${acfo_calculated:,.0f}k), indicating no material working capital impact on cash flow."
    elif acfo_calculated and not affo_for_comparison:
        gap_interpretation = "ACFO calculated but AFFO not available for comparison"
    else:
        gap_interpretation = "ACFO not calculated - requires cash flow statement data"

    # Dilution analysis (v1.0.8)
    dilution_analysis = metrics.get('dilution_analysis', {})

    # Extract Phase 4 sections (with flexible lookup for variations)
    def get_section(sections, *possible_names):
        """Try multiple section name variations with case-insensitive matching"""
        for name in possible_names:
            # Try exact match (case-insensitive)
            for key in sections:
                if key.upper() == name.upper():
                    return sections[key]
            # Try partial match (case-insensitive)
            for key in sections:
                if key.upper().startswith(name.upper()):
                    return sections[key]
        return 'Not available'

    # Phase 4 Output Format Standard v1.0.0 - Use EXACT headers (no variations)
    # See: docs/PHASE4_OUTPUT_FORMAT_STANDARD.md
    exec_summary = get_section(analysis_sections, '1. Credit Opinion Summary')
    scorecard_table = get_section(analysis_sections, '2. Key Credit Factors')
    rating_outlook = get_section(analysis_sections, '3. Rating Outlook')
    credit_strengths = get_section(analysis_sections, '5. Credit Strengths')  # Optional - can synthesize from scorecard
    credit_challenges = get_section(analysis_sections, '6. Credit Challenges')  # Optional - can synthesize from scorecard

    # Upgrade/downgrade factors are embedded in Rating Outlook section
    upgrade_factors = 'Not available'
    downgrade_factors = 'Not available'

    # For backward compatibility with older Phase 4 outputs, fall back to variations if needed
    if exec_summary == 'Not available':
        exec_summary = get_section(analysis_sections, 'Executive Summary', 'EXECUTIVE SUMMARY', 'Credit Opinion Summary', 'CREDIT OPINION SUMMARY')
        print("⚠️  WARNING: Phase 4 used non-standard header. Please update Phase 4 agent to use '1. Credit Opinion Summary'")

    if scorecard_table == 'Not available':
        scorecard_table = get_section(analysis_sections, 'Factor-by-Factor Scoring', 'Five-Factor Rating Scorecard Analysis', '5-Factor Rating Scorecard', 'Five-Factor Scorecard', 'Five-Factor Rating Scorecard', 'FIVE-FACTOR CREDIT SCORECARD', 'Rating Methodology and Scorecard', 'Scorecard Assessment', 'Key Credit Factors', 'KEY CREDIT FACTORS')
        print("⚠️  WARNING: Phase 4 used non-standard header. Please update Phase 4 agent to use '2. Key Credit Factors'")

    if rating_outlook == 'Not available':
        rating_outlook = get_section(analysis_sections, 'Rating Outlook', 'RATING OUTLOOK')
        print("⚠️  WARNING: Phase 4 used non-standard header. Please update Phase 4 agent to use '3. Rating Outlook'")

    # Add fallbacks for Credit Strengths and Credit Challenges (Issue #52)
    if credit_strengths == 'Not available':
        credit_strengths = get_section(analysis_sections, 'Credit Strengths', 'CREDIT STRENGTHS', 'Strengths', 'STRENGTHS')
        if credit_strengths != 'Not available':
            print("⚠️  WARNING: Phase 4 used non-standard header for Credit Strengths. Please update Phase 4 agent to use '5. Credit Strengths'")

    if credit_challenges == 'Not available':
        credit_challenges = get_section(analysis_sections, 'Credit Challenges', 'CREDIT CHALLENGES', 'Credit Concerns', 'CREDIT CONCERNS', 'Challenges', 'CHALLENGES', 'Concerns', 'CONCERNS')
        if credit_challenges != 'Not available':
            print("⚠️  WARNING: Phase 4 used non-standard header for Credit Challenges. Please update Phase 4 agent to use '6. Credit Challenges'")

    key_observations = get_section(analysis_sections, 'Key Observations', 'KEY OBSERVATIONS AND CONCLUSIONS')

    # Extract key drivers from Executive Summary (look for bullets after "Key Credit Drivers:")
    drivers = []
    if exec_summary and 'Key Credit Drivers:' in exec_summary:
        # Extract section after "Key Credit Drivers:"
        drivers_section = exec_summary.split('Key Credit Drivers:')[1].split('\n\n')[0]
        # Extract bullet points
        for line in drivers_section.split('\n'):
            line = line.strip()
            if line.startswith('-') or line.startswith('•'):
                drivers.append(line.lstrip('-•').strip())

        # Remove "Key Credit Drivers:" section from executive summary to avoid duplication
        # Template will re-add it with numbered list
        exec_summary = exec_summary.split('**Key Credit Drivers:**')[0].strip()

    # If no drivers found in exec summary, try to extract from Key Credit Factors table
    if not drivers and scorecard_table:
        # Extract factor names from markdown table (format: | **1. Factor Name** | Weight | Assessment | Score | Rationale |)
        for line in scorecard_table.split('\n'):
            # Look for table rows with factors (starts with |, contains "**", and has "Factor" in it)
            if line.strip().startswith('|') and '**' in line and not line.startswith('|---') and not line.startswith('| **Factor**'):
                # Extract text between ** ** (factor name)
                factor_match = re.search(r'\*\*([^\*]+)\*\*', line)
                if factor_match:
                    factor_text = factor_match.group(1).strip()
                    # Remove leading numbers (e.g., "1. " or "1)")
                    factor_text = re.sub(r'^\d+[\.\)]\s*', '', factor_text)
                    # Skip header rows
                    if factor_text and 'Factor' not in factor_text:
                        drivers.append(factor_text)

    # Remove "Scorecard-Indicated Rating:" from exec summary if present (template adds it)
    if exec_summary and 'Scorecard-Indicated Rating:' in exec_summary:
        # Remove just the first line with the rating
        exec_summary = re.sub(r'\*\*Scorecard-Indicated Rating:\s*[^\n]+\*\*\n\n', '', exec_summary)

    # Synthesize Credit Strengths and Credit Challenges from scorecard table if not available
    if credit_strengths == 'Not available' and scorecard_table:
        strengths_list = []
        challenges_list = []

        for line in scorecard_table.split('\n'):
            if line.strip().startswith('|') and '**' in line and not line.startswith('|---'):
                # Parse table row: | **Factor** | Weight | Assessment | Score | Rationale |
                cells = [cell.strip() for cell in line.split('|')]
                if len(cells) >= 6:
                    factor_match = re.search(r'\*\*([^\*]+)\*\*', cells[1])
                    score_match = re.search(r'(\d+)/5', cells[4])  # Score column
                    rationale = cells[5] if len(cells) > 5 else ''

                    if factor_match and score_match:
                        factor_name = factor_match.group(1).strip()
                        factor_name = re.sub(r'^\d+[\.\)]\s*', '', factor_name)  # Remove numbers
                        score = int(score_match.group(1))

                        # Skip header rows
                        if 'Factor' in factor_name or 'Overall' in factor_name:
                            continue

                        # Strengths: score >= 4, Challenges: score <= 2
                        if score >= 4:
                            strengths_list.append(f"- **{factor_name}:** {rationale}")
                        elif score <= 2:
                            challenges_list.append(f"- **{factor_name}:** {rationale}")

        if strengths_list:
            credit_strengths = '\n'.join(strengths_list)
        if challenges_list:
            credit_challenges = '\n'.join(challenges_list)

    # Extract outlook value from Phase 4 analysis
    outlook = 'Stable'  # default fallback
    if rating_outlook:
        # Search for "**Outlook: NEGATIVE**" or "Outlook: STABLE", etc.
        outlook_match = re.search(r'\*\*Outlook:\s+(\w+)\*\*', rating_outlook)
        if outlook_match:
            outlook = outlook_match.group(1)  # Extract: NEGATIVE, STABLE, POSITIVE, etc.

    # Remove duplicate header if present (after extracting the value)
    if rating_outlook and rating_outlook.startswith('**Outlook:'):
        # Remove the duplicate "Outlook: STABLE" header that's already in the narrative
        rating_outlook = re.sub(r'^\*\*Outlook:\s+\w+\*\*\n\n', '', rating_outlook)

    # Extract upgrade/downgrade factors from Rating Outlook section (Phase 4 Format Standard v1.0.0)
    if rating_outlook and rating_outlook != 'Not available':
        # Primary extraction: Use exact subsection titles from standard
        upgrade_match = re.search(r'\*\*Rating Upgrade Factors[^\n]*\*\*:?(.*?)(?=\*\*Rating Downgrade Factors|\*\*Key Monitoring|---|\Z)', rating_outlook, re.DOTALL)
        if upgrade_match:
            upgrade_factors = upgrade_match.group(1).strip()
        elif upgrade_factors == 'Not available':
            # Backward compatibility: Fall back to old variations
            upgrade_match = re.search(r'\*\*Upgrade Scenarios[^\n]*\*\*:?(.*?)(?=\*\*Downgrade Scenarios|---|\Z)', rating_outlook, re.DOTALL)
            if upgrade_match:
                upgrade_factors = upgrade_match.group(1).strip()
                print("⚠️  WARNING: Phase 4 used non-standard subsection '**Upgrade Scenarios**'. Please update to '**Rating Upgrade Factors**'")

    if rating_outlook and rating_outlook != 'Not available':
        # Primary extraction: Use exact subsection title from standard
        downgrade_match = re.search(r'\*\*Rating Downgrade Factors[^\n]*\*\*:?(.*?)(?=---|\Z)', rating_outlook, re.DOTALL)
        if downgrade_match:
            downgrade_factors = downgrade_match.group(1).strip()
        elif downgrade_factors == 'Not available':
            # Backward compatibility: Fall back to old variations
            downgrade_match = re.search(r'\*\*Downgrade Scenarios[^\n]*\*\*:?(.*?)(?=---|\Z)', rating_outlook, re.DOTALL)
            if downgrade_match:
                downgrade_factors = downgrade_match.group(1).strip()
                print("⚠️  WARNING: Phase 4 used non-standard subsection '**Downgrade Scenarios**'. Please update to '**Rating Downgrade Factors**'")

    # Enhanced template sections (from Report A)
    company_background = get_section(analysis_sections, 'Company Background', 'COMPANY BACKGROUND', 'Company Profile', 'COMPANY PROFILE', 'Profile', 'PROFILE', 'Background', 'BACKGROUND')
    business_strategy = get_section(analysis_sections, 'Business Strategy', 'BUSINESS STRATEGY', 'Strategy', 'STRATEGY', 'Strategic Direction', 'STRATEGIC DIRECTION')
    portfolio_composition_detail = get_section(analysis_sections, 'Portfolio Composition', 'PORTFOLIO COMPOSITION')
    management_governance = get_section(analysis_sections, 'Management and Governance', 'MANAGEMENT AND GOVERNANCE')
    peer_comparison = get_section(analysis_sections, 'Peer Comparison', 'PEER COMPARISON', 'Peer Analysis', 'PEER ANALYSIS', 'Competitive Position', 'COMPETITIVE POSITION', 'Competitive Positioning', 'COMPETITIVE POSITIONING')
    earnings_analysis = get_section(analysis_sections, 'Earnings Analysis', 'EARNINGS ANALYSIS')
    leverage_coverage_detail = get_section(analysis_sections, 'Leverage and Coverage Analysis', 'LEVERAGE AND COVERAGE ANALYSIS')
    growth_strategy = get_section(analysis_sections, 'Growth Strategy and Capital Allocation', 'GROWTH STRATEGY', 'Capital Allocation')
    operating_track_record = get_section(analysis_sections, 'Operating Track Record and Portfolio Quality', 'OPERATING TRACK RECORD', 'Portfolio Quality')

    # Get full ESG section and parse into components (Issue #29)
    esg_section = get_section(analysis_sections, 'ESG Considerations', 'ESG', 'Environmental', 'Social', 'Governance')
    parsed_esg = parse_esg_section(esg_section)
    environmental_analysis = parsed_esg.get('ENVIRONMENTAL_ANALYSIS', 'Not available')
    social_analysis = parsed_esg.get('SOCIAL_ANALYSIS', 'Not available')
    governance_analysis = parsed_esg.get('GOVERNANCE_ANALYSIS', 'Not available')

    scenario_analysis = get_section(analysis_sections, 'Scenario Analysis and Stress Testing', 'SCENARIO ANALYSIS', 'Stress Testing')

    # Parse scenario analysis into individual components (Issue #28)
    parsed_scenarios = parse_scenario_analysis(scenario_analysis)

    # Parse structural considerations from Phase 4 content (Issue #32)
    # Reconstruct full Phase 4 content for parsing
    phase4_full_content = '\n\n'.join([f"## {k}\n{v}" for k, v in analysis_sections.items()])

    debt_structure = parse_debt_structure(phase4_full_content, phase2_data, metrics)
    collateral_analysis = parse_security_collateral(phase4_full_content, phase2_data, metrics)
    perpetual_securities = check_perpetual_securities(phase4_full_content, phase2_data, metrics)

    debt_reconciliation = get_section(analysis_sections, 'Moody\'s-Adjusted Debt Reconciliation', 'Debt Reconciliation', 'DEBT RECONCILIATION')
    ebitda_reconciliation = get_section(analysis_sections, 'Moody\'s-Adjusted EBITDA Reconciliation', 'EBITDA Reconciliation', 'EBITDA RECONCILIATION')

    # ========================================
    # Pre-calculate values for reported vs calculated sections (v1.0.12)
    # ========================================
    # Extract reported metrics from Phase 2
    # Prefer YTD values for consistency with YTD ACFO/AFCF totals (Issue #33 period mismatch fix)
    ffo_affo_reported = phase2_data.get('ffo_affo', {}) if phase2_data else {}

    # Override with YTD values if available (for multi-quarter reports)
    if phase2_data:
        ytd_section = phase2_data.get('ffo_affo', {}).get('ytd_2025', {})
        if ytd_section:
            # Merge YTD values over quarterly values for consistency
            ffo_affo_reported = {**ffo_affo_reported, **ytd_section}

    # Get distributions per unit (now YTD if available)
    distributions_per_unit_reported = ffo_affo_reported.get('distributions_per_unit', distributions)

    # Get unit counts for per-unit calculations
    # Priority: Phase 3 balance_sheet → Phase 2 balance_sheet → fallback to 100,000
    balance_sheet = metrics.get('balance_sheet', {})
    common_units = balance_sheet.get('common_units_outstanding')

    # Fallback to Phase 2 if Phase 3 doesn't have it
    if not common_units and phase2_data:
        common_units = phase2_data.get('balance_sheet', {}).get('common_units_outstanding')

    # Final fallback (should rarely happen with proper extraction)
    if not common_units:
        common_units = 100000

    # Get diluted units with same fallback chain
    diluted_units = balance_sheet.get('diluted_units_outstanding')
    if not diluted_units and phase2_data:
        diluted_units = phase2_data.get('balance_sheet', {}).get('diluted_units_outstanding')
    if not diluted_units:
        diluted_units = common_units

    # Calculate total distributions for coverage ratios
    distributions_total = distributions * common_units if distributions and common_units else 0

    # Calculate residual cash flows after distributions (Issue #31)
    # Use total_distributions from afcf_coverage (YTD total) not distributions_total (quarterly × units)
    acfo_amount = acfo_metrics.get('acfo', 0) if acfo_metrics else 0
    afcf_amount = afcf_metrics.get('afcf', 0) if afcf_metrics else 0
    total_distributions_ytd = afcf_coverage.get('total_distributions', 0)
    residual_acfo = acfo_amount - total_distributions_ytd if acfo_amount and total_distributions_ytd else None
    residual_afcf = afcf_amount - total_distributions_ytd if afcf_amount and total_distributions_ytd else None

    # Extract total-level coverage metrics from Phase 3 (Issue #33)
    # These are comprehensive metrics from afcf_coverage section
    afcf_debt_service_cov = afcf_coverage.get('afcf_debt_service_coverage')
    afcf_dist_cov_total = afcf_coverage.get('afcf_distribution_coverage')
    afcf_self_funding = afcf_coverage.get('afcf_self_funding_ratio')
    total_debt_service = afcf_coverage.get('total_debt_service', 0)
    afcf_self_funding_capacity = afcf_coverage.get('afcf_self_funding_capacity', 0)

    # Calculate total-level ACFO distribution coverage (ACFO doesn't have a coverage section in Phase 3)
    acfo_dist_cov_total = (acfo_amount / total_distributions_ytd) if acfo_amount and total_distributions_ytd else None

    # Calculate reported coverage ratios (per-unit basis)
    ffo_rep = ffo_affo_reported.get('ffo', ffo)
    affo_rep = ffo_affo_reported.get('affo', affo)
    acfo_rep = ffo_affo_reported.get('acfo', 0)

    # Convert reported totals to per-unit for coverage calculations
    ffo_per_unit_rep = ffo_affo_reported.get('ffo_per_unit', calculate_per_unit(ffo_rep, common_units))
    affo_per_unit_rep = ffo_affo_reported.get('affo_per_unit', calculate_per_unit(affo_rep, common_units))
    acfo_per_unit_rep = ffo_affo_reported.get('acfo_per_unit', calculate_per_unit(acfo_rep, common_units)) if acfo_rep else None

    # Calculate coverage ratios using per-unit values
    ffo_cov_rep = calculate_coverage_ratio(ffo_per_unit_rep, distributions)

    # Format variance percentages with None handling
    ffo_var_pct = reit_metrics.get('validation', {}).get('ffo_variance_percent')
    ffo_var_formatted = f"{ffo_var_pct:.1f}%" if ffo_var_pct is not None else "N/A (not reported)"

    affo_var_pct = reit_metrics.get('validation', {}).get('affo_variance_percent')
    affo_var_formatted = f"{affo_var_pct:.1f}%" if affo_var_pct is not None else "N/A (not reported)"
    affo_cov_rep = calculate_coverage_ratio(affo_per_unit_rep, distributions)
    acfo_cov_rep = calculate_coverage_ratio(acfo_per_unit_rep, distributions) if acfo_per_unit_rep else None

    # Get calculated coverage ratios from Phase 3 (per-unit basis)
    coverage_ratios_detail = reit_metrics.get('coverage_ratios', {})

    # Calculate per-unit values for calculated metrics (from *_calculation_detail objects)
    ffo_calc = reit_metrics.get('ffo_calculated', ffo)
    ffo_calc_detail = reit_metrics.get('ffo_calculation_detail', {})
    ffo_per_unit_calc = ffo_calc_detail.get('ffo_per_unit', calculate_per_unit(ffo_calc, common_units))

    affo_calc = reit_metrics.get('affo_calculated', affo)
    affo_calc_detail = reit_metrics.get('affo_calculation_detail', {})
    affo_per_unit_calc = affo_calc_detail.get('affo_per_unit', calculate_per_unit(affo_calc, common_units))

    acfo_calc_detail = acfo_metrics.get('acfo_calculation_detail', {}) if acfo_metrics else {}
    acfo_per_unit_calc = acfo_calc_detail.get('acfo_per_unit', calculate_per_unit(acfo_metrics.get('acfo', 0), common_units)) if acfo_metrics.get('acfo') else None

    afcf_per_unit_calc = afcf_metrics.get('afcf_per_unit', calculate_per_unit(afcf_metrics.get('afcf', 0), common_units)) if afcf_metrics.get('afcf') else None

    # Calculate coverage ratios using per-unit values
    ffo_cov_calc = coverage_ratios_detail.get('ffo_coverage', calculate_coverage_ratio(ffo_per_unit_calc, distributions))
    affo_cov_calc = coverage_ratios_detail.get('affo_coverage', calculate_coverage_ratio(affo_per_unit_calc, distributions))
    acfo_cov_calc = coverage_ratios_detail.get('acfo_coverage', calculate_coverage_ratio(acfo_per_unit_calc, distributions)) if acfo_per_unit_calc else None
    afcf_cov_calc = calculate_coverage_ratio(afcf_per_unit_calc, distributions) if afcf_per_unit_calc else None

    # FFO to AFFO bridge (reported)
    ffo_to_affo_reduction_rep = ffo_rep - affo_rep if ffo_rep and affo_rep else 0
    ffo_to_affo_pct_rep = (ffo_to_affo_reduction_rep / ffo_rep * 100) if ffo_rep else 0

    # Gap analysis (reported)
    affo_acfo_gap_rep = affo_rep - acfo_rep if affo_rep and acfo_rep else 0
    affo_acfo_gap_pct_rep = (affo_acfo_gap_rep / affo_rep * 100) if affo_rep and acfo_rep else 0

    # Gap analysis (calculated)
    affo_calc = reit_metrics.get('affo_calculated', affo)
    acfo_calc = acfo_metrics.get('acfo', 0) if acfo_metrics else 0
    affo_acfo_gap_calc = affo_calc - acfo_calc if affo_calc and acfo_calc else 0
    affo_acfo_gap_pct_calc = (affo_acfo_gap_calc / affo_calc * 100) if affo_calc and acfo_calc else 0

    # AFCF from Reported ACFO (if available)
    net_cfi = phase2_data.get('cash_flow_investing', {}).get('total_cfi', 0) if phase2_data else 0
    afcf_rep_based = acfo_rep + net_cfi if acfo_rep else None

    # Extract validation data
    validation = reit_metrics.get('validation', {})
    acfo_validation = acfo_metrics.get('acfo_validation', {}) if acfo_metrics else {}

    # Pre-calculate payout ratios for calculated metrics (Issue #57: handle negative values)
    # When metric is negative (loss), payout ratio is meaningless → returns None → displays as "N/A"
    # IMPORTANT: Get per-unit values from calculation_detail sections (not top-level issuer-reported values)
    ffo_per_unit_calc = reit_metrics.get('ffo_calculation_detail', {}).get('ffo_per_unit_diluted')
    affo_per_unit_calc = reit_metrics.get('affo_calculation_detail', {}).get('affo_per_unit_diluted')

    ffo_payout_calc = calculate_payout_ratio(ffo_per_unit_calc, distributions)
    affo_payout_calc = calculate_payout_ratio(affo_per_unit_calc, distributions)
    acfo_payout_calc = calculate_payout_ratio(acfo_metrics.get('acfo_per_unit_diluted'), distributions) if acfo_metrics else None
    afcf_payout_calc = calculate_payout_ratio(afcf_metrics.get('afcf_per_unit'), distributions) if afcf_metrics else None





    # Build replacements dictionary
    replacements = {
        'ISSUER_NAME': issuer_name,
        'REPORT_DATE': datetime.now().strftime('%B %d, %Y'),
        'REPORT_PERIOD': report_period,
        'REPORTING_PERIOD_FORMATTED': format_reporting_period(report_period),
        'REPORTING_DATE': reporting_date,
        'CURRENCY': currency,

        # Phase 4 sections
        'EXECUTIVE_SUMMARY': exec_summary,
        'CREDIT_STRENGTHS': credit_strengths,
        'CREDIT_CHALLENGES': credit_challenges,
        'RATING_OUTLOOK': rating_outlook,
        'UPGRADE_FACTORS': upgrade_factors,
        'DOWNGRADE_FACTORS': downgrade_factors,
        'SCORECARD_TABLE': scorecard_table,
        'KEY_OBSERVATIONS': key_observations,

        # Metrics
        'TOTAL_DEBT': f"{total_debt:,.0f}",
        'NET_DEBT': f"{net_debt:,.0f}",
        'GROSS_ASSETS': f"{gross_assets:,.0f}",
        'DEBT_TO_ASSETS': f"{debt_to_assets:.1f}",
        'NET_DEBT_RATIO': f"{net_debt_ratio:.1f}",

        'FFO': f"{ffo:,.0f}",
        'AFFO': f"{affo:,.0f}",
        'FFO_PER_UNIT': f"{ffo_per_unit:.2f}",
        'AFFO_PER_UNIT': f"{affo_per_unit:.2f}",
        'DISTRIBUTIONS_PER_UNIT': f"{distributions:.2f}",
        'FFO_PAYOUT': f"{ffo_payout:.1f}",
        'AFFO_PAYOUT': f"{affo_payout:.1f}",

        # ========================================
        # Section 2.2.1: Issuer-Reported Metrics (v1.0.12)
        # ========================================
        # FFO Reported
        'FFO_REPORTED': f"{ffo_affo_reported.get('ffo', ffo):,.0f}",
        'FFO_PER_UNIT_REPORTED': f"{ffo_affo_reported.get('ffo_per_unit', ffo_per_unit):.4f}",
        'FFO_PAYOUT_REPORTED': f"{calculate_payout_ratio(ffo_affo_reported.get('ffo_per_unit', ffo_per_unit), distributions_per_unit_reported) or 0:.1f}",

        # AFFO Reported
        'AFFO_REPORTED': f"{ffo_affo_reported.get('affo', affo):,.0f}",
        'AFFO_PER_UNIT_REPORTED': f"{ffo_affo_reported.get('affo_per_unit', affo_per_unit):.4f}",
        'AFFO_PAYOUT_REPORTED': f"{calculate_payout_ratio(ffo_affo_reported.get('affo_per_unit', affo_per_unit), distributions_per_unit_reported) or 0:.1f}",

        # ACFO Reported (if available - rare)
        'ACFO_REPORTED': f"{ffo_affo_reported.get('acfo', 0):,.0f}" if ffo_affo_reported.get('acfo') else 'Not reported',
        'ACFO_PER_UNIT_REPORTED': f"{ffo_affo_reported.get('acfo_per_unit', 0):.4f}" if ffo_affo_reported.get('acfo_per_unit') else 'N/A',
        'ACFO_PAYOUT_REPORTED': f"{calculate_payout_ratio(ffo_affo_reported.get('acfo_per_unit'), distributions_per_unit_reported):.1f}" if ffo_affo_reported.get('acfo_per_unit') else 'N/A',

        # ========================================
        # Section 2.2.2: REALPAC-Calculated Metrics (v1.0.12)
        # ========================================
        # FFO Calculated - Use Phase 3 per-unit values from calculation_detail (Issue #57)
        'FFO_CALCULATED': f"{reit_metrics.get('ffo_calculated', ffo):,.0f}",
        'FFO_PER_UNIT_CALCULATED': f"{ffo_per_unit_calc:.4f}" if ffo_per_unit_calc is not None else '0.0000',
        'FFO_PAYOUT_CALCULATED': f"{ffo_payout_calc:.1f}" if ffo_payout_calc is not None else 'N/A',

        # AFFO Calculated - Use Phase 3 per-unit values from calculation_detail (Issue #57)
        'AFFO_CALCULATED': f"{reit_metrics.get('affo_calculated', affo):,.0f}",
        'AFFO_PER_UNIT_CALCULATED': f"{affo_per_unit_calc:.4f}" if affo_per_unit_calc is not None else '0.0000',
        'AFFO_PAYOUT_CALCULATED': f"{affo_payout_calc:.1f}" if affo_payout_calc is not None else 'N/A',

        # ACFO Calculated - Use Phase 3 per-unit values (already corrected for unit mismatch)
        'ACFO_CALCULATED': f"{acfo_metrics.get('acfo', 0):,.0f}" if acfo_metrics.get('acfo') else 'Not available',
        'ACFO_PER_UNIT_CALCULATED': f"{acfo_metrics.get('acfo_per_unit_diluted', 0):.4f}" if acfo_metrics.get('acfo_per_unit_diluted') else 'Not available',  # Use Phase 3 value
        'ACFO_PAYOUT_CALCULATED': f"{acfo_payout_calc:.1f}" if acfo_payout_calc is not None else 'N/A',

        # AFCF Calculated
        'AFCF_CALCULATED': f"{afcf_metrics.get('afcf', 0):,.0f}" if afcf_metrics.get('afcf') else 'Not available',
        'AFCF_PER_UNIT_CALCULATED': f"{afcf_metrics.get('afcf_per_unit', 0):.4f}" if afcf_metrics.get('afcf_per_unit') else 'Not available',
        'AFCF_PAYOUT_CALCULATED': f"{afcf_payout_calc:.1f}" if afcf_payout_calc is not None else 'N/A',

        # ========================================
        # Variance Placeholders (Reported vs Calculated)
        # ========================================


        # FFO Variance
        'FFO_VARIANCE_PERCENT': f"{validation.get('ffo_variance_percent', 0):.1f}" if validation.get('ffo_variance_percent') is not None else 'N/A',
        'FFO_VARIANCE_FLAG': (
            "✓" if validation.get('ffo_within_threshold')
            else "⚠️"
        ) if validation.get('ffo_variance_percent') is not None else '-',
        'FFO_VALIDATION_STATUS': (
            f"✓ Validated: {validation.get('ffo_variance_percent', 0):.1f}% variance"
            if validation.get('ffo_within_threshold')
            else f"⚠️ Exceeds threshold: {validation.get('ffo_variance_percent', 0):.1f}% variance"
        ) if validation.get('ffo_variance_percent') is not None else 'Not available',

        # AFFO Variance
        'AFFO_VARIANCE_PERCENT': f"{validation.get('affo_variance_percent', 0):.1f}" if validation.get('affo_variance_percent') is not None else 'N/A',
        'AFFO_VARIANCE_FLAG': (
            "✓" if validation.get('affo_within_threshold')
            else "⚠️"
        ) if validation.get('affo_variance_percent') is not None else '-',
        'AFFO_VARIANCE': (
            f"{validation.get('affo_variance_amount', 0):,.0f} ({validation.get('affo_variance_percent', 0):+.1f}%)"
            if validation.get('affo_variance_amount') is not None and validation.get('affo_variance_percent') is not None
            else 'N/A'
        ),
        'AFFO_VALIDATION_STATUS': (
            f"✓ Validated: {validation.get('affo_variance_percent', 0):.1f}% variance"
            if validation.get('affo_within_threshold')
            else f"⚠️ Exceeds threshold: {validation.get('affo_variance_percent', 0):.1f}% variance"
        ) if validation.get('affo_variance_percent') is not None else 'Not available',

        # ACFO Variance
        'ACFO_VARIANCE_PERCENT': f"{acfo_validation.get('acfo_variance_percent', 0):.1f}" if acfo_validation.get('acfo_variance_percent') is not None else 'N/A',
        'ACFO_VARIANCE_FLAG': (
            "✓" if acfo_validation.get('acfo_within_threshold')
            else "⚠️"
        ) if acfo_validation.get('acfo_variance_percent') is not None else '-',
        'ACFO_VARIANCE': (
            f"{acfo_validation.get('acfo_variance_amount', 0):,.0f} ({acfo_validation.get('acfo_variance_percent', 0):+.1f}%)"
            if acfo_validation.get('acfo_variance_amount') is not None and acfo_validation.get('acfo_variance_percent') is not None
            else 'N/A (issuer did not report ACFO)'
        ),
        'ACFO_VALIDATION_STATUS': (
            f"✓ Validated: {acfo_validation.get('acfo_variance_percent', 0):.1f}% variance"
            if acfo_validation.get('acfo_within_threshold')
            else f"⚠️ Exceeds threshold: {acfo_validation.get('acfo_variance_percent', 0):.1f}% variance"
        ) if acfo_validation.get('acfo_variance_percent') is not None else 'Not available - issuer does not report ACFO',

        # AFCF Reported (issuers typically don't report AFCF as a standard metric)
        'AFCF_REPORTED': 'Not available',
        'AFCF_PER_UNIT_REPORTED': 'N/A',
        'AFCF_PAYOUT_REPORTED': 'N/A',

        # AFCF Variance (issuers typically don't report AFCF)
        'AFCF_VARIANCE_PERCENT': 'N/A (not reported)',
        'AFCF_VARIANCE_FLAG': '-',

        # ========================================
        # Section 2.5.1: Distribution Coverage (Reported)
        # ========================================




        'FFO_COVERAGE_REPORTED': f"{ffo_cov_rep:.2f}" if ffo_cov_rep else 'N/A',
        'FFO_COVERAGE_ASSESSMENT_REPORTED': assess_distribution_coverage(ffo_cov_rep),
        'AFFO_COVERAGE_REPORTED': f"{affo_cov_rep:.2f}" if affo_cov_rep else 'N/A',
        'AFFO_COVERAGE_ASSESSMENT_REPORTED': assess_distribution_coverage(affo_cov_rep),
        'ACFO_COVERAGE_REPORTED': f"{acfo_cov_rep:.2f}" if acfo_cov_rep else 'N/A',
        'ACFO_COVERAGE_ASSESSMENT_REPORTED': assess_distribution_coverage(acfo_cov_rep) if acfo_rep else 'Not reported',

        # ========================================
        # Section 2.5.2: Distribution Coverage (Calculated)
        # ========================================


        'FFO_COVERAGE_CALCULATED': f"{ffo_cov_calc:.2f}" if ffo_cov_calc else 'N/A',
        'AFFO_COVERAGE_CALCULATED': f"{affo_cov_calc:.2f}" if affo_cov_calc else 'N/A',
        'ACFO_COVERAGE_CALCULATED': f"{acfo_cov_calc:.2f}" if acfo_cov_calc else 'N/A',
        'FFO_COVERAGE_ASSESSMENT_CALCULATED': assess_distribution_coverage(ffo_cov_calc),
        'AFFO_COVERAGE_ASSESSMENT_CALCULATED': assess_distribution_coverage(affo_cov_calc),
        'ACFO_COVERAGE_ASSESSMENT_CALCULATED': assess_distribution_coverage(acfo_cov_calc) if acfo_cov_calc else 'Not available',

        # ========================================
        # Section 2.6.1: Bridge Analysis (Reported)
        # ========================================


        'FFO_TO_AFFO_REDUCTION_REPORTED': f"{ffo_to_affo_reduction_rep:,.0f}",
        'FFO_TO_AFFO_PERCENT_REPORTED': f"{ffo_to_affo_pct_rep:.1f}",
        'FFO_TO_AFFO_ADJUSTMENTS_REPORTED': generate_reported_adjustments_list(
            phase2_data.get('ffo_affo_components', {}) if phase2_data else {}
        ),
        'CFO_TO_ACFO_REDUCTION_REPORTED': 'N/A - issuer does not report ACFO',
        'CFO_TO_ACFO_PERCENT_REPORTED': 'N/A',

        # ========================================
        # Section 2.6.2: Bridge Analysis (Calculated)
        # ========================================
        # FFO → AFFO Bridge (uses calculated values from lines 930-948)
        'FFO_TO_AFFO_REDUCTION_CALCULATED': f"{ffo_affo_reduction_calc:,.0f}",
        'FFO_TO_AFFO_PERCENT_CALCULATED': f"{ffo_affo_reduction_pct:.1f}",
        'FFO_TO_AFFO_ADJUSTMENTS_CALCULATED': ffo_affo_top_adjustments,

        # AFFO → ACFO Bridge (uses calculated values from lines 950-962)
        'AFFO_TO_ACFO_ADJUSTMENT_CALCULATED': f"{affo_acfo_adjustment:,.0f}",
        'AFFO_TO_ACFO_PERCENT_CALCULATED': f"{affo_acfo_adjustment_pct:.1f}",
        'AFFO_TO_ACFO_ADJUSTMENTS_CALCULATED': affo_acfo_top_adjustments,

        # Legacy placeholders (kept for backward compatibility)
        'CFO_TO_ACFO_REDUCTION_CALCULATED': f"{affo_acfo_adjustment:,.0f}",
        'CFO_TO_ACFO_PERCENT_CALCULATED': f"{affo_acfo_adjustment_pct:.1f}",
        'CFO_TO_ACFO_ADJUSTMENTS_CALCULATED': affo_acfo_top_adjustments,

        # ========================================
        # Section 2.6.3: AFFO vs ACFO Gap Analysis
        # ========================================
        'BRIDGE_ANALYSIS_INTERPRETATION': gap_interpretation,
        'AFFO_ACFO_GAP_ANALYSIS': gap_interpretation,  # Template uses this name

        'AFFO_ACFO_GAP_REPORTED': f"{affo_acfo_gap_rep:,.0f}" if acfo_rep else 'N/A',
        'AFFO_ACFO_GAP_PERCENT_REPORTED': f"{affo_acfo_gap_pct_rep:.1f}" if acfo_rep else 'N/A',
        'AFFO_ACFO_GAP_CALCULATED': f"{affo_acfo_adjustment:,.0f}",
        'AFFO_ACFO_GAP_PERCENT_CALCULATED': f"{affo_acfo_adjustment_pct:.1f}",
        'AFFO_ACFO_GAP_VARIANCE': f"{(affo_acfo_adjustment - affo_acfo_gap_rep):,.0f}" if acfo_rep else 'Not available',

        # ========================================
        # Section 2.7: AFCF Analysis (Enhanced)
        # ========================================


        'AFCF_REPORTED_BASED': f"{afcf_rep_based:,.0f}" if afcf_rep_based else 'N/A - issuer does not report ACFO',
        'AFCF_PER_UNIT_REPORTED_BASED': f"{calculate_per_unit(afcf_rep_based, common_units):.4f}" if afcf_rep_based else 'N/A',
        'AFCF_DEBT_SERVICE_ASSESSMENT': assess_afcf_coverage(afcf_coverage.get('afcf_debt_service_coverage', 0)) if afcf_coverage.get('afcf_debt_service_coverage') else 'Not available',
        'AFCF_DISTRIBUTION_ASSESSMENT': assess_distribution_coverage(calculate_coverage_ratio(afcf_metrics.get('afcf', 0), distributions_total)),
        'AFCF_SELF_FUNDING_ASSESSMENT': assess_self_funding_capacity(afcf_coverage.get('afcf_self_funding_ratio', 0)) if afcf_coverage.get('afcf_self_funding_ratio') else 'Not available',

        'NOI_INTEREST_COVERAGE': f"{noi_coverage:.2f}",
        'ANNUALIZED_INTEREST': f"{annualized_interest:,.0f}",
        'QUARTERLY_INTEREST': f"{quarterly_interest:,.0f}",

        'OCCUPANCY': f"{occupancy:.1f}",
        'OCCUPANCY_WITH_COMMITMENTS': f"{occupancy_with_commitments:.1f}",
        'NOI_GROWTH': f"{noi_growth:.1f}",
        'PROPERTY_COUNT': str(property_count),
        'GLA': f"{gla:.1f}",

        # Assessments
        'LEVERAGE_LEVEL': leverage_level,
        'LEVERAGE_RATING_CATEGORY': leverage_rating,
        'LEVERAGE_THRESHOLD': leverage_threshold,
        'LEVERAGE_ASSESSMENT': f"{leverage_level.capitalize()} leverage ({leverage_rating} range)",

        'COVERAGE_LEVEL': coverage_level,
        'COVERAGE_RATING_CATEGORY': coverage_rating,
        'COVERAGE_THRESHOLD': coverage_threshold,
        'COVERAGE_ASSESSMENT': f"{coverage_level.capitalize()} coverage ({coverage_rating} range)",

        'FFO_PAYOUT_ASSESSMENT': ffo_assessment,
        'AFFO_PAYOUT_ASSESSMENT': affo_assessment,
        'FFO_ASSESSMENT': ffo_assessment,
        'AFFO_ASSESSMENT': affo_assessment,

        'OCCUPANCY_ASSESSMENT': occupancy_assessment,
        'OCCUPANCY_QUALITY_ASSESSMENT': occupancy_assessment,
        'NOI_GROWTH_ASSESSMENT': noi_growth_assessment,
        'GROWTH_ASSESSMENT': noi_growth_assessment,

        # Additional fields
        'PORTFOLIO_COMPOSITION': f"{property_count} properties totaling {gla:.1f} million square feet",
        'NOI': 'Not provided separately (incorporated in coverage metrics)',
        'DILUTED_UNITS': 'Not provided',
        'LIQUIDITY_ASSESSMENT': f"Based on available metrics, the issuer demonstrates {coverage_level} liquidity with {noi_coverage:.2f}x interest coverage. Detailed liquidity analysis requires review of debt maturity schedule and available credit facilities.",

        # Source references
        'LEVERAGE_METRICS_SOURCE': 'Calculated from Phase 2 extracted data',
        'REIT_METRICS_SOURCE': 'Calculated from Phase 2 extracted data',
        'COVERAGE_METRICS_SOURCE': 'Calculated from Phase 2 extracted data',
        'PORTFOLIO_METRICS_SOURCE': 'Extracted from financial statements in Phase 2',

        # Enhanced template sections
        'COMPANY_BACKGROUND': company_background,
        'BUSINESS_STRATEGY': business_strategy,
        'MANAGEMENT_GOVERNANCE': management_governance,
        'PEER_COMPARISON': peer_comparison,
        'EARNINGS_ANALYSIS': earnings_analysis,
        'LEVERAGE_COVERAGE_DETAIL': leverage_coverage_detail,
        'GROWTH_STRATEGY': growth_strategy,
        'OPERATING_TRACK_RECORD': operating_track_record,
        'ENVIRONMENTAL_ANALYSIS': environmental_analysis,
        'SOCIAL_ANALYSIS': social_analysis,
        'GOVERNANCE_ANALYSIS': governance_analysis,
        'SENSITIVITY_ANALYSIS': scenario_analysis,
        'DEBT_STRUCTURE': debt_structure,
        'COLLATERAL_ANALYSIS': collateral_analysis,
        'PERPETUAL_SECURITIES': perpetual_securities,
        'DEBT_RECONCILIATION': debt_reconciliation,
        'EBITDA_RECONCILIATION': ebitda_reconciliation,

        # Placeholder defaults for sections that may not be in Phase 4 analysis
        'RATING': 'Not available',
        'RATING_SOURCE': 'Analysis-derived',
        'RATING_DATE': reporting_date,
        'RATING_DISCLAIMER': 'This is a credit analysis report, not an official credit rating assignment.',
        'SCORECARD_RATING': 'Ba2 / Ba3 (analysis-derived)',
        'EXECUTIVE_SUMMARY_NARRATIVE': exec_summary,
        'DRIVER_1': drivers[0] if len(drivers) > 0 else 'See Executive Summary',
        'DRIVER_2': drivers[1] if len(drivers) > 1 else '',
        'DRIVER_3': drivers[2] if len(drivers) > 2 else '',
        'DRIVER_4': drivers[3] if len(drivers) > 3 else '',
        'OUTLOOK': outlook,  # Extracted from Phase 4 analysis (was hardcoded 'Stable')
        'OUTLOOK_RATIONALE': rating_outlook,
        'OUTLOOK_SCENARIOS': '',
        'STABILIZATION_CRITERIA': 'Not specified',
        'METHODOLOGY_DESCRIPTION': 'This analysis applies a 5-factor scorecard methodology consistent with Moody\'s, DBRS, and S&P rating frameworks for real estate companies.',
        'SCORECARD_CALCULATION': 'See scorecard table above',
        'ACTUAL_RATING': 'Not available',
        'VARIANCE_NARRATIVE': 'Not available',
        'ESG_SCORE': 'CIS-3 (Neutral-to-Low)',
        'E_SCORE': 'E-3',
        'S_SCORE': 'S-3',
        'G_SCORE': 'G-3',
        'E_CREDIT_IMPACT': 'Neutral',
        'S_CREDIT_IMPACT': 'Neutral',
        'G_CREDIT_IMPACT': 'Neutral',
        'ESG_OVERALL': 'ESG factors are assessed as having neutral-to-low credit impact.',

        # Scenario analysis placeholders (Issue #28 - parsed from Phase 4)
        'BASE_ASSUMPTIONS': parsed_scenarios.get('BASE_ASSUMPTIONS', 'Not available'),
        'BASE_METRICS': parsed_scenarios.get('BASE_METRICS', 'Not available'),
        'BASE_RATING_IMPACT': parsed_scenarios.get('BASE_RATING_IMPACT', 'Not available'),
        'BASE_LIKELIHOOD': parsed_scenarios.get('BASE_LIKELIHOOD', 'Not available'),
        'UPSIDE_ASSUMPTIONS': parsed_scenarios.get('UPSIDE_ASSUMPTIONS', 'Not available'),
        'UPSIDE_METRICS': parsed_scenarios.get('UPSIDE_METRICS', 'Not available'),
        'UPSIDE_RATING_IMPACT': parsed_scenarios.get('UPSIDE_RATING_IMPACT', 'Not available'),
        'UPSIDE_LIKELIHOOD': parsed_scenarios.get('UPSIDE_LIKELIHOOD', 'Not available'),
        'DOWNSIDE_ASSUMPTIONS': parsed_scenarios.get('DOWNSIDE_ASSUMPTIONS', 'Not available'),
        'DOWNSIDE_METRICS': parsed_scenarios.get('DOWNSIDE_METRICS', 'Not available'),
        'DOWNSIDE_RATING_IMPACT': parsed_scenarios.get('DOWNSIDE_RATING_IMPACT', 'Not available'),
        'DOWNSIDE_LIKELIHOOD': parsed_scenarios.get('DOWNSIDE_LIKELIHOOD', 'Not available'),
        'STRESS_ASSUMPTIONS': parsed_scenarios.get('STRESS_ASSUMPTIONS', 'Not available'),
        'STRESS_METRICS': parsed_scenarios.get('STRESS_METRICS', 'Not available'),
        'STRESS_RATING_IMPACT': parsed_scenarios.get('STRESS_RATING_IMPACT', 'Not available'),
        'STRESS_LIKELIHOOD': parsed_scenarios.get('STRESS_LIKELIHOOD', 'Not available'),
        'DOWNGRADE_TRIGGERS': parsed_scenarios.get('DOWNGRADE_TRIGGERS', 'Not available'),
        'DELEVERAGING_SCENARIOS': 'Not available',

        # AFCF Metrics (v1.0.6) - Section 2.7
        'ACFO': f"{acfo_metrics.get('acfo', 0):,.0f}" if acfo_metrics.get('acfo') else 'Not available',
        'ACFO_PER_UNIT': f"{acfo_metrics.get('acfo_per_unit', 0):.4f}" if acfo_metrics.get('acfo_per_unit') else 'Not available',
        'NET_CFI': f"{afcf_metrics.get('net_cfi', 0):,.0f}" if afcf_metrics.get('net_cfi') else 'Not available',
        'AFCF': f"{afcf_metrics.get('afcf', 0):,.0f}" if afcf_metrics.get('afcf') else 'Not available',
        'AFCF_PER_UNIT': f"{afcf_metrics.get('afcf_per_unit', 0):.4f}" if afcf_metrics.get('afcf_per_unit') else 'Not available',
        'AFCF_DEBT_SERVICE_COVERAGE': f"{afcf_coverage.get('afcf_debt_service_coverage', 0):.2f}" if afcf_coverage.get('afcf_debt_service_coverage') else 'Not available',
        'AFCF_PAYOUT_RATIO': f"{afcf_coverage.get('afcf_payout_ratio', 0):.1f}" if afcf_coverage.get('afcf_payout_ratio') else 'Not available',
        'AFCF_SELF_FUNDING_RATIO': f"{afcf_coverage.get('afcf_self_funding_ratio', 0):.2f}" if afcf_coverage.get('afcf_self_funding_ratio') else 'Not available',
        'AFCF_SELF_FUNDING_CAPACITY': f"{afcf_coverage.get('afcf_self_funding_capacity', 0):,.0f}" if afcf_coverage.get('afcf_self_funding_capacity') is not None else 'Not available',
        'AFCF_SURPLUS_SHORTFALL': f"({abs(afcf_coverage.get('afcf_self_funding_capacity', 0)):,.0f})" if afcf_coverage.get('afcf_self_funding_capacity') is not None and afcf_coverage.get('afcf_self_funding_capacity') < 0 else (f"{afcf_coverage.get('afcf_self_funding_capacity', 0):,.0f}" if afcf_coverage.get('afcf_self_funding_capacity') is not None else 'Not available'),
        'TOTAL_DEBT_SERVICE': f"{afcf_coverage.get('total_debt_service', 0):,.0f}" if afcf_coverage.get('total_debt_service') else 'Not available',
        'TOTAL_OBLIGATIONS': f"{afcf_coverage.get('total_debt_service', 0) + afcf_coverage.get('total_distributions', 0):,.0f}" if afcf_coverage.get('total_debt_service') and afcf_coverage.get('total_distributions') else 'Not available',
        'NET_FINANCING_NEEDS': f"{afcf_coverage.get('net_financing_needs', 0):,.0f}" if afcf_coverage.get('net_financing_needs') else 'Not available',
        'AFCF_COVERAGE_ASSESSMENT': assess_afcf_coverage(afcf_coverage.get('afcf_debt_service_coverage', 0)) if afcf_coverage.get('afcf_debt_service_coverage') else 'Not available',
        'SELF_FUNDING_ASSESSMENT': assess_self_funding_ratio(afcf_coverage.get('afcf_self_funding_ratio', 0)) if afcf_coverage.get('afcf_self_funding_ratio') else 'Not available',

        # AFCF Components (CFI breakdown)
        'DEV_CAPEX': f"{afcf_metrics.get('cfi_breakdown', {}).get('development_capex', {}).get('amount', 0):,.0f}" if afcf_metrics.get('cfi_breakdown') else 'Not available',
        'PROPERTY_ACQUISITIONS': f"{afcf_metrics.get('cfi_breakdown', {}).get('property_acquisitions', {}).get('amount', 0):,.0f}" if afcf_metrics.get('cfi_breakdown') else 'Not available',
        'PROPERTY_DISPOSITIONS': f"{afcf_metrics.get('cfi_breakdown', {}).get('property_dispositions', {}).get('amount', 0):,.0f}" if afcf_metrics.get('cfi_breakdown') else 'Not available',
        'JV_CONTRIBUTIONS': f"{afcf_metrics.get('cfi_breakdown', {}).get('jv_capital_contributions', {}).get('amount', 0):,.0f}" if afcf_metrics.get('cfi_breakdown') else 'Not available',
        'JV_DISTRIBUTIONS': f"{afcf_metrics.get('cfi_breakdown', {}).get('jv_return_of_capital', {}).get('amount', 0):,.0f}" if afcf_metrics.get('cfi_breakdown') else 'Not available',

        # Liquidity Position (v1.0.7) - Section 4.1
        'CASH_AND_EQUIVALENTS': f"{liquidity_position.get('cash_and_equivalents', 0):,.0f}" if liquidity_position.get('cash_and_equivalents') else 'Not available',
        'MARKETABLE_SECURITIES': f"{liquidity_position.get('marketable_securities', 0):,.0f}" if liquidity_position.get('marketable_securities') else 'Not available',
        'RESTRICTED_CASH': f"{liquidity_position.get('restricted_cash', 0):,.0f}" if liquidity_position.get('restricted_cash') else 'Not available',
        'AVAILABLE_CASH': f"{liquidity_position.get('available_cash', 0):,.0f}" if liquidity_position.get('available_cash') else 'Not available',
        'UNDRAWN_CREDIT_FACILITIES': f"{liquidity_position.get('undrawn_credit_facilities', 0):,.0f}" if liquidity_position.get('undrawn_credit_facilities') else 'Not available',
        'CREDIT_FACILITY_LIMIT': f"{liquidity_position.get('credit_facility_limit', 0):,.0f}" if liquidity_position.get('credit_facility_limit') else 'Not available',
        'TOTAL_AVAILABLE_LIQUIDITY': f"{liquidity_position.get('total_available_liquidity', 0):,.0f}" if liquidity_position.get('total_available_liquidity') else 'Not available',

        # Burn Rate Analysis (v1.0.7+) - Section 4.3
        'REPORTING_PERIOD': metrics.get('reporting_period', 'Unknown'),
        'REPORT_DATE': datetime.now().strftime('%Y-%m-%d'),  # Today's date in YYYY-MM-DD format
        'BURN_RATE_APPLICABLE': 'Yes' if burn_rate_analysis.get('applicable') else 'No',
        'MONTHLY_BURN_RATE': f"{burn_rate_analysis.get('monthly_burn_rate', 0):,.0f}" if burn_rate_analysis.get('monthly_burn_rate') else 'N/A',
        'MONTHLY_BURN_RATE_ABS': f"{abs(burn_rate_analysis.get('monthly_burn_rate', 0)):,.0f}" if burn_rate_analysis.get('monthly_burn_rate') else 'N/A',
        'BURN_MANDATORY_OBLIGATIONS': f"{burn_rate_analysis.get('mandatory_obligations', 0):,.0f}" if burn_rate_analysis.get('mandatory_obligations') else 'N/A',
        'BURN_PERIOD_DEFICIT': f"{burn_rate_analysis.get('period_burn_rate', 0):,.0f}" if burn_rate_analysis.get('period_burn_rate') else 'N/A',
        'BURN_PERIOD_MONTHS': str(burn_rate_analysis.get('period_months', 'N/A')) if burn_rate_analysis.get('period_months') else 'N/A',
        'ANNUALIZED_BURN_RATE': f"{burn_rate_analysis.get('annualized_burn_rate', 0):,.0f}" if burn_rate_analysis.get('annualized_burn_rate') else 'N/A',

        # Self-Funding & Burn Rate Interpretation
        'SELF_FUNDING_RATIO': f"{burn_rate_analysis.get('self_funding_ratio', 0):.2f}" if burn_rate_analysis.get('self_funding_ratio') else 'Not available',
        'SELF_FUNDING_INTERPRETATION': (
            'Strong self-funding capacity' if burn_rate_analysis.get('self_funding_ratio', 0) >= 1.0 else
            'Near self-sufficient' if burn_rate_analysis.get('self_funding_ratio', 0) >= 0.8 else
            'Moderate capital markets reliance' if burn_rate_analysis.get('self_funding_ratio', 0) >= 0.5 else
            'High capital markets reliance'
        ) if burn_rate_analysis.get('self_funding_ratio') else 'Not calculated without AFCF',
        'CAPITAL_MARKETS_RELIANCE': (
            'No external financing required' if burn_rate_analysis.get('self_funding_ratio', 0) >= 1.0 else
            f'Requires ${(burn_rate_analysis.get("mandatory_obligations", 0) - burn_rate_analysis.get("afcf", 0)):,.0f} external financing ({(1 - burn_rate_analysis.get("self_funding_ratio", 0)) * 100:.0f}% of obligations)'
        ) if burn_rate_analysis.get('self_funding_ratio') and burn_rate_analysis.get('applicable') else 'Unable to assess without AFCF self-funding ratio',
        'BURN_RATE_INTERPRETATION': (
            f"AFCF of ${burn_rate_analysis.get('afcf', 0):,.0f} covers {burn_rate_analysis.get('self_funding_ratio', 0):.0%} of mandatory obligations (${burn_rate_analysis.get('mandatory_obligations', 0):,.0f}). "
            f"Monthly cash deficit of ${abs(burn_rate_analysis.get('monthly_burn_rate', 0)):,.0f} must be funded through capital markets or asset sales."
        ) if burn_rate_analysis.get('applicable') else 'AFCF sufficient to cover all mandatory obligations - no burn rate',
        'BURN_RATE_CREDIT_IMPLICATIONS': (
            '🚨 Critical - High dependence on capital markets and undrawn credit facilities' if burn_rate_analysis.get('self_funding_ratio', 0) < 0.5 else
            '⚠️ Moderate - Partial reliance on capital markets for financing obligations' if burn_rate_analysis.get('self_funding_ratio', 0) < 0.8 else
            '✓ Adequate - Near self-sufficient with minimal capital markets reliance' if burn_rate_analysis.get('self_funding_ratio', 0) < 1.0 else
            '✓ Strong - Fully self-funded from operating and investing cash flows'
        ) if burn_rate_analysis.get('self_funding_ratio') else 'Not assessed without AFCF data',
        'BURN_STATUS': sustainable_burn.get('status', 'Not calculated') if sustainable_burn.get('status') else 'Not calculated',

        # Liquidity Position Details
        'END_PERIOD_CASH': f"{liquidity_position.get('cash_and_equivalents', 0):,.0f}" if liquidity_position.get('cash_and_equivalents') else 'Not available',
        'MARKETABLE_SECURITIES': f"{liquidity_position.get('marketable_securities', 0):,.0f}" if liquidity_position.get('marketable_securities') is not None else '0',
        'RESTRICTED_CASH': f"{liquidity_position.get('restricted_cash', 0):,.0f}" if liquidity_position.get('restricted_cash') is not None else '0',

        # Cash Runway Details
        'CASH_RUNWAY_MONTHS': f"{cash_runway.get('runway_months', 0):.1f}" if cash_runway.get('runway_months') else 'N/A',
        'CASH_RUNWAY_YEARS': f"{cash_runway.get('runway_years', 0):.1f}" if cash_runway.get('runway_years') else 'N/A',
        'CASH_DEPLETION_DATE': cash_runway.get('depletion_date', 'N/A') if cash_runway.get('depletion_date') else 'N/A',
        'EXTENDED_RUNWAY_MONTHS': f"{cash_runway.get('extended_runway_months', 0):.1f}" if cash_runway.get('extended_runway_months') else 'N/A',
        'EXTENDED_RUNWAY_YEARS': f"{cash_runway.get('extended_runway_years', 0):.1f}" if cash_runway.get('extended_runway_years') else 'N/A',
        'EXTENDED_DEPLETION_DATE': cash_runway.get('extended_depletion_date', 'N/A') if cash_runway.get('extended_depletion_date') else 'N/A',

        # Risk Assessment
        'LIQUIDITY_RISK_LEVEL': liquidity_risk.get('risk_level', 'N/A') if liquidity_risk.get('risk_level') else 'N/A',
        'LIQUIDITY_RISK_SCORE': str(liquidity_risk.get('risk_score', 'N/A')) if liquidity_risk.get('risk_score') else 'N/A',
        'LIQUIDITY_RISK_ASSESSMENT': assess_liquidity_risk(liquidity_risk.get('risk_level', '')) if liquidity_risk.get('risk_level') else 'Not available',
        'RUNWAY_RISK': liquidity_risk.get('risk_level', 'N/A') if liquidity_risk.get('risk_level') else 'N/A',
        'EXTENDED_RISK': liquidity_risk.get('risk_level', 'N/A') if liquidity_risk.get('risk_level') else 'N/A',  # Same as runway risk for extended

        # Sustainable Burn Analysis
        'SUSTAINABLE_MONTHLY_BURN': f"{sustainable_burn.get('sustainable_monthly_burn', 0):,.0f}" if sustainable_burn.get('sustainable_monthly_burn') else 'N/A',
        'EXCESS_BURN': f"{sustainable_burn.get('excess_burn_per_month', 0):,.0f}" if sustainable_burn.get('excess_burn_per_month') else 'N/A',
        'BURN_SUSTAINABILITY_STATUS': sustainable_burn.get('status', 'Not available') if sustainable_burn.get('status') else 'Not available',
        'BURN_SUSTAINABILITY_ASSESSMENT': assess_burn_rate_sustainability(sustainable_burn.get('status', '')) if sustainable_burn.get('status') else 'Not available',
        'WARNING_FLAGS': ', '.join(liquidity_risk.get('warning_flags', [])) if liquidity_risk.get('warning_flags') else 'None',
        'LIQUIDITY_RECOMMENDATIONS': '\n'.join([f"- {rec}" for rec in liquidity_risk.get('recommendations', [])]) if liquidity_risk.get('recommendations') else 'Monitor liquidity position quarterly',

        # Reconciliation Tables (v1.0.13) - Dual-table support
        'FFO_AFFO_RECONCILIATION_TABLE_REPORTED': ffo_affo_table_reported,  # NEW - Issuer-reported
        'FFO_AFFO_RECONCILIATION_TABLE_CALCULATED': ffo_affo_table,         # NEW - REALPAC calculated
        'FFO_AFFO_RECONCILIATION_TABLE': ffo_affo_table,                    # Backward compat
        'FFO_AFFO_RECONCILIATION_TABLE_DETAILED': ffo_affo_table,           # For Appendix F

        'ACFO_RECONCILIATION_TABLE_REPORTED': acfo_table_reported,          # NEW - Issuer-reported
        'ACFO_RECONCILIATION_TABLE_CALCULATED': acfo_table,                 # NEW - REALPAC calculated
        'ACFO_RECONCILIATION_TABLE': acfo_table,                            # Backward compat
        'ACFO_RECONCILIATION_TABLE_DETAILED': acfo_table,                   # For Appendix F
        'AFFO_VALIDATION_SUMMARY': affo_validation_summary,
        'ACFO_VALIDATION_SUMMARY': acfo_validation_summary,
        'AFCF_CFI_BREAKDOWN_TABLE': cfi_breakdown_table,
        'AFCF_RECONCILIATION_TABLE': afcf_recon_table,

        # Additional Payout Ratios (v1.0.11)
        'ACFO_PAYOUT': f"{(distributions / acfo_metrics.get('acfo_per_unit', 1) * 100):.1f}" if acfo_metrics.get('acfo_per_unit', 0) > 0 else 'Not available',
        'AFCF_PAYOUT': f"{afcf_coverage.get('afcf_payout_ratio', 0):.1f}" if afcf_coverage.get('afcf_payout_ratio') else 'Not available',

        # Dilution Analysis (v1.0.8) - Optional
        'DILUTION_AVAILABLE': 'Yes' if dilution_analysis.get('has_dilution_detail') else 'No',
        'DILUTION_PERCENTAGE': f"{dilution_analysis.get('dilution_percentage', 0):.2f}" if dilution_analysis.get('dilution_percentage') else 'Not available',
        'DILUTION_MATERIALITY': dilution_analysis.get('dilution_materiality', 'Not assessed').upper() if dilution_analysis.get('dilution_materiality') else 'Not available',
        'MATERIAL_INSTRUMENTS': ', '.join([item.get('instrument', str(item)) if isinstance(item, dict) else str(item) for item in dilution_analysis.get('material_instruments', [])]) if dilution_analysis.get('material_instruments') else 'None',
        'CONVERTIBLE_DEBT_RISK': dilution_analysis.get('convertible_debt_risk', 'Not assessed').upper() if dilution_analysis.get('convertible_debt_risk') else 'Not available',
        'GOVERNANCE_SCORE': dilution_analysis.get('governance_score', 'Not assessed').capitalize() if dilution_analysis.get('governance_score') else 'Not available',
        'DILUTION_CREDIT_ASSESSMENT': dilution_analysis.get('credit_assessment', 'Dilution analysis not available') if dilution_analysis.get('credit_assessment') else 'Not available',
        'BASIC_UNITS': f"{dilution_analysis.get('detail', {}).get('basic_units', 0):,.0f}" if dilution_analysis.get('detail', {}).get('basic_units') else 'Not available',
        'DILUTED_UNITS_TOTAL': f"{dilution_analysis.get('detail', {}).get('diluted_units_reported', 0):,.0f}" if dilution_analysis.get('detail', {}).get('diluted_units_reported') else 'Not available',
        'DILUTION_ANALYSIS': dilution_analysis.get('credit_assessment', 'Dilution detail not extracted in Phase 2. Enable comprehensive extraction for detailed dilution analysis.') if dilution_analysis else 'Dilution detail not extracted in Phase 2.',

        # FFO/AFFO Validation Placeholders (duplicate FFO_REPORTED removed - Issue #33)
        'FFO_CALCULATED': f"{reit_metrics.get('ffo_calculated', 0):,.0f}",
        'FFO_VARIANCE_AMOUNT': f"{reit_metrics.get('validation', {}).get('ffo_variance_amount', 0):,.0f}" if reit_metrics.get('validation', {}).get('ffo_variance_amount') is not None else 'N/A',
        'FFO_VARIANCE_PERCENT': f"{reit_metrics.get('validation', {}).get('ffo_variance_percent', 0):.1f}" if reit_metrics.get('validation', {}).get('ffo_variance_percent') is not None else 'N/A',
        'FFO_VALIDATION_STATUS': '✓ Within threshold' if reit_metrics.get('validation', {}).get('ffo_within_threshold') else '⚠️ Exceeds threshold - review methodology',
        'FFO_VALIDATION_SUMMARY': reit_metrics.get('validation', {}).get('validation_summary', 'Validation not available'),
        'AFFO_REPORTED_STATUS': f"Issuer reported AFFO: {reit_metrics.get('affo', 0):,.0f} (${reit_metrics.get('affo_per_unit', 0):.2f}/unit)" if reit_metrics.get('affo') else 'AFFO not reported by issuer',
        'AFFO_STATUS': f"Calculated AFFO: {reit_metrics.get('affo_calculated', 0):,.0f} vs. Reported: {'Not reported' if not reit_metrics.get('affo') else f'{reit_metrics.get('affo', 0):,.0f}'}",
        'FFO_ADJUSTMENTS_AVAILABLE': str(reit_metrics.get('ffo_calculation_detail', {}).get('available_adjustments', 0)),
        'AFFO_ADJUSTMENTS_AVAILABLE': str(reit_metrics.get('affo_calculation_detail', {}).get('available_adjustments', 0)),
        'FFO_AFFO_DATA_QUALITY': reit_metrics.get('ffo_calculation_detail', {}).get('data_quality', 'Unknown').upper(),
        'FFO_AFFO_OBSERVATIONS': f"FFO variance: {ffo_var_formatted}. AFFO variance: {affo_var_formatted}.",

        # Distribution Coverage Placeholders (Per-Unit Basis)
        'FFO_COVERAGE': f"{(1 / (ffo_payout / 100) if ffo_payout > 0 else 0):.2f}",
        'AFFO_COVERAGE': f"{(1 / (affo_payout / 100) if affo_payout > 0 else 0):.2f}",
        'ACFO_COVERAGE': f"{acfo_cov_calc:.2f}x" if acfo_cov_calc else 'Not available',  # Per-unit
        'AFCF_COVERAGE': f"{afcf_cov_calc:.2f}" if afcf_cov_calc else 'Not available',  # Per-unit
        'FFO_COVERAGE_ASSESSMENT': 'Adequate' if ffo_payout < 90 else 'Tight coverage',
        'AFFO_COVERAGE_ASSESSMENT': 'Unsustainable' if affo_payout > 100 else 'Adequate',
        'ACFO_COVERAGE_ASSESSMENT': assess_distribution_coverage(acfo_cov_calc) if acfo_cov_calc else 'Not available',
        'AFCF_COVERAGE_ASSESSMENT': assess_distribution_coverage(afcf_cov_calc) if afcf_cov_calc else 'Not available',
        'DISTRIBUTION_COVERAGE_ANALYSIS': f"FFO coverage: {(1 / (ffo_payout / 100) if ffo_payout > 0 else 0):.2f}x. AFFO coverage: {(1 / (affo_payout / 100) if affo_payout > 0 else 0):.2f}x. AFFO payout ratio of {affo_payout:.1f}% indicates distributions exceed sustainable cash flow.",
        'DISTRIBUTION_SUSTAINABILITY': 'Unsustainable' if affo_payout > 100 else 'Sustainable',
        'DISTRIBUTION_SUSTAINABILITY_CONCLUSION': f"Distributions {'exceed' if affo_payout > 100 else 'within'} sustainable cash flow (AFFO payout: {affo_payout:.1f}%)",
        'DISTRIBUTION_COVERAGE_OVERALL': 'mixed' if ffo_payout < 100 and affo_payout > 100 else 'adequate',

        # Total-Level Coverage Metrics (Issue #33 - Option 3)
        'ACFO_DIST_COV_TOTAL': f"{acfo_dist_cov_total:.2f}x" if acfo_dist_cov_total else 'Not available',
        'ACFO_DIST_COV_TOTAL_ASSESSMENT': assess_distribution_coverage(acfo_dist_cov_total) if acfo_dist_cov_total else 'Not available',
        'AFCF_DIST_COV_TOTAL': f"{afcf_dist_cov_total:.2f}x" if afcf_dist_cov_total else 'Not available',
        'AFCF_DIST_COV_TOTAL_ASSESSMENT': assess_distribution_coverage(afcf_dist_cov_total) if afcf_dist_cov_total else 'Not available',
        'AFCF_DEBT_SERVICE_COV': f"{afcf_debt_service_cov:.2f}x" if afcf_debt_service_cov else 'Not available',
        'AFCF_SELF_FUNDING_RATIO': f"{afcf_self_funding:.2f}x" if afcf_self_funding else 'Not available',
        'TOTAL_DEBT_SERVICE': f"{total_debt_service:,.0f}" if total_debt_service else 'Not available',
        'TOTAL_DISTRIBUTIONS_YTD': f"{total_distributions_ytd:,.0f}" if total_distributions_ytd else 'Not available',
        'AFCF_SELF_FUNDING_CAPACITY': f"{afcf_self_funding_capacity:,.0f}" if afcf_self_funding_capacity else 'Not available',
        'ACFO_PER_UNIT_CALC': f"{acfo_per_unit_calc:.4f}" if acfo_per_unit_calc else 'Not available',
        'AFCF_PER_UNIT_CALC': f"{afcf_per_unit_calc:.4f}" if afcf_per_unit_calc else 'Not available',
        'DISTRIBUTIONS_PER_UNIT': f"{distributions:.4f}" if distributions else 'Not available',

        # Bridge Analysis Placeholders
        'FFO_TO_AFFO_REDUCTION': f"{(ffo - affo):,.0f}",
        'FFO_TO_AFFO_PERCENT': f"{((ffo - affo) / ffo * 100 if ffo != 0 else 0):.1f}",
        'FFO_TO_AFFO_ADJUSTMENTS': f"Sustaining CAPEX, leasing costs, tenant improvements totaling ${(ffo - affo):,.0f}k",
        'CFO_TO_ACFO_REDUCTION': 'Not available - requires cash flow statement',
        'CFO_TO_ACFO_PERCENT': 'Not available',
        'CFO_TO_ACFO_ADJUSTMENTS': 'Not available - requires ACFO components extraction',
        'CFO_ACFO_REDUCTION_ASSESSMENT': 'Not calculated',
        'FFO_AFFO_REDUCTION_ASSESSMENT': f"{'High' if ffo != 0 and (ffo - affo) / ffo > 0.3 else 'Moderate' if ffo != 0 else 'Not available'} reduction from FFO to AFFO" if ffo != 0 else 'Not available - FFO not reported',
        'AFFO_ACFO_GAP': 'Not available',
        'AFFO_ACFO_GAP_PERCENT': 'Not available',
        # 'AFFO_ACFO_GAP_ANALYSIS' is set earlier at line 1315 with calculated value - don't override here
        'AFFO_ACFO_GAP_INTERPRETATION': 'Gap analysis unavailable without ACFO',

        # ACFO Placeholders
        'ACFO': f"{acfo_metrics.get('acfo', 0):,.0f}" if acfo_metrics.get('acfo') else 'Not available',
        'ACFO_PER_UNIT': f"{calculate_per_unit(acfo_metrics.get('acfo', 0), common_units) or 0:.4f}" if acfo_metrics.get('acfo') else 'Not available',
        'ACFO_SOURCE': acfo_metrics.get('data_source', 'not calculated'),
        'ACFO_PERIOD': report_period,
        'ACFO_CALCULATED': f"{acfo_metrics.get('acfo', 0):,.0f}" if acfo_metrics.get('acfo') else 'Not available',
        'ACFO_REPORTED': f"{acfo_rep:,.0f}" if acfo_rep else 'Not available',
        'ACFO_VARIANCE_AMOUNT': f"{(acfo_metrics.get('acfo', 0) - acfo_rep):,.0f}" if acfo_metrics.get('acfo') and acfo_rep else 'Not available',
        'ACFO_VARIANCE_PERCENT': f"{((acfo_metrics.get('acfo', 0) - acfo_rep) / acfo_rep * 100):.1f}" if acfo_metrics.get('acfo') and acfo_rep and acfo_rep != 0 else 'N/A',
        'ACFO_VALIDATION_STATUS': '✓ ACFO calculated successfully' if acfo_metrics.get('acfo') else 'Not calculated - requires cash flow statement',
        'ACFO_DATA_QUALITY': acfo_metrics.get('data_quality', 'Not available').capitalize() if acfo_metrics.get('acfo') else 'Not available',
        'ACFO_CALCULATION_METHOD': acfo_metrics.get('calculation_method', 'Not calculated') if acfo_metrics.get('acfo') else 'Not calculated',
        'ACFO_JV_TREATMENT': acfo_metrics.get('jv_treatment_method', 'Not applicable') if acfo_metrics.get('acfo') else 'Not applicable',
        'ACFO_ADJUSTMENTS_AVAILABLE': str(len([k for k, v in acfo_metrics.get('acfo_calculation_detail', {}).get('adjustments', {}).items() if v != 0])) if acfo_metrics.get('acfo') else '0',
        'ACFO_OBSERVATIONS': f"ACFO calculated: {acfo_metrics.get('acfo', 0):,.0f}" if acfo_metrics.get('acfo') else 'ACFO not calculated. Requires cash_flow_from_operations in Phase 2 extraction.',
        'ACFO_CONSISTENCY_CHECKS': 'Performed - see reconciliation section' if acfo_metrics.get('acfo') else 'Not performed - ACFO not calculated',
        'ACFO_PAYOUT_ASSESSMENT': assess_distribution_coverage(acfo_cov_calc) if acfo_cov_calc else 'Not available',
        'CAPEX_CONSISTENCY_STATUS': '✅ Consistent' if acfo_metrics.get('acfo_reconciliation', {}).get('capex_consistent') else 'Not verified',
        'TI_CONSISTENCY_STATUS': '✅ Consistent' if acfo_metrics.get('acfo_reconciliation', {}).get('ti_consistent') else 'Not verified',
        'LEASING_CONSISTENCY_STATUS': '✅ Consistent' if acfo_metrics.get('acfo_reconciliation', {}).get('leasing_consistent') else 'Not verified',

        # AFCF Placeholders (unique ones - duplicates removed, Issue #33)
        'AFCF_ANNUALIZED': 'Not available',
        'AFCF_PERIOD': report_period,
        'AFCF_DATA_SOURCE': 'calculated' if afcf_metrics.get('afcf') else 'not calculated',
        'AFCF_DATA_QUALITY': afcf_metrics.get('data_quality', 'Not available') if afcf_metrics.get('afcf') else 'Not available',
        'AFCF_KEY_OBSERVATIONS': f"AFCF of ${afcf_metrics.get('afcf', 0):,.0f} represents free cash flow after all investing activities" if afcf_metrics.get('afcf') else 'AFCF not calculated - requires ACFO as starting point',
        'AFCF_CREDIT_ASSESSMENT': f"AFCF debt service coverage of {afcf_coverage.get('afcf_debt_service_coverage', 0):.2f}x indicates {assess_afcf_coverage(afcf_coverage.get('afcf_debt_service_coverage', 0)).lower()}" if afcf_coverage.get('afcf_debt_service_coverage') else 'Not available without AFCF calculation',
        'AFCF_VALIDATION_NOTES': f"AFCF calculated from ACFO (${acfo_metrics.get('acfo', 0):,.0f}) + Net CFI (${afcf_metrics.get('net_cfi', 0):,.0f})" if afcf_metrics.get('afcf') else 'AFCF calculation requires ACFO (CFO + adjustments)',
        'AFCF_PAYOUT_ASSESSMENT': assess_distribution_coverage(afcf_cov_calc) if afcf_cov_calc else 'Not calculated - requires AFCF',
        'AFCF_DS_ASSESSMENT': assess_afcf_coverage(afcf_coverage.get('afcf_debt_service_coverage', 0)) if afcf_coverage.get('afcf_debt_service_coverage') is not None else 'Not calculated',
        'AFCF_SF_ASSESSMENT': assess_self_funding_ratio(afcf_coverage.get('afcf_self_funding_ratio', 0)) if afcf_coverage.get('afcf_self_funding_ratio') is not None else 'Not calculated',
        'AFCF_DISTRIBUTION_COVERAGE': f"{afcf_coverage.get('afcf_distribution_coverage', 0):.2f}" if afcf_coverage.get('afcf_distribution_coverage') else 'Not available',

        # Cash Flow & Debt Service Placeholders
        'CASH_FLOW_FROM_OPERATIONS': f"{reit_metrics.get('acfo_calculation_detail', {}).get('cash_flow_from_operations', 0):,.0f}" if reit_metrics.get('acfo_calculation_detail', {}).get('cash_flow_from_operations') else 'Not extracted',
        'TOTAL_DEBT_SERVICE': f"{afcf_coverage.get('total_debt_service', 0):,.0f}" if afcf_coverage.get('total_debt_service') else 'Not available',
        'DEBT_SERVICE_ANNUALIZED': f"{afcf_coverage.get('total_debt_service', 0):,.0f}" if afcf_coverage.get('total_debt_service') else 'Not available',
        'DEBT_SERVICE_PERIOD': f"{coverage_ratios.get('detected_period', 'unknown').replace('_', ' ').title()}",
        'PRINCIPAL_REPAYMENTS': f"{abs(phase2_data.get('cash_flow_financing', {}).get('debt_principal_repayments', 0)):,.0f}" if phase2_data and phase2_data.get('cash_flow_financing') else 'Not available',
        'NEW_FINANCING': f"{phase2_data.get('cash_flow_financing', {}).get('new_debt_issuances', 0):,.0f}" if phase2_data and phase2_data.get('cash_flow_financing') else 'Not available',
        'FINANCING_ANNUALIZED': 'Not available',
        'FINANCING_PERIOD': report_period,
        'NET_FINANCING_ANNUALIZED': 'Not available',
        'DISTRIBUTIONS_TOTAL': f"{afcf_coverage.get('total_distributions', 0):,.0f}" if afcf_coverage.get('total_distributions') else 'Not available',
        'DIST_ANNUALIZED': f"{abs(phase2_data.get('cash_flow_financing', {}).get('distributions_common', 0)) * coverage_ratios.get('annualization_factor', 2):,.0f}" if phase2_data and phase2_data.get('cash_flow_financing') else 'Not available',
        'DIST_PERIOD': report_period,

        # Liquidity Placeholders (from Phase 2)
        'CASH_SOURCE': phase2_data.get('liquidity', {}).get('data_source', 'Not available') if phase2_data else 'Not available',
        'TOTAL_LIQUIDITY': f"{phase2_data.get('liquidity', {}).get('total_available_liquidity', 0):,.0f}" if phase2_data and phase2_data.get('liquidity') else 'Not available',
        'UNDRAWN_FACILITIES': f"{phase2_data.get('liquidity', {}).get('undrawn_credit_facilities', 0):,.0f}" if phase2_data and phase2_data.get('liquidity') else 'Not available',
        'FACILITY_LIMIT': f"{phase2_data.get('liquidity', {}).get('credit_facility_limit', 0):,.0f}" if phase2_data and phase2_data.get('liquidity') else 'Not available',
        'LIQUIDITY_DATA_SOURCE': phase2_data.get('liquidity', {}).get('data_source', 'Not available') if phase2_data else 'Not available',
        'LIQUIDITY_WARNING_FLAGS': 'None identified' if phase2_data and phase2_data.get('liquidity', {}).get('total_available_liquidity', 0) > 50000 else 'Monitor liquidity position',

        # Target runway for sustainable burn analysis
        'TARGET_RUNWAY_MONTHS': '24',

        # Additional placeholders
        'SELF_FUNDING_PERCENT': 'Not available',
        'RESIDUAL_ACFO': f"{residual_acfo:,.0f}" if residual_acfo is not None else 'Not available',
        'RESIDUAL_AFCF': f"{residual_afcf:,.0f}" if residual_afcf is not None else 'Not available',

        # Additional Financial Data Placeholders
        # NET_INCOME: Priority Phase 3 (calculated) → Phase 2 (extracted) → 0
        'NET_INCOME': f"{reit_metrics.get('ffo_calculation_detail', {}).get('net_income_ifrs') or (phase2_data.get('income_statement', {}).get('net_income') if phase2_data else None) or 0:,.0f}",
        'NET_INCOME_PER_UNIT_CALCULATED': f"{calculate_per_unit(reit_metrics.get('ffo_calculation_detail', {}).get('net_income_ifrs') or (phase2_data.get('income_statement', {}).get('net_income') if phase2_data else 0), common_units) or 0:.4f}",
        'SUSTAINING_CAPEX': f"{abs(reit_metrics.get('affo_calculation_detail', {}).get('adjustments_detail', {}).get('adjustment_V_capex_sustaining', 0)):,.0f}",

        # Assessment & Analysis Placeholders
        'COVERAGE_ANALYSIS': f"NOI/Interest coverage of {noi_coverage:.2f}x is {'below' if noi_coverage < 2.0 else 'at or above'} typical REIT minimum (2.0x)",
        'CAPEX_ANALYSIS_TABLE': 'CAPEX breakdown not available - requires detailed Phase 2 extraction',
        'CAPEX_INSIGHTS': 'Sustaining CAPEX analysis unavailable',
        'DEBT_MATURITIES_SUMMARY': 'Debt maturity schedule not extracted',

        # Covenant & Monitoring Placeholders
        'FFO_AFFO_ACFO_AFCF_SOURCE': reit_metrics.get('source', 'Unknown'),
        'FFO_AFFO_ACFO_RATING_IMPLICATIONS': f"AFFO payout ratio of {affo_payout:.1f}% {'negative' if affo_payout > 100 else 'neutral'} for credit rating",
        'FFO_AFFO_ACFO_MONITORING': 'Monitor AFFO payout ratio and distribution sustainability quarterly',
        'FFO_AFFO_ACFO_COVENANT_PERFORMANCE': 'Covenant compliance analysis requires detailed debt documentation',
        'PEER_FFO_AFFO_ACFO_AFCF_COMPARISON': 'Peer comparison not available in this analysis',

        # ========== Issue #40: Market Risk Placeholders (26) ==========
        # Fixed: Corrected data paths to match enrich_phase4_data.py output structure
        'MARKET_CURRENT_PRICE': f"{market_risk.get('price_stress', {}).get('current_price', 0):.2f}" if market_risk else 'N/A',
        'MARKET_52W_HIGH': f"{market_risk.get('price_stress', {}).get('high_52w', 0):.2f}" if market_risk else 'N/A',
        'MARKET_52W_LOW': f"{market_risk.get('price_stress', {}).get('low_52w', 0):.2f}" if market_risk else 'N/A',
        'MARKET_DECLINE_FROM_PEAK': f"{market_risk.get('price_stress', {}).get('decline_from_peak_pct', 0):.1f}" if market_risk else 'N/A',  # Fixed: decline_from_peak_pct not decline_pct
        'MARKET_DAYS_SINCE_PEAK': f"{market_risk.get('price_stress', {}).get('days_since_peak', 0):.0f}" if market_risk else 'N/A',
        'MARKET_STRESS_LEVEL': market_risk.get('price_stress', {}).get('stress_level', 'N/A') if market_risk else 'N/A',
        'MARKET_VOLATILITY_30D': f"{market_risk.get('volatility', {}).get('metrics', {}).get('30d', {}).get('volatility_annualized_pct', 0):.1f}" if market_risk else 'N/A',  # Fixed: 30d not 30_day, volatility_annualized_pct
        'MARKET_VOLATILITY_90D': f"{market_risk.get('volatility', {}).get('metrics', {}).get('90d', {}).get('volatility_annualized_pct', 0):.1f}" if market_risk else 'N/A',  # Fixed: 90d not 90_day
        'MARKET_VOLATILITY_252D': f"{market_risk.get('volatility', {}).get('metrics', {}).get('252d', {}).get('volatility_annualized_pct', 0):.1f}" if market_risk else 'N/A',  # Fixed: 252d not 252_day
        'MARKET_VOL_30D_CLASS': market_risk.get('volatility', {}).get('metrics', {}).get('30d', {}).get('classification', 'N/A') if market_risk else 'N/A',  # Fixed: 30d
        'MARKET_VOL_90D_CLASS': market_risk.get('volatility', {}).get('metrics', {}).get('90d', {}).get('classification', 'N/A') if market_risk else 'N/A',  # Fixed: 90d
        'MARKET_VOL_252D_CLASS': market_risk.get('volatility', {}).get('metrics', {}).get('252d', {}).get('classification', 'N/A') if market_risk else 'N/A',  # Fixed: 252d
        'MARKET_VOL_CLASSIFICATION': market_risk.get('volatility', {}).get('classification', 'N/A') if market_risk else 'N/A',  # Fixed: removed 'overall_classification' level
        'MARKET_MOMENTUM_3M': f"{market_risk.get('momentum', {}).get('metrics', {}).get('3_month', {}).get('total_return_pct', 0):.1f}" if market_risk else 'N/A',
        'MARKET_MOMENTUM_6M': f"{market_risk.get('momentum', {}).get('metrics', {}).get('6_month', {}).get('total_return_pct', 0):.1f}" if market_risk else 'N/A',
        'MARKET_MOMENTUM_12M': f"{market_risk.get('momentum', {}).get('metrics', {}).get('12_month', {}).get('total_return_pct', 0):.1f}" if market_risk else 'N/A',
        'MARKET_MOMENTUM_TREND': market_risk.get('momentum', {}).get('trend', 'N/A') if market_risk else 'N/A',
        'MARKET_VOLUME_TREND': market_risk.get('volume', {}).get('trend', 'N/A') if market_risk else 'N/A',
        'MARKET_PRICE_STRESS_SCORE': f"{market_risk.get('risk_score', {}).get('components', {}).get('stress_points', 0):.0f}" if market_risk else 'N/A',  # Fixed: risk_score.components.stress_points
        'MARKET_VOLATILITY_SCORE': f"{market_risk.get('risk_score', {}).get('components', {}).get('volatility_points', 0):.0f}" if market_risk else 'N/A',  # Fixed: components.volatility_points
        'MARKET_MOMENTUM_SCORE': f"{market_risk.get('risk_score', {}).get('components', {}).get('momentum_points', 0):.0f}" if market_risk else 'N/A',  # Fixed: components.momentum_points
        'MARKET_VOLUME_SCORE': f"{market_risk.get('risk_score', {}).get('components', {}).get('volume_points', 0):.0f}" if market_risk else 'N/A',  # Fixed: components.volume_points
        'MARKET_RISK_SCORE': f"{market_risk.get('risk_score', {}).get('total_score', 0):.0f}" if market_risk else 'N/A',
        'MARKET_RISK_LEVEL': market_risk.get('risk_score', {}).get('risk_level', 'N/A') if market_risk else 'N/A',
        'MARKET_RISK_NARRATIVE': market_risk.get('overall_assessment', 'Market risk assessment unavailable') if market_risk else 'Market risk assessment unavailable',
        'MARKET_CREDIT_IMPLICATIONS': market_risk.get('credit_implications', 'Credit implications analysis unavailable') if market_risk else 'Credit implications analysis unavailable',

        # ========== Issue #40: Macro Environment Placeholders (13) ==========
        # Fixed: Added missing 'policy_rate' nesting level for Canada and US rates
        'MACRO_CA_RATE': f"{macro_environment.get('canada', {}).get('policy_rate', {}).get('current_rate', 0):.2f}" if macro_environment else 'N/A',
        'MACRO_CA_CHANGE_BPS': f"{macro_environment.get('canada', {}).get('policy_rate', {}).get('change_12m_bps', 0):.0f}" if macro_environment else 'N/A',
        'MACRO_CA_CYCLE': macro_environment.get('canada', {}).get('policy_rate', {}).get('cycle', 'N/A') if macro_environment else 'N/A',
        'MACRO_CA_PEAK_RATE': f"{macro_environment.get('canada', {}).get('policy_rate', {}).get('max_rate', 0):.2f}" if macro_environment else 'N/A',
        'MACRO_CA_CREDIT_ENVIRONMENT': macro_environment.get('canada', {}).get('credit_environment', 'N/A') if macro_environment else 'N/A',  # Fixed: under canada not top level
        'MACRO_CA_STRESS_SCORE': f"{macro_environment.get('canada', {}).get('credit_stress_score', 0):.0f}" if macro_environment else 'N/A',  # Fixed: under canada not top level
        'MACRO_US_RATE': f"{macro_environment.get('united_states', {}).get('policy_rate', {}).get('current_rate', 0):.2f}" if macro_environment and macro_environment.get('united_states') else 'N/A',
        'MACRO_US_CHANGE_BPS': f"{macro_environment.get('united_states', {}).get('policy_rate', {}).get('change_12m_bps', 0):.0f}" if macro_environment and macro_environment.get('united_states') else 'N/A',
        'MACRO_US_CYCLE': macro_environment.get('united_states', {}).get('policy_rate', {}).get('cycle', 'N/A') if macro_environment and macro_environment.get('united_states') else 'N/A',
        'MACRO_SPREAD_BPS': f"{macro_environment.get('rate_differential', {}).get('ca_minus_us_bps', 0):.0f}" if macro_environment and macro_environment.get('rate_differential') else 'N/A',  # Fixed: rate_differential.ca_minus_us_bps
        'MACRO_SPREAD_TREND': 'N/A',  # Note: spread_trend not in enriched data structure - would need to be added to enrich_phase4_data.py
        'MACRO_RATE_NARRATIVE': macro_environment.get('overall_assessment', 'Macro environment assessment unavailable') if macro_environment else 'Macro environment assessment unavailable',
        'MACRO_CREDIT_IMPLICATIONS': macro_environment.get('credit_implications', 'Credit implications analysis unavailable') if macro_environment else 'Credit implications analysis unavailable',

        # ========== Issue #40: Distribution Cut Prediction Placeholders (32) ==========
        'PRED_CUT_PROBABILITY': f"{distribution_prediction.get('cut_probability_pct', 0):.1f}" if distribution_prediction else 'N/A',
        'PRED_RISK_LEVEL': distribution_prediction.get('risk_level', 'N/A') if distribution_prediction else 'N/A',
        'PRED_RISK_BADGE': distribution_prediction.get('risk_badge', '❓') if distribution_prediction else '❓',
        'PRED_CONFIDENCE': distribution_prediction.get('confidence', 'N/A') if distribution_prediction else 'N/A',
        'PRED_DATE': distribution_prediction.get('prediction_date', 'N/A') if distribution_prediction else 'N/A',
        # Top 5 risk drivers
        'PRED_DRIVER_1_NAME': distribution_prediction.get('top_drivers', [{}])[0].get('feature', 'N/A') if distribution_prediction and distribution_prediction.get('top_drivers') else 'N/A',
        'PRED_DRIVER_1_VALUE': f"{distribution_prediction.get('top_drivers', [{}])[0].get('value', 0):.4f}" if distribution_prediction and distribution_prediction.get('top_drivers') else 'N/A',
        'PRED_DRIVER_1_DIRECTION': distribution_prediction.get('top_drivers', [{}])[0].get('direction', 'N/A') if distribution_prediction and distribution_prediction.get('top_drivers') else 'N/A',
        'PRED_DRIVER_1_COEF': f"{distribution_prediction.get('top_drivers', [{}])[0].get('coefficient', 0):.4f}" if distribution_prediction and distribution_prediction.get('top_drivers') else 'N/A',
        'PRED_DRIVER_2_NAME': distribution_prediction.get('top_drivers', [{}, {}])[1].get('feature', 'N/A') if distribution_prediction and len(distribution_prediction.get('top_drivers', [])) > 1 else 'N/A',
        'PRED_DRIVER_2_VALUE': f"{distribution_prediction.get('top_drivers', [{}, {}])[1].get('value', 0):.4f}" if distribution_prediction and len(distribution_prediction.get('top_drivers', [])) > 1 else 'N/A',
        'PRED_DRIVER_2_DIRECTION': distribution_prediction.get('top_drivers', [{}, {}])[1].get('direction', 'N/A') if distribution_prediction and len(distribution_prediction.get('top_drivers', [])) > 1 else 'N/A',
        'PRED_DRIVER_2_COEF': f"{distribution_prediction.get('top_drivers', [{}, {}])[1].get('coefficient', 0):.4f}" if distribution_prediction and len(distribution_prediction.get('top_drivers', [])) > 1 else 'N/A',
        'PRED_DRIVER_3_NAME': distribution_prediction.get('top_drivers', [{}, {}, {}])[2].get('feature', 'N/A') if distribution_prediction and len(distribution_prediction.get('top_drivers', [])) > 2 else 'N/A',
        'PRED_DRIVER_3_VALUE': f"{distribution_prediction.get('top_drivers', [{}, {}, {}])[2].get('value', 0):.4f}" if distribution_prediction and len(distribution_prediction.get('top_drivers', [])) > 2 else 'N/A',
        'PRED_DRIVER_3_DIRECTION': distribution_prediction.get('top_drivers', [{}, {}, {}])[2].get('direction', 'N/A') if distribution_prediction and len(distribution_prediction.get('top_drivers', [])) > 2 else 'N/A',
        'PRED_DRIVER_3_COEF': f"{distribution_prediction.get('top_drivers', [{}, {}, {}])[2].get('coefficient', 0):.4f}" if distribution_prediction and len(distribution_prediction.get('top_drivers', [])) > 2 else 'N/A',
        'PRED_DRIVER_4_NAME': distribution_prediction.get('top_drivers', [{}, {}, {}, {}])[3].get('feature', 'N/A') if distribution_prediction and len(distribution_prediction.get('top_drivers', [])) > 3 else 'N/A',
        'PRED_DRIVER_4_VALUE': f"{distribution_prediction.get('top_drivers', [{}, {}, {}, {}])[3].get('value', 0):.4f}" if distribution_prediction and len(distribution_prediction.get('top_drivers', [])) > 3 else 'N/A',
        'PRED_DRIVER_4_DIRECTION': distribution_prediction.get('top_drivers', [{}, {}, {}, {}])[3].get('direction', 'N/A') if distribution_prediction and len(distribution_prediction.get('top_drivers', [])) > 3 else 'N/A',
        'PRED_DRIVER_4_COEF': f"{distribution_prediction.get('top_drivers', [{}, {}, {}, {}])[3].get('coefficient', 0):.4f}" if distribution_prediction and len(distribution_prediction.get('top_drivers', [])) > 3 else 'N/A',
        'PRED_DRIVER_5_NAME': distribution_prediction.get('top_drivers', [{}, {}, {}, {}, {}])[4].get('feature', 'N/A') if distribution_prediction and len(distribution_prediction.get('top_drivers', [])) > 4 else 'N/A',
        'PRED_DRIVER_5_VALUE': f"{distribution_prediction.get('top_drivers', [{}, {}, {}, {}, {}])[4].get('value', 0):.4f}" if distribution_prediction and len(distribution_prediction.get('top_drivers', [])) > 4 else 'N/A',
        'PRED_DRIVER_5_DIRECTION': distribution_prediction.get('top_drivers', [{}, {}, {}, {}, {}])[4].get('direction', 'N/A') if distribution_prediction and len(distribution_prediction.get('top_drivers', [])) > 4 else 'N/A',
        'PRED_DRIVER_5_COEF': f"{distribution_prediction.get('top_drivers', [{}, {}, {}, {}, {}])[4].get('coefficient', 0):.4f}" if distribution_prediction and len(distribution_prediction.get('top_drivers', [])) > 4 else 'N/A',
        # Model narrative and implications
        'PRED_NARRATIVE': distribution_prediction.get('narrative', 'Prediction narrative unavailable') if distribution_prediction else 'Prediction narrative unavailable',
        'PRED_CREDIT_IMPLICATIONS': distribution_prediction.get('credit_implications', 'Credit implications unavailable') if distribution_prediction else 'Credit implications unavailable',

        # ========== Issue #40: Distribution History Placeholders (12) ==========
        'DIST_CURRENT_MONTHLY': f"{distribution_history.get('current_monthly', 0):.4f}" if distribution_history else 'N/A',
        'DIST_CURRENT_ANNUAL': f"{distribution_history.get('current_annual', 0):.4f}" if distribution_history else 'N/A',
        'DIST_CURRENT_YIELD': f"{distribution_history.get('current_yield', 0):.2f}" if distribution_history and distribution_history.get('current_yield') else 'N/A',
        'DIST_CUT_COUNT': f"{distribution_history.get('cuts_detected', 0)}" if distribution_history else 'N/A',
        'DIST_LATEST_CUT_DATE': distribution_history.get('latest_cut_date', 'N/A') if distribution_history and distribution_history.get('latest_cut_date') else 'N/A',
        'DIST_LATEST_CUT_MAGNITUDE': f"{distribution_history.get('latest_cut_magnitude_pct', 0):.1f}" if distribution_history and distribution_history.get('latest_cut_magnitude_pct') else 'N/A',
        'DIST_RECOVERY_STATUS': distribution_history.get('recovery_status', 'N/A') if distribution_history else 'N/A',
        'DIST_RECOVERY_LEVEL': f"{distribution_history.get('recovery_level_pct', 0):.1f}" if distribution_history and distribution_history.get('recovery_level_pct') else 'N/A',
        'DIST_RECOVERY_NARRATIVE': distribution_history.get('recovery_narrative', 'Recovery analysis unavailable') if distribution_history else 'Recovery analysis unavailable',
        'DIST_STABILITY_ASSESSMENT': f"{'Stable' if distribution_history.get('cuts_detected', 0) == 0 else 'Cut history requires monitoring'}" if distribution_history else 'N/A',
        'DIST_MGMT_ASSESSMENT': f"{'Consistent distribution policy' if distribution_history.get('cuts_detected', 0) == 0 else 'Distribution cut history indicates financial stress'}" if distribution_history else 'N/A',
        'DIST_SUSTAINABILITY_OUTLOOK': f"{'Positive' if distribution_history.get('cuts_detected', 0) == 0 else 'Monitor closely'}" if distribution_history else 'N/A',

        # Generation metadata
        'GENERATION_TIMESTAMP': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    # Replace all placeholders
    report = template
    for key, value in replacements.items():
        report = report.replace(f"{{{{{key}}}}}", str(value))

    return report


def main():
    """Main execution - command-line interface"""
    import argparse
    import pytz

    parser = argparse.ArgumentParser(
        description='Phase 5: Generate final credit opinion report',
        epilog='Example: python generate_final_report.py metrics.json analysis.md'
    )
    parser.add_argument(
        'metrics_json',
        help='Path to Phase 3 calculated metrics JSON (REQUIRED)'
    )
    parser.add_argument(
        'analysis_md',
        help='Path to Phase 4 credit analysis markdown (REQUIRED)'
    )
    parser.add_argument(
        '--output',
        default=None,
        help='Output path for final report (default: auto-generated with ET timestamp)'
    )
    parser.add_argument(
        '--template',
        default='credit_opinion_template.md',
        help='Template filename (default: credit_opinion_template.md)'
    )

    args = parser.parse_args()

    # Generate Eastern Time timestamp for default filename
    eastern = pytz.timezone('America/New_York')
    et_now = datetime.now(eastern)
    timestamp = et_now.strftime('%Y-%m-%d_%H%M%S')

    use_auto_filename = args.output is None

    print("=" * 70)
    print("PHASE 5: FINAL REPORT GENERATION")
    print("=" * 70)

    try:
        # Load inputs
        metrics = load_metrics(args.metrics_json)

        # Auto-detect and load Phase 2 extraction data (for reconciliation tables)
        metrics_path = Path(args.metrics_json).resolve()
        phase2_path = None
        phase2_data = None

        # Try to find phase2_extracted_data.json in the same temp/ folder
        if 'temp' in metrics_path.parts:
            temp_folder = metrics_path.parent
            potential_phase2 = temp_folder / 'phase2_extracted_data.json'
            if potential_phase2.exists():
                phase2_path = potential_phase2
                try:
                    with open(phase2_path, 'r') as f:
                        phase2_data = json.load(f)
                    print(f"✓ Phase 2 extraction data loaded: {phase2_path}")
                except Exception as e:
                    print(f"⚠️  Phase 2 data found but couldn't load: {e}")

        # If output path is auto-generated, create in issuer's reports/ folder
        if use_auto_filename:
            issuer_name = metrics.get('issuer_name', 'Unknown_Issuer')
            # Clean issuer name for filename (remove spaces, special chars)
            import re
            clean_name = issuer_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
            # Keep only alphanumeric, underscore, hyphen
            clean_name = re.sub(r'[^a-zA-Z0-9_-]', '', clean_name)

            # Infer issuer folder from metrics path (e.g., ./Issuer_Reports/{issuer}/temp/...)
            metrics_path = Path(args.metrics_json).resolve()  # Convert to absolute path
            # Navigate up from temp/ to issuer folder
            if 'temp' in metrics_path.parts:
                temp_index = metrics_path.parts.index('temp')
                issuer_folder = Path(*metrics_path.parts[:temp_index])
                reports_folder = issuer_folder / 'reports'
            else:
                # Fallback: create in Issuer_Reports/{clean_name}/reports/ (absolute path)
                cwd = Path.cwd()
                reports_folder = cwd / 'Issuer_Reports' / clean_name / 'reports'

            # Create reports folder
            reports_folder.mkdir(parents=True, exist_ok=True)

            args.output = str(reports_folder / f'{timestamp}_Credit_Opinion_{clean_name}.md')

        analysis_sections = load_analysis(args.analysis_md)

        # Load template
        print(f"\n📋 Loading template: {args.template}")
        template = load_template(args.template)
        print(f"✓ Template loaded ({len(template)} characters)")

        # Generate report
        print("\n⚙️  Assembling final report...")
        report = generate_final_report(metrics, analysis_sections, template, phase2_data)

        # Save report
        output_path = Path(args.output)
        with open(output_path, 'w') as f:
            f.write(report)

        print(f"\n✅ Success! Final report generated")
        print(f"\n📄 Output: {output_path}")
        print(f"📊 Report length: {len(report):,} characters")
        print(f"💰 Token usage: 0 tokens (pure templating)")

        print("\n" + "=" * 70)
        print("FINAL REPORT SUMMARY")
        print("=" * 70)
        print(f"Issuer: {metrics.get('issuer_name')}")
        print(f"Period: {metrics.get('reporting_period')}")
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)

        sys.exit(0)

    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

    except json.JSONDecodeError as e:
        print(f"\n❌ Error: Invalid JSON in metrics file: {e}")
        sys.exit(1)

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
