"""Extract by-country / total tables from Kemenpar PDFs (downloaded by download_kemenpar_files.py).
Run: python -I scripts/extract_kemenpar.py -> 03_extract/kemenpar_by_country.csv, kemenpar_totals.csv"""
import importlib.util, csv, re, glob
from pathlib import Path
import fitz
_s = importlib.util.spec_from_file_location("s4", Path(__file__).resolve().parent / "s4_common.py")
C = importlib.util.module_from_spec(_s); _s.loader.exec_module(C)
F = C.RAW / "kemenpar" / "files"
man = C._man(F)
NUM = re.compile(r"^-?[\d.]+(,\d+)?$|^-$")

def num(tok):
    tok = tok.strip()
    if tok in ("-", "", "..."): return None
    return float(tok.replace(".", "").replace(",", "."))   # Indonesian format: 1.234,56

def parse_rows(pdf, years, skip=("NEGARA", "Sumber", "Satuan", "Tahun", "Catatan")):
    toks = [l.strip() for l in fitz.open(pdf)[0].get_text().split("\n") if l.strip()]
    rows, cur = [], None
    for t in toks:
        if NUM.match(t) and not re.fullmatch(r"20\d\d", t) or (t == "-" and cur):
            if cur is not None: cur[1].append(t)
        elif re.fullmatch(r"20\d\d", t) and cur is None:
            continue
        else:
            if t.startswith(skip) or "TEMPAT" in t or t.upper().startswith(("DEVISA", "RATA-RATA", "RATA - RATA", "SATUAN", "SUMBER", "PERKEMBANGAN", "MENURUT")):
                cur = None; continue
            cur = [t, []]; rows.append(cur)
    return [(n, v) for n, v in rows if len(v) == len(years)]

def find(prefix): return glob.glob(str(F / (prefix + "*")))[0]

out = []
def add(prefix, years, indicator, unit, basis, title):
    p = find(prefix); fn = Path(p).name
    rows = parse_rows(p, years)
    for n, v in rows:
        for y, x in zip(years, v):
            val = num(x)
            if val is None: continue
            out.append(dict(source="Kemenpar (Pusdatin) / PES", table_title=title, indicator=indicator,
                            country_residence_id=(re.sub(r"\s+","",n) if re.fullmatch(r"(\w ){2,}\w",n.strip()) else re.sub(r"\s{2,}"," ",n.strip())), year=y, value=val, unit=unit, basis=basis,
                            raw_file=fn, url=man[fn]["url"], retrieved_at=man[fn]["retrieved_at_utc"]))
    print(prefix, len(rows), "rows")
    return rows

