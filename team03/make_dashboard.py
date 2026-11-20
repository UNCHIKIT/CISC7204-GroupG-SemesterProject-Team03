"""Assemble the self-contained two-page web dashboard.

Step 7 of the Team 03 data pipeline.

Produces ``web/index.html`` (interactive outputs, single self-contained file that
embeds plotly.js exactly once) and ``web/method.html`` (a static, library-free
"how the data becomes the charts" page). Both share the same top navigation and
are written entirely in English with inline CSS and no external fonts or CDNs.
"""

from __future__ import annotations

import base64
import re
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

import make_figures as mf  # noqa: E402

WEB = REPO_ROOT / "web"
DATASETS = REPO_ROOT / "Datasets"
FIGURES = REPO_ROOT / "Figures"

SECTORS = ["Industry", "Transport", "Residential", "Services_Other"]

CSS = """
:root { --ink:#1a1a2e; --accent:#16213e; --muted:#5b6070; --line:#e2e4ea; --bg:#ffffff; }
* { box-sizing: border-box; }
body { margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
       color:var(--ink); background:var(--bg); line-height:1.55; }
nav { position:sticky; top:0; background:var(--accent); color:#fff; padding:12px 24px; display:flex; gap:24px; z-index:10; }
nav a { color:#fff; text-decoration:none; font-weight:600; }
nav a:hover { text-decoration:underline; }
header { padding:36px 24px 8px; border-bottom:1px solid var(--line); }
h1 { margin:0 0 4px; font-size:28px; }
.subtitle { color:var(--muted); margin:0 0 8px; }
.meta { color:var(--muted); font-size:14px; margin:0; }
section { padding:20px 24px; max-width:1200px; margin:0 auto; }
#key-figures { display:flex; flex-wrap:wrap; gap:16px; }
.kf { flex:1 1 150px; border:1px solid var(--line); border-radius:8px; padding:14px; text-align:center; }
.kf .num { font-size:24px; font-weight:700; }
.kf .lbl { color:var(--muted); font-size:13px; }
.chart { border:1px solid var(--line); border-radius:10px; padding:16px; margin:20px 0; }
.chart h3 { margin-top:0; }
.caption { color:var(--muted); font-size:14px; }
.buttons { margin-top:8px; display:flex; gap:10px; }
.buttons a { display:inline-block; padding:6px 12px; border:1px solid var(--accent); border-radius:6px;
             color:var(--accent); text-decoration:none; font-size:13px; font-weight:600; }
.buttons a:hover { background:var(--accent); color:#fff; }
h2 { border-bottom:1px solid var(--line); padding-bottom:6px; }
.step { margin:10px 0; padding:10px 14px; border-left:3px solid var(--accent); background:#f7f8fa; }
.step a { color:var(--accent); }
table { border-collapse:collapse; width:100%; font-size:14px; }
th,td { border:1px solid var(--line); padding:6px 10px; text-align:left; }
th { background:#f7f8fa; }
pre { background:#f4f4f7; padding:12px; border-radius:6px; overflow-x:auto; font-size:13px; }
code { font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; }
ul { padding-left:22px; }
"""

NAV = ('<nav>'
       '<a href="#outputs">Outputs</a>'
       '<a href="method.html">Method</a>'
       '<a href="#data-dictionary">Data dictionary</a>'
       '<a href="#files">Files</a>'
       '</nav>')


def _csv_to_uri(df: pd.DataFrame) -> str:
    b64 = base64.b64encode(df.to_csv(index=False).encode("utf-8")).decode("ascii")
    return f"data:text/csv;base64,{b64}"


def _clean_plotlyjs(html: str) -> str:
    """Remove the Chinese calendar month-name regexes from the embedded plotly.js.

    The full plotly.js bundle ships a d3-time-format Chinese locale whose month
    names are CJK characters. We never use Chinese date formatting, so the two
    regexes are replaced with no-ops to keep the self-contained page CJK-free.
    """
    return re.sub(r"(ker|Ler)=/[^/]*[\u4e00-\u9fff][^/]*/m", r"\1=/^$/m", html)


