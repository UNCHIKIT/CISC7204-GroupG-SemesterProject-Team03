"""Build the supplementary-source verification outputs.

Step 4.5 of the Team 03 data pipeline (companion to ``build_analysis_tables.py``).

Reproduces the two outputs of Kelden's ``Supplementary/Supplementary_sources.ipynb``
that the rebuild pipeline did not yet produce, with the supplementary national-source
verification finalised (Pakistan transport 2020-2022, Malaysia, Bangladesh, and the
Indonesia fills now resolved):

* ``Datasets/undata_sector_gap_table_1990_2022.csv`` — per-country sector gap table,
  ranked by 2022 final consumption.
* ``Datasets/supplementary_source_register.csv`` — the per-country source register
  (source examined, decision, caveat, licence, URL).

Both are derived from the committed ``electricity_consumption_1990_2023.csv`` and
``UN_CL_AREA_codelist.xml``; the register rows are the curated verification decisions
documented in ``HANDOFF.md`` / ``HANDOFF_REMAINING_WORK.md`` (with citations). The
numeric fills themselves are applied by ``build_analysis_tables.py``.
"""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
DATASETS = REPO_ROOT / "Datasets"

CLEANED = DATASETS / "electricity_consumption_1990_2023.csv"
CL_AREA = DATASETS / "UN_CL_AREA_codelist.xml"

OUT_GAP = DATASETS / "undata_sector_gap_table_1990_2022.csv"
OUT_REGISTER = DATASETS / "supplementary_source_register.csv"

TJ_PER_TWH = 3600.0
YEARS = list(range(1990, 2023))
SECTORS = {
    "Industry": ["B26_121"],
    "Transport": ["B40_122"],
    "Residential": ["B50_1231"],
    "Services/Other": ["B48_1232", "B49_1235", "B51_1234"],
}

# Curated register. Columns: country, gap, source, decision, reason/caveat, licence,
# source_url. Decisions reflect the final state of the supplementary verification:
#   * Pakistan transport 2020-2022 is now sourced (Pakistan Railways yearbook: electric
#     energy = Nil, electric-locomotive service suspended), not merely assumed.
#   * Malaysia NEB 2012 (archived copy) confirms transport is "-" (not collected)
#     before 2006, so 1990-1996 stays missing (first electric rail: KTM Komuter Aug
#     1995, STAR LRT Dec 1996 -- small, unquantified).
#   * Bangladesh has a real transport gap: Bangladesh Railway is diesel-hauled and the
#     first electric urban rail (Dhaka MRT Line-6) opened only on 28 Dec 2022.
REGISTER = [
    ("France", "All sectors",
     "UNdata code 251 (France-Monaco)",
     "Use UNdata",
     "SDES kept as cross-check (climate-adjusted)",
     "SDES: open licence (decret 2017-638); cite SDES + update date",
     "https://www.statistiques.developpement-durable.gouv.fr/mentions-legales"),
    ("Germany", "All sectors, 1990",
     "AGEB Evaluation Tables EBD24e, Tables 6.1-6.6",
     "Accepted",
     "Transport/Residential direct; Industry/Services/Other boundary differs, linked estimate used",
     "No licence stated; values cited, PDF not redistributed",
     "https://ag-energiebilanzen.de/wp-content/uploads/EBD24e_Auswertungstabellen_english.pdf"),
    ("Saudi Arabia", "Transport, all years",
     "GASTAT Electricity Statistics; ECRA Statistical Booklet",
     "Unresolved",
     "No transport/railway category in any source; Riyadh Metro opened late 2024 (outside window)",
     "GASTAT open reuse with attribution; tables sourced to Ministry of Energy (not confirmed)",
     "https://stats.gov.sa/en/use-policy"),
    ("Indonesia", "Transport 1990-2007, 2016",
     "ESDM HEESI 2012 / 2018 Table 5.4.1",
     "Accepted (2000-2007, 2016; applied)",
     "1990-1999 still missing (no HEESI edition covers them); UNdata matches HEESI exactly 2008-2014",
     "Copyright claimed, no reuse terms; values cited, PDFs not redistributed",
     "https://esdm.go.id/en/publikasi/handbook-of-energy-economic-statistics-of-indonesia-heesi"),
    ("Viet Nam", "Transport 1995-2022",
     "EVN sales by component",
     "Rejected",
     "Sales; no transport category; first metro (Hanoi) opened 2021",
     "-",
     ""),
    ("Thailand", "Transport 1990-1998",
     "DEDE Energy Balance; EPPO electricity statistics",
     "Not accessible / rejected",
     "DEDE unreachable; EPPO = sales by tariff, no transport; UNdata reports 0.0 in 1999",
     "-",
     ""),
    ("Egypt", "Transport 1990-2011",
     "EEHC Annual Report 2018/19",
     "Rejected",
     "Sales, fiscal years, no transport category",
     "Not used; PDF not redistributed",
     "http://www.moee.gov.eg/english_new/EEHC_Rep/2018-2019en.pdf"),
    ("Malaysia", "Transport 1990-1996",
     "Energy Commission NEB 2012 (archived) Figure 31",
     "Unresolved (documented)",
     "NEB 2012 reports transport '-' (not collected) before 2006; KTM Komuter (Aug 1995) and STAR LRT (Dec 1996) imply small unquantified values, nil before 1995",
     "All rights reserved; excerpts with 'Source: Energy Commission' only",
     "https://web.archive.org/web/20220725103818/https://www.st.gov.my/en/contents/publications/statistics_electricity/National%20Energy%20Balance%202012.pdf"),
    ("UAE", "Transport, all years",
     "FCSC/MoEI; DEWA statistics",
     "Rejected",
     "No transport category; DEWA is Dubai only",
     "-",
     ""),
    ("Pakistan", "Industry 1990-1992; Transport 2017-2022",
     "SBP Handbook Table 2.3; NEPRA SIR 2021; Pakistan Railways Yearbook 2023-24",
     "Accepted (industry 1990-92; transport 2017-22 reported nil, sourced)",
     "Transport 2017-19 nil (SBP '-'); 2020-22 nil (Pakistan Railways: electric energy = Nil, electric-locomotive service suspended); 2019-20 SBP row's non-traction components do not sum to its total but traction is unambiguously nil",
     "SBP: non-commercial personal use, unaltered, with source; values cited, PDF not redistributed",
     "https://archive.sbp.org.pk/departments/stats/pakEconomy_HandBook/Chap-2.3.pdf"),
    ("Iran", "Transport 1990-1998",
     "Ministry of Energy energy balance",
     "Not accessible",
     "Sites unreachable; Persian only",
     "-",
     ""),
    ("Bangladesh", "Transport 1990-2020",
     "Bangladesh Railway; Dhaka MRT Line-6",
     "Unresolved (documented)",
     "Bangladesh Railway is diesel-hauled; first electric urban rail (Dhaka MRT Line-6) opened 28 Dec 2022, so 1990-2020 is nil in practice. UNdata itself reports 2021=0.465 and 2022=0.498 TWh (kept as-is; the 2021 value slightly precedes the documented metro opening - observation only)",
     "-",
     "https://www.bd.emb-japan.go.jp/itpr_en/11_000001_00654.html"),
]

