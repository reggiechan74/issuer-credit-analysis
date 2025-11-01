#!/usr/bin/env python3
"""
Schema Validator for Phase 2 Extraction Output

Validates that Phase 2 extracted JSON conforms to the required schema
for Phase 3 calculations.

Usage:
    python scripts/validate_extraction_schema.py <path_to_extracted_json>

Example:
    python scripts/validate_extraction_schema.py Issuer_Reports/Artis_REIT/temp/phase2_extracted_data.json
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any


def validate_required_field(data: Dict, field_path: str) -> Tuple[bool, str]:
    """
    Validate that a required field exists in the data.

    Args:
        data: The JSON data dictionary
        field_path: Dot-notation path (e.g., 'balance_sheet.total_assets')

    Returns:
        Tuple of (is_valid, error_message)
    """
    keys = field_path.split('.')
    current = data

    for i, key in enumerate(keys):
        if not isinstance(current, dict):
            path_so_far = '.'.join(keys[:i])
            return False, f"Field '{path_so_far}' is not a dictionary, cannot access '{key}'"

        if key not in current:
            return False, f"Missing required field: {field_path}"

        current = current[key]

    return True, ""


def validate_field_type(data: Dict, field_path: str, expected_type: type, allow_null: bool = False) -> Tuple[bool, str]:
    """
    Validate that a field has the expected type.

    Args:
        data: The JSON data dictionary
        field_path: Dot-notation path
        expected_type: Expected Python type (int, float, str, etc.)
        allow_null: Whether None/null is acceptable

    Returns:
        Tuple of (is_valid, error_message)
    """
    keys = field_path.split('.')
    current = data

    for key in keys:
        if key not in current:
            return True, ""  # Field doesn't exist, will be caught by required check
        current = current[key]

    if current is None and allow_null:
        return True, ""

    if not isinstance(current, expected_type):
        return False, f"Field '{field_path}' has type {type(current).__name__}, expected {expected_type.__name__}"

    return True, ""


def validate_schema(data: Dict) -> Tuple[bool, List[str]]:
    """
    Validate the complete extraction schema.

    Args:
        data: The extracted JSON data

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    # Required top-level fields
    required_top_level = [
        ('issuer_name', str),
        ('reporting_date', str),
        ('currency', str)
    ]

    for field, expected_type in required_top_level:
        valid, error = validate_required_field(data, field)
        if not valid:
            errors.append(f"❌ {error}")
        else:
            valid, error = validate_field_type(data, field, expected_type)
            if not valid:
                errors.append(f"❌ {error}")

    # Balance sheet required fields
    balance_sheet_fields = [
        ('balance_sheet.total_assets', (int, float)),
        ('balance_sheet.mortgages_noncurrent', (int, float)),
        ('balance_sheet.mortgages_current', (int, float)),
        ('balance_sheet.credit_facilities', (int, float)),
        ('balance_sheet.cash', (int, float))
    ]

    for field, expected_type in balance_sheet_fields:
        valid, error = validate_required_field(data, field)
        if not valid:
            errors.append(f"❌ {error}")
        else:
            # Check if numeric
            keys = field.split('.')
            value = data
            for key in keys:
                value = value[key]
            if not isinstance(value, (int, float)):
                errors.append(f"❌ Field '{field}' must be numeric, got {type(value).__name__}")

    # Income statement required fields
    income_fields = [
        ('income_statement.noi', (int, float)),
        ('income_statement.interest_expense', (int, float)),
        ('income_statement.revenue', (int, float))
    ]

    for field, expected_type in income_fields:
        valid, error = validate_required_field(data, field)
        if not valid:
            errors.append(f"❌ {error}")
        else:
            keys = field.split('.')
            value = data
            for key in keys:
                value = value[key]
            if not isinstance(value, (int, float)):
                errors.append(f"❌ Field '{field}' must be numeric, got {type(value).__name__}")

    # FFO/AFFO required fields
    ffo_fields = [
        ('ffo_affo.ffo', (int, float)),
        ('ffo_affo.affo', (int, float)),
        ('ffo_affo.ffo_per_unit', (int, float)),
        ('ffo_affo.affo_per_unit', (int, float)),
        ('ffo_affo.distributions_per_unit', (int, float))
    ]

    for field, expected_type in ffo_fields:
        valid, error = validate_required_field(data, field)
        if not valid:
            errors.append(f"❌ {error}")
        else:
            keys = field.split('.')
            value = data
            for key in keys:
                value = value[key]
            if not isinstance(value, (int, float)):
                errors.append(f"❌ Field '{field}' must be numeric, got {type(value).__name__}")

    # Portfolio fields (optional, but must be correct type if present)
    if 'portfolio' in data:
        portfolio = data['portfolio']

        # Check occupancy_rate
        if 'occupancy_rate' in portfolio:
            if not isinstance(portfolio['occupancy_rate'], (int, float)):
                errors.append(f"❌ Field 'portfolio.occupancy_rate' must be numeric")
            elif portfolio['occupancy_rate'] > 1.0:
                errors.append(f"⚠️  Warning: portfolio.occupancy_rate is {portfolio['occupancy_rate']}, should be decimal (e.g., 0.878 for 87.8%)")

        # Check for null values that should be 0
        if 'total_gla_sf' in portfolio and portfolio['total_gla_sf'] is None:
            errors.append(f"⚠️  Warning: portfolio.total_gla_sf is null, should be 0 if unknown")

        # Check field name consistency
        if 'occupancy_including_commitments' in portfolio:
            errors.append(f"⚠️  Warning: Use 'occupancy_with_commitments' instead of 'occupancy_including_commitments'")

        if 'same_property_noi_growth' in portfolio and 'same_property_noi_growth_6m' not in portfolio:
            errors.append(f"⚠️  Warning: Use 'same_property_noi_growth_6m' instead of 'same_property_noi_growth'")

    # Validation checks
    if 'validation' in data:
        val = data['validation']

        if 'balance_sheet_balanced' in val:
            if val['balance_sheet_balanced'] is False:
                errors.append(f"⚠️  Warning: Balance sheet does not balance (assets != liabilities + equity)")

    is_valid = len([e for e in errors if e.startswith('❌')]) == 0
    return is_valid, errors


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_extraction_schema.py <path_to_json>")
        print("\nExample:")
        print("  python scripts/validate_extraction_schema.py Issuer_Reports/Artis_REIT/temp/phase2_extracted_data.json")
        sys.exit(1)

    input_path = Path(sys.argv[1])

    if not input_path.exists():
        print(f"❌ Error: File not found: {input_path}")
        sys.exit(1)

    print(f"📋 Validating schema for: {input_path}")
    print("=" * 70)

    try:
        with open(input_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON: {e}")
        sys.exit(1)

    is_valid, errors = validate_schema(data)

    if is_valid:
        print("\n✅ Schema validation PASSED")
        print(f"\nIssuer: {data.get('issuer_name', 'Unknown')}")
        print(f"Reporting Date: {data.get('reporting_date', 'Unknown')}")
        print(f"Currency: {data.get('currency', 'Unknown')}")

        if errors:
            print(f"\n⚠️  {len(errors)} warnings (non-blocking):")
            for error in errors:
                if error.startswith('⚠️'):
                    print(f"  {error}")

        print("\n✅ This file is compatible with Phase 3 calculations")
        sys.exit(0)
    else:
        print("\n❌ Schema validation FAILED")
        print(f"\nFound {len([e for e in errors if e.startswith('❌')])} errors:\n")

        for error in errors:
            print(f"  {error}")

        print("\n💡 Fix these errors before running Phase 3 calculations")
        print("\n📚 Schema reference: .claude/knowledge/phase2_extraction_schema_v2.json")
        sys.exit(1)


if __name__ == "__main__":
    main()
