#!/usr/bin/env python3
"""
Automated Phase 1-3 extraction pipeline for Phase 1B observations.

Runs for all 20 observations:
- Phase 1: PDF → Markdown (PyMuPDF4LLM + Camelot)
- Phase 2: Markdown → JSON (extract_key_metrics_efficient.py)
- Phase 3: Calculate metrics (calculate_credit_metrics.py)
- Extract fundamentals (extract_fundamentals_from_phase3.py)

Usage:
    python scripts/run_phase1b_extraction.py [--observations 1,2,3] [--skip-phase1]
"""

import argparse
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import List, Tuple


# Observation metadata: (num, ticker, name, quarter, year)
OBSERVATIONS = [
    (1, "HR-UN.TO", "H&R REIT", "Q4", 2022),
    (2, "AX-UN.TO", "Artis REIT", "Q4", 2022),
    (3, "SOT-UN.TO", "Slate Office REIT", "Q1", 2023),
    (4, "D-UN.TO", "Dream Office REIT", "Q2", 2023),
    (5, "NWH-UN.TO", "NorthWest Healthcare Properties REIT", "Q2", 2023),
    (6, "AP-UN.TO", "Allied Properties REIT", "Q4", 2023),
    (7, "HR-UN.TO", "H&R REIT", "Q4", 2023),
    (8, "CAR-UN.TO", "Canadian Apartment Properties REIT", "Q4", 2024),
    (9, "HR-UN.TO", "H&R REIT", "Q4", 2024),
    (10, "ERE-UN.TO", "European Residential REIT", "Q4", 2024),
    (11, "CRT-UN.TO", "CT REIT", "Q3", 2022),
    (12, "NXR-UN.TO", "Nexus Industrial REIT", "Q3", 2022),
    (13, "CRT-UN.TO", "CT REIT", "Q1", 2023),
    (14, "NXR-UN.TO", "Nexus Industrial REIT", "Q2", 2023),
    (15, "IIP-UN.TO", "InterRent REIT", "Q2", 2023),
    (16, "EXE.TO", "Extendicare", "Q3", 2023),
    (17, "SRU-UN.TO", "SmartCentres REIT", "Q3", 2023),
    (18, "PLZ-UN.TO", "Plaza Retail REIT", "Q3", 2024),
    (19, "CRT-UN.TO", "CT REIT", "Q4", 2024),
    (20, "EXE.TO", "Extendicare", "Q4", 2024),
]


def run_command(cmd: List[str], description: str) -> Tuple[bool, str]:
    """Run shell command and return success status + output."""
    print(f"  Running: {description}...")
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout per command
        )
        if result.returncode == 0:
            print(f"  ✓ {description} complete")
            return True, result.stdout
        else:
            print(f"  ✗ {description} FAILED")
            print(f"    Error: {result.stderr[:200]}")
            return False, result.stderr
    except subprocess.TimeoutExpired:
        print(f"  ✗ {description} TIMEOUT (>5 minutes)")
        return False, "Timeout"
    except Exception as e:
        print(f"  ✗ {description} ERROR: {str(e)}")
        return False, str(e)


def extract_observation(
    obs_num: int,
    ticker: str,
    name: str,
    quarter: str,
    year: int,
    skip_phase1: bool = False
) -> dict:
    """
    Run Phase 1-3 extraction for a single observation.

    Returns:
        Dictionary with extraction results
    """
    print(f"\n{'='*80}")
    print(f"Observation {obs_num}: {name} {quarter} {year}")
    print(f"{'='*80}")

    # Paths
    pdf_dir = Path(f"Issuer_Reports/phase1b/pdfs/{obs_num:02d}_{ticker.replace('.TO', '')}_{quarter}_{year}")
    issuer_folder = name.replace(" ", "_").replace("&", "and")
    output_dir = Path(f"Issuer_Reports/{issuer_folder}")
    temp_dir = output_dir / "temp"

    results = {
        "obs_num": obs_num,
        "name": name,
        "ticker": ticker,
        "quarter": quarter,
        "year": year,
        "phase1": False,
        "phase2": False,
        "phase3": False,
        "fundamentals": False,
        "errors": []
    }

    # Find PDFs in directory
    if not pdf_dir.exists():
        print(f"✗ PDF directory not found: {pdf_dir}")
        results["errors"].append(f"PDF directory not found: {pdf_dir}")
        return results

    pdfs = list(pdf_dir.glob("*.pdf"))
    if not pdfs:
        print(f"✗ No PDFs found in {pdf_dir}")
        results["errors"].append(f"No PDFs found in {pdf_dir}")
        return results

    print(f"Found {len(pdfs)} PDF(s):")
    for pdf in pdfs:
        print(f"  - {pdf.name}")

    start_time = time.time()

    # Phase 1: PDF → Markdown
    if not skip_phase1:
        phase1_cmd = [
            "python", "scripts/preprocess_pdfs_enhanced.py",
            "--issuer-name", name
        ] + [str(pdf) for pdf in pdfs]

        success, output = run_command(phase1_cmd, "Phase 1: PDF → Markdown")
        results["phase1"] = success
        if not success:
            results["errors"].append(f"Phase 1 failed: {output[:200]}")
            return results
    else:
        print("  ⊙ Phase 1 skipped (using existing markdown)")
        results["phase1"] = True

    # Phase 2: Markdown → JSON
    markdown_files = list((temp_dir / "phase1_markdown").glob("*.md"))
    if not markdown_files:
        print(f"✗ No markdown files found in {temp_dir / 'phase1_markdown'}")
        results["errors"].append("No markdown files from Phase 1")
        return results

    phase2_cmd = [
        "python", "scripts/extract_key_metrics_efficient.py",
        "--issuer-name", name
    ] + [str(md) for md in markdown_files]

    success, output = run_command(phase2_cmd, "Phase 2: Markdown → JSON")
    results["phase2"] = success
    if not success:
        results["errors"].append(f"Phase 2 failed: {output[:200]}")
        return results

    # Phase 3: Calculate metrics
    phase2_json = temp_dir / "phase2_extracted_data.json"
    if not phase2_json.exists():
        print(f"✗ Phase 2 JSON not found: {phase2_json}")
        results["errors"].append(f"Phase 2 JSON not found: {phase2_json}")
        return results

    phase3_cmd = [
        "python", "scripts/calculate_credit_metrics.py",
        str(phase2_json)
    ]

    success, output = run_command(phase3_cmd, "Phase 3: Calculate metrics")
    results["phase3"] = success
    if not success:
        results["errors"].append(f"Phase 3 failed: {output[:200]}")
        return results

    # Extract fundamentals
    phase3_json = temp_dir / "phase3_calculated_metrics.json"
    if not phase3_json.exists():
        print(f"✗ Phase 3 JSON not found: {phase3_json}")
        results["errors"].append(f"Phase 3 JSON not found: {phase3_json}")
        return results

    fundamentals_output = Path(f"Issuer_Reports/phase1b/fundamentals/{ticker.replace('.TO', '')}_{quarter}_{year}.json")
    fundamentals_cmd = [
        "python", "scripts/extract_fundamentals_from_phase3.py",
        str(phase3_json),
        "--output", str(fundamentals_output)
    ]

    success, output = run_command(fundamentals_cmd, "Extract fundamentals")
    results["fundamentals"] = success
    if not success:
        results["errors"].append(f"Fundamentals extraction failed: {output[:200]}")

    elapsed = time.time() - start_time
    print(f"\n✓ Observation {obs_num} complete in {elapsed:.1f}s")

    return results


