"""Build the two report DOCX files (answers + technical findings).

Produces, in ``Docs/``:

* ``Question_A_B_Answers.docx`` — the generation-mix (A) and drivers (B) answers,
  with the figures and tables.
* ``Data_Consistency_Technical_Findings.docx`` — the supplementary-source
  verification, robustness, sensitivity, pipeline review, validation,
  reproducibility and technical explanations.

Run from the repo root: ``python team03/build_docs.py``. PDF conversion is done
separately with Word/LibreOffice (the DOCX is the source of truth).
"""

from __future__ import annotations

import sys
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor

REPO_ROOT = Path(__file__).resolve().parent.parent
FIGURES = REPO_ROOT / "Figures"
DOCS = REPO_ROOT / "Docs"

ACCENT = RGBColor(0x1A, 0x1A, 0x2E)


def _doc() -> Document:
    d = Document()
    st = d.styles["Normal"]
    st.font.name = "Calibri"
    st.font.size = Pt(10.5)
    return d


def _title(d: Document, text: str, subtitle: str = "") -> None:
    d.add_heading(text, level=0)
    if subtitle:
        p = d.add_paragraph()
        r = p.add_run(subtitle)
        r.italic = True
        r.font.color.rgb = RGBColor(0x5B, 0x60, 0x70)


def _h(d: Document, text: str, level: int = 1) -> None:
    d.add_heading(text, level=level)


def _p(d: Document, text: str, bold: bool = False) -> None:
    p = d.add_paragraph()
    r = p.add_run(text)
    r.bold = bold


def _bullet(d: Document, text: str) -> None:
    d.add_paragraph(text, style="List Bullet")


def _table(d: Document, headers: list[str], rows: list[list[str]]) -> None:
    t = d.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    for i, h in enumerate(headers):
        cell = t.rows[0].cells[i]
        cell.text = h
        for para in cell.paragraphs:
            for run in para.runs:
                run.bold = True
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = v


def _fig(d: Document, name: str, width_in: float = 6.3, caption: str = "") -> None:
    path = FIGURES / name
    if not path.exists():
        _p(d, f"[missing figure: {name}]")
        return
    d.add_picture(str(path), width=Inches(width_in))
    d.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    if caption:
        c = d.add_paragraph()
        r = c.add_run(caption)
        r.italic = True
        r.font.size = Pt(9)
        r.font.color.rgb = RGBColor(0x5B, 0x60, 0x70)
        c.alignment = WD_ALIGN_PARAGRAPH.CENTER


