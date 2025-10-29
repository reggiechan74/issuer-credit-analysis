# OpenBB Data Collector - Usage Guide

**Script:** `scripts/openbb_data_collector.py`
**Version:** 1.0.0
**Purpose:** Collect dividend history, market data, and peer comparisons for Canadian REITs

---

## Quick Start

### Installation

```bash
# Install required packages
pip install openbb openbb-tmx pandas

# Verify installation
python scripts/openbb_data_collector.py --help
```

### Basic Usage

```bash
# Collect data for RioCan REIT
python scripts/openbb_data_collector.py --ticker REI-UN.TO

# Collect data with peer comparison
python scripts/openbb_data_collector.py \
  --ticker REI-UN.TO \
  --peers DIR-UN.TO,AX-UN.TO,SRU-UN.TO

# Validate against issuer-reported distribution
python scripts/openbb_data_collector.py \
  --ticker REI-UN.TO \
  --validate-distribution 0.08

# Export to CSV as well as JSON
python scripts/openbb_data_collector.py \
  --ticker DIR-UN.TO \
  --export-csv \
  --output data/dream_industrial_complete.json
```

---

## Features

### 1. Dividend History Collection

Retrieves 10+ years of dividend history from OpenBB (TMX or YFinance providers).

**Data Fields:**
- `ex_dividend_date` - Ex-dividend date
- `amount` - Dividend amount per share/unit
- `currency` - Currency (CAD)
- `record_date` - Record date
- `payment_date` - Payment date
- `declaration_date` - Declaration date (TMX only)

**Example Output:**
```json
{
  "dividend_history": {
    "total_records": 200,
    "date_range": {
      "earliest": "2009-01-15",
      "latest": "2025-10-15"
    },
    "records": [
      {
        "ex_dividend_date": "2025-10-15",
        "amount": 0.08,
        "currency": "CAD",
        "record_date": "2025-10-15",
        "payment_date": "2025-10-31"
      }
    ]
  }
}
```

### 2. TTM Metrics Calculation

Calculates trailing-twelve-months metrics:
- Annual dividend (sum of last 12 months)
- Dividend yield (annual dividend / current price)
- Payment count (number of payments in TTM)
- Monthly distribution (most recent)

**Example:**
```json
{
  "current_metrics": {
    "annual_dividend_ttm": 1.0,
    "dividend_yield_ttm": 5.27,
    "payment_count_ttm": 12,
    "monthly_distribution": 0.0833,
    "current_price": 18.97,
    "calculation_date": "2025-10-21"
  }
}
```

### 3. Automatic Cut Detection

Automatically detects dividend cuts >10% from historical data.

**Example:**
```json
{
  "detected_cuts": [
    {
      "cut_date": "2020-12",
      "previous_monthly": 0.12,
      "new_monthly": 0.08,
      "cut_percentage": 33.3,
      "previous_annual": 1.44,
      "new_annual": 0.96
    }
  ],
  "cut_count": 1
}
```

### 4. Peer Comparison

Compare dividend yield and metrics across multiple REITs.

**Usage:**
```bash
python scripts/openbb_data_collector.py \
  --ticker REI-UN.TO \
  --peers DIR-UN.TO,AX-UN.TO,SRU-UN.TO,FCR-UN.TO
```

**Output:**
```
Peer Comparison:
      ticker reit_name  current_price  annual_dividend  dividend_yield  monthly_distribution
    AX-UN.TO        AX           6.02           0.6500           10.80                0.0542
  REI-UN.TO       REI          18.97           1.0000            5.27                0.0833
  DIR-UN.TO       DIR          12.33           0.7008            5.68                0.0584
  SRU-UN.TO       SRU          28.45           1.8000            6.33                0.1500
```

### 5. Issuer Validation

Validate OpenBB data against issuer-reported distributions.

**Usage:**
```bash
python scripts/openbb_data_collector.py \
  --ticker REI-UN.TO \
  --validate-distribution 0.0833  # Issuer reports $0.0833/month
```

**Output:**
```
✓ VALID - OpenBB: $0.0833, Variance: 0.0% (<5% tolerance)
```

---

## Command-Line Arguments

### Required

| Argument | Description | Example |
|----------|-------------|---------|
| `--ticker` | REIT ticker symbol | `REI-UN.TO` |

