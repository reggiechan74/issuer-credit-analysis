#!/usr/bin/env python3
"""
Test Phase 2: LLM-based Financial Data Extraction with Validation

These tests ensure:
1. Extraction produces valid JSON with required fields
2. Validation catches errors (balance sheet imbalance, etc.)
3. Output includes issuer identification
"""

import pytest
import sys
import json
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))


class TestPhase2Validation:
    """Test validation logic"""

    def test_validate_balance_sheet_balanced(self):
        """Test that validator catches balance sheet imbalances"""
        from validate_extraction_schema import validate_schema

        # Minimal valid structure but missing required fields
        invalid_data = {
            'issuer_name': 'Test REIT',
            'reporting_date': '2025-06-30',
            'currency': 'CAD',
            'balance_sheet': {
                'total_assets': 1000000,
                'mortgages_noncurrent': 300000,
                'mortgages_current': 100000,
                'credit_facilities': 200000,
                'cash': 50000
            },
            'income_statement': {
                'noi': 50000,
                'interest_expense': 20000,
                'revenue': 100000
            },
            'ffo_affo': {
                'ffo': 40000,
                'affo': 35000,
                'ffo_per_unit': 0.50,
                'affo_per_unit': 0.45,
                'distributions_per_unit': 0.30
            },
            'validation': {
                'balance_sheet_balanced': False  # This flags imbalance
            }
        }

        is_valid, errors = validate_schema(invalid_data)

        # Should flag warning about imbalance
        warning_found = any('Balance sheet does not balance' in err for err in errors)
        assert warning_found, "Should warn about balance sheet imbalance"

    def test_validate_positive_revenue(self):
        """Test that validator catches missing revenue field"""
        from validate_extraction_schema import validate_schema

        # Missing revenue in income_statement
        invalid_data = {
            'issuer_name': 'Test REIT',
            'reporting_date': '2025-06-30',
            'currency': 'CAD',
            'balance_sheet': {
                'total_assets': 1000000,
                'mortgages_noncurrent': 300000,
                'mortgages_current': 100000,
                'credit_facilities': 200000,
                'cash': 50000
            },
            'income_statement': {
                'noi': 50000,
                'interest_expense': 20000
                # revenue is missing - should cause validation error
            },
            'ffo_affo': {
                'ffo': 40000,
                'affo': 35000,
                'ffo_per_unit': 0.50,
                'affo_per_unit': 0.45,
                'distributions_per_unit': 0.30
            }
        }

        is_valid, errors = validate_schema(invalid_data)

        # Should flag error about missing revenue
        assert is_valid is False
        assert any('revenue' in err.lower() for err in errors)

    def test_validate_occupancy_range(self):
        """Test that validator catches invalid occupancy rates"""
        from validate_extraction_schema import validate_schema

        # occupancy_rate > 1.0 (should be decimal)
        invalid_data = {
            'issuer_name': 'Test REIT',
            'reporting_date': '2025-06-30',
            'currency': 'CAD',
            'balance_sheet': {
                'total_assets': 1000000,
                'mortgages_noncurrent': 300000,
                'mortgages_current': 100000,
                'credit_facilities': 200000,
                'cash': 50000
            },
            'income_statement': {
                'noi': 50000,
                'interest_expense': 20000,
                'revenue': 100000
            },
            'ffo_affo': {
                'ffo': 40000,
                'affo': 35000,
                'ffo_per_unit': 0.50,
                'affo_per_unit': 0.45,
                'distributions_per_unit': 0.30
            },
            'portfolio': {
                'occupancy_rate': 87.8  # Invalid (should be 0.878)
            }
        }

        is_valid, errors = validate_schema(invalid_data)

        # Should flag warning about occupancy format
        warning_found = any('occupancy_rate' in err and 'should be decimal' in err for err in errors)
        assert warning_found, "Should warn about occupancy rate format"


class TestPhase2OutputFormat:
    """Test that extraction produces correct output format"""

    def test_extraction_requires_markdown_input(self):
        """Test that extraction script exists and has proper interface"""
        from pathlib import Path

        # Check that the production extraction script exists (v1 - markdown-first with file references)
        script_path = Path(__file__).parent.parent / 'scripts' / 'extract_key_metrics_efficient.py'
        assert script_path.exists(), f"Extraction script not found at {script_path}"

        # V2 experimental script should exist in experimental folder
        v2_script_path = Path(__file__).parent.parent / 'scripts' / 'experimental' / 'extract_key_metrics_v2.py'
        assert v2_script_path.exists(), f"Experimental v2 script not found at {v2_script_path}"

    def test_extraction_output_structure(self):
        """Test validation of a properly structured output"""
        from validate_extraction_schema import validate_schema

        # Valid complete structure
        valid_data = {
            'issuer_name': 'Test REIT',
            'reporting_date': '2025-06-30',
            'reporting_period': 'Q2 2025',
            'currency': 'CAD',
            'balance_sheet': {
                'total_assets': 1000000,
                'mortgages_noncurrent': 300000,
                'mortgages_current': 100000,
                'credit_facilities': 200000,
                'cash': 50000,
                'senior_unsecured_debentures': 0,
                'investment_properties': 800000,
                'total_liabilities': 600000,
                'unitholders_equity': 400000
            },
            'income_statement': {
                'noi': 50000,
                'interest_expense': 20000,
                'revenue': 100000,
                'property_operating_expenses': 40000,
                'net_income': 25000
            },
            'ffo_affo': {
                'ffo': 40000,
                'affo': 35000,
                'ffo_per_unit': 0.50,
                'affo_per_unit': 0.45,
                'distributions_per_unit': 0.30,
                'ffo_payout_ratio': 0.60,
                'affo_payout_ratio': 0.667
            },
            'portfolio': {
                'property_count': 50,
                'total_gla_sf': 5000000,
                'occupancy_rate': 0.878,
                'occupancy_with_commitments': 0.90
            }
        }

        is_valid, errors = validate_schema(valid_data)

        # Should pass validation
        assert is_valid is True, f"Valid data should pass validation. Errors: {errors}"


class TestPhase2MainScript:
    """Test main script command-line interface"""

    def test_main_script_requires_input_files(self):
        """Test that main script requires input markdown files"""
        import subprocess

        result = subprocess.run(
            ['python', 'scripts/extract_key_metrics_v2.py'],
            capture_output=True,
            text=True
        )

        # Should fail with usage error (no arguments provided)
        assert result.returncode != 0

    def test_validation_script_exists(self):
        """Test that validation script exists and works"""
        from pathlib import Path

        script_path = Path(__file__).parent.parent / 'scripts' / 'validate_extraction_schema.py'
        assert script_path.exists(), f"Validation script not found at {script_path}"

        # Test running validation script without arguments
        import subprocess
        result = subprocess.run(
            ['python', str(script_path)],
            capture_output=True,
            text=True
        )

        # Should show usage message
        assert 'Usage' in result.stdout or 'Usage' in result.stderr


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
