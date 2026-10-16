"""Build 03_extract/destination_side.csv (Indonesia's travel DEBIT seen from the destination side) from raw files.
Run: python -X utf8 -I scripts/build_destination_side.py
Sources: Tourism Malaysia (Tourist Profile 2024; KPI 2025), STB Singapore (media releases + annexes), JTA Japan (calendar-year summaries),
Thailand MOTS (annual 'Tourism receipts from international tourist arrivals' xlsx)."""
import importlib.util, csv, re, collections, html as H
from pathlib import Path
import fitz, openpyxl
_s = importlib.util.spec_from_file_location("s4", Path(__file__).resolve().parent / "s4_common.py")
C = importlib.util.module_from_spec(_s); _s.loader.exec_module(C)
COLS = ["source", "destination_iso3", "year", "period", "indicator", "value", "currency", "unit", "page_or_table", "url", "retrieved_at"]
out = []


def add(src, iso, year, period, ind, val, cur, unit, where, url, ts):
    out.append(dict(source=src, destination_iso3=iso, year=year, period=period, indicator=ind, value=val,
                    currency=cur, unit=unit, page_or_table=where, url=url, retrieved_at=ts))


# ---------------- Malaysia
R = C.RAW / "tourism_malaysia"
M = C._man(R)
TP = "https://data.tourism.gov.my/frontend/pdf/Malaysia_Tourist_Profile_2024%20v2.pdf"
ts = M["TouristProfile2024_pages_9_10_13_15_subset.pdf"]["retrieved_at_utc"]
S = "Tourism Malaysia - Malaysia's Tourist Profile 2024 by Selected Markets"
t15 = {r["country"]: r for r in csv.DictReader(open(C.EXTRACT / "tourism_malaysia_p15_expenditure_by_country.csv", encoding="utf-8-sig"))}
i = t15["Indonesia"]
pg = "PDF p.15 (printed pp.18-19) 'Tourist Expenditure by Country', Indonesia row"
for y in ("2024", "2023"):
    add(S, "MYS", y, "Jan-Dec", "arrivals_from_indonesia", int(float(i[f"arrivals_{y}"])), "", "persons (tourist arrivals, overnight)", pg, TP, ts)
    add(S, "MYS", y, "Jan-Dec", "spend_per_capita", i[f"per_capita_rm_{y}"], "MYR",
        "RM per tourist per visit (per capita expenditure, tourists only; includes all spend items, incl. any international airfare component)", pg, TP, ts)
    add(S, "MYS", y, "Jan-Dec", "receipts_from_indonesia", i[f"total_exp_rm_mil_{y}"], "MYR", "RM million (total tourist expenditure)", pg, TP, ts)
    add(S, "MYS", y, "Jan-Dec", "avg_stay_nights", i[f"avg_stay_nights_{y}"], "", "nights", pg, TP, ts)
t13 = {r["country"]: r for r in csv.DictReader(open(C.EXTRACT / "tourism_malaysia_p13_expenditure_components.csv", encoding="utf-8-sig"))}["Indonesia"]
pg13 = "PDF p.13 (printed p.15) 'Expenditure Components', Indonesia row"
add(S, "MYS", "2024", "Jan-Dec", "intl_airfare_share_of_expenditure", t13["International Airfares"], "",
    "% of tourist expenditure (to be excluded from the Indonesia-resident debit later)", pg13, TP, ts)
add(S, "MYS", "2024", "Jan-Dec", "medical_share_of_expenditure", t13["Medical"], "",
    "% of tourist expenditure (0.0 printed although 30.35% of Indonesian tourists cite medical purpose - anomaly, unexplained in the PDF)", pg13, TP, ts)
t9 = {r["country"]: r for r in csv.DictReader(open(C.EXTRACT / "tourism_malaysia_p9_purpose_of_visit.csv", encoding="utf-8-sig"))}["Indonesia"]
add(S, "MYS", "2024", "Jan-Dec", "medical_purpose_share_of_tourists", t9["Medical"], "", "% of Indonesian tourists whose main purpose = medical",
    "PDF p.9 (printed p.10) 'Main Purpose of Visit', Indonesia row", TP, ts)
