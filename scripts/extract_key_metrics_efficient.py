#!/usr/bin/env python3
"""
Phase 2 (EFFICIENT): Extract key financial metrics using Claude Code (no API required)

IMPROVEMENT: Instead of embedding 140K tokens of markdown in the prompt,
this version references file paths and lets Claude Code read them directly.

Token reduction: ~140K → ~1K tokens (99% reduction)

Configuration support: v1.1.0
- Supports markdown→JSON or PDF→JSON extraction
- Configurable via config/extraction_config.yaml
"""

import json
import sys
from pathlib import Path

# Import configuration loader
try:
    from config_loader import load_config
except ImportError:
    # Fallback if not in same directory
    sys.path.insert(0, str(Path(__file__).parent))
    from config_loader import load_config


def generate_template_from_schema(schema_path=None):
    """
    Generate pre-filled JSON template with all required fields from schema

    This function reads the authoritative Phase 2 extraction schema and creates
    a template with correct structure and field names, using zero/empty values.
    This ensures extractors follow the exact schema structure from the start.

    Args:
        schema_path: Path to schema JSON file (default: .claude/knowledge/phase2_extraction_schema_v2.json)

    Returns:
        dict: Template with correct structure and field names, zero/empty values
    """
    if schema_path is None:
        schema_path = Path(__file__).parent.parent / '.claude' / 'knowledge' / 'phase2_extraction_schema_v2.json'

    with open(schema_path) as f:
        schema = json.load(f)

    def process_field(field_spec):
        """Recursively process a field specification to generate default value"""
        field_type = field_spec.get('type')

        # Handle array of types (e.g., ["number", "null"])
        if isinstance(field_type, list):
            # Use the first non-null type
            for t in field_type:
                if t != 'null':
                    field_type = t
                    break
            else:
                field_type = 'null'

        # Generate default value based on type
        if field_type == 'object':
            # Recursively process nested object
            result = {}
            if 'properties' in field_spec:
                for subfield, subspec in field_spec['properties'].items():
                    result[subfield] = process_field(subspec)
            return result

        elif field_type == 'array':
            # Return empty array (extractor will populate as needed)
            return []

        elif field_type == 'string':
            return ""

        elif field_type == 'number':
            return 0

        elif field_type == 'integer':
            return 0

        elif field_type == 'boolean':
            return False

        elif field_type == 'null':
            return None

        else:
            # Unknown type, default to empty string
            return ""

    # Generate template from schema properties
    template = {}
    for field, spec in schema['properties'].items():
        template[field] = process_field(spec)

    return template


def format_error_guidance(errors):
    """
    Generate specific guidance based on validation error types

    Args:
        errors: List of validation error messages

    Returns:
        str: Formatted guidance for fixing errors
    """
    guidance = []

    # Check for common error patterns
    if any('issuer_name' in e for e in errors):
        guidance.append("• Move issuer_name to TOP LEVEL (not nested in issuer_info or data_quality)")

    if any('reporting_date' in e for e in errors):
        guidance.append("• Move reporting_date to TOP LEVEL (not nested)")

    if any('currency' in e for e in errors):
        guidance.append("• Move currency to TOP LEVEL (not nested)")

    if any('cash' in e and 'balance_sheet' in e for e in errors):
        guidance.append("• Use exact field name 'cash' in balance_sheet (NOT 'cash_and_equivalents')")

    if any('mortgages' in e for e in errors):
        guidance.append("• Split debt: balance_sheet.mortgages_noncurrent, balance_sheet.mortgages_current, balance_sheet.credit_facilities")

    if any('ffo_per_unit' in e for e in errors):
        guidance.append("• Include ffo_per_unit, affo_per_unit, distributions_per_unit in ffo_affo section")

    if any('noi' in e or 'interest_expense' in e or 'revenue' in e for e in errors):
        guidance.append("• Ensure income_statement has TOP-LEVEL noi, interest_expense, and revenue fields")

    if any('cash_flow_from_operations' in e for e in errors):
        guidance.append("• CRITICAL: Extract cash_flow_from_operations from Cash Flow Statement - required for ACFO/AFCF calculations")

    if any('type' in e.lower() and 'null' in e.lower() for e in errors):
        guidance.append("• Replace null values with 0 for numeric fields (Phase 3 cannot process nulls)")

    if any('nested' in e.lower() or 'dictionary' in e.lower() for e in errors):
        guidance.append("• Flatten structure: balance_sheet should be FLAT (no nested objects by period)")

    # Generic fallback if no specific patterns matched
    if not guidance:
        guidance.append("• Follow the template structure EXACTLY - do not modify field names or structure")
        guidance.append("• Check schema specification: .claude/knowledge/phase2_extraction_schema_v2.json")

    return "\n".join(guidance)


def save_failed_extraction(output_path, data, errors, attempt_number):
    """
    Save failed extraction with errors for debugging

    Args:
        output_path: Original output path
        data: The extracted data that failed validation
        errors: List of validation errors
        attempt_number: Which attempt failed (1, 2, or 3)
    """
    output_path = Path(output_path)
    failed_dir = output_path.parent / 'failed_extractions'
    failed_dir.mkdir(exist_ok=True)

    timestamp = Path(output_path).stem
    failed_path = failed_dir / f"{timestamp}_attempt{attempt_number}_FAILED.json"

    failed_data = {
        "extraction_data": data,
        "validation_errors": errors,
        "attempt_number": attempt_number,
        "original_output_path": str(output_path)
    }

    with open(failed_path, 'w') as f:
        json.dump(failed_data, f, indent=2)

    print(f"\n💾 Failed extraction saved for debugging: {failed_path}")
    return failed_path


