"""Shared helpers for BPS WebAPI fetching. Key is read from env BPS_API_KEY and never written anywhere."""
import os, sys, time, json, hashlib, csv, datetime, re
import requests

ROOT = r"D:\Download\Indonesia_Travel_Services_BOP"
RAW_API = os.path.join(ROOT, "02_raw", "bps", "api")
RAW_PDF = os.path.join(ROOT, "02_raw", "bps", "pdf")
MANIFEST = os.path.join(ROOT, "02_raw", "bps", "manifest.csv")
EXTRACT = os.path.join(ROOT, "03_extract")
HOST = "https://webapi.bps.go.id/v1/api/"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

KEY = os.environ.get("BPS_API_KEY", "")
if not KEY:
    sys.exit("BPS_API_KEY not set")

_sess = requests.Session()
_sess.headers.update({"User-Agent": UA})
_last = [0.0]

def scrub(s):
    """Replace the API key with KEY anywhere in a string."""
    return s.replace(KEY, "KEY") if isinstance(s, str) else s

def throttle(min_gap=1.1):
    d = time.time() - _last[0]
    if d < min_gap:
        time.sleep(min_gap - d)
    _last[0] = time.time()

def http_get(url, stream=False, tries=5):
    """Polite GET with exponential backoff. Returns requests.Response (errors scrubbed of key)."""
    last = None
    for i in range(tries):
        throttle()
        try:
            r = _sess.get(url, timeout=120, stream=stream)
            if r.status_code == 200:
                return r
            last = f"HTTP {r.status_code}"
            if r.status_code in (400, 401, 403, 404):
                break
        except requests.RequestException as e:
            last = scrub(type(e).__name__ + ": " + str(e))
        time.sleep(2 ** (i + 1))
    raise RuntimeError(f"GET failed for {scrub(url)}: {last}")

def _manifest_append(row):
    new = not os.path.exists(MANIFEST)
    existing = set()
    if not new:
        with open(MANIFEST, newline="", encoding="utf-8") as f:
            existing = {r["file"] for r in csv.DictReader(f)}
    if row["file"] in existing:
        # rewrite row (re-run): replace line
        with open(MANIFEST, newline="", encoding="utf-8") as f:
            rows = [r for r in csv.DictReader(f) if r["file"] != row["file"]]
        rows.append(row)
        with open(MANIFEST, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["file","url_without_key","retrieved_at_utc","sha256","bytes"])
            w.writeheader(); w.writerows(rows)
        return
    with open(MANIFEST, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["file","url_without_key","retrieved_at_utc","sha256","bytes"])
        if new: w.writeheader()
        w.writerow(row)

def save_raw(content: bytes, folder, name, url):
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, name)
    if KEY.encode() in content:
        content = content.replace(KEY.encode(), b"KEY")  # defensive: never persist key
    with open(path, "wb") as f:
        f.write(content)
    rel = os.path.relpath(path, os.path.join(ROOT, "02_raw", "bps")).replace("\\", "/")
    _manifest_append({
        "file": rel, "url_without_key": scrub(url),
        "retrieved_at_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sha256": hashlib.sha256(content).hexdigest(), "bytes": len(content)})
    return path

def api_json(path_tail, name, cache=True):
    """GET HOST+path_tail (path_tail has no key; /key/KEY/ appended). Save raw json, return parsed."""
    folder = RAW_API
    fp = os.path.join(folder, name)
    if cache and os.path.exists(fp):
        with open(fp, encoding="utf-8") as f:
            return json.load(f)
    url = f"{HOST}{path_tail}key/{KEY}/"
    r = http_get(url)
    save_raw(r.content, folder, name, url)
    return r.json()

def write_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f); w.writerow(header); w.writerows(rows)
