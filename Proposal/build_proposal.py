"""Build the CISC7204 Team 03 Team Project Proposal from Kelden's discussion draft.

    python Proposal/build_proposal.py

Writes cisc7204-Class_G-Team_03_TeamProjectProposal.docx next to this file and exports the PDF
through Word COM. Content is a restructuring of 'The Power Hungry World Group Discussion Draft.docx';
every figure in it came from that draft.
"""
import subprocess
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

OUT_DIR = Path(__file__).resolve().parent
STEM = 'cisc7204-Class_G-Team_03_TeamProjectProposal'
DOCX, PDF = OUT_DIR / f'{STEM}.docx', OUT_DIR / f'{STEM}.pdf'

ACCENT = RGBColor(0x0B, 0x4F, 0x6C)
INK = RGBColor(0x1F, 0x2A, 0x37)
MUTED = RGBColor(0x5A, 0x64, 0x70)

TITLE = 'The Power-Hungry World: Comparing Global Electricity Consumption Across Sectors'
RQ = ('How has electricity consumption changed across the world\u2019s countries and regions between '
      '1990 and 2022, and which countries and sectors account for the largest shares of that '
      'consumption?')
SUBMIT = '5 November 2026'

MEMBERS = [
    ('UN CHI KIT', 'mc653081', 'Team coordinator and project tracker'),
    ('KELDEN JAMTSHO', 'mc664183', 'Project analyst and quality reviewer'),
    ('GAN RUIYAN', 'mc664801', 'Lead project developer'),
    ('HE YIFEI', 'mc664916', 'Team reporter and team liaison'),
    ('SHENG TIAN', 'mc664961', 'Second project developer'),
    ('TANG JING', 'mc666256', 'Second project analyst and team scribe'),
]

SOURCES = [
    ('IEA World Energy Balances Highlights, 2026 edition',
     '54 countries and 10 aggregates incl. World', '1971\u20132024 (2025 provisional)',
     'PJ', 'industry, transport, residential, commercial and public services',
     'Free IEA account; raw file must not be redistributed',
     'Primary: sectors, world and regional totals'),
    ('UN Statistics Division, Energy Balance dataflow DF_UNData_EnergyBalance',
     '218 countries and territories; no aggregates; 4 combined entries', '1990\u20132023',
     'TJ', 'industry, transport, households, commerce and public services',
     'Public API and CSV, no account; free to copy with UNSD cited',
     'Primary: country totals and rankings'),
    ('Our World in Data energy data (Ember and Energy Institute)',
     '213 countries with demand data; 6 territories absent 2000\u20132022', '2000\u20132022',
     'TWh', 'none \u2014 totals, per-person values and generation mix only',
     'Free CSV, XLSX and JSON',
     'Secondary context and generation mix only'),
]

DECISIONS = [
    ('1', 'Research question', 'The wording below and its three sub-questions, as drafted'),
    ('2', 'Window', '1990\u20132022'),
    ('3', 'Sector grouping', 'Four groups: industry; transport; residential; services and other'),
    ('4', 'Unit', 'TWh (1 TWh = 3.6 PJ = 3 600 TJ)'),
    ('5', 'Regions', 'IEA aggregates for world and regional totals; UN for country detail; no self-built mapping'),
    ('6', 'Extensions', 'Include the generation-mix panel (OWID, 2000\u20132022); include only the simple '
                        'comparison of consumption growth against population and GDP growth, not the '
                        'three-way decomposition'),
    ('7', 'Roles', 'As recorded in the 1st meeting minutes (Section 6)'),
    ('8', 'Brief compliance', 'Checked line by line against the brief by UN CHI KIT'),
    ('9', 'Environment', 'python 3.14.7, pandas 3.0.3, numpy 2.4.6, openpyxl 3.1.5, requests 2.34.2, '
                         'notebook 7.5.7, ipykernel 6.31.0, matplotlib 3.11.0, seaborn 0.13.2, pinned in requirements.txt'),
]