def create_retry_prompt(markdown_files, output_path, issuer_name, previous_errors, previous_data, attempt_number):
    """
    Create extraction prompt with previous errors for retry

    Args:
        markdown_files: Source markdown files
        output_path: Path where JSON should be saved
        issuer_name: Name of issuer
        previous_errors: List of validation errors from previous attempt
        previous_data: Previously extracted data (partially correct)
        attempt_number: Which attempt this is (2 or 3)

    Returns:
        str: Enhanced prompt with error corrections
    """
    # Generate template from schema
    schema_path = Path(__file__).parent.parent / '.claude' / 'knowledge' / 'phase2_extraction_schema_v2.json'
    template = generate_template_from_schema(schema_path)

    # Identify specific problems
    error_list = "\n".join(f"  • {e}" for e in previous_errors[:20])  # Show first 20 errors
    guidance = format_error_guidance(previous_errors)

    # Create file list
    file_list = "\n".join([f"- `{f}`" for f in markdown_files])

    prompt = f"""# Phase 2: RETRY EXTRACTION (Attempt {attempt_number}/3) - {issuer_name}

⚠️ **PREVIOUS ATTEMPT FAILED VALIDATION** - {len(previous_errors)} error(s) found

**Task:** Re-extract financial data with corrections based on validation errors.

**Input Files:**
{file_list}

**Output File:** `{output_path}`

---

## VALIDATION ERRORS FROM PREVIOUS ATTEMPT

{error_list}

---

## CRITICAL FIXES NEEDED

{guidance}

---

## CORRECTED EXTRACTION INSTRUCTIONS

### Step 1: Read Files
Use the Read tool to access each markdown file listed above.

### Step 2: Use EXACT Template Structure

**DO NOT REPEAT THE SAME ERRORS.** Follow this template structure EXACTLY:

```json
{json.dumps(template, indent=2)}
```

**CRITICAL VALIDATION RULES - CHECK BEFORE SAVING:**

1. ✅ **Top-level fields:** issuer_name, reporting_date, currency MUST be at top level (NOT nested)
2. ✅ **Exact field names:** Use 'cash' in balance_sheet (NOT 'cash_and_equivalents')
3. ✅ **Required fields:** All balance_sheet fields must exist: cash, mortgages_noncurrent, mortgages_current, credit_facilities
4. ✅ **No nulls:** Use 0 for missing numeric values (NOT null)
5. ✅ **Flat structure:** balance_sheet is FLAT (no nested objects by period)
6. ✅ **FFO/AFFO fields:** Must include ffo, affo, ffo_per_unit, affo_per_unit, distributions_per_unit
7. ✅ **Income statement:** Must include TOP-LEVEL noi, interest_expense, revenue
8. ✅ **ACFO required:** Must include acfo_components.cash_flow_from_operations from cash flow statement

### Step 3: Extract Data

Extract financial data from the markdown files following the template above.

**WHERE TO FIND DATA:**

**Critical Fields (often missing):**
- **cash_flow_from_operations:** Cash Flow Statement → "Cash provided by operating activities"
- **noi (Net Operating Income):** Income Statement → Revenue minus operating expenses
- **interest_expense:** Income Statement → Interest/financing costs
- **mortgages_noncurrent:** Balance Sheet or Notes → "Mortgages payable - non-current"
- **mortgages_current:** Balance Sheet or Notes → "Current portion of mortgages"

### Step 4: Self-Validate BEFORE Saving

**Run through this checklist before saving:**

- [ ] issuer_name is at TOP LEVEL (not nested)
- [ ] reporting_date is at TOP LEVEL
- [ ] currency is at TOP LEVEL
- [ ] balance_sheet.cash exists and is numeric
- [ ] balance_sheet.mortgages_noncurrent exists
- [ ] balance_sheet.mortgages_current exists
- [ ] balance_sheet.credit_facilities exists
- [ ] income_statement.noi exists and is numeric
- [ ] income_statement.interest_expense exists and is numeric
- [ ] income_statement.revenue exists and is numeric
- [ ] ffo_affo.ffo_per_unit exists
- [ ] ffo_affo.affo_per_unit exists
- [ ] ffo_affo.distributions_per_unit exists
- [ ] acfo_components.cash_flow_from_operations exists
- [ ] No null values in numeric fields (use 0 instead)
- [ ] balance_sheet is FLAT (no nested quarterly/annual sections)

**ONLY save the JSON if ALL checkboxes are checked!**

### Step 5: Save JSON

Save to: `{output_path}`

### Step 6: Validation

The script will automatically validate after saving. If this attempt also fails, you'll get one more retry with additional guidance.

---

## REFERENCE: PREVIOUS ATTEMPT DATA (Partially Correct)

The previous extraction got some things right. Use this as reference but FIX THE ERRORS:

```json
{json.dumps(previous_data, indent=2)[:5000]}...
```

**Remember:** The structure above has errors. Use the CORRECTED template from Step 2 instead.

---

**Schema Reference:** `.claude/knowledge/phase2_extraction_schema_v2.json`
**Extraction Guide:** `.claude/knowledge/COMPREHENSIVE_EXTRACTION_GUIDE.md`
"""

    return prompt


def check_and_validate_existing_output(output_path):
    """
    Check if output JSON exists and validate it

    Args:
        output_path: Path to output JSON file

    Returns:
        Tuple of (exists, is_valid, errors, data, attempt_number)
        - exists: Boolean, whether file exists
        - is_valid: Boolean, whether validation passed (None if doesn't exist)
        - errors: List of validation errors (empty if valid/doesn't exist)
        - data: The extracted data (None if doesn't exist)
        - attempt_number: Current attempt number (1 if doesn't exist, 2-3 based on retries)
    """
    output_path = Path(output_path)

    # Check for retry metadata file
    metadata_path = output_path.parent / f".{output_path.stem}_retry_metadata.json"

    if not output_path.exists():
        return False, None, [], None, 1

    # Load existing data
    try:
        with open(output_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return True, False, [f"Invalid JSON: {e}"], None, 1

    # Load retry metadata if exists
    attempt_number = 1
    if metadata_path.exists():
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
                attempt_number = metadata.get('attempt_number', 1)
        except:
            pass

    # Validate the data using the validation module
    sys.path.insert(0, str(Path(__file__).parent))
    from validate_extraction_schema import validate_schema

    is_valid, errors = validate_schema(data)

    return True, is_valid, errors, data, attempt_number


def save_retry_metadata(output_path, attempt_number):
    """
    Save metadata about retry attempts

    Args:
        output_path: Path to output JSON file
        attempt_number: Current attempt number
    """
    output_path = Path(output_path)
    metadata_path = output_path.parent / f".{output_path.stem}_retry_metadata.json"

    metadata = {
        "attempt_number": attempt_number,
        "last_attempt_timestamp": str(Path(output_path).stat().st_mtime) if output_path.exists() else None
    }

    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)


