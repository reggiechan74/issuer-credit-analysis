"""
Cash burn rate and liquidity runway analysis

Functions for assessing liquidity risk when AFCF cannot cover financing obligations.
Per v1.0.7+ methodology.
"""


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




__all__ = [
    'calculate_burn_rate',
    'calculate_cash_runway',
    'assess_liquidity_risk',
    'calculate_sustainable_burn_rate'
]
