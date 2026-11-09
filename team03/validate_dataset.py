"""Four-layer validation of the rebuilt dataset.

Step 5 of the Team 03 data pipeline. Every check is deterministic and re-runnable.

* Layer 1 -- internal consistency (no external data): sector-sum == FEC, the
  year-on-year >50% jump list, per-capita kWh bounds (World Bank SP.POP.TOTL),
  and region sums == World.
* Layer 2 -- cross-dataset: 2022 UNdata FEC / OWID electricity demand ratio
  (expected 0.85-0.95; extremes are flagged) -> ``validation_crosscheck.csv``.
* Layer 3 -- Kelden's headline numbers (observation count, area count, top-30
  share, sector-sum completeness).
* Layer 4 -- duplicate-count check (250/380/578/756 absent; 076/840 present).

Writes ``Datasets/validation_jumps.csv`` and ``Datasets/validation_crosscheck.csv``.
"""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
DATASETS = REPO_ROOT / "Datasets"

COUNTRY_YEAR = DATASETS / "analysis_country_year.csv"
REGION_YEAR = DATASETS / "analysis_region_year.csv"
CLEANED = DATASETS / "electricity_consumption_1990_2023.csv"

OUT_JUMPS = DATASETS / "validation_jumps.csv"
OUT_CROSSCHECK = DATASETS / "validation_crosscheck.csv"

OWID_URL = "https://ourworldindata.org/grapher/electricity-demand.csv"
OWID_CSV = DATASETS / "owid_electricity_demand.csv"

WB_URL = (
    "https://api.worldbank.org/v2/country/all/indicator/SP.POP.TOTL"
    "?format=json&per_page=30000&date=1990:2022"
)
WB_JSON = DATASETS / "worldbank_population.json"

SECTORS = ["Industry", "Transport", "Residential", "Services_Other"]


def _get(url: str, dest: Path, min_bytes: int = 1000) -> None:
    if dest.exists() and dest.stat().st_size > min_bytes:
        return
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = resp.read()
    dest.write_bytes(data)
    print(f"[ok] {dest.name}: {len(data)} bytes")


def layer1(df: pd.DataFrame) -> None:
    print("== Layer 1: internal consistency ==")
    # (a) sector sum vs FEC
    ssum = df[SECTORS].sum(axis=1, min_count=1)
    ratio = ssum / df["FEC"]
    ok = ((ratio >= 0.99) & (ratio <= 1.01)).sum()
    print(f"(a) sector-sum == FEC within 1%: {ok}/{ratio.notna().sum()}")

    # (b) YoY jumps > 50%
    jumps = []
    for code, g in df.sort_values("year").groupby("code"):
        g = g.sort_values("year")
        fec = g["FEC"].values
        years = g["year"].values
        for i in range(1, len(g)):
            prev, cur = fec[i - 1], fec[i]
            if prev and abs(cur - prev) / abs(prev) > 0.5:
                jumps.append({
                    "code": code,
                    "area": g["area"].iloc[0],
                    "year": int(years[i]),
                    "prev_year": int(years[i - 1]),
                    "prev_fec_twh": round(float(prev), 2),
                    "fec_twh": round(float(cur), 2),
                    "change_pct": round(100.0 * (cur - prev) / prev, 1),
                })
    pd.DataFrame(jumps).to_csv(OUT_JUMPS, index=False)
    print(f"(b) year-over-year jumps >50%: {len(jumps)} -> {OUT_JUMPS.name}")

    # (c) per-capita bounds
    _get(WB_URL, WB_JSON, min_bytes=100)
    wb = json.loads(WB_JSON.read_text(encoding="utf-8"))
    pop: dict[tuple[str, int], float] = {}
    for row in wb[1]:
        iso3 = row.get("countryiso3code")
        val = row.get("value")
        yr = row.get("date")
        if iso3 and val is not None and yr:
            pop[(iso3, int(yr))] = float(val)

    cr = pd.read_csv(DATASETS / "country_region.csv", dtype={"code": str})[
        ["code", "iso3"]
    ].set_index("code")["iso3"].to_dict()

    outliers = []
    for _, r in df.iterrows():
        iso3 = cr.get(r["code"])
        if not iso3:
            continue
        p = pop.get((iso3, int(r["year"])))
        if not p:
            continue
        per_capita = r["FEC"] * 1e9 / p
        if not (100 <= per_capita <= 25000):
            outliers.append((r["code"], r["area"], int(r["year"]), round(per_capita)))
    print(f"(c) per-capita outside 100-25,000 kWh: {len(outliers)}")
    for o in outliers[:15]:
        print(f"    {o[0]} {o[1]} {o[2]} {o[3]} kWh")

    # (d) region sums == World
    reg = pd.read_csv(REGION_YEAR)
    world = reg[reg["region"] == "World"].set_index("year")["FEC"]
    region_sum = reg[reg["region"] != "World"].groupby("year")["FEC"].sum()
    max_diff = (region_sum - world).abs().max()
    print(f"(d) region-sum vs World max |diff|: {max_diff:.4f} TWh")


