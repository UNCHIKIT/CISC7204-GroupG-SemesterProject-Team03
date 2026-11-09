"""Build the country x year and region x year analysis tables.

Step 4 of the Team 03 data pipeline.

Reads the cleaned ``electricity_consumption_1990_2023.csv`` (TJ), restricts to
1990-2022, converts to TWh (``OBS_VALUE / 3600``), pivots each
``(REF_AREA, year)`` into the four sectors plus the ``B25_FEC`` total, applies
the three documented data decisions (each with a 0/1 flag), then joins the
country/region mapping and writes:

* ``Datasets/analysis_country_year.csv``
* ``Datasets/analysis_region_year.csv`` (region x year, plus a ``World`` row)

``Services_Other`` is the row-wise sum of the three service components
(``B48_1232`` + ``B49_1235`` + ``B51_1234``, ``min_count=1``). The parent
aggregate ``B47_123`` is NEVER added.
"""

from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
DATASETS = REPO_ROOT / "Datasets"

CLEANED_CSV = DATASETS / "electricity_consumption_1990_2023.csv"
COUNTRY_REGION = DATASETS / "country_region.csv"
OUT_COUNTRY_YEAR = DATASETS / "analysis_country_year.csv"
OUT_REGION_YEAR = DATASETS / "analysis_region_year.csv"

AGEB_URL = "https://ag-energiebilanzen.de/wp-content/uploads/EBD24e_Auswertungstabellen_english.pdf"
AGEB_PDF = DATASETS / "EBD24e_Auswertungstabellen_english.pdf"

INDUSTRY = "B26_121"
TRANSPORT = "B40_122"
RESIDENTIAL = "B50_1231"
SERVICES = ["B48_1232", "B49_1235", "B51_1234"]
FEC = "B25_FEC"

FLAGS = ["flag_germany_linked", "flag_fec_recomputed", "flag_reported_nil"]

COLUMNS = [
    "code", "area", "iso2", "iso3", "admin", "region", "subregion", "year",
    "Industry", "Transport", "Residential", "Services_Other", "FEC",
    *FLAGS,
]

TJ_PER_TWH = 3600.0
PJ_PER_TWH = 3.6