def create_efficient_extraction_prompt(markdown_files, output_path, issuer_name):
    """
    Create EFFICIENT extraction prompt for Claude Code

    Instead of embedding full markdown text (~140K tokens),
    just reference file paths (~1K tokens)

    Args:
        markdown_files: List of markdown file paths
        output_path: Path where JSON should be saved
        issuer_name: Name of issuer

    Returns:
        str: Compact prompt for Claude Code
    """

    # Load schema from single source of truth
    schema_path = Path(__file__).parent.parent / '.claude' / 'knowledge' / 'phase2_extraction_schema_v2.json'
    with open(schema_path, 'r') as f:
        schema_template = f.read()

    # Generate pre-filled template
    template = generate_template_from_schema(schema_path)

    # Create file list with paths
    file_list = "\n".join([f"- `{f}`" for f in markdown_files])

    prompt = f"""# Phase 2: Extract Financial Data for {issuer_name}

**Task:** Extract structured financial data from markdown files and save as JSON.

**Input Files:**
{file_list}

**Output File:** `{output_path}`

---

## EXTRACTION INSTRUCTIONS

### Step 1: Read Files
Use the Read tool to access each markdown file listed above.

### Step 2: Extract Required Data

**IMPORTANT: Use this EXACT JSON structure** (fill in actual values from source documents, keep structure unchanged):

This pre-filled template includes ALL required fields with correct names and structure:

```json
{json.dumps(template, indent=2)}
```

**Schema Rules:**
1. **Top-level fields:** issuer_name, reporting_date, currency (NOT nested in issuer_info)
2. **Exact field names:** Use names EXACTLY as shown above (e.g., 'cash' not 'cash_and_equivalents' in balance_sheet)
3. **All required fields:** Every field shown above must be present
4. **Use 0 for missing numeric values** (NOT null)
5. **Flat structure:** No unnecessary nesting (balance_sheet is flat, not nested by period)

**Full schema specification available at:** `.claude/knowledge/phase2_extraction_schema_v2.json`

### Step 3: Data Extraction Guidelines

**CRITICAL RULES:**
1. **Numbers:** No commas or $ signs (e.g., `2611435` not `$2,611,435`)
2. **Units:** All amounts in thousands (as shown in statements)
3. **Decimals:** Rates as decimals (e.g., `0.878` for 87.8%, NOT `87.8`)
4. **Field Names:** EXACTLY as shown above
5. **Structure:** FLAT - no nested objects in balance_sheet
6. **Most Recent Period:** Use latest period data (e.g., Q2 2025, six months)

**CRITICAL FIELD NAMES - VALIDATION CHECKLIST**

⚠️ **Most Common Extraction Errors** (check these BEFORE saving):

**acfo_components:**
- ✅ `cash_flow_from_operations` (NOT "cash_from_operations", NOT "cfo", NOT "operating_cash_flow")
  - **Location:** Cash Flow Statement - "Cash provided by operating activities"
  - **Required:** This field is MANDATORY - without it, ACFO/AFCF/burn rate cannot be calculated

**cash_flow_investing:**
- ✅ `development_capex` (NOT "capex_investment_properties", NOT "development_capital_expenditures")
- ✅ `other_investing_outflows` (NOT "capex_other", NOT "other_capex")

**liquidity:**
- ✅ `cash_and_equivalents` (NOT "cash", NOT "cash_equivalents")
- ✅ `undrawn_credit_facilities` (NOT "revolver_available", NOT "available_credit", NOT "undrawn_revolver")

**Common Section Mistakes:**
- ❌ DO NOT put `leasing_costs` or `tenant_improvements` in `cash_flow_investing`
  - ✅ They belong in `acfo_components` and `ffo_affo_components`
- ❌ DO NOT use `cash` in liquidity section
  - ✅ Use `cash_and_equivalents` (even if source says "cash")

**FIELD NAME MAPPING TABLE**

Use this table to map terms in financial statements → correct schema field names:

| Source Document Term | Schema Field Name | Section | Notes |
|---------------------|-------------------|---------|-------|
| "Cash and cash equivalents" | `cash_and_equivalents` | liquidity | Use even if balance sheet says "Cash" |
| "Cash" (balance sheet line) | `cash` | balance_sheet | For balance sheet consistency only |
| "Cash provided by operating activities" | `cash_flow_from_operations` | acfo_components | REQUIRED field |
| "Available capacity" / "Undrawn" | `undrawn_credit_facilities` | liquidity | Sum across all facilities |
| "Revolver available" | `undrawn_credit_facilities` | liquidity | NOT "revolver_available" |
| "Additions to investment properties" | `development_capex` | cash_flow_investing | Negative number |
| "Development expenditures" | `development_capex` | cash_flow_investing | NOT "capex_investment_properties" |
| "Property acquisitions" | `property_acquisitions` | cash_flow_investing | Negative number |
| "Proceeds from dispositions" | `property_dispositions` | cash_flow_investing | Positive number |
| "Leasing commissions" | `leasing_costs` | acfo_components | NOT in cash_flow_investing |
| "Tenant improvements" | `tenant_improvements` | acfo_components | NOT in cash_flow_investing |

**WHERE TO FIND DATA:**

**Balance Sheet:**
- Look for "Consolidated Balance Sheets" or "Statement of Financial Position"
- Usually in consolidated financial statements PDF
- Extract: total_assets, cash, mortgages (current/non-current), debentures, equity

**Income Statement:**
- Look for "Consolidated Statements of Operations" or "Statement of Income"
- Calculate NOI = Revenue - Operating Expenses - Realty Taxes
- Extract: revenue, NOI, interest expense, net income

**FFO/AFFO (Basic - Required):**
- Usually in MD&A document
- Look for "FFO and AFFO" section or tables showing "Funds from Operations"
- Extract: FFO, AFFO, per unit amounts, payout ratios
- **Minimum Required:** `ffo`, `affo`, `ffo_per_unit`, `affo_per_unit`, `distributions_per_unit`

**FFO/AFFO Components (COMPREHENSIVE - enables reconciliation tables):**
- Enables calculating FFO/AFFO from first principles per REALPAC methodology (Jan 2022)
- Look in "Notes to Financial Statements" - often has FFO/AFFO reconciliation table
- **Starting Point:** Net income from Statement of Comprehensive Income
- **Key Adjustments to Extract:**
  - **Adjustment A:** Unrealized fair value changes in investment properties
  - **Adjustment B:** Depreciation of depreciable real estate assets
  - **Adjustment C:** Amortization of tenant allowances
  - **Adjustment D:** Amortization of tenant/customer relationship intangibles
  - **Adjustment E:** Gains/losses from property sales
  - **Adjustment V (for AFFO):** Sustaining capital expenditures
  - **Adjustment W (for AFFO):** Leasing costs (internal + external)
  - **Adjustment X (for AFFO):** Tenant improvements (sustaining only)
  - **Adjustment Y (for AFFO):** Straight-line rent adjustment
- **Common Section:** "Reconciliation of Net Income to FFO" or "FFO Calculation"
- **Note:** Extract actual amounts shown in reconciliation, not formulas

**FFO/AFFO "Other" Adjustments (NEW - for complete reconciliation):**
- **Purpose:** Capture issuer-specific adjustments that don't fit REALPAC A-Z categories
- **When to use "Other" adjustments:**
  - Issuer uses non-standard terminology (e.g., "Expected credit loss on preferred investments")
  - Company-specific items (e.g., "Loss on redemption of debt", "Transaction costs")
  - Bundled categories that combine multiple REALPAC adjustments
  - Clearly an adjustment but doesn't match any A-Z category
- **Extraction priority:**
  1. **First:** Try to map to REALPAC categories (A-Z) - use exact matches when possible
  2. **If no match:** Extract as "Other" adjustment with EXACT description from issuer's table
- **How to extract Other adjustments:**
  - Use sequential labels: `other_1`, `other_2`, `other_3`, etc.
  - Copy the EXACT line item description from issuer's reconciliation table
  - Record amount (positive or negative as shown)
  - Note source page (e.g., "MD&A page 20")
- **Example Other adjustments:**
  - "Expected credit loss on preferred investments" → other_1
  - "Loss on redemption/modification of debt" → other_2
  - "Transaction costs - property dispositions" → other_3
  - "Impairment charges - non-real estate assets" → other_4
- **CRITICAL VALIDATION:**
  - Sum ALL adjustments (REALPAC A-Z + Other)
  - Compare to: Issuer-reported FFO minus Net Income = Total Adjustments
  - Flag if variance > 2% → indicates missing adjustments
  - Set `reconciliation_complete` = true if variance < 2%

**ACFO Components (OPTIONAL - for REALPAC ACFO calculation):**
- Enables calculating ACFO per REALPAC ACFO White Paper (January 2023)
- Look for "Consolidated Statements of Cash Flows" for starting point
- **Starting Point:** Cash flow from operations (IFRS) from cash flow statement
- **Key Adjustments to Extract (if disclosed in notes):**
  - **Adjustment 1:** Change in working capital (to eliminate non-sustainable fluctuations)
  - **Adjustment 2:** Interest expense in financing activities (add back)
  - **Adjustment 3:** JV distributions received OR calculated JV ACFO
  - **Adjustment 4:** Sustaining/maintenance CAPEX (should match AFFO Adj V)
  - **Adjustment 5:** External leasing costs only
  - **Adjustment 6:** Sustaining tenant improvements (should match AFFO Adj X)
  - **Adjustment 14:** Interest expense/income timing adjustments
  - **Adjustment 16:** ROU (Right of Use) asset adjustments for ground leases
- **Common Sections:**
  - Cash flow statement for CFO starting point
  - Notes showing "Non-IFRS measures" or "ACFO reconciliation"
  - May be in MD&A "Adjusted Cash Flow from Operations" section
- **Important:** Many issuers don't disclose full ACFO - extract what's available

**Portfolio Data:**
- Look in MD&A "PROPERTY PORTFOLIO" section
- Search for: "XX properties", "Portfolio Summary", "GLA", "Occupancy"
- Common table headers: "Property count", "GLA (000's S.F.)", "% Occupied"
- **GLA Units:** Usually shown as "9,549" meaning 9,549,000 SF → enter as `9549000`

**Debt Details:**
- Current vs non-current mortgages usually in Notes (e.g., "Note 11: Mortgages")
- Debentures in separate note (e.g., "Note 12: Debentures")
- Check cash flow statement for recent repayments

**Cash Flow from Investing Activities (OPTIONAL - for AFCF analysis):**
- Look for "Consolidated Statements of Cash Flows" or "Cash Flow Statement"
- Find the "INVESTING ACTIVITIES" section
- Extract the following (use NEGATIVE for outflows, POSITIVE for inflows):
  - **Development CAPEX:** "Additions to investment properties" or "Development expenditures" (negative)
    - Should match `capex_development_acfo` if extracting ACFO components
  - **Property Acquisitions:** "Acquisition of investment properties" (negative)
  - **Property Dispositions:** "Proceeds from sale of investment properties" (positive)
  - **JV Capital Contributions:** "Investment in equity accounted entities" or "Contributions to joint ventures" (negative)
  - **JV Return of Capital:** "Distribution from equity accounted entities" or "Return of capital from JVs" (positive)
  - **Business Combinations:** "Acquisition of subsidiaries" or "Business combinations" (negative)
  - **Total CFI:** "Net cash used in investing activities" (for reconciliation)
- **IMPORTANT:** Do NOT include sustaining CAPEX here - that's already in ACFO components
- **Sign Convention:** Outflows are negative, inflows are positive (as shown in cash flow statement)

**Cash Flow from Financing Activities (OPTIONAL - for AFCF coverage analysis):**
- Look in the "FINANCING ACTIVITIES" section of the cash flow statement
- Extract the following (use NEGATIVE for outflows, POSITIVE for inflows):
  - **Debt Principal Repayments:** "Repayment of mortgages" or "Principal payments on debt" (negative)
  - **New Debt Issuances:** "Proceeds from mortgages" or "Issuance of debentures" (positive)
  - **Distributions - Common:** "Distributions to unitholders" or "Dividends paid" (negative)
  - **Distributions - Preferred:** "Distributions on preferred units" (negative, if separate line)
  - **Distributions - NCI:** "Distributions to non-controlling interests" (negative, if separate line)
  - **Equity Issuances:** "Issuance of units" or "Proceeds from equity" (positive)
  - **Unit Buybacks:** "Repurchase of units" or "Unit buyback" (negative)
  - **Deferred Financing Costs:** "Deferred financing costs paid" (negative)
  - **Total CFF:** "Net cash from (used in) financing activities" (for reconciliation)
- **Note:** Some statements combine all distributions into one line - extract as `distributions_common`
- **Sign Convention:** Outflows are negative, inflows are positive (as shown in statement)

### Step 4: Self-Validate BEFORE Saving (CRITICAL)

**⚠️ DO NOT save the JSON file until ALL checks pass!**

Before proceeding to Step 5, perform these validation checks:

**Check 1: Required Field Presence**
Verify these REQUIRED fields exist and have non-zero values:
- ✅ `acfo_components.cash_flow_from_operations` (from cash flow statement)
- ✅ `balance_sheet.cash` (from balance sheet)
- ✅ `liquidity.cash_and_equivalents` (must equal balance_sheet.cash)
- ✅ `liquidity.undrawn_credit_facilities` (from credit facility note or MD&A)

**Check 2: Field Name Accuracy**
Compare your field names against the schema checklist above:
- ✅ Used `cash_and_equivalents` (NOT "cash") in liquidity section
- ✅ Used `development_capex` (NOT "capex_investment_properties")
- ✅ Used `undrawn_credit_facilities` (NOT "revolver_available")
- ✅ Used `other_investing_outflows` (NOT "capex_other")

**Check 3: Section Placement**
- ✅ `leasing_costs` and `tenant_improvements` are in `acfo_components` (NOT in cash_flow_investing)
- ✅ `development_capex` is in `cash_flow_investing` (NOT in acfo_components)
- ✅ `balance_sheet` has FLAT structure (no nested objects)

**Check 4: Data Quality**
- ✅ Numbers have no commas or $ signs
- ✅ Rates are decimals (0.878 not 87.8)
- ✅ Interest expense is POSITIVE
- ✅ Occupancy between 0.0-1.0
- ✅ Balance sheet approximately balances

**If any check fails:**
1. ❌ DO NOT save the file
2. 🔍 Review the schema again
3. 🔧 Correct the field names/structure/values
4. 🔄 Retry all checks
5. ✅ Only proceed to Step 5 when ALL checks pass

### Step 5: Save JSON

**Only after Step 4 validation passes:**

Save to: `{output_path}`

### Step 6: Validate Schema

Run validation:
```bash
python scripts/validate_extraction_schema.py {output_path}
```

Fix any errors before proceeding to Phase 3.

---

## REFERENCE DOCUMENTS

**Schema & Templates:**
- Schema specification: `.claude/knowledge/phase2_extraction_schema_v2.json`
- Template with examples: `.claude/knowledge/phase2_extraction_template.json`
- Full schema documentation: `.claude/knowledge/SCHEMA_README.md`

**Comprehensive Extraction Guide (NEW - v1.0.11):**
- **Detailed extraction guide:** `.claude/knowledge/COMPREHENSIVE_EXTRACTION_GUIDE.md`
- **Purpose:** Step-by-step instructions for extracting FFO/AFFO/ACFO components
- **Includes:**
  - 26 FFO/AFFO adjustments (A-U + V-Z) with lookup tables
  - 17 ACFO adjustments with consistency checks
  - Cash flow investing/financing extraction
  - Liquidity and dilution data extraction (including multiple credit facilities)
  - Credit facility extraction priority order (MD&A → Notes → Balance Sheet)
  - Handling conflicting information and borrowing base limitations
  - Validation procedures and sign conventions
- **🔥 READ THIS GUIDE FIRST** before starting comprehensive extraction

---

**IMPORTANT:**
- Read the markdown files using the Read tool (do NOT ask user for content)
- Search thoroughly across all files for portfolio data
- Use exact field names from schema
- Save valid JSON to output path specified above
"""

    return prompt


