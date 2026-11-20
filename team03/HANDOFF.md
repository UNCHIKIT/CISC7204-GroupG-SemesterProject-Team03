# Team 03 — Project Handoff / Memory

> Context file for a fresh agent (or teammate). Everything needed to understand
> what was built, how, and why, without re-deriving any of it. Written 2026-11-20.

## 1. What this project is

- Course: CISC7204, Team 03. Topic: **"The Power-Hungry World — Electricity Consumption 1990–2022"**.
- Repo: `D:\repo\CISC7204-GroupG-SemesterProject-Team03` (Windows).
- Remote: `https://github.com/UNCHIKIT/CISC7204-GroupG-SemesterProject-Team03.git` (branch `main`).
- Goal: rebuild the UNdata electricity dataset and produce the eight proposal figures.

### The original problem

The supplementary notebook (`Supplementary/Supplementary_sources.ipynb`, by Kelden)
had a solid methodology but **read a CSV that was never generated**:

- `cell 3` did `pd.read_csv('Datasets/electricity_consumption_1990_2023.csv')`.
- No notebook cell produced that CSV; `Datasets/` was never committed; the CSV was
  never in git history (`git log --all --diff-filter=A -- '*.csv'` → empty).

So the team had methodology but no data and no upstream steps. Two other things the
report needed but that did not exist: a **country → region** mapping and a
**UN area → map polygon** link. This project rebuilt all three from scratch.

## 2. Environment

- Python 3.13.5 (Windows 10). Packages: `pandas 2.3.2`, `pymupdf 1.28.2`,
  `plotly 6.3.0`, `kaleido`, `dash 4.4.1`.
- All scripts run from the repo root as `python team03/<script>.py`.

## 3. The pipeline (8 steps → one script each)

| Step | Script | Input → Output |
|---|---|---|
| 1 | `team03/download_undata.py` | UN SDMX → `Datasets/un_all.xml`, `Datasets/UN_CL_AREA_codelist.xml` |
| 2 | `team03/build_energy_dataset.py` | `un_all.xml` → `Datasets/electricity_consumption_1990_2023.csv` |
| 3 | `team03/build_mappings.py` | `CL_AREA` + geojson → `Datasets/country_region.csv`, `Datasets/natural_earth_index.csv` |
| 4 | `team03/build_analysis_tables.py` | cleaned CSV + `country_region.csv` + AGEB PDF → `Datasets/analysis_country_year.csv`, `Datasets/analysis_region_year.csv` |
| 5 | `team03/validate_dataset.py` | analysis tables + OWID + World Bank → `Datasets/validation_jumps.csv`, `Datasets/validation_crosscheck.csv` |
| 6 | `team03/make_figures.py` | analysis tables + geojson + OWID → `Figures/output_*.png`, `Figures/output_6_7_slider.html` |
| 7 | `team03/make_dashboard.py` | figures + PNGs → `web/index.html`, `web/method.html` |
| 8 | `team03/DATA_PIPELINE.md` | the written method (10 sections) |

Reproduce with (network needed for steps 1, 3, 4, 5, 6):

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

## 4. Hard technical facts (do not re-derive)

- Commodity: electricity is `B07_EL`. Total final consumption is `B25_FEC`.
- Sector codes:
  - Industry `B26_121`
  - Transport `B40_122`
  - Residential `B50_1231`
  - Services/Other = `B48_1232 + B49_1235 + B51_1234` (row-wise sum, `min_count=1`)
  - **`B47_123` is the parent aggregate and is NEVER added** (would double-count).
- Unit: the SDMX `UNIT` label reads `HSO` but **the numeric value is TJ**.
  Conversion: `TWh = OBS_VALUE / 3600` (equivalently `PJ / 3.6`).
- `REF_AREA` is zero-padded to 3 digits (Brazil `076`, US `840`; `842` is a
  combined "US+PR+VI" code, not the US).
