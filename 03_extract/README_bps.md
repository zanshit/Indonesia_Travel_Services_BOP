# BPS extraction: README (retrieved 2026-10-15)

Purpose: components for reconstructing Indonesia's travel-services balance by partner country (credit = arrivals x spend per visit; debit = outbound trips x destination share x spend per trip). **Nothing here is multiplied or combined**; the files only hold extracted numbers and the cross-checks.

Access: only `https://webapi.bps.go.id/v1/api/...` and the `download.php` PDF links it returned. `www.bps.go.id` was never contacted. The API key was read from `BPS_API_KEY`, replaced by `KEY` in every stored URL, and a byte scan of the whole project found it in no file. Throttle >= 1.1 s between requests, exponential backoff on errors. All downloaded files are treated as untrusted data (parsed only, never executed; scripts run with `python -I`).

Raw files: `02_raw/bps/api/` (191 unchanged JSON files), `02_raw/bps/pdf/` (21 unchanged PDFs, 262 MB), `02_raw/bps/manifest.csv` (file, url_without_key, retrieved_at_utc, sha256, bytes; 212 rows).

Scripts (`scripts/`, re-runnable; JSON is cached, `--refresh` re-downloads):
`bps_common.py` (key handling, throttle, manifest) - `fetch_bps_api.py` (variables, keyword search, publication details) - `fetch_bps_pdfs.py` (PDF downloads) - `pdf_tables.py` (position-based table reader) - `extract_bps_pdfs.py [swn|pengeluaran|kunjungan|tsa|los|all]` - `build_bps_nationality_rows.py` - `crosscheck_bps.py`.
Order: fetch_bps_api -> fetch_bps_pdfs -> extract_bps_pdfs all -> build_bps_nationality_rows -> crosscheck_bps. Side logs: `scripts/_*.log`, `_*.json`.

## 1. API variables (domain 0000)

| Var | Content | Unit | Years returned | File (rows) |
|---|---|---|---|---|
| 272 | Avg spend per visit by nationality ("Negara Tempat Tinggal"; PES) | USD | 2000-2016, 2018-2025 (**2017 absent**) | `bps_spend_per_visit_by_nationality.csv` (820) |
| 356 | Avg length of stay by nationality (immigration + MPD) | days | same as 272 | `bps_length_of_stay_by_nationality.csv` (886) |
| 1470 | Monthly arrivals by passport held (248 rows) | visits | 2017-2025 complete; **2026 only Jan-Aug** | `bps_arrivals_by_nationality_monthly.csv` (28,768; months 1-12 only) and `bps_arrivals_by_nationality_annual.csv` (2,480) |
| 331 | Receipts from foreign visitors by nationality (+ "Jumlah") | USD million | 2000-2014 only | totals in `bps_tourism_receipts_total.csv`; full country rows in `bps_receipts_from_wisman_by_nationality_2000_2014.csv` (516, extra file) |
| 1160 | Tourism foreign-exchange earnings (source: Bank Indonesia) | USD billion | 2015-2022 | `bps_tourism_receipts_total.csv` (23 rows = 15 from var 331 + 8 from var 1160) |
| 2195 | Number of national tourist (outbound) trips | trips | 2022-2025 annual; 2026 Jan-Aug | `bps_outbound_trips.csv` (2,093; all rows kept, total row = `row_label_clean = Jumlah`) |

Decoding: the key `vervar+var+turvar+th+turth` was decoded against the lists returned in the same response (reverse lookup built and asserted unique; any undecodable key stops the script). Example: `427201240` = vervar 4 (Singapura), var 272, th 124 (2024) = 707.69. Output columns: `row_label` is the verbatim API label, `row_label_clean` removes HTML tags and letter-spacing ("R u s i a" -> "Rusia"), `row_kind` = country_or_entity / residual_or_regional_group / region_subtotal / grand_total_or_average.

