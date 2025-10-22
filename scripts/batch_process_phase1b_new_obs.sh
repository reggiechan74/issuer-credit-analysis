#!/bin/bash
# Batch process Phase 2-3 for new Phase 1B observations (obs 22-27)
# Run after all Phase 1 conversions complete

set -e  # Exit on error

echo "========================================"
echo "Phase 1B Batch Processing: Observations 22-27"
echo "========================================"
echo ""

# Base directory
BASE_DIR="/workspaces/issuer-credit-analysis"
EXTRACTION_DIR="$BASE_DIR/Issuer_Reports/phase1b/extractions"

# Function to process a single observation through Phase 2-3
process_observation() {
    local obs_num=$1
    local issuer_name=$2
    local period=$3
    local markdown_dir=$4
    local cut_type=${5:-"CONTROL"}  # Default to CONTROL unless specified

    echo "----------------------------------------"
    echo "Processing Observation $obs_num: $issuer_name $period"
    echo "----------------------------------------"

    # Find markdown files
    local md_files=$(find "$markdown_dir" -name "*.md" -type f 2>/dev/null | tr '\n' ' ')

    if [ -z "$md_files" ]; then
        echo "ERROR: No markdown files found in $markdown_dir"
        return 1
    fi

    echo "Found markdown files: $md_files"

    # Phase 2: Extract data (using financial_data_extractor agent)
    echo "Phase 2: Extracting financial data..."
    local extraction_file="$EXTRACTION_DIR/obs${obs_num}_${issuer_name// /_}_${period//()/}_extracted_data.json"

    # Note: This requires manual agent invocation - placeholder for now
    echo "  → Extraction target: $extraction_file"
    echo "  → (Agent invocation required - see script output)"

    # Phase 3: Calculate metrics (only if extraction exists)
    if [ -f "$extraction_file" ]; then
        echo "Phase 3: Calculating credit metrics..."
        python "$BASE_DIR/scripts/calculate_credit_metrics.py" "$extraction_file"

        # Rename phase3 output with obs number
        local phase3_output="$EXTRACTION_DIR/phase3_calculated_metrics.json"
        local phase3_renamed="$EXTRACTION_DIR/obs${obs_num}_${issuer_name// /_}_${period//()/}_phase3_metrics.json"

        if [ -f "$phase3_output" ]; then
            mv "$phase3_output" "$phase3_renamed"
            echo "  ✓ Phase 3 complete: $phase3_renamed"
        fi
    else
        echo "  ⚠  Skipping Phase 3 (extraction file not found)"
    fi

    echo ""
}

# Process each new observation

# Obs 22: RioCan 2023
process_observation 22 "RioCan_REIT" "Q4_2023" \
    "$BASE_DIR/Issuer_Reports/RioCan_REIT/temp/phase1_markdown" "CONTROL"

# Obs 23: Boardwalk 2024
process_observation 23 "Boardwalk_REIT" "Q4_2024" \
    "$BASE_DIR/Issuer_Reports/Boardwalk_REIT/temp/phase1_markdown" "CONTROL"

# Obs 24: Dream Industrial 2024
process_observation 24 "Dream_Industrial_REIT" "Q4_2024" \
    "$BASE_DIR/Issuer_Reports/Dream_Industrial_REIT/temp/phase1_markdown" "CONTROL"

# Obs 25: First Capital 2023
process_observation 25 "First_Capital_REIT" "Q4_2023" \
    "$BASE_DIR/Issuer_Reports/First_Capital_REIT/temp/phase1_markdown" "CONTROL"

# Obs 26: Killam 2023
process_observation 26 "Killam_Apartment_REIT" "Q4_2023" \
    "$BASE_DIR/Issuer_Reports/Killam_Apartment_REIT/temp/phase1_markdown" "CONTROL"

# Obs 27: Choice Properties 2024
process_observation 27 "Choice_Properties_REIT" "Q4_2024" \
    "$BASE_DIR/Issuer_Reports/Choice_Properties_REIT/temp/phase1_markdown" "CONTROL"

echo "========================================"
echo "Batch Processing Complete"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Review extraction files in: $EXTRACTION_DIR"
echo "2. Run market + macro data collection"
echo "3. Merge expanded dataset and retrain model"
