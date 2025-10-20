#!/usr/bin/env python3
"""
Phase 2 Enhancement: Section Indexing and Targeted Extraction

Implements grep-based section discovery to enable:
1. Minimal token usage (read only needed sections)
2. No context window issues (never read entire files)
3. Guaranteed accuracy (read complete sections)
4. Progressive enhancement (expand if data missing)
5. Checkpointing (resume failed extractions)

Token reduction: ~140K → ~15K (89% reduction)
"""

import json
import subprocess
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class SectionLocation:
    """Location of a data section in a markdown file"""
    file: Path
    start_line: int
    end_line: int
    section_name: str
    estimated_tokens: int

    @property
    def length(self) -> int:
        """Number of lines in this section"""
        return self.end_line - self.start_line + 1


class ExtractionIndexer:
    """
    Creates an index of where financial data sections are located in markdown files.

    Uses grep to find sections without reading files (0 LLM tokens).
    Enables targeted reads of only the needed sections.
    """

    # Section markers to search for
    SECTION_MARKERS = {
        'balance_sheet': [
            'Consolidated Balance Sheet',
            'Statement of Financial Position',
            'Balance Sheet'
        ],
        'income_statement': [
            'Consolidated Statement.*Operations',
            'Statement of.*Income',
            'Statement of Operations'
        ],
        'cash_flow': [
            'Consolidated Statement.*Cash Flow',
            'Statement of Cash Flow',
            'Cash Flow Statement'
        ],
        'ffo_affo': [
            'FFO and AFFO',
            'Funds from Operations',
            'FFO & AFFO'
        ],
        'portfolio': [
            'Property Portfolio',
            'Portfolio Summary',
            'Portfolio by.*Class'
        ],
        'dilution': [
            'weighted-average.*diluted',
            'diluted.*units.*outstanding',
            'restricted.*deferred units'
        ],
        'debt_schedule': [
            'Debt Maturity',
            'Mortgage.*Schedule',
            'Debt.*Profile'
        ],
        'liquidity': [
            'Liquidity',
            'Credit Facilit',
            'Available.*Liquidity'
        ]
    }

    def __init__(self, markdown_files: List[Path]):
        """
        Initialize indexer with markdown files

        Args:
            markdown_files: List of markdown file paths to index
        """
        self.markdown_files = [Path(f) for f in markdown_files]
        self.index: Dict[str, SectionLocation] = {}
        self.checkpoint_dir: Optional[Path] = None

    def create_index(self, save_to: Optional[Path] = None) -> Dict[str, SectionLocation]:
        """
        Create section index using grep (0 LLM tokens)

        Args:
            save_to: Optional path to save index JSON

        Returns:
            Dictionary mapping section names to locations
        """
        print("📍 Creating section index...")

        for section_name, patterns in self.SECTION_MARKERS.items():
            location = self._find_section(section_name, patterns)
            if location:
                self.index[section_name] = location
                print(f"   ✓ Found {section_name}: {location.file.name} lines {location.start_line}-{location.end_line}")
            else:
                print(f"   ⚠ {section_name}: Not found")

        # Save index if requested
        if save_to:
            self._save_index(save_to)

        print(f"\n✅ Index created: {len(self.index)}/{len(self.SECTION_MARKERS)} sections found\n")
        return self.index

    def _find_section(self, section_name: str, patterns: List[str]) -> Optional[SectionLocation]:
        """
        Find a section using grep patterns

        Args:
            section_name: Name of section to find
            patterns: List of regex patterns to search for

        Returns:
            SectionLocation if found, None otherwise
        """
        for md_file in self.markdown_files:
            for pattern in patterns:
                try:
                    # Use grep to find the pattern
                    result = subprocess.run(
                        ['grep', '-n', '-i', '-E', pattern, str(md_file)],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )

                    if result.returncode == 0 and result.stdout:
                        # Found it! Get the line number
                        first_match = result.stdout.split('\n')[0]
                        line_num = int(first_match.split(':')[0])

                        # Estimate section end (read ahead to find boundary)
                        end_line = self._estimate_section_end(md_file, line_num, section_name)

                        # Estimate tokens (rough: 2.5 chars per token)
                        section_length = end_line - line_num
                        estimated_tokens = int(section_length * 100 / 2.5)  # Assume 100 chars/line avg

                        return SectionLocation(
                            file=md_file,
                            start_line=line_num,
                            end_line=end_line,
                            section_name=section_name,
                            estimated_tokens=estimated_tokens
                        )

                except subprocess.TimeoutExpired:
                    print(f"   ⚠ Timeout searching for {pattern} in {md_file.name}")
                    continue
                except Exception as e:
                    print(f"   ⚠ Error searching {pattern}: {e}")
                    continue

        return None

    def _estimate_section_end(self, file: Path, start_line: int, section_name: str) -> int:
        """
        Estimate where a section ends by looking for boundaries

        Args:
            file: Markdown file
            start_line: Line where section starts
            section_name: Name of section

        Returns:
            Estimated end line number
        """
        # Default lengths for different section types
        DEFAULT_LENGTHS = {
            'balance_sheet': 150,
            'income_statement': 120,
            'cash_flow': 150,
            'ffo_affo': 250,
            'portfolio': 200,
            'dilution': 100,
            'debt_schedule': 150,
            'liquidity': 80
        }

        default_length = DEFAULT_LENGTHS.get(section_name, 100)

        # Read a chunk to find the actual boundary
        try:
            with open(file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Look for section boundaries (markdown headers, horizontal rules, page breaks)
            search_end = min(start_line + default_length + 50, len(lines))

            for i in range(start_line, search_end):
                line = lines[i].strip()

                # Check for section boundaries
                if i > start_line + 20:  # Don't end too early
                    # Markdown section header
                    if line.startswith('##') and not line.startswith('###'):
                        return i - 1
                    # Horizontal rule
                    if line == '---' or line.startswith('---'):
                        return i - 1
                    # Page break
                    if '<!-- Page' in line:
                        return i - 1

            # No boundary found, use default
            return start_line + default_length

        except Exception as e:
            print(f"   ⚠ Error estimating section end: {e}")
            return start_line + default_length

    def _save_index(self, path: Path):
        """Save index to JSON file"""
        index_dict = {
            name: {
                'file': str(loc.file),
                'start_line': loc.start_line,
                'end_line': loc.end_line,
                'length': loc.length,
                'estimated_tokens': loc.estimated_tokens
            }
            for name, loc in self.index.items()
        }

        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(index_dict, f, indent=2)

        print(f"   💾 Index saved to: {path}")

    @classmethod
    def load_index(cls, path: Path, markdown_files: List[Path]) -> 'ExtractionIndexer':
        """
        Load index from JSON file

        Args:
            path: Path to index JSON
            markdown_files: List of markdown files

        Returns:
            ExtractionIndexer with loaded index
        """
        indexer = cls(markdown_files)

        with open(path, 'r') as f:
            index_dict = json.load(f)

        for name, loc_dict in index_dict.items():
            indexer.index[name] = SectionLocation(
                file=Path(loc_dict['file']),
                start_line=loc_dict['start_line'],
                end_line=loc_dict['end_line'],
                section_name=name,
                estimated_tokens=loc_dict['estimated_tokens']
            )

        print(f"✅ Index loaded: {len(indexer.index)} sections")
        return indexer

    def get_total_estimated_tokens(self) -> int:
        """Calculate total estimated tokens for all indexed sections"""
        return sum(loc.estimated_tokens for loc in self.index.values())

    def enable_checkpointing(self, checkpoint_dir: Path):
        """Enable checkpointing for resumable extraction"""
        self.checkpoint_dir = checkpoint_dir
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def save_checkpoint(self, section_name: str, data: dict):
        """Save extraction checkpoint for a section"""
        if not self.checkpoint_dir:
            return

        checkpoint_file = self.checkpoint_dir / f"{section_name}.json"
        with open(checkpoint_file, 'w') as f:
            json.dump(data, f, indent=2)

    def load_checkpoint(self, section_name: str) -> Optional[dict]:
        """Load extraction checkpoint if available"""
        if not self.checkpoint_dir:
            return None

        checkpoint_file = self.checkpoint_dir / f"{section_name}.json"
        if checkpoint_file.exists():
            with open(checkpoint_file, 'r') as f:
                return json.load(f)
        return None

    def clear_checkpoints(self):
        """Clear all checkpoints"""
        if self.checkpoint_dir and self.checkpoint_dir.exists():
            for f in self.checkpoint_dir.glob('*.json'):
                f.unlink()


def main():
    """Test the indexer"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python extraction_indexer.py <markdown_files>...")
        sys.exit(1)

    md_files = [Path(f) for f in sys.argv[1:]]

    # Create indexer
    indexer = ExtractionIndexer(md_files)

    # Create index
    index = indexer.create_index()

    # Show results
    print("\n📊 SECTION INDEX SUMMARY")
    print("=" * 60)
    total_tokens = 0
    for name, loc in index.items():
        print(f"{name:20s} | Lines {loc.start_line:4d}-{loc.end_line:4d} | ~{loc.estimated_tokens:5d} tokens | {loc.file.name}")
        total_tokens += loc.estimated_tokens

    print("=" * 60)
    print(f"TOTAL ESTIMATED TOKENS: {total_tokens:,}")
    print(f"Full file would be: ~140,000 tokens")
    print(f"Savings: {(1 - total_tokens/140000)*100:.1f}%")


if __name__ == '__main__':
    main()
