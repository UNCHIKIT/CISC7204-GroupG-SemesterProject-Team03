"""Generate the proposal and answer figures (PNG + interactive HTML).

Step 6 of the Team 03 data pipeline.

Every figure is produced in two formats: a high-resolution PNG (kaleido,
1200x650 @ scale 2) for the report/PDF, and an interactive Plotly figure that
is embedded in the dashboard. ``make_map_figure(year)`` returns the choropleth
figure for direct use inside a Dash ``dcc.Graph``.

Outputs land in ``Figures/``: ``output_1_global_trend.png`` ...
``output_8_generation_mix.png`` plus ``output_6_7_slider.html`` (self-contained
year slider with a play button).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

REPO_ROOT = Path(__file__).resolve().parent.parent
DATASETS = REPO_ROOT / "Datasets"
FIGURES = REPO_ROOT / "Figures"

COUNTRY_YEAR = DATASETS / "analysis_country_year.csv"
REGION_YEAR = DATASETS / "analysis_region_year.csv"
GEOJSON = DATASETS / "ne_50m_admin_0_countries.geojson"
PROD_SOURCE = DATASETS / "owid_electricity_prod_source.csv"
CARBON_INTENSITY = DATASETS / "carbon_intensity_electricity.csv"
POP_JSON = DATASETS / "worldbank_population.json"
GDP_JSON = DATASETS / "worldbank_gdp_ppp.json"

MIX_COUNTRIES = ["China", "United States", "India", "Japan", "Russia",
                 "Brazil", "South Korea", "Canada", "Germany", "France"]
MIX_SOURCES = ["Other renewables", "Bioenergy", "Solar", "Wind", "Hydropower",
               "Nuclear", "Gas", "Oil", "Coal"]
MIX_REGIONS = ["Africa", "Asia", "Europe", "North America", "South America", "Oceania"]

SECTORS = ["Industry", "Transport", "Residential", "Services_Other"]
COMBINED_TO_MAIN = {"251": "250", "382": "380", "579": "578", "757": "756"}

PNG_SIZE = dict(width=1200, height=650, scale=2)


def load_country_year() -> pd.DataFrame:
    return pd.read_csv(COUNTRY_YEAR, dtype={"code": str})


def load_region_year() -> pd.DataFrame:
    return pd.read_csv(REGION_YEAR)


def load_geojson() -> dict:
    return json.loads(GEOJSON.read_text(encoding="utf-8"))


def _save(fig: go.Figure, name: str) -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig.write_image(FIGURES / name, **PNG_SIZE)
    print(f"[png] {name}")


# --------------------------------------------------------------------------- #
# Output 1: global trend (two lines)
# --------------------------------------------------------------------------- #
def fig_global_trend(df: pd.DataFrame) -> go.Figure:
    world = df.groupby("year")["FEC"].sum().reset_index()
    fixed_codes = set(df[df["year"] == 1990]["code"])
    fixed = df[df["code"].isin(fixed_codes)].groupby("year")["FEC"].sum().reset_index()

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=world["year"], y=world["FEC"], name="All reporting countries",
                             mode="lines", line=dict(width=2.5, color="#1f77b4")))
    fig.add_trace(go.Scatter(x=fixed["year"], y=fixed["FEC"],
                             name=f"{len(fixed_codes)}-country fixed sample",
                             mode="lines", line=dict(width=2.5, color="#ff7f0e", dash="dash")))
    fig.update_layout(
        title="Global electricity final consumption, 1990-2022",
        xaxis_title="Year", yaxis_title="Final consumption (TWh)",
        template="plotly_white", hovermode="x unified",
    )
    return fig


# --------------------------------------------------------------------------- #
# Output 2: top 10 consumers 2022
# --------------------------------------------------------------------------- #
def fig_top10(df: pd.DataFrame) -> go.Figure:
    d = df[df["year"] == 2022].nlargest(10, "FEC").sort_values("FEC")
    fig = px.bar(d, x="FEC", y="area", orientation="h",
                 title="Top 10 electricity consumers, 2022",
                 labels={"FEC": "Final consumption (TWh)", "area": ""},
                 color="FEC", color_continuous_scale="Viridis")
    fig.update_layout(template="plotly_white", coloraxis_showscale=False, showlegend=False)
    fig.update_yaxes(autorange="reversed")
    return fig


# --------------------------------------------------------------------------- #
# Output 3: regional trends
# --------------------------------------------------------------------------- #
def fig_regional(reg: pd.DataFrame) -> go.Figure:
    d = reg[reg["region"] != "World"]
    fig = px.line(d, x="year", y="FEC", color="region",
                  title="Electricity final consumption by region, 1990-2022",
                  labels={"FEC": "Final consumption (TWh)", "year": "Year", "region": "Region"})
    fig.update_layout(template="plotly_white")
    return fig


# --------------------------------------------------------------------------- #
# Output 4: sector structure 1990 vs 2022 (100% stacked)
# --------------------------------------------------------------------------- #
def fig_sector_structure(df: pd.DataFrame) -> go.Figure:
    rows = []
    for yr in (1990, 2022):
        d = df[df["year"] == yr]
        totals = d[SECTORS].sum()
        share = totals / totals.sum() * 100
        for s in SECTORS:
            rows.append({"year": str(yr), "sector": s, "share": share[s]})
    d = pd.DataFrame(rows)
    fig = px.bar(d, x="year", y="share", color="sector",
                 title="World electricity consumption by sector, 1990 vs 2022",
                 labels={"share": "Share of total (%)", "year": ""},
                 color_discrete_sequence=px.colors.qualitative.Set2)
    fig.update_layout(template="plotly_white", barmode="stack", yaxis_ticksuffix="%")
    return fig


# --------------------------------------------------------------------------- #
# Output 5: country share change (slope chart, fixed sample)
# --------------------------------------------------------------------------- #
def fig_share_change(df: pd.DataFrame) -> go.Figure:
    fixed = set(df[df["year"] == 1990]["code"])
    d = df[df["code"].isin(fixed) & df["year"].isin([1990, 2022])]
    tot = d.groupby("year")["FEC"].transform("sum")
    d = d.assign(share=d["FEC"] / tot * 100)
    pivot = d.pivot(index="code", columns="year", values="share").dropna()

    fig = go.Figure()
    for code, r in pivot.iterrows():
        fig.add_trace(go.Scatter(
            x=[1990, 2022], y=[r[1990], r[2022]], mode="lines+markers",
            line=dict(width=0.7, color="rgba(150,150,150,0.5)"),
            marker=dict(size=4), showlegend=False, hoverinfo="skip",
        ))
    # highlight the five biggest 2022 shares
    top = pivot[2022].nlargest(5).index
    for code in top:
        r = pivot.loc[code]
        fig.add_trace(go.Scatter(
            x=[1990, 2022], y=[r[1990], r[2022]], mode="lines+markers+text",
            text=["", df[df["code"] == code]["area"].iloc[0]],
            textposition="middle right", textfont=dict(size=10),
            line=dict(width=2), marker=dict(size=6), showlegend=False,
        ))
    fig.update_layout(
        title=f"Country share of world electricity, 1990 vs 2022 ({len(pivot)}-country fixed sample)",
        xaxis=dict(tickvals=[1990, 2022], title=""),
        yaxis_title="Share of world total (%)",
        template="plotly_white",
    )
    return fig


# --------------------------------------------------------------------------- #
# Output 6/7: choropleth
# --------------------------------------------------------------------------- #
def make_map_figure(year: int, df: pd.DataFrame | None = None) -> go.Figure:
    if df is None:
        df = load_country_year()
    d = df[df["year"] == year][["code", "FEC"]].copy()
    d["map_code"] = d["code"].map(COMBINED_TO_MAIN).fillna(d["code"])
    d["FEC_log"] = np.log10(d["FEC"].clip(lower=0.1))

    geojson = load_geojson()
    fig = px.choropleth(
        d, geojson=geojson, locations="map_code", featureidkey="properties.UN_A3",
        color="FEC_log", color_continuous_scale="Viridis", range_color=[-1, 4],
        labels={"FEC_log": "FEC (TWh, log10)"},
        title=f"Electricity final consumption by country, {year}",
        hover_name="code",
    )
    fig.update_geos(projection_type="natural earth", showframe=False,
                    showcoastlines=False, showcountries=False)
    fig.update_layout(template="plotly_white", margin=dict(l=0, r=0, t=40, b=0))
    fig.update_coloraxes(colorbar_title="FEC (TWh, log10)")
    return fig


def fig_map_1990(df: pd.DataFrame) -> go.Figure:
    return make_map_figure(1990, df)


def fig_map_2022(df: pd.DataFrame) -> go.Figure:
    return make_map_figure(2022, df)


def fig_map_slider(df: pd.DataFrame) -> go.Figure:
    d = df[["code", "year", "FEC"]].copy()
    d["map_code"] = d["code"].map(COMBINED_TO_MAIN).fillna(d["code"])
    d["FEC_log"] = np.log10(d["FEC"].clip(lower=0.1))
    geojson = load_geojson()
    fig = px.choropleth(
        d, geojson=geojson, locations="map_code", featureidkey="properties.UN_A3",
        color="FEC_log", animation_frame="year", color_continuous_scale="Viridis",
        range_color=[-1, 4], labels={"FEC_log": "FEC (TWh, log10)"},
        title="Electricity final consumption by country, 1990-2022",
    )
    fig.update_geos(projection_type="natural earth", showframe=False,
                    showcoastlines=False, showcountries=False)
    fig.update_layout(template="plotly_white", margin=dict(l=0, r=0, t=40, b=0))
    fig.update_coloraxes(colorbar_title="FEC (TWh, log10)")
    # The geojson is identical for every year; store it once on the base trace
    # instead of duplicating the ~3 MB payload across all 33 frames.
    for frame in fig.frames:
        for trace in frame.data:
            if hasattr(trace, "geojson"):
                trace.geojson = None
    return fig


# --------------------------------------------------------------------------- #
# Output 8: generation mix (world, 2000 vs 2022)
# --------------------------------------------------------------------------- #
def fig_generation_mix() -> go.Figure:
    ow = pd.read_csv(PROD_SOURCE)
    world = ow[ow["Entity"] == "World"]
    srcs = ["Other renewables", "Bioenergy", "Solar", "Wind", "Hydropower",
            "Nuclear", "Gas", "Oil", "Coal"]
    rows = []
    for yr in (2000, 2022):
        w = world[world["Year"] == yr][srcs].sum()
        for s in srcs:
            rows.append({"year": str(yr), "source": s, "share": w[s]})
    d = pd.DataFrame(rows)
    d["share"] = d["share"] / d.groupby("year")["share"].transform("sum") * 100
    fig = px.bar(d, x="year", y="share", color="source",
                 title="World electricity generation mix, 2000 vs 2022 (generation, not consumption)",
                 labels={"share": "Share of generation (%)", "year": ""},
                 color_discrete_sequence=px.colors.qualitative.Set1)
    fig.update_layout(template="plotly_white", barmode="stack", yaxis_ticksuffix="%")
    return fig


# --------------------------------------------------------------------------- #
# Output 10: drivers of consumption change (Kaya decomposition, 2000 -> 2022)
# --------------------------------------------------------------------------- #
DRIVER_COUNTRIES = [
    # (label, code, iso3). France (251) has no iso3 in country_region (Natural
    # Earth France ISO_A3=-99), so it is carried explicitly.
    ("China", "156", "CHN"), ("United States", "840", "USA"), ("India", "356", "IND"),
    ("Japan", "392", "JPN"), ("Russia", "643", "RUS"), ("Brazil", "076", "BRA"),
    ("South Korea", "410", "KOR"), ("Canada", "124", "CAN"), ("Germany", "276", "DEU"),
    ("France", "251", "FRA"), ("Indonesia", "360", "IDN"),
]


def _wb_series(path: Path) -> dict[tuple[str, int], float]:
    data = json.loads(path.read_text(encoding="utf-8"))
    out: dict[tuple[str, int], float] = {}
    for row in data[1]:
        iso3 = row.get("countryiso3code")
        val = row.get("value")
        yr = row.get("date")
        if iso3 and val is not None and yr:
            out[(iso3, int(yr))] = float(val)
    return out


def drivers_decomposition_data(df: pd.DataFrame) -> pd.DataFrame:
    """Kaya decomposition table (log-growth percentage points, 2000 -> 2022)."""
    pop = _wb_series(POP_JSON)
    gdp = _wb_series(GDP_JSON)

    rows = []
    for label, code, iso3 in DRIVER_COUNTRIES:
        e = df[(df["code"] == code) & (df["year"].isin([2000, 2022]))].set_index("year")["FEC"]
        p00, p22 = pop.get((iso3, 2000)), pop.get((iso3, 2022))
        g00, g22 = gdp.get((iso3, 2000)), gdp.get((iso3, 2022))
        if None in (p00, p22, g00, g22) or 2000 not in e.index or 2022 not in e.index:
            continue
        ge = np.log(e[2022] / e[2000]) * 100
        gp = np.log(p22 / p00) * 100
        gy = np.log((g22 / p22) / (g00 / p00)) * 100
        gi = np.log((e[2022] / g22) / (e[2000] / g00)) * 100
        rows.append({"country": label, "population_pp": round(gp, 1),
                     "income_per_person_pp": round(gy, 1), "e_gdp_pp": round(gi, 1),
                     "total_growth_pp": round(ge, 1)})
    return pd.DataFrame(rows).sort_values("total_growth_pp")


def fig_drivers_decomposition(df: pd.DataFrame) -> go.Figure:
    """Log-growth Kaya decomposition E = P x (GDP/P) x (E/GDP), 2000 -> 2022.

    Each component is additive in log growth, so the three stacked bars sum
    exactly to the total electricity-growth rate (barmode='relative' renders the
    usually-negative efficiency term E/GDP below the axis).
    """
    tab = drivers_decomposition_data(df)
    d = tab.rename(columns={"population_pp": "Population",
                            "income_per_person_pp": "Income per person",
                            "e_gdp_pp": "Efficiency (E/GDP)",
                            "total_growth_pp": "Total electricity growth"})

    fig = go.Figure()
    comps = ["Population", "Income per person", "Efficiency (E/GDP)"]
    colors = ["#66c2a5", "#fc8d62", "#8da0cb"]
    for comp, color in zip(comps, colors):
        fig.add_trace(go.Bar(
            y=d["country"], x=d[comp], name=comp, orientation="h",
            marker_color=color, hovertemplate="%{y}: %{x:.1f} pp<extra>" + comp + "</extra>",
        ))
    fig.add_trace(go.Scatter(
        y=d["country"], x=d["Total electricity growth"], mode="markers", name="Total (E)",
        marker=dict(color="#1a1a2e", size=7, symbol="diamond"),
        hovertemplate="%{y}: %{x:.1f} pp<extra>total</extra>",
    ))
    fig.update_layout(
        title="What accounts for electricity-consumption growth, 2000 → 2022",
        barmode="relative",
        xaxis_title="Log growth, percentage points (population + income/person + E/GDP = total)",
        yaxis_title="",
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    return fig


# --------------------------------------------------------------------------- #
# Output 11: generation mix by region, 2022 (OWID continent definitions)
# --------------------------------------------------------------------------- #
def fig_generation_mix_regions() -> go.Figure:
    ow = pd.read_csv(PROD_SOURCE)
    srcs = ["Other renewables", "Bioenergy", "Solar", "Wind", "Hydropower",
            "Nuclear", "Gas", "Oil", "Coal"]
    regions = ["Africa", "Asia", "Europe", "North America", "South America", "Oceania"]

    rows = []
    for region in regions:
        r = ow[ow["Entity"] == region]
        for s in srcs:
            rows.append({"region": region, "source": s, "twh": float(r[r["Year"] == 2022][s].sum())})
    d = pd.DataFrame(rows)
    d["share"] = d["twh"] / d.groupby("region")["twh"].transform("sum") * 100

    fig = px.bar(d, x="share", y="region", color="source",
                 title="Electricity generation mix by region, 2022 (generation, not consumption)",
                 labels={"share": "Share of generation (%)", "region": ""},
                 color_discrete_sequence=px.colors.qualitative.Set1,
                 category_orders={"region": list(reversed(regions))})
    fig.update_layout(template="plotly_white", barmode="stack", xaxis_ticksuffix="%")
    return fig


# --------------------------------------------------------------------------- #
# Output 12: generation mix by region, animated 2000-2022 (A.3 slider)
# --------------------------------------------------------------------------- #
def fig_generation_mix_regions_slider() -> go.Figure:
    ow = pd.read_csv(PROD_SOURCE)
    rows = []
    for region in MIX_REGIONS:
        r = ow[ow["Entity"] == region]
        for yr in range(2000, 2023):
            y = r[r["Year"] == yr]
            tot = float(y[MIX_SOURCES].sum().sum())
            for s in MIX_SOURCES:
                rows.append({"region": region, "year": yr, "source": s,
                             "share": 100 * float(y[s].sum()) / tot if tot else 0.0})
    d = pd.DataFrame(rows)

    fig = px.bar(d, x="region", y="share", color="source",
                 animation_frame="year",
                 title="Electricity generation mix by region, 2000-2022 (generation)",
                 labels={"share": "Share of generation (%)", "region": ""},
                 color_discrete_sequence=px.colors.qualitative.Set1,
                 category_orders={"region": MIX_REGIONS})
    fig.update_layout(template="plotly_white", barmode="stack", yaxis_ticksuffix="%",
                      xaxis_tickangle=-30)
    fig.update_yaxes(range=[0, 100])
    return fig


# --------------------------------------------------------------------------- #
# Output 13: generation mix, largest countries 2022 (A.4)
# --------------------------------------------------------------------------- #
def fig_generation_mix_countries() -> go.Figure:
    ow = pd.read_csv(PROD_SOURCE)
    rows = []
    for country in MIX_COUNTRIES:
        c = ow[(ow["Entity"] == country) & (ow["Year"] == 2022)]
        tot = float(c[MIX_SOURCES].sum().sum())
        for s in MIX_SOURCES:
            rows.append({"country": country, "source": s,
                         "share": 100 * float(c[s].sum()) / tot if tot else 0.0})
    d = pd.DataFrame(rows)
    order = d.groupby("country")["share"].sum().sort_values(ascending=True).index.tolist()

    fig = px.bar(d, x="share", y="country", color="source",
                 title="Electricity generation mix, largest countries 2022 (generation)",
                 labels={"share": "Share of generation (%)", "country": ""},
                 color_discrete_sequence=px.colors.qualitative.Set1,
                 category_orders={"country": order})
    fig.update_layout(template="plotly_white", barmode="stack", xaxis_ticksuffix="%")
    return fig


# --------------------------------------------------------------------------- #
# Output 14: carbon intensity, largest countries 2000-2022 (A.4)
# --------------------------------------------------------------------------- #
def fig_carbon_intensity() -> go.Figure:
    ci = pd.read_csv(CARBON_INTENSITY)
    d = ci[ci["Entity"].isin(MIX_COUNTRIES) & ci["Year"].between(2000, 2022)]
    fig = px.line(d, x="Year", y="Carbon intensity", color="Entity",
                  title="Carbon intensity of electricity, 2000-2022 (gCO₂/kWh)",
                  labels={"Carbon intensity": "gCO₂/kWh", "Year": ""})
    fig.update_layout(template="plotly_white")
    return fig


# --------------------------------------------------------------------------- #
# Output 15: generation vs consumption, world 2022 (A.5)
# --------------------------------------------------------------------------- #
def fig_generation_vs_consumption(df: pd.DataFrame) -> go.Figure:
    ow = pd.read_csv(PROD_SOURCE)
    w = ow[(ow["Entity"] == "World") & (ow["Year"] == 2022)]
    generation = float(w[MIX_SOURCES].sum().sum())
    consumption = float(df[df["year"] == 2022]["FEC"].sum())
    gap = generation - consumption
    gap_pct = 100 * gap / generation

    d = pd.DataFrame({
        "Quantity": ["Generation", "Final consumption"],
        "TWh": [generation, consumption],
    })
    fig = px.bar(d, x="Quantity", y="TWh", color="Quantity",
                 title="World electricity: generation vs final consumption, 2022",
                 labels={"TWh": "TWh", "Quantity": ""},
                 color_discrete_map={"Generation": "#1f77b4", "Final consumption": "#2ca02c"})
    fig.update_layout(template="plotly_white", showlegend=False)
    fig.add_annotation(
        x=0.5, y=max(generation, consumption),
        text=f"gap {gap:,.0f} TWh ({gap_pct:.0f}%) = losses + own-use + net trade",
        showarrow=False, yshift=12, font=dict(size=12, color="#5b6070"),
    )
    return fig


# --------------------------------------------------------------------------- #
# Output 16: consumption vs population vs GDP growth (B.5 simpler comparison)
# --------------------------------------------------------------------------- #
def fig_consumption_comparison(df: pd.DataFrame) -> go.Figure:
    pop = _wb_series(POP_JSON)
    gdp = _wb_series(GDP_JSON)
    rows = []
    for label, code, iso3 in DRIVER_COUNTRIES:
        e = df[(df["code"] == code) & (df["year"].isin([2000, 2022]))].set_index("year")["FEC"]
        p00, p22 = pop.get((iso3, 2000)), pop.get((iso3, 2022))
        g00, g22 = gdp.get((iso3, 2000)), gdp.get((iso3, 2022))
        if None in (p00, p22, g00, g22) or 2000 not in e.index or 2022 not in e.index:
            continue
        rows.append({"country": label,
                     "Electricity (E)": np.log(e[2022] / e[2000]) * 100,
                     "Population": np.log(p22 / p00) * 100,
                     "GDP": np.log(g22 / g00) * 100})
    d = pd.DataFrame(rows).melt(id_vars="country", var_name="metric", value_name="growth_pp")
    order = (d[d["metric"] == "Electricity (E)"].set_index("country")["growth_pp"]
             .sort_values().index.tolist())

    fig = px.bar(d, x="growth_pp", y="country", color="metric", barmode="group",
                 orientation="h", category_orders={"country": order},
                 title="Consumption growth vs population and GDP growth, 2000→2022",
                 labels={"growth_pp": "Log growth, percentage points", "country": ""},
                 color_discrete_map={"Electricity (E)": "#1a1a2e", "Population": "#66c2a5",
                                     "GDP": "#fc8d62"})
    fig.update_layout(template="plotly_white")
    return fig


# --------------------------------------------------------------------------- #
# Output 17: per-capita electricity vs per-capita GDP, 2022 (B.2)
# --------------------------------------------------------------------------- #
ISO3_FALLBACK = {"251": "FRA", "579": "NOR"}


def _country_iso3() -> dict[str, str]:
    cr = pd.read_csv(DATASETS / "country_region.csv", dtype={"code": str})
    m = cr.set_index("code")["iso3"].to_dict()
    m.update(ISO3_FALLBACK)
    return m


def fig_percapita_scatter(df: pd.DataFrame) -> go.Figure:
    pop = _wb_series(POP_JSON)
    gdp = _wb_series(GDP_JSON)
    iso3 = _country_iso3()

    rows = []
    for _, r in df[df["year"] == 2022].iterrows():
        iso = iso3.get(r["code"])
        if not iso:
            continue
        p = pop.get((iso, 2022))
        g = gdp.get((iso, 2022))
        if not p or not g:
            continue
        rows.append({"country": r["area"], "region": r["region"],
                     "electricity_per_capita_kwh": r["FEC"] * 1e9 / p,
                     "gdp_per_capita_usd": g / p})
    d = pd.DataFrame(rows)

    fig = px.scatter(d, x="gdp_per_capita_usd", y="electricity_per_capita_kwh",
                     color="region", hover_name="country", log_x=True, log_y=True,
                     title="Electricity use vs income per person, 2022 (association, not causation)",
                     labels={"gdp_per_capita_usd": "GDP per person (2011 intl $, log)",
                             "electricity_per_capita_kwh": "Electricity per person (kWh, log)",
                             "region": "Region"})
    fig.update_layout(template="plotly_white")
    return fig


# --------------------------------------------------------------------------- #
# Output 18: Kaya decomposition waterfall, China (B.3 method illustration)
# --------------------------------------------------------------------------- #
def fig_kaya_waterfall(df: pd.DataFrame) -> go.Figure:
    tab = drivers_decomposition_data(df)
    china = tab[tab["country"] == "China"].iloc[0]
    fig = go.Figure(go.Waterfall(
        x=["Population", "Income per person", "Efficiency (E/GDP)", "Total E growth"],
        measure=["relative", "relative", "relative", "total"],
        y=[china["population_pp"], china["income_per_person_pp"],
           china["e_gdp_pp"], china["total_growth_pp"]],
        connector=dict(line=dict(color="#c8c8d0")),
        increasing=dict(marker=dict(color="#66c2a5")),
        decreasing=dict(marker=dict(color="#fc8d62")),
        totals=dict(marker=dict(color="#1a1a2e")),
        text=[f"{v:+.1f}" for v in (china["population_pp"], china["income_per_person_pp"],
                                    china["e_gdp_pp"], china["total_growth_pp"])],
        textposition="outside",
    ))
    fig.update_layout(
        title="Kaya decomposition, China 2000→2022 (E = population × income/person × E/GDP)",
        yaxis_title="Log growth, percentage points",
        template="plotly_white",
    )
    return fig


# --------------------------------------------------------------------------- #
# Slider variants (dashboard): year-by-year granularity for the year-vs-year
# comparison charts. Used only in the dashboard; the static PNGs keep the
# 1990-vs-2022 / 2000-vs-2022 view for the report.
# --------------------------------------------------------------------------- #
def fig_sector_structure_slider(df: pd.DataFrame) -> go.Figure:
    rows = []
    for yr in range(1990, 2023):
        d = df[df["year"] == yr]
        tot = d[SECTORS].sum().sum()
        for s in SECTORS:
            rows.append({"year": yr, "sector": s, "share": 100 * d[s].sum() / tot})
    dd = pd.DataFrame(rows)
    fig = px.bar(dd, x="sector", y="share", color="sector", animation_frame="year",
                 title="World electricity consumption by sector, 1990-2022",
                 labels={"share": "Share of total (%)", "sector": ""},
                 color_discrete_sequence=px.colors.qualitative.Set2)
    fig.update_layout(template="plotly_white", showlegend=False, yaxis_ticksuffix="%")
    fig.update_yaxes(range=[0, 60])
    return fig


def fig_generation_mix_slider() -> go.Figure:
    ow = pd.read_csv(PROD_SOURCE)
    world = ow[ow["Entity"] == "World"]
    rows = []
    for yr in range(2000, 2023):
        w = world[world["Year"] == yr]
        for s in MIX_SOURCES:
            rows.append({"year": yr, "source": s, "share": float(w[s].sum())})
    d = pd.DataFrame(rows)
    d["share"] = 100 * d["share"] / d.groupby("year")["share"].transform("sum")
    fig = px.bar(d, x="source", y="share", color="source", animation_frame="year",
                 title="World electricity generation mix, 2000-2022",
                 labels={"share": "Share of generation (%)", "source": ""},
                 color_discrete_sequence=px.colors.qualitative.Set1)
    fig.update_layout(template="plotly_white", showlegend=False, yaxis_ticksuffix="%")
    fig.update_yaxes(range=[0, 45])
    return fig


def fig_generation_mix_countries_slider() -> go.Figure:
    ow = pd.read_csv(PROD_SOURCE)
    rows = []
    for yr in range(2000, 2023):
        for country in MIX_COUNTRIES:
            c = ow[(ow["Entity"] == country) & (ow["Year"] == yr)]
            tot = float(c[MIX_SOURCES].sum().sum())
            for s in MIX_SOURCES:
                rows.append({"country": country, "year": yr, "source": s,
                             "share": 100 * float(c[s].sum()) / tot if tot else 0.0})
    d = pd.DataFrame(rows)
    fig = px.bar(d, x="share", y="country", color="source", animation_frame="year",
                 title="Electricity generation mix, largest countries 2000-2022",
                 labels={"share": "Share of generation (%)", "country": ""},
                 color_discrete_sequence=px.colors.qualitative.Set1,
                 category_orders={"country": MIX_COUNTRIES})
    fig.update_layout(template="plotly_white", barmode="stack", xaxis_ticksuffix="%")
    fig.update_xaxes(range=[0, 100])
    return fig


def main() -> int:
    df = load_country_year()
    reg = load_region_year()

    figures = {
        "output_1_global_trend.png": fig_global_trend(df),
        "output_2_top10_consumers.png": fig_top10(df),
        "output_3_regional_trends.png": fig_regional(reg),
        "output_4_sector_structure.png": fig_sector_structure(df),
        "output_5_share_change.png": fig_share_change(df),
        "output_6_map_1990.png": fig_map_1990(df),
        "output_7_map_2022.png": fig_map_2022(df),
        "output_8_generation_mix.png": fig_generation_mix(),
        "output_10_drivers_decomposition.png": fig_drivers_decomposition(df),
        "output_11_generation_mix_regions.png": fig_generation_mix_regions(),
        "output_12_generation_mix_regions_slider.png": fig_generation_mix_regions_slider(),
        "output_13_generation_mix_countries.png": fig_generation_mix_countries(),
        "output_14_carbon_intensity.png": fig_carbon_intensity(),
        "output_15_generation_vs_consumption.png": fig_generation_vs_consumption(df),
        "output_16_consumption_comparison.png": fig_consumption_comparison(df),
        "output_17_percapita_scatter.png": fig_percapita_scatter(df),
        "output_18_kaya_waterfall.png": fig_kaya_waterfall(df),
    }

    FIGURES.mkdir(parents=True, exist_ok=True)
    for name, fig in figures.items():
        fig.write_image(FIGURES / name, **PNG_SIZE)
        print(f"[png] {name}")

    # self-contained slider HTML
    slider = fig_map_slider(df)
    html = slider.to_html(include_plotlyjs=True, full_html=True, div_id="map-slider")
    (FIGURES / "output_6_7_slider.html").write_text(html, encoding="utf-8")
    print(f"[html] output_6_7_slider.html ({len(html)} bytes)")

    # sanity numbers for captions
    w90 = df[df["year"] == 1990]["FEC"].sum()
    w22 = df[df["year"] == 2022]["FEC"].sum()
    fixed = set(df[df["year"] == 1990]["code"])
    f22 = df[(df["code"].isin(fixed)) & (df["year"] == 2022)]["FEC"].sum()
    miss90 = df[(df["year"] == 1990) & df["Industry"].isna()]["code"].nunique()
    miss22 = df[(df["year"] == 2022) & df["Industry"].isna()]["code"].nunique()
    print(f"world FEC 1990={w90:.1f} 2022={w22:.1f}  fixed-sample 2022={f22:.1f} "
          f"({len(fixed)} countries)")
    print(f"missing Industry: 1990={miss90} 2022={miss22}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
