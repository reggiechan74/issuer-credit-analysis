"""
Leverage metrics calculations for real estate issuers

Functions for calculating debt-to-assets, net debt, and leverage ratios
"""

from .validation import validate_required_fields


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
