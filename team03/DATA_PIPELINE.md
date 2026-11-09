# Team 03 — Electricity Consumption Data Pipeline

This document explains, step by step, how the raw UN SDMX data becomes the
country × year and region × year analysis tables and the eight proposal
figures. It is written so that anyone can reproduce every number from scratch.

---

## Purpose and scope

The UNdata Energy Balance electricity series (`B07_EL`) is the single source
for this project. The pipeline rebuilds a dataset that the supplementary
notebook previously *read* but never *produced*, then turns it into:

* `electricity_consumption_1990_2023.csv` — the cleaned long table (TJ), with
  the exact column contract the notebook expects;
* `country_region.csv` — the country → continent and country → map-polygon
  mapping that did not exist before;
* `analysis_country_year.csv` — one row per (country, year) with the four
  sectors and the total, in TWh;
* `analysis_region_year.csv` — the same, aggregated to continents plus a
  `World` row;
* the eight proposal outputs (figures) and the two-page web dashboard.

Time range is **1990–2022** (33 years). Four sectors are tracked — Industry,
Transport, Residential, Services/Other — plus the `B25_FEC` final-consumption
total. The unit of the analysis tables is **TWh**.

---

## Data sources

| Source | URL | Accessed | Size |
|---|---|---|---|
| UN SDMX dataflow | `https://data.un.org/WS/rest/dataflow/UNSD/DF_UNData_EnergyBalance/latest` | 2026-11-10 | (HTTP 200) |
| UN SDMX data query | `https://data.un.org/WS/rest/data/UNSD,DF_UNData_EnergyBalance,1.0/.B07_EL.B25_FEC+B26_121+B40_122+B50_1231+B48_1232+B49_1235+B51_1234.HSO?startPeriod=1990&endPeriod=2023` (header `Accept: application/vnd.sdmx.structurespecificdata+xml;version=2.1`) | 2026-11-10 | 2,822,591 bytes |
| UN CL_AREA code list | `https://data.un.org/WS/rest/codelist/UNSD/CL_AREA/1.0` | 2026-11-10 | 268,851 bytes |
| OWID electricity demand | `https://ourworldindata.org/grapher/electricity-demand.csv` | 2026-11-10 | 161,196 bytes |
| OWID production source stack | `https://ourworldindata.org/grapher/electricity-prod-source-stacked.csv` | 2026-11-10 | 544,028 bytes |
| Natural Earth 50m countries | `https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_50m_admin_0_countries.geojson` | 2026-11-10 | 3,083,490 bytes |
| World Bank population | `https://api.worldbank.org/v2/country/all/indicator/SP.POP.TOTL?format=json&per_page=30000&date=1990:2022` | 2026-11-10 | 1,765,148 bytes |
| AGEB evaluation tables (PDF) | `https://ag-energiebilanzen.de/wp-content/uploads/EBD24e_Auswertungstabellen_english.pdf` | 2026-11-10 | 1,270,123 bytes |

The `endPeriod` is 2023 so the CSV honestly matches its `_1990_2023` name;
every downstream step filters to the 1990–2022 analysis window.

---

## How to reproduce

Run from the repository root (Python 3.13, `pandas`, `pymupdf`, `plotly`,
`kaleido`):

```
python team03/download_undata.py
python team03/build_energy_dataset.py
python team03/build_mappings.py
python team03/build_analysis_tables.py
python team03/validate_dataset.py
python team03/make_figures.py
python team03/make_dashboard.py
```

Network is required by steps 1, 3 (Natural Earth), 4 (AGEB PDF), 5 (OWID and
World Bank) and 6 (OWID generation mix). Downloads are cached, so re-runs are
free. Downloading takes about 10 seconds; the rest runs in under a minute.

