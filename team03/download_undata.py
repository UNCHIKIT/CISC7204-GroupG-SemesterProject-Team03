"""Download raw UN SDMX Energy Balance data and the CL_AREA code list.

Step 1 of the Team 03 data pipeline.

Fetches, in a single request each:
  1. All electricity (B07_EL) series for 1990-2023 across every REF_AREA and the
     seven sector transactions plus the FEC total, into ``Datasets/un_all.xml``.
  2. The UN CL_AREA area code list into ``Datasets/UN_CL_AREA_codelist.xml``.

Downloads are cached: an existing output file (larger than 100 KB) is left
untouched, so the script is cheap to re-run.
"""

from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATASETS = REPO_ROOT / "Datasets"

UN_ALL_URL = (
    "https://data.un.org/WS/rest/data/UNSD,DF_UNData_EnergyBalance,1.0/"
    ".B07_EL.B25_FEC+B26_121+B40_122+B50_1231+B48_1232+B49_1235+B51_1234.HSO"
    "?startPeriod=1990&endPeriod=2023"
)
CL_AREA_URL = "https://data.un.org/WS/rest/codelist/UNSD/CL_AREA/1.0"

ACCEPT_HEADER = {"Accept": "application/vnd.sdmx.structurespecificdata+xml;version=2.1"}

UN_ALL_PATH = DATASETS / "un_all.xml"
CL_AREA_PATH = DATASETS / "UN_CL_AREA_codelist.xml"


def _fetch(url: str, dest: Path, headers: dict[str, str] | None) -> int:
    """Download ``url`` into ``dest`` (binary). Returns the byte size."""
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = resp.read()
    dest.write_bytes(data)
    return len(data)


def _cached(dest: Path, min_bytes: int = 100_000) -> bool:
    return dest.exists() and dest.stat().st_size > min_bytes


def main() -> int:
    DATASETS.mkdir(parents=True, exist_ok=True)

    targets = [
        (UN_ALL_URL, UN_ALL_PATH, ACCEPT_HEADER),
        (CL_AREA_URL, CL_AREA_PATH, None),
    ]

    for url, dest, headers in targets:
        if _cached(dest):
            print(f"[skip] {dest.name} already cached ({dest.stat().st_size} bytes)")
            continue
        try:
            size = _fetch(url, dest, headers)
            print(f"[ok] {dest.name}: HTTP 200, {size} bytes")
        except Exception as exc:  # noqa: BLE001 - report a clear, actionable message
            print(f"[fail] {dest.name}: {exc}")
            # Fallback: if the cleaned CSV already exists we can proceed downstream;
            # otherwise the pipeline cannot run and we must ask for the CSV.
            fallback = DATASETS / "electricity_consumption_1990_2023.csv"
            if fallback.exists():
                print(f"[fallback] {fallback.name} already exists; continuing.")
                return 0
            print(
                "UN SDMX unreachable — request "
                "Datasets/electricity_consumption_1990_2023.csv from Kelden"
            )
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
