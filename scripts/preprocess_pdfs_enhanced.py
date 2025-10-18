#!/usr/bin/env python3
"""
Phase 1 Enhanced: PDF to Markdown with Improved Table Rendering (v3)
Uses PyMuPDF4LLM page-chunked + Camelot hybrid approach
- No duplication
- Removes confusing base text tables
- Attempts to add proper column headers to Camelot tables
"""

import os
import sys
import re
from pathlib import Path
import pymupdf4llm
import camelot
import pandas as pd
from typing import List, Dict, Tuple, Optional


def extract_pages_with_pymupdf(pdf_path: Path) -> List[Dict]:
    """
    Extract markdown page by page using PyMuPDF4LLM

    Args:
        pdf_path: Path to PDF file

    Returns:
        List of page dictionaries with metadata and text
    """
    print(f"  → Extracting pages with PyMuPDF4LLM...")
    pages = pymupdf4llm.to_markdown(
        str(pdf_path),
        page_chunks=True,  # Returns list of pages
        write_images=False,  # Skip images for faster processing
        show_progress=False
    )
    print(f"    ✓ Extracted {len(pages)} pages")
    return pages


def extract_tables_with_camelot(pdf_path: Path, flavor: str = 'lattice') -> Dict[int, List]:
    """
    Extract tables using Camelot, organized by page number

    Args:
        pdf_path: Path to PDF file
        flavor: 'lattice' (for bordered tables) or 'stream' (for borderless)

    Returns:
        Dictionary mapping page_number -> list of table objects
    """
    print(f"  → Extracting tables with Camelot ({flavor} mode)...")

    try:
        tables = camelot.read_pdf(
            str(pdf_path),
            pages='all',
            flavor=flavor,
            suppress_stdout=True
        )

        if len(tables) == 0:
            print(f"    ⚠ No tables found with {flavor} mode")
            return {}

        print(f"    ✓ Found {len(tables)} tables")

        # Organize tables by page number
        tables_by_page = {}
        for idx, table in enumerate(tables):
            page_num = table.page
            if page_num not in tables_by_page:
                tables_by_page[page_num] = []
            tables_by_page[page_num].append((table, idx))

        return tables_by_page

    except Exception as e:
        print(f"    ✗ Camelot extraction failed: {e}")
        return {}


def detect_table_lines(text: str) -> List[int]:
    """
    Detect line numbers that appear to be table rows (multiple numbers)

    Args:
        text: Page text

    Returns:
        List of line numbers that look like table rows
    """
    lines = text.split('\n')
    table_lines = []

    for i, line in enumerate(lines):
        # Skip headers and empty lines
        if not line.strip() or line.strip().startswith('#'):
            continue

        # Count numeric values in line (including $ and ,)
        numbers = re.findall(r'\$?[\d,]+', line)

        # If line has 2+ numbers, it's probably a table row
        if len(numbers) >= 2:
            table_lines.append(i)

    return table_lines


def remove_table_lines_from_text(text: str) -> str:
    """
    Remove lines that look like table rows from base text

    Args:
        text: Original page text

    Returns:
        Text with table-like lines removed
    """
    lines = text.split('\n')
    table_line_nums = detect_table_lines(text)

    # Remove table lines
    cleaned_lines = [line for i, line in enumerate(lines) if i not in table_line_nums]

    return '\n'.join(cleaned_lines)


def extract_column_headers_from_context(page_text: str, table_position: int = 0) -> Optional[List[str]]:
    """
    Try to extract column headers from the page text context

    Args:
        page_text: Full page text
        table_position: Position of table on page (0-indexed)

    Returns:
        List of column header names or None
    """
    lines = page_text.split('\n')

    # Look for common header patterns in first 20 lines
    for i, line in enumerate(lines[:20]):
        # Pattern: "June 30, December 31,"
        if re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d+,', line):
            date_headers = [h.strip() for h in line.split(',') if h.strip()]

            # Look for year line nearby
            for j in range(max(0, i-2), min(len(lines), i+5)):
                year_match = re.findall(r'\b(20\d{2})\b', lines[j])
                if len(year_match) >= 2:
                    # Combine dates with years
                    headers = ['Line Item', 'Note']
                    for k, date in enumerate(date_headers):
                        if k < len(year_match):
                            headers.append(f"{date} {year_match[k]}")
                    return headers

    return None


