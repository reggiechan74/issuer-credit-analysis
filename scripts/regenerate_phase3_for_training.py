#!/usr/bin/env python3
"""
Regenerate Phase 3 metrics for all 24 training observations using current sustainable AFCF methodology.
"""

import subprocess
from pathlib import Path

# Define the 24 observations needed for training
observations = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 18, 19, 20, 21, 22, 25, 26, 27]

extractions_dir = Path("Issuer_Reports/phase1b/extractions")

print("="*70)
print("Regenerating Phase 3 Metrics with Sustainable AFCF")
print("="*70)
print(f"\nProcessing {len(observations)} observations...")
print()

success_count = 0
error_count = 0
errors = []

for obs_num in observations:
    # Find the Phase 2 extracted data file for this observation
    phase2_files = list(extractions_dir.glob(f"obs{obs_num}_*_extracted_data.json"))

    if not phase2_files:
        print(f"❌ Observation {obs_num}: Phase 2 file not found")
        error_count += 1
        errors.append((obs_num, "Phase 2 file not found"))
        continue

    phase2_file = phase2_files[0]
    obs_name = phase2_file.stem.replace("_extracted_data", "")
    output_file = extractions_dir / f"{obs_name}_phase3_metrics_v2.json"

    print(f"Processing obs{obs_num}: {phase2_file.name}")

    try:
        # Run calculate_credit_metrics.py
        result = subprocess.run(
            ["python", "scripts/calculate_credit_metrics.py", str(phase2_file), "--output", str(output_file)],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            print(f"  ✓ Success: {output_file.name}")
            success_count += 1
        else:
            print(f"  ❌ Error: {result.stderr[:100]}")
            error_count += 1
            errors.append((obs_num, result.stderr[:200]))

    except subprocess.TimeoutExpired:
        print(f"  ❌ Timeout")
        error_count += 1
        errors.append((obs_num, "Timeout"))
    except Exception as e:
        print(f"  ❌ Exception: {str(e)[:100]}")
        error_count += 1
        errors.append((obs_num, str(e)[:200]))

print()
print("="*70)
print("Summary")
print("="*70)
print(f"✓ Successful: {success_count}/{len(observations)}")
print(f"❌ Errors: {error_count}/{len(observations)}")

if errors:
    print("\nErrors:")
    for obs_num, error in errors:
        print(f"  obs{obs_num}: {error}")

print()
print("Next step: Run build_fundamentals_dataset.py to create training CSV")
