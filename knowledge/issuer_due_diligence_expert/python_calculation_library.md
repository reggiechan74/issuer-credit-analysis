# Python Calculation Library for Issuer Due Diligence

## Overview

This document specifies all Python scripts required to calculate financial metrics for real estate issuer due diligence reports. All calculations must be performed explicitly using Python to ensure transparency, reproducibility, and auditability.

**Required Libraries:**
- `pandas`: Data manipulation and analysis
- `numpy`: Numerical calculations
- `datetime`: Date handling for maturity profiles
- `typing`: Type hints for code clarity

---

## I. Core Financial Metrics Calculations

### 1. EBITDA Calculations

```python
import pandas as pd
import numpy as np
from typing import Dict, Union

def calculate_ebitda_base(
    net_income: float,
    interest_expense: float,
    tax_expense: float,
    depreciation: float,
    amortization: float
) -> float:
    """
    Calculate base EBITDA from financial statement components.

    EBITDA = Net Income + Interest + Taxes + Depreciation + Amortization

    Parameters:
    -----------
    net_income : float
        Net income from income statement
    interest_expense : float
        Interest expense (positive number)
    tax_expense : float
        Tax expense (positive number)
    depreciation : float
        Depreciation expense
    amortization : float
        Amortization expense

    Returns:
    --------
    float : Calculated EBITDA
    """
    ebitda = (net_income +
              interest_expense +
              tax_expense +
              depreciation +
              amortization)

    return ebitda


def calculate_adjusted_ebitda(
    base_ebitda: float,
    adjustments: Dict[str, float]
) -> Dict[str, Union[float, pd.DataFrame]]:
    """
    Calculate Moody's-adjusted EBITDA with detailed reconciliation.

    Common adjustments:
    - Add back: Non-cash charges, restructuring costs, asset impairments
    - Subtract: Gains on asset sales, non-recurring income
    - Adjust for: JV proportionate share, straight-line rent differences

    Parameters:
    -----------
    base_ebitda : float
        As-reported EBITDA
    adjustments : Dict[str, float]
        Dictionary of adjustment items and amounts (positive = add back)

    Returns:
    --------
    Dict containing:
        - 'adjusted_ebitda': float
        - 'reconciliation': pd.DataFrame with adjustment details
    """
    adjustment_df = pd.DataFrame(
        list(adjustments.items()),
        columns=['Adjustment', 'Amount']
    )

    total_adjustments = sum(adjustments.values())
    adjusted_ebitda = base_ebitda + total_adjustments

    # Create reconciliation table
    reconciliation = pd.DataFrame({
        'Item': ['As Reported EBITDA'] + list(adjustments.keys()) + ['Adjusted EBITDA'],
        'Amount': [base_ebitda] + list(adjustments.values()) + [adjusted_ebitda]
    })

    return {
        'adjusted_ebitda': adjusted_ebitda,
        'reconciliation': reconciliation
    }
```

### 2. REIT-Specific Metrics

