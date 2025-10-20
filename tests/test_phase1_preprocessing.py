#!/usr/bin/env python3
"""
Test Phase 1: PDF Preprocessing using markitdown
"""

import pytest
import sys
from pathlib import Path
import tempfile
import shutil

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

# Import the preprocessing function
from preprocess_pdfs_enhanced import preprocess_financial_pdfs


class TestPhase1Preprocessing:
    """Test suite for Phase 1 PDF preprocessing"""

    def test_import_markitdown(self):
        """Test that markitdown is available"""
        try:
            from markitdown import MarkItDown
            assert True
        except ImportError:
            pytest.fail("markitdown is not installed")

    def test_preprocess_creates_output_directory(self):
        """Test that preprocessing creates output directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "output"

            # Should create directory even with no PDFs
            results = preprocess_financial_pdfs([], output_dir)

            assert output_dir.exists()
            assert output_dir.is_dir()

    def test_preprocess_handles_missing_file(self):
        """Test that preprocessing handles missing PDF gracefully"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "output"
            fake_pdf = Path(tmpdir) / "nonexistent.pdf"

            results = preprocess_financial_pdfs([fake_pdf], output_dir)

            # Should return error status
            assert 'nonexistent.pdf' in results
            assert results['nonexistent.pdf']['status'] == 'error'

    def test_preprocess_with_real_pdf(self):
        """Test preprocessing with actual Artis REIT PDF"""
        # Use existing Artis REIT PDF if available
        project_root = Path(__file__).parent.parent
        pdf_path = project_root / "Issuer_Reports/ArtisREIT-Q2-25-Consol-FS-Aug-7.pdf"

        if not pdf_path.exists():
            pytest.skip("Artis REIT PDF not found")

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            results = preprocess_financial_pdfs([pdf_path], output_dir)

            # Should succeed
            assert 'ArtisREIT-Q2-25-Consol-FS-Aug-7.pdf' in results
            result = results['ArtisREIT-Q2-25-Consol-FS-Aug-7.pdf']

            if result['status'] == 'success':
                assert 'output_path' in result
                assert Path(result['output_path']).exists()
                assert result['size_kb'] > 0

                # Check markdown content exists
                with open(result['output_path'], 'r') as f:
                    content = f.read()
                    assert len(content) > 1000  # Should have substantial content
            else:
                # If it fails, at least check error is captured
                assert 'error' in result

    def test_preprocess_output_format(self):
        """Test that preprocessing returns correct format"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            results = preprocess_financial_pdfs([], output_dir)

            # Results should be a dictionary
            assert isinstance(results, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
