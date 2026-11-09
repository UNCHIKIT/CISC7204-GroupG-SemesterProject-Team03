"""Build the country <-> region <-> map-polygon mapping tables.

Step 3 of the Team 03 data pipeline.

Produces two files in ``Datasets/``:

* ``natural_earth_index.csv`` — every Natural Earth ``ne_50m`` feature with its
  ``UN_A3`` / ``ISO_A3`` / ``ISO_A2`` / ``ADMIN`` / ``NAME`` identifiers.
* ``country_region.csv`` — one row per reference area present in the energy
  data, with its UN name, ISO alpha-2 code, subregion, continent (``region``)
  and the Natural Earth polygon identifiers it links to (``matched`` = 1 when
  a polygon was found).

The ``region`` (continent) is derived from the UN M49 subregion via a static
lookup, because subregions in ``CL_AREA`` carry no parent of their own.
Combined "super-area" codes (e.g. ``251`` France-Monaco) are resolved to their
main country so the choropleth can colour them.
"""

from __future__ import annotations

import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
DATASETS = REPO_ROOT / "Datasets"

CL_AREA = DATASETS / "UN_CL_AREA_codelist.xml"
UN_ALL = DATASETS / "un_all.xml"
GEOJSON = DATASETS / "ne_50m_admin_0_countries.geojson"

OUT_NE_INDEX = DATASETS / "natural_earth_index.csv"
OUT_COUNTRY_REGION = DATASETS / "country_region.csv"

GEOJSON_URL = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/"
    "geojson/ne_50m_admin_0_countries.geojson"
)

S_NS = "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure"
C_NS = "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common"

ISO2_RE = re.compile(r"ISO 3166-2 code:\s*([A-Z]{2})")

# UN M49 subregion -> continent (static; subregions have no parent in CL_AREA).
SUBREGION_TO_REGION = {
    "155": "Europe", "151": "Europe", "154": "Europe", "039": "Europe",
    "034": "Asia",   "030": "Asia",   "035": "Asia",   "143": "Asia", "145": "Asia",
    "015": "Africa", "011": "Africa", "017": "Africa", "014": "Africa", "018": "Africa",
    "021": "Americas", "029": "Americas", "013": "Americas", "005": "Americas",
    "053": "Oceania", "054": "Oceania", "057": "Oceania", "061": "Oceania",
}
SUBREGIONS = set(SUBREGION_TO_REGION)

# Combined "super-area" data codes -> the main-country code whose ISO2 and
# Natural Earth polygon they represent.
COMBINED_TO_MAIN = {
    "251": "250",   # France-Monaco            -> France
    "382": "380",   # Italy-San Marino         -> Italy
    "579": "578",   # Norway-Svalbard          -> Norway
    "757": "756",   # Switzerland-Liechtenstein-> Switzerland
}

_MISSING = {None, "", "-99", "-099", "-999"}


def parse_cl_area(path: Path) -> dict[str, tuple[str, str, str | None]]:
    """Return {code: (name, description, parent_code)} for every CL_AREA code."""
    tree = ET.parse(path)
    codes: dict[str, tuple[str, str, str | None]] = {}
    for code in tree.getroot().iter(f"{{{S_NS}}}Code"):
        cid = code.get("id")
        name_el = code.find(f"{{{C_NS}}}Name")
        desc_el = code.find(f"{{{C_NS}}}Description")
        name = (name_el.text or "").strip() if name_el is not None else ""
        desc = (desc_el.text or "").strip() if desc_el is not None else ""
        parent = None
        parent_el = code.find(f"{{{S_NS}}}Parent")
        if parent_el is not None:
            ref = parent_el.find("Ref")
            if ref is not None:
                parent = ref.get("id")
        codes[cid] = (name, desc, parent)
    return codes


def iso2_of(codes: dict, code: str) -> str:
    """Alpha-2 code for a CL_AREA code, falling back to its main country."""
    for c in (code, COMBINED_TO_MAIN.get(code, "")):
        if not c:
            continue
        desc = codes.get(c, ("", "", None))[1]
        m = ISO2_RE.search(desc)
        if m:
            return m.group(1)
    return ""