```python
def calculate_ffo(
    net_income: float,
    depreciation_real_estate: float,
    amortization_real_estate: float,
    gains_on_property_sales: float
) -> float:
    """
    Calculate Funds From Operations (FFO) per NAREIT definition.

    FFO = Net Income
          - Gains on Property Sales
          + Depreciation (Real Estate)
          + Amortization (Real Estate)

    Parameters:
    -----------
    net_income : float
        Net income attributable to common shareholders
    depreciation_real_estate : float
        Depreciation on real estate assets
    amortization_real_estate : float
        Amortization related to real estate
    gains_on_property_sales : float
        Gains from sale of properties (positive number)

    Returns:
    --------
    float : FFO
    """
    ffo = (net_income
           - gains_on_property_sales
           + depreciation_real_estate
           + amortization_real_estate)

    return ffo


def calculate_affo(
    ffo: float,
    recurring_capex: float,
    straight_line_rent_adjustment: float = 0,
    other_non_cash_adjustments: float = 0
) -> float:
    """
    Calculate Adjusted Funds From Operations (AFFO).

    AFFO = FFO
           - Recurring Capital Expenditures
           - Straight-line Rent Adjustments
           - Other Non-cash Items

    Parameters:
    -----------
    ffo : float
        Funds From Operations
    recurring_capex : float
        Recurring/maintenance capital expenditures (positive number)
    straight_line_rent_adjustment : float
        Difference between straight-line rent and cash rent
    other_non_cash_adjustments : float
        Other non-cash revenue items to back out

    Returns:
    --------
    float : AFFO
    """
    affo = (ffo
            - recurring_capex
            - straight_line_rent_adjustment
            - other_non_cash_adjustments)

    return affo


def calculate_nav_per_share(
    property_values: float,
    cash: float,
    receivables: float,
    total_debt: float,
    other_liabilities: float,
    preferred_stock: float,
    diluted_shares: float
) -> Dict[str, float]:
    """
    Calculate Net Asset Value per share.

    NAV = Property Values + Cash + Receivables
          - Debt - Other Liabilities - Preferred Stock
    NAV per Share = NAV / Diluted Shares

    Parameters:
    -----------
    property_values : float
        Market value of all properties (estimated via cap rate or appraisals)
    cash : float
        Cash and equivalents
    receivables : float
        Accounts receivable (net)
    total_debt : float
        Total debt (including pro rata JV debt)
    other_liabilities : float
        Other liabilities
    preferred_stock : float
        Preferred equity (if treated as liability)
    diluted_shares : float
        Fully diluted share count

    Returns:
    --------
    Dict with 'nav' (total) and 'nav_per_share'
    """
    nav_total = (property_values
                 + cash
                 + receivables
                 - total_debt
                 - other_liabilities
                 - preferred_stock)

    nav_per_share = nav_total / diluted_shares

    return {
        'nav': nav_total,
        'nav_per_share': nav_per_share
    }


def calculate_payout_ratio(
    annual_dividends: float,
    ffo: float = None,
    affo: float = None
) -> Dict[str, float]:
    """
    Calculate dividend payout ratios.

    Parameters:
    -----------
    annual_dividends : float
        Total annual dividends declared
    ffo : float, optional
        Funds From Operations
    affo : float, optional
        Adjusted Funds From Operations

    Returns:
    --------
    Dict with payout ratios vs FFO and AFFO
    """
    result = {}

    if ffo is not None:
        result['payout_ratio_ffo'] = annual_dividends / ffo

    if affo is not None:
        result['payout_ratio_affo'] = annual_dividends / affo

    return result
```

### 3. Leverage Ratios

