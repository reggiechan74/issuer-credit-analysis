# Fast Download Workflow for Phase 1B (Manual Process)

**Reality:** SEDAR+ requires manual browser interaction and cannot be automated due to:
- Anti-bot protections / CAPTCHA
- Multiple filings per quarter requiring human judgment
- Government securities filing system with access controls

**Solution:** Optimize manual workflow for maximum speed

---

## Fastest Workflow Strategy

### Setup (5 minutes)

1. **Open Multiple Browser Windows** (4-6 windows)
   - Window 1: SEDAR+ search for Tickers A-E
   - Window 2: SEDAR+ search for Tickers F-M
   - Window 3: SEDAR+ search for Tickers N-S
   - Window 4: SEDAR+ search for Tickers T-Z
   - Window 5: Local file manager (for moving downloads)
   - Window 6: This instruction document

2. **Configure Browser Downloads**
   - Set download location to a single folder (e.g., ~/Downloads/phase1b/)
   - Enable "Ask where to save each file" for precise placement
   - OR: Use default downloads folder and batch-move afterward

3. **Pre-search All REITs**
   - Open tabs for each unique REIT (12 unique tickers)
   - Keep tabs open throughout process

---

## Batch Strategy (Fastest Approach)

### Batch 1: Q4 2022-2023 Observations (7 obs, ~2.5 hours)

**REITs:** H&R, Artis, Allied Properties
**Quarters:** Q4 2022 (3 obs), Q3 2022 (2 obs), Q4 2023 (2 obs)

| # | REIT | Quarter | Ticker | Cut/Control | Save To |
|---|------|---------|--------|-------------|---------|
| 1 | H&R | Q4 2022 | HR-UN.TO | Cut 77.6% | 01_HR-UN_Q4_2022/ |
| 2 | Artis | Q4 2022 | AX-UN.TO | Cut 52.4% | 02_AX-UN_Q4_2022/ |
| 11 | CT REIT | Q3 2022 | CRT-UN.TO | Control | 11_CRT-UN_Q3_2022/ |
| 12 | Nexus | Q3 2022 | NXR-UN.TO | Control | 12_NXR-UN_Q3_2022/ |
| 6 | Allied | Q4 2023 | AP-UN.TO | Cut 52.4% | 06_AP-UN_Q4_2023/ |
| 7 | H&R | Q4 2023 | HR-UN.TO | Cut 33.3% | 07_HR-UN_Q4_2023/ |

**Strategy:**
- Download all H&R filings at once (Q4 2022, Q4 2023 in same search)
- Download all CT REIT filings at once (Q3 2022, Q1 2023)
- Group by REIT to minimize searching

---

### Batch 2: Q1-Q2 2023 Observations (5 obs, ~2 hours)

**REITs:** Slate Office, Dream Office, NorthWest Healthcare, CT, Nexus, InterRent
**Quarters:** Q1 2023 (2 obs), Q2 2023 (3 obs)

| # | REIT | Quarter | Ticker | Cut/Control | Save To |
|---|------|---------|--------|-------------|---------|
| 3 | Slate Office | Q1 2023 | SOT-UN.TO | Cut 70.0% | 03_SOT-UN_Q1_2023/ |
| 13 | CT REIT | Q1 2023 | CRT-UN.TO | Control | 13_CRT-UN_Q1_2023/ |
| 4 | Dream Office | Q2 2023 | D-UN.TO | Cut 96.4% | 04_D-UN_Q2_2023/ |
| 5 | NorthWest | Q2 2023 | NWH-UN.TO | Cut 55.0% | 05_NWH-UN_Q2_2023/ |
| 14 | Nexus | Q2 2023 | NXR-UN.TO | Control | 14_NXR-UN_Q2_2023/ |
| 15 | InterRent | Q2 2023 | IIP-UN.TO | Control | 15_IIP-UN_Q2_2023/ |

---

### Batch 3: Q3 2023 Observations (2 obs, ~1 hour)

**REITs:** Extendicare, SmartCentres
**Quarters:** Q3 2023

| # | REIT | Quarter | Ticker | Cut/Control | Save To |
|---|------|---------|--------|-------------|---------|
| 16 | Extendicare | Q3 2023 | EXE.TO | Control | 16_EXE_Q3_2023/ |
| 17 | SmartCentres | Q3 2023 | SRU-UN.TO | Control | 17_SRU-UN_Q3_2023/ |

---

### Batch 4: 2024 Observations (6 obs, ~2.5 hours)

**REITs:** CAPREIT, H&R, European Residential, Plaza Retail, CT REIT, Extendicare
**Quarters:** Q3 2024 (1 obs), Q4 2024 (5 obs)

⚠️ **Q4 2024 May Not Be Available** - Use Q3 2024 as proxy if needed