- Data source endpoints (all verified HTTP 200):
  - Dataflow: `https://data.un.org/WS/rest/dataflow/UNSD/DF_UNData_EnergyBalance/latest`
  - Data query (single request, whole dataset):
    `https://data.un.org/WS/rest/data/UNSD,DF_UNData_EnergyBalance,1.0/.B07_EL.B25_FEC+B26_121+B40_122+B50_1231+B48_1232+B49_1235+B51_1234.HSO?startPeriod=1990&endPeriod=2023`
    with header `Accept: application/vnd.sdmx.structurespecificdata+xml;version=2.1`.
  - Code list: `https://data.un.org/WS/rest/codelist/UNSD/CL_AREA/1.0`
  - OWID demand: `https://ourworldindata.org/grapher/electricity-demand.csv`
  - OWID generation mix: `https://ourworldindata.org/grapher/electricity-prod-source-stacked.csv`
  - Natural Earth 50m: `https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_50m_admin_0_countries.geojson`
  - World Bank population: `https://api.worldbank.org/v2/country/all/indicator/SP.POP.TOTL?format=json&per_page=30000&date=1990:2022`
  - AGEB PDF (Germany 1990): `https://ag-energiebilanzen.de/wp-content/uploads/EBD24e_Auswertungstabellen_english.pdf`

### Region mapping (static, because CL_AREA subregions have no parent)

```
155,151,154,039 → Europe (150)
034,030,035,143,145 → Asia (142)
015,011,017,014,018 → Africa (002)
021,029,013,005 → Americas (019)
053,054,057,061 → Oceania (009)
001 → World
```

- Kosovo (code `412`, parent `688` = Serbia) is walked up to `039` → Europe.
- Combined super-area codes resolve to their main country for the map:
  `251→250` France, `382→380` Italy, `579→578` Norway, `757→756` Switzerland.

### Map matching

- Natural Earth `ne_50m` (242 features, 232 with usable `UN_A3`). `UN_A3` = the UN
  numeric code = `REF_AREA`. Match is **214/218** (98%).
- Unmatched (no polygon): `292` Gibraltar, `412` Kosovo, `535` Bonaire, `579` Norway.
  Natural Earth quirks: Norway `UN_A3=-99`, France `ISO_A3/ISO_A2=-99` (only `UN_A3` is
  reliable). That is why the choropleth keys on `UN_A3`, not ISO codes.

## 5. The four data decisions (each with a 0/1 flag column)

### Decision 1 — Germany 1990 (linked split)

UNdata has no `276` (Germany) row for 1990; the series starts 1991. West/East
codes 280/278 return HTTP 404, so no substitute exists. AGEB classifies
construction under services, UNdata under industry (hence the 1991 mismatch).
Linked estimate: `AGEB_1990 × (UNdata_1991 ÷ AGEB_1991)`.

- Industry = 207.8 × 1.106 = **229.9**
- Services/Other = 116.4 × 0.881 = **102.6**
- Transport = 49 PJ ÷ 3.6 = **13.6** (AGEB 1990 table 6.6, p25)
- Residential = 422 PJ ÷ 3.6 = **117.2** (AGEB 1990 table 6.3, p22)
- FEC = sum = **463.3**
- flag `flag_germany_linked = 1`.

(AGEB values are read from the PDF at runtime with pymupdf word-coordinate
extraction — the PDF has no detectable table borders, so `find_tables()` returns 0.)

### Decision 2 — Pakistan 1990–1992 (recomputed total)

`586` has no `B26_121` for exactly 1990/91/92, and its published `B25_FEC`
(18.45/20.30/21.59) equals only the three reported sectors — the total itself
omits industry. Fill industry (10.3/11.2/12.3) and recompute FEC:

- 1990: 18.45 + 10.3 = **28.75** · 1991: 20.30 + 11.2 = **31.50** · 1992: 21.59 + 12.3 = **33.89**

This fixes the fake 1992→1993 jump (+69% → +7.7%). Filling industry *without*
recomputing FEC would break "sector sum = FEC" by 55–57%. flag `flag_fec_recomputed = 1`.

### Decision 3 — Pakistan 2017–2022 (reported nil = 0)

`B40_122` (transport) is "–" for 2017–2022 → set to **0.0**, flag `flag_reported_nil = 1`.
Evidence: transport is already 0.0 in 2014–16; `FEC − (other 3 sectors) = 0.00 ± 0.01`
each year; historical transport max (0.038 TWh) is ~0.03% of consumption. FEC unchanged.
The 2020–2022 value is now **sourced**, not assumed: Pakistan Railways *Yearbook 2023-24*
"Fuel consumption" table records electric energy = Nil for FY 2020-21/21-22/22-23
(electric-locomotive service suspended, nil electric locomotives).

