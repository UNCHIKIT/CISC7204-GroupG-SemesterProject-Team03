# Team 03 — Answers: Generation Mix (A) and Drivers of Consumption Change (B)

Data-backed answers to the two review questions. All numbers computed from the
committed datasets (OWID generation mix, OWID carbon intensity, World Bank
population + GDP PPP, and `analysis_country_year.csv`).

---

## A. Fuel-by-fuel generation mix — how is electricity produced?

### A.1 Data, units, years (now confirmed)

- Source: OWID `electricity-prod-source-stacked.csv` (cached as
  `Datasets/owid_electricity_prod_source.csv`, 544 KB).
- **Units: TWh** per fuel per year. Columns (9 fuels): Coal, Gas, Oil, Nuclear,
  Hydropower, Wind, Solar, Bioenergy, Other renewables. Coverage **1900–2025**,
  249 entities (countries + regional aggregates).
- Carbon intensity: OWID `carbon-intensity-electricity.csv`, **gCO₂/kWh**.
- This is **generation**, not final consumption — see A.5.

### A.2 World: fuel shares 2000 → 2022

World generation rose **15,279 → 28,918 TWh (+89%)**.

| Fuel | 2000 share | 2022 share | Amount 2000→2022 (TWh) | Growth |
|---|---|---|---|---|
| Coal | 38.0% | 35.4% | 5,809 → 10,240 | +76% |
| Gas | 18.0% | 22.9% | 2,746 → 6,628 | +141% |
| Oil | 8.7% | 3.1% | 1,324 → 887 | −33% |
| Nuclear | 16.6% | 9.1% | 2,540 → 2,640 | +4% |
| Hydropower | 17.2% | 15.0% | 2,630 → 4,324 | +64% |
| Wind | 0.2% | 7.3% | 31 → 2,108 | +6,666% |
| Solar | 0.0% | 4.6% | 1 → 1,333 | +130,000% |
| Bioenergy | 1.0% | 2.3% | 154 → 669 | +334% |
| Other renewables | 0.3% | 0.3% | 44 → 88 | +101% |

Headline: the world still runs mostly on **coal + gas** (58% in 2022), but the
**fastest growth** is wind and solar, which went from ~0.2% to ~12% of generation.

### A.3 Regions: 2000 → 2022 (OWID continent definitions)

| Region | Total growth | 2022 dominant mix (share) | Notable shift |
|---|---|---|---|
| Africa | +109% | Gas 43%, Coal 26%, Hydro 18% | coal share halved, gas tripled |
| Asia | +238% | Coal 51%, Gas 17%, Hydro 12% | coal absolute +291%, solar/wind from ~0 to ~10% |
| Europe | +9% | Gas 26%, Nuclear 21%, Coal 15% | coal −40%, wind→11%, solar→5% |
| North America | +15% | Gas 37%, Coal 16%, Nuclear 16% | coal −58%, gas +187%, wind→9% |
| South America | +77% | Hydro 56%, Gas 16%, Wind 9% | hydro dominant throughout |
| Oceania | +25% | Coal 40%, Gas 17%, Hydro 14%, Solar 12% | coal −28%, solar→12% |

(OWID splits the Americas into North + South; the project's `region` column uses
"Americas" as one continent — North+South America combined.)

### A.4 Largest countries: 2000 → 2022

| Country | Total growth | 2022 mix (top 4 by share) |
|---|---|---|
| China | +553% | Coal 61%, Hydro 15%, Wind 9%, Solar 5% |
| United States | +13% | Gas 39%, Coal 19%, Nuclear 18%, Wind 10% |
| India | +216% | Coal 74%, Hydro 10%, Solar 5%, Wind 4% |
| Japan | −5% | Gas 36%, Coal 34%, Solar 9%, Hydro 7% |
| Russia | +33% | Gas 46%, Nuclear 19%, Hydro 17%, Coal 16% |
| Brazil | +94% | Hydro 63%, Wind 12%, Bioenergy 8%, Gas 6% |
| South Korea | +114% | Coal 34%, Nuclear 28%, Gas 28%, Solar 5% |
| Canada | +10% | Hydro 60%, Gas 14%, Nuclear 13%, Wind 6% |
| Germany | −0% | Coal 32%, Wind 22%, Gas 14%, Solar 11% |
| France | −12% | Nuclear 63%, Gas 10%, Hydro 10%, Wind 8% |

Pattern: China and India are coal-led growth; Europe/North America swapped coal
for gas + wind/solar; Brazil/Canada/France are hydro/nuclear-based and low-carbon.

