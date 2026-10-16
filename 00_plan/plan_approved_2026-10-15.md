# Plan: Indonesia's travel services balance by partner country

## Context

**Target (a balance, not visitor counts):** for each partner country, in USD:
- **Credit:** spending by foreign visitors (wisman) in Indonesia.
- **Debit:** spending by Indonesian residents abroad.
- **Balance** = credit − debit.

You already checked the IMF and the World Bank and found nothing. Opus then mapped all the sources on 2026-10-15 and tested each one directly (API, PDF, XLSX). Scraping runs only after this plan is approved. A source is declared "not available" only with documented proof.

**Defaults (can be changed):**
- Annual data, 2010 through the latest year, plus quarterly where the source provides it.
- USD million.
- Output: a tidy CSV, then a simple Excel workbook (section 8).

## Status of the BPS WebAPI (checked 2026-10-15)

- `BPS_API_KEY` is **SET** at User scope and in the PowerShell process (32 characters), and it is also visible from Bash.
- A live call to var 272 returned `status=OK, data-availability=available`, with rows such as Brunei, Malaysia, Filipina, Singapura, Thailand.
- The key is never printed. Scripts read it from the environment variable.

---

## 1. Balance test for each source (every link is clickable and returned HTTP 200)

**Legend:**
- 🟢 **FULL BALANCE:** credit and debit by country, in value terms, so the balance can be computed directly.
- 🟡 **ONE SIDE ONLY:** value for credit only or debit only. It becomes a balance only when paired with the other side.
- 🔴 **NOT A BALANCE:** only counts of people or trips. Used only as a multiplier or allocation key, never as output.
- ⚫ **TOTAL ONLY:** no country breakdown. Used as a control total.

### 🟢 Full balance by country

