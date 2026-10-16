"""Download selected Kemenpar files listed in 03_extract/kemenpar_posts_index.csv (run fetch_kemenpar.py first).
Run: python -I scripts/download_kemenpar_files.py   -> 02_raw/kemenpar/files/ + manifest.csv"""
import importlib.util, csv, re
from pathlib import Path
from urllib.parse import unquote, urlparse
_s = importlib.util.spec_from_file_location("s4", Path(__file__).resolve().parent / "s4_common.py")
C = importlib.util.module_from_spec(_s); _s.loader.exec_module(C)
RAW = C.RAW / "kemenpar"
C.S.headers.update({"Referer": "https://kemenpar.go.id/"})
rows = list(csv.DictReader(open(C.EXTRACT / "kemenpar_posts_index.csv", encoding="utf-8-sig")))

def want(r):
    t, p = r["title"], r["page"]
    if p in ("statistik-jasa-perjalanan", "statistik-devisa-pariwisata", "publikasi-passenger-exit-survey",
             "publikasi-nesparnas", "statistik-satelit-pariwisata"):
        return True
    if r["category"] == "Neraca Jasa Perjalanan Indonesia": return True
    if p == "direktori-statistik" and r["category"] in ("Publikasi Wisatawan Nusantara",): return True
    if p == "statistik-wisatawan-nasional" and re.search(r"2019-2024|Pintu Kedatangan|OUTBOUND|Agustus Tahun 2026", t): return True
    if p == "statistik-wisatawan-mancanegara" and (re.search(r"Pengeluaran|Menurut|Rata|Devisa|Profil|Rekapitulasi", t)): return True
    if p == "publikasi-statistik-kunjungan-wisatawan-mancanegara" and re.search(r"Dalam Angka (2021|2023)|Dalam Angka 2023", t): return True  # 2022 edition (186 MB) deliberately skipped (>100 MB)
    return False

seen = set(); n = 0
for r in rows:
    if r["page"] == "direktori-statistik" and not want(r): continue
    if not want(r): continue
    for u in r["links"].split(" | "):
        u = u.strip()
        if not u or u in seen or "api.kemenpar" not in u and "api2.kemenparekraf" not in u: continue
        if not re.search(r"\.(pdf|xlsx?|docx?|zip)$", u, re.I): continue
        seen.add(u)
        base = unquote(Path(urlparse(u).path).name)
        fn = f"{r['id']}_{re.sub(r'[^A-Za-z0-9._-]+', '_', base)}"
        st, p = C.save(u, RAW / "files", fn)
        n += 1
        print(f"[{n}] {st} {fn} {p.stat().st_size if p.exists() else 0}", flush=True)