Carbon intensity (gCO₂/kWh, 2000 → 2022): World 527 → 490 (−7%); China 784 → 587
(−25%); US 608 → 410 (−32%); Germany 573 → 420 (−27%); India 740 → 706 (−5%);
Japan 424 → 520 (**+22%**, post-Fukushima coal/gas); France 80 → 79; Brazil 89 → 103.

### A.5 Generation vs consumption — show side by side

Generation is **not** consumption. In 2022 world generation = **28,918 TWh** vs
final consumption (FEC) = **24,936 TWh**. The gap (3,982 TWh, ~14%) is
transmission/distribution losses, plant own-use, and net trade/statistical
difference. This is exactly why the generation mix must **stay out of the sector
shares** (Industry/Transport/Residential/Services). The two belong side by side:
a generation-mix figure (this section) and a consumption figure (Output 1–7),
with an explicit note that they are different quantities.

### A.6 IEA free file (still to check)

The free IEA file may offer a longer series via its electricity **output** rows.
Whether those rows split output **by fuel** in the free file has **not** been
checked. Also note the IEA original files are **not redistributable**, so any IEA
data can only be cited, not committed (see `DATA_PIPELINE.md` §8).

---

## B. Why did consumption change? Associations, not proof of causes

### B.1 Framing

This dataset is **observational** and contains no prices, policies, technology
costs or weather. It can therefore **describe patterns and associations, but not
demonstrate causation**. We report results as "consistent with" an explanation,
never as proof.

### B.2 What we can relate consumption to

Population (World Bank `SP.POP.TOTL`) and income (World Bank
`NY.GDP.MKTP.PP.KD`, GDP in **international dollars at 2011 prices**, ending
2022). GDP is missing for 55 of 220 countries/territories in 2022 (mostly small
islands). Both are available for the eleven large consumers we checked.

### B.3 Decomposition (Kaya identity for electricity)

Electricity consumption factors into three arithmetic parts:

```
E = P × (GDP/P) × (E/GDP)
```

- **P** — population
- **GDP/P** — income per person
- **E/GDP** — electricity used per unit of GDP (the "intensity")

Taking log growth, the total growth splits **exactly and additively**:

```
g_E = g_population + g_income-per-person + g_electricity-per-GDP
```

Each part is arithmetic, not causal: it says *how much* each term accounts for,
not *why* the term moved.

### B.4 Results, 2000 → 2022 (log growth, percentage points; E = final consumption)

| Country | E growth | Population | Income/person | E/GDP |
|---|---|---|---|---|
| China | +196% | +11.2 | +166.5 | +18.2 |
| United States | +13.5% | +16.9 | +28.0 | −31.3 |
| India | +148.9% | +29.8 | +102.0 | +17.1 |
| Japan | −7.5% | −1.4 | +16.4 | −22.6 |
| Russia | +30.2% | −1.6 | +65.9 | −34.1 |
| Brazil | +54.0% | +18.9 | +28.1 | +6.9 |
| South Korea | +72.2% | +9.5 | +70.1 | −7.4 |
| Canada | +21.3% | +23.8 | +19.1 | −21.7 |
| Germany | −1.3% | +1.2 | +24.4 | −26.9 |
| France | +7.5% | +11.3 | +15.6 | −19.3 |
| Indonesia | +131.2% | +25.5 | +78.9 | +26.8 |

Reading the table (associations, not causes):

- **China / India / Indonesia**: income-per-person grew very fast **and** E/GDP
  rose (electrification catching up), so consumption roughly tripled.
- **US / Japan / Germany / France / Canada**: E/GDP **fell** sharply (efficiency /
  decoupling), roughly cancelling income growth, so consumption grew little or
  fell.
- **Population** is the smallest component everywhere (≤ +30% over 22 years);
  income and intensity dominate.

This is a **description** of what accounts for the change. It does not say *why*
income or intensity moved — that would need data this project does not hold:
electricity prices, electrification policy (e.g. heat pumps, EVs), industrial
structure, and climate/weather.

### B.5 Decision: decomposition vs simpler comparison

Recommendation: **do the full decomposition** (it is only three extra columns of
arithmetic and answers the "what accounts for the change" question directly),
but present it alongside the simpler comparison (consumption growth vs population
growth vs GDP growth) so readers see both the raw growth rates and the split.
Either way, the caption must state: observational data, associations only, no
causal claim.

---

## Files to add if this is adopted

- `Datasets/owid_electricity_prod_source.csv` — already cached (generation mix).
- `Datasets/carbon_intensity_electricity.csv` — cached this session.
- `Datasets/worldbank_gdp_ppp.json` — cached this session (GDP PPP constant 2011).
- Population already cached (`worldbank_population.json`).

If the generation-mix and decomposition figures are adopted, they would be added
to `make_figures.py` / `make_dashboard.py` and documented in `DATA_PIPELINE.md`.
