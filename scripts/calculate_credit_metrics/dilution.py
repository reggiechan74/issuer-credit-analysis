"""
Share dilution analysis

Functions for analyzing dilution from convertible securities, options, and warrants.
Per v1.0.8+ dilution tracking methodology.
"""


def analyze_dilution(financial_data):
    """
    Analyze share dilution from dilution_detail section

    Provides materiality assessment and credit quality implications of dilution.

    Args:
        financial_data (dict): Phase 2 extraction with optional dilution_detail section

    Returns:
        dict: {
            'has_dilution_detail': bool,
            'dilution_percentage': float | None,
            'dilution_materiality': str,  # 'minimal', 'low', 'moderate', 'high'
            'material_instruments': list,  # Instruments contributing >1% dilution
            'convertible_debt_risk': str,  # 'none', 'low', 'moderate', 'high'
            'governance_score': str,  # 'standard', 'enhanced' (based on disclosure)
            'credit_assessment': str,  # Overall credit quality impact
            'detail': dict  # Full dilution_detail if available
        }
    """

    if 'dilution_detail' not in financial_data:
        return {
            'has_dilution_detail': False,
            'dilution_percentage': None,
            'dilution_materiality': 'unknown',
            'material_instruments': [],
            'convertible_debt_risk': 'unknown',
            'governance_score': 'standard',
            'credit_assessment': 'No detailed dilution disclosure - standard for many REITs',
            'detail': None
        }

    dilution = financial_data['dilution_detail']

    # Calculate dilution percentage if not provided
    dilution_pct = dilution.get('dilution_percentage')
    if dilution_pct is None and 'basic_units' in dilution and 'diluted_units_reported' in dilution:
        basic = dilution['basic_units']
        diluted = dilution['diluted_units_reported']
        if basic and basic > 0:
            dilution_pct = ((diluted - basic) / basic) * 100

    # Assess materiality
    if dilution_pct is None:
        materiality = 'unknown'
    elif dilution_pct < 1.0:
        materiality = 'minimal'
    elif dilution_pct < 3.0:
        materiality = 'low'
    elif dilution_pct < 7.0:
        materiality = 'moderate'
    else:
        materiality = 'high'

    # Identify material instruments (>1% dilution each)
    material_instruments = []
    instruments = dilution.get('dilutive_instruments', {})
    basic_units = dilution.get('basic_units', 1)  # Avoid division by zero

    for instrument, count in instruments.items():
        if count and basic_units > 0:
            instrument_pct = (count / basic_units) * 100
            if instrument_pct > 1.0:
                material_instruments.append({
                    'instrument': instrument,
                    'units': count,
                    'dilution_pct': round(instrument_pct, 2)
                })

    # Assess convertible debt risk
    convertible_units = instruments.get('convertible_debentures', 0)
    if convertible_units and basic_units > 0:
        convertible_pct = (convertible_units / basic_units) * 100
        if convertible_pct == 0:
            conv_risk = 'none'
        elif convertible_pct < 3:
            conv_risk = 'low'
        elif convertible_pct < 7:
            conv_risk = 'moderate'
        else:
            conv_risk = 'high'
    else:
        conv_risk = 'none'

    # Governance score (enhanced disclosure = better governance)
    governance = 'enhanced' if dilution.get('disclosure_source') else 'standard'

    # Overall credit assessment
    if materiality == 'minimal' or materiality == 'low':
        if conv_risk == 'none':
            assessment = '✓ Low dilution risk - minimal equity overhang, positive for creditworthiness'
        else:
            assessment = '⚠ Low overall dilution but monitor convertible debt for forced conversion scenarios'
    elif materiality == 'moderate':
        if conv_risk in ['none', 'low']:
            assessment = '⚠ Moderate dilution from equity compensation - typical for REITs, manageable credit impact'
        else:
            assessment = '⚠ Moderate dilution with material convertibles - assess conversion terms and debt capacity implications'
    else:  # high
        assessment = '🚨 HIGH dilution - material equity overhang, review impact on debt capacity and unit holder value dilution'

    return {
        'has_dilution_detail': True,
        'dilution_percentage': round(dilution_pct, 2) if dilution_pct else None,
        'dilution_materiality': materiality,
        'material_instruments': material_instruments,
        'convertible_debt_risk': conv_risk,
        'governance_score': governance,
        'credit_assessment': assessment,
        'detail': dilution
    }


__all__ = ['analyze_dilution']