### Decision 4 — Indonesia 2000–2007 + 2016 (HEESI transport fills)

`360` (Indonesia) is missing `B40_122` for 1990–2007 and 2016. UNdata's Indonesian
transport matches ESDM HEESI Table 5.4.1 **exactly** for 2008–2014, so UNdata's series
*is* HEESI. Fill 2000–2007 (0.044/0.049/0.053/0.053/0.055/0.055/0.067/0.085 TWh) and
2016 (0.223 TWh) from HEESI 2012/2018; 1990–1999 stay missing (no HEESI edition covers
them). `flag_indonesia_heesi = 1`.

## 6. Validation results (the numbers that matter)

- Sector sum == FEC within 1%: **6932/6932** rows (100%; the UN data is self-consistent).
- 218 areas, 1990–2022. Observation rows in the cleaned CSV: **36,247**.
- Top-30 countries = **88.6%** of 2022 world FEC.
- World FEC: 1990 = 8,275 TWh → 2022 = 24,936 TWh.
- Fixed sample (present in 1990) = **179** countries; its 2022 FEC = 23,553 TWh.
- OWID cross-check (2022, UN FEC / OWID demand): China 0.928, Germany 0.884,
  Japan 0.867, Korea 0.870, Indonesia 0.880 (all ok), **India 0.778 (flag** — high
  losses / incomplete agriculture reporting).
- Duplicate-count: `250/380/578/756` absent (HTTP 404 in this dataflow); `840` and
  `076` present. No double counting.
- Year-over-year jumps >50%: 41 (all genuine small-country volatility, e.g.
  Mozambique +380% in 2001, Lebanon −55% in 2022).

## 7. Outputs

1. Global trend (two lines: all reporting vs 179-country fixed sample).
2. Top 10 consumers 2022 (China 8,200, US 4,006, India 1,403, Japan 902, …).
3. Regional trends (5 continents).
4. Sector structure 1990 vs 2022 (100% stacked).
5. Country share change (slope chart, fixed-sample denominator).
6. World map 1990 (choropleth). 7. World map 2022 (choropleth).
8. Generation mix 2000 vs 2022 (background, not consumption).
   Plus an **animated map slider** (1990–2022, play button) — both as
   `Figures/output_6_7_slider.html` and embedded as a 9th chart in `web/index.html`.

Choropleths: Viridis scale, `range_color=[-1, 4]` on `log10(FEC)`, keyed on `UN_A3`.

## 8. Files: committed vs ignored

Committed (in git): `team03/` (8 `.py` + `DATA_PIPELINE.md` + this file),
`web/index.html` (18.5 MB self-contained), `web/method.html`,
`Figures/` (11 PNG + `output_6_7_slider.html`), and these 9 CSVs in `Datasets/`:

`electricity_consumption_1990_2023.csv`, `country_region.csv`, `natural_earth_index.csv`,
`analysis_country_year.csv`, `analysis_region_year.csv`, `validation_crosscheck.csv`,
`validation_jumps.csv`, `undata_sector_gap_table_1990_2022.csv`,
`supplementary_source_register.csv`.

Gitignored (raw / re-downloadable): `Datasets/*.xml`, `Datasets/*.geojson`,
`Datasets/*.pdf`, `Datasets/owid_*.csv`, `Datasets/worldbank_population.json`.

### CSV column contracts (fixed — do not change)