Y0914 = list(range(2009, 2015))
r629 = add("629_", Y0914, "wisman_receipts_total", "USD million", "inbound (credit-side), by country of residence, PES-based", "Devisa (Penerimaan) Wisman Menurut Negara Tempat Tinggal, 2009-2014")
add("626_", Y0914, "wisman_spend_per_visit", "USD", "inbound avg per visit", "Rata-rata Pengeluaran Wisman per Kunjungan Menurut Negara Tempat Tinggal, 2009-2014")
add("628_", Y0914, "wisman_spend_per_day", "USD", "inbound avg per day", "Rata-rata Pengeluaran Wisman per Hari Menurut Negara Tempat Tinggal, 2009-2014")
add("627_", Y0914, "wisman_length_of_stay", "days", "inbound", "Rata-rata Lama Tinggal Wisman Menurut Negara Tempat Tinggal, 2009-2014")
add("625_", Y0914, "wisman_arrivals", "persons", "inbound", "Perkembangan Wisman Menurut Negara Tempat Tinggal, 2009-2014")
Y1524 = [2015, 2016, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
add("10015_", Y1524, "wisman_spend_per_visit", "USD", "inbound avg per visit (BPS-derived; 2017 not published)", "Rata-Rata Pengeluaran Wisman per Kunjungan Menurut Negara Tempat Tinggal, 2015-2024")
Y1525 = Y1524 + [2025]
add("10133_", Y1525, "wisman_spend_per_visit", "USD", "inbound avg per visit by passport held (selected markets)", "Rata-Rata Pengeluaran Wisman per Kunjungan Menurut Paspor yang Dipegang, 2015-2025")

with open(C.EXTRACT / "kemenpar_by_country.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
print("by_country rows", len(out))

# totals
tot = []
def T(**k): tot.append(k)
def tokens(prefix): return [l.strip() for l in fitz.open(find(prefix))[0].get_text().split("\n") if l.strip()]
# BI-based devisa annual 2015-2024 (USD bn)
t = tokens("10006_"); fn = Path(find("10006_")).name
for i, x in enumerate(t):
    if re.fullmatch(r"20\d\d( \*\))?", x.strip()) and i + 1 < len(t) and re.fullmatch(r"[\d,]+", t[i + 1]):
        T(series="devisa_pariwisata_total", period=x.replace(" *)", " (provisional)"), value=float(t[i + 1].replace(",", ".")), unit="USD billion", basis="BI balance of payments travel credit (status: 2024 provisional)", raw_file=fn, url=man[fn]["url"], retrieved_at=man[fn]["retrieved_at_utc"])
fn = Path(find("10160_")).name; t = tokens("10160_")
for i, x in enumerate(t):
    if re.match(r"(Triwulan|20\d\d)", x) and i + 1 < len(t) and re.fullmatch(r"[\d.]+,\d+", t[i + 1]):
        T(series="devisa_pariwisata_total", period=x.replace("*)", "").strip(), value=num(t[i + 1]), unit="USD million", basis="BI balance of payments travel credit (2025 provisional; 2026 very provisional)", raw_file=fn, url=man[fn]["url"], retrieved_at=man[fn]["retrieved_at_utc"])
# 2022 quarterly (from the 2022-2025 sheet; later years taken from the newer sheet above)
fn = Path(find("10023_")).name; t = tokens("10023_")
for i, x in enumerate(t):
    if re.match(r"(Triwulan [IV]+ 2022|2022)$", x.replace("*)", "").strip()) and i + 1 < len(t) and re.fullmatch(r"[\d.]+,\d+", t[i + 1]):
        T(series="devisa_pariwisata_total", period=x.replace("*)", "").strip(), value=num(t[i + 1]), unit="USD million", basis="BI balance of payments travel credit", raw_file=fn, url=man[fn]["url"], retrieved_at=man[fn]["retrieved_at_utc"])
# NPI travel 2010-2016H1
fn = Path(find("2182_")).name; t = tokens("2182_")
i = 0
while i < len(t) - 3:
    if re.match(r"^(20\d\d\*{0,2}|Triwulan I-II 2016\*\*)$", t[i]) and re.fullmatch(r"-?[\d.]+", t[i + 1]):
        for k, nm in enumerate(["export_credit", "import_debit", "net"]):
            T(series="npi_travel_" + nm, period=t[i].replace("*", ""), value=float(t[i + 1 + k].replace(".", "")) , unit="USD million", basis="BI BoP travel credit/debit totals as republished by Kemenpar (Neraca Jasa Perjalanan Indonesia); thousands separator '.'", raw_file=fn, url=man[fn]["url"], retrieved_at=man[fn]["retrieved_at_utc"])
        i += 4
    else: i += 1
# wisnas outbound 2011-2016 (rekap)
fn = Path(find("582_")).name
T(series="wisnas_outbound_note", period="2011-2016", value="", unit="", basis="Totals only (no destination country): 2011 6,750,416 trips, USD 934.50/person, 7.67 days, USD 6,308.26m; 2012 7,453,633 (estimate), USD 926.20, USD 6,903.55m; 2013 8,024,876, USD 912.31, 6.49 days, USD 7,321.21m; 2014-2016 counts only (7,899,070; 7,908,534; 6,677,918 Jan-Oct)", raw_file=fn, url=man[fn]["url"], retrieved_at=man[fn]["retrieved_at_utc"])
with open(C.EXTRACT / "kemenpar_totals.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=["series", "period", "value", "unit", "basis", "raw_file", "url", "retrieved_at"]); w.writeheader(); w.writerows(tot)
print("totals rows", len(tot))
