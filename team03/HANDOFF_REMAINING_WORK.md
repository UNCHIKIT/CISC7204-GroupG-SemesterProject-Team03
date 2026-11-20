# Team 03 — Handoff: Data Consistency & Supplementary Source Verification (Remaining Work)

> Companion to `HANDOFF.md`. This one hands off the **unfinished** part of the
> project: finalising data consistency and the supplementary national-source
> verification, with the open Pakistan issues as the priority. Everything here
> comes from `Supplementary/Supplementary_sources.ipynb` (Kelden's methodology)
> and the source register that notebook produces.

## 1. What "supplementary source verification" is

Kelden's notebook (`Supplementary/Supplementary_sources.ipynb`) does three things:

1. **Gap table** — ranks countries by 2022 final consumption and marks each of
   Industry / Transport / Residential / Services as `complete`, `missing N: years`,
   or `ABSENT` → writes `Datasets/undata_sector_gap_table_1990_2022.csv`.
2. **Reconcile check** — for the top-30 countries, sums the sector components and
   compares to `B25_FEC`, proving that a "missing" row usually only re-assigns
   electricity between sectors rather than losing it (see `HANDOFF.md` §6: my
   pipeline reproduced this — 100% reconcile).
3. **Source register** — for each gap country, documents the national source
   examined, whether it was accepted/rejected, and the licence → writes
   `Datasets/supplementary_source_register.csv`.

The rebuilt pipeline (`HANDOFF.md`) only applied **three** numeric decisions
(Germany 1990, Pakistan industry 1990–92, Pakistan transport 2017–22 nil). It did
**not** reproduce the full gap table, the per-country source register, or the
Indonesia transport fills. That is the gap this handoff covers.

## 2. The source register — current status (11 countries)

From the notebook's `supplementary_source_register.csv`:

| Country | Gap | Source | Decision | Caveat |
|---|---|---|---|---|
| France | All sectors | SDES *Chiffres clés* | Use UNdata | SDES kept as climate-adjusted cross-check only |
| Germany | All sectors 1990 | AGEB EBD24e T6.1–6.6 | Accepted | linked estimate (see `HANDOFF.md` §5) |
| **Saudi Arabia** | Transport, all years | GASTAT; ECRA booklet | **Unresolved** | no transport category; ECRA copy refused (403) |
| **Indonesia** | Transport 1990–2007, 2016 | ESDM HEESI 2012/2018 T5.4.1 | Accepted (2000–07, 2016) | **1990–1999 still missing** |
| Viet Nam | Transport 1995–2022 | EVN sales | Rejected | sales, no transport category |
| Thailand | Transport 1990–1998 | DEDE / EPPO | Not accessible | DEDE unreachable; EPPO = sales |
| Egypt | Transport 1990–2011 | EEHC report | Rejected | sales, fiscal years |
| **Malaysia** | Transport 1990–1996 | NEB 2022 / NEB 2012 | **Pending** | NEB 2022 starts 2005; archive rate-limited (429) |
| UAE | Transport, all years | FCSC/MoEI; DEWA | Rejected | no transport; DEWA is Dubai only |
| **Pakistan** | Industry 1990–92; Transport 2017–22 | SBP Handbook T2.3; NEPRA SIR 2021 | Accepted (partial) | **transport 2020–22 still missing** |
| **Iran** | Transport 1990–1998 | Ministry of Energy balance | Not accessible | Persian only |

Not yet examined at all: **Bangladesh** (flagged "未查" in the plan limitations).

## 3. Pakistan — the priority (remaining issues)

Pakistan is the only gap country where a missing row **understates the national
total** (industry 1990–92 was omitted from `B25_FEC`), not just re-assigns a
sector. Three things are still open:

### 3.1 Transport 2020–2022 — no source yet

- The State Bank of Pakistan (SBP) *Handbook of Statistics* Table 2.3
  (*Electricity, GWh*) runs only to **FY 2019-20**, so it cannot source 2020–2022.
- NEPRA's *State of Industry Report 2021* (sales: domestic, commercial,
  industrial, agricultural, public lighting, bulk supply, others) has a *railway
  traction* **tariff** but **no traction sales line**.
- Lahore's Orange Line metro (opened October 2020) is counted inside another
  category, so it cannot be split out cleanly.
- Current state: my pipeline sets transport 2020–22 to **0.0** with
  `flag_reported_nil = 1`. This is a *provisional* convention, not a verified
  source value. To finalise, either (a) find a traction source for FY 2020-21 →
  2022-23 (e.g. a newer SBP/NEPRA table or Pakistan Railways), or (b) formally
  document "2020–2022 transport = reported nil, no source" in the limitations.

### 3.2 Transport 2019 — reconciliation warning

SBP's 2019 (FY 2019-20) traction is "–" (nil), but that row "does not reconcile to
its total". The notebook records it as **"use with caution"**. Decide whether to
keep 0 with a caveat or drop the value.

