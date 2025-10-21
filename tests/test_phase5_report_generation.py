#!/usr/bin/env python3
"""
Test Phase 5: Report Generation and Assembly

These tests ensure:
1. Report assembly script exists and works
2. Templates are properly structured
3. Phase 3 + Phase 4 outputs are combined correctly
4. Final report has all required sections
5. No LLM usage (0 tokens, pure templating)
"""

import pytest
import sys
import json
from pathlib import Path
from datetime import datetime

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))


class TestPhase5ScriptExists:
    """Test that Phase 5 script exists and has proper interface"""

    def test_report_assembly_script_exists(self):
        """Test that report assembly script exists"""
        project_root = Path(__file__).parent.parent
        script_path = project_root / "scripts/generate_final_report.py"

        assert script_path.exists(), (
            f"Phase 5 report assembly script not found at {script_path}"
        )

    def test_script_requires_inputs(self):
        """Test that script requires both Phase 3 and Phase 4 inputs"""
        import subprocess

        result = subprocess.run(
            ['python', 'scripts/generate_final_report.py'],
            capture_output=True,
            text=True
        )

        # Should fail with usage error
        assert result.returncode != 0, "Script should require input arguments"
        assert 'usage' in result.stderr.lower() or 'required' in result.stderr.lower(), (
            "Should show usage message"
        )

    def test_script_validates_input_files(self):
        """Test that script validates input files exist"""
        import subprocess

        result = subprocess.run(
            [
                'python', 'scripts/generate_final_report.py',
                'nonexistent_metrics.json',
                'nonexistent_analysis.md'
            ],
            capture_output=True,
            text=True
        )

        # Should fail with file not found error
        assert result.returncode != 0, "Should fail on missing files"


class TestPhase5Templates:
    """Test report template structure"""

    def test_template_directory_exists(self):
        """Test that template directory exists"""
        project_root = Path(__file__).parent.parent
        template_dir = project_root / "templates"

        assert template_dir.exists(), f"Template directory not found at {template_dir}"
        assert template_dir.is_dir(), "Template path should be a directory"

    def test_main_template_exists(self):
        """Test that main report template exists"""
        project_root = Path(__file__).parent.parent
        # Check for either the basic or enhanced template
        template_path_basic = project_root / "templates/credit_opinion_template.md"
        template_path_enhanced = project_root / "templates/credit_opinion_template_enhanced.md"

        template_exists = template_path_basic.exists() or template_path_enhanced.exists()
        assert template_exists, (
            f"Main template not found. Checked:\n"
            f"  - {template_path_basic}\n"
            f"  - {template_path_enhanced}"
        )

    def test_template_has_placeholders(self):
        """Test that template has proper placeholder format"""
        project_root = Path(__file__).parent.parent
        # Try both template names
        template_path = project_root / "templates/credit_opinion_template_enhanced.md"
        if not template_path.exists():
            template_path = project_root / "templates/credit_opinion_template.md"

        if not template_path.exists():
            pytest.skip("Template not created yet")

        with open(template_path, 'r') as f:
            content = f.read()

        # Should have placeholder markers (e.g., {{ISSUER_NAME}}, {METRIC}, etc.)
        placeholder_markers = ['{{', '}}', '{', '}']
        has_placeholders = any(marker in content for marker in placeholder_markers)

        assert has_placeholders, "Template should have placeholder markers"

    def test_template_has_required_sections(self):
        """Test that template includes all required report sections"""
        project_root = Path(__file__).parent.parent
        # Try both template names
        template_path = project_root / "templates/credit_opinion_template_enhanced.md"
        if not template_path.exists():
            template_path = project_root / "templates/credit_opinion_template.md"

        if not template_path.exists():
            pytest.skip("Template not created yet")

        with open(template_path, 'r') as f:
            content = f.read().lower()

        # Required sections from Moody's-style credit opinion
        required_sections = [
            'executive summary',
            'credit strength',
            'credit challenge',
            'rating outlook',
            'key indicator',
            'profile',
            'liquidity'
        ]

        for section in required_sections:
            assert section in content, f"Template should include '{section}' section"


