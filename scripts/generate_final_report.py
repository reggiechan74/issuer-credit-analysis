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


def load_metrics(metrics_path):
    """
    Load Phase 3 calculated metrics

    Args:
        metrics_path: Path to Phase 3 metrics JSON

    Returns:
        dict: Metrics data

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
        metrics = json.load(f)

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


def generate_final_report(metrics, analysis_sections, template):
    """
    Generate final report by combining metrics and analysis with template

    Args:
        metrics: Phase 3 metrics dictionary
        analysis_sections: Phase 4 analysis sections
        template: Report template string

    Returns:
        str: Complete report
    """

    # Extract metrics
    issuer_name = metrics.get('issuer_name', 'Unknown Issuer')
    reporting_date = metrics.get('reporting_date', 'Unknown')
    report_period = metrics.get('report_period', 'Unknown')
    currency = metrics.get('currency', 'CAD')

    leverage_metrics = metrics.get('leverage_metrics', {})
    reit_metrics = metrics.get('reit_metrics', {})
    coverage_ratios = metrics.get('coverage_ratios', {})
    portfolio_metrics = metrics.get('portfolio_metrics', {})

    # Extract specific values
    total_debt = leverage_metrics.get('total_debt', 0)
    net_debt = leverage_metrics.get('net_debt', 0)
    gross_assets = leverage_metrics.get('gross_assets', 0)
    debt_to_assets = leverage_metrics.get('debt_to_assets_percent', 0)
    net_debt_ratio = leverage_metrics.get('net_debt_ratio', 0)

    ffo = reit_metrics.get('ffo', 0)
    affo = reit_metrics.get('affo', 0)
    ffo_per_unit = reit_metrics.get('ffo_per_unit', 0)
    affo_per_unit = reit_metrics.get('affo_per_unit', 0)
    distributions = reit_metrics.get('distributions_per_unit', 0)
    ffo_payout = reit_metrics.get('ffo_payout_ratio', 0)
    affo_payout = reit_metrics.get('affo_payout_ratio', 0)

    noi_coverage = coverage_ratios.get('noi_interest_coverage', 0)
    annualized_interest = coverage_ratios.get('annualized_interest_expense', 0)
    quarterly_interest = coverage_ratios.get('quarterly_interest_expense', 0)

    occupancy = portfolio_metrics.get('occupancy_rate', 0)
    occupancy_with_commitments = portfolio_metrics.get('occupancy_including_commitments', 0)
    noi_growth = portfolio_metrics.get('same_property_noi_growth', 0)
    property_count = portfolio_metrics.get('total_properties', 0)
    gla = portfolio_metrics.get('gla_sf', 0) / 1_000_000  # Convert to millions

    # Generate assessments
    leverage_level, leverage_rating, leverage_threshold = assess_leverage(debt_to_assets)
    coverage_level, coverage_rating, coverage_threshold = assess_coverage(noi_coverage)
    ffo_assessment = assess_payout_ratio(ffo_payout, "FFO")
    affo_assessment = assess_payout_ratio(affo_payout, "AFFO")
    occupancy_assessment = assess_occupancy(occupancy)
    noi_growth_assessment = assess_noi_growth(noi_growth)

    # Extract Phase 4 sections (with flexible lookup for variations)
    def get_section(sections, *possible_names):
        """Try multiple section name variations"""
        for name in possible_names:
            if name in sections:
                return sections[name]
            # Try partial match (e.g., "Rating Outlook: NEGATIVE" matches "Rating Outlook")
            for key in sections:
                if key.startswith(name):
                    return sections[key]
        return 'Not available'

    exec_summary = get_section(analysis_sections, 'Executive Summary')
    credit_strengths = get_section(analysis_sections, 'Credit Strengths')
    credit_challenges = get_section(analysis_sections, 'Credit Challenges')
    rating_outlook = get_section(analysis_sections, 'Rating Outlook')
    upgrade_factors = get_section(analysis_sections, 'Upgrade Factors')
    downgrade_factors = get_section(analysis_sections, 'Downgrade Factors')
    scorecard_table = get_section(analysis_sections, 'Five-Factor Rating Scorecard Analysis', '5-Factor Rating Scorecard', 'Five-Factor Scorecard', 'Five-Factor Rating Scorecard')
    key_observations = get_section(analysis_sections, 'Key Observations')

    # Build replacements dictionary
    replacements = {
        'ISSUER_NAME': issuer_name,
        'REPORT_DATE': datetime.now().strftime('%B %d, %Y'),
        'REPORT_PERIOD': report_period,
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

        # If output path is auto-generated, create in issuer's reports/ folder
        if use_auto_filename:
            issuer_name = metrics.get('issuer_name', 'Unknown_Issuer')
            # Clean issuer name for filename (remove spaces, special chars)
            import re
            clean_name = issuer_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
            # Keep only alphanumeric, underscore, hyphen
            clean_name = re.sub(r'[^a-zA-Z0-9_-]', '', clean_name)

            # Infer issuer folder from metrics path (e.g., ./Issuer_Reports/{issuer}/temp/...)
            metrics_path = Path(args.metrics_json)
            # Navigate up from temp/ to issuer folder
            if 'temp' in metrics_path.parts:
                temp_index = metrics_path.parts.index('temp')
                issuer_folder = Path(*metrics_path.parts[:temp_index])
                reports_folder = issuer_folder / 'reports'
            else:
                # Fallback: create in Issuer_Reports/{clean_name}/reports/
                reports_folder = Path(f'./Issuer_Reports/{clean_name}/reports')

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
        report = generate_final_report(metrics, analysis_sections, template)

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
        print(f"Period: {metrics.get('report_period')}")
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
