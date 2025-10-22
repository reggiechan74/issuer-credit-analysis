# Phase 1B: Next Steps - Data Merge

**Status:** Fundamentals extraction complete (19/19 observations)

**Current Dataset:** `data/fundamentals_dataset_phase1b.csv`
- 19 observations (10 targets, 9 controls)
- 33 fundamental features extracted from Phase 3 metrics

---

## Required for Merge: Market + Macro Data

### 1. Ticker Symbol Mapping

Map each issuer to its TSX ticker symbol:

| Observation | Issuer | Reporting Date | Ticker (Estimated) |
|-------------|--------|----------------|-------------------|
| 1 | H&R REIT | 2022-12-31 | HR-UN.TO |
| 2 | Artis REIT | 2022-12-31 | AX-UN.TO |
| 3 | Slate Office REIT | 2023-03-31 | SOT-UN.TO |
| 4 | Dream Office REIT | 2023-06-30 | D-UN.TO |
| 5 | NorthWest Healthcare | 2023-06-30 | NWH-UN.TO |
| 6 | Allied Properties | 2023-12-31 | AP-UN.TO |
| 7 | H&R REIT | 2023-12-31 | HR-UN.TO |
| 8 | CAPREIT | 2024-12-31 | CAR-UN.TO |
| 9 | H&R REIT | 2024-12-31 | HR-UN.TO |
| 10 | European Residential | 2024-12-31 | ERE-UN.TO |
| 11 | CT REIT | 2022-09-30 | CRT-UN.TO |
| 12 | Nexus Industrial | 2022-09-30 | NXR-UN.TO |
| 13 | CT REIT | 2023-03-31 | CRT-UN.TO |
| 14 | Nexus Industrial | 2023-06-30 | NXR-UN.TO |
| 15 | InterRent REIT | 2023-09-30 | IIP-UN.TO |
| 16 | Extendicare | 2023-09-30 | EXE.TO |
| 18 | Plaza Retail REIT | 2024-09-30 | PLZ-UN.TO |
| 19 | CT REIT | 2024-12-31 | CRT-UN.TO |
| 20 | Extendicare | 2024-12-31 | EXE.TO |

**Note:** Obs 17 (SmartCentres) excluded due to incomplete extraction.

### 2. Market Data Collection

For each observation, collect market data as of reporting date:

```bash
# Example for Obs 1 (H&R REIT Q4 2022)
python scripts/openbb_market_monitor.py \
  --ticker HR-UN.TO \
  --date 2022-12-31 \
  --output data/market/obs1_hr_q4_2022_market.json
```

**Features to extract:**
- Price stress (% decline from 52-week high)
- Volatility (30d, 90d, 252d annualized)
- Momentum (3/6/12-month returns)
- Market risk score (0-100)

### 3. Macro Data Collection

For each unique reporting date, collect macro environment:

```bash
# Example for Q4 2022 observations
python scripts/openbb_macro_monitor.py \
  --date 2022-12-31 \
  --output data/macro/2022_q4_macro.json
```

**Features to extract:**
- Bank of Canada policy rate
- US Federal Funds rate
- Rate environment (easing/tightening/neutral)
- Credit stress score (0-100)
- Rate differential (Canada - US)

### 4. Dataset Merge Script

Create `scripts/merge_training_dataset.py`:

```python
#!/usr/bin/env python3
"""
Merge fundamentals, market, and macro data into final training dataset.

Input:
- data/fundamentals_dataset_phase1b.csv (19 obs)
- data/market/obs*_market.json (19 files)
- data/macro/*_macro.json (5-7 unique dates)

Output:
- data/training_dataset_v2_phase1b.csv (19 obs × ~50 features)

Features:
- 33 fundamental features (from Phase 3)
- 10-15 market features (from OpenBB)
- 5-7 macro features (from OpenBB)
"""
```

### 5. Automation Script (Recommended)

Create `scripts/collect_phase1b_market_data.sh`:

```bash
#!/bin/bash
# Collect market + macro data for all 19 Phase 1B observations

# Market data (19 API calls)
python scripts/openbb_market_monitor.py --ticker HR-UN.TO --date 2022-12-31 --output data/market/obs1_market.json
python scripts/openbb_market_monitor.py --ticker AX-UN.TO --date 2022-12-31 --output data/market/obs2_market.json
# ... [17 more]

# Macro data (5-7 unique dates)
python scripts/openbb_macro_monitor.py --date 2022-09-30 --output data/macro/2022_q3_macro.json
python scripts/openbb_macro_monitor.py --date 2022-12-31 --output data/macro/2022_q4_macro.json
# ... [3-5 more dates]

# Merge all data
python scripts/merge_training_dataset.py \
  --fundamentals data/fundamentals_dataset_phase1b.csv \
  --market-dir data/market \
  --macro-dir data/macro \
  --output data/training_dataset_v2_phase1b.csv
```

**Execution time:** ~5-10 minutes (19 market calls × 5-10s each)

---

## Alternative: Use Existing Market Data (If Available)

If market data was already collected during Issue #39 testing, check:

```bash
ls -lh data/*market*.json data/*macro*.json
```

Match tickers and dates, then proceed directly to merge step.

---

## Final Training Dataset Schema

**Target:** `data/training_dataset_v2_phase1b.csv`

| Feature Category | Count | Examples |
|-----------------|-------|----------|
| **Metadata** | 5 | observation, issuer, date, period, cut_type |
| **Fundamentals** | 33 | affo_payout, debt_assets, coverage, ffo_unit, ... |
| **Market** | 10-15 | price_stress, volatility_30d, momentum_3m, risk_score |
| **Macro** | 5-7 | boc_rate, fed_rate, rate_cycle, credit_stress |
| **Total** | 53-60 | Comprehensive feature set for model training |

**Rows:** 19 observations (10 target cuts, 9 controls)

---

## Decision Point: Proceed or Stop?

**Option A: Full Pipeline (Recommended)**
- Collect market data for all 19 observations (~10 min)
- Collect macro data for unique dates (~3 min)
- Merge into final training dataset (~1 min)
- Train LightGBM model with 5-fold CV
- **Target:** F1 ≥ 0.75 (vs baseline 0.553)

**Option B: Manual Merge (If time-constrained)**
- Manually merge with existing market data files
- Skip unavailable observations
- Train on smaller subset (n=10-15)

**Option C: Fundamentals-Only Test (Quick validation)**
- Train model on fundamentals only (33 features)
- Validates if AFFO payout + leverage improve baseline
- If successful, proceed with full merge for final model

---

**Recommendation:** Option A - Full pipeline ensures complete dataset and best chance of achieving F1 ≥ 0.75 target.

**Next Command:**
```bash
# Create ticker mapping config
cat > data/phase1b_ticker_mapping.yaml << 'YAML'
observations:
  1: {ticker: "HR-UN.TO", date: "2022-12-31"}
  2: {ticker: "AX-UN.TO", date: "2022-12-31"}
  # ... [rest of mapping]
YAML

# Run automated collection
bash scripts/collect_phase1b_market_data.sh
```

