#!/usr/bin/env python3
"""
Batch process all REITs: Phase 1 → Phase 2 → Phase 3
Ensures all REITs are up-to-date with sustainable AFCF methodology.
"""

import subprocess
import json
from pathlib import Path
from datetime import datetime

def find_all_reits():
    """Find all REIT folders with Phase 1 data."""
    reits = []
    for p in Path('Issuer_Reports').iterdir():
        if p.is_dir() and p.name != 'phase1b':
            phase1_dir = p / 'temp' / 'phase1_markdown'
            if phase1_dir.exists():
                md_files = list(phase1_dir.glob('*.md'))
                if md_files:
                    reits.append({
                        'name': p.name,
                        'folder': p,
                        'phase1_files': md_files,
                        'phase2_file': p / 'temp' / 'phase2_extracted_data.json',
                        'phase3_file': p / 'temp' / 'phase3_calculated_metrics.json'
                    })
    return sorted(reits, key=lambda x: x['name'])

def run_phase2(reit):
    """Run Phase 2 extraction for a REIT."""
    print(f"\n{'='*70}")
    print(f"Phase 2: {reit['name']}")
    print(f"{'='*70}")

    # Get issuer name from folder name
    issuer_name = reit['name'].replace('_', ' ')

    # Build command
    md_paths = [str(f) for f in reit['phase1_files']]
    cmd = [
        'python', 'scripts/extract_key_metrics_efficient.py',
        '--issuer-name', issuer_name
    ] + md_paths

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)

        if result.returncode == 0:
            print(f"✓ Phase 2 complete: {reit['phase2_file']}")
            return True
        else:
            print(f"✗ Phase 2 failed:")
            print(result.stderr[:500])
            return False

    except subprocess.TimeoutExpired:
        print(f"✗ Phase 2 timeout (>180s)")
        return False
    except Exception as e:
        print(f"✗ Phase 2 error: {e}")
        return False

def run_phase3(reit):
    """Run Phase 3 calculation for a REIT."""
    print(f"\nPhase 3: {reit['name']}")

    if not reit['phase2_file'].exists():
        print(f"✗ Phase 2 file missing - skipping")
        return False

    cmd = [
        'python', 'scripts/calculate_credit_metrics.py',
        str(reit['phase2_file']),
        '--output', str(reit['phase3_file'])
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        if result.returncode == 0:
            print(f"✓ Phase 3 complete: {reit['phase3_file']}")
            return True
        else:
            print(f"✗ Phase 3 failed:")
            print(result.stderr[:500])
            return False

    except subprocess.TimeoutExpired:
        print(f"✗ Phase 3 timeout (>60s)")
        return False
    except Exception as e:
        print(f"✗ Phase 3 error: {e}")
        return False

def main():
    print("="*70)
    print("BATCH PROCESSING ALL REITs")
    print("="*70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Find all REITs
    reits = find_all_reits()
    print(f"Found {len(reits)} REITs with Phase 1 data")
    print()

    # Track results
    phase2_success = 0
    phase2_failed = 0
    phase2_skipped = 0

    phase3_success = 0
    phase3_failed = 0

    # Process each REIT
    for i, reit in enumerate(reits, 1):
        print(f"\n[{i}/{len(reits)}] Processing: {reit['name']}")
        print("-"*70)

        # Phase 2: Extract if missing or force regenerate
        if not reit['phase2_file'].exists():
            print("Phase 2 not found - extracting...")
            if run_phase2(reit):
                phase2_success += 1
            else:
                phase2_failed += 1
                continue  # Skip Phase 3 if Phase 2 failed
        else:
            print(f"✓ Phase 2 exists: {reit['phase2_file']}")
            phase2_skipped += 1

        # Phase 3: Always regenerate to ensure sustainable AFCF
        print("Regenerating Phase 3 with sustainable AFCF...")
        if run_phase3(reit):
            phase3_success += 1
        else:
            phase3_failed += 1

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"\nPhase 2:")
    print(f"  ✓ Successful: {phase2_success}")
    print(f"  ✗ Failed: {phase2_failed}")
    print(f"  - Skipped (existing): {phase2_skipped}")

    print(f"\nPhase 3:")
    print(f"  ✓ Successful: {phase3_success}")
    print(f"  ✗ Failed: {phase3_failed}")

    print(f"\nTotal REITs ready: {phase3_success}/{len(reits)}")
    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == '__main__':
    main()