def layer2(df: pd.DataFrame) -> None:
    print("== Layer 2: OWID cross-dataset (2022) ==")
    _get(OWID_URL, OWID_CSV, min_bytes=10_000)
    ow = pd.read_csv(OWID_CSV)
    ow22 = ow[ow["Year"] == 2022][["Code", "Electricity demand"]].dropna(subset=["Code"])
    ow22 = ow22.set_index("Code")["Electricity demand"].to_dict()

    d22 = df[df["year"] == 2022]  # already carries 'area' and 'iso3' columns

    rows = []
    for _, r in d22.iterrows():
        iso3 = r["iso3"]
        if not iso3 or iso3 not in ow22:
            continue
        demand = ow22[iso3]
        if not demand or demand <= 0:
            continue
        ratio = r["FEC"] / demand
        if 0.85 <= ratio <= 0.95:
            status, reason = "ok", ""
        else:
            status = "flag"
            if r["code"] == "356":  # India
                reason = (
                    "Ratio below the 0.85-0.95 band: high transmission and distribution "
                    "losses and/or incomplete reporting of agriculture/other electricity "
                    "in the UN final-consumption classification."
                )
            elif ratio < 0.75:
                reason = "Ratio < 0.75: UN final consumption is far below generation-side demand."
            elif ratio > 1.00:
                reason = "Ratio > 1.00: UN final consumption exceeds generation-side demand."
            else:
                reason = "Ratio outside the expected 0.85-0.95 band."
        rows.append({
            "country": r["area"],
            "year": 2022,
            "un_fec_twh": round(float(r["FEC"]), 2),
            "owid_demand_twh": round(float(demand), 2),
            "ratio": round(float(ratio), 3),
            "status": status,
            "reason": reason,
        })

    cc = pd.DataFrame(rows)[
        ["country", "year", "un_fec_twh", "owid_demand_twh", "ratio", "status", "reason"]
    ]
    cc.to_csv(OUT_CROSSCHECK, index=False)
    n_flag = (cc["status"] == "flag").sum()
    print(f"crosscheck rows={len(cc)}  flagged={n_flag} -> {OUT_CROSSCHECK.name}")
    for _, r in cc[cc["status"] == "flag"].iterrows():
        print(f"    FLAG {r['country']} ratio={r['ratio']}")
    for name in ["China", "Germany", "Japan", "Republic of Korea", "Indonesia", "India"]:
        row = cc[cc["country"] == name]
        if len(row):
            print(f"    {name}: ratio={row.iloc[0]['ratio']} status={row.iloc[0]['status']}")


def layer3(df: pd.DataFrame) -> None:
    print("== Layer 3: Kelden headline numbers ==")
    cleaned = pd.read_csv(CLEANED, dtype={"REF_AREA": str})
    n_obs = len(cleaned)
    n_areas = cleaned["REF_AREA"].nunique()
    top30 = df[df["year"] == 2022].nlargest(30, "FEC")["FEC"].sum()
    world22 = df[df["year"] == 2022]["FEC"].sum()
    share = top30 / world22
    ssum = df[SECTORS].sum(axis=1, min_count=1)
    complete = ((ssum / df["FEC"]).between(0.99, 1.01)).mean()
    print(f"observations={n_obs} (plan expected ~51,000; actual {n_obs})")
    print(f"areas={n_areas}")
    print(f"top-30 share of 2022 world FEC={share:.1%}")
    print(f"sector-sum completeness (within 1%)={complete:.1%}")


def layer4(df: pd.DataFrame) -> None:
    print("== Layer 4: duplicate-count check ==")
    codes = set(df["code"])
    for c in ("250", "380", "578", "756"):
        assert c not in codes, f"duplicate code {c} present!"
    for c in ("840", "076"):
        assert c in codes, f"expected code {c} missing!"
    print("250/380/578/756 absent; 840 (US) and 076 (Brazil) present -- no double counting.")


def main() -> int:
    df = pd.read_csv(COUNTRY_YEAR, dtype={"code": str})
    layer1(df)
    layer2(df)
    layer3(df)
    layer4(df)
    print("validation complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
