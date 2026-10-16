"""Tourism Malaysia: (1) page-level read of the 860 MB Tourist Profile 2024 via HTTP Range (no full download);
(2) full download of Statistics in Brief 2024 and KPI 2025 (small). Extracts destination_side rows.
Run: python -I scripts/fetch_tourism_malaysia.py -> 02_raw/tourism_malaysia/ , 03_extract/tourism_malaysia_*.csv"""
import importlib.util, re, csv, sys, io
from pathlib import Path
_s = importlib.util.spec_from_file_location("s4", Path(__file__).resolve().parent / "s4_common.py")
C = importlib.util.module_from_spec(_s); _s.loader.exec_module(C)
_s2 = importlib.util.spec_from_file_location("rp", Path(__file__).resolve().parent / "rangepdf.py")
RP = importlib.util.module_from_spec(_s2); _s2.loader.exec_module(RP)
import pypdf
RAW = C.RAW / "tourism_malaysia"; RAW.mkdir(parents=True, exist_ok=True)
U = "https://data.tourism.gov.my/frontend/pdf/Malaysia_Tourist_Profile_2024%20v2.pdf"
PAGES = {9: "purpose_of_visit", 13: "expenditure_components", 15: "tourist_expenditure_by_country", 10: "arrivals_by_country"}

f = RP.RangeFile(U, block=1 << 20, cache_dir=C.ROOT / "02_raw" / "tourism_malaysia" / "_blk_cache")
rd = pypdf.PdfReader(f, strict=False)
print("total pages", len(rd.pages), "size", f.size)
texts = {}
w = pypdf.PdfWriter()
for p in sorted(PAGES):
    texts[p] = rd.pages[p - 1].extract_text()
    (RAW / f"TouristProfile2024_pdfpage{p:02d}_{PAGES[p]}.txt").write_text(texts[p], encoding="utf-8")
    C.add_manifest(RAW, f"TouristProfile2024_pdfpage{p:02d}_{PAGES[p]}.txt", U + f"#page={p}",
                   path=RAW / f"TouristProfile2024_pdfpage{p:02d}_{PAGES[p]}.txt")
    w.add_page(rd.pages[p - 1])
sub = RAW / "TouristProfile2024_pages_9_10_13_15_subset.pdf"
with open(sub, "wb") as fh: w.write(fh)
C.add_manifest(RAW, sub.name, U + "#pages=9,10,13,15 (page subset extracted by HTTP Range; not the full 860 MB file)", path=sub)
print("range requests:", f.nreq)
import shutil; shutil.rmtree(RAW / "_blk_cache", ignore_errors=True)

for u, fn in [("https://data.tourism.gov.my/frontend/pdf/New_Final_Malaysia%20Tourism%20Statistics%20in%20Brief%202024.pdf", "Malaysia_Tourism_Statistics_in_Brief_2024.pdf"),
              ("https://data.tourism.gov.my/frontend/pdf/2025/publications/kpi/kpi_2025_new.pdf", "kpi_2025_new.pdf")]:
    st, p = C.save(u, RAW, fn); print(fn, st, p.stat().st_size if p.exists() else 0)

# ---- parse
M = C.MCOLS
retr = C._man(RAW)[sub.name]["retrieved_at_utc"]
rows = []
def num(s): return None if s in ("-", "") else float(s.replace(",", ""))
# p15: left half rows + right half rows (same order)
lines = [l.strip() for l in texts[15].split("\n")]
left, right = [], []
for l in lines:
    m = re.match(r"^(.*?)\s+([\d,]+)\s+([\d,]+)\s+(-?[\d.]+)\s+([\d,.]+|-)\s+([\d,.]+|-)\s*$", l)
    if m and not l.startswith(("18", "PER", "TOURIST")): left.append(m.groups())
    else:
        t = l.split()
        if len(t) == 7 and all(re.fullmatch(r"-?[\d,.]+|-", x) for x in t): right.append(t)
print("p15 left", len(left), "right", len(right))
assert len(left) == len(right), "row mismatch"
tab15 = []
for L, R in zip(left, right):
    tab15.append(dict(country=L[0].strip(), arrivals_2024=num(L[1]), arrivals_2023=num(L[2]), arrivals_growth_pct=num(L[3]),
                      per_capita_rm_2024=num(L[4]), per_capita_rm_2023=num(L[5]), per_capita_growth_pct=num(R[0]),
                      avg_stay_nights_2024=num(R[1]), avg_stay_nights_2023=num(R[2]), avg_stay_diff=num(R[3]),
                      total_exp_rm_mil_2024=num(R[4]), total_exp_rm_mil_2023=num(R[5]), total_exp_growth_pct=num(R[6]),
                      pdf_page=15, printed_pages="18-19", source="Tourism Malaysia, Malaysia's Tourist Profile 2024 by Selected Markets",
                      url=U, retrieved_at=retr))
with open(C.EXTRACT / "tourism_malaysia_p15_expenditure_by_country.csv", "w", newline="", encoding="utf-8-sig") as fh:
    wr = csv.DictWriter(fh, fieldnames=list(tab15[0])); wr.writeheader(); wr.writerows(tab15)
# p13 components
comp_cols = ["Shopping", "Accommodation", "Food & Beverages", "International Airfares", "Local Transportation", "Medical", "Organised Tour", "Domestic Airfares", "Entertainment", "Fuel", "Others", "Sport"]
tab13 = []
for l in texts[13].split("\n"):
    m = re.match(r"^([A-Za-z ]+?)\s+((?:\d+\.\d\s*){12})$", l.strip())
    if m:
        v = [float(x) for x in m.group(2).split()]
        d = dict(country=m.group(1).strip(), **{c: x for c, x in zip(comp_cols, v)}, sum_pct=round(sum(v), 1), pdf_page=13, printed_page=15, url=U, retrieved_at=retr)
        tab13.append(d)
with open(C.EXTRACT / "tourism_malaysia_p13_expenditure_components.csv", "w", newline="", encoding="utf-8-sig") as fh:
    wr = csv.DictWriter(fh, fieldnames=list(tab13[0])); wr.writeheader(); wr.writerows(tab13)
print("p13 rows", len(tab13))
# p9 purpose
pur_cols = ["Holiday/Vacation", "Visit Friend/Relatives", "Shopping", "Medical", "Business", "M.I.C.E", "Sports", "Education", "Others", "Religious Purpose", "Honeymoon", "Official Mission", "Golfing", "Spa & Wellness"]
tab9 = []
for l in texts[9].split("\n"):
    m = re.match(r"^([A-Za-z .&-]+?)\s+((?:\d+\.\d\d\s*){14})$", l.strip())
    if m:
        v = [float(x) for x in m.group(2).split()]
        tab9.append(dict(country=m.group(1).strip(), **dict(zip(pur_cols, v)), sum_pct=round(sum(v), 2), pdf_page=9, printed_page=10, url=U, retrieved_at=retr))
with open(C.EXTRACT / "tourism_malaysia_p9_purpose_of_visit.csv", "w", newline="", encoding="utf-8-sig") as fh:
    wr = csv.DictWriter(fh, fieldnames=list(tab9[0])); wr.writeheader(); wr.writerows(tab9)
print("p9 rows", len(tab9))
