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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
