#!/usr/bin/env python3
"""
Test Phase 4: Slim Agent Credit Analysis

These tests ensure:
1. Slim agent profile exists and is properly configured
2. Knowledge base is minimal (<10,000 tokens estimated)
3. Agent can be invoked with metrics JSON
4. Output includes required credit assessment sections
5. Agent uses on-demand knowledge loading (not preloading everything)
"""

import pytest
import sys
import json
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))


class TestPhase4AgentProfile:
    """Test that slim agent profile is correctly configured"""

    def test_slim_agent_file_exists(self):
        """Test that slim agent profile file exists"""
        agent_path = Path("/workspaces/geniusstrategies/.claude/agents/domain_expert/issuer_due_diligence_expert_slim.md")

        assert agent_path.exists(), f"Slim agent profile not found at {agent_path}"

    def test_slim_agent_has_yaml_frontmatter(self):
        """Test that slim agent has proper YAML frontmatter"""
        agent_path = Path("/workspaces/geniusstrategies/.claude/agents/domain_expert/issuer_due_diligence_expert_slim.md")

        if not agent_path.exists():
            pytest.skip("Slim agent profile not created yet")

        with open(agent_path, 'r') as f:
            content = f.read()

        # Should start with YAML frontmatter
        assert content.startswith('---'), "Agent file should start with YAML frontmatter"
        assert 'name:' in content, "Agent should have 'name' in frontmatter"
        assert 'issuer_due_diligence_expert_slim' in content, "Agent name should include 'slim'"
        assert 'description:' in content, "Agent should have description"

    def test_slim_agent_size_is_minimal(self):
        """Test that slim agent file is small (<15KB, roughly <10K tokens)"""
        agent_path = Path("/workspaces/geniusstrategies/.claude/agents/domain_expert/issuer_due_diligence_expert_slim.md")

        if not agent_path.exists():
            pytest.skip("Slim agent profile not created yet")

        file_size = agent_path.stat().st_size

        # Target: <15KB (roughly <10K tokens)
        max_size = 15 * 1024  # 15KB
        assert file_size < max_size, (
            f"Slim agent file too large: {file_size} bytes (target: <{max_size} bytes). "
            f"Should use on-demand knowledge loading, not inline everything."
        )

    def test_slim_agent_references_knowledge_files(self):
        """Test that slim agent uses on-demand knowledge loading"""
        agent_path = Path("/workspaces/geniusstrategies/.claude/agents/domain_expert/issuer_due_diligence_expert_slim.md")

        if not agent_path.exists():
            pytest.skip("Slim agent profile not created yet")

        with open(agent_path, 'r') as f:
            content = f.read()

        # Should reference knowledge base files for on-demand loading
        assert '.claude/knowledge/' in content.lower() or 'read' in content.lower(), (
            "Slim agent should reference knowledge base files for on-demand loading"
        )


class TestPhase4KnowledgeBase:
    """Test that knowledge base is minimal and properly structured"""

    def test_slim_knowledge_base_exists(self):
        """Test that slim knowledge base directory exists"""
        kb_path = Path("/workspaces/geniusstrategies/.claude/knowledge/domain-experts/issuer_due_diligence_expert_slim/")

        # May not exist yet - that's ok, full knowledge base can be used with selective loading
        if kb_path.exists():
            # If it exists, check structure
            assert kb_path.is_dir(), "Knowledge base should be a directory"

    def test_knowledge_base_size_is_reasonable(self):
        """Test that knowledge base is not massive"""
        kb_path = Path("/workspaces/geniusstrategies/.claude/knowledge/domain-experts/issuer_due_diligence_expert_slim/")

        if not kb_path.exists():
            pytest.skip("Slim knowledge base not created yet - may use selective loading from full KB")

        total_size = 0
        for file in kb_path.rglob("*.md"):
            total_size += file.stat().st_size

        # Target: <40KB total (roughly <25K tokens estimated)
        max_size = 40 * 1024
        if total_size > max_size:
            pytest.fail(
                f"Knowledge base too large: {total_size} bytes (target: <{max_size} bytes). "
                f"Use on-demand loading instead of inline content."
            )


