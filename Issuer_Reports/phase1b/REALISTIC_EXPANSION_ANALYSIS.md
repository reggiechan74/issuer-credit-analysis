# Realistic Dataset Expansion Analysis

**Constraint:** Canada has only ~25-30 publicly traded REITs

**Current Coverage:** 13 unique REITs, 19 observations

---

## Canadian REIT Universe by Sector

### ✅ Already Included (13 REITs)

**Office (4):**
- Allied Properties - TARGET ✓
- Dream Office - TARGET ✓
- Slate Office - TARGET ✓
- (H&R REIT - diversified/office component)

**Residential (3):**
- CAPREIT - TARGET ✓
- InterRent - CONTROL ✓
- European Residential - TARGET ✓

**Retail (2):**
- Plaza Retail - CONTROL ✓
- CT REIT - CONTROL ✓

**Industrial (1):**
- Nexus Industrial - CONTROL ✓

**Diversified (2):**
- H&R REIT - TARGET ✓ (3 observations)
- Artis REIT - TARGET ✓

**Healthcare (1):**
- NorthWest Healthcare - TARGET ✓

**Other (1):**
- Extendicare - CONTROL ✓ (senior care, not REIT)

---

## 🔍 Potential Additions (7-12 more REITs)

### Large Cap REITs Not Yet Included

**Retail:**
- **RioCan REIT** (REI-UN.TO) - Largest retail REIT, $4B+ market cap
  - Potential: Likely has distribution history data
  - Check for cuts: 2020-2024 period
  - Estimated: 2-3 observations

- **SmartCentres REIT** (SRU-UN.TO) - Walmart-anchored retail
  - Phase 1B Obs 17 (incomplete - file too large)
  - Retry extraction: Q3 2023
  - Estimated: 1 observation

- **Choice Properties REIT** (CHP-UN.TO) - Loblaw-controlled, grocery-anchored
  - Potential: Very stable, may not have cuts
  - Type: Likely CONTROL
  - Estimated: 1-2 observations

- **First Capital REIT** (FCR-UN.TO) - Urban retail centers
  - Potential: Check for COVID-era cuts
  - Estimated: 1-2 observations

**Residential:**
- **Boardwalk REIT** (BEI-UN.TO) - Western Canada apartments
  - Potential: Stable residential, likely CONTROL
  - Estimated: 1-2 observations

- **Killam Apartment REIT** (KMP-UN.TO) - Atlantic Canada apartments
  - Potential: Regional exposure, check for cuts
  - Estimated: 1-2 observations

- **Minto Apartment REIT** (MI-UN.TO) - Ontario apartments
  - Potential: Recently public (2018), check history
  - Estimated: 1-2 observations

**Industrial:**
- **Dream Industrial REIT** (DIR-UN.TO) - Canadian/European industrial
  - Potential: Strong sector, likely CONTROL
  - Estimated: 1-2 observations

- **Granite REIT** (GRT-UN.TO) - Global logistics (Magna spin-off)
  - Potential: Unique exposure, check for cuts
  - Estimated: 1-2 observations

- **Summit Industrial Income REIT** (SMU-UN.TO) - Canadian industrial
  - Potential: Small cap, check stability
  - Estimated: 1-2 observations

**Diversified:**
- **Cominar REIT** - Was large diversified REIT
  - Status: Taken private 2021 (not available)

**Healthcare:**
- **Chartwell Retirement Residences** (CSH-UN.TO) - Senior housing
  - Similar to Extendicare, not pure REIT
  - Estimated: 1-2 observations

---

## 📊 Realistic Expansion Estimate

### Scenario A: Conservative (n=25-30 total)
- Add 5-7 unique REITs
- Each with 1-2 observations (different quarters)
- Total: 19 current + 6-11 new = **25-30 observations**

**Priority additions:**
1. **RioCan** (2-3 obs) - Must have, largest retail REIT
2. **SmartCentres** (1 obs) - Fix incomplete Obs 17
3. **Boardwalk** (1-2 obs) - Large residential CONTROL
4. **Dream Industrial** (1-2 obs) - Industrial CONTROL
5. **First Capital** (1-2 obs) - Retail, check for cuts
6. **Killam** (1-2 obs) - Regional residential
7. **Choice Properties** (1 obs) - Stable CONTROL

