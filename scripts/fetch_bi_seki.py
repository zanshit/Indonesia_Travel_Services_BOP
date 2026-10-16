"""Download BI SEKI Table V.3 (XLS + PDF) into 02_raw/bi (re-runnable)."""
import csv, hashlib, time, datetime, pathlib, requests
ROOT = pathlib.Path(r"D:\Download\Indonesia_Travel_Services_BOP")
OUT = ROOT / "02_raw" / "bi"
URLS = ["https://www.bi.go.id/SEKI/tabel/TABEL5_3.xls", "https://www.bi.go.id/SEKI/tabel/TABEL5_3.pdf"]
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
OUT.mkdir(parents=True, exist_ok=True)
s = requests.Session(); s.headers.update({"User-Agent": UA, "Referer": "https://www.bi.go.id/id/statistik/ekonomi-keuangan/seki/Default.aspx"})
rows = []
for url in URLS:
    r = s.get(url, timeout=120, allow_redirects=True); r.raise_for_status()
    f = url.rsplit("/", 1)[1]
    (OUT / f).write_bytes(r.content)
    rows.append([f, url, datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), hashlib.sha256(r.content).hexdigest(), len(r.content)])
    print(f, r.status_code, len(r.content), r.headers.get("Content-Type")); time.sleep(1.5)
with open(OUT / "manifest.csv", "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["file","url","retrieved_at_utc","sha256","bytes"]); w.writerows(rows)