```python
def calculate_debt_to_assets(
    total_debt: float,
    gross_assets: float,
    jv_debt_pro_rata: float = 0,
    perpetual_securities: float = 0,
    perpetual_equity_treatment: float = 0.5
) -> float:
    """
    Calculate Debt / Gross Assets ratio with Moody's adjustments.

    Adjusted Debt = Reported Debt
                   + JV Debt (Pro Rata Share)
                   + Perpetual Securities × (1 - Equity Treatment %)

    Parameters:
    -----------
    total_debt : float
        Reported total debt
    gross_assets : float
        Total book value of assets
    jv_debt_pro_rata : float
        Pro rata share of JV debt to include
    perpetual_securities : float
        Perpetual/hybrid securities outstanding
    perpetual_equity_treatment : float
        % treated as equity (0.5 = 50% equity, 50% debt). Default 0.5

    Returns:
    --------
    float : Debt / Gross Assets ratio
    """
    adjusted_debt = (total_debt
                     + jv_debt_pro_rata
                     + perpetual_securities * (1 - perpetual_equity_treatment))

    ratio = adjusted_debt / gross_assets

    return ratio


def calculate_net_debt_to_ebitda(
    total_debt: float,
    cash: float,
    ebitda: float,
    jv_debt_pro_rata: float = 0,
    jv_ebitda_pro_rata: float = 0,
    perpetual_securities: float = 0,
    perpetual_equity_treatment: float = 0.5
) -> float:
    """
    Calculate Net Debt / EBITDA ratio with Moody's adjustments.

    Net Debt = Total Debt + JV Debt (Pro Rata)
               + Perpetual Securities × (1 - Equity Treatment %)
               - Cash

    EBITDA = Adjusted EBITDA + JV EBITDA (Pro Rata)

    Parameters:
    -----------
    total_debt : float
        Reported total debt
    cash : float
        Cash and equivalents
    ebitda : float
        Adjusted EBITDA
    jv_debt_pro_rata : float
        Pro rata share of JV debt
    jv_ebitda_pro_rata : float
        Pro rata share of JV EBITDA
    perpetual_securities : float
        Perpetual/hybrid securities
    perpetual_equity_treatment : float
        % treated as equity (default 0.5)

    Returns:
    --------
    float : Net Debt / EBITDA ratio
    """
    adjusted_debt = (total_debt
                     + jv_debt_pro_rata
                     + perpetual_securities * (1 - perpetual_equity_treatment))

    net_debt = adjusted_debt - cash

    adjusted_ebitda = ebitda + jv_ebitda_pro_rata

    ratio = net_debt / adjusted_ebitda

    return ratio


def calculate_interest_coverage(
    ebitda: float,
    interest_expense: float,
    jv_ebitda_pro_rata: float = 0,
    jv_interest_pro_rata: float = 0,
    perpetual_distributions: float = 0,
    perpetual_equity_treatment: float = 0.5
) -> float:
    """
    Calculate EBITDA / Interest Expense coverage ratio with Moody's adjustments.

    EBITDA = Adjusted EBITDA + JV EBITDA (Pro Rata)

    Interest = Interest Expense
               + JV Interest (Pro Rata)
               + Perpetual Distributions × (1 - Equity Treatment %)

    Parameters:
    -----------
    ebitda : float
        Adjusted EBITDA
    interest_expense : float
        Interest expense
    jv_ebitda_pro_rata : float
        Pro rata JV EBITDA
    jv_interest_pro_rata : float
        Pro rata JV interest
    perpetual_distributions : float
        Distributions on perpetual securities
    perpetual_equity_treatment : float
        % treated as equity (default 0.5)

    Returns:
    --------
    float : Interest coverage ratio
    """
    adjusted_ebitda = ebitda + jv_ebitda_pro_rata

    adjusted_interest = (interest_expense
                         + jv_interest_pro_rata
                         + perpetual_distributions * (1 - perpetual_equity_treatment))

    coverage = adjusted_ebitda / adjusted_interest

    return coverage


def calculate_dscr(
    noi: float,
    interest: float,
    principal: float
) -> float:
    """
    Calculate Debt Service Coverage Ratio.

    DSCR = NOI / (Interest + Principal Payments)

    Parameters:
    -----------
    noi : float
        Net Operating Income
    interest : float
        Annual interest payments
    principal : float
        Annual principal payments

    Returns:
    --------
    float : DSCR
    """
    debt_service = interest + principal

    if debt_service == 0:
        return np.inf

    dscr = noi / debt_service

    return dscr
```

### 4. Operating Metrics