### 3.3 Fiscal-year → calendar-year mapping (the 2002 switch)

UNdata's Pakistan series switches year convention:

- **up to 2001**: UNdata year *Y* = SBP fiscal year *(Y−1)–Y* (e.g. 1993 = 1992-93).
- **from 2002**: UNdata year *Y* = SBP fiscal year *Y–(Y+1)* (e.g. 2002 = 2002-03).
- **FY 2001-02 is absent** from UNdata.
- **2017 and 2019–2023 have no exact SBP match** (UNdata holds revised/newer
  figures; e.g. 2017 UNdata 27,398 vs SBP 2017-18 27,468 GWh, −0.3%).

Any new Pakistan source work must respect this mapping or it will misalign years.

## 4. Indonesia transport fills (not yet applied to the analysis table)

The notebook accepted ESDM HEESI values for Indonesia transport 2000–2007 and 2016
(9 values, in GWh → tiny in TWh):

| Year | 2000 | 2001 | 2002 | 2003 | 2004 | 2005 | 2006 | 2007 | 2016 |
|---|---|---|---|---|---|---|---|---|---|
| GWh | 44.0 | 49.0 | 53.0 | 53.0 | 55.0 | 55.0 | 67.0 | 85.0 | 223.0 |

Note: 2008–2014 UNdata already matches HEESI exactly; from 2015 HEESI diverges
from UNdata (vintage difference). 1990–1999 remain **missing** (no HEESI edition
covers them). My pipeline did **not** write these into `analysis_country_year.csv`;
only the three decisions in `HANDOFF.md` §5 are applied. Decide whether to fold
these 9 values in (they are ~0.04–0.22 TWh, negligible vs Indonesia's ~294 TWh).

## 5. What "finalise" concretely means (checklist)

1. **Pakistan transport 2020–22** — source it or formally close as "reported nil,
   unresolved" (update `flag_reported_nil` / limitations).
2. **Pakistan 2019 transport** — resolve the "does not reconcile" caveat.
3. **Pakistan year-convention** — confirm the 2002 switch is reflected in any new
   values and in the final write-up.
4. **Indonesia** — decide whether to apply the 9 HEESI fills; keep 1990–99 as
   missing (documented).
5. **Saudi Arabia** — retry ECRA (or a Ministry of Energy table) for a transport
   line; otherwise keep "unresolved".
6. **Malaysia** — retry the archived NEB 2012 (URL in the register) after the 429
   rate-limit clears; expect small values 1995–96 (KTM Komuter 1995, STAR LRT
   Dec 1996) and nil before.
7. **Iran** — find an English or translated energy balance, or close as "not
   accessible".
8. **Bangladesh** — check whether it has a transport gap at all and assess a source.
9. **Data consistency** — after any new fill, re-run `validate_dataset.py` and
   confirm the sector-sum == FEC invariant still holds 100% (it must; `B47_123`
   is never added). Update `validation_crosscheck.csv` if a fill changes a 2022
   FEC that is cross-checked against OWID.
10. **Regenerate** — if the analysis CSV changes, re-run
    `build_analysis_tables.py` → `validate_dataset.py` → `make_figures.py` →
    `make_dashboard.py`, and update `DATA_PIPELINE.md` (§5 Data decisions,
    §8 Known limitations) and both handoff files.

## 6. Files the notebook reads/writes (per-country, not yet in git)

The notebook (once the rebuilt `electricity_consumption_1990_2023.csv` is present)
writes these into `Datasets/` — none are committed yet:

- `undata_sector_gap_table_1990_2022.csv` — the gap table.
- `supplementary_source_register.csv` — the 11-country register (above).
- `pakistan_sbp_electricity_by_group_original.csv` — SBP Table 2.3 parsed.
- `pakistan_electricity_fills_sbp.csv` — the Pakistan fills (industry 1990–92,
  transport 2017–19 nil).
- `indonesia_transport_electricity_2000_2016_heesi.csv` — the 9 Indonesia fills.
- `germany_electricity_1990_4sectors.csv` — Germany 1990 AGEB vs linked.

It also **reads** `Datasets/france_electricity_consumption_4sectors_1990_2022.csv`
(an SDES compilation) — this file must exist before the France cross-check cell
runs. Confirm whether it was manually compiled and, if so, commit it.

## 7. Rules to follow (from the notebook's own stated rules)

- Sector-level data only; final consumption, not generation or sales, unless a
  sales series is explicitly documented as a proxy.
- Preserve original categories; never treat missing values as zero without evidence.
- Record the URL, table, and licence for every source.
- Licences: UNSD free (cite); SDES open (décret 2017-638, cite + update date);
  GASTAT open-with-attribution; AGEB/ESDM/SBP/Malaysia-EC = cite or excerpt only,
  do not redistribute the PDFs.