def enhance_table_with_headers(table_obj, page_text: str, table_idx: int) -> str:
    """
    Create markdown table with enhanced column headers if possible

    Args:
        table_obj: Camelot table object
        page_text: Full page text for context
        table_idx: Table index

    Returns:
        Markdown table string with enhanced headers
    """
    df = table_obj.df

    # Try to extract meaningful headers from context
    extracted_headers = extract_column_headers_from_context(page_text, table_idx)

    if extracted_headers and len(extracted_headers) >= 2:
        # Use extracted headers (expand for 6-column format if needed)
        num_cols = len(df.columns)
        if num_cols == 6 and len(extracted_headers) == 4:
            # Expand: Line Item, Note, Date1, Date2 -> Line Item, Note, $, Date1, $, Date2
            df.columns = [
                extracted_headers[0],  # Line Item
                extracted_headers[1],  # Note
                '',                     # Empty column (currency/spacing)
                extracted_headers[2],  # Date 1 (e.g., "June 30 2025")
                '',                     # Empty column (currency/spacing)
                extracted_headers[3]   # Date 2 (e.g., "December 31 2024")
            ]
        elif num_cols <= len(extracted_headers):
            df.columns = extracted_headers[:num_cols]
        else:
            # Not enough headers extracted, use fallback
            if num_cols == 6:
                df.columns = ['Line Item', 'Note', '', 'Current Period', '', 'Prior Period']
            elif num_cols == 4:
                df.columns = ['Line Item', 'Note', 'Current Period', 'Prior Period']
            else:
                df.columns = [f'Column {i+1}' for i in range(num_cols)]
    else:
        # Provide generic but descriptive headers
        num_cols = len(df.columns)
        if num_cols == 6:
            # Common financial statement format
            df.columns = ['Line Item', 'Note', '', 'Current Period', '', 'Prior Period']
        elif num_cols == 4:
            df.columns = ['Line Item', 'Note', 'Current Period', 'Prior Period']
        else:
            # Fallback to Column 1, Column 2, etc.
            df.columns = [f'Column {i+1}' for i in range(num_cols)]

    # Convert to markdown with new headers
    return df.to_markdown(index=False)


def identify_table_category(table_md: str) -> str:
    """
    Identify the category of a financial table

    Args:
        table_md: Markdown representation of table

    Returns:
        Category name
    """
    table_lower = table_md.lower()

    balance_sheet_keywords = ['assets', 'liabilities', 'equity', 'shareholders', 'balance sheet']
    income_keywords = ['revenue', 'expenses', 'net income', 'income statement', 'profit', 'loss', 'noi']
    cash_flow_keywords = ['cash flow', 'operating activities', 'investing activities', 'financing activities']
    ffo_keywords = ['ffo', 'affo', 'funds from operations', 'adjusted funds']

    if any(kw in table_lower for kw in balance_sheet_keywords):
        return 'Balance Sheet'
    elif any(kw in table_lower for kw in income_keywords):
        return 'Income Statement'
    elif any(kw in table_lower for kw in cash_flow_keywords):
        return 'Cash Flow Statement'
    elif any(kw in table_lower for kw in ffo_keywords):
        return 'FFO/AFFO'
    else:
        return 'Other'


def merge_pages_with_tables(pages: List[Dict], tables_by_page: Dict[int, List],
                            pdf_name: str) -> str:
    """
    Merge page content with extracted tables inline
    - Removes confusing table-like lines from base text
    - Adds proper column headers to Camelot tables

    Args:
        pages: List of page dictionaries from PyMuPDF4LLM
        tables_by_page: Dictionary mapping page_number -> list of (table_obj, table_index)
        pdf_name: Name of PDF file for reference

    Returns:
        Complete markdown document with enhanced tables
    """
    print(f"  → Merging {sum(len(t) for t in tables_by_page.values())} tables into {len(pages)} pages...")
    print(f"  → Removing confusing table text and adding proper headers...")

    final_md = f"# {pdf_name}\n\n"
    final_md += f"**Extraction Method:** PyMuPDF4LLM + Camelot Enhanced (v3)\n\n"
    final_md += f"**Note:** Tables have been enhanced with proper formatting and column headers.\n"
    final_md += f"Confusing text-based tables have been removed for clarity.\n\n"
    final_md += "---\n\n"

    for page_dict in pages:
        page_num = page_dict['metadata']['page']
        page_text = page_dict['text']

        # Remove confusing table-like lines from base text
        cleaned_text = remove_table_lines_from_text(page_text)

        # Add page content (cleaned)
        final_md += f"<!-- Page {page_num} -->\n\n"
        final_md += cleaned_text
        final_md += "\n\n"

        # Add Camelot tables for this page (if any) with enhanced headers
        if page_num in tables_by_page:
            page_tables = tables_by_page[page_num]
            final_md += f"---\n"
            final_md += f"### 📊 Enhanced Financial Tables (Page {page_num})\n\n"
            final_md += f"*{len(page_tables)} table(s) with proper column headers and formatting*\n\n"

            for table_obj, table_idx in page_tables:
                # Enhance table with proper headers
                table_md = enhance_table_with_headers(table_obj, page_text, table_idx)
                category = identify_table_category(table_md)

                final_md += f"**Table {table_idx + 1}** - *{category}*\n\n"
                final_md += table_md + "\n\n"

            final_md += "---\n\n"

    return final_md