def _png_to_uri(name: str) -> str:
    b64 = base64.b64encode((FIGURES / name).read_bytes()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def _fig_csvs(df: pd.DataFrame, reg: pd.DataFrame) -> dict[int, pd.DataFrame]:
    fixed = set(df[df["year"] == 1990]["code"])
    world = df.groupby("year")["FEC"].sum().rename("all_reporting_twh").reset_index()
    fixed_s = df[df["code"].isin(fixed)].groupby("year")["FEC"].sum().rename("fixed_sample_twh").reset_index()

    top10 = df[df["year"] == 2022].nlargest(10, "FEC")[["code", "area", "FEC"]]

    regional = reg[reg["region"] != "World"][["region", "year", "FEC"]]

    sec_rows = []
    for yr in (1990, 2022):
        d = df[df["year"] == yr]
        totals = d[SECTORS].sum()
        for s in SECTORS:
            sec_rows.append({"year": yr, "sector": s, "share_pct": round(100 * totals[s] / totals.sum(), 2)})
    sector = pd.DataFrame(sec_rows)

    share = df[df["code"].isin(fixed) & df["year"].isin([1990, 2022])]
    share = share.assign(share=share["FEC"] / share.groupby("year")["FEC"].transform("sum") * 100)
    share = share.pivot_table(index=["code", "area"], columns="year", values="share").reset_index()
    share.columns = ["code", "area", "share_1990_pct", "share_2022_pct"]

    map90 = df[df["year"] == 1990][["code", "area", "FEC"]].rename(columns={"FEC": "fec_twh"})
    map22 = df[df["year"] == 2022][["code", "area", "FEC"]].rename(columns={"FEC": "fec_twh"})

    ow = pd.read_csv(DATASETS / "owid_electricity_prod_source.csv")
    world_mix = ow[ow["Entity"] == "World"]
    srcs = ["Other renewables", "Bioenergy", "Solar", "Wind", "Hydropower",
            "Nuclear", "Gas", "Oil", "Coal"]
    mix_rows = []
    for yr in (2000, 2022):
        w = world_mix[world_mix["Year"] == yr][srcs].sum()
        for s in srcs:
            mix_rows.append({"year": yr, "source": s, "share_pct": round(100 * w[s] / w.sum(), 2)})
    mix = pd.DataFrame(mix_rows)

    drivers = mf.drivers_decomposition_data(df)

    regions = ["Africa", "Asia", "Europe", "North America", "South America", "Oceania"]
    srcs = ["Other renewables", "Bioenergy", "Solar", "Wind", "Hydropower",
            "Nuclear", "Gas", "Oil", "Coal"]
    reg_mix_rows = []
    for region in regions:
        r = ow[ow["Entity"] == region]
        for s in srcs:
            reg_mix_rows.append({"region": region, "source": s,
                                 "share_pct": round(100 * float(r[r["Year"] == 2022][s].sum())
                                                    / float(r[r["Year"] == 2022][srcs].sum().sum()), 2)})
    reg_mix = pd.DataFrame(reg_mix_rows)

    # 12: region x year mix (slider)
    ry_rows = []
    for region in mf.MIX_REGIONS:
        r = ow[ow["Entity"] == region]
        for yr in range(2000, 2023):
            y = r[r["Year"] == yr]
            tot = float(y[mf.MIX_SOURCES].sum().sum())
            for s in mf.MIX_SOURCES:
                ry_rows.append({"region": region, "year": yr, "source": s,
                                "share_pct": round(100 * float(y[s].sum()) / tot, 2) if tot else 0.0})
    region_year_mix = pd.DataFrame(ry_rows)

    # 13: largest-country mix 2022
    c_rows = []
    for country in mf.MIX_COUNTRIES:
        c = ow[(ow["Entity"] == country) & (ow["Year"] == 2022)]
        tot = float(c[mf.MIX_SOURCES].sum().sum())
        for s in mf.MIX_SOURCES:
            c_rows.append({"country": country, "source": s,
                           "share_pct": round(100 * float(c[s].sum()) / tot, 2) if tot else 0.0})
    country_mix = pd.DataFrame(c_rows)

    # 14: carbon intensity
    ci = pd.read_csv(DATASETS / "carbon_intensity_electricity.csv")
    carbon = ci[ci["Entity"].isin(mf.MIX_COUNTRIES) & ci["Year"].between(2000, 2022)][
        ["Entity", "Year", "Carbon intensity"]
    ].rename(columns={"Entity": "country", "Carbon intensity": "gco2_kwh"})

    # 15: generation vs consumption (world 2022)
    w22 = ow[(ow["Entity"] == "World") & (ow["Year"] == 2022)]
    gen = float(w22[mf.MIX_SOURCES].sum().sum())
    cons = float(df[df["year"] == 2022]["FEC"].sum())
    gen_cons = pd.DataFrame({"quantity": ["Generation", "Final consumption"],
                             "twh": [round(gen, 1), round(cons, 1)]})

    # 16: consumption vs population vs GDP growth
    pop = mf._wb_series(mf.POP_JSON)
    gdp = mf._wb_series(mf.GDP_JSON)
    comp_rows = []
    for label, code, iso3 in mf.DRIVER_COUNTRIES:
        e = df[(df["code"] == code) & (df["year"].isin([2000, 2022]))].set_index("year")["FEC"]
        p00, p22 = pop.get((iso3, 2000)), pop.get((iso3, 2022))
        g00, g22 = gdp.get((iso3, 2000)), gdp.get((iso3, 2022))
        if None in (p00, p22, g00, g22) or 2000 not in e.index or 2022 not in e.index:
            continue
        comp_rows.append({"country": label,
                          "electricity_growth_pp": round(float(np.log(e[2022] / e[2000]) * 100), 1),
                          "population_growth_pp": round(float(np.log(p22 / p00) * 100), 1),
                          "gdp_growth_pp": round(float(np.log(g22 / g00) * 100), 1)})
    comparison = pd.DataFrame(comp_rows)

    # 17: per-capita scatter
    iso3_map = mf._country_iso3()
    pc_rows = []
    for _, r in df[df["year"] == 2022].iterrows():
        iso = iso3_map.get(r["code"])
        if not iso:
            continue
        p = pop.get((iso, 2022))
        g = gdp.get((iso, 2022))
        if not p or not g:
            continue
        pc_rows.append({"country": r["area"], "region": r["region"],
                        "electricity_per_capita_kwh": round(r["FEC"] * 1e9 / p, 1),
                        "gdp_per_capita_usd": round(g / p, 1)})
    percapita = pd.DataFrame(pc_rows)

    # 18: China Kaya waterfall
    waterfall = drivers[drivers["country"] == "China"][
        ["country", "population_pp", "income_per_person_pp", "e_gdp_pp", "total_growth_pp"]]

    return {
        1: world.merge(fixed_s, on="year"),
        2: top10,
        3: regional,
        4: sector,
        5: share,
        6: map90,
        7: map22,
        8: mix,
        9: df[["code", "area", "year", "FEC"]].rename(columns={"FEC": "fec_twh"}),
        10: drivers,
        11: reg_mix,
        12: region_year_mix,
        13: country_mix,
        14: carbon,
        15: gen_cons,
        16: comparison,
        17: percapita,
        18: waterfall,
    }


def _captions() -> dict[int, str]:
    return {
        1: "Two series: all reporting countries (coverage varies over time) and a "
           "fixed sample of countries present in 1990. Twelve former Soviet countries "
           "(Russia, Ukraine, Kazakhstan, ...) have no data for 1990-91 and appear from "
           "1992, so the 'all reporting' rise includes a coverage effect.",
        2: "Ten largest final electricity consumers in 2022, ranked by B25_FEC (final "
           "consumption). All values are terminal consumption, not generation.",
        3: "Final consumption aggregated to UN M49 continents (Africa, Americas, Asia, "
           "Europe, Oceania). Kosovo is assigned to Europe.",
        4: "World sector split, 1990-2022 (use the slider to scrub the year). 21 areas "
           "(1990) and 15 areas (2022) do not report an industry row; the sector sums still "
           "equal the FEC total to within 1%.",
        5: "Each country's share of world final consumption in 1990 versus 2022, using "
           "the same fixed sample of countries as the denominator in both years.",
        6: "Country-level final consumption, 1990 (Natural Earth 50m, UN_A3 link; "
           "214 of 218 areas have a matching polygon).",
        7: "Country-level final consumption, 2022 (Natural Earth 50m, UN_A3 link; "
           "214 of 218 areas have a matching polygon).",
        8: "World electricity generation mix, 2000-2022 (use the slider to scrub the year). "
           "This is generation, not final consumption, shown only as background context.",
        9: "Animated world map, 1990-2022. Use the slider or the play button to scrub "
           "through every year.",
        10: "Kaya decomposition of final-consumption growth, 2000-2022: E = P x (GDP/P) "
            "x (E/GDP). Population, income-per-person and electricity-per-GDP are "
            "additive in log growth, so the three bars sum exactly to total growth. "
            "Associations only - observational data, no causal claim.",
        11: "Electricity generation mix by OWID continent, 2022. Generation, not final "
            "consumption, shown for background; the project's own region column merges "
            "North and South America into one 'Americas' continent.",
        12: "Generation mix by region animated across 2000-2022. Use the slider or "
            "play button to scrub the year; shares are % of each region's own generation.",
        13: "Generation mix of the ten largest consumers, 2000-2022 (use the slider to "
            "scrub the year). China and India are coal-led; Brazil/Canada/France are "
            "hydro/nuclear-based.",
        14: "Carbon intensity of electricity, 2000-2022. World falls 527→490; Japan "
            "rises 424→520 after Fukushima; France stays ~80.",
        15: "World generation vs final consumption, 2022. The ~14% gap is "
            "transmission/distribution losses, plant own-use and net trade - the reason "
            "generation stays out of the sector shares.",
        16: "Consumption growth vs population and GDP growth, 2000-2022. Where electricity "
            "growth outpaces GDP, electrification is catching up; where it trails, "
            "efficiency/decoupling. Associations only.",
        17: "Electricity use vs income per person, 2022 (log-log). The upward slope shows "
            "richer countries use more electricity per person - an association, not proof "
            "that income causes consumption.",
        18: "Kaya decomposition for China, 2000-2022, illustrating the method: "
            "E = population x income/person x E/GDP. The three parts sum exactly to total "
            "growth (associations, not causes).",
    }


def _figures(df: pd.DataFrame, reg: pd.DataFrame) -> dict[int, object]:
    return {
        1: mf.fig_global_trend(df),
        2: mf.fig_top10(df),
        3: mf.fig_regional(reg),
        4: mf.fig_sector_structure_slider(df),
        5: mf.fig_share_change(df),
        6: mf.make_map_figure(1990, df),
        7: mf.make_map_figure(2022, df),
        8: mf.fig_generation_mix_slider(),
        9: mf.fig_map_slider(df),
        10: mf.fig_drivers_decomposition(df),
        11: mf.fig_generation_mix_regions(),
        12: mf.fig_generation_mix_regions_slider(),
        13: mf.fig_generation_mix_countries_slider(),
        14: mf.fig_carbon_intensity(),
        15: mf.fig_generation_vs_consumption(df),
        16: mf.fig_consumption_comparison(df),
        17: mf.fig_percapita_scatter(df),
        18: mf.fig_kaya_waterfall(df),
    }


_PNG_NAMES = {
    1: "output_1_global_trend.png",
    2: "output_2_top10_consumers.png",
    3: "output_3_regional_trends.png",
    4: "output_4_sector_structure.png",
    5: "output_5_share_change.png",
    6: "output_6_map_1990.png",
    7: "output_7_map_2022.png",
    8: "output_8_generation_mix.png",
    9: "output_9_map_slider.png",
    10: "output_10_drivers_decomposition.png",
    11: "output_11_generation_mix_regions.png",
    12: "output_12_generation_mix_regions_slider.png",
    13: "output_13_generation_mix_countries.png",
    14: "output_14_carbon_intensity.png",
    15: "output_15_generation_vs_consumption.png",
    16: "output_16_consumption_comparison.png",
    17: "output_17_percapita_scatter.png",
    18: "output_18_kaya_waterfall.png",
}

_TITLES = {
    1: "Output 1 — Global trend, 1990-2022",
    2: "Output 2 — Top 10 consumers (2022)",
    3: "Output 3 — Regional trends",
    4: "Output 4 — Sector structure, 1990-2022 (animated)",
    5: "Output 5 — Country share change",
    6: "Output 6 — World map, 1990",
    7: "Output 7 — World map, 2022",
    8: "Output 8 — Generation mix, 2000-2022 (animated)",
    9: "Output 6-7 — Animated world map (1990-2022)",
    10: "Drivers of consumption change",
    11: "Generation mix by region (2022)",
    12: "Generation mix by region (2000-2022, animated)",
    13: "Generation mix, largest countries (2000-2022, animated)",
    14: "Carbon intensity of electricity (2000-2022)",
    15: "Generation vs final consumption (2022)",
    16: "Consumption vs population and GDP growth (2000-2022)",
    17: "Electricity use vs income per person (2022)",
    18: "Kaya decomposition, China (2000-2022)",
}


def build_index_html(df: pd.DataFrame, reg: pd.DataFrame) -> str:
    figs = _figures(df, reg)
    csvs = _fig_csvs(df, reg)
    captions = _captions()

    # Render a static thumbnail of the animated slider for its PNG download button.
    slider_png = FIGURES / "output_9_map_slider.png"
    if not slider_png.exists():
        figs[9].write_image(slider_png, **mf.PNG_SIZE)

    world22 = df[df["year"] == 2022]["FEC"].sum()
    n_areas = df["code"].nunique()
    n_years = df["year"].nunique()
    fixed = len(set(df[df["year"] == 1990]["code"]))

    parts = ["<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n",
             "<title>The Power-Hungry World — Electricity Consumption 1990–2022</title>\n",
             f"<style>{CSS}</style>\n</head>\n<body>\n{NAV}\n",
             "<header>\n",
             "<h1>The Power-Hungry World — Electricity Consumption 1990–2022</h1>\n",
             "<p class=\"subtitle\">Data pipeline, validation and outputs</p>\n",
             "<p class=\"meta\">Team 03 / CISC7204 · Data: UN SDMX Energy Balance "
             f"(1990–2022) · Generated {date.today().isoformat()}</p>\n</header>\n"]

    parts.append("<section id=\"key-figures\">\n")
    kfs = [
        (f"{world22:,.0f}", "World final consumption 2022 (TWh)"),
        (str(n_areas), "Areas"),
        (str(n_years), "Years (1990-2022)"),
        ("4", "Sectors"),
        (str(fixed), "Fixed-sample countries"),
    ]
    for num, lbl in kfs:
        parts.append(f'<div class="kf"><div class="num">{num}</div><div class="lbl">{lbl}</div></div>\n')
    parts.append("</section>\n")

    parts.append("<section id=\"outputs\">\n<h2>The outputs</h2>\n")
    for n in range(1, 19):
        png_uri = _png_to_uri(_PNG_NAMES[n])
        csv_uri = _csv_to_uri(csvs[n])
        if n in (6, 7):
            # Static choropleths have no useful hover (hover_name is the numeric
            # code only) and each embeds the ~3 MB geojson as an SVG with 242
            # polygons. Render the PNG instead of an interactive figure: removes
            # ~6.4 MB of geojson and two heavy SVG layers, which is what makes the
            # page lag on scroll.
            fig_html = (f'<img src="{png_uri}" alt="{_TITLES[n]}" '
                        'style="width:100%;height:auto;border:1px solid var(--line);'
                        'border-radius:10px;" loading="lazy">')
        elif n == 1:
            fig_html = figs[n].to_html(include_plotlyjs=True, full_html=False, div_id=f"chart{n}")
            fig_html = _clean_plotlyjs(fig_html)
        else:
            fig_html = figs[n].to_html(include_plotlyjs=False, full_html=False, div_id=f"chart{n}")
        parts.append('<div class="chart">\n')
        parts.append(f"<h3>{_TITLES[n]}</h3>\n")
        parts.append(fig_html)
        parts.append(f"<p class=\"caption\">{captions[n]}</p>\n")
        parts.append('<div class="buttons">\n')
        parts.append(f'<a href="{png_uri}" download="{_PNG_NAMES[n]}">Download PNG</a>\n')
        parts.append(f'<a href="{csv_uri}" download="output_{n}_data.csv">Download CSV</a>\n')
        parts.append("</div>\n</div>\n")
    parts.append("</section>\n")

    parts.append("<section id=\"steps\">\n<h2>Steps</h2>\n")
    steps = [
        ("Download", "One UN SDMX request pulls every B07_EL series (B25_FEC plus the "
         "six sector codes B26_121, B40_122, B50_1231, B48_1232, B49_1235, B51_1234) for "
         "1990-2022, plus the CL_AREA code list."),
        ("Parse", "The combined XML is parsed into a tidy CSV (REF_AREA, TIME_PERIOD, "
         "TRANSACTION, OBS_VALUE, ESTIMATE, UNIT); the parent aggregate B47_123 is never added."),
        ("Map", "CL_AREA gives each area a name, ISO alpha-2 code and subregion; a static "
         "table maps subregion to continent; the Natural Earth ne_50m UN_A3 link attaches polygons."),
        ("Decide", "Four documented decisions: Germany 1990 (linked estimate, Industry 229.9), "
         "Pakistan 1990-92 (recompute FEC to 28.75/31.50/33.89), Pakistan 2017-22 transport = 0 "
         "(reported nil), and Indonesia transport 2000-07 + 2016 (ESDM HEESI fills)."),
        ("Validate", "Four validation layers: internal consistency, an OWID demand cross-check, "
         "Kelden's headline numbers, and a duplicate-count check."),
        ("Trend", "The global rise is drawn as two lines so the ex-Soviet coverage effect is visible."),
        ("Rank", "The 2022 top-10 consumers are ranked directly by final consumption."),
        ("Structure", "Sector shares and regional totals are summed from the country table."),
        ("Map", "Two choropleths share one colour scale; a slider animates 1990-2022."),
        ("Assemble", "Figures are embedded in this self-contained page with PNG/CSV downloads."),
    ]
    for i, (title, body) in enumerate(steps, 1):
        parts.append(f'<div class="step"><b>{i}. {title}</b> — {body} '
                     f'<a href="method.html#s{i}">Read the full method →</a></div>\n')
    parts.append("</section>\n")

    parts.append("<section id=\"data-dictionary\">\n<h2>Data dictionary</h2>\n")
    parts.append("<p>Columns of <code>Datasets/analysis_country_year.csv</code>:</p>\n<table>\n")
    dd = [
        ("code", "3-digit UN M49 reference-area code (e.g. 156 = China)."),
        ("area", "UN area name."),
        ("iso2", "ISO 3166-1 alpha-2 code."),
        ("iso3", "ISO 3166-1 alpha-3 code (from the Natural Earth UN_A3 link)."),
        ("admin", "Natural Earth administrative name."),
        ("region", "UN M49 continent (Africa, Americas, Asia, Europe, Oceania)."),
        ("subregion", "UN M49 subregion name."),
        ("year", "Calendar year (1990-2022)."),
        ("Industry", "Final consumption, industry (B26_121), TWh."),
        ("Transport", "Final consumption, transport (B40_122), TWh."),
        ("Residential", "Final consumption, residential (B50_1231), TWh."),
        ("Services_Other", "Services/other = B48_1232 + B49_1235 + B51_1234, TWh."),
        ("FEC", "Total final consumption (B25_FEC), TWh."),
        ("flag_germany_linked", "1 = Germany 1990 sector split is a linked AGEB estimate."),
        ("flag_fec_recomputed", "1 = Pakistan 1990-92 FEC was recomputed (industry added)."),
        ("flag_reported_nil", "1 = Pakistan 2017-22 transport recorded as reported nil (0)."),
        ("flag_indonesia_heesi", "1 = Indonesia transport 2000-07 + 2016 filled from ESDM HEESI."),
    ]
    parts.append("<tr><th>Column</th><th>Meaning</th></tr>\n")
    for col, desc in dd:
        parts.append(f"<tr><td><code>{col}</code></td><td>{desc}</td></tr>\n")
    parts.append("</table>\n</section>\n")

    parts.append("<section id=\"files\">\n<h2>Files</h2>\n")
    parts.append("<p>Source repository: <a href=\"https://github.com/UNCHIKIT/"
                 "CISC7204-GroupG-SemesterProject-Team03\">github.com/UNCHIKIT/"
                 "CISC7204-GroupG-SemesterProject-Team03</a></p>\n<ul>\n")
    files = [
        ("team03/download_undata.py", "Step 1: download raw UN SDMX + CL_AREA."),
        ("team03/build_energy_dataset.py", "Step 2: parse XML into the cleaned CSV."),
        ("team03/build_mappings.py", "Step 3: region/ISO/map mapping tables."),
        ("team03/build_analysis_tables.py", "Step 4: country x year and region x year tables."),
        ("team03/build_supplementary_sources.py", "Step 4.5: gap table + source register."),
        ("team03/validate_dataset.py", "Step 5: four-layer validation."),
        ("team03/make_figures.py", "Step 6: the figures (1-8 proposal + 10-11 answer charts)."),
        ("team03/make_dashboard.py", "Step 7: this dashboard."),
        ("team03/DATA_PIPELINE.md", "Full written method (see Method page)."),
        ("Figures/output_6_7_slider.html", "Self-contained 1990-2022 map slider."),
        ("Datasets/analysis_country_year.csv", "Country x year analysis table."),
        ("Datasets/analysis_region_year.csv", "Region x year analysis table."),
    ]
    for path, desc in files:
        parts.append(f"<li><a href=\"../{path}\"><code>{path}</code></a> — {desc}</li>\n")
    parts.append("</ul>\n</section>\n</body>\n</html>\n")

    return "".join(parts)


def _method_sections() -> list[dict]:
    return [
        {"id": "o1", "title": "Output 1 — Global trend",
         "input": "analysis_country_year.csv: code, area, year, FEC.",
         "trans": "Group by year and sum FEC (all reporting); build the fixed sample as "
                  "the codes present in 1990 and sum FEC for those codes per year.",
         "code": "world = df.groupby('year')['FEC'].sum()\n"
                 "fixed = set(df[df.year == 1990]['code'])\n"
                 "fixed_s = df[df.code.isin(fixed)].groupby('year')['FEC'].sum()\n"
                 "fig = px.line(...)  # two series",
         "spec": "Line chart, x=year, y=FEC (TWh), two series (all reporting vs fixed sample). "
                 "Caption must disclose the ex-Soviet 1990-91 coverage effect."},
        {"id": "o2", "title": "Output 2 — Top 10 consumers",
         "input": "analysis_country_year.csv filtered to year == 2022.",
         "trans": "Take the 10 largest FEC values with nlargest(10), sort ascending, "
                  "plot as a horizontal bar.",
         "code": "d = df[df.year == 2022].nlargest(10, 'FEC').sort_values('FEC')\n"
                 "fig = px.bar(d, x='FEC', y='area', orientation='h')",
         "spec": "Horizontal bar, x=FEC (TWh), y=country, ranked."},
        {"id": "o3", "title": "Output 3 — Regional trends",
         "input": "analysis_region_year.csv (region, year, FEC), excluding World.",
         "trans": "Filter out the World row and plot one line per region.",
         "code": "d = reg[reg.region != 'World']\n"
                 "fig = px.line(d, x='year', y='FEC', color='region')",
         "spec": "Multi-line chart, x=year, y=FEC (TWh), one line per continent."},
        {"id": "o4", "title": "Output 4 — Sector structure",
         "input": "analysis_country_year.csv, years 1990 and 2022, sector columns.",
         "trans": "Sum the four sector columns across all countries for each year, "
                  "normalise to 100%, stack by sector.",
         "code": "totals = d[['Industry','Transport','Residential','Services_Other']].sum()\n"
                 "share = totals / totals.sum() * 100\n"
                 "fig = px.bar(..., barmode='stack')",
         "spec": "100% stacked bar, two bars (1990, 2022), stacked by sector. Caption "
                 "discloses the 21 (1990) / 15 (2022) areas missing an industry row."},
        {"id": "o5", "title": "Output 5 — Country share change",
         "input": "analysis_country_year.csv, fixed sample, years 1990 and 2022.",
         "trans": "For each fixed-sample country compute share = FEC / world FEC in each "
                  "year, then draw a line from the 1990 share to the 2022 share.",
         "code": "share = d.FEC / d.groupby('year').FEC.transform('sum') * 100\n"
                 "fig = go.Figure(); ...  # slope lines per country",
         "spec": "Slope chart, x in {1990, 2022}, y = share (%), one line per country, "
                 "same fixed sample as denominator in both years."},
        {"id": "o6", "title": "Output 6 — World map, 1990",
         "input": "analysis_country_year.csv (year == 1990) + Natural Earth ne_50m geojson.",
         "trans": "Resolve combined codes (251→250, 382→380, 579→578, 757→756) to the main "
                  "country, take log10(FEC), and colour by the UN_A3 link.",
         "code": "d['map_code'] = d.code.map({'251':'250','382':'380','579':'578','757':'756'}).fillna(d.code)\n"
                 "fig = px.choropleth(d, geojson=geojson, locations='map_code',\n"
                 "                    featureidkey='properties.UN_A3', color='FEC_log',\n"
                 "                    color_continuous_scale='Viridis', range_color=[-1, 4])",
         "spec": "Choropleth (Natural Earth 50m, UN_A3 link, 214/218 areas coloured). Uses the "
                 "Viridis scale with range_color=[-1, 4] (log10 TWh)."},
        {"id": "o7", "title": "Output 7 — World map, 2022",
         "input": "analysis_country_year.csv (year == 2022) + Natural Earth ne_50m geojson.",
         "trans": "Identical to Output 6 but for 2022, so both years share the same colour "
                  "scale and range_color for a fair visual comparison. A separate "
                  "animation_frame slider (output_6_7_slider.html) plays 1990-2022.",
         "code": "fig = make_map_figure(2022, df)  # same scale and range_color as 1990",
         "spec": "Choropleth (Natural Earth 50m, UN_A3 link). Shares the Viridis scale and "
                 "range_color=[-1, 4] with Output 6."},
        {"id": "o8", "title": "Output 8 — Generation mix",
         "input": "OWID electricity-prod-source-stacked.csv, Entity == 'World'.",
         "trans": "Sum the nine source columns for 2000 and 2022, normalise to 100%, "
                  "stack by source.",
         "code": "w = world[world.Year == yr][srcs].sum()\n"
                 "fig = px.bar(..., barmode='stack')",
         "spec": "100% stacked bar, 2000 vs 2022, stacked by generation source. Caption "
                 "states this is generation, not consumption, shown only as background."},
        {"id": "o10", "title": "Drivers of consumption change",
         "input": "analysis_country_year.csv (FEC), World Bank SP.POP.TOTL, "
                  "NY.GDP.MKTP.PP.KD, for eleven large consumers.",
         "trans": "Kaya identity E = P x (GDP/P) x (E/GDP). Take log growth over "
                  "2000-2022 so the three components are exactly additive in "
                  "percentage points; render with barmode='relative' so the usually "
                  "negative E/GDP term stacks below the axis.",
         "code": "ge = log(E22/E00)*100; gp = log(P22/P00)*100\n"
                 "gy = log((GDP22/P22)/(GDP00/P00))*100\n"
                 "gi = log((E22/GDP22)/(E00/GDP00))*100  # ge = gp + gy + gi",
         "spec": "Horizontal stacked bars (Population, Income/person, E/GDP) summing to "
                 "total growth, with a diamond marker for total E. Caption states this is "
                 "observational and associative, not causal."},
        {"id": "o11", "title": "Generation mix by region",
         "input": "OWID electricity-prod-source-stacked.csv, continent entities.",
         "trans": "For each OWID continent (Africa, Asia, Europe, North America, South "
                  "America, Oceania), sum the nine fuel columns for 2022, normalise to "
                  "100%, stack by fuel.",
         "code": "r = ow[ow.Entity == region]\n"
                 "share = 100 * r[r.Year == 2022][srcs].sum() / r[r.Year == 2022][srcs].sum().sum()\n"
                 "fig = px.bar(..., barmode='stack')",
         "spec": "100% stacked horizontal bar per continent, stacked by generation fuel. "
                 "Generation, not consumption; the project's own region column merges the "
                 "two Americas into one continent."},
        {"id": "o12", "title": "Generation mix by region (animated)",
         "input": "OWID electricity-prod-source-stacked.csv, continent entities, 2000-2022.",
         "trans": "Compute each continent's fuel share for every year, then animate with "
                  "animation_frame='year' so a slider scrubs 2000-2022.",
         "code": "d = region_year_mix  # region, year, source, share_pct\n"
                 "fig = px.bar(d, x='region', y='share', color='source',\n"
                 "             animation_frame='year', barmode='stack')",
         "spec": "Stacked bar per continent, animated by year with slider + play button; "
                 "y-axis fixed to 0-100%."},
        {"id": "o13", "title": "Generation mix, largest countries",
         "input": "OWID electricity-prod-source-stacked.csv, ten largest consumers, 2022.",
         "trans": "For each country sum the nine fuels for 2022, normalise to 100%, stack.",
         "code": "share = 100 * c[c.Year == 2022][srcs].sum() / c[c.Year == 2022][srcs].sum().sum()\n"
                 "fig = px.bar(..., barmode='stack')",
         "spec": "Horizontal 100% stacked bar per country, ranked by total generation."},
        {"id": "o14", "title": "Carbon intensity of electricity",
         "input": "OWID carbon-intensity-electricity.csv, ten largest consumers, 2000-2022.",
         "trans": "Plot each country's gCO2/kWh as a line over 2000-2022.",
         "code": "d = ci[ci.Entity.isin(countries) & ci.Year.between(2000, 2022)]\n"
                 "fig = px.line(d, x='Year', y='Carbon intensity', color='Entity')",
         "spec": "Multi-line chart, x=year, y=gCO2/kWh, one line per country."},
        {"id": "o15", "title": "Generation vs final consumption",
         "input": "OWID world generation 2022; analysis_country_year.csv world FEC 2022.",
         "trans": "Sum the nine fuels for world 2022 (generation) and sum FEC for 2022 "
                  "(consumption); plot as two bars and annotate the gap.",
         "code": "gen = world[world.Year == 2022][srcs].sum().sum()\n"
                 "cons = df[df.year == 2022]['FEC'].sum()\n"
                 "gap = gen - cons  # ~14% = losses + own-use + trade",
         "spec": "Two bars (generation, consumption) with a caption noting the ~14% gap is "
                 "why generation stays out of the sector shares."},
        {"id": "o16", "title": "Consumption vs population and GDP growth",
         "input": "analysis_country_year.csv (FEC), World Bank SP.POP.TOTL and NY.GDP.MKTP.PP.KD.",
         "trans": "For each of eleven countries compute log growth of FEC, population and "
                  "total GDP over 2000-2022, and plot as grouped bars.",
         "code": "ge = log(E22/E00)*100; gp = log(P22/P00)*100; gg = log(GDP22/GDP00)*100\n"
                 "fig = px.bar(d, x='growth_pp', y='country', color='metric', barmode='group')",
         "spec": "Grouped horizontal bar, one group per country (E, population, GDP)."},
        {"id": "o17", "title": "Electricity use vs income per person",
         "input": "analysis_country_year.csv FEC, World Bank population and GDP PPP, 2022.",
         "trans": "For every country with both population and GDP, compute per-capita "
                  "electricity (kWh) and per-capita GDP, then plot on log-log axes coloured "
                  "by region.",
         "code": "e_pc = FEC*1e9/P; g_pc = GDP/P\n"
                 "fig = px.scatter(d, x='gdp_per_capita_usd', y='electricity_per_capita_kwh',\n"
                 "                 color='region', log_x=True, log_y=True)",
         "spec": "Log-log scatter, one point per country, coloured by continent; caption "
                 "states association, not causation."},
        {"id": "o18", "title": "Kaya decomposition, China",
         "input": "analysis_country_year.csv FEC, World Bank population and GDP PPP, China.",
         "trans": "Compute China's population / income-per-person / E-per-GDP log-growth "
                  "components and draw them as a waterfall summing to total growth.",
         "code": "fig = go.Figure(go.Waterfall(\n"
                 "    x=['Population','Income per person','Efficiency (E/GDP)','Total E growth'],\n"
                 "    measure=['relative','relative','relative','total'],\n"
                 "    y=[gp, gy, gi, ge]))",
         "spec": "Waterfall showing the three additive parts and their total."},
    ]


def build_method_html() -> str:
    parts = ["<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n",
             "<title>Method — The Power-Hungry World</title>\n",
             f"<style>{CSS}</style>\n</head>\n<body>\n"]
    parts.append('<nav><a href="index.html">Outputs</a><a href="#overview">Method</a>'
                 '<a href="index.html#data-dictionary">Data dictionary</a>'
                 '<a href="index.html#files">Files</a></nav>\n')

    parts.append("<header><h1>Method — how the data becomes the charts</h1>"
                 "<p class=\"subtitle\">From raw UN SDMX XML to eighteen outputs</p></header>\n")

    parts.append("<section id=\"overview\">\n<h2>Overview</h2>\n<pre>"
                 "un_all.xml (UN SDMX) ──► electricity_consumption_1990_2023.csv (TJ)\n"
                 "        │                              │\n"
                 "UN_CL_AREA_codelist.xml ─┐            TWh = OBS_VALUE / 3600\n"
                 "ne_50m geojson ──────────┴─► country_region.csv ─► analysis_country_year.csv\n"
                 "                                                          │\n"
                 "                                              analysis_region_year.csv\n"
                 "                                                          │\n"
                 "                                   eighteen figures + this dashboard</pre>\n"
                 "<p>Intermediate files: <code>un_all.xml</code>, <code>UN_CL_AREA_codelist.xml</code>, "
                 "<code>electricity_consumption_1990_2023.csv</code>, <code>country_region.csv</code>, "
                 "<code>natural_earth_index.csv</code>, <code>analysis_country_year.csv</code>, "
                 "<code>analysis_region_year.csv</code>.</p>\n</section>\n")

    parts.append("<section id=\"shared\">\n<h2>Shared preparation</h2>\n")
    shared = [
        ("TWh conversion", "Every value is stored in TJ by the UN service (the UNIT label "
         "reads HSO but the number is TJ). Convert with:", "TWh = OBS_VALUE / 3600\n"
         "# e.g. China 2022 FEC: 29,518,462 TJ / 3600 = 8,200 TWh"),
        ("Sector composition", "Services_Other is the row-wise sum of three components "
         "(missing values skipped). The parent B47_123 is never added:",
         "Services_Other = B48_1232 + B49_1235 + B51_1234  (min_count=1)\n"
         "# B47_123 is the parent aggregate and MUST NOT be included"),
        ("Region derivation", "Each CL_AREA country has a Parent (subregion); a static "
         "table maps subregion to continent because subregions have no parent:",
         "SUBREGION_TO_REGION = {'155':'Europe', '151':'Europe', ..., '053':'Oceania'}\n"
         "region = SUBREGION_TO_REGION[subregion_of(code)]"),
        ("ISO / map link", "Natural Earth polygons expose UN_A3 (the UN numeric code); "
         "the map is coloured by matching REF_AREA to UN_A3:",
         "fig = px.choropleth(d, geojson=geojson, locations='map_code',\n"
         "                    featureidkey='properties.UN_A3', ...)"),
    ]
    for title, body, code in shared:
        parts.append(f"<h3>{title}</h3><p>{body}</p><pre><code>{code}</code></pre>\n")
    parts.append("</section>\n")

    for s in _method_sections():
        parts.append(f"<section id=\"{s['id']}\">\n<h2>{s['title']}</h2>\n")
        parts.append(f"<h3>Input</h3><p>{s['input']}</p>\n")
        parts.append(f"<h3>Transformation</h3><p>{s['trans']}</p>\n")
        parts.append(f"<h3>Code</h3><pre><code>{s['code']}</code></pre>\n")
        parts.append(f"<h3>Chart specification</h3><p>{s['spec']}</p>\n</section>\n")

    parts.append("<section id=\"validation\">\n<h2>Validation trace</h2>\n<ul>\n")
    for li in [
        "Sector sum == FEC within 1%: 6932/6932 rows (100%).",
        "OWID 2022 ratio (UN FEC / OWID demand): China 0.928, Germany 0.884, Japan 0.867, "
        "Korea 0.870, Indonesia 0.880 (all in the 0.85-0.95 band); India 0.778 is flagged "
        "(high losses / incomplete agriculture reporting).",
        "Duplicate count: codes 250/380/578/756 are absent; 840 (US) and 076 (Brazil) present.",
        "Top-30 countries account for 88.6% of 2022 world FEC.",
        "If any of these changed materially, the chart captions and the limitations "
        "section of DATA_PIPELINE.md would have to be revisited.",
    ]:
        parts.append(f"<li>{li}</li>\n")
    parts.append("</ul>\n</section>\n")

    parts.append("<section id=\"reproduce\">\n<h2>Reproduce</h2>\n<pre>"
                 "python team03/download_undata.py\n"
                 "python team03/build_energy_dataset.py\n"
                 "python team03/build_mappings.py\n"
                 "python team03/build_analysis_tables.py\n"
                 "python team03/build_supplementary_sources.py\n"
                 "python team03/validate_dataset.py\n"
                 "python team03/make_figures.py\n"
                 "python team03/make_dashboard.py</pre>\n"
                 "<p>Expected outputs are described in <a href=\"../team03/DATA_PIPELINE.md\">"
                 "team03/DATA_PIPELINE.md</a>.</p>\n</section>\n")

    parts.append("<p><a href=\"index.html\">Back to outputs</a></p>\n</body>\n</html>\n")
    return "".join(parts)


def main() -> int:
    df = mf.load_country_year()
    reg = mf.load_region_year()

    WEB.mkdir(parents=True, exist_ok=True)
    index = build_index_html(df, reg)
    method = build_method_html()

    (WEB / "index.html").write_text(index, encoding="utf-8")
    (WEB / "method.html").write_text(method, encoding="utf-8")
    print(f"web/index.html: {len(index)} bytes")
    print(f"web/method.html: {len(method)} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