# --------------------------------------------------------------------------- #
# DOCX 1 — Question A & B
# --------------------------------------------------------------------------- #
def build_answers_docx() -> None:
    d = _doc()
    _title(d, "Question A & B — How is electricity produced, and why did consumption change?",
           "CISC7204 Team 03 · The Power-Hungry World · 1990–2022")

    _p(d, "Two review questions, answered from OWID generation/carbon-intensity data and "
          "World Bank population/GDP, cross-referenced against the UN final-consumption "
          "pipeline. All figures are in Figures/ and reproduced in this document.")

    _h(d, "The questions", level=1)
    _p(d, "A. Fuel by fuel generation mix: how is the electricity produced?", bold=True)
    _bullet(d, "OWID has electricity generated from coal, gas, oil, nuclear, hydro, solar, wind, "
              "biofuel and other renewables, as amounts and as shares of generation, plus the "
              "carbon intensity of electricity. Units and years for these columns still need "
              "confirming in the codebook.")
    _bullet(d, "Compare each fuel's share for the world, the regions and the largest countries in "
              "2000 and 2022, and how fast each fuel grew.")
    _bullet(d, "Generation is not consumption. It includes losses and trade, so it stays out of the "
              "sector shares, and we would show the two side by side and say so.")
    _bullet(d, "The IEA file may offer a longer series through its electricity output rows. We have "
              "not checked whether those rows split by fuel in the free file.")
    _p(d, "B. Why did consumption change? Associations, not proof of causes", bold=True)
    _bullet(d, "This data cannot prove causes. It has no prices, policies, technology costs or "
              "weather, and it is observational, so we can describe patterns but not show that one "
              "thing caused another.")
    _bullet(d, "What we can do is relate consumption to population and income. OWID has both for the "
              "eleven large countries we checked, including China, the United States, India, Russia "
              "and Japan. GDP is missing for 55 of 220 countries and territories in 2022, mostly "
              "small islands, and it is measured in international dollars at 2011 prices, ending in 2022.")
    _bullet(d, "A decomposition splits growth in electricity use into three arithmetic parts: "
              "population growth, income per person, and electricity used per unit of GDP. It "
              "describes what accounts for the change, and it does not say why each part moved.")
    _bullet(d, "Results are reported as consistent with an explanation, never as proof, and we list "
              "the data a real test would need, such as electricity prices and electrification policies.")
    _bullet(d, "The group should decide whether to do the decomposition, or only the simpler "
              "comparison of consumption growth against population and GDP growth.")

    _h(d, "Summary", level=1)
    _p(d, "A — The world still runs mostly on coal + gas (58% of generation in 2022), but the "
          "fastest growth is wind and solar (≈0.2% → ≈12%). China and India are coal-led; "
          "Europe and North America swapped coal for gas + wind/solar; Brazil, Canada and France "
          "are hydro/nuclear-based and low-carbon. Generation (28,918 TWh) is not consumption "
          "(24,936 TWh): the ~14% gap is losses, own-use and trade.")
    _p(d, "B — The Kaya decomposition (E = P × GDP/P × E/GDP) shows income-per-person and "
          "electricity-per-GDP dominate consumption growth, while population is the smallest "
          "component. China/India/Indonesia grew via income + electrification; the US, Europe and "
          "Japan grew little or fell because efficiency (E/GDP) cancelled income growth. These are "
          "associations, not proof of causes.")

    # ---- A -----------------------------------------------------------------
    _h(d, "A. Fuel-by-fuel generation mix — how is electricity produced?", level=1)

    _h(d, "A.1 Data, units, years (confirmed)", level=2)
    _bullet(d, "Source: OWID electricity-prod-source-stacked.csv (cached "
              "Datasets/owid_electricity_prod_source.csv).")
    _bullet(d, "Units: TWh per fuel per year; carbon intensity in gCO₂/kWh "
              "(OWID carbon-intensity-electricity.csv).")
    _bullet(d, "9 fuels: Coal, Gas, Oil, Nuclear, Hydropower, Wind, Solar, Bioenergy, "
              "Other renewables. Coverage 1900–2025, 249 entities.")
    _bullet(d, "This is generation, not final consumption (see A.5).")

    _h(d, "A.2 World: 2000 → 2022", level=2)
    _p(d, "World generation rose 15,279 → 28,918 TWh (+89%).")
    _table(d, ["Fuel", "2000 share", "2022 share", "Amount 2000→2022 (TWh)", "Growth"],
           [["Coal", "38.0%", "35.4%", "5,809 → 10,240", "+76%"],
            ["Gas", "18.0%", "22.9%", "2,746 → 6,628", "+141%"],
            ["Oil", "8.7%", "3.1%", "1,324 → 887", "−33%"],
            ["Nuclear", "16.6%", "9.1%", "2,540 → 2,640", "+4%"],
            ["Hydropower", "17.2%", "15.0%", "2,630 → 4,324", "+64%"],
            ["Wind", "0.2%", "7.3%", "31 → 2,108", "+6,666%"],
            ["Solar", "0.0%", "4.6%", "1 → 1,333", "+130,000%"],
            ["Bioenergy", "1.0%", "2.3%", "154 → 669", "+334%"],
            ["Other renewables", "0.3%", "0.3%", "44 → 88", "+101%"]])
    _p(d, "Headline: the world still runs mostly on coal + gas (58% in 2022), but the "
          "fastest growth is wind and solar (≈0.2% → ≈12%).")
    _fig(d, "output_8_generation_mix.png", caption="Figure A.2 — World generation mix, 2000 vs 2022.")

    _h(d, "A.3 Regions: 2000 → 2022 (OWID continent definitions)", level=2)
    _table(d, ["Region", "Total growth", "2022 dominant mix", "Notable shift"],
           [["Africa", "+109%", "Gas 43%, Coal 26%, Hydro 18%", "coal share halved, gas tripled"],
            ["Asia", "+238%", "Coal 51%, Gas 17%, Hydro 12%", "coal absolute +291%, solar/wind ~0→~10%"],
            ["Europe", "+9%", "Gas 26%, Nuclear 21%, Coal 15%", "coal −40%, wind→11%, solar→5%"],
            ["North America", "+15%", "Gas 37%, Coal 16%, Nuclear 16%", "coal −58%, gas +187%, wind→9%"],
            ["South America", "+77%", "Hydro 56%, Gas 16%, Wind 9%", "hydro dominant throughout"],
            ["Oceania", "+25%", "Coal 40%, Gas 17%, Hydro 14%, Solar 12%", "coal −28%, solar→12%"]])
    _p(d, "OWID splits the Americas into North + South; the project's own region column "
          "merges them into one 'Americas'.")
    _fig(d, "output_11_generation_mix_regions.png", caption="Figure A.3a — Generation mix by region, 2022.")
    _fig(d, "output_12_generation_mix_regions_slider.png",
         caption="Figure A.3b — Region mix, 2000–2022 (animated slider; see Figures/output_6_7_slider-style HTML).")

    _h(d, "A.4 Largest countries: 2000 → 2022", level=2)
    _table(d, ["Country", "Total growth", "2022 mix (top 4 by share)"],
           [["China", "+553%", "Coal 61%, Hydro 15%, Wind 9%, Solar 5%"],
            ["United States", "+13%", "Gas 39%, Coal 19%, Nuclear 18%, Wind 10%"],
            ["India", "+216%", "Coal 74%, Hydro 10%, Solar 5%, Wind 4%"],
            ["Japan", "−5%", "Gas 36%, Coal 34%, Solar 9%, Hydro 7%"],
            ["Russia", "+33%", "Gas 46%, Nuclear 19%, Hydro 17%, Coal 16%"],
            ["Brazil", "+94%", "Hydro 63%, Wind 12%, Bioenergy 8%, Gas 6%"],
            ["South Korea", "+114%", "Coal 34%, Nuclear 28%, Gas 28%, Solar 5%"],
            ["Canada", "+10%", "Hydro 60%, Gas 14%, Nuclear 13%, Wind 6%"],
            ["Germany", "−0%", "Coal 32%, Wind 22%, Gas 14%, Solar 11%"],
            ["France", "−12%", "Nuclear 63%, Gas 10%, Hydro 10%, Wind 8%"]])
    _p(d, "Carbon intensity (gCO₂/kWh, 2000 → 2022): World 527→490 (−7%); China 784→587 (−25%); "
          "US 608→410 (−32%); Germany 573→420 (−27%); India 740→706 (−5%); Japan 424→520 "
          "(+22%, post-Fukushima coal/gas); France 80→79; Brazil 89→103.")
    _fig(d, "output_13_generation_mix_countries.png", caption="Figure A.4a — Generation mix, largest countries 2022.")
    _fig(d, "output_14_carbon_intensity.png", caption="Figure A.4b — Carbon intensity of electricity, 2000–2022.")

    _h(d, "A.5 Generation vs consumption — side by side", level=2)
    _p(d, "Generation is not consumption. 2022: world generation 28,918 TWh vs final "
          "consumption (FEC) 24,936 TWh; the gap (3,982 TWh, ~14%) is transmission/"
          "distribution losses, plant own-use and net trade. This is why generation stays "
          "out of the sector shares.")
    _fig(d, "output_15_generation_vs_consumption.png", caption="Figure A.5 — Generation vs final consumption, 2022.")

    _h(d, "A.6 IEA free file", level=2)
    _p(d, "Not yet checked whether the free IEA file's electricity output rows split by fuel. "
          "The original IEA files are not redistributable, so any IEA data can only be cited, "
          "not committed.")

    # ---- B -----------------------------------------------------------------
    d.add_page_break()
    _h(d, "B. Why did consumption change? — associations, not proof of causes", level=1)

    _h(d, "B.1 Framing", level=2)
    _p(d, "The data is observational: no prices, policies, technology costs or weather. It can "
          "describe patterns and associations, but not demonstrate causation. Results are "
          "reported as 'consistent with' an explanation, never as proof.")

    _h(d, "B.2 What we can relate consumption to", level=2)
    _bullet(d, "Population: World Bank SP.POP.TOTL.")
    _bullet(d, "Income: World Bank NY.GDP.MKTP.PP.KD (GDP, international $, constant prices, "
              "ending 2022). GDP is missing for 55 of 220 countries/territories in 2022 (mostly "
              "small islands).")
    _bullet(d, "Both are available for the eleven large consumers checked.")
    _fig(d, "output_17_percapita_scatter.png",
         caption="Figure B.2 — Electricity use vs income per person, 2022 (association, not causation).")

    _h(d, "B.3 Decomposition (Kaya identity for electricity)", level=2)
    _p(d, "E = P × (GDP/P) × (E/GDP), where P = population, GDP/P = income per person, "
          "E/GDP = electricity per unit of GDP (intensity). Taking log growth, the total splits "
          "exactly and additively:")
    _p(d, "g_E = g_population + g_income-per-person + g_electricity-per-GDP", bold=True)
    _p(d, "Each part is arithmetic, not causal: it says how much each term accounts for, not why "
          "the term moved.")
    _fig(d, "output_18_kaya_waterfall.png",
         caption="Figure B.3 — Kaya decomposition for China, 2000→2022 (method illustration).")

    _h(d, "B.4 Results, 2000 → 2022 (log growth, percentage points; E = final consumption)", level=2)
    _table(d, ["Country", "E growth", "Population", "Income/person", "E/GDP"],
           [["China", "+196.0", "+11.2", "+166.5", "+18.2"],
            ["India", "+148.9", "+29.8", "+102.0", "+17.1"],
            ["Indonesia", "+131.2", "+25.5", "+78.9", "+26.8"],
            ["South Korea", "+72.2", "+9.5", "+70.1", "−7.4"],
            ["Brazil", "+54.0", "+18.9", "+28.1", "+6.9"],
            ["Russia", "+30.2", "−1.6", "+65.9", "−34.1"],
            ["Canada", "+21.3", "+23.8", "+19.1", "−21.7"],
            ["United States", "+13.5", "+16.9", "+28.0", "−31.3"],
            ["France", "+7.5", "+11.3", "+15.6", "−19.3"],
            ["Germany", "−1.3", "+1.2", "+24.4", "−26.9"],
            ["Japan", "−7.5", "−1.4", "+16.4", "−22.6"]])
    _p(d, "China/India/Indonesia: income grew fast AND E/GDP rose (electrification catching up) → "
          "consumption roughly tripled. US/Japan/Germany/France/Canada: E/GDP fell sharply "
          "(efficiency/decoupling), cancelling income growth. Population is the smallest "
          "component everywhere.")
    _fig(d, "output_10_drivers_decomposition.png", caption="Figure B.4 — Decomposition across the eleven countries.")

    _h(d, "B.5 Decision: decomposition vs simpler comparison", level=2)
    _p(d, "Recommendation: do the full decomposition (it answers 'what accounts for the change' "
          "directly) AND present it alongside the simpler comparison of consumption vs population "
          "vs GDP growth.")
    _fig(d, "output_16_consumption_comparison.png",
         caption="Figure B.5 — Consumption vs population vs GDP growth, 2000–2022 (the simpler comparison).")

    # ---- method steps ------------------------------------------------------
    d.add_page_break()
    _h(d, "Solution method steps", level=1)
    steps = [
        "Confirmed OWID column units (TWh per fuel; carbon intensity gCO₂/kWh) and coverage.",
        "Summed the nine fuel columns for World, the six OWID continents, and the ten largest countries, for 2000 and 2022.",
        "Normalised to 100% shares and computed growth rates.",
        "Loaded World Bank population (SP.POP.TOTL) and GDP PPP (NY.GDP.MKTP.PP.KD); verified the Kaya log-growth decomposition sums exactly (residual 0.0 pp per country).",
        "Built every figure in make_figures.py (plotly → PNG → dashboard) and embedded them in this document.",
        "For B, framed all results as associations only; listed the data a causal test would need (prices, policy, technology cost, weather).",
    ]
    for i, s in enumerate(steps, 1):
        d.add_paragraph(f"{i}. {s}")

    DOCS.mkdir(parents=True, exist_ok=True)
    out = DOCS / "Question_A_B_Answers.docx"
    d.save(str(out))
    print(f"[docx] {out.name}")