def preprocess_pdf_enhanced(pdf_path: Path, output_dir: Path) -> Dict:
    """
    Main preprocessing with v3 improvements:
    - Removes confusing base text tables
    - Adds proper column headers to Camelot tables

    Args:
        pdf_path: Path to input PDF
        output_dir: Directory for output markdown

    Returns:
        Dictionary with processing results
    """
    print(f"\n📄 Processing: {pdf_path.name}")

    try:
        # Step 1: Extract pages with PyMuPDF4LLM (page-chunked)
        pages = extract_pages_with_pymupdf(pdf_path)

        # Step 2: Extract tables with Camelot (try lattice first, then stream)
        tables_by_page = extract_tables_with_camelot(pdf_path, flavor='lattice')

        # If no tables found with lattice, try stream mode
        if not tables_by_page:
            print(f"  → Retrying with stream mode...")
            tables_by_page = extract_tables_with_camelot(pdf_path, flavor='stream')

        # Step 3: Merge pages with enhanced tables
        total_tables = sum(len(t) for t in tables_by_page.values())
        if tables_by_page:
            final_md = merge_pages_with_tables(pages, tables_by_page, pdf_path.name)
        else:
            print(f"  ⚠ No tables extracted, using base pages only")
            final_md = f"# {pdf_path.name}\n\n"
            for page_dict in pages:
                page_num = page_dict['metadata']['page']
                final_md += f"<!-- Page {page_num} -->\n\n"
                final_md += page_dict['text'] + "\n\n"

        # Step 4: Save output
        output_path = output_dir / f"{pdf_path.stem}.md"
        output_path.write_text(final_md, encoding='utf-8')

        result = {
            'status': 'success',
            'output_path': str(output_path),
            'size_chars': len(final_md),
            'size_kb': len(final_md) / 1024,
            'tables_extracted': total_tables,
            'pages': len(pages)
        }

        print(f"  ✓ Saved to: {output_path}")
        print(f"  ✓ Size: {result['size_kb']:.1f} KB")
        print(f"  ✓ Pages: {result['pages']}, Tables: {result['tables_extracted']}")

        return result

    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return {
            'status': 'error',
            'error': str(e)
        }


def preprocess_financial_pdfs(pdf_paths: List[Path], output_dir: Path) -> Dict:
    """
    Process multiple PDFs

    Args:
        pdf_paths: List of PDF file paths
        output_dir: Directory to save markdown files

    Returns:
        Dictionary with conversion results
    """
    # Create output directory
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = {}

    for pdf_path in pdf_paths:
        pdf_path = Path(pdf_path)
        results[pdf_path.name] = preprocess_pdf_enhanced(pdf_path, output_dir)

    return results


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Convert financial statement PDFs to markdown (v3 - clean tables with proper headers)'
    )
    parser.add_argument(
        'pdf_files',
        nargs='+',
        help='PDF files to process'
    )
    parser.add_argument(
        '--issuer-name',
        required=True,
        help='Issuer name (creates folder: Issuer_Reports/{issuer_name}/temp/phase1_markdown/)'
    )
    parser.add_argument(
        '--output-dir',
        default=None,
        help='Output directory (default: auto-generated from issuer name)'
    )

    args = parser.parse_args()

    # Auto-generate output directory if not specified
    if args.output_dir is None:
        # Sanitize issuer name for folder name
        safe_name = args.issuer_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
        safe_name = re.sub(r'[^a-zA-Z0-9_-]', '', safe_name)
        # Use absolute path from current working directory
        cwd = Path.cwd()
        args.output_dir = str(cwd / 'Issuer_Reports' / safe_name / 'temp' / 'phase1_markdown')

    print("=" * 80)
    print("PHASE 1 ENHANCED v3: PDF TO MARKDOWN (PyMuPDF4LLM + Camelot)")
    print("✨ Clean output - removes confusing text, adds proper column headers")
    print("=" * 80)
    print(f"\nIssuer: {args.issuer_name}")
    print(f"Input files: {len(args.pdf_files)}")
    print(f"Output directory: {args.output_dir}\n")

    # Process PDFs
    results = preprocess_financial_pdfs(args.pdf_files, args.output_dir)

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    success_count = sum(1 for r in results.values() if r['status'] == 'success')
    error_count = len(results) - success_count

    print(f"\n✓ Successfully converted: {success_count}")
    print(f"✗ Errors: {error_count}")

    if success_count > 0:
        total_size = sum(r['size_kb'] for r in results.values() if r['status'] == 'success')
        total_tables = sum(r.get('tables_extracted', 0) for r in results.values() if r['status'] == 'success')
        total_pages = sum(r.get('pages', 0) for r in results.values() if r['status'] == 'success')
        print(f"\nTotal markdown size: {total_size:.1f} KB")
        print(f"Total pages: {total_pages}")
        print(f"Total tables extracted: {total_tables}")

    # Exit code
    sys.exit(0 if error_count == 0 else 1)


if __name__ == "__main__":
    main()