| # | REIT | Quarter | Ticker | Cut/Control | Save To |
|---|------|---------|--------|-------------|---------|
| 18 | Plaza Retail | Q3 2024 | PLZ-UN.TO | Control | 18_PLZ-UN_Q3_2024/ |
| 8 | CAPREIT | Q4 2024 (or Q3) | CAR-UN.TO | Cut 84.5% | 08_CAR-UN_Q4_2024/ |
| 9 | H&R | Q4 2024 (or Q3) | HR-UN.TO | Cut 41.2% | 09_HR-UN_Q4_2024/ |
| 10 | Euro Res | Q4 2024 (or Q3) | ERE-UN.TO | Cut 99.0% | 10_ERE-UN_Q4_2024/ |
| 19 | CT REIT | Q4 2024 (or Q3) | CRT-UN.TO | Control | 19_CRT-UN_Q4_2024/ |
| 20 | Extendicare | Q4 2024 (or Q3) | EXE.TO | Control | 20_EXE_Q4_2024/ |

---

## Speed Tips

### 1. Group by REIT (Minimize Searches)

**REITs with multiple observations:**
- **H&R REIT (3x):** Q4 2022, Q4 2023, Q4 2024
- **CT REIT (3x):** Q3 2022, Q1 2023, Q4 2024
- **Nexus Industrial (2x):** Q3 2022, Q2 2023
- **Extendicare (2x):** Q3 2023, Q4 2024

**Strategy:** Download all quarters for these REITs in one session

### 2. Batch Downloads (Browser Feature)

- Queue multiple downloads before clicking
- Most browsers allow 6-10 simultaneous downloads
- Let them download while you search for next batch

### 3. Keyboard Shortcuts

- `Ctrl+T` - New tab
- `Ctrl+F` - Find in page (search for quarter)
- `Ctrl+Click` - Open download link in new tab (queue downloads)
- `Alt+S` - Save download (some browsers)

### 4. Template Search Queries

Pre-paste these into SEDAR+ search:
```
HR-UN.TO
CRT-UN.TO
AX-UN.TO
NXR-UN.TO
EXE.TO
SOT-UN.TO
D-UN.TO
NWH-UN.TO
AP-UN.TO
CAR-UN.TO
ERE-UN.TO
IIP-UN.TO
SRU-UN.TO
PLZ-UN.TO
```

### 5. File Organization

**Option A: Batch Move (Faster)**
1. Download all files to default ~/Downloads/
2. Sort by download time
3. Batch move to correct directories at end
4. Rename if needed

**Option B: Direct Save (More Organized)**
1. Save each file directly to target directory
2. Name correctly during download
3. No post-processing needed

**Recommended:** Option A for speed, Option B for organization

---

## Verification Checkpoints

After each batch, verify downloads:

```bash
# Quick count
find Issuer_Reports/phase1b/pdfs/ -name "*.pdf" | wc -l

# Detailed verification
python scripts/verify_phase1b_downloads.py
```

**Expected counts after each batch:**
- After Batch 1: 14 PDFs (7 obs × 2 files)
- After Batch 2: 24 PDFs (12 obs × 2 files)
- After Batch 3: 28 PDFs (14 obs × 2 files)
- After Batch 4: 40 PDFs (20 obs × 2 files) ✅

---

## Troubleshooting

### Q4 2024 Not Available

**Check filing status:**
- Most REITs file Q4 by end of February
- Check SEDAR+ for "Date filed"
- If not available: Use Q3 2024 instead

**Update tracking:**
```python
# Mark observation as using proxy quarter
notes = "Used Q3 2024 as proxy (Q4 2024 not filed yet)"
```

### Wrong Quarter Downloaded

**How to verify:**
- Check filing date in PDF
- Look for "Quarter ended [DATE]" on first page
- Verify matches observation quarter

### Missing MD&A

**Some REITs combine statements and MD&A in one PDF:**
- Check if single PDF contains both sections
- Look for "Management's Discussion" section
- If combined: Save same PDF to both filenames

### CAPTCHA / Rate Limiting

**If SEDAR+ blocks you:**
- Wait 5-10 minutes
- Switch to different browser/incognito
- Resume from last completed observation

---

## Expected Timeline

| Batch | Observations | Time | Cumulative |
|-------|--------------|------|------------|
| 1 | 6 obs | 2.5 hours | 2.5 hours |
| 2 | 6 obs | 2 hours | 4.5 hours |
| 3 | 2 obs | 1 hour | 5.5 hours |
| 4 | 6 obs | 2.5 hours | 8 hours |
| **Total** | **20 obs** | **8 hours** | **8 hours** |

**With breaks and Q4 2024 issues:** 8-10 hours total

---

## After Downloads Complete

1. **Verify all files:**
   ```bash
   python scripts/verify_phase1b_downloads.py
   ```

2. **Commit downloads** (optional - PDFs are large):
   ```bash
   git lfs track "*.pdf"  # If using Git LFS
   # OR: Don't commit PDFs (add to .gitignore)
   ```

3. **Proceed to extraction:**
   ```bash
   # Next step: Run Phase 1-3 extraction pipeline
   python scripts/run_phase1b_extraction.py
   ```

---

**Ready to start!** Follow batches 1-4 in order, or parallelize by opening multiple SEDAR+ tabs for different REITs.

**Remember:** The download process is manual but the extraction afterward (Phase 1-3) is fully automated and takes only ~9 minutes runtime.