# KPI 2025 p.19 Indonesia monthly -> annual totals
KPI = "https://data.tourism.gov.my/frontend/pdf/2025/publications/kpi/kpi_2025_new.pdf"
tsk = M["kpi_2025_new.pdf"]["retrieved_at_utc"]
toks = [l.strip() for l in fitz.open(R / "kpi_2025_new.pdf")[18].get_text().split("\n") if l.strip()]
blocks = {}
cur = None
k = 0
while k < len(toks):
    if toks[k] in ("VISITOR", "TOURIST", "EXCURSIONIST"):
        cur = toks[k]
        blocks[cur] = {}
        k += 1
        continue
    if cur and re.fullmatch(r"20\d\d", toks[k]) and k + 13 < len(toks):
        vals = toks[k + 1:k + 14]
        if all(re.fullmatch(r"[\d,]+", v) for v in vals):
            blocks[cur][toks[k]] = int(vals[-1].replace(",", ""))
            k += 14
            continue
    k += 1
for kind, lab in (("TOURIST", "persons (tourists = overnight visitors)"), ("VISITOR", "persons (visitors = tourists + excursionists)")):
    for y, v in sorted(blocks[kind].items()):
        add("Tourism Malaysia - Malaysia Tourism Key Performance Indicators 2025", "MYS", y, "Jan-Dec", "arrivals_from_indonesia", v, "", lab,
            "PDF p.19 'Indonesia' monthly table, TOTAL column", KPI, tsk)
print("MYS rows", sum(1 for o in out if o["destination_iso3"] == "MYS"), {k: len(v) for k, v in blocks.items()})

# ---------------- Singapore (values read from saved release text / annex charts; phrase asserted below)
SB = C._man(C.RAW / "stb")
BASE = "https://www.stb.gov.sg/about-stb/media-publications/media-centre/"
REL = {
    "2025": ("rel_jan_sep_2025.html", BASE + "record-singapore-tourism-receipts-from-january-to-september-2025/"),
    "2024": ("rel_singapore-achieves-historical-high-in-tourism-receipts-in-20.html", BASE + "singapore-achieves-historical-high-in-tourism-receipts-in-2024/"),
    "2023": ("rel_singapore-s-tourism-sector-posts-strong-recovery-in-2023--ex.html", BASE + "singapore-s-tourism-sector-posts-strong-recovery-in-2023--exceeds-forecasts-for-tourism-receipts/"),
    "2022": ("rel_singapore-s-tourism-sector-recovers-strongly-in-2022--visito.html", BASE + "singapore-s-tourism-sector-recovers-strongly-in-2022--visitor-numbers-expected-to-double-in-2023/"),
    "2021": ("rel_singapore-s-tourism-sector-remained-resilient-in-2021--ready.html", BASE + "singapore-s-tourism-sector-remained-resilient-in-2021--ready-for-recovery-in-2022-and-beyond/"),
}


def htmltxt(f):
    h = (C.RAW / "stb" / f).read_text(encoding="utf-8", errors="ignore")
    h = re.sub(r"<script.*?</script>|<style.*?</style>", "", h, flags=re.S)
    return re.sub(r"\s+", " ", H.unescape(re.sub(r"<[^>]+>", " ", h)))


VALS = {
    "2021": (127, "text: 'Visitors from China, Indonesia and India contributed $432 million, $127 million and $58 million in TR'", 33000, "$127 million", "33,000"),
    "2022": (1100, "text: 'top TR generating markets were Indonesia, India and Australia ... $1.1 billion, $704 million, and $633 million' (rounded to S$0.1bn)", 1100000, "$1.1 billion", "1.1 million"),
    "2023": (2183, "annex A chart 3: Indonesia 2,183 (S$ mil); text '$2.2 billion'", 2300000, "$2.2 billion", "2.3 million"),
    "2024": (2130, "annex A chart 3: S$2.13B; text '$2.13 billion'", 2490000, "$2.13 billion", "2.49 million"),
    "2025": (2090, "annex A chart 3: S$2.09B (YoY -3%); text 'S$2.09 billion'", 2400000, "S$2.09 billion", "2.4 million"),
}
for y, (rec, how, arr, phrase, arrtxt) in VALS.items():
    f, u = REL[y]
    assert phrase in htmltxt(f), (y, phrase)
    t = SB[f]["retrieved_at_utc"]
    add("Singapore Tourism Board (media release + annex)", "SGP", y, "Jan-Sep", "receipts_from_indonesia", rec, "SGD",
        "S$ million; tourism receipts EXCLUDING Sightseeing, Entertainment & Gaming (STB country analysis); Jan-Sep only (full-year by-market receipts not found in releases)", how, u, t)
    add("Singapore Tourism Board (media release)", "SGP", y, "Jan-Dec", "arrivals_from_indonesia", arr, "",
        f"persons (international visitor arrivals; rounded as published: {arrtxt})", "release text, IVA by market", u, t)
