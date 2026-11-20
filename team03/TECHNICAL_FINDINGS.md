# Team 03 — Technical Findings (report & PPT)

Final technical summary for the report and presentation. All numbers are
reproducible from `Datasets/` via the scripts in `team03/`; the sensitivity and
robustness tables are produced by `team03/sensitivity_analysis.py`
(→ `Datasets/sensitivity_analysis.csv`).

---

## 1. Headline numbers (PPT slide)

| Quantity | Value |
|---|---|
| World final electricity consumption, 1990 → 2022 | **8,275 → 24,936 TWh** (+201%) |
| World generation, 2022 (OWID) | 28,918 TWh |
| Generation − consumption gap, 2022 | 3,982 TWh (~14% = losses + own-use + trade) |
| Top-30 countries' share of 2022 world FEC | **88.6%** |
| Areas | 218 |
| Observation rows (cleaned CSV) | 36,247 |
| Fixed sample (present in 1990) | 179 countries; 2022 FEC = 23,553 TWh |
| Sector-sum == FEC (all country-years) | **6,932 / 6,932 (100%)** |

Top-5 consumers 2022: China 8,200 · US 4,006 · India 1,403 · Japan 902 · Russia 823 TWh.

---

## 2. The four data decisions — and how much each one matters

| # | Decision | What it changes | Magnitude |
|---|---|---|---|
| 1 | Germany 1990 (linked AGEB estimate) | adds a whole missing country-year | **+463 TWh to world 1990 (5.6%)**; fixed sample 178→179 |
| 2 | Pakistan 1990–92 (recompute FEC, add industry) | fixes a total that omitted industry | +10.3 / +11.2 / +12.3 TWh (~0.1% of world) |
| 3 | Pakistan 2017–22 transport = 0 (reported nil) | sector split only | **0 TWh** (FEC unchanged) |
| 4 | Indonesia 2000–07 + 2016 transport (HEESI fills) | sector split only | **0 TWh** (FEC unchanged; ~0.04–0.22 TWh) |

**Sensitivity result:** the only decision that moves a headline aggregate is
**Germany 1990** — and only in 1990. Removing it drops world 1990 from 8,275 to
7,812 TWh and the 1990 Industry share from 44.92% to 44.64% (−0.28 pp). The
other three decisions move world FEC by <0.15% or nothing, and none of them
touch 2022. Conclusion: **the conclusions are not artefacts of the decisions.**

*(Full counterfactual table: `Datasets/sensitivity_analysis.csv`.)*

---

## 3. Sector-level robustness

| Check | Result |
|---|---|
| Four-sector sum == FEC within 1% | 6,932 / 6,932 (100%) |
| `B47_123` (parent aggregate) present in raw data | **No** — never added, no double counting |
| `Services_Other` recomputed from the 3 components | max \|diff\| = 0.0000 TWh (6,774 rows) |
| Areas missing an Industry row: 1990 / 2022 | 21 / 15 areas, covering **2.7 / 4.1 TWh (0.03% of world)** |
| Those areas' 3-sector sum vs their FEC | gap 0.00 TWh (they genuinely have ~0 industry) |

Interpretation: the 100% reconcile means a "missing" sector row **re-assigns
electricity between sectors rather than losing it from the total**. The 21/15
areas lacking an Industry row are tiny (0.03% of world FEC) and reconcile
exactly, so the sector-structure figure (Output 4) is **not materially
understated** on Industry.

---

## 4. Validation (four layers)

1. **Internal consistency** — sector-sum == FEC 100%; region sums == World to 0.0 TWh;
   41 remaining year-over-year jumps >50% are genuine small-country volatility.
2. **Cross-dataset (OWID, 2022)** — UN FEC / OWID demand: China 0.928, Germany 0.884,
   Japan 0.867, Korea 0.870, Indonesia 0.880 (band 0.85–0.95); **India 0.778 flagged**
   (high T&D losses / incomplete agriculture reporting).
3. **Headline numbers** — 218 areas; top-30 = 88.6%; sector-sum completeness 100%;
   observations 36,247 (not the plan's ~51,000 — the electricity dataflow carries fewer
   transactions per country).
4. **Duplicate-count** — combined codes 250/380/578/756 are absent (HTTP 404); only the
   combined territories 251/382/579/757 carry data; 840 (US) and 076 (Brazil) present.
   No double counting.

---

## 5. Reproducibility

From the repo root (network needed only for steps 1, 3, 4, 5, 6; downloads are cached):

```
python team03/download_undata.py
python team03/build_energy_dataset.py
python team03/build_mappings.py
python team03/build_analysis_tables.py
python team03/build_supplementary_sources.py
python team03/sensitivity_analysis.py
python team03/validate_dataset.py
python team03/make_figures.py
python team03/make_dashboard.py
```