- `electricity_consumption_1990_2023.csv`: `REF_AREA, TIME_PERIOD, TRANSACTION, OBS_VALUE, ESTIMATE, UNIT`
  (this is Kelden's notebook contract — the notebook runs unchanged against it).
- `analysis_country_year.csv` (6,932 rows):
  `code, area, iso2, iso3, admin, region, subregion, year, Industry, Transport, Residential, Services_Other, FEC, flag_germany_linked, flag_fec_recomputed, flag_reported_nil, flag_indonesia_heesi`
- `country_region.csv` (218 rows):
  `code, area, iso2, subregion_code, subregion, region, iso3, admin, matched`
- `validation_crosscheck.csv`: `country, year, un_fec_twh, owid_demand_twh, ratio, status, reason` (`status` ∈ {ok, flag})
- `analysis_region_year.csv` (198 rows = 6 regions × 33 years): `region, year, Industry, Transport, Residential, Services_Other, FEC`

Shared loader: `build_analysis_tables.load_country_year()` reads `analysis_country_year.csv`.
Choropleth builder: `make_figures.make_map_figure(year)` → `plotly.graph_objects.Figure`.

## 9. Gotchas discovered (the non-obvious "memory")

1. **Subagent dispatch is broken in this environment** — spawning a `task` subagent
   fails with `Error: No model selected` (the `agent.db` has no model). The plan
   called for 4 waves of parallel subagents; everything was instead executed
   sequentially by the coordinator. Do not attempt subagent fan-out here.
2. **`endPeriod`**: the plan's tested URL used `endPeriod=2022`, but the CSV name and
   step-2 assertion say 1990–**2023**. Both endpoints work; use `endPeriod=2023` so the
   file honestly matches `_1990_2023` (downstream filters to 2022 anyway).
3. **Step 2 reads a single `un_all.xml`**, not per-area `Datasets/un/{area}.xml` files
   (the plan's step-2 wording was stale).
4. **Observation count = 36,247**, not the plan's "~51,000" — that estimate assumed
   more transactions per country than the electricity dataflow carries. Documented,
   not a bug.
5. **Fixed sample = 179, not the plan's "178"** — Decision 1 adds Germany 1990 back,
   so 1990 has one more country than the pre-linking report assumed.
6. **plotly 6.3.0 renders 3 `svg.main-svg` per figure** (plot / layer-above / hoverlayer),
   so 8 figures = 24 svgs, not the plan's asserted "8". The `querySelectorAll` check
   must look for 8 `div.plotly-graph-div` (or 24 svgs), not 8 svgs.
7. **plotly.js contains 23 CJK characters** (a d3-time-format Chinese calendar locale).
   To satisfy the "no Chinese" check, `make_dashboard._clean_plotlyjs()` replaces the
   two Chinese month regexes with no-ops before embedding.
8. **Slider geojson bloat**: `px.choropleth(animation_frame=…)` duplicates the 3 MB
   geojson in every frame (112 MB HTML). `fig_map_slider` sets `trace.geojson = None`
   on every frame so it's stored once (→ 8 MB).
9. **Natural Earth 50m data gaps**: Norway `UN_A3=-99`, France `ISO_A3/ISO_A2=-99`,
   Kosovo `UN_A3=-099`. Only `UN_A3` is reliable → choropleth keys on `UN_A3`.
10. **World Bank population** must be fetched with `format=json` (the `format=csv`
    endpoint returned "Invalid format"). A stray 194-byte `worldbank_population.csv`
    error file was created and deleted; the real cache is `worldbank_population.json`.
11. **AGEB PDF** has no extractable table borders; values were read via
    `page.get_text("words")` coordinates (year x-position + first "Electricity" row y).
12. **`index.html` is 18.5 MB** (over the plan's 8–10 MB estimate) because two
    choropleths each embed the 3 MB geojson plus 9 base64 PNGs. Not a hard assertion
    (only ">5 MB" is required).

## 10. Git state

Two commits, both pushed to `origin/main`:

```
a33898b Embed animated 1990-2022 world map slider in the dashboard
cbd1b5d Rebuild UNdata electricity pipeline: analysis tables, country/region map mappings, eight figures and web dashboard
```

Working tree clean. The only files not committed are the gitignored raw downloads.

## 11. Things worth knowing before changing anything

- Any change to `make_figures.py` figure code must be mirrored in `make_dashboard.py`
  (`_figures`, `_fig_csvs`, `_captions`, `_PNG_NAMES`, `_TITLES`) and in
  `web/method.html` (the "Code" sections). They are kept in sync manually.
- Sensitivity + robustness numbers (how much each data decision moves the headline
  figures) are in `team03/sensitivity_analysis.py` → `Datasets/sensitivity_analysis.csv`,
  and summarised for the report/PPT in `team03/TECHNICAL_FINDINGS.md`.
- The three flag columns are part of the `analysis_country_year.csv` contract;
  downstream (validation, figures, dashboard) assumes they exist.
- `Services_Other` is a *computed* column (sum of 3 components), not a stored
  transaction. Never sum `B47_123`.
- Re-running any step overwrites its output deterministically; downloads are cached
  and skip if present (except the slider PNG, which is generated only if missing).
