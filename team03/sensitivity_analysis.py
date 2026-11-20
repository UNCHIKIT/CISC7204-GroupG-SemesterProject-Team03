"""Sensitivity and robustness analysis for the Team 03 data decisions.

Companion to ``build_analysis_tables.py`` (step 4) and ``validate_dataset.py``
(step 5). Quantifies how much each of the four documented data decisions moves
the headline numbers (sensitivity), and re-checks the sector-level invariants
(robustness). Writes ``Datasets/sensitivity_analysis.csv`` and prints a summary.

Run from the repo root:  ``python team03/sensitivity_analysis.py``
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
DATASETS = REPO_ROOT / "Datasets"

COUNTRY_YEAR = DATASETS / "analysis_country_year.csv"
CLEANED = DATASETS / "electricity_consumption_1990_2023.csv"
OUT = DATASETS / "sensitivity_analysis.csv"

SECTORS = ["Industry", "Transport", "Residential", "Services_Other"]
SERVICES_CODES = ["B48_1232", "B49_1235", "B51_1234"]

# Pakistan 1990-92 published B25_FEC (before industry was added back).
PK_PUBLISHED_FEC = {1990: 18.45, 1991: 20.30, 1992: 21.59}


def load() -> pd.DataFrame:
    return pd.read_csv(COUNTRY_YEAR, dtype={"code": str})


def world_fec(df: pd.DataFrame, year: int) -> float:
    return float(df[df["year"] == year]["FEC"].sum())


def sector_shares(df: pd.DataFrame, year: int) -> dict[str, float]:
    d = df[df["year"] == year]
    tot = d[SECTORS].sum().sum()
    return {s: 100.0 * float(d[s].sum()) / tot for s in SECTORS}


def top30_share(df: pd.DataFrame, year: int) -> float:
    d = df[df["year"] == year]
    return float(d.nlargest(30, "FEC")["FEC"].sum() / d["FEC"].sum())


def main() -> int:
    df = load()

    # --- Sensitivity: each decision on/off -----------------------------------
    fixed = set(df[df["year"] == 1990]["code"])
    base = {
        "scenario": "all decisions (base)",
        "world_fec_1990": round(world_fec(df, 1990), 1),
        "world_fec_2022": round(world_fec(df, 2022), 1),
        "fixed_sample_countries": len(fixed),
        "top30_share_2022_pct": round(100 * top30_share(df, 2022), 1),
        "industry_share_1990_pct": round(sector_shares(df, 1990)["Industry"], 2),
    }
    rows = [base]

    # CF1: drop Germany 1990 (linked estimate)
    no_ger = df[~((df["code"] == "276") & (df["year"] == 1990))].copy()
    fixed_ng = set(no_ger[no_ger["year"] == 1990]["code"])
    rows.append({
        "scenario": "no Germany 1990",
        "world_fec_1990": round(world_fec(no_ger, 1990), 1),
        "world_fec_2022": round(world_fec(no_ger, 2022), 1),
        "fixed_sample_countries": len(fixed_ng),
        "top30_share_2022_pct": round(100 * top30_share(no_ger, 2022), 1),
        "industry_share_1990_pct": round(sector_shares(no_ger, 1990)["Industry"], 2),
    })

    # CF2: Pakistan 1990-92 industry not filled (revert to published FEC)
    no_pk = df.copy()
    for yr, pub in PK_PUBLISHED_FEC.items():
        m = (no_pk["code"] == "586") & (no_pk["year"] == yr)
        no_pk.loc[m, "FEC"] = pub
        no_pk.loc[m, "Industry"] = np.nan
    rows.append({
        "scenario": "no Pakistan 1990-92 industry fill",
        "world_fec_1990": round(world_fec(no_pk, 1990), 1),
        "world_fec_2022": round(world_fec(no_pk, 2022), 1),
        "fixed_sample_countries": len(fixed),
        "top30_share_2022_pct": round(100 * top30_share(no_pk, 2022), 1),
        "industry_share_1990_pct": round(sector_shares(no_pk, 1990)["Industry"], 2),
    })

    # CF3: Pakistan transport 2017-22 not zeroed (NaN)
    no_pkt = df.copy()
    m = (no_pkt["code"] == "586") & (no_pkt["year"].between(2017, 2022))
    no_pkt.loc[m, "Transport"] = np.nan
    rows.append({
        "scenario": "no Pakistan transport 2017-22 (NaN)",
        "world_fec_1990": round(world_fec(no_pkt, 1990), 1),
        "world_fec_2022": round(world_fec(no_pkt, 2022), 1),
        "fixed_sample_countries": len(fixed),
        "top30_share_2022_pct": round(100 * top30_share(no_pkt, 2022), 1),
        "industry_share_1990_pct": round(sector_shares(no_pkt, 1990)["Industry"], 2),
    })

    # CF4: Indonesia transport fills removed (NaN)
    no_idn = df.copy()
    m = (no_idn["code"] == "360") & (no_idn["year"].isin([2000, 2001, 2002, 2003,
                                                          2004, 2005, 2006, 2007, 2016]))
    no_idn.loc[m, "Transport"] = np.nan
    rows.append({
        "scenario": "no Indonesia transport fills",
        "world_fec_1990": round(world_fec(no_idn, 1990), 1),
        "world_fec_2022": round(world_fec(no_idn, 2022), 1),
        "fixed_sample_countries": len(fixed),
        "top30_share_2022_pct": round(100 * top30_share(no_idn, 2022), 1),
        "industry_share_1990_pct": round(sector_shares(no_idn, 1990)["Industry"], 2),
    })

    sens = pd.DataFrame(rows)
    sens.to_csv(OUT, index=False)
    print("== Sensitivity: headline numbers under each decision on/off ==")
    print(sens.to_string(index=False))

    # --- Robustness: sector-level invariants ---------------------------------
    print("\n== Robustness: sector-level checks ==")

    # (a) sector-sum == FEC
    ssum = df[SECTORS].sum(axis=1, min_count=1)
    ratio = ssum / df["FEC"]
    print(f"(a) sector-sum == FEC within 1%: {int(((ratio >= 0.99) & (ratio <= 1.01)).sum())}/{int(ratio.notna().sum())}")

    # (b) B47_123 never appears in the raw data
    raw = pd.read_csv(CLEANED, dtype={"REF_AREA": str})
    raw = raw[raw["TIME_PERIOD"].between(1990, 2022)]
    print(f"(b) B47_123 parent aggregate present in raw CSV: {bool((raw['TRANSACTION'] == 'B47_123').any())}")

    # (c) Services_Other == sum of the three service components
    piv = raw.pivot_table(index=["REF_AREA", "TIME_PERIOD"], columns="TRANSACTION",
                          values="OBS_VALUE", aggfunc="sum")
    svc_cols = [c for c in SERVICES_CODES if c in piv.columns]
    svc_sum = piv[svc_cols].sum(axis=1, min_count=1) / 3600.0
    svc_an = df.set_index(["code", "year"])["Services_Other"]
    svc_idx = svc_sum.index.to_frame(index=False)
    svc_idx.columns = ["code", "year"]
    svc_idx["code"] = svc_idx["code"].astype(str).str.zfill(3)
    svc_sum_df = svc_sum.reset_index(drop=True)
    svc_sum_df.index = pd.MultiIndex.from_frame(svc_idx[["code", "year"]])
    cmp = pd.DataFrame({"recomputed": svc_sum_df, "stored": svc_an})
    cmp = cmp.dropna()
    max_dev = float((cmp["recomputed"] - cmp["stored"]).abs().max())
    print(f"(c) Services_Other recomputed vs stored: max |diff| = {max_dev:.4f} TWh "
          f"({int(len(cmp))} rows)")

    # (d) industry-missing areas: how much FEC they cover and their reconcile gap
    for yr in (1990, 2022):
        d = df[df["year"] == yr]
        miss = d[d["Industry"].isna()]
        tot_fec = miss["FEC"].sum()
        three = miss[["Transport", "Residential", "Services_Other"]].sum(axis=1, min_count=1)
        gap = (three - miss["FEC"]).abs().sum()
        print(f"(d) {yr}: {len(miss)} areas missing industry, FEC={tot_fec:.1f} TWh "
              f"({100 * tot_fec / d['FEC'].sum():.1f}% of world), "
              f"3-sector-sum vs FEC gap={gap:.2f} TWh")

    return 0


if __name__ == "__main__":
    sys.exit(main())
