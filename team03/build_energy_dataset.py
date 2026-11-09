"""Parse the combined UN SDMX XML into Kelden's cleaned CSV contract.

Step 2 of the Team 03 data pipeline.

Reads ``Datasets/un_all.xml`` (all REF_AREA x COMMODITY x TRANSACTION series),
keeps only electricity (``B07_EL``) rows whose ``TRANSACTION`` is one of the
seven code paths used downstream (the six sector components plus the ``B25_FEC``
total), and writes ``Datasets/electricity_consumption_1990_2023.csv`` with the
exact column contract Kelden's notebook expects:

    REF_AREA, TIME_PERIOD, TRANSACTION, OBS_VALUE, ESTIMATE, UNIT

No unit conversion is performed here: ``OBS_VALUE`` stays in TJ (the ``UNIT``
label reads ``HSO`` but the numeric value is in fact TJ).
"""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
DATASETS = REPO_ROOT / "Datasets"

UN_ALL = DATASETS / "un_all.xml"
OUT_CSV = DATASETS / "electricity_consumption_1990_2023.csv"

COMMODITY = "B07_EL"
TRANSACTIONS = {
    "B25_FEC",    # total final consumption
    "B26_121",    # industry
    "B40_122",    # transport
    "B50_1231",   # residential
    "B48_1232",   # services/other (component 1)
    "B49_1235",   # services/other (component 2)
    "B51_1234",   # services/other (component 3)
}
# NOTE: B47_123 (the parent aggregate of the three services components) is
# deliberately NOT requested and MUST NOT be added to any sum.


def parse_un_xml(path: Path) -> pd.DataFrame:
    """Stream-iterate the combined XML and return a tidy DataFrame."""
    rows: list[dict[str, object]] = []
    for _event, elem in ET.iterparse(path, events=("end",)):
        if elem.tag != "Series":
            continue
        attrs = elem.attrib
        if attrs.get("COMMODITY") != COMMODITY:
            elem.clear()
            continue
        transaction = attrs.get("TRANSACTION")
        if transaction not in TRANSACTIONS:
            elem.clear()
            continue
        ref_area = attrs.get("REF_AREA", "").zfill(3)
        unit = attrs.get("UNIT", "")
        for obs in elem.iter("Obs"):
            value = obs.get("OBS_VALUE")
            if value is None or value == "":
                continue
            rows.append({
                "REF_AREA": ref_area,
                "TIME_PERIOD": int(obs.get("TIME_PERIOD")),
                "TRANSACTION": transaction,
                "OBS_VALUE": value,
                "ESTIMATE": obs.get("ESTIMATE", ""),
                "UNIT": unit,
            })
        elem.clear()
    return pd.DataFrame(rows)


def main() -> int:
    if not UN_ALL.exists():
        print("missing", UN_ALL, "— run download_undata.py first")
        return 1

    df = parse_un_xml(UN_ALL)

    if not df.empty:
        df["OBS_VALUE"] = pd.to_numeric(df["OBS_VALUE"], errors="coerce")
        df = df.dropna(subset=["OBS_VALUE"])
        df["TIME_PERIOD"] = df["TIME_PERIOD"].astype(int)

    df = df[["REF_AREA", "TIME_PERIOD", "TRANSACTION", "OBS_VALUE", "ESTIMATE", "UNIT"]]
    df.to_csv(OUT_CSV, index=False)

    n_areas = df["REF_AREA"].nunique()
    n_obs = len(df)
    years = (df["TIME_PERIOD"].min(), df["TIME_PERIOD"].max())

    print(f"areas={n_areas}  obs={n_obs}  years={years[0]}-{years[1]}")
    print(f"wrote {OUT_CSV} ({OUT_CSV.stat().st_size} bytes)")

    # Sanity checks (soft): area count and year window are authoritative.
    assert 213 <= n_areas <= 223, f"unexpected area count {n_areas}"
    assert years == (1990, 2023), f"unexpected year window {years}"
    return 0


if __name__ == "__main__":
    sys.exit(main())