REGISTER_COLUMNS = ["country", "gap", "source", "decision", "reason / caveat",
                    "licence", "source_url"]


def _area_names() -> dict[str, str]:
    root = ET.parse(CL_AREA).getroot()
    return {c.get("id"): c.findtext("./{*}Name") for c in root.findall(".//{*}Code")}


def _describe_missing(missing: list[int]) -> str:
    if not missing:
        return "complete"
    if len(missing) == len(YEARS):
        return "ABSENT"
    contiguous = missing == list(range(missing[0], missing[-1] + 1))
    span = f"{missing[0]}-{missing[-1]}" if contiguous else ",".join(map(str, missing))
    return f"missing {len(missing)}: {span}"


def build_gap_table() -> pd.DataFrame:
    names = _area_names()
    un = pd.read_csv(CLEANED, dtype={"REF_AREA": str})
    un = un[un["TIME_PERIOD"].between(1990, 2022)].copy()
    fec = un[un["TRANSACTION"] == "B25_FEC"].pivot_table(
        index="REF_AREA", columns="TIME_PERIOD", values="OBS_VALUE"
    )
    fec22 = fec[2022] / TJ_PER_TWH

    rows = []
    for code, g in un.groupby("REF_AREA"):
        row = {
            "code": code,
            "area": names.get(code) or names.get(code.zfill(3)),
            "FEC_2022_TWh": round(float(fec22.get(code, float("nan"))), 1),
        }
        for sector, txs in SECTORS.items():
            present = set(g.loc[g["TRANSACTION"].isin(txs), "TIME_PERIOD"])
            row[sector] = _describe_missing(sorted(set(YEARS) - present))
        rows.append(row)

    gap = pd.DataFrame(rows).sort_values("FEC_2022_TWh", ascending=False)
    gap["share_%"] = (100 * gap["FEC_2022_TWh"] / gap["FEC_2022_TWh"].sum()).round(2)
    gap["cum_%"] = gap["share_%"].cumsum().round(1)
    gap["any_gap"] = gap[list(SECTORS)].ne("complete").any(axis=1)
    return gap


def main() -> int:
    if not CLEANED.exists():
        print("missing cleaned CSV — run build_energy_dataset.py first")
        return 1
    if not CL_AREA.exists():
        print("missing UN_CL_AREA_codelist.xml — run download_undata.py first")
        return 1

    gap = build_gap_table()
    gap.to_csv(OUT_GAP, index=False)

    register = pd.DataFrame(REGISTER, columns=REGISTER_COLUMNS)
    register.to_csv(OUT_REGISTER, index=False)

    print(f"gap table: {len(gap)} areas, {int(gap['any_gap'].sum())} with a gap -> {OUT_GAP.name}")
    print(f"source register: {len(register)} countries -> {OUT_REGISTER.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