TASKS = [
    ('1', 'Acquire the three sources and freeze them',
     'IEA Excel (each member downloads their own copy), UN CSV from the SDMX API, OWID CSV; date-stamp each file',
     'Three untouched raw files plus a dated manifest'),
    ('2', 'Harmonise into one analysis table',
     'Replace UN area codes with names, convert TJ\u2192PJ\u2192TWh, reconcile country spellings across sources, '
     'group sectors into the four agreed groups, carry the estimate flag',
     'Table of country, year, sector, TWh, estimate-flag, source'),
    ('3', 'Sub-question 1 \u2014 change over time',
     'Totals by region and largest country 1990\u20132022; absolute change, compound annual growth rate, '
     'index with 1990 = 100; decade growth as well as the full window',
     'Trend table plus a small-multiple line-figure set'),
    ('4', 'Sub-question 2 \u2014 country shares',
     'Each country\u2019s share of world consumption in 1990, 2000, 2010 and 2022; top ten and rank changes; '
     'top-five and top-ten concentration; world total cross-checked against the IEA World row',
     'Ranking table plus a share figure'),
    ('5', 'Sub-question 3 \u2014 sector shares',
     'Share of each group in world and regional totals, 1990 vs 2022 in percentage points; each sector\u2019s '
     'growth rate and contribution to total growth; IEA primary, UN as second view',
     'Sector table plus a stacked-share figure'),
    ('6', 'Validation, generation mix and reporting',
     'Run the nine validation checks; add the OWID generation-mix panel; assemble the report, the '
     'dashboard and the video',
     'Validated results, four figures, dashboard, report and video'),
]

CHECKS = [
    ('Data quality', 'Missing values, estimates and coverage gaps stated for every table'),
    ('Reproducibility', 'The notebook runs clean from a restart on a fresh environment'),
    ('Calculation correctness', 'Sector shares sum to 100 %; TJ, PJ and TWh conversions consistent'),
    ('Figure clarity', 'Every figure carries title, units, source and years'),
    ('Citations and licences', 'Every source and licence condition covered, IEA cited in its required form'),
    ('Brief compliance', 'Checked line by line against the assignment brief'),
    ('Reporting bias', 'Sector trends repeated using only countries that report in every year'),
    ('Estimate sensitivity', 'Key results re-run with estimated values excluded'),
    ('Traceability', 'Every sentence in the report ties to a number in the outputs'),
]

TIMELINE = [
    ('1', '5\u201311 Nov 2026', 'Acquire and freeze the three sources; harmonise country names and sector groups; '
     'build the UN world total and reconcile it with the IEA World row', 'Analyst (Kelden) + developer (Gan)'),
    ('2', '12\u201318 Nov 2026', 'Sub-questions 1 and 2: growth rates, index series, regional totals, country '
     'shares and concentration', 'Analyst + second analyst (Tang)'),
    ('3', '19\u201325 Nov 2026', 'Sub-question 3: sector shares and contributions to growth; generation-mix '
     'panel; first drafts of the four figures', 'Developer (Sheng) + analyst'),
    ('4', '26 Nov\u20133 Dec 2026', 'Report, dashboard, rehearsal, and the collaboration record (5 Dec); '
     'final validation pass before submission', 'Reporter (He Yifei) + coordinator (Un Chi Kit)'),
]

REFERENCES = [
    'Cleveland, W. S., & McGill, R. (1984). Graphical perception: Theory, experimentation, and application '
    'to the development of graphical methods. Journal of the American Statistical Association, 79(387), '
    '531\u2013554. https://doi.org/10.1080/01621459.1984.10478080',
    'Csereklyei, Z., Rubio, M. d. M., & Stern, D. I. (2016). Energy and economic growth: The stylized facts. '
    'The Energy Journal, 37(2), 223\u2013255. https://doi.org/10.5547/01956574.37.2.zcse',
    'Hunter, J. D. (2007). Matplotlib: A 2D graphics environment. Computing in Science & Engineering, 9(3), '
    '90\u201395. https://doi.org/10.1109/MCSE.2007.55',
    'International Energy Agency. (2026). World energy balances highlights [Data set]. '
    'https://www.iea.org/data-and-statistics/data-product/world-energy-balances-highlights',
    'McKinney, W. (2010). Data structures for statistical computing in Python. In S. van der Walt & '
    'J. Millman (Eds.), Proceedings of the 9th Python in Science Conference (pp. 56\u201361). '
    'https://doi.org/10.25080/Majora-92bf1922-00a',
    'Ritchie, H., Roser, M., & Rosado, P. (2024). Energy. Our World in Data. https://ourworldindata.org/energy',
    'Stern, D. I. (2011). The role of energy in economic growth. Annals of the New York Academy of Sciences, '
    '1219(1), 26\u201351. https://doi.org/10.1111/j.1749-6632.2010.05921.x',
    'United Nations Statistics Division. (2025). Energy statistics: Energy balance dataflow '
    '(DF_UNData_EnergyBalance) [Data set]. https://unstats.un.org/unsd/energystats/data',
]


