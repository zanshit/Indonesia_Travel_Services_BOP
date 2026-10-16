"""Merge sub-folder manifests of 02_raw/kemenpar into one manifest.csv (file = path relative to 02_raw/kemenpar).
Also registers the JS chunks (+ early API probe) fetched during discovery. Run: python -I scripts/finalize_kemenpar_manifest.py"""
import importlib.util, csv, hashlib
from pathlib import Path
from urllib.parse import quote
_s = importlib.util.spec_from_file_location("s4", Path(__file__).resolve().parent / "s4_common.py")
C = importlib.util.module_from_spec(_s); _s.loader.exec_module(C)
R = C.RAW / "kemenpar"
rows = {}
for sub in ("pages", "api", "files"):
    for k, r in C._man(R / sub).items():
        rows[f"{sub}/{k}"] = dict(file=f"{sub}/{k}", url=r["url"], retrieved_at_utc=r["retrieved_at_utc"], sha256=r["sha256"], bytes=r["bytes"])
JS = {"8174-f9fa623e84ec46d9.js": "8174-f9fa623e84ec46d9.js",
      "app__home___5Barticles_5D_page-d414c8f6859a833e.js": "app/(home)/%5Barticles%5D/page-d414c8f6859a833e.js",
      "app__home__layout-6dc35e3a81c31778.js": "app/(home)/layout-6dc35e3a81c31778.js"}
for fn, tail in JS.items():
    p = R / "js" / fn
    if p.exists():
        rows[f"js/{fn}"] = dict(file=f"js/{fn}", url="https://kemenpar.go.id/_next/static/chunks/" + tail, retrieved_at_utc="2026-10-15T15:10:00Z (approx.)",
                                sha256=hashlib.sha256(p.read_bytes()).hexdigest(), bytes=p.stat().st_size)
p = R / "api_stat_cat25.json"
if p.exists():
    rows["api_stat_cat25.json"] = dict(file="api_stat_cat25.json", url="https://api.kemenpar.go.id/api/v1/statistics/posts?pageSize=50&query=&filterData=%7B%22category_id%22%3A%2225%22%7D&order_by=published_at&order_dir=desc&pageIndex=0",
                                       retrieved_at_utc="2026-10-15T15:10:00Z (approx.)", sha256=hashlib.sha256(p.read_bytes()).hexdigest(), bytes=p.stat().st_size)
with open(R / "manifest.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=C.MCOLS); w.writeheader()
    for k in sorted(rows): w.writerow(rows[k])
print(len(rows), "rows")
