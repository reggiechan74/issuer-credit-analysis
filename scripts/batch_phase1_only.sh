#!/bin/bash
# Batch run Phase 1 (PDF → Markdown) for all 20 Phase 1B observations

set -e

echo "======================================================================"
echo "Phase 1B: Batch PDF → Markdown Conversion"
echo "======================================================================"
echo "Processing 20 observations..."
echo ""

# Array of observations: (num:ticker:name:quarter:year)
observations=(
    "1:HR-UN.TO:H&R REIT:Q4:2022"
    "2:AX-UN.TO:Artis REIT:Q4:2022"
    "3:SOT-UN.TO:Slate Office REIT:Q1:2023"
    "4:D-UN.TO:Dream Office REIT:Q2:2023"
    "5:NWH-UN.TO:NorthWest Healthcare Properties REIT:Q2:2023"
    "6:AP-UN.TO:Allied Properties REIT:Q4:2023"
    "7:HR-UN.TO:H&R REIT:Q4:2023"
    "8:CAR-UN.TO:Canadian Apartment Properties REIT:Q4:2024"
    "9:HR-UN.TO:H&R REIT:Q4:2024"
    "10:ERE-UN.TO:European Residential REIT:Q4:2024"
    "11:CRT-UN.TO:CT REIT:Q3:2022"
    "12:NXR-UN.TO:Nexus Industrial REIT:Q3:2022"
    "13:CRT-UN.TO:CT REIT:Q1:2023"
    "14:NXR-UN.TO:Nexus Industrial REIT:Q2:2023"
    "15:IIP-UN.TO:InterRent REIT:Q2:2023"
    "16:EXE.TO:Extendicare:Q3:2023"
    "17:SRU-UN.TO:SmartCentres REIT:Q3:2023"
    "18:PLZ-UN.TO:Plaza Retail REIT:Q3:2024"
    "19:CRT-UN.TO:CT REIT:Q4:2024"
    "20:EXE.TO:Extendicare:Q4:2024"
)

completed=0
failed=0

for obs in "${observations[@]}"; do
    IFS=':' read -r num ticker name quarter year <<< "$obs"

    echo "----------------------------------------------------------------------"
    echo "[$((completed + failed + 1))/20] Obs $num: $name $quarter $year"
    echo "----------------------------------------------------------------------"

    # Find PDF directory
    pdf_dir="Issuer_Reports/phase1b/pdfs/$(printf "%02d" $num)_${ticker//.TO/}_${quarter}_${year}"

    if [ ! -d "$pdf_dir" ]; then
        echo "✗ PDF directory not found: $pdf_dir"
        ((failed++))
        continue
    fi

    # Find PDFs
    pdf_files=$(find "$pdf_dir" -name "*.pdf" 2>/dev/null)
    if [ -z "$pdf_files" ]; then
        echo "✗ No PDFs found in $pdf_dir"
        ((failed++))
        continue
    fi

    pdf_count=$(echo "$pdf_files" | wc -l)
    echo "Found $pdf_count PDF(s)"

    # Run Phase 1
    echo "Running Phase 1..."
    if python scripts/preprocess_pdfs_enhanced.py --issuer-name "$name" $pdf_files > /tmp/phase1_${num}.log 2>&1; then
        echo "✓ Phase 1 complete"
        ((completed++))
    else
        echo "✗ Phase 1 failed (see /tmp/phase1_${num}.log)"
        ((failed++))
    fi
    echo ""
done

echo "======================================================================"
echo "PHASE 1 COMPLETE"
echo "======================================================================"
echo "Success: $completed/20"
echo "Failed: $failed/20"
echo ""
echo "Next: Run Phase 2-3 sequentially for each observation"