**Expected distribution:**
- Targets (cuts): 12-15 total (+2-5 new)
- Controls (no cuts): 13-15 total (+4-6 new)
- **Total: 25-30 observations**

### Scenario B: Aggressive (n=30-35 total)
- Add all 10-12 available REITs
- Multiple quarters for some (before/after distribution changes)
- Total: 19 current + 11-16 new = **30-35 observations**

**Additional REITs beyond Scenario A:**
8. Granite REIT (1-2 obs)
9. Summit Industrial (1-2 obs)
10. Minto Apartment (1-2 obs)
11. Chartwell (1 obs)

---

## 🎯 Recommended Strategy

### Option 1: Temporal Expansion (Easiest)
**Add more quarters for REITs we already have:**
- H&R REIT: Add Q1-Q3 2022, 2023, 2024 (6 more obs)
- Artis REIT: Add Q1-Q3 2022, Q1-Q4 2023 (7 more obs)
- Allied Properties: Add Q1-Q3 2023, 2024 (6 more obs)

**Pros:**
- Already have PDFs/access for these issuers
- Can track distribution cut trajectory over time
- Total: 19 + 19 = **38 observations** easily achievable

**Cons:**
- Observations from same REIT are not fully independent
- May need to adjust CV strategy (group by issuer)

### Option 2: Breadth Expansion (Better for diversity)
**Add 5-7 new unique REITs:**
- RioCan (2 obs)
- SmartCentres (1 obs - fix incomplete)
- Boardwalk (2 obs)
- Dream Industrial (2 obs)
- First Capital (2 obs)
- Killam (2 obs)

**Total: 19 + 11 = 30 observations**

**Pros:**
- More diverse REIT coverage
- Better generalization across issuers
- More representative of Canadian REIT universe

**Cons:**
- Need to source new PDFs
- More extraction time (Phase 1-3 pipeline)

### Option 3: Hybrid (Recommended) ✅
**Combine both strategies:**
1. Add RioCan (2-3 obs) - MUST HAVE
2. Fix SmartCentres Obs 17 (1 obs)
3. Add 2-3 more unique REITs (Boardwalk, Dream Industrial, First Capital)
4. Add 2-3 more quarters for existing cut REITs (Artis, Allied)

**Total: 19 + 8-10 = 27-29 observations**

**This achieves:**
- Breadth: 16-17 unique REITs (covers 60-65% of Canadian REIT universe)
- Depth: Multiple observations for key distribution cut issuers
- Balance: ~14-15 targets, ~13-14 controls

---

## 🚀 Execution Plan (Hybrid Strategy)

**Week 1: Add Key Missing REITs (5 new obs)**
1. RioCan Q4 2023, Q4 2024 (2 obs) - Large retail REIT
2. SmartCentres Q3 2023 (1 obs) - Fix incomplete extraction
3. Boardwalk Q4 2023 (1 obs) - Residential CONTROL
4. Dream Industrial Q4 2024 (1 obs) - Industrial CONTROL

**Week 2: Temporal Expansion for Cut REITs (5 new obs)**
5. Artis Q1-Q3 2022 (3 obs) - Track cut trajectory
6. Allied Q2 2023 (1 obs) - Pre-cut observation
7. H&R Q2 2023 (1 obs) - Mid-cut period

**Result:**
- Total observations: 19 + 10 = **29 observations**
- Unique REITs: 13 + 3 = **16 REITs**
- Coverage: 55-60% of Canadian REIT universe
- Expected F1: **0.75-0.80** with n=29 and better features

---

## 📍 Bottom Line

**You're right - we can't get to n=50 in Canada.**

**Realistic targets:**
- **n=25-30:** Achievable with Scenario A/B
- **n=30-35:** Possible with Hybrid strategy
- **n=50+:** Not possible (insufficient Canadian REITs)

**For F1 ≥ 0.75:**
- n=25-30 should be sufficient with proper feature engineering
- Focus on temporal patterns (quarters before/after cuts)
- Consider alternative models (logistic regression) that work better with n=25-30

**Next Decision:**
- Proceed with Hybrid expansion to n=27-29? (~2 weeks work)
- Or accept current F1=0.690 and focus on interpretability?