def create_pdf_direct_extraction_prompt(pdf_files, output_path, issuer_name):
    """
    Create extraction prompt for DIRECT PDF→JSON extraction

    Skips markdown conversion entirely, reads PDFs directly.

    Args:
        pdf_files: List of PDF file paths
        output_path: Path where JSON should be saved
        issuer_name: Name of issuer

    Returns:
        str: Compact prompt for Claude Code
    """

    # Load schema from single source of truth
    schema_path = Path(__file__).parent.parent / '.claude' / 'knowledge' / 'phase2_extraction_schema_v2.json'

    # Generate pre-filled template
    template = generate_template_from_schema(schema_path)

    # Create file list with paths
    file_list = "\n".join([f"- `{f}`" for f in pdf_files])

    prompt = f"""# Phase 2: Extract Financial Data for {issuer_name} (DIRECT PDF EXTRACTION)

**Task:** Extract structured financial data DIRECTLY from PDF files and save as JSON.

**Input Files (PDFs):**
{file_list}

**Output File:** `{output_path}`

---

## EXTRACTION INSTRUCTIONS

### Step 1: Read PDFs Directly
Use the Read tool to access each PDF file listed above. Claude Code can read PDFs natively.

### Step 2: Extract Required Data

**IMPORTANT: Use this EXACT JSON structure** (fill in actual values from source documents, keep structure unchanged):

This pre-filled template includes ALL required fields with correct names and structure:

```json
{json.dumps(template, indent=2)}
```

**Schema Rules:**
1. **Top-level fields:** issuer_name, reporting_date, currency (NOT nested in issuer_info)
2. **Exact field names:** Use names EXACTLY as shown above (e.g., 'cash' not 'cash_and_equivalents' in balance_sheet)
3. **All required fields:** Every field shown above must be present
4. **Use 0 for missing numeric values** (NOT null)
5. **Flat structure:** No unnecessary nesting (balance_sheet is flat, not nested by period)

**Full schema specification available at:** `.claude/knowledge/phase2_extraction_schema_v2.json`

### Step 3: Data Extraction Guidelines

**CRITICAL RULES:**
1. **Numbers:** No commas or $ signs (e.g., `2611435` not `$2,611,435`)
2. **Units:** All amounts in thousands (as shown in statements)
3. **Decimals:** Rates as decimals (e.g., `0.878` for 87.8%, NOT `87.8`)
4. **Field Names:** EXACTLY as shown above
5. **Structure:** FLAT - no nested objects in balance_sheet
6. **Most Recent Period:** Use latest period data (e.g., Q2 2025, six months)

**CRITICAL FIELD NAMES - VALIDATION CHECKLIST**

⚠️ **Most Common Extraction Errors** (check these BEFORE saving):

**acfo_components:**
- ✅ `cash_flow_from_operations` (NOT "cash_from_operations", NOT "cfo", NOT "operating_cash_flow")
  - **Location:** Cash Flow Statement - "Cash provided by operating activities"
  - **Required:** This field is MANDATORY - without it, ACFO/AFCF/burn rate cannot be calculated

**cash_flow_investing:**
- ✅ `development_capex` (NOT "capex_investment_properties", NOT "development_capital_expenditures")
- ✅ `other_investing_outflows` (NOT "capex_other", NOT "other_capex")

**liquidity:**
- ✅ `cash_and_equivalents` (NOT "cash", NOT "cash_equivalents")
- ✅ `undrawn_credit_facilities` (NOT "revolver_available", NOT "available_credit", NOT "undrawn_revolver")

**Common Section Mistakes:**
- ❌ DO NOT put `leasing_costs` or `tenant_improvements` in `cash_flow_investing`
  - ✅ They belong in `acfo_components` and `ffo_affo_components`
- ❌ DO NOT use `cash` in liquidity section
  - ✅ Use `cash_and_equivalents` (even if source says "cash")

**FIELD NAME MAPPING TABLE**

Use this table to map terms in financial statements → correct schema field names:

| Source Document Term | Schema Field Name | Section | Notes |
|---------------------|-------------------|---------|-------|
| "Cash and cash equivalents" | `cash_and_equivalents` | liquidity | Use even if balance sheet says "Cash" |
| "Cash" (balance sheet line) | `cash` | balance_sheet | For balance sheet consistency only |
| "Cash provided by operating activities" | `cash_flow_from_operations` | acfo_components | REQUIRED field |
| "Available capacity" / "Undrawn" | `undrawn_credit_facilities` | liquidity | Sum across all facilities |
| "Revolver available" | `undrawn_credit_facilities` | liquidity | NOT "revolver_available" |
| "Additions to investment properties" | `development_capex` | cash_flow_investing | Negative number |
| "Development expenditures" | `development_capex` | cash_flow_investing | NOT "capex_investment_properties" |
| "Property acquisitions" | `property_acquisitions` | cash_flow_investing | Negative number |
| "Proceeds from dispositions" | `property_dispositions` | cash_flow_investing | Positive number |
| "Leasing commissions" | `leasing_costs` | acfo_components | NOT in cash_flow_investing |
| "Tenant improvements" | `tenant_improvements` | acfo_components | NOT in cash_flow_investing |

**WHERE TO FIND DATA:**

**Balance Sheet:**
- Look for "Consolidated Balance Sheets" or "Statement of Financial Position"
- Usually in consolidated financial statements PDF
- Extract: total_assets, cash, mortgages (current/non-current), debentures, equity

**Income Statement:**
- Look for "Consolidated Statements of Operations" or "Statement of Income"
- Calculate NOI = Revenue - Operating Expenses - Realty Taxes
- Extract: revenue, NOI, interest expense, net income

**FFO/AFFO (Basic - Required):**
- Usually in MD&A document
- Look for "FFO and AFFO" section or tables showing "Funds from Operations"
- Extract: FFO, AFFO, per unit amounts, payout ratios
- **Minimum Required:** `ffo`, `affo`, `ffo_per_unit`, `affo_per_unit`, `distributions_per_unit`

**FFO/AFFO Components (COMPREHENSIVE - enables reconciliation tables):**
- Enables calculating FFO/AFFO from first principles per REALPAC methodology (Jan 2022)
- Look in "Notes to Financial Statements" - often has FFO/AFFO reconciliation table
- **Starting Point:** Net income from Statement of Comprehensive Income
- **Key Adjustments to Extract:**
  - **Adjustment A:** Unrealized fair value changes in investment properties
  - **Adjustment B:** Depreciation of depreciable real estate assets
  - **Adjustment C:** Amortization of tenant allowances
  - **Adjustment D:** Amortization of tenant/customer relationship intangibles
  - **Adjustment E:** Gains/losses from property sales
  - **Adjustment V (for AFFO):** Sustaining capital expenditures
  - **Adjustment W (for AFFO):** Leasing costs (internal + external)
  - **Adjustment X (for AFFO):** Tenant improvements (sustaining only)
  - **Adjustment Y (for AFFO):** Straight-line rent adjustment
- **Common Section:** "Reconciliation of Net Income to FFO" or "FFO Calculation"
- **Note:** Extract actual amounts shown in reconciliation, not formulas

**FFO/AFFO "Other" Adjustments (NEW - for complete reconciliation):**
- **Purpose:** Capture issuer-specific adjustments that don't fit REALPAC A-Z categories
- **When to use "Other" adjustments:**
  - Issuer uses non-standard terminology (e.g., "Expected credit loss on preferred investments")
  - Company-specific items (e.g., "Loss on redemption of debt", "Transaction costs")
  - Bundled categories that combine multiple REALPAC adjustments
  - Clearly an adjustment but doesn't match any A-Z category
- **Extraction priority:**
  1. **First:** Try to map to REALPAC categories (A-Z) - use exact matches when possible
  2. **If no match:** Extract as "Other" adjustment with EXACT description from issuer's table
- **How to extract Other adjustments:**
  - Use sequential labels: `other_1`, `other_2`, `other_3`, etc.
  - Copy the EXACT line item description from issuer's reconciliation table
  - Record amount (positive or negative as shown)
  - Note source page (e.g., "MD&A page 20")
- **Example Other adjustments:**
  - "Expected credit loss on preferred investments" → other_1
  - "Loss on redemption/modification of debt" → other_2
  - "Transaction costs - property dispositions" → other_3
  - "Impairment charges - non-real estate assets" → other_4
- **CRITICAL VALIDATION:**
  - Sum ALL adjustments (REALPAC A-Z + Other)
  - Compare to: Issuer-reported FFO minus Net Income = Total Adjustments
  - Flag if variance > 2% → indicates missing adjustments
  - Set `reconciliation_complete` = true if variance < 2%

**ACFO Components (OPTIONAL - for REALPAC ACFO calculation):**
- Enables calculating ACFO per REALPAC ACFO White Paper (January 2023)
- Look for "Consolidated Statements of Cash Flows" for starting point
- **Starting Point:** Cash flow from operations (IFRS) from cash flow statement
- **Key Adjustments to Extract (if disclosed in notes):**
  - **Adjustment 1:** Change in working capital (to eliminate non-sustainable fluctuations)
  - **Adjustment 2:** Interest expense in financing activities (add back)
  - **Adjustment 3:** JV distributions received OR calculated JV ACFO
  - **Adjustment 4:** Sustaining/maintenance CAPEX (should match AFFO Adj V)
  - **Adjustment 5:** External leasing costs only
  - **Adjustment 6:** Sustaining tenant improvements (should match AFFO Adj X)
  - **Adjustment 14:** Interest expense/income timing adjustments
  - **Adjustment 16:** ROU (Right of Use) asset adjustments for ground leases
- **Common Sections:**
  - Cash flow statement for CFO starting point
  - Notes showing "Non-IFRS measures" or "ACFO reconciliation"
  - May be in MD&A "Adjusted Cash Flow from Operations" section
- **Important:** Many issuers don't disclose full ACFO - extract what's available

**Portfolio Data:**
- Look in MD&A "PROPERTY PORTFOLIO" section
- Search for: "XX properties", "Portfolio Summary", "GLA", "Occupancy"
- Common table headers: "Property count", "GLA (000's S.F.)", "% Occupied"
- **GLA Units:** Usually shown as "9,549" meaning 9,549,000 SF → enter as `9549000`

**Debt Details:**
- Current vs non-current mortgages usually in Notes (e.g., "Note 11: Mortgages")
- Debentures in separate note (e.g., "Note 12: Debentures")
- Check cash flow statement for recent repayments

**Cash Flow from Investing Activities (OPTIONAL - for AFCF analysis):**
- Look for "Consolidated Statements of Cash Flows" or "Cash Flow Statement"
- Find the "INVESTING ACTIVITIES" section
- Extract the following (use NEGATIVE for outflows, POSITIVE for inflows):
  - **Development CAPEX:** "Additions to investment properties" or "Development expenditures" (negative)
    - Should match `capex_development_acfo` if extracting ACFO components
  - **Property Acquisitions:** "Acquisition of investment properties" (negative)
  - **Property Dispositions:** "Proceeds from sale of investment properties" (positive)
  - **JV Capital Contributions:** "Investment in equity accounted entities" or "Contributions to joint ventures" (negative)
  - **JV Return of Capital:** "Distribution from equity accounted entities" or "Return of capital from JVs" (positive)
  - **Business Combinations:** "Acquisition of subsidiaries" or "Business combinations" (negative)
  - **Total CFI:** "Net cash used in investing activities" (for reconciliation)
- **IMPORTANT:** Do NOT include sustaining CAPEX here - that's already in ACFO components
- **Sign Convention:** Outflows are negative, inflows are positive (as shown in cash flow statement)

**Cash Flow from Financing Activities (OPTIONAL - for AFCF coverage analysis):**
- Look in the "FINANCING ACTIVITIES" section of the cash flow statement
- Extract the following (use NEGATIVE for outflows, POSITIVE for inflows):
  - **Debt Principal Repayments:** "Repayment of mortgages" or "Principal payments on debt" (negative)
  - **New Debt Issuances:** "Proceeds from mortgages" or "Issuance of debentures" (positive)
  - **Distributions - Common:** "Distributions to unitholders" or "Dividends paid" (negative)
  - **Distributions - Preferred:** "Distributions on preferred units" (negative, if separate line)
  - **Distributions - NCI:** "Distributions to non-controlling interests" (negative, if separate line)
  - **Equity Issuances:** "Issuance of units" or "Proceeds from equity" (positive)
  - **Unit Buybacks:** "Repurchase of units" or "Unit buyback" (negative)
  - **Deferred Financing Costs:** "Deferred financing costs paid" (negative)
  - **Total CFF:** "Net cash from (used in) financing activities" (for reconciliation)
- **Note:** Some statements combine all distributions into one line - extract as `distributions_common`
- **Sign Convention:** Outflows are negative, inflows are positive (as shown in statement)

### Step 4: Self-Validate BEFORE Saving (CRITICAL)

**⚠️ DO NOT save the JSON file until ALL checks pass!**

Before proceeding to Step 5, perform these validation checks:

**Check 1: Required Field Presence**
Verify these REQUIRED fields exist and have non-zero values:
- ✅ `acfo_components.cash_flow_from_operations` (from cash flow statement)
- ✅ `balance_sheet.cash` (from balance sheet)
- ✅ `liquidity.cash_and_equivalents` (must equal balance_sheet.cash)
- ✅ `liquidity.undrawn_credit_facilities` (from credit facility note or MD&A)

**Check 2: Field Name Accuracy**
Compare your field names against the schema checklist above:
- ✅ Used `cash_and_equivalents` (NOT "cash") in liquidity section
- ✅ Used `development_capex` (NOT "capex_investment_properties")
- ✅ Used `undrawn_credit_facilities` (NOT "revolver_available")
- ✅ Used `other_investing_outflows` (NOT "capex_other")

**Check 3: Section Placement**
- ✅ `leasing_costs` and `tenant_improvements` are in `acfo_components` (NOT in cash_flow_investing)
- ✅ `development_capex` is in `cash_flow_investing` (NOT in acfo_components)
- ✅ `balance_sheet` has FLAT structure (no nested objects)

**Check 4: Data Quality**
- ✅ Numbers have no commas or $ signs
- ✅ Rates are decimals (0.878 not 87.8)
- ✅ Interest expense is POSITIVE
- ✅ Occupancy between 0.0-1.0
- ✅ Balance sheet approximately balances

**If any check fails:**
1. ❌ DO NOT save the file
2. 🔍 Review the schema again
3. 🔧 Correct the field names/structure/values
4. 🔄 Retry all checks
5. ✅ Only proceed to Step 5 when ALL checks pass

### Step 5: Save JSON

**Only after Step 4 validation passes:**

Save to: `{output_path}`

### Step 6: Validate Schema

Run validation:
```bash
python scripts/validate_extraction_schema.py {output_path}
```

Fix any errors before proceeding to Phase 3.

---

## REFERENCE DOCUMENTS

**Schema & Templates:**
- Schema specification: `.claude/knowledge/phase2_extraction_schema_v2.json`
- Template with examples: `.claude/knowledge/phase2_extraction_template.json`
- Full schema documentation: `.claude/knowledge/SCHEMA_README.md`

**Comprehensive Extraction Guide (NEW - v1.0.11):**
- **Detailed extraction guide:** `.claude/knowledge/COMPREHENSIVE_EXTRACTION_GUIDE.md`
- **Purpose:** Step-by-step instructions for extracting FFO/AFFO/ACFO components
- **Includes:**
  - 26 FFO/AFFO adjustments (A-U + V-Z) with lookup tables
  - 17 ACFO adjustments with consistency checks
  - Cash flow investing/financing extraction
  - Liquidity and dilution data extraction (including multiple credit facilities)
  - Credit facility extraction priority order (MD&A → Notes → Balance Sheet)
  - Handling conflicting information and borrowing base limitations
  - Validation procedures and sign conventions
- **🔥 READ THIS GUIDE FIRST** before starting comprehensive extraction

---

**IMPORTANT:**
- Read the PDF files using the Read tool (Claude Code has native PDF support)
- Search thoroughly across all files for portfolio data
- Use exact field names from schema
- Save valid JSON to output path specified above
"""

    return prompt