Expected outputs are listed in the [File manifest](#file-manifest).

---

## Pipeline stages

### `download_undata.py` (step 1)

Input: the UN SDMX service. Output: `Datasets/un_all.xml` (the full 1990–2023
electricity series in a single request) and `Datasets/UN_CL_AREA_codelist.xml`.
If the service is unreachable and `electricity_consumption_1990_2023.csv`
already exists it continues; otherwise it stops and asks for that CSV.

### `build_energy_dataset.py` (step 2)

Parses `un_all.xml` with `xml.etree.ElementTree`, walking `Series` and `Obs`.
It keeps only `COMMODITY == "B07_EL"` and the seven transactions
`B25_FEC, B26_121, B40_122, B50_1231, B48_1232, B49_1235, B51_1234`, drops
empty `OBS_VALUE`, and writes the long CSV with columns
`REF_AREA, TIME_PERIOD, TRANSACTION, OBS_VALUE, ESTIMATE, UNIT`.
`REF_AREA` is zero-padded to three digits (Brazil is `076`, the US is `840`;
`842` is a combined code). No unit conversion happens here.

### `build_mappings.py` (step 3)

Reads `CL_AREA` into `code → (name, iso2, parent)` (the alpha-2 code is
extracted from the description with `ISO 3166-2 code: ([A-Z]{2})`). The
subregion is the parent code; a static table maps subregion to continent
because subregions carry no parent of their own:

```
155,151,154,039 -> Europe (150)
034,030,035,143,145 -> Asia (142)
015,011,017,014,018 -> Africa (002)
021,029,013,005 -> Americas (019)
053,054,057,061 -> Oceania (009)
001 -> World
```

Kosovo (412, parent 688 = Serbia) is walked up to 039 → Europe. Combined
super-area codes are resolved to their main country — `251→250` (France),
`382→380` (Italy), `579→578` (Norway), `757→756` (Switzerland) — so the map
can colour them. Natural Earth features are indexed by `UN_A3` (the UN numeric
code). Output: `natural_earth_index.csv` and `country_region.csv`.

### `build_analysis_tables.py` (step 4)

Reads the cleaned CSV, filters `1990 ≤ TIME_PERIOD ≤ 2022`, converts
`TWh = OBS_VALUE / 3600` (the `UNIT` label reads `HSO` but the value is TJ),
pivots each `(REF_AREA, year)` into the four sectors plus `FEC`.
`Services_Other` is the row-wise sum of the three service components with
`min_count=1`; the parent aggregate `B47_123` is **never** added. Applies the
three data decisions (below), joins `country_region.csv`, and writes
`analysis_country_year.csv` and `analysis_region_year.csv`.

### `validate_dataset.py` (step 5)

The four-layer validation described in [Validation](#validation).

### `make_figures.py` (step 6) and `make_dashboard.py` (step 7)

Generate the eight figures (PNG + interactive) and assemble the two-page web
dashboard.

---

## Data decisions

### 1. Germany 1990 — linked sector split

UNdata has no `276` (Germany) row for 1990; the series begins in 1991. The
former West/East codes (280/278) return HTTP 404, so no West-German series can
be substituted. The 1990 sector split is therefore *linked* from AGEB:

```
linked_1990 = AGEB_1990 × (UNdata_1991 ÷ AGEB_1991)
```

AGEB classifies construction under services while UNdata classifies it under
industry, so UNdata 1991 industry (214.5 TWh) is ~10.6% higher than AGEB 1991
industry and services ~11.9% lower. Applying the ratio:

* Industry = 207.8 × 1.106 = **229.9** TWh
* Services/Other = 116.4 × 0.881 = **102.6** TWh
* Transport = 49 PJ ÷ 3.6 = **13.6** TWh (AGEB 1990, table 6.6)
* Residential = 422 PJ ÷ 3.6 = **117.2** TWh (AGEB 1990, table 6.3)
* FEC = sum = **463.3** TWh

Transport and Residential are taken directly from AGEB 1990 (they differ from
UNdata by <1% in 1991). `flag_germany_linked = 1`.

### 2. Pakistan 1990–1992 — recomputed total

`586` (Pakistan) is missing `B26_121` (industry) for exactly 1990, 1991 and
1992. Its published `B25_FEC` for those years (18.45 / 20.30 / 21.59) equals
the sum of only the *three* reported sectors, so the total itself omits
industry. Industry is filled from the State Bank of Pakistan (10.3 / 11.2 /
12.3 TWh) and the FEC is recomputed as `FEC + industry`:

* 1990: 18.45 + 10.3 = **28.75**
* 1991: 20.30 + 11.2 = **31.50**
* 1992: 21.59 + 12.3 = **33.89**

The 1992→1993 jump of +69% is thereby corrected to +7.7%, consistent with the
industry change of +6.0% (12.3 → 13.04). Filling industry *without* recomputing
FEC is not viable: the four-sector sum would exceed the total by 55–57% and
break the "sector sum = FEC" invariant. `flag_fec_recomputed = 1`.

### 3. Pakistan 2017–2022 — reported nil treated as 0

Pakistan reports `B40_122` (transport) as "–" (nil) for 2017–2022. These are
set to 0 with `flag_reported_nil = 1`. Three pieces of evidence support this:
(i) the transport value is already 0.0 in 2014–2016, so 0 continues the same
convention; (ii) `FEC − (Industry + Residential + Services_Other)` is 0.00 ±
0.01 TWh in each of those six years, so the total is fully explained by the
other three sectors; (iii) the historical transport maximum (0.038 TWh) is
~0.03% of national consumption, so the impact is negligible. FEC is unchanged.
Any other missing value is **never** treated as 0.

---

## Validation

Four layers, all deterministic.

**Layer 1 — internal consistency.** The four-sector sum equals `FEC` to within
1% for **6932/6932** country-years (100%). Year-on-year changes >50% are listed
in `validation_jumps.csv`; after the three decisions the three planned
breakpoints (Germany 1990, Pakistan 1992→93, former USSR 1991→92) are gone, and
the 41 remaining entries are genuine small-country volatility (e.g. Mozambique
+380% in 2001, Lebanon −55% in 2022). Per-capita consumption
(`FEC × 10⁹ ÷ population`, World Bank `SP.POP.TOTL`) is checked against
100–25,000 kWh; 924 country-years fall below 100 kWh (low-income countries).
Each region's sum equals the `World` row exactly (max |difference| 0.0 TWh).

**Layer 2 — cross-dataset (OWID).** For 2022, `UNdata FEC / OWID electricity
demand` should sit in 0.85–0.95 (transmission/distribution losses and own-use
sit between final consumption and generation-side demand):

| Country | Ratio | Status |
|---|---|---|
| China | 0.928 | ok |
| Germany | 0.884 | ok |
| Japan | 0.867 | ok |
| Republic of Korea | 0.870 | ok |
| Indonesia | 0.880 | ok |
| India | 0.778 | flag |

India sits below the band and is recorded in `validation_crosscheck.csv` with a
reason: high transmission and distribution losses and/or incomplete reporting
of agriculture/other electricity in the UN final-consumption classification.
Every ratio <0.75 or >1.00 is recorded individually.

**Layer 3 — Kelden's headline numbers.** 218 areas; top-30 countries account
for 88.6% of 2022 world FEC; sector-sum completeness 100%. (The observation
count is 36,247 rows for the seven-transaction electricity query, not the
~51,000 the report estimated — that estimate appears to have assumed more
transactions per country than the electricity dataflow actually carries.)

**Layer 4 — duplicate-count check.** Codes `250` (France), `380` (Italy),
`578` (Norway) and `756` (Switzerland) all return HTTP 404 in this dataflow;
only the combined codes `251/382/579/757` carry data, so there is no double
counting. The script asserts the four codes are absent from
`analysis_country_year.csv` and that `840` (US) and `076` (Brazil) are present.

---

## Outputs

1. **Global trend** — two lines: all reporting countries and a fixed sample of
   179 countries present in 1990. Caption discloses that 15 former Soviet
   countries have no 1990–91 data (they appear from 1992), so the all-reporting
   rise includes a coverage effect.
2. **Top 10 consumers (2022)** — horizontal bar, ranked by `FEC`.
3. **Regional trends** — one line per continent (Africa, Americas, Asia,
   Europe, Oceania).
4. **Sector structure 1990 vs 2022** — 100% stacked world totals; caption notes
   that 21 (1990) / 15 (2022) areas lack an industry row.
5. **Country share change** — slope chart with the same 179-country fixed
   sample as the denominator in both years.
6. **World map 1990** and **7. World map 2022** — choropleths on Natural Earth
   50m via the `UN_A3` link (214/218 areas coloured), sharing one Viridis scale
   and `range_color=[-1, 4]` (log10 TWh). A separate `output_6_7_slider.html`
   animates 1990–2022.
8. **Generation mix** — OWID world generation stack, 2000 vs 2022; the caption
   states this is generation, not consumption, shown only as background.

---

## Known limitations

* Fifteen former Soviet countries (Russia, Ukraine, Kazakhstan, …) have no data
  for 1990–91 and appear from 1992.
* 21 areas (1990) and 15 areas (2022) do not report an industry row.
* Pakistan 2017–2022 transport is set to 0 by convention (reported nil), not
  because there is no transport electricity.
* Saudi Arabia reports no separate transport classification in UNdata.
* Indonesia is missing from the early 1990s.
* Malaysia and Bangladesh were not individually audited.
* `ESTIMATE=Y` values are retained and the flag is preserved in the raw CSV.
* The original IEA source files cannot be redistributed; only the UN-derived
  aggregates are committed.
* Four areas (Norway `579`, Gibraltar `292`, Kosovo `412`, Bonaire `535`) have
  no Natural Earth 50m polygon; Norway's `UN_A3` is absent from the geojson.

---

## File manifest

| Script | Input | Output |
|---|---|---|
| `download_undata.py` | UN SDMX | `un_all.xml`, `UN_CL_AREA_codelist.xml` |
| `build_energy_dataset.py` | `un_all.xml` | `electricity_consumption_1990_2023.csv` |
| `build_mappings.py` | `UN_CL_AREA_codelist.xml`, geojson | `natural_earth_index.csv`, `country_region.csv` |
| `build_analysis_tables.py` | cleaned CSV, `country_region.csv`, AGEB PDF | `analysis_country_year.csv`, `analysis_region_year.csv` |
| `validate_dataset.py` | analysis tables, OWID, World Bank | `validation_jumps.csv`, `validation_crosscheck.csv` |
| `make_figures.py` | analysis tables, geojson, OWID | `Figures/output_*.png`, `output_6_7_slider.html` |
| `make_dashboard.py` | figures, PNGs | `web/index.html`, `web/method.html` |

`Datasets/` CSV contents:

| File | Rows | Columns |
|---|---|---|
| `electricity_consumption_1990_2023.csv` | 36,247 | `REF_AREA, TIME_PERIOD, TRANSACTION, OBS_VALUE, ESTIMATE, UNIT` (TJ) |
| `country_region.csv` | 218 | `code, area, iso2, subregion_code, subregion, region, iso3, admin, matched` |
| `natural_earth_index.csv` | 242 | `UN_A3, ISO_A3, ISO_A2, ADMIN, NAME` |
| `analysis_country_year.csv` | 6,932 | `code, area, iso2, iso3, admin, region, subregion, year, Industry, Transport, Residential, Services_Other, FEC, flag_germany_linked, flag_fec_recomputed, flag_reported_nil` (TWh) |
| `analysis_region_year.csv` | 198 | `region, year, Industry, Transport, Residential, Services_Other, FEC` (TWh) |
| `validation_crosscheck.csv` | 201 | `country, year, un_fec_twh, owid_demand_twh, ratio, status, reason` |
| `validation_jumps.csv` | 41 | `code, area, year, prev_year, prev_fec_twh, fec_twh, change_pct` |

---

## Differences from the supplementary notebook

The supplementary notebook (`Supplementary/Supplementary_sources.ipynb`) read
`Datasets/electricity_consumption_1990_2023.csv` but never generated it, and
the `Datasets/` directory was never committed. This pipeline:

* adds the missing **upstream download** step (a single UN SDMX request);
* reproduces the notebook's cleaning contract exactly (same columns, same
  `TWh = OBS_VALUE / 3600` conversion, same four sector codes, `B47_123` never
  added), so the notebook still runs unchanged against the rebuilt CSV;
* **commits the produced CSVs** so any team member can regenerate the figures
  without re-downloading;
* adds the two mappings the notebook lacked: **country → continent** and
  **UN area → map polygon** (`country_region.csv`), which are required by the
  regional and choropleth figures.
