"""Thailand MOTS: discover 'TOURISM RECEIPTS FROM INTERNATIONAL TOURIST ARRIVALS' files per year (2015-2025) and download.
Run: python -I scripts/fetch_thailand_mots.py -> 02_raw/thailand_mots/ (manifest.csv), 02_raw/thailand_mots/discovery_log.csv"""
import importlib.util, re, html, csv
from pathlib import Path
_s = importlib.util.spec_from_file_location("s4", Path(__file__).resolve().parent / "s4_common.py")
C = importlib.util.module_from_spec(_s); _s.loader.exec_module(C)
RAW = C.RAW / "thailand_mots"; RAW.mkdir(parents=True, exist_ok=True)
YEARCAT = {2015: 479, 2016: 435, 2017: 414, 2018: 497, 2019: 521, 2020: 592, 2021: 628, 2022: 655, 2023: 704, 2024: 758, 2025: 805}
B = "https://www.mots.go.th"
def page(path):
    r = C.get(B + path)
    return r.text if r is not None and r.status_code == 200 else ""
def anchors(h):
    out = []
    for m in re.finditer(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', h, re.S):
        t = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", m.group(2)))).strip()
        out.append((m.group(1), t))
    return out
log = []
for y, c in YEARCAT.items():
    h = page(f"/news/category/{c}")
    (RAW / f"cat{c}.html").write_text(h, encoding="utf-8"); C.add_manifest(RAW, f"cat{c}.html", f"{B}/news/category/{c}", path=RAW / f"cat{c}.html")
    subs = [(u, t) for u, t in anchors(h) if "/news/category/" in u and re.search(r"RECEIPT|รายได้", t, re.I)]
    for u, t in subs:
        sid = u.rsplit("/", 1)[1]
        h2 = page(f"/news/category/{sid}")
        for fu, ft in anchors(h2):
            if re.search(r"\.(xlsx?|pdf)$", fu, re.I):
                log.append(dict(year_cat=y, subcat=sid, subcat_title=t[:80], file_title=ft[:100], url=fu))
                fn = f"{y}_{sid}_" + re.sub(r"[^A-Za-z0-9]+", "_", ft)[:60] + "_" + Path(fu).stem[-8:] + Path(fu).suffix
                st, p = C.save(fu if fu.startswith("http") else B + fu, RAW, fn)
                log[-1].update(saved=fn, status=st)
                print(y, sid, st, fn, flush=True)
        if not any(l["subcat"] == sid for l in log):
            log.append(dict(year_cat=y, subcat=sid, subcat_title=t[:80], file_title="(no xls/pdf links found)", url="", saved="", status=""))
            print(y, sid, "no files", t[:60], flush=True)
    if not subs:
        log.append(dict(year_cat=y, subcat="", subcat_title="(no receipts subcategory found)", file_title="", url="", saved="", status=""))
        print(y, "no receipts subcategory", flush=True)
with open(RAW / "discovery_log.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=["year_cat", "subcat", "subcat_title", "file_title", "url", "saved", "status"]); w.writeheader(); w.writerows(log)