def main():
    """Main execution - creates efficient extraction prompt"""
    import argparse
    import re

    parser = argparse.ArgumentParser(
        description='Phase 2 (EFFICIENT): Extract financial metrics - Supports markdown or PDF input',
        epilog='Example: python extract_key_metrics_efficient.py --issuer-name "Artis REIT" FS.md MDA.md\n'
               'Example: python extract_key_metrics_efficient.py --issuer-name "Artis REIT" --pdf statements.pdf mda.pdf'
    )
    parser.add_argument(
        'input_files',
        nargs='+',
        help='Input file(s) - can be markdown (.md) or PDF (.pdf) files'
    )
    parser.add_argument(
        '--issuer-name',
        required=True,
        help='Issuer name'
    )
    parser.add_argument(
        '--output',
        default=None,
        help='Output JSON path (default: auto-generated)'
    )
    parser.add_argument(
        '--pdf',
        action='store_true',
        help='Treat input as PDF files (direct PDF→JSON extraction)'
    )

    args = parser.parse_args()

    # Load configuration
    try:
        config = load_config()
    except Exception as e:
        print(f"⚠️  Warning: Could not load config ({e}), using defaults")
        config = None

    # Auto-generate output path
    if args.output is None:
        import re
        safe_name = args.issuer_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
        safe_name = re.sub(r'[^a-zA-Z0-9_-]', '', safe_name)
        # Use absolute path from current working directory
        cwd = Path.cwd()
        args.output = str(cwd / 'Issuer_Reports' / safe_name / 'temp' / 'phase2_extracted_data.json')

    # Determine extraction mode
    # Priority: 1) CLI flag --pdf, 2) Config setting, 3) Auto-detect from file extensions
    use_pdf_mode = False

    if args.pdf:
        # Explicit CLI flag
        use_pdf_mode = True
        extraction_mode = "PDF→JSON (CLI flag)"
    elif config and config.get_phase2_method() == "pdf_to_json":
        # Config setting
        use_pdf_mode = True
        extraction_mode = "PDF→JSON (config)"
    else:
        # Auto-detect from file extensions
        first_file = Path(args.input_files[0])
        if first_file.suffix.lower() == '.pdf':
            use_pdf_mode = True
            extraction_mode = "PDF→JSON (auto-detected)"
        else:
            extraction_mode = "Markdown→JSON (default)"

    print("=" * 70)
    print("PHASE 2: FINANCIAL DATA EXTRACTION (EFFICIENT MODE)")
    print("=" * 70)
    if config:
        config.print_active_config()
    print(f"Extraction mode: {extraction_mode}\n")

    # Validate input files exist
    input_paths = []
    total_size = 0
    file_type = "PDF" if use_pdf_mode else "Markdown"

    for input_file in args.input_files:
        input_path = Path(input_file)
        if not input_path.exists():
            print(f"❌ Error: File not found: {input_path}")
            sys.exit(1)

        size = input_path.stat().st_size
        total_size += size
        input_paths.append(str(input_path))
        print(f"✓ Found: {input_path.name} ({size/1024:.1f} KB)")

    print(f"\n📊 Total {file_type} size: {total_size/1024:.1f} KB")

    if use_pdf_mode:
        print(f"📊 Estimated tokens (PDF reading): ~{total_size//4:,}")
    else:
        print(f"📊 Estimated tokens if embedded: ~{total_size//4:,}")

    # Check if output exists and validate (for automatic retry)
    print(f"\n🔍 Checking for existing extraction...")
    exists, is_valid, errors, previous_data, attempt_number = check_and_validate_existing_output(args.output)

    MAX_ATTEMPTS = 3

    if exists and is_valid:
        # Extraction completed successfully!
        print(f"✅ Extraction already complete and valid!")
        print(f"   Output: {args.output}")
        print(f"   Issuer: {previous_data.get('issuer_name', 'Unknown')}")
        print(f"   Reporting Date: {previous_data.get('reporting_date', 'Unknown')}")
        print("\n✅ This file is compatible with Phase 3 calculations")
        print("\n💡 To re-extract, delete the output file and run again")
        sys.exit(0)

    elif exists and not is_valid:
        # Validation failed - generate retry prompt
        next_attempt = attempt_number + 1

        if next_attempt > MAX_ATTEMPTS:
            # Max retries exceeded
            print(f"❌ Maximum retry attempts ({MAX_ATTEMPTS}) exceeded")
            print(f"\nLast extraction had {len(errors)} validation errors:")
            for error in errors[:10]:
                print(f"  {error}")

            # Save failed extraction
            save_failed_extraction(args.output, previous_data, errors, attempt_number)

            print(f"\n💡 Manual intervention required:")
            print(f"   1. Review failed extraction: {args.output}")
            print(f"   2. Check validation errors above")
            print(f"   3. Fix manually or delete output file to start fresh")
            print(f"\n📚 Schema reference: .claude/knowledge/phase2_extraction_schema_v2.json")
            sys.exit(1)

        # Generate retry prompt
        print(f"⚠️  Previous extraction (attempt {attempt_number}) failed validation")
        print(f"   Found {len([e for e in errors if e.startswith('❌')])} errors")
        print(f"\n🔄 Generating RETRY prompt (attempt {next_attempt}/{MAX_ATTEMPTS})...")

        # Save failed attempt for debugging
        save_failed_extraction(args.output, previous_data, errors, attempt_number)

        # Update retry metadata
        save_retry_metadata(args.output, next_attempt)

        # Generate retry prompt with errors
        prompt = create_retry_prompt(
            input_paths,
            args.output,
            args.issuer_name,
            errors,
            previous_data,
            next_attempt
        )

        # Save retry prompt
        output_dir = Path(args.output).parent
        prompt_path = output_dir / f'phase2_extraction_prompt_RETRY{next_attempt}.txt'

    else:
        # No existing extraction - generate initial prompt
        print(f"   No existing extraction found")
        print(f"\n🚀 Creating extraction prompt (attempt 1/{MAX_ATTEMPTS})...")

        # Initialize retry metadata
        save_retry_metadata(args.output, 1)

        # Generate initial prompt
        if use_pdf_mode:
            print("   (Direct PDF→JSON extraction, skips Phase 1)")
            prompt = create_pdf_direct_extraction_prompt(
                input_paths,
                args.output,
                args.issuer_name
            )
        else:
            print("   (References file paths instead of embedding content)")
            prompt = create_efficient_extraction_prompt(
                input_paths,
                args.output,
                args.issuer_name
            )

        # Save initial prompt
        output_dir = Path(args.output).parent
        prompt_path = output_dir / 'phase2_extraction_prompt.txt'

    # Save prompt (unified for both initial and retry)
    prompt_path.parent.mkdir(parents=True, exist_ok=True)

    with open(prompt_path, 'w') as f:
        f.write(prompt)

    prompt_size = len(prompt)
    print(f"\n✅ Extraction prompt saved: {prompt_path}")
    print(f"   Prompt size: {prompt_size/1024:.1f} KB (~{prompt_size//4:,} tokens)")

    if not use_pdf_mode and not (exists and not is_valid):
        print(f"   🎯 Token reduction: ~{total_size//4:,} → ~{prompt_size//4:,} tokens")
        print(f"   💰 Efficiency gain: {100*(1-prompt_size/total_size):.1f}% smaller")

    # Instructions - different for retry vs initial
    print("\n" + "=" * 70)
    print("NEXT STEPS")
    print("=" * 70)

    if exists and not is_valid:
        # Retry instructions
        next_attempt = attempt_number + 1
        print(f"\n🔄 RETRY EXTRACTION (Attempt {next_attempt}/{MAX_ATTEMPTS})")
        print(f"\n📋 Previous attempt had {len([e for e in errors if e.startswith('❌')])} validation errors")
        print(f"   Retry prompt includes:")
        print(f"   • Specific error guidance")
        print(f"   • Corrected template structure")
        print(f"   • Validation checklist")
        print(f"\n📋 Claude Code will now:")
        print(f"   1. Read the RETRY extraction prompt")
        if use_pdf_mode:
            print(f"   2. Use Read tool to access PDF files")
        else:
            print(f"   2. Use Read tool to access markdown files")
        print(f"   3. Re-extract financial data FIXING previous errors")
        print(f"   4. Self-validate before saving")
        print(f"   5. Overwrite JSON: {args.output}")
        print(f"\n⚠️  After extraction, run this script again to validate")
        print(f"   If validation passes: ✅ Complete!")
        print(f"   If validation fails: 🔄 Auto-retry (up to attempt {MAX_ATTEMPTS})")
    else:
        # Initial extraction instructions
        print(f"\n📋 Claude Code will now:")
        print(f"   1. Read the extraction prompt")
        if use_pdf_mode:
            print(f"   2. Use Read tool to access PDF files directly")
        else:
            print(f"   2. Use Read tool to access markdown files")
        print(f"   3. Extract financial data per schema")
        print(f"   4. Validate extraction")
        print(f"   5. Save JSON to: {args.output}")
        print(f"\n⚠️  After extraction, run this script again to validate")
        print(f"   If validation passes: ✅ Complete!")
        print(f"   If validation fails: 🔄 Auto-retry with error corrections (up to {MAX_ATTEMPTS} attempts)")

    print("\n⏳ Ready for Claude Code extraction...")
    print("=" * 70)

    sys.exit(0)


if __name__ == "__main__":
    main()