f, u = REL["2023"]
add("Singapore Tourism Board (annex A 2023, derived)", "SGP", "2019", "Jan-Sep", "receipts_from_indonesia", round(2183 / 0.964), "SGD",
    "S$ million DERIVED = 2,183 / 0.964 (annex chart 3 shows Indonesia Jan-Sep 2023 = 96.4% of Jan-Sep 2019); same exclusions",
    "annex A chart 3 (2023 release): total TR 2,183; '% of Jan to Sep 2019 TR' 96.4%", u, SB["YIR2023_annexA.pdf"]["retrieved_at_utc"])

# ---------------- Japan (numbers asserted against the saved PDFs)
JM = C._man(C.RAW / "jta")
JB = "https://www.mlit.go.jp/kankocho/content/"
SJ = "Japan Tourism Agency (Inbound consumption survey, formerly 訪日外国人消費動向調査) - calendar-year summary"


def ptxt(f, pg):
    return " ".join(fitz.open(C.RAW / "jta" / f)[pg - 1].get_text().split())


def jrow(y, f, v, pgno, anchor, ind, unit, where):
    assert anchor in ptxt(f, pgno), (f, pgno, anchor)
    add(SJ, "JPN", y, "Jan-Dec", ind, v, "JPY" if ind != "arrivals_from_indonesia" else "", unit, where, JB + f, JM[f]["retrieved_at_utc"])


OKU = "JPY 100 million (億円) - 訪日外国人旅行消費額 (all purposes); "
jrow("2018", "002020396.pdf", 558, 4, "インドネシア 558億円", "receipts_from_indonesia", OKU + "definitive, prior-year reference in 2019 summary", "p.4 prior-year pie")
jrow("2019", "002020396.pdf", 539, 4, "インドネシア 539億円", "receipts_from_indonesia", OKU + "definitive (確報)", "p.4")
jrow("2020", "002026218.pdf", 119, 1, "インドネシア 119億円", "receipts_from_indonesia", OKU + "trial estimate (試算値) from Q1 only (COVID)", "p.1")
jrow("2022", "002020310.pdf", 230, 1, "インドネシア 230億円", "receipts_from_indonesia", OKU + "trial values (試算値), limited airports", "p.1")
jrow("2023", "002020295.pdf", 852, 1, "インドネシア 852億円", "receipts_from_indonesia", OKU + "definitive", "p.1")
jrow("2024", "002020210.pdf", 1109, 1, "インドネシア 1,109億円", "receipts_from_indonesia", OKU + "definitive", "p.1")
jrow("2025", "002020046.pdf", 1309, 1, "インドネシア 1,309億円", "receipts_from_indonesia", OKU + "definitive (確報, published 2026-03-31)", "p.1")
PPU = "JPY per person per trip (1人当たり旅行支出, 一般客 = excluding cruise passengers, all purposes)"
jrow("2019", "002020396.pdf", 131087, 7, "インドネシア 131,087", "spend_per_capita", PPU, "p.7")
jrow("2020", "002026218.pdf", 153448, 2, "インドネシア 153,448", "spend_per_capita", PPU + "; Q1-2020 survey only", "p.2")
jrow("2023", "002020295.pdf", 198442, 4, "インドネシア 198,442", "spend_per_capita", PPU, "p.4")
jrow("2024", "002020210.pdf", 215034, 4, "インドネシア 215,034", "spend_per_capita", PPU, "p.4")
jrow("2025", "002020046.pdf", 205276, 4, "インドネシア 205,276", "spend_per_capita", PPU, "p.4")
AU = "persons (訪日外国人旅行者数)"
jrow("2019", "002020396.pdf", 410288, 6, "410,288", "arrivals_from_indonesia", AU, "p.6")
jrow("2020", "002026218.pdf", 77658, 2, "77,658", "arrivals_from_indonesia", AU + " (estimate)", "p.2")
jrow("2023", "002020295.pdf", 429262, 3, "429,262", "arrivals_from_indonesia", AU, "p.3")
jrow("2024", "002020210.pdf", 515468, 3, "515,468", "arrivals_from_indonesia", AU, "p.3")
jrow("2025", "002020046.pdf", 637382, 3, "637,382", "arrivals_from_indonesia", AU, "p.3")

