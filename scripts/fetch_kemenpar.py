"""Kemenpar discovery + download. Run: python -I scripts/fetch_kemenpar.py
Reads page RSC config per statistic page -> API module + filterData -> lists posts -> downloads linked files.
Outputs: 02_raw/kemenpar/{pages,api,files}/ + manifest.csv ; 03_extract/kemenpar_posts_index.csv"""
import importlib.util, json, re, csv, sys, html
from pathlib import Path
from urllib.parse import quote, urljoin
_s = importlib.util.spec_from_file_location("s4", Path(__file__).resolve().parent / "s4_common.py")
C = importlib.util.module_from_spec(_s); _s.loader.exec_module(C)

RAW = C.RAW / "kemenpar"
SLUGS = ["statistik-jasa-perjalanan", "statistik-devisa-pariwisata", "statistik-wisatawan-nasional",
         "statistik-wisatawan-mancanegara", "statistik-satelit-pariwisata", "publikasi-passenger-exit-survey",
         "publikasi-nesparnas", "publikasi-statistik-kunjungan-wisatawan-mancanegara", "direktori-statistik"]
API = "https://api.kemenpar.go.id/api/v1/"
C.S.headers.update({"Referer": "https://kemenpar.go.id/", "Origin": "https://kemenpar.go.id"})


def rsc_config(h):
    parts = re.findall(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)</script>', h, re.S)
    s = "\n".join(parts).encode().decode("unicode_escape", errors="ignore")
    m = re.search(r'"config":(\{"id".*?"filterData":(?:\{.*?\}|null)\})', s)
    if not m:
        m = re.search(r'"config":(\{.*?\})\}\]', s)
    try:
        return json.loads(m.group(1)) if m else None
    except Exception:
        return None


index = []
for slug in SLUGS:
    st, p = C.save("https://kemenpar.go.id/" + slug, RAW / "pages", slug + ".html")
    print(slug, st, flush=True)
    if st != 200:
        continue
    cfg = rsc_config(p.read_text(encoding="utf-8", errors="ignore"))
    print("  config:", json.dumps(cfg, ensure_ascii=False)[:400] if cfg else None, flush=True)
    if not cfg or not cfg.get("module"):
        continue
    pi = 0
    while True:
        q = dict(pageSize="100", query="", filterData=json.dumps(cfg.get("filterData") or {}),
                 order_by=cfg.get("orderBy") or "published_at", order_dir=cfg.get("orderDir") or "desc", pageIndex=str(pi))
        r = C.get(API + cfg["module"], params=q)
        if r is None or r.status_code != 200:
            print("  API fail", r.status_code if r is not None else None); break
        fn = f"{slug}__p{pi}.json"
        (RAW / "api").mkdir(parents=True, exist_ok=True)
        (RAW / "api" / fn).write_bytes(r.content)
        C.add_manifest(RAW / "api", fn, r.url, data=r.content)
        j = r.json()
        data = j.get("data", [])
        for d in data:
            desc = d.get("description") or ""
            links = re.findall(r"""href=["']([^"'\s>]+)""", desc.replace("\\", ""))
            files = [f.get("path") for f in (d.get("files") or []) if isinstance(f, dict)]
            index.append(dict(page=slug, id=d.get("id"), title=d.get("name"), published_at=d.get("published_at"),
                              category=(d.get("category") or {}).get("name"), links=" | ".join(links + [x for x in files if x]),
                              desc=re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", desc)))[:300]))
        print(f"  page {pi}: {len(data)} posts (last_page={j.get('last_page')} total={j.get('total')})", flush=True)
        if pi + 1 >= (j.get("last_page") or 1) or not data:
            break
        pi += 1

with open(C.EXTRACT / "kemenpar_posts_index.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=["page", "id", "title", "published_at", "category", "links", "desc"])
    w.writeheader(); w.writerows(index)
print("index rows", len(index))
