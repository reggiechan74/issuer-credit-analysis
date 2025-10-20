#!/usr/bin/env python3
"""
Phase 2 Enhancement: Section-by-Section Extraction with Validation

Implements targeted extraction with:
1. Read only indexed sections (minimal tokens)
2. Validate each section immediately
3. Progressive enhancement (expand if data missing)
4. Checkpointing (resume on failure)

This module works with ExtractionIndexer to read and extract specific sections.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field

from extraction_indexer import ExtractionIndexer, SectionLocation


@dataclass
class ExtractionResult:
    """Result of extracting a section"""
    section_name: str
    data: dict
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    expanded: bool = False  # True if progressive enhancement was used


class SectionValidator:
    """Validates extracted data for each section"""

    @staticmethod
    def validate_balance_sheet(data: dict) -> Tuple[bool, List[str], List[str]]:
        """
        Validate balance sheet data

        Returns:
            (is_valid, errors, warnings)
        """
        errors = []
        warnings = []

        # Required fields
        required = [
            'total_assets', 'mortgages_noncurrent', 'mortgages_current',
            'credit_facilities', 'cash'
        ]

        for field in required:
            if field not in data:
                errors.append(f"Missing required field: {field}")

        # Validation checks
        if 'total_assets' in data and 'total_liabilities' in data and 'total_unitholders_equity' in data:
            assets = data['total_assets']
            liabilities = data['total_liabilities']
            equity = data['total_unitholders_equity']

            # Check if balance sheet balances (within 1% tolerance)
            if abs(assets - (liabilities + equity)) / assets > 0.01:
                warnings.append(
                    f"Balance sheet may not balance: Assets={assets}, "
                    f"Liabilities+Equity={liabilities + equity}"
                )

        is_valid = len(errors) == 0
        return is_valid, errors, warnings

    @staticmethod
    def validate_income_statement(data: dict) -> Tuple[bool, List[str], List[str]]:
        """Validate income statement data"""
        errors = []
        warnings = []

        # Required fields
        required = ['noi', 'interest_expense', 'revenue']

        for field in required:
            if field not in data:
                errors.append(f"Missing required field: {field}")

        # Validation checks
        if 'revenue' in data and 'noi' in data:
            if data['noi'] > data['revenue']:
                errors.append(f"NOI ({data['noi']}) cannot exceed Revenue ({data['revenue']})")

            # NOI margin check (typical REIT: 40-70%)
            noi_margin = data['noi'] / data['revenue']
            if noi_margin < 0.30 or noi_margin > 0.80:
                warnings.append(
                    f"NOI margin {noi_margin:.1%} is outside typical range (40-70%)"
                )

        # Interest expense should be positive
        if 'interest_expense' in data:
            if data['interest_expense'] < 0:
                errors.append("Interest expense should be positive")

        is_valid = len(errors) == 0
        return is_valid, errors, warnings

    @staticmethod
    def validate_ffo_affo(data: dict) -> Tuple[bool, List[str], List[str]]:
        """Validate FFO/AFFO data"""
        errors = []
        warnings = []

        # Required fields
        required = ['ffo', 'affo', 'ffo_per_unit', 'affo_per_unit', 'distributions_per_unit']

        for field in required:
            if field not in data:
                errors.append(f"Missing required field: {field}")

        # Validation checks
        if 'ffo' in data and 'affo' in data:
            if data['affo'] > data['ffo']:
                warnings.append(f"AFFO ({data['affo']}) typically should be < FFO ({data['ffo']})")

        # Payout ratio checks
        if 'ffo_payout_ratio' in data:
            if data['ffo_payout_ratio'] > 1.5:
                warnings.append(f"FFO payout ratio {data['ffo_payout_ratio']:.1%} is very high")

        if 'affo_payout_ratio' in data:
            if data['affo_payout_ratio'] > 2.0:
                warnings.append(f"AFFO payout ratio {data['affo_payout_ratio']:.1%} is unsustainable")

        is_valid = len(errors) == 0
        return is_valid, errors, warnings

    @staticmethod
    def validate_portfolio(data: dict) -> Tuple[bool, List[str], List[str]]:
        """Validate portfolio data"""
        errors = []
        warnings = []

        # Required fields
        required = ['total_properties', 'total_gla_sf', 'occupancy_rate']

        for field in required:
            if field not in data:
                errors.append(f"Missing required field: {field}")

        # Occupancy validation
        if 'occupancy_rate' in data:
            occ = data['occupancy_rate']
            if occ < 0 or occ > 1:
                errors.append(f"Occupancy rate {occ} should be between 0 and 1 (not percentage)")
            elif occ < 0.70:
                warnings.append(f"Low occupancy rate: {occ:.1%}")

        is_valid = len(errors) == 0
        return is_valid, errors, warnings


class SectionExtractor:
    """
    Extracts data from indexed sections with validation and progressive enhancement
    """

    def __init__(self, indexer: ExtractionIndexer):
        """
        Initialize extractor with an indexer

        Args:
            indexer: ExtractionIndexer with section locations
        """
        self.indexer = indexer
        self.validator = SectionValidator()
        self.results: Dict[str, ExtractionResult] = {}

    def read_section(self, location: SectionLocation, expand_by: int = 0) -> str:
        """
        Read a section from markdown file

        Args:
            location: Section location
            expand_by: Number of additional lines to read (progressive enhancement)

        Returns:
            Section content as string
        """
        try:
            with open(location.file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Calculate read range
            start = location.start_line - 1  # 0-indexed
            end = location.end_line + expand_by

            # Read the section
            section_lines = lines[start:end]
            content = ''.join(section_lines)

            return content

        except Exception as e:
            print(f"   ❌ Error reading section {location.section_name}: {e}")
            return ""

    def extract_balance_sheet(self, content: str, progressive: bool = False) -> ExtractionResult:
        """
        Extract balance sheet data from content

        Args:
            content: Section content
            progressive: If True, previously tried and failed

        Returns:
            ExtractionResult with extracted data
        """
        # This is a simplified extractor - in real implementation,
        # Claude Code would parse the content using Read tool
        # For now, return structure for testing
        data = {
            "total_assets": None,
            "mortgages_noncurrent": None,
            "mortgages_current": None,
            "credit_facilities": None,
            "cash": None
        }

        # Validate
        is_valid, errors, warnings = self.validator.validate_balance_sheet(data)

        return ExtractionResult(
            section_name="balance_sheet",
            data=data,
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            expanded=progressive
        )

    def extract_with_progressive_enhancement(
        self,
        section_name: str,
        max_expansions: int = 3
    ) -> ExtractionResult:
        """
        Extract section data with progressive enhancement

        If extraction fails validation, expand read range and retry.

        Args:
            section_name: Name of section to extract
            max_expansions: Maximum number of times to expand read range

        Returns:
            ExtractionResult with extracted data
        """
        if section_name not in self.indexer.index:
            return ExtractionResult(
                section_name=section_name,
                data={},
                is_valid=False,
                errors=[f"Section {section_name} not found in index"]
            )

        location = self.indexer.index[section_name]
        expansion = 0

        for attempt in range(max_expansions + 1):
            # Read section (with expansion if retrying)
            content = self.read_section(location, expand_by=expansion)

            # Extract data (this would call Claude Code in real implementation)
            # For now, create placeholder result
            result = ExtractionResult(
                section_name=section_name,
                data={},
                is_valid=False,
                errors=["Extraction not implemented - placeholder"],
                expanded=(expansion > 0)
            )

            # If valid, we're done
            if result.is_valid:
                # Save checkpoint
                if self.indexer.checkpoint_dir:
                    self.indexer.save_checkpoint(section_name, result.data)
                return result

            # If missing required fields, expand and retry
            if attempt < max_expansions:
                missing_fields = [e for e in result.errors if 'Missing required field' in e]
                if missing_fields:
                    expansion += 50  # Expand by 50 lines
                    print(f"   🔄 Expanding {section_name} by {expansion} lines (attempt {attempt + 2})")
                    continue

            # Can't fix it, return failed result
            return result

        return result

    def extract_all_sections(
        self,
        use_checkpoints: bool = True,
        progressive: bool = True
    ) -> Dict[str, ExtractionResult]:
        """
        Extract all indexed sections

        Args:
            use_checkpoints: If True, load from checkpoints if available
            progressive: If True, use progressive enhancement on failures

        Returns:
            Dictionary of section results
        """
        print("\n📊 Extracting sections...")

        for section_name in self.indexer.index.keys():
            # Check for checkpoint
            if use_checkpoints and self.indexer.checkpoint_dir:
                checkpoint_data = self.indexer.load_checkpoint(section_name)
                if checkpoint_data:
                    print(f"   ✓ {section_name}: Loaded from checkpoint")
                    self.results[section_name] = ExtractionResult(
                        section_name=section_name,
                        data=checkpoint_data,
                        is_valid=True
                    )
                    continue

            # Extract section
            if progressive:
                result = self.extract_with_progressive_enhancement(section_name)
            else:
                location = self.indexer.index[section_name]
                content = self.read_section(location)
                result = ExtractionResult(
                    section_name=section_name,
                    data={},
                    is_valid=False,
                    errors=["Extraction not implemented"]
                )

            self.results[section_name] = result

            # Print status
            status = "✓" if result.is_valid else "❌"
            expanded_msg = " (expanded)" if result.expanded else ""
            print(f"   {status} {section_name}{expanded_msg}")

            if result.errors:
                for error in result.errors:
                    print(f"      ❌ {error}")
            if result.warnings:
                for warning in result.warnings:
                    print(f"      ⚠️  {warning}")

        return self.results

    def assemble_final_json(self) -> dict:
        """
        Assemble final JSON from all section results

        Returns:
            Complete financial data dictionary
        """
        final_data = {
            "issuer_name": "",
            "reporting_date": "",
            "currency": ""
        }

        # Merge all section data
        for section_name, result in self.results.items():
            if result.is_valid:
                final_data[section_name] = result.data

        return final_data


def main():
    """Test the extractor"""
    import sys
    from extraction_indexer import ExtractionIndexer

    if len(sys.argv) < 2:
        print("Usage: python section_extractor.py <markdown_files>...")
        sys.exit(1)

    md_files = [Path(f) for f in sys.argv[1:]]

    # Create indexer and index sections
    indexer = ExtractionIndexer(md_files)
    indexer.create_index()

    # Enable checkpointing
    indexer.enable_checkpointing(Path("temp/checkpoints"))

    # Create extractor
    extractor = SectionExtractor(indexer)

    # Extract all sections
    results = extractor.extract_all_sections(
        use_checkpoints=True,
        progressive=True
    )

    # Show results
    print("\n📊 EXTRACTION SUMMARY")
    print("=" * 60)
    valid_count = sum(1 for r in results.values() if r.is_valid)
    print(f"Sections extracted: {valid_count}/{len(results)}")
    print(f"Total estimated tokens: {indexer.get_total_estimated_tokens():,}")


if __name__ == '__main__':
    main()
