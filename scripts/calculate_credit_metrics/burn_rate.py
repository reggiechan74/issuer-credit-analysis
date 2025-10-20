"""
Cash burn rate and liquidity runway analysis

Functions for assessing liquidity risk when AFCF cannot cover financing obligations.
"""

from ._core import (
    calculate_burn_rate,
    calculate_cash_runway,
    assess_liquidity_risk,
    calculate_sustainable_burn_rate
)

__all__ = [
    'calculate_burn_rate',
    'calculate_cash_runway',
    'assess_liquidity_risk',
    'calculate_sustainable_burn_rate'
]