```python
def calculate_occupancy_rate(
    occupied_sqft: float,
    total_leasable_sqft: float
) -> float:
    """
    Calculate portfolio occupancy rate.

    Occupancy % = (Occupied SF / Total Leasable SF) × 100%

    Parameters:
    -----------
    occupied_sqft : float
        Occupied/leased square footage
    total_leasable_sqft : float
        Total leasable square footage

    Returns:
    --------
    float : Occupancy rate as percentage (0-100)
    """
    if total_leasable_sqft == 0:
        return 0.0

    occupancy = (occupied_sqft / total_leasable_sqft) * 100

    return occupancy


def calculate_wale(
    lease_data: pd.DataFrame,
    weight_by: str = 'rent'
) -> float:
    """
    Calculate Weighted Average Lease Expiry (WALE).

    WALE = Σ(Remaining Lease Term × Weight) / Σ(Weight)

    where Weight = Annual Rent (or Leasable Area)

    Parameters:
    -----------
    lease_data : pd.DataFrame
        DataFrame with columns:
        - 'remaining_term_years': Remaining lease term in years
        - 'annual_rent': Annual rent for each lease (if weight_by='rent')
        - 'leasable_area': Leasable area (if weight_by='area')
    weight_by : str
        'rent' or 'area' - determines weighting method

    Returns:
    --------
    float : WALE in years
    """
    if weight_by == 'rent':
        weight_col = 'annual_rent'
    elif weight_by == 'area':
        weight_col = 'leasable_area'
    else:
        raise ValueError("weight_by must be 'rent' or 'area'")

    lease_data['weighted_term'] = (lease_data['remaining_term_years'] *
                                   lease_data[weight_col])

    wale = lease_data['weighted_term'].sum() / lease_data[weight_col].sum()

    return wale


def calculate_rental_reversion(
    new_rent: float,
    expiring_rent: float
) -> float:
    """
    Calculate rental reversion percentage.

    Reversion % = (New Rent - Expiring Rent) / Expiring Rent × 100%

    Parameters:
    -----------
    new_rent : float
        New/renewal rent
    expiring_rent : float
        Expiring/previous rent

    Returns:
    --------
    float : Rental reversion as percentage
    """
    if expiring_rent == 0:
        return np.nan

    reversion = ((new_rent - expiring_rent) / expiring_rent) * 100

    return reversion


def calculate_same_store_noi_growth(
    current_period_noi: float,
    prior_period_noi: float
) -> float:
    """
    Calculate same-store NOI growth rate.

    Same-Store Growth % = (Current NOI - Prior NOI) / Prior NOI × 100%

    Note: Should only include properties owned in both periods

    Parameters:
    -----------
    current_period_noi : float
        Current period same-store NOI
    prior_period_noi : float
        Prior period same-store NOI

    Returns:
    --------
    float : Growth rate as percentage
    """
    if prior_period_noi == 0:
        return np.nan

    growth = ((current_period_noi - prior_period_noi) / prior_period_noi) * 100

    return growth
```

### 5. Developer-Specific Metrics

```python
def calculate_development_yield(
    stabilized_noi: float,
    total_development_cost: float
) -> float:
    """
    Calculate development yield (yield on cost).

    Development Yield = Stabilized NOI / Total Development Cost

    Parameters:
    -----------
    stabilized_noi : float
        Expected NOI at stabilization
    total_development_cost : float
        All-in development cost (land + hard costs + soft costs)

    Returns:
    --------
    float : Yield on cost as percentage
    """
    if total_development_cost == 0:
        return 0.0

    yield_on_cost = (stabilized_noi / total_development_cost) * 100

    return yield_on_cost


def calculate_development_margin(
    stabilized_value: float,
    total_development_cost: float
) -> float:
    """
    Calculate development profit margin.

    Margin % = (Stabilized Value - Total Cost) / Total Cost × 100%

    Parameters:
    -----------
    stabilized_value : float
        Estimated value at stabilization (via cap rate or comparable sales)
    total_development_cost : float
        All-in development cost

    Returns:
    --------
    float : Margin as percentage
    """
    if total_development_cost == 0:
        return 0.0

    margin = ((stabilized_value - total_development_cost) /
              total_development_cost) * 100

    return margin


def calculate_loan_to_cost(
    construction_loan: float,
    total_development_cost: float
) -> float:
    """
    Calculate Loan-to-Cost ratio.

    LTC = Construction Loan / Total Development Cost

    Parameters:
    -----------
    construction_loan : float
        Construction loan amount
    total_development_cost : float
        Total development cost

    Returns:
    --------
    float : LTC as percentage
    """
    if total_development_cost == 0:
        return 0.0

    ltc = (construction_loan / total_development_cost) * 100

    return ltc


def calculate_loan_to_value(
    construction_loan: float,
    estimated_stabilized_value: float
) -> float:
    """
    Calculate Loan-to-Value ratio.

    LTV = Construction Loan / Estimated Stabilized Value

    Parameters:
    -----------
    construction_loan : float
        Construction loan amount
    estimated_stabilized_value : float
        Estimated value upon stabilization

    Returns:
    --------
    float : LTV as percentage
    """
    if estimated_stabilized_value == 0:
        return 0.0

    ltv = (construction_loan / estimated_stabilized_value) * 100

    return ltv
```

