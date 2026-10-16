# ABS mirror data and Bank Indonesia SEKI V.3 control totals

Retrieved 2026-10-15 (UTC). Raw files are unchanged in `02_raw/abs/` and `02_raw/bi/` (each has `manifest.csv` with url, retrieved_at_utc, sha256, bytes).
Scripts (re-run with `python -I`): `scripts/fetch_abs.py`, `scripts/fetch_bi_seki.py`, `scripts/extract_abs.py`, `scripts/extract_bi.py`.

## 1. mirror_abs.csv (1,434 rows: 478 credit, 478 debit, 478 balance)

Source: ABS, International Trade: Supplementary Information, Calendar Year 2025 (released 30 Apr 2026).
Release page: https://www.abs.gov.au/statistics/economy/international-trade/international-trade-supplementary-information-calendar-year/latest-release
Files: 536805500405.xlsx (Tables 5.x), ...406 (6.x), ...407 (7.x), ...408 (8.x), ...409 (9.1).

Conventions
- Only the 'Indonesia' row of each sub-table is extracted (one row per sub-table). Currency AUD, millions; `unit_mult` = 1000000.
- Flip to Indonesia's perspective: ABS credits (Tables 5, 7) become flow_idn = debit; ABS debits (Tables 6, 8) become flow_idn = credit. Values are absolute (ABS debits are negative in the file).
- balance rows = Indonesia credit minus Indonesia debit for each year/item/table pair (5.k+6.k, 7.k+8.k); `source` reads "Tables 7.1+8.1" etc. and `url` holds both file URLs.
- `quarter` is blank (annual, calendar year). `source` carries the ABS table number; `item_label` is the ABS table title (footnote markers removed).
- ABS "-" (nil or rounded to zero) is stored as 0 (none occurred as text in the Indonesia rows; zeros are numeric 0).
- Tables 5/6 and 7/8 are separate ABS publications of overlapping content: Table 5.4 equals Table 7.1 and Table 6.4 equals Table 8.1 for 2000-2025 (max difference 0). Both are kept; filter by `source` to avoid double counting.

Sub-tables extracted
| Tables | Content | item code | Years |
|---|---|---|---|
| 7.1 / 8.1 | Travel, Total | SD | 1998-2025 |
| 7.2 / 8.2 | Travel, Business | SDA | 1998-2025 |
| 7.3 / 8.3 | Travel, Personal | SDB | 1998-2025 |
| 7.4 / 8.4 | Travel, Education | SDB2 | 1998-2025 |
| 7.5 / 8.5 | Travel, Other (= Personal excl. Education; includes health-related and other personal, not separable) | ABS_OTHER_PERSONAL (not SDB3, because it also contains SDB1) | 1998-2025 |
| 5.1 / 6.1 | Manufacturing services on physical inputs owned by others | SA | 2000-2025 |
| 5.2 / 6.2 | Maintenance and repair n.i.e. | SB | 2000-2025 |
| 5.3 / 6.3 | Transport | SC | 2000-2025 |
| 5.4 / 6.4 | Travel | SD | 2000-2025 |
| 5.5 / 6.5 | Construction | SE | 2000-2025 |
| 5.6 / 6.6 | Insurance and pension | SF | 2000-2025 |
| 5.7 / 6.7 | Financial | SG | 2000-2025 |
| 5.8 / 6.8 | Charges for use of IP n.i.e. | SH | 2000-2025 |
| 5.9 / 6.9 | Telecommunications, computer and information | SI | 2000-2025 |
| 5.10 / 6.10 | Other business | SJ | 2000-2025 |
| 5.11 / 6.11 | Personal, cultural and recreational | SK | 2000-2025 |
| 5.12 / 6.12 | Government goods and services n.i.e. | SL | 2000-2025 |
| 5.13 / 6.13 | Total services | S | 2000-2025 |

Table 9.1 (education-related travel credits by education sector and type of expenditure) has NO country dimension (rows are Higher Education / Vocational / Schools / ELICOS / New Zealand / Non-Award, Australia total only, from 2000). Recorded and skipped.