# --------------------------------------------------------------------------- #
# DOCX 2 — Data consistency / robustness / sensitivity / review
# --------------------------------------------------------------------------- #
def build_technical_docx() -> None:
    d = _doc()
    _title(d, "Data Consistency, Robustness, Sensitivity & Technical Findings",
           "CISC7204 Team 03 · The Power-Hungry World · supplementary source verification and review")

    _h(d, "1. Data consistency & supplementary source verification", level=1)
    _p(d, "The core invariant — Industry + Transport + Residential + Services/Other == FEC "
          "(B25_FEC) — holds for 6,932/6,932 country-years (100%). A missing sector row usually "
          "re-assigns electricity between sectors rather than losing it; the one exception is "
          "Pakistan 1990–1992, where the published total itself omitted industry.")

    _h(d, "1.1 The four applied data decisions", level=2)
    _table(d, ["#", "Decision", "Change", "Magnitude"],
           [["1", "Germany 1990 (linked AGEB estimate)", "adds a missing country-year", "+463 TWh to world 1990 (5.6%)"],
            ["2", "Pakistan 1990–92 (recompute FEC, add industry)", "fixes a total that omitted industry", "+10.3/+11.2/+12.3 TWh (~0.1%)"],
            ["3", "Pakistan 2017–22 transport = 0 (reported nil)", "sector split only", "0 TWh (FEC unchanged)"],
            ["4", "Indonesia 2000–07 + 2016 transport (HEESI fills)", "sector split only", "0 TWh (FEC unchanged)"]])

    _h(d, "1.2 Pakistan — the priority (resolved)", level=2)
    _bullet(d, "Industry 1990–92: UNdata's published FEC (18.45/20.30/21.59) omitted industry. "
              "Filled industry from the State Bank of Pakistan (10.3/11.2/12.3) and recomputed FEC "
              "to 28.75/31.50/33.89; fixes the fake 1992→1993 jump (+69% → +7.7%). flag_fec_recomputed=1.")
    _bullet(d, "Transport 2017–19 = 0: SBP Table 2.3 records traction '–' (nil). The 2019-20 row's "
              "non-traction components do not reconcile to its total (−10,001 GWh), but the traction "
              "cell is unambiguously nil. flag_reported_nil=1.")
    _bullet(d, "Transport 2020–22 = 0 (sourced): Pakistan Railways Yearbook 2023-24 'Fuel consumption' "
              "table records electric energy = Nil for FY 2020-21/21-22/22-23 (electric-locomotive "
              "service suspended). Now a sourced value, not a convention.")
    _bullet(d, "Year convention: UNdata year Y = SBP fiscal year (Y−1)–Y up to 2001, then Y–(Y+1) from "
              "2002; FY 2001-02 is absent.")

    _h(d, "1.3 Remaining gap countries (documented, not filled)", level=2)
    _table(d, ["Country", "Gap", "Decision", "Reason"],
           [["Indonesia", "Transport 1990–2007, 2016", "Accepted (applied)", "UNdata == HEESI for 2008–14; filled 9 values"],
            ["Malaysia", "Transport 1990–96", "Documented missing", "NEB 2012 reports transport '–' before 2006"],
            ["Saudi Arabia", "Transport (ABSENT)", "Unresolved", "no transport category in any source"],
            ["Iran", "Transport 1990–98", "Not accessible", "Persian only"],
            ["Bangladesh", "Transport 1990–2020", "Assessed", "diesel railway; MRT opened Dec 2022"],
            ["Viet Nam", "Transport 1995–2022", "Rejected", "EVN = sales, no transport category"],
            ["Thailand", "Transport 1990–98", "Not accessible / rejected", "DEDE unreachable; EPPO = sales"],
            ["Egypt", "Transport 1990–2011", "Rejected", "sales, fiscal years, no transport"],
            ["UAE", "Transport (ABSENT)", "Rejected", "no transport category; DEWA Dubai only"]])

    _h(d, "2. Sector-level robustness checks", level=1)
    _table(d, ["Check", "Result", "Interpretation"],
           [["Four-sector sum == FEC", "6,932 / 6,932 (100%)", "reconcile holds after all fills"],
            ["B47_123 parent aggregate in raw data", "No", "never added; no double count"],
            ["Services_Other recomputed vs stored", "max diff 0.0000 TWh", "3 components sum correctly"],
            ["Areas missing Industry (1990 / 2022)", "21 / 15 areas, 2.7 / 4.1 TWh (0.03%)", "gap 0.00 TWh → Output 4 not understated"]])

    _h(d, "3. Sensitivity of the four decisions", level=1)
    _table(d, ["Scenario", "World FEC 1990", "World FEC 2022", "Fixed sample", "2022 top-30", "1990 Industry"],
           [["All decisions (base)", "8,275.2", "24,936.3", "179", "88.6%", "44.92%"],
            ["No Germany 1990", "7,811.8", "24,936.3", "178", "88.6%", "44.64%"],
            ["No Pakistan 1990–92 industry", "8,264.9", "24,936.3", "179", "88.6%", "44.85%"],
            ["No Pakistan transport 2017–22", "8,275.2", "24,936.3", "179", "88.6%", "44.92%"],
            ["No Indonesia transport fills", "8,275.2", "24,936.3", "179", "88.6%", "44.92%"]])
    _p(d, "Only Germany 1990 moves a headline aggregate (−5.6% on world 1990), and only in 1990. "
          "The other three decisions move world FEC <0.15% or not at all, and none affects 2022. "
          "The conclusions are not artefacts of the data decisions.")

    _h(d, "4. Pipeline review", level=1)
    _p(d, "Nine scripts, each with a clear input→output contract, caching, and error handling: "
          "download (cached, fallback) → parse (excludes B47_123) → mappings (combined codes, "
          "UN_A3 link) → analysis (4 flagged decisions) → supplementary (gap table + register) → "
          "sensitivity (counterfactuals + robustness) → validate (4 layers) → figures (18) → "
          "dashboard (web). No dead code, no TODOs, no stubs.")

    _h(d, "5. Validation results (re-run, confirmed)", level=1)
    _table(d, ["Layer", "Result"],
           [["1 Internal consistency", "sector-sum == FEC 6,932/6,932 (100%); region sum == World 0.0 TWh"],
            ["2 Cross-dataset (OWID 2022)", "China 0.928, Germany 0.884, Japan 0.867, Korea 0.870, Indonesia 0.880; India 0.778 flagged"],
            ["3 Headline numbers", "218 areas; top-30 = 88.6%; 36,247 observations"],
            ["4 Duplicate-count", "250/380/578/756 absent; 840 (US) and 076 (Brazil) present"]])

    _h(d, "6. Reproducibility", level=1)
    _p(d, "The whole pipeline was re-run end-to-end and diffed against the committed files. Data "
          "steps (1–4.6, 5) and the 18 PNGs + dashboard pages are byte-identical. One finding: "
          "Figures/output_6_7_slider.html was not byte-identical because Plotly's to_html() assigned "
          "a random container div_id (UUID) each run — the chart data was identical, only three lines "
          "differed. Fixed by pinning div_id='map-slider'.")

    _h(d, "7. Technical explanations (report / PPT)", level=1)
    _bullet(d, "Unit: SDMX UNIT reads 'HSO' but OBS_VALUE is TJ; TWh = OBS_VALUE / 3600.")
    _bullet(d, "Sectors: Industry B26_121, Transport B40_122, Residential B50_1231, Services/Other = "
              "B48_1232 + B49_1235 + B51_1234; never add B47_123.")
    _bullet(d, "Combined codes: data-bearing 251/382/579/757; 250/380/578/756 return 404; choropleth "
              "keys on UN_A3 with 251→250 etc.")
    _bullet(d, "Fixed sample: 179 countries present in 1990 (Germany added back); ex-Soviet states "
              "appear only from 1992.")
    _bullet(d, "Generation ≠ consumption: 28,918 vs 24,936 TWh (gap ~14% = losses + own-use + trade).")
    _bullet(d, "Associations, not causes: the Kaya decomposition is arithmetic and observational.")

    _fig(d, "output_1_global_trend.png", width_in=6.0,
         caption="Context — global trend; the Germany-1990 decision moves only the 1990 point.")
    _fig(d, "output_4_sector_structure.png", width_in=6.0,
         caption="Context — sector structure; the missing-Industry areas are 0.03% of world FEC.")

    _h(d, "References", level=1)
    refs = [
        "UNSD SDMX dataflow — https://data.un.org/WS/rest/dataflow/UNSD/DF_UNData_EnergyBalance/latest",
        "UNSD data query (B07_EL, seven transactions) — https://data.un.org/WS/rest/data/UNSD,DF_UNData_EnergyBalance,1.0/.B07_EL.B25_FEC+B26_121+B40_122+B50_1231+B48_1232+B49_1235+B51_1234.HSO?startPeriod=1990&endPeriod=2023",
        "UN CL_AREA code list — https://data.un.org/WS/rest/codelist/UNSD/CL_AREA/1.0",
        "OWID electricity demand — https://ourworldindata.org/grapher/electricity-demand.csv",
        "OWID electricity production by source — https://ourworldindata.org/grapher/electricity-prod-source-stacked.csv",
        "OWID carbon intensity of electricity — https://ourworldindata.org/grapher/carbon-intensity-electricity.csv",
        "Natural Earth 50m countries — https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_50m_admin_0_countries.geojson",
        "World Bank population (SP.POP.TOTL) — https://api.worldbank.org/v2/country/all/indicator/SP.POP.TOTL?format=json&per_page=30000&date=1990:2022",
        "World Bank GDP PPP (NY.GDP.MKTP.PP.KD) — https://api.worldbank.org/v2/country/all/indicator/NY.GDP.MKTP.PP.KD?format=json&per_page=30000&date=1990:2022",
        "AGEB (Germany 1990, EBD24e) — https://ag-energiebilanzen.de/wp-content/uploads/EBD24e_Auswertungstabellen_english.pdf",
        "State Bank of Pakistan Handbook, Table 2.3 — https://archive.sbp.org.pk/departments/stats/pakEconomy_HandBook/Chap-2.3.pdf",
        "NEPRA State of Industry Report 2021 — https://www.nepra.org.pk/publications/State%20of%20Industry%20Reports/State%20of%20Industry%20Report%202021.pdf",
        "Pakistan Railways Yearbook 2023-24 (electric energy = Nil) — http://pakrail.gov.pk/images/yearbook/yearbook2023_24.pdf",
        "ESDM HEESI 2012 — https://www.esdm.go.id/assets/media/content/content-handbook-of-energy-economic-statistics-of-indonesia-2012-dcexnjb.pdf",
        "ESDM HEESI 2018 final — https://www.esdm.go.id/assets/media/content/content-handbook-of-energy-and-economic-statistics-of-indonesia-2018-final-edition.pdf",
        "Malaysia NEB 2012 (archived) — https://web.archive.org/web/20220725103818/https://www.st.gov.my/en/contents/publications/statistics_electricity/National%20Energy%20Balance%202012.pdf",
        "GASTAT use policy — https://stats.gov.sa/en/use-policy",
        "Dhaka MRT Line-6 opening (Bangladesh) — https://www.bd.emb-japan.go.jp/itpr_en/11_000001_00654.html",
        "GitHub repository — https://github.com/UNCHIKIT/CISC7204-GroupG-SemesterProject-Team03",
    ]
    for r in refs:
        d.add_paragraph(r, style="List Number")

    DOCS.mkdir(parents=True, exist_ok=True)
    out = DOCS / "Data_Consistency_Technical_Findings.docx"
    d.save(str(out))
    print(f"[docx] {out.name}")


def main() -> int:
    DOCS.mkdir(parents=True, exist_ok=True)
    build_answers_docx()
    build_technical_docx()
    return 0


if __name__ == "__main__":
    sys.exit(main())