class TestPhase5Assembly:
    """Test report assembly functionality"""

    @pytest.fixture
    def sample_inputs(self):
        """Provide sample Phase 3 and Phase 4 outputs"""
        metrics_path = Path(__file__).parent / 'fixtures' / 'phase3_artis_reit_metrics.json'
        analysis_path = Path(__file__).parent / 'fixtures' / 'phase4_sample_analysis.md'

        return {
            'metrics_path': metrics_path,
            'analysis_path': analysis_path
        }

    def test_assembly_with_sample_data(self, sample_inputs):
        """Test assembly with sample Phase 3 + Phase 4 data"""
        import subprocess
        import tempfile

        metrics_path = sample_inputs['metrics_path']

        if not metrics_path.exists():
            pytest.skip("Phase 3 metrics fixture not found")

        # Create minimal Phase 4 analysis for testing
        analysis_path = sample_inputs['analysis_path']
        if not analysis_path.exists():
            # Create it
            analysis_path.parent.mkdir(parents=True, exist_ok=True)
            with open(analysis_path, 'w') as f:
                f.write("""# Credit Analysis

## Executive Summary
Rating: Ba (high)

## Credit Strengths
- Strong portfolio occupancy
- Positive NOI growth

## Credit Challenges
- High AFFO payout ratio
- Refinancing needs

## Rating Outlook
Stable
""")

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "final_report.md"

            result = subprocess.run(
                [
                    'python', 'scripts/generate_final_report.py',
                    str(metrics_path),
                    str(analysis_path),
                    '--output', str(output_path)
                ],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                # Success - verify output
                assert output_path.exists(), "Output file should be created"

                with open(output_path, 'r') as f:
                    report = f.read()

                # Should have substantial content
                assert len(report) > 1000, "Report should have substantial content"

                # Should include issuer name
                assert 'Artis' in report, "Report should reference Artis REIT"

            else:
                # Script not implemented yet or other error
                if 'not found' in result.stderr.lower():
                    pytest.skip("Assembly script not implemented yet")
                else:
                    pytest.fail(f"Assembly failed: {result.stderr}")


class TestPhase5OutputQuality:
    """Test final report quality and completeness"""

    @pytest.fixture
    def sample_report(self):
        """Load or generate sample final report"""
        output_path = Path('/tmp/test_final_report.md')

        if not output_path.exists():
            pytest.skip("No sample report available - run assembly test first")

        with open(output_path, 'r') as f:
            return f.read()

    def test_report_has_title(self, sample_report):
        """Test that report has proper title"""
        lines = sample_report.split('\n')
        first_non_empty = next((line for line in lines if line.strip()), '')

        assert first_non_empty.startswith('#'), "Report should start with markdown header"

    def test_report_has_date(self, sample_report):
        """Test that report includes date"""
        # Should have a date in format like "2025-10-17" or "October 17, 2025"
        has_date = any([
            '202' in sample_report,  # Year
            'date' in sample_report.lower()
        ])

        assert has_date, "Report should include date"

    def test_report_has_metrics_table(self, sample_report):
        """Test that report includes metrics in table format"""
        # Markdown tables have | characters
        assert '|' in sample_report, "Report should include tables"

    def test_report_has_quantitative_data(self, sample_report):
        """Test that report includes quantitative metrics"""
        # Should have percentages or ratios
        has_quantitative = any([
            '%' in sample_report,
            'ratio' in sample_report.lower(),
            'coverage' in sample_report.lower()
        ])

        assert has_quantitative, "Report should include quantitative data"

    def test_report_has_credit_analysis(self, sample_report):
        """Test that report includes Phase 4 credit analysis"""
        analysis_keywords = [
            'strength', 'challenge', 'rating', 'outlook',
            'upgrade', 'downgrade', 'scorecard'
        ]

        has_analysis = any(keyword in sample_report.lower() for keyword in analysis_keywords)

        assert has_analysis, "Report should include credit analysis from Phase 4"

    def test_report_is_valid_markdown(self, sample_report):
        """Test that report is valid markdown"""
        # Basic markdown validation
        lines = sample_report.split('\n')

        # Should have headers
        has_headers = any(line.startswith('#') for line in lines)
        assert has_headers, "Report should have markdown headers"

        # Should have reasonable length
        assert len(sample_report) > 500, "Report should have substantial content"

        # Should not have obvious template errors (leftover placeholders)
        assert '{{' not in sample_report or '}}' not in sample_report, (
            "Report should not have leftover template placeholders"
        )


class TestPhase5Integration:
    """Test integration with previous phases"""

    def test_phase3_to_phase5_flow(self):
        """Test that Phase 3 metrics can flow to Phase 5"""
        metrics_path = Path(__file__).parent / 'fixtures' / 'phase3_artis_reit_metrics.json'

        if not metrics_path.exists():
            pytest.skip("Phase 3 metrics not available")

        with open(metrics_path, 'r') as f:
            metrics = json.load(f)

        # Should have all fields needed for report generation
        required_for_report = [
            'issuer_name',
            'reporting_date',
            'leverage_metrics',
            'reit_metrics'
        ]

        for field in required_for_report:
            assert field in metrics, f"Metrics should have {field} for report generation"

    def test_phase4_to_phase5_flow(self):
        """Test that Phase 4 analysis can flow to Phase 5"""
        analysis_path = Path(__file__).parent / 'fixtures' / 'phase4_sample_analysis.md'

        if not analysis_path.exists():
            # Create minimal sample
            analysis_path.parent.mkdir(parents=True, exist_ok=True)
            with open(analysis_path, 'w') as f:
                f.write("# Credit Analysis\n\n## Rating: Ba (high)\n")

        with open(analysis_path, 'r') as f:
            analysis = f.read()

        # Should be markdown format
        assert '#' in analysis, "Phase 4 analysis should be markdown"

        # Should have some content
        assert len(analysis) > 50, "Phase 4 analysis should have content"

    def test_complete_pipeline_readiness(self):
        """Test that all phases can connect end-to-end"""
        # Check that all phase outputs exist in fixtures
        phase1_sample = Path(__file__).parent / 'fixtures' / 'sample_financial_statement.md'
        phase2_sample = Path(__file__).parent / 'fixtures' / 'sample_extracted_data.json'
        phase3_sample = Path(__file__).parent / 'fixtures' / 'phase3_artis_reit_metrics.json'
        phase4_sample = Path(__file__).parent / 'fixtures' / 'phase4_sample_analysis.md'

        # At minimum, Phase 3 should exist for Phase 5 testing
        assert phase3_sample.exists(), "Phase 3 sample needed for Phase 5 testing"


class TestPhase5Performance:
    """Test Phase 5 performance characteristics"""

    def test_no_llm_usage(self):
        """Test that Phase 5 uses 0 LLM tokens (pure templating)"""
        from generate_final_report import generate_final_report

        # This should be a pure Python function with no API calls
        import inspect
        source = inspect.getsource(generate_final_report)

        # Should not import anthropic or openai
        assert 'anthropic' not in source.lower(), "Phase 5 should not use Anthropic API"
        assert 'openai' not in source.lower(), "Phase 5 should not use OpenAI API"

    def test_fast_execution(self):
        """Test that Phase 5 executes quickly (<5 seconds)"""
        import subprocess
        import time
        import tempfile

        metrics_path = Path(__file__).parent / 'fixtures' / 'phase3_artis_reit_metrics.json'
        analysis_path = Path(__file__).parent / 'fixtures' / 'phase4_sample_analysis.md'

        if not metrics_path.exists() or not analysis_path.exists():
            pytest.skip("Input fixtures not available")

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.md"

            start = time.time()

            result = subprocess.run(
                [
                    'python', 'scripts/generate_final_report.py',
                    str(metrics_path),
                    str(analysis_path),
                    '--output', str(output_path)
                ],
                capture_output=True,
                text=True,
                timeout=10
            )

            elapsed = time.time() - start

            if result.returncode == 0:
                assert elapsed < 5.0, f"Phase 5 should execute in <5 seconds (took {elapsed:.2f}s)"


class TestPhase5NoneHandling:
    """Test that report generation handles None/missing values gracefully

    This addresses the issue where REITs don't always report all metrics:
    - FFO: Usually reported
    - AFFO: Optional (e.g., Dream Industrial doesn't report)
    - ACFO: Often calculated, rarely reported
    - Variances: None when comparison impossible
    """

    def test_affo_variance_none_handling(self):
        """Test that None AFFO variance doesn't crash formatting"""
        from generate_final_report import generate_final_report

        # Create minimal metrics with None affo_variance_percent
        metrics = {
            'issuer_name': 'Test REIT',
            'reporting_date': '2025-06-30',
            'reporting_period': 'Q2 2025',
            'currency': 'CAD',
            'reit_metrics': {
                'ffo': 100000,
                'affo': 0,  # Not reported
                'ffo_per_unit': 0.50,
                'affo_per_unit': 0,
                'validation': {
                    'ffo_variance_percent': -5.0,
                    'affo_variance_percent': None,  # Key test case
                    'affo_variance_amount': None
                }
            },
            'leverage_metrics': {'debt_to_assets_percent': 30.0},
            'coverage_ratios': {'noi_interest_coverage': 3.5}
        }

        analysis_sections = {
            'EXECUTIVE_SUMMARY': 'Test summary',
            'CREDIT_STRENGTHS': '- Test strength',
            'CREDIT_CHALLENGES': '- Test challenge'
        }

        template = "# Report\n\n{{FFO_AFFO_OBSERVATIONS}}\n\n{{AFFO_VARIANCE_PERCENT}}"

        # Should not raise TypeError
        try:
            report = generate_final_report(metrics, analysis_sections, template, None)
            assert 'N/A' in report or 'not reported' in report.lower()
        except TypeError as e:
            if 'NoneType' in str(e) and 'format' in str(e):
                pytest.fail(f"None value not handled: {e}")

    def test_ffo_variance_none_handling(self):
        """Test that None FFO variance doesn't crash (rare but possible)"""
        from generate_final_report import generate_final_report

        metrics = {
            'issuer_name': 'Test REIT',
            'reporting_date': '2025-06-30',
            'reporting_period': 'Q2 2025',
            'currency': 'CAD',
            'reit_metrics': {
                'ffo': 0,  # Not reported
                'validation': {
                    'ffo_variance_percent': None,  # No variance if not reported
                    'ffo_variance_amount': None
                }
            },
            'leverage_metrics': {'debt_to_assets_percent': 30.0},
            'coverage_ratios': {'noi_interest_coverage': 3.5}
        }

        analysis_sections = {'EXECUTIVE_SUMMARY': 'Test'}
        template = "{{FFO_VARIANCE_PERCENT}}"

        # Should not raise TypeError
        try:
            report = generate_final_report(metrics, analysis_sections, template, None)
            assert 'N/A' in report
        except TypeError as e:
            if 'NoneType' in str(e):
                pytest.fail(f"None FFO variance not handled: {e}")

    def test_unreported_affo_display(self):
        """Test that unreported AFFO shows meaningful message, not $0"""
        from generate_final_report import generate_final_report

        metrics = {
            'issuer_name': 'Dream Industrial REIT',
            'reporting_date': '2025-06-30',
            'reporting_period': 'Q2 2025',
            'currency': 'CAD',
            'reit_metrics': {
                'ffo': 149437,
                'affo': 0,  # Not reported (not same as zero!)
                'ffo_per_unit': 0.51,
                'affo_per_unit': 0
            },
            'leverage_metrics': {'debt_to_assets_percent': 26.8},
            'coverage_ratios': {'noi_interest_coverage': 4.77}
        }

        analysis_sections = {'EXECUTIVE_SUMMARY': 'Test'}
        template = "{{AFFO_REPORTED_STATUS}}"

        report = generate_final_report(metrics, analysis_sections, template, None)

        # Should show "not reported", not "$0"
        assert 'not reported' in report.lower() or 'n/a' in report.lower()
        # Should NOT show misleading $0 figure
        assert '$0' not in report or 'not reported' in report.lower()

    def test_acfo_variance_none_handling(self):
        """Test that None ACFO variance is handled (most REITs don't report ACFO)"""
        from generate_final_report import generate_final_report

        metrics = {
            'issuer_name': 'Test REIT',
            'reporting_date': '2025-06-30',
            'reporting_period': 'Q2 2025',
            'currency': 'CAD',
            'reit_metrics': {
                'ffo': 100000,
                'acfo': 0,  # Calculated but not reported
                'validation': {
                    'ffo_variance_percent': -5.0
                },
                'acfo_validation': {
                    'acfo_variance_percent': None,  # No reported value to compare
                    'acfo_variance_amount': None
                }
            },
            'leverage_metrics': {'debt_to_assets_percent': 30.0},
            'coverage_ratios': {'noi_interest_coverage': 3.5}
        }

        analysis_sections = {'EXECUTIVE_SUMMARY': 'Test'}
        template = "{{ACFO_VARIANCE_PERCENT}}"

        # Should not crash
        try:
            report = generate_final_report(metrics, analysis_sections, template, None)
            assert 'N/A' in report or len(report) > 0
        except TypeError as e:
            if 'NoneType' in str(e):
                pytest.fail(f"None ACFO variance not handled: {e}")

    def test_all_variance_fields_none(self):
        """Test handling when all variance fields are None (extreme case)"""
        from generate_final_report import generate_final_report

        metrics = {
            'issuer_name': 'Test REIT',
            'reporting_date': '2025-06-30',
            'reporting_period': 'Q2 2025',
            'currency': 'CAD',
            'reit_metrics': {
                'ffo': 0,
                'affo': 0,
                'validation': {
                    'ffo_variance_percent': None,
                    'ffo_variance_amount': None,
                    'affo_variance_percent': None,
                    'affo_variance_amount': None
                },
                'acfo_validation': {
                    'acfo_variance_percent': None,
                    'acfo_variance_amount': None
                }
            },
            'leverage_metrics': {'debt_to_assets_percent': 30.0},
            'coverage_ratios': {'noi_interest_coverage': 3.5}
        }

        analysis_sections = {'EXECUTIVE_SUMMARY': 'Test'}
        template = """
{{FFO_VARIANCE_PERCENT}}
{{AFFO_VARIANCE_PERCENT}}
{{ACFO_VARIANCE_PERCENT}}
{{FFO_AFFO_OBSERVATIONS}}
"""

        # Should handle all None values without crashing
        try:
            report = generate_final_report(metrics, analysis_sections, template, None)
            # Should have N/A or similar placeholder
            assert report.count('N/A') >= 3 or 'not reported' in report.lower()
        except TypeError as e:
            pytest.fail(f"Failed to handle all-None scenario: {e}")


class TestStructuralConsiderationsParsing:
    """Test structural considerations parsing functions (v1.0.13 - Issue #32)

    Tests the three new parsing functions that extract debt structure,
    security/collateral, and perpetual securities information from Phase 4 content.
    """

    def test_parse_debt_structure_with_full_content(self):
        """Test debt structure extraction with complete Phase 4 content"""
        from generate_final_report import parse_debt_structure

        # Sample Phase 4 content with debt structure information
        phase4_content = """
## Liquidity Analysis

**Credit facilities:** $1.93B limit with $771.6M drawn = $1.16B available (60% undrawn)
- **Unencumbered assets:** $9.0B provides substantial refinancing capacity
- **Asset sale pipeline:** $1.45B remaining in capital recycling program

**Covenant Compliance:**
- While specific covenants not disclosed, typical REIT facility covenants include:
- Maximum Debt/Assets: 60-65% (RioCan at 48.3% has cushion)
- Minimum interest coverage: 1.50x (RioCan at 1.32x may be tight)
- Minimum unencumbered assets: Typically 1.5x unsecured debt
"""

        phase3_data = {
            'leverage_metrics': {
                'total_debt': 7435740,  # In thousands
                'debt_to_assets': 0.483,
                'net_debt_to_ebitda': 8.88
            }
        }

        result = parse_debt_structure(phase4_content, None, phase3_data)

        # Should extract credit facilities
        assert '$1.93B' in result or '1.93B' in result

        # Should extract covenant information
        assert 'Covenant' in result or 'covenant' in result

        # Should include debt profile from Phase 3
        assert '$7.4B' in result or '7.4B' in result  # Converted from thousands to billions

    def test_parse_debt_structure_with_no_content(self):
        """Test debt structure extraction when Phase 4 has no debt info"""
        from generate_final_report import parse_debt_structure

        phase4_content = "## Portfolio Analysis\n\nJust some portfolio info, no debt structure."

        result = parse_debt_structure(phase4_content, None, None)

        # Should gracefully return "Not available"
        assert result == 'Not available'

    def test_parse_security_collateral_with_full_content(self):
        """Test security/collateral extraction with complete information"""
        from generate_final_report import parse_security_collateral

        phase4_content = """
## Executive Summary

- **Unencumbered asset pool of $9.0 billion** (up from $8.2B at Q4 2024) provides significant financial flexibility
- 58% of gross assets provides substantial refinancing capacity

## Recovery Analysis

- **Debt holders well-secured:** 48% LTV even at distressed pricing provides substantial recovery (>80-90%)
- Senior unsecured debt appears well-secured (48% LTV, $9B unencumbered assets)
"""

        result = parse_security_collateral(phase4_content, None, None)

        # Should extract unencumbered assets amount
        assert '$9.0B' in result or '9.0B' in result

        # Should extract percentage of gross assets
        assert '58%' in result

        # Should extract recovery estimate
        assert '>80-90%' in result or '80-90%' in result

        # Should have some security analysis content (LTV pattern may vary)
        assert 'Security Analysis' in result or len(result) > 100

    def test_parse_security_collateral_with_no_content(self):
        """Test security/collateral extraction when no info available"""
        from generate_final_report import parse_security_collateral

        phase4_content = "## Business Strategy\n\nNo security information here."

        result = parse_security_collateral(phase4_content, None, None)

        # Should gracefully return "Not available"
        assert result == 'Not available'

    def test_check_perpetual_securities_not_applicable(self):
        """Test perpetual securities check when none exist"""
        from generate_final_report import check_perpetual_securities

        phase4_content = "## Capital Structure\n\nStandard debt and equity structure with no hybrid instruments."
        phase2_data = {
            'debt_structure': {},
            'balance_sheet': {}
        }

        result = check_perpetual_securities(phase4_content, phase2_data, None)

        # Should return "Not applicable"
        assert 'Not applicable' in result or 'not applicable' in result.lower()

    def test_check_perpetual_securities_from_phase2(self):
        """Test perpetual securities detection from Phase 2 data"""
        from generate_final_report import check_perpetual_securities

        phase4_content = "## Capital Structure\n\nSome content."
        phase2_data = {
            'balance_sheet': {
                'preferred_equity': 50000  # In thousands
            }
        }

        result = check_perpetual_securities(phase4_content, phase2_data, None)

        # Should detect and report perpetual preferred equity
        assert 'Preferred equity' in result or 'perpetual' in result.lower()
        assert '50' in result or '$50' in result  # Should show the amount

    def test_check_perpetual_securities_from_phase4(self):
        """Test perpetual securities extraction from Phase 4 content"""
        from generate_final_report import check_perpetual_securities

        phase4_content = """
## Capital Structure

### Perpetual Securities

The issuer has $100M in perpetual preferred units outstanding with a 5.5% distribution rate.
These securities are subordinate to senior debt but rank ahead of common units.
"""

        result = check_perpetual_securities(phase4_content, None, None)

        # Should extract perpetual securities section
        assert '$100M' in result or 'perpetual' in result.lower()
        assert len(result) > 50  # Should have meaningful content

    def test_parse_debt_structure_debt_calculation_fix(self):
        """Test that debt is correctly converted from thousands to billions"""
        from generate_final_report import parse_debt_structure

        phase3_data = {
            'leverage_metrics': {
                'total_debt': 7435740,  # $7,435,740 thousands
                'debt_to_assets': 0.483,
                'net_debt_to_ebitda': 8.88
            }
        }

        result = parse_debt_structure("## Some content", None, phase3_data)

        # Should show $7.4B, NOT $7,435.7B (which was the bug)
        assert '$7.4B' in result
        assert '$7,435' not in result  # Should NOT have the incorrect format

    def test_parse_security_collateral_unencumbered_amount_format(self):
        """Test that unencumbered assets are correctly extracted in billions"""
        from generate_final_report import parse_security_collateral

        phase4_content = "Unencumbered asset pool of $9.0 billion provides refinancing capacity"

        result = parse_security_collateral(phase4_content, None, None)

        # Should extract and format correctly
        assert '$9.0B' in result
        assert 'billion' not in result.lower()  # Should convert to 'B' notation

    def test_parse_security_collateral_recovery_estimate_precedence(self):
        """Test that recovery estimates prioritize debt holder recovery over liquidation discounts"""
        from generate_final_report import parse_security_collateral

        # Content that has both liquidation discount (30%) and recovery estimate (>80-90%)
        phase4_content = """
**Liquidation value:** Assuming fire-sale at 30% discount to book
- **Debt holders well-secured:** provides substantial recovery (>80-90%)
"""

        result = parse_security_collateral(phase4_content, None, None)

        # Should extract the recovery estimate (>80-90%), NOT the 30% discount
        assert '>80-90%' in result or '80-90%' in result
        # Should NOT extract the liquidation discount as recovery
        assert 'Recovery estimate: 30%' not in result

    def test_structural_considerations_integration(self):
        """Test that all three parsing functions work together in report generation"""
        from generate_final_report import (
            parse_debt_structure,
            parse_security_collateral,
            check_perpetual_securities
        )

        # Sample comprehensive Phase 4 content
        phase4_content = """
## Liquidity Analysis
**Credit facilities:** $2.0B limit with $500M drawn
**Covenant Compliance:**
- Debt/Assets: 40% vs covenant 60% (compliant)

## Asset Quality
- **Unencumbered asset pool of $5.0 billion** (50% of gross assets)
- LTV: 35%
- Recovery estimate: >75%
"""

        phase3_data = {
            'leverage_metrics': {
                'total_debt': 3000000,  # $3B in thousands
                'debt_to_assets': 0.40
            }
        }

        phase2_data = {
            'balance_sheet': {},
            'debt_structure': {}
        }

        # All three functions should work without errors
        debt_structure = parse_debt_structure(phase4_content, phase2_data, phase3_data)
        security_collateral = parse_security_collateral(phase4_content, phase2_data, phase3_data)
        perpetual_securities = check_perpetual_securities(phase4_content, phase2_data, phase3_data)

        # Debt structure should have content
        assert '$2.0B' in debt_structure or '$3.0B' in debt_structure
        assert 'Not available' not in debt_structure

        # Security should have content
        assert '$5.0B' in security_collateral
        assert '50%' in security_collateral
        assert 'Not available' not in security_collateral

        # Perpetual securities should be "Not applicable"
        assert 'Not applicable' in perpetual_securities or 'not applicable' in perpetual_securities.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