Anchor and cross-checks
- Table 7.1 Indonesia 1998-2004 = 706, 799, 788, 810, 746, 766, 735: matches. Table 8.1 Indonesia 1998 = -711, 1999 = -620: matches. In the output, Indonesia debit 1998 = 706, Indonesia credit 1998 = 711.
- Internal: Total = Business + Personal and Personal = Education + Other hold within +/-1 (rounding/perturbation).
- 2023 Indonesia (AUD m): ABS credits (Australia's exports = Indonesian residents' spending in Australia) = 1,984 -> Indonesia debit; ABS debits (Australians' spending in Indonesia) = 8,809 -> Indonesia credit; balance = 6,825.
- OECD TIS 2023 (USD m): Australia D = 5,852.4 and C = 1,318.1. Implied AUD per USD: 8,809 / 5,852.4 = 1.5052; 1,984 / 1,318.1 = 1.5052. Both fall in the expected 1.45-1.55 range and agree with each other (annual average 2023 around 1.51 is plausible).

## 2. bi_travel_totals.csv (672 rows)

Source: Bank Indonesia SEKI Table V.3 "Transaksi Berjalan: Jasa-Jasa", https://www.bi.go.id/SEKI/tabel/TABEL5_3.xls (the PDF twin is saved too and used only for a spot check). The XLS downloaded normally (102,912 bytes, no zero-byte problem); read with xlrd 2.0.2.
- Sheets used: 'Th 2004-2010' (quarters and annual 2004-2010) and '5.3' (2010 to 2026 Q2). 2010 appears in both and is identical (30 overlap comparisons, 0 differences); '5.3' is used.
- Items: `travel` (row "D. Perjalanan", "- Ekspor", "- Impor") and `services_total` ("Jasa-jasa", "- Ekspor", "- Impor"). Debits are stored as absolute values (BI shows imports negative). Balance = credit - debit; it reproduces BI's own net row (D. Perjalanan / Jasa-jasa) within 0.02 in every period.
- Coverage: annual 2004-2025 (22 years; 2026 annual not yet available); quarterly 2004 Q1 to 2026 Q2 (90 quarters). The file starts in 2004; earlier years are not in the current V.3 file.
- Annual columns have no header in the file; annual = sum of Q1-Q4 was verified for every year/flow (no mismatches).
- status_flag: BI marks 2025 Q1-Q4 and 2026 Q1 with * (provisional) and 2026 Q2 with ** (very provisional). The annual 2025 column carries no marker in the file; I derived * from its quarters. Balance rows take the most provisional flag of their components. Years up to 2024 are unflagged.
- Context: Memorandum rows (visitor counts) were not extracted. Other service categories (A-L) were not extracted, as requested.

Anchor and cross-checks
- Q1 2024 travel: credit 3,632.88, debit 2,547.48, balance 1,085.40 USD m. Matches the NPI report (3.6bn / 2.5bn / 1.1bn).
- 2023 annual travel: credit 14,000.91, debit 11,683.00, balance 2,317.91 USD m. BaTIS World-reported 2023 X 14,000.9 / M 11,683.0: identical to rounding (differences 0.01 and 0.00).
- 2023 total services: credit 33,606.82, debit 51,282.91, balance -17,676.09 USD m.
- PDF spot check (rounded to integers, covers 2019-2023 annual plus recent quarters): 2019 travel 16,911 / -11,308 and 2023 14,001 / -11,683 agree with the XLS.

## Problems and cautions
- ABS Tables 5, 6, 7.1, 7.3 and 8.x note that cells may be perturbed for confidentiality; small Indonesia cells (e.g. Table 8.4 education, 2-27) carry relative noise.
- ABS Table 7.5/8.5 'Other' mixes health and other personal travel, so the SDB1/SDB3 split is not available from these tables.
- ABS and BI measure different pairs: ABS gives Australia-Indonesia bilateral travel (AUD, calendar year), BI gives Indonesia's total travel with the world (USD). ABS credit-side ratios are not comparable to BI without a currency and coverage adjustment.
- Table 5/6 and 7/8 duplicates (SD) as noted; do not sum across them.
- ABS 2021 Indonesia values are tiny (border closures), so ratios for 2020-2021 are unstable.