---

## II. Debt Reconciliations

```python
def reconcile_moodys_adjusted_debt(
    reported_debt: float,
    adjustments: Dict[str, float]
) -> pd.DataFrame:
    """
    Create Moody's-adjusted debt reconciliation table.

    Common adjustments:
    - + Hybrid/perpetual securities (50% debt treatment)
    - + Pro rata share of JV debt
    - + Operating lease obligations (if applicable)
    - +/- Other adjustments

    Parameters:
    -----------
    reported_debt : float
        As-reported debt from balance sheet
    adjustments : Dict[str, float]
        Dict of adjustment line items

    Returns:
    --------
    pd.DataFrame : Reconciliation table
    """
    recon_items = ['As Reported Debt'] + list(adjustments.keys()) + ['Moody\'s-Adjusted Debt']

    amounts = [reported_debt] + list(adjustments.values()) + [
        reported_debt + sum(adjustments.values())
    ]

    reconciliation = pd.DataFrame({
        'Item': recon_items,
        'Amount': amounts
    })

    return reconciliation
```

---

## III. Liquidity Analysis

```python
from datetime import datetime, timedelta
from typing import List

def calculate_liquidity_coverage(
    sources: Dict[str, float],
    uses: Dict[str, float]
) -> Dict[str, Union[float, pd.DataFrame]]:
    """
    Calculate liquidity coverage ratio and create sources/uses table.

    Parameters:
    -----------
    sources : Dict[str, float]
        Dict of liquidity sources (cash, undrawn facilities, etc.)
    uses : Dict[str, float]
        Dict of liquidity uses (maturities, capex, dividends, etc.)

    Returns:
    --------
    Dict with:
        - 'total_sources': float
        - 'total_uses': float
        - 'coverage_ratio': float
        - 'excess_liquidity': float
        - 'table': pd.DataFrame
    """
    total_sources = sum(sources.values())
    total_uses = sum(uses.values())

    coverage_ratio = total_sources / total_uses if total_uses > 0 else np.inf
    excess_liquidity = total_sources - total_uses

    # Create summary table
    sources_df = pd.DataFrame(
        list(sources.items()),
        columns=['Item', 'Amount']
    )
    sources_df['Type'] = 'Source'

    uses_df = pd.DataFrame(
        list(uses.items()),
        columns=['Item', 'Amount']
    )
    uses_df['Type'] = 'Use'

    summary_df = pd.concat([sources_df, uses_df], ignore_index=True)

    return {
        'total_sources': total_sources,
        'total_uses': total_uses,
        'coverage_ratio': coverage_ratio,
        'excess_liquidity': excess_liquidity,
        'table': summary_df
    }


def analyze_debt_maturity_profile(
    debt_schedule: pd.DataFrame
) -> Dict[str, Union[pd.DataFrame, float]]:
    """
    Analyze debt maturity profile and identify concentration risk.

    Parameters:
    -----------
    debt_schedule : pd.DataFrame
        DataFrame with columns:
        - 'instrument': Debt instrument name
        - 'maturity_date': Maturity date (datetime)
        - 'amount': Outstanding amount
        - 'type': Type (e.g., 'Term Loan', 'Bond', 'Revolver')

    Returns:
    --------
    Dict with:
        - 'maturity_by_year': pd.DataFrame (maturities by year)
        - 'concentration_risk': pd.DataFrame (% of debt in each year)
        - 'max_annual_concentration': float (highest % in one year)
    """
    # Extract year from maturity date
    debt_schedule['maturity_year'] = debt_schedule['maturity_date'].dt.year

    # Group by year
    maturity_by_year = debt_schedule.groupby('maturity_year').agg({
        'amount': 'sum'
    }).reset_index()
    maturity_by_year.columns = ['Year', 'Amount Maturing']

    # Calculate concentration %
    total_debt = debt_schedule['amount'].sum()
    maturity_by_year['% of Total Debt'] = (
        maturity_by_year['Amount Maturing'] / total_debt * 100
    )

    max_concentration = maturity_by_year['% of Total Debt'].max()

    return {
        'maturity_by_year': maturity_by_year,
        'max_annual_concentration': max_concentration
    }
```

