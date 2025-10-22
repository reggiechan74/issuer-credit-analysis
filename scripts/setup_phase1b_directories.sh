#!/bin/bash
# Setup Phase 1B directory structure for PDF downloads
# Creates 20 directories for the 20 observations

set -e

BASE_DIR="Issuer_Reports/phase1b/pdfs"

echo "Creating Phase 1B PDF download directories..."

# Target Cuts (1-10)
mkdir -p "${BASE_DIR}/01_HR-UN_Q4_2022"
mkdir -p "${BASE_DIR}/02_AX-UN_Q4_2022"
mkdir -p "${BASE_DIR}/03_SOT-UN_Q1_2023"
mkdir -p "${BASE_DIR}/04_D-UN_Q2_2023"
mkdir -p "${BASE_DIR}/05_NWH-UN_Q2_2023"
mkdir -p "${BASE_DIR}/06_AP-UN_Q4_2023"
mkdir -p "${BASE_DIR}/07_HR-UN_Q4_2023"
mkdir -p "${BASE_DIR}/08_CAR-UN_Q4_2024"
mkdir -p "${BASE_DIR}/09_HR-UN_Q4_2024"
mkdir -p "${BASE_DIR}/10_ERE-UN_Q4_2024"

# Matched Controls (11-20)
mkdir -p "${BASE_DIR}/11_CRT-UN_Q3_2022"
mkdir -p "${BASE_DIR}/12_NXR-UN_Q3_2022"
mkdir -p "${BASE_DIR}/13_CRT-UN_Q1_2023"
mkdir -p "${BASE_DIR}/14_NXR-UN_Q2_2023"
mkdir -p "${BASE_DIR}/15_IIP-UN_Q2_2023"
mkdir -p "${BASE_DIR}/16_EXE_Q3_2023"
mkdir -p "${BASE_DIR}/17_SRU-UN_Q3_2023"
mkdir -p "${BASE_DIR}/18_PLZ-UN_Q3_2024"
mkdir -p "${BASE_DIR}/19_CRT-UN_Q4_2024"
mkdir -p "${BASE_DIR}/20_EXE_Q4_2024"

echo "✓ Created 20 directories in ${BASE_DIR}/"

# Create placeholder README in each directory
for dir in ${BASE_DIR}/*/; do
    obs_name=$(basename "$dir")
    cat > "${dir}/README.txt" << EOF
Phase 1B Observation: ${obs_name}

Required files:
1. ${obs_name}_statements.pdf - Quarterly/Annual Financial Statements
2. ${obs_name}_mda.pdf - Management's Discussion and Analysis

Download from: https://www.sedarplus.ca/

See: Issuer_Reports/phase1b/SEDAR_PLUS_DOWNLOAD_INSTRUCTIONS.md
EOF
done

echo "✓ Created README.txt placeholders in each directory"

# List all directories
echo ""
echo "Created directories:"
ls -1 "${BASE_DIR}/" | nl

echo ""
echo "✅ Phase 1B directory structure ready!"
echo "   Next: Download PDFs following SEDAR_PLUS_DOWNLOAD_INSTRUCTIONS.md"
echo "   Verify: Run scripts/verify_phase1b_downloads.py"
