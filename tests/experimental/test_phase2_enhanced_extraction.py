#!/usr/bin/env python3
"""
Test Phase 2 Enhanced Extraction (v2.0)

Tests for:
1. extraction_indexer.py - Section indexing and caching
2. section_extractor.py - Validation, progressive enhancement, checkpointing
3. extract_key_metrics_v2.py - Integration workflow
"""

import pytest
import sys
import json
import tempfile
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from extraction_indexer import ExtractionIndexer, SectionLocation
from section_extractor import SectionValidator, SectionExtractor, ExtractionResult


# ============================================================================
# TEST FIXTURES
# ============================================================================

@pytest.fixture
def sample_markdown_files():
    """Sample markdown files for testing"""
    return [
        Path(__file__).parent.parent / 'Issuer_Reports/Artis_REIT/temp/phase1_markdown/ArtisREIT-Q2-25-Consol-FS-Aug-7.md',
        Path(__file__).parent.parent / 'Issuer_Reports/Artis_REIT/temp/phase1_markdown/ArtisREIT-Q2-25-MDA-Aug-7.md'
    ]


@pytest.fixture
def sample_balance_sheet_data():
    """Valid balance sheet data"""
    return {
        'total_assets': 2611435,
        'mortgages_noncurrent': 1141063,
        'mortgages_current': 42234,
        'credit_facilities': 186290,
        'cash': 16639,
        'total_liabilities': 1616178,
        'total_unitholders_equity': 995257
    }


@pytest.fixture
def sample_income_statement_data():
    """Valid income statement data"""
    return {
        'noi': 30729,
        'interest_expense': 16937,
        'revenue': 59082,
        'property_operating_expenses': 20131,
        'realty_taxes': 8222
    }


@pytest.fixture
def sample_ffo_affo_data():
    """Valid FFO/AFFO data"""
    return {
        'ffo': 16956,
        'affo': 8204,
        'ffo_per_unit': 0.17,
        'affo_per_unit': 0.08,
        'distributions_per_unit': 0.15,
        'ffo_payout_ratio': 0.882,
        'affo_payout_ratio': 1.875
    }


@pytest.fixture
def sample_portfolio_data():
    """Valid portfolio data"""
    return {
        'total_properties': 83,
        'total_gla_sf': 9700000,
        'occupancy_rate': 0.878,
        'occupancy_with_commitments': 0.890
    }


# ============================================================================
# EXTRACTION INDEXER TESTS
# ============================================================================

class TestExtractionIndexer:
    """Test suite for ExtractionIndexer"""

    def test_indexer_initialization(self, sample_markdown_files):
        """Test that indexer initializes correctly"""
        if not sample_markdown_files[0].exists():
            pytest.skip("Sample markdown files not available")

        indexer = ExtractionIndexer(sample_markdown_files)

        assert indexer.markdown_files == sample_markdown_files
        assert indexer.index == {}
        assert indexer.checkpoint_dir is None

    def test_create_index(self, sample_markdown_files):
        """Test section index creation"""
        if not sample_markdown_files[0].exists():
            pytest.skip("Sample markdown files not available")

        indexer = ExtractionIndexer(sample_markdown_files)
        index = indexer.create_index()

        # Should find multiple sections
        assert len(index) > 0, "Should find at least one section"

        # Check for expected sections
        expected_sections = ['balance_sheet', 'income_statement', 'ffo_affo', 'portfolio']
        found_sections = [s for s in expected_sections if s in index]

        assert len(found_sections) >= 2, f"Should find at least 2 key sections, found: {found_sections}"

    def test_section_location_properties(self):
        """Test SectionLocation dataclass"""
        location = SectionLocation(
            file=Path("test.md"),
            start_line=100,
            end_line=200,
            section_name="balance_sheet",
            estimated_tokens=2500
        )

        assert location.length == 101  # 200 - 100 + 1
        assert location.start_line == 100
        assert location.end_line == 200

    def test_token_estimation(self, sample_markdown_files):
        """Test that token estimation is reasonable"""
        if not sample_markdown_files[0].exists():
            pytest.skip("Sample markdown files not available")

        indexer = ExtractionIndexer(sample_markdown_files)
        indexer.create_index()

        total_tokens = indexer.get_total_estimated_tokens()

        # Should be significantly less than full file (140K tokens)
        assert total_tokens < 25000, f"Estimated tokens too high: {total_tokens}"
        assert total_tokens > 5000, f"Estimated tokens too low: {total_tokens}"

        # Should save at least 80% vs full file
        savings_pct = (1 - total_tokens / 140000) * 100
        assert savings_pct > 80, f"Token savings too low: {savings_pct:.1f}%"

    def test_index_caching(self, sample_markdown_files):
        """Test index save and load"""
        if not sample_markdown_files[0].exists():
            pytest.skip("Sample markdown files not available")

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_file = Path(tmpdir) / "index.json"

            # Create and save index
            indexer1 = ExtractionIndexer(sample_markdown_files)
            indexer1.create_index(save_to=cache_file)

            assert cache_file.exists(), "Index file should be created"

            # Load index
            indexer2 = ExtractionIndexer.load_index(cache_file, sample_markdown_files)

            assert len(indexer2.index) == len(indexer1.index), "Loaded index should match saved"

    def test_checkpointing_enable(self, sample_markdown_files):
        """Test enabling checkpointing"""
        if not sample_markdown_files[0].exists():
            pytest.skip("Sample markdown files not available")

        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_dir = Path(tmpdir) / "checkpoints"

            indexer = ExtractionIndexer(sample_markdown_files)
            indexer.enable_checkpointing(checkpoint_dir)

            assert indexer.checkpoint_dir == checkpoint_dir
            assert checkpoint_dir.exists()