| Source | Indonesia coverage | Direct link (data) | Notes |
|---|---|---|---|
| **OECD TIS**, partner-reported mirror data | Partner = IDN, item SD. Credit, debit and balance from **32 reporters + EU27**: ARG, AUS, AUT, BEL, BGR, CAN, CHE, CZE, DNK, EST, FIN, FRA, GBR, GRC, HKG, HRV, HUN, ISL, ITA, JPN, LTU, LUX, LVA, NLD, NZL, POL, ROU, RUS, SVK, SVN, SWE, USA. 2019–2025 verified (514 rows). **Not included:** CHN, MYS, SGP, SAU, KOR, THA, IND and DEU. Germany is checked in Eurostat. | [Indonesia CSV](https://sdmx.oecd.org/public/rest/data/OECD.SDD.TPS,DSD_BOP@DF_TIS,1.0/.IDN.SD...A.USD_EXC.?startPeriod=2019&format=csvfilewithlabels) | Official figures from partner countries. Credit and debit must be flipped (partner debit = Indonesian credit). |
| **OECD-WTO BaTIS** | IDN × **201 partners**, X/M, **2005–2024** verified (8,060 N/F rows). | [Balanced CSV](https://sdmx.oecd.org/public/rest/data/OECD.SDD.TPS,DSD_BATIS@DF_BATIS,1.0/IDN..X+M.S.SD.A.USD_EXC.B?startPeriod=2019&format=csvfilewithlabels) · [WTO page](https://data.wto.org/en/dataset/batis) · [**Methodology PDF**](https://www.wto.org/english/res_e/statis_e/daily_update_e/OECD-WTO_Batis_methodology_BPM6.pdf) | **Modelled data (verified).** Indonesia has reported **only its world total** for every year from 2005 to 2024 (all 40 "reported" rows have partner = World). The Indonesian side of each partner flow therefore comes from a gravity model: about 99% of rows are method "ME" for 2005–2022, while 2023–2024 are mostly "IE" (extrapolations). Saudi Arabia is badly off (see below). |
| **Eurostat** `bop_its6_det` | Partner = ID: credit, debit and balance, 2018–2025. Sub-items: business, health, education, other personal. | [EU27 vs ID CSV](https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/bop_its6_det/A.MIO_EUR.SD.CRE+DEB+BAL.ID.EU27_2020?format=SDMX-CSV&startPeriod=2018) · [Databrowser](https://ec.europa.eu/eurostat/databrowser/view/bop_its6_det/default/table?lang=en) | EUR million. Also available per member state. |
| **ABS Australia** | Table 7 (credits) and Table 8 (debits) by country × travel service. Indonesia row from **1998 to 2025** (verified). | [Table 7 xlsx](https://www.abs.gov.au/statistics/economy/international-trade/international-trade-supplementary-information-calendar-year/2025/536805500407.xlsx) · [Table 8 xlsx](https://www.abs.gov.au/statistics/economy/international-trade/international-trade-supplementary-information-calendar-year/2025/536805500408.xlsx) · [Release](https://www.abs.gov.au/statistics/economy/international-trade/international-trade-supplementary-information-calendar-year/latest-release) | AUD million. Split into business, education, other personal and so on. Australia is Indonesia's largest partner. |
| **BEA (US)**, ONS (UK), MOF (Japan) | Already included in OECD TIS (US, UK and Japan verified). The national sources are used only for sub-items or the latest year. | [BEA iTable](https://apps.bea.gov/iTable/?reqid=62&step=9&isuri=1&product=4) · [ONS dataset](https://www.ons.gov.uk/businessindustryandtrade/internationaltrade/datasets/uktradeinservicesservicetypebypartnercountrynonseasonallyadjusted) · [MOF BoP](https://www.mof.go.jp/english/policy/international_policy/reference/balance_of_payments/index.htm) | |

**Proof that these are balances (2023, Indonesia's side, already flipped):**

| Partner | Source | Credit | Debit | **Balance** |
|---|---|---:|---:|---:|
| Australia | OECD TIS (USD m) | 5,852.4 | 1,318.1 | **+4,534.3** |
| Japan | OECD TIS (USD m) | 419.0 | 636.8 | **−217.8** |
| United States | OECD TIS (USD m) | 658.0 | 798.0 | **−140.0** |
| United Kingdom | OECD TIS (USD m) | 379.1 | 279.7 | **+99.4** |
| EU27 | Eurostat (EUR m) | 1,829.8 | 351.9 | **+1,477.9** |
| Australia | BaTIS balanced (USD m) | 3,110.0 | 1,099.9 | **+2,010.1** ⚠ differs from the mirror figure |
| Malaysia | BaTIS balanced (USD m) | 760.1 | 1,462.8 | **−702.7** |
| Saudi Arabia | BaTIS balanced (USD m) | 158.8 | 110.7 | **+48.1** ⚠ implausible (hajj and umrah) |
| World | BaTIS reported (USD m) | 14,000.9 | 11,683.0 | **+2,317.9** (to be matched against BI V.3) |

### 🟡 One side only (value) → becomes a balance once the two sides are paired

| Source | Side | Direct link | Content |
|---|---|---|---|
| **BPS var 272:** average spending per visit **by country of residence/nationality** | Credit (× arrivals) | [BPS table](https://www.bps.go.id/id/statistics-table/2/MjcyIzI=/rata-rata-pengeluaran-wisatawan-mancanegara-per-kunjungan-menurut-negara-tempat-tinggal.html) | 37 rows of countries/regions, ≥2015–2025. API verified. |
| **BPS Statistik Pengeluaran Wisman 2025** | Credit | [Publication](https://www.bps.go.id/id/publication/2026/05/05/5d0ec91c10b00f0302bc6757/statistik-pengeluaran-wisatawan-mancanegara-2025.html) | Table 14: spending per visit by nationality, quarters I–IV. Table 15: by type of expenditure. |
| **BPS Statistik Wisatawan Nasional 2025** (also the 2022–2024 editions) | **Debit** | [Publication](https://www.bps.go.id/id/publication/2026/04/30/7344d8c9b1935d342f2ff9e7/statistik-wisatawan-nasional-2025.html) | **Figure 9: spending per trip by destination country (USD)** and Figure 2: share of trips by destination. Sources: Imigrasi, mobile positioning data (MPD) and the Survei Digital Wisnas (n=5,037). |
| **STB Singapore**, receipts by market | Debit to Singapore | [STB release Jan–Sep 2025](https://www.stb.gov.sg/about-stb/media-publications/media-centre/record-singapore-tourism-receipts-from-january-to-september-2025/) | Indonesia S$2.09bn (anchor value). |
| Tourism Malaysia, JTA Japan, MOTS Thailand, TRA Australia | Debit to those countries | (to be found in Phase 1) | Visitor spending by nationality. |
| Hajj and umrah (Kemenag / Kementerian Haji & Umrah) | Debit to Saudi Arabia | (Phase 1) | Pilgrim numbers × cost, **minus the airfare** (airfare counts as transport, not travel). |

### 🔴 Not a balance (counts only; never used as output)

- [BI SEKI V.28 wisman by entry port](https://www.bi.go.id/SEKI/tabel/TABEL5_28.pdf)
- [BI SEKI V.29 wisnas by exit port](https://www.bi.go.id/SEKI/tabel/TABEL5_29.pdf)
- [BPS var 1470: wisman arrivals by passport](https://www.bps.go.id/id/statistics-table/2/MTQ3MCMy/jumlah-kunjungan-wisatawan-mancanegara-per-bulan-menurut-paspor-yang-dipegang.html)
- [BPS var 2195: wisnas trips by exit port](https://www.bps.go.id/id/statistics-table/2/MjE5NSMy/jumlah-perjalanan-wisatawan-nasional.html)
- [UN Tourism arrivals](https://www.untourism.int/tourism-statistics/tourism-statistics-database)
- Hajj quotas

### ⚫ Total only (proof that there is no country breakdown)

| Source | Link | Proof |
|---|---|---|
| **IMF BOP** | [DSD structure](https://api.imf.org/external/sdmx/2.1/dataflow/IMF.STA/BOP/latest?references=datastructure) | Its dimensions are COUNTRY, ENTRY, INDICATOR, UNIT and FREQUENCY only. **There is no partner dimension**, so a bilateral figure cannot exist. |
| **World Bank WDI** | [Receipts](https://data.worldbank.org/indicator/ST.INT.RCPT.CD?locations=ID) · [Expenditures](https://data.worldbank.org/indicator/ST.INT.XPND.CD?locations=ID) | Country-year only. |
| **BI SEKI V.3 Jasa-jasa** | [PDF](https://www.bi.go.id/SEKI/tabel/TABEL5_3.pdf) · [XLS](https://www.bi.go.id/SEKI/tabel/TABEL5_3.xls) · [SEKI list](https://www.bi.go.id/id/statistik/ekonomi-keuangan/seki/default.aspx) | Has the row "D. Perjalanan – Ekspor/Impor" (total). None of the 40 tables in section V breaks services down by country. This is the **control total**. |
| **BI quarterly NPI report** | [Q1-2024 PDF](https://www.bi.go.id/id/publikasi/laporan/Documents/NPI_Tw_I_2024.pdf) | Page 18 has narrative only ("wisman asal Tiongkok", "wisnas ke ASEAN"). Chart 10 shows totals. |
| **UN Comtrade (services)** | [Indonesia as reporter](https://comtradeapi.un.org/public/v1/preview/S/A/EB?reporterCode=360&period=2022) · [Singapore vs IDN](https://comtradeapi.un.org/public/v1/preview/S/A/EB?reporterCode=702&period=2022&partnerCode=360) | Indonesia reports partner = World only. Singapore reports partner = Indonesia, but without the travel code. |
| **WTO TiSMoS** (Mode 2) | [Dataset](https://data.wto.org/en/dataset/tismos) | No partner dimension. |

### 🔒 Cannot access yet (logged separately, NOT "not available")

- [ASEANstats SITS](https://data.aseanstats.org/sits): returns "Not Authorized" and needs a free login. This is the only potential source of balances *reported by Indonesia itself* with ASEAN partners.
- [Kemenpar](https://kemenpar.go.id/): a single-page app whose content comes from `api.kemenpar.go.id`, so the endpoints need inspecting. The historical PES reports are on `api2.kemenparekraf.go.id/storage` ([example PES 2013](https://api2.kemenparekraf.go.id/storage/app/resources/PES2013.pdf)).

**Working conclusion:** Indonesia does not publish a travel balance by country. The final balance is built from three lines and triangulated:
- **Line A, BaTIS (modelled):** covers every partner.
- **Line B, partner mirror data:** strongest; roughly 35+ countries.
- **Line C, BPS components:** credit from arrivals × spending by nationality; debit from trips × share by destination × spending by destination, plus hajj and umrah.

---

## 2. Concept ladder and keywords (start broad, then narrow down)

**Concept ladder:**
- **Item:** Current account → Services → **Travel (SD)** → Business (SDA) / Personal (SDB: health, education, other) → goods, local transport, accommodation, food.
- **Partner:** World → region (ASEAN, EU, Middle East) → country.
- **Nearest neighbours:**
  - SDZ tourism-related.
  - Inbound and outbound expenditure in the Tourism Satellite Account (TSA).
  - Mode 2.
  - Tourism receipts by market (destination side).
  - Arrivals × spending per visit.

**Keywords (Indonesian):**
- *Core:* `neraca jasa perjalanan`, `jasa perjalanan menurut negara`, `neraca perjalanan`
- *Balance-of-payments wording:* `neraca pembayaran menurut negara/kawasan`, `ekspor/impor jasa menurut negara`
- *Foreign-exchange wording:* `devisa pariwisata menurut negara asal`
- *Survey wording:* `pengeluaran wisman menurut kebangsaan`, `pengeluaran wisnas menurut negara tujuan`
- *Components:* `haji`, `umrah`, `Bipih`, `Siskopatuh`, `pelajar RI di luar negeri`

**Keywords (English):**
- `travel services by partner country Indonesia`, `bilateral travel credit debit`, `trade in services by partner economy`
- `EBOPS SD counterpart area`, `mirror statistics`
- `tourism receipts by source market`, `education-/health-related travel by country`

**Keywords (partner-country languages):**
- Japanese: `訪日外国人消費動向調査 インドネシア`, `地域別国際収支 旅行`
- Korean: `국제수지 지역별 여행`
- Malay: `penerimaan pelancong mengikut negara`

## 3. Phase 1: Finish discovery (Opus) → `source_inventory.csv` + `absence_log.md`

Each item is checked against the balance test above.

**T1 Bank Indonesia**
- [SDDS/metadata page](https://www.bi.go.id/id/statistik/sdds/default.aspx): how travel is compiled.
- Annual NPI report and Laporan Perekonomian Indonesia: search the PDFs for "perjalanan".
- SEKDA.
- Foreign-exchange flow reporting (LLD) by country code: not published, so it becomes a data request.

**T2 ASEANstats SITS** (after login), the ASEAN Statistical Yearbook and StatsAPEC.

**T3 International sources**
- [UNCTADstat](https://unctadstat.unctad.org/datacentre/)
- [ITC Trade Map](https://www.trademap.org/)
- BaTIS full history 2005–2018 and its vintage ([WTO bulk download](https://www.wto.org/english/res_e/statis_e/trade_datasets_e.htm))
- Comtrade, re-checked year by year for 2015–2024

**T4 Partner mirror sources not in OECD TIS**
- Singapore: SingStat and STB tables.
- Malaysia: [DOSM](https://www.dosm.gov.my/portal-main/release-content/statistics-of-international-trade-in-services-2019), Tourism Malaysia and MHTC.
- Thailand: BOT and MOTS.
- Hong Kong: C&SD.
- Korea: BOK ECOS and KTO.
- Saudi Arabia: GASTAT.
- China: no bilateral data expected; this gets proven.

**T5 Indonesian components**
- Kemenpar: inspect the API and the historical Profil Wisnas and PES reports for 2010–2021.
- Imigrasi.
- Kemenag / Kementerian Haji & Umrah.
- [UNESCO UIS](https://data.uis.unesco.org/): students abroad.
- [BPS TSA 2023–2025](https://www.bps.go.id/id/publication/2026/09/01/27b61f56c20226ca8ecfd974/tourism-satellite-account-indonesia-2023-2025.html): is inbound or outbound split by country?

**T6 Household and village surveys**
- Download each questionnaire and codebook and search for `luar negeri` / `negara` / `perjalanan` / `wisata`. The source is microdata.bps.go.id, which was unreachable from here, so the fallback is the IHSN catalogue.

| Survey | What to check | Expectation (to be proven) |
|---|---|---|
| SUSENAS KOR, consumption module and MSBP module | Overseas trips, destination country, spending abroad | No by-country balance; at most trip frequency or spending without a country |
| SAKERNAS | Cross-border or seasonal workers | No travel balance |
| PODES | Tourist attractions, border villages | No BOP |

**Absence protocol:**
- A source is marked **NOT AVAILABLE** only with ≥3 of these five pieces of evidence:
  1. Structural proof: no partner dimension in the DSD or codelist.
  2. A search with the full keyword matrix, with every query and result count logged.
  3. The publication's table of contents has been saved.
  4. The metadata or methodology states the source's scope.
  5. A data request was sent (BI, BPS PST, Kemenpar). If there is no reply yet, it is logged as *pending*.
- Every entry records: link, access date, query, snippet, and the sha256 of the evidence file.
- 🔒 sources are always logged separately, never as "not available".

## 4. Phase 2: Scraping and extraction (`agen-scrap`, model **sonnet**, effort **high**, in the background)

| Batch | Scope |
|---|---|
| **S1 BaTIS** | IDN × all partners × SD (and SDA/SDB if available) × X/M × N/F/B, 2005–latest, including OBS_STATUS and METHODOLOGY_TYPE. |
| **S2 Mirrors** | OECD TIS (all reporters, partner IDN, C/D/B, SD and sub-items). Eurostat (partner ID, all SD codes, all geo). ABS Tables 7, 8 and 9. Plus the T4 sources from Phase 1. |
| **S3 BPS** | WebAPI vars 272, 356, 1470, 331, 1160 and 2195. Tables from the PDFs: Pengeluaran Wisman, Kunjungan Wisman (arrivals by nationality), Wisnas 2022–2025 (Figures 2 and 9), and the TSA. |
| **S4 Other components** | Kemenpar API and historical reports, hajj/umrah, UNESCO UIS, MHTC. |
| **S5 Control totals** | BI SEKI V.3: travel exports and imports, annual and quarterly. |

**Rules for the agent:**
- Do not bypass Cloudflare on bps.go.id. Use `webapi.bps.go.id`.
- Read the key from `BPS_API_KEY` and never print it.
- Keep raw files unchanged in `02_raw/<source>/` with a manifest (url, retrieved_at, sha256).
- Put each download in its own directory and run Python with `-I`.

**Tidy schema:**
- *Identification:* `source, line, reporter, partner_iso3`
- *Item:* `flow_idn (credit/debit/balance)`, `item`, `year, quarter`
- *Value:* `value, currency, value_usd_m`
- *Quality:* `method (mirror/reconstruction/model)`
- *Provenance:* `url, retrieved_at`

Mirror rows are flipped to Indonesia's perspective as they are extracted.

## 5. Phase 3: QA and triangulation (Opus)

**1. Control totals:**
- For each line, the sum over partners vs BI V.3 (perjalanan, ekspor/impor) for each year.
- BaTIS "World, reported" vs BI.

**2. Per-partner comparison:**
- Compare the balance from the mirror, the BPS reconstruction and BaTIS.
- Flag gaps above ±30%. Example already found: Australia, mirror +4.5bn vs BaTIS +2.0bn.

**3. Anchors:**
- BI Q1-2024: credit US$3.6bn, debit US$2.5bn.
- STB: S$2.09bn for Jan–Sep 2025.

**4. Adjustments:**
- Residence vs nationality.
- Remove the airfare from hajj/umrah packages.
- USD conversion at the annual average exchange rate.

**5. Best estimate per country.** Order of preference:
1. Official mirror data.
2. BPS reconstruction.
3. Model (BaTIS).

The source and method are recorded in the table.

## 6. Folder

```
D:\Download\Indonesia_Travel_Services_BOP\
  00_plan\  01_discovery\ (source_inventory.csv, absence_log.md, evidence\)
  02_raw\<source>\ (+manifest)  03_extract\  04_qa\  scripts\  output\ (Excel)
```

## 7. Verification

- Every 🟢/🟡 source: Opus spot-checks 3 values against the original page.
- Every ⚫/"not available" source: meets the absence protocol.
- The sum across partners reconciles to BI V.3, with every gap explained.
- The scripts re-run and produce the same output.

## 8. Excel (simple, McKinsey colours, minimal notes)

**Sheets (one data source = one sheet, each with its own Top 5 charts):**

| Sheet | Content |
|---|---|
| **Ringkasan** | Best estimate per partner country × Credit, Debit, **Balance** (USD m) for the latest year, sorted by the balance. A "Sumber" column (clickable link) and a "Metode" column (mirror / reconstruction / model). |
| **Top 5 – Perbandingan** | Compares the Top 5 from every source side by side (details below). |
| **Mirror – OECD TIS** | Data + Top 5 charts. Covers about 35 reporting countries. |
| **Mirror – Eurostat** | Data per EU country + Top 5 charts. |
| **Mirror – ABS** | Australia, including the business / education / other personal split. This is a single partner, so it gets no Top 5, only a trend chart. |
| **BaTIS Data** | Per partner: Indonesian-side estimate (F) · partner mirror · balanced value (B) · method code · gap in %. Plus Top 5 charts. |
| **BaTIS – Cara Model** | A sheet of its own explaining how BaTIS is modelled (details below). |
| **BPS Rekonstruksi** | Credit = arrivals × spending per visit by nationality. Debit = trips × share by destination × spending per trip. Plus Top 5 charts. |
| **Sisi Tujuan** | STB, Tourism Malaysia, JTA and so on. Debit side only, so it gets only the Top 5 debit chart. |
| **Tren** | The balance per country × year (2010–latest). |
| **Rekonsiliasi** | Sum across partners vs BI totals (one small table). |
| **Sumber** | List of sources + links. |

**What "Top 5" means.** The same three charts appear on every source sheet, using the latest common year (2024; 2019 as the pre-COVID comparison year can be added):
1. **Top 5 credit ("countries to Indonesia"):** the countries whose residents spend the most in Indonesia, i.e. the largest sources of foreign-exchange earnings.
2. **Top 5 debit:** the countries where Indonesian residents spend the most.
3. **Balance:** the 5 largest surpluses and the 5 largest deficits for Indonesia, as a diverging bar chart.

**Chart style:**
- Native Excel horizontal bar charts with identical formatting on every sheet.
- Navy bars, with the accent `#2251FF` for countries that make the Top 5 in **every** source.
- Data labels in USD m; no gridlines, no legend, and an action title (for example, "Australia is the largest source of travel receipts in every source").

**"Top 5 – Perbandingan" sheet:**
- A table of ranks 1–5 × source (OECD TIS · Eurostat · BaTIS · BPS · Sisi Tujuan), one table each for credit, debit and balance.
- Cells for a country that appears in every source are coloured with the accent.
- An "Overlap" row shows how many of the Top 5 match each other source (e.g. 4/5).
- A single small line below the table: **mirror coverage is limited to the reporting countries**. For example, OECD TIS does not include China, Malaysia, Singapore, Saudi Arabia, Korea or Thailand, so some differences in the Top 5 come from coverage, not from real differences. Only BaTIS covers every country. The BPS reconstruction covers the main markets (about 37 nationalities, plus the main destinations).

**Content of the "BaTIS – Cara Model" sheet** (from the [OECD-WTO methodology, Jan 2025](https://www.wto.org/english/res_e/statis_e/daily_update_e/OECD-WTO_Batis_methodology_BPM6.pdf), short and in tables):

**Table 1: steps in the model**

| Step | What BaTIS does | Effect on Indonesia's figures |
|---|---|---|
| A. Collect | Gathers reported bilateral data from all countries | Indonesia reports **World only**, so there is no Indonesian bilateral data. Partner countries (AUS, EU, US, JPN, …) do report Indonesia. |
| B. Gravity estimate | Missing flows are estimated with a gravity model | Variables used: GDP of both countries, distance, shared border, common language, colonial ties, GDP per capita, services trade with the world, time trend, bilateral goods trade, partner fixed effects, and **tourist arrivals/departures (travel only, UN Tourism data)** |
| C. Scaling | The estimates are rescaled to each country's world total | The Indonesian-side total = Indonesia's world total (BI). Partner shares stay the same, because Indonesia is "Group 1": all of its bilateral flows are modelled. |
| D. Consistency (RAS) | Travel = business + personal; the sum over partners = world | Small adjustments |
| E. Balancing | Balanced value = weighted average of the Indonesian-side value and the partner's mirror value | Weight = symmetry index (1 − asymmetry, 3-year average) × confidence weight |
| F. Extrapolation | The latest years are extrapolated from the time series | For 2023–2024, most Indonesian rows are "IE" (extrapolated) |

**Table 2: confidence weights:** reported = 1.00 · time series (interpolation/extrapolation) = 0.75 · gravity model = 0.50 · reported but implausible = 0.25.

**Table 3: code dictionary:**
- N = reported
- F = adjusted/imputed
- B = balanced
- ME = model-based (gravity)
- IE = interpolation/extrapolation
- AG = aggregation

**Table 4: one worked example (Australia, 2023, credit):**
- Indonesian-side estimate: 519 USD m.
- Australia's mirror: 5,852.
- BaTIS balanced value: 3,110.
- So the mirror carries roughly 49% of the weight.

**Table 5: model limits:** the gravity model knows nothing about hajj and umrah. That is why the Saudi Arabia figure (debit about 111 USD m) is far below reality, and why BaTIS ranks last in the best-estimate order.

**Formatting:**
- Colours: navy `#051C2C` for headers, a single accent `#2251FF`, light grey for separators.
- No gridlines and one font.
- Numbers formatted `#,##0.0`, with negatives in brackets.
- **Minimal notes:** one source line under each table. No "how calculated" rows and no long explanations. Traceability comes only from the source/method column and the links.

## 9. Open items that need your action

- **ASEANstats:** the SITS module needs a login. Please register (it's free) or approve skipping it.
- **Data requests** (BI travel by country / LLD, BPS PST, Kemenpar): I'll draft the emails and you send them.
- **After approval, saved to memory:**
  - Scraping for this project uses Sonnet **high**.
  - For this project the Excel is simple, with McKinsey colours and minimal notes, replacing the earlier heavy-annotation style.
  - A project memory for this work.
