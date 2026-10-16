"""Download ABS International Trade: Supplementary Information CY2025 tables 5-9 into 02_raw/abs (re-runnable)."""
import csv, hashlib, sys, time, datetime, pathlib, requests
ROOT = pathlib.Path(r"D:\Download\Indonesia_Travel_Services_BOP")
OUT = ROOT / "02_raw" / "abs"
BASE = "https://www.abs.gov.au/statistics/economy/international-trade/international-trade-supplementary-information-calendar-year/2025/"
FILES = ["536805500405.xlsx","536805500406.xlsx","536805500407.xlsx","536805500408.xlsx","536805500409.xlsx"]
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
OUT.mkdir(parents=True, exist_ok=True)
s = requests.Session(); s.headers.update({"User-Agent": UA, "Referer": "https://www.abs.gov.au/statistics/economy/international-trade/international-trade-supplementary-information-calendar-year/latest-release"})
rows = []
for f in FILES:
    url = BASE + f
    r = s.get(url, timeout=120); r.raise_for_status()
    (OUT / f).write_bytes(r.content)
    rows.append([f, url, datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), hashlib.sha256(r.content).hexdigest(), len(r.content)])
    print(f, r.status_code, len(r.content), r.headers.get("Content-Type")); time.sleep(1.5)
with open(OUT / "manifest.csv", "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["file","url","retrieved_at_utc","sha256","bytes"]); w.writerows(rows)