---

## IV. Forecasting Functions

```python
def forecast_revenue(
    prior_revenue: float,
    same_store_growth: float,
    acquisition_noi: float = 0,
    disposition_noi: float = 0
) -> float:
    """
    Forecast revenue for next period.

    Revenue = (Prior Revenue × (1 + Same-Store Growth %))
              + Acquisition Contributions
              - Disposition Impact

    Parameters:
    -----------
    prior_revenue : float
        Prior period revenue
    same_store_growth : float
        Expected same-store growth rate (as decimal, e.g., 0.03 = 3%)
    acquisition_noi : float
        Expected NOI from acquisitions
    disposition_noi : float
        NOI from dispositions to remove

    Returns:
    --------
    float : Forecasted revenue
    """
    forecast = (prior_revenue * (1 + same_store_growth)
                + acquisition_noi
                - disposition_noi)

    return forecast


def forecast_ebitda(
    forecast_revenue: float,
    ebitda_margin: float
) -> float:
    """
    Forecast EBITDA based on revenue and margin assumption.

    EBITDA = Revenue × EBITDA Margin

    Parameters:
    -----------
    forecast_revenue : float
        Forecasted revenue
    ebitda_margin : float
        Expected EBITDA margin (as decimal, e.g., 0.65 = 65%)

    Returns:
    --------
    float : Forecasted EBITDA
    """
    return forecast_revenue * ebitda_margin


def forecast_interest_expense(
    beginning_debt: float,
    new_debt: float,
    debt_repayments: float,
    weighted_avg_rate: float
) -> float:
    """
    Forecast interest expense.

    Average Debt = (Beginning Debt + Ending Debt) / 2
    Interest Expense = Average Debt × Weighted Average Rate

    Parameters:
    -----------
    beginning_debt : float
        Debt at beginning of period
    new_debt : float
        New debt issued during period
    debt_repayments : float
        Debt repaid during period
    weighted_avg_rate : float
        Weighted average interest rate (as decimal, e.g., 0.045 = 4.5%)

    Returns:
    --------
    float : Forecasted interest expense
    """
    ending_debt = beginning_debt + new_debt - debt_repayments
    average_debt = (beginning_debt + ending_debt) / 2

    interest_expense = average_debt * weighted_avg_rate

    return interest_expense
```

---

## V. Peer Comparison

