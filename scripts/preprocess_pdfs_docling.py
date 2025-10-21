#!/usr/bin/env python3
"""
Phase 1: PDF to Markdown Conversion using Docling

Alternative to preprocess_pdfs_enhanced.py that uses Docling instead of PyMuPDF4LLM + Camelot.

Key differences:
- Uses Docling with TableFormerMode.FAST for table extraction
- Produces cleaner, more compact markdown (4 columns vs 14)
- Slower (~9.6 minutes per 48-page PDF vs 15 seconds)
- No cleanup/enhancement needed (Docling produces clean output)

Usage:
    python scripts/preprocess_pdfs_docling.py --issuer-name "Artis REIT" file1.pdf file2.pdf

Author: Claude Code Pipeline v1.0.12
Date: 2025-10-21
"""

import argparse
import os
import sys
import time
from pathlib import Path
from typing import List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def sanitize_issuer_name(name: str) -> str:
    """Convert issuer name to safe folder name."""
    return name.replace(" ", "_").replace("/", "_").replace("\\", "_")

def convert_pdf_docling(pdf_path: str, output_path: str, issuer_name: str) -> dict:
    """
    Convert a single PDF to markdown using Docling.

    Args:
        pdf_path: Path to PDF file
        output_path: Output directory for markdown
        issuer_name: Name of issuer (for reporting)

    Returns:
        dict with conversion stats
    """
    try:
        from docling.document_converter import DocumentConverter, PdfFormatOption
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
    except ImportError:
        print("ERROR: Docling not installed. Run: pip install docling")
        sys.exit(1)

    print(f"\n{'='*70}")
    print(f"Converting: {os.path.basename(pdf_path)}")
    print(f"Issuer: {issuer_name}")
    print(f"Method: Docling (FAST mode)")
    print(f"{'='*70}")

    start_time = time.time()

    # Configure Docling for fast table extraction
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_table_structure = True
    pipeline_options.table_structure_options.mode = TableFormerMode.FAST
    pipeline_options.table_structure_options.do_cell_matching = True
    pipeline_options.do_ocr = True  # Enable OCR for scanned sections

    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )

    # Convert PDF
    print(f"[1/2] Converting PDF to structured document...")
    result = converter.convert(pdf_path)

    # Export to markdown
    print(f"[2/2] Exporting to markdown...")
    markdown_content = result.document.export_to_markdown()

    # Save markdown
    os.makedirs(output_path, exist_ok=True)
    output_file = os.path.join(
        output_path,
        os.path.splitext(os.path.basename(pdf_path))[0] + ".md"
    )

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    elapsed_time = time.time() - start_time
    file_size = os.path.getsize(output_file)

    # Count lines and tables
    with open(output_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
        line_count = len(lines)
        table_count = sum(1 for line in lines if line.strip().startswith("|") and "---" in line)

    print(f"\n✓ Conversion complete!")
    print(f"  Output: {output_file}")
    print(f"  Size: {file_size / 1024:.1f} KB")
    print(f"  Lines: {line_count:,}")
    print(f"  Tables detected: {table_count}")
    print(f"  Time: {elapsed_time:.1f} seconds ({elapsed_time/60:.1f} minutes)")

    return {
        "pdf": pdf_path,
        "output": output_file,
        "size_kb": file_size / 1024,
        "lines": line_count,
        "tables": table_count,
        "time_seconds": elapsed_time,
        "success": True
    }

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Convert PDFs to Markdown using Docling (Phase 1 - Alternative Pipeline)"
    )
    parser.add_argument(
        "pdf_files",
        nargs="+",
        help="PDF files to convert (e.g., statements.pdf mda.pdf)"
    )
    parser.add_argument(
        "--issuer-name",
        required=True,
        help="Name of the issuer (e.g., 'Artis REIT')"
    )
    parser.add_argument(
        "--output-dir",
        default="Issuer_Reports",
        help="Base output directory (default: Issuer_Reports)"
    )

    args = parser.parse_args()

    # Setup paths
    issuer_folder = sanitize_issuer_name(args.issuer_name)
    output_base = os.path.join(args.output_dir, issuer_folder, "temp")
    markdown_output = os.path.join(output_base, "phase1_markdown")

    print(f"\n{'='*70}")
    print(f"PHASE 1: PDF → Markdown Conversion (Docling)")
    print(f"{'='*70}")
    print(f"Issuer: {args.issuer_name}")
    print(f"PDF files: {len(args.pdf_files)}")
    print(f"Output: {markdown_output}")
    print(f"Pipeline: Docling FAST mode (TableFormer)")

    # Verify PDFs exist
    missing_files = [f for f in args.pdf_files if not os.path.exists(f)]
    if missing_files:
        print(f"\nERROR: PDF files not found:")
        for f in missing_files:
            print(f"  - {f}")
        sys.exit(1)

    # Convert each PDF
    results = []
    total_start = time.time()

    for i, pdf_file in enumerate(args.pdf_files, 1):
        print(f"\nProcessing file {i}/{len(args.pdf_files)}")
        result = convert_pdf_docling(pdf_file, markdown_output, args.issuer_name)
        results.append(result)

    total_time = time.time() - total_start

    # Summary
    print(f"\n{'='*70}")
    print(f"PHASE 1 COMPLETE - Summary")
    print(f"{'='*70}")
    print(f"Files processed: {len(results)}")
    print(f"Total time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
    print(f"Average time per PDF: {total_time/len(results):.1f} seconds")
    print(f"\nOutput location: {markdown_output}/")

    successful = sum(1 for r in results if r["success"])
    if successful == len(results):
        print(f"\n✓ All files converted successfully!")
        print(f"\nNext step: Run Phase 2 extraction")
        print(f"  python scripts/extract_key_metrics_efficient.py \\")
        print(f"    --issuer-name \"{args.issuer_name}\" \\")
        print(f"    {markdown_output}/*.md")
    else:
        print(f"\n⚠ {len(results) - successful} file(s) failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
