"""Generate the eight proposal figures (PNG + interactive HTML).

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
    }

    FIGURES.mkdir(parents=True, exist_ok=True)
    for name, fig in figures.items():
        fig.write_image(FIGURES / name, **PNG_SIZE)
        print(f"[png] {name}")

    # self-contained slider HTML
    slider = fig_map_slider(df)
    html = slider.to_html(include_plotlyjs=True, full_html=True)
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