```python
def create_peer_comparison_table(
    issuer_metrics: Dict[str, float],
    peer_data: pd.DataFrame,
    issuer_name: str
) -> pd.DataFrame:
    """
    Create peer comparison table.

    Parameters:
    -----------
    issuer_metrics : Dict[str, float]
        Metrics for the issuer being analyzed
    peer_data : pd.DataFrame
        DataFrame with peer metrics (columns = metric names, rows = peers)
    issuer_name : str
        Name of the issuer

    Returns:
    --------
    pd.DataFrame : Comparison table with issuer and peers
    """
    # Add issuer to peer data
    issuer_row = pd.DataFrame([issuer_metrics])
    issuer_row.insert(0, 'Company', issuer_name)

    peer_data_copy = peer_data.copy()

    # Combine
    comparison = pd.concat([issuer_row, peer_data_copy], ignore_index=True)

    return comparison


def calculate_percentile_rank(
    issuer_value: float,
    peer_values: List[float],
    higher_is_better: bool = True
) -> float:
    """
    Calculate issuer's percentile rank vs. peers for a given metric.

    Parameters:
    -----------
    issuer_value : float
        Issuer's value for the metric
    peer_values : List[float]
        List of peer values
    higher_is_better : bool
        True if higher values are better (e.g., interest coverage)
        False if lower is better (e.g., leverage)

    Returns:
    --------
    float : Percentile rank (0-100)
    """
    all_values = peer_values + [issuer_value]
    all_values_sorted = sorted(all_values, reverse=higher_is_better)

    issuer_rank = all_values_sorted.index(issuer_value) + 1

    percentile = ((len(all_values) - issuer_rank + 1) / len(all_values)) * 100

    return percentile
```

---

## VI. Scenario Analysis

```python
def run_leverage_sensitivity(
    base_ebitda: float,
    base_debt: float,
    base_assets: float,
    ebitda_scenarios: Dict[str, float],
    asset_value_scenarios: Dict[str, float]
) -> pd.DataFrame:
    """
    Run sensitivity analysis on leverage metrics under different scenarios.

    Parameters:
    -----------
    base_ebitda : float
        Base case EBITDA
    base_debt : float
        Current debt level
    base_assets : float
        Current asset value
    ebitda_scenarios : Dict[str, float]
        Scenarios with EBITDA changes (e.g., {'Base': 0, 'Downside': -0.15})
    asset_value_scenarios : Dict[str, float]
        Scenarios with asset value changes (e.g., {'Base': 0, 'Downside': -0.10})

    Returns:
    --------
    pd.DataFrame : Sensitivity table with scenarios and resulting metrics
    """
    results = []

    for ebitda_scenario, ebitda_change in ebitda_scenarios.items():
        for asset_scenario, asset_change in asset_value_scenarios.items():
            scenario_ebitda = base_ebitda * (1 + ebitda_change)
            scenario_assets = base_assets * (1 + asset_change)

            # Calculate metrics
            net_debt_ebitda = base_debt / scenario_ebitda
            debt_assets = (base_debt / scenario_assets) * 100

            results.append({
                'EBITDA Scenario': ebitda_scenario,
                'Asset Value Scenario': asset_scenario,
                'EBITDA': scenario_ebitda,
                'Assets': scenario_assets,
                'Net Debt / EBITDA': net_debt_ebitda,
                'Debt / Assets %': debt_assets
            })

    sensitivity_df = pd.DataFrame(results)

    return sensitivity_df
```

---

## VII. Utility Functions

```python
def format_currency(value: float, decimals: int = 1) -> str:
    """Format value as currency in millions."""
    return f"${value:,.{decimals}f}"


def format_percentage(value: float, decimals: int = 1) -> str:
    """Format value as percentage."""
    return f"{value:.{decimals}f}%"


def format_multiple(value: float, decimals: int = 1) -> str:
    """Format value as multiple (e.g., 7.5x)."""
    return f"{value:.{decimals}f}x"
```

---

## VIII. Example Workflow Script