# ============================================================================
# SECTION VALIDATOR TESTS
# ============================================================================

class TestSectionValidator:
    """Test suite for SectionValidator"""

    def test_balance_sheet_valid(self, sample_balance_sheet_data):
        """Test validation of valid balance sheet"""
        validator = SectionValidator()
        is_valid, errors, warnings = validator.validate_balance_sheet(sample_balance_sheet_data)

        assert is_valid is True, f"Should be valid, errors: {errors}"
        assert len(errors) == 0, "Should have no errors"

    def test_balance_sheet_missing_required_fields(self):
        """Test that missing required fields are caught"""
        validator = SectionValidator()
        incomplete_data = {
            'total_assets': 1000000
            # Missing: mortgages_noncurrent, mortgages_current, credit_facilities, cash
        }

        is_valid, errors, warnings = validator.validate_balance_sheet(incomplete_data)

        assert is_valid is False, "Should be invalid"
        assert len(errors) > 0, "Should have errors"
        assert any('mortgages_noncurrent' in e for e in errors)

    def test_balance_sheet_imbalance_warning(self):
        """Test that balance sheet imbalance triggers warning"""
        validator = SectionValidator()
        imbalanced_data = {
            'total_assets': 1000000,
            'mortgages_noncurrent': 300000,
            'mortgages_current': 100000,
            'credit_facilities': 200000,
            'cash': 50000,
            'total_liabilities': 500000,
            'total_unitholders_equity': 400000  # Only adds to 900k, not 1000k
        }

        is_valid, errors, warnings = validator.validate_balance_sheet(imbalanced_data)

        # Should be valid (no required fields missing) but have warning
        assert is_valid is True
        assert len(warnings) > 0, "Should have warnings about imbalance"
        assert any('balance' in w.lower() for w in warnings)

    def test_income_statement_valid(self, sample_income_statement_data):
        """Test validation of valid income statement"""
        validator = SectionValidator()
        is_valid, errors, warnings = validator.validate_income_statement(sample_income_statement_data)

        assert is_valid is True
        assert len(errors) == 0

    def test_income_statement_noi_exceeds_revenue(self):
        """Test that NOI > Revenue is caught"""
        validator = SectionValidator()
        invalid_data = {
            'noi': 100000,
            'interest_expense': 10000,
            'revenue': 80000  # NOI can't be > revenue!
        }

        is_valid, errors, warnings = validator.validate_income_statement(invalid_data)

        assert is_valid is False
        assert any('cannot exceed' in e.lower() for e in errors)

    def test_income_statement_negative_interest(self):
        """Test that negative interest expense is caught"""
        validator = SectionValidator()
        invalid_data = {
            'noi': 50000,
            'interest_expense': -10000,  # Should be positive
            'revenue': 100000
        }

        is_valid, errors, warnings = validator.validate_income_statement(invalid_data)

        assert is_valid is False
        assert any('positive' in e.lower() for e in errors)

    def test_income_statement_noi_margin_warning(self):
        """Test that unusual NOI margin triggers warning"""
        validator = SectionValidator()
        unusual_data = {
            'noi': 90000,  # 90% margin is unusually high
            'interest_expense': 10000,
            'revenue': 100000
        }

        is_valid, errors, warnings = validator.validate_income_statement(unusual_data)

        assert is_valid is True  # No errors
        assert len(warnings) > 0, "Should warn about unusual margin"

    def test_ffo_affo_valid(self, sample_ffo_affo_data):
        """Test validation of valid FFO/AFFO"""
        validator = SectionValidator()
        is_valid, errors, warnings = validator.validate_ffo_affo(sample_ffo_affo_data)

        assert is_valid is True
        assert len(errors) == 0

    def test_ffo_affo_missing_required(self):
        """Test that missing required FFO/AFFO fields are caught"""
        validator = SectionValidator()
        incomplete_data = {
            'ffo': 16956
            # Missing: affo, ffo_per_unit, affo_per_unit, distributions_per_unit
        }

        is_valid, errors, warnings = validator.validate_ffo_affo(incomplete_data)

        assert is_valid is False
        assert len(errors) >= 4  # Missing 4 required fields

    def test_ffo_affo_high_payout_warning(self):
        """Test that very high payout ratios trigger warnings"""
        validator = SectionValidator()
        high_payout_data = {
            'ffo': 10000,
            'affo': 5000,
            'ffo_per_unit': 0.10,
            'affo_per_unit': 0.05,
            'distributions_per_unit': 0.15,
            'ffo_payout_ratio': 1.5,  # 150% - very high
            'affo_payout_ratio': 3.0  # 300% - unsustainable
        }

        is_valid, errors, warnings = validator.validate_ffo_affo(high_payout_data)

        assert is_valid is True  # No errors
        assert len(warnings) >= 2, "Should warn about both high payout ratios"

    def test_portfolio_valid(self, sample_portfolio_data):
        """Test validation of valid portfolio data"""
        validator = SectionValidator()
        is_valid, errors, warnings = validator.validate_portfolio(sample_portfolio_data)

        assert is_valid is True
        assert len(errors) == 0

    def test_portfolio_occupancy_as_percentage(self):
        """Test that occupancy as percentage (not decimal) is caught"""
        validator = SectionValidator()
        wrong_format_data = {
            'total_properties': 83,
            'total_gla_sf': 9700000,
            'occupancy_rate': 87.8  # Should be 0.878!
        }

        is_valid, errors, warnings = validator.validate_portfolio(wrong_format_data)

        assert is_valid is False
        assert any('between 0 and 1' in e.lower() for e in errors)

    def test_portfolio_low_occupancy_warning(self):
        """Test that low occupancy triggers warning"""
        validator = SectionValidator()
        low_occupancy_data = {
            'total_properties': 83,
            'total_gla_sf': 9700000,
            'occupancy_rate': 0.65  # 65% is low
        }

        is_valid, errors, warnings = validator.validate_portfolio(low_occupancy_data)

        assert is_valid is True
        assert len(warnings) > 0, "Should warn about low occupancy"


