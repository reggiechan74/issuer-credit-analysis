"""
Validation functions for credit metrics calculations

SAFETY: All validation functions fail loudly with clear error messages
"""


def validate_required_fields(data, required_fields):
    """
    Ensure all required fields exist - fail loudly if missing

    Args:
        data: Dictionary to validate
        required_fields: List of dot-notation field paths (e.g., 'balance_sheet.total_assets')

    Raises:
        KeyError: If any required field is missing
    """
    for field in required_fields:
        keys = field.split('.')
        current = data
        for key in keys:
            if key not in current:
                raise KeyError(
                    f"Missing required field: {field}. "
                    f"Ensure Phase 2 extraction included this field."
                )
            current = current[key]