Notes on the API files
* **Var 2195 row dimension is "Pintu Masuk Kedatangan Wisnas" (arrival gate when returning), not exit port.** The 36 rows are the gates; "Jumlah" is the total. Annual totals: 2022 3,540,542; 2023 7,518,895; 2024 8,946,794; 2025 9,165,894. `period_label` = month names plus "Tahunan" (annual).
* Var 1470 annual file: `sum_of_months_1_12` equals BPS's own "Tahunan" value for every row and year (`sum_minus_reported` = 0 in the GRAND TOTAL). `year_completeness_flag` is taken from the GRAND TOTAL months: 2017-2025 complete; 2026 INCOMPLETE (months 9-12 missing). Individual rows may have fewer than 12 months with a value (no key returned = no value; read `n_months_with_value`, `months_without_value`). Var 1470 has odd labels (e.g. "Zomba", "Maseru", "Alaska", "Scotlandia") that are not countries; see `bps_nationality_rows.csv`.
* Var 1470 puts Timor Leste inside the ASEAN subtotal; the 2021-2024 publications put it under "Asia excl. ASEAN" (2025 edition: ASEAN). Group-level comparisons therefore differ; country rows match.
* Var 272/356 return 36 named rows (+ "Rata- Rata"): Hong Kong, Taiwan, Vietnam, Cambodia, UAE, Qatar etc. are not separate rows (they sit in "Negara lainnya"). The 2022-2025 publication tables below give 61 rows with those countries.
* Anchor check var 272, 2024: row "Rata- Rata" = **1391.85** (matches the news figure). Malaysia 693.07 (slightly below the 700-1,400 range in the task note), Singapura 707.69, Thailand 1107.35, Brunei 1064.90, Filipina 1005.25; The five values quoted in the task belong to Singapura 707.69, Pakistan 1315.53, Korea Selatan 1383.63, Spanyol 2109.05 and Filipina 1005.25 (the task's row labels were approximate).
* Keyword search (`bps_keyword_search_vars.csv`): other relevant variables are **74** (monthly arrivals by entry port 2008-2017) and **1150** (monthly arrivals by entry port 2008-now); neither is by nationality. "negara tujuan" only returns export variables 2380/2382 (irrelevant). No API variable exists for outbound trips or spend by destination country, and none for arrivals by nationality other than 1470 (annual nationality tables exist only in the PDFs). "negara tempat tinggal" returned no list.

## 2. Publication PDFs (text layer, position-based reader)

Index: `bps_publication_index.csv` (37 publications found by the API search or listed in the task). All 21 listed PDFs downloaded (earlier Pengeluaran editions 2019, 2021, 2022 added because the task asked to search for earlier editions). Page numbers: "pdf p" = page index in the PDF file, "printed" = number printed on the page.

### 2.1 Outbound: `bps_outbound_by_destination.csv` (3,235 rows) - Statistik Wisatawan Nasional 2022-2025
Long format. Required columns: `year, destination, purpose, trip_share_pct, spend_per_trip_usd, source_page, figure_or_table_id`; extra: edition, `measure`, `value`, `unit`, `column_header` (type of expenditure or leaf header), raw text, status, `table_family`, title, extraction method. `trip_share_pct` is filled only for the share of ALL trips by destination; the within-destination purpose mix has measure `trip_share_pct_within_destination` (read it from `value`). `purpose` is blank for expenditure-by-type tables (see `column_header`).

| table_family | 2025 edition (pdf p / printed p) | other editions (pdf p) |
|---|---|---|
| share_by_destination_year (Lampiran 4, share of all trips, 2021-2025) | 68-69 / 50-51 | 2024: 98-99 (2020-24); 2023: 70-71 (2019-23); 2022 Tabel 4: 73-74 (2019-22) |
| share_by_destination_purpose (Lampiran 10, % within destination) | 76-77 / 58-59 | 2024: 106-107; 2023: 78-79; 2022 Tabel 10: 80 |
| spend_by_destination_purpose (Lampiran 20, USD per trip) | 90-91 / 72-73 | 2024: 120-121; 2023: 92-93; 2022 Tabel 23: 95 |
| spend_by_destination_type (Lampiran 16: accommodation, food, transport...) | 83-85 / 65-67 | 2024: 113-115; 2023: 85-87; 2022 Tabel 19: 89-91 |
| spend_nights_pernight (Lampiran 28: USD per trip incl. overall total, nights, USD per night) | 101 / 83 | 2024: 131; 2023: 103; 2022 Tabel 27: 99 |
| prepost_spend (Lampiran 29, USD) | 102 / 84 | **none in 2022-2024** |
| sample_size (Lampiran 30) | 103 / 85 | 2024: 132; 2023: 104 |
| nights_by_destination_year | - | 2022 Tabel 5: 75 |

Figures of the 2025 edition (rows with `table_family` = `FIGURE:...`): all three are **raster images without a text layer**; the printed data labels were read from the extracted image and every value was cross-checked in code against the appendix tables.
* **Gambar 2** (pdf p23, printed 5; top 10 destinations + 7 regional shares): all labels printed. 16 of 17 values equal Lampiran 4 (2025). **Kamboja 2.43 % appears only in the figure** (it is inside "ASEAN Lainnya" in Lampiran 4). The same ten values are repeated as a text-layer chart in the TSA 2023-2025, Gambar 2.6 (pdf p36), which confirms the reading.
* **Gambar 9** (pdf p33, printed 15; spend per trip by purpose and destination): **only 6 segment labels are printed** (Malaysia Berlibur 803.11, Malaysia Kesehatan/Kecantikan 2,844.83, Vietnam Berlibur 885.40, Arab Saudi Keagamaan 2,604.82, Eropa Bisnis 4,162.58, Eropa Diklat 6,913.11), all equal to Lampiran 20. The other segments carry no label; nothing was estimated from bar lengths. The complete numbers are in Lampiran 20 (text layer).
* **Gambar 17** (pdf p49, printed 31; pre-/post-trip spend, 9 destinations): all 18 labels printed and equal to Lampiran 29. (The legend is cut off in the image; which bar is pre/post follows from Lampiran 29.)

Things Opus must know about the outbound numbers
* **Destination detail differs by measure.** Trip shares (mobile positioning data, MPD; Lampiran 4) list about 40 destinations. Spend per trip comes from the Survei Digital Wisnas (n = 5,037 in 2025) and is published only for 13 groups in 2025: Malaysia, Singapura, Thailand, Vietnam, Jepang, Korea Selatan, RR Tiongkok, Asia Lainnya, Arab Saudi, Australia, Eropa, Lainnya. Per the table note, "Lainnya" = Africa, the Americas (incl. USA), Oceania except Australia, Middle East except Saudi Arabia, ASEAN except MY/SG/TH/VN. "Asia Lainnya" = Asia outside ASEAN and the listed East Asian countries (Hong Kong, Taiwan, India, ...). The 2023 and 2024 editions have more rows (e.g. Amerika Serikat, Hong Kong, Turkiye, Timur Tengah Lainnya).
* Samples per group (Lampiran 30, 2025): Malaysia 1,441; Singapura 503; Thailand 420; Vietnam 135; Jepang 399; Korea 127; China 175; Other Asia 213; Saudi 1,121; Australia 104; Europe 200; Others 199.
* Overall average spend per trip (Lampiran 28 "Total"): 2025 **1,875.27** (nights 14.64; 128.06 per night); also in the executive summary (pdf p10) and text p26 (1,875 vs 1,820 in 2024). Total trips 2025 9,165,894 (pdf p10; equals var 2195). Pre-trip average 105.13, post-trip 58.68 (Lampiran 29 total).
* Overall total of the purpose table uses footnote 2 "total includes the units in NA".
* Cell values: "NA" = no value shown (the Pengeluaran publications state "data cannot be displayed due to insufficient sample"; the SWN tables do not define it). A lone dash (stored as `value_status = dash`) is not defined either. Footnote digits glued to numbers ("1.068,692" = 1,068.69 + footnote 2) were stripped and flagged `footnote_digit_stripped` (77 cells). Lampiran 29 uses dot decimals; all other tables use decimal commas. "Timor Leste2" = footnote 2 (Timor-Leste joined ASEAN in 2025; it moves between groups across years, so 2021-2024 vs 2025 ASEAN subtotals are not comparable).
* Shares by purpose do not sum to 100 when cells are NA (e.g. Malaysia 2025: 99.41 + NA for religious).
* The share table for 2022 and later editions revises earlier years (cross-check C1: 1 mismatch per older edition, "Asia Lainnya" changes by reclassification). Use the newest edition for each year.

### 2.2 Inbound spend: `bps_spend_per_visit_detail.csv` (5,719 rows) - Statistik Pengeluaran Wisman
Columns: edition, year, nationality (raw and clean), `row_kind` (group heading "1. ASEAN" etc. / row / total), `table_family`, `column_header`, `period_or_component`, `measure` (spend_per_visit_usd, spend_per_night_usd, avg_length_of_stay_nights), value, raw value, status, page, table id.
* **2025 edition**: Lampiran 14 (annual + Triwulan I-IV, pdf p129 / printed 107; 62 rows), Lampiran 15 (by type of expenditure, pdf p130-131 / 108-109), Lampiran 27 (spend per visit, nights, per night, pdf p143 / 121). Grand total 2025 = **1,267.07** (quarters 1,277.17 / 1,199.71 / 1,297.31 / 1,286.84).
* **2024 edition**: Lampiran 14 (quarterly) pdf p106; 15 (type) p107-108; 27 p120. Grand total 2024 = 1,391.85 (quarters 1,429.40 / 1,443.72 / 1,375.08 / 1,287.33).
* 2023: Lampiran 9 (type) pdf p92-95; Lampiran 17 (spend/visit and nights) p105-106 (printed 89-90). 2022: Tabel 13 (type) p92-94; spend/visit-nights table p103 (printed 78; number printed on the preceding page). 2021: Tabel 16 (type) p64-69, Tabel 22 (per night) p79-80. 2019: Tabel 7 (type) p52-53, **Tabel 6 = spend per visit by country of residence 2009-2019 (pdf p50-51; 2017 column also absent)**.
* "NA" cells (21, all in the 2025 edition, e.g. Laos) = not shown due to insufficient sample (text of the table note, 2025 edition). 2021 and 2019 contain 17 dash cells (undefined in the source).
* Quarterly spend exists only in the 2024 and 2025 editions (Lampiran 14); earlier editions publish annual values only.

### 2.3 Inbound arrivals: `bps_arrivals_by_nationality_pub.csv` (6,400 rows) - Statistik Kunjungan Wisman 2016-2025
Annual arrivals by nationality, from the multi-year nationality table of each edition: 2016 Tabel 4 (pdf p31-32), 2017 p31-32, 2018 p35-36, 2019 p32-33, 2020 p40-41, 2021 p35-36, 2022 Tabel 4 p60 (title says 2009-2022, the page shows 2018-2022), 2023 Lampiran 4 p61, 2024 Lampiran 3 p70, 2025 Lampiran 3 p74 (printed 58). Each edition repeats earlier years (use the newest edition; revisions are visible by comparing). Years are read from the header words nearest each column. 64 cells are "NA". Subtotal and grand-total rows are flagged in `row_kind`.
Also `bps_length_of_stay_pub.csv` (304 rows): Kunjungan 2025 / 2024 Lampiran 11 (immigration + MPD; pdf p100 / p96) and Lampiran 12 (immigration only; p101 / p97). Lampiran 11 is the same series as API var 356.

### 2.4 TSA 2023-2025: `bps_tsa_table_list.csv`
17 appendix tables (listed with titles and verified pages). **No inbound or outbound expenditure by country**: every table is by product, industry, indicator or year (inbound/outbound spend by product: Lampiran 1 pdf p98 and Lampiran 3 pdf p100). The only country-level item is Gambar 2.6 (pdf p36, printed 18), the share of outbound trips for 10 destinations (percent of trips, copied from SWN 2025).

## 3. `bps_nationality_rows.csv` (244 rows)
Side-by-side row labels of var 272, 356, 331, 1470 and the 2025 publication tables (spend Lampiran 14, arrivals Lampiran 3). `iso3` filled only when `row_type = country`; groups are `GROUP:...` keys with blank ISO3, totals `TOTAL:...`; entities that are not countries or are ambiguous (stateless, UNO, Zomba, Maseru, Guiana, Polynesia, Scotland/Wales/Alaska/Siberia as parts of other countries) have `row_type` non_country / ambiguous / sub_national / historic and a note. Hand-built variant dictionary: **0 labels unmapped**, but judgement calls are in `note` (e.g. var 331 "Korea" read as South Korea; "Samoa Barat" as Samoa; "Volta Atas" as Burkina Faso). The mapping is a proposal for Opus to confirm. Groups that overlap with country rows inside the same source (e.g. "Central America" and Costa Rica in var 1470) are noted.

## 4. Cross-checks (`bps_crosscheck.csv`, 3,485 comparisons; summary)
| Check | Result |
|---|---|
| A1 var 272 vs publication spend per visit (quarterly table + Lampiran 27/17/L-tables, 2022-2025) | 188 of 194 identical; the 6 diffs are 3 distinct values (each seen in two tables): Filipina 2024 1005.25 vs 1005.24, Portugal 2024 2000.70 vs 2000.07 (typo in one source), South America 2025 1,992.85 vs 1,991.76 |
| A2 var 272 vs 2019-edition series 2009-2019 | 358 of 360 identical (2 diffs: Norway 2019 0.01; "Negara lainnya" 2009 1,208.02 vs 1,221.77) |
| A3 var 356 vs the **Pengeluaran** publications' length of stay | **Does not match (different source/measure)**: the publication stay is from the exit survey in nights, var 356 is the immigration + MPD series. Do not mix them. |
| A4 var 356 vs **Kunjungan** Lampiran 11 (immigration + MPD) | 140 of 142 identical (2024: 70/70; 2025: 70/72; diffs USA 15.39 vs 11.56 and Italy 12.98 vs 13.87) |
| B1 var 1470 annual sums vs publication arrivals (2017-2025) | **Country rows: 1,483 of 1,530 identical.** Grand totals identical for 2017, 2018, 2020-2023 and 2025; 2019: 16,106,781 (API) vs 16,106,954 (publications); 2024: API 13,886,678 = 2025 edition, while the 2024 edition printed 13,902,420 (later revised). Remaining differences: preliminary 2024 edition values, one likely typo (China 2021: 4,713 in the 2023 edition vs 54,713), and group definitions (Timor Leste). |
| C1 SWN trip shares across editions | 548 of 552 identical; the 4 differences are "Asia Lainnya" (reclassification) |
| C2/C3 | var 2195 total 2025 = text 9,165,894; Lampiran 28 total = text 1,875.27 |
| D1 anchor | var 272 2024 "Rata- Rata" 1,391.85 = news figure |

## 5. Problems and gaps
1. **2017 spend per visit and length of stay by nationality do not exist** in var 272/356 or in the 2019 edition series (jumps 2016 -> 2018). Var 331 (receipts by nationality) stops in 2014.
2. Var 2195 has only 2022-2025 (+2026 Jan-Aug); no outbound count by destination country exists in absolute numbers. Destination counts must come from share x total trips.
3. Outbound spend per trip by destination exists only as 13 groups (2025) with small samples for Australia (104), Korea (127), Vietnam (135); several purpose cells are NA.
4. Gambar 9 labels are mostly unprinted (see 2.1), so the figure alone cannot give the data; Lampiran 20 does.
5. The TSA has no country breakdown.
6. 2026 data in vars 1470/2195 is partial (Jan-Aug).
7. SWN 2022 splits purposes only into Personal / Bisnis; spend by destination before 2022 is not in these PDFs (the 2022 edition covers 2019-2022 for trip shares and nights only).
8. Pdf extraction relies on text positions; every table row count was checked (e.g. 62 rows for the 2025 nationality tables) and the checks above come out consistent, but wrapped labels and footnote digits are the main risk. Raw label text is kept (`destination_label_raw`, `nationality_label_raw`, `value_raw`) so any cell can be audited against the PDF page cited in the same row.
