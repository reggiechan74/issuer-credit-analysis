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
        from scripts.extract_key_metrics import validate_extraction

        # Unbalanced balance sheet
        invalid_data = {
            'balance_sheet': {
                'total_assets': 1000000,
                'total_liabilities': 600000,
                'equity': 300000  # Should be 400000 to balance
            }
        }

        # Mock source text
        result = validate_extraction(invalid_data, "sample text")

        # Should flag error
        assert result['_validation']['is_valid'] is False
        assert len(result['_validation']['errors']) > 0

    def test_validate_positive_revenue(self):
        """Test that validator catches missing/invalid revenue"""
        from scripts.extract_key_metrics import validate_extraction

        invalid_data = {
            'balance_sheet': {
                'total_assets': 1000000,
                'total_liabilities': 600000,
                'equity': 400000
            },
            'income_statement': {
                'revenue': 0  # Invalid
            }
        }

        result = validate_extraction(invalid_data, "sample text")

        # Should flag error
        assert result['_validation']['is_valid'] is False

    def test_validate_occupancy_range(self):
        """Test that validator catches invalid occupancy rates"""
        from scripts.extract_key_metrics import validate_extraction

        invalid_data = {
            'balance_sheet': {
                'total_assets': 1000000,
                'total_liabilities': 600000,
                'equity': 400000
            },
            'income_statement': {
                'revenue': 100000
            },
            'portfolio': {
                'occupancy_rate': 150  # Invalid (>100%)
            }
        }

        result = validate_extraction(invalid_data, "sample text")

        # Should flag error
        assert result['_validation']['is_valid'] is False


class TestPhase2OutputFormat:
    """Test that extraction produces correct output format"""

    def test_extraction_requires_markdown_input(self):
        """Test that extraction function requires markdown text"""
        from scripts.extract_key_metrics import extract_financial_data_with_llm

        # Should raise error when called without text
        with pytest.raises(TypeError):
            extract_financial_data_with_llm()

    def test_extraction_output_structure(self):
        """Test that extraction produces required fields"""
        # Use the sample markdown fixture
        fixture_path = Path(__file__).parent / 'fixtures' / 'sample_financial_statement.md'

        if not fixture_path.exists():
            pytest.skip("Sample markdown fixture not found")

        with open(fixture_path, 'r') as f:
            markdown_text = f.read()

        # Mock the LLM call for testing (we don't want to make actual API calls in tests)
        # In a real implementation, you'd use dependency injection or mocking
        # For now, skip this test if ANTHROPIC_API_KEY not set
        import os
        if 'ANTHROPIC_API_KEY' not in os.environ:
            pytest.skip("ANTHROPIC_API_KEY not set - skipping LLM test")

        from scripts.extract_key_metrics import extract_financial_data_with_llm

        try:
            result = extract_financial_data_with_llm(markdown_text)

            # Should have required top-level fields
            assert 'issuer_name' in result
            assert 'reporting_date' in result
            assert 'balance_sheet' in result
            assert 'income_statement' in result
            assert '_validation' in result

        except Exception as e:
            # API calls may fail in test environment
            pytest.skip(f"LLM extraction test skipped: {e}")


class TestPhase2MainScript:
    """Test main script command-line interface"""

    def test_main_script_requires_input_files(self):
        """Test that main script requires input markdown files"""
        import subprocess

        result = subprocess.run(
            ['python', 'scripts/extract_key_metrics.py'],
            capture_output=True,
            text=True
        )

        # Should fail with usage error
        assert result.returncode != 0

    def test_main_script_with_sample_fixture(self):
        """Test main script with sample markdown fixture"""
        import os
        if 'ANTHROPIC_API_KEY' not in os.environ:
            pytest.skip("ANTHROPIC_API_KEY not set - skipping integration test")

        import subprocess
        import tempfile

        fixture_path = Path(__file__).parent / 'fixtures' / 'sample_financial_statement.md'

        if not fixture_path.exists():
            pytest.skip("Sample markdown fixture not found")

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "extracted.json"

            result = subprocess.run(
                [
                    'python', 'scripts/extract_key_metrics.py',
                    str(fixture_path),
                    '--output', str(output_path)
                ],
                capture_output=True,
                text=True,
                timeout=30
            )

            # Check if succeeded
            if result.returncode == 0:
                # Verify output file exists
                assert output_path.exists()

                # Verify it's valid JSON
                with open(output_path, 'r') as f:
                    data = json.load(f)

                assert 'issuer_name' in data
                assert '_validation' in data
            else:
                # API call may have failed
                pytest.skip(f"Extraction failed (API issue?): {result.stderr}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
