# Data review — Kelden's draft, checked against the sources (4 Nov 2026)

Scope: the dataset work described in `The Power Hungry World Group Discussion Draft.docx`, checked
independently where the source is public. Verdicts are mine, run against live files today.

## What the draft proposes

| element | draft |
|---|---|
| question | how electricity consumption changed across countries and regions 1990–2022, and which countries and sectors hold the largest shares |
| primary source A | IEA World Energy Balances Highlights, 2026 edition — PJ, 54 countries + 10 aggregates, 1971–2024, sectors split |
| primary source B | UN Statistics Division, energy balance dataflow `DF_UNData_EnergyBalance` — TJ, 218 areas, 1990–2023, no aggregates |
| context source | OWID energy data (Ember + Energy Institute) — TWh, 2000–2022, totals only |
| unit / window | TWh; 1990–2022; 2023 excluded for estimate inflation |
| excluded | data centres, cryptocurrency mining, forecasting |

## Claims I could verify, and the result

| # | draft claim | check | verdict |
|---|---|---|---|
| 1 | 1 TWh = 3.6 PJ = 3 600 TJ | arithmetic | **holds** |
| 2 | 2022 world final consumption 88,859 PJ ≈ 24,700 TWh | 88,859 / 3.6 = 24,683 TWh | **holds** (rounding to 24,700 is fair) |
| 3 | OWID has no sector detail | scanned all 130 columns for electricity-by-sector fields | **holds** — zero such columns; the split must come from IEA/UN |
| 4 | OWID covers 2000–2022 solidly | per-country non-null demand, 2000–2022 | **holds** — **210** countries have demand in all 23 years; 213 have demand in 2022 |
| 5 | "OWID drops to 173 countries in 2023" | counted 2023 entities with demand (212), with demand+generation (212), with demand+GDP (0) | **not reproducible** — 2023 demand is present for 212 entities. OWID's GDP column is empty for 2023 entirely, which may be what the number actually reflects |
| 6 | six territories lack demand 2000–2022 (Antarctica, Curaçao, Micronesia, Netherlands Antilles, N. Mariana Is., Tuvalu) | per-country year coverage | **holds, incomplete** — those six are among **ten** with gaps; the others are East Timor, Montenegro, South Sudan and Western Sahara |
| 7 | UN totals complete for all 218 areas, 2012–2023 | SDMX data endpoint | **unverified here** — the dataflow metadata resolves but every data query under `data.un.org/ws/rest/data/...` returned 404 from this host; needs the interactive download or a working key path |
| 8 | UN transport reported for 98 of 218 areas in 2022 (81 in 2012, 102 in 2023) | same | **unverified here** |
| 9 | 17.3 % of 2022 UN values flagged as estimates (12.9 % 2012, 20.9 % 2023) | same | **unverified here** |
| 10 | UN/IEA total ratios: Indonesia 0.77, China 1.09, India 0.98, Korea 0.95 | requires the IEA file | **unverified here** — IEA World Energy Balances needs a free account and forbids redistribution, so it cannot be re-derived from the repository |

## The structural problem this exposes

Neither primary source is reproducible from the repository. The UN file is a dated manual download; the
IEA file may not be redistributed at all. So a marker — or a teammate — cannot rerun the analysis from
`git clone`, and the numbers in the report can only be traced to a locally cached file that nobody else
holds.

That is a real risk for a proposal whose success criteria include "the notebook runs clean from a restart".
Two ways to remove it, in order of preference:

1. **Cache a checksum-stamped extract of the variables actually used** — country, year, sector, value for
   the shared countries only, with the IEA licence statement and the download date. A derived extract is
   not the licensed raw file.
2. **Make OWID the reproducibility anchor** — it is public, downloadable in one request and covers totals
   and generation for 2000–2022, so anyone can reproduce the world/country trend and generation-mix parts
   even without IEA or UN. Keep IEA as the sector source and say so in the limitations.

Also worth fixing before the proposal is drafted: the draft says the group still has **nine open
decisions**, the first three of which (question wording, window, sector grouping) change every downstream
number. The proposal cannot be written as a plan until at least those three are recorded.