def shade(cell, hexcolor):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear'); shd.set(qn('w:color'), 'auto'); shd.set(qn('w:fill'), hexcolor)
    tcPr.append(shd)


def add_field(paragraph, instr):
    run = paragraph.add_run()
    fld = OxmlElement('w:fldSimple'); fld.set(qn('w:instr'), instr)
    run._r.addnext(fld)


def table(doc, header, rows, widths, font=9.0):
    t = doc.add_table(rows=1, cols=len(header))
    t.style = 'Table Grid'
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for cell, text, w in zip(t.rows[0].cells, header, widths):
        cell.width = w
        cell.paragraphs[0].text = ''
        run = cell.paragraphs[0].add_run(text)
        run.bold = True; run.font.size = Pt(font); run.font.color.rgb = INK
        shade(cell, 'E7EEF3')
    for row in rows:
        cells = t.add_row().cells
        for cell, text, w in zip(cells, row, widths):
            cell.width = w
            cell.paragraphs[0].text = ''
            p = cell.paragraphs[0]
            run = p.add_run(str(text)); run.font.size = Pt(font); run.font.color.rgb = INK
            p.paragraph_format.space_after = Pt(0)
    for row in t.rows:
        trPr = row._tr.get_or_add_trPr(); trPr.append(OxmlElement('w:cantSplit'))
    doc.add_paragraph()
    return t


def heading(doc, text, level=1):
    h = doc.add_heading('', level=level)
    run = h.add_run(text)
    run.font.color.rgb = ACCENT
    run.font.size = Pt(13 if level == 1 else 11)
    run.bold = True
    h.paragraph_format.space_before = Pt(10 if level == 1 else 6)
    return h


def para(doc, text, size=10, bold_lead=None, italic=False, space_after=5):
    p = doc.add_paragraph()
    if bold_lead:
        r = p.add_run(bold_lead); r.bold = True; r.font.size = Pt(size); r.font.color.rgb = INK
    r = p.add_run(text); r.font.size = Pt(size); r.font.color.rgb = INK; r.italic = italic
    p.paragraph_format.space_after = Pt(space_after)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    return p


def bullet(doc, text, size=10, bold_lead=None):
    p = doc.add_paragraph(style='List Bullet')
    if bold_lead:
        r = p.add_run(bold_lead); r.bold = True; r.font.size = Pt(size); r.font.color.rgb = INK
    r = p.add_run(text); r.font.size = Pt(size); r.font.color.rgb = INK
    p.paragraph_format.space_after = Pt(2)
    return p