```python
def analyze_issuer_credit_metrics(
    financial_data: Dict[str, float],
    lease_data: pd.DataFrame = None
) -> Dict[str, Union[float, str]]:
    """
    Complete workflow to calculate all key credit metrics for an issuer.

    Parameters:
    -----------
    financial_data : Dict[str, float]
        Dictionary with all required financial inputs
    lease_data : pd.DataFrame, optional
        Lease schedule data for WALE calculation

    Returns:
    --------
    Dict : All calculated metrics formatted for report
    """
    # Calculate EBITDA
    ebitda_result = calculate_adjusted_ebitda(
        base_ebitda=financial_data['base_ebitda'],
        adjustments=financial_data.get('ebitda_adjustments', {})
    )

    ebitda = ebitda_result['adjusted_ebitda']

    # Calculate leverage ratios
    debt_to_assets = calculate_debt_to_assets(
        total_debt=financial_data['total_debt'],
        gross_assets=financial_data['gross_assets'],
        jv_debt_pro_rata=financial_data.get('jv_debt', 0),
        perpetual_securities=financial_data.get('perpetual_securities', 0)
    )

    net_debt_ebitda = calculate_net_debt_to_ebitda(
        total_debt=financial_data['total_debt'],
        cash=financial_data['cash'],
        ebitda=ebitda,
        jv_debt_pro_rata=financial_data.get('jv_debt', 0),
        jv_ebitda_pro_rata=financial_data.get('jv_ebitda', 0),
        perpetual_securities=financial_data.get('perpetual_securities', 0)
    )

    interest_coverage = calculate_interest_coverage(
        ebitda=ebitda,
        interest_expense=financial_data['interest_expense'],
        jv_ebitda_pro_rata=financial_data.get('jv_ebitda', 0),
        jv_interest_pro_rata=financial_data.get('jv_interest', 0),
        perpetual_distributions=financial_data.get('perpetual_distributions', 0)
    )

    # Calculate REIT metrics if applicable
    reit_metrics = {}
    if 'net_income' in financial_data and 'depreciation_re' in financial_data:
        ffo = calculate_ffo(
            net_income=financial_data['net_income'],
            depreciation_real_estate=financial_data['depreciation_re'],
            amortization_real_estate=financial_data.get('amortization_re', 0),
            gains_on_property_sales=financial_data.get('gains_on_sales', 0)
        )

        affo = calculate_affo(
            ffo=ffo,
            recurring_capex=financial_data.get('recurring_capex', 0),
            straight_line_rent_adjustment=financial_data.get('sl_rent_adj', 0)
        )

        reit_metrics['FFO'] = ffo
        reit_metrics['AFFO'] = affo

    # Calculate WALE if lease data provided
    if lease_data is not None:
        wale = calculate_wale(lease_data, weight_by='rent')
        reit_metrics['WALE'] = wale

    # Package results
    metrics = {
        'Gross Assets': format_currency(financial_data['gross_assets']),
        'EBITDA': format_currency(ebitda),
        'Debt / Gross Assets': format_percentage(debt_to_assets * 100),
        'Net Debt / EBITDA': format_multiple(net_debt_ebitda),
        'EBITDA / Interest Expense': format_multiple(interest_coverage),
        **{k: format_currency(v) if 'FFO' in k or 'AFFO' in k else f"{v:.1f} years"
           for k, v in reit_metrics.items()}
    }

    return metrics
```

---

## IX. Notes on Implementation

### Code Quality Standards

1. **Type Hints:** All functions use type hints for clarity
2. **Docstrings:** Comprehensive docstrings with parameter descriptions
3. **Error Handling:** Division by zero checks, graceful handling of missing data
4. **Consistency:** Consistent naming conventions (snake_case for functions/variables)

### Testing Requirements

Each calculation function should be unit tested with:
- Standard case (typical inputs)
- Edge cases (zero values, missing data)
- Validation against known correct answers (using Moody's report figures)

### Data Input Format

Financial data should be provided as:
- **Python dict** for single-period metrics
- **Pandas DataFrame** for time-series (historical + forecast)
- **Consistent units:** All currency in same unit (e.g., $ millions)
- **Decimals for percentages:** Use 0.05 for 5%, not 5

### Integration with Report Generation

These calculations feed into visualization and PDF report generation scripts (see `python_visualization_library.md`).