### Optional

| Argument | Description | Default | Example |
|----------|-------------|---------|---------|
| `--output` | Output JSON path | `data/<ticker>_openbb.json` | `data/riocan_full.json` |
| `--peers` | Peer tickers (comma-separated) | None | `DIR-UN.TO,AX-UN.TO` |
| `--validate-distribution` | Issuer-reported monthly distribution | None | `0.08` |
| `--provider` | Data provider | `tmx` | `yfinance` |
| `--export-csv` | Also export to CSV | False | (flag) |

---

## Use Cases

### Use Case 1: Validate Pipeline Extractions

Compare Phase 2 extracted distributions against OpenBB market data:

```bash
# Extract distribution from OpenBB
python scripts/openbb_data_collector.py \
  --ticker AX-UN.TO \
  --validate-distribution 0.0542

# Compare with Phase 2 extraction
# Issuer_Reports/Artis_REIT/temp/phase2_extracted_data.json
```

### Use Case 2: Historical Cut Analysis

Identify all historical cuts for model training:

```bash
# Collect 10+ years of data
python scripts/openbb_data_collector.py \
  --ticker REI-UN.TO \
  --export-csv

# Review detected_cuts in output JSON
# Use for training distribution cut prediction model
```

### Use Case 3: Peer Comparison for Credit Analysis

Enhance Phase 4 credit analysis with peer context:

```bash
# Collect peer data for industrial REITs
python scripts/openbb_data_collector.py \
  --ticker DIR-UN.TO \
  --peers GRT-UN.TO,PMZ-UN.TO,SUM-UN.TO

# Compare yields, payout trends, cut histories
```

### Use Case 4: Track Yield Trends Over Time

Monitor how dividend yield has evolved:

```bash
# Export full history
python scripts/openbb_data_collector.py \
  --ticker HR-UN.TO \
  --export-csv \
  --output data/hr_reit_analysis.json

# Analyze yield trends pre/post COVID-19 cut (May 2020)
```

---

## Integration with Pipeline

### Phase 2.5: Market Data Enrichment (Proposed)

```python
# In extract_key_metrics_efficient.py or new script

from scripts.openbb_data_collector import OpenBBDataCollector

# After Phase 2 extraction completes
collector = OpenBBDataCollector(ticker="REI-UN.TO")

# Validate extracted distribution
validation = collector.validate_against_issuer(
    issuer_reported_distribution=0.08
)

# Get peer comparison data
peer_df = collector.compare_peers(["DIR-UN.TO", "AX-UN.TO", "SRU-UN.TO"])

# Detect historical cuts (for risk assessment)
div_df = collector.get_dividend_history()
cuts = collector.detect_dividend_cuts(div_df)

# Enrich Phase 2 output
phase2_data['market_validation'] = validation
phase2_data['peer_comparison'] = peer_df.to_dict(orient='records')
phase2_data['historical_cuts'] = cuts
```

### Phase 4 Enhancement: Peer Context

Use peer comparison data to enhance qualitative credit assessment:

```markdown
### Distribution Sustainability (Enhanced)

**Current Yield:** 5.27% (RioCan)
**Peer Comparison:**
- Dream Industrial: 5.68%
- Artis REIT: 10.80% (distressed)
- SmartCentres: 6.33%
- **Peer Median:** 6.00%

**Assessment:** RioCan's yield is below peer median, suggesting market perceives
lower distribution risk compared to sector. Artis' elevated 10.8% yield signals
market expects further cuts.
```

---

## Ticker Format Reference

### Canadian REITs

| REIT | Correct Format | Alternative Formats |
|------|----------------|---------------------|
| RioCan REIT | `REI-UN.TO` | `REI.UN.TO` (TMX accepts both) |
| Dream Industrial | `DIR-UN.TO` | `DIR.UN.TO` |
| Artis REIT | `AX-UN.TO` | `AX.UN.TO` |
| H&R REIT | `HR-UN.TO` | `HR.UN.TO` |
| Allied Properties | `AP-UN.TO` | `AP.UN.TO` |
| SmartCentres | `SRU-UN.TO` | `SRU.UN.TO` |
| First Capital | `FCR-UN.TO` | `FCR.UN.TO` |

