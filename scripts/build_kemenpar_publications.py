"""Historical Kemenpar publications list with content flags (flags verified by text search of the downloaded PDFs, see README_s4.md).
Run: python -I scripts/build_kemenpar_publications.py -> 03_extract/kemenpar_publications.csv"""
import importlib.util, csv, re
from pathlib import Path
from urllib.parse import unquote, urlparse
_s = importlib.util.spec_from_file_location("s4", Path(__file__).resolve().parent / "s4_common.py")
C = importlib.util.module_from_spec(_s); _s.loader.exec_module(C)
rows = list(csv.DictReader(open(C.EXTRACT / "kemenpar_posts_index.csv", encoding="utf-8-sig")))
man = C._man(C.RAW / "kemenpar" / "files")
out, seen = [], set()
def local(url, pid):
    fn = f"{pid}_{re.sub(r'[^A-Za-z0-9._-]+', '_', unquote(Path(urlparse(url).path).name))}"
    return fn if fn in man else ""
def add(series, r, url, inbound, outbound, note):
    if url in seen: return
    seen.add(url)
    y = re.search(r"(20\d\d)", r["title"]); lf = local(url, r["id"])
    alt = url.replace("https://api.kemenpar.go.id/", "https://api2.kemenparekraf.go.id/") if "/storage/app/resources/" in url else ""
    out.append(dict(series=series, year=y.group(1) if y else "", title=r["title"], url=url, alt_url_api2=alt, kemenpar_page=r["page"],
                    inbound_spend_by_nationality=inbound, outbound_spend_by_destination_country=outbound, note=note, local_file=("files/" + lf) if lf else "(not downloaded)"))
for r in rows:
    t, p, c = r["title"], r["page"], r["category"]
    for u in [x.strip() for x in r["links"].split(" | ") if x.strip()]:
        if not re.search(r"\.(pdf|xlsx?)$", u, re.I): continue
        if p == "publikasi-passenger-exit-survey":
            add("Passenger Exit Survey (PES) / Statistik Profil Wisman", r, u, "YES (avg spend per day and per visit by country of residence; Tables ~10-33; no total-receipts-by-country table found in the table titles checked)", "NO", "Inbound survey at exit airports/ports; outbound residents not covered")
        elif p == "publikasi-nesparnas":
            add("Neraca Satelit Pariwisata Nasional (Nesparnas)", r, u, "TOTAL ONLY (wisman spend by product; not by nationality)", "NO (outbound = total Indonesian spend abroad; Buku 1 states destination country is not asked in the immigration A/D card; outbound survey last run 2013)", "Nesparnas 2014 p.66: qualitative only - outbound tourists mostly visit Malaysia and Singapore")
        elif p == "direktori-statistik" and c == "Publikasi Wisatawan Nusantara":
            add("Statistik Profil Wisatawan Nusantara (domestic)", r, u, "NO", "NO", "Domestic (nusantara) trips only; not outbound")
        elif p == "direktori-statistik" and c == "Neraca Jasa Perjalanan Indonesia":
            add("Neraca Jasa Perjalanan Indonesia", r, u, "TOTAL ONLY (BI BoP travel credit/debit 2010-2016H1)", "TOTAL ONLY", "Republished BI figures; no partner country")
        elif p == "statistik-wisatawan-nasional" and re.search(r"OUTBOUND|2019-2024|Pintu Kedatangan", t):
            add("Wisatawan Nasional (outbound) statistics", r, u, "NO", "NO (counts of trips; 2011-13 also total spend + per-person spend; no destination)", "rekap_wisnas.pdf 2011-2016: trips, USD/person, nights, total USD m")
        elif p == "publikasi-statistik-kunjungan-wisatawan-mancanegara" and re.search(r"Dalam Angka|Statistical Arrivals", t):
            add("Wisman Dalam Angka / Statistical Arrivals", r, u, "Dalam Angka: YES per-day/per-visit spend by residence (BPS-based); Statistical Arrivals: arrivals only", "NO", "")
        elif p == "statistik-devisa-pariwisata":
            add("Perkembangan Jumlah Devisa Sektor Pariwisata", r, u, "TOTAL ONLY (BI travel credit)", "NO", "No country split")
        elif p == "statistik-wisatawan-mancanegara" and re.search(r"Menurut|Per Kunjungan|Devisa|Profil", t):
            add("Wisman tables by country of residence (2009-2014 / 2015-2025)", r, u, "YES (see 03_extract/kemenpar_by_country.csv)", "NO", "")
out.sort(key=lambda d: (d["series"], d["year"]))
with open(C.EXTRACT / "kemenpar_publications.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
print(len(out), "rows")