def subregion_of(codes: dict, code: str) -> str:
    """Walk up the parent chain to the first M49 subregion code."""
    cur = codes.get(code, ("", "", None))[2]
    while cur:
        if cur in SUBREGIONS:
            return cur
        cur = codes.get(cur, ("", "", None))[2]
    return ""


def data_codes(path: Path) -> list[str]:
    raw = path.read_bytes()
    return sorted({c.decode() for c in re.findall(rb'REF_AREA="(\d+)"', raw)})


def download_geojson() -> None:
    if GEOJSON.exists() and GEOJSON.stat().st_size > 1_000_000:
        print(f"[skip] {GEOJSON.name} cached ({GEOJSON.stat().st_size} bytes)")
        return
    req = urllib.request.Request(GEOJSON_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = resp.read()
    GEOJSON.write_bytes(data)
    print(f"[ok] {GEOJSON.name}: {len(data)} bytes")


def build_ne_index() -> dict[str, dict[str, str]]:
    """Return {UN_A3 (3-digit): {ISO_A3, ISO_A2, ADMIN, NAME}} for matchable features."""
    gj = json.loads(GEOJSON.read_text(encoding="utf-8"))
    records: list[dict[str, str]] = []
    index: dict[str, dict[str, str]] = {}
    for f in gj["features"]:
        p = f["properties"]
        un = str(p.get("UN_A3", "")).zfill(3) if str(p.get("UN_A3", "")).isdigit() else str(p.get("UN_A3", ""))
        rec = {
            "UN_A3": str(p.get("UN_A3", "")),
            "ISO_A3": str(p.get("ISO_A3", "")),
            "ISO_A2": str(p.get("ISO_A2", "")),
            "ADMIN": str(p.get("ADMIN", "")),
            "NAME": str(p.get("NAME", "")),
        }
        records.append(rec)
        if p.get("UN_A3") not in _MISSING:
            key = str(p.get("UN_A3")).zfill(3)
            index[key] = rec
    pd.DataFrame(records)[["UN_A3", "ISO_A3", "ISO_A2", "ADMIN", "NAME"]].to_csv(
        OUT_NE_INDEX, index=False
    )
    return index


def clean(v: str) -> str:
    return "" if v in _MISSING else v


def main() -> int:
    if not CL_AREA.exists() or not UN_ALL.exists():
        print("missing CL_AREA or un_all.xml — run download_undata.py first")
        return 1

    codes = parse_cl_area(CL_AREA)
    areas = data_codes(UN_ALL)
    download_geojson()
    ne_index = build_ne_index()

    rows: list[dict[str, object]] = []
    for code in areas:
        name, _desc, _parent = codes.get(code, ("", "", None))
        iso2 = iso2_of(codes, code)
        sub = subregion_of(codes, code)
        region = SUBREGION_TO_REGION.get(sub, "Unassigned")
        sub_name = codes.get(sub, ("", "", None))[0] if sub else ""

        map_code = COMBINED_TO_MAIN.get(code, code)
        hit = ne_index.get(map_code)
        if hit is not None:
            matched, iso3, admin = 1, clean(hit["ISO_A3"]), hit["ADMIN"]
        else:
            matched, iso3, admin = 0, "", ""

        rows.append({
            "code": code,
            "area": name,
            "iso2": iso2,
            "subregion_code": sub,
            "subregion": sub_name,
            "region": region,
            "iso3": iso3,
            "admin": admin,
            "matched": matched,
        })

    df = pd.DataFrame(rows)[
        ["code", "area", "iso2", "subregion_code", "subregion", "region", "iso3", "admin", "matched"]
    ]
    df.to_csv(OUT_COUNTRY_REGION, index=False)

    n = len(df)
    n_matched = int(df["matched"].sum())
    n_unassigned = int((df["region"] == "Unassigned").sum())
    unmatched = df.loc[df["matched"] == 0, "code"].tolist()
    print(f"areas={n}  matched={n_matched}  unassigned={n_unassigned}")
    print(f"coverage={n_matched}/{n} = {n_matched / n:.1%}")
    print(f"unmatched codes: {unmatched}")

    fr = df[df["code"] == "251"].iloc[0]
    print(f"France: code={fr['code']} iso2={fr['iso2']} matched={fr['matched']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