def download_ageb_pdf() -> None:
    if AGEB_PDF.exists() and AGEB_PDF.stat().st_size > 500_000:
        print(f"[skip] {AGEB_PDF.name} cached ({AGEB_PDF.stat().st_size} bytes)")
        return
    req = urllib.request.Request(AGEB_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = resp.read()
    AGEB_PDF.write_bytes(data)
    print(f"[ok] {AGEB_PDF.name}: {len(data)} bytes")


def extract_electricity_pj(pdf_path: Path, page_index: int, year: int = 1990) -> float:
    """Return the ``Electricity`` row value (in PJ) for ``year`` on a 0-indexed page."""
    import pymupdf  # imported lazily; only needed for the Germany 1990 decision

    doc = pymupdf.open(str(pdf_path))
    page = doc[page_index]
    words = page.get_text("words")  # (x0, y0, x1, y1, word, block, line, word_no)

    year_x = None
    for w in words:
        if w[4] == str(year) and w[1] < 145:
            year_x = w[0]
            break
    elec_y = None
    for w in words:
        if w[4] == "Electricity":
            elec_y = w[1]
            break
    if year_x is None or elec_y is None:
        raise RuntimeError(f"could not locate {year}/Electricity on page {page_index + 1}")

    for w in words:
        if w[4] in ("Electricity", str(year)):
            continue
        if abs(w[1] - elec_y) < 4 and abs(w[0] - year_x) < 10:
            val = w[4].replace(",", "")
            try:
                return float(val)
            except ValueError:
                continue
    raise RuntimeError(f"could not read Electricity {year} value on page {page_index + 1}")


def germany_1990(pdf_path: Path) -> dict[str, float]:
    """Linked estimate for Germany (code 276) 1990, which has no UNdata row."""
    transport_pj = extract_electricity_pj(pdf_path, 24, 1990)   # 6.6 transport (p25)
    residential_pj = extract_electricity_pj(pdf_path, 21, 1990)  # 6.3 households (p22)

    industry = 229.9          # AGEB_1990 (207.8) x (UNdata_1991 214.5 / AGEB_1991 194.0)
    services = 102.6          # AGEB_1990 (116.4) x (UNdata_1991 103.3 / AGEB_1991 117.3)
    transport = transport_pj / PJ_PER_TWH
    residential = residential_pj / PJ_PER_TWH
    fec = industry + transport + residential + services
    return {
        "Industry": industry,
        "Transport": transport,
        "Residential": residential,
        "Services_Other": services,
        "FEC": fec,
    }


def load_country_year() -> pd.DataFrame:
    """Read the analysis_country_year.csv table (shared loader for steps 6-8)."""
    return pd.read_csv(OUT_COUNTRY_YEAR, dtype={"code": str})


def main() -> int:
    if not CLEANED_CSV.exists():
        print("missing cleaned CSV — run build_energy_dataset.py first")
        return 1
    if not COUNTRY_REGION.exists():
        print("missing country_region.csv — run build_mappings.py first")
        return 1

    df = pd.read_csv(CLEANED_CSV, dtype={"REF_AREA": str})
    df = df[df["TIME_PERIOD"].between(1990, 2022)]
    df["TWh"] = df["OBS_VALUE"] / TJ_PER_TWH

    piv = df.pivot_table(
        index=["REF_AREA", "TIME_PERIOD"], columns="TRANSACTION", values="TWh", aggfunc="sum"
    )

    out = pd.DataFrame(index=piv.index)
    out["Industry"] = piv.get(INDUSTRY)
    out["Transport"] = piv.get(TRANSPORT)
    out["Residential"] = piv.get(RESIDENTIAL)
    svc_cols = [c for c in SERVICES if c in piv.columns]
    out["Services_Other"] = piv[svc_cols].sum(axis=1, min_count=1)
    out["FEC"] = piv.get(FEC)
    for f in FLAGS:
        out[f] = 0

    # --- Decision 1: Germany 1990 (linked estimate; no UNdata row exists) ---
    download_ageb_pdf()
    ger = germany_1990(AGEB_PDF)
    ger_row = pd.DataFrame(
        [[ger["Industry"], ger["Transport"], ger["Residential"], ger["Services_Other"], ger["FEC"], 1, 0, 0]],
        index=pd.MultiIndex.from_tuples([("276", 1990)], names=out.index.names),
        columns=out.columns,
    )
    out = pd.concat([out, ger_row])

    # --- Decision 2: Pakistan 1990-1992 (industry missing; recompute FEC) ---
    pk_industry = {1990: 10.3, 1991: 11.2, 1992: 12.3}
    for yr, ind in pk_industry.items():
        out.loc[("586", yr), "Industry"] = ind
        out.loc[("586", yr), "FEC"] = out.loc[("586", yr), "FEC"] + ind
        out.loc[("586", yr), "flag_fec_recomputed"] = 1

    # --- Decision 3: Pakistan 2017-2022 transport reported nil ("-") -> 0 ---
    for yr in range(2017, 2023):
        out.loc[("586", yr), "Transport"] = 0.0
        out.loc[("586", yr), "flag_reported_nil"] = 1

    out = out.sort_index().reset_index()
    out = out.rename(columns={"REF_AREA": "code", "TIME_PERIOD": "year"})
    out["code"] = out["code"].astype(str).str.zfill(3)

    # Join country/region mapping.
    cr = pd.read_csv(COUNTRY_REGION, dtype={"code": str})[
        ["code", "area", "iso2", "iso3", "admin", "region", "subregion"]
    ]
    out = out.merge(cr, on="code", how="left")

    out = out[COLUMNS]
    out.to_csv(OUT_COUNTRY_YEAR, index=False)

    # --- region x year (plus World) ---
    value_cols = ["Industry", "Transport", "Residential", "Services_Other", "FEC"]
    region = out.groupby(["region", "year"], as_index=False)[value_cols].sum()
    world = out.groupby("year", as_index=False)[value_cols].sum()
    world["region"] = "World"
    region = pd.concat([region, world], ignore_index=True).sort_values(["region", "year"])
    region.to_csv(OUT_REGION_YEAR, index=False)

    n_countries = out["code"].nunique()
    n_years = out["year"].nunique()
    china = out[(out["code"] == "156") & (out["year"] == 2022)].iloc[0]
    ger90 = out[(out["code"] == "276") & (out["year"] == 1990)].iloc[0]
    pk = {y: out[(out["code"] == "586") & (out["year"] == y)].iloc[0] for y in (1990, 1991, 1992, 1993)}

    print(f"countries={n_countries}  years={out['year'].min()}-{out['year'].max()}  rows={len(out)}")
    print(f"China 2022 FEC={china['FEC']:.1f} TWh  Industry={china['Industry']:.1f}")
    print(f"Germany 1990: Industry={ger90['Industry']} Services={ger90['Services_Other']} "
          f"FEC={ger90['FEC']:.2f} flag={ger90['flag_germany_linked']}")
    print(f"Pakistan FEC 1990-93: " + ", ".join(f"{y}={pk[y]['FEC']:.2f}" for y in (1990, 1991, 1992, 1993)))
    print(f"wrote {OUT_COUNTRY_YEAR.name} ({OUT_COUNTRY_YEAR.stat().st_size} bytes), "
          f"{OUT_REGION_YEAR.name} ({OUT_REGION_YEAR.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
