#!/usr/bin/env python3
"""
Step 1: PDF Pre-processing using Microsoft markitdown
Converts financial statement PDFs to markdown format
"""

import os
import sys
from pathlib import Path
from markitdown import MarkItDown

def preprocess_financial_pdfs(pdf_paths, output_dir):
    """
    Convert financial statement PDFs to markdown using markitdown

    Args:
        pdf_paths: List of PDF file paths
        output_dir: Directory to save markdown files

    Returns:
        Dictionary with conversion results
    """

    # Initialize markitdown
    md = MarkItDown()

    # Create output directory
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = {}

    for pdf_path in pdf_paths:
        pdf_path = Path(pdf_path)
        print(f"\n📄 Processing: {pdf_path.name}")

        try:
            # Convert PDF to markdown
            result = md.convert(str(pdf_path))

            # Create output filename
            output_filename = pdf_path.stem + ".md"
            output_path = output_dir / output_filename

            # Save markdown
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(result.text_content)

            results[pdf_path.name] = {
                'status': 'success',
                'output_path': str(output_path),
                'size_chars': len(result.text_content),
                'size_kb': len(result.text_content) / 1024
            }

            print(f"  ✓ Converted to markdown: {output_path}")
            print(f"  ✓ Size: {results[pdf_path.name]['size_kb']:.1f} KB")

        except Exception as e:
            results[pdf_path.name] = {
                'status': 'error',
                'error': str(e)
            }
            print(f"  ✗ Error: {e}")

    return results


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Convert financial statement PDFs to markdown'
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
        import re
        # Sanitize issuer name for folder name
        safe_name = args.issuer_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
        safe_name = re.sub(r'[^a-zA-Z0-9_-]', '', safe_name)
        args.output_dir = f'./Issuer_Reports/{safe_name}/temp/phase1_markdown'

    print("=" * 70)
    print("STEP 1: PDF PRE-PROCESSING (markitdown)")
    print("=" * 70)
    print(f"\nIssuer: {args.issuer_name}")
    print(f"Input files: {len(args.pdf_files)}")
    print(f"Output directory: {args.output_dir}\n")

    # Process PDFs
    results = preprocess_financial_pdfs(args.pdf_files, args.output_dir)

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    success_count = sum(1 for r in results.values() if r['status'] == 'success')
    error_count = len(results) - success_count

    print(f"\n✓ Successfully converted: {success_count}")
    print(f"✗ Errors: {error_count}")

    if success_count > 0:
        total_size = sum(r['size_kb'] for r in results.values() if r['status'] == 'success')
        print(f"\nTotal markdown size: {total_size:.1f} KB")

    # Exit code
    sys.exit(0 if error_count == 0 else 1)


if __name__ == "__main__":
    main()
