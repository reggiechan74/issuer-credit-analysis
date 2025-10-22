#!/usr/bin/env python3
"""
Systematic extraction of CAPREIT Q4 2024 financial data from markdown file.
Handles large file (304KB) by reading specific line ranges.
"""

import json
import re

def read_lines(filepath, start=None, end=None):
    """Read specific lines from file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        if start and end:
            return lines[start:end]
        elif start:
            return lines[start:]
        elif end:
            return lines[:end]
        return lines

def extract_table_value(lines, pattern, col_index=1):
    """Extract numeric value from table row matching pattern."""
    for line in lines:
        if re.search(pattern, line, re.IGNORECASE):
            # Extract numbers from line
            numbers = re.findall(r'[\d,]+', line)
            if numbers and len(numbers) > col_index:
                return int(numbers[col_index].replace(',', ''))
    return 0

def main():
    filepath = "/workspaces/issuer-credit-analysis/Issuer_Reports/Canadian_Apartment_Properties_REIT/temp/phase1_markdown/Q4-2024-Annual-Report.md"

    # Read entire file once
    with open(filepath, 'r') as f:
        content = f.read()
        lines = content.split('\n')

    print(f"Total lines in file: {len(lines)}")

    # Initialize extraction structure
    extraction = {
        "issuer_name": "Canadian Apartment Properties Real Estate Investment Trust",
        "reporting_date": "2024-12-31",
        "reporting_period": "Q4 2024 / Year ended December 31, 2024",
        "currency": "CAD"
    }

    # Find key sections by line number (from earlier grep results)
    # Balance Sheet starts around line 6813
    # Income Statement around line 6833
    # Cash Flow Statement around line 6910
    # FFO/AFFO tables around lines 5100-5300

    #Find balance sheet data - look for table with 2024 and 2023 columns
    print("\nSearching for Balance Sheet data...")
    for i, line in enumerate(lines[6813:6900], start=6813):
        if '2024' in line and '2023' in line:
            print(f"Found balance sheet table header at line {i}: {line[:100]}")
            # Extract next 50 lines for balance sheet data
            bs_lines = lines[i:i+50]
            break

    # Search for specific balance sheet items in financial statements section
    print("\nSearching for financial statement items...")

    # Look for consolidated balance sheets table
    for i in range(len(lines)):
        if 'Total assets' in lines[i] or 'total assets' in lines[i]:
            print(f"Line {i}: {lines[i][:150]}")
            # Check surrounding lines for numbers
            for j in range(max(0, i-2), min(len(lines), i+3)):
                if any(char.isdigit() for char in lines[j]):
                    print(f"  Data line {j}: {lines[j][:150]}")

    # Look for mortgages payable
    for i in range(len(lines)):
        if re.search(r'mortgages payable|total mortgages', lines[i], re.IGNORECASE):
            if any(char.isdigit() for char in lines[i]):
                print(f"Mortgages line {i}: {lines[i][:150]}")

    # Look for credit facilities
    for i in range(len(lines)):
        if 'credit facilities' in lines[i].lower() and any(char.isdigit() for char in lines[i]):
            print(f"Credit facilities line {i}: {lines[i][:150]}")

    # Save preliminary extraction
    output_path = "/workspaces/issuer-credit-analysis/temp_capreit_extraction.json"
    with open(output_path, 'w') as f:
        json.dump(extraction, f, indent=2)

    print(f"\nPreliminary extraction saved to: {output_path}")
    print("\nNeed to manually locate financial tables in the 304KB file")
    print("Suggestion: Use grep patterns or split file into smaller sections")

if __name__ == "__main__":
    main()