# ---------------- Thailand
TM = C._man(C.RAW / "thailand_mots")
TH = "Thailand Ministry of Tourism & Sports - Tourism receipts from international tourist arrivals"
P = "TOURISM_RECEIPTS_FROM_INTERNATIONAL_TOURIST_ARRIVALS_"
ANN = {
    2015: (f"2015_480_{P}Jan_Dec_06145106.xlsx", "Total"),
    2016: (f"2016_436_{P}Jan_Dec_30102746.xlsx", "Summary"),
    2017: (f"2017_506_{P}2017_8__08182348.xlsx", "Summary"),
    2018: (f"2018_529_{P}Q1_Q4_2_09103229.xlsx", "Summary"),
    2019: (f"2019_615_{P}Q1_Q4_2_28135301.xlsx", "Summary"),
    2020: (f"2020_742_{P}Q1_Q4_2_Lnhsc3g=.xlsx", "Q1_Q4"),
    2021: (f"2021_745_{P}202116__Lnhsc3g=.xlsx", "Q1-Q4"),
    2022: (f"2022_761_{P}Q1_Q4_2_fab67039.xlsx", "Q1_Q4"),
    2023: (f"2023_797_{P}2023_9__11b2c1aa.xlsx", "Q1_Q4"),
    2024: (f"2024_810_{P}Q1_Q4_2_8cebf658.xlsx", "Q1-Q4"),
    2025: (f"2025_836_{P}Q1_Q4_2_b17486e2.xlsx", "Q1-Q4"),
}
for y, (f, sh) in ANN.items():
    ws = openpyxl.load_workbook(C.RAW / "thailand_mots" / f, data_only=True, read_only=True)[sh]
    rows = list(ws.iter_rows(values_only=True))
    hdr = " ".join(str(c) for r in rows[:4] for c in r if c is not None).upper()
    if str(y) not in hdr:   # 2021 sheet has Thai notes first; check whole top 8 rows
        hdr = " ".join(str(c) for r in rows[:8] for c in r if c is not None)
        assert "2564" in hdr or str(y) in hdr, (y, hdr[:150])
    row = next(r for r in rows if r and isinstance(r[0], str) and r[0].strip().lower() == "indonesia")
    arr, stay, bpd, upd, bmil, umil = row[1:7]
    url = TM[f]["url"]
    t = TM[f]["retrieved_at_utc"]
    wh = f"sheet '{sh}', row 'Indonesia' ({f})"
    add(TH, "THA", y, "Jan-Dec", "arrivals_from_indonesia", arr, "", "persons (international tourist arrivals)", wh, url, t)
    add(TH, "THA", y, "Jan-Dec", "spend_per_capita", round(bpd, 2), "THB", "THB per tourist per day (per capita spending)", wh, url, t)
    add(TH, "THA", y, "Jan-Dec", "spend_per_capita_usd", round(upd, 2), "USD", "USD per tourist per day (as published; MOTS exchange rate)", wh, url, t)
    add(TH, "THA", y, "Jan-Dec", "avg_stay_days", round(stay, 2), "", "days (length of stay)", wh, url, t)
    add(TH, "THA", y, "Jan-Dec", "receipts_from_indonesia", round(bmil, 2), "THB", "THB million (tourism receipts)", wh, url, t)
    add(TH, "THA", y, "Jan-Dec", "receipts_from_indonesia_usd", round(umil, 2), "USD", "USD million (tourism receipts, as published; MOTS exchange rate)", wh, url, t)

with open(C.EXTRACT / "destination_side.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=COLS)
    w.writeheader()
    w.writerows(out)
print(len(out), "rows", collections.Counter(o["destination_iso3"] for o in out))
