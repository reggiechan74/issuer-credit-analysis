#!/usr/bin/env python3
"""
Test Phase 3: Safe Calculation Library (CRITICAL SAFETY TESTS)

These tests ensure the calculation library:
1. Has NO hardcoded financial data
2. Requires explicit input (no defaults)
3. Fails loudly when data is missing
4. Produces correct calculations
"""

import pytest
import sys
import json
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))


class TestPhase3SafetyRequirements:
    """CRITICAL: Test that calculation library is safe from misuse"""

    def test_module_has_no_financial_constants(self):
        """CRITICAL: Ensure no hardcoded financial data exists in module"""
        import calculate_credit_metrics as calc_module

        # Get module code
        import inspect
        source = inspect.getsource(calc_module)

        # Check for suspicious numeric constants that look like financial data
        # (Large numbers like 2611435, 1079968, etc.)
        import re

        # Find all numeric constants > 1000
        numbers = re.findall(r'\b\d{4,}\b', source)
        numbers = [int(n) for n in numbers if not n.startswith('0')]

        # Whitelist: Years, percentages, reasonable thresholds
        whitelist = [1000, 2000, 2025, 2024, 2026]

        suspicious_numbers = [n for n in numbers if n not in whitelist]

        if suspicious_numbers:
            pytest.fail(
                f"Found suspicious large numbers in calculation library: {suspicious_numbers}. "
                f"This may indicate hardcoded financial data. Remove all constants."
            )

    def test_calculate_leverage_requires_input(self):
        """CRITICAL: Functions must require input, no defaults"""
        from calculate_credit_metrics import calculate_leverage_metrics

        # Should raise TypeError when called without arguments
        with pytest.raises(TypeError):
            calculate_leverage_metrics()

    def test_calculate_leverage_fails_on_missing_fields(self):
        """CRITICAL: Functions must fail loudly when required fields missing"""
        from calculate_credit_metrics import calculate_leverage_metrics

        # Empty dictionary should raise KeyError
        with pytest.raises(KeyError):
            calculate_leverage_metrics({})

        # Partial data should raise KeyError
        with pytest.raises(KeyError):
            calculate_leverage_metrics({
                'balance_sheet': {
                    'total_assets': 1000000
                    # Missing other required fields
                }
            })

    def test_calculate_leverage_fails_on_invalid_values(self):
        """CRITICAL: Functions must validate data reasonableness"""
        from calculate_credit_metrics import calculate_leverage_metrics

        # Zero or negative assets should raise ValueError
        with pytest.raises(ValueError):
            calculate_leverage_metrics({
                'balance_sheet': {
                    'total_assets': 0,
                    'mortgages_noncurrent': 100000,
                    'mortgages_current': 50000,
                    'credit_facilities': 200000,
                    'cash': 10000
                }
            })

        # Negative debt should raise ValueError
        with pytest.raises(ValueError):
            calculate_leverage_metrics({
                'balance_sheet': {
                    'total_assets': 1000000,
                    'mortgages_noncurrent': -100000,  # Invalid
                    'mortgages_current': 50000,
                    'credit_facilities': 200000,
                    'cash': 10000
                }
            })


class TestPhase3CalculationAccuracy:
    """Test that calculations are mathematically correct"""

    @pytest.fixture
    def sample_data(self):
        """Load sample extracted data fixture"""
        fixture_path = Path(__file__).parent / 'fixtures' / 'sample_extracted_data.json'
        with open(fixture_path, 'r') as f:
            return json.load(f)

    def test_calculate_leverage_metrics(self, sample_data):
        """Test leverage metrics calculation accuracy"""
        from calculate_credit_metrics import calculate_leverage_metrics

        result = calculate_leverage_metrics(sample_data)

        # Expected calculations based on fixture data:
        # Total Debt = 250000 + 150000 + 300000 = 700000
        # Net Debt = 700000 - 25000 = 675000
        # Gross Assets = 1500000
        # Debt/Assets = 700000 / 1500000 = 46.67%

        assert result['total_debt'] == 700000
        assert result['net_debt'] == 675000
        assert result['gross_assets'] == 1500000
        assert abs(result['debt_to_assets_percent'] - 46.67) < 0.1

    def test_calculate_reit_metrics(self, sample_data):
        """Test REIT-specific metrics calculation"""
        from calculate_credit_metrics import calculate_reit_metrics

        result = calculate_reit_metrics(sample_data)

        # Should extract values correctly from fixture
        assert result['ffo_per_unit'] == 0.25
        assert result['affo_per_unit'] == 0.20
        assert abs(result['ffo_payout_ratio'] - 72.0) < 0.1  # 0.18 / 0.25 = 72%
        assert abs(result['affo_payout_ratio'] - 90.0) < 0.1  # 0.18 / 0.20 = 90%

    def test_calculate_coverage_ratios(self, sample_data):
        """Test interest coverage and EBITDA calculations"""
        from calculate_credit_metrics import calculate_coverage_ratios

        result = calculate_coverage_ratios(sample_data)

        # NOI / Interest = 30000 / 12000 = 2.5x
        assert abs(result['noi_interest_coverage'] - 2.5) < 0.01

        # Annualized calculations (Q2 * 4)
        # Expected: interest_expense annualized = 12000 * 4 = 48000
        assert result['annualized_interest_expense'] == 48000


class TestPhase3OutputFormat:
    """Test that output includes issuer identification and is properly formatted"""

    @pytest.fixture
    def sample_data(self):
        """Load sample extracted data fixture"""
        fixture_path = Path(__file__).parent / 'fixtures' / 'sample_extracted_data.json'
        with open(fixture_path, 'r') as f:
            return json.load(f)

    def test_main_script_requires_input_file(self):
        """Test that main script requires input file argument"""
        import subprocess
        result = subprocess.run(
            ['python', 'scripts/calculate_credit_metrics.py'],
            capture_output=True,
            text=True
        )

        # Should fail with usage error (exit code 2)
        assert result.returncode == 2
        assert 'required' in result.stderr.lower() or 'usage' in result.stderr.lower()

    def test_output_includes_issuer_identification(self, sample_data):
        """Test that calculations preserve issuer identification"""
        from calculate_credit_metrics import calculate_all_metrics

        result = calculate_all_metrics(sample_data)

        # Output must include issuer identification
        assert 'issuer_name' in result
        assert 'reporting_date' in result
        assert result['issuer_name'] == sample_data['issuer_name']
        assert result['reporting_date'] == sample_data['reporting_date']

    def test_output_structure(self, sample_data):
        """Test that output has expected structure"""
        from calculate_credit_metrics import calculate_all_metrics

        result = calculate_all_metrics(sample_data)

        # Should have standard sections
        assert 'issuer_name' in result
        assert 'reporting_date' in result
        assert 'leverage_metrics' in result
        assert 'reit_metrics' in result
        assert 'coverage_ratios' in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