Every step is deterministic (same inputs → same bytes); re-runs overwrite outputs
identically. Verified end-to-end: the committed `analysis_country_year.csv`
(6,932 rows), the validation CSV, the 18 figures and the two dashboard pages
regenerate to the same numbers above.

---

## 6. Technical explanations (report appendix / PPT speaker notes)

* **Unit.** SDMX `UNIT` reads `HSO` but the numeric `OBS_VALUE` is **TJ**.
  Convert `TWh = OBS_VALUE / 3600`.
* **Sector codes.** Industry `B26_121`, Transport `B40_122`, Residential `B50_1231`,
  Services/Other = `B48_1232 + B49_1235 + B51_1234`. The parent `B47_123` is
  **never** added (would double-count).
* **Combined territory codes.** France-Monaco `251`, Italy-San Marino `382`,
  Norway-Svalbard `579`, Switzerland-Liechtenstein `757` are the data-bearing codes;
  `250/380/578/756` return 404. The choropleth keys on `UN_A3` (Natural Earth), with
  `251→250`, `382→380`, `579→578`, `757→756` for the map.
* **Fixed sample.** 179 countries present in 1990 (Germany 1990 added back by Decision 1).
  Ex-Soviet states appear only from 1992, so the "all reporting" trend includes a
  coverage effect; the fixed sample is the denominator for share comparisons.
* **Generation ≠ consumption.** Generation (28,918 TWh) exceeds final consumption
  (24,936 TWh) by ~14% (losses, own-use, net trade). Generation mix is shown only as
  background and stays out of the four sector shares.
* **Pakistan year convention.** UNdata year *Y* = SBP fiscal year *(Y−1)–Y* up to 2001,
  then *Y–(Y+1)* from 2002; FY 2001-02 is absent. Transport 2020–22 = 0 is sourced to
  the Pakistan Railways *Yearbook 2023-24* (electric energy = Nil; electric-locomotive
  service suspended).
* **Associations, not causes.** The drivers analysis (Kaya decomposition
  E = P × (GDP/P) × (E/GDP)) is arithmetic and observational; it describes *what*
  accounts for growth, never *why*. Any causal claim would need prices, policy,
  technology cost and weather data this project does not hold.

---

## 7. Review — pipeline, validation, reproducibility (what was checked)

### Pipeline (9 scripts)

Every script has a clear input→output contract, caching, and error handling:

1. `download_undata.py` — cached; falls back to the existing cleaned CSV if the
   SDMX service is unreachable.
2. `build_energy_dataset.py` — streams the XML, keeps only `B07_EL` × the 7
   transactions, **excludes `B47_123`**.
3. `build_mappings.py` — CL_AREA name/ISO/parent, static subregion→continent walk-up,
   combined-code resolution, Natural Earth `UN_A3` link.
4. `build_analysis_tables.py` — pivot to TWh, applies the 4 flagged decisions.
4.5 `build_supplementary_sources.py` — gap table + 12-country source register.
4.6 `sensitivity_analysis.py` — decision counterfactuals + sector robustness.
5. `validate_dataset.py` — the four validation layers.
6. `make_figures.py` — 18 figures (PNG + interactive) + the map slider.
7. `make_dashboard.py` — `web/index.html` + `web/method.html`.

No dead code, no unreferenced outputs, no `TODO`s or stubs.

### Validation results (re-run, confirmed)

`validate_dataset.py` re-run confirms the documented numbers exactly: sector-sum == FEC
**6,932/6,932 (100%)**; 218 areas; top-30 = **88.6%**; 36,247 observations; no
double-count (250/380/578/756 absent, 840 and 076 present); OWID cross-check flags
India (0.778) as documented.

### Reproducibility (full re-run)

The whole pipeline was re-run end-to-end and checked against the committed files:

* **Data steps (1–4.6, 5): byte-identical** — `git status` stayed clean after re-running
  all seven; the regenerated CSVs differ by zero bytes.
* **Figures (18 PNGs) + dashboard (`web/index.html`, `web/method.html`): byte-identical.**
* **One finding, now fixed:** `Figures/output_6_7_slider.html` was the only file that
  did not reproduce byte-for-byte. The cause was Plotly's `to_html()` assigning a
  **random container `div_id` (UUID)** on each run — the chart data was identical, only
  three lines (the `<div id>` and its two references) differed. Fixed by pinning
  `div_id="map-slider"`; verified that two serializations now produce equal bytes.

**Conclusion:** the pipeline is deterministic and reproducible; the only
non-determinism found was a cosmetic container ID, now eliminated.
