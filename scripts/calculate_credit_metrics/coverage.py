"""
Coverage ratio calculations

Functions for calculating debt service coverage and interest coverage ratios.
"""

from .validation import validate_required_fields


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

    # REIT Quarterly Pattern: Q1=3mo, Q2=6mo, Q3=9mo, Q4=12mo
    if 'q2' in reporting_period or ' q2' in reporting_period:
        # Q2 = 6 months ending (YTD)
        annualization_factor = 2
        period_label = 'semi_annual_q2'
    elif 'q3' in reporting_period or ' q3' in reporting_period:
        # Q3 = 9 months ending (YTD)
        annualization_factor = 12/9  # 1.33
        period_label = 'nine_months_q3'
    elif 'q4' in reporting_period or ' q4' in reporting_period or 'q4' in reporting_period:
        # Q4 = 12 months ending (annual)
        annualization_factor = 1
        period_label = 'annual_q4'
    elif 'q1' in reporting_period or ' q1' in reporting_period:
        # Q1 = 3 months ending
        annualization_factor = 4
        period_label = 'quarterly_q1'
    elif 'six months' in reporting_period or '6 months' in reporting_period or 'six-month' in reporting_period:
        # 6-month period: multiply by 2 to annualize
        annualization_factor = 2
        period_label = 'semi_annual'
    elif 'nine months' in reporting_period or '9 months' in reporting_period or 'nine-month' in reporting_period:
        # 9-month period: multiply by 12/9 to annualize
        annualization_factor = 12/9
        period_label = 'nine_months'
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


__all__ = ['calculate_coverage_ratios']