**Note:** TMX provider accepts both `-` and `.` formats. YFinance requires `-UN.TO` format (hyphen mandatory).

---

## Output File Structure

```json
{
  "ticker": "REI-UN.TO",
  "reit_name": "REI",
  "data_provider": "tmx",
  "collection_date": "2025-10-21 14:30:00",

  "current_metrics": {
    "annual_dividend_ttm": 1.0,
    "dividend_yield_ttm": 5.27,
    "payment_count_ttm": 12,
    "monthly_distribution": 0.0833,
    "current_price": 18.97,
    "calculation_date": "2025-10-21"
  },

  "dividend_history": {
    "total_records": 200,
    "date_range": {
      "earliest": "2009-01-15",
      "latest": "2025-10-15"
    },
    "records": [ /* 200 dividend records */ ]
  },

  "detected_cuts": [
    {
      "cut_date": "2020-12",
      "previous_monthly": 0.12,
      "new_monthly": 0.08,
      "cut_percentage": 33.3,
      "previous_annual": 1.44,
      "new_annual": 0.96
    }
  ],

  "cut_count": 1
}
```

---

## Troubleshooting

### Issue: "Missing required package: openbb"

**Solution:**
```bash
pip install openbb openbb-tmx pandas
```

### Issue: "No dividend data available"

**Causes:**
1. Incorrect ticker format (use `SYMBOL-UN.TO`)
2. REIT has no dividend history (new IPO?)
3. OpenBB API rate limit exceeded

**Solution:**
```bash
# Try alternative provider
python scripts/openbb_data_collector.py --ticker REI-UN.TO --provider yfinance

# Verify ticker on TMX Money: https://money.tmx.com/
```

### Issue: Validation fails with high variance

**Causes:**
1. Issuer recently changed distribution amount
2. Special/irregular dividends included
3. Currency mismatch (USD vs CAD)

**Solution:**
- Check issuer's latest press release for current distribution
- Increase tolerance: modify `tolerance=0.10` in code (10%)
- Review `dividend_history.records` for irregular payments

---

## Examples

### Example 1: RioCan REIT Full Analysis

```bash
python scripts/openbb_data_collector.py \
  --ticker REI-UN.TO \
  --peers DIR-UN.TO,AX-UN.TO,SRU-UN.TO,FCR-UN.TO \
  --validate-distribution 0.0833 \
  --export-csv \
  --output data/riocan_complete_analysis.json
```

**Output:**
- `data/riocan_complete_analysis.json` - Full dataset
- `data/riocan_complete_analysis_dividends.csv` - 200 dividend records
- `data/riocan_complete_analysis_peer_comparison.csv` - Peer table

### Example 2: H&R REIT (Pre-Cut Analysis)

```bash
# Analyze H&R REIT's May 2020 distribution cut
python scripts/openbb_data_collector.py \
  --ticker HR-UN.TO \
  --export-csv

# Review detected_cuts in output:
# "cut_date": "2020-05"
# "previous_monthly": 0.115
# "new_monthly": 0.0575
# "cut_percentage": 50.0%
```

### Example 3: Artis REIT (Multiple Cuts)

```bash
python scripts/openbb_data_collector.py \
  --ticker AX-UN.TO \
  --export-csv \
  --output data/artis_historical_cuts.json

# Expected: 2+ detected cuts (2018, 2020+)
```

---

## Limitations

1. **Free tier only provides dividend data** - No financial statements
2. **TMX data starts ~2009** - Older data may be incomplete
3. **Cut detection threshold 10%** - Small adjustments (<10%) not flagged
4. **No FFO/AFFO data** - Must be extracted from PDF financial statements
5. **Manual REIT ticker mapping** - No automated issuer name → ticker lookup

**Mitigation:** Use OpenBB for dividend validation and peer comparison. Continue using PDF extraction pipeline for financial metrics (FFO, AFFO, ACFO, balance sheet, cash flow).

---

## Next Steps

1. **Test with all 13 REITs from historical cut research**
2. **Build training dataset** combining OpenBB + PDF extractions
3. **Create ticker mapping** (Issuer Name → TSX Ticker)
4. **Integrate into Phase 2.5** (market data enrichment)
5. **Use for model training** (distribution cut prediction)

---

**Version:** 1.0.0
**Last Updated:** 2025-10-21
**Author:** Claude Code
