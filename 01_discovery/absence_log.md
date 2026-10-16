# Absence log: sources with NO travel balance by country (checked 2026-10-15, Opus)

A source is marked "not available" only with at least 3 pieces of evidence: structural, search, table of contents, metadata, or data request. Locked sources (login or JavaScript) are listed separately and are **not** treated as "not available".

| Source | Verdict | Structural evidence | Search / TOC evidence | Metadata / scope |
|---|---|---|---|---|
| IMF BOP | NOT AVAILABLE | [DSD](https://api.imf.org/external/sdmx/2.1/dataflow/IMF.STA/BOP/latest?references=datastructure) dimensions are COUNTRY, BOP_ACCOUNTING_ENTRY, INDICATOR, UNIT, FREQUENCY. There is no counterpart. | The IMF's bilateral datasets (IMTS, DOTS) cover goods only | BPM6 BOP by country vs the world |
| World Bank WDI | NOT AVAILABLE | Indicators ST.INT.RCPT.CD / ST.INT.XPND.CD are country-year series | WITS uses the same WDI series | Source is UN Tourism / IMF totals |
| BI SEKI | NO BY-COUNTRY TABLE | The 40 tables in section V are listed. By-country tables exist only for goods (V.11, V.15, V.17, V.20, V.24, V.26), migrant-worker remittances (V.30–V.32) and FDI (V.33–V.38). | V.3 Jasa-jasa breaks services down only by type ("D. Perjalanan – Ekspor/Impor") | The NPI Q1-2024 report (p.18) mentions countries in narrative only. Grafik 10 shows totals. |
| UN Comtrade services | NOT AVAILABLE for IDN | Indonesia as reporter has partner = World only (2015, 2016, 2018, 2019, 2020, 2022) | 14 partner reporters were tested for 2022; none report travel (code 4) with IDN | — |
| WTO TiSMoS | NOT AVAILABLE | No partner dimension | Dataset page | Mode 2 by economy only |
| BaTIS (Indonesia-reported part) | Indonesia REPORTS WORLD ONLY | 0 IDN-reported (N) bilateral rows in each of the 20 years 2005–2024 | All 40 N rows have partner = World | Methodology Group 1: all bilateral values are modelled |
| SUSENAS | NOT AVAILABLE | KOR 2016 R603–R607: trips in the last 6 months, purpose, **province** of destination (domestic) | IHSN variable search ("luar negeri / negara / wisata / perjalanan / haji") across KOR 2016, modules 2013/2014/2016, MSBP 2015 | No overseas-spending items |
| SAKERNAS | NOT AVAILABLE | Only B5_R45A/B "ever worked abroad / country" (migration) | IHSN variable search, Aug 2016 | Labour survey |
| Kemenpar (statistik-jasa-perjalanan, statistik-devisa-pariwisata) | NOT AVAILABLE (as a balance) | API `api.kemenpar.go.id/api/v1/statistics/posts` (category 25 = jasa perjalanan, 27 = devisa) | "Jasa perjalanan" is travel-agency counts for 2007–2011. "Devisa" is BI credit totals with no country and no debit. Receipts by country exist only for 2009–2014 (credit). | Nesparnas 2015: the immigration card does not ask for the destination country, and the last outbound survey was in 2013 |
| BPS Tourism Satellite Account 2023–2025 | NOT AVAILABLE (by country) | Table list checked | Only a top-10 trip-share figure | — |
| PODES | NOT AVAILABLE | Only items on resources used for tourism and on TKI presence | IHSN variable search, 2011 and 2014 | Village survey |

**Limitation:** the BPS microdata portal (microdata.bps.go.id) could not be reached from this machine, so the Susenas checks after 2016 rely on IHSN coverage (through 2016). Since 2018/2021, domestic tourism statistics come from mobile positioning data, not Susenas.

## Locked (not counted as "not available")
| Source | Status | What would unlock it |
|---|---|---|
| [ASEANstats SITS](https://data.aseanstats.org/sits) | "Not Authorized" | Free user registration (needs the user) |
| (Kemenpar has been unlocked; it is now listed in the table above) | | |