class TestPhase4Orchestration:
    """Test Phase 4 orchestration script"""

    def test_orchestration_script_exists(self):
        """Test that Phase 4 orchestration script exists"""
        script_path = Path("/workspaces/geniusstrategies/Issuer_Reports/scripts/analyze_credit_with_agent.py")

        assert script_path.exists(), (
            f"Phase 4 orchestration script not found at {script_path}. "
            f"This script should invoke the slim agent with metrics JSON."
        )

    def test_orchestration_script_requires_input(self):
        """Test that orchestration script requires input metrics"""
        import subprocess

        result = subprocess.run(
            ['python', 'scripts/analyze_credit_with_agent.py'],
            capture_output=True,
            text=True
        )

        # Should fail with usage error (exit code 2) or require arguments
        assert result.returncode != 0, "Script should require input arguments"

    def test_orchestration_with_sample_metrics(self):
        """Test orchestration with sample metrics fixture"""
        import subprocess
        import tempfile

        fixture_path = Path(__file__).parent / 'fixtures' / 'phase3_artis_reit_metrics.json'

        if not fixture_path.exists():
            pytest.skip("Sample metrics fixture not found")

        script_path = Path("scripts/analyze_credit_with_agent.py")
        if not script_path.exists():
            pytest.skip("Orchestration script not implemented yet")

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_credit_analysis.md"

            result = subprocess.run(
                [
                    'python', str(script_path),
                    str(fixture_path),
                    '--output', str(output_path)
                ],
                capture_output=True,
                text=True,
                timeout=30  # 30 second timeout
            )

            # Script should succeed (exit 0) - it prepares for agent invocation
            assert result.returncode == 0, f"Script failed: {result.stderr}"

            # Should create prompt file (not output file - that requires agent invocation)
            prompt_path = output_path.parent / "phase4_agent_prompt.txt"
            assert prompt_path.exists(), f"Prompt file should be created at {prompt_path}"

            with open(prompt_path, 'r') as f:
                prompt = f.read()

            # Prompt should have substantial content
            assert len(prompt) > 500, "Prompt should have substantial content"

            # Prompt should reference the issuer
            assert 'Artis' in prompt, "Prompt should reference Artis REIT"

            # Prompt should include metrics
            assert 'leverage_metrics' in prompt or 'debt_to_assets' in prompt.lower(), (
                "Prompt should include metrics"
            )


class TestPhase4OutputQuality:
    """Test that Phase 4 output has required sections"""

    @pytest.fixture
    def sample_output(self):
        """Generate or load sample credit analysis output"""
        output_path = Path('/tmp/test_credit_analysis.md')

        if not output_path.exists():
            pytest.skip("No sample output available - run orchestration test first")

        with open(output_path, 'r') as f:
            return f.read()

    def test_output_has_credit_strengths(self, sample_output):
        """Test that output includes credit strengths section"""
        assert 'strength' in sample_output.lower(), (
            "Credit analysis should include strengths section"
        )

    def test_output_has_credit_challenges(self, sample_output):
        """Test that output includes credit challenges section"""
        assert 'challenge' in sample_output.lower() or 'weakness' in sample_output.lower(), (
            "Credit analysis should include challenges/weaknesses section"
        )

    def test_output_has_rating_assessment(self, sample_output):
        """Test that output includes rating assessment"""
        rating_keywords = ['rating', 'scorecard', 'credit opinion', 'assessment']
        has_rating = any(keyword in sample_output.lower() for keyword in rating_keywords)

        assert has_rating, "Credit analysis should include rating assessment"

    def test_output_has_issuer_identification(self, sample_output):
        """Test that output includes issuer name"""
        # Should reference the issuer (Artis REIT in our test case)
        assert 'artis' in sample_output.lower() or 'issuer' in sample_output, (
            "Credit analysis should identify the issuer"
        )

    def test_output_references_metrics(self, sample_output):
        """Test that output references the calculated metrics"""
        metric_keywords = [
            'leverage', 'debt', 'coverage', 'ffo', 'affo',
            'occupancy', 'noi', 'interest'
        ]

        references_metrics = any(keyword in sample_output.lower() for keyword in metric_keywords)

        assert references_metrics, (
            "Credit analysis should reference the calculated metrics"
        )


class TestPhase4Integration:
    """Integration tests for Phase 4"""

    def test_phase3_to_phase4_flow(self):
        """Test that Phase 3 output can feed into Phase 4"""
        # Phase 3 output
        phase3_output = Path(__file__).parent / 'fixtures' / 'phase3_artis_reit_metrics.json'

        if not phase3_output.exists():
            pytest.skip("Phase 3 fixture not available")

        # Load and validate it's proper JSON
        with open(phase3_output, 'r') as f:
            metrics = json.load(f)

        # Should have required fields for Phase 4
        required_fields = [
            'issuer_name',
            'reporting_date',
            'leverage_metrics',
            'reit_metrics',
            'coverage_ratios'
        ]

        for field in required_fields:
            assert field in metrics, f"Phase 3 output missing required field: {field}"

    def test_phase4_output_is_markdown(self):
        """Test that Phase 4 produces valid markdown"""
        output_path = Path('/tmp/test_credit_analysis.md')

        if not output_path.exists():
            pytest.skip("Phase 4 output not available")

        with open(output_path, 'r') as f:
            content = f.read()

        # Basic markdown validation
        # Should have headers
        assert '#' in content, "Markdown should have headers"

        # Should be readable text
        assert len(content.split()) > 100, "Output should have substantial text content"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