def build():
    doc = Document()
    st = doc.styles['Normal']
    st.font.name = 'Calibri'; st.font.size = Pt(10); st.font.color.rgb = INK
    st.paragraph_format.space_after = Pt(4)
    st.paragraph_format.line_spacing = 1.06

    s = doc.sections[0]
    s.page_width, s.page_height = Cm(21), Cm(29.7)
    for m in ('top_margin', 'bottom_margin', 'left_margin', 'right_margin'):
        setattr(s, m, Cm(1.9))

    fp = s.footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = fp.add_run(f'{STEM}  \u00b7  page ')
    r.font.size = Pt(8); r.font.color.rgb = MUTED
    add_field(fp, 'PAGE')

    # ---------------- cover ----------------
    for _ in range(4):
        doc.add_paragraph()
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run('CISC7204 Data Science and Data Visualization')
    r.bold = True; r.font.size = Pt(14); r.font.color.rgb = ACCENT
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run('Semester Project \u00b7 Team Project Proposal')
    r.font.size = Pt(11); r.font.color.rgb = MUTED
    doc.add_paragraph()
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(TITLE)
    r.bold = True; r.font.size = Pt(22); r.font.color.rgb = INK
    doc.add_paragraph()
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run('2026/2027, Semester 1  \u00b7  Class G - Team 03  \u00b7  Submitted: 5 November 2026')
    r.font.size = Pt(10.5); r.font.color.rgb = MUTED
    doc.add_paragraph()
    doc.add_paragraph()

    t = doc.add_table(rows=1, cols=3)
    t.style = 'Table Grid'; t.alignment = WD_TABLE_ALIGNMENT.CENTER
    widths = [Cm(6.0), Cm(3.4), Cm(7.6)]
    for cell, text, w in zip(t.rows[0].cells, ('Member', 'Student ID', 'Role'), widths):
        cell.width = w; cell.paragraphs[0].text = ''
        run = cell.paragraphs[0].add_run(text); run.bold = True; run.font.size = Pt(9.5)
        shade(cell, 'E7EEF3')
    for name, sid, role in MEMBERS:
        cells = t.add_row().cells
        for cell, text, w in zip(cells, (name, sid, role), widths):
            cell.width = w; cell.paragraphs[0].text = ''
            run = cell.paragraphs[0].add_run(text); run.font.size = Pt(9.5)

    doc.add_page_break()

    # ---------------- 1 ----------------
    heading(doc, '1. Project Title and Research Question')
    para(doc, TITLE, bold_lead='Title: ')
    para(doc, RQ, bold_lead='Research question: ')
    para(doc, 'Three sub-questions make the question measurable, and each is answered from the same '
              'harmonised table:')
    bullet(doc, 'how has electricity consumption grown by region and in the largest countries, and which '
                'regions grew fastest?', bold_lead='Change over time \u2014 ')
    bullet(doc, 'which countries account for the largest part of world consumption, and has that changed '
                'between 1990 and 2022?', bold_lead='Country shares \u2014 ')
    bullet(doc, 'how is consumption split between industry, residential, commercial, transport and other '
                'uses, worldwide and by region, and how has that split moved?', bold_lead='Sector shares \u2014 ')
    para(doc, 'The question is answerable from public data with descriptive statistics and a small number '
              'of tests, which is what makes it suitable for statistical and data-science inquiry rather '
              'than for speculation about causes.', italic=True)

    # ---------------- 2 ----------------
    heading(doc, '2. Project Purpose')
    para(doc, 'Electricity is the fastest-moving part of the world energy system, yet the public '
              'conversation about it usually cites a single global number. This project replaces that '
              'number with a decomposition: which regions, which countries and which sectors drove the '
              'change between 1990 and 2022, and how much of the movement is measured rather than '
              'estimated. The output is a defensible description of where consumption sits today and how '
              'the balance shifted over three decades.')
    para(doc, 'The team will exercise the full data-science workflow on three genuinely awkward public '
              'sources: acquisition with licence constraints, harmonisation of three units and three '
              'sector taxonomies, reconciliation of country spellings across sources, cross-source '
              'validation, growth-rate and share arithmetic, and figure production for a non-specialist '
              'reader.', bold_lead='Outcomes. ')
    para(doc, 'pandas joins and reshaping across mismatched country lists; unit conversion between TJ, PJ '
              'and TWh; compound annual growth rates, index series and contribution-to-growth '
              'decomposition; cross-source reconciliation and reporting-bias checks; matplotlib and '
              'seaborn panels for trends and shares; reproducible notebooks with pinned environments.',
         bold_lead='Skills. ')
    para(doc, 'energy economics and structural change across three decades; the difference between '
              'generation and final consumption; why observational national statistics support '
              'description rather than causal claims; how statistical agencies' + ' estimation practices '
              'shape what a comparison can support.', bold_lead='Knowledge. ')

    # ---------------- 3 ----------------
    heading(doc, '3. Data Context')
    para(doc, 'The geographic region is global: 218 countries and territories, aggregated to the IEA '
              'regions for the regional view. The domain category is energy economics, specifically final '
              'electricity consumption by end-use sector. Three sources are used, each covering the other' + '\u2019s '
              'gaps:', bold_lead='Region and domain. ')
    table(doc, ['Source', 'Coverage', 'Years', 'Unit', 'Sector detail', 'Access and licence', 'Role'],
          SOURCES,
          [Cm(4.4), Cm(3.2), Cm(2.2), Cm(1.2), Cm(3.0), Cm(3.2), Cm(2.8)], font=8.0)
    para(doc, 'KAPSARC electricity consumption by sectors was reviewed and dropped: it covers Saudi '
              'Arabia only, which cannot answer a global question.', size=9, italic=True)

    para(doc, 'Consumption means final electricity consumption, the electricity delivered to end '
              'users; in the UN data, power-plant own use and grid losses are separate lines outside this '
              'figure. The window is 1990 to 2022: the UN series begins in 1990, and 2023 carries a higher '
              'share of estimates. The reporting unit is TWh, where one TWh equals 3.6 PJ, which equals '
              '3 600 TJ. Data centres, cryptocurrency mining and demand forecasting are out of scope, '
              'because no source in this set reports them separately.', bold_lead='Definitions. ')

    heading(doc, 'Data quality and limitations', 2)
    bullet(doc, 'the IEA 2022 world total for final electricity consumption is 88,859 PJ, about '
                '24,700 TWh, and its sector flows add up to that total for 2021\u20132024 within rounding.',
           bold_lead='Internal consistency \u2014 ')
    bullet(doc, 'the two main sources disagree for some large countries. UN/IEA total ratios are 0.77 for '
                'Indonesia, 1.09 for China, 0.98 for India and 0.95 for Korea, and neither gap is '
                'explained. Nine other large countries agree within 3 %, and five of those match exactly '
                'on every sector \u2014 which suggests both sources draw on the same national reports, so '
                'agreement is weak evidence of accuracy.', bold_lead='Cross-source disagreement \u2014 ')
    bullet(doc, 'UN transport is reported for 98 of 218 areas in 2022 (81 in 2012, 102 in 2023), so a '
                'rising sector trend can partly reflect more countries reporting. 17.3 % of 2022 UN '
                'values are flagged as estimates, against 12.9 % in 2012 and 20.9 % in 2023, and the '
                'meaning of the flag is assumed rather than confirmed.', bold_lead='Uneven coverage \u2014 ')
    bullet(doc, 'four UN entries combine territories (France with Monaco, Italy with San Marino, Norway '
                'with Svalbard and Jan Mayen, Switzerland with Liechtenstein), and China has no commerce '
                'row, with its 4,363 PJ "other" row possibly absorbing it.',
           bold_lead='Definitional edges \u2014 ')
    bullet(doc, 'the IEA licence forbids redistributing the raw file, so each member downloads their own '
                'copy and the repository holds code, instructions and a derived extract only. That '
                'constraint is why OWID, downloadable in one request, anchors reproducibility for the '
                'totals and generation mix.', bold_lead='Licence and reproducibility \u2014 ')

    # ---------------- 4 ----------------
    heading(doc, '4. Project Tasks and Deliverables')
    para(doc, 'Preparation turns three differently shaped files into one comparable table of country, '
              'year, sector and TWh. Raw files stay untouched; the UN download is kept as a dated CSV; the '
              'IEA file is read from its TimeSeries sheet with ".." treated as missing and the provisional '
              '2025 column dropped. A missing sector row is treated as not separately reported, never as '
              'zero. The work then runs in six steps:')
    table(doc, ['#', 'Task', 'Method and tools', 'Output'],
          TASKS, [Cm(0.9), Cm(3.8), Cm(7.6), Cm(4.7)], font=8.5)

    para(doc, 'Executed Jupyter notebook reproducing every number; four figures (regional trend, country '
              'share shift, sector share change, generation mix); one interactive dashboard; this '
              'proposal; and the five-minute introductory video.',
         bold_lead='Deliverables. ')

    heading(doc, 'Data preparation steps', 2)
    para(doc, 'The steps run in this order, and each is visible in the notebook:', size=9.5)
    for text in [
        'Keep the raw files untouched. The UN download is saved as a dated CSV; each member downloads '
        'their own copy of the IEA file, because the licence forbids redistribution.',
        'Load the IEA workbook from its TimeSeries sheet with the real header row, treat the text value '
        '".." as missing, drop the helper columns, and drop the provisional 2025 column.',
        'Load the UN file and replace numeric area codes with names from the official code list, '
        'labelling the four combined entries clearly.',
        'Convert units: UN values from TJ to PJ (divide by 1,000), then both sources from PJ to TWh '
        '(divide by 3.6).',
        'Match country names across sources \u2014 China, Korea, Turkey, Czechia, Slovakia, the United '
        'States and the United Kingdom are spelled differently, and a raw join would silently drop them.',
        'Group sectors identically in both sources: industry; transport; residential (households); and '
        'services and other (commerce and public services, agriculture, other).',
        'Treat a missing sector row as not separately reported, never as zero \u2014 UN totals equal the '
        'sum of reported parts, so a missing row hides no amount but may be counted inside another.',
        'Build the UN world total by summing its 218 areas, since it has no World row, and compare it '
        'with the IEA World row.',
        'Prepare OWID for context only: keep rows with an ISO code (aggregates have none) and the years '
        '2000 to 2022.',
        'Carry the estimate flag through the analysis, so any result can be re-run with estimated values '
        'excluded.',
    ]:
        bullet(doc, text, size=9.5)

    heading(doc, 'Analysis by sub-question', 2)
    para(doc, 'Every result is reported with its source, its year range, its unit and the share of values '
              'that are estimates.', size=9.5)
    bullet(doc, 'total consumption in TWh by region and for the largest countries for every year from 1990 '
                'to 2022; absolute change, compound annual growth rate, and an index with 1990 equal to '
                '100; growth by decade as well as over the full window, because the 2020 pandemic dip '
                'bends any single rate. Regions come from the IEA aggregates; country detail from the UN '
                'data.', size=9.5, bold_lead='Change over time \u2014 ')
    bullet(doc, 'each country\u2019s share of the world total in 1990, 2000, 2010 and 2022, the top ten and '
                'how their ranks changed, and the combined share of the top five and top ten to show '
                'concentration; the world total is the sum of the UN areas, cross-checked against the IEA '
                'World row.', size=9.5, bold_lead='Country shares \u2014 ')
    bullet(doc, 'each grouped sector\u2019s share of world and regional totals, 1990 against 2022, with the '
                'change in percentage points; each sector\u2019s growth rate and its contribution to total '
                'growth. The IEA file is primary for sectors and the UN data gives a second view; where '
                'they differ, both are reported.', size=9.5, bold_lead='Sector shares \u2014 ')

    heading(doc, 'Additional analysis', 2)
    para(doc, 'Two questions sit beside the main one and do not change it. The first uses OWID\u2019s '
              'electricity columns, which cover 2000 to 2022: the fuel-by-fuel generation mix \u2014 coal, '
              'gas, oil, nuclear, hydro, solar, wind, biofuel and other renewables \u2014 compared for the '
              'world, the regions and the largest countries in 2000 and 2022, plus each fuel\u2019s growth '
              'rate. Generation is not consumption: it includes losses and trade, so it stays out of the '
              'sector shares and is shown side by side with them, labelled as such.',
         size=9.5, bold_lead='A. Generation mix \u2014 ')
    para(doc, 'the data is observational and carries no prices, policies, technology costs or weather, so '
              'it can describe patterns but cannot show that one thing caused another. The team relates '
              'consumption growth to population growth and to GDP per person for the largest countries, '
              'and reports the result as consistent with an explanation, never as proof; the data a real '
              'test would need is stated explicitly.',
         size=9.5, bold_lead='B. Why consumption changed \u2014 ')

    heading(doc, 'Resolved scope decisions', 2)
    para(doc, 'The nine decisions the draft left open are settled as follows, so every downstream number '
              'has a fixed definition.', size=9.5)
    table(doc, ['#', 'Decision', 'Value'], DECISIONS, [Cm(0.9), Cm(3.4), Cm(12.7)], font=8.5)

    para(doc, 'The shared environment is pinned so every member reproduces the same figures: python 3.14.7, '
              'pandas 3.0.3, numpy 2.4.6, openpyxl 3.1.5, requests 2.34.2, notebook 7.5.7, ipykernel '
              '6.31.0, matplotlib 3.11.0, seaborn 0.13.2. Each notebook prints its versions in the first '
              'cell, and the pins live in requirements.txt beside the code.', bold_lead='Environment. ')

    # ---------------- 5 ----------------
    heading(doc, '5. Success Criteria')
    para(doc, 'Nine checks decide whether the final work is good enough. Each is observable, and each is '
              'run before submission rather than asserted afterwards.')
    table(doc, ['Check', 'What makes it pass'], CHECKS, [Cm(4.4), Cm(12.6)], font=9.0)

    # ---------------- 6 ----------------
    heading(doc, '6. Team Collaboration')
    para(doc, 'Roles are as recorded in the 1st meeting minutes of 28 October 2026. The four roles the '
              'brief names explicitly are held by the members below, and the remaining work is divided so '
              'that every task has one accountable owner.')
    table(doc, ['Member', 'Student ID', 'Role(s)'],
          MEMBERS, [Cm(5.6), Cm(3.0), Cm(8.4)], font=9.5)
    para(doc, 'the team is coordinated by UN CHI KIT, who also keeps the progress tracker; the minutes '
              'and the shared repository are kept by TANG JING as team scribe; and HE YIFEI is the '
              'liaison with the instructor, relaying requirements and feedback. Major decisions are taken '
              'by the team together and recorded in the minutes.',
         bold_lead='Designated roles. ')
    para(doc, 'Working rules.', space_after=1)
    bullet(doc, 'one shared repository, files filed under the agreed naming convention, and every change '
                'to code, filters or design documented in Git.')
    bullet(doc, 'every number in a deliverable comes from the notebook; nothing is typed by hand.')
    bullet(doc, 'the quality reviewer signs off each deliverable before it is submitted, and the '
                'coordinator ticks off each member\u2019s individual submission by name.')

    # ---------------- 7 ----------------
    heading(doc, '7. Timeline')
    para(doc, 'The schedule begins on the proposal submission date and completes all project activity '
              'within four weeks, ending on 3 December 2026; the collaboration record follows on '
              '5 December. One online meeting is held each week.')
    table(doc, ['Week', 'Dates', 'Activity', 'Owner'],
          TIMELINE, [Cm(1.2), Cm(3.0), Cm(9.0), Cm(3.8)], font=9.0)

    # ---------------- references ----------------
    heading(doc, 'References')
    for ref in REFERENCES:
        p = doc.add_paragraph()
        r = p.add_run(ref); r.font.size = Pt(9)
        p.paragraph_format.left_indent = Cm(1.0)
        p.paragraph_format.first_line_indent = Cm(-1.0)
        p.paragraph_format.space_after = Pt(3)

    doc.save(DOCX)
    return DOCX


def export_pdf():
    ps = ("$ErrorActionPreference='Stop';$w=New-Object -ComObject Word.Application;$w.Visible=$false;"
          f"$d=$w.Documents.Open('{DOCX}',$false,$true);"
          f"$d.ExportAsFixedFormat('{PDF}',17);"
          "Write-Output ('PAGES=' + $d.ComputeStatistics(2));"
          "$d.Close($false);$w.Quit()")
    out = subprocess.run(['powershell', '-NoProfile', '-Command', ps],
                         capture_output=True, text=True, timeout=300)
    return (out.stdout or out.stderr).strip()


if __name__ == '__main__':
    build()
    print('docx:', DOCX, f'{DOCX.stat().st_size / 1024:.0f} KB')
    print(export_pdf())
    print('pdf :', PDF, f'{PDF.stat().st_size / 1024:.0f} KB' if PDF.exists() else 'MISSING')