# ============================================================================
# SECTION EXTRACTOR TESTS
# ============================================================================

class TestSectionExtractor:
    """Test suite for SectionExtractor"""

    def test_extractor_initialization(self, sample_markdown_files):
        """Test that extractor initializes correctly"""
        if not sample_markdown_files[0].exists():
            pytest.skip("Sample markdown files not available")

        indexer = ExtractionIndexer(sample_markdown_files)
        indexer.create_index()

        extractor = SectionExtractor(indexer)

        assert extractor.indexer == indexer
        assert extractor.validator is not None
        assert extractor.results == {}

    def test_read_section(self, sample_markdown_files):
        """Test reading a section from markdown file"""
        if not sample_markdown_files[0].exists():
            pytest.skip("Sample markdown files not available")

        indexer = ExtractionIndexer(sample_markdown_files)
        indexer.create_index()

        if 'balance_sheet' not in indexer.index:
            pytest.skip("Balance sheet section not found in index")

        extractor = SectionExtractor(indexer)
        location = indexer.index['balance_sheet']

        content = extractor.read_section(location)

        assert len(content) > 0, "Should read non-empty content"
        assert 'assets' in content.lower() or 'balance' in content.lower()

    def test_read_section_with_expansion(self, sample_markdown_files):
        """Test reading section with progressive enhancement"""
        if not sample_markdown_files[0].exists():
            pytest.skip("Sample markdown files not available")

        indexer = ExtractionIndexer(sample_markdown_files)
        indexer.create_index()

        if 'balance_sheet' not in indexer.index:
            pytest.skip("Balance sheet section not found in index")

        extractor = SectionExtractor(indexer)
        location = indexer.index['balance_sheet']

        # Read without expansion
        content_normal = extractor.read_section(location)

        # Read with expansion
        content_expanded = extractor.read_section(location, expand_by=50)

        assert len(content_expanded) > len(content_normal), "Expanded content should be longer"

    def test_extraction_result_dataclass(self):
        """Test ExtractionResult dataclass"""
        result = ExtractionResult(
            section_name="balance_sheet",
            data={'total_assets': 1000000},
            is_valid=True,
            errors=[],
            warnings=["Some warning"],
            expanded=False
        )

        assert result.section_name == "balance_sheet"
        assert result.is_valid is True
        assert len(result.warnings) == 1


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestEnhancedExtractionIntegration:
    """Integration tests for the complete enhanced extraction workflow"""

    def test_end_to_end_indexing(self, sample_markdown_files):
        """Test complete indexing workflow"""
        if not sample_markdown_files[0].exists():
            pytest.skip("Sample markdown files not available")

        # Step 1: Create indexer
        indexer = ExtractionIndexer(sample_markdown_files)

        # Step 2: Create index
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_file = Path(tmpdir) / "index.json"
            index = indexer.create_index(save_to=cache_file)

            # Verify index created
            assert len(index) > 0
            assert cache_file.exists()

            # Step 3: Calculate token savings
            total_tokens = indexer.get_total_estimated_tokens()
            savings = (1 - total_tokens / 140000) * 100

            # Should achieve significant savings
            assert savings > 80, f"Should save >80% tokens, got {savings:.1f}%"

    def test_checkpoint_workflow(self, sample_markdown_files):
        """Test checkpointing workflow"""
        if not sample_markdown_files[0].exists():
            pytest.skip("Sample markdown files not available")

        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_dir = Path(tmpdir) / "checkpoints"

            # Create indexer with checkpointing
            indexer = ExtractionIndexer(sample_markdown_files)
            indexer.create_index()
            indexer.enable_checkpointing(checkpoint_dir)

            # Save a checkpoint
            test_data = {'test': 'data'}
            indexer.save_checkpoint('balance_sheet', test_data)

            # Verify checkpoint saved
            assert (checkpoint_dir / 'balance_sheet.json').exists()

            # Load checkpoint
            loaded_data = indexer.load_checkpoint('balance_sheet')
            assert loaded_data == test_data

            # Clear checkpoints
            indexer.clear_checkpoints()
            assert not (checkpoint_dir / 'balance_sheet.json').exists()


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

class TestPerformance:
    """Performance benchmarks for enhanced extraction"""

    def test_indexing_speed(self, sample_markdown_files):
        """Test that indexing completes in <2 seconds"""
        if not sample_markdown_files[0].exists():
            pytest.skip("Sample markdown files not available")

        import time

        indexer = ExtractionIndexer(sample_markdown_files)

        start = time.time()
        indexer.create_index()
        elapsed = time.time() - start

        # Should complete in <2 seconds
        assert elapsed < 2.0, f"Indexing took {elapsed:.2f}s, should be <2s"

    def test_token_efficiency(self, sample_markdown_files):
        """Test that token usage is <20K"""
        if not sample_markdown_files[0].exists():
            pytest.skip("Sample markdown files not available")

        indexer = ExtractionIndexer(sample_markdown_files)
        indexer.create_index()

        total_tokens = indexer.get_total_estimated_tokens()

        # Should use <20K tokens
        assert total_tokens < 20000, f"Token usage {total_tokens} exceeds 20K"

        # Should save >85% vs full file
        savings = (1 - total_tokens / 140000) * 100
        assert savings > 85, f"Token savings {savings:.1f}% below target 85%"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