def post_github_update(obs_num: int, name: str, quarter: str, year: int, success: bool):
    """Post progress update to GitHub Issue #38."""
    status = "✅ Complete" if success else "❌ Failed"
    comment = f"**Extraction Progress:** Obs {obs_num} - {name} {quarter} {year} {status}"

    try:
        subprocess.run(
            ["gh", "issue", "comment", "38", "--body", comment],
            capture_output=True,
            timeout=10
        )
    except:
        pass  # Don't fail extraction if GitHub update fails


def extract_observation_wrapper(args):
    """Wrapper for parallel execution."""
    obs_num, ticker, name, quarter, year, skip_phase1 = args
    result = extract_observation(obs_num, ticker, name, quarter, year, skip_phase1)

    # Post update to GitHub
    post_github_update(obs_num, name, quarter, year, result["fundamentals"])

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Run Phase 1-3 extraction for Phase 1B observations"
    )
    parser.add_argument(
        "--observations",
        type=str,
        help="Comma-separated observation numbers (e.g., '1,2,3'). Default: all"
    )
    parser.add_argument(
        "--skip-phase1",
        action="store_true",
        help="Skip Phase 1 (use existing markdown)"
    )
    parser.add_argument(
        "--parallel",
        type=int,
        default=4,
        help="Number of parallel workers (default: 4)"
    )

    args = parser.parse_args()

    # Parse observation numbers
    if args.observations:
        obs_nums = [int(x.strip()) for x in args.observations.split(",")]
        observations = [obs for obs in OBSERVATIONS if obs[0] in obs_nums]
    else:
        observations = OBSERVATIONS

    print("="*80)
    print("Phase 1B Extraction Pipeline")
    print("="*80)
    print(f"Observations to process: {len(observations)}")
    print(f"Skip Phase 1: {args.skip_phase1}")
    print(f"Parallel workers: {args.parallel}")
    print()

    # Prepare arguments for parallel execution
    extraction_args = [
        (obs_num, ticker, name, quarter, year, args.skip_phase1)
        for obs_num, ticker, name, quarter, year in observations
    ]

    # Run extractions in parallel
    all_results = []
    with ProcessPoolExecutor(max_workers=args.parallel) as executor:
        futures = {executor.submit(extract_observation_wrapper, arg): arg for arg in extraction_args}

        for future in as_completed(futures):
            arg = futures[future]
            try:
                result = future.result()
                all_results.append(result)
                print(f"\n✓ Completed {len(all_results)}/{len(observations)} observations")
            except Exception as e:
                obs_num = arg[0]
                print(f"\n✗ Observation {obs_num} failed with exception: {str(e)}")
                all_results.append({
                    "obs_num": obs_num,
                    "fundamentals": False,
                    "errors": [str(e)]
                })

    # Summary
    print("\n" + "="*80)
    print("EXTRACTION SUMMARY")
    print("="*80)

    success_count = sum(1 for r in all_results if r["fundamentals"])
    print(f"Total: {len(all_results)} observations")
    print(f"Success: {success_count} ({success_count/len(all_results)*100:.1f}%)")
    print(f"Failed: {len(all_results) - success_count}")
    print()

    # Failed observations
    failed = [r for r in all_results if not r["fundamentals"]]
    if failed:
        print("Failed Observations:")
        for r in failed:
            print(f"  ✗ {r['obs_num']}: {r['name']} {r['quarter']} {r['year']}")
            for error in r["errors"]:
                print(f"      {error}")
        print()

    # Next steps
    if success_count == len(all_results):
        print("✅ ALL EXTRACTIONS COMPLETE!")
        print()
        print("Next Steps:")
        print("  1. Merge fundamentals with market/macro data")
        print("  2. Train model on n=20 subset")
        print("  3. Evaluate hypothesis (target F1 ≥ 0.75)")
    else:
        print("⚠️  Some extractions failed. Review errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
